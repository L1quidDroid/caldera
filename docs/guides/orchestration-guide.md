# Caldera Global Orchestration Pattern - Implementation Guide

**Version:** 1.0.0  
**Status:** Phase 1-3 Implemented, Phase 4-9 Scaffolded  
**Date:** December 14, 2025

## Overview

This implementation provides a comprehensive global orchestration pattern for MITRE Caldera that enables centralized management of multi-phase adversary emulation campaigns. The system orchestrates infrastructure provisioning, agent enrollment, operation execution, SIEM integration, reporting, and notifications—enabling AI-assisted purple team operations.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│            Campaign Specification (YAML)                 │
│  - Environment, Targets, Adversary, SIEM, Governance   │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│             Orchestrator CLI (cli.py)                    │
│  Campaign Management • Operations • Agents • Reports    │
└───┬───────┬──────────┬──────────┬──────────┬───────────┘
    │       │          │          │          │
    ▼       ▼          ▼          ▼          ▼
┌────────┐ ┌─────┐  ┌──────┐  ┌──────┐  ┌─────────┐
│Caldera │ │Cloud│  │SIEM  │  │Slack/│  │Reports  │
│REST API│ │ APIs│  │APIs  │  │N8N   │  │PDF/JSON │
└────────┘ └─────┘  └──────┘  └──────┘  └─────────┘
```

### Data Model

**Campaign Object** (`app/objects/c_campaign.py`)
- Centralized state tracking for multi-operation campaigns
- Timeline, errors, agent enrollment, reports
- Integrated with Caldera DataService

**Webhook Publisher** (`orchestrator/webhook_publisher.py`)
- Event-driven notifications to external systems
- Retry logic and filtering
- SIEM-specific formatters (Elastic, Splunk)

**Orchestrator Plugin** (`plugins/orchestrator/`)
- Caldera plugin integration
- REST API endpoints for webhooks and campaigns
- Event service integration

## Implementation Status

### ✅ Phase 1-2: Completed

#### Infrastructure & Baseline
- [x] Campaign specification schema (`schemas/campaign_spec.schema.json`)
- [x] Example campaign spec (`schemas/campaign_spec_example.yml`)
- [x] Campaign object model (`app/objects/c_campaign.py`)
- [x] DataService integration for campaigns
- [x] Health check script (`orchestrator/health_check.py`)
  - Validates Caldera services (UI, API, plugins)
  - Checks API keys and configuration
  - Campaign environment validation

#### Agent Automation
- [x] Orchestrator CLI foundation (`orchestrator/cli.py`)
  - Campaign create/start/status/stop commands
  - Operation creation via REST API
  - Agent enrollment command generation
- [x] Agent enrollment script generator (`orchestrator/generate_agent_enrollment.py`)
  - Windows PowerShell scripts
  - Linux/macOS bash scripts
  - Campaign-aware tagging
  - Docker Compose templates
  - Terraform AWS infrastructure-as-code

### ✅ Phase 3: Completed

#### SIEM Integration & Webhooks
- [x] Webhook publisher (`orchestrator/webhook_publisher.py`)
  - Publishes events to external webhooks
  - Retry logic and error handling
  - Event filtering by exchange/queue
- [x] SIEM integration class
  - Elasticsearch formatting
  - Splunk HEC formatting
  - Campaign/test_run_id tagging
- [x] Orchestrator plugin (`plugins/orchestrator/`)
  - REST API for webhook management
  - Campaign notification endpoints
  - Web UI dashboard

### ✅ Phase 5: Completed (December 2025)

#### Enrollment API Plugin
- [x] **Enrollment plugin with CALDERA integration** (`plugins/enrollment/`)
- [x] **REST API for dynamic agent registration**
  - POST `/plugin/enrollment/enroll` - Create enrollment with platform-specific bootstrap
  - GET `/plugin/enrollment/enroll/{id}` - Get enrollment status
  - GET `/plugin/enrollment/requests` - List all enrollments
  - GET `/plugin/enrollment/campaigns/{id}/agents` - List agents by campaign
  - GET `/plugin/enrollment/health` - Health check
- [x] **JSON-based persistent storage** (`plugins/enrollment/data/enrollment_requests.json`)
- [x] **Platform-specific bootstrap generation** (Windows PowerShell, Linux/macOS bash)
- [x] **Campaign-aware agent tagging** - Automatic tags from enrollment request
- [x] **Environment variable configuration** (`CALDERA_URL` with localhost:8888 fallback)
- [x] **CLI/API separation maintained** - Distinct from orchestrator CLI
- [x] **Local testing examples** (`examples/enrollment/`)
  - `test_enrollment_api.sh` - Comprehensive bash test script with curl/jq
  - `enroll_from_python.py` - Python client with EnrollmentClient class
  - `.env.example` - Configuration template
- [x] **Comprehensive documentation** (`plugins/enrollment/docs/`)
  - `README.md` - Installation, quickstart, troubleshooting (5000+ bytes)
  - `API.md` - Complete endpoint reference with examples (6000+ bytes)
- [x] **Comprehensive testing** (`tests/test_phase5_requirements.py`)
  - 50+ test cases across 8 requirement categories
  - Color-coded reporting and detailed validation

### 🚧 Phase 4, 6-9: Scaffolded

#### Phase 4: Internal Branding
- [ ] Internal theme plugin skeleton
- [ ] Customizable colors and logos
- [ ] Template overrides

#### Phase 6: PDF Reporting
- [ ] Report aggregation across operations
- [ ] ATT&CK Navigator layer generation
- [ ] PDF template with Jinja2
- [ ] Charts and visualizations

#### Phase 7: Slack/N8N Integration
- [ ] Slack bot with commands
- [ ] N8N workflow examples
- [ ] Operation lifecycle notifications
- [ ] Status queries

#### Phase 8: Governance
- [ ] RBAC configuration templates
- [ ] Environment scoping validation
- [ ] Approval workflow enforcement
- [ ] Prometheus/Grafana dashboards
- [ ] Compliance reporting

#### Phase 9: AI-Driven TTP Evolution
- [ ] AI plugin for ability generation
- [ ] Threat model gap analysis
- [ ] Regression test framework
- [ ] Automated adversary composition

## Quick Start

### Prerequisites

```bash
# Install Caldera dependencies
pip install -r requirements.txt

