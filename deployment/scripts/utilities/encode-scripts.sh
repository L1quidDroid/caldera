#!/bin/bash
# ============================================================================
# Script Encoding Helper
# ============================================================================
# Encodes deployment scripts as base64 for Bicep parameter injection
# ============================================================================

set -euo pipefail

SCRIPTS_DIR="./bicep/scripts"
OUTPUT_DIR="./bicep/parameters"

echo "Encoding deployment scripts..."

# Function to encode script
encode_script() {
    local input_file=$1
    local output_var=$2
    
    if [ ! -f "$input_file" ]; then
        echo "Error: File not found: $input_file"
        return 1
    fi
    
    echo "Encoding: $input_file"
    local encoded
    encoded=$(base64 -w 0 < "$input_file")
    
    echo "    \"$output_var\": {"
    echo "      \"value\": \"$encoded\""
    echo "    },"
    
    return 0
}

# Create temporary JSON file
temp_json=$(mktemp)

echo "{" > "$temp_json"
echo "  \"calderaElkInstallScript\": {" >> "$temp_json"

# Encode main CALDERA+ELK script
if [ -f "$SCRIPTS_DIR/install-caldera-elk.sh" ]; then
    local encoded
    encoded=$(base64 -w 0 < "$SCRIPTS_DIR/install-caldera-elk.sh")
    echo "    \"value\": \"$encoded\"" >> "$temp_json"
else
    echo "Error: install-caldera-elk.sh not found"
    exit 1
fi

echo "  }," >> "$temp_json"

# Encode Windows agent script  
echo "  \"windowsAgentInstallScript\": {" >> "$temp_json"
if [ -f "$SCRIPTS_DIR/install-windows-agent.ps1" ]; then
    local encoded
    encoded=$(base64 -w 0 < "$SCRIPTS_DIR/install-windows-agent.ps1")
    echo "    \"value\": \"$encoded\"" >> "$temp_json"
else
    echo "Error: install-windows-agent.ps1 not found"
    exit 1
fi

echo "  }," >> "$temp_json"

# Encode Linux agent script
echo "  \"linuxAgentInstallScript\": {" >> "$temp_json"
if [ -f "$SCRIPTS_DIR/install-linux-agent.sh" ]; then
    local encoded
    encoded=$(base64 -w 0 < "$SCRIPTS_DIR/install-linux-agent.sh")
    echo "    \"value\": \"$encoded\"" >> "$temp_json"
else
    echo "Error: install-linux-agent.sh not found"
    exit 1
fi

echo "  }" >> "$temp_json"
echo "}" >> "$temp_json"

# Display results
echo ""
echo "=========================================="
echo "Encoded scripts prepared"
echo "=========================================="
echo ""
echo "Add these values to your parameters file:"
echo ""
cat "$temp_json"

# Cleanup
rm -f "$temp_json"

exit 0
