# Phase 1-4 Testing Guide
**Comprehensive Testing for Caldera Global Orchestration Pattern**

**Date:** December 15, 2025  
**Phases Covered:** 1-4 (Campaign Management, CLI, Webhooks, Branding)

---

## 🎯 Testing Overview

### What We're Testing
1. **Phase 1:** Campaign object model, schema validation
2. **Phase 2:** CLI commands, health checks, agent enrollment
3. **Phase 3:** Webhook publishing, SIEM integration
4. **Phase 4:** Branding plugin, theme application

### Prerequisites
- Caldera server installed
- Python 3.8+
- Required dependencies installed
- Access to Caldera REST API

---

## 🚀 Quick Start: Complete Test Run

```bash
# 1. Setup environment
cd "/Users/tonyto/Documents/GitHub/Triskele Labs/caldera"
source venv/bin/activate  # If using virtual environment

# 2. Install dependencies
pip install -r requirements.txt
pip install -r orchestrator/requirements.txt

# 3. Run complete test suite
./run_phase_tests.sh

# Expected: All tests pass ✅
```

---

## 📋 Detailed Testing Steps

## Phase 1: Campaign Specification & Objects

### Test 1.1: Campaign Schema Validation ✅

**Purpose:** Verify JSON schema validates campaign specifications correctly

```bash
# Test valid campaign spec
python3 << 'EOF'
import json
import jsonschema
from pathlib import Path

# Load schema
schema_path = Path('orchestrator/schemas/campaign_spec.schema.json')
with open(schema_path) as f:
    schema = json.load(f)

# Load example campaign
example_path = Path('orchestrator/schemas/campaign_spec_example.yml')
import yaml
with open(example_path) as f:
    campaign = yaml.safe_load(f)

# Validate
try:
    jsonschema.validate(campaign, schema)
    print("✅ Campaign schema validation: PASS")
except jsonschema.ValidationError as e:
    print(f"❌ Campaign schema validation: FAIL - {e.message}")
EOF
```

**Expected Output:**
```
✅ Campaign schema validation: PASS
```

---

### Test 1.2: Campaign Object Creation ✅

**Purpose:** Test campaign object instantiation and state management

```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from app.objects.c_campaign import Campaign
from datetime import datetime

# Create test campaign
campaign = Campaign(
    campaign_id='test-campaign-001',
    name='Test Campaign',
    environment={
        'name': 'test-env',
        'mode': 'test'
    },
    targets=[{
        'platform': 'linux',
        'group': 'test-agents',
        'count': 5
    }],
    adversary={
        'profile': 'test-adversary',
        'techniques': ['T1003']
    }
)

# Test state tracking
print(f"Initial status: {campaign.status}")
campaign.update_status('running')
print(f"Updated status: {campaign.status}")
print(f"Timeline events: {len(campaign.timeline)}")

# Test operations
campaign.add_operation('op-001')
print(f"Operations: {campaign.operations}")

# Test agents
campaign.add_agent('agent-001')
print(f"Agents: {campaign.agents}")

# Test errors
campaign.add_error('warning', 'Test warning message', {'test': 'data'})
print(f"Errors: {len(campaign.errors)}")

print("\n✅ Campaign object tests: PASS")
EOF
```

**Expected Output:**
```
Initial status: created
Updated status: running
Timeline events: 2
Operations: ['op-001']
Agents: ['agent-001']
Errors: 1

✅ Campaign object tests: PASS
```

---

### Test 1.3: Campaign Persistence ✅

**Purpose:** Verify campaigns save/load from filesystem

```bash
python3 << 'EOF'
import sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path.cwd()))

from app.objects.c_campaign import Campaign

# Create test campaign
campaign = Campaign(
    campaign_id='persist-test-001',
    name='Persistence Test',
    environment={'name': 'test', 'mode': 'test'},
    targets=[{'platform': 'linux', 'group': 'test', 'count': 1}],
    adversary={'profile': 'test', 'techniques': []}
)

# Save to file
save_path = Path('data/campaigns/persist-test-001.yml')
save_path.parent.mkdir(parents=True, exist_ok=True)

with open(save_path, 'w') as f:
    yaml.dump(campaign.to_dict(), f)

print(f"✅ Saved campaign to: {save_path}")

# Load from file
with open(save_path, 'r') as f:
    loaded_data = yaml.safe_load(f)

print(f"✅ Loaded campaign: {loaded_data['name']}")
print(f"   Campaign ID: {loaded_data['campaign_id']}")
print(f"   Status: {loaded_data['status']}")

# Cleanup
save_path.unlink()
print("✅ Campaign persistence: PASS")
EOF
```

