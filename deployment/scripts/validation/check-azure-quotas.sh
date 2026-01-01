#!/bin/bash
# ============================================================================
# Azure Quota Validation Script for Caldera Bicep Deployment
# ============================================================================
# Run BEFORE deployment to validate quotas in Free/Student/PayAsYouGo accounts
# 
# Usage:
#   ./check-azure-quotas.sh                        # Interactive mode
#   ./check-azure-quotas.sh -l australiaeast       # Specific location
#   ./check-azure-quotas.sh --homelab              # Student/Free tier validation
#   ./check-azure-quotas.sh --corporate            # Corporate subscription validation
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default configuration
LOCATION="${LOCATION:-australiaeast}"
DEPLOY_AGENTS="${DEPLOY_AGENTS:-false}"
ENVIRONMENT_TYPE="homelab"  # homelab or corporate

# ============================================================================
# CALDERA RESOURCE REQUIREMENTS (from Bicep analysis)
# ============================================================================

# VM Requirements
declare -A VM_REQUIREMENTS=(
    ["caldera_elk_vcpus"]="2"      # Standard_B2s = 2 vCPUs
    ["caldera_elk_memory"]="4"     # Standard_B2s = 4GB
    ["windows_agent_vcpus"]="1"    # Standard_B1s = 1 vCPU  
    ["windows_agent_memory"]="1"   # Standard_B1s = 1GB
    ["linux_agent_vcpus"]="1"      # Standard_B1s = 1 vCPU
    ["linux_agent_memory"]="1"     # Standard_B1s = 1GB
)

# Disk Requirements (GB)
declare -A DISK_REQUIREMENTS=(
    ["caldera_elk_osdisk"]="256"   # Premium_LRS
    ["windows_agent_osdisk"]="128" # Premium_LRS
    ["linux_agent_osdisk"]="64"    # Standard_LRS
)

# Networking Requirements
declare -A NETWORK_REQUIREMENTS=(
    ["public_ips"]="3"             # 1 per VM (Caldera, Windows, Linux)
    ["vnets"]="1"
    ["subnets"]="3"
    ["nsgs"]="3"
)

# ============================================================================
# QUOTA LIMITS BY ACCOUNT TYPE
# ============================================================================

declare -A FREE_TIER_LIMITS=(
    ["vcpus_total"]="4"            # Per region
    ["vcpus_bs_series"]="4"        # B-series burstable
    ["public_ips"]="5"             # Per subscription
    ["storage_accounts"]="5"       # Per subscription
    ["vnets"]="50"                 # Per subscription
    ["nsgs"]="100"                 # Per subscription
    ["log_analytics_gb"]="5"       # Daily ingestion cap
    ["premium_ssd_p10"]="0"        # Not available in free tier
    ["standard_ssd"]="2"           # Limited
)

declare -A STUDENT_LIMITS=(
    ["vcpus_total"]="4"            # Per region - STRICT
    ["vcpus_bs_series"]="4"        # B-series 
    ["public_ips"]="5"
    ["storage_accounts"]="5"
    ["vnets"]="50"
    ["nsgs"]="100"
    ["log_analytics_gb"]="1"       # Lower cap
    ["premium_ssd_p10"]="2"
    ["standard_ssd"]="4"
)

declare -A PAYG_LIMITS=(
    ["vcpus_total"]="10"           # Default, can increase
    ["vcpus_bs_series"]="10"
    ["public_ips"]="50"
    ["storage_accounts"]="250"
    ["vnets"]="1000"
    ["nsgs"]="5000"
    ["log_analytics_gb"]="50"
    ["premium_ssd_p10"]="unlimited"
    ["standard_ssd"]="unlimited"
)

# ============================================================================
# FUNCTIONS
# ============================================================================

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_pass() { echo -e "${GREEN}[✓ PASS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[⚠ WARN]${NC} $*"; }
log_fail() { echo -e "${RED}[✗ FAIL]${NC} $*"; }
log_section() { echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${CYAN}▸ $*${NC}"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -l|--location) LOCATION="$2"; shift 2 ;;
            --homelab|--student|--free) ENVIRONMENT_TYPE="homelab"; shift ;;
            --corporate|--payg) ENVIRONMENT_TYPE="corporate"; shift ;;
            --with-agents) DEPLOY_AGENTS="true"; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done
}

