#!/bin/bash
# ============================================================================
# CALDERA Deployment Health Check Script
# ============================================================================
# Verifies all deployed components are functioning correctly
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CALDERA_IP="${1:-localhost}"
CALDERA_PORT="${2:-8888}"
ELASTICSEARCH_PORT="${3:-9200}"
KIBANA_PORT="${4:-5601}"
TIMEOUT="${5:-10}"

# State
PASSED=0
FAILED=0

# ============================================================================
# FUNCTIONS
# ============================================================================

check_service() {
    local name=$1
    local host=$2
    local port=$3
    local endpoint=$4
    
    printf "%-30s " "Checking $name..."
    
    local url="http://${host}:${port}${endpoint}"
    
    if curl -sf --connect-timeout "$TIMEOUT" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

check_tcp_port() {
    local name=$1
    local host=$2
    local port=$3
    
    printf "%-30s " "Checking $name (TCP $port)..."
    
    if timeout "$TIMEOUT" bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

get_service_status() {
    local name=$1
    local host=$2
    local port=$3
    
    printf "%-30s " "Status of $name..."
    
    local status
    status=$(curl -sf --connect-timeout "$TIMEOUT" "http://${host}:${port}" 2>/dev/null | head -c 100)
    
    if [ -n "$status" ]; then
        echo -e "${BLUE}$status${NC}"
    else
        echo -e "${YELLOW}No response${NC}"
    fi
}

# ============================================================================
# CHECKS
# ============================================================================

echo -e "${BLUE}=========================================="
echo "CALDERA Purple Team Lab - Health Check"
echo "==========================================${NC}"
echo ""

echo -e "${BLUE}Network Connectivity:${NC}"
check_tcp_port "CALDERA Server" "$CALDERA_IP" "$CALDERA_PORT"
check_tcp_port "Elasticsearch" "$CALDERA_IP" "$ELASTICSEARCH_PORT"
check_tcp_port "Kibana" "$CALDERA_IP" "$KIBANA_PORT"
check_tcp_port "Logstash Beats" "$CALDERA_IP" "5044"

echo ""
echo -e "${BLUE}Service Health:${NC}"
check_service "CALDERA API" "$CALDERA_IP" "$CALDERA_PORT" ""
check_service "Elasticsearch" "$CALDERA_IP" "$ELASTICSEARCH_PORT" "/_cluster/health"
check_service "Kibana" "$CALDERA_IP" "$KIBANA_PORT" "/api/status"

echo ""
echo -e "${BLUE}CALDERA Operations:${NC}"
check_service "CALDERA Agents API" "$CALDERA_IP" "$CALDERA_PORT" "/api/agents"
check_service "CALDERA Abilities" "$CALDERA_IP" "$CALDERA_PORT" "/api/abilities"
check_service "CALDERA Operations" "$CALDERA_IP" "$CALDERA_PORT" "/api/operations"

echo ""
echo -e "${BLUE}Elasticsearch Indices:${NC}"
indices=$(curl -sf --connect-timeout "$TIMEOUT" \
    "http://${CALDERA_IP}:${ELASTICSEARCH_PORT}/_cat/indices?h=index" 2>/dev/null)

if [ -n "$indices" ]; then
    printf "%-30s " "Available Indices..."
    echo -e "${GREEN}Found ${PASSED:-0} indices${NC}"
    echo "$indices" | sed 's/^/  - /'
else
    printf "%-30s " "Available Indices..."
    echo -e "${YELLOW}No indices found (expected for new deployment)${NC}"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}=========================================="
echo "Summary"
echo "==========================================${NC}"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ "$FAILED" -eq 0 ]; then
    echo -e ""
    echo -e "${GREEN}All checks passed! Deployment is healthy.${NC}"
    echo -e ""
    echo "Access URLs:"
    echo "  CALDERA:  http://${CALDERA_IP}:${CALDERA_PORT}"
    echo "  Kibana:   http://${CALDERA_IP}:${KIBANA_PORT}"
    echo "  Elasticsearch: http://${CALDERA_IP}:${ELASTICSEARCH_PORT}"
    exit 0
else
    echo -e ""
    echo -e "${RED}Some checks failed. Please review above.${NC}"
    exit 1
fi