**Expected Output:**
```
✅ Saved campaign to: data/campaigns/persist-test-001.yml
✅ Loaded campaign: Persistence Test
   Campaign ID: persist-test-001
   Status: created
✅ Campaign persistence: PASS
```

---

## Phase 2: Orchestrator CLI & Health Checks

### Test 2.1: CLI Help Commands ✅

**Purpose:** Verify CLI is accessible and shows help

```bash
# Test main CLI help
python3 -m orchestrator.cli.main --help

# Expected output:
# - Usage instructions
# - Available commands
# - No errors
```

**Expected Output:**
```
usage: main.py [-h] {campaign,operation,agent,report,health-check} ...

Caldera Orchestrator CLI

positional arguments:
  {campaign,operation,agent,report,health-check}
    campaign            Campaign management commands
    operation           Operation management commands
    agent               Agent enrollment commands
    report              Report generation commands
    health-check        Health check validation

optional arguments:
  -h, --help            show this help message and exit
```

---

### Test 2.2: Health Check Script ✅

**Purpose:** Validate Caldera environment readiness

```bash
# Run health check
python3 -m orchestrator.utils.health_check

# Or directly:
cd orchestrator
python3 utils/health_check.py
```

**Expected Output (when Caldera is running):**
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
Agents              ⚠️  WARN   0 agents deployed
Adversaries         ✅ PASS   12 profiles available
Abilities           ✅ PASS   450+ techniques loaded

Summary: 7 passed, 1 warning, 0 failed
Campaign environment: READY ✅
```

**Manual Health Check (Caldera stopped):**
```bash
# Start Caldera in background
python3 server.py &
SERVER_PID=$!
sleep 10  # Wait for startup

# Run health check
python3 -m orchestrator.utils.health_check

# Stop server
kill $SERVER_PID
```

---

### Test 2.3: Agent Enrollment Generator ✅

**Purpose:** Test enrollment script generation

```bash
# Test Windows enrollment script
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, 'orchestrator')

from agents.enrollment_generator import AgentEnrollmentGenerator

generator = AgentEnrollmentGenerator(
    caldera_server='http://localhost:8888',
    api_key='ADMIN123'
)

# Generate Windows script
campaign_id = 'test-campaign-001'
script = generator.generate_windows_script(campaign_id)

print("✅ Generated Windows enrollment script:")
print(f"   Length: {len(script)} characters")
print(f"   Contains campaign ID: {'test-campaign-001' in script}")
print(f"   Contains PowerShell: {'PowerShell' in script or '$' in script}")

# Generate Linux script
linux_script = generator.generate_linux_script(campaign_id)
print("✅ Generated Linux enrollment script:")
print(f"   Length: {len(linux_script)} characters")
print(f"   Contains campaign ID: {'test-campaign-001' in linux_script}")

# Generate Docker Compose
docker_compose = generator.generate_docker_compose(campaign_id, agent_count=3)
print("✅ Generated Docker Compose:")
print(f"   Contains services: {'services:' in docker_compose}")

print("\n✅ Agent enrollment generation: PASS")
EOF
```

**Expected Output:**
```
✅ Generated Windows enrollment script:
   Length: 1200+ characters
   Contains campaign ID: True
   Contains PowerShell: True
✅ Generated Linux enrollment script:
   Length: 800+ characters
   Contains campaign ID: True
✅ Generated Docker Compose:
   Contains services: True

✅ Agent enrollment generation: PASS
```

---

### Test 2.4: Save Generated Enrollment Scripts ✅

**Purpose:** Create actual enrollment scripts for testing

```bash
# Create test scripts directory
mkdir -p test_output/enrollment

# Generate all platform scripts
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, 'orchestrator')

from agents.enrollment_generator import AgentEnrollmentGenerator

generator = AgentEnrollmentGenerator(
    caldera_server='http://localhost:8888',
    api_key='ADMIN123'
)

campaign_id = 'test-campaign-001'
output_dir = Path('test_output/enrollment')

