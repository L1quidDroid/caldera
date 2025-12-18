# CALDERA Purple Team Demo - Azure Deployment

## 🎯 Overview

This deployment script creates a complete 3-VM purple team environment in Azure for executive demos of CALDERA as an internal security tool.

**Setup Time**: 15 minutes  
**Demo Time**: 5-10 minutes  
**Cost**: ~$75-100/month (if running 24/7)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Resource Group                  │
│                                                           │
│  ┌──────────────────┐  ┌──────────────┐  ┌────────────┐│
│  │ CALDERA+ELK      │  │ Red Agent    │  │ Blue Agent ││
│  │ Ubuntu 22.04     │  │ Windows 2022 │  │ Ubuntu 22  ││
│  │                  │  │              │  │            ││
│  │ :8888 CALDERA    │◄─┤ Sandcat      │  │ Elasticat  │◄┐
│  │ :5601 Kibana     │  │ Group: red   │  │ Group: blue│ │
│  │ :9200 ES API     │◄─┴──────────────┘  └────────────┘ │
│  └──────────────────┘         Agent C2                   │
│         │                   :7010-7012                    │
│         │                                                 │
│    Public Internet                                        │
└─────────┼───────────────────────────────────────────────┘
          │
      Executive
    Demo Access
```

### Network Security Group Rules

| Priority | Port(s) | Purpose |
|----------|---------|---------|
| 100 | 22 | SSH (Linux VMs) |
| 110 | 3389 | RDP (Windows VM) |
| 120 | 8888 | CALDERA Web UI |
| 130 | 5601 | Kibana Dashboard |
| 140 | 9200 | Elasticsearch API |
| 150 | 7010-7012 | Agent C2 Communication |

## 🚀 Quick Start

### Prerequisites

- Azure CLI installed and logged in (`az login`)
- Azure subscription with permissions to create resources
- Terminal access (bash/zsh)

### 1. Deploy Infrastructure

```bash
cd scripts
./demo_caldera_internal.sh
```

**What it does**:
- Creates Azure resource group with timestamp
- Deploys 3 VMs with public IPs
- Configures NSG rules
- Generates all helper scripts in `demo_scripts_<timestamp>/`

**Duration**: 10-15 minutes

### 2. Setup CALDERA Server

```bash
# Copy setup script to server
scp demo_scripts_*/caldera_server_setup.sh tonyto@<CALDERA_IP>:~/

# SSH and run setup
ssh tonyto@<CALDERA_IP>
bash caldera_server_setup.sh
```

**What it does**:
- Installs ELK stack (Elasticsearch, Kibana, Logstash)
- Clones and installs CALDERA
- Creates systemd service for auto-restart
- Starts all services

**Duration**: 5-10 minutes

### 3. Deploy Red Agent (Windows)

```bash
# RDP to Windows VM
mstsc /v:<RED_IP>

# Or on macOS
open rdp://<RED_IP>

# Copy deploy_red_agent.ps1 to Windows
# Run in PowerShell:
.\deploy_red_agent.ps1
```

**Duration**: 2 minutes

### 4. Deploy Blue Agent (Linux)

```bash
# Copy setup script to blue agent
scp demo_scripts_*/deploy_blue_agent.sh tonyto@<BLUE_IP>:~/

# SSH and run setup
ssh tonyto@<BLUE_IP>
bash deploy_blue_agent.sh
```

**Duration**: 2 minutes

### 5. Validate Setup

```bash
cd demo_scripts_*
./demo_validation.sh <CALDERA_IP>
```

**Expected Output**:
```
================================================
🔍 DEMO VALIDATION
================================================

✅ CALDERA Web UI:
   ✅ http://X.X.X.X:8888 - OK (200)

✅ Kibana Dashboard:
   ✅ http://X.X.X.X:5601 - OK (200)

✅ Elasticsearch API:
   ✅ http://X.X.X.X:9200 - OK (200)

✅ Registered Agents:
   📊 2 agent(s) registered
   Agent details:
      - abc123: windows (red)
      - def456: linux (blue)
```

## 🎬 Executive Demo Flow (5-10 minutes)

### Step 1: Show Architecture (1 min)

- Open Azure Portal
- Navigate to resource group
- Show 3 VMs running
- Highlight NSG security rules
- Mention systemd services (production-ready)

### Step 2: CALDERA UI (1 min)

1. Navigate to `http://<CALDERA_IP>:8888`
2. Login: `admin / admin`
3. Click **Agents** tab
4. Point out 2 agents:
   - Windows (red group)
   - Linux (blue group)

