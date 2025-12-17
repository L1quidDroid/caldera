# CALDERA REST API v2 Documentation

**Status**: ✅ Complete  
**Base URL**: `http://localhost:8888/api/v2`  
**Authentication**: API Key header (`KEY: ADMIN123`)

---

## Authentication

All API v2 endpoints require authentication via API key header:

```bash
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/health
```

### API Keys

Configured in `conf/default.yml`:
- **Red Team** (admin): `ADMIN123` - Full access
- **Blue Team**: `BLUEADMIN123` - Limited access

---

## Core Endpoints

### Health Check
```bash
GET /api/v2/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "5.0.0"
}
```

---

### Agents

#### List all agents
```bash
GET /api/v2/agents
```

#### Get specific agent
```bash
GET /api/v2/agents/{paw}
```

#### Update agent
```bash
PATCH /api/v2/agents/{paw}
Content-Type: application/json

{
  "trusted": 1,
  "sleep_min": 30,
  "sleep_max": 60
}
```

---

### Operations

#### List all operations
```bash
GET /api/v2/operations
```

#### Create operation
```bash
POST /api/v2/operations
Content-Type: application/json

{
  "name": "my-operation",
  "adversary": {"adversary_id": "ad-hoc"},
  "auto_close": true,
  "state": "running"
}
```

#### Get operation status
```bash
GET /api/v2/operations/{operation-id}
```

#### Update operation
```bash
PATCH /api/v2/operations/{operation-id}
Content-Type: application/json

{
  "state": "finished"
}
```

---

### Abilities

#### List all abilities
```bash
GET /api/v2/abilities
```

#### Get specific ability
```bash
GET /api/v2/abilities/{ability-id}
```

---

### Adversaries

#### List all adversaries
```bash
GET /api/v2/adversaries
```

---

### Other Endpoints

- `GET /api/v2/objectives` - List objectives
- `GET /api/v2/planners` - List planners
- `GET /api/v2/sources` - List fact sources
- `GET /api/v2/contacts` - List contact methods

---

## Plugin APIs

### Orchestrator Plugin

```bash
GET /plugin/orchestrator/health
GET /plugin/orchestrator/webhooks
POST /plugin/orchestrator/webhooks
```

### Enrollment Plugin

```bash
GET /plugin/enrollment/health
POST /plugin/enrollment/enroll
GET /plugin/enrollment/enroll/{id}
```

See [Webhook Documentation](webhooks.md) for webhook details.

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An error occurred processing your request"
}
```

---

## Complete Examples

See [End-to-End User Journey](../orchestration/user-journey.md) for comprehensive API usage examples.

For troubleshooting API issues, see [Troubleshooting Guide](../TROUBLESHOOTING.md#api-errors).
