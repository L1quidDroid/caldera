#!/bin/bash
################################################################################
# Check CALDERA Setup Progress
################################################################################

CALDERA_IP="68.218.0.170"

echo "🔍 Checking CALDERA setup progress..."
echo ""

# Check if CALDERA web UI is accessible
echo "Testing CALDERA Web UI (http://$CALDERA_IP:8888)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$CALDERA_IP:8888 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ CALDERA is READY!"
    echo ""
    echo "================================================"
    echo "🎉 CALDERA + ELK Stack Deployed!"
    echo "================================================"
    echo ""
    echo "CALDERA Web UI: http://$CALDERA_IP:8888"
    echo "  Login: admin / admin"
    echo ""
    echo "Kibana Dashboard: http://$CALDERA_IP:5601"
    echo "Elasticsearch API: http://$CALDERA_IP:9200"
    echo ""
    echo "Next Steps:"
    echo "  1. Open http://$CALDERA_IP:8888 in browser"
    echo "  2. Deploy agents (see demo_scripts_*/)"
    echo "  3. Run validation: ./demo_validation.sh $CALDERA_IP"
    echo ""
    exit 0
elif [ "$HTTP_CODE" = "000" ]; then
    echo "⏳ CALDERA not ready yet (connection timeout)"
    echo "   Setup is still running... check again in 2-3 minutes"
else
    echo "⏳ CALDERA not ready yet (HTTP $HTTP_CODE)"
    echo "   Setup is still running... check again in 2-3 minutes"
fi

echo ""
echo "Installation typically takes 10-15 minutes."
echo "Run this script again to check progress."
echo ""

# Check if Kibana is up
echo "Testing Kibana (http://$CALDERA_IP:5601)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$CALDERA_IP:5601 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Kibana is ready!"
else
    echo "⏳ Kibana not ready yet"
fi

echo ""
echo "Testing Elasticsearch (http://$CALDERA_IP:9200)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$CALDERA_IP:9200 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Elasticsearch is ready!"
else
    echo "⏳ Elasticsearch not ready yet"
fi

echo ""
