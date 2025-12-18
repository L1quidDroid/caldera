#!/bin/bash
################################################################################
# CALDERA Purple Team Lab - Configurable Deployment Template
# 
# Purpose: Reusable deployment for work/personal environments
# Usage: 
#   ./deploy_caldera_lab.sh --env personal
#   ./deploy_caldera_lab.sh --env work --location eastus
#   ./deploy_caldera_lab.sh --env production --secure
################################################################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() { echo -e "${CYAN}===== $1 =====${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

################################################################################
# CONFIGURATION PROFILES
################################################################################

# Default values
ENVIRONMENT="personal"
LOCATION="australiaeast"
SECURE_MODE=false
VM_SIZE_SERVER="Standard_B2s"
VM_SIZE_AGENT="Standard_B1s"
ADMIN_USER="tonyto"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --secure)
            SECURE_MODE=true
            shift
            ;;
        --server-size)
            VM_SIZE_SERVER="$2"
            shift 2
            ;;
        --agent-size)
            VM_SIZE_AGENT="$2"
            shift 2
            ;;
        --user)
            ADMIN_USER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --env ENV           Environment: personal|work|production (default: personal)"
            echo "  --location LOC      Azure region (default: australiaeast)"
            echo "  --secure            Enable production security hardening"
            echo "  --server-size SIZE  Server VM size (default: Standard_B2s)"
            echo "  --agent-size SIZE   Agent VM size (default: Standard_B1s)"
            echo "  --user USER         Admin username (default: tonyto)"
            echo "  --help              Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --env personal"
            echo "  $0 --env work --location eastus"
            echo "  $0 --env production --secure --server-size Standard_D2s_v3"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Run with --help for usage"
            exit 1
            ;;
    esac
done

# Environment-specific configuration
case $ENVIRONMENT in
    personal)
        RG_PREFIX="rg-caldera-personal"
        VNET="vnet-personal-lab"
        NSG="nsg-personal-lab"
        ADMIN_PASS="P@ssw0rd123!"
        ;;
    work)
        RG_PREFIX="rg-caldera-work"
        VNET="vnet-work-lab"
        NSG="nsg-work-lab"
        print_info "Work environment: Use secure password"
        read -sp "Enter admin password: " ADMIN_PASS
        echo
        ;;
    production)
        RG_PREFIX="rg-caldera-prod"
        VNET="vnet-prod-purple"
        NSG="nsg-prod-purple"
        SECURE_MODE=true
        print_info "Production environment: Use secure password"
        read -sp "Enter admin password: " ADMIN_PASS
        echo
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        echo "Valid options: personal, work, production"
        exit 1
        ;;
esac

RG="${RG_PREFIX}-$(date +%Y%m%d-%H%M)"
DEMO_DIR="lab_${ENVIRONMENT}_$(date +%Y%m%d-%H%M)"

################################################################################
# SUMMARY
################################################################################

print_header "Deployment Configuration"
echo ""
echo "Environment:    $ENVIRONMENT"
echo "Location:       $LOCATION"
echo "Resource Group: $RG"
echo "Server Size:    $VM_SIZE_SERVER"
echo "Agent Size:     $VM_SIZE_AGENT"
echo "Secure Mode:    $SECURE_MODE"
echo "Output Dir:     $DEMO_DIR"
echo ""

read -p "Continue with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled"
    exit 1
fi

################################################################################
# PRE-FLIGHT CHECKS
################################################################################

print_header "Pre-Flight Checks"

if ! command -v az &> /dev/null; then
    print_error "Azure CLI not found"
    exit 1
fi
print_success "Azure CLI installed"

if ! az account show &> /dev/null; then
    print_error "Not logged into Azure"
    exit 1
fi
SUBSCRIPTION=$(az account show --query name -o tsv)
print_success "Logged into Azure: $SUBSCRIPTION"

################################################################################
# DEPLOY INFRASTRUCTURE
################################################################################

print_header "Deploying Infrastructure"

# Create resource group
print_info "Creating resource group: $RG"
az group create --name "$RG" --location "$LOCATION" --output none
print_success "Resource group created"

# Create network
print_info "Creating virtual network"
az network vnet create \
    --resource-group "$RG" \
    --name "$VNET" \
    --address-prefix "10.0.0.0/16" \
    --subnet-name "subnet-lab" \
    --subnet-prefix "10.0.1.0/24" \
    --output none
print_success "Virtual network created"

# Create NSG
print_info "Creating NSG"
az network nsg create --resource-group "$RG" --name "$NSG" --output none
print_success "NSG created"

