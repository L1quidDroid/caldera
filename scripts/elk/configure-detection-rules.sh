#!/bin/bash
# ============================================================================
# Configure ELK Detection Rules for CALDERA Purple Team Operations
# ============================================================================
# Imports MITRE ATT&CK detection rules and configures Kibana dashboards
# Usage: ./configure-detection-rules.sh <elk-host>
# ============================================================================

set -euo pipefail

ELK_HOST="${1:-localhost}"
ELASTICSEARCH_URL="http://${ELK_HOST}:9200"
KIBANA_URL="http://${ELK_HOST}:5601"

echo "[$(date)] Configuring ELK detection rules for CALDERA operations..."

# Wait for Elasticsearch to be ready
echo "[$(date)] Waiting for Elasticsearch..."
for i in {1..30}; do
    if curl -s "$ELASTICSEARCH_URL/_cluster/health" | grep -q '"status":"green\|yellow"'; then
        echo "[$(date)] ✅ Elasticsearch is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[$(date)] ❌ Elasticsearch did not become ready in time"
        exit 1
    fi
    sleep 2
done

# Create index template for CALDERA logs
echo "[$(date)] Creating index template for caldera-* indices..."
curl -X PUT "$ELASTICSEARCH_URL/_index_template/caldera-logs" -H 'Content-Type: application/json' -d '{
  "index_patterns": ["caldera-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "index.mapping.total_fields.limit": 2000
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" },
        "mitre_technique": { "type": "keyword" },
        "mitre_tactic": { "type": "keyword" },
        "operation_id": { "type": "keyword" },
        "agent_id": { "type": "keyword" },
        "host": {
          "properties": {
            "name": { "type": "keyword" },
            "os": { "type": "keyword" }
          }
        },
        "event": {
          "properties": {
            "action": { "type": "keyword" },
            "category": { "type": "keyword" },
            "outcome": { "type": "keyword" }
          }
        }
      }
    }
  }
}' -s | jq .

# Create saved search for MITRE ATT&CK techniques
echo "[$(date)] Creating saved searches in Kibana..."
curl -X POST "$KIBANA_URL/api/saved_objects/search" -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '{
  "attributes": {
    "title": "CALDERA - MITRE ATT&CK Techniques",
    "description": "All CALDERA operations with detected MITRE ATT&CK techniques",
    "columns": ["@timestamp", "mitre_technique", "mitre_tactic", "operation_id", "agent_id", "message"],
    "sort": [["@timestamp", "desc"]],
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": "{\"index\":\"caldera-*\",\"query\":{\"query\":\"mitre_technique:*\",\"language\":\"lucene\"}}"
    }
  }
}' -s | jq .

# Create visualization for technique frequency
echo "[$(date)] Creating visualizations..."
curl -X POST "$KIBANA_URL/api/saved_objects/visualization" -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '{
  "attributes": {
    "title": "CALDERA - Top MITRE Techniques",
    "description": "Frequency of detected MITRE ATT&CK techniques",
    "visState": "{\"title\":\"Top MITRE Techniques\",\"type\":\"pie\",\"aggs\":[{\"id\":\"1\",\"type\":\"count\",\"schema\":\"metric\"},{\"id\":\"2\",\"type\":\"terms\",\"schema\":\"segment\",\"params\":{\"field\":\"mitre_technique\",\"size\":10}}],\"params\":{\"type\":\"pie\",\"addTooltip\":true,\"addLegend\":true}}",
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": "{\"index\":\"caldera-*\",\"query\":{\"query\":\"mitre_technique:*\",\"language\":\"lucene\"}}"
    }
  }
}' -s | jq .

# Create dashboard
echo "[$(date)] Creating CALDERA Purple Team dashboard..."
curl -X POST "$KIBANA_URL/api/saved_objects/dashboard" -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '{
  "attributes": {
    "title": "CALDERA Purple Team Operations",
    "description": "Real-time monitoring of CALDERA adversary emulation and MITRE ATT&CK technique detection",
    "panelsJSON": "[]",
    "optionsJSON": "{\"darkTheme\":false}",
    "timeRestore": true,
    "timeTo": "now",
    "timeFrom": "now-24h"
  }
}' -s | jq .

