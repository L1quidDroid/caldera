# End-to-End User Journey: Caldera Global Orchestration Pattern

**Date:** December 16, 2025  
**Status:** Phase 1-5 Implementation Complete, Testing In Progress  
**Estimated Time:** 30-45 minutes for complete workflow

---

## ⚠️ Testing Status

**✅ Verified Components:**
- Campaign specification schema and YAML files
- Orchestrator CLI code structure
- Enrollment API plugin code structure  
- Documentation complete for all phases
- Test suite created with 50+ validation cases

**🔧 Known Issues Requiring Fixes:**
1. **Server startup**: May encounter plugin loading errors on first start
   - `emu` plugin tries to clone repository (requires internet)
   - `debrief` plugin requires `reportlab` library
   - **Fix**: Comment out optional plugins or install dependencies

2. **API health endpoint**: `/api/v2/health` returns 500 error
   - May be related to plugin loading issues
   - **Workaround**: Use plugin-specific health checks

3. **Virtual environment**: Ensure using Python 3.10-3.12 (not 3.13)
   - Some dependencies may have compatibility issues with Python 3.13

**📝 Recommendation:**
This guide provides the complete end-to-end workflow. Some steps may need adjustment based on your environment. Follow troubleshooting sections for common issues.

---

## Overview

This guide walks through the complete user journey from initial setup to running a full adversary emulation campaign using the Global Orchestration Pattern with all Phase 1-5 features.

---

## Prerequisites

- **System Requirements:**
  - macOS or Linux
  - Python 3.10+
  - Node.js v16+ (for Magma UI)
  - 8GB+ RAM, 2+ CPUs
  - Git installed

- **Network Requirements:**
  - Port 8888 available for CALDERA server
  - Internet access for initial setup (package installation)

---

## Phase 1: Initial Setup & Validation

### Step 1.1: Clone and Install CALDERA

```bash
# Navigate to your projects directory
cd ~/Documents/GitHub/

# Clone the repository (if not already done)
git clone https://github.com/L1quidDroid/caldera.git --recursive
cd caldera

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r orchestrator/requirements.txt
```

**Expected Result:** Virtual environment created, all packages installed without errors.

---

### Step 1.2: Configure Plugins

The following plugins should be enabled in `conf/default.yml`:

```yaml
plugins:
- access
- atomic
- builder
- compass
# - debrief  # Optional: requires reportlab (pip install reportlab)
# - emu      # Optional: downloads adversary emulation library on first start
- enrollment
- fieldmanual
- gameboard
- magma
- manx
- response
- sandcat
- stockpile
- training
- branding
- orchestrator
```

**Note:** 
- `debrief` plugin requires `reportlab` library: `pip install reportlab`
- `emu` plugin downloads MITRE adversary emulation library on first start (requires internet)
- For minimal setup, you can comment out `debrief` and `emu` initially

**Verification:**
```bash
grep -A 20 "plugins:" conf/default.yml
```

---

### Step 1.3: Start CALDERA Server

```bash
# Start server with insecure mode for local testing
python3 server.py --insecure --build
```

**Expected Output:**
```
2025-12-16 10:00:00 - INFO - (app.py:starting) All systems ready.
2025-12-16 10:00:00 - INFO - (server.py) Server started on http://0.0.0.0:8888
```

**Wait for:** "All systems ready" message (takes ~30-60 seconds on first start with --build)

---

### Step 1.4: Verify Web UI Access

**In a new terminal tab:**
```bash
# Test web UI access
curl -s http://localhost:8888 | grep -i caldera
```

**Browser Access:**
1. Open browser: http://localhost:8888
2. Login credentials:
   - Red team: `red` / `admin`
   - Blue team: `blue` / `admin`
   - Admin: `admin` / `admin`

**Expected Result:** CALDERA UI loads with purple theme and custom navigation showing team indicator badge.

---

### Step 1.5: Run Health Check (Phase 1)

**In a new terminal (keep server running):**
```bash
cd ~/Documents/GitHub/Triskele\ Labs/caldera
source venv/bin/activate

# Run comprehensive health check
python3 orchestrator/health_check.py --url=http://localhost:8888 --api-key-red=ADMIN123
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════╗
║          CALDERA HEALTH CHECK - PHASE 1                   ║
╚═══════════════════════════════════════════════════════════╝

✅ Web UI is accessible
✅ REST API v2 is responding
✅ Red team API key is valid
✅ 17 plugins loaded: access, atomic, builder, compass, debrief, emu, enrollment, ...
✅ 0 agents currently connected
✅ 50+ adversaries available
✅ 500+ abilities available

Health Check: PASSED ✅
```