# Install orchestrator dependencies
pip install -r orchestrator/requirements.txt
```

### 1. Validate Caldera Instance

```bash
python3 orchestrator/health_check.py --url=http://localhost:8888 --api-key-red=ADMIN123
```

Expected output:
```
╔═══════════════════════════════════════════════════════════╗
║          CALDERA HEALTH CHECK - PHASE 1                 ║
╚═══════════════════════════════════════════════════════════╝

✅ Web UI is accessible
✅ REST API v2 is responding
✅ Red team API key is valid
✅ 15 plugins loaded: stockpile, sandcat, atomic, ...
```

### 2. Create Campaign

```bash
# Copy and edit example spec
cp schemas/campaign_spec_example.yml my_campaign.yml

# Create campaign
python3 orchestrator/cli.py campaign create my_campaign.yml
```

Output:
```
✅ Campaign created: Q4 2025 Purple Team Exercise
   Campaign ID: 550e8400-e29b-41d4-a716-446655440000
   Environment: prod-finance-001
   Mode: production
   Spec saved: data/campaigns/550e8400-e29b-41d4-a716-446655440000.yml
```

### 3. Generate Agent Enrollment Scripts

```bash
# Windows enrollment
python3 orchestrator/generate_agent_enrollment.py \
  --campaign=550e8400-e29b-41d4-a716-446655440000 \
  --platform=windows \
  --output=enroll_windows.ps1

# Linux enrollment
python3 orchestrator/generate_agent_enrollment.py \
  --campaign=550e8400-e29b-41d4-a716-446655440000 \
  --platform=linux \
  --output=enroll_linux.sh
```

### 4. Start Campaign

```bash
python3 orchestrator/cli.py campaign start 550e8400-e29b-41d4-a716-446655440000
```

Progress output:
```
Starting Campaign: Q4 2025 Purple Team Exercise

✓ Phase 1: Validating infrastructure...
✓ Phase 2: Preparing agent enrollment...
✓ Creating operation...

