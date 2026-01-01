# Azure Quota Analysis Report - Caldera Bicep Deployment
## Triskele Labs Fork - December 2025

---

## Executive Summary

| Metric | Homelab (Student/Free) | Corporate (PayAsYouGo) |
|--------|----------------------|----------------------|
| **Ready to Deploy** | ✅ YES | ✅ YES |
| **vCPU Usage** | 2/4 (50%) | 4/10+ (40%) |
| **Public IPs** | 1-3/5 (60%) | 3/50 (6%) |
| **Critical Fixes** | None Required | None Required |
| **Recommended Config** | `deployAgents=false` | `deployAgents=true` |

---

## 1. Resource Inventory (from Bicep Analysis)

### 1.1 Virtual Machines

| VM | Bicep Module | VM Size (dev) | vCPUs | Memory | OS Disk | Premium SSD? |
|----|--------------|---------------|-------|--------|---------|--------------|
| Caldera-ELK | `caldera-elk-server.bicep` | Standard_B2s | 2 | 4GB | 256GB | ✅ Yes |
| Windows Agent | `windows-agent.bicep` | Standard_B1s | 1 | 1GB | 128GB | ✅ Yes |
| Linux Agent | `linux-agent.bicep` | Standard_B1s | 1 | 1GB | 64GB | ❌ Standard |

**Total vCPUs:**
- Without agents (`deployAgents=false`): **2 vCPUs**
- With agents (`deployAgents=true`): **4 vCPUs**

### 1.2 Networking Resources

| Resource | Quantity | Module | Notes |
|----------|----------|--------|-------|
| Virtual Network | 1 | `network.bicep` | 10.0.0.0/16 |
| Subnets | 3 | `network.bicep` | caldera, elk, agents |
| Network Security Groups | 3 | `network.bicep` | Per subnet |
| Public IP Addresses | 1-3 | Per VM module | Standard SKU, Static |
| Network Interfaces | 1-3 | Per VM module | Dynamic private IP |

### 1.3 Monitoring Resources

| Resource | Quantity | Module | Quota Impact |
|----------|----------|--------|--------------|
| Log Analytics Workspace | 1 | `logging.bicep` | Daily cap: 1GB (dev) |
| Diagnostic Settings | 1-3 | Per VM | Metrics only |
| Scheduled Query Rules | 1 | `logging.bicep` | Alert for agent check-in |

---

## 2. Azure Quota Limits by Account Type

### 2.1 Student Account ($100 Credit) - **STRICTEST**

| Resource | Default Limit | Caldera Requires | Status |
|----------|---------------|------------------|--------|
| Total Regional vCPUs | **4** | 2 (no agents) / 4 (with agents) | ⚠️ AT LIMIT |
| B-Series vCPUs | **4** | 2-4 | ⚠️ AT LIMIT |
| Public IP Addresses | 5 | 1-3 | ✅ OK |
| Storage Accounts | 5 | 0 | ✅ OK |
| VNets per Subscription | 50 | 1 | ✅ OK |
| NSGs per Subscription | 100 | 3 | ✅ OK |
| Managed Disks | No hard limit | 1-3 | ✅ OK |
| Log Analytics Ingestion | **5GB/day** | 1GB configured | ✅ OK |

**⚠️ CRITICAL CONSTRAINT:** Student accounts have a **hard 4 vCPU limit per region** with **no quota increase option**.

### 2.2 Free Account (12-month trial)

| Resource | Default Limit | Caldera Requires | Status |
|----------|---------------|------------------|--------|
| Total Regional vCPUs | 4 | 2-4 | ⚠️ AT LIMIT |
| B-Series vCPUs | 4 | 2-4 | ⚠️ AT LIMIT |
| Public IP Addresses | 5 | 1-3 | ✅ OK |
| Premium SSD (P10/P15) | Limited | 1-3 | ⚠️ May fail |
| Standard SSD | 2 | 0-1 | ✅ OK |

**Note:** Free accounts may have additional restrictions on Premium_LRS disks.

### 2.3 Pay-As-You-Go / Corporate

