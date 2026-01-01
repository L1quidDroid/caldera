# CALDERA Purple Team Lab - Production Deployment Guide

## Overview

This repository contains a **production-ready** Infrastructure as Code (Bicep) deployment for CALDERA adversary emulation platform with integrated ELK Stack (Elasticsearch, Kibana, Logstash) on Azure.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Subscription                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               Virtual Network (10.0.0.0/16)          │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │ CALDERA & ELK Server (Ubuntu 22.04)        │   │  │
│  │  │ - CALDERA (port 8888)                      │   │  │
│  │  │ - Elasticsearch (port 9200)                │   │  │
│  │  │ - Kibana (port 5601)                       │   │  │
│  │  │ - Logstash (port 5044)                     │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                       │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐ │  │
│  │  │ Windows Agent VM     │  │ Linux Agent VM       │ │  │
│  │  │ (Server 2022)        │  │ (Ubuntu 22.04)       │ │  │
│  │  │ - Sandcat Agent      │  │ - Sandcat Agent      │ │  │
│  │  │ - Winlogbeat         │  │ - Filebeat           │ │  │
│  │  └──────────────────────┘  └──────────────────────┘ │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Log Analytics Workspace (Monitoring)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

✅ **Modularized Bicep Templates**
- Separate modules for networking, logging, VMs
- Reusable components for multiple environments
- Proper separation of concerns

✅ **Production-Ready Scripts**
- Comprehensive error handling and retry logic
- Service health checks and verification
- Structured logging with timestamps
- Idempotent installations (safe to retry)

✅ **Security-Focused**
- Network Security Groups for traffic isolation
- Subnet segmentation (Caldera/ELK, Agents)
- SSH/RDP management restricted to defined CIDR
- Azure Log Analytics integration

✅ **Environment Support**
- `dev` - Single B2s VM (budget constrained)
- `stage` - Standard D-series for testing
- `prod-lab` - E-series for production workloads

✅ **Scalability**
- Conditional agent deployment
- Configurable VM sizes per environment
- Modular ELK configuration

## Directory Structure

```
caldera/
├── bicep/
│   ├── main.bicep                 # Main orchestration template
│   ├── main.json                  # Compiled template
│   ├── modules/
│   │   ├── network.bicep          # Network & NSG configuration
│   │   ├── logging.bicep          # Log Analytics setup
│   │   ├── caldera-elk-server.bicep
│   │   ├── windows-agent.bicep
│   │   └── linux-agent.bicep
│   ├── parameters/
│   │   ├── dev.parameters.json
│   │   ├── stage.parameters.json
│   │   └── prod-lab.parameters.json
│   └── scripts/
│       ├── lib-common.sh          # Common functions
│       ├── lib-elasticsearch.sh   # ES installation
│       ├── lib-caldera.sh         # CALDERA installation
│       ├── lib-elk.sh             # Kibana/Logstash setup
│       ├── install-caldera-elk.sh # Main server install
│       ├── install-linux-agent.sh # Linux agent
│       └── install-windows-agent.ps1 # Windows agent
│
└── deployment/
    ├── scripts/
    │   ├── setup/
    │   │   └── deploy.sh          # Main deployment orchestrator
    │   ├── validation/
    │   │   ├── pre-deploy-check.sh  # Pre-flight validation
    │   │   └── health-check.sh    # Post-deployment verification
    │   └── utilities/
    │       └── encode-scripts.sh  # Script encoding helper
    └── configs/
        └── (custom configurations)
```

## Prerequisites

### Local Machine

```bash
# Azure CLI
brew install azure-cli

# Required tools
brew install jq
```

### Azure Subscription

- Active Azure subscription
- Sufficient quota for VM deployment (check Azure Portal → Quotas)
- For dev: ≥ 1 vCPU quota for B-series VMs
- For prod-lab: ≥ 8 vCPU quota for E-series VMs

### Authentication

```bash
az login
az account set --subscription <YOUR_SUBSCRIPTION_ID>
```

## Deployment Options

### Option 1: Quick Deploy (Recommended)

```bash
# Navigate to project root
cd caldera

# Run pre-flight checks
./deployment/scripts/validation/pre-deploy-check.sh

# Deploy to dev environment
ENVIRONMENT=dev ./deployment/scripts/setup/deploy.sh

# Check health
./deployment/scripts/validation/health-check.sh <CALDERA_IP>
```

### Option 2: Custom Parameters

```bash
# Deploy with custom settings
az deployment sub create \
  --name "caldera-$(date +%Y%m%d-%H%M%S)" \
  --template-file bicep/main.bicep \
  --parameters bicep/parameters/dev.parameters.json \
  --parameters adminUsername="your-user" \
  --parameters adminPassword="Your!P@ss123" \
  --parameters managementCidr="YOUR_IP/32" \
  --parameters deployAgents=true \
  --location australiaeast
```

### Option 3: Azure Portal

1. Go to Azure Portal → "Deploy a custom template"
2. Use the compiled `bicep/main.json`
3. Fill in parameters interactively

## Configuration

### Environment Parameters

Edit `bicep/parameters/<environment>.parameters.json`:

```json
{
  "parameters": {
    "environment": { "value": "dev" },
    "location": { "value": "australiaeast" },
    "adminUsername": { "value": "calderaadmin" },
    "managementCidr": { "value": "YOUR_IP/32" },
    "deployAgents": { "value": false }
  }
}
```

### VM Sizing