**Troubleshooting:**
- If plugins missing: Check `conf/default.yml` plugins list
- If API key invalid: Verify `api_key_red: ADMIN123` in config
- If port conflict: Change port in `conf/default.yml`

---

## Phase 2: Campaign Creation & Agent Automation

### Step 2.1: Review Campaign Specification

**Examine the example campaign spec:**
```bash
cat orchestrator/schemas/campaign_spec_example.yml
```

**Key sections to understand:**
- `environment`: CALDERA URL, API keys, infrastructure
- `targets`: Agent groups, platforms, tags
- `adversary`: Adversary ID, planner, techniques
- `siem`: SIEM integration settings
- `notifications`: Slack, webhooks
- `governance`: Approvals, scheduling, compliance

---

### Step 2.2: Create Custom Campaign Specification

```bash
# Copy example spec
cp orchestrator/schemas/campaign_spec_example.yml my_test_campaign.yml

# Edit for local testing
nano my_test_campaign.yml
```

**Minimal configuration for local testing:**
```yaml
campaign_id: "test-campaign-001"
name: "Local Test Campaign"
description: "Testing Phase 1-5 orchestration features"

environment:
  environment_id: "local-test-001"
  type: "test"
  caldera_url: "http://localhost:8888"
  api_key_red: "ADMIN123"

mode: "test"

targets:
  agent_groups: ["test_agents"]
  platforms: ["darwin"]  # macOS for local testing
  tags:
    test_run_id: "test-001"
    environment: "local"

adversary:
  adversary_id: "de07f52d-9928-4071-9142-cb1d437b4502"  # Collection adversary
  name: "Local Test Adversary"
  planner: "atomic"

siem:
  enabled: false

notifications:
  slack:
    enabled: false

governance:
  owner: "test@local.dev"
  approval_status: "approved"
  max_duration_hours: 1

state:
  status: "created"
  current_phase: 1
  operations: []
  agents_enrolled: []
  reports: {}
  errors: []
  timeline: []
```

---

### Step 2.3: Create Campaign via CLI

```bash
# Create campaign from spec
python3 orchestrator/cli.py campaign create my_test_campaign.yml
```

**Expected Output:**
```
✅ Campaign created: Local Test Campaign
   Campaign ID: test-campaign-001
   Environment: local-test-001
   Mode: test
   Spec saved: data/campaigns/test-campaign-001.yml
```

**Verification:**
```bash
# Verify campaign file created
ls -la data/campaigns/test-campaign-001.yml

# Check campaign status
python3 orchestrator/cli.py campaign status test-campaign-001
```

---

### Step 2.4: Generate Agent Enrollment Scripts (CLI Method)

**Option A: Windows PowerShell script**
```bash
python3 orchestrator/generate_agent_enrollment.py \
  --campaign=test-campaign-001 \
  --platform=windows \
  --output=enroll_windows.ps1
```

**Option B: Linux/macOS bash script**
```bash
python3 orchestrator/generate_agent_enrollment.py \
  --campaign=test-campaign-001 \
  --platform=darwin \
  --output=enroll_macos.sh
```

**Expected Output:**
```
✅ Enrollment script generated: enroll_macos.sh
   Platform: darwin
   Campaign ID: test-campaign-001
   Server: http://localhost:8888
   Tags: test_run_id=test-001, environment=local
```

**View generated script:**
```bash
cat enroll_macos.sh
```

---

## Phase 3: Webhook Publisher & SIEM Integration

### Step 3.1: Verify Orchestrator Plugin Loaded

```bash
# Check if orchestrator plugin is active
curl -s http://localhost:8888/api/v2/plugins | jq '.[] | select(.name=="orchestrator")'
```

**Expected Output:**
```json
{
  "name": "orchestrator",
  "enabled": true,
  "description": "Campaign orchestration and webhook publishing"
}
```

---

### Step 3.2: Register Test Webhook

```bash
# Register a webhook for testing (webhook.site for testing)
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://webhook.site/your-unique-id",
    "exchanges": ["operations"],
    "queues": ["*"]
  }'
```

**Alternative: Local webhook listener**
```bash
# In a separate terminal, start a simple webhook listener
python3 -m http.server 9000
```

