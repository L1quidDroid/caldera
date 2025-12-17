#!/bin/bash
################################################################################
# Upload Branding Plugin to CALDERA VM
# Run this from your local machine after CALDERA is installed on VM
################################################################################

set -e

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <vm-ip-address>"
    echo "Example: $0 68.218.11.202"
    exit 1
fi

VM_IP=$1
VM_USER="tonyto"

echo "================================================"
echo "🎨 Uploading Branding Plugin to CALDERA VM"
echo "================================================"
echo "VM: $VM_USER@$VM_IP"
echo ""

# Get the script directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CALDERA_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "📂 CALDERA root: $CALDERA_ROOT"

# Check if branding plugin exists locally
if [ ! -d "$CALDERA_ROOT/plugins/branding" ]; then
    echo "❌ Error: Branding plugin not found at $CALDERA_ROOT/plugins/branding"
    exit 1
fi

echo "✅ Found branding plugin locally"
echo ""

# Upload branding plugin to VM
echo "📤 Uploading branding plugin..."
scp -r "$CALDERA_ROOT/plugins/branding" "$VM_USER@$VM_IP:~/branding_plugin_temp/"

echo "✅ Branding plugin uploaded"
echo ""

# SSH into VM and move plugin to correct location
echo "📦 Installing branding plugin on VM..."
ssh "$VM_USER@$VM_IP" << 'ENDSSH'
cd ~/caldera
if [ -d "plugins/branding" ]; then
    echo "⚠️  Branding plugin already exists, backing up..."
    mv plugins/branding plugins/branding.backup.$(date +%Y%m%d_%H%M%S)
fi

mv ~/branding_plugin_temp/branding plugins/
rm -rf ~/branding_plugin_temp

echo "✅ Branding plugin installed at ~/caldera/plugins/branding"

# Verify plugin structure
echo ""
echo "📋 Plugin structure:"
ls -la plugins/branding/

# Integrate branding CSS into Magma frontend
echo ""
echo "🎨 Integrating branding CSS into Magma frontend..."
MAGMA_HTML="$HOME/caldera/plugins/magma/dist/index.html"
TIMESTAMP=$(date +%s)

if [ -f "$MAGMA_HTML" ]; then
    # Backup original if not already backed up
    if [ ! -f "${MAGMA_HTML}.original" ]; then
        cp "$MAGMA_HTML" "${MAGMA_HTML}.original"
        echo "✅ Backed up original Magma index.html"
    fi
    
    # Remove any existing branding links
    sed -i '/branding.*css/d' "$MAGMA_HTML"
    
    # Add only override.css (consolidated branding styles)
    sed -i "s|</head>|    <link rel=\"stylesheet\" href=\"/plugin/branding/static/css/override.css?v=${TIMESTAMP}\">\n  </head>|" "$MAGMA_HTML"
    
    echo "✅ Branding CSS integrated into Magma (cache-busting: v=${TIMESTAMP})"
else
    echo "⚠️  Magma dist/index.html not found, skipping frontend integration"
fi

# Also update the dev index.html
MAGMA_DEV_HTML="$HOME/caldera/plugins/magma/index.html"
if [ -f "$MAGMA_DEV_HTML" ]; then
    sed -i '/branding.*css/d' "$MAGMA_DEV_HTML"
    sed -i "s|</head>|    <link rel=\"stylesheet\" href=\"/plugin/branding/static/css/override.css?v=${TIMESTAMP}\">\n  </head>|" "$MAGMA_DEV_HTML"
    echo "✅ Branding CSS integrated into Magma dev index.html"
fi

# Restart CALDERA service if it's running
if systemctl is-active --quiet caldera; then
    echo ""
    echo "🔄 Restarting CALDERA service to load branding plugin..."
    sudo systemctl restart caldera
    sleep 5
    
    if systemctl is-active --quiet caldera; then
        echo "✅ CALDERA service restarted successfully"
        echo ""
        echo "📋 Verifying branding plugin loaded:"
        sudo journalctl -u caldera -n 20 --no-pager | grep -i "branding" | tail -5
    else
        echo "⚠️  CALDERA service failed to restart, check logs:"
        echo "    sudo journalctl -u caldera -n 50"
    fi
else
    echo ""
    echo "ℹ️  CALDERA service not running. Plugin will load on next start."
fi
ENDSSH

echo ""
echo "================================================"
echo "✅ Branding Plugin Installation Complete"
echo "================================================"
echo ""
echo "🌐 Access CALDERA with custom branding:"
echo "   http://$VM_IP:8888"
echo ""
echo "🎨 Branding Features:"
echo "   - Triskele Labs color scheme"
echo "   - Custom logo and favicon"
echo "   - Modified UI layout"
echo ""
echo "🔍 Verify branding in CALDERA logs:"
echo "   ssh $VM_USER@$VM_IP"
echo "   sudo journalctl -u caldera -n 50 | grep -i branding"
echo ""
echo "Expected log message:"
echo "   INFO Branding plugin enabled with theme: triskele_labs"
echo "   INFO Primary colors: #020816 / #48CFA0"
echo "================================================"
