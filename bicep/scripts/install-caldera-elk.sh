#!/bin/bash
# ============================================================================
# CALDERA & ELK Server Installation Script
# ============================================================================
# Production-ready installer for Caldera adversary emulation platform
# with integrated ELK Stack (Elasticsearch, Kibana, Logstash)
#
# Target: Ubuntu 22.04 LTS
# Deployment: Azure VM via CustomScript extension
# ============================================================================

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source library functions
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib-common.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib-elasticsearch.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib-caldera.sh"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib-elk.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

ADMIN_USERNAME="${1-}"
CALDERA_HOME="/home/${ADMIN_USERNAME:-$(detect_admin_user)}"
ELASTICSEARCH_HEAP_SIZE="${ES_HEAP_SIZE:-256m}"
LOG_FILE="/var/log/caldera-elk-setup.log"
START_TIME=$(date +%s)

# Export for subshells
export CALDERA_HOME ADMIN_USERNAME LOG_FILE

# ============================================================================
# SETUP
# ============================================================================

setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2>&1
    
    log_info "Caldera & ELK installation started"
    log_info "Admin user: $ADMIN_USERNAME"
    log_info "Caldera home: $CALDERA_HOME"
    log_info "Elasticsearch heap: $ELASTICSEARCH_HEAP_SIZE"
}

validate_environment() {
    log_info "Validating environment..."
    
    assert_ubuntu
    require_command curl
    require_command git
    require_command python3
    require_command apt-get
    require_command systemctl
    
    check_disk_space 50  # 50GB required
    check_memory 2048    # 2GB minimum
    
    log_success "Environment validation passed"
}

update_system() {
    log_info "Updating system packages..."
    
    export DEBIAN_FRONTEND=noninteractive
    
    # Clean existing state
    apt-get clean || true
    rm -rf /var/lib/apt/lists/* || true
    
    # Update with retries
    retry apt-get update \
        -o Acquire::Retries=5 \
        -o Acquire::http::Timeout=30 \
        -o Acquire::https::Timeout=30 \
        -qq
    
    # Install base packages
    apt_install \
        ca-certificates apt-transport-https gnupg curl wget \
        software-properties-common build-essential git
    
    # Add universe repository
    add-apt-repository -y universe || true
    
    retry apt-get update -qq
    
    log_success "System packages updated"
}

main() {
    log_info "=========================================="
    log_info "CALDERA & ELK Stack Installation"
    log_info "=========================================="
    
    # Phase 1: System preparation
    setup_logging
    validate_environment
    update_system
    
    # Phase 2: Elasticsearch installation
    log_info "=========================================="
    log_info "Phase 1: Installing Elasticsearch..."
    log_info "=========================================="
    install_elasticsearch_complete "$ELASTICSEARCH_HEAP_SIZE"
    
    # Phase 3: CALDERA installation
    log_info "=========================================="
    log_info "Phase 2: Installing CALDERA..."
    log_info "=========================================="
    install_caldera_complete "$CALDERA_HOME" "$ADMIN_USERNAME"
    
    # Phase 4: ELK Stack completion (Kibana + Logstash)
    log_info "=========================================="
    log_info "Phase 3: Configuring ELK Stack..."
    log_info "=========================================="
    configure_elk_stack "localhost"
    
    # Phase 5: Health checks
    log_info "=========================================="
    log_info "Running health checks..."
    log_info "=========================================="
    
    sleep 30  # Give services time to stabilize
    
    if curl -sf "http://localhost:9200/_cluster/health" > /dev/null; then
        log_success "✓ Elasticsearch is healthy"
    else
        error_exit "Elasticsearch health check failed"
    fi
    
    if curl -sf "http://localhost:5601/api/status" > /dev/null; then
        log_success "✓ Kibana is healthy"
    else
        log_warn "⚠ Kibana health check failed (may still be initializing)"
    fi
    
    if curl -sf "http://localhost:8888" > /dev/null; then
        log_success "✓ CALDERA is responding"
    else
        error_exit "CALDERA health check failed"
    fi
    
    # Phase 6: Summary
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    log_info "=========================================="
    log_success "Installation completed successfully!"
    log_info "=========================================="
    log_info "Duration: $((duration / 60))m $((duration % 60))s"
    log_info ""
    log_info "Access URLs:"
    log_info "  CALDERA:  http://localhost:8888 (user: red, pass: admin)"
    log_info "  Kibana:   http://localhost:5601"
    log_info "  Elasticsearch: http://localhost:9200"
    log_info ""
    log_info "Configuration:"
    log_info "  Caldera home: $CALDERA_HOME"
    log_info "  Config: $CALDERA_HOME/caldera/conf/local.yml"
    log_info "  Logs: $LOG_FILE"
    log_info "=========================================="
}

# ============================================================================
# EXECUTION
# ============================================================================

main "$@"
exit $?