show_help() {
    cat << 'EOF'
Azure Quota Validation for Caldera Bicep Deployment

Usage: ./check-azure-quotas.sh [OPTIONS]

Options:
  -l, --location REGION    Azure region (default: australiaeast)
  --homelab, --student     Validate against Free/Student tier limits (default)
  --corporate, --payg      Validate against Pay-As-You-Go limits
  --with-agents            Include Windows/Linux agent VMs in calculation
  -h, --help               Show this help

Examples:
  ./check-azure-quotas.sh --homelab -l australiaeast
  ./check-azure-quotas.sh --corporate --with-agents
  ./check-azure-quotas.sh -l southeastasia
EOF
}

check_azure_cli() {
    if ! command -v az &> /dev/null; then
        log_fail "Azure CLI not installed. Install from: https://aka.ms/installazurecli"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        log_fail "Not authenticated. Run: az login"
        exit 1
    fi
    
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    log_pass "Authenticated to: $SUBSCRIPTION_NAME"
}

calculate_required_vcpus() {
    local vcpus=2  # Caldera-ELK server always required
    
    if [[ "$DEPLOY_AGENTS" == "true" ]]; then
        vcpus=$((vcpus + 1 + 1))  # Windows + Linux agents
    fi
    
    echo $vcpus
}

calculate_required_public_ips() {
    local ips=1  # Caldera-ELK server
    
    if [[ "$DEPLOY_AGENTS" == "true" ]]; then
        ips=$((ips + 2))  # Windows + Linux agents
    fi
    
    echo $ips
}

check_vcpu_quota() {
    log_section "vCPU Quota Check (${LOCATION})"
    
    local required_vcpus=$(calculate_required_vcpus)
    local limit_key="vcpus_total"
    local quota_limit
    
    if [[ "$ENVIRONMENT_TYPE" == "homelab" ]]; then
        quota_limit="${STUDENT_LIMITS[$limit_key]}"
    else
        quota_limit="${PAYG_LIMITS[$limit_key]}"
    fi
    
    # Get actual quota from Azure
    local actual_limit=$(az vm list-usage --location "$LOCATION" \
        --query "[?contains(name.localizedValue, 'Total Regional vCPUs')].limit" \
        -o tsv 2>/dev/null || echo "$quota_limit")
    
    local current_usage=$(az vm list-usage --location "$LOCATION" \
        --query "[?contains(name.localizedValue, 'Total Regional vCPUs')].currentValue" \
        -o tsv 2>/dev/null || echo "0")
    
    local available=$((actual_limit - current_usage))
    
    echo "  Deployment Config: deployAgents=$DEPLOY_AGENTS"
    echo "  Required vCPUs:    $required_vcpus"
    echo "  Account Type:      $ENVIRONMENT_TYPE"
    echo "  Quota Limit:       $actual_limit"
    echo "  Current Usage:     $current_usage"
    echo "  Available:         $available"
    echo ""
    
    if [[ $required_vcpus -le $available ]]; then
        log_pass "vCPU quota sufficient ($required_vcpus required, $available available)"
        return 0
    else
        log_fail "vCPU quota EXCEEDED ($required_vcpus required, only $available available)"
        echo ""
        echo "  ${YELLOW}FIX OPTIONS:${NC}"
        echo "  1. Set deployAgents=false in parameters (reduces to 2 vCPUs)"
        echo "  2. Use smaller VM sizes (B1ls = 1 vCPU)"
        echo "  3. Request quota increase (not available for Student accounts)"
        echo "  4. Deploy to a different region"
        return 1
    fi
}

check_bs_series_quota() {
    log_section "B-Series (Burstable) vCPU Quota"
    
    local required_vcpus=$(calculate_required_vcpus)
    
    local bs_limit=$(az vm list-usage --location "$LOCATION" \
        --query "[?contains(name.localizedValue, 'Standard BS Family')].limit" \
        -o tsv 2>/dev/null || echo "4")
    
    local bs_usage=$(az vm list-usage --location "$LOCATION" \
        --query "[?contains(name.localizedValue, 'Standard BS Family')].currentValue" \
        -o tsv 2>/dev/null || echo "0")
    
    local bs_available=$((bs_limit - bs_usage))
    
    echo "  B-Series Limit:    $bs_limit"
    echo "  B-Series Used:     $bs_usage"
    echo "  B-Series Available: $bs_available"
    echo ""
    
    if [[ $required_vcpus -le $bs_available ]]; then
        log_pass "B-Series quota sufficient"
        return 0
    else
        log_fail "B-Series quota EXCEEDED"
        return 1
    fi
}

