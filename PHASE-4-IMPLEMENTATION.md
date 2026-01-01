# Phase 4 Implementation Guide: Automated Sequencing

## Overview

Phase 4 adds **automated multi-step operation sequencing** with failure recovery to the Caldera orchestrator. This enables:

- **Automated campaign execution**: Chain multiple operations with fact passing
- **Intelligent retry logic**: Exponential backoff, tactic fallback, skip on failure
- **Web GUI interface**: Monitor and control sequences from Caldera UI
- **Workflow integration**: Automatic ELK tagging, Slack notifications, PDF reports

## What Was Implemented

### 1. CLI Extension ([orchestrator/cli.py](caldera/orchestrator/cli.py))

Added `sequence_campaign()` method (~250 lines):
- Creates operations sequentially via Caldera API
- Polls operation state (5s interval, configurable timeout)
- Implements exponential backoff retry (2^n seconds, max 30s)
- Chains facts between operations using `fact_filters`
- Supports tactic fallback and critical step marking

**New CLI command:**
```bash
caldera-orchestrator campaign sequence <campaign_id> <sequence.yml> \
  --max-retries 3 \
  --timeout 300
```

### 2. Sequencer Plugin ([plugins/sequencer/](caldera/plugins/sequencer/))

**Structure:**
```
plugins/sequencer/
├── __init__.py
├── hook.py                     # Plugin registration
├── README.md                   # Documentation
├── app/
│   └── sequencer_service.py    # Backend REST API
└── gui/
    └── views/
        └── sequencer.vue       # Vue.js UI component
```

**REST API Endpoints:**
- `POST /plugin/sequencer/api/start` - Start sequence job
- `GET /plugin/sequencer/api/jobs` - List all jobs
- `GET /plugin/sequencer/api/status/{job_id}` - Get job details
- `POST /plugin/sequencer/api/retry/{job_id}` - Retry failed job
- `POST /plugin/sequencer/api/cancel/{job_id}` - Cancel running job
- `GET /plugin/sequencer/api/sequences` - List available sequences

### 3. Vue.js GUI ([plugins/sequencer/gui/views/sequencer.vue](caldera/plugins/sequencer/gui/views/sequencer.vue))

**Features:**
- Real-time job progress tracking (5s polling)
- Sequence template selection
- Campaign selection dropdown
- Retry/cancel controls
- Visual progress bars
- Failed step highlighting

### 4. Workflow Integration ([orchestrator/services/webhook_service.py](caldera/orchestrator/services/webhook_service.py))

Added `on_sequence_complete()` handler to `ConsolidatedWorkflowService`:
- Tags ELK alerts for all operations in sequence
- Sends Slack summary with success rate, duration, failed steps
- Generates combined ATT&CK coverage report
- Exports sequence PDF (placeholder implemented)
- Publishes to GitHub Pages

### 5. Example Sequences

**[examples/sequence-discovery.yml](caldera/examples/sequence-discovery.yml)**
- Discovery → Credential Access → Lateral Movement → Exfiltration Prep
- Demonstrates fact chaining, fallback, critical steps

**[data/sequences/lateral-movement.yml](caldera/data/sequences/lateral-movement.yml)**
- LSASS dump → Parse creds → Network discovery → PSExec → Persistence
- Shows complex credential chain with WMI fallback

## Installation & Setup

### 1. Enable the Plugin

Edit `conf/local.yml`:
```yaml
plugins:
  - sequencer
```

### 2. Install Dependencies (if needed)

```bash
cd orchestrator
pip install -r requirements.txt
```

### 3. Create Sequence Directory

```bash
mkdir -p data/sequences
cp examples/sequence-discovery.yml data/sequences/
```

### 4. Restart Caldera

```bash
python server.py --insecure
```

### 5. Verify Installation

```bash
# Run test suite
python test_sequencer.py

# Check plugin loaded
curl -H "KEY: ADMIN123" http://localhost:8888/api/rest?index=plugins | jq '.[] | select(.name=="Sequencer")'

# List sequences
curl http://localhost:8888/plugin/sequencer/api/sequences
```

