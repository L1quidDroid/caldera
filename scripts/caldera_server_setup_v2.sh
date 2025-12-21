#!/bin/bash
# CALDERA + ELK Stack Setup Script v2
# Includes pre-built Magma frontend upload
# Usage: ./caldera_server_setup_v2.sh

set -euo pipefail

# Configuration
LOG_FILE=~/setup_output.log
CALDERA_DIR=~/caldera
MAGMA_DIST_ARCHIVE=~/magma-dist.tar.gz

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root. It will use sudo when needed."
    exit 1
fi

log "Starting CALDERA + ELK Stack setup v2"
log "Log file: $LOG_FILE"

# Phase 1: Install ELK Stack
log "Phase 1: Installing ELK Stack 8.x"
sudo apt-get update -qq
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg -qq

# Add Elastic GPG key (non-interactive)
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | \
    sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg

# Add Elastic repository
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
    sudo tee /etc/apt/sources.list.d/elastic-8.x.list > /dev/null

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y elasticsearch kibana logstash -qq
log "ELK Stack installed successfully"

# Phase 2: Configure ELK
log "Phase 2: Configuring ELK Stack"

# Configure Elasticsearch
sudo tee -a /etc/elasticsearch/elasticsearch.yml > /dev/null << 'EOF'
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
EOF

# Configure Kibana
sudo tee -a /etc/kibana/kibana.yml > /dev/null << 'EOF'
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://localhost:9200"]
EOF

# Configure Logstash
sudo tee /etc/logstash/conf.d/caldera.conf > /dev/null << 'EOF'
input {
  beats {
    port => 5044
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "caldera-%{+YYYY.MM.dd}"
  }
}
EOF

log "ELK Stack configured"

# Phase 3: Start ELK Services
log "Phase 3: Starting ELK services"
sudo systemctl enable elasticsearch kibana logstash
sudo systemctl start elasticsearch

# Wait for Elasticsearch
log "Waiting for Elasticsearch to start..."
for i in {1..30}; do
    if curl -s http://localhost:9200 >/dev/null 2>&1; then
        log "Elasticsearch is up"
        break
    fi
    sleep 2
done

sudo systemctl start kibana
sudo systemctl start logstash
log "ELK services started"

# Phase 4: Install CALDERA
log "Phase 4: Installing CALDERA"

if [ -d "$CALDERA_DIR" ]; then
    warn "CALDERA directory exists, removing..."
    rm -rf "$CALDERA_DIR"
fi

git clone https://github.com/mitre/caldera.git --recursive --branch master "$CALDERA_DIR"
cd "$CALDERA_DIR"

# Create virtual environment
python3 -m venv caldera_venv
source caldera_venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel --quiet

# Install requirements
log "Installing Python requirements (this may take a few minutes)..."
pip install -r requirements.txt --quiet 2>&1 | tee -a "$LOG_FILE"

deactivate
log "CALDERA installed successfully"

# Phase 5: Extract pre-built Magma frontend
log "Phase 5: Extracting pre-built Magma frontend"
if [ -f "$MAGMA_DIST_ARCHIVE" ]; then
    cd "$CALDERA_DIR/plugins/magma"
    tar xzf "$MAGMA_DIST_ARCHIVE"
    if [ -d "dist" ]; then
        log "Magma dist/ extracted successfully"
        log "Dist contents: $(ls -la dist/ | wc -l) files"
    else
        error "Failed to extract Magma dist/"
        exit 1
    fi
else
    warn "Magma dist archive not found at $MAGMA_DIST_ARCHIVE"
    warn "You will need to build Magma or upload dist/ manually"
fi

# Phase 6: Configure CALDERA
log "Phase 6: Configuring CALDERA"
cd "$CALDERA_DIR"

cat > conf/local.yml << 'EOF'
host: 0.0.0.0
plugins:
  - access
  - atomic
  - compass
  - fieldmanual
  - gameboard
  - magma
  - manx
  - response
  - sandcat
  - stockpile
  - training
EOF

log "CALDERA configured"

# Phase 7: Create systemd service
log "Phase 7: Creating systemd service"
sudo tee /etc/systemd/system/caldera.service > /dev/null << EOF
[Unit]
Description=CALDERA Adversary Emulation Platform
After=network.target elasticsearch.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$CALDERA_DIR
ExecStart=$CALDERA_DIR/caldera_venv/bin/python $CALDERA_DIR/server.py --insecure
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable caldera
log "Systemd service created"

# Phase 8: Start CALDERA
log "Phase 8: Starting CALDERA"
sudo systemctl start caldera

# Wait for CALDERA
log "Waiting for CALDERA to start..."
sleep 15

if systemctl is-active --quiet caldera; then
    log "CALDERA service is active"
    
    # Test web interface
    if curl -s http://localhost:8888 | grep -q "html"; then
        log "CALDERA web interface is responding"
    else
        warn "CALDERA service active but web interface not responding yet"
    fi
else
    error "CALDERA service failed to start"
    sudo journalctl -u caldera -n 50 --no-pager
    exit 1
fi

# Phase 9: Final verification
log "Phase 9: Verifying installation"
echo ""
echo "=== Service Status ==="
systemctl is-active elasticsearch && echo "✅ Elasticsearch: ACTIVE" || echo "❌ Elasticsearch: INACTIVE"
systemctl is-active kibana && echo "✅ Kibana: ACTIVE" || echo "❌ Kibana: INACTIVE"
systemctl is-active logstash && echo "✅ Logstash: ACTIVE" || echo "❌ Logstash: INACTIVE"
systemctl is-active caldera && echo "✅ CALDERA: ACTIVE" || echo "❌ CALDERA: INACTIVE"

echo ""
echo "=== Port Status ==="
sudo ss -tlnp | grep -E ':(8888|9200|5601|5044)' && echo "✅ Services listening on expected ports" || warn "Some ports may not be listening"

echo ""
log "🎉 Setup complete!"
log "CALDERA URL: http://$(hostname -I | awk '{print $1}'):8888"
log "Default credentials: admin / admin"
log "Kibana URL: http://$(hostname -I | awk '{print $1}'):5601"
log "Elasticsearch URL: http://$(hostname -I | awk '{print $1}'):9200"