Operation created: a7c857-37a0-4c4a-85f7-4e9f7f30e31a
Campaign started
```

### 5. Monitor Status

```bash
python3 orchestrator/cli.py campaign status 550e8400-e29b-41d4-a716-446655440000 --verbose
```

## Campaign Specification

### Minimal Example

```yaml
campaign_id: "550e8400-e29b-41d4-a716-446655440000"
name: "My First Campaign"
mode: "test"

environment:
  environment_id: "dev-001"
  type: "development"
  caldera_url: "http://localhost:8888"
  api_key_red: "ADMIN123"

targets:
  agent_groups: ["red"]
  platforms: ["linux"]

adversary:
  adversary_id: "de07f52d-9928-4071-9142-cb1d437b4502"
  planner: "atomic"
```

### Full-Featured Example

See `schemas/campaign_spec_example.yml` for a complete example including:
- SIEM integration (Elasticsearch)
- Slack notifications
- Governance fields (owner, ticket_id, approval)
- Multi-platform targeting
- Custom tags and metadata

## API Reference

### Orchestrator CLI

```bash
# Campaign management
python3 orchestrator/cli.py campaign create <spec_file>
python3 orchestrator/cli.py campaign start <campaign_id>
python3 orchestrator/cli.py campaign status <campaign_id> [--verbose]
python3 orchestrator/cli.py campaign stop <campaign_id> [--force]

# Health check
python3 orchestrator/health_check.py [--url=URL] [--api-key=KEY]

# Agent enrollment
python3 orchestrator/cli.py agent enroll <campaign_id> <host> <platform>
python3 orchestrator/generate_agent_enrollment.py --campaign=<id> --platform=<windows|linux>

# Operations
python3 orchestrator/cli.py operation create <campaign_id> [--start] [--wait]

# Reports
python3 orchestrator/cli.py report generate <campaign_id> [--format=pdf]
```

### REST API Endpoints

**Webhook Management** (via Orchestrator Plugin)
```
GET    /plugin/orchestrator/webhooks
POST   /plugin/orchestrator/webhooks
DELETE /plugin/orchestrator/webhooks/{url}
```

**Campaign Management**
```
GET    /plugin/orchestrator/campaigns
GET    /plugin/orchestrator/campaigns/{campaign_id}
POST   /plugin/orchestrator/campaigns/{campaign_id}/notify
```

**Enrollment API** (via Enrollment Plugin)
```
GET    /plugin/enrollment/health
POST   /plugin/enrollment/enroll
GET    /plugin/enrollment/enroll/{request_id}
GET    /plugin/enrollment/requests
GET    /plugin/enrollment/campaigns/{campaign_id}/agents
```

**Caldera Core APIs** (used by orchestrator)
```
GET/POST   /api/v2/operations
GET/POST   /api/v2/agents
GET        /api/v2/adversaries
GET        /api/v2/abilities
GET        /api/v2/config
```

## Integration Examples

### Enrollment API Usage

```bash
# Create enrollment request
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linux",
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "tags": ["production", "web-server"],
    "hostname": "web-01"
  }'

# Response includes bootstrap command
{
  "request_id": "abc-123",
  "bootstrap_command": "curl -sk http://localhost:8888/file/download ...",
  "status": "pending"
}

# Execute on target host
ssh user@web-01 "$(curl -s http://localhost:8888/plugin/enrollment/enroll/abc-123 | jq -r '.bootstrap_command')"

# List campaign agents
curl http://localhost:8888/plugin/enrollment/campaigns/550e8400-e29b-41d4-a716-446655440000/agents
```

### Python Enrollment Client

```python
import requests

# Create enrollment
response = requests.post(
    'http://localhost:8888/plugin/enrollment/enroll',
    json={
        'platform': 'linux',
        'campaign_id': 'my-campaign',
        'tags': ['automated']
    }
)
enrollment = response.json()

# Execute bootstrap
import subprocess
subprocess.run(enrollment['bootstrap_command'], shell=True)
```

### SIEM Tagging (Elasticsearch)

```python
from orchestrator.webhook_publisher import SIEMIntegration

siem = SIEMIntegration(
    siem_type='elastic',
    endpoint='https://elasticsearch.internal:9200',
    api_key='your-api-key',
    index_name='caldera-purple-team'
)

await siem.start()
await siem.send_event(event_data)
```

### Webhook Notifications

```python
from orchestrator.webhook_publisher import WebhookPublisher

