#!/bin/bash
################################################################################
# Cleanup Failed Deployment and Redeploy with Quota Fix
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Cleanup and Redeploy CALDERA Demo${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Step 1: Find and delete the failed resource group
echo -e "${YELLOW}Step 1: Finding CALDERA resource groups...${NC}"
echo ""
az group list --query "[?contains(name, 'caldera')].{Name:name, Location:location, State:properties.provisioningState}" -o table

echo ""
read -p "Enter the exact resource group name to delete (or press Enter to skip): " RG_TO_DELETE

if [ ! -z "$RG_TO_DELETE" ]; then
    echo -e "${YELLOW}Deleting resource group: $RG_TO_DELETE${NC}"
    az group delete --name "$RG_TO_DELETE" --yes --no-wait
    echo -e "${GREEN}✅ Deletion initiated (running in background)${NC}"
    echo -e "${YELLOW}⏳ Waiting 30 seconds for cleanup...${NC}"
    sleep 30
else
    echo -e "${YELLOW}⏭️  Skipping cleanup${NC}"
fi

# Step 2: Check current quota usage
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Step 2: Checking Current Quota${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

LOCATION="australiaeast"
echo -e "${YELLOW}Checking B-Series quota in $LOCATION...${NC}"
az vm list-usage --location "$LOCATION" --query "[?contains(name.value, 'standardBSFamily')]" -o table

echo ""
echo -e "${YELLOW}Current VMs using quota:${NC}"
az vm list --query '[?location==`australiaeast`].{Name:name, Size:hardwareProfile.vmSize, RG:resourceGroup, State:powerState}' -o table

# Step 3: Redeploy with optimized sizes
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Step 3: Redeploy with Quota-Optimized Sizes${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

echo -e "${GREEN}Configuration:${NC}"
echo "  Server:  1x Standard_B2s (2 cores)"
echo "  Agents:  2x Standard_B1s (1 core each)"
echo "  Total:   4 cores"
echo ""

read -p "Ready to deploy? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Starting deployment...${NC}"
    export VM_SIZE_AGENT=Standard_B1s
    cd "$(dirname "$0")"
    ./demo_caldera_internal.sh
else
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi
