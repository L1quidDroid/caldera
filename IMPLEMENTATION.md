# CALDERA Deployment Scripts - Complete Reference

## Quick Navigation

### 🚀 For Operators (Deployment)
- **[DEPLOYMENT-README.md](DEPLOYMENT-README.md)** - Start here! Complete deployment guide
- **[deployment/scripts/setup/deploy.sh](deployment/scripts/setup/deploy.sh)** - Main orchestrator
- **[deployment/scripts/validation/pre-deploy-check.sh](deployment/scripts/validation/pre-deploy-check.sh)** - Pre-flight checks
- **[deployment/scripts/validation/health-check.sh](deployment/scripts/validation/health-check.sh)** - Post-deployment verification

### 🏗️ For Architects (Architecture)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical design document
- **[bicep/main.bicep](bicep/main.bicep)** - Main orchestration template
- **[bicep/modules/](bicep/modules/)** - Network, logging, VM modules

### 👨‍💻 For Developers (Implementation)
- **[bicep/scripts/](bicep/scripts/)** - Installation scripts and libraries
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Development guide (this file)

---

## Script Organization

### Installation Scripts (Entry Points)

#### 1. **install-caldera-elk.sh** (5.7 KB)
**Purpose**: Main server installation (CALDERA + ELK Stack)
```bash
# Called by: Azure CustomScript Extension
# Sources: lib-common.sh, lib-elasticsearch.sh, lib-caldera.sh, lib-elk.sh
# Runtime: ~7 minutes
# Output: /var/log/caldera-elk-setup.log

# Example direct execution (for testing):
source bicep/scripts/lib-common.sh
source bicep/scripts/lib-elasticsearch.sh
source bicep/scripts/lib-caldera.sh
source bicep/scripts/lib-elk.sh
./bicep/scripts/install-caldera-elk.sh calderaadmin
```

#### 2. **install-linux-agent.sh** (7.0 KB)
**Purpose**: Linux agent installation (Sandcat + Filebeat)
```bash
# Called by: Azure CustomScript Extension
# Sources: lib-common.sh
# Runtime: ~2 minutes
# Output: /var/log/caldera-agent-setup.log

# Signature:
./install-linux-agent.sh <CALDERA_IP> [PORT] [GROUP] [AGENT_NAME]

# Example:
./install-linux-agent.sh 10.0.1.4 8888 blue agent-01
```

#### 3. **install-windows-agent.ps1** (9.0 KB)
**Purpose**: Windows agent installation (Sandcat + Winlogbeat)
```powershell
# Called by: Azure CustomScript Extension (CustomScriptExtension for Windows)
# Runtime: ~5 minutes
# Output: Transcript to C:\AzureData\caldera-agent-setup.log

# Signature:
powershell -ExecutionPolicy Bypass -File .\install-windows-agent.ps1 `
    -CalderaServerIp <IP> -CalderaServerPort <PORT> `
    -AgentGroup <GROUP> -ELKServerIp <IP>

# Example:
powershell -ExecutionPolicy Bypass -File .\install-windows-agent.ps1 `
    -CalderaServerIp "10.0.1.4" -AgentGroup "red"
```

---

### Library Functions (Reusable Components)

#### **lib-common.sh** (5.6 KB)
Shared utilities used by all bash scripts.

**Logging Functions:**
```bash
log_info "Message"          # Standard info log
log_success "Message"       # Success indicator (✓)
log_warn "Message"          # Warning indicator (⚠)
log_error "Message"         # Error indicator (✗)
error_exit "Message"        # Log error and exit
```

**Validation Functions:**
```bash
assert_ubuntu               # Check OS is Ubuntu
require_command <cmd>       # Check tool exists
check_disk_space <GB>       # Verify disk space
check_memory <MB>           # Verify available memory
```

**Network & Service Functions:**
```bash
wait_for_port <host> <port> [timeout]      # TCP connectivity
wait_for_http <url> [timeout]               # HTTP endpoint polling
check_service <service> [timeout]           # Systemd service status
```

**Utility Functions:**
```bash
retry <command>             # Execute with exponential backoff (5 attempts)
apt_install <packages>      # Apt with timeout and retry
detect_admin_user           # Find primary non-root user
safe_write_file <path> <content>  # Write with backup
```

**Usage:**
```bash
#!/bin/bash
source "$(dirname "$0")/lib-common.sh"

check_disk_space 50
log_info "Starting installation..."
wait_for_port localhost 9200 120
```

---

#### **lib-elasticsearch.sh** (3.6 KB)
Elasticsearch-specific installation and configuration.

**Functions:**
```bash
setup_elasticsearch_repository()             # Add Elastic GPG + repo
install_elasticsearch()                      # Apt install
configure_elasticsearch_kernel()             # Tune vm.max_map_count
configure_elasticsearch_heap()               # Set -Xms/-Xmx
configure_elasticsearch_yml()                # Generate config
install_elasticsearch_complete()             # Full pipeline
```

**Key Features:**
- Idempotent configuration (removes stale config files)
- Memory-aware heap sizing (256MB for B2s)
- Kernel parameter tuning for production
- Health check integration
- Proper error handling on startup failures

**Usage:**
```bash
source lib-common.sh
source lib-elasticsearch.sh