# NSG Rules
print_header "Configuring Security Rules"

az network nsg rule create --resource-group "$RG" --nsg-name "$NSG" \
    --name "AllowSSH" --priority 100 --protocol Tcp \
    --destination-port-ranges 22 --access Allow --output none
print_success "SSH rule added"

az network nsg rule create --resource-group "$RG" --nsg-name "$NSG" \
    --name "AllowRDP" --priority 110 --protocol Tcp \
    --destination-port-ranges 3389 --access Allow --output none
print_success "RDP rule added"

az network nsg rule create --resource-group "$RG" --nsg-name "$NSG" \
    --name "AllowCaldera" --priority 120 --protocol Tcp \
    --destination-port-ranges 8888 --access Allow --output none
print_success "CALDERA rule added"

az network nsg rule create --resource-group "$RG" --nsg-name "$NSG" \
    --name "AllowKibana" --priority 130 --protocol Tcp \
    --destination-port-ranges 5601 --access Allow --output none
print_success "Kibana rule added"

az network nsg rule create --resource-group "$RG" --nsg-name "$NSG" \
    --name "AllowElasticsearch" --priority 140 --protocol Tcp \
    --destination-port-ranges 9200 --access Allow --output none
print_success "Elasticsearch rule added"

az network nsg rule create --resource-group "$RG" --nsg-name "$NSG" \
    --name "AllowAgentC2" --priority 150 --protocol Tcp \
    --destination-port-ranges "7010-7012" --access Allow --output none
print_success "Agent C2 rules added"

az network vnet subnet update \
    --resource-group "$RG" \
    --vnet-name "$VNET" \
    --name "subnet-lab" \
    --network-security-group "$NSG" \
    --output none
print_success "NSG associated"

################################################################################
# DEPLOY VMs
################################################################################

print_header "Deploying Virtual Machines"

# CALDERA Server
print_info "Deploying CALDERA+ELK server - $VM_SIZE_SERVER"
az vm create \
    --resource-group "$RG" \
    --name "caldera-server" \
    --image "Ubuntu2204" \
    --size "$VM_SIZE_SERVER" \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name "$VNET" \
    --subnet "subnet-lab" \
    --nsg "$NSG" \
    --public-ip-sku Standard \
    --authentication-type password \
    --output none
print_success "CALDERA server deployed"

# Red Agent
print_info "Deploying Red agent (Windows) - $VM_SIZE_AGENT"
az vm create \
    --resource-group "$RG" \
    --name "red-agent" \
    --image "Win2022Datacenter" \
    --size "$VM_SIZE_AGENT" \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name "$VNET" \
    --subnet "subnet-lab" \
    --nsg "$NSG" \
    --public-ip-sku Standard \
    --authentication-type password \
    --output none
print_success "Red agent deployed"

# Blue Agent
print_info "Deploying Blue agent (Linux) - $VM_SIZE_AGENT"
az vm create \
    --resource-group "$RG" \
    --name "blue-agent" \
    --image "Ubuntu2204" \
    --size "$VM_SIZE_AGENT" \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name "$VNET" \
    --subnet "subnet-lab" \
    --nsg "$NSG" \
    --public-ip-sku Standard \
    --authentication-type password \
    --output none
print_success "Blue agent deployed"

################################################################################
# RETRIEVE IPs
################################################################################

print_header "Retrieving Network Information"

CALDERA_PUBLIC=$(az vm show -d -g "$RG" -n "caldera-server" --query publicIps -o tsv)
CALDERA_PRIVATE=$(az vm show -d -g "$RG" -n "caldera-server" --query privateIps -o tsv)
RED_PUBLIC=$(az vm show -d -g "$RG" -n "red-agent" --query publicIps -o tsv)
RED_PRIVATE=$(az vm show -d -g "$RG" -n "red-agent" --query privateIps -o tsv)
BLUE_PUBLIC=$(az vm show -d -g "$RG" -n "blue-agent" --query publicIps -o tsv)
BLUE_PRIVATE=$(az vm show -d -g "$RG" -n "blue-agent" --query privateIps -o tsv)

print_success "Network info retrieved"

################################################################################
# GENERATE SETUP SCRIPTS
################################################################################

print_header "Generating Setup Scripts"

mkdir -p "$DEMO_DIR"

# Generate server setup script
if [ "$SECURE_MODE" = true ]; then
    # Production mode - with SSL placeholders
    cat > "$DEMO_DIR/setup_server.sh" << 'EOFSERVER'
#!/bin/bash
# CALDERA+ELK Production Setup with Security
set -e

