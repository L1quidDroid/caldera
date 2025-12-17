# GitHub Copilot Instructions for CALDERA

**Project**: MITRE CALDERA v5.0.0 (Triskele Labs Enhanced)  
**Language**: Python 3.10+, JavaScript (Node.js), Go  
**Framework**: aiohttp (async web framework)  
**Last Updated**: December 18, 2025

---

## Project Overview

CALDERA is a cyber security platform for adversary emulation, red teaming, and incident response built on the MITRE ATT&CK framework. This enhanced version includes global orchestration capabilities for multi-environment campaigns.

**Deployment Objective**: Create a working proof of concept designed for Azure VM environments (Windows/Linux). All code, configurations, and deployment scripts must be portable and replicable when cloned to different VM directories. Development targets VM infrastructure with streamlined deployment scripts. Local development references have been removed in favour of VM-only production deployment.

**Current State**: Production-ready VM deployment with Phase 1-6 orchestrator, ELK stack, Filebeat logging, and Triskele Labs branding plugin. All redundant local testing files and documentation removed (December 18, 2025).

### Key Technologies
- **Backend**: Python 3.10+ with aiohttp (async)
- **Frontend**: VueJS 3 (Magma plugin), Alpine.js, Bulma CSS
- **Database**: In-memory object store with disk persistence
- **Agents**: Go (Sandcat), PowerShell, Bash
- **API**: REST API v2 with marshmallow schemas
- **Target Platform**: Azure Windows VM (production) with Linux/macOS support (development)

---

## Architecture Patterns

### 1. Service Layer Pattern

All services inherit from `BaseService` and follow dependency injection:

```python
from app.utility.base_service import BaseService

class MyService(BaseService):
    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')
        self.log = self.add_service('my_svc', self)
    
    async def my_method(self):
        data = await self.data_svc.locate('abilities')
        return data
```

**Key Services**:
- `app_svc` - Application lifecycle
- `data_svc` - Object storage and retrieval
- `auth_svc` - Authentication and authorization
- `file_svc` - File operations and compilation
- `contact_svc` - Agent C2 communication
- `planning_svc` - Operation planning
- `rest_svc` - REST API operations

### 2. Object Model

All persistent objects inherit from `BaseObject`:

```python
from app.utility.base_object import BaseObject

class MyObject(BaseObject):
    @property
    def unique(self):
        return self.hash('%s' % self.name)
    
    @property
    def display(self):
        return dict(
            name=self.name,
            description=self.description
        )
    
    def store(self, ram):
        return dict(
            name=self.name,
            created=self.created.strftime('%Y-%m-%d %H:%M:%S')
        )
```

**Core Objects**:
- `c_agent.py` - Adversary simulation agent
- `c_ability.py` - Atomic capability/technique
- `c_adversary.py` - Collection of abilities
- `c_operation.py` - Execution of adversary against agents
- `c_planner.py` - Decision logic for ability execution
- `c_objective.py` - Goal-based constraints

### 3. Plugin System

Plugins extend CALDERA with isolated functionality:

```python
name = 'MyPlugin'
description = 'Plugin description'
address = '/plugin/myplugin/gui'

async def initialize(app, services):
    my_service = MyService(services)
    app.router.add_route('GET', '/plugin/myplugin/health', my_service.health)
```

**Plugin Structure**:
```
plugins/myplugin/
├── hook.py              # Entry point
├── app/
│   └── myplugin_svc.py  # Service logic
├── data/                # Plugin data
├── templates/           # Jinja2 templates
└── static/              # CSS/JS assets
```

### 4. API v2 Pattern

API endpoints use marshmallow schemas and handler classes:

```python
from aiohttp import web
from marshmallow import Schema, fields
from app.api.v2.handlers.base_api import BaseApi

class MySchema(Schema):
    name = fields.String(required=True)
    value = fields.Integer()

class MyApi(BaseApi):
    def __init__(self, services):
        super().__init__(auth_svc=services['auth_svc'])
        self.my_svc = services['my_svc']
        self.schema = MySchema()
    
    def add_routes(self, app: web.Application):
        app.router.add_get('/api/v2/myresource', self.get_resources)
        app.router.add_post('/api/v2/myresource', self.create_resource)
    
    async def get_resources(self, request: web.Request):
        access = await self.get_request_permissions(request)
        resources = await self.my_svc.get_all(access=access)
        return web.json_response(resources)
```