### Step 3: Run Operation (2-3 min)

1. Navigate to **Operations** tab
2. Click **+ Create Operation**
3. Configure:
   - Name: "Executive Demo"
   - Adversary: "Collection" (or any T1xxx profile)
   - Group: Select "red"
   - Planner: "atomic"
4. Click **Start**
5. Watch abilities execute in real-time
6. Show command output and results

**Talking Points**:
- "Simulating real-world adversary TTPs"
- "Automated red team operations"
- "Testing detection capabilities"

### Step 4: Blue Team Monitoring (1 min)

1. Open Kibana: `http://<CALDERA_IP>:5601`
2. Show agent activity logs
3. Demonstrate correlation with CALDERA operations
4. Purple team value proposition

**Talking Points**:
- "Real-time visibility into attacks"
- "Detection validation"
- "Continuous security testing"

### Step 5: API Integration (1 min)

```bash
# Show REST API capabilities
curl -u admin:admin http://<CALDERA_IP>:8888/api/v2/agents | jq
curl -u admin:admin http://<CALDERA_IP>:8888/api/v2/operations | jq
```

**Talking Points**:
- "Full REST API for automation"
- "Integration with CI/CD pipelines"
- "Copilot integration ready"
- "Infrastructure as code security testing"

## 🎯 Approval Points

### Technical Excellence

✅ **Production Architecture**
- Systemd services (not manual processes)
- Auto-restart on failure
- Persistent across reboots

✅ **Multi-Agent Orchestration**
- Group-based segregation (red/blue)
- Platform diversity (Windows/Linux)
- Scalable to dozens of agents

✅ **Real-Time Monitoring**
- ELK stack integration
- Centralized logging
- Visual dashboards

✅ **API-First Design**
- RESTful API for all operations
- Automation-ready
- Webhook support for notifications

✅ **Purple Team Capabilities**
- Adversary emulation (red team)
- Detection validation (blue team)
- Comprehensive security testing

### Business Value

- **Time Savings**: Automated vs. manual testing
- **Cost Efficiency**: ~$75/month for complete lab
- **Reusability**: Teardown and rebuild as needed
- **Scalability**: Production-ready architecture
- **Integration**: CI/CD and automation ready

## 🧹 Cleanup

When done with the demo:

```bash
cd demo_scripts_*
./cleanup_demo.sh
```

This deletes all Azure resources (runs in background).

## 📊 Cost Breakdown

### Azure Resources (Australia East)

| Resource | Size | Cost/Month |
|----------|------|------------|
| 3x VMs | Standard_B2s | ~$60 |
| 3x Public IPs | Standard | ~$3 |
| Storage | Managed Disks | ~$10 |
| Network | Egress | Variable |

**Total**: ~$75-100/month (if running 24/7)

### Cost Optimization

- Stop VMs when not demoing (Azure Portal or CLI)
- Delete resource group after demo
- Use Azure Dev/Test pricing if available
- Consider B1s VMs for agents (~$40/month savings)

## 🔧 Troubleshooting

### Agent Not Appearing

**Symptoms**: Agent script runs but doesn't show in CALDERA UI

**Solutions**:
1. Check NSG rules allow ports 7010-7012
2. Verify CALDERA URL is correct in agent script
3. Check agent logs:
   - Windows: Task Manager → Check process
   - Linux: `tail -f ~/elasticat.log`
4. Ensure CALDERA is running: `sudo systemctl status caldera`

### CALDERA Not Starting

**Symptoms**: Cannot access http://<IP>:8888

**Solutions**:
1. Check service status: `sudo systemctl status caldera`
2. View logs: `sudo journalctl -u caldera -f`
3. Verify Python environment: `ls ~/caldera/venv/bin/python`
4. Check port 8888: `sudo netstat -tlnp | grep 8888`
5. Restart service: `sudo systemctl restart caldera`

### ELK Stack Issues

**Symptoms**: Kibana or Elasticsearch not accessible

**Solutions**:
1. Check Elasticsearch: `curl localhost:9200`
2. Check Kibana: `curl localhost:5601`
3. View logs:
   - ES: `sudo journalctl -u elasticsearch -f`
   - Kibana: `sudo journalctl -u kibana -f`
