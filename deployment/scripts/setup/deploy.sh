#!/bin/bash
# ============================================================================
# CALDERA Purple Team Lab - Main Deployment Script
# ============================================================================
# Orchestrates the complete deployment of CALDERA with ELK Stack on Azure
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BICEP_DIR="$PROJECT_ROOT/bicep"
SCRIPTS_DIR="$BICEP_DIR/scripts"
PARAMS_DIR="$BICEP_DIR/parameters"

# Environment (dev, stage, prod-lab)
ENVIRONMENT="${ENVIRONMENT:-dev}"
PARAM_FILE="${PARAMS_DIR}/${ENVIRONMENT}.parameters.json"
LOCATION="${LOCATION:-australiaeast}"

# Azure settings
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
ADMIN_USER="${ADMIN_USERNAME:-calderaadmin}"
MANAGEMENT_CIDR="${MANAGEMENT_CIDR:-0.0.0.0/0}"
DEPLOY_AGENTS="${DEPLOY_AGENTS:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

error_exit() {
    log_error "$1"
    exit 1
}

# ============================================================================
# VALIDATION
# ============================================================================

validate_environment() {
    log_info "Validating environment..."
    
    # Check required tools
    local required_tools=("az" "jq" "base64")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error_exit "Required tool not found: $tool"
        fi
    done
    
    # Check parameter file
    if [ ! -f "$PARAM_FILE" ]; then
        error_exit "Parameter file not found: $PARAM_FILE"
    fi
    
    # Validate Bicep files (skip if az bicep validate not available)
    if ! az bicep validate --file "$BICEP_DIR/main.bicep" >/dev/null 2>&1; then
        log_warn "Bicep validation unavailable, proceeding with deployment"
    fi
    
    # Check Azure authentication
    if ! az account show >/dev/null 2>&1; then
        error_exit "Not authenticated to Azure. Run: az login"
    fi
    
    log_success "Environment validation passed"
}

# ============================================================================
# SCRIPT ENCODING
# ============================================================================

encode_deployment_scripts() {
    log_info "Encoding deployment scripts for Bicep injection..."
    
    local caldera_elk_b64
    local linux_agent_b64
    local windows_agent_b64
    
    # Encode scripts
    caldera_elk_b64=$(base64 -w 0 < "$SCRIPTS_DIR/install-caldera-elk.sh")
    linux_agent_b64=$(base64 -w 0 < "$SCRIPTS_DIR/install-linux-agent.sh")
    windows_agent_b64=$(base64 -w 0 < "$SCRIPTS_DIR/install-windows-agent.ps1")
    
    # Create temporary parameters file with encoded scripts
    local temp_params
    temp_params=$(mktemp)
    
    jq --arg caldera_elk "$caldera_elk_b64" \
       --arg linux_agent "$linux_agent_b64" \
       --arg windows_agent "$windows_agent_b64" \
       '.parameters.calderaElkInstallScript.value = $caldera_elk |
        .parameters.linuxAgentInstallScript.value = $linux_agent |
        .parameters.windowsAgentInstallScript.value = $windows_agent' \
       "$PARAM_FILE" > "$temp_params"
    
    echo "$temp_params"
}

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy_infrastructure() {
    log_info "=========================================="
    log_info "Deploying CALDERA Purple Team Lab"
    log_info "=========================================="
    log_info "Environment: $ENVIRONMENT"
    log_info "Location: $LOCATION"
    log_info "Admin User: $ADMIN_USER"
    log_info "Deploy Agents: $DEPLOY_AGENTS"
    log_info "Management CIDR: $MANAGEMENT_CIDR"
    
    # Encode scripts
    local params_with_scripts
    params_with_scripts=$(encode_deployment_scripts)
    
    # Set subscription if provided
    if [ -n "$SUBSCRIPTION_ID" ]; then
        log_info "Setting subscription: $SUBSCRIPTION_ID"
        az account set --subscription "$SUBSCRIPTION_ID"
    fi
    
    # Deployment name with timestamp
    local deployment_name="caldera-$(date +%Y%m%d-%H%M%S)"
    
    log_info "Starting deployment: $deployment_name"
    log_info "This may take 10-20 minutes..."
    
    # Deploy Bicep template
    az deployment sub create \
        --name "$deployment_name" \
        --template-file "$BICEP_DIR/main.bicep" \
        --parameters "$params_with_scripts" \
        --parameters environment="$ENVIRONMENT" \
        --parameters location="$LOCATION" \
        --parameters adminUsername="$ADMIN_USER" \
        --parameters deployAgents="$DEPLOY_AGENTS" \
        --parameters managementCidr="$MANAGEMENT_CIDR" \
        --output json | tee /tmp/deployment-output.json
    
    # Cleanup
    rm -f "$params_with_scripts"
    
    log_success "Deployment completed: $deployment_name"
}

# ============================================================================
# POST-DEPLOYMENT
# ============================================================================

display_outputs() {
    log_info "=========================================="
    log_success "Deployment Outputs"
    log_info "=========================================="
    
    # Extract outputs from deployment
    if [ -f /tmp/deployment-output.json ]; then
        jq '.properties.outputs // .outputs' /tmp/deployment-output.json | jq '.'
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    validate_environment
    deploy_infrastructure
    display_outputs
    
    log_info "=========================================="
    log_success "CALDERA Purple Team Lab deployed successfully!"
    log_info "=========================================="
}

# ============================================================================
# EXECUTION
# ============================================================================

main "$@"
exit $?