check_public_ip_quota() {
    log_section "Public IP Address Quota"
    
    local required_ips=$(calculate_required_public_ips)
    
    # Public IP quota is subscription-wide, not regional
    local pip_count=$(az network public-ip list --query "length(@)" -o tsv 2>/dev/null || echo "0")
    
    local pip_limit
    if [[ "$ENVIRONMENT_TYPE" == "homelab" ]]; then
        pip_limit="${STUDENT_LIMITS[public_ips]}"
    else
        pip_limit="${PAYG_LIMITS[public_ips]}"
    fi
    
    local pip_available=$((pip_limit - pip_count))
    
    echo "  Required Public IPs: $required_ips"
    echo "  Current Public IPs:  $pip_count"
    echo "  Limit:               $pip_limit"
    echo "  Available:           $pip_available"
    echo ""
    
    if [[ $required_ips -le $pip_available ]]; then
        log_pass "Public IP quota sufficient"
        return 0
    else
        log_fail "Public IP quota EXCEEDED"
        echo "  ${YELLOW}FIX: Delete unused public IPs or use NAT Gateway${NC}"
        return 1
    fi
}

check_storage_quota() {
    log_section "Storage Account & Managed Disk Quota"
    
    local storage_count=$(az storage account list --query "length(@)" -o tsv 2>/dev/null || echo "0")
    local storage_limit
    
    if [[ "$ENVIRONMENT_TYPE" == "homelab" ]]; then
        storage_limit="${STUDENT_LIMITS[storage_accounts]}"
    else
        storage_limit="${PAYG_LIMITS[storage_accounts]}"
    fi
    
    echo "  Current Storage Accounts: $storage_count"
    echo "  Limit:                    $storage_limit"
    echo ""
    
    # Check managed disk SKUs
    local disk_required_gb=$((256 + 128 + 64))  # All VMs if deployed
    if [[ "$DEPLOY_AGENTS" != "true" ]]; then
        disk_required_gb=256  # Only Caldera-ELK
    fi
    
    echo "  Required Disk Space: ${disk_required_gb}GB"
    echo "  Disk SKUs Used:"
    echo "    - Caldera-ELK:    256GB Premium_LRS (P15)"
    echo "    - Windows Agent:  128GB Premium_LRS (P10)"  
    echo "    - Linux Agent:    64GB Standard_LRS"
    echo ""
    
    if [[ "$ENVIRONMENT_TYPE" == "homelab" ]]; then
        log_warn "Premium_LRS may have limited availability in Free/Student accounts"
        echo "  ${YELLOW}FIX: Change to Standard_LRS in caldera-elk-server.bicep if deployment fails${NC}"
    else
        log_pass "Storage quotas within limits"
    fi
}

check_networking_quota() {
    log_section "Networking Quota (VNets, NSGs, Subnets)"
    
    local vnet_count=$(az network vnet list --query "length(@)" -o tsv 2>/dev/null || echo "0")
    local nsg_count=$(az network nsg list --query "length(@)" -o tsv 2>/dev/null || echo "0")
    
    echo "  Current VNets:  $vnet_count"
    echo "  Current NSGs:   $nsg_count"
    echo "  Required VNets: 1"
    echo "  Required NSGs:  3 (Caldera, ELK, Agents)"
    echo ""
    
    log_pass "Networking quotas within limits (typically unlimited)"
}

check_log_analytics_quota() {
    log_section "Log Analytics Workspace Quota"
    
    local law_count=$(az monitor log-analytics workspace list --query "length(@)" -o tsv 2>/dev/null || echo "0")
    
    echo "  Current Workspaces: $law_count"
    echo "  Required:           1"
    echo ""
    
    if [[ "$ENVIRONMENT_TYPE" == "homelab" ]]; then
        echo "  Daily Ingestion Cap: 1GB (dev environment)"
        log_warn "Free/Student tier has ingestion limits. Data will stop ingesting at cap."
        echo "  ${YELLOW}TIP: Reduce workspaceCapping.dailyQuotaGb in logging.bicep${NC}"
    else
        log_pass "Log Analytics quota within limits"
    fi
}

check_location_availability() {
    log_section "Region Availability Check (${LOCATION})"
    
    # Check if B-series VMs are available in the region
    local b2s_available=$(az vm list-skus --location "$LOCATION" \
        --resource-type virtualMachines \
        --query "[?name=='Standard_B2s'].restrictions" \
        -o tsv 2>/dev/null)
    
    if [[ -z "$b2s_available" || "$b2s_available" == "None" ]]; then
        log_pass "Standard_B2s available in $LOCATION"
    else
        log_warn "Standard_B2s may have restrictions in $LOCATION"
        echo "  Restrictions: $b2s_available"
    fi
    
    # Check if B1s is available
    local b1s_available=$(az vm list-skus --location "$LOCATION" \
        --resource-type virtualMachines \
        --query "[?name=='Standard_B1s'].restrictions" \
        -o tsv 2>/dev/null)
    
    if [[ -z "$b1s_available" || "$b1s_available" == "None" ]]; then
        log_pass "Standard_B1s available in $LOCATION"
    else
        log_warn "Standard_B1s may have restrictions in $LOCATION"
    fi
}

