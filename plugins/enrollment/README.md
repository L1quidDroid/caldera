# Enrollment API Plugin - Phase 5

**Status:** ✅ Completed (December 2025)

## Overview

Dynamic agent enrollment REST API for CALDERA, enabling CI/CD integration and automated agent deployment workflows. The plugin integrates directly with CALDERA's core services and provides platform-specific bootstrap command generation with JSON-based persistence.

## Features

- ✅ REST API for programmatic agent enrollment
- ✅ Platform-specific bootstrap generation (Windows, Linux, macOS)
- ✅ Campaign-aware agent tagging
- ✅ JSON-based persistent storage
- ✅ Environment variable configuration
- ✅ Consistent error handling following CALDERA patterns
- ✅ Comprehensive testing examples and documentation

## Quick Start

1. **Enable plugin** in `conf/local.yml`:
   ```yaml
   plugins:
     - enrollment
   ```

2. **Start CALDERA:**
   ```bash
   python server.py
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:8888/plugin/enrollment/health
   ```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plugin/enrollment/health` | Health check |
| POST | `/plugin/enrollment/enroll` | Create enrollment request |
| GET | `/plugin/enrollment/enroll/{request_id}` | Get enrollment status |
| GET | `/plugin/enrollment/requests` | List enrollment requests |
| GET | `/plugin/enrollment/campaigns/{campaign_id}/agents` | List campaign agents |

## Documentation

- **Complete Guide:** [docs/README.md](docs/README.md) - Installation, usage, troubleshooting
- **API Reference:** [docs/API.md](docs/API.md) - Full endpoint documentation with examples
- **Test Suite:** [../../tests/test_phase5_requirements.py](../../tests/test_phase5_requirements.py) - Requirement validation
- **Examples:** [../../examples/enrollment/](../../examples/enrollment/) - Bash and Python examples

## Testing

```bash
# Run comprehensive test suite
./tests/test_phase5_requirements.py

# Or use provided examples
./examples/enrollment/test_enrollment_api.sh
./examples/enrollment/enroll_from_python.py
```

See [docs/README.md](docs/README.md) for complete documentation.