---

## Coding Conventions

### 1. Async/Await Usage

**Always** use async/await for I/O operations:

```python
# Good
async def get_data(self):
    agents = await self.data_svc.locate('agents')
    return agents

# Bad - blocking call
def get_data(self):
    agents = self.data_svc.locate('agents')
    return agents
```

### 2. Error Handling

Use try/except with specific exceptions and logging:

```python
async def risky_operation(self):
    try:
        result = await self.external_api_call()
        return result
    except aiohttp.ClientError as e:
        self.log.error(f"API call failed: {e}")
        raise web.HTTPServiceUnavailable(reason="External service unavailable")
    except Exception as e:
        self.log.error(f"Unexpected error: {e}")
        raise
```

### 3. Authentication

All API endpoints require authentication. Use decorators:

```python
from app.service.auth_svc import for_all_public_methods, check_authorization

@for_all_public_methods(check_authorization)
class MyApi:
    async def protected_endpoint(self, request):
        pass
```

### 4. Logging

Use the service logger:

```python
class MyService(BaseService):
    def __init__(self, services):
        self.log = self.create_logger('my_service')
    
    async def do_something(self):
        self.log.info("Starting operation")
        self.log.debug("Debug details: %s", data)
        self.log.error("Error occurred: %s", error)
```

### 5. Configuration

Load config from `conf/default.yml`:

```python
config = self.get_config('plugin_name')
api_key = config.get('api_key', 'default_value')
```

### 6. File Paths

Always use `pathlib.Path` for cross-platform compatibility:

```python
from pathlib import Path

# Good
data_dir = Path('data') / 'campaigns'
file_path = data_dir / 'campaign.yml'

# Bad - not cross-platform
data_dir = 'data/campaigns'
file_path = data_dir + '/campaign.yml'
```

---

## Common Patterns

### 1. Accessing Services

```python
other_svc = self.get_service('other_svc')
data = await other_svc.method()

services = app['services']
data_svc = services.get('data_svc')
```

### 2. Object Storage

```python
await self.data_svc.store(my_object)

all_agents = await self.data_svc.locate('agents')

agent = await self.data_svc.locate('agents', match=dict(paw='agent-id'))

await self.data_svc.remove('agents', match=dict(paw='agent-id'))
```

### 3. Creating Operations

```python
operation = Operation(
    name='my-operation',
    agents=agents,
    adversary=adversary,
    planner=planner,
    source=source
)
await self.data_svc.store(operation)
await operation.run(self)
```

### 4. Adding Abilities

```python
ability = Ability(
    ability_id='12345678-1234-1234-1234-123456789012',
    name='My Ability',
    description='What it does',
    tactic='discovery',
    technique_id='T1082',
    technique_name='System Information Discovery',
    executors=[
        Executor(
            name='sh',
            platform='linux',
            command='uname -a',
            cleanup=None
        )
    ]
)
await self.data_svc.store(ability)
```

### 5. Agent Communication

```python
class MyContact:
    async def contact(self, message):
        agent_data = json.loads(message)
        agent = await self.agent_svc.handle_heartbeat(agent_data)
        instructions = await self.instruction_svc.get_instructions(agent)
        return instructions
```

---

## Testing Patterns

### 1. Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def my_service():
    services = {
        'data_svc': AsyncMock(),
        'auth_svc': AsyncMock()
    }
    return MyService(services)

@pytest.mark.asyncio
async def test_my_method(my_service):
    my_service.data_svc.locate.return_value = [mock_agent]
    
    result = await my_service.my_method()
    
    assert len(result) == 1
    my_service.data_svc.locate.assert_called_once()
```

### 2. Integration Tests

```python
async def test_api_endpoint(aiohttp_client):
    app = await create_app()
    client = await aiohttp_client(app)
    
    response = await client.get('/api/v2/agents', headers={'KEY': 'ADMIN123'})
    
    assert response.status == 200
    data = await response.json()
    assert isinstance(data, list)