4. Verify memory (needs 4GB): `free -h`
5. Restart services:
   ```bash
   sudo systemctl restart elasticsearch
   sleep 10
   sudo systemctl restart kibana
   ```

### Network Connectivity

**Symptoms**: Cannot access CALDERA from browser

**Solutions**:
1. Test from local machine: `curl http://<CALDERA_IP>:8888`
2. Check Azure NSG rules in portal
3. Verify public IP: `az vm show -d -g <RG> -n <VM> --query publicIps`
4. Check VM firewall: `sudo ufw status` (should be inactive)

### Windows RDP Issues

**Symptoms**: Cannot RDP to Windows VM

**Solutions**:
1. Verify NSG allows port 3389
2. Check VM is running in Azure Portal
3. Get correct IP: `az vm show -d -g <RG> -n win-red-agent --query publicIps`
4. Try from different network (corporate firewall might block)

## 📚 Additional Resources

### Files Generated

After running `demo_caldera_internal.sh`:

```
demo_scripts_<timestamp>/
├── caldera_server_setup.sh   # Server installation
├── deploy_red_agent.ps1       # Windows agent
├── deploy_blue_agent.sh       # Linux agent
├── demo_validation.sh         # Health checks
├── cleanup_demo.sh            # Resource deletion
└── deployment_info.txt        # All IPs and credentials
```

### Useful Commands

```bash
# Check CALDERA service
ssh tonyto@<CALDERA_IP>
sudo systemctl status caldera
sudo journalctl -u caldera -f

# Check agents in CALDERA
curl -u admin:admin http://<CALDERA_IP>:8888/api/v2/agents | jq

# Stop/Start VMs to save costs
az vm deallocate -g <RG> -n <VM_NAME>
az vm start -g <RG> -n <VM_NAME>

# List all resources
az resource list -g <RG> --output table

# Delete everything
az group delete -n <RG> --yes --no-wait
```

### API Endpoints

```bash
# Health check
curl http://<IP>:8888/api/v2/health

# List agents
curl -u admin:admin http://<IP>:8888/api/v2/agents

# List operations
curl -u admin:admin http://<IP>:8888/api/v2/operations

# List abilities
curl -u admin:admin http://<IP>:8888/api/v2/abilities

# List adversaries
curl -u admin:admin http://<IP>:8888/api/v2/adversaries
```

## 🔐 Security Considerations

### ⚠️ Demo Environment Only

This configuration is for **internal demos only**:
- `--insecure` flag (no HTTPS)
- Default credentials (`admin/admin`)
- No Elasticsearch authentication
- Permissive NSG rules
- Public IPs on all VMs

### Production Hardening Required

For production deployment:

1. **Enable HTTPS**
   - Install SSL certificates
   - Remove `--insecure` flag
   - Configure proper TLS

2. **Change Credentials**
   - Update CALDERA admin password
   - Enable Elasticsearch security
   - Use Azure Key Vault for secrets

3. **Network Security**
   - Use private endpoints
   - Implement least-privilege NSG rules
   - Consider Azure Firewall
   - VPN or Azure Bastion for access

4. **Monitoring**
   - Enable Azure Monitor
   - Configure alerts
   - Log Analytics integration

5. **Backup**
   - VM snapshots
   - Configuration backups
   - Disaster recovery plan

## 📞 Support

For questions or issues:
- CALDERA Docs: https://caldera.readthedocs.io
- Azure CLI Docs: https://learn.microsoft.com/cli/azure
- Project README: ../README.md
- Troubleshooting: ../docs/TROUBLESHOOTING.md

## 📝 Next Steps After Approval

1. **Production Architecture Design**
   - High availability setup
   - Disaster recovery
   - Backup strategy

2. **Security Hardening**
   - SSL/TLS implementation
   - Secret management (Key Vault)
   - Network segmentation

3. **Integration Planning**
   - SIEM integration
   - Ticketing system webhooks
   - CI/CD pipeline integration

4. **Training & Documentation**
   - Admin runbooks
   - User guides
   - Video tutorials

5. **Pilot Program**
   - Select test team
   - Define success metrics
   - Gather feedback

---

**Version**: 1.0  
**Date**: December 17, 2025  
**Maintained By**: Triskele Labs