Then register local webhook:
```bash
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:9000/webhook",
    "exchanges": ["operations"],
    "queues": ["*"]
  }'
```

---

### Step 3.3: List Registered Webhooks

```bash
curl -s http://localhost:8888/plugin/orchestrator/webhooks | jq '.'
```

**Expected Output:**
```json
[
  {
    "url": "http://localhost:9000/webhook",
    "exchanges": ["operations"],
    "queues": ["*"],
    "stats": {
      "sent": 0,
      "failed": 0
    }
  }
]
```

---

## Phase 5: Enrollment API Plugin

### Step 5.1: Verify Enrollment Plugin Health

```bash
# Check enrollment plugin health (no auth required for health endpoint)
curl -s http://localhost:8888/plugin/enrollment/health | jq '.'
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "enrollment",
  "version": "1.0.0",
  "storage_path": "/path/to/plugins/enrollment/data/enrollment_requests.json",
  "requests_count": 0,
  "caldera_url": "http://localhost:8888"
}
```

**Troubleshooting:**
If you get 404, the enrollment plugin may not be loaded:
```bash
# Check server logs
tail -f logs/caldera.log | grep -i enrollment

# Verify plugin is in config
grep enrollment conf/default.yml

# Restart server if needed
```

---

### Step 5.2: Create Enrollment Request via API

```bash
# Create enrollment for macOS agent
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "darwin",
    "campaign_id": "test-campaign-001",
    "tags": ["local-test", "phase5"],
    "hostname": "my-macbook",
    "description": "Testing Phase 5 enrollment API"
  }' | jq '.'
```

**Expected Output:**
```json
{
  "id": "enroll_abc123def456",
  "status": "pending",
  "platform": "darwin",
  "campaign_id": "test-campaign-001",
  "tags": ["local-test", "phase5"],
  "hostname": "my-macbook",
  "created_at": "2025-12-16T10:30:00Z",
  "bootstrap_command": "server='http://localhost:8888';curl -s -X POST -H \"file:sandcat.go\" -H \"platform:darwin\" $server/file/download > sandcat.go && chmod +x sandcat.go && ./sandcat.go -server $server -group test_agents -v -tags local-test,phase5,campaign_id:test-campaign-001,test_run_id:test-001,environment:local"
}
```

**Save the enrollment ID and bootstrap command for next step.**

---

### Step 5.3: Execute Bootstrap Command

**Copy the `bootstrap_command` from the response and execute it:**

```bash
# Execute the bootstrap command (this will start the agent)
server='http://localhost:8888';curl -s -X POST -H "file:sandcat.go" -H "platform:darwin" $server/file/download > sandcat.go && chmod +x sandcat.go && ./sandcat.go -server $server -group test_agents -v -tags local-test,phase5,campaign_id:test-campaign-001,test_run_id:test-001,environment:local
```

**Expected Output:**
```
[sandcat] Starting sandcat agent
[sandcat] Server: http://localhost:8888
[sandcat] Group: test_agents
[sandcat] Platform: darwin
[sandcat] Beacon interval: 60s
[sandcat] Checking in with server...
```

**Keep this terminal open - the agent is now running!**

---

### Step 5.4: Verify Agent Registration

**In a new terminal:**
```bash
# Check agents via CALDERA API
curl -s http://localhost:8888/api/v2/agents | jq '.[] | {paw, hostname, platform, group, tags}'
```

**Expected Output:**
```json
{
  "paw": "abc123",
  "hostname": "my-macbook",
  "platform": "darwin",
  "group": "test_agents",
  "tags": ["local-test", "phase5", "campaign_id:test-campaign-001", "test_run_id:test-001", "environment:local"]
}
```

---

### Step 5.5: Check Enrollment Status

```bash
# Get enrollment status using the enrollment ID
curl -s http://localhost:8888/plugin/enrollment/enroll/enroll_abc123def456 | jq '.'
```

**Expected Output:**
```json
{
  "id": "enroll_abc123def456",
  "status": "completed",
  "platform": "darwin",
  "campaign_id": "test-campaign-001",
  "agent_paw": "abc123",
  "completed_at": "2025-12-16T10:32:00Z"
}
```

---

### Step 5.6: List Campaign Agents

```bash
# List all agents for the campaign
curl -s http://localhost:8888/plugin/enrollment/campaigns/test-campaign-001/agents | jq '.'
```