install_elasticsearch_complete "256m"   # Install with 256MB heap
# Returns: 0 if successful, 1 if failed
```

---

#### **lib-caldera.sh** (5.4 KB)
CALDERA-specific installation and configuration.

**Functions:**
```bash
setup_caldera_dependencies()             # Install Python, Node, build tools
install_nodejs()                         # Install Node.js from NodeSource
clone_caldera_repository()               # Git clone with submodules
setup_caldera_venv()                     # Python venv + pip install
build_magma_ui()                         # Compile Magma frontend
configure_caldera_yml()                  # Generate local.yml
configure_caldera_systemd()              # Create systemd service
install_caldera_complete()               # Full pipeline
```

**Key Features:**
- Idempotent Magma build (checks dist/index.html)
- Timeout protection (600s) on npm build
- Recursive git clone for submodules
- Proper systemd dependencies (After=elasticsearch)
- User/group permission management

**Usage:**
```bash
source lib-common.sh
source lib-caldera.sh

install_caldera_complete "/home/calderaadmin" "calderaadmin"
# Installs to /home/calderaadmin/caldera
```

---

#### **lib-elk.sh** (4.5 KB)
Kibana and Logstash installation and configuration.

**Functions:**
```bash
install_kibana()                         # Apt install kibana
install_logstash()                       # Apt install logstash
configure_kibana()                       # Generate kibana.yml
configure_logstash_beats_input()         # Input configuration
configure_logstash_winlogbeat()          # Windows event processing
configure_logstash_default_output()      # Elasticsearch output
configure_elk_stack()                    # Full pipeline
```

**Key Features:**
- Multi-input/output Logstash configuration
- Windows event code parsing
- Index naming: `winlogbeat-YYYY.MM.dd`
- Permission management for logstash user
- Service health checks

**Usage:**
```bash
source lib-common.sh
source lib-elk.sh

configure_elk_stack "localhost"   # Configure against localhost ES
```

---

## Deployment Orchestration

### **deploy.sh** (6.5 KB)
Main deployment orchestrator that:
1. Validates environment (tools, auth, bicep syntax)
2. Encodes deployment scripts to base64
3. Calls Azure Bicep deployment
4. Extracts and displays outputs

**Usage:**
```bash
# Deploy to dev environment
ENVIRONMENT=dev ./deployment/scripts/setup/deploy.sh

# Deploy to prod-lab with custom settings
ENVIRONMENT=prod-lab \
ADMIN_USER=sysadmin \
MANAGEMENT_CIDR="203.0.113.0/24" \
./deployment/scripts/setup/deploy.sh

# Environment variables:
ENVIRONMENT         # dev, stage, prod-lab (required)
LOCATION           # Azure region (default: australiaeast)
ADMIN_USER         # VM admin username (default: calderaadmin)
ADMIN_PASSWORD     # VM password (prompted if not set)
DEPLOY_AGENTS      # true/false (default: false)
SUBSCRIPTION_ID    # Azure subscription (uses default if not set)
```

---

### **pre-deploy-check.sh** (3.3 KB)
Pre-flight validation before deployment.

**Checks:**
- ✓ Azure CLI installed and authenticated
- ✓ Required tools (jq, etc.) available
- ✓ Bicep files exist
- ✓ Parameter files valid JSON
- ✓ Bicep syntax valid

**Usage:**
```bash
./deployment/scripts/validation/pre-deploy-check.sh [bicep_dir] [param_file]

# Examples:
./deployment/scripts/validation/pre-deploy-check.sh
./deployment/scripts/validation/pre-deploy-check.sh \
  ./caldera/bicep ./caldera/bicep/parameters/dev.parameters.json
```

---

### **health-check.sh** (4.4 KB)
Post-deployment health verification.

**Checks:**
- ✓ TCP connectivity (ports 8888, 9200, 5601, 5044)
- ✓ HTTP endpoints (CALDERA, ES, Kibana APIs)
- ✓ Service health
- ✓ Index availability

**Usage:**
```bash
./deployment/scripts/validation/health-check.sh \
  [CALDERA_IP] [CALDERA_PORT] [ES_PORT] [KIBANA_PORT] [TIMEOUT]

# Examples:
./deployment/scripts/validation/health-check.sh
./deployment/scripts/validation/health-check.sh 10.0.1.4 8888 9200 5601 10
```

---

## Code Examples

### Example 1: Manual Server Installation (Testing)

```bash
#!/bin/bash

