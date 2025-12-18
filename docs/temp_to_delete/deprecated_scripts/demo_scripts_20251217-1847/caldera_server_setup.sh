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

# Install CALDERA
cd ~
git clone --recursive https://github.com/mitre/caldera.git
cd caldera
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ CALDERA installed"

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
echo "🎉 CALDERA + ELK Stack Ready!"
echo "================================================"
echo "CALDERA:       http://$PUBLIC_IP:8888"
echo "  Credentials: admin / admin (red team)"
echo "               blue / admin (blue team)"
echo ""
echo "Kibana:        http://$PUBLIC_IP:5601"
echo "Elasticsearch: http://$PUBLIC_IP:9200"
echo ""
echo "API:           curl -u admin:admin http://$PUBLIC_IP:8888/api/v2/agents"
echo "================================================"
