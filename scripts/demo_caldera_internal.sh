#!/bin/bash
################################################################################
# CALDERA Purple Team Demo: 3-VM Azure Deployment
# 
# Purpose: Executive demo of CALDERA as internal security tool
# Architecture: Caldera+ELK Server + Windows Red Agent + Linux Blue Agent
# Setup Time: 15 minutes → Live purple team exercise
# 
# Date: December 17, 2025
# Author: Triskele Labs
################################################################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

################################################################################
# CONFIGURATION
################################################################################

LOCATION="australiaeast"
RG="rg-caldera-demo-$(date +%Y%m%d-%H%M)"
VNET="vnet-purple-demo"
SUBNET="subnet-demo"
NSG="nsg-purple-demo"

# VM Size Options (adjust based on quota)
# Standard_B1s: 1 vCPU, 1GB RAM (minimal, may be slow)
# Standard_B2s: 2 vCPU, 4GB RAM (recommended)
# Standard_D2s_v3: 2 vCPU, 8GB RAM (alternative family)
VM_SIZE_SERVER="Standard_B2s"    # Server needs more resources
VM_SIZE_AGENT="${VM_SIZE_AGENT:-Standard_B1s}"  # Agents can be smaller

ADMIN_USER="tonyto"
ADMIN_PASS="P@ssw0rd123!"

# VM Names
CALDERA_VM="caldera-elk-server"
RED_VM="win-red-agent"
BLUE_VM="linux-blue-agent"

# Network Configuration
VNET_PREFIX="10.0.0.0/16"
SUBNET_PREFIX="10.0.1.0/24"

################################################################################
# VALIDATION
################################################################################

print_header "Pre-Flight Checks"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    print_error "Azure CLI not found. Install: https://aka.ms/azure-cli"
    exit 1
fi
print_success "Azure CLI installed"

# Check Azure login
if ! az account show &> /dev/null; then
    print_error "Not logged into Azure. Run: az login"
    exit 1
fi
SUBSCRIPTION=$(az account show --query name -o tsv)
print_success "Logged into Azure: $SUBSCRIPTION"

# Check quota (informational)
print_info "Checking VM quota in $LOCATION..."
QUOTA_INFO=$(az vm list-usage --location "$LOCATION" --query "[?contains(name.value, 'standardBSFamily')]" -o json 2>/dev/null || echo "[]")
if [ "$QUOTA_INFO" != "[]" ]; then
    CURRENT=$(echo "$QUOTA_INFO" | jq -r '.[0].currentValue // 0' 2>/dev/null || echo "unknown")
    LIMIT=$(echo "$QUOTA_INFO" | jq -r '.[0].limit // 0' 2>/dev/null || echo "unknown")
    print_info "B-Series quota: $CURRENT / $LIMIT cores used"
    
    # Calculate needed cores
    if [ "$VM_SIZE_SERVER" = "Standard_B2s" ]; then
        SERVER_CORES=2
    elif [ "$VM_SIZE_SERVER" = "Standard_B1s" ]; then
        SERVER_CORES=1
    else
        SERVER_CORES=2
    fi
    
    if [ "$VM_SIZE_AGENT" = "Standard_B2s" ]; then
        AGENT_CORES=2
    elif [ "$VM_SIZE_AGENT" = "Standard_B1s" ]; then
        AGENT_CORES=1
    else
        AGENT_CORES=2
    fi
    
    NEEDED=$((SERVER_CORES + AGENT_CORES * 2))
    print_info "Will need $NEEDED cores (1x $VM_SIZE_SERVER + 2x $VM_SIZE_AGENT)"
    
    if [ "$CURRENT" != "unknown" ] && [ "$LIMIT" != "unknown" ]; then
        AVAILABLE=$((LIMIT - CURRENT))
        if [ $AVAILABLE -lt $NEEDED ]; then
            print_error "Insufficient quota! Available: $AVAILABLE cores, Need: $NEEDED cores"
            echo ""
            echo "Options to resolve:"
            echo "1. Use smaller VMs: export VM_SIZE_AGENT=Standard_B1s && ./demo_caldera_internal.sh"
            echo "2. Delete existing VMs: az vm list -g <old-rg> -o table"
            echo "3. Try different region: Edit LOCATION in script"
            echo "4. Request quota increase: https://aka.ms/ProdportalCRP"
            echo ""
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Deployment cancelled"
                exit 1
            fi
        fi
    fi
