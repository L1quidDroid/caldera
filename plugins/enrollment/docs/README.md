# Enrollment API Plugin

Dynamic agent enrollment REST API for CALDERA, enabling CI/CD integration and automated agent deployment workflows.

## Overview

The Enrollment plugin provides a REST API that simplifies agent enrollment for automated deployments, infrastructure-as-code scenarios, and CI/CD pipelines. It generates platform-specific bootstrap commands and tracks enrollment requests with JSON-based persistence.

**Key Features:**
- REST API for programmatic agent enrollment
- Platform-specific bootstrap command generation (Windows, Linux, macOS)
- Campaign-aware agent tagging
- JSON-based enrollment tracking with persistence
- Environment variable configuration
- Consistent error handling following CALDERA patterns

## Architecture

The plugin integrates with CALDERA's core services and follows the standard plugin architecture:

```
plugins/enrollment/
├── hook.py                    # Plugin integration
├── app/
│   ├── enrollment_api.py      # REST endpoints
│   └── enrollment_svc.py      # Core enrollment logic
├── data/
│   └── enrollment_requests.json  # Persistent storage
├── docs/
│   └── API.md                 # API documentation
└── README.md                  # This file
```

## Installation

The plugin is included in the CALDERA distribution. To enable it:

1. Ensure the plugin directory exists in `plugins/enrollment/`
2. Add `enrollment` to the list of enabled plugins in `conf/local.yml`:

```yaml
plugins:
  - atomic
  - stockpile
  - sandcat
  - enrollment  # Add this line
```

3. Restart CALDERA server

## Configuration

The plugin uses environment variables for configuration:

```bash
# Caldera instance URL (defaults to http://localhost:8888)
export CALDERA_URL=http://localhost:8888

# Optional: Caldera API keys for authenticated operations
export CALDERA_API_KEY_RED=your-red-key
export CALDERA_API_KEY_BLUE=your-blue-key
```

For local development, create a `.env` file:

```bash
cp examples/enrollment/.env.example .env
# Edit .env with your settings
```

## Quick Start

### 1. Verify Plugin is Running

Check the health endpoint:

```bash
curl http://localhost:8888/plugin/enrollment/health | jq '.'
```

Expected response:
```json
{
  "status": "healthy",
  "service": "enrollment",
  "caldera_url": "http://localhost:8888",
  "storage_path": "/path/to/data/enrollment_requests.json",
  "total_requests": 0
}
```

### 2. Enroll an Agent

Create an enrollment request for a Linux agent:

```bash
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linux",
    "campaign_id": "test-campaign-001",
    "tags": ["web-server", "production"],
    "hostname": "web-01"
  }' | jq '.'
```

Response includes the bootstrap command:

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "linux",
  "campaign_id": "test-campaign-001",
  "tags": ["web-server", "production"],
  "status": "pending",
  "created_at": "2025-12-16T10:30:00.000000",
  "bootstrap_command": "curl -sk http://localhost:8888/file/download -o sandcat.go && chmod +x sandcat.go && ./sandcat.go -server http://localhost:8888 -group red -tags web-server,production,campaign:test-campaign-001 &",
  "agent_download_url": "http://localhost:8888/file/download",
  "caldera_url": "http://localhost:8888"
}
```

### 3. Execute Bootstrap Command

On the target host, run the bootstrap command:

```bash
# Linux/macOS
curl -sk http://localhost:8888/file/download -o sandcat.go && \
chmod +x sandcat.go && \
./sandcat.go -server http://localhost:8888 -group red \
  -tags web-server,production,campaign:test-campaign-001 &
```

```powershell
# Windows (PowerShell)
$url="http://localhost:8888/file/download"
$output="sandcat.exe"
Invoke-WebRequest -Uri $url -OutFile $output
.\sandcat.exe -server http://localhost:8888 -group red -tags web-server,production,campaign:test-campaign-001
```

### 4. Verify Agent Connection

Check the agent appears in CALDERA UI or query via API:

```bash
curl http://localhost:8888/plugin/enrollment/campaigns/test-campaign-001/agents | jq '.'
```

## API Reference

See [docs/API.md](docs/API.md) for complete API documentation.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plugin/enrollment/health` | Health check |
| POST | `/plugin/enrollment/enroll` | Create enrollment request |
| GET | `/plugin/enrollment/enroll/{request_id}` | Get enrollment status |
| GET | `/plugin/enrollment/requests` | List enrollment requests |
| GET | `/plugin/enrollment/campaigns/{campaign_id}/agents` | List campaign agents |

## Examples

### Shell Script Testing

Use the provided test script:

```bash
chmod +x examples/enrollment/test_enrollment_api.sh
./examples/enrollment/test_enrollment_api.sh
```

### Python Integration

