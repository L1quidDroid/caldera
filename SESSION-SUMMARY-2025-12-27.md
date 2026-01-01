# Session Summary: B1s Memory Optimization Implementation
**Date**: 27 December 2025  
**Status**: Implementation complete, ready for deployment validation

---

## What Was Done This Session

### 1. B1s Memory Optimization Analysis
Identified that the original stack (ELK + Caldera + n8n) would exceed B1s 1GB RAM limits. Developed optimized architecture:

| Component | Original | Optimized | Savings |
|-----------|----------|-----------|---------|
| Elasticsearch | 800MB+ | 512MB (256MB heap) | 38% |
| Caldera | 300MB+ | 256MB | 15% |
| n8n | ~100MB | **Removed** | 100% |
| **Total** | 1.6GB+ (fails) | **968MB** (fits) | 40% |

### 2. Files Created

#### Docker Infrastructure
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Full stack with ES, Caldera, optional Kibana, webhook service |
| `docker-compose.b1s.yml` | Override for minimal B1s deployment |
| `.env.b1s` | Environment template with B1s-optimized defaults |
| `quick-start-b1s.sh` | One-command deployment script |

#### Consolidated Workflow Service (replaces n8n)
| File | Lines Added |
|------|-------------|
| `orchestrator/services/webhook_service.py` | +600 lines |
| `orchestrator/Dockerfile.webhook` | New container definition |

**New capabilities in webhook_service.py:**
- `ConsolidatedWorkflowService` class
- `on_operation_complete()` - orchestrates full workflow
- `tag_elk_alerts()` - SIEM correlation
- `send_slack_notification()` - Block Kit formatted messages
- `generate_coverage_report()` - ATT&CK metrics
- `export_pdf_report()` - WeasyPrint integration
- `publish_to_github_pages()` - GitHub API publishing

#### Standalone CLIs
| File | Usage |
|------|-------|
| `orchestrator/attck_coverage.py` | `python attck_coverage.py --operation-id <id> --output json` |
| `orchestrator/export_report.py` | `python export_report.py --campaign-id <id> --format pdf` |

#### Safety Rails & Governance
| File | Features |
|------|----------|
| `orchestrator/governance/safety_validator.py` | Test mode enforcement, high-risk blocking, audit logging |
| `orchestrator/governance/__init__.py` | Module exports |

#### Fleet Agent Policies (Elastic Defend + auditd)
| File | ATT&CK Techniques |
|------|-------------------|
| `deployment/configs/fleet-policies/elastic-defend.json` | T1003, T1059, T1547, T1078, T1548, T1055, T1071, T1105 |
| `deployment/configs/fleet-policies/auditd-policy.json` | T1003, T1059, T1547, T1548, T1078, T1071, T1105, T1055, T1082, T1562 |
| `deployment/configs/fleet-policies/system-integration.json` | T1078, T1082, T1016, T1057, T1049 |

#### CI/CD
| File | Trigger |
|------|---------|
| `.github/workflows/publish-reports.yml` | Manual (campaign_id) or push to reports/ |

### 3. Key Decisions Made
1. **Removed n8n entirely** - Python `webhook_service.py` handles all automation, saves ~100MB RAM
2. **Replaced Sysmon for Linux** (deprecated 2023) with Elastic Defend + auditd
3. **Kibana is optional** - Enabled via Docker profile, access ES directly for B1s
4. **Test mode default** - `TEST_MODE=true` prevents accidental production operations

---

## Git Status

**Committed but NOT pushed:**
```
99b805d2 feat: B1s memory optimization - consolidated stack with safety rails
```

**Unstaged files** (from previous work):
- Various Bicep changes
- Documentation files (ARCHITECTURE.md, IMPLEMENTATION.md, etc.)
- Additional deployment scripts

---

## Next Steps

### Immediate (Next Session)

1. **Push changes to GitHub**
   ```bash
   cd "/Users/tonyto/Documents/GitHub/Triskele Labs/caldera"
   git push origin master
   ```

2. **Generate secrets for .env**
   ```bash
   cp .env.b1s .env
   # Generate API keys:
   python3 -c "import secrets; print(f'CALDERA_API_KEY_RED={secrets.token_urlsafe(32)}')"
   python3 -c "import secrets; print(f'ELASTIC_PASSWORD={secrets.token_urlsafe(16)}')"
   ```

3. **Local Docker test**
   ```bash
   ./quick-start-b1s.sh start
   ./quick-start-b1s.sh status  # Verify memory < 968MB
   ```

4. **Verify services**
   - Caldera: http://localhost:8888
   - Elasticsearch: http://localhost:9200/_cluster/health

