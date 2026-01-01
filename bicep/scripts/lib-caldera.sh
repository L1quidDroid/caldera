#!/bin/bash
# ============================================================================
# CALDERA Installation and Configuration Library
# ============================================================================
# Functions for installing CALDERA with proper plugin management
# ============================================================================

setup_caldera_dependencies() {
    log_info "Installing CALDERA dependencies..."
    
    apt_install \
        python3-venv python3-pip python3-dev build-essential git \
        libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libffi-dev libjpeg-turbo8 libopenjp2-7 shared-mime-info fonts-liberation
    
    log_success "Dependencies installed"
}

install_nodejs() {
    local node_version=${1:-20}
    
    log_info "Installing Node.js ${node_version}.x..."
    
    require_command curl
    curl -fsSL "https://deb.nodesource.com/setup_${node_version}.x" | bash - || true
    apt_install nodejs
    
    log_success "Node.js installed: $(node --version)"
}

clone_caldera_repository() {
    local caldera_home=$1
    local branch=${2:-master}
    
    log_info "Cloning CALDERA repository to $caldera_home..."
    
    require_command git
    
    if [ -d "$caldera_home/caldera/.git" ]; then
        log_warn "CALDERA already cloned, pulling latest..."
        cd "$caldera_home/caldera"
        git fetch origin
        git checkout "$branch"
        git pull origin "$branch"
    else
        mkdir -p "$caldera_home"
        cd "$caldera_home"
        git clone https://github.com/mitre/caldera.git --recursive --branch "$branch"
    fi
    
    cd "$caldera_home/caldera"
    log_success "CALDERA repository ready: $(git describe --tags --always 2>/dev/null || echo 'unknown version')"
}

setup_caldera_venv() {
    local caldera_home=$1
    
    log_info "Setting up Python virtual environment for CALDERA..."
    
    cd "$caldera_home/caldera"
    
    python3 -m venv caldera_venv
    # shellcheck source=/dev/null
    source caldera_venv/bin/activate
    
    pip install --upgrade pip setuptools wheel --quiet
    pip install -r requirements.txt --quiet
    deactivate
    
    log_success "Python virtual environment configured"
}

build_magma_ui() {
    local caldera_home=$1
    
    log_info "Building Magma UI..."
    
    cd "$caldera_home/caldera/plugins/magma"
    
    # Skip rebuild if already built
    if [ -f "dist/index.html" ]; then
        log_warn "Magma already built, skipping rebuild"
        return 0
    fi
    
    npm install --quiet
    
    # Build with timeout and error handling
    if ! timeout 600 npm run build; then
        error_exit "Magma build failed (timeout or error)"
    fi
    
    if [ ! -f "dist/index.html" ]; then
        error_exit "Magma build did not produce dist/index.html"
    fi
    
    log_success "Magma UI built successfully"
}

configure_caldera_yml() {
    local caldera_home=$1
    local plugins=${2:-"access atomic compass fieldmanual gameboard magma manx response sandcat stockpile training"}
    
    log_info "Configuring CALDERA (local.yml)..."
    
    cd "$caldera_home/caldera"
    
    cat > conf/local.yml << 'EOF'
host: 0.0.0.0
port: 8888
plugins:
  - access
  - atomic
  - compass
  - fieldmanual
  - gameboard
  - magma
  - manx
  - response
  - sandcat
  - stockpile
  - training
users:
  red:
    red: admin
  blue:
    blue: admin
logging:
  version: 1
  disable_existing_loggers: false
  formatters:
    simple:
      format: "[%(levelname)s] %(asctime)s - %(message)s"
  handlers:
    console:
      class: logging.StreamHandler
      level: DEBUG
      formatter: simple
  root:
    level: WARNING
    handlers: [console]
EOF
    
    log_success "CALDERA configuration created"
}

configure_caldera_systemd() {
    local caldera_home=$1
    local admin_user=$2
    
    log_info "Creating CALDERA systemd service..."
    
    cat > /etc/systemd/system/caldera.service << EOF
[Unit]
Description=CALDERA Adversary Emulation Platform
Documentation=https://caldera.mitre.org/
After=network.target elasticsearch.service
Wants=elasticsearch.service

[Service]
Type=simple
User=$admin_user
WorkingDirectory=$caldera_home/caldera
Environment="PATH=$caldera_home/caldera/caldera_venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$caldera_home/caldera/caldera_venv/bin/python $caldera_home/caldera/server.py --insecure
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=caldera

[Install]
WantedBy=multi-user.target
EOF
    
    chown -R "$admin_user:$admin_user" "$caldera_home/caldera"
    
    systemctl daemon-reload
    systemctl enable caldera
    
    log_success "CALDERA systemd service configured"
}

install_caldera_complete() {
    local caldera_home=${1:-/home/calderaadmin}
    local admin_user=${2:-$(detect_admin_user)}
    
    log_info "Starting CALDERA complete installation..."
    
    setup_caldera_dependencies
    install_nodejs 20
    clone_caldera_repository "$caldera_home" "master"
    setup_caldera_venv "$caldera_home"
    build_magma_ui "$caldera_home"
    configure_caldera_yml "$caldera_home"
    configure_caldera_systemd "$caldera_home" "$admin_user"
    
    systemctl start caldera
    
    wait_for_http "http://localhost:8888" "120"
    
    log_success "CALDERA installation complete"
}

export -f setup_caldera_dependencies install_nodejs
export -f clone_caldera_repository setup_caldera_venv build_magma_ui
export -f configure_caldera_yml configure_caldera_systemd install_caldera_complete
