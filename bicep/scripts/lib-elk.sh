#!/bin/bash
# ============================================================================
# Kibana and Logstash Configuration Library
# ============================================================================
# Functions for configuring ELK Stack logging and visualization
# ============================================================================

install_kibana() {
    log_info "Installing Kibana..."
    apt_install kibana
    log_success "Kibana installed"
}

install_logstash() {
    log_info "Installing Logstash..."
    apt_install logstash
    log_success "Logstash installed"
}

configure_kibana() {
    local elasticsearch_host=${1:-localhost}
    local kibana_host=${2:-0.0.0.0}
    local kibana_port=${3:-5601}
    
    log_info "Configuring Kibana..."
    
    cat >> /etc/kibana/kibana.yml << EOF

# ============================================================================
# Kibana Configuration (CALDERA Purple Team Lab)
# ============================================================================
server.host: "${kibana_host}"
server.port: ${kibana_port}
server.name: "caldera-kibana"

elasticsearch.hosts: ["http://${elasticsearch_host}:9200"]
elasticsearch.requestTimeout: 90000
elasticsearch.shardTimeout: 30000

logging:
  appenders:
    default:
      type: console
      layout:
        type: pattern
        pattern: "[%date{ISO8601}][%level]"
  root:
    level: warn

# Monitoring
monitoring.ui.container.elasticsearch.enabled: false
telemetry.enabled: false
xpack.security.enabled: false
EOF
    
    log_success "Kibana configuration created"
}

configure_logstash_beats_input() {
    log_info "Configuring Logstash beats input..."
    
    mkdir -p /etc/logstash/conf.d
    
    cat > /etc/logstash/conf.d/00-inputs.conf << 'EOF'
# ============================================================================
# Logstash Input Configuration
# ============================================================================

input {
  beats {
    port => 5044
    host => "0.0.0.0"
    ssl => false
    type => "beats"
  }
}
EOF
    
    log_success "Logstash inputs configured"
}

configure_logstash_winlogbeat() {
    log_info "Configuring Logstash for Winlogbeat..."
    
    mkdir -p /etc/logstash/conf.d
    
    cat > /etc/logstash/conf.d/40-winlogbeat.conf << 'EOF'
# ============================================================================
# Logstash Filter and Output for Windows Event Logs
# ============================================================================

filter {
  if [type] == "wineventlog" or [agent.type] == "winlogbeat" {
    mutate {
      add_field => { "[@metadata][index_name]" => "winlogbeat-%{+YYYY.MM.dd}" }
    }
    
    # Parse Windows event codes if needed
    if [winlog][event_id] {
      mutate {
        add_field => { "[event][id]" => "%{[winlog][event_id]}" }
      }
    }
  }
}

output {
  if [type] == "wineventlog" or [agent.type] == "winlogbeat" {
    elasticsearch {
      hosts => ["http://localhost:9200"]
      index => "%{[@metadata][index_name]}"
      document_type => "_doc"
    }
  }
}
EOF
    
    log_success "Logstash Winlogbeat output configured"
}

configure_logstash_default_output() {
    log_info "Configuring Logstash default output..."
    
    cat > /etc/logstash/conf.d/90-output.conf << 'EOF'
# ============================================================================
# Logstash Default Output
# ============================================================================

output {
  elasticsearch {
    hosts => ["http://localhost:9200"]
    index => "%{[@metadata][index_name]}-%{+YYYY.MM.dd}"
    document_type => "_doc"
  }
}
EOF
    
    log_success "Logstash default output configured"
}

configure_elk_stack() {
    local elasticsearch_host=${1:-localhost}
    
    log_info "Configuring ELK Stack..."
    
    install_kibana
    install_logstash
    configure_kibana "$elasticsearch_host" "0.0.0.0" "5601"
    configure_logstash_beats_input
    configure_logstash_winlogbeat
    configure_logstash_default_output
    
    # Fix permissions
    chown -R logstash:logstash /etc/logstash/conf.d
    chmod -R 644 /etc/logstash/conf.d/*
    
    # Enable and start services
    systemctl daemon-reload
    systemctl enable kibana logstash
    systemctl start kibana logstash
    
    wait_for_http "http://localhost:5601/api/status" "120"
    
    log_success "ELK Stack configured and running"
}

export -f install_kibana install_logstash
export -f configure_kibana configure_logstash_beats_input
export -f configure_logstash_winlogbeat configure_logstash_default_output
export -f configure_elk_stack