# Source all libraries
source bicep/scripts/lib-common.sh
source bicep/scripts/lib-elasticsearch.sh
source bicep/scripts/lib-caldera.sh
source bicep/scripts/lib-elk.sh

# Setup
export CALDERA_HOME="/home/testuser"
export ADMIN_USER="testuser"

# Validate environment
check_disk_space 50
check_memory 2048
assert_ubuntu
require_command python3 git curl

# Install in phases
log_info "Phase 1: Elasticsearch..."
install_elasticsearch_complete "256m"

log_info "Phase 2: CALDERA..."
install_caldera_complete "$CALDERA_HOME" "$ADMIN_USER"

log_info "Phase 3: ELK Stack..."
configure_elk_stack "localhost"

log_success "Installation complete!"
```

### Example 2: Extending with Custom Script

```bash
#!/bin/bash
source "$(dirname "$0")/lib-common.sh"

# Reuse common functions
check_disk_space 20
log_info "Starting custom task..."

# Use retry for external API calls
retry curl -sf https://api.example.com/health > /dev/null

if [ $? -eq 0 ]; then
    log_success "API is healthy"
else
    error_exit "API is unreachable"
fi

# Use wait_for_http for service startup
wait_for_http "http://localhost:3000" 60
```

### Example 3: Agent Registration (Manual)

```bash
#!/bin/bash
source lib-common.sh

CALDERA_IP="10.0.1.4"
CALDERA_PORT="8888"

# Wait for server
wait_for_http "http://${CALDERA_IP}:${CALDERA_PORT}" 120

# Download agent
log_info "Downloading Sandcat agent..."
curl -sf "http://${CALDERA_IP}:${CALDERA_PORT}/file/download" \
    -o /tmp/sandcat
chmod +x /tmp/sandcat

# Start agent
log_info "Starting agent..."
/tmp/sandcat -server "http://${CALDERA_IP}:${CALDERA_PORT}" \
    -group blue -v &

log_success "Agent started (PID: $!)"
```

---

## Testing & Development

### Unit Testing Library Functions

```bash
#!/bin/bash
# test-lib-common.sh

source bicep/scripts/lib-common.sh

test_retry() {
    echo "Testing retry function..."
    
    # Should succeed immediately
    if retry echo "success"; then
        echo "✓ Retry with successful command"
    fi
    
    # Should fail after retries
    if ! retry false; then
        echo "✓ Retry with failing command exits with error"
    fi
}

test_wait_for_http() {
    echo "Testing wait_for_http..."
    
    # Start dummy HTTP server
    python3 -m http.server 9999 &
    HTTP_PID=$!
    
    if wait_for_http "http://localhost:9999" 10; then
        echo "✓ wait_for_http works"
    fi
    
    kill $HTTP_PID 2>/dev/null
}

test_retry
test_wait_for_http
```

### Integration Testing

```bash
#!/bin/bash
# test-integration.sh

source bicep/scripts/lib-common.sh
source bicep/scripts/lib-elasticsearch.sh

test_elasticsearch_installation() {
    echo "Testing Elasticsearch installation..."
    
    # Remove if already installed
    apt-get remove -y elasticsearch || true
    
    # Install
    if install_elasticsearch_complete "256m"; then
        echo "✓ Installation succeeded"
        
        # Verify service
        if systemctl is-active --quiet elasticsearch; then
            echo "✓ Service is running"
        fi
    else
        echo "✗ Installation failed"
        return 1
    fi
}

test_elasticsearch_installation
```

---

## Troubleshooting

### Issue: Scripts fail with "command not found"

**Solution:** Ensure library is sourced correctly
```bash
# Wrong
source lib-common.sh   # Can't find if not in PATH

# Correct
source "$(dirname "$0")/lib-common.sh"     # Uses script directory
source "${BASH_SOURCE%/*}/lib-common.sh"   # Alternative
```

### Issue: "set -e" causing early exit

**Solution:** Use proper error handling
```bash
# Wrong
if some_command; then   # Won't work with set -e inside functions
    log_info "success"
fi

# Correct
if some_command || error_exit "Command failed"; then
    log_info "success"
fi

# Or temporarily disable
set +e
some_command
set -e
```

### Issue: Bash function not available in subprocess

**Solution:** Export function with -f flag
```bash
# Make function available to subshells
export -f log_info log_error

# Or reload library in subprocess
(source lib-common.sh; log_info "In subshell")
```

---

## References

- **CALDERA**: https://caldera.mitre.org/
- **Azure Bicep**: https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/
- **Elasticsearch**: https://www.elastic.co/guide/en/elasticsearch/reference/current/
- **Bash Best Practices**: https://mywiki.wooledge.org/BashGuide

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-23 | Initial production release |
| | | - Modular library architecture |
| | | - Production-grade error handling |
| | | - Comprehensive documentation |

---

**Status**: ✅ Production Ready  
**Maintainer**: Triskele Labs  
**License**: Per parent repository