echo "🚀 Installing ELK Stack (Production Mode)..."

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
    sudo tee /etc/apt/sources.list.d/elastic-8.x.list

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    elasticsearch kibana logstash \
    git python3 python3-pip python3-venv curl jq \
    nginx certbot python3-certbot-nginx

echo "✅ Packages installed"

# Configure ELK with security enabled
sudo sed -i 's/#network.host: 192.168.0.1/network.host: localhost/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/#http.port: 9200/http.port: 9200/' /etc/elasticsearch/elasticsearch.yml

sudo sed -i 's/#server.port: 5601/server.port: 5601/' /etc/kibana/kibana.yml
sudo sed -i 's/#server.host: "localhost"/server.host: "localhost"/' /etc/kibana/kibana.yml

echo "✅ ELK configured (production mode - localhost only)"

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

# TODO: Configure SSL certificates
echo "⚠️  Production mode: Configure SSL certificates manually"
echo "    See: docs/How-to-Build-Plugins.md#ssl-certificates"

# Create systemd service
sudo tee /etc/systemd/system/caldera.service > /dev/null << EOF
[Unit]
Description=MITRE CALDERA
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/caldera
Environment="PATH=/home/$USER/caldera/venv/bin"
ExecStart=/home/$USER/caldera/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable caldera
sudo systemctl start caldera

echo "✅ CALDERA service configured"

PUBLIC_IP=$(curl -4 -s icanhazip.com)
echo ""
echo "🎉 CALDERA+ELK Ready (Production Mode)"
echo "CALDERA: http://$PUBLIC_IP:8888"
echo "⚠️  TODO: Configure SSL, change default passwords, enable ES security"
EOFSERVER
else
    # Demo/Dev mode - insecure but easy
    cat > "$DEMO_DIR/setup_server.sh" << 'EOFSERVER'
#!/bin/bash
# CALDERA+ELK Dev/Demo Setup
set -e

echo "🚀 Installing ELK Stack..."

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | \
    sudo tee /etc/apt/sources.list.d/elastic-8.x.list

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    elasticsearch kibana logstash \
    git python3 python3-pip python3-venv curl jq

echo "✅ Packages installed"

sudo sed -i 's/#network.host: 192.168.0.1/network.host: 0.0.0.0/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/#http.port: 9200/http.port: 9200/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/xpack.security.enabled: true/xpack.security.enabled: false/' /etc/elasticsearch/elasticsearch.yml
sudo sed -i 's/xpack.security.enrollment.enabled: true/xpack.security.enrollment.enabled: false/' /etc/elasticsearch/elasticsearch.yml

sudo sed -i 's/#server.port: 5601/server.port: 5601/' /etc/kibana/kibana.yml
sudo sed -i 's/#server.host: "localhost"/server.host: "0.0.0.0"/' /etc/kibana/kibana.yml
sudo sed -i 's/#elasticsearch.hosts:/elasticsearch.hosts:/' /etc/kibana/kibana.yml

echo "✅ ELK configured"

sudo systemctl daemon-reload
sudo systemctl enable elasticsearch kibana logstash
sudo systemctl start elasticsearch
sleep 10
sudo systemctl start kibana
sudo systemctl start logstash

echo "✅ ELK services started"

cd ~
git clone --recursive https://github.com/mitre/caldera.git
cd caldera
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ CALDERA installed"

sudo tee /etc/systemd/system/caldera.service > /dev/null << EOF
[Unit]
Description=MITRE CALDERA
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/caldera
Environment="PATH=/home/$USER/caldera/venv/bin"
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

for i in {1..30}; do
    if curl -s http://localhost:8888/api/v2/health > /dev/null 2>&1; then
        echo "✅ CALDERA is running"
        break
    fi
    sleep 2
done

PUBLIC_IP=$(curl -4 -s icanhazip.com)
echo ""
echo "🎉 CALDERA+ELK Ready!"
echo "CALDERA: http://$PUBLIC_IP:8888 (admin/admin)"
echo "Kibana: http://$PUBLIC_IP:5601"
echo "Elasticsearch: http://$PUBLIC_IP:9200"
EOFSERVER
fi

chmod +x "$DEMO_DIR/setup_server.sh"
print_success "Server setup script generated"

# Generate agent scripts
cat > "$DEMO_DIR/deploy_red_agent.ps1" << EOFWINDOWS
# Deploy Red Team Agent
\$SERVER = "$CALDERA_PUBLIC"
\$URL = "http://\$SERVER:8888"