| Environment | Caldera/ELK VM | Agent VM | Use Case |
|-----------|---|---|---|
| dev | Standard_B2s (2vCPU, 4GB) | B1s | Development, low quota |
| stage | Standard_D8s_v3 (8vCPU, 32GB) | D2s_v5 | Testing, realistic workload |
| prod-lab | Standard_E8s_v3 (8vCPU, 64GB) | D2s_v5 | Production emulation |

### Network Security

Default configuration allows access from anywhere (`0.0.0.0/0`). For production, set `managementCidr`:

```bash
# Allow only your IP
MANAGEMENT_CIDR="203.0.113.45/32"

# Or a corporate network
MANAGEMENT_CIDR="203.0.113.0/24"
```

## Post-Deployment

### Access CALDERA

```bash
# SSH to server
ssh calderaadmin@<CALDERA_PUBLIC_IP>

# Default credentials
URL: http://<CALDERA_PUBLIC_IP>:8888
User: red
Password: admin
```

### Access Kibana

```
URL: http://<CALDERA_PUBLIC_IP>:5601
(No authentication in this configuration)
```

### Install Additional Plugins

```bash
ssh calderaadmin@<CALDERA_IP>
cd /home/calderaadmin/caldera

# Install orchestrator plugin
cd orchestrator
source ../caldera_venv/bin/activate
pip install -r requirements.txt
deactivate

# Update conf/local.yml
nano conf/local.yml
# Add: - orchestrator

# Restart
sudo systemctl restart caldera
```

### Configure Agents Manually

The deployment includes optional agent VMs. To manually connect agents:

```bash
# Linux agent
ssh ubuntu@<LINUX_AGENT_IP>
curl -s "http://<CALDERA_IP>:8888/file/download" -o /tmp/sandcat
chmod +x /tmp/sandcat
/tmp/sandcat -server "http://<CALDERA_IP>:8888" -group blue -v

# Windows agent (PowerShell as Admin)
$calderaUrl = "http://<CALDERA_IP>:8888"
$sandcatUrl = "$calderaUrl/file/download"
Invoke-WebRequest -Uri $sandcatUrl -OutFile "$env:TEMP\sandcat.exe"
& "$env:TEMP\sandcat.exe" -server $calderaUrl -group red -v
```

## Troubleshooting

### Deployment Fails with Elasticsearch Error

**Error**: "Duplicate field 'xpack.security.enabled'"

**Solution**: The installation script now removes existing config before writing new one.

### Low Memory Issues (B2s)

**Symptoms**: Services crash, high CPU usage

**Solution**:
```bash
# Check available memory
free -h

# Reduce Elasticsearch heap (edit on server)
sudo nano /etc/elasticsearch/jvm.options.d/heap.options
# Change: -Xms256m -Xmx256m
sudo systemctl restart elasticsearch
```

### CALDERA Won't Start

**Check logs**:
```bash
sudo journalctl -u caldera -n 50 --no-pager

# Or direct log
cat /var/log/caldera-elk-setup.log
```

### Agents Not Registering

```bash
# Check agent log
ssh ubuntu@<AGENT_IP>
tail -f /var/log/caldera-agent-setup.log

# Verify network connectivity
curl -v http://<CALDERA_IP>:8888

# Restart agent
sudo systemctl restart sandcat
```

## Cleanup

To delete all deployed resources:

```bash
# Get resource group name
az deployment sub show --name <DEPLOYMENT_NAME> --query "properties.parameters"

# Delete resource group (this deletes everything)
az group delete --name rg-caldera-dev-<ID> --yes
```

## Monitoring & Logging

### Azure Monitor Integration

All VMs send metrics to Log Analytics workspace. View in Azure Portal:
- Virtual Machines → Insights
- Log Analytics Workspace → Logs

### Query Agent Activity

```kusto
// CALDERA agent checkins
Heartbeat
| where Computer contains "agent"
| summarize LastCheckin=max(TimeGenerated) by Computer
| order by LastCheckin desc

// Elasticsearch metrics
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.OPERATIONALINSIGHTS"
| summarize AvgCpu=avg(CounterValue) by bin(TimeGenerated, 5m)
```

## Security Considerations

⚠️ **Lab Environment Only**: This configuration disables security features for ease of testing.

For production adversary emulation:

1. **Enable Elasticsearch Security**
   - Update `xpack.security.enabled: true`
   - Set admin credentials
   - Use SSL/TLS

2. **Network Hardening**
   - Restrict management CIDR to specific IPs
   - Use Azure Bastion for VM access
   - Enable Network Watcher flow logs

3. **Access Control**
   - Use Azure AD integration
   - Implement RBAC for Kibana
   - Enable multi-factor authentication

4. **Compliance**
   - Enable Azure Policy guardrails
   - Configure audit logging retention
   - Document data handling procedures

## Support & Development

### Contributing

To modify deployment scripts:

1. Edit scripts in `bicep/scripts/`
2. Test locally if possible
3. Encode scripts: `./deployment/scripts/utilities/encode-scripts.sh`
4. Update parameters file
5. Validate: `./deployment/scripts/validation/pre-deploy-check.sh`

### Common Customizations

**Add Custom Ability**:
```bash
# SSH to CALDERA
cd /home/calderaadmin/caldera/data/abilities
# Add YAML files for new abilities
sudo systemctl restart caldera
```

**Install Custom Plugin**:
```bash
cd /home/calderaadmin/caldera/plugins
git clone https://github.com/user/plugin.git
cd ..
sudo systemctl restart caldera
```

## References

- [CALDERA Documentation](https://caldera.mitre.org/)
- [Azure Bicep Reference](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [ELK Stack Documentation](https://www.elastic.co/guide/index.html)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)

---

**Last Updated**: December 2025  
**Status**: Production Ready  
**Maintainer**: Tony To (Triskele Labs)
