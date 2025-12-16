# 🎯 Caldera Global Orchestration Pattern

> **Comprehensive campaign orchestration for MITRE Caldera** - Centralized management of multi-phase adversary emulation operations with AI-assisted automation.

[![Status](https://img.shields.io/badge/Status-Phase%201--5%20Complete-success)]()
[![Caldera](https://img.shields.io/badge/Caldera-4.x%2F5.x-blue)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)]()

## Overview

The **Global Orchestration Pattern** transforms Caldera into an enterprise-grade purple team platform by adding:

- 📋 **Campaign Specifications** - YAML-based configuration for environment, targets, adversaries, SIEM, governance
- 🎮 **Orchestrator CLI** - Command-line interface wrapping Caldera REST API, cloud APIs, SIEM APIs, webhooks  
- 🔗 **Webhook Publisher** - Event-driven notifications to Slack, N8N, SIEM platforms
- 📊 **SIEM Integration** - Automatic tagging and enrichment for Elasticsearch, Splunk
- 🆕 **Enrollment API** - REST API for dynamic agent enrollment with CI/CD integration (Phase 5)
- 🚀 **Platform Bootstrap** - Automated generation of Windows/Linux/macOS enrollment commands
- 🤖 **AI-Ready** - Enables AI to generate configs and scripts rather than manual UI clicks
- 🛡️ **Governance** - Approval workflows, scheduling, RBAC, compliance tracking

## Quick Start

### 1. Validate Caldera Instance

```bash
python3 orchestrator/health_check.py --url=http://localhost:8888
```

### 2. Create Campaign

```bash
cp schemas/campaign_spec_example.yml my_campaign.yml
python3 orchestrator/cli.py campaign create my_campaign.yml
```

### 3. Enroll Agents

**Option A: CLI-generated scripts**
```bash
python3 orchestrator/generate_agent_enrollment.py \
  --campaign=<campaign_id> \
  --platform=windows \
  --output=enroll.ps1
```

**Option B: Enrollment API (Phase 5)**
```bash
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{"platform":"linux","campaign_id":"<campaign_id>"}'
```

### 4. Start Campaign

```bash
python3 orchestrator/cli.py campaign start <campaign_id>
```

### 5. Monitor Status

```bash
python3 orchestrator/cli.py campaign status <campaign_id> --verbose
```

## Architecture

```
Campaign Spec (YAML) → Orchestrator CLI → Multiple APIs
                                          ├─ Caldera REST API
                                          ├─ Cloud APIs (AWS, Azure, GCP)
                                          ├─ SIEM APIs (Elastic, Splunk)
                                          ├─ Slack/N8N Webhooks
                                          └─ Report Generation (PDF, JSON)
```

## Implementation Status

### ✅ Phase 1-2: Infrastructure & Agent Automation (Complete)

- [x] Campaign specification schema and example
- [x] Campaign object model integrated with Caldera DataService
- [x] Orchestrator CLI with campaign/operation/agent/report commands
- [x] Health check script validating Caldera services
- [x] Agent enrollment script generator (Windows, Linux, macOS)
- [x] Infrastructure-as-code templates (Docker Compose, Terraform AWS)

### ✅ Phase 3: SIEM & Webhooks (Complete)

- [x] Webhook publisher with retry logic and filtering
- [x] SIEM integration for Elasticsearch and Splunk
- [x] Orchestrator plugin for Caldera
- [x] REST API endpoints for webhook management
- [x] Event-driven campaign notifications

### 🚧 Phase 4-9: Advanced Features (Scaffolded)

- [ ] Internal branding plugin with theme customization
- [ ] Enrollment API service for dynamic agent registration  
- [ ] PDF report generation with ATT&CK Navigator layers
- [ ] Slack bot and N8N workflow integration
- [ ] Governance enforcement (RBAC, approvals, scheduling)
- [ ] Prometheus/Grafana metrics dashboards
- [ ] AI plugin for ability generation and gap analysis
- [ ] Regression test framework

## Key Components

### Campaign Specification

```yaml
campaign_id: "550e8400-e29b-41d4-a716-446655440000"
name: "Q4 2025 Purple Team Exercise"
mode: "production"  # test | production | simulation

environment:
  environment_id: "prod-finance-001"
  caldera_url: "https://caldera.internal:8888"
  api_key_red: "${CALDERA_API_KEY_RED}"

targets:
  agent_groups: ["finance_servers"]
  platforms: ["windows", "linux"]
  tags:
    test_run_id: "Q4-2025-001"
    department: "finance"

adversary:
  adversary_id: "de07f52d-9928-4071-9142-cb1d437b4502"
  planner: "atomic"

siem:
  enabled: true
  type: "elastic"
  endpoint: "https://elasticsearch.internal:9200"
  tags:
    caldera_test: "true"

notifications:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#purple-team-ops"

governance:
  owner: "purple-team-lead@company.com"
  ticket_id: "SEC-2025-1234"
  approval_status: "approved"
  max_duration_hours: 4
```

### CLI Commands

```bash
# Campaign Management
orchestrator/cli.py campaign create <spec_file>
orchestrator/cli.py campaign start <campaign_id>
orchestrator/cli.py campaign status <campaign_id>
orchestrator/cli.py campaign stop <campaign_id>

# Health & Validation
orchestrator/health_check.py --url=http://localhost:8888

# Agent Enrollment
orchestrator/cli.py agent enroll <campaign_id> <host> <platform>
orchestrator/generate_agent_enrollment.py --campaign=<id> --platform=<windows|linux>

# Operations & Reports
orchestrator/cli.py operation create <campaign_id> --start
orchestrator/cli.py report generate <campaign_id> --format=pdf
```

### REST API (via Orchestrator Plugin)

```
GET    /plugin/orchestrator/webhooks          # List webhooks
POST   /plugin/orchestrator/webhooks          # Register webhook
GET    /plugin/orchestrator/campaigns         # List campaigns
GET    /plugin/orchestrator/campaigns/{id}    # Get campaign
POST   /plugin/orchestrator/campaigns/{id}/notify  # Publish event
```

## File Structure

```
caldera/
├── ORCHESTRATION_GUIDE.md              # Complete implementation guide
├── orchestrator/
│   ├── cli.py                          # Main orchestrator CLI
│   ├── health_check.py                 # Service validation
│   ├── generate_agent_enrollment.py    # Enrollment scripts
│   ├── webhook_publisher.py            # Event publishing & SIEM
│   ├── requirements.txt                # Dependencies
│   └── README.md                       # Orchestrator docs
├── app/objects/
│   └── c_campaign.py                   # Campaign data model
├── plugins/orchestrator/
│   ├── hook.py                         # Plugin integration
│   └── README.md
├── schemas/
│   ├── campaign_spec.schema.json       # JSON Schema validation
│   └── campaign_spec_example.yml       # Full example
└── data/campaigns/                     # Campaign YAML files
```

## Documentation

- **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)** - Complete implementation guide with examples
- **[orchestrator/README.md](orchestrator/README.md)** - Orchestrator CLI documentation
- **[schemas/campaign_spec_example.yml](schemas/campaign_spec_example.yml)** - Full campaign specification example
- **[schemas/campaign_spec.schema.json](schemas/campaign_spec.schema.json)** - JSON Schema for validation

## Features

### Campaign Management
- ✅ YAML-based campaign specifications
- ✅ Multi-operation orchestration
- ✅ State tracking and timeline
- ✅ Error logging and recovery

### Agent Automation
- ✅ Platform-specific enrollment scripts (Windows, Linux, macOS)
- ✅ Campaign-aware tagging
- ✅ Docker Compose templates
- ✅ Terraform AWS infrastructure-as-code

### SIEM Integration
- ✅ Elasticsearch event formatting
- ✅ Splunk HEC formatting
- ✅ Campaign/test_run_id tagging
- ✅ Automatic enrichment

### Notifications
- ✅ Webhook publishing with retry logic
- ✅ Event filtering (exchange/queue)
- ✅ Slack integration ready
- ✅ N8N workflow triggers ready

### Governance
- ✅ Owner and ticket tracking
- ✅ Approval status workflow
- ✅ Scheduled start/end times
- ✅ Maximum duration limits
- ✅ Production mode safeguards

## Installation

### Prerequisites

- MITRE Caldera 4.x or 5.x
- Python 3.8+
- pip

### Setup

```bash
# Install Caldera (if not already)
git clone https://github.com/mitre/caldera.git --recursive
cd caldera
pip install -r requirements.txt

# Install orchestrator dependencies
pip install -r orchestrator/requirements.txt

# Make scripts executable
chmod +x orchestrator/*.py

# Start Caldera
python3 server.py --insecure
```

### Verify Installation

```bash
python3 orchestrator/health_check.py
```

## Usage Examples

### Example 1: Simple Test Campaign

```yaml
campaign_id: "test-001"
name: "Simple Test"
mode: "test"
environment:
  environment_id: "dev-001"
  type: "development"
  caldera_url: "http://localhost:8888"
  api_key_red: "ADMIN123"
targets:
  agent_groups: ["red"]
adversary:
  adversary_id: "de07f52d-9928-4071-9142-cb1d437b4502"
  planner: "atomic"
```

```bash
python3 orchestrator/cli.py campaign create test_campaign.yml
python3 orchestrator/cli.py campaign start test-001
```

### Example 2: Production Campaign with SIEM

```yaml
campaign_id: "prod-q4-2025"
name: "Q4 2025 Financial Services Test"
mode: "production"
environment:
  environment_id: "prod-finance-001"
  caldera_url: "https://caldera.internal:8888"
  api_key_red: "${CALDERA_API_KEY_RED}"
targets:
  agent_groups: ["finance_servers", "finance_workstations"]
  platforms: ["windows", "linux"]
  tags:
    test_run_id: "Q4-2025-001"
adversary:
  adversary_id: "apt29-emulation"
  planner: "atomic"
siem:
  enabled: true
  type: "elastic"
  endpoint: "https://elasticsearch.internal:9200"
  api_key: "${ELASTIC_API_KEY}"
  index_name: "caldera-purple-team"
notifications:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#purple-team-ops"
governance:
  owner: "purple-team-lead@company.com"
  ticket_id: "SEC-2025-1234"
  approval_status: "approved"
  scheduled_start: "2025-12-20T14:00:00Z"
  max_duration_hours: 4
```

### Example 3: Infrastructure Provisioning

```bash
# Generate Terraform for AWS
python3 orchestrator/generate_agent_enrollment.py \
  --campaign-spec=prod_campaign.yml \
  --platform=terraform-aws \
  --output=infra.tf

# Provision infrastructure
terraform init
terraform apply

# Generate enrollment scripts
python3 orchestrator/generate_agent_enrollment.py \
  --campaign=prod-q4-2025 \
  --platform=windows \
  --output=enroll_windows.ps1
```

## Integration Examples

### Slack Notifications

```python
from orchestrator.webhook_publisher import WebhookPublisher

publisher = WebhookPublisher()
await publisher.start()

publisher.register_webhook(
    url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
    name='Slack Purple Team',
    filters={'exchange': ['operation'], 'queue': ['completed', 'started']}
)

await publisher.publish_event(
    exchange='operation',
    queue='completed',
    data={'operation_id': 'abc123'},
    campaign_id='prod-q4-2025'
)
```

### SIEM Integration

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

## Best Practices

1. **Use Environment Variables** - Never commit API keys in campaign specs
2. **Test in Dev First** - Validate campaigns in development environments
3. **Tag Everything** - Use `test_run_id` for SIEM correlation
4. **Health Check Always** - Run health check before starting campaigns
5. **Monitor Status** - Use `campaign status --verbose` for detailed tracking
6. **Production Safeguards** - Require explicit confirmation for production mode
7. **Cleanup Properly** - Stop campaigns explicitly rather than letting them timeout

## Troubleshooting

See [ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md) for comprehensive troubleshooting guidance.

Common issues:
- **Campaign won't start** - Verify Caldera API connectivity and adversary ID
- **Agents not appearing** - Check network connectivity and firewall rules
- **Webhooks not firing** - Validate webhook URL accessibility and filters
- **SIEM events missing tags** - Ensure campaign spec includes SIEM configuration

## Contributing

Contributions welcome! Priority areas:

- Additional IaC providers (Azure, GCP, Kubernetes)
- Enhanced SIEM integrations (Sentinel, Chronicle)
- Report templates and visualizations
- CI/CD pipeline examples
- Slack bot implementation
- AI-assisted TTP generation

## License

Apache 2.0 (same as MITRE Caldera)

## Acknowledgments

- MITRE Caldera team for the excellent C2 framework
- ATT&CK framework for TTP taxonomy
- Community contributors

---

**Status**: Phase 1-3 Complete | **Ready for**: Campaign management, agent enrollment, webhook publishing  
**Documentation**: [ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md) | **Examples**: [schemas/](schemas/)
