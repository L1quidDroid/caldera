# Enrollment API Documentation

Complete REST API reference for the CALDERA Enrollment plugin.

## Base URL

```
http://localhost:8888/plugin/enrollment
```

## Authentication

**Current:** None (PoC phase)  
**Future:** Bearer token authentication planned for production

## Response Format

All responses are JSON with consistent structure:

**Success Response:**
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Error Response:**
```json
{
  "error": "Error message description"
}
```

## Endpoints

### Health Check

Get service status and configuration.

**Endpoint:** `GET /plugin/enrollment/health`

**Request:**
```bash
curl http://localhost:8888/plugin/enrollment/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "enrollment",
  "caldera_url": "http://localhost:8888",
  "storage_path": "/path/to/enrollment_requests.json",
  "total_requests": 42
}
```

---

### Create Enrollment Request

Generate agent enrollment instructions.

**Endpoint:** `POST /plugin/enrollment/enroll`

**Request Body:**
```json
{
  "platform": "linux|windows|darwin",
  "campaign_id": "optional-campaign-uuid",
  "tags": ["optional", "tags"],
  "contact": "http",
  "hostname": "optional-hostname"
}
```

**Required Fields:**
- `platform` (string): Target OS - must be `windows`, `linux`, or `darwin`

**Optional Fields:**
- `campaign_id` (string): UUID for campaign tracking
- `tags` (array): Additional agent tags
- `contact` (string): Contact method (default: `http`)
- `hostname` (string): Target hostname

**Example Request:**
```bash
curl -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linux",
    "campaign_id": "test-campaign-001",
    "tags": ["web-server", "production"],
    "hostname": "web-01.example.com"
  }'
```

**Response:** `201 Created`
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "linux",
  "campaign_id": "test-campaign-001",
  "tags": ["web-server", "production"],
  "contact": "http",
  "hostname": "web-01.example.com",
  "status": "pending",
  "created_at": "2025-12-16T10:30:00.000000",
  "bootstrap_command": "curl -sk http://localhost:8888/file/download -o sandcat.go && chmod +x sandcat.go && ./sandcat.go -server http://localhost:8888 -group red -tags web-server,production,campaign:test-campaign-001 &",
  "agent_download_url": "http://localhost:8888/file/download",
  "caldera_url": "http://localhost:8888"
}
```

**Error Responses:**

`400 Bad Request` - Missing or invalid fields:
```json
{
  "error": "Missing required field: platform"
}
```

`400 Bad Request` - Invalid platform:
```json
{
  "error": "Invalid platform: invalid-platform. Must be windows, linux, or darwin"
}
```

`500 Internal Server Error` - Server error:
```json
{
  "error": "Failed to create enrollment: <error details>"
}
```

---

### Get Enrollment Status

Retrieve enrollment request details by ID.

**Endpoint:** `GET /plugin/enrollment/enroll/{request_id}`

**Path Parameters:**
- `request_id` (string): Enrollment request UUID

**Example Request:**
```bash
curl http://localhost:8888/plugin/enrollment/enroll/550e8400-e29b-41d4-a716-446655440000
```

**Response:** `200 OK`
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "linux",
  "campaign_id": "test-campaign-001",
  "tags": ["web-server", "production"],
  "contact": "http",
  "hostname": "web-01.example.com",
  "status": "pending",
  "created_at": "2025-12-16T10:30:00.000000",
  "bootstrap_command": "curl -sk http://localhost:8888/file/download -o sandcat.go && chmod +x sandcat.go && ./sandcat.go -server http://localhost:8888 -group red -tags web-server,production,campaign:test-campaign-001 &",
  "agent_download_url": "http://localhost:8888/file/download",
  "caldera_url": "http://localhost:8888"
}
```

**Error Response:**