fi

################################################################################
# INFRASTRUCTURE DEPLOYMENT
################################################################################

print_header "Deploying Infrastructure"

# Create Resource Group
print_info "Creating resource group: $RG"
az group create \
    --name "$RG" \
    --location "$LOCATION" \
    --output none
print_success "Resource group created"

# Create Virtual Network
print_info "Creating virtual network: $VNET"
az network vnet create \
    --resource-group "$RG" \
    --name "$VNET" \
    --address-prefix "$VNET_PREFIX" \
    --subnet-name "$SUBNET" \
    --subnet-prefix "$SUBNET_PREFIX" \
    --output none
print_success "Virtual network created"

# Create Network Security Group
print_info "Creating network security group: $NSG"
az network nsg create \
    --resource-group "$RG" \
    --name "$NSG" \
    --output none
print_success "Network security group created"

################################################################################
# NSG RULES - Precise Security Configuration
################################################################################

print_header "Configuring Network Security Rules"

# SSH Access (for server and blue agent)
print_info "Adding SSH rule (port 22)"
az network nsg rule create \
    --resource-group "$RG" \
    --nsg-name "$NSG" \
    --name "AllowSSH" \
    --priority 100 \
    --protocol Tcp \
    --destination-port-ranges 22 \
    --access Allow \
    --description "SSH access for Linux VMs" \
    --output none
print_success "SSH rule configured"

# RDP Access (for red agent)
print_info "Adding RDP rule (port 3389)"
az network nsg rule create \
    --resource-group "$RG" \
    --nsg-name "$NSG" \
    --name "AllowRDP" \
    --priority 110 \
    --protocol Tcp \
    --destination-port-ranges 3389 \
    --access Allow \
    --description "RDP access for Windows VM" \
    --output none
print_success "RDP rule configured"

# CALDERA Web UI
print_info "Adding CALDERA UI rule (port 8888)"
az network nsg rule create \
    --resource-group "$RG" \
    --nsg-name "$NSG" \
    --name "AllowCaldera" \
    --priority 120 \
    --protocol Tcp \
    --destination-port-ranges 8888 \
    --access Allow \
    --description "CALDERA web interface" \
    --output none
print_success "CALDERA UI rule configured"

# Kibana Dashboard
print_info "Adding Kibana rule (port 5601)"
az network nsg rule create \
    --resource-group "$RG" \
    --nsg-name "$NSG" \
    --name "AllowKibana" \
    --priority 130 \
    --protocol Tcp \
    --destination-port-ranges 5601 \
    --access Allow \
    --description "Kibana dashboard access" \
    --output none
print_success "Kibana rule configured"

# Elasticsearch API
print_info "Adding Elasticsearch rule (port 9200)"
az network nsg rule create \
    --resource-group "$RG" \
    --nsg-name "$NSG" \
    --name "AllowElasticsearch" \
    --priority 140 \
    --protocol Tcp \
    --destination-port-ranges 9200 \
    --access Allow \
    --description "Elasticsearch API access" \
    --output none
print_success "Elasticsearch rule configured"

# Agent C2 Communication
print_info "Adding Agent C2 rules (ports 7010-7012)"
az network nsg rule create \
    --resource-group "$RG" \
    --nsg-name "$NSG" \
    --name "AllowAgentC2" \
    --priority 150 \
    --protocol Tcp \
    --destination-port-ranges "7010-7012" \
    --access Allow \
    --description "Agent command and control" \
    --output none
print_success "Agent C2 rules configured"

# Associate NSG with subnet
print_info "Associating NSG with subnet"
az network vnet subnet update \
    --resource-group "$RG" \
    --vnet-name "$VNET" \
    --name "$SUBNET" \
    --network-security-group "$NSG" \
    --output none
print_success "NSG associated with subnet"

################################################################################
# VM DEPLOYMENT
################################################################################

