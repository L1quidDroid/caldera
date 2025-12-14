# Folder Structure Reorganization Plan
**Date:** December 14, 2025  
**Purpose:** Improve maintainability, scalability, and developer experience

---

## Current Issues

1. **Root directory clutter**: 10+ markdown files in root (IMPLEMENTATION_SUMMARY.md, ORCHESTRATION_GUIDE.md, etc.)
2. **Mixed concerns**: Orchestrator CLI tools mixed with webhook/SIEM integration
3. **Schema location**: Campaign schemas in generic `/schemas/` instead of organized by domain
4. **No clear separation**: CLI tools vs. library code vs. services
5. **Documentation scattered**: READMEs in multiple locations
6. **No test structure**: Tests not organized by feature
7. **Future phases unclear**: No designated space for phases 5-9

---

## Proposed Structure

```
caldera/
├── docs/                              # 📚 All documentation centralized
│   ├── README.md                      # Index of all documentation
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── data-flow.md
│   │   └── integration-points.md
│   ├── guides/
│   │   ├── getting-started.md
│   │   ├── orchestration-guide.md
│   │   └── deployment-guide.md
│   ├── api/
│   │   ├── rest-api-reference.md
│   │   └── cli-reference.md
│   └── presentations/
│       └── team-presentation.md
│
├── orchestrator/                      # 🎯 Orchestration system (reorganized)
│   ├── README.md                      # Quick reference
│   ├── __init__.py
│   ├── cli/                           # CLI entry points
│   │   ├── __init__.py
│   │   ├── main.py                    # Main CLI (moved from cli.py)
│   │   ├── campaign_commands.py       # Campaign subcommands
│   │   ├── operation_commands.py      # Operation subcommands
│   │   ├── agent_commands.py          # Agent subcommands
│   │   └── report_commands.py         # Report subcommands
│   │
│   ├── core/                          # Core orchestration logic
│   │   ├── __init__.py
│   │   ├── campaign_manager.py        # Campaign lifecycle management
│   │   ├── operation_scheduler.py     # Operation scheduling
│   │   └── state_tracker.py           # State machine implementation
│   │
│   ├── services/                      # External service integrations
│   │   ├── __init__.py
│   │   ├── webhook_service.py         # Webhook publishing (moved)
│   │   ├── siem_service.py            # SIEM integrations (extracted)
│   │   ├── notification_service.py    # Slack/email (phase 7)
│   │   └── cloud_service.py           # AWS/Azure/GCP (future)
│   │
│   ├── agents/                        # Agent management
│   │   ├── __init__.py
│   │   ├── enrollment_generator.py    # Agent enrollment (moved)
│   │   ├── templates/                 # Enrollment script templates
│   │   │   ├── windows.ps1.j2
│   │   │   ├── linux.sh.j2
│   │   │   ├── docker-compose.yml.j2
│   │   │   └── terraform-aws.tf.j2
│   │   └── deployment/                # Deployment helpers
│   │       ├── docker.py
│   │       ├── terraform.py
│   │       └── kubernetes.py
│   │
│   ├── reporting/                     # Phase 6: Reporting system
│   │   ├── __init__.py
│   │   ├── report_generator.py
│   │   ├── pdf_generator.py
│   │   ├── attack_navigator.py
│   │   └── templates/
│   │       ├── executive_summary.html
│   │       └── technical_report.html
│   │
│   ├── governance/                    # Phase 8: Governance framework
│   │   ├── __init__.py
│   │   ├── approval_workflow.py
│   │   ├── rbac_enforcer.py
│   │   ├── audit_logger.py
│   │   └── compliance_checker.py
│   │
│   ├── ai/                            # Phase 9: AI-driven features
│   │   ├── __init__.py
│   │   ├── ttp_generator.py
│   │   ├── threat_modeler.py
│   │   ├── ability_composer.py
│   │   └── models/
│   │       └── prompts/
│   │
│   ├── schemas/                       # Orchestration-specific schemas
│   │   ├── campaign_spec.schema.json
│   │   ├── campaign_spec_example.yml
│   │   ├── enrollment_config.schema.json
│   │   └── report_config.schema.json
│   │
│   ├── utils/                         # Shared utilities
│   │   ├── __init__.py
│   │   ├── health_check.py            # Health validation (moved)
│   │   ├── validators.py              # Schema validators
│   │   ├── api_client.py              # REST API wrapper
│   │   └── config.py                  # Config management
│   │
│   ├── tests/                         # Orchestrator tests
│   │   ├── __init__.py
│   │   ├── test_cli.py
│   │   ├── test_campaign_manager.py
│   │   ├── test_webhook_service.py
│   │   ├── test_enrollment.py
│   │   └── fixtures/
│   │       └── sample_campaigns.yml
│   │
│   ├── requirements.txt               # Dependencies
│   └── setup.py                       # Installable package
│
├── plugins/
│   ├── orchestrator/                  # Caldera plugin for orchestration
│   │   ├── __init__.py
│   │   ├── hook.py
│   │   ├── api/                       # REST API routes
│   │   │   ├── __init__.py
│   │   │   ├── campaign_routes.py
│   │   │   ├── webhook_routes.py
│   │   │   └── health_routes.py
│   │   ├── templates/
│   │   │   └── dashboard.html
│   │   ├── static/
│   │   │   ├── css/
│   │   │   └── js/
│   │   └── README.md
│   │
│   ├── branding/                      # Branding plugin (already good structure)
│   │   ├── hook.py
│   │   ├── branding_config.yml
│   │   ├── static/
│   │   ├── templates/
│   │   └── README.md
│   │
│   └── enrollment/                    # Phase 5: Standalone enrollment API
│       ├── __init__.py
│       ├── hook.py
│       ├── api/
│       │   ├── enrollment_routes.py
│       │   └── agent_routes.py
│       ├── service/
│       │   └── enrollment_service.py
│       └── README.md
│
├── app/                               # Caldera core (existing)
│   ├── objects/
│   │   ├── c_campaign.py              # Keep here (core object)
│   │   └── ...
│   └── ...
│
├── conf/                              # Configuration (existing)
├── data/                              # Runtime data (existing)
│   ├── campaigns/                     # Campaign state files
│   └── ...
│
├── tests/                             # Caldera core tests (existing)
│   └── orchestrator/                  # Add orchestrator tests
│       └── (link to orchestrator/tests/)
│
├── scripts/                           # 🔧 Development & deployment scripts
│   ├── setup_orchestrator.sh
│   ├── deploy_aws.sh
│   ├── backup_campaigns.sh
│   └── dev/
│       ├── reset_test_env.sh
│       └── seed_data.sh
│
└── (root level files - minimal)
    ├── README.md                      # Main project README
    ├── GETTING_STARTED.md             # Quick start only
    ├── CHANGELOG.md                   # Version history
    ├── server.py
    ├── requirements.txt
    ├── docker-compose.yml
    └── ...
```

