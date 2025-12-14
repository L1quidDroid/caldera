# Caldera Campaign Orchestrator

Comprehensive orchestration system for multi-phase adversary emulation campaigns using MITRE Caldera.

## Overview

The Caldera Campaign Orchestrator provides centralized management for purple team operations through:

- **Campaign Specifications**: YAML-based configuration defining environment, targets, adversaries, SIEM integration, notifications, and governance
- **CLI Tool**: Command-line interface wrapping Caldera REST API, cloud APIs, SIEM APIs, and webhooks
- **Multi-Phase Automation**: Orchestrates infrastructure provisioning, agent enrollment, operation execution, SIEM tagging, reporting, and notifications
- **AI-Assisted Operations**: Enables AI to generate configurations and scripts rather than manual UI interaction

## Architecture

```
Campaign Spec (YAML)
        ↓
Orchestrator CLI
        ↓
    ┌───────────┬──────────────┬────────────┬──────────────┐
    ↓           ↓              ↓            ↓              ↓
Caldera API  Cloud APIs   SIEM APIs   Slack/N8N    Report Gen
```

### Components

1. **Campaign Object** (`app/objects/c_campaign.py`)
   - Core data model for campaign state
   - Tracks operations, agents, timeline, errors, reports
   - Integrates with Caldera DataService

2. **Orchestrator CLI** (`orchestrator/cli.py`)
   - Main command-line interface
   - Commands: campaign, operation, agent, report, health-check
   - Async HTTP client for Caldera REST API

3. **Health Check** (`orchestrator/health_check.py`)
   - Validates Caldera services (UI, API, plugins, agents)
   - Checks campaign environment configuration
   - Phase 1 prerequisite for campaign execution

4. **Agent Enrollment Generator** (`orchestrator/generate_agent_enrollment.py`)
   - Creates platform-specific enrollment scripts
   - Windows PowerShell, Linux/macOS bash
   - Docker Compose and Terraform IaC templates
   - Campaign-aware tagging and metadata

5. **Campaign Specification Schema** (`schemas/campaign_spec.schema.json`)
   - JSON Schema for campaign YAML validation
   - Defines structure for environment, targets, adversary, SIEM, notifications, governance

## Quick Start

### 1. Install Dependencies

```bash
cd orchestrator
pip install -r requirements.txt
```

### 2. Create Campaign Specification

```bash
cp ../schemas/campaign_spec_example.yml my_campaign.yml
# Edit my_campaign.yml with your configuration
```

### 3. Validate Caldera Instance

```bash
python3 health_check.py --url=http://localhost:8888 --api-key-red=ADMIN123
```

### 4. Create Campaign

```bash
python3 cli.py campaign create my_campaign.yml
```

### 5. Start Campaign

```bash
python3 cli.py campaign start <campaign_id>
```

### 6. Monitor Status

```bash
python3 cli.py campaign status <campaign_id> --verbose
```

## Campaign Specification Format

```yaml
campaign_id: "550e8400-e29b-41d4-a716-446655440000"
name: "Q4 2025 Purple Team Exercise"
mode: "production"  # test | production | simulation | validation

environment:
  environment_id: "prod-finance-001"
  type: "production"
  caldera_url: "https://caldera.internal:8888"
  api_key_red: "${CALDERA_API_KEY_RED}"
  infrastructure:
    caldera_host: "caldera-server-01.internal"
    red_vms: ["attacker-01.red.internal"]
    blue_vms: ["dc01.corp.internal"]

targets:
  agent_groups: ["finance_servers"]
  platforms: ["windows", "linux"]
  tags:
    test_run_id: "Q4-2025-001"
    department: "finance"

adversary:
  adversary_id: "de07f52d-9928-4071-9142-cb1d437b4502"
  name: "APT29 Emulation"
  planner: "atomic"

siem:
  enabled: true
  type: "elastic"
  endpoint: "https://elasticsearch.internal:9200"
  api_key: "${ELASTIC_API_KEY}"
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
  scheduled_start: "2025-12-20T14:00:00Z"
  max_duration_hours: 4
```

## CLI Commands

### Health Check

Verify Caldera services:

```bash
python3 health_check.py [OPTIONS]

Options:
  --url=URL                Caldera base URL (default: http://localhost:8888)
  --api-key-red=KEY        Red team API key
  --api-key-blue=KEY       Blue team API key
  --environment=FILE       Campaign spec YAML (auto-loads config)
  --required-plugins=LIST  Comma-separated required plugins
  --json                   Output in JSON format
```

### Campaign Management

```bash
# Create campaign from spec
python3 cli.py campaign create <spec_file>

# Start campaign execution
python3 cli.py campaign start <campaign_id>

# Check campaign status
python3 cli.py campaign status <campaign_id> [--verbose]

# Stop campaign
python3 cli.py campaign stop <campaign_id> [--force]
```

### Operation Management

```bash
# Create operation for campaign
python3 cli.py operation create <campaign_id> [--start] [--wait]
```

### Agent Enrollment

```bash
# Get enrollment commands
python3 cli.py agent enroll <campaign_id> <host> <platform>

# Generate enrollment scripts
python3 generate_agent_enrollment.py --campaign=<campaign_id> --platform=<windows|linux>

# Output to file
python3 generate_agent_enrollment.py --campaign=<campaign_id> --platform=windows --output=enroll.ps1
```

### Report Generation

```bash
# Generate campaign report
python3 cli.py report generate <campaign_id> [--format=pdf] [--include-output]
```

## Multi-Phase Workflow

### Phase 1: Infrastructure Validation