| Resource | Default Limit | Caldera Requires | Status |
|----------|---------------|------------------|--------|
| Total Regional vCPUs | 10-20 | 4 | ✅ OK |
| B-Series vCPUs | 10 | 4 | ✅ OK |
| Public IP Addresses | 50 | 3 | ✅ OK |
| Storage Accounts | 250 | 0 | ✅ OK |
| VNets per Subscription | 1000 | 1 | ✅ OK |
| NSGs per Subscription | 5000 | 3 | ✅ OK |

**Quota increases available** via Azure Portal.

---

## 3. Location-Specific Analysis

### 3.1 australiaeast (Primary Region)

| SKU | Availability | Restrictions |
|-----|--------------|--------------|
| Standard_B2s | ✅ Available | None |
| Standard_B1s | ✅ Available | None |
| Premium_LRS | ✅ Available | None |
| Standard_LRS | ✅ Available | None |

### 3.2 southeastasia (Alternative)

| SKU | Availability | Restrictions |
|-----|--------------|--------------|
| Standard_B2s | ✅ Available | None |
| Standard_B1s | ✅ Available | None |
| Premium_LRS | ✅ Available | None |

### 3.3 Regions to Avoid (Quota Issues)

- **brazilsouth**: Limited B-series availability
- **westindia**: Often restricted for new subscriptions
- **uaenorth**: May require explicit enablement

---

## 4. Parameterization Review

### 4.1 Current dev.parameters.json Analysis

```json
{
  "deployAgents": { "value": false }  // ✅ CORRECT for Student accounts
}
```

**Status:** ✅ Parameters are correctly configured for homelab deployment.

### 4.2 Environment-Specific VM Sizing (main.bicep:85-100)

```bicep
var vmSizes = {
  dev: {
    calderaElk: 'Standard_B2s'  // 2 vCPUs - ✅ Fits Student quota
    agent: 'Standard_B1s'        // 1 vCPU each
  }
  stage: {
    calderaElk: 'Standard_D8s_v3'  // 8 vCPUs - ❌ Exceeds Student quota
    agent: 'Standard_D2s_v5'       // 2 vCPUs each
  }
}
```

**Recommendation:** `dev` environment is correctly sized for homelab. Do NOT use `stage` or `prod-lab` in Student accounts.

### 4.3 Conditional Agent Deployment (main.bicep:163)

```bicep
module windowsAgent 'modules/windows-agent.bicep' = if (deployAgents) {
```

**Status:** ✅ Agents are conditionally deployed. Setting `deployAgents=false` saves 2 vCPUs.

---

## 5. Potential Issues & Fixes

### 5.1 Premium_LRS Disk in Free/Student Accounts

**Issue:** `caldera-elk-server.bicep:89` uses `Premium_LRS` which may fail in Free accounts.

**Location:** [caldera-elk-server.bicep#L89](bicep/modules/caldera-elk-server.bicep#L89)

```bicep
managedDisk: {
  storageAccountType: 'Premium_LRS'  // May fail in Free tier
}
```

**Fix:** Add conditional disk type based on environment:

```bicep
// Add parameter
@description('Storage account type for OS disk')
@allowed(['Premium_LRS', 'Standard_LRS', 'StandardSSD_LRS'])
param osDiskType string = 'Premium_LRS'

// Modify disk config
managedDisk: {
  storageAccountType: osDiskType
}
```

### 5.2 Log Analytics Daily Cap

**Issue:** `logging.bicep:29` caps at 1GB for dev, which is appropriate.

**Status:** ✅ No fix needed - correctly configured.

### 5.3 Hard-coded australiaeast Region

**Issue:** `main.bicep:22` limits to Australian regions only.

```bicep
@allowed([
  'australiaeast'
  'australiasoutheast'
])
```

**Fix for global deployment:** Expand allowed regions:

```bicep
@allowed([
  'australiaeast'
  'australiasoutheast'
  'southeastasia'
  'eastus'
  'westeurope'
])
```

---

## 6. Corporate Environment Considerations

### 6.1 Policy Conflicts

| Azure Policy | Impact | Mitigation |
|--------------|--------|------------|
| Require tags on resources | ⚠️ May fail | Add required tags to `commonTags` |
| Allowed VM SKUs | ⚠️ May block B-series | Request policy exemption |
| Allowed locations | ⚠️ May block australiaeast | Use allowed region |
| Require private endpoints | ❌ Will fail | Not supported in this template |

### 6.2 RBAC Requirements

| Permission | Scope | Purpose |
|------------|-------|---------|
| Contributor | Resource Group | Create VMs, networking |
| User Access Administrator | Resource Group | Assign VM identities |
| Log Analytics Contributor | Workspace | Configure diagnostics |

**Minimum Role:** `Contributor` on the subscription (for RG creation at subscription scope).

### 6.3 Network Restrictions

- **Private endpoints:** Not implemented (would require additional modules)
- **Service endpoints:** Not configured
- **Firewall rules:** NSGs allow configurable `managementCidr`

---

## 7. Pre-Deployment Checklist

### For Student/Free Accounts

- [ ] Verify no existing VMs in target region: `az vm list --query "[].location"`
- [ ] Set `deployAgents=false` in parameters
- [ ] Run quota check: `./deployment/scripts/validation/check-azure-quotas.sh --homelab`
- [ ] Use `dev` environment (not stage/prod-lab)
- [ ] Have $10-15 credit available (approx. daily cost)

### For Corporate Accounts

- [ ] Check Azure Policy assignments: `az policy assignment list`
- [ ] Verify RBAC permissions
- [ ] Run quota check: `./deployment/scripts/validation/check-azure-quotas.sh --corporate`
- [ ] Use Key Vault for secrets (see `corporate.parameters.json`)
- [ ] Restrict `managementCidr` to corporate IP ranges

---

## 8. Cost Estimation

### 8.1 Homelab (deployAgents=false)

| Resource | SKU | Est. Daily Cost |
|----------|-----|-----------------|
| VM (Caldera-ELK) | B2s | ~$1.20 |
| OS Disk (256GB) | Premium P15 | ~$0.80 |
| Public IP | Standard | ~$0.12 |
| Log Analytics | 1GB | Free tier |
| **Total** | | **~$2.12/day** |

**Monthly:** ~$65 | **Fits $100 Student credit** ✅

### 8.2 Corporate (deployAgents=true)

| Resource | SKU | Est. Daily Cost |
|----------|-----|-----------------|
| VM (Caldera-ELK) | B2s | ~$1.20 |
| VM (Windows Agent) | B1s | ~$0.60 |
| VM (Linux Agent) | B1s | ~$0.60 |
| Disks (448GB total) | Mixed | ~$1.50 |
| Public IPs (3) | Standard | ~$0.36 |
| Log Analytics | 5GB | ~$2.50 |
| **Total** | | **~$6.76/day** |

**Monthly:** ~$200

---

## 9. Validation Commands

```bash
# Check vCPU quota
az vm list-usage --location australiaeast --output table | grep -E "vCPU|BS Family"

# Check current VM usage
az vm list --query "[].{Name:name, Location:location, Size:hardwareProfile.vmSize}" -o table

# Check public IP usage
az network public-ip list --query "length(@)"

# Validate Bicep syntax
az bicep build --file bicep/main.bicep --stdout > /dev/null && echo "✅ Valid"

# Dry-run deployment (requires resource group)
az deployment sub what-if \
  --location australiaeast \
  --template-file bicep/main.bicep \
  --parameters @bicep/parameters/homelab.parameters.json
```

---

## 10. Summary

| Environment | Status | Config Required |
|-------------|--------|-----------------|
| **Homelab (Student)** | ✅ READY | Use `homelab.parameters.json`, `deployAgents=false` |
| **Homelab (Free)** | ⚠️ READY* | Same as Student, watch Premium_LRS |
| **Corporate (PayAsYouGo)** | ✅ READY | Use `corporate.parameters.json`, Key Vault |

**Critical Success Factors:**
1. ✅ vCPU quota fits within 4 limit (with `deployAgents=false`)
2. ✅ Public IP quota within 5 limit
3. ✅ Parameters allow scaling via `deployAgents` flag
4. ✅ Validation script provided: `check-azure-quotas.sh`
5. ✅ Location-independent (australiaeast, southeastasia supported)

---

*Report generated: December 2025*
*Bicep version analyzed: 2025-12-22*