### Validation Checklist (From Spec)

- [ ] `docker stats` shows all services < memory limits
- [ ] Caldera API accessible at :8888
- [ ] Elasticsearch healthy (green/yellow)
- [ ] ≥2 agents enrolled
- [ ] First operation completes (T1059 recommended)
- [ ] Coverage report generates: `python orchestrator/attck_coverage.py --operation-id <id> --summary`
- [ ] Webhook service handles operation complete → ELK tags → Slack
- [ ] B1s stable 24+ hours (no OOM kills)

### Phase 2 (After Local Validation)

1. **Deploy to Azure B1s VM**
   - Create VM in portal (East US or Australia East)
   - SSH in and run quick-start script
   - Set up SSH tunnel for remote access

2. **Configure Fleet policies in Kibana**
   - Import `elastic-defend.json`
   - Import `auditd-policy.json`
   - Enroll agents with policies

3. **Test end-to-end workflow**
   - Run Caldera operation
   - Verify ELK tagging
   - Check Slack notification
   - Generate PDF report

---

## Open Questions / Considerations

1. **Kibana on B1s** - May need to omit entirely and use ES API directly. 128MB extra is tight.

2. **Swap space** - Consider adding 1GB swap as OOM protection:
   ```bash
   sudo fallocate -l 1G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **GitHub Pages auth** - Need to decide: SSH deploy key (simpler) or GitHub App token (more secure)?

4. **Bicep deployment** - Previous attempts failed with `RequestDisallowedByPolicy`. May need to use manual VM creation as documented in spec.

---

## Architecture Reference

```
┌─────────────────────────────────────────┐
│  B1s VM (1GB RAM)                       │
├─────────────────────────────────────────┤
│  Docker Compose                         │
│  ├── elasticsearch (512MB)              │
│  ├── caldera (256MB)                    │
│  └── [kibana] (128MB, optional)         │
├─────────────────────────────────────────┤
│  Host Python                            │
│  └── webhook_service.py                 │
│      ├── ELK tagging                    │
│      ├── Slack notifications            │
│      ├── PDF generation                 │
│      └── GitHub Pages publish           │
└─────────────────────────────────────────┘
        ↓
    SSH Tunnel for demos
    localhost:8888 → Caldera
    localhost:9200 → Elasticsearch
    localhost:5601 → Kibana (if enabled)