```

---

## Orchestrator Pattern (Triskele Labs Extension)

### 1. Campaign Specifications

```yaml
campaign_id: my-campaign-001
name: "My Campaign"
description: "Campaign description"

environment:
  infra_type: local
  caldera_url: http://localhost:8888

targets:
  groups: ["red"]
  platforms: ["linux", "darwin"]
  tags:
    environment: production
    test_run_id: test-001

adversary: discovery-adversary
planner: atomic
auto_cleanup: true

phases:
  - name: "Discovery"
    adversary: discovery-adversary
    duration: "30m"
```

### 2. Orchestrator CLI

```bash
python orchestrator/cli.py campaign list
python orchestrator/cli.py campaign run my-campaign-001
python orchestrator/cli.py campaign status my-campaign-001
python orchestrator/cli.py campaign stop my-campaign-001
```

### 3. Webhook Integration

```python
from orchestrator.webhook_publisher import WebhookPublisher

publisher = WebhookPublisher(caldera_url, api_key)
await publisher.register_webhook(
    url="https://webhook.site/unique-id",
    exchanges=["operation", "campaign"],
    queues=["*"]
)

await publisher.publish_event(
    exchange="operation",
    routing_key="operation.created",
    data=operation_data
)
```

### 4. Enrollment API

```python
POST /plugin/enrollment/enroll
{
    "platform": "linux",
    "campaign_id": "my-campaign-001",
    "tags": ["production"],
    "hostname": "target-host"
}

{
    "id": "enroll_abc123",
    "bootstrap_command": "curl ... | bash"
}
```

---

## Security Best Practices

### 1. API Keys

```python
api_key = self.get_config('api_key')

if not self.auth_svc.validate_key(request):
    raise web.HTTPUnauthorized()
```

### 2. Input Validation

```python
from marshmallow import Schema, fields, validate

class InputSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    value = fields.Integer(validate=validate.Range(min=0, max=1000))

try:
    data = schema.load(request_data)
except ValidationError as e:
    raise web.HTTPBadRequest(reason=str(e))
```

### 3. File Operations

```python
from pathlib import Path

def safe_file_path(base_dir: Path, filename: str) -> Path:
    safe_name = filename.replace('..', '').replace('/', '')
    full_path = base_dir / safe_name
    
    if not full_path.resolve().is_relative_to(base_dir.resolve()):
        raise ValueError("Invalid file path")
    
    return full_path
```

---

## Performance Considerations

### 1. Async Best Practices

```python
# Good - concurrent execution
import asyncio

results = await asyncio.gather(
    self.operation_a(),
    self.operation_b(),
    self.operation_c()
)

# Bad - sequential execution
result_a = await self.operation_a()
result_b = await self.operation_b()
result_c = await self.operation_c()
```

### 2. Caching

```python
from functools import lru_cache

class MyService:
    @lru_cache(maxsize=128)
    def expensive_computation(self, param):
        return result
```

### 3. Database Queries

```python
# Good - single query with filter
agents = await self.data_svc.locate('agents', match={'group': 'red'})

# Bad - load all then filter in Python
all_agents = await self.data_svc.locate('agents')
red_agents = [a for a in all_agents if a.group == 'red']
```

---

## Documentation Standards

### 1. Docstrings

```python
async def my_method(self, param1: str, param2: int) -> dict:
    """
    Brief description of what the method does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        dict: Description of return value
    
    Raises:
        ValueError: When param1 is invalid
        aiohttp.ClientError: When external API fails
    """
    pass
```

### 2. Code Comments

```python
# Good - explains WHY
# Retry 3 times because external API is flaky
for attempt in range(3):
    try:
        return await self.api_call()
    except Exception:
        if attempt == 2:
            raise

# Bad - explains WHAT
# Loop 3 times
for attempt in range(3):
    ...
```

---

## Common Gotchas

### 1. Access Levels

```python
from app.utility.base_world import BaseWorld

if access >= BaseWorld.Access.RED:
```

### 2. Object Serialization

```python
class MyObject(BaseObject):
    def store(self, ram):
        return self.__dict__
    
    @property
    def display(self):
        return dict(name=self.name)
