# Caldera Global Orchestration Pattern
## Technical Presentation for Team

**Date:** December 14, 2025  
**Project:** Multi-Phase Adversary Emulation Campaign Orchestration  
**Status:** Phases 1-4 Complete, Phases 5-9 Planned

---

## Executive Summary

We've built a **global orchestration pattern** for MITRE Caldera that transforms it from a manual, UI-driven tool into an **automated, API-first, enterprise-ready adversary emulation platform**. This enables:

- **Centralized campaign management** - Single YAML specification drives entire multi-phase operations
- **External integrations** - SIEM, Slack, webhooks, cloud providers
- **Audit trails** - Timeline tracking, governance workflows, compliance reporting
- **Scalability** - Orchestrate hundreds of agents across multiple environments
- **AI-readiness** - Foundation for AI-driven threat modeling and TTP evolution

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Campaign Specification (YAML)                   │
│  Defines: Environment, Targets, Adversary, Schedule, SIEM Tags  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Orchestrator CLI (cli.py)                      │
│  Commands: campaign create/start/stop, agent enroll, reports    │
└───┬───────┬─────────┬──────────┬──────────┬────────────┬───────┘
    │       │         │          │          │            │
    ▼       ▼         ▼          ▼          ▼            ▼
┌────────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌─────────┐ ┌──────────┐
│Caldera │ │Cloud│ │SIEM  │ │Slack/│ │Reports  │ │Branding  │
│REST API│ │ APIs│ │APIs  │ │N8N   │ │PDF/JSON │ │Theme UI  │
└────────┘ └─────┘ └──────┘ └──────┘ └─────────┘ └──────────┘
```

### **Data Flow:**
1. User creates campaign specification (YAML)
2. CLI validates and creates campaign object
3. Campaign object stored in Caldera DataService
4. Operations executed via Caldera REST API
5. Events published to webhooks/SIEM
6. Timeline and errors tracked
7. Reports generated at campaign completion

---

## Phase 1: Campaign Specification & Core Objects
### **What Problem Does This Solve?**

**Before:** Caldera operations were manually configured through the UI. No way to:
- Define a campaign as code
- Track state across multiple operations
- Persist campaign metadata
- Reproduce operations reliably

**After:** Campaign-as-code enables GitOps workflow for adversary emulation.

### **Components Built**

#### 1. **Campaign Specification Schema** (`schemas/campaign_spec.schema.json`)
```yaml
# Example campaign spec structure:
campaign_id: "550e8400-e29b-41d4-a716-446655440000"
name: "Q4 2025 Purple Team Exercise"
environment:
  name: "prod-finance-001"
  mode: "production"  # or "test"
targets:
  - platform: "windows"
    group: "finance-workstations"
    count: 10
adversary:
  profile: "apt29"
  techniques: ["T1003", "T1047", "T1059"]
siem:
  platform: "elasticsearch"
  tags:
    campaign_id: "${campaign_id}"
    environment: "prod-finance-001"
notifications:
  slack:
    webhook_url: "${SLACK_WEBHOOK}"
    channel: "#security-ops"
governance:
  approval_required: true
  approvers: ["CISO", "Security Lead"]
  max_duration_hours: 4
```

**How it works:**
- JSON Schema validates all fields before campaign creation
- Supports environment variable substitution for secrets (`${SLACK_WEBHOOK}`)
- Production mode requires explicit confirmation
- Can be version controlled in Git

**Code Location:** `schemas/campaign_spec.schema.json` (450 lines)

---

#### 2. **Campaign Object Model** (`app/objects/c_campaign.py`)

```python
class Campaign:
    """
    Central state tracker for multi-operation campaigns.
    Integrated with Caldera's DataService for persistence.
    """
    
    def __init__(self, campaign_id, name, environment, ...):
        self.campaign_id = campaign_id          # UUID
        self.name = name                        # Human-readable name
        self.status = 'created'                 # Status tracking
        self.operations = []                    # List of operation IDs
        self.agents = []                        # Enrolled agent IDs
        self.timeline = []                      # Event history
        self.errors = []                        # Error tracking
        self.reports = {}                       # Generated reports
        
    def update_status(self, new_status):
        """Update campaign status and add timeline event"""
        self.timeline.append({
            'timestamp': datetime.now(),
            'event': f'Status changed: {self.status} -> {new_status}',
            'status': new_status
        })
        self.status = new_status
        
    def add_operation(self, operation_id):
        """Track operations belonging to this campaign"""
        self.operations.append(operation_id)
        self.timeline.append({
            'timestamp': datetime.now(),
            'event': f'Operation added: {operation_id}',
            'operation_id': operation_id
        })
```

**Key Features:**
- **Timeline tracking**: Every status change, operation, agent, error logged
- **State machine**: 14 possible statuses (created → planning → running → completed)
- **Error logging**: Severity levels (info, warning, error, critical)
- **Persistence**: Saved to `data/campaigns/{campaign_id}.yml`

**Integration with Caldera:**
```python
# In app/service/data_svc.py:
DATA_FILE_GLOBS = [
    'abilities/**/*.yml',
    'adversaries/**/*.yml',
    'campaigns/**/*.yml',  # ← Added for campaign persistence
    # ...
]
```

**Why This Matters:**
- Campaign state survives Caldera restarts
- Audit trail for compliance
- Can query historical campaigns
- Enables report generation across all operations

**Code Location:** `app/objects/c_campaign.py` (250 lines)

---

### **Phase 1 Summary**

| Metric | Value |
|--------|-------|
| Files Created | 3 (schema, example, object model) |
| Lines of Code | ~700 lines |
| Integration Points | DataService, File Service |
| Testing | quick_test.py validates object model |

**Deliverable:** Campaign-as-code foundation for all future phases.

---

## Phase 2: Orchestrator CLI & Health Checks
### **What Problem Does This Solve?**

**Before:** 
- Manual clicking through Caldera UI
- No automated health checks
- Agent enrollment scripts manually created
- No way to script operations

**After:** 
- Command-line automation for CI/CD
- Pre-flight validation prevents failures
- Automated agent deployment to any platform

### **Components Built**

#### 1. **Orchestrator CLI** (`orchestrator/cli.py`)

```python
class CalderaOrchestratorCLI:
    """
    Main CLI for campaign orchestration.
    Wraps Caldera REST API v2 with user-friendly commands.
    """
    
    async def campaign_create(self, spec_path):
        """
        Create campaign from YAML specification.
        
        Flow:
        1. Load and validate YAML against schema
        2. Substitute environment variables
        3. Create Campaign object
        4. POST to Caldera REST API
        5. Save campaign spec to data/campaigns/
        """
        spec = self._load_campaign_spec(spec_path)
        campaign = Campaign(**spec)
        
        # Save to Caldera
        response = await self._api_request(
            'POST', 
            '/api/v2/campaigns',
            json=campaign.to_dict()
        )
        
        # Persist spec
        spec_file = f'data/campaigns/{campaign.campaign_id}.yml'
        with open(spec_file, 'w') as f:
            yaml.dump(spec, f)
            
        print(f"✅ Campaign created: {campaign.name}")
        print(f"   Campaign ID: {campaign.campaign_id}")
        return campaign
        
    async def campaign_start(self, campaign_id):
        """
        Start campaign operations.
        
        Flow:
        1. Retrieve campaign from DataService
        2. Check prerequisites (agents enrolled, adversary exists)
        3. Create operations for each target group
        4. Start operations via REST API
        5. Update campaign status to 'running'
        """
        # Implementation handles multi-operation orchestration
        
    async def agent_enroll(self, campaign_id, platform, output_path):
        """
        Generate platform-specific agent enrollment script.
        Calls generate_agent_enrollment.py
        """
```

**Available Commands:**

```bash
# Campaign management
python3 orchestrator/cli.py campaign create campaign_spec.yml
python3 orchestrator/cli.py campaign start <campaign_id>
python3 orchestrator/cli.py campaign status <campaign_id>
python3 orchestrator/cli.py campaign stop <campaign_id>

# Operation management
python3 orchestrator/cli.py operation create <campaign_id> --adversary apt29

# Agent enrollment
python3 orchestrator/cli.py agent enroll <campaign_id> --platform windows

# Reporting
python3 orchestrator/cli.py report generate <campaign_id> --format json

# Health validation
python3 orchestrator/cli.py health-check
```

**Rich Terminal UI:**
- Color-coded output (green=success, red=error, yellow=warning)
- Progress bars for long operations
- Formatted tables for status displays
- Interactive prompts for production mode

**Code Location:** `orchestrator/cli.py` (700 lines)

---

#### 2. **Health Check Script** (`orchestrator/health_check.py`)

```python
class CalderaHealthCheck:
    """
    Comprehensive pre-flight validation.
    Prevents campaign failures by checking all prerequisites.
    """
    
    def run_all_checks(self):
        """Execute all health checks and report results"""
        checks = [
            ('Web UI', self.check_web_ui),
            ('REST API v2', self.check_rest_api),
            ('API Keys', self.check_api_keys),
            ('Plugins', self.check_plugins),
            ('Agents', self.check_agents),
            ('Adversaries', self.check_adversaries),
            ('Abilities', self.check_abilities),
        ]
        
        results = []
        for name, check_func in checks:
            status, message = check_func()
            results.append((name, status, message))
            
        self._print_results_table(results)
        return all(status == 'PASS' for _, status, _ in results)
        
    def check_rest_api(self):
        """Validate REST API v2 is responding"""
        try:
            response = requests.get(f'{self.base_url}/api/v2/health')
            if response.status_code == 200:
                return 'PASS', 'REST API v2 responding'
            return 'FAIL', f'HTTP {response.status_code}'
        except Exception as e:
            return 'FAIL', str(e)
            
    def check_agents(self):
        """Check agent availability for campaign"""
        response = requests.get(
            f'{self.base_url}/api/v2/agents',
            headers={'KEY': self.api_key}
        )
        agents = response.json()
        
        if len(agents) == 0:
            return 'WARN', 'No agents deployed'
        
        active = [a for a in agents if a['last_seen'] < 60]
        return 'PASS', f'{len(active)}/{len(agents)} agents active'
```

**Checks Performed:**

| Check | Purpose | Failure Impact |
|-------|---------|----------------|
| **Web UI** | Caldera server running | Can't access any features |
| **REST API** | API v2 available | CLI commands will fail |
| **API Keys** | Authentication works | Unauthorized errors |
| **Plugins** | Required plugins loaded | Missing functionality |
| **Agents** | Agents deployed | No targets for operations |
| **Adversaries** | Adversary profiles exist | Can't create operations |
| **Abilities** | Techniques available | Empty operations |

**Output Example:**

```
╔═══════════════════════════════════════════╗
║     CALDERA HEALTH CHECK - PHASE 2       ║
╚═══════════════════════════════════════════╝