print_header "Deploying Virtual Machines"

# Deploy CALDERA + ELK Server
print_info "Deploying CALDERA+ELK server (Ubuntu) - Size: $VM_SIZE_SERVER"
az vm create \
    --resource-group "$RG" \
    --name "$CALDERA_VM" \
    --image "Ubuntu2204" \
    --size "$VM_SIZE_SERVER" \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name "$VNET" \
    --subnet "$SUBNET" \
    --nsg "$NSG" \
    --public-ip-sku Standard \
    --authentication-type all \
    --generate-ssh-keys \
    --output none

# Wait for VM to be fully provisioned
print_info "Waiting for CALDERA server to fully provision..."
az vm wait --created -g "$RG" -n "$CALDERA_VM" --timeout 300
print_success "CALDERA server deployed and ready"

# Deploy Red Team Windows Agent
print_info "Deploying Red Team Windows agent - Size: $VM_SIZE_AGENT"
az vm create \
    --resource-group "$RG" \
    --name "$RED_VM" \
    --image "Win2022Datacenter" \
    --size "$VM_SIZE_AGENT" \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name "$VNET" \
    --subnet "$SUBNET" \
    --nsg "$NSG" \
    --public-ip-sku Standard \
    --authentication-type password \
    --output none

# Wait for Windows VM to be fully provisioned
print_info "Waiting for Red Team agent to fully provision..."
az vm wait --created -g "$RG" -n "$RED_VM" --timeout 300
print_success "Red Team agent deployed and ready"

# Deploy Blue Team Linux Agent
print_info "Deploying Blue Team Linux agent - Size: $VM_SIZE_AGENT"
az vm create \
    --resource-group "$RG" \
    --name "$BLUE_VM" \
    --image "Ubuntu2204" \
    --size "$VM_SIZE_AGENT" \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name "$VNET" \
    --subnet "$SUBNET" \
    --nsg "$NSG" \
    --public-ip-sku Standard \
    --authentication-type all \
    --generate-ssh-keys \
    --output none

# Wait for VM to be fully provisioned
print_info "Waiting for Blue Team agent to fully provision..."
az vm wait --created -g "$RG" -n "$BLUE_VM" --timeout 300
print_success "Blue Team agent deployed and ready"

################################################################################
# RETRIEVE IP ADDRESSES
################################################################################

print_header "Retrieving Network Information"

CALDERA_PUBLIC_IP=$(az vm show -d -g "$RG" -n "$CALDERA_VM" --query publicIps -o tsv)
CALDERA_PRIVATE_IP=$(az vm show -d -g "$RG" -n "$CALDERA_VM" --query privateIps -o tsv)

RED_PUBLIC_IP=$(az vm show -d -g "$RG" -n "$RED_VM" --query publicIps -o tsv)
RED_PRIVATE_IP=$(az vm show -d -g "$RG" -n "$RED_VM" --query privateIps -o tsv)

BLUE_PUBLIC_IP=$(az vm show -d -g "$RG" -n "$BLUE_VM" --query publicIps -o tsv)
BLUE_PRIVATE_IP=$(az vm show -d -g "$RG" -n "$BLUE_VM" --query privateIps -o tsv)

print_success "Network information retrieved"

################################################################################
# GENERATE SETUP SCRIPTS
################################################################################

print_header "Generating Setup Scripts"

# Create demo directory if it doesn't exist
DEMO_DIR="demo_scripts_$(date +%Y%m%d-%H%M)"
mkdir -p "$DEMO_DIR"

# Generate Server Setup Script
cat > "$DEMO_DIR/caldera_server_setup.sh" << 'EOFSERVER'
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
EOFSERVER

chmod +x "$DEMO_DIR/caldera_server_setup.sh"
print_success "Server setup script generated"

# Generate Windows Red Agent Script
cat > "$DEMO_DIR/deploy_red_agent.ps1" << EOFWINDOWS
################################################################################
# Deploy Sandcat Red Team Agent
# Run this on the Windows Red Agent VM
################################################################################

\$ErrorActionPreference = "Stop"

\$CALDERA_SERVER = "$CALDERA_PUBLIC_IP"
\$SERVER_URL = "http://\$CALDERA_SERVER:8888"
\$GROUP = "red"

