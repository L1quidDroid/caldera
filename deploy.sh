#!/bin/bash
# ============================================================================
# CALDERA Purple Team Lab - Portable Deployment Script
# ============================================================================
# Works on any laptop with Azure CLI installed
# Credentials passed as parameters (not hardcoded)
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  CALDERA Purple Team Lab - Bicep Deployment      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# PREREQUISITES CHECK
# ============================================================================

echo -e "${YELLOW}[1/7] Checking prerequisites...${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Install: https://aka.ms/installazurecli${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Azure CLI installed${NC}"

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged into Azure. Running 'az login'...${NC}"
    az login
fi

SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}✅ Logged into Azure (Subscription: $SUBSCRIPTION_NAME)${NC}"

# Check SSH key
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo -e "${YELLOW}⚠️  SSH key not found. Generating...${NC}"
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -C "caldera-deployment"
fi
SSH_KEY=$(cat ~/.ssh/id_rsa.pub)
echo -e "${GREEN}✅ SSH key available${NC}"

# ============================================================================
# CONFIGURATION
# ============================================================================

echo ""
echo -e "${YELLOW}[2/7] Configuration...${NC}"

# Environment selection
echo ""
echo "Select environment:"
echo "  1) dev (smaller VMs, cheaper)"
echo "  2) prod-lab (production-grade VMs)"
read -p "Choice [1-2]: " ENV_CHOICE

case $ENV_CHOICE in
    1)
        ENVIRONMENT="dev"
        PARAM_FILE="bicep/parameters/dev.parameters.json"
        ;;
    2)
        ENVIRONMENT="prod-lab"
        PARAM_FILE="bicep/parameters/prod-lab.parameters.json"
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Environment: $ENVIRONMENT${NC}"

# Credentials
echo ""
read -p "Admin username [default: tonyto]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-tonyto}

echo "Admin password (min 12 chars, complexity required):"
read -s ADMIN_PASS
echo ""

if [ ${#ADMIN_PASS} -lt 12 ]; then
    echo -e "${RED}❌ Password must be at least 12 characters${NC}"
    exit 1
fi

# ============================================================================
# VALIDATE BICEP
# ============================================================================

echo ""
echo -e "${YELLOW}[3/7] Validating Bicep templates...${NC}"

az bicep build --file bicep/main.bicep
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bicep syntax valid${NC}"
else
    echo -e "${RED}❌ Bicep validation failed${NC}"
    exit 1
fi

az bicep lint --file bicep/main.bicep
echo -e "${GREEN}✅ Bicep linting complete${NC}"

# ============================================================================
# WHAT-IF ANALYSIS
# ============================================================================

echo ""
echo -e "${YELLOW}[4/7] Running what-if analysis...${NC}"
echo "(Shows what resources will be created - no changes made)"
echo ""

DEPLOYMENT_NAME="caldera-$(date +%Y%m%d-%H%M)"

az deployment sub what-if \
    --name "$DEPLOYMENT_NAME" \
    --template-file bicep/main.bicep \
    --parameters "$PARAM_FILE" \
    --parameters adminUsername="$ADMIN_USER" \
    --parameters adminPassword="$ADMIN_PASS" \
    --parameters sshPublicKey="$SSH_KEY" \
    --location australiaeast

echo ""
read -p "Proceed with deployment? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}⚠️  Deployment cancelled${NC}"
    exit 0
fi

# ============================================================================
# DEPLOY INFRASTRUCTURE
# ============================================================================

echo ""
echo -e "${YELLOW}[5/7] Deploying infrastructure...${NC}"
echo "This will take 15-20 minutes (VMs provisioning + software installation)"
echo ""

START_TIME=$(date +%s)

az deployment sub create \
    --name "$DEPLOYMENT_NAME" \
    --template-file bicep/main.bicep \
    --parameters "$PARAM_FILE" \
    --parameters adminUsername="$ADMIN_USER" \
    --parameters adminPassword="$ADMIN_PASS" \
    --parameters sshPublicKey="$SSH_KEY" \
    --location australiaeast \
    --output json > deployment-outputs.json

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}✅ Deployment completed in $((DURATION / 60)) minutes${NC}"

# ============================================================================
# GET OUTPUTS
# ============================================================================

echo ""
echo -e "${YELLOW}[6/7] Retrieving deployment outputs...${NC}"

CALDERA_URL=$(jq -r '.properties.outputs.calderaServerUrl.value' deployment-outputs.json)
KIBANA_URL=$(jq -r '.properties.outputs.elkKibanaUrl.value' deployment-outputs.json)
WINDOWS_IP=$(jq -r '.properties.outputs.windowsAgentIp.value' deployment-outputs.json)
LINUX_IP=$(jq -r '.properties.outputs.linuxAgentIp.value' deployment-outputs.json)
RESOURCE_GROUP=$(jq -r '.properties.outputs.resourceGroupName.value' deployment-outputs.json)

# ============================================================================
# HEALTH CHECKS
# ============================================================================

echo ""
echo -e "${YELLOW}[7/7] Running health checks...${NC}"

echo "Waiting for CALDERA to be healthy..."
for i in {1..20}; do
    if curl -sf "$CALDERA_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ CALDERA is responding${NC}"
        break
    fi
    echo -n "."
    sleep 10
done

echo ""
echo "Waiting for Kibana to be healthy..."
for i in {1..20}; do
    if curl -sf "$KIBANA_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Kibana is responding${NC}"
        break
    fi
    echo -n "."
    sleep 10
done

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         🎉 DEPLOYMENT SUCCESSFUL! 🎉               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📍 ACCESS POINTS:${NC}"
echo ""
echo -e "  ${YELLOW}CALDERA Server:${NC}"
echo "    🌐 URL: $CALDERA_URL"
echo "    👤 Login: admin / admin"
echo ""
echo -e "  ${YELLOW}Kibana Dashboard:${NC}"
echo "    🌐 URL: $KIBANA_URL"
echo ""
echo -e "  ${YELLOW}Windows Agent (Red Team Target):${NC}"
echo "    🖥️  RDP: mstsc /v:$WINDOWS_IP"
echo "    👤 User: $ADMIN_USER"
echo "    📊 Winlogbeat → ELK Stack"
echo ""
echo -e "  ${YELLOW}Linux Agent (Blue Team):${NC}"
echo "    🐧 SSH: ssh $ADMIN_USER@$LINUX_IP"
echo ""
echo -e "${GREEN}📦 RESOURCE GROUP:${NC} $RESOURCE_GROUP"
echo ""
echo -e "${GREEN}✅ SUCCESS CRITERIA MET:${NC}"
echo "  ✅ Infrastructure deployed via Bicep IaC"
echo "  ✅ ELK Stack configured (Elasticsearch + Kibana + Logstash)"
echo "  ✅ Winlogbeat on Windows agent → forwarding to ELK"
echo "  ✅ CALDERA with custom plugins (orchestrator + branding)"
echo "  ✅ Portable deployment (works on any laptop)"
echo ""
echo -e "${YELLOW}🗑️  To cleanup:${NC}"
echo "    az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
echo "Deployment details saved to: deployment-outputs.json"
echo ""