---

## Migration Steps

### Step 1: Create New Directory Structure
```bash
# Documentation
mkdir -p docs/{architecture,guides,api,presentations}

# Orchestrator reorganization
mkdir -p orchestrator/{cli,core,services,agents/{templates,deployment},reporting/{templates},governance,ai/{models/prompts},schemas,utils,tests/fixtures}

# Plugin API structure
mkdir -p plugins/orchestrator/api
mkdir -p plugins/enrollment/{api,service}

# Scripts directory
mkdir -p scripts/dev
```

### Step 2: Move Documentation Files
```bash
# From root to docs/
mv IMPLEMENTATION_SUMMARY.md docs/implementation-summary.md
mv ORCHESTRATION_GUIDE.md docs/guides/orchestration-guide.md
mv GETTING_STARTED.md docs/guides/getting-started.md
mv TEAM_PRESENTATION.md docs/presentations/team-presentation.md
mv ORCHESTRATION_README.md docs/guides/orchestration-readme.md

# Create index
cat > docs/README.md << 'EOF'
# Caldera Orchestration Documentation

## Quick Links
- [Getting Started](guides/getting-started.md)
- [Orchestration Guide](guides/orchestration-guide.md)
- [Team Presentation](presentations/team-presentation.md)

## Architecture
- [System Overview](architecture/overview.md)
- [Data Flow](architecture/data-flow.md)

## API Reference
- [REST API](api/rest-api-reference.md)
- [CLI Commands](api/cli-reference.md)
EOF
```

### Step 3: Reorganize Orchestrator
```bash
# Move CLI
mv orchestrator/cli.py orchestrator/cli/main.py
touch orchestrator/cli/__init__.py

# Move services
mv orchestrator/webhook_publisher.py orchestrator/services/webhook_service.py
touch orchestrator/services/__init__.py

# Move agent tools
mv orchestrator/generate_agent_enrollment.py orchestrator/agents/enrollment_generator.py
touch orchestrator/agents/__init__.py

# Move utilities
mv orchestrator/health_check.py orchestrator/utils/health_check.py
touch orchestrator/utils/__init__.py

# Move schemas
mv schemas/campaign_spec* orchestrator/schemas/

# Move tests
mv orchestrator/quick_test.py orchestrator/tests/test_cli.py
```

### Step 4: Reorganize Plugin
```bash
# Split hook.py into routes
cd plugins/orchestrator
# (Will create separate route files in Step 5)
```

### Step 5: Move Miscellaneous Scripts
```bash
mv setup_orchestrator.sh scripts/
mv branding_preview.html scripts/dev/
```

### Step 6: Update Import Statements
```python
# orchestrator/cli/main.py
from orchestrator.services.webhook_service import WebhookPublisher
from orchestrator.agents.enrollment_generator import AgentEnrollmentGenerator
from orchestrator.utils.health_check import CalderaHealthCheck
from orchestrator.core.campaign_manager import CampaignManager

# plugins/orchestrator/hook.py
from orchestrator.services.webhook_service import WebhookPublisher
```

