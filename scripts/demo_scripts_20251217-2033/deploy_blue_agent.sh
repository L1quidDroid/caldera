#!/bin/bash
################################################################################
# Deploy Elasticat Blue Team Agent
# Run this on the Linux Blue Agent VM
################################################################################

set -e

CALDERA_SERVER="68.218.11.202"
SERVER_URL="http://$CALDERA_SERVER:8888"
ES_URL="http://$CALDERA_SERVER:9200"
GROUP="blue"

echo "🔵 Deploying Elasticat Blue Team Agent..."
echo "CALDERA: $SERVER_URL"
echo "Elasticsearch: $ES_URL"

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv curl jq

# Create virtual environment
echo "🐍 Creating Python environment..."
python3 -m venv ~/elasticat-venv
source ~/elasticat-venv/bin/activate

# Install required packages
pip install --quiet requests

# Download elasticat agent
echo "⬇️  Downloading agent..."
curl -s -X POST     -H "file:elasticat.py"     -H "platform:linux"     "$SERVER_URL/file/download" > elasticat.py

chmod +x elasticat.py

# Start agent
echo "🚀 Starting agent..."
nohup python elasticat.py     --server="$SERVER_URL"     --es-host="$ES_URL"     --group=$GROUP     --minutes-since=60     > elasticat.log 2>&1 &

AGENT_PID=$!
echo "✅ Agent started (PID: $AGENT_PID)"
echo ""
echo "Agent logs: tail -f elasticat.log"
echo "Check CALDERA UI -> Agents tab to see this agent"