# Create Watcher alert for critical techniques
echo "[$(date)] Creating Watcher alert for critical MITRE techniques..."
curl -X PUT "$ELASTICSEARCH_URL/_watcher/watch/caldera-critical-techniques" -H 'Content-Type: application/json' -d '{
  "trigger": {
    "schedule": {
      "interval": "5m"
    }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["caldera-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {
                  "range": {
                    "@timestamp": {
                      "gte": "now-5m"
                    }
                  }
                },
                {
                  "terms": {
                    "mitre_technique": ["T1003", "T1078", "T1059.001", "T1055", "T1486"]
                  }
                }
              ]
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.hits.total": {
        "gt": 0
      }
    }
  },
  "actions": {
    "log_critical_technique": {
      "logging": {
        "text": "CRITICAL: Detected {{ctx.payload.hits.total}} high-impact MITRE ATT&CK techniques in the last 5 minutes. Techniques: T1003 (Credential Dumping), T1078 (Valid Accounts), T1059.001 (PowerShell), T1055 (Process Injection), T1486 (Data Encrypted for Impact)."
      }
    }
  }
}' -s | jq .

# Create detection rules for common CALDERA techniques
echo "[$(date)] Creating detection rules..."

# T1078 - Valid Accounts
curl -X PUT "$ELASTICSEARCH_URL/_watcher/watch/caldera-t1078-valid-accounts" -H 'Content-Type: application/json' -d '{
  "trigger": { "schedule": { "interval": "10m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["caldera-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                { "range": { "@timestamp": { "gte": "now-10m" } } },
                { "term": { "mitre_technique": "T1078" } }
              ]
            }
          }
        }
      }
    }
  },
  "condition": { "compare": { "ctx.payload.hits.total": { "gt": 3 } } },
  "actions": {
    "log_alert": {
      "logging": {
        "text": "ALERT: Multiple Valid Accounts attempts detected (T1078). Count: {{ctx.payload.hits.total}}"
      }
    }
  }
}' -s | jq .

# T1003 - Credential Dumping
curl -X PUT "$ELASTICSEARCH_URL/_watcher/watch/caldera-t1003-credential-dumping" -H 'Content-Type: application/json' -d '{
  "trigger": { "schedule": { "interval": "10m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["caldera-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                { "range": { "@timestamp": { "gte": "now-10m" } } },
                { "term": { "mitre_technique": "T1003" } }
              ]
            }
          }
        }
      }
    }
  },
  "condition": { "compare": { "ctx.payload.hits.total": { "gt": 0 } } },
  "actions": {
    "log_alert": {
      "logging": {
        "text": "CRITICAL: Credential dumping detected (T1003). Count: {{ctx.payload.hits.total}}"
      }
    }
  }
}' -s | jq .

# T1059.001 - PowerShell Execution
curl -X PUT "$ELASTICSEARCH_URL/_watcher/watch/caldera-t1059-001-powershell" -H 'Content-Type: application/json' -d '{
  "trigger": { "schedule": { "interval": "10m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["caldera-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                { "range": { "@timestamp": { "gte": "now-10m" } } },
                { "term": { "mitre_technique": "T1059.001" } }
              ]
            }
          }
        }
      }
    }
  },
  "condition": { "compare": { "ctx.payload.hits.total": { "gt": 10 } } },
  "actions": {
    "log_alert": {
      "logging": {
        "text": "ALERT: High volume of PowerShell execution detected (T1059.001). Count: {{ctx.payload.hits.total}}"
      }
    }
  }
}' -s | jq .

# Verify configuration
echo "[$(date)] Verifying configuration..."
TEMPLATE_COUNT=$(curl -s "$ELASTICSEARCH_URL/_index_template" | jq '.index_templates | length')
WATCHER_COUNT=$(curl -s "$ELASTICSEARCH_URL/_watcher/watch/_search?size=100" | jq '.hits.total.value')

echo "[$(date)] ✅ Index templates: $TEMPLATE_COUNT"
echo "[$(date)] ✅ Watcher alerts: $WATCHER_COUNT"

# Display access information
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ELK Detection Rules Configuration Complete"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Kibana Dashboard: $KIBANA_URL/app/dashboards"
echo "Elasticsearch: $ELASTICSEARCH_URL"
echo ""
echo "Created Detection Rules:"
echo "  - Critical MITRE Techniques (T1003, T1078, T1059.001, T1055, T1486)"
echo "  - Valid Accounts Detection (T1078)"
echo "  - Credential Dumping Detection (T1003)"
echo "  - PowerShell Execution Detection (T1059.001)"
echo ""
echo "Index Pattern: caldera-*"
echo ""

echo "[$(date)] ✅ Configuration complete"