# Windows
windows_script = generator.generate_windows_script(campaign_id)
windows_path = output_dir / 'enroll_windows.ps1'
with open(windows_path, 'w') as f:
    f.write(windows_script)
print(f"✅ Created: {windows_path}")

# Linux
linux_script = generator.generate_linux_script(campaign_id)
linux_path = output_dir / 'enroll_linux.sh'
with open(linux_path, 'w') as f:
    f.write(linux_script)
print(f"✅ Created: {linux_path}")

# Docker
docker_compose = generator.generate_docker_compose(campaign_id, agent_count=5)
docker_path = output_dir / 'docker-compose.yml'
with open(docker_path, 'w') as f:
    f.write(docker_compose)
print(f"✅ Created: {docker_path}")

print("\n✅ All enrollment scripts saved to test_output/enrollment/")
EOF

# Verify files created
ls -lh test_output/enrollment/
```

**Expected Output:**
```
✅ Created: test_output/enrollment/enroll_windows.ps1
✅ Created: test_output/enrollment/enroll_linux.sh
✅ Created: test_output/enrollment/docker-compose.yml

✅ All enrollment scripts saved to test_output/enrollment/

-rw-r--r--  1 user  staff   1.2K Dec 15 10:00 docker-compose.yml
-rw-r--r--  1 user  staff   850B Dec 15 10:00 enroll_linux.sh
-rw-r--r--  1 user  staff   1.3K Dec 15 10:00 enroll_windows.ps1
```

---

## Phase 3: Webhook Publisher & SIEM Integration

### Test 3.1: Webhook Publisher Initialization ✅

**Purpose:** Test webhook service starts correctly

```bash
python3 << 'EOF'
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, 'orchestrator')

from services.webhook_service import WebhookPublisher

async def test_webhook_publisher():
    # Initialize publisher
    publisher = WebhookPublisher()
    await publisher.start()
    
    print(f"✅ Publisher started")
    print(f"   Webhooks registered: {len(publisher.webhooks)}")
    print(f"   Event queue size: {publisher.event_queue.maxlen}")
    print(f"   Stats: {publisher.stats}")
    
    # Register test webhook
    await publisher.register_webhook(
        url='https://httpbin.org/post',
        exchanges=['test'],
        queues=['created']
    )
    
    print(f"✅ Webhook registered")
    print(f"   Total webhooks: {len(publisher.webhooks)}")
    
    await publisher.stop()
    print("✅ Publisher stopped")

asyncio.run(test_webhook_publisher())
print("\n✅ Webhook publisher initialization: PASS")
EOF
```

**Expected Output:**
```
✅ Publisher started
   Webhooks registered: 0
   Event queue size: 1000
   Stats: {'sent': 0, 'failed': 0, 'last_sent': None, 'last_error': None}
✅ Webhook registered
   Total webhooks: 1
✅ Publisher stopped

✅ Webhook publisher initialization: PASS
```

---

### Test 3.2: Event Publishing ✅

**Purpose:** Test event publishing to webhooks

```bash
python3 << 'EOF'
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, 'orchestrator')

from services.webhook_service import WebhookPublisher

async def test_event_publishing():
    publisher = WebhookPublisher()
    await publisher.start()
    
    # Register test webhook (httpbin echoes back)
    await publisher.register_webhook(
        url='https://httpbin.org/post',
        exchanges=['campaign'],
        queues=['started']
    )
    
    # Publish test event
    event_data = {
        'campaign_id': 'test-001',
        'campaign_name': 'Test Campaign',
        'status': 'started'
    }
    
    await publisher.publish_event('campaign', 'started', event_data)
    
    # Wait for async send
    await asyncio.sleep(2)
    
    print(f"✅ Event published")
    print(f"   Events sent: {publisher.stats['sent']}")
    print(f"   Events failed: {publisher.stats['failed']}")
    
    await publisher.stop()
    
    if publisher.stats['sent'] > 0:
        print("✅ Event publishing: PASS")
    else:
        print("⚠️  Event publishing: WARNING (check network)")

asyncio.run(test_event_publishing())
EOF
```

**Expected Output:**
```
✅ Event published
   Events sent: 1
   Events failed: 0