### Step 7: Create Setup.py for Installable Package
```python
# orchestrator/setup.py
from setuptools import setup, find_packages

setup(
    name='caldera-orchestrator',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'aiohttp>=3.8.0',
        'pyyaml>=6.0',
        'rich>=13.0.0',
        'jsonschema>=4.0.0',
    ],
    entry_points={
        'console_scripts': [
            'caldera-orchestrator=orchestrator.cli.main:main',
        ],
    },
)
```

---

## Benefits

### ✅ Immediate Benefits
1. **Cleaner root**: Only essential files (server.py, requirements.txt, README.md)
2. **Clear separation**: CLI vs. services vs. core logic
3. **Better imports**: `from orchestrator.services import webhook_service`
4. **Test organization**: Tests next to code they test
5. **Documentation hub**: All docs in `/docs/`

### 🚀 Future Benefits
1. **Phase 5-9 ready**: Clear structure for enrollment API, reporting, governance, AI
2. **Installable package**: `pip install -e orchestrator/`
3. **Independent testing**: Test orchestrator without full Caldera
4. **Microservice ready**: Could split services into separate containers
5. **Team scalability**: Clear ownership boundaries

### 📦 Package Structure
```python
# After reorganization, can do:
from orchestrator.cli import campaign_commands
from orchestrator.services import webhook_service, siem_service
from orchestrator.agents import enrollment_generator
from orchestrator.reporting import report_generator  # Phase 6
from orchestrator.governance import approval_workflow  # Phase 8
from orchestrator.ai import ttp_generator  # Phase 9
```

---

## Phase-Specific Organization

### Phase 5: Enrollment API
```
plugins/enrollment/
├── hook.py                    # FastAPI app registration
├── api/
│   ├── enrollment_routes.py   # POST /enroll
│   └── agent_routes.py        # GET /agents
└── service/
    └── enrollment_service.py  # Business logic
```

### Phase 6: Reporting
```
orchestrator/reporting/
├── report_generator.py        # Main report engine
├── pdf_generator.py           # PDF export (WeasyPrint)
├── attack_navigator.py        # ATT&CK layer generation
└── templates/
    ├── executive_summary.html
    └── technical_report.html
```

### Phase 7: Slack/N8N
```
orchestrator/services/
├── notification_service.py    # Base notification class
├── slack_service.py           # Slack bot + commands
└── n8n_service.py             # N8N workflow triggers
```

### Phase 8: Governance
```
orchestrator/governance/
├── approval_workflow.py       # State machine for approvals
├── rbac_enforcer.py           # Role-based access control
├── audit_logger.py            # Comprehensive audit trail
└── compliance_checker.py      # Policy validation
```

### Phase 9: AI Features
```
orchestrator/ai/
├── ttp_generator.py           # LLM-based TTP generation
├── threat_modeler.py          # Gap analysis
├── ability_composer.py        # Automated ability creation
└── models/
    └── prompts/
        ├── generate_ability.txt
        └── analyze_threat.txt
```

---

## Backward Compatibility

### During Migration
1. Keep symlinks for old paths:
   ```bash
   ln -s orchestrator/cli/main.py orchestrator/cli.py
   ln -s docs/guides/orchestration-guide.md ORCHESTRATION_GUIDE.md
   ```

2. Update all documentation with new paths

3. Add deprecation warnings:
   ```python
   # orchestrator/cli.py (old location)
   import warnings
   warnings.warn("Import from orchestrator.cli.main instead", DeprecationWarning)
   from orchestrator.cli.main import *
   ```

---

## Testing Strategy

### After Reorganization
```bash
# Test orchestrator as package
cd orchestrator
python -m pytest tests/

# Test imports
python -c "from orchestrator.services import webhook_service"
python -c "from orchestrator.cli import campaign_commands"

# Test CLI still works
python -m orchestrator.cli.main campaign --help

# Test plugin loads
python server.py  # Check logs for orchestrator plugin
```

---

## Timeline

| Step | Effort | Risk |
|------|--------|------|
| Create directories | 15 min | Low |
| Move documentation | 30 min | Low |
| Reorganize orchestrator | 2 hours | Medium |
| Update imports | 1-2 hours | Medium |
| Update tests | 1 hour | Medium |
| Create setup.py | 30 min | Low |
| Testing & validation | 2 hours | High |
| **Total** | **~7-8 hours** | **Medium** |

---

## Success Criteria

✅ All tests pass after migration  
✅ CLI commands work identically  
✅ Plugins load successfully  
✅ Documentation links updated  
✅ Import statements follow new structure  
✅ Root directory has <10 files  
✅ Clear path for phases 5-9  
✅ Package installable via `pip install -e orchestrator/`

---

## Next Steps

1. **Review this plan** with team
2. **Create feature branch**: `git checkout -b feature/folder-reorganization`
3. **Execute migration** steps 1-7
4. **Run validation** tests
5. **Update CI/CD** if needed
6. **Merge to master** after approval
7. **Update team documentation** with new paths

---

**Questions?** Review with team before proceeding with migration.
