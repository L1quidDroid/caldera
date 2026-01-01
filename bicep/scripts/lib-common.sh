#!/bin/bash
# ============================================================================
# Common Library Functions for Caldera Deployment
# ============================================================================
# Shared functions for logging, error handling, and system checks
# Source this file in other scripts: source "$(dirname "$0")/lib-common.sh"
# ============================================================================

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} [$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

log_success() {
    echo -e "${GREEN}[✓]${NC} [$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} [$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

log_error() {
    echo -e "${RED}[✗]${NC} [$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Assert command exists
require_command() {
    if ! command -v "$1" &> /dev/null; then
        error_exit "Required command not found: $1"
    fi
}

# Assert OS/distro
assert_ubuntu() {
    if ! grep -qi ubuntu /etc/os-release; then
        error_exit "This script requires Ubuntu. Current OS: $(cat /etc/os-release | grep PRETTY_NAME)"
    fi
}

# Retry function with exponential backoff
retry() {
    local max_attempts=5
    local timeout=1
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if "$@"; then
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            log_warn "Attempt $attempt failed. Retrying in ${timeout}s..."
            sleep "$timeout"
            timeout=$((timeout * 2))
        fi
        
        attempt=$((attempt + 1))
    done
    
    error_exit "Command failed after $max_attempts attempts: $*"
}

# Apt helper with retry and timeout
apt_install() {
    log_info "Installing packages: $*"
    retry apt-get install -y \
        -o Acquire::Retries=5 \
        -o Acquire::http::Timeout=30 \
        -o Acquire::https::Timeout=30 \
        "$@" >/dev/null 2>&1
}

# Check systemd service health
check_service() {
    local service=$1
    local timeout=${2:-60}
    local elapsed=0
    
    log_info "Waiting for $service to be active (max ${timeout}s)..."
    
    while [ $elapsed -lt $timeout ]; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service is active"
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    error_exit "$service failed to start within ${timeout}s"
}

# Wait for TCP port
wait_for_port() {
    local host=$1
    local port=$2
    local timeout=${3:-60}
    local elapsed=0
    
    log_info "Waiting for $host:$port (max ${timeout}s)..."
    
    while [ $elapsed -lt $timeout ]; do
        if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
            log_success "Port $port is open on $host"
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    error_exit "Port $port on $host did not open within ${timeout}s"
}

# Wait for HTTP endpoint with retry
wait_for_http() {
    local url=$1
    local timeout=${2:-60}
    local elapsed=0
    
    log_info "Waiting for HTTP endpoint: $url (max ${timeout}s)..."
    
    while [ $elapsed -lt $timeout ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "HTTP endpoint is responding: $url"
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    error_exit "HTTP endpoint not responding within ${timeout}s: $url"
}

# Detect admin user
detect_admin_user() {
    # Prefer UID 1000 (standard first user), fallback to first /home entry
    local user
    user=$(getent passwd 1000 2>/dev/null | cut -d: -f1)
    
    if [ -z "$user" ]; then
        user=$(ls /home 2>/dev/null | head -n1)
    fi
    
    echo "${user:-calderaadmin}"
}

# Safely write file with validation
safe_write_file() {
    local dest=$1
    local content=$2
    local backup="${dest}.bak"
    
    # Backup existing file
    if [ -f "$dest" ]; then
        cp "$dest" "$backup"
        log_info "Backed up $dest to $backup"
    fi
    
    # Write new file
    echo "$content" > "$dest"
    
    # Validate file is not empty
    if [ ! -s "$dest" ]; then
        if [ -f "$backup" ]; then
            cp "$backup" "$dest"
        fi
        error_exit "Failed to write file: $dest (file is empty)"
    fi
}

# Check disk space
check_disk_space() {
    local required_gb=${1:-10}
    local available_gb
    
    available_gb=$(df / | awk 'NR==2 {print $4 / 1024 / 1024}' | cut -d. -f1)
    
    if [ "$available_gb" -lt "$required_gb" ]; then
        error_exit "Insufficient disk space. Required: ${required_gb}GB, Available: ${available_gb}GB"
    fi
    
    log_success "Disk space check passed (${available_gb}GB available)"
}

# Check memory
check_memory() {
    local required_mb=${1:-2048}
    local available_mb
    
    available_mb=$(free -m | awk 'NR==2 {print $7}')
    
    if [ "$available_mb" -lt "$required_mb" ]; then
        log_warn "Low available memory. Required: ${required_mb}MB, Available: ${available_mb}MB"
    else
        log_success "Memory check passed (${available_mb}MB available)"
    fi
}

# Export commonly used variables
export -f log_info log_success log_warn log_error error_exit
export -f require_command assert_ubuntu retry apt_install
export -f check_service wait_for_port wait_for_http detect_admin_user
export -f safe_write_file check_disk_space check_memory