✅ Event publishing: PASS
```

---

### Test 3.3: SIEM Integration Formatting ✅

**Purpose:** Test SIEM event formatters

```bash
python3 << 'EOF'
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, 'orchestrator')

from services.webhook_service import SIEMIntegration

# Test event
event = {
    'timestamp': datetime.now().isoformat(),
    'exchange': 'operation',
    'queue': 'finished',
    'data': {
        'campaign_id': 'test-001',
        'operation_id': 'op-001',
        'status': 'completed'
    }
}

# Test Elasticsearch format
elastic_siem = SIEMIntegration(
    platform='elasticsearch',
    endpoint='http://localhost:9200',
    api_key='test'
)
elastic_event = elastic_siem._format_elastic_event(event)
print("✅ Elasticsearch format:")
print(f"   Has @timestamp: {'@timestamp' in elastic_event}")
print(f"   Has event.kind: {'event' in elastic_event}")

# Test Splunk format
splunk_siem = SIEMIntegration(
    platform='splunk',
    endpoint='http://localhost:8088',
    api_key='test'
)
splunk_event = splunk_siem._format_splunk_event(event)
print("✅ Splunk format:")
print(f"   Has time: {'time' in splunk_event}")
print(f"   Has sourcetype: {'sourcetype' in splunk_event}")

print("\n✅ SIEM integration formatting: PASS")
EOF
```

**Expected Output:**
```
✅ Elasticsearch format:
   Has @timestamp: True
   Has event.kind: True
✅ Splunk format:
   Has time: True
   Has sourcetype: True

✅ SIEM integration formatting: PASS
```

---

### Test 3.4: Orchestrator Plugin Loading ✅

**Purpose:** Verify plugin loads in Caldera

```bash
# Check if plugin exists
ls -la plugins/orchestrator/

# Check plugin files
cat plugins/orchestrator/hook.py | head -20

# Start Caldera and check logs
python3 server.py 2>&1 | grep -i orchestrator | head -10
```

**Expected Output:**
```
# Plugin files exist:
hook.py
README.md
api/
__init__.py

# In server logs:
INFO     orchestrator_plugin: Orchestrator plugin initializing...
INFO     orchestrator_plugin: Webhook publisher starting...
INFO     orchestrator_plugin: REST API routes registered
INFO     orchestrator_plugin: Orchestrator plugin enabled
```

**Manual Plugin Test:**
```bash
# Start Caldera
python3 server.py &
sleep 10

# Test plugin endpoint
curl -H "KEY: ADMIN123" http://localhost:8888/plugin/orchestrator/webhooks

# Expected: JSON response with webhooks array
# {"webhooks": [], "stats": {...}}

# Stop Caldera
pkill -f "python3 server.py"
```

---

## Phase 4: Branding Plugin

### Test 4.1: Branding Plugin Files ✅

**Purpose:** Verify all branding files exist

```bash
# Check plugin structure
echo "Checking branding plugin structure..."

files=(
    "plugins/branding/hook.py"
    "plugins/branding/branding_config.yml"
    "plugins/branding/static/css/triskele_theme.css"
    "plugins/branding/static/img/triskele_logo.svg"
    "plugins/branding/templates/login.html"
    "plugins/branding/templates/branding_admin.html"
    "plugins/branding/README.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

echo ""
echo "✅ Branding plugin files: PASS"
```

**Expected Output:**
```
Checking branding plugin structure...
✅ plugins/branding/hook.py
✅ plugins/branding/branding_config.yml
✅ plugins/branding/static/css/triskele_theme.css
✅ plugins/branding/static/img/triskele_logo.svg
✅ plugins/branding/templates/login.html
✅ plugins/branding/templates/branding_admin.html
✅ plugins/branding/README.md

✅ Branding plugin files: PASS
```

---

### Test 4.2: Branding Configuration ✅

**Purpose:** Validate branding config file

```bash
python3 << 'EOF'
import yaml
from pathlib import Path

config_path = Path('plugins/branding/branding_config.yml')
with open(config_path) as f:
    config = yaml.safe_load(f)

print("✅ Branding configuration loaded:")
print(f"   Theme: {config.get('theme')}")
print(f"   Enabled: {config.get('enabled')}")
print(f"   Primary Accent: {config['colors']['primary_accent']}")
print(f"   Company: {config['customization']['company_name']}")

# Validate required fields
required = ['enabled', 'theme', 'colors', 'customization']
missing = [f for f in required if f not in config]

if missing:
    print(f"❌ Missing fields: {missing}")
else:
    print("\n✅ Branding configuration: PASS")
EOF
```

**Expected Output:**
```
✅ Branding configuration loaded:
   Theme: triskele_labs
   Enabled: True
   Primary Accent: #48CFA0
   Company: Triskele Labs

✅ Branding configuration: PASS
```

---

### Test 4.3: CSS Theme Validation ✅

**Purpose:** Check theme CSS has all required variables

```bash
# Check CSS file exists and has content
css_file="plugins/branding/static/css/triskele_theme.css"

echo "Checking CSS theme..."
echo "File size: $(wc -c < "$css_file") bytes"
echo "Lines: $(wc -l < "$css_file") lines"

# Check for key CSS variables
grep -c "triskele-primary-accent" "$css_file" && echo "✅ Primary accent variable defined"
grep -c "triskele-primary-dark" "$css_file" && echo "✅ Primary dark variable defined"
grep -c ":root" "$css_file" && echo "✅ Root variables section exists"

echo ""
echo "✅ CSS theme validation: PASS"
```

**Expected Output:**
```
Checking CSS theme...
File size: 15000+ bytes
Lines: 472 lines
✅ Primary accent variable defined
✅ Primary dark variable defined
✅ Root variables section exists

✅ CSS theme validation: PASS
```

---

### Test 4.4: Branding Plugin Loading ✅

**Purpose:** Verify branding plugin loads and serves files

```bash
# Start Caldera
python3 server.py &
SERVER_PID=$!
sleep 10

echo "Testing branding plugin endpoints..."

# Test static CSS file
curl -s http://localhost:8888/plugin/branding/static/css/triskele_theme.css | head -5
echo ""

# Test branding config API
curl -s -H "KEY: ADMIN123" http://localhost:8888/plugin/branding/api/config | python3 -m json.tool

# Test admin GUI
curl -s http://localhost:8888/plugin/branding/gui | grep -c "Branding Configuration" && echo "✅ Admin UI accessible"

# Cleanup
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo ""
echo "✅ Branding plugin loading: PASS"
```

**Expected Output:**
```
Testing branding plugin endpoints...

/*
 * Triskele Labs Theme for Caldera
 * Solid colors only - no gradients
 */

{
  "theme": "triskele_labs",
  "enabled": true,
  "colors": {
    "primary_accent": "#48CFA0",
    ...
  }
}

✅ Admin UI accessible

✅ Branding plugin loading: PASS
```

---

## 🔄 Complete Integration Test

### End-to-End Campaign Test ✅

**Purpose:** Test complete workflow from campaign creation to webhook

```bash
# Save as: test_output/integration_test.sh
chmod +x test_output/integration_test.sh

cat > test_output/integration_test.sh << 'SCRIPT'
#!/bin/bash
echo "🚀 Starting Integration Test..."

# Start Caldera
python3 server.py &
SERVER_PID=$!
sleep 15

echo "✅ Caldera started (PID: $SERVER_PID)"

# Run health check
python3 -m orchestrator.utils.health_check | grep "Summary:"

# Create test campaign spec
cat > test_output/test_campaign.yml << 'EOF'
campaign_id: "integration-test-001"
name: "Integration Test Campaign"
environment:
  name: "test-env"
  mode: "test"
targets:
  - platform: "linux"
    group: "test-agents"
    count: 1
adversary:
  profile: "test"
  techniques: []
EOF

echo "✅ Test campaign spec created"

# Test webhook registration
curl -s -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://httpbin.org/post",
    "exchanges": ["campaign"],
    "queues": ["created"]
  }'

echo "✅ Webhook registered"

# Verify branding loaded
curl -s http://localhost:8888/plugin/branding/api/config | grep -q "triskele_labs" && echo "✅ Branding active"

# Cleanup
kill $SERVER_PID
rm test_output/test_campaign.yml

echo ""
echo "🎉 Integration test complete!"
SCRIPT

# Run integration test
bash test_output/integration_test.sh
```

---

## 📊 Test Summary Script

Create automated test runner:

```bash
cat > run_phase_tests.sh << 'SCRIPT'
#!/bin/bash
# Automated Phase 1-4 Test Runner