publisher = WebhookPublisher()
await publisher.start()

# Register Slack webhook
publisher.register_webhook(
    url='https://hooks.slack.com/services/...',
    name='Slack Purple Team',
    filters={'exchange': ['operation'], 'queue': ['completed', 'started']}
)

# Publish event
await publisher.publish_event(
    exchange='operation',
    queue='completed',
    data={'operation_id': 'abc123'},
    campaign_id='550e8400-e29b-41d4-a716-446655440000',
    test_run_id='Q4-2025-001'
)
```

### Campaign Object Usage

```python
from app.objects.c_campaign import Campaign

campaign = Campaign(
    campaign_id='550e8400-e29b-41d4-a716-446655440000',
    name='My Campaign',
    mode='test',
    environment={'environment_id': 'dev-001', 'type': 'development'},
    adversary={'adversary_id': 'abc-123', 'planner': 'atomic'}
)

# Update status
campaign.update_status('operation_running')

# Track operation
campaign.add_operation('op-123', 'Operation Name', 'running')

# Track agent
campaign.add_agent('paw-456', 'hostname', 'linux')

# Log error
campaign.add_error('phase2', 'Connection timeout', 'warning')

# Save to data service
data_svc = services.get('data_svc')
await data_svc.store(campaign)
```

## File Structure

```
caldera/
├── orchestrator/
│   ├── cli.py                          # Main orchestrator CLI
│   ├── health_check.py                 # Service validation
│   ├── generate_agent_enrollment.py    # Enrollment scripts
│   ├── webhook_publisher.py            # Event publishing
│   ├── requirements.txt                # Dependencies
│   └── README.md                       # Orchestrator docs
├── app/
│   └── objects/
│       ├── c_campaign.py               # Campaign model
│       └── campaign/
│           └── __init__.py
├── plugins/
│   ├── orchestrator/
│   │   ├── hook.py                     # Orchestrator plugin
│   │   ├── __init__.py
│   │   └── README.md
│   └── enrollment/                     # NEW: Phase 5
│       ├── hook.py                     # Enrollment plugin integration
│       ├── app/
│       │   ├── enrollment_api.py       # REST endpoints
│       │   └── enrollment_svc.py       # Core service logic
│       ├── data/
│       │   └── enrollment_requests.json # Persistent storage
│       └── docs/
│           ├── README.md               # Plugin documentation
│           └── API.md                  # API reference
├── examples/
│   └── enrollment/                     # NEW: Phase 5
│       ├── test_enrollment_api.sh      # Bash testing script
│       ├── enroll_from_python.py       # Python client example
│       └── .env.example                # Configuration template
├── schemas/
│   ├── campaign_spec.schema.json       # JSON Schema
│   └── campaign_spec_example.yml       # Example spec
├── data/
│   └── campaigns/                      # Campaign YAML files
└── ORCHESTRATION_GUIDE.md              # This file
```

## Configuration

### Environment Variables

```bash
# Caldera API keys (for campaigns)
export CALDERA_API_KEY_RED="your-red-key"
export CALDERA_API_KEY_BLUE="your-blue-key"

# SIEM integration
export ELASTIC_API_KEY="your-elastic-key"
export SPLUNK_HEC_TOKEN="your-splunk-token"

# Notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Orchestrator config
export CALDERA_URL="http://localhost:8888"
```

### Orchestrator Config File

Create `orchestrator/config.yml`:

```yaml
campaigns_dir: "data/campaigns"
reports_dir: "data/reports"
caldera_url: "http://localhost:8888"
api_key_red: "${CALDERA_API_KEY_RED}"
timeout: 300

webhook_defaults:
  max_retries: 3
  retry_delay: 5
  timeout: 30

siem:
  enabled: true
  type: "elastic"
  endpoint: "https://elasticsearch.internal:9200"
