# CALDERA Orchestration Overview

**📌 For complete orchestration guide, see [ORCHESTRATION_GUIDE.md](../../ORCHESTRATION_GUIDE.md) in the repository root.**

---

## What is Orchestration?

CALDERA's orchestration system enables automated, repeatable campaign execution across multiple environments. It provides:

- **Campaign Management** - Define and execute multi-phase operations
- **Agent Enrollment** - Automated agent deployment
- **Webhook Integration** - Real-time event notifications
- **Result Collection** - Automated reporting and analysis

---

## Key Components

### 1. Campaign Specifications

YAML files defining campaign structure:

```yaml
campaign_id: my-campaign-001
name: "My Test Campaign"
description: "Automated penetration test"

phases:
  - name: "Discovery"
    adversary: "discovery-adversary"
    duration: "30m"
  
  - name: "Exploitation"
    adversary: "exploit-adversary"
    duration: "1h"
```

### 2. Orchestrator CLI

Command-line interface for campaign management:

```bash
# List campaigns
python orchestrator/cli.py campaign list

# Run campaign
python orchestrator/cli.py campaign run my-campaign-001

# Check status
python orchestrator/cli.py campaign status my-campaign-001
```

### 3. Enrollment API

Automated agent enrollment:

```bash
# Create enrollment request
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linux",
    "campaign_id": "my-campaign-001"
  }'
```

### 4. Webhook Publisher

Real-time event notifications:

```bash
# Register webhook
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -d '{"url": "https://webhook.site/...", "exchanges": ["campaign"]}'
```

---

## Workflow

```
1. Define Campaign → 2. Deploy Agents → 3. Execute Operations → 4. Collect Results
       ↓                     ↓                     ↓                     ↓
   campaign.yml     Enrollment API       Orchestrator CLI        Webhook Events
```

---

## Quick Start

### 1. Create Campaign

```bash
# Create campaign specification
cat > data/campaigns/test-campaign.yml << EOF
campaign_id: test-001
name: "Test Campaign"
description: "Quick test"

targets:
  groups: ["red"]
  
adversary: "ad-hoc"
planner: "atomic"
EOF
```

### 2. Register Webhook

```bash
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/your-id", "exchanges": ["campaign"]}'
```

### 3. Run Campaign

```bash
python orchestrator/cli.py campaign run test-001
```

### 4. Monitor Progress

```bash
# Check campaign status
python orchestrator/cli.py campaign status test-001

# Watch webhook events
# (Visit webhook.site to see real-time events)
```

---

## Advanced Topics

### Multi-Environment Deployment

Deploy across AWS, Azure, local infrastructure using Terraform modules.

See: [Infrastructure as Code Guide](#)

### Custom Reporting

Generate PDF reports with operation results.

See: [Debrief Plugin Documentation](#)

### CI/CD Integration

Integrate campaigns into your CI/CD pipeline.

See: [CI/CD Integration Guide](#)

---

## Complete Examples

For step-by-step examples, see:
- [End-to-End User Journey](user-journey.md) - Complete workflow
- [Demo Walkthrough](demo.md) - Guided tutorial
- [ORCHESTRATION_GUIDE.md](../../ORCHESTRATION_GUIDE.md) - Detailed reference

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                CALDERA Core Server                   │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Orchestrator │  │  Enrollment  │  │  Webhook  │ │
│  │    Plugin    │  │    Plugin    │  │ Publisher │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
         │                    │                │
         ▼                    ▼                ▼
  ┌─────────────┐    ┌──────────────┐  ┌────────────┐
  │  Campaign   │    │    Agents    │  │  External  │
  │    Specs    │    │  (Sandcat)   │  │  Systems   │
  └─────────────┘    └──────────────┘  └────────────┘
```

---

## Best Practices

1. **Test Campaigns** - Always test in dev environment first
2. **Version Control** - Store campaign specs in git
3. **Monitoring** - Use webhooks for real-time monitoring
4. **Cleanup** - Remove old operations and agents
5. **Security** - Rotate API keys regularly

---

For troubleshooting orchestration issues, see:
- [Troubleshooting Guide - Orchestrator Issues](../TROUBLESHOOTING.md#orchestrator-issues)
