#!/bin/bash
################################################################################
# Demo Validation Script
# Validates that all components are ready for executive demo
################################################################################

if [ -z "$1" ]; then
    echo "Usage: $0 <CALDERA_IP>"
    exit 1
fi

CALDERA_IP=$1
API_USER="admin"
API_PASS="admin"

echo "================================================"
echo "🔍 DEMO VALIDATION"
echo "================================================"
echo ""

# Check CALDERA
echo "✅ CALDERA Web UI:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$CALDERA_IP:8888)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ http://$CALDERA_IP:8888 - OK ($HTTP_CODE)"
else
    echo "   ❌ http://$CALDERA_IP:8888 - FAIL ($HTTP_CODE)"
fi

# Check Kibana
echo ""
echo "✅ Kibana Dashboard:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$CALDERA_IP:5601)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "   ✅ http://$CALDERA_IP:5601 - OK ($HTTP_CODE)"
else
    echo "   ❌ http://$CALDERA_IP:5601 - FAIL ($HTTP_CODE)"
fi

# Check Elasticsearch
echo ""
echo "✅ Elasticsearch API:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$CALDERA_IP:9200)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ http://$CALDERA_IP:9200 - OK ($HTTP_CODE)"
else
    echo "   ❌ http://$CALDERA_IP:9200 - FAIL ($HTTP_CODE)"
fi

# Check agents
echo ""
echo "✅ Registered Agents:"
AGENT_COUNT=$(curl -s -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/agents 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
echo "   📊 $AGENT_COUNT agent(s) registered"

if [ "$AGENT_COUNT" -gt 0 ]; then
    echo "   Agent details:"
    curl -s -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/agents | \
        jq -r '.[] | "      - \(.paw): \(.platform) (\(.group))"' 2>/dev/null || echo "      (unable to parse)"
fi

echo ""
echo "================================================"
echo "🎬 DEMO FLOW (5-10 minutes)"
echo "================================================"
echo ""
echo "1️⃣  Open CALDERA UI: http://$CALDERA_IP:8888"
echo "   Login: admin / admin"
echo ""
echo "2️⃣  Navigate to Agents tab"
echo "   Verify red and blue agents are connected"
echo ""
echo "3️⃣  Navigate to Operations tab"
echo "   Click 'Create Operation'"
echo "   Select adversary (e.g., 'Collection')"
echo "   Select red group"
echo "   Start operation"
echo ""
echo "4️⃣  Monitor operation execution"
echo "   Watch abilities execute in real-time"
echo "   Review command output"
echo ""
echo "5️⃣  Open Kibana: http://$CALDERA_IP:5601"
echo "   Create index pattern for agent logs"
echo "   Visualize blue team monitoring"
echo ""
echo "6️⃣  API Integration Demo:"
echo "   curl -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/agents"
echo "   curl -u $API_USER:$API_PASS http://$CALDERA_IP:8888/api/v2/operations"
echo ""
echo "================================================"
echo "🎯 APPROVAL POINTS"
echo "================================================"
echo ""
echo "✅ Production-ready architecture (systemd services)"
echo "✅ Multi-agent orchestration (red/blue teams)"
echo "✅ Real-time monitoring (ELK integration)"
echo "✅ REST API for automation (Copilot integration ready)"
echo "✅ Purple team capabilities (adversary emulation + detection)"
echo ""
echo "================================================"