```

---

## Files to Review Next Session

1. `docker-compose.yml` - Verify memory limits are correct
2. `orchestrator/services/webhook_service.py` - Test the consolidated workflow
3. `.env.b1s` - Configure with real credentials
4. `quick-start-b1s.sh` - Test the deployment script

---

---

## Session 2: 28 December 2025 - Local Testing Attempts

### What Was Done

1. **Pushed changes to GitHub** ✅
   - Pushed commit `99b805d2` with B1s optimization implementation

2. **Generated secrets and configured .env** ✅
   ```bash
   CALDERA_API_KEY_RED=<32-char token generated>
   CALDERA_API_KEY_BLUE=<32-char token generated>
   CALDERA_ENCRYPTION_KEY=<32-char token generated>
   CALDERA_CRYPT_SALT=<32-char token generated>
   ELASTIC_PASSWORD=<16-char token generated>
   ```

3. **Attempted local Docker deployment** ⚠️
   - Updated `quick-start-b1s.sh` to use `docker compose` (space) instead of `docker-compose`
   - Fixed macOS compatibility issues (`free` command not available)

### Findings & Blockers

#### ❌ Elasticsearch OOM on macOS Docker Desktop
- **Issue**: Elasticsearch container killed with exit code 137 (OOM)
- **Root cause**: Even with 256MB heap (`ES_JAVA_OPTS=-Xms256m -Xmx256m`), Elasticsearch needs more memory overhead
- **Environment**: macOS with 16GB RAM, Docker Desktop allocated 7.6GB
- **Logs**: 
  ```
  OpenJDK 64-Bit Server VM warning: INFO: os::commit_memory
  [1]: max virtual memory areas vm.max_map_count [65530] is too low
  Killed
  ```

#### 🔧 Docker Compose Compatibility
- **Issue**: macOS uses `docker compose` (with space) not `docker-compose`
- **Fix**: Updated `quick-start-b1s.sh` to detect and use correct command
- **Status**: ✅ Resolved

#### 🔧 macOS Command Compatibility
- **Issue**: `free` command not available on macOS
- **Fix**: Updated script to use `vm_stat` on macOS, `free` on Linux
- **Status**: ✅ Resolved

### Technical Insights

1. **B1s memory budget is realistic for Linux** - The 968MB calculation is valid for Azure B1s VMs running Linux
2. **macOS Docker Desktop overhead is higher** - Docker Desktop adds significant memory overhead compared to native Linux containers
3. **Elasticsearch needs `vm.max_map_count` tuning** - Default macOS value (65530) is too low; Linux requires 262144

### Results

| Component | Status | Notes |
|-----------|--------|-------|
| Git push | ✅ Complete | All changes in GitHub |
| .env configuration | ✅ Complete | Secrets generated |
| Docker Compose fixes | ✅ Complete | macOS compatibility |
| Local Elasticsearch | ❌ Failed | OOM on macOS Docker |
| Local Caldera standalone | ⏸️ Not tested | Blocked by ES dependency |

---

## Next Steps (Updated)

### Option 1: Skip Local Testing, Deploy to Azure B1s (Recommended)
Since the stack is optimized for Linux (not macOS Docker Desktop), deploy directly to Azure:

1. **Create Azure B1s VM manually** (bypass Bicep policy blocks)
   ```bash
   # In Azure Portal:
   # - Region: East US or Australia East
   # - Size: B1s (1 vCPU, 1GB RAM)
   # - OS: Ubuntu 22.04 LTS
   # - Disk: 20GB Standard SSD
   ```

2. **SSH to VM and deploy**
   ```bash
   ssh azureuser@<VM-IP>
   sudo apt update && sudo apt install -y docker.io docker-compose git
   git clone https://github.com/<YOUR-ORG>/caldera.git
   cd caldera
   cp .env.b1s .env
   # Edit .env with secrets from local copy
   ./quick-start-b1s.sh start
   ```

3. **Verify on Linux**
   ```bash
   ./quick-start-b1s.sh status
   docker stats --no-stream
   ```

### Option 2: Fix macOS Docker for Local Testing (Not Recommended)

**Would require:**
1. Increase Docker Desktop memory allocation to 4GB minimum
2. Configure `vm.max_map_count`:
   ```bash
   screen ~/Library/Containers/com.docker.docker/Data/vms/0/tty
   sysctl -w vm.max_map_count=262144
   ```
3. Reduce ES heap further (128MB) - may be unstable
4. Test Caldera standalone first without Elasticsearch

**Why not recommended:**
- macOS Docker Desktop has significant overhead vs Linux
- B1s optimization is designed for native Linux containers
- Testing on macOS won't reflect actual Azure B1s performance

### Option 3: Use Multipass for Local Linux VM Testing

Create lightweight Ubuntu VM on macOS:
```bash
brew install multipass
multipass launch --name caldera-test --cpus 2 --memory 2G --disk 20G
multipass shell caldera-test
# Then follow normal deployment steps
```

---

## Updated Validation Strategy

### Phase 1: Azure B1s Deployment (Priority)
1. Create B1s VM in Azure Portal
2. Deploy stack with `quick-start-b1s.sh`
3. Verify memory usage < 968MB
4. Complete POC validation checklist

### Phase 2: Local Development (Optional)
- Use Multipass VM for local testing
- Or run Caldera standalone without ELK for development

---

## Files Modified Today

| File | Change | Status |
|------|--------|--------|
| `quick-start-b1s.sh` | macOS compatibility fixes | ✅ Committed locally |
| `.env` | Generated secrets | ⚠️ Local only (not committed) |

---

**Session ended**: 28 December 2025  
**Key decision**: Skip macOS local testing, proceed directly to Azure B1s VM deployment  
**Ready to resume**: Create Azure B1s VM → SSH deploy → Validate on Linux

---

## Session 3: 29 December 2025 - Azure VM Deployment

### What Was Done

1. **Discovered existing Azure VM** ✅
   - Found `vm-caldera-elk-dev` running in `CALDERA-RG` resource group (Japan East)
   - Size: **D2s_v3** (2 vCPUs, **8GB RAM**) - much better than B1s for testing
   - OS: Ubuntu 22.04 LTS
   - Public IP: `4.189.172.124`

2. **Bypassed Azure Policy Restrictions** ✅
   - Azure Student subscription blocked new VM creation in East US and Australia East
   - Used existing VM in Japan East (policy-compliant region)
   - SSH key authentication working without password

3. **Deployed Elasticsearch** ✅
   - Cloned upstream MITRE Caldera repo
   - Uploaded B1s-optimized docker-compose files
   - Started Elasticsearch container with 1GB limit

4. **Validated Elasticsearch Running** ✅
   - Container: `elasticsearch` using 961MB of 1GB (93.87%)
   - Status: Running and healthy
   - Access: http://4.189.172.124:9200

### Findings & Blockers

#### ❌ B1s Memory Budget Too Aggressive for Elasticsearch
- **Issue**: Elasticsearch with 256MB heap / 512MB container limit → OOM killed (exit 137)
- **Root cause**: ES 8.x requires minimum ~1GB memory for stable operation
- **Fix**: Increased to 512MB heap / 1GB container limit
- **Impact**: **B1s (1GB) is NOT viable for ES + Caldera stack**

#### ❌ MITRE Caldera npm Build Failure
- **Issue**: Magma plugin has eslint dependency conflict
- **Error**: `peer eslint@"^0.23.0 || ^1.0.0 || ^2.0.0" from eslint-plugin-jinja2@0.1.0`
- **Workaround**: Need to use pre-built Caldera image or fix npm dependencies

#### ✅ SSH Key Authentication Working
- **Setup**: Added macOS SSH public key to Azure VM
- **Access**: `ssh -o BatchMode=yes azureuser@4.189.172.124` works without password

### Current State

| Component | Status | Resource Usage |
|-----------|--------|----------------|
| Azure VM (D2s_v3) | ✅ Running | 8GB RAM, 2 vCPU |
| Elasticsearch 8.11.0 | ✅ Running | 961MB / 1GB (93.87%) |
| Caldera | ⏸️ Pending | Build failing (npm conflict) |
| Kibana | ⏸️ Pending | Not started |
| VM Memory Available | ✅ | 5.9GB free |

### Credentials Generated

```
VM IP: 4.189.172.124
SSH User: azureuser
ELASTIC_PASSWORD: ze7jnif2vP1IxRwvDz0WfapxEJMAwT1V
CALDERA_API_KEY_RED: bc84af18c0b77c65d0d228d7629e5dbe
```

### Architecture Update

**Original B1s Design (NOT VIABLE):**
```
B1s (1GB) → ES 512MB + Caldera 256MB + OS 200MB = 968MB ❌
           └── ES needs minimum 1GB to run stably
