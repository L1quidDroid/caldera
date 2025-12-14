# Folder Structure Visualization

## Current vs. Proposed Structure

### ❌ Current Structure (Problems)
```
caldera/
├── 📄 IMPLEMENTATION_SUMMARY.md          # ← Root clutter
├── 📄 ORCHESTRATION_GUIDE.md             # ← Root clutter
├── 📄 TEAM_PRESENTATION.md               # ← Root clutter
├── 📄 ORCHESTRATION_README.md            # ← Root clutter
├── 📄 GETTING_STARTED.md                 # ← Should stay
├── 📄 branding_preview.html              # ← Misplaced
├── 📄 setup_orchestrator.sh              # ← Misplaced
├── orchestrator/
│   ├── cli.py                            # ← Monolithic 700 lines
│   ├── webhook_publisher.py              # ← Mixed concerns
│   ├── health_check.py                   # ← Should be utility
│   ├── generate_agent_enrollment.py      # ← Agent-specific
│   └── quick_test.py                     # ← Should be in tests/
├── schemas/
│   ├── campaign_spec.schema.json         # ← Should be with orchestrator
│   └── campaign_spec_example.yml         # ← Should be with orchestrator
└── plugins/
    ├── orchestrator/
    │   ├── hook.py                       # ← Monolithic plugin file
    │   └── README.md
    └── branding/                         # ✅ Good structure
        ├── hook.py
        ├── api/
        ├── static/
        └── templates/
```

**Issues:**
- 🔴 10+ markdown files in root directory
- 🔴 CLI is single 700-line file
- 🔴 No clear separation between CLI, services, utilities
- 🔴 Schemas separated from orchestrator code
- 🔴 No structure for phases 5-9
- 🔴 Test files mixed with source code
- 🔴 Scripts scattered in root

---

### ✅ Proposed Structure (Clean & Scalable)

```
caldera/
├── 📄 README.md                          # Main project README only
├── 📄 GETTING_STARTED.md                 # Quick start guide
├── 📄 CHANGELOG.md                       # Version history
├── 📄 server.py                          # Caldera entry point
├── 📄 requirements.txt
├── 📄 docker-compose.yml
│
├── 📚 docs/                              # ← All documentation centralized
│   ├── README.md                         # Documentation index
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
│       ├── team-presentation.md
│       └── implementation-summary.md
│
├── 🎯 orchestrator/                      # ← Main orchestration package
│   ├── README.md
│   ├── setup.py                          # Installable package
│   ├── requirements.txt
│   │
│   ├── cli/                              # ← CLI commands organized
│   │   ├── __init__.py
│   │   ├── main.py                       # Entry point
│   │   ├── campaign_commands.py          # campaign create/start/stop
│   │   ├── operation_commands.py         # operation create/monitor
│   │   ├── agent_commands.py             # agent enroll/list
│   │   └── report_commands.py            # report generate/export
│   │
│   ├── core/                             # ← Core business logic
│   │   ├── __init__.py
│   │   ├── campaign_manager.py           # Campaign lifecycle
│   │   ├── operation_scheduler.py        # Operation scheduling
│   │   └── state_tracker.py              # State machine
│   │
│   ├── services/                         # ← External integrations
│   │   ├── __init__.py
│   │   ├── webhook_service.py            # Webhook publishing
│   │   ├── siem_service.py               # SIEM integrations
│   │   ├── notification_service.py       # [Phase 7] Slack/email
│   │   └── cloud_service.py              # [Future] AWS/Azure/GCP
│   │
│   ├── agents/                           # ← Agent management
│   │   ├── __init__.py
│   │   ├── enrollment_generator.py       # Script generation
│   │   ├── templates/                    # Jinja2 templates
│   │   │   ├── windows.ps1.j2
│   │   │   ├── linux.sh.j2
│   │   │   ├── docker-compose.yml.j2
│   │   │   └── terraform-aws.tf.j2
│   │   └── deployment/                   # [Future] Deployment tools
│   │       ├── docker.py
│   │       ├── terraform.py
│   │       └── kubernetes.py
│   │
│   ├── reporting/                        # [Phase 6] PDF reporting
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── report_generator.py
│   │   ├── pdf_generator.py
│   │   ├── attack_navigator.py
│   │   └── templates/
│   │       ├── executive_summary.html
│   │       └── technical_report.html
│   │
│   ├── governance/                       # [Phase 8] Governance
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── approval_workflow.py
│   │   ├── rbac_enforcer.py
│   │   ├── audit_logger.py
│   │   └── compliance_checker.py
│   │
│   ├── ai/                               # [Phase 9] AI features
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── ttp_generator.py
│   │   ├── threat_modeler.py
│   │   ├── ability_composer.py
│   │   └── models/
│   │       └── prompts/
│   │           ├── generate_ability.txt
│   │           └── analyze_threat.txt
│   │
│   ├── schemas/                          # ← Schemas with orchestrator
│   │   ├── __init__.py
│   │   ├── campaign_spec.schema.json
│   │   ├── campaign_spec_example.yml
│   │   ├── enrollment_config.schema.json
│   │   └── report_config.schema.json
│   │
│   ├── utils/                            # ← Shared utilities
│   │   ├── __init__.py
│   │   ├── health_check.py
│   │   ├── validators.py
│   │   ├── api_client.py
│   │   └── config.py
│   │
│   └── tests/                            # ← Tests next to code
│       ├── __init__.py
│       ├── test_cli.py
│       ├── test_campaign_manager.py
│       ├── test_webhook_service.py
│       ├── test_enrollment.py
│       └── fixtures/
│           └── sample_campaigns.yml
│
├── 🔌 plugins/
│   ├── orchestrator/                     # Caldera integration plugin
│   │   ├── __init__.py
│   │   ├── hook.py                       # Plugin initialization
│   │   ├── api/                          # ← REST routes organized
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
│   ├── branding/                         # ✅ Already well-structured
│   │   ├── hook.py
│   │   ├── branding_config.yml
│   │   ├── static/
│   │   ├── templates/
│   │   └── README.md
│   │
│   └── enrollment/                       # [Phase 5] Enrollment API
│       ├── __init__.py
│       ├── hook.py
│       ├── README.md
│       ├── api/
│       │   ├── enrollment_routes.py
│       │   └── agent_routes.py
│       └── service/
│           └── enrollment_service.py
│
├── 🔧 scripts/                           # ← Development scripts
│   ├── setup_orchestrator.sh
│   ├── deploy_aws.sh
│   ├── backup_campaigns.sh
│   └── dev/
│       ├── branding_preview.html
│       ├── reset_test_env.sh
│       └── seed_data.sh
│
├── app/                                  # Caldera core (unchanged)
│   ├── objects/
│   │   ├── c_campaign.py                 # Core campaign object
│   │   └── ...
│   └── ...
│
├── conf/                                 # Configuration (unchanged)
├── data/                                 # Runtime data (unchanged)
│   ├── campaigns/                        # Campaign state files
│   └── ...
│
└── tests/                                # Caldera core tests
    └── orchestrator/                     # Link to orchestrator/tests/
```