`404 Not Found` - Request ID not found:
```json
{
  "error": "Enrollment request not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

---

### List Enrollment Requests

Query enrollment requests with optional filters.

**Endpoint:** `GET /plugin/enrollment/requests`

**Query Parameters:**
- `campaign_id` (string, optional): Filter by campaign UUID
- `platform` (string, optional): Filter by platform (windows, linux, darwin)
- `status` (string, optional): Filter by status (pending, connected, failed)
- `limit` (integer, optional): Maximum results (default: 100)

**Example Requests:**

List all enrollments:
```bash
curl http://localhost:8888/plugin/enrollment/requests
```

Filter by campaign:
```bash
curl "http://localhost:8888/plugin/enrollment/requests?campaign_id=test-campaign-001"
```

Filter by platform and limit:
```bash
curl "http://localhost:8888/plugin/enrollment/requests?platform=linux&limit=50"
```

Multiple filters:
```bash
curl "http://localhost:8888/plugin/enrollment/requests?campaign_id=test-campaign-001&status=pending&limit=10"
```

**Response:** `200 OK`
```json
{
  "total": 5,
  "limit": 100,
  "requests": [
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "platform": "linux",
      "campaign_id": "test-campaign-001",
      "status": "pending",
      "created_at": "2025-12-16T10:30:00.000000"
    },
    {
      "request_id": "660e8400-e29b-41d4-a716-446655440001",
      "platform": "windows",
      "campaign_id": "test-campaign-001",
      "status": "pending",
      "created_at": "2025-12-16T10:25:00.000000"
    }
  ]
}
```

**Notes:**
- Results are sorted by `created_at` descending (newest first)
- All filters are optional and can be combined
- Invalid `limit` values default to 100

---

### List Campaign Agents

Get all agents enrolled for a specific campaign.

**Endpoint:** `GET /plugin/enrollment/campaigns/{campaign_id}/agents`

**Path Parameters:**
- `campaign_id` (string): Campaign UUID

**Example Request:**
```bash
curl http://localhost:8888/plugin/enrollment/campaigns/test-campaign-001/agents
```

**Response:** `200 OK`
```json
{
  "campaign_id": "test-campaign-001",
  "total_agents": 3,
  "agents": [
    {
      "paw": "agent-123-456",
      "hostname": "web-01.example.com",
      "platform": "linux",
      "group": "red",
      "tags": ["web-server", "production", "campaign:test-campaign-001"],
      "last_seen": "2025-12-16T10:45:00.000000"
    },
    {
      "paw": "agent-789-012",
      "hostname": "web-02.example.com",
      "platform": "linux",
      "group": "red",
      "tags": ["web-server", "production", "campaign:test-campaign-001"],
      "last_seen": "2025-12-16T10:44:30.000000"
    }
  ]
}
```

**Notes:**
- Only returns agents with the `campaign:{campaign_id}` tag
- Agents must be currently connected or recently seen in CALDERA
- Empty array returned if no agents found for campaign

**Error Response:**

`500 Internal Server Error` - Error fetching agents:
```json
{
  "error": "Failed to fetch campaign agents: <error details>"
}
```

---

## Data Models

### Enrollment Request

```typescript
{
  request_id: string;          // UUID
  platform: "windows"|"linux"|"darwin";
  campaign_id?: string;        // Optional campaign UUID
  tags: string[];              // Agent tags
  contact: string;             // Contact method (default: "http")
  hostname?: string;           // Optional hostname
  status: "pending"|"connected"|"failed";
  created_at: string;          // ISO 8601 timestamp
  updated_at?: string;         // ISO 8601 timestamp
  bootstrap_command: string;   // Platform-specific command
  agent_download_url: string;  // Sandcat download URL
  caldera_url: string;         // Caldera base URL
  agent_paw?: string;          // PAW if agent connected
}
```

### Campaign Agent

```typescript
{
  paw: string;                 // Agent PAW identifier
  hostname: string;            // Agent hostname
  platform: string;            // OS platform
  group: string;               // Agent group (red/blue)
  tags: string[];              // All agent tags
  last_seen: string;           // ISO 8601 timestamp
}
```

## Bootstrap Commands

### Linux/macOS

```bash
curl -sk http://localhost:8888/file/download -o sandcat.go && \
chmod +x sandcat.go && \
./sandcat.go -server http://localhost:8888 -group red -tags tag1,tag2 &
```

### Windows (PowerShell)

```powershell
$url="http://localhost:8888/file/download";
$output="sandcat.exe";
Invoke-WebRequest -Uri $url -OutFile $output;
.\sandcat.exe -server http://localhost:8888 -group red -tags tag1,tag2
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success - GET requests |
| 201 | Created - POST enrollment request |
| 400 | Bad Request - Invalid or missing parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server-side error |

## Rate Limiting

**Current:** None (PoC phase)  
**Future:** Planned implementation with configurable limits per client

## Versioning

**Current Version:** 1.0 (PoC)  
**API Stability:** Unstable - breaking changes may occur

Future versions will use URL versioning: `/plugin/enrollment/v2/...`

## Examples

### Complete Workflow

```bash
# 1. Check API health
curl http://localhost:8888/plugin/enrollment/health

# 2. Create enrollment
RESPONSE=$(curl -s -X POST http://localhost:8888/plugin/enrollment/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linux",
    "campaign_id": "my-campaign",
    "tags": ["test"]
  }')

# 3. Extract request ID and bootstrap command
REQUEST_ID=$(echo $RESPONSE | jq -r '.request_id')
BOOTSTRAP=$(echo $RESPONSE | jq -r '.bootstrap_command')

# 4. Execute bootstrap on target host
ssh user@target-host "$BOOTSTRAP"

# 5. Monitor enrollment status
curl http://localhost:8888/plugin/enrollment/enroll/$REQUEST_ID

# 6. List campaign agents
curl http://localhost:8888/plugin/enrollment/campaigns/my-campaign/agents
```

### Python Client

```python
import requests

# Create enrollment
response = requests.post(
    "http://localhost:8888/plugin/enrollment/enroll",
    json={
        "platform": "linux",
        "campaign_id": "my-campaign",
        "tags": ["automated"]
    }
)
enrollment = response.json()

# Execute bootstrap (pseudo-code)
import subprocess
subprocess.run(enrollment['bootstrap_command'], shell=True)

# Check status
status = requests.get(
    f"http://localhost:8888/plugin/enrollment/enroll/{enrollment['request_id']}"
).json()
print(f"Status: {status['status']}")
```

## Support

- **Documentation:** [plugins/enrollment/docs/](.)
- **Examples:** [examples/enrollment/](../../examples/enrollment/)
- **Issues:** Check CALDERA logs for detailed error messages