Write-Host "🔴 Deploying Red Team Agent..." -ForegroundColor Red
\$wc = New-Object System.Net.WebClient
\$wc.Headers.Add("file", "sandcat.go")
\$wc.Headers.Add("platform", "windows")
\$data = \$wc.DownloadData("\$URL/file/download")
[IO.File]::WriteAllBytes("C:\Temp\sandcat.exe", \$data)
Start-Process "C:\Temp\sandcat.exe" -ArgumentList "-server \$URL -group red -v" -WindowStyle Hidden
Write-Host "✅ Red agent started" -ForegroundColor Green
EOFWINDOWS

cat > "$DEMO_DIR/deploy_blue_agent.sh" << EOFLINUX
#!/bin/bash
# Deploy Blue Team Agent
SERVER="$CALDERA_PUBLIC"
URL="http://\$SERVER:8888"

echo "🔵 Deploying Blue Team Agent..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv curl

python3 -m venv ~/agent-venv
source ~/agent-venv/bin/activate
pip install --quiet requests

curl -s -X POST -H "file:elasticat.py" -H "platform:linux" "\$URL/file/download" > elasticat.py
nohup python elasticat.py --server="\$URL" --es-host="http://\$SERVER:9200" --group=blue --minutes-since=60 > agent.log 2>&1 &

echo "✅ Blue agent started (PID: \$!)"
EOFLINUX

chmod +x "$DEMO_DIR/deploy_blue_agent.sh"
print_success "Agent scripts generated"

# Generate deployment info
cat > "$DEMO_DIR/deployment_info.txt" << EOFINFO
CALDERA Purple Team Lab - $ENVIRONMENT Environment
========================================
Date: $(date)
Resource Group: $RG
Location: $LOCATION
Secure Mode: $SECURE_MODE

CALDERA Server:
  Public IP:  $CALDERA_PUBLIC
  Private IP: $CALDERA_PRIVATE
  SSH: ssh $ADMIN_USER@$CALDERA_PUBLIC
  
Red Agent (Windows):
  Public IP:  $RED_PUBLIC
  Private IP: $RED_PRIVATE
  RDP: mstsc /v:$RED_PUBLIC
  
Blue Agent (Linux):
  Public IP:  $BLUE_PUBLIC
  Private IP: $BLUE_PRIVATE
  SSH: ssh $ADMIN_USER@$BLUE_PUBLIC

Credentials:
  Username: $ADMIN_USER
  Password: [REDACTED - stored securely]

URLs (after setup):
  CALDERA: http://$CALDERA_PUBLIC:8888
  Kibana: http://$CALDERA_PUBLIC:5601
  Elasticsearch: http://$CALDERA_PUBLIC:9200

Next Steps:
  1. ssh $ADMIN_USER@$CALDERA_PUBLIC
  2. bash setup_server.sh
  3. Deploy agents
  4. Access http://$CALDERA_PUBLIC:8888

Cleanup:
  az group delete --name $RG --yes --no-wait
EOFINFO

print_success "Deployment info saved"

# Generate cleanup script
cat > "$DEMO_DIR/cleanup.sh" << EOFCLEANUP
#!/bin/bash
echo "🧹 Cleaning up $ENVIRONMENT environment..."
az group delete --name $RG --yes --no-wait
echo "✅ Cleanup initiated"
EOFCLEANUP

chmod +x "$DEMO_DIR/cleanup.sh"

################################################################################
# SUMMARY
################################################################################

print_header "Deployment Complete!"

echo ""
echo "================================================"
echo "🎯 CALDERA LAB DEPLOYED - $ENVIRONMENT"
echo "================================================"
echo ""
echo "Resource Group: $RG"
echo "Location: $LOCATION"
echo ""
echo "CALDERA Server: $CALDERA_PUBLIC"
echo "Red Agent:      $RED_PUBLIC"
echo "Blue Agent:     $BLUE_PUBLIC"
echo ""
echo "All files saved to: $DEMO_DIR/"
echo ""
echo "Next Steps:"
echo "  1. Setup server:"
echo "     scp $DEMO_DIR/setup_server.sh $ADMIN_USER@$CALDERA_PUBLIC:~/"
echo "     ssh $ADMIN_USER@$CALDERA_PUBLIC 'bash setup_server.sh'"
echo ""
echo "  2. Or use Azure run-command:"
echo "     az vm run-command invoke -g $RG -n caldera-server \\"
echo "       --command-id RunShellScript --scripts @$DEMO_DIR/setup_server.sh --no-wait"
echo ""
echo "================================================"
echo ""

print_success "Deployment information: $DEMO_DIR/deployment_info.txt"

exit 0
