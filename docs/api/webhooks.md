# Webhook Integration Guide

**📌 For complete webhook examples, see [END_TO_END_USER_JOURNEY.md](../../END_TO_END_USER_JOURNEY.md#step-34-verify-webhook-functionality)**

---

## Overview

CALDERA's webhook system allows you to receive real-time notifications about campaign and operation events.

### Supported Events

| Event Type | Routing Key | Description |
|------------|-------------|-------------|
| Operation Created | `operation.created` | New operation started |
| Operation Updated | `operation.updated` | Operation state changed |
| Operation Completed | `operation.completed` | Operation finished |
| Campaign Started | `campaign.started` | Campaign initiated |
| Campaign Completed | `campaign.completed` | All campaign operations done |
| Agent Connected | `agent.connected` | New agent beacon |
| Agent Disconnected | `agent.disconnected` | Agent timeout |

---

## Quick Start

### 1. Register a Webhook

```bash
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://webhook.site/your-unique-id",
    "exchanges": ["operation", "campaign"],
    "queues": ["*"]
  }'
```

### 2. Trigger an Event

```bash
# Create an operation (triggers operation.created)
curl -X POST http://localhost:8888/api/v2/operations \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-operation",
    "adversary": {"adversary_id": "ad-hoc"}
  }'
```

### 3. Receive Payload

Your webhook endpoint will receive:

```json
{
  "exchange": "operation",
  "routing_key": "operation.created",
  "timestamp": "2025-12-17T10:30:00Z",
  "data": {
    "id": "operation-id",
    "name": "test-operation",
    "state": "running",
    "adversary": {...}
  }
}
```

---

## Testing Webhooks

### Option A: webhook.site (Recommended)

1. Visit https://webhook.site
2. Copy your unique URL
3. Register it with CALDERA
4. Trigger events and watch them appear

### Option B: Local Test Server

```python
# webhook_receiver.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        print("📥 Webhook Received:")
        print(json.dumps(json.loads(body), indent=2))
        
        self.send_response(200)
        self.end_headers()

HTTPServer(('localhost', 9000), WebhookHandler).serve_forever()
```

```bash
python3 webhook_receiver.py
```

---

## Advanced Configuration

### Filter by Specific Events

```bash
# Only operation updates
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-endpoint.com/webhook",
    "exchanges": ["operation"],
    "queues": ["operation.updated"]
  }'
```

### Filter by Campaign

```bash
# Only events for specific campaign
curl -X POST http://localhost:8888/plugin/orchestrator/webhooks \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-endpoint.com/webhook",
    "exchanges": ["campaign"],
    "queues": ["campaign.my-campaign-id"]
  }'
```

---

## Management

### List Webhooks

```bash
curl -H "KEY: ADMIN123" http://localhost:8888/plugin/orchestrator/webhooks
```

### Webhook Statistics

```json
{
  "url": "https://webhook.site/...",
  "stats": {
    "sent": 42,
    "failed": 0,
    "last_sent": "2025-12-17T10:30:00Z"
  }
}
```

---

## Troubleshooting

For webhook troubleshooting, see:
- [Troubleshooting Guide - Webhook Issues](../TROUBLESHOOTING.md#webhook-troubleshooting)
- [End-to-End User Journey - Step 3.4](../../END_TO_END_USER_JOURNEY.md#step-34-verify-webhook-functionality)

---

## Security Considerations

1. **HTTPS Only** - Use HTTPS URLs in production
2. **Validate Payloads** - Verify webhook source
3. **Rate Limiting** - Implement rate limits on your endpoint
4. **Timeouts** - Handle slow webhook receivers gracefully
5. **Secrets** - Consider webhook signing (future feature)