**Expected Output:**
```json
{
  "campaign_id": "test-campaign-001",
  "agent_count": 1,
  "agents": [
    {
      "paw": "abc123",
      "hostname": "my-macbook",
      "platform": "darwin",
      "group": "test_agents",
      "last_seen": "2025-12-16T10:32:00Z"
    }
  ]
}
```

---

## Phase 4: Campaign Execution

### Step 4.1: Start Campaign Operation

```bash
# Start the campaign
python3 orchestrator/cli.py campaign start test-campaign-001
```

**Expected Output:**
```
Starting campaign: test-campaign-001
Mode: test (auto-approved)

Creating operation...
✅ Operation created: op_xyz789
✅ Operation started with 1 agent(s)

Campaign started successfully.
Monitor progress: python3 orchestrator/cli.py campaign status test-campaign-001 --verbose
```

---

### Step 4.2: Monitor Campaign Progress

```bash
# Check campaign status with verbose output
python3 orchestrator/cli.py campaign status test-campaign-001 --verbose
```

**Expected Output:**
```
Campaign: Local Test Campaign (test-campaign-001)
Status: running
Mode: test
Environment: local-test-001

Operations:
- op_xyz789 (running)
  - Started: 2025-12-16 10:35:00
  - Agents: 1
  - Abilities executed: 5

Agents Enrolled: 1
- abc123 (my-macbook, darwin)

Timeline:
- 2025-12-16 10:30:00: campaign_created
- 2025-12-16 10:32:00: agent_enrolled (abc123)
- 2025-12-16 10:35:00: operation_started (op_xyz789)
```

---

### Step 4.3: Monitor via Web UI

1. Open browser: http://localhost:8888
2. Login as `red` / `admin`
3. Navigate to **Operations** tab
4. You should see your operation running with the test agent
5. Click on the operation to view:
   - Agents participating
   - Abilities being executed
   - Results and output
   - ATT&CK technique coverage

**UI Features (Phase 1 Navigation):**
- Purple-themed navigation with semantic icons
- Team indicator badge showing "RED TEAM"
- Hover effects and active state highlighting
- Keyboard navigation support

---

### Step 4.4: Check Webhook Events

**If you set up a webhook listener:**
```bash
# Check webhook listener logs (in the terminal running python3 -m http.server 9000)
# You should see POST requests with operation events
```

**Expected webhook payload:**
```json
{
  "exchange": "operations",
  "queue": "created",
  "timestamp": "2025-12-16T10:35:00Z",
  "data": {
    "id": "op_xyz789",
    "name": "test-campaign-001-operation",
    "adversary": "de07f52d-9928-4071-9142-cb1d437b4502",
    "state": "running"
  }
}
```

---

## Phase 5: Testing & Validation

### Step 5.1: Run Phase 5 Test Suite

```bash
# Run comprehensive Phase 5 requirements test
python3 tests/test_phase5_requirements.py
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════════╗
║         PHASE 5 ENROLLMENT API - REQUIREMENTS VALIDATION       ║
╚═══════════════════════════════════════════════════════════════╝

✅ Requirement 1: Plugin Structure & Integration (5/5 tests passed)
✅ Requirement 2: REST API Endpoints (7/7 tests passed)
✅ Requirement 3: JSON Persistent Storage (4/4 tests passed)
✅ Requirement 4: Platform-Specific Bootstrap (4/4 tests passed)
✅ Requirement 5: Environment Configuration (4/4 tests passed)
✅ Requirement 6: Testing Examples (4/4 tests passed)
✅ Requirement 7: Documentation (4/4 tests passed)
✅ Requirement 8: CLI/API Separation (3/3 tests passed)

════════════════════════════════════════════════════════════════
✅ ALL PHASE 5 REQUIREMENTS MET (35/35 tests passed)
════════════════════════════════════════════════════════════════
```

---

### Step 5.2: Test Enrollment API Examples

**Bash test script:**
```bash
cd examples/enrollment
./test_enrollment_api.sh
```

**Python client example:**
```bash
cd examples/enrollment
python3 enroll_from_python.py
```

**Expected:** Both examples complete successfully with agent enrollment.

---

## Complete Workflow Summary

### What You've Accomplished:

✅ **Phase 1: Infrastructure & Validation**
- Installed and configured CALDERA with all plugins
- Verified health check passes
- Confirmed Web UI access with custom purple theme

✅ **Phase 2: Campaign Management**
- Created campaign specification (YAML)
- Generated campaign via CLI
- Generated platform-specific enrollment scripts