## Usage Examples

### CLI Usage

```bash
# Create a campaign
caldera-orchestrator campaign create examples/campaign-spec.yml

# Run automated sequence
caldera-orchestrator campaign sequence campaign-12345 data/sequences/lateral-movement.yml

# With custom retry/timeout
caldera-orchestrator campaign sequence campaign-12345 sequence.yml \
  --max-retries 5 \
  --timeout 600
```

### GUI Usage

1. **Navigate to Sequencer**:
   - Open Caldera UI at `http://localhost:8888`
   - Click **Plugins** → **Sequencer**
   - Or access directly: `http://localhost:8888/plugin/sequencer/gui`

2. **Start a Sequence**:
   - Select campaign from dropdown
   - Choose sequence template (or upload custom YAML)
   - Adjust max retries / timeout
   - Click **Start Sequence**

3. **Monitor Progress**:
   - View real-time progress bar
   - See completed/failed steps
   - Click **Details** for full job info
   - **Retry** failed jobs or **Cancel** running jobs

### REST API Usage

```bash
# Start sequence job
curl -X POST http://localhost:8888/plugin/sequencer/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "campaign-123",
    "sequence_name": "lateral-movement",
    "max_retries": 3,
    "timeout": 300
  }'

# Monitor job status
JOB_ID="<returned-job-id>"
curl http://localhost:8888/plugin/sequencer/api/status/$JOB_ID

# List all jobs
curl http://localhost:8888/plugin/sequencer/api/jobs
```

## Sequence YAML Specification

### Minimal Example

```yaml
name: "Simple Discovery"
steps:
  - name: "Host Discovery"
    adversary_id: "discovery-adversary-uuid"
```

### Full Example with All Features

```yaml
name: "Advanced Sequence"
description: "Full-featured sequence example"

steps:
  - name: "Initial Discovery"
    adversary_id: "abc-123"
    agent_group: "red"
    planner: "atomic"
    source: "source-uuid"        # Optional fact source
    autonomous: 1                # Autonomy level
    critical: true               # Abort if fails
    on_fail: "retry"            # retry|skip|fallback
    
  - name: "Credential Access"
    adversary_id: "def-456"
    inherit_facts: true          # Receive facts from prior steps
    fact_filters:                # Filter which facts to inherit
      - "host.*"
      - "user.name"
    on_fail: "fallback"
    fallback_adversary_id: "ghi-789"  # Alternative adversary
    
  - name: "Lateral Movement"
    adversary_id: "jkl-012"
    inherit_facts: true
    fact_filters:
      - "user.password"
      - "host.hostname"
    on_fail: "skip"             # Continue even if fails
    critical: false
```

### Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Human-readable step name |
| `adversary_id` | string | Yes | - | Caldera adversary UUID |
| `agent_group` | string | No | `red` | Agent group |
| `planner` | string | No | `atomic` | Planner ID (atomic, batch, etc.) |
| `source` | string | No | - | Fact source UUID |
| `autonomous` | int | No | `1` | Autonomy level |
| `inherit_facts` | bool | No | `false` | Receive facts from prior steps |
| `fact_filters` | list | No | `[]` | Glob patterns for fact traits |
| `on_fail` | string | No | `retry` | Failure action (retry/skip/fallback) |
| `fallback_adversary_id` | string | No | - | Alternative adversary if fallback |
| `critical` | bool | No | `false` | Abort sequence on failure |

## Fact Chaining

Facts are passed between steps using trait filters:

```yaml
# Step 1 collects facts
- name: "Discovery"
  adversary_id: "..."
  # Collects: host.hostname, host.ip, user.name, etc.

# Step 2 inherits filtered facts
- name: "Lateral Movement"
  adversary_id: "..."
  inherit_facts: true
  fact_filters:
    - "host.*"      # Matches: host.hostname, host.ip, host.fqdn
    - "user.name"   # Exact match
```

