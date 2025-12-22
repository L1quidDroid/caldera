#!/bin/bash
set -euo pipefail

# ============================================================================
# CALDERA Server Setup Script (for Bicep CustomScriptExtension)
# ============================================================================
# This script is downloaded and executed on the CALDERA VM.
# It handles all software installation and configuration.
# ============================================================================

# Parameters passed from Bicep
ADMIN_USERNAME=$1

# Setup logging
LOG_FILE=/var/log/caldera-setup.log
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "[$(date)] Starting CALDERA setup..."

# Install dependencies
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y python3-venv python3-pip python3-dev build-essential git curl -qq

# Install Node.js 20.x (for Magma plugin build)
echo "[$(date)] Installing Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs -qq
node --version
npm --version

# Clone CALDERA repository
echo "[$(date)] Cloning CALDERA repository..."
cd "/home/$ADMIN_USERNAME"
if [ ! -d "caldera" ]; then
  git clone https://github.com/mitre/caldera.git --recursive --branch master
fi
cd caldera

# Create Python virtual environment
echo "[$(date)] Creating Python virtual environment..."
python3 -m venv caldera_venv
source caldera_venv/bin/activate
pip install --upgrade pip setuptools wheel --quiet
echo "[$(date)] Installing Python requirements..."
pip install -r requirements.txt --quiet
deactivate

# Build Magma frontend (CRITICAL - prevents FileNotFoundError)
echo "[$(date)] Building Magma frontend..."
cd plugins/magma
npm install --quiet
timeout 300 npm run build || { echo "Magma build failed"; exit 1; }
if [ -d "dist" ]; then
  echo "[$(date)] Magma dist/ created successfully ($(du -sh dist | cut -f1))"
else
  echo "ERROR: Magma dist/ not found after build"
  exit 1
fi
cd ../.. # Back to caldera root

# Install orchestrator plugin dependencies
echo "[$(date)] Installing orchestrator plugin dependencies..."
cd orchestrator
source ../caldera_venv/bin/activate
pip install -r requirements.txt --quiet
deactivate
cd .. # Back to caldera root

# Configure CALDERA
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

# Create systemd service
echo "[$(date)] Creating systemd service..."
cat > /etc/systemd/system/caldera.service << EOF
[Unit]
Description=CALDERA Adversary Emulation Platform
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$ADMIN_USERNAME
WorkingDirectory=/home/$ADMIN_USERNAME/caldera
ExecStart=/home/$ADMIN_USERNAME/caldera/caldera_venv/bin/python /home/$ADMIN_USERNAME/caldera/server.py --insecure
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R "$ADMIN_USERNAME:$ADMIN_USERNAME" "/home/$ADMIN_USERNAME/caldera"

# Enable and start service
echo "[$(date)] Starting CALDERA service..."
systemctl daemon-reload
systemctl enable caldera
systemctl start caldera

# Wait for startup
sleep 20

# Verify health
if curl -sf http://localhost:8888 > /dev/null; then
  echo "[$(date)] ✅ CALDERA setup complete - service healthy"
  systemctl status caldera --no-pager
else
  echo "[$(date)] ❌ CALDERA setup failed - service not responding"
  systemctl status caldera --no-pager
  journalctl -u caldera -n 50 --no-pager
  exit 1
fi

echo "[$(date)] CALDERA deployment completed successfully"