---

## Import Path Examples

### Before Reorganization ❌
```python
# Messy imports from flat structure
from orchestrator.cli import *
from orchestrator.webhook_publisher import WebhookPublisher
from orchestrator.generate_agent_enrollment import AgentEnrollmentGenerator
import orchestrator.health_check as health
```

### After Reorganization ✅
```python
# Clean, organized imports
from orchestrator.cli import campaign_commands, operation_commands
from orchestrator.services import webhook_service, siem_service
from orchestrator.agents import enrollment_generator
from orchestrator.utils import health_check, validators
from orchestrator.core import campaign_manager

# Or import classes directly
from orchestrator.services.webhook_service import WebhookPublisher
from orchestrator.services.siem_service import SIEMIntegration
from orchestrator.agents.enrollment_generator import AgentEnrollmentGenerator
from orchestrator.utils.health_check import CalderaHealthCheck
```

---

## Package Installation

### After Reorganization
```bash
# Install orchestrator as editable package
cd orchestrator
pip install -e .

# Now can import from anywhere
python -c "from orchestrator.cli import main"

# CLI available as command
caldera-orchestrator --help
caldera-orchestrator campaign create spec.yml
caldera-orchestrator health-check
```

---

## Benefits by Stakeholder

### 👨‍💻 **For Developers**
✅ **Clear code organization** - Know exactly where to add new features  
✅ **Modular imports** - Import only what you need  
✅ **Tests next to code** - Easy to find and run tests  
✅ **Installable package** - Use orchestrator in other projects  
✅ **Type hints work better** - IDEs understand structure  

### 🏗️ **For Architects**
✅ **Separation of concerns** - CLI, services, core logic separated  
✅ **Scalability** - Clear path for phases 5-9  
✅ **Microservice ready** - Can split services into containers  
✅ **Plugin architecture** - Easy to add new integrations  
✅ **Documentation hub** - All docs in one place  

### 👥 **For Team Leads**
✅ **Ownership boundaries** - Clear module ownership  
✅ **Onboarding** - New devs understand structure quickly  
✅ **Code review** - Know which files to review for PRs  
✅ **Parallel work** - Team can work on different modules  
✅ **Technical debt** - Easier to refactor isolated modules  

### 📊 **For Project Managers**
✅ **Progress tracking** - Clear structure for each phase  
✅ **Resource allocation** - Assign teams to modules  
✅ **Risk management** - Isolated modules reduce risk  
✅ **Timeline planning** - Can parallelize phase development  
✅ **Quality assurance** - Easier to test isolated components  

