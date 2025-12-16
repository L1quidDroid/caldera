# Phase 5 Requirements Test Suite

Comprehensive test suite to validate all Phase 5 Enrollment API requirements are met.

## Requirements Tested

### 1. Plugin Structure & Integration
- ✓ Plugin directory exists at `plugins/enrollment/`
- ✓ `hook.py` implements proper plugin interface
- ✓ Plugin integrates with CALDERA services
- ✓ Service modules exist (enrollment_svc.py, enrollment_api.py)

### 2. REST API Endpoints
- ✓ `GET /plugin/enrollment/health` - Health check
- ✓ `POST /plugin/enrollment/enroll` - Create enrollment
- ✓ `GET /plugin/enrollment/enroll/{id}` - Get enrollment status
- ✓ `GET /plugin/enrollment/requests` - List enrollments with filters
- ✓ `GET /plugin/enrollment/campaigns/{id}/agents` - List campaign agents
- ✓ Error handling (400, 404, 500 responses)
- ✓ Response structure validation

### 3. JSON Persistent Storage
- ✓ Storage file exists at `plugins/enrollment/data/enrollment_requests.json`
- ✓ Valid JSON structure
- ✓ Required fields present in entries
- ✓ Data persists across operations

### 4. Platform-Specific Bootstrap Generation
- ✓ Windows PowerShell commands
- ✓ Linux bash commands
- ✓ macOS bash commands
- ✓ Campaign tagging included in commands
- ✓ Custom tags included in commands

### 5. Environment Configuration
- ✓ `CALDERA_URL` environment variable support
- ✓ Localhost fallback (`http://localhost:8888`)
- ✓ Configuration exposed in health endpoint
- ✓ URLs included in enrollment responses

### 6. Testing Examples
- ✓ Bash test script exists and is executable
- ✓ Python client example exists and is executable
- ✓ `.env.example` configuration template
- ✓ Examples contain proper test commands

### 7. Comprehensive Documentation
- ✓ Plugin README (>3000 bytes)
- ✓ API documentation (>5000 bytes)
- ✓ All endpoints documented
- ✓ Examples and responses included
- ✓ ORCHESTRATION_GUIDE.md updated

### 8. CLI/API Separation
- ✓ Orchestrator CLI exists independently
- ✓ Enrollment API works independently
- ✓ Documentation clarifies separation

## Running the Tests

### Prerequisites

1. **Start Caldera server:**
   ```bash
   cd /path/to/caldera
   source venv/bin/activate
   python server.py
   ```

2. **Enable enrollment plugin** in `conf/local.yml`:
   ```yaml
   plugins:
     - enrollment
   ```

3. **Set environment variables** (optional):
   ```bash
   export CALDERA_URL=http://localhost:8888
   ```

### Run Test Suite

```bash
# From caldera directory
./tests/test_phase5_requirements.py

# Or with explicit path
python3 tests/test_phase5_requirements.py
```

### Expected Output

```
╔══════════════════════════════════════════════════════════════════╗
║         PHASE 5 ENROLLMENT API - REQUIREMENTS VALIDATION         ║
║                                                                  ║
║  Caldera URL: http://localhost:8888                             ║
╚══════════════════════════════════════════════════════════════════╝

==================================================================
Requirement 1: Plugin Structure & Integration
==================================================================

→ Testing: Plugin directory structure
  ✓ PASS: Plugin directory exists at plugins/enrollment/
    Found: /path/to/caldera/plugins/enrollment

→ Testing: hook.py plugin integration
  ✓ PASS: hook.py implements plugin interface
    name=True, enable()=True, routes=True

...

==================================================================
TEST SUMMARY
==================================================================

Total Tests:  50+
Passed:       50+
Failed:       0
Pass Rate:    100.0%

✓ ALL PHASE 5 REQUIREMENTS MET
```

## Test Categories

### File System Tests
- Directory structure
- File existence
- File permissions (executable)
- File content validation

### API Tests
- HTTP endpoint accessibility
- Request/response validation
- Error handling
- Query parameter filtering
- JSON response structure

### Functional Tests
- Enrollment creation
- Status retrieval
- Data persistence
- Bootstrap command generation
- Campaign agent listing

### Documentation Tests
- File existence
- Content completeness
- Section presence
- Example inclusion
- File size (as proxy for thoroughness)

## Troubleshooting

### Test Failures

**Connection Errors:**
```
Error: Cannot connect to Caldera at http://localhost:8888
```
- Ensure Caldera is running: `python server.py`
- Check port 8888 is not blocked
- Verify CALDERA_URL environment variable

**Plugin Not Enabled:**
```
Response status: 404
```
- Add `enrollment` to `conf/local.yml` plugins list
- Restart Caldera server

**Import Errors:**
```
ModuleNotFoundError: No module named 'requests'
```
- Install dependencies: `pip install requests`

### Partial Failures

If some tests fail, the output will show:
```
✗ SOME REQUIREMENTS NOT MET

Failed Tests:
  - Test name
    Error message
```

Review the specific failed test and:
1. Check the error message for details
2. Verify file paths are correct
3. Ensure Caldera is fully started
4. Check plugin initialization in Caldera logs

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed or error occurred
- `130` - Tests interrupted by user (Ctrl+C)

## Integration with CI/CD

This test suite can be integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
- name: Test Phase 5 Requirements
  run: |
    source venv/bin/activate
    python server.py &
    SERVER_PID=$!
    sleep 10  # Wait for server startup
    python tests/test_phase5_requirements.py
    kill $SERVER_PID
```

### Local Testing

```bash
# Run as part of development workflow
./tests/test_phase5_requirements.py && echo "Ready to commit"
```

## Test Coverage

This suite covers:
- **8 requirement categories**
- **50+ individual test cases**
- **File system, API, and documentation validation**
- **Error handling and edge cases**

## Maintenance

When updating Phase 5 implementation:

1. Run test suite before changes
2. Make implementation changes
3. Run test suite after changes
4. Update tests if requirements change
5. Document any new requirements

## Contributing

To add new tests:

1. Add test method to `Phase5TestSuite` class
2. Follow naming convention: `test_requirement_N_description`
3. Use `self.assert_test()` for assertions
4. Include descriptive messages
5. Update this README with new test category

## License

Apache 2.0 (same as CALDERA)
