#!/bin/bash
set -euo pipefail

# ============================================================================
# ELK Stack Setup Script (for Bicep CustomScriptExtension)
# ============================================================================
# This script is downloaded and executed on the ELK VM.
# It handles all software installation and configuration.
# ============================================================================

LOG_FILE=/var/log/elk-setup.log
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "[$(date)] Starting ELK Stack setup..."

# Install dependencies
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y apt-transport-https ca-certificates curl gnupg -qq

# Add Elastic repository
echo "[$(date)] Adding Elastic repository..."
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list

# Install ELK components
echo "[$(date)] Installing Elasticsearch, Kibana, Logstash..."
apt-get update -qq
apt-get install -y elasticsearch kibana logstash -qq

# Configure Elasticsearch
echo "[$(date)] Configuring Elasticsearch..."
cat >> /etc/elasticsearch/elasticsearch.yml << EOF
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
EOF

# Configure Kibana
echo "[$(date)] Configuring Kibana..."
cat >> /etc/kibana/kibana.yml << EOF
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://localhost:9200"]
EOF

# Configure Logstash to receive Winlogbeat data
echo "[$(date)] Configuring Logstash..."
cat > /etc/logstash/conf.d/winlogbeat.conf << EOF
input {
  beats {
    port => 5044
  }
}
output {
  elasticsearch {
    hosts => ["http://localhost:9200"]
    index => "winlogbeat-%{+YYYY.MM.dd}"
  }
}
EOF

# Enable and start services
echo "[$(date)] Starting ELK services..."
systemctl daemon-reload
systemctl enable elasticsearch
systemctl enable kibana
systemctl enable logstash
systemctl start elasticsearch
systemctl start kibana
systemctl start logstash

# Wait for services to start
echo "[$(date)] Waiting for services to stabilize..."
sleep 60

# Health checks
echo "[$(date)] Running health checks..."
if curl -sf "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=50s"; then
    echo "[$(date)] ✅ Elasticsearch is healthy"
else
    echo "[$(date)] ❌ Elasticsearch health check failed"
    exit 1
fi

if curl -sf "http://localhost:5601/api/status"; then
    echo "[$(date)] ✅ Kibana is healthy"
else
    echo "[$(date)] ❌ Kibana health check failed"
    exit 1
fi

echo "[$(date)] ✅ ELK Stack setup complete"
