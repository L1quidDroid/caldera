# Caldera Orchestration - Quick Reference Card

## 🎯 All 6 Phases At-A-Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: CAMPAIGN PLANNING                       │
├─────────────────────────────────────────────────────────────────────┤
│ PURPOSE: Define comprehensive campaign specification                │
│ COMMAND: python orchestrator/cli.py campaign create <spec.yml>      │
│ OUTPUT:  Campaign ID, saved specification                           │
│ FILES:   data/campaigns/<campaign_id>.yml                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                  PHASE 2: AGENT ENROLLMENT                          │
├─────────────────────────────────────────────────────────────────────┤
│ PURPOSE: Generate platform-specific enrollment scripts              │
│ COMMAND: python orchestrator/cli.py agent enroll <id> <host> <os>  │
│ OUTPUT:  PowerShell (Windows) or Bash (Linux) enrollment commands  │
│ PLATFORMS: windows, linux, darwin, docker                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                 PHASE 3: HEALTH VALIDATION                          │
├─────────────────────────────────────────────────────────────────────┤
│ PURPOSE: Verify all CALDERA services are operational                │
│ COMMAND: python orchestrator/cli.py health-check                    │
│ CHECKS:  Server, REST API, Plugins, Database, Campaign              │
│ OUTPUT:  Health status table with pass/fail indicators              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│               PHASE 4: OPERATION EXECUTION                          │
├─────────────────────────────────────────────────────────────────────┤
│ PURPOSE: Execute multi-phase operations with orchestration           │
│ COMMAND: python orchestrator/cli.py campaign start <campaign_id>    │
│ STATUS:  python orchestrator/cli.py campaign status <campaign_id>   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                PHASE 5: ENROLLMENT API                              │
├─────────────────────────────────────────────────────────────────────┤
│ PURPOSE: Programmatic agent enrollment via REST API                 │
│ ENDPOINT: POST /plugin/enrollment/api/requests                      │
│ AUTH:    Header "KEY: ADMIN123"                                     │
│ BODY:    {"campaign_id", "hostname", "platform", "group"}          │
│ OUTPUT:  Enrollment request with generated script                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 6: PDF REPORTING                                 │
├─────────────────────────────────────────────────────────────────────┤
│ PURPOSE: Generate comprehensive PDF reports with Triskele branding  │
│ COMMAND: python orchestrator/cli.py report generate <campaign_id>   │
│ OUTPUT:  PDF report + ATT&CK Navigator layer JSON                   │
│ FILES:   data/reports/<campaign_id>_report.pdf                     │
│          data/reports/<campaign_id>_attack_layer.json              │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Command Cheat Sheet

### Campaign Management
```bash
# Create campaign
python orchestrator/cli.py campaign create data/campaigns/my_campaign.yml

# Start campaign
python orchestrator/cli.py campaign start my_campaign_id

# Check status
python orchestrator/cli.py campaign status my_campaign_id --verbose

# Stop campaign
python orchestrator/cli.py campaign stop my_campaign_id
```

### Agent Enrollment
```bash
# Generate Windows enrollment
python orchestrator/cli.py agent enroll my_campaign workstation-01 windows

# Generate Linux enrollment
python orchestrator/cli.py agent enroll my_campaign server-01 linux
```

### Health Checks
```bash
# Basic health check
python orchestrator/cli.py health-check

# Campaign-specific check
python orchestrator/cli.py health-check --campaign my_campaign_id
```

### Enrollment API (Phase 5)
```bash
# Create enrollment request
curl -X POST http://localhost:8888/plugin/enrollment/api/requests \
  -H "Content-Type: application/json" \
  -H "KEY: ADMIN123" \
  -d '{"campaign_id": "test", "hostname": "host1", "platform": "linux"}'

# List requests
curl -H "KEY: ADMIN123" \
  http://localhost:8888/plugin/enrollment/api/requests

# Get specific request
curl -H "KEY: ADMIN123" \
  http://localhost:8888/plugin/enrollment/api/requests/<request_id>
```

