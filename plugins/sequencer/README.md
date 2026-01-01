# Sequencer Plugin

Automated multi-step operation sequencing with failure recovery and fact chaining for MITRE Caldera.

## Features

- ✅ **Automated Sequencing**: Chain multiple operations with fact passing
- 🔄 **Failure Recovery**: Exponential backoff retry with configurable max attempts
- 🎯 **Tactic Fallback**: Fallback to alternative adversary profiles on failure
- 📊 **Real-time Tracking**: Monitor progress via REST API or Vue.js GUI
- 🔗 **Fact Chaining**: Filter and pass facts between operations (e.g., credentials, hosts)
- ⚡ **Async Execution**: Non-blocking background job processing

## Installation

1. **Enable the plugin** in `conf/local.yml`:
```yaml
plugins:
  - sequencer
```

2. **Restart Caldera**:
```bash
python server.py --insecure
```

3. **Access GUI**:
   - Navigate to Caldera UI → Plugins → Sequencer
   - Or via Magma: Click "Sequencer" tab

## Usage

### CLI Usage

```bash
# Run a sequence
caldera-orchestrator campaign sequence <campaign_id> <sequence_file.yml>

# With custom retries/timeout
caldera-orchestrator campaign sequence campaign-123 sequence.yml \
  --max-retries 5 \
  --timeout 600
```

### GUI Usage

1. Navigate to **Sequencer** plugin in Caldera UI
2. Select a campaign
3. Choose a sequence template (or upload custom YAML)
4. Click **Start Sequence**
5. Monitor real-time progress

### REST API

#### Start Sequence
```bash
POST /plugin/sequencer/api/start
{
  "campaign_id": "campaign-123",
  "sequence_name": "discovery",
  "max_retries": 3,
  "timeout": 300
}
```

#### Get Job Status
```bash
GET /plugin/sequencer/api/status/{job_id}
```

#### List Jobs
```bash
GET /plugin/sequencer/api/jobs
```

#### Cancel Job
```bash
POST /plugin/sequencer/api/cancel/{job_id}
```

#### Retry Failed Job
```bash
POST /plugin/sequencer/api/retry/{job_id}
```

## Sequence YAML Format

```yaml
name: "Discovery Phase"
description: "Automated reconnaissance with fact chaining"

steps:
  - name: "Host Discovery"
    adversary_id: "discovery-adversary-uuid"
    agent_group: "red"
    planner: "atomic"
    critical: true  # Abort sequence if this fails
    on_fail: "retry"  # Options: retry|skip|fallback
    
  - name: "Credential Dumping"
    adversary_id: "credential-adversary-uuid"
    agent_group: "red"
    planner: "atomic"
    inherit_facts: true  # Receive facts from previous steps
    fact_filters:
      - "host.*"
      - "domain.*"
    on_fail: "fallback"
    fallback_adversary_id: "credential-light-uuid"
    critical: false
    
  - name: "Lateral Movement"
    adversary_id: "lateral-adversary-uuid"
    inherit_facts: true
    fact_filters:
      - "user.password"
      - "user.name"
      - "host.hostname"
    on_fail: "skip"  # Continue even if fails
```

### Step Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Human-readable step name |
| `adversary_id` | Yes | Caldera adversary profile UUID |
| `agent_group` | No | Agent group (default: `red`) |
| `planner` | No | Planner ID (default: `atomic`) |
| `source` | No | Fact source ID |
| `inherit_facts` | No | Receive facts from prior steps (default: `false`) |
| `fact_filters` | No | Glob patterns for fact traits (e.g., `["host.*", "user.*"]`) |
| `on_fail` | No | Failure action: `retry`, `skip`, `fallback` (default: `retry`) |
| `fallback_adversary_id` | No | Alternative adversary if `on_fail: fallback` |
| `critical` | No | Abort sequence on failure (default: `false`) |

## Fact Filtering

Facts are filtered using glob-style patterns:

```yaml
fact_filters:
  - "host.*"              # All host traits
  - "user.name"           # Exact match
  - "process.command_line" # Process commands
  - "file.path"           # File paths
```

Common fact traits:
- `host.hostname`, `host.ip`, `host.fqdn`
- `user.name`, `user.password`, `user.sid`
- `domain.name`, `domain.admin`
- `process.name`, `process.pid`, `process.command_line`
- `file.path`, `file.name`

## Examples

### Discovery Sequence
See `caldera/examples/sequence-discovery.yml`

### Credential Theft Sequence
```yaml
name: "Credential Theft Chain"
steps:
  - name: "LSASS Dump"
    adversary_id: "lsass-dump-uuid"
    critical: true
    on_fail: "retry"
    
  - name: "Parse Credentials"
    adversary_id: "parse-creds-uuid"
    inherit_facts: true
    fact_filters: ["file.path"]
```

## Integration with Workflow Service

The sequencer automatically notifies `ConsolidatedWorkflowService` on completion:

```python
# In workflow_service.py
async def on_sequence_complete(self, job_id: str, job: dict):
    # Trigger ELK tagging
    # Send Slack notification
    # Generate PDF report
```

## Troubleshooting

### Sequence not starting
- Verify campaign ID exists: `caldera-orchestrator campaign status <id>`
- Check sequence YAML is valid: `python -c "import yaml; yaml.safe_load(open('seq.yml'))"`

### Operations timeout
- Increase timeout: `--timeout 600`
- Check agent connectivity: `GET /api/v2/agents`

### Facts not chaining
- Verify `inherit_facts: true` is set
- Check fact filters match actual trait names
- View operation report: `GET /api/v2/operations/{op_id}/report`

## Development

### Add Custom Fact Filters

Edit `orchestrator/cli.py`:
```python
def _filter_facts(self, facts: Dict, filters: list) -> list:
    # Add custom filtering logic
```

### Extend Job Tracking

Edit `plugins/sequencer/app/sequencer_service.py`:
```python
async def _run_sequence_job(self, job_id: str):
    # Add custom event handlers
```

## License

MIT License - See main Caldera project for details
