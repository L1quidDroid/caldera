# Phase 4 Deployment Checklist

Use this checklist when deploying Phase 4 to the Corporate VM.

## Pre-Deployment (Local Machine)

- [x] **Code complete**: All Phase 4 code implemented
- [x] **Tests passing**: `python3 test_sequencer.py` ✅ 4/4 passed
- [x] **Documentation created**:
  - [x] `PHASE-4-SUMMARY.md`
  - [x] `PHASE-4-IMPLEMENTATION.md`
  - [x] `plugins/sequencer/README.md`
- [x] **Example sequences created**:
  - [x] `examples/sequence-discovery.yml`
  - [x] `data/sequences/lateral-movement.yml`
- [ ] **Git committed**:
  ```bash
  cd caldera
  git add -A
  git commit -m "Phase 4: Automated operation sequencing with GUI plugin"
  git push origin main
  ```

---

## Corporate VM Deployment

### 1. Pull Latest Code

```bash
cd /path/to/caldera
git pull origin main
```

**Verify:**
```bash
ls -la plugins/sequencer/
ls -la examples/sequence-discovery.yml
```

### 2. Enable Sequencer Plugin

Edit `conf/local.yml`:

```yaml
plugins:
  - access
  - atomic
  - compass
  - debrief
  - enrollment
  - orchestrator
  - sequencer  # ← ADD THIS LINE
  - sandcat
  - stockpile
```

**Verify:**
```bash
grep -A 10 "^plugins:" conf/local.yml
```

### 3. Install Python Dependencies (if needed)

```bash
cd orchestrator
pip install -r requirements.txt
```

**Verify:**
```bash
python3 -c "import aiohttp, yaml, rich; print('OK')"
```

### 4. Start Caldera

```bash
cd /path/to/caldera
python3 server.py --insecure
```

**Wait for:**
```
...
[INFO] Sequencer plugin enabled - API: /plugin/sequencer
```

### 5. Verify Plugin Loaded

```bash
# Check via API
curl -H "KEY: ADMIN123" http://localhost:8888/api/rest?index=plugins | \
  jq '.[] | select(.name=="Sequencer")'

# Should return plugin metadata
```

### 6. Run Test Suite

```bash
cd /path/to/caldera
python3 test_sequencer.py
```

**Expected output:**
```
Total: 4 passed, 0 failed, 1 skipped (if Caldera running, 5 passed)
ALL TESTS PASSED
```

### 7. Test CLI Sequencing

```bash
# Create a test campaign
caldera-orchestrator campaign create examples/campaign-spec.yml

# Get campaign ID from output (e.g., campaign-abc123)
CAMPAIGN_ID="<campaign-id>"

# Run discovery sequence
caldera-orchestrator campaign sequence $CAMPAIGN_ID examples/sequence-discovery.yml
```

### 8. Test GUI

**Navigate to:**
```
http://<vm-ip>:8888/plugin/sequencer/gui
```

**Verify:**
- [ ] Page loads without errors
- [ ] Campaign dropdown populates
- [ ] Sequence templates appear
- [ ] "Start Sequence" button works
- [ ] Job progress updates in real-time

### 9. Test REST API

```bash
# Start a sequence via API
curl -X POST http://localhost:8888/plugin/sequencer/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "'"$CAMPAIGN_ID"'",
    "sequence_name": "lateral-movement",
    "max_retries": 3,
    "timeout": 300
  }'

# Get returned job_id
JOB_ID="<job-id>"

# Monitor status
watch -n 2 "curl -s http://localhost:8888/plugin/sequencer/api/status/$JOB_ID | jq ."
```

### 10. Test Workflow Integration

If ELK + Slack configured:

```bash
# Set environment variables
export ELASTIC_ENDPOINT="http://localhost:9200"
export ELASTIC_PASSWORD="changeme"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Run sequence
caldera-orchestrator campaign sequence $CAMPAIGN_ID examples/sequence-discovery.yml
```

**Verify:**
- [ ] ELK alerts tagged with ATT&CK technique IDs
- [ ] Slack notification received with:
  - [ ] Success rate
  - [ ] Duration
  - [ ] Failed steps (if any)
- [ ] ATT&CK coverage report generated in `reports/sequences/<job-id>/`

---

## Post-Deployment Validation

### Checklist

- [ ] **Plugin loaded**: Sequencer appears in `GET /api/rest?index=plugins`
- [ ] **CLI works**: `caldera-orchestrator campaign sequence` executes
- [ ] **GUI accessible**: `/plugin/sequencer/gui` loads
- [ ] **Jobs tracked**: `GET /plugin/sequencer/api/jobs` returns list
- [ ] **Fact chaining works**: Facts passed between steps
- [ ] **Retry logic works**: Failed steps retry with backoff
- [ ] **Workflow integration**: ELK tagging + Slack notifications sent

### Common Issues

**Issue:** Plugin not loading

**Solution:**
```bash
# Check conf/local.yml
grep sequencer conf/local.yml

# Check plugin directory exists
ls -la plugins/sequencer/hook.py

# Check Caldera logs
tail -100 logs/caldera.log | grep -i error
```

---

**Issue:** CLI import error

**Solution:**
```bash
# Verify orchestrator is in PYTHONPATH
export PYTHONPATH="/path/to/caldera:$PYTHONPATH"

# Or run from caldera directory
cd /path/to/caldera
python3 -m orchestrator.cli campaign sequence ...
```

---

**Issue:** GUI 404 error

**Solution:**
```bash
# Verify static files exist
ls -la plugins/sequencer/gui/views/sequencer.vue

# Check hook.py registered routes
grep "add_route" plugins/sequencer/hook.py

# Restart Caldera
pkill -f server.py
python3 server.py --insecure
```

---

**Issue:** Sequences not appearing

**Solution:**
```bash
# Verify sequences directory
mkdir -p data/sequences
cp examples/sequence-discovery.yml data/sequences/

# Check via API
curl http://localhost:8888/plugin/sequencer/api/sequences | jq .
```

---

## Rollback Plan

If Phase 4 causes issues:

1. **Disable plugin** in `conf/local.yml`:
```yaml
plugins:
  # - sequencer  # ← COMMENT OUT
```

2. **Restart Caldera**:
```bash
pkill -f server.py
python3 server.py --insecure
```

3. **Revert code** (if needed):
```bash
git log --oneline  # Find commit before Phase 4
git revert <commit-hash>
```

---

## Success Criteria

Phase 4 is successfully deployed when:

✅ **All tests pass** (`python3 test_sequencer.py`)  
✅ **Plugin loads** (appears in plugin list)  
✅ **CLI executes sequences** (no errors)  
✅ **GUI accessible** (can start/monitor jobs)  
✅ **Facts chain** between steps  
✅ **Retry logic works** (exponential backoff on failure)  
✅ **Workflow events fire** (ELK tags, Slack notifications)

---

## Support Resources

- **Implementation Guide**: [PHASE-4-IMPLEMENTATION.md](PHASE-4-IMPLEMENTATION.md)
- **Plugin README**: [plugins/sequencer/README.md](plugins/sequencer/README.md)
- **Summary**: [PHASE-4-SUMMARY.md](PHASE-4-SUMMARY.md)
- **Test Suite**: `python3 test_sequencer.py`
- **Example Sequences**:
  - `examples/sequence-discovery.yml`
  - `data/sequences/lateral-movement.yml`

---

**Last Updated:** January 1, 2026  
**Status:** ✅ Ready for Corporate VM Deployment