### Report Generation (Phase 6)
```bash
# Generate PDF report
python orchestrator/cli.py report generate my_campaign_id

# Generate with options
python orchestrator/cli.py report generate my_campaign_id \
  --format pdf \
  --output /path/to/report.pdf \
  --include-output \
  --no-attack-layer

# Generate JSON export
python orchestrator/cli.py report generate my_campaign_id --format json
```

## 🔧 Dependencies

### Core (Already Installed)
- Python 3.8+
- aiohttp
- jinja2
- pyyaml

### Phase 6 PDF Reporting (Install if needed)
```bash
pip install matplotlib numpy weasyprint

# macOS system dependencies
brew install pango cairo gdk-pixbuf

# Ubuntu system dependencies
sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
```

## 📁 Key Files & Directories

```
caldera/
├── orchestrator/
│   ├── cli.py                      # Main CLI interface
│   ├── report_aggregator.py        # Data collection (Phase 6)
│   ├── attack_navigator.py         # ATT&CK layers (Phase 6)
│   ├── report_visualizations.py    # Charts (Phase 6)
│   ├── pdf_generator.py            # PDF engine (Phase 6)
│   └── templates/
│       └── report_template.html    # Report template (Phase 6)
│
├── plugins/
│   └── enrollment/                 # Enrollment API (Phase 5)
│       ├── hook.py
│       └── app/
│           ├── enrollment_svc.py
│           └── enrollment_api.py
│
├── data/
│   ├── campaigns/                  # Campaign specs (Phase 1)
│   └── reports/                    # Generated reports (Phase 6)
│
└── docs/
    ├── ORCHESTRATION_GUIDE.md      # Full documentation
    ├── DEMO_WALKTHROUGH.md         # Step-by-step demo
    ├── END_TO_END_USER_JOURNEY.md  # User workflow guide
    └── phases/
        ├── phase5-enrollment.md    # Phase 5 docs
        └── phase6-pdf-reporting.md # Phase 6 docs
```

## 🎯 Typical Workflow

1. **Plan** (Phase 1): Create campaign specification
2. **Enroll** (Phase 2): Generate enrollment scripts for targets
3. **Validate** (Phase 3): Run health checks
4. **Execute** (Phase 4): Run operations via UI or API
5. **Scale** (Phase 5): Use API for dynamic enrollment
6. **Report** (Phase 6): Generate PDF reports and ATT&CK layers

## 📊 Report Contents (Phase 6)

Your PDF report includes:
- ✅ Cover page with Triskele Labs branding
- ✅ Executive summary with key metrics
- ✅ Operations overview table
- ✅ ATT&CK technique coverage (color-coded)
- ✅ Agent deployment details
- ✅ Timeline visualization
- ✅ Error analysis
- ✅ 5+ charts (pie, bar, heatmap, timeline)

## 🔗 Resources

- **Documentation**: `ORCHESTRATION_GUIDE.md`
- **Demo**: `DEMO_WALKTHROUGH.md` or run `python demo_all_phases.py`
- **API Reference**: `plugins/enrollment/docs/API.md`
- **ATT&CK Navigator**: https://mitre-attack.github.io/attack-navigator/
- **CALDERA Docs**: https://caldera.readthedocs.io/

## 💡 Tips

- Always run `health-check` before starting operations
- Use `--verbose` flag for detailed status output
- Test in `mode: test` before `mode: production`
- Generate reports after operations complete
- Upload ATT&CK layers to Navigator for visualization
- Keep campaign specs in version control

## 🆘 Troubleshooting

```bash
# CALDERA not running
python server.py --insecure

# Import errors
pip install -r requirements.txt

# CLI not found
export PYTHONPATH="$PWD:$PYTHONPATH"

# Phase 6 dependencies missing
pip install matplotlib numpy weasyprint
brew install pango cairo gdk-pixbuf  # macOS

# Check plugin status
curl -s http://localhost:8888/api/v2/health | jq '.plugins'
```

---

**Version**: Phase 1-3, 5-6 Complete | Phase 4, 7-9 Planned  
**Last Updated**: January 2025  
**Status**: ✅ Production Ready
