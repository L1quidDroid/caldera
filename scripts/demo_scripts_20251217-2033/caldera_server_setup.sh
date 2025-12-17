#!/bin/bash
################################################################################
# CALDERA + ELK Stack Production Setup
# Run this on the CALDERA server VM
################################################################################

set -e

echo "🚀 Installing ELK Stack..."

# Add Elasticsearch repository
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
    sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# Install packages
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    elasticsearch \
    kibana \
    logstash \
    filebeat \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    jq

echo "✅ Packages installed"

# Configure Elasticsearch for external access
sudo sed -i 's/#network.host: 192.168.0.1/network.host: 0.0.0.0/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/#http.port: 9200/http.port: 9200/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/xpack.security.enabled: true/xpack.security.enabled: false/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/xpack.security.enrollment.enabled: true/xpack.security.enrollment.enabled: false/' /etc/elasticsearch/elasticsearch.yml

# Configure Kibana for external access
sudo sed -i 's/#server.port: 5601/server.port: 5601/' /etc/kibana/kibana.yml
sudo sed -i 's/#server.host: "localhost"/server.host: "0.0.0.0"/' /etc/kibana/kibana.yml
sudo sed -i 's/#elasticsearch.hosts:/elasticsearch.hosts:/' /etc/kibana/kibana.yml

echo "✅ ELK configured"

# Enable and start ELK services
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch kibana logstash
sudo systemctl start elasticsearch
sleep 10
sudo systemctl start kibana
sudo systemctl start logstash

echo "✅ ELK services started"

# Configure Filebeat for CALDERA log collection
echo "📦 Configuring Filebeat for CALDERA logs..."

mkdir -p ~/caldera/logs
sudo mkdir -p /var/log/caldera/agents

sudo tee /etc/filebeat/filebeat.yml > /dev/null << 'FBEOF'
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /home/*/caldera/logs/*.log
  fields:
    log_type: caldera_operation
    service: caldera
  fields_under_root: true

- type: journald
  enabled: true
  id: caldera-service
  include_matches:
    - _SYSTEMD_UNIT=caldera.service
  fields:
    log_type: caldera_service
  fields_under_root: true

- type: log
  enabled: true
  paths:
    - /home/*/elasticat.log
    - /home/*/sandcat.log
  fields:
    log_type: caldera_agent
  fields_under_root: true

- type: log
  enabled: true
  paths:
    - /var/log/auth.log
  fields:
    log_type: system_security
  fields_under_root: true

processors:
  - add_host_metadata: ~
  - add_fields:
      target: ''
      fields:
        environment: azure_demo
        deployment: purple_team_lab

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "caldera-logs-%{+yyyy.MM.dd}"

setup.ilm.enabled: false
setup.template.name: "caldera-logs"
setup.template.pattern: "caldera-logs-*"

logging.level: info
logging.to_files: true
FBEOF

sudo filebeat setup --index-management -E output.logstash.enabled=false -E 'output.elasticsearch.hosts=["localhost:9200"]' || true
sudo systemctl enable filebeat
sudo systemctl start filebeat

echo "✅ Filebeat configured and started"

# Install CALDERA
cd ~
git clone --recursive https://github.com/mitre/caldera.git
cd caldera
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install jsonschema

echo "✅ CALDERA installed"

# Enable branding and orchestrator plugins in local.yml
echo "📦 Configuring custom plugins (branding, orchestrator)..."

cat >> conf/local.yml << 'LOCALEOF'

# Custom Triskele Labs plugins
plugins:
- access
- atomic
- compass
- debrief
- fieldmanual
- manx
- response
- sandcat
- stockpile
- training
- branding
- orchestrator
LOCALEOF

echo "✅ Custom plugins configured in local.yml"

# Create systemd service for CALDERA
sudo tee /etc/systemd/system/caldera.service > /dev/null << EOF
[Unit]
Description=MITRE CALDERA
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/caldera
Environment="PATH=/home/$USER/caldera/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/$USER/caldera/venv/bin/python server.py --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable caldera
sudo systemctl start caldera

echo "✅ CALDERA service configured"

# Wait for CALDERA to start
echo "⏳ Waiting for CALDERA to start..."
for i in {1..30}; do
    if curl -s http://localhost:8888/api/v2/health > /dev/null 2>&1; then
        echo "✅ CALDERA is running"
        break
    fi
    sleep 2
done

PUBLIC_IP=$(curl -4 -s icanhazip.com)

echo ""
echo "================================================"
echo "🎉 CALDERA + ELK Stack + Filebeat Ready!"
echo "================================================"
echo "CALDERA:       http://$PUBLIC_IP:8888"
echo "  Credentials: admin / admin (red team)"
echo "               blue / admin (blue team)"
echo ""
echo "Kibana:        http://$PUBLIC_IP:5601"
echo "  Index:       caldera-logs-*"
echo "Elasticsearch: http://$PUBLIC_IP:9200"
echo ""
echo "Filebeat:      Collecting CALDERA logs → Elasticsearch"
echo "  Service:     sudo systemctl status filebeat"
echo "  Logs:        sudo journalctl -u filebeat -f"
echo ""
echo "API:           curl -u admin:admin http://$PUBLIC_IP:8888/api/v2/agents"
echo "================================================"
echo ""
echo "📊 View Logs in Kibana:"
echo "   1. Open Kibana: http://$PUBLIC_IP:5601"
echo "   2. Go to: Discover"
echo "   3. Create index pattern: caldera-logs-*"
echo "   4. Filter by log_type field:"
echo "      - caldera_operation (operation logs)"
echo "      - caldera_agent (agent activity)"
echo "      - system_security (auth logs)"
echo "================================================"