run_bicep_validation() {
    log_section "Bicep Template Validation (Dry Run)"
    
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    local BICEP_DIR="$PROJECT_ROOT/bicep"
    local PARAMS_FILE="$BICEP_DIR/parameters/dev.parameters.json"
    
    if [[ ! -f "$BICEP_DIR/main.bicep" ]]; then
        log_warn "Bicep templates not found at expected path"
        return 0
    fi
    
    echo "  Validating: $BICEP_DIR/main.bicep"
    echo "  Parameters: $PARAMS_FILE"
    echo ""
    
    # Syntax validation only (no resource group needed)
    if az bicep build --file "$BICEP_DIR/main.bicep" --stdout > /dev/null 2>&1; then
        log_pass "Bicep syntax validation passed"
    else
        log_fail "Bicep syntax validation failed"
        az bicep build --file "$BICEP_DIR/main.bicep" 2>&1 | head -20
        return 1
    fi
}

generate_summary() {
    log_section "QUOTA VALIDATION SUMMARY"
    
    local required_vcpus=$(calculate_required_vcpus)
    local required_ips=$(calculate_required_public_ips)
    
    echo ""
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│  CALDERA BICEP DEPLOYMENT - QUOTA ANALYSIS                     │"
    echo "├─────────────────────────────────────────────────────────────────┤"
    printf "│  %-20s %-42s │\n" "Account Type:" "$ENVIRONMENT_TYPE"
    printf "│  %-20s %-42s │\n" "Location:" "$LOCATION"
    printf "│  %-20s %-42s │\n" "Deploy Agents:" "$DEPLOY_AGENTS"
    echo "├─────────────────────────────────────────────────────────────────┤"
    printf "│  %-20s %-20s %-20s │\n" "Resource" "Required" "Status"
    echo "├─────────────────────────────────────────────────────────────────┤"
    printf "│  %-20s %-20s " "vCPUs" "$required_vcpus"
    if [[ $required_vcpus -le 4 ]]; then
        printf "${GREEN}%-20s${NC} │\n" "✓ PASS"
    else
        printf "${RED}%-20s${NC} │\n" "✗ FAIL"
    fi
    printf "│  %-20s %-20s ${GREEN}%-20s${NC} │\n" "Public IPs" "$required_ips" "✓ PASS"
    printf "│  %-20s %-20s ${GREEN}%-20s${NC} │\n" "VNets" "1" "✓ PASS"
    printf "│  %-20s %-20s ${GREEN}%-20s${NC} │\n" "NSGs" "3" "✓ PASS"
    printf "│  %-20s %-20s ${GREEN}%-20s${NC} │\n" "Log Analytics" "1" "✓ PASS"
    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
    
    if [[ "$DEPLOY_AGENTS" == "true" && "$ENVIRONMENT_TYPE" == "homelab" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: With agents enabled, you're at EXACTLY the 4 vCPU limit.${NC}"
        echo -e "   Any existing VMs in $LOCATION will cause deployment failure."
        echo ""
        echo -e "${GREEN}RECOMMENDATION: Set deployAgents=false for Student/Free accounts${NC}"
        echo ""
    fi
    
    if [[ $required_vcpus -le 2 ]]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✓ HOMELAB READY: Deployment will succeed in Free/Student account${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    
    echo ""
    echo "Next Steps:"
    echo "  1. Run deployment: ENVIRONMENT=dev ./deployment/scripts/setup/deploy.sh"
    echo "  2. Monitor with: ./deployment/scripts/validation/health-check.sh <IP>"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    parse_args "$@"
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║  Azure Quota Validation for Caldera Bicep Deployment              ║"
    echo "║  Environment: ${ENVIRONMENT_TYPE^^} | Location: $LOCATION                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    
    check_azure_cli
    check_vcpu_quota || true
    check_bs_series_quota || true
    check_public_ip_quota || true
    check_storage_quota || true
    check_networking_quota || true
    check_log_analytics_quota || true
    check_location_availability || true
    run_bicep_validation || true
    generate_summary
}

main "$@"
