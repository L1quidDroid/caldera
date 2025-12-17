# CALDERA Troubleshooting Guide

**Last Updated**: December 17, 2025  
**Version**: 1.0

Quick navigation:
- [Server Won't Start](#server-wont-start)
- [Agent Connection Issues](#agent-connection-issues)
- [Operation Failures](#operation-failures)
- [API Errors](#api-errors)
- [Plugin Problems](#plugin-problems)
- [Performance Issues](#performance-issues)
- [Orchestrator Issues](#orchestrator-issues)
- [Debug Mode](#debug-mode)

---

## 🚀 Quick Diagnostics

Before diving into specific issues, run these quick checks:

```bash
# 1. Run setup validation
./scripts/setup_check.sh

# 2. Check dependencies
python scripts/check_dependencies.py

# 3. Verify Python version
python3 --version  # Should be 3.10+

# 4. Test server health (if running)
curl http://localhost:8888/api/v2/health
```

---

## Server Won't Start

### Error: "ModuleNotFoundError: No module named 'XXX'"

**Cause**: Missing Python dependencies

**Solutions**:

1. **Activate virtual environment** (most common fix):
   ```bash
   source venv/bin/activate
   # Or if you used a different name:
   source .venv/bin/activate
   ```

2. **Install core dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check specific module**:
   ```bash
   python3 -c "import aiohttp"  # Test specific import
   ```

4. **Run automated dependency check**:
   ```bash
   python scripts/check_dependencies.py
   ```

5. **Verify pip is using the right Python**:
   ```bash
   which python3
   which pip3
   # Should both point to venv/bin/
   ```

**Still not working?**
```bash
# Nuclear option: rebuild virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Error: "Plugin 'XXX' failed to load"

**Cause**: Plugin missing dependencies or misconfigured

**Solutions**:

1. **Check plugin-specific dependencies**:
   ```bash
   # Debrief plugin
   pip install reportlab svglib
   
   # Orchestrator plugin (should be in requirements.txt)
   pip install matplotlib numpy weasyprint
   
   # Check all:
   python scripts/check_dependencies.py
   ```

2. **Temporarily disable problematic plugin** in `conf/default.yml`:
   ```yaml
   plugins:
     - access
     - atomic
     # - debrief  # Disabled temporarily
     # - emu      # Requires internet on first start
     - orchestrator
     - enrollment
   ```

3. **Check plugin README for specific requirements**:
   ```bash
   cat plugins/debrief/README.md
   cat plugins/emu/README.md
   ```

**Common Plugin Issues**:

| Plugin | Issue | Solution |
|--------|-------|----------|
| **emu** | Requires internet to clone repository on first start | Ensure connectivity or disable |
| **debrief** | Requires reportlab (large dependency) | `pip install reportlab svglib` |
| **gameboard** | Git submodule not initialized | `git submodule update --init --recursive` |
| **orchestrator** | Missing matplotlib/numpy/weasyprint | Already in requirements.txt |

---

### Error: "Address already in use" (Port 8888)

**Cause**: Another process using port 8888

**Solutions**:

1. **Find and kill the process**:
   ```bash
   # macOS/Linux
   lsof -ti:8888 | xargs kill -9
   
   # Or manually:
   lsof -i :8888
   # Note the PID, then:
   kill -9 <PID>
   ```

2. **Change port in config**:
   ```yaml
   # conf/default.yml
   port: 9999
   ```

3. **Verify nothing is running**:
   ```bash
   curl http://localhost:8888
   # Should fail with "Connection refused" if port is free
   ```

---

### Error: "Permission denied" when starting server

**Cause**: Insufficient file permissions or port restrictions

**Solutions**:

1. **Check file permissions**:
   ```bash
   ls -la server.py
   chmod +x server.py
   ```

2. **Don't use privileged ports (< 1024)** without sudo:
   ```yaml
   # conf/default.yml
   port: 8888  # ✅ OK
   # port: 80  # ❌ Requires sudo
   ```

3. **Check data directory permissions**:
   ```bash
   ls -la data/
   # Should be writable by your user
   chmod -R u+w data/
   ```

---

## Agent Connection Issues

### Symptom: Agent doesn't appear after running bootstrap script

**Diagnostic Steps**:

1. **Check agent is running on target**:
   ```bash
   # Windows
   tasklist | findstr sandcat
   
   # Linux/macOS
   ps aux | grep sandcat
   ```

2. **Test network connectivity** from target machine:
   ```bash
   curl http://<caldera-server>:8888/ping
   # Should return 200 OK
   ```

3. **Check server logs for beacon**:
   ```bash
   tail -f logs/caldera.log | grep beacon
   # Look for incoming beacon messages
   ```

4. **Verify contact method**:
   ```bash
   # List active contacts
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/contacts | jq '.'
   ```

5. **Check firewall rules**:
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   
   # Linux (iptables)
   sudo iptables -L -n | grep 8888
   ```

**Common Causes**:

| Cause | Symptom | Fix |
|-------|---------|-----|
| **Firewall blocking** | Agent can't reach port 8888 | Allow port 8888 in firewall |
| **Wrong server URL** | Agent connects to wrong IP | Check bootstrap script URL |
| **Contact method mismatch** | HTTP agent vs TCP server | Use matching contact (http) |
| **Untrusted agent** | Agent visible but greyed out | Wait 60s or manually trust |
| **Antivirus** | Agent exe deleted/quarantined | Add exception for agent |

**Quick Fixes**:

```bash
# Force trust all agents (testing only!)
curl -X PATCH http://localhost:8888/api/v2/agents/<paw> \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{"trusted": 1}'

# Test agent connectivity
curl -v http://<caldera-server>:8888/ping
```

---

### Symptom: Agent shows as "untrusted"

**Cause**: Agent hasn't been trusted or exceeded silence timer

**Solutions**:

1. **Manually trust agent via API**:
   ```bash
   curl -X PATCH http://localhost:8888/api/v2/agents/<paw> \
     -H "KEY: ADMIN123" \
     -H "Content-Type: application/json" \
     -d '{"trusted": 1}'
   ```

2. **Manually trust via Web UI**:
   - Navigate to Agents tab
   - Click on agent
   - Toggle "Trusted" switch

3. **Check agent heartbeat**:
   ```bash
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents/<paw> | jq '.last_seen'
   ```

4. **Adjust trust timer** in `conf/agents.yml`:
   ```yaml
   untrusted_timer: 300  # 5 minutes instead of default 60s
   ```

5. **Check agent isn't sleeping**:
   ```bash
   # Get agent details
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents/<paw> | jq '{paw, sleep_min, sleep_max, last_seen}'
   ```

---

### Symptom: Agent connects then immediately disconnects

**Cause**: Communication errors or agent crashes

**Diagnostic Steps**:

1. **Check agent logs on target**:
   ```bash
   # Windows
   type C:\Users\<user>\AppData\Local\Temp\sandcat.log
   
   # Linux/macOS
   cat /tmp/sandcat.log
   ```

2. **Review server error logs**:
   ```bash
   grep -i error logs/caldera.log | tail -20
   ```

3. **Test with verbose agent**:
   ```bash
   # Add -v flag when deploying agent
   sandcat.exe -v -server http://caldera:8888
   ```

**Common Fixes**:
- Update agent to latest version
- Check SSL/TLS certificates if using HTTPS
- Verify agent platform matches (32-bit vs 64-bit)
- Ensure agent has internet access if C2 is external

---

## Operation Failures

### Symptom: Operation stuck in "running" state

**Diagnostic Steps**:

1. **Check operation status**:
   ```bash
   curl -H "KEY: ADMIN123" \
     http://localhost:8888/api/v2/operations/<op-id> | jq '.state'
   ```

2. **List active links** (pending commands):
   ```bash
   curl -H "KEY: ADMIN123" \
     "http://localhost:8888/api/v2/operations/<op-id>/links?status=0" | jq 'length'
   ```

3. **Check agent availability**:
   ```bash
   curl -H "KEY: ADMIN123" \
     "http://localhost:8888/api/v2/agents?group=red" | jq '.[].paw'
   ```

4. **Review operation logs**:
   ```bash
   # In Web UI: Operations → Select operation → View Logs
   # Or via API:
   curl -H "KEY: ADMIN123" \
     "http://localhost:8888/api/v2/operations/<op-id>/event-logs"
   ```

**Manual Resolution**:

```bash
# Stop operation forcefully
curl -X PATCH http://localhost:8888/api/v2/operations/<op-id> \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{"state": "finished"}'

# Or cleanup hung operations
curl -X DELETE http://localhost:8888/api/v2/operations/<op-id> \
  -H "KEY: ADMIN123"
```

---

### Symptom: All abilities failing with "command not found"

**Cause**: Platform mismatch or executor unavailable

**Solutions**:

1. **Verify agent platform**:
   ```bash
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents/<paw> | jq '.platform'
   # Returns: "windows", "linux", or "darwin"
   ```

2. **Check ability requirements**:
   ```bash
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/abilities/<ability-id> | jq '.executors[].platform'
   ```

3. **List agent executors**:
   ```bash
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents/<paw> | jq '.executors'
   # Example: ["psh", "cmd"] for Windows, ["sh", "bash"] for Linux
   ```

4. **Use adversary with platform-specific abilities**:
   - Windows: Use adversaries with `psh`, `cmd` executors
   - Linux: Use adversaries with `sh`, `bash` executors
   - macOS: Use adversaries with `sh`, `bash` executors

**Quick Test**:
```bash
# Test if agent has required executor
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents/<paw> | \
  jq '.executors[] | select(.name=="psh")'
```

---

### Symptom: Abilities timeout without results

**Cause**: Long-running commands or agent sleep intervals

**Solutions**:

1. **Increase ability timeout** in adversary profile:
   ```yaml
   # data/adversaries/custom.yml
   abilities:
     - ability_id: some-ability
       timeout: 600  # 10 minutes
   ```

2. **Reduce agent sleep** (more frequent beacons):
   ```bash
   curl -X PATCH http://localhost:8888/api/v2/agents/<paw> \
     -H "KEY: ADMIN123" \
     -H "Content-Type: application/json" \
     -d '{"sleep_min": 3, "sleep_max": 5}'
   ```

3. **Check if ability is actually running**:
   ```bash
   # On target, check processes
   ps aux | grep <command>
   ```

---

## API Errors

### Error: 401 Unauthorized

**Solutions**:

1. **Check API key header** (most common):
   ```bash
   # ✅ Correct
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/health
   
   # ❌ Wrong - don't use Bearer token
   curl -H "Authorization: Bearer ADMIN123" http://localhost:8888/api/v2/health
   ```

2. **Verify API key in config**:
   ```bash
   grep api_key conf/default.yml
   # api_key_red: ADMIN123
   # api_key_blue: BLUEADMIN123
   ```

3. **Try alternate key**:
   ```bash
   # Red team key (full access)
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents
   
   # Blue team key (limited access)
   curl -H "KEY: BLUEADMIN123" http://localhost:8888/api/v2/agents
   ```

4. **Check if using session auth** (web UI):
   ```bash
   # Login first to get session cookie
   curl -c cookies.txt -X POST http://localhost:8888/api/login \
     -d '{"username":"admin","password":"admin"}'
   
   # Then use cookie for subsequent requests
   curl -b cookies.txt http://localhost:8888/api/v2/agents
   ```

---

### Error: 403 Forbidden

**Cause**: Insufficient permissions for operation

**Solutions**:

1. **Use RED team API key** (admin access):
   ```bash
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/operations
   ```

2. **Check user permissions**:
   ```yaml
   # conf/default.yml
   users:
     red:
       admin: admin  # Full access
     blue:
       blue: admin   # Limited access
   ```

3. **Verify endpoint requires admin**:
   - Operations: RED team only
   - Abilities: RED team only  
   - Agents (read): Both teams
   - Agents (modify): RED team only

---

### Error: 404 Not Found

**Solutions**:

1. **Double-check resource ID**:
   ```bash
   # List all operations
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/operations | jq '.[].id'
   
   # Then get specific one
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/operations/<correct-id>
   ```

2. **Check resource type** (singular vs plural):
   ```bash
   # ✅ Correct
   /api/v2/operations
   /api/v2/agents
   /api/v2/abilities
   
   # ❌ Wrong
   /api/v2/operation
   /api/v2/agent
   ```

3. **Verify resource exists**:
   ```bash
   # List all resources of that type
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/<resource-type>
   ```

---

### Error: 500 Internal Server Error

**Diagnostic Steps**:

1. **Check server logs** (most important):
   ```bash
   tail -50 logs/caldera.log
   # Look for stack traces and error messages
   ```

2. **Test server health**:
   ```bash
   curl http://localhost:8888/api/v2/health
   ```

3. **Verify database state**:
   ```bash
   # Check data directory
   ls -lah data/object_store/
   ```

4. **Look for plugin errors**:
   ```bash
   grep -i "plugin" logs/caldera.log | tail -20
   ```

**Common Causes & Fixes**:

| Cause | Log Message | Fix |
|-------|-------------|-----|
| Corrupted object store | `Failed to load` | Delete `data/object_store/*` and restart |
| Plugin error | `Plugin XXX failed` | Disable plugin or install dependencies |
| Race condition | `AttributeError` | Restart server |
| Memory error | `MemoryError` | Increase system memory or clean old data |

**Quick Fixes**:
```bash
# Reset object store (CAUTION: loses all operations/agents)
mv data/object_store data/object_store.backup
mkdir data/object_store
python server.py --insecure

# Clean old completed operations
curl -X DELETE http://localhost:8888/api/v2/operations/<old-op-id> \
  -H "KEY: ADMIN123"
```

---

## Plugin Problems

### Orchestrator Plugin: "Campaign not found"

**Solutions**:

1. **List campaigns**:
   ```bash
   python orchestrator/cli.py campaign list
   ```

2. **Check campaign file exists**:
   ```bash
   ls -l data/campaigns/
   cat data/campaigns/demo_campaign.yml
   ```

3. **Create test campaign**:
   ```bash
   python orchestrator/cli.py campaign create \
     data/campaigns/demo_campaign.yml
   ```

4. **Verify campaign ID** matches:
   ```bash
   # Check campaign_id in YAML file
   grep campaign_id data/campaigns/demo_campaign.yml
   
   # Use exact ID
   python orchestrator/cli.py campaign status <campaign_id>
   ```

---

### Enrollment Plugin: "Bootstrap script fails"

**Diagnostic Steps**:

1. **Test enrollment API health**:
   ```bash
   curl http://localhost:8888/plugin/enrollment/health
   ```

2. **Check enrollment requests**:
   ```bash
   curl -H "KEY: ADMIN123" \
     http://localhost:8888/plugin/enrollment/api/requests | jq '.'
   ```

3. **Verify script syntax**:
   ```bash
   # Test PowerShell syntax
   powershell -File enroll_windows.ps1 -WhatIf
   
   # Test bash syntax
   bash -n enroll_linux.sh
   ```

4. **Manual script execution**:
   ```bash
   # Windows (PowerShell)
   Set-ExecutionPolicy Bypass -Scope Process
   .\enroll_windows.ps1
   
   # Linux/macOS
   chmod +x enroll_linux.sh
   ./enroll_linux.sh
   ```

**Common Script Issues**:
- PowerShell execution policy blocked
- Missing execute permissions on Linux/macOS
- Wrong server URL in script
- Firewall blocking download

---

## Performance Issues

### Symptom: Server slow or unresponsive

**Diagnostic Steps**:

1. **Check resource usage**:
   ```bash
   # CPU/Memory
   top -p $(pgrep -f server.py)
   
   # Or
   ps aux | grep server.py
   ```

2. **Count active operations**:
   ```bash
   curl -H "KEY: ADMIN123" \
     "http://localhost:8888/api/v2/operations?state=running" | jq 'length'
   ```

3. **Check database size**:
   ```bash
   du -sh data/object_store/
   ```

4. **Monitor logs in real-time**:
   ```bash
   tail -f logs/caldera.log
   ```

**Solutions**:

1. **Clean old operations**:
   ```bash
   # List old operations
   curl -H "KEY: ADMIN123" \
     "http://localhost:8888/api/v2/operations?state=finished" | jq '.[].id'
   
   # Delete old operation
   curl -X DELETE http://localhost:8888/api/v2/operations/<op-id> \
     -H "KEY: ADMIN123"
   ```

2. **Reduce agent polling frequency**:
   ```bash
   # Increase agent sleep times
   curl -X PATCH http://localhost:8888/api/v2/agents/<paw> \
     -H "KEY: ADMIN123" \
     -H "Content-Type: application/json" \
     -d '{"sleep_min": 30, "sleep_max": 60}'
   ```

3. **Disable unused plugins**:
   ```yaml
   # conf/default.yml
   plugins:
     - orchestrator
     - enrollment
     # Comment out unused plugins:
     # - training
     # - debrief
   ```

4. **Archive old data**:
   ```bash
   # Backup object store
   tar -czf object_store_backup_$(date +%Y%m%d).tar.gz data/object_store/
   
   # Clean old data
   rm -rf data/object_store/*
   ```

---

## Orchestrator Issues

### Campaign CLI: "No module named 'orchestrator'"

**Cause**: Python path issue or orchestrator plugin not loaded

**Solutions**:

1. **Check orchestrator plugin is enabled**:
   ```yaml
   # conf/default.yml
   plugins:
     - orchestrator  # ← Must be present
   ```

2. **Verify orchestrator files exist**:
   ```bash
   ls -la orchestrator/cli/
   ls -la orchestrator/agents/
   ls -la orchestrator/reporting/
   ```

3. **Run from project root**:
   ```bash
   # ✅ Correct
   cd /path/to/caldera
   python orchestrator/cli.py campaign list
   
   # ❌ Wrong
   cd orchestrator
   python cli.py campaign list
   ```

---

### Webhook Publisher: "Connection refused"

**Cause**: Webhook endpoint unreachable

**Solutions**:

1. **Test webhook endpoint**:
   ```bash
   curl -X POST https://webhook.site/your-id \
     -H "Content-Type: application/json" \
     -d '{"test": "message"}'
   ```

2. **Use webhook testing service**:
   - https://webhook.site - Get instant test URL
   - https://httpbin.org/post - Echo service

3. **Check webhook is registered**:
   ```bash
   curl -H "KEY: ADMIN123" \
     http://localhost:8888/plugin/orchestrator/webhooks | jq '.'
   ```

4. **Register webhook**:
   ```bash
   curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
     -H "KEY: ADMIN123" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://webhook.site/your-id",
       "exchanges": ["campaign", "operation"]
     }'
   ```

---

## Debug Mode

Enable verbose logging for troubleshooting:

### Start Server in Debug Mode

```bash
python server.py --insecure --log DEBUG
```

### Tail Logs in Real-Time

```bash
# All logs
tail -f logs/caldera.log

# Filter by level
grep -i error logs/caldera.log
grep -i warning logs/caldera.log

# Filter by component
grep -i "plugin" logs/caldera.log
grep -i "agent" logs/caldera.log
grep -i "operation" logs/caldera.log
```

### Python REPL Testing

```python
# Test imports
python3
>>> from app.service.app_svc import AppService
>>> from app.objects.c_operation import Operation
>>> from app.objects.c_agent import Agent
>>> # No errors = good!
```

### Enable Network Traffic Logging

```bash
# Use mitmproxy to inspect HTTP traffic
pip install mitmproxy
mitmproxy -p 8080

# Configure agent to use proxy:
sandcat.exe -server http://caldera:8888 -http-proxy http://localhost:8080
```

---

## Getting Help

### Before Reporting Issues

1. **Run diagnostics**:
   ```bash
   ./scripts/setup_check.sh > setup_report.txt
   python scripts/check_dependencies.py > deps_report.txt
   ```

2. **Gather logs**:
   ```bash
   tail -100 logs/caldera.log > error_logs.txt
   ```

3. **Document environment**:
   ```bash
   python3 --version > environment.txt
   pip list >> environment.txt
   uname -a >> environment.txt
   ```

### Support Resources

1. **Search documentation**:
   ```bash
   grep -r "error message" docs/
   ```

2. **Review test files** for examples:
   ```bash
   ls tests/
   cat tests/test_phase5_requirements.py
   ```

3. **GitHub Issues**: https://github.com/mitre/caldera/issues
4. **CALDERA Docs**: https://caldera.readthedocs.io
5. **Community**: https://github.com/mitre/caldera/discussions

### When Reporting Bugs

Include:
- **Server version**: `cat app/version.py`
- **Python version**: `python3 --version`
- **OS**: `uname -a` or `ver` (Windows)
- **Error logs**: Last 50 lines of `logs/caldera.log`
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots** (if UI issue)

---

## Appendix: Common Error Messages

| Error Message | Cause | Quick Fix |
|---------------|-------|-----------|
| `ModuleNotFoundError: No module named 'aiohttp'` | Missing dependencies | `pip install -r requirements.txt` |
| `Address already in use` | Port 8888 busy | `lsof -ti:8888 \| xargs kill -9` |
| `401 Unauthorized` | Missing/wrong API key | Use `KEY: ADMIN123` header |
| `Plugin 'XXX' failed to load` | Missing plugin deps | `python scripts/check_dependencies.py` |
| `Agent not found` | Agent disconnected/deleted | Check `GET /api/v2/agents` |
| `Operation timeout` | Slow ability execution | Increase timeout in adversary |
| `Campaign not found` | Wrong campaign ID | `python orchestrator/cli.py campaign list` |
| `Connection refused` | Server not running | `python server.py --insecure` |

---

**Document Version**: 1.0  
**Maintained By**: Triskele Labs Development Team  
**Feedback**: Submit issues to GitHub repository