```

## Best Practices

### Campaign Design

1. **Use Unique IDs**: Generate campaign_id with `uuidgen` or similar
2. **Tag Everything**: Use `test_run_id` and tags for SIEM correlation
3. **Environment Isolation**: Separate dev/staging/prod configurations
4. **Approval Workflow**: Set `requires_human_approval: true` for production
5. **Time Windows**: Define `scheduled_start` and `max_duration_hours`

### Security

1. **Never Commit Secrets**: Use environment variables in campaign specs
2. **API Key Rotation**: Regularly rotate Caldera API keys
3. **Network Isolation**: Use separate VPCs/networks for test environments
4. **Audit Trail**: Campaign timeline tracks all state changes
5. **Production Confirmation**: CLI requires explicit "yes" for production mode

### Operations

1. **Health Check First**: Always run `health_check.py` before starting campaigns
2. **Monitor Status**: Use `campaign status --verbose` for detailed progress
3. **Test in Dev**: Validate campaigns in development before production
4. **Incremental Deployment**: Start with small agent groups
5. **Cleanup**: Stop campaigns explicitly rather than letting them timeout

## Troubleshooting

### Campaign Won't Start

**Symptom**: `campaign start` fails with API error

**Solutions**:
- Verify Caldera is running: `curl http://localhost:8888`
- Check API key: `curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/config`
- Validate adversary ID exists in Caldera
- Ensure agent group matches enrolled agents

### Agents Not Appearing

**Symptom**: Enrollment script runs but agents don't show in Caldera

**Solutions**:
- Check network connectivity to Caldera server
- Verify firewall allows port 8888
- Review Caldera server logs: `tail -f caldera/logs/caldera.log`
- Ensure agent binary downloaded successfully
- Check agent process is running: `ps aux | grep sandcat`

### Webhooks Not Firing

**Symptom**: Events not reaching external systems

**Solutions**:
- Check webhook URL is accessible from Caldera host
- Verify webhook filters match event exchange/queue
- Review webhook stats: `GET /plugin/orchestrator/webhooks`
- Check webhook publisher logs in Caldera output
- Test webhook manually with `curl`

### SIEM Events Missing Tags

**Symptom**: Events in SIEM but missing campaign_id/test_run_id

**Solutions**:
- Ensure campaign spec includes SIEM configuration
- Verify webhook publisher has SIEM integration enabled
- Check event payload includes metadata fields
- Review SIEM ingest pipeline parsing

## Next Steps

### For Phase 4-9 Implementation

1. **Internal Branding Plugin**
   - Create plugin skeleton with theme CSS variables
   - Implement logo/color customization
   - Override core templates

2. **Enrollment API Service**
   - Build Flask/FastAPI enrollment service
   - Implement `/enroll` endpoint
   - Add CI/CD integration examples

3. **PDF Report Generation**
   - Aggregate operation reports
   - Generate ATT&CK Navigator layers
   - Create PDF templates with charts

4. **Slack/N8N Integration**
   - Implement Slack bot commands
   - Create N8N workflow templates
   - Add operation lifecycle notifications

5. **Governance Framework**
   - Enforce RBAC configurations
   - Implement approval workflows
   - Create Prometheus/Grafana dashboards

6. **AI Plugin**
   - Build ability generator
   - Implement threat model gap analysis
   - Create regression test framework

## Contributing

Contributions are welcome! Priority areas:

- Additional IaC providers (Azure, GCP, Kubernetes)
- Enhanced SIEM integrations (Sentinel, Chronicle, Datadog)
- Report templates and visualizations
- CI/CD pipeline examples (GitHub Actions, GitLab CI)
- Slack bot implementation
- AI-assisted TTP generation

## References

- [MITRE Caldera](https://github.com/mitre/caldera)
- [Caldera Documentation](https://caldera.readthedocs.io/)
- [ATT&CK Framework](https://attack.mitre.org/)
- [Orchestrator README](orchestrator/README.md)
- [Campaign Spec Schema](schemas/campaign_spec.schema.json)

## License

Apache 2.0 (same as MITRE Caldera)

## Support

For issues or questions:
1. Check this guide and `orchestrator/README.md`
2. Review example campaign specs in `schemas/`
3. Run health check to validate setup
4. Check Caldera logs for errors
5. Review GitHub issues for similar problems

---

**Implementation Complete**: Phase 1-5 (Infrastructure, Agents, SIEM/Webhooks, Enrollment API)  
**Ready for Use**: Campaign management, agent enrollment CLI, webhook publishing, REST enrollment API  
**Latest Addition**: Enrollment plugin with JSON persistence and CI/CD integration examples  
**Next Phase**: Internal branding plugin (Phase 4) and PDF reporting (Phase 6)