**Common Fact Traits:**
- `host.*` - Hostname, IP, FQDN, MAC, etc.
- `user.*` - Username, password, SID, domain
- `domain.*` - Domain name, admin, DC, etc.
- `process.*` - Process name, PID, command line
- `file.*` - File path, name, hash, content
- `service.*` - Service name, display name, path

## Failure Recovery

### Retry Strategy

```yaml
on_fail: "retry"
```
- Exponential backoff: 2s, 4s, 8s, 16s, 30s (capped)
- Configurable max retries (default: 3)
- Retries same adversary/operation

### Tactic Fallback

```yaml
on_fail: "fallback"
fallback_adversary_id: "alternative-adversary-uuid"
```
- Switch to alternative adversary on failure
- Example: PSExec fails → try WMI

### Skip on Failure

```yaml
on_fail: "skip"
critical: false
```
- Continue to next step even if current fails
- Non-blocking for non-critical steps

### Critical Steps

```yaml
critical: true
```
- Abort entire sequence if this step fails
- Use for must-succeed steps (e.g., initial access)

## Testing

Run the test suite:

```bash
python test_sequencer.py
```

**Tests:**
1. CLI sequence_campaign function
2. Sequencer REST API
3. YAML validation
4. Retry logic
5. Fact filtering

## Troubleshooting

### Plugin not loading

```bash
# Check logs
tail -f logs/caldera.log | grep sequencer

# Verify plugin directory
ls -la plugins/sequencer/
```

### Sequences not appearing

```bash
# Check sequences directory
ls -la data/sequences/

# Verify YAML syntax
python -c "import yaml; print(yaml.safe_load(open('data/sequences/myseq.yml')))"
```

### Operations timeout

- Increase timeout: `--timeout 600`
- Check agent connectivity: `curl http://localhost:8888/api/v2/agents`
- Verify adversary exists: `curl http://localhost:8888/api/v2/adversaries`

### Facts not chaining

- Enable verbose logging: `--log-level DEBUG`
- Check operation report: `curl http://localhost:8888/api/v2/operations/{op_id}/report`
- Verify fact filters match actual trait names

## Performance Considerations

- **Poll interval**: 5 seconds (hardcoded in `sequence_campaign`)
- **Timeout**: Default 300s per operation (configurable)
- **Max retries**: Default 3 (configurable)
- **Memory**: Job tracking in-memory (not persisted across restarts)

## Next Steps

### Planned Enhancements

1. **Persistent job storage** - Save jobs to database
2. **WebSocket updates** - Real-time push notifications instead of polling
3. **Sequence templates** - Pre-built sequences for common attack paths
4. **Conditional branching** - "If technique X succeeds, run step Y"
5. **Parallel execution** - Run multiple steps concurrently
6. **Sequence editor** - Visual drag-drop sequence builder in GUI

### Integration Opportunities

- **SOAR platforms**: Trigger sequences from SecurityOnion, TheHive, Cortex
- **CI/CD pipelines**: Run sequences as part of security validation
- **Purple team exercises**: Coordinate red/blue actions via sequences

## Files Changed/Created

| File | Status | Lines | Description |
|------|--------|-------|-------------|
| orchestrator/cli.py | Modified | +370 | Added sequence_campaign() |
| plugins/sequencer/__init__.py | Created | 3 | Plugin package |
| plugins/sequencer/hook.py | Created | 73 | Plugin registration |
| plugins/sequencer/app/sequencer_service.py | Created | 324 | REST API backend |
| plugins/sequencer/gui/views/sequencer.vue | Created | 510 | Vue.js UI |
| plugins/sequencer/README.md | Created | 250 | Plugin documentation |
| orchestrator/services/webhook_service.py | Modified | +180 | Workflow integration |
| examples/sequence-discovery.yml | Created | 67 | Example sequence |
| data/sequences/lateral-movement.yml | Created | 75 | Example sequence |
| test_sequencer.py | Created | 275 | Test suite |

**Total:** ~2,130 lines of new code

## License

MIT License - See main Caldera project for details