```

### 3. Plugin Loading Order

```python
async def initialize(app, services):
    await asyncio.sleep(1)
    other_plugin = app.get('plugin_name')
```

---

## Debugging Tips

### 1. Enable Debug Logging

```bash
python server.py --insecure --log DEBUG
```

### 2. Inspect Object Store

```python
from app.service.app_svc import AppService

app_svc = AppService.get_service('app_svc')
data_svc = AppService.get_service('data_svc')

agents = await data_svc.locate('agents')
print([a.display for a in agents])
```

### 3. Test API Endpoints

```bash
curl -v -H "KEY: ADMIN123" http://localhost:8888/api/v2/health
```

---

## Quick Reference

### Service Registry
```python
svc = self.get_service('service_name')
```

### Common Services
- `app_svc` - Application management
- `data_svc` - Object storage
- `auth_svc` - Authentication
- `file_svc` - File operations
- `contact_svc` - Agent C2
- `planning_svc` - Operation planning
- `learning_svc` - Fact learning
- `knowledge_svc` - Knowledge base
- `rest_svc` - REST API operations
- `event_svc` - Event handling

### Object Keys
- `agents` - Agent objects
- `operations` - Operation objects
- `abilities` - Ability objects
- `adversaries` - Adversary objects
- `planners` - Planner objects
- `sources` - Fact sources
- `objectives` - Objective objects
- `schedules` - Schedule objects

---

## Resources

- **Documentation**: https://caldera.readthedocs.io
- **API Reference**: [docs/api/rest-api.md](docs/api/rest-api.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Orchestration Guide**: [ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)
- **User Journey**: [END_TO_END_USER_JOURNEY.md](END_TO_END_USER_JOURNEY.md)

---

**For Copilot**: When generating code for this project:
1. Always use async/await for I/O operations
2. Inherit from appropriate base classes (BaseService, BaseObject)
3. Follow the service injection pattern
4. Use marshmallow schemas for API validation
5. Include proper error handling and logging
6. Write docstrings for all public methods
7. Use pathlib.Path for file operations
8. Validate and sanitise all external input
9. Check authentication for all API endpoints
10. Write tests for new functionality
11. Use Australian spelling (e.g., realise, organise, authorise)
12. Never use emojis in code or comments
13. Minimise comments - only add when explaining complex logic or non-obvious decisions
14. Write self-documenting code with clear variable and function names
15. Apply security best practices as standard (input validation, path sanitisation, authentication)
16. Assume experienced developer audience - avoid obvious comments
17. Check if code exists in current codebase before suggesting new implementations

**Deployment Requirements**:
- Target platform is Azure VM (Ubuntu 22.04 for server, Windows Server 2022 for agents)
- All paths must be portable using pathlib.Path (no hardcoded absolute paths)
- Configuration should use environment variables or relative paths
- Code must work when cloned to different VM directories without modification
- Scripts should detect VM environment and adapt accordingly
- Network configurations should use public IPs or DNS names (not localhost/127.0.0.1)
- Document external dependencies (Azure resources, firewall rules, network security groups)
- Deployment scripts should be idempotent and handle existing resources gracefully

**Current Deployment Package** (`scripts/demo_scripts_20251217-2033/`):
- `caldera_server_setup.sh` - CALDERA + ELK + Filebeat + custom plugins
- `upload_branding_plugin.sh` - Upload Triskele Labs branding to VM
- `setup_orchestrator_complete.sh` - Phase 1-6 orchestrator installation
- `deploy_blue_agent.sh` - Blue team Linux agent
- `deploy_red_agent.ps1` - Red team Windows agent
- `demo_validation.sh` - End-to-end validation
- `cleanup_demo.sh` - Azure resource cleanup
- `DEPLOYMENT_GUIDE.txt` - Complete deployment workflow (447 lines)

**Removed Files** (December 18, 2025):
- 18 redundant markdown files (testing logs, migration docs, implementation summaries)
- 5 local testing scripts (install_orchestrator.sh, test_user_journey_phases.sh, etc.)
- Total cleanup: ~250KB of outdated development documentation

---

**Version**: 1.3  
**Maintained By**: Triskele Labs Development Team  
**Last Updated**: December 18, 2025
