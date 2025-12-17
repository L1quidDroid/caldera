#!/bin/bash
################################################################################
# Install Filebeat for CALDERA Log Collection
# Collects CALDERA operation logs and sends to Elasticsearch/Kibana
################################################################################

set -e

echo "================================================"
echo "🚀 Installing Filebeat for CALDERA Logging"
echo "================================================"
echo ""

# Check if Elasticsearch repository is configured
if [ ! -f /usr/share/keyrings/elastic.gpg ]; then
    echo "📦 Adding Elasticsearch repository..."
    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
    echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
        sudo tee /etc/apt/sources.list.d/elastic-8.x.list
    sudo apt-get update
fi

# Install Filebeat
echo "📦 Installing Filebeat..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y filebeat

echo "✅ Filebeat installed"

# Configure Filebeat for CALDERA
echo "⚙️  Configuring Filebeat for CALDERA..."

sudo tee /etc/filebeat/filebeat.yml > /dev/null << 'EOF'
###################### Filebeat Configuration ######################

# ============================== Filebeat inputs ==============================
filebeat.inputs:

# CALDERA Operation Logs
- type: log
  enabled: true
  paths:
    - /home/*/caldera/logs/*.log
    - /var/log/caldera/*.log
  fields:
    log_type: caldera_operation
    service: caldera
  fields_under_root: true
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

# CALDERA systemd service logs
- type: journald
  enabled: true
  id: caldera-service
  include_matches:
    - _SYSTEMD_UNIT=caldera.service
  fields:
    log_type: caldera_service
    service: caldera
  fields_under_root: true

# Agent activity logs (if agents write to files)
- type: log
  enabled: true
  paths:
    - /home/*/elasticat.log
    - /home/*/sandcat.log
    - /var/log/caldera/agents/*.log
  fields:
    log_type: caldera_agent
    service: caldera_agent
  fields_under_root: true

# System security logs (for agent activity correlation)
- type: log
  enabled: true
  paths:
    - /var/log/auth.log
    - /var/log/secure
  fields:
    log_type: system_security
    service: system
  fields_under_root: true

# ============================== Processors ===============================
processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_cloud_metadata: ~
  - add_docker_metadata: ~
  - add_kubernetes_metadata: ~
  - add_fields:
      target: ''
      fields:
        environment: azure_demo
        deployment: purple_team_lab

# ============================= Elasticsearch output ==============================
output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "caldera-logs-%{+yyyy.MM.dd}"
  
# Disable ILM (Index Lifecycle Management) for simpler setup
setup.ilm.enabled: false

# ============================= Kibana setup =====================================
setup.kibana:
  host: "localhost:5601"

# Index template settings
setup.template.name: "caldera-logs"
setup.template.pattern: "caldera-logs-*"
setup.template.settings:
  index.number_of_shards: 1
  index.number_of_replicas: 0

# ============================= Logging ========================================
logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644

EOF

echo "✅ Filebeat configuration created"

# Set permissions for log directories
echo "📁 Setting up log directories..."

# Create CALDERA log directory if it doesn't exist
mkdir -p ~/caldera/logs
sudo mkdir -p /var/log/caldera/agents

# Allow Filebeat to read user logs
sudo usermod -a -G adm filebeat 2>/dev/null || true

echo "✅ Log directories configured"

# Configure CALDERA to output structured logs
echo "⚙️  Configuring CALDERA logging..."

if [ -f ~/caldera/conf/local.yml ]; then
    # Add logging configuration if not present
    if ! grep -q "logging:" ~/caldera/conf/local.yml; then
        cat >> ~/caldera/conf/local.yml << 'EOF'

# Logging configuration for ELK integration
logging:
  level: INFO
  format: json
  output: file
  file: logs/caldera.log
EOF
        echo "✅ Added logging configuration to local.yml"
    else
        echo "ℹ️  Logging already configured in local.yml"
    fi
fi

# Setup Filebeat
echo "🔧 Setting up Filebeat..."

# Load index template
sudo filebeat setup --index-management -E output.logstash.enabled=false -E 'output.elasticsearch.hosts=["localhost:9200"]'

# Enable and start Filebeat
sudo systemctl daemon-reload
sudo systemctl enable filebeat
sudo systemctl restart filebeat

echo "✅ Filebeat started"

# Wait for Filebeat to start
sleep 5

# Check Filebeat status
if sudo systemctl is-active --quiet filebeat; then
    echo "✅ Filebeat is running"
else
    echo "❌ Filebeat failed to start"
    sudo journalctl -u filebeat -n 20 --no-pager
    exit 1
fi

# Test Elasticsearch connection
echo ""
echo "🧪 Testing Elasticsearch connection..."
if curl -s http://localhost:9200/_cat/indices | grep -q caldera; then
    echo "✅ CALDERA indices detected in Elasticsearch"
else
    echo "⏳ CALDERA indices not yet created (will appear after log activity)"
fi

# Create Kibana index pattern
echo ""
echo "📊 Setting up Kibana index pattern..."

# Wait for Kibana to be ready
for i in {1..30}; do
    if curl -s http://localhost:5601/api/status | grep -q "available"; then
        break
    fi
    sleep 2
done

# Create index pattern via Kibana API
curl -X POST "http://localhost:5601/api/saved_objects/index-pattern/caldera-logs-*" \
    -H 'kbn-xsrf: true' \
    -H 'Content-Type: application/json' \
    -d '{
        "attributes": {
            "title": "caldera-logs-*",
            "timeFieldName": "@timestamp"
        }
    }' 2>/dev/null || echo "ℹ️  Index pattern may already exist"

echo ""
echo "================================================"
echo "✅ FILEBEAT INSTALLATION COMPLETE"
echo "================================================"
echo ""
echo "📊 Log Collection Configured:"
echo "   • CALDERA operation logs: ~/caldera/logs/*.log"
echo "   • CALDERA service logs: journald (caldera.service)"
echo "   • Agent activity logs: ~/elasticat.log, ~/sandcat.log"
echo "   • System security logs: /var/log/auth.log"
echo ""
echo "📈 Elasticsearch Index: caldera-logs-YYYY.MM.DD"
echo ""
echo "🌐 View Logs in Kibana:"
echo "   1. Open: http://$(curl -s icanhazip.com):5601"
echo "   2. Navigate to: Discover"
echo "   3. Select index pattern: caldera-logs-*"
echo "   4. Filter by:"
echo "      - log_type: caldera_operation"
echo "      - log_type: caldera_agent"
echo "      - log_type: system_security"
echo ""
echo "🔍 Verify Filebeat Status:"
echo "   sudo systemctl status filebeat"
echo "   sudo filebeat test output"
echo "   sudo filebeat test config"
echo ""
echo "📝 View Filebeat Logs:"
echo "   sudo journalctl -u filebeat -f"
echo ""
echo "🔄 Restart Services:"
echo "   sudo systemctl restart filebeat"
echo "   sudo systemctl restart caldera"
echo ""
echo "================================================"
echo ""
