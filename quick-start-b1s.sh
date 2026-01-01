#!/bin/bash
# =============================================================================
# B1s Quick Start Script
# Deploys Caldera + Elasticsearch stack optimized for Azure B1s (1GB RAM)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Pre-flight checks
# =============================================================================
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Install with: sudo apt install docker.io"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose not found. Install with: sudo apt install docker-compose"
        exit 1
    fi
    
    # Determine compose command (docker-compose vs docker compose)
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Check available memory (Linux only)
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
        if [ "$TOTAL_MEM" -lt 900 ]; then
            log_warn "Low memory detected: ${TOTAL_MEM}MB. B1s requires careful tuning."
        fi
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_warn ".env file not found. Creating from template..."
        cp .env.b1s .env
        log_info "Please edit .env with your configuration before proceeding."
        log_info "At minimum, set CALDERA_API_KEY_RED and ELASTIC_PASSWORD"
        exit 1
    fi
    
    log_info "Pre-flight checks passed ✅"
}

# =============================================================================
# Start B1s-optimized stack
# =============================================================================
start_b1s_stack() {
    log_info "Starting B1s-optimized Caldera + ELK stack..."
    
    # Use B1s override
    if [ -f "docker-compose.b1s.yml" ]; then
        $COMPOSE_CMD -f docker-compose.yml -f docker-compose.b1s.yml up -d
    else
        $COMPOSE_CMD up -d elasticsearch caldera
    fi
    
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check Elasticsearch health
    log_info "Checking Elasticsearch health..."
    for i in {1..30}; do
        if curl -s "http://localhost:9200/_cluster/health" | grep -q '"status":"green"\|"status":"yellow"'; then
            log_info "Elasticsearch is healthy ✅"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Elasticsearch failed to start"
            docker-compose logs elasticsearch
            exit 1
        fi
        sleep 10
    done
    
    # Check Caldera health
    log_info "Checking Caldera health..."
    for i in {1..20}; do
        if curl -s "http://localhost:8888/api/v2/health" | grep -q 'ok'; then
            log_info "Caldera is healthy ✅"
            break
        fi
        if [ $i -eq 20 ]; then
            log_warn "Caldera may still be starting. Check logs with: docker-compose logs caldera"
        fi
        sleep 5
    done
}

# =============================================================================
# Show memory usage
# =============================================================================
show_memory() {
    log_info "Docker container memory usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo ""
    log_info "System memory:"
    if command -v free &> /dev/null; then
        free -h
    else
        # macOS alternative
        vm_stat | head -10
    fi
}

# =============================================================================
# Start webhook service (host Python, not containerized)
# =============================================================================
start_webhook_service() {
    log_info "Installing webhook service dependencies..."
    pip3 install flask aiohttp weasyprint jinja2 --quiet 2>/dev/null || {
        log_warn "pip3 install failed. You may need to install manually."
    }
    
    log_info "Starting webhook service..."
    cd orchestrator
    nohup python3 services/webhook_service.py > ../logs/webhook.log 2>&1 &
    WEBHOOK_PID=$!
    echo $WEBHOOK_PID > ../webhook.pid
    cd ..
    
    sleep 3
    if kill -0 $WEBHOOK_PID 2>/dev/null; then
        log_info "Webhook service started (PID: $WEBHOOK_PID) ✅"
        log_info "Webhook endpoint: http://localhost:5000/webhook/caldera-complete"
    else
        log_warn "Webhook service may have failed. Check logs/webhook.log"
    fi
}

# =============================================================================
# Stop all services
# =============================================================================
stop_all() {
    log_info "Stopping all services..."
    
    # Stop webhook service
    if [ -f "webhook.pid" ]; then
        kill $(cat webhook.pid) 2>/dev/null || true
        rm webhook.pid
    fi
    
    # Stop Docker containers
    $COMPOSE_CMD down
    
    log_info "All services stopped ✅"
}

# =============================================================================
# Main
# =============================================================================
case "${1:-}" in
    start)
        preflight_checks
        start_b1s_stack
        show_memory
        echo ""
        log_info "🎯 Caldera POC Stack Started!"
        log_info "  Caldera:       http://localhost:8888"
        log_info "  Elasticsearch: http://localhost:9200"
        log_info ""
        log_info "To start webhook automation:"
        log_info "  $0 webhook"
        ;;
    webhook)
        start_webhook_service
        ;;
    stop)
        stop_all
        ;;
    status)
        show_memory
        echo ""
        log_info "Service endpoints:"
        curl -s "http://localhost:8888/api/v2/health" && echo " <- Caldera" || echo "Caldera: DOWN"
        curl -s "http://localhost:9200/_cluster/health?pretty" | head -5 || echo "Elasticsearch: DOWN"
        curl -s "http://localhost:5000/health" && echo " <- Webhook" || echo "Webhook: DOWN"
        ;;
    logs)
        $COMPOSE_CMD logs -f --tail=100
        ;;
    *)
        echo "Caldera POC B1s Quick Start"
        echo ""
        echo "Usage: $0 {start|stop|status|webhook|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Caldera + Elasticsearch (B1s optimized)"
        echo "  stop    - Stop all services"
        echo "  status  - Show memory usage and service health"
        echo "  webhook - Start webhook automation service"
        echo "  logs    - Follow Docker container logs"
        echo ""
        echo "Memory Budget (B1s 1GB):"
        echo "  Elasticsearch: 512MB (256MB heap)"
        echo "  Caldera:       256MB"
        echo "  OS/Docker:     ~200MB"
        echo "  Headroom:      32MB"
        ;;
esac
