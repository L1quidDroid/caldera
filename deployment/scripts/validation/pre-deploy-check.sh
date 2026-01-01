#!/bin/bash
# ============================================================================
# Pre-Deployment Validation Script
# ============================================================================
# Validates Bicep templates and environment before deployment
# ============================================================================

set -euo pipefail

BICEP_DIR="${1:-.}/bicep"
PARAM_FILE="${2:-.}/bicep/parameters/dev.parameters.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Validating CALDERA Bicep Deployment${NC}"
echo "========================================"

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ Azure CLI not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Azure CLI${NC}"

if ! command -v jq &> /dev/null; then
    echo -e "${RED}✗ jq not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ jq${NC}"

# Validate bicep files exist
echo ""
echo "Checking Bicep files..."

files=(
    "$BICEP_DIR/main.bicep"
    "$BICEP_DIR/modules/network.bicep"
    "$BICEP_DIR/modules/logging.bicep"
    "$BICEP_DIR/modules/caldera-elk-server.bicep"
    "$BICEP_DIR/modules/windows-agent.bicep"
    "$BICEP_DIR/modules/linux-agent.bicep"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ Missing: $file${NC}"
        exit 1
    fi
done

# Validate parameter file
echo ""
echo "Checking parameter files..."

if [ -f "$PARAM_FILE" ]; then
    echo -e "${GREEN}✓ Parameter file found${NC}"
    
    # Validate JSON
    if jq empty "$PARAM_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ JSON is valid${NC}"
    else
        echo -e "${RED}✗ Invalid JSON in parameter file${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Parameter file not found: $PARAM_FILE${NC}"
fi

# Validate Bicep syntax
echo ""
echo "Validating Bicep syntax..."

if az bicep validate --file "$BICEP_DIR/main.bicep" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Bicep syntax valid${NC}"
else
    echo -e "${RED}✗ Bicep validation failed${NC}"
    az bicep validate --file "$BICEP_DIR/main.bicep"
    exit 1
fi

# Check Azure CLI authentication
echo ""
echo "Checking Azure authentication..."

if az account show >/dev/null 2>&1; then
    ACCOUNT=$(az account show --query "[name,user.name]" -o tsv)
    echo -e "${GREEN}✓ Authenticated as: $ACCOUNT${NC}"
else
    echo -e "${RED}✗ Not authenticated. Run: az login${NC}"
    exit 1
fi

# Validate scripts exist
echo ""
echo "Checking deployment scripts..."

scripts=(
    "$BICEP_DIR/scripts/install-caldera-elk.sh"
    "$BICEP_DIR/scripts/install-linux-agent.sh"
    "$BICEP_DIR/scripts/install-windows-agent.ps1"
    "$BICEP_DIR/scripts/lib-common.sh"
    "$BICEP_DIR/scripts/lib-elasticsearch.sh"
    "$BICEP_DIR/scripts/lib-caldera.sh"
    "$BICEP_DIR/scripts/lib-elk.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        echo -e "${GREEN}✓ $script${NC}"
    else
        echo -e "${RED}✗ Missing: $script${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All validations passed! Ready to deploy.${NC}"
echo -e "${GREEN}========================================${NC}"

exit 0