---

## Phase-Specific Organization

### Phase 5: Enrollment API 🆕
```
plugins/enrollment/
├── hook.py                    # FastAPI app registration
├── api/
│   ├── enrollment_routes.py   # POST /api/enroll
│   └── agent_routes.py        # GET /api/agents
└── service/
    └── enrollment_service.py  # Business logic
```
**Location Rationale:** Plugin for Caldera integration, separate API from orchestrator CLI

### Phase 6: Reporting 📊
```
orchestrator/reporting/
├── report_generator.py        # Aggregate data from operations
├── pdf_generator.py           # WeasyPrint PDF export
├── attack_navigator.py        # ATT&CK layer JSON
└── templates/
    ├── executive_summary.html
    └── technical_report.html
```
**Location Rationale:** Part of orchestrator package, used by CLI report commands

### Phase 7: Slack/N8N 💬
```
orchestrator/services/
├── notification_service.py    # Base class
├── slack_service.py           # Slack bot + webhook
└── n8n_service.py             # N8N workflow triggers
```
**Location Rationale:** External service integration, extends webhook_service

### Phase 8: Governance 🔐
```
orchestrator/governance/
├── approval_workflow.py       # State machine for approvals
├── rbac_enforcer.py           # Role-based access control
├── audit_logger.py            # Comprehensive audit trail
└── compliance_checker.py      # Policy validation
```
**Location Rationale:** Core orchestrator feature, used across all operations

### Phase 9: AI Features 🤖
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
**Location Rationale:** Advanced orchestrator feature, clear AI boundary

---

## File Count Comparison

### Before Reorganization
```
Root directory:        15 files (too many)
orchestrator/:         7 files (mixed concerns)
schemas/:              2 files (separated)
plugins/orchestrator/: 3 files (monolithic)
Documentation:         Scattered across 10+ files
```

### After Reorganization
```
Root directory:        6 files (clean)
docs/:                 12+ files (organized)
orchestrator/:         50+ files (modular)
  ├── cli/            4 files
  ├── core/           3 files
  ├── services/       4 files
  ├── agents/         3 files
  ├── reporting/      4 files (phase 6)
  ├── governance/     4 files (phase 8)
  ├── ai/             4 files (phase 9)
  ├── schemas/        4 files
  ├── utils/          4 files
  └── tests/          6 files
plugins/orchestrator/: 10+ files (organized)
scripts/:              8 files (utilities)
```

---

## Migration Timeline

### Automated Migration (1 hour)
```bash
# Dry run first
./migrate_folder_structure.sh --dry-run

# Execute migration
./migrate_folder_structure.sh

# Review changes
cat MIGRATION_SUMMARY.md
```

### Manual Updates (2-3 hours)
1. ✏️ Update import statements in code
2. ✏️ Update documentation links
3. ✏️ Review and test CLI commands
4. ✏️ Update CI/CD configuration
5. ✏️ Test plugin loading

### Validation (1-2 hours)
1. ✅ Run all tests
2. ✅ Test CLI commands
3. ✅ Start Caldera server
4. ✅ Verify plugins load
5. ✅ Run health check

### Total Time: **4-6 hours**

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Root directory files | 15 | 6 | < 10 |
| Documentation centralized | No | Yes | 100% |
| Modular CLI | No | Yes | ✅ |
| Clear service boundaries | No | Yes | ✅ |
| Tests organized | No | Yes | ✅ |
| Phase 5-9 structure ready | No | Yes | ✅ |
| Installable package | No | Yes | ✅ |
| Import statement clarity | Low | High | ✅ |

---

## Risk Mitigation

### Automated Backup
```bash
# Backup created automatically
backups/pre-reorganization-YYYYMMDD_HHMMSS/
└── caldera-backup.tar.gz
```

### Backward Compatibility
- Symlinks maintain old paths
- Deprecation warnings added
- Old imports still work (temporarily)

### Rollback Plan
```bash
# If migration fails
cd backups/pre-reorganization-*/
tar -xzf caldera-backup.tar.gz
# Restore files manually
```

---

## Next Steps

1. ✅ **Review this plan** with team
2. ⏳ **Run dry-run migration**: `./migrate_folder_structure.sh --dry-run`
3. ⏳ **Execute migration**: `./migrate_folder_structure.sh`
4. ⏳ **Update imports** in all code files
5. ⏳ **Run validation tests**
6. ⏳ **Commit changes**: `git commit -m "Reorganize folder structure for scalability"`
7. ⏳ **Update team documentation**
8. ⏳ **Proceed to Phase 5** with clean structure

---

**Questions?** Review `FOLDER_STRUCTURE_PLAN.md` for detailed implementation plan.
