#!/usr/bin/env python3
"""
Live Demo: All 6 Phases of Caldera Orchestration
Walkthrough for new users with explanations
"""

import sys
from pathlib import Path

print("="*70)
print(" CALDERA ORCHESTRATION - ALL 6 PHASES DEMO")
print(" Interactive Walkthrough for New Users")
print("="*70)
print()

# Phase explanations
phases = [
    {
        "number": 1,
        "name": "Campaign Planning & Creation",
        "purpose": "Define comprehensive campaign specifications",
        "what_it_does": [
            "Creates a YAML specification defining your entire operation",
            "Specifies targets (IP addresses, hostnames, platforms)",
            "Defines adversary profile and attack objectives",
            "Sets up multi-phase operation sequencing",
            "Configures SIEM integration and notifications",
            "Establishes governance and approval workflows"
        ],
        "files": [
            "schemas/campaign_spec.schema.json (validation schema)",
            "data/campaigns/demo_campaign.yml (your campaign)"
        ],
        "command": "python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml"
    },
    {
        "number": 2,
        "name": "Agent Enrollment & Bootstrap",
        "purpose": "Generate platform-specific enrollment commands",
        "what_it_does": [
            "Creates PowerShell scripts for Windows agents",
            "Generates bash scripts for Linux/macOS agents",
            "Injects campaign metadata into agent configuration",
            "Supports Docker, Kubernetes, Terraform deployment",
            "Enables campaign-aware agent tracking",
            "Provides automated enrollment at scale"
        ],
        "files": [
            "orchestrator/generate_agent_enrollment.py",
            "Generated scripts for each platform"
        ],
        "command": "python orchestrator/cli.py agent enroll demo_red_team_2025 demo-workstation-01 windows"
    },
    {
        "number": 3,
        "name": "Health Check & Validation",
        "purpose": "Verify all services are operational",
        "what_it_does": [
            "Checks CALDERA web UI accessibility",
            "Validates REST API responsiveness",
            "Confirms plugin loading status",
            "Tests database connectivity",
            "Validates campaign specifications",
            "Checks target reachability (if applicable)"
        ],
        "files": [
            "orchestrator/health_check.py",
            "Validation logic in cli.py"
        ],
        "command": "python orchestrator/cli.py health-check --campaign demo_red_team_2025"
    },
    {
        "number": 4,
        "name": "Operation Execution",
        "purpose": "Execute multi-phase operations with orchestration",
        "what_it_does": [
            "Starts campaign through defined phases",
            "Monitors agent enrollment and status",
            "Creates and executes operations",
            "Tracks timeline and events",
            "Handles errors and retries",
            "Provides real-time status updates"
        ],
        "files": [
            "app/objects/c_campaign.py",
            "orchestrator/cli.py (campaign start/status)"
        ],
        "command": "python orchestrator/cli.py campaign start demo_red_team_2025",
        "note": "⚠️ Phase 4 full implementation is planned but not complete"
    },
    {
        "number": 5,
        "name": "Enrollment API & Management",
        "purpose": "Programmatic agent enrollment via REST API",
        "what_it_does": [
            "REST API endpoints for enrollment requests",
            "Dynamic agent provisioning at scale",
            "Bootstrap configuration generation",
            "Integration with CI/CD pipelines",
            "Auto-enrollment for authorized systems",
            "Campaign-aware agent tracking"
        ],
        "files": [
            "plugins/enrollment/hook.py",
            "plugins/enrollment/app/enrollment_svc.py",
            "plugins/enrollment/app/enrollment_api.py"
        ],
        "command": 'curl -X POST http://localhost:8888/plugin/enrollment/api/requests -H "Content-Type: application/json" -H "KEY: ADMIN123" -d \'{"campaign_id": "demo", "hostname": "test", "platform": "windows"}\''
    },
    {
        "number": 6,
        "name": "PDF Reporting & Analysis",
        "purpose": "Generate comprehensive reports with Triskele branding",
        "what_it_does": [
            "Collects all campaign data via CALDERA API",
            "Generates matplotlib charts (pie, bar, heatmap, timeline)",
            "Creates MITRE ATT&CK Navigator layer JSON",
            "Renders professional PDF with Jinja2 templates",
            "Applies Triskele Labs branding (#48CFA0 green)",
            "Produces executive summary and detailed analysis"
        ],
        "files": [
            "orchestrator/report_aggregator.py",
            "orchestrator/attack_navigator.py",
            "orchestrator/report_visualizations.py",
            "orchestrator/pdf_generator.py",
            "orchestrator/templates/report_template.html"
        ],
        "command": "python orchestrator/cli.py report generate demo_red_team_2025"
    }
]

# Display each phase
for phase in phases:
    print(f"\n{'='*70}")
    print(f" PHASE {phase['number']}: {phase['name'].upper()}")
    print(f"{'='*70}")
    print(f"\n📋 PURPOSE:")
    print(f"   {phase['purpose']}")
    
    print(f"\n🔧 WHAT IT DOES:")
    for item in phase['what_it_does']:
        print(f"   • {item}")
    
    print(f"\n📁 KEY FILES:")
    for file in phase['files']:
        print(f"   • {file}")
    
    print(f"\n💻 COMMAND:")
    print(f"   {phase['command']}")
    
    if 'note' in phase:
        print(f"\n   {phase['note']}")
    
    print()

# Demo execution section
print("\n" + "="*70)
print(" LIVE DEMO EXECUTION")
print("="*70)