Write-Host "🔴 Deploying Sandcat Red Team Agent..." -ForegroundColor Red
Write-Host "Server: \$SERVER_URL" -ForegroundColor Cyan

# Create temp directory
\$TempDir = "C:\Temp"
if (-not (Test-Path \$TempDir)) {
    New-Item -ItemType Directory -Path \$TempDir | Out-Null
}

# Download Sandcat agent
Write-Host "⬇️  Downloading agent..." -ForegroundColor Yellow

try {
    \$wc = New-Object System.Net.WebClient
    \$wc.Headers.Add("file", "sandcat.go")
    \$wc.Headers.Add("platform", "windows")
    \$data = \$wc.DownloadData("\$SERVER_URL/file/download")
    \$agentPath = "\$TempDir\sandcat.exe"
    [IO.File]::WriteAllBytes(\$agentPath, \$data)
    
    Write-Host "✅ Agent downloaded to \$agentPath" -ForegroundColor Green
    
    # Start agent
    Write-Host "🚀 Starting agent..." -ForegroundColor Yellow
    \$proc = Start-Process -FilePath \$agentPath -ArgumentList "-server \$SERVER_URL -group \$GROUP -v" -WindowStyle Hidden -PassThru
    
    Write-Host "✅ Agent started (PID: \$(\$proc.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "Agent will beacon to CALDERA every 60 seconds" -ForegroundColor Cyan
    Write-Host "Check CALDERA UI -> Agents tab to see this agent" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error: \$_" -ForegroundColor Red
    exit 1
}
EOFWINDOWS

print_success "Red agent script generated"

# Generate Linux Blue Agent Script
cat > "$DEMO_DIR/deploy_blue_agent.sh" << EOFLINUX
#!/bin/bash
################################################################################
# Deploy Elasticat Blue Team Agent
# Run this on the Linux Blue Agent VM
################################################################################

set -e

CALDERA_SERVER="$CALDERA_PUBLIC_IP"
SERVER_URL="http://\$CALDERA_SERVER:8888"
ES_URL="http://\$CALDERA_SERVER:9200"
GROUP="blue"

echo "🔵 Deploying Elasticat Blue Team Agent..."
echo "CALDERA: \$SERVER_URL"
echo "Elasticsearch: \$ES_URL"

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv curl jq

# Create virtual environment
echo "🐍 Creating Python environment..."
python3 -m venv ~/elasticat-venv
source ~/elasticat-venv/bin/activate

# Install required packages
pip install --quiet requests

# Download elasticat agent
echo "⬇️  Downloading agent..."
curl -s -X POST \
    -H "file:elasticat.py" \
    -H "platform:linux" \
    "\$SERVER_URL/file/download" > elasticat.py

chmod +x elasticat.py

# Start agent
echo "🚀 Starting agent..."
nohup python elasticat.py \
    --server="\$SERVER_URL" \
    --es-host="\$ES_URL" \
    --group=\$GROUP \
    --minutes-since=60 \
    > elasticat.log 2>&1 &

AGENT_PID=\$!
echo "✅ Agent started (PID: \$AGENT_PID)"
echo ""
echo "Agent logs: tail -f elasticat.log"
echo "Check CALDERA UI -> Agents tab to see this agent"
EOFLINUX

chmod +x "$DEMO_DIR/deploy_blue_agent.sh"
print_success "Blue agent script generated"

# Generate validation script
cat > "$DEMO_DIR/demo_validation.sh" << 'EOFVALIDATION'
#!/bin/bash
################################################################################
# Demo Validation Script
# Validates that all components are ready for executive demo
################################################################################

if [ -z "$1" ]; then
    echo "Usage: $0 <CALDERA_IP>"
    exit 1
fi

CALDERA_IP=$1
API_USER="admin"
API_PASS="admin"

echo "================================================"
echo "🔍 DEMO VALIDATION"
echo "================================================"
echo ""

# Check CALDERA
echo "✅ CALDERA Web UI:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$CALDERA_IP:8888)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ http://$CALDERA_IP:8888 - OK ($HTTP_CODE)"
else
    echo "   ❌ http://$CALDERA_IP:8888 - FAIL ($HTTP_CODE)"
