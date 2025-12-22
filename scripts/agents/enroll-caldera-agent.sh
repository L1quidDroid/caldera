#!/bin/bash
# ============================================================================
# Enroll CALDERA Agent - Linux
# ============================================================================
# Installs and starts Sandcat agent on Linux hosts
# Usage: ./enroll-caldera-agent.sh <caldera-url> <group>
# ============================================================================

set -euo pipefail

CALDERA_URL="${1:-http://localhost:8888}"
GROUP="${2:-blue}"

echo "[$(date)] Enrolling agent in CALDERA at $CALDERA_URL..."

# Download Sandcat agent
SANDCAT_URL="${CALDERA_URL}/file/download"
AGENT_PATH="/tmp/sandcat"

echo "[$(date)] Downloading Sandcat agent..."
curl -s "$SANDCAT_URL" -o "$AGENT_PATH"

if [ ! -f "$AGENT_PATH" ]; then
    echo "[$(date)] ❌ Failed to download Sandcat agent"
    exit 1
fi

chmod +x "$AGENT_PATH"
echo "[$(date)] Downloaded: $AGENT_PATH ($(stat -f%z "$AGENT_PATH" 2>/dev/null || stat -c%s "$AGENT_PATH") bytes)"

# Start agent in background
echo "[$(date)] Starting Sandcat agent (group: $GROUP)..."
nohup "$AGENT_PATH" -server "$CALDERA_URL" -group "$GROUP" -v > /dev/null 2>&1 &
AGENT_PID=$!

if ps -p $AGENT_PID > /dev/null; then
    echo "[$(date)] ✅ Agent started successfully (PID: $AGENT_PID)"
else
    echo "[$(date)] ❌ Failed to start Sandcat agent"
    exit 1
fi

# Verify beacon (wait 15 seconds)
sleep 15

if command -v curl &> /dev/null; then
    ACTIVE_AGENTS=$(curl -s -H "KEY: ADMIN123" "${CALDERA_URL}/api/v2/agents" | grep -o "\"group\":\"$GROUP\"" | wc -l || echo "0")
    echo "[$(date)] Active agents in group '$GROUP': $ACTIVE_AGENTS"
    
    if [ "$ACTIVE_AGENTS" -gt 0 ]; then
        echo "[$(date)] ✅ Agent check-in confirmed"
    else
        echo "[$(date)] ⚠️ Agent not visible in CALDERA yet (may take 30-60s for first beacon)"
    fi
fi

echo "[$(date)] ✅ Enrollment complete"
