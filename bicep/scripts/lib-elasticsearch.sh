#!/bin/bash
# ============================================================================
# Elasticsearch Configuration Library
# ============================================================================
# Functions for installing and configuring Elasticsearch with proper heap/tuning
# ============================================================================

setup_elasticsearch_repository() {
    log_info "Adding Elasticsearch repository..."
    curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg
    echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" \
        | tee /etc/apt/sources.list.d/elastic-8.x.list > /dev/null
    log_success "Elasticsearch repository added"
}

install_elasticsearch() {
    log_info "Installing Elasticsearch..."
    apt_install elasticsearch
    log_success "Elasticsearch installed"
}

configure_elasticsearch_heap() {
    local heap_size=${1:-256m}
    
    log_info "Configuring Elasticsearch heap size: $heap_size"
    
    mkdir -p /etc/elasticsearch/jvm.options.d
    
    cat > /etc/elasticsearch/jvm.options.d/heap.options << EOF
-Xms${heap_size}
-Xmx${heap_size}
EOF
    
    log_success "Elasticsearch heap configured to $heap_size"
}

configure_elasticsearch_kernel() {
    log_info "Tuning kernel parameters for Elasticsearch..."
    
    echo "vm.max_map_count=262144" > /etc/sysctl.d/99-elasticsearch.conf
    sysctl -w vm.max_map_count=262144 || true
    sysctl --system || true
    
    log_success "Kernel parameters tuned"
}

configure_elasticsearch_yml() {
    local network_host=${1:-0.0.0.0}
    local security_enabled=${2:-false}
    
    log_info "Creating elasticsearch.yml configuration..."
    
    # Remove any existing config to avoid duplicate fields
    rm -f /etc/elasticsearch/elasticsearch.yml
    
    cat > /etc/elasticsearch/elasticsearch.yml << EOF
# ============================================================================
# Elasticsearch Configuration (Auto-generated for CALDERA Purple Team Lab)
# ============================================================================

# Node and cluster settings
node.name: caldera-elasticsearch
cluster.name: caldera-elk-cluster
cluster.initial_master_nodes: ["caldera-elasticsearch"]

# Network settings
network.host: ${network_host}
http.port: 9200

# Discovery (single-node cluster)
discovery.type: single-node

# Security (disabled for lab environment - ENABLE in production)
xpack.security.enabled: ${security_enabled}
xpack.security.enrollment.enabled: false

# Logging
logger.level: warn
EOF
    
    log_success "Elasticsearch configuration created"
}

install_elasticsearch_complete() {
    local heap_size=${1:-256m}
    
    log_info "Starting Elasticsearch installation..."
    
    setup_elasticsearch_repository
    apt_install elasticsearch
    configure_elasticsearch_kernel
    configure_elasticsearch_heap "$heap_size"
    configure_elasticsearch_yml "0.0.0.0" "false"
    
    systemctl daemon-reload
    systemctl enable elasticsearch
    systemctl start elasticsearch
    
    wait_for_port "localhost" "9200" "120"
    
    # Health check
    if curl -sf "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=50s" > /dev/null; then
        log_success "Elasticsearch is healthy"
    else
        error_exit "Elasticsearch health check failed"
    fi
}

export -f setup_elasticsearch_repository install_elasticsearch
export -f configure_elasticsearch_heap configure_elasticsearch_kernel
export -f configure_elasticsearch_yml install_elasticsearch_complete
