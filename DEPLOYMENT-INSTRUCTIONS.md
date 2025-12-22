# CALDERA Purple Team Lab - Deployment Instructions

## Overview
This repository contains Infrastructure as Code (Bicep) to deploy a complete purple team environment in Azure with CALDERA, ELK Stack, and target agents.

## Architecture
- **CALDERA Server** (Ubuntu 22.04) - Adversary emulation platform
- **ELK Server** (Ubuntu 22.04) - Elasticsearch + Kibana + Logstash
- **Windows Agent** (Server 2022) - Red team target
- **Linux Agent** (Ubuntu 22.04) - Blue team monitoring

## Prerequisites
- Azure CLI installed: `brew install azure-cli`
- Active Azure subscription
- SSH key: `ssh-keygen -t rsa -b 4096`
- Git access to this repository

## Deployment Options

### Option 1: GitHub Actions (Recommended)
1. Configure GitHub secrets:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

2. Push to master branch or run workflow manually

3. GitHub Actions will:
   - Validate Bicep templates
   - Run security scans (Checkov)
   - Deploy infrastructure
   - Run health checks

### Option 2: Local Deployment (Current Status: Bicep needs fixes)
```bash
# Clone repository
git clone <repo-url>
cd caldera

# Login to Azure
az login

# Run deployment script
./deploy.sh
```

**Note:** Bicep files currently have escape sequence errors in embedded bash scripts that need to be fixed before local deployment works.

### Option 3: Manual Azure CLI
```bash
# After fixing Bicep syntax errors:
az deployment sub create \
  --name "caldera-$(date +%Y%m%d-%H%M)" \
  --template-file bicep/main.bicep \
  --parameters bicep/parameters/dev.parameters.json \
  --parameters adminUsername="youruser" \
  --parameters adminPassword="YourP@ss123!" \
  --parameters sshPublicKey="$(cat ~/.ssh/id_rsa.pub)" \
  --location australiaeast
```

## Post-Deployment Configuration

### Add Orchestrator Plugin to CALDERA
```bash
# SSH into CALDERA server
ssh tonyto@<caldera-ip>

# Navigate to caldera directory
cd /home/tonyto/caldera

# Install orchestrator dependencies
cd orchestrator
source ../caldera_venv/bin/activate
pip install -r requirements.txt
deactivate

# Update conf/local.yml to include:
# plugins:
#   - orchestrator
#   - branding

# Restart CALDERA
sudo systemctl restart caldera
```

### Install Winlogbeat on Windows Agent
```powershell
# RDP to Windows agent
mstsc /v:<windows-ip>

# Download Winlogbeat
$winlogbeatUrl = 'https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-8.11.0-windows-x86_64.zip'
Invoke-WebRequest -Uri $winlogbeatUrl -OutFile "$env:TEMP\winlogbeat.zip"

# Extract
Expand-Archive -Path "$env:TEMP\winlogbeat.zip" -DestinationPath "C:\Program Files\Winlogbeat"

# Configure winlogbeat.yml
$config = @"
winlogbeat.event_logs:
  - name: Application
  - name: Security  
  - name: System

output.logstash:
  hosts: ["<elk-private-ip>:5044"]

logging.level: info
"@

Set-Content -Path "C:\Program Files\Winlogbeat\winlogbeat.yml" -Value $config

# Install service
& "C:\Program Files\Winlogbeat\install-service-winlogbeat.ps1"
Start-Service winlogbeat
```

## Success Criteria Validation

### ✅ Infrastructure Present
```bash
az resource list --resource-group <rg-name> --output table
```

### ✅ ELK Stack Running
```bash
# Check Elasticsearch
curl http://<elk-ip>:9200/_cluster/health

# Access Kibana
open http://<elk-ip>:5601
```

### ✅ CALDERA with Plugins
```bash
# Access CALDERA
open http://<caldera-ip>:8888
# Login: admin / admin
# Verify plugins: orchestrator, branding visible in UI
```

### ✅ Winlogbeat on Windows
```powershell
# On Windows agent
Get-Service winlogbeat
Get-Content "C:\ProgramData\winlogbeat\Logs\winlogbeat"
```

### ✅ GitHub Actions Build
- Push to master
- Check Actions tab
- Verify deployment workflow succeeds

## Known Issues

**Bicep Escape Sequences:** The embedded bash scripts in Bicep CustomScriptExtension have escape sequence syntax errors. These occur because:
- Bicep requires specific escape sequences: `\$`, `\'`, `\\`, `\n`, `\r`, `\t`, `\u{...}`
- Bash scripts use `\d`, `\{`, `\}`, `\[`, etc. which Bicep doesn't recognize

**Solutions:**
1. Externalize scripts to separate .sh files, upload to blob storage, download in CustomScriptExtension
2. Use fileUris + commandToExecute pattern
3. Use GitHub Actions which handles this better

## Portability

This code works on any laptop because:
- ✅ No hardcoded credentials (passed as parameters)
- ✅ SSH keys read from `~/.ssh/id_rsa.pub`
- ✅ Environment selection (dev/prod)
- ✅ Deployment script prompts for inputs
- ✅ Works from any Azure CLI-enabled system

## Cleanup
```bash
# Delete resource group
az group delete --name rg-caldera-<environment>-<timestamp> --yes --no-wait

# Verify deletion
az group list --query "[?contains(name, 'caldera')]" --output table
```

## Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│  Azure Subscription (Australia East)                    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Resource Group: rg-caldera-{env}-{timestamp}      │ │
│  │                                                      │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │  VNet: 10.0.0.0/16                          │  │ │
│  │  │                                              │  │ │
│  │  │  Subnet: Servers (10.0.1.0/24)             │  │ │
│  │  │  ├─ CALDERA Server (Ubuntu 22.04)          │  │ │
│  │  │  │   - Port 8888 (Web UI)                  │  │ │
│  │  │  │   - Plugins: orchestrator, branding     │  │ │
│  │  │  └─ ELK Server (Ubuntu 22.04)              │  │ │
│  │  │      - Port 9200 (Elasticsearch)           │  │ │
│  │  │      - Port 5601 (Kibana)                  │  │ │
│  │  │      - Port 5044 (Logstash/Beats)          │  │ │
│  │  │                                              │  │ │
│  │  │  Subnet: Agents (10.0.2.0/24)              │  │ │
│  │  │  ├─ Windows Agent (Server 2022)            │  │ │
│  │  │  │   - Sandcat agent → CALDERA             │  │ │
│  │  │  │   - Winlogbeat → ELK                    │  │ │
│  │  │  └─ Linux Agent (Ubuntu 22.04)             │  │ │
│  │  │      - Sandcat agent → CALDERA             │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  │                                                      │ │
│  │  Log Analytics Workspace                             │ │
│  │  NSG Rules (SSH, RDP, CALDERA, ELK)                 │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Support
- Review logs: `journalctl -u caldera -f` (on CALDERA server)
- Check Bicep: `az bicep build --file bicep/main.bicep`
- Validate deployment: `az deployment sub show --name <deployment-name>`