✅ **Phase 3: External Integration**
- Registered webhook for event notifications
- Verified webhook publisher is operational

✅ **Phase 5: Dynamic Enrollment**
- Created enrollment request via REST API
- Executed bootstrap command
- Agent registered and checked in
- Verified campaign-agent association

✅ **Phase 4: Operation Execution**
- Started campaign operation
- Monitored via CLI and Web UI
- Observed abilities executing on agent

---

## Cleanup

### Stop Running Processes

```bash
# Stop the agent (Ctrl+C in agent terminal)
# Stop the CALDERA server (Ctrl+C in server terminal)

# Remove test campaign data
rm -f data/campaigns/test-campaign-001.yml
rm -f my_test_campaign.yml
rm -f enroll_macos.sh
rm -f sandcat.go

# Clear enrollment data (optional)
rm -f plugins/enrollment/data/enrollment_requests.json
```

---

## Troubleshooting

### Issue: Server won't start

**Common Causes:**
1. Port 8888 already in use
2. Plugin dependencies missing
3. Python version incompatibility

**Solution:**
```bash
# Check port availability
lsof -i :8888

# Kill existing process if needed
kill -9 <PID>

# Check Python version (use 3.10-3.12, not 3.13)
python3 --version

# Install missing dependencies
pip install reportlab  # For debrief plugin

# Start with minimal plugins first
# Edit conf/default.yml and comment out: emu, debrief, builder

# Check logs for specific errors
tail -f logs/caldera.log
```

### Issue: Plugins not loading

**Solution:**
```bash
# Verify plugin directory structure
ls -la plugins/enrollment/
ls -la plugins/enrollment/app/

# Check if __init__.py files exist
find plugins/enrollment -name "__init__.py"

# Restart server with fresh build
python3 server.py --insecure --fresh

# Check plugin list in config
grep -A 20 "plugins:" conf/default.yml
```

---

### Issue: Agent won't connect

**Solution:**
```bash
# Verify server URL is correct
curl http://localhost:8888/api/v2/health

# Check firewall settings
# Ensure agent can reach server on port 8888

# Run agent with verbose logging
./sandcat.go -server http://localhost:8888 -group test_agents -v
```

---

### Issue: Enrollment API returns 500 error

**Solution:**
```bash
# Check enrollment plugin is loaded
curl http://localhost:8888/api/v2/plugins | grep enrollment

# Check enrollment data directory exists
mkdir -p plugins/enrollment/data

# Check server logs for errors
tail -f logs/caldera.log
```

---

### Issue: Health check fails

**Solution:**
```bash
# Verify API key matches config
grep api_key_red conf/default.yml

# Check all plugins loaded
curl -s http://localhost:8888/api/v2/plugins | jq '.[] | .name'

# Restart server with --fresh flag to rebuild
python3 server.py --insecure --fresh
```

---

## Next Steps

### Explore Advanced Features:

1. **SIEM Integration:**
   - Enable Elasticsearch or Splunk in campaign spec
   - Configure SIEM tags for automatic event enrichment

2. **PDF Reporting (Phase 6 - Planned):**
   - Generate comprehensive campaign reports
   - ATT&CK Navigator visualizations

3. **Slack Integration (Phase 7 - Planned):**
   - Real-time notifications to Slack channels
   - Interactive bot commands

4. **CI/CD Integration:**
   - Use Enrollment API in GitHub Actions
   - Automate agent deployment in pipelines

5. **Custom Adversaries:**
   - Build custom adversary profiles
   - Test specific threat scenarios

---

## Resources

- **Documentation:** `/docs/README.md`
- **Orchestration Guide:** `ORCHESTRATION_GUIDE.md`
- **Enrollment API:** `plugins/enrollment/docs/README.md`
- **API Reference:** `plugins/enrollment/docs/API.md`
- **Test Suite:** `tests/test_phase5_requirements.py`
- **Examples:** `examples/enrollment/`

---

## Success Metrics

By completing this journey, you've successfully:

- ✅ Set up a complete CALDERA orchestration environment
- ✅ Created and managed campaigns as code
- ✅ Deployed agents using both CLI and API methods
- ✅ Integrated external systems via webhooks
- ✅ Executed adversary emulation operations
- ✅ Validated all Phase 1-5 requirements

**Total Time:** ~30-45 minutes  
**Skills Gained:** Campaign orchestration, agent automation, API integration, purple team operations

---

**End of User Journey**