Check               Status    Details
─────────────────────────────────────────────
Web UI              ✅ PASS   Accessible at http://localhost:8888
REST API v2         ✅ PASS   Responding
Red Team API Key    ✅ PASS   Valid authentication
Blue Team API Key   ✅ PASS   Valid authentication
Plugins Loaded      ✅ PASS   15 plugins active
Agents              ⚠️  WARN   3/5 agents active (2 stale)
Adversaries         ✅ PASS   12 profiles available
Abilities           ✅ PASS   450 techniques loaded

Summary: 7 passed, 1 warning, 0 failed
Campaign environment: READY ✅
```

**Code Location:** `orchestrator/health_check.py` (500 lines)

---

#### 3. **Agent Enrollment Generator** (`orchestrator/generate_agent_enrollment.py`)

```python
class AgentEnrollmentGenerator:
    """
    Generate platform-specific agent deployment scripts.
    Injects campaign metadata for tracking.
    """
    
    def generate_windows_script(self, campaign_id, caldera_server):
        """
        Generate PowerShell script for Windows agent enrollment.
        
        Features:
        - Downloads Sandcat agent from Caldera
        - Configures contact method (HTTP/TCP/etc)
        - Injects campaign metadata as agent facts
        - Error handling and retry logic
        """
        script = f"""
# Caldera Agent Enrollment - Campaign {campaign_id}
# Generated: {datetime.now()}

$calderaServer = "{caldera_server}"
$campaignId = "{campaign_id}"
$contact = "http"

# Download Sandcat agent
$agentUrl = "$calderaServer/file/download"
$agentPath = "$env:TEMP\\sandcat.exe"

try {{
    Write-Host "Downloading Caldera agent..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $agentUrl -OutFile $agentPath
    
    # Start agent with campaign metadata
    Start-Process -FilePath $agentPath -ArgumentList `
        "-server", $calderaServer, `
        "-contact", $contact, `
        "-group", "campaign-$campaignId", `
        "-v"
        
    Write-Host "Agent enrolled successfully!" -ForegroundColor Green
    Write-Host "Campaign ID: $campaignId"
}} catch {{
    Write-Host "Enrollment failed: $_" -ForegroundColor Red
    exit 1
}}
"""
        return script
        
    def generate_docker_compose(self, campaign_id):
        """
        Generate Docker Compose file for multi-agent deployment.
        
        Use case: Deploy 10 agents across different networks
        """
        compose = {
            'version': '3.8',
            'services': {}
        }
        
        for i in range(1, 11):
            compose['services'][f'agent-{i}'] = {
                'image': 'caldera-sandcat:latest',
                'environment': {
                    'CALDERA_SERVER': '${CALDERA_SERVER}',
                    'CAMPAIGN_ID': campaign_id,
                    'AGENT_GROUP': f'campaign-{campaign_id}',
                    'CONTACT': 'http'
                },
                'networks': [f'agent-network-{i}']
            }
            
        return yaml.dump(compose)
        
    def generate_terraform_aws(self, campaign_id, region='us-east-1'):
        """
        Generate Terraform IaC for AWS EC2 agent deployment.
        
        Creates:
        - EC2 instances with Sandcat pre-installed
        - Security groups for Caldera communication
        - Campaign tags for billing/tracking
        """
        terraform = f"""
terraform {{
  required_version = ">= 1.0"
}}

provider "aws" {{
  region = "{region}"
}}

resource "aws_instance" "caldera_agent" {{
  count         = var.agent_count
  ami           = var.ami_id
  instance_type = "t3.micro"
  
  user_data = <<-EOF
    #!/bin/bash
    curl -o /tmp/sandcat.sh ${{var.caldera_server}}/file/download
    chmod +x /tmp/sandcat.sh
    /tmp/sandcat.sh -server ${{var.caldera_server}} \\
                    -group campaign-{campaign_id} \\
                    -contact http
  EOF
  
  tags = {{
    Name        = "Caldera-Agent-${{count.index}}"
    Campaign    = "{campaign_id}"
    ManagedBy   = "Terraform"
  }}
}}
"""
        return terraform