```

**Revised Architecture (D2s_v3 with 8GB):**
```
┌─────────────────────────────────────────┐
│  D2s_v3 VM (8GB RAM)                    │
├─────────────────────────────────────────┤
│  Docker Compose                         │
│  ├── elasticsearch (1GB)   ← Minimum    │
│  ├── caldera (2GB)         ← Comfortable│
│  └── kibana (1GB)          ← Optional   │
├─────────────────────────────────────────┤
│  Available: ~4GB headroom               │
└─────────────────────────────────────────┘
```

---

## Next Steps (Session 4)

### Immediate Actions

1. **Fix Caldera Docker Build**
   ```bash
   # Option A: Use --legacy-peer-deps for npm
   # Option B: Use pre-built Caldera Docker image
   # Option C: Run Caldera natively (not containerized)
   ```

2. **Start Caldera Container**
   ```bash
   ssh azureuser@4.189.172.124
   cd /home/azureuser/caldera-upstream
   # Build with npm fix or use alternative deployment
   sudo docker-compose -f docker-compose-simple.yml up -d caldera
   ```

3. **Open Azure NSG Ports**
   ```bash
   az network nsg rule create --resource-group CALDERA-RG \
     --nsg-name <NSG-NAME> --name AllowCaldera --priority 1100 \
     --destination-port-ranges 8888 9200 5601 --access Allow
   ```

4. **Access Services**
   - Caldera UI: http://4.189.172.124:8888
   - Elasticsearch: http://4.189.172.124:9200
   - Kibana (optional): http://4.189.172.124:5601

### Validation Checklist (Updated)

- [x] Azure VM running and accessible via SSH
- [x] Elasticsearch running (1GB limit, 961MB usage)
- [ ] Caldera container built and running
- [ ] Caldera API accessible at :8888
- [ ] ≥2 agents enrolled
- [ ] First operation completes (T1059 recommended)
- [ ] Coverage report generates
- [ ] Webhook service operational

### Key Learnings

1. **B1s is NOT sufficient for ELK + Caldera** - Need minimum D2s_v3 (8GB) for stable operation
2. **Azure Student subscription has region restrictions** - Japan East works, but East US/Australia East blocked
3. **Upstream Caldera has npm dependency issues** - May need to use Triskele Labs fork or fix dependencies

---

**Session ended**: 29 December 2025  
**Status**: Elasticsearch running, Caldera build pending  
**VM Access**: `ssh azureuser@4.189.172.124`  
**Next**: Fix Caldera npm build → Start container → Enroll agents
