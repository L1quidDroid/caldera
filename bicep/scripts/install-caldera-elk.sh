#!/bin/bash
set -euo pipefail

# ============================================================================
# CALDERA & ELK Server Setup Script
# ============================================================================
# This script installs both CALDERA and the ELK Stack on a single VM.
# ============================================================================

# Parameters
ADMIN_USERNAME=$1

# Setup logging
LOG_FILE=/var/log/caldera-elk-setup.log
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "[$(date)] Starting CALDERA & ELK setup..."

# --- Dependencies ---
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y python3-venv python3-pip python3-dev build-essential git curl gnupg apt-transport-https ca-certificates -qq

# --- Node.js for Caldera ---
echo "[$(date)] Installing Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs -qq

# --- Elastic Repository ---
echo "[$(date)] Adding Elastic repository..."
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list

# --- Install ELK and Caldera ---
echo "[$(date)] Installing Elasticsearch, Kibana, Logstash..."
apt-get update -qq
apt-get install -y elasticsearch kibana logstash -qq

# --- Caldera Installation ---
echo "[$(date)] Cloning CALDERA repository..."
cd "/home/$ADMIN_USERNAME"
if [ ! -d "caldera" ]; then
  git clone https://github.com/mitre/caldera.git --recursive --branch master
fi
cd caldera

echo "[$(date)] Creating Python virtual environment for Caldera..."
python3 -m venv caldera_venv
source caldera_venv/bin/activate
pip install --upgrade pip setuptools wheel --quiet
pip install -r requirements.txt --quiet
deactivate

echo "[$(date)] Building Magma frontend..."
cd plugins/magma
npm install --quiet
timeout 300 npm run build || { echo "Magma build failed"; exit 1; }
cd ../..

echo "[$(date)] Installing orchestrator plugin dependencies..."
cd orchestrator
source ../caldera_venv/bin/activate
pip install -r requirements.txt --quiet
deactivate
cd ..

echo "[$(date)] Configuring CALDERA..."
cat > conf/local.yml << "EOF"
host: 0.0.0.0
plugins:
  - access
  - atomic
  - branding
  - compass
  - fieldmanual
  - gameboard
  - magma
  - manx
  - orchestrator
  - response
  - sandcat
  - stockpile
  - training
users:
  red:
    red: admin
  blue:
    blue: admin
EOF

echo "[$(date)] Creating Caldera systemd service..."
cat > /etc/systemd/system/caldera.service << EOF
[Unit]
Description=CALDERA Adversary Emulation Platform
After=network.target elasticsearch.service
Wants=network-online.target

[Service]
Type=simple
User=$ADMIN_USERNAME
WorkingDirectory=/home/$ADMIN_USERNAME/caldera
ExecStart=/home/$ADMIN_USERNAME/caldera/caldera_venv/bin/python /home/$ADMIN_USERNAME/caldera/server.py --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

chown -R "$ADMIN_USERNAME:$ADMIN_USERNAME" "/home/$ADMIN_USERNAME/caldera"

# --- ELK Configuration ---
echo "[$(date)] Configuring Elasticsearch..."
cat >> /etc/elasticsearch/elasticsearch.yml << EOF
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
EOF

echo "[$(date)] Configuring Kibana..."
cat >> /etc/kibana/kibana.yml << EOF
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://localhost:9200"]
EOF

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

# --- Start Services ---
echo "[$(date)] Starting all services..."
systemctl daemon-reload
systemctl enable elasticsearch kibana logstash caldera
systemctl start elasticsearch
echo "[$(date)] Waiting for Elasticsearch to start..."
sleep 60
systemctl start kibana logstash caldera

# --- Health Checks ---
echo "[$(date)] Waiting for services to stabilize..."
sleep 60

echo "[$(date)] Running health checks..."
if curl -sf "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=50s"; then
    echo "[$(date)] ✅ Elasticsearch is healthy"
else
    echo "[$(date)] ❌ Elasticsearch health check failed"
    journalctl -u elasticsearch -n 50 --no-pager
    exit 1
fi

if curl -sf "http://localhost:5601/api/status"; then
    echo "[$(date)] ✅ Kibana is healthy"
else
    echo "[$(date)] ❌ Kibana health check failed"
    journalctl -u kibana -n 50 --no-pager
    exit 1
fi

if curl -sf http://localhost:8888 > /dev/null; then
  echo "[$(date)] ✅ CALDERA is healthy"
else
  echo "[$(date)] ❌ CALDERA health check failed"
  journalctl -u caldera -n 50 --no-pager
  exit 1
fi

echo "[$(date)] ✅ CALDERA & ELK setup complete"