```

**Generated Scripts:**

1. **Windows PowerShell** (`.ps1`)
   - Downloads Sandcat from Caldera
   - Configures contact method
   - Sets campaign group
   - Error handling

2. **Linux/macOS Bash** (`.sh`)
   - Similar to Windows
   - Uses curl/wget
   - Systemd service creation

3. **Docker Compose** (`.yml`)
   - Multi-container deployment
   - Network isolation
   - Environment variable config

4. **Terraform AWS** (`.tf`)
   - Infrastructure-as-code
   - Auto-scaling groups
   - Campaign tagging for cost tracking

**Why This Matters:**
- **Scale**: Deploy 100s of agents with one command
- **Consistency**: Same configuration every time
- **Tracking**: Campaign metadata in agent facts
- **Automation**: CI/CD integration ready

**Code Location:** `orchestrator/generate_agent_enrollment.py` (600 lines)

---

### **Phase 2 Summary**

| Metric | Value |
|--------|-------|
| Files Created | 3 (CLI, health check, enrollment generator) |
| Lines of Code | ~1,800 lines |
| CLI Commands | 12 commands across 5 categories |
| Platform Support | Windows, Linux, macOS, Docker, AWS |
| Health Checks | 7 critical system validations |

**Deliverable:** Production-ready CLI for campaign automation.

---

## Phase 3: Webhook Publisher & SIEM Integration
### **What Problem Does This Solve?**

**Before:**
- Caldera events trapped inside the platform
- No way to alert SOC when operations complete
- Manual correlation with SIEM logs
- No audit trail in enterprise systems

**After:**
- Real-time event streaming to external systems
- SIEM integration for log correlation
- Slack notifications for team awareness
- Webhook-based automation (N8N, Zapier)

### **Components Built**

#### 1. **Webhook Publisher** (`orchestrator/webhook_publisher.py`)

```python
class WebhookPublisher:
    """
    Publish Caldera events to external webhooks.
    Handles retries, filtering, and statistics tracking.
    """
    
    def __init__(self):
        self.webhooks = []          # Registered webhooks
        self.event_queue = deque(maxlen=1000)  # Recent events
        self.stats = {
            'sent': 0,
            'failed': 0,
            'last_sent': None,
            'last_error': None
        }
        
    async def register_webhook(self, url, exchanges=None, queues=None):
        """
        Register webhook for event notifications.
        
        Args:
            url: Webhook endpoint
            exchanges: Filter by exchange (operation, agent, ability)
            queues: Filter by queue (created, started, finished)
        """
        webhook = {
            'url': url,
            'exchanges': exchanges or ['*'],  # All by default
            'queues': queues or ['*'],
            'retry_attempts': 3,
            'retry_delay': 5  # seconds
        }
        self.webhooks.append(webhook)
        
    async def publish_event(self, exchange, queue, event_data):
        """
        Publish event to all matching webhooks.
        
        Event structure:
        {
            'timestamp': '2025-12-14T10:30:00Z',
            'exchange': 'operation',
            'queue': 'finished',
            'campaign_id': '550e8400...',
            'operation_id': 'abc123...',
            'data': {
                'status': 'completed',
                'agent_count': 5,
                'ability_count': 12
            }
        }
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'exchange': exchange,
            'queue': queue,
            **event_data
        }
        
        self.event_queue.append(event)
        
        # Publish to matching webhooks
        for webhook in self._filter_webhooks(exchange, queue):
            await self._send_with_retry(webhook, event)
            
    async def _send_with_retry(self, webhook, event):
        """Send event with exponential backoff retry"""
        for attempt in range(webhook['retry_attempts']):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook['url'],
                        json=event,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            self.stats['sent'] += 1
                            self.stats['last_sent'] = datetime.now()
                            return
                            
            except Exception as e:
                if attempt == webhook['retry_attempts'] - 1:
                    self.stats['failed'] += 1
                    self.stats['last_error'] = str(e)
                else:
                    await asyncio.sleep(webhook['retry_delay'] * (2 ** attempt))
```

**Event Exchanges & Queues:**

| Exchange | Queues | Example Use Case |
|----------|--------|------------------|
| `operation` | created, started, paused, finished | Notify when operation completes |
| `agent` | connected, disconnected, heartbeat | Alert on agent loss |
| `ability` | executed, failed | Track technique success rate |
| `campaign` | created, started, completed, error | Campaign lifecycle notifications |

**Example Webhook Registration:**

```python
# In Caldera startup code:
webhook_publisher = WebhookPublisher()

# Register Slack webhook for campaign events
await webhook_publisher.register_webhook(
    url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
    exchanges=['campaign'],
    queues=['started', 'completed', 'error']
)

# Register N8N webhook for all operation events
await webhook_publisher.register_webhook(
    url='https://n8n.example.com/webhook/caldera',
    exchanges=['operation'],
    queues=['*']  # All queues
)
```

**Code Location:** `orchestrator/webhook_publisher.py` (400 lines, WebhookPublisher class)

---

#### 2. **SIEM Integration** (`orchestrator/webhook_publisher.py`)

```python
class SIEMIntegration:
    """
    Format Caldera events for specific SIEM platforms.
    Enables correlation with enterprise security logs.
    """
    
    def __init__(self, platform, endpoint, api_key):
        self.platform = platform  # elasticsearch, splunk, qradar, sentinel
        self.endpoint = endpoint
        self.api_key = api_key
        self.formatters = {
            'elasticsearch': self._format_elastic_event,
            'splunk': self._format_splunk_event,
            'qradar': self._format_qradar_event,
            'sentinel': self._format_sentinel_event
        }
        
    def _format_elastic_event(self, event):
        """
        Format for Elasticsearch/ELK Stack.
        
        Output:
        {
            "@timestamp": "2025-12-14T10:30:00.000Z",
            "event": {
                "kind": "event",
                "category": "security",
                "type": "info",
                "action": "operation-completed"
            },
            "caldera": {
                "campaign_id": "550e8400...",
                "operation_id": "abc123...",
                "agent_count": 5,
                "technique_count": 12
            },
            "tags": ["caldera", "purple-team", "apt29"]
        }
        """
        return {
            '@timestamp': event['timestamp'],
            'event': {
                'kind': 'event',
                'category': 'security',
                'type': 'info',
                'action': f"{event['exchange']}-{event['queue']}"
            },
            'caldera': event.get('data', {}),
            'tags': event.get('tags', [])
        }
        
    def _format_splunk_event(self, event):
        """
        Format for Splunk HEC (HTTP Event Collector).
        
        Output:
        {
            "time": 1702550400,
            "host": "caldera-server",
            "source": "caldera:orchestrator",
            "sourcetype": "caldera:campaign",
            "event": {
                "campaign_id": "550e8400...",
                "operation_id": "abc123...",
                "status": "completed"
            }
        }
        """
        return {
            'time': int(datetime.fromisoformat(event['timestamp']).timestamp()),
            'host': 'caldera-server',
            'source': 'caldera:orchestrator',
            'sourcetype': f"caldera:{event['exchange']}",
            'event': event.get('data', {})
        }
        
    async def send_event(self, event):
        """Send formatted event to SIEM"""
        formatter = self.formatters[self.platform]
        formatted = formatter(event)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint,
                json=formatted,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            ) as response:
                return response.status == 200
```

**Supported SIEM Platforms:**

1. **Elasticsearch/ELK**
   - Standard JSON format
   - @timestamp field
   - ECS (Elastic Common Schema) compliant

2. **Splunk**
   - HTTP Event Collector (HEC)
   - Epoch timestamps
   - Custom sourcetype for indexing

3. **QRadar**
   - LEEF (Log Event Extended Format)
   - Custom properties
   - Device event classification

4. **Microsoft Sentinel**
   - Azure Log Analytics format
   - Custom log table
   - KQL query ready

**Use Case: SIEM Correlation**

```
Timeline:
10:00:00 - Caldera operation starts (→ SIEM)
10:05:23 - Technique T1003 executed (→ SIEM)
10:05:25 - EDR alert: Credential dump detected (→ SIEM)
10:05:30 - SIEM correlates: Purple team test ✓

Without integration:
SOC sees alert, investigates, escalates → wasted 30 minutes
With integration:
SIEM auto-correlates campaign_id, suppresses alert ✓
```

**Code Location:** `orchestrator/webhook_publisher.py` (400 lines, SIEMIntegration class)

---

#### 3. **Orchestrator Plugin** (`plugins/orchestrator/hook.py`)

```python
"""
Caldera plugin that integrates orchestration features.
Provides REST API and web UI for webhook/campaign management.
"""

async def enable(services):
    """
    Plugin initialization called by Caldera on startup.
    
    Registers:
    - Webhook publisher service
    - REST API routes
    - Event listeners
    """
    app = services.get('app_svc').application
    
    # Initialize webhook publisher
    webhook_publisher = WebhookPublisher()
    await webhook_publisher.start()
    services['webhook_publisher'] = webhook_publisher
    
    # Register REST API routes
    app.router.add_route('GET', '/plugin/orchestrator/webhooks', 
                         get_webhooks)
    app.router.add_route('POST', '/plugin/orchestrator/webhooks', 
                         register_webhook)
    app.router.add_route('GET', '/plugin/orchestrator/campaigns', 
                         list_campaigns)
    app.router.add_route('POST', '/plugin/orchestrator/campaigns/{id}/notify',
                         send_campaign_notification)
    
    # Web UI dashboard
    app.router.add_route('GET', '/plugin/orchestrator/gui', 
                         orchestrator_dashboard)

async def get_webhooks(request):
    """GET /plugin/orchestrator/webhooks - List registered webhooks"""
    webhook_publisher = request.app['services']['webhook_publisher']
    return web.json_response({
        'webhooks': webhook_publisher.webhooks,
        'stats': webhook_publisher.stats
    })

async def register_webhook(request):
    """POST /plugin/orchestrator/webhooks - Register new webhook"""
    data = await request.json()
    webhook_publisher = request.app['services']['webhook_publisher']
    
    await webhook_publisher.register_webhook(
        url=data['url'],
        exchanges=data.get('exchanges'),
        queues=data.get('queues')
    )
    
    return web.json_response({'status': 'registered'})
```

**REST API Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/plugin/orchestrator/webhooks` | List all webhooks + stats |
| POST | `/plugin/orchestrator/webhooks` | Register new webhook |
| DELETE | `/plugin/orchestrator/webhooks/{id}` | Remove webhook |
| GET | `/plugin/orchestrator/campaigns` | List all campaigns |
| POST | `/plugin/orchestrator/campaigns/{id}/notify` | Manual event publish |
| GET | `/plugin/orchestrator/gui` | Web dashboard |

**Example API Usage:**

```bash
# Register Slack webhook
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK",
    "exchanges": ["campaign"],
    "queues": ["started", "completed"]
  }'

# List webhooks and stats
curl http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123"
  
# Response:
{
  "webhooks": [
    {
      "url": "https://hooks.slack.com/...",
      "exchanges": ["campaign"],
      "queues": ["started", "completed"]
    }
  ],
  "stats": {
    "sent": 145,
    "failed": 3,
    "last_sent": "2025-12-14T10:30:00Z"
  }
}
```

**Code Location:** `plugins/orchestrator/hook.py` (300 lines)

---

### **Phase 3 Summary**

| Metric | Value |
|--------|-------|
| Files Created | 2 (webhook publisher, plugin) |
| Lines of Code | ~700 lines |
| SIEM Platforms | 4 (Elasticsearch, Splunk, QRadar, Sentinel) |
| Event Types | 12+ exchanges/queues |
| REST Endpoints | 6 API routes |

**Deliverable:** Enterprise integration layer for external systems.

---

## Phase 4: Internal Branding Plugin
### **What Problem Does This Solve?**

**Before:**
- Default Caldera UI (generic open-source look)
- No corporate branding
- Can't customize for clients
- Difficult to white-label for MSP/consultancy use

**After:**
- **Triskele Labs branded UI**
- Professional corporate aesthetic
- Easy customization via config file
- White-label ready for client deployments

### **Components Built**

#### 1. **Branding Plugin Structure** (`plugins/branding/`)

```
plugins/branding/
├── hook.py                    # Plugin initialization (146 lines)
├── branding_config.yml        # Configuration (93 lines)
├── README.md                  # Documentation (444 lines)
├── static/
│   ├── css/
│   │   └── triskele_theme.css # Main stylesheet (472 lines)
│   └── img/
│       ├── triskele_logo.svg         # Header logo
│       └── triskele_logo_large.svg   # Login page logo
└── templates/
    ├── login.html             # Custom login page (300 lines)
    └── branding_admin.html    # Admin UI (370 lines)
```

---

#### 2. **Theme System** (`static/css/triskele_theme.css`)

```css
/*
 * Triskele Labs Theme for Caldera
 * Solid colors only - no gradients
 */

:root {
    /* Color Variables */
    --triskele-primary-dark: #020816;    /* Navy - headers, navigation */
    --triskele-primary-accent: #48CFA0;  /* Green - buttons, links */
    --triskele-neutral-light: #F5F7FA;   /* Light grey - background */
    --triskele-text-dark: #1F2937;       /* Dark text */
    --triskele-text-mid: #6B7280;        /* Mid grey - secondary text */
    
    /* Typography */
    --triskele-h1-size: 48px;
    --triskele-h2-size: 32px;
    --triskele-body-size: 16px;
    
    /* Spacing & Borders */
    --triskele-spacing-md: 24px;
    --triskele-radius-lg: 12px;
}

/* Global Styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
    background-color: var(--triskele-neutral-light);
    color: var(--triskele-text-dark);
}

/* Navigation */
#navbar {
    background: var(--triskele-primary-dark);
    border-bottom: 2px solid var(--triskele-primary-accent);
}

/* Buttons */
button {
    background: var(--triskele-primary-accent);
    color: white;
    border-radius: var(--triskele-radius-lg);
    transition: all 0.2s ease;
}

button:hover {
    background: #40BB90;  /* Slightly darker green */
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(72, 207, 160, 0.3);
}

/* Cards */
.card {
    background: white;
    border-radius: var(--triskele-radius-lg);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
    background: var(--triskele-primary-accent);
    color: white;
    padding: var(--triskele-spacing-md);
    border-radius: var(--triskele-radius-lg) var(--triskele-radius-lg) 0 0;
}

/* Hero Sections */
.hero {
    background: var(--triskele-primary-dark);
    color: white;
    border-bottom: 3px solid var(--triskele-primary-accent);
}
```

**Styled Components:**
- Navigation bars
- Buttons (primary, secondary, danger)
- Cards and panels
- Forms (inputs, selects, textareas)
- Tables
- Badges and status indicators
- Alerts (info, success, warning, error)
- Login page
- Hero sections

**Design Principles:**
✅ Solid colors (no gradients)  
✅ Triskele Labs green (#48CFA0)  
✅ Navy backgrounds (#020816)  
✅ Rounded corners (8-12px)  
✅ Subtle shadows for depth  
✅ Smooth animations (200ms)  
✅ Responsive design  

**Code Location:** `plugins/branding/static/css/triskele_theme.css` (472 lines)

---

#### 3. **Configuration System** (`branding_config.yml`)

```yaml
# Triskele Labs Branding Configuration

enabled: true
theme: triskele_labs

# Color Palette
colors:
  primary_dark: "#020816"       # Navy
  primary_accent: "#48CFA0"     # Triskele Labs green
  neutral_light: "#F5F7FA"      # Light background
  text_dark: "#1F2937"          # Dark text
  text_mid: "#6B7280"           # Mid grey text

# Typography
typography:
  font_family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto"
  h1_size: "48px"
  h2_size: "32px"
  body_size: "16px"

# Logo and Favicon
logo:
  header_logo: "/plugin/branding/static/img/triskele_logo.svg"
  login_logo: "/plugin/branding/static/img/triskele_logo_large.svg"
  favicon: "/plugin/branding/static/img/favicon.ico"

# Customization Text
customization:
  company_name: "Triskele Labs"
  tagline: "Advanced Cybersecurity Services"
  login_title: "Caldera Platform"
  login_message: "Secure Access to Adversary Emulation Platform"
  footer_text: "© 2025 Triskele Labs. All rights reserved."

# Feature Toggles
features:
  show_company_logo: true
  custom_login_page: true
  custom_dashboard: true
  rounded_corners: true
  card_shadows: true
```

**How to Customize:**

```bash
# Edit colors
vim plugins/branding/branding_config.yml

# Change primary accent to blue:
colors:
  primary_accent: "#0066CC"

# Update company name
customization:
  company_name: "Your Company"
  tagline: "Your Tagline"

# Restart Caldera to apply
python3 server.py
```

**Code Location:** `plugins/branding/branding_config.yml` (93 lines)

---

#### 4. **Plugin Initialization** (`hook.py`)

```python
"""
Branding Plugin for Caldera
Provides theme customization and REST API for configuration.
"""

async def enable(services):
    """
    Enable branding plugin on Caldera startup.
    
    Registers:
    - Static file routes (CSS, images)
    - REST API endpoints
    - Configuration service
    """
    app = services.get('app_svc').application
    plugin_dir = Path(__file__).parent
    
    # Load branding configuration
    config_path = plugin_dir / 'branding_config.yml'
    with open(config_path, 'r') as f:
        branding_config = yaml.safe_load(f)
    
    # Store in services for access across Caldera
    services['branding_config'] = branding_config
    
    # Register static files (CSS, images)
    static_dir = plugin_dir / 'static'
    app.router.add_static(
        '/plugin/branding/static/', 
        static_dir, 
        name='branding_static'
    )
    
    # Register REST API routes
    app.router.add_route('GET', '/plugin/branding/api/config', 
                         get_branding_config)
    app.router.add_route('POST', '/plugin/branding/api/config', 
                         update_branding_config)
    app.router.add_route('GET', '/plugin/branding/gui', 
                         branding_admin_gui)
    
    log.info(f"Branding plugin enabled: {branding_config['theme']}")
    log.info(f"Colors: {branding_config['colors']}")

async def get_branding_config(request):
    """GET /plugin/branding/api/config - Return current config"""
    branding_config = request.app['services']['branding_config']
    return web.json_response(branding_config)

async def update_branding_config(request):
    """POST /plugin/branding/api/config - Update configuration"""
    data = await request.json()
    
    # Update config in memory
    branding_config = request.app['services']['branding_config']
    branding_config.update(data)
    
    # Save to file
    config_path = Path(__file__).parent / 'branding_config.yml'
    with open(config_path, 'w') as f:
        yaml.dump(branding_config, f)
    
    return web.json_response({'status': 'updated'})
```

**REST API:**

```bash
# Get current branding config
curl http://localhost:8888/plugin/branding/api/config \
  -H "KEY: ADMIN123"

# Update colors
curl -X POST http://localhost:8888/plugin/branding/api/config \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "colors": {
      "primary_accent": "#0066CC"
    }
  }'
```

**Code Location:** `plugins/branding/hook.py` (146 lines)

---

#### 5. **Admin UI** (`templates/branding_admin.html`)

```html
<!-- Branding Configuration Dashboard -->
<!DOCTYPE html>
<html>
<head>
    <title>Branding Admin | Caldera</title>
    <link rel="stylesheet" href="/plugin/branding/static/css/triskele_theme.css">
</head>
<body>
    <div class="hero">
        <h1>🎨 Branding Configuration</h1>
        <p>Customize Caldera's appearance</p>
    </div>
    
    <div class="admin-container">
        <!-- Color Picker -->
        <div class="card">
            <div class="card-header">Color Palette</div>
            <div class="card-body">
                <label>Primary Accent (Green)</label>
                <input type="color" id="primary_accent" value="#48CFA0">
                <input type="text" id="primary_accent_text" value="#48CFA0">
                
                <!-- More color pickers... -->
            </div>
        </div>
        
        <!-- Live Preview -->
        <div class="card">
            <div class="card-header">Live Preview</div>
            <div class="preview-section">
                <h1>Heading 1 Preview</h1>
                <button>Primary Button</button>
                <span class="badge-success">Success Badge</span>
            </div>
        </div>
        
        <!-- Save/Reset Buttons -->
        <button onclick="saveConfig()">💾 Save Configuration</button>
        <button class="secondary" onclick="resetToDefault()">🔄 Reset</button>
    </div>
    
    <script>
        // Real-time color picker sync
        document.getElementById('primary_accent').addEventListener('input', (e) => {
            document.documentElement.style.setProperty(
                '--triskele-primary-accent', 
                e.target.value
            );
        });
        
        // Save configuration via API
        async function saveConfig() {
            const config = {
                colors: {
                    primary_accent: document.getElementById('primary_accent').value
                }
            };
            
            await fetch('/plugin/branding/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            
            alert('Configuration saved!');
        }
    </script>
</body>
</html>
```

**Features:**
- Real-time color preview
- Typography configuration
- Logo upload (planned)
- Save/reset functionality
- Live CSS variable updates

**Access:** `http://localhost:8888/plugin/branding/gui`

**Code Location:** `plugins/branding/templates/branding_admin.html` (370 lines)

---

### **Phase 4 Summary**

| Metric | Value |
|--------|-------|
| Files Created | 8 files |
| Lines of Code | 1,828 lines |
| - Python | 146 lines |
| - CSS | 472 lines |
| - HTML | 673 lines |
| - YAML | 93 lines |
| - Documentation | 444 lines |
| REST Endpoints | 3 (get config, update config, admin UI) |
| Styled Components | 15+ (buttons, cards, forms, tables, etc) |

**Deliverable:** Production-ready Triskele Labs branded Caldera UI.

---

## How It All Fits Together

### **End-to-End Campaign Flow**

```
1. Define Campaign (YAML)
   ↓
   schemas/campaign_spec_example.yml
   ↓
2. Create Campaign (CLI)
   ↓
   orchestrator/cli.py campaign create
   ↓
3. Campaign Object Created
   ↓
   app/objects/c_campaign.py
   ↓
4. Stored in DataService
   ↓
   app/service/data_svc.py
   ↓
5. Health Check (Pre-flight)
   ↓
   orchestrator/health_check.py
   ↓
6. Generate Enrollment Scripts
   ↓
   orchestrator/generate_agent_enrollment.py
   ↓
7. Deploy Agents
   ↓
   Windows/Linux/Docker/AWS
   ↓
8. Start Operations (CLI)
   ↓
   orchestrator/cli.py campaign start
   ↓
9. Operations Execute (Caldera Core)
   ↓
   REST API v2: /api/v2/operations
   ↓
10. Events Published
    ↓
    orchestrator/webhook_publisher.py
    ↓
11. External Systems Notified
    ↓
    SIEM / Slack / N8N
    ↓
12. Campaign Completes
    ↓
    Status: completed
    ↓
13. Reports Generated
    ↓
    orchestrator/cli.py report generate
    ↓
14. View in Branded UI
    ↓
    plugins/branding/ theme applied
```

---

### **Integration Points**

#### **With Caldera Core:**

1. **DataService** (`app/service/data_svc.py`)
   - Campaigns stored alongside operations/agents/adversaries
   - Persisted to `data/campaigns/*.yml`
   - Loaded on Caldera startup

2. **REST API v2** (All orchestrator commands)
   - CLI wraps `/api/v2/*` endpoints
   - Authentication via API keys
   - JSON responses parsed by CLI

3. **Plugin System** (`plugins/orchestrator/`, `plugins/branding/`)
   - Hooks into Caldera application service
   - Registers routes, services, static files
   - Event service integration

4. **File Service**
   - Campaign specs saved/loaded
   - Reports generated to `data/results/`
   - Logs to `logs/orchestrator.log`

#### **With External Systems:**

1. **SIEM Platforms**
   - Elasticsearch: Direct JSON indexing
   - Splunk: HEC endpoint
   - QRadar: LEEF format
   - Sentinel: Azure Log Analytics

2. **Notification Systems**
   - Slack: Webhook API
   - N8N: Workflow automation
   - Email: SMTP (planned)

3. **Cloud Providers**
   - AWS: Terraform templates
   - Azure: ARM templates (planned)
   - GCP: Deployment Manager (planned)

4. **CI/CD Pipelines**
   - GitHub Actions: CLI commands in workflows
   - Jenkins: Scripted pipeline integration
   - GitLab CI: YAML pipeline definitions

---

## Phases 5-9: Roadmap

### **Phase 5: Standalone Enrollment API Service** (Next)
- FastAPI REST service
- Dynamic agent registration
- CI/CD integration examples
- **Estimated:** 12-16 hours

### **Phase 6: PDF Reporting System**
- Report aggregation across operations
- ATT&CK Navigator layer generation
- PDF template with charts
- **Estimated:** 20-24 hours

### **Phase 7: Slack/N8N Integration**
- Slack bot with commands
- N8N workflow templates
- Operation lifecycle notifications
- **Estimated:** 16-20 hours

### **Phase 8: Governance & Compliance Framework**
- RBAC policy enforcement
- Approval workflow engine
- Audit logging
- Prometheus/Grafana dashboards
- **Estimated:** 24-32 hours

### **Phase 9: AI-Driven TTP Evolution**
- LLM ability generation
- Threat model gap analysis
- Regression testing framework
- Automated adversary composition
- **Estimated:** 40-60 hours

---

## Benefits & Impact

### **For Purple Teams:**
✅ Automated campaign execution  
✅ Consistent testing across environments  
✅ Audit trail for compliance  
✅ SIEM correlation out-of-box  
✅ Scalable to 100s of agents  

### **For Security Operations:**
✅ Real-time alerts via Slack/SIEM  
✅ Reduced false positives (campaign tagging)  
✅ Metrics dashboard  
✅ Historical campaign analysis  
✅ Integration with SOC tools  

### **For Management:**
✅ Professional branded UI  
✅ Executive summary reports  
✅ Compliance documentation  
✅ Cost tracking via cloud tags  
✅ ROI metrics  

---

## Questions & Discussion

**Key Points to Emphasize:**

1. **Not just a UI**: This is infrastructure automation
2. **GitOps-ready**: Everything defined as code
3. **Enterprise integration**: SIEM, Slack, cloud providers
4. **Audit trail**: Every event logged with timeline
5. **Scalable**: Handles 100s of agents, multiple environments
6. **Extensible**: Plugin architecture for future additions

**Demo Opportunities:**

- Show campaign spec → campaign creation → operation execution
- Live webhook publishing to Slack
- SIEM event correlation
- Branded UI customization
- Health check validation

---

## Next Steps

1. **Review Phase 1-4 implementation**
2. **Discuss Phase 5 requirements** (Enrollment API)
3. **Prioritize Phases 6-9** based on business needs
4. **Assign resources** for remaining work
5. **Set timeline** for completion

**Estimated Remaining Work:** 120-164 hours (Phases 5-9)

---

## Appendix: Code Statistics

```
Phase 1-4 Totals:
- Python Code:         ~2,800 lines
- CSS:                 ~500 lines
- HTML:                ~700 lines
- YAML/JSON:           ~700 lines
- Documentation:       ~5,000 lines
- Total:               ~9,700 lines

Files Created:         25+ files
Directories:           8 directories
Git Commits:           7 commits
```

---

**End of Presentation**

*For questions or detailed walkthrough of any component, please ask!*