```bash
# Validate Caldera and environment
python3 health_check.py --environment=campaign.yml

# Provision infrastructure (if using IaC)
python3 generate_agent_enrollment.py --campaign-spec=campaign.yml --platform=terraform-aws --output=main.tf
terraform init && terraform apply
```

### Phase 2: Agent Enrollment

```bash
# Generate enrollment scripts
python3 generate_agent_enrollment.py --campaign=<id> --platform=windows --output=enroll_windows.ps1
python3 generate_agent_enrollment.py --campaign=<id> --platform=linux --output=enroll_linux.sh

# Deploy to targets
# Windows: Run enroll_windows.ps1 as Administrator
# Linux: sudo bash enroll_linux.sh
```

### Phase 3: Operation Execution

```bash
# Start campaign (auto-creates operation)
python3 cli.py campaign start <campaign_id>

# Or create operation manually
python3 cli.py operation create <campaign_id> --start --wait
```

### Phase 4: Monitoring & Reporting

```bash
# Monitor status
python3 cli.py campaign status <campaign_id> --verbose

# Generate reports when complete
python3 cli.py report generate <campaign_id> --format=pdf
```

## Integration Points

### Caldera REST API

Uses `/api/v2` endpoints:
- `GET/POST /api/v2/operations` - Operation management
- `GET/POST /api/v2/agents` - Agent management
- `GET /api/v2/adversaries` - Adversary profiles
- `GET /api/v2/abilities` - Available TTPs
- `GET /api/v2/config` - Configuration

### SIEM Integration

Placeholder for Phase 3:
- Elasticsearch/Splunk event ingestion
- Campaign tagging in SIEM events
- Dashboard linking

### Notification Integration

Placeholder for Phase 7:
- Slack webhook notifications
- N8N workflow triggers
- Email notifications
- Custom webhooks

## Directory Structure

```
orchestrator/
├── cli.py                         # Main orchestrator CLI
├── health_check.py                # Service validation
├── generate_agent_enrollment.py   # Enrollment script generator
├── requirements.txt               # Python dependencies
└── README.md                      # This file

app/objects/
└── c_campaign.py                  # Campaign data model

data/campaigns/
└── *.yml                          # Campaign specification files

schemas/
├── campaign_spec.schema.json      # JSON Schema for validation
└── campaign_spec_example.yml      # Example campaign spec
```

## Environment Variables

Campaign specs support environment variable substitution:

```yaml
environment:
  api_key_red: "${CALDERA_API_KEY_RED}"
  
siem:
  api_key: "${ELASTIC_API_KEY}"
  
notifications:
  slack:
    webhook_url: "${SLACK_WEBHOOK_URL}"
```

Set in shell:

```bash
export CALDERA_API_KEY_RED="your-red-key"
export CALDERA_API_KEY_BLUE="your-blue-key"
export ELASTIC_API_KEY="your-elastic-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

## Development Status

### ✅ Completed (Phase 1-2)

- [x] Campaign specification schema
- [x] Campaign object model
- [x] Orchestrator CLI foundation
- [x] Health check script
- [x] Agent enrollment script generator
- [x] Infrastructure-as-code templates (Docker, Terraform)
- [x] Basic operation creation via API
- [x] Campaign status tracking

### 🚧 In Progress

- [ ] SIEM tagging and event integration (Phase 3)
- [ ] Internal branding plugin (Phase 4)
- [ ] Enrollment API service (Phase 5)
- [ ] PDF report generation (Phase 6)
- [ ] Slack/N8N notifications (Phase 7)
- [ ] Governance enforcement (Phase 8)
- [ ] AI-driven TTP evolution (Phase 9)

### 📋 Planned Features

- Operation polling and completion detection
- ATT&CK Navigator layer generation
- Multi-operation campaign coordination
- Webhook event publisher
- Report aggregation across operations
- RBAC and permission enforcement
- Metrics and dashboards (Prometheus/Grafana)
- AI plugin for ability generation
- Regression test framework

## Security Considerations

1. **API Keys**: Store in environment variables or secrets manager, never in campaign specs
2. **Production Mode**: Requires explicit confirmation before execution
3. **Governance**: Campaign specs support approval workflow and scheduling
4. **Isolation**: Use separate Caldera instances or agent groups per environment
5. **Audit Trail**: Campaign timeline tracks all state changes

## Troubleshooting

### Health Check Fails

```bash
# Check Caldera is running
curl http://localhost:8888

# Verify API key
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/config

# Check logs
tail -f server.log
```

### Agent Not Appearing

- Verify network connectivity to Caldera server
- Check firewall rules (port 8888)
- Ensure agent has correct server URL
- Check Caldera logs for beacon activity

### Operation Not Starting

- Verify adversary ID exists in Caldera
- Check agent group matches target agents
- Ensure agents are not already in another operation
- Review operation state via CLI or UI

## Contributing

Contributions welcome! Areas for improvement:

- Additional IaC providers (Azure, GCP, Kubernetes)
- Enhanced SIEM integrations (Sentinel, Chronicle)
- Report templates and visualizations
- CI/CD pipeline examples
- Plugin development patterns
- AI-assisted TTP generation

## License

Same as MITRE Caldera - Apache 2.0

## References

- [MITRE Caldera Documentation](https://caldera.readthedocs.io/)
- [Caldera REST API](https://caldera.readthedocs.io/en/latest/REST-API.html)
- [ATT&CK Framework](https://attack.mitre.org/)
- [Campaign Spec Schema](../schemas/campaign_spec.schema.json)