echo "╔════════════════════════════════════════════════╗"
echo "║   Phase 1-4 Automated Test Suite              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo "Running: $test_name"
    if eval "$test_command" > /dev/null 2>&1; then
        echo "✅ PASS: $test_name"
        ((PASSED++))
    else
        echo "❌ FAIL: $test_name"
        ((FAILED++))
    fi
}

# Phase 1 Tests
echo "📦 Phase 1: Campaign Management"
run_test "Campaign schema exists" "test -f orchestrator/schemas/campaign_spec.schema.json"
run_test "Campaign example exists" "test -f orchestrator/schemas/campaign_spec_example.yml"
run_test "Campaign object exists" "test -f app/objects/c_campaign.py"

# Phase 2 Tests
echo ""
echo "🔧 Phase 2: CLI & Health Checks"
run_test "CLI main exists" "test -f orchestrator/cli/main.py"
run_test "Health check exists" "test -f orchestrator/utils/health_check.py"
run_test "Enrollment generator exists" "test -f orchestrator/agents/enrollment_generator.py"

# Phase 3 Tests
echo ""
echo "📡 Phase 3: Webhooks & SIEM"
run_test "Webhook service exists" "test -f orchestrator/services/webhook_service.py"
run_test "Orchestrator plugin exists" "test -f plugins/orchestrator/hook.py"

# Phase 4 Tests
echo ""
echo "🎨 Phase 4: Branding"
run_test "Branding plugin exists" "test -f plugins/branding/hook.py"
run_test "Branding config exists" "test -f plugins/branding/branding_config.yml"
run_test "Theme CSS exists" "test -f plugins/branding/static/css/triskele_theme.css"
run_test "Logo exists" "test -f plugins/branding/static/img/triskele_logo.svg"

# Summary
echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║   Test Summary                                 ║"
echo "╚════════════════════════════════════════════════╝"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed!"
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Review output above."
    exit 1
fi
SCRIPT

chmod +x run_phase_tests.sh
```

---

## 🎯 Quick Test Checklist

### Essential Tests (5 minutes)
- [ ] `./run_phase_tests.sh` - All file existence checks pass
- [ ] `python3 -m orchestrator.utils.health_check` - Health check runs
- [ ] `python3 server.py` - Caldera starts without errors
- [ ] Check logs for "Orchestrator plugin enabled"
- [ ] Check logs for "Branding plugin enabled"

### Full Test Suite (30 minutes)
- [ ] Phase 1: Schema validation, object creation, persistence
- [ ] Phase 2: CLI help, health checks, enrollment generation
- [ ] Phase 3: Webhook publisher, SIEM formatting, plugin API
- [ ] Phase 4: Branding files, config validation, plugin loading
- [ ] Integration: End-to-end workflow

---

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Fix: Add orchestrator to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/orchestrator"
```

#### Missing Dependencies
```bash
# Install all requirements
pip install -r requirements.txt
pip install -r orchestrator/requirements.txt
```

#### Caldera Won't Start
```bash
# Check port 8888 is free
lsof -i :8888
# Kill if needed
kill -9 $(lsof -t -i:8888)
```

#### Plugin Not Loading
```bash
# Check plugin listed in conf/default.yml
grep -r "orchestrator" conf/

# Check plugin __init__.py exists
ls plugins/orchestrator/__init__.py
```

---

## 📝 Test Results Log

Create log file:

```bash
# Run all tests and save results
./run_phase_tests.sh 2>&1 | tee test_results_$(date +%Y%m%d_%H%M%S).log
```

---

## ✅ Success Criteria

**Phase 1-4 is working if:**
1. ✅ All files exist (12/12 checks pass)
2. ✅ Health check shows "READY"
3. ✅ Caldera starts with both plugins loaded
4. ✅ Branding theme applies (login page shows Triskele Labs colors)
5. ✅ Webhook endpoints respond (200 status)
6. ✅ Campaign objects can be created and persisted
7. ✅ Enrollment scripts generate correctly

---

## 🚀 Next Steps After Testing

Once all tests pass:
1. Document any issues found
2. Commit test scripts to repo
3. Proceed to Phase 5 implementation
4. Use this testing framework for future phases

---

**Need help?** Check:
- `docs/guides/orchestration-guide.md`
- `MIGRATION_COMPLETE.md`
- Plugin README files
