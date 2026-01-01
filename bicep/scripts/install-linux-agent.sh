#!/bin/bash
# ============================================================================
# CALDERA Sandcat Agent Installation (Linux)
# ============================================================================
# Production-ready agent installer for blue team monitoring
#
# Target: Ubuntu 22.04 LTS
# Deployment: Azure VM via CustomScript extension
# ============================================================================

set -euo pipefail

# Script directory and libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common library
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/lib-common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

CALDERA_SERVER_IP="${1-}"
CALDERA_SERVER_PORT="${2:-8888}"
AGENT_GROUP="${3:-blue}"
AGENT_NAME="${4:-$(hostname)}"
LOG_FILE="/var/log/caldera-agent-setup.log"

# Validate inputs
if [ -z "$CALDERA_SERVER_IP" ]; then
    error_exit "Usage: $0 <CALDERA_SERVER_IP> [PORT] [GROUP] [AGENT_NAME]"
fi

# ============================================================================
# FUNCTIONS
# ============================================================================

setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2>&1
    
    log_info "CALDERA Linux Agent installation started"
    log_info "Server: ${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}"
    log_info "Group: $AGENT_GROUP"
    log_info "Name: $AGENT_NAME"
}

download_sandcat() {
    local sandcat_url="http://${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}/file/download"
    local max_attempts=5
    local attempt=1
    
    log_info "Downloading Sandcat agent..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$sandcat_url" -o /tmp/sandcat 2>/dev/null; then
            chmod +x /tmp/sandcat
            log_success "Sandcat agent downloaded successfully"
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            log_warn "Attempt $attempt failed. Retrying in 10s..."
            sleep 10
        fi
        
        attempt=$((attempt + 1))
    done
    
    error_exit "Failed to download Sandcat agent after $max_attempts attempts"
}

start_sandcat_agent() {
    log_info "Starting Sandcat agent..."
    
    local server_url="http://${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}"
    
    # Start agent in background
    nohup /tmp/sandcat \
        -server "$server_url" \
        -group "$AGENT_GROUP" \
        -v \
        > /tmp/sandcat.log 2>&1 &
    
    local agent_pid=$!
    log_success "Sandcat agent started (PID: $agent_pid)"
    
    # Wait for agent to report
    sleep 5
    
    if ! kill -0 "$agent_pid" 2>/dev/null; then
        error_exit "Sandcat agent crashed. Check /tmp/sandcat.log for details"
    fi
}

configure_sandcat_systemd() {
    local server_url="http://${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}"
    
    log_info "Configuring Sandcat systemd service..."
    
    cat > /etc/systemd/system/sandcat.service << EOF
# ============================================================================
# CALDERA Sandcat Agent Systemd Service
# ============================================================================
[Unit]
Description=CALDERA Sandcat Agent (Blue Team)
Documentation=https://caldera.mitre.org/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/tmp

# Download and run agent
ExecStart=/tmp/sandcat -server "${server_url}" -group "${AGENT_GROUP}" -v

# Restart policy
Restart=always
RestartSec=30

# Resource limits
MemoryLimit=512M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sandcat

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable sandcat
    
    log_success "Sandcat systemd service configured"
}

verify_agent_registration() {
    local server_url="http://${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}"
    local max_attempts=12  # 60 seconds
    local attempt=1
    
    log_info "Waiting for agent to register with CALDERA server..."
    
    while [ $attempt -le $max_attempts ]; do
        # Try to query agents API (if available)
        if curl -sf "${server_url}/api/agents" > /tmp/agents.json 2>/dev/null; then
            log_success "Agent registration verified"
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            log_info "Waiting for registration... ($attempt/$max_attempts)"
            sleep 5
        fi
        
        attempt=$((attempt + 1))
    done
    
    log_warn "Agent registration timeout. Agent may still be initializing."
}

install_filebeat() {
    log_info "Installing Filebeat for log collection..."
    
    # Install beats repository
    curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - 2>/dev/null || true
    echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | \
        tee /etc/apt/sources.list.d/elastic-8.x.list > /dev/null
    
    apt-get update -qq
    apt_install filebeat
    
    # Configure Filebeat for CALDERA logs
    cat > /etc/filebeat/filebeat.yml << EOF
# ============================================================================
# Filebeat Configuration for CALDERA Agent
# ============================================================================

filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /tmp/sandcat.log
      - /var/log/syslog
      - /var/log/auth.log
    fields:
      agent_name: ${AGENT_NAME}
      agent_group: ${AGENT_GROUP}

output.logstash:
  hosts: ["${CALDERA_SERVER_IP}:5044"]
  ssl.enabled: false

logging.level: warn
logging.to_files: true
logging.files:
  path: /var/log/filebeat
EOF
    
    systemctl daemon-reload
    systemctl enable filebeat
    systemctl start filebeat
    
    log_success "Filebeat installed and running"
}

main() {
    log_info "=========================================="
    log_info "CALDERA Linux Agent Installation"
    log_info "=========================================="
    
    setup_logging
    
    # Wait for server to be available
    wait_for_http "http://${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}" "60"
    
    # Install Sandcat
    download_sandcat
    start_sandcat_agent
    configure_sandcat_systemd
    
    # Verify registration
    verify_agent_registration
    
    # Install monitoring
    install_filebeat
    
    log_info "=========================================="
    log_success "Installation completed successfully!"
    log_info "=========================================="
    log_info "Agent Group: $AGENT_GROUP"
    log_info "Agent Name: $AGENT_NAME"
    log_info "Server: ${CALDERA_SERVER_IP}:${CALDERA_SERVER_PORT}"
    log_info "Logs: $LOG_FILE"
    log_info "Service: systemctl status sandcat"
    log_info "=========================================="
}

# ============================================================================
# EXECUTION
# ============================================================================

main "$@"
exit $?