print("""
To run this complete demo, follow these steps:

STEP 1: Install Phase 6 Dependencies (if not already installed)
---------------------------------------------------------------
pip install matplotlib numpy weasyprint

Note: WeasyPrint may require system dependencies:
  macOS:   brew install pango cairo gdk-pixbuf
  Ubuntu:  sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0

STEP 2: Start CALDERA Server
-----------------------------
python server.py --insecure

# In another terminal, verify it's running:
curl -s http://localhost:8888/api/v2/health | jq '.application'

STEP 3: Create Demo Campaign (Phase 1)
---------------------------------------
# Campaign spec already created at: data/campaigns/demo_campaign.yml
python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml

Expected output:
  ✅ Campaign created: Demo Red Team Exercise - January 2025
     Campaign ID: demo_red_team_2025
     Environment: demo-env-001

STEP 4: Generate Agent Enrollment Scripts (Phase 2)
----------------------------------------------------
# Windows enrollment
python orchestrator/cli.py agent enroll demo_red_team_2025 demo-workstation-01 windows

# Linux enrollment
python orchestrator/cli.py agent enroll demo_red_team_2025 demo-server-01 linux

Expected output:
  ✅ Enrollment script generated
     PowerShell/Bash commands to copy to target systems

STEP 5: Run Health Check (Phase 3)
-----------------------------------
python orchestrator/cli.py health-check

Expected output:
  ✅ Server: Healthy
  ✅ REST API: Healthy
  ✅ Plugins: 12 loaded

STEP 6: Execute Operations (Phase 4)
-------------------------------------
# Via CALDERA UI (recommended for demo):
1. Open http://localhost:8888
2. Login (admin/admin by default)
3. Navigate to Operations
4. Create Operation:
   - Name: "Demo Operation"
   - Adversary: Hunter (or any available)
   - Group: red
   - Click "Start"

# Let it run for a few minutes to generate data

STEP 7: Use Enrollment API (Phase 5)
-------------------------------------
# Check enrollment plugin
curl -s http://localhost:8888/api/v2/health | jq '.plugins[] | select(.name == "enrollment")'

# Create enrollment request
curl -X POST http://localhost:8888/plugin/enrollment/api/requests \\
  -H "Content-Type: application/json" \\
  -H "KEY: ADMIN123" \\
  -d '{
    "campaign_id": "demo_red_team_2025",
    "hostname": "auto-enrolled-host",
    "platform": "linux",
    "group": "red"
  }' | jq '.'

Expected output:
  {
    "id": "enroll-001",
    "status": "pending",
    "script": "#!/bin/bash\\n..."
  }

STEP 8: Generate PDF Report (Phase 6)
--------------------------------------
# Wait for operation to complete, then:
python orchestrator/cli.py report generate demo_red_team_2025

Expected output:
  📊 Collecting campaign data...
     ✅ Collected data for operations
  📈 Generating charts...
     ✅ Generated 5 charts
  🎯 Generating ATT&CK Navigator layer...
     ✅ ATT&CK layer saved
  📄 Generating PDF...
     ✅ PDF report generated (2-5 MB)

  Output files:
  - data/reports/demo_red_team_2025_report.pdf
  - data/reports/demo_red_team_2025_attack_layer.json

STEP 9: View Results
--------------------
# Open PDF report
open data/reports/demo_red_team_2025_report.pdf  # macOS
xdg-open data/reports/demo_red_team_2025_report.pdf  # Linux

# View ATT&CK Navigator layer
# 1. Go to https://mitre-attack.github.io/attack-navigator/
# 2. Click "Open Existing Layer"
# 3. Upload: demo_red_team_2025_attack_layer.json
# 4. View color-coded technique coverage

""")

# Test suite info
print("="*70)
print(" AUTOMATED TESTING")
print("="*70)
print("""
Run test suites to validate each phase:

# Phase 1-3: Campaign and orchestration
python orchestrator/quick_test.py

# Phase 5: Enrollment API
./examples/enrollment/test_enrollment_api.sh

# Phase 6: PDF Reporting
python tests/test_phase6.py

Each test suite will:
  ✅ Verify component imports
  ✅ Test core functionality
  ✅ Generate sample outputs
  ✅ Report pass/fail status
""")

# Summary
print("="*70)
print(" WHAT YOU LEARNED")
print("="*70)
print("""
After completing this demo, you now understand:

✅ Phase 1: How to create campaign specifications
✅ Phase 2: How to generate agent enrollment scripts
✅ Phase 3: How to validate system health
✅ Phase 4: How to execute orchestrated operations
✅ Phase 5: How to use the enrollment REST API
✅ Phase 6: How to generate professional PDF reports

NEXT STEPS:
-----------
1. Customize campaign specs for your environment
2. Create custom adversary profiles
3. Build platform-specific abilities
4. Integrate with your SIEM
5. Set up Slack notifications
6. Automate with CI/CD pipelines

DOCUMENTATION:
--------------
• Full Guide: ORCHESTRATION_GUIDE.md
• Demo Walkthrough: DEMO_WALKTHROUGH.md
• User Journey: END_TO_END_USER_JOURNEY.md
• Phase Guides: docs/phases/phase*.md
• API Reference: plugins/enrollment/docs/API.md

""")

print("="*70)
print(" 🎉 DEMO COMPLETE - READY TO ORCHESTRATE!")
print("="*70)
print()