```python
from examples.enrollment.enroll_from_python import EnrollmentClient

client = EnrollmentClient("http://localhost:8888")

# Enroll agent
enrollment = client.enroll_agent(
    platform="linux",
    campaign_id="my-campaign",
    tags=["test"],
    hostname="test-host"
)

print(f"Bootstrap: {enrollment['bootstrap_command']}")
```

### CI/CD Pipeline (GitHub Actions)

```yaml
- name: Enroll Caldera Agent
  run: |
    curl -X POST ${{ secrets.CALDERA_URL }}/plugin/enrollment/enroll \
      -H "Content-Type: application/json" \
      -d '{
        "platform": "linux",
        "campaign_id": "${{ github.run_id }}",
        "tags": ["ci", "github-actions"],
        "hostname": "${{ runner.name }}"
      }' | jq -r '.bootstrap_command' | bash
```

## Data Storage

Enrollment requests are persisted to JSON for resilience across restarts:

**Location:** `plugins/enrollment/data/enrollment_requests.json`

**Format:**
```json
{
  "550e8400-e29b-41d4-a716-446655440000": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "platform": "linux",
    "campaign_id": "test-campaign-001",
    "tags": ["web-server", "production"],
    "status": "pending",
    "created_at": "2025-12-16T10:30:00.000000",
    "bootstrap_command": "...",
    "agent_download_url": "http://localhost:8888/file/download",
    "caldera_url": "http://localhost:8888"
  }
}
```

**Backup:** Recommended to periodically backup this file for audit trails.

## Troubleshooting

### Plugin Not Loading

**Symptom:** Enrollment endpoints return 404

**Solutions:**
- Verify plugin is in enabled plugins list: `conf/local.yml`
- Check CALDERA logs for plugin initialization errors
- Restart CALDERA server

### Bootstrap Command Fails

**Symptom:** Agent doesn't appear in CALDERA

**Solutions:**
- Verify Caldera URL is accessible from target host
- Check firewall allows port 8888
- Test download URL manually: `curl http://localhost:8888/file/download`
- Review agent logs on target host
- Ensure `sandcat` plugin is enabled in CALDERA

### Enrollment Requests Not Persisting

**Symptom:** Requests disappear after restart

**Solutions:**
- Check `data/` directory permissions
- Verify disk space available
- Review CALDERA logs for write errors
- Manually create `data/enrollment_requests.json` if missing

### Campaign Agents Not Found

**Symptom:** `/campaigns/{id}/agents` returns empty list

**Solutions:**
- Ensure agents use correct tag format: `campaign:{campaign_id}`
- Verify agents are connected (check last_seen timestamp)
- Check agent group matches campaign specification
- Query all agents via CALDERA API: `/api/v2/agents`

## Production Considerations

### Current Limitations (PoC Phase)

- **No Authentication:** Endpoints are open to any caller with network access
- **Single Instance:** JSON storage doesn't support clustering
- **In-Memory Cache:** Some data lost on crash (restored from JSON on restart)
- **No Rate Limiting:** Susceptible to abuse without rate limits

### Future Enhancements

See [ORCHESTRATION_GUIDE.md](../../ORCHESTRATION_GUIDE.md) for the complete roadmap. Planned Phase 5 enhancements:

1. **API Key Authentication**
   - Bearer token authentication
   - Campaign-scoped keys
   - Rate limiting per key

2. **Database Backend**
   - PostgreSQL/SQLite option
   - Transaction support
   - Query performance optimization

3. **Multi-Tenancy**
   - Tenant isolation
   - Resource quotas
   - Audit logging

4. **High Availability**
   - Request queuing (Redis/RabbitMQ)
   - Graceful degradation during Caldera downtime
   - Load balancing support

## Integration with Orchestrator CLI

The enrollment API and orchestrator CLI are **separate** tools:

- **CLI:** Direct Caldera API usage, campaign management, script generation
- **Enrollment API:** REST API for programmatic enrollment, CI/CD integration

Both can be used independently or together:

```bash
# Option 1: Use CLI to generate script, execute manually
python3 orchestrator/cli.py agent enroll campaign-001 host-01 linux

# Option 2: Use enrollment API for automated deployment
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -d '{"platform":"linux","campaign_id":"campaign-001"}'
```

## Support

For issues or questions:

1. Check this README and [docs/API.md](docs/API.md)
2. Review [ORCHESTRATION_GUIDE.md](../../ORCHESTRATION_GUIDE.md)
3. Run health check: `curl http://localhost:8888/plugin/enrollment/health`
4. Check CALDERA logs for errors
5. Test with provided examples in `examples/enrollment/`

## License

Apache 2.0 (same as MITRE CALDERA)

## Contributing

Contributions welcome! Priority areas:

- API key authentication implementation
- Database backend (SQLite/PostgreSQL)
- Rate limiting middleware
- Additional CI/CD platform examples
- Kubernetes operator integration
- Terraform provider