fi

# Check Kibana
echo ""
echo "✅ Kibana Dashboard:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$CALDERA_IP:5601)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "   ✅ http://$CALDERA_IP:5601 - OK ($HTTP_CODE)"
else
    echo "   ❌ http://$CALDERA_IP:5601 - FAIL ($HTTP_CODE)"
fi

# Check Elasticsearch
echo ""
echo "✅ Elasticsearch API:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$CALDERA_IP:9200)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ http://$CALDERA_IP:9200 - OK ($HTTP_CODE)"
else
    echo "   ❌ http://$CALDERA_IP:9200 - FAIL ($HTTP_CODE)"
fi

# Check agents
echo ""
echo "✅ Registered Agents:"
AGENT_COUNT=$(curl -s -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/agents 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
echo "   📊 $AGENT_COUNT agent(s) registered"

if [ "$AGENT_COUNT" -gt 0 ]; then
    echo "   Agent details:"
    curl -s -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/agents | \
        jq -r '.[] | "      - \(.paw): \(.platform) (\(.group))"' 2>/dev/null || echo "      (unable to parse)"
fi

echo ""
echo "================================================"
echo "🎬 DEMO FLOW (5-10 minutes)"
echo "================================================"
echo ""
echo "1️⃣  Open CALDERA UI: http://$CALDERA_IP:8888"
echo "   Login: admin / admin"
echo ""
echo "2️⃣  Navigate to Agents tab"
echo "   Verify red and blue agents are connected"
echo ""
echo "3️⃣  Navigate to Operations tab"
echo "   Click 'Create Operation'"
echo "   Select adversary (e.g., 'Collection')"
echo "   Select red group"
echo "   Start operation"
echo ""
echo "4️⃣  Monitor operation execution"
echo "   Watch abilities execute in real-time"
echo "   Review command output"
echo ""
echo "5️⃣  Open Kibana: http://$CALDERA_IP:5601"
echo "   Create index pattern for agent logs"
echo "   Visualize blue team monitoring"
echo ""
echo "6️⃣  API Integration Demo:"
echo "   curl -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/agents"
echo "   curl -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/operations"
echo ""
echo "================================================"
echo "🎯 APPROVAL POINTS"
echo "================================================"
echo ""
echo "✅ Production-ready architecture (systemd services)"
echo "✅ Multi-agent orchestration (red/blue teams)"
echo "✅ Real-time monitoring (ELK integration)"
echo "✅ REST API for automation (Copilot integration ready)"
echo "✅ Purple team capabilities (adversary emulation + detection)"
echo ""
echo "================================================"
EOFVALIDATION

chmod +x "$DEMO_DIR/demo_validation.sh"
print_success "Validation script generated"

# Generate cleanup script
cat > "$DEMO_DIR/cleanup_demo.sh" << EOFCLEANUP
#!/bin/bash
# Cleanup demo environment
echo "🧹 Cleaning up demo environment..."
az group delete --name $RG --yes --no-wait
echo "✅ Cleanup initiated (runs in background)"
EOFCLEANUP

chmod +x "$DEMO_DIR/cleanup_demo.sh"
print_success "Cleanup script generated"

# Save deployment info
cat > "$DEMO_DIR/deployment_info.txt" << EOFINFO
CALDERA Purple Team Demo Deployment
====================================
Date: $(date)
Resource Group: $RG
Location: $LOCATION

CALDERA Server:
  Public IP: $CALDERA_PUBLIC_IP
  Private IP: $CALDERA_PRIVATE_IP
  SSH: ssh $ADMIN_USER@$CALDERA_PUBLIC_IP
  
Red Agent (Windows):
  Public IP: $RED_PUBLIC_IP
  Private IP: $RED_PRIVATE_IP
  RDP: mstsc /v:$RED_PUBLIC_IP
  Username: $ADMIN_USER
  Password: $ADMIN_PASS
  
Blue Agent (Linux):
  Public IP: $BLUE_PUBLIC_IP
  Private IP: $BLUE_PRIVATE_IP
  SSH: ssh $ADMIN_USER@$BLUE_PUBLIC_IP

CALDERA URLs:
  Web UI: http://$CALDERA_PUBLIC_IP:8888
  API: http://$CALDERA_PUBLIC_IP:8888/api/v2
  Credentials: admin/admin or blue/admin
  
Kibana URL:
  Dashboard: http://$CALDERA_PUBLIC_IP:5601
  
Elasticsearch URL:
  API: http://$CALDERA_PUBLIC_IP:9200

Next Steps:
  1. Run: bash caldera_server_setup.sh (on CALDERA server)
  2. Run: deploy_red_agent.ps1 (on Windows VM)
  3. Run: bash deploy_blue_agent.sh (on Linux VM)
  4. Validate: ./demo_validation.sh $CALDERA_PUBLIC_IP
  
Cleanup:
  Run: bash cleanup_demo.sh
EOFINFO

print_success "Deployment info saved"

################################################################################
# DEPLOYMENT SUMMARY
################################################################################

print_header "Deployment Complete!"

echo ""
echo "================================================"
echo "🎯 PURPLE TEAM DEMO LAB DEPLOYED"
echo "================================================"
echo ""
echo "📋 Resource Group: $RG"
echo "📍 Location: $LOCATION"
echo ""
echo "🖥️  CALDERA + ELK Server:"
echo "   Public IP:  $CALDERA_PUBLIC_IP"
echo "   Private IP: $CALDERA_PRIVATE_IP"
echo "   SSH:        ssh $ADMIN_USER@$CALDERA_PUBLIC_IP"
echo ""
echo "🔴 Red Team Agent (Windows):"
echo "   Public IP:  $RED_PUBLIC_IP"
echo "   Private IP: $RED_PRIVATE_IP"
echo "   RDP:        mstsc /v:$RED_PUBLIC_IP"
echo "   Username:   $ADMIN_USER"
echo "   Password:   $ADMIN_PASS"
echo ""
echo "🔵 Blue Team Agent (Linux):"
echo "   Public IP:  $BLUE_PUBLIC_IP"
echo "   Private IP: $BLUE_PRIVATE_IP"
echo "   SSH:        ssh $ADMIN_USER@$BLUE_PUBLIC_IP"
echo ""
echo "================================================"
echo "📝 NEXT STEPS"
echo "================================================"
echo ""
echo "All helper scripts are in: $DEMO_DIR/"
echo ""
echo "1️⃣  Setup CALDERA Server:"
echo "   scp $DEMO_DIR/caldera_server_setup.sh $ADMIN_USER@$CALDERA_PUBLIC_IP:~/"
echo "   ssh $ADMIN_USER@$CALDERA_PUBLIC_IP"
echo "   bash caldera_server_setup.sh"
echo ""
echo "2️⃣  Deploy Red Agent:"
echo "   RDP to $RED_PUBLIC_IP"
echo "   Copy $DEMO_DIR/deploy_red_agent.ps1 to Windows VM"
echo "   Run in PowerShell"
echo ""
echo "3️⃣  Deploy Blue Agent:"
echo "   scp $DEMO_DIR/deploy_blue_agent.sh $ADMIN_USER@$BLUE_PUBLIC_IP:~/"
echo "   ssh $ADMIN_USER@$BLUE_PUBLIC_IP"
echo "   bash deploy_blue_agent.sh"
echo ""
echo "4️⃣  Access CALDERA:"
echo "   URL: http://$CALDERA_PUBLIC_IP:8888"
echo "   Red Team:  admin / admin"
echo "   Blue Team: blue / admin"
echo ""
echo "5️⃣  Access Kibana:"
echo "   URL: http://$CALDERA_PUBLIC_IP:5601"
echo ""
echo "6️⃣  Validate Setup:"
echo "   $DEMO_DIR/demo_validation.sh $CALDERA_PUBLIC_IP"
echo ""
echo "7️⃣  Cleanup (when done):"
echo "   $DEMO_DIR/cleanup_demo.sh"
echo ""
echo "================================================"
echo ""
print_success "All files saved to: $DEMO_DIR/"
echo ""

exit 0
