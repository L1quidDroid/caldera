#!/bin/bash
# CALDERA Global Orchestration Setup Checker
# Validates all dependencies and configuration before first run

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

echo -e "${BLUE}🔍 CALDERA Setup Validation${NC}"
echo "======================================"

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        ERRORS=$((ERRORS + 1))
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. Python Version Check
echo ""
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_status 0 "Python $PYTHON_VERSION (>= 3.10 required)"
    else
        print_status 1 "Python $PYTHON_VERSION (< 3.10, upgrade required)"
        print_info "Download: https://www.python.org/downloads/"
    fi
else
    print_status 1 "Python 3 not found"
    print_info "Install Python 3.10+: https://www.python.org/downloads/"
fi

# 2. Virtual Environment Check
echo ""
echo "2️⃣  Checking Virtual Environment..."
if [ -d "venv" ] || [ -d ".venv" ] || [ -d ".calderavenv" ]; then
    print_status 0 "Virtual environment found"
    if [ -n "$VIRTUAL_ENV" ]; then
        print_status 0 "Virtual environment activated: $VIRTUAL_ENV"
    else
        print_warning "Virtual environment not activated"
        print_info "Activate with: source venv/bin/activate"
    fi
else
    print_warning "No virtual environment found"
    print_info "Create one: python3 -m venv venv"
    print_info "Then activate: source venv/bin/activate"
fi

# 3. Core Dependencies
echo ""
echo "3️⃣  Checking Core Dependencies..."
REQUIRED_PACKAGES=("aiohttp" "jinja2" "yaml" "cryptography" "marshmallow")
MISSING_CORE=0

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        print_status 0 "$pkg installed"
    else
        print_status 1 "$pkg missing"
        MISSING_CORE=$((MISSING_CORE + 1))
    fi
done

if [ $MISSING_CORE -gt 0 ]; then
    print_info "Install core dependencies: pip install -r requirements.txt"
fi

# 4. Orchestrator Dependencies
echo ""
echo "4️⃣  Checking Orchestrator Dependencies..."
ORCHESTRATOR_PACKAGES=("matplotlib" "numpy" "weasyprint")
MISSING_ORCH=0

for pkg in "${ORCHESTRATOR_PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        print_status 0 "$pkg installed"
    else
        print_warning "$pkg missing (orchestrator features limited)"
        MISSING_ORCH=$((MISSING_ORCH + 1))
    fi
done

if [ $MISSING_ORCH -gt 0 ]; then
    print_info "Already in requirements.txt: pip install -r requirements.txt"
fi

# 5. Optional Plugin Dependencies
echo ""
echo "5️⃣  Checking Optional Plugin Dependencies..."
OPTIONAL_PACKAGES=("reportlab:debrief" "svglib:debrief")

for pkg_info in "${OPTIONAL_PACKAGES[@]}"; do
    pkg=$(echo $pkg_info | cut -d':' -f1)
    plugin=$(echo $pkg_info | cut -d':' -f2)
    
    if python3 -c "import $pkg" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} $pkg installed (for $plugin plugin)"
    else
        echo -e "  ${YELLOW}⚠️${NC}  $pkg missing (for $plugin plugin)"
        print_info "Optional: pip install -r requirements-optional.txt"
    fi
done

# 6. File Structure
echo ""
echo "6️⃣  Checking File Structure..."
REQUIRED_FILES=("server.py" "conf/default.yml" "requirements.txt" "requirements-optional.txt")

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "$file exists"
    else
        print_status 1 "$file missing"
    fi
done

# Check orchestrator structure
ORCHESTRATOR_DIRS=("orchestrator/cli" "orchestrator/agents" "orchestrator/reporting")
MISSING_DIRS=0

for dir in "${ORCHESTRATOR_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_status 0 "$dir exists"
    else
        print_warning "$dir missing (orchestrator features unavailable)"
        MISSING_DIRS=$((MISSING_DIRS + 1))
    fi
done

# 7. Port Availability
echo ""
echo "7️⃣  Checking Port Availability..."
if command -v nc &> /dev/null; then
    if nc -z localhost 8888 2>/dev/null; then
        print_warning "Port 8888 already in use (server may be running)"
        print_info "Check with: lsof -ti:8888"
    else
        print_status 0 "Port 8888 available"
    fi
elif command -v lsof &> /dev/null; then
    if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 8888 already in use"
        print_info "Kill process: lsof -ti:8888 | xargs kill -9"
    else
        print_status 0 "Port 8888 available"
    fi
else
    print_warning "netcat/lsof not found, skipping port check"
fi

# 8. GoLang (optional for agent compilation)
echo ""
echo "8️⃣  Checking Optional: GoLang..."
if command -v go &> /dev/null; then
    GO_VERSION=$(go version | cut -d' ' -f3)
    GO_MAJOR=$(echo $GO_VERSION | sed 's/go//' | cut -d'.' -f1)
    GO_MINOR=$(echo $GO_VERSION | sed 's/go//' | cut -d'.' -f2)
    
    if [ "$GO_MAJOR" -ge 1 ] && [ "$GO_MINOR" -ge 19 ]; then
        print_status 0 "GoLang $GO_VERSION (>= 1.19 recommended)"
    else
        print_warning "GoLang $GO_VERSION (< 1.19, upgrade recommended)"
    fi
else
    print_warning "GoLang not found (agent compilation unavailable)"
    print_info "Install: https://go.dev/doc/install"
fi

# 9. Git Submodules (plugins)
echo ""
echo "9️⃣  Checking Git Submodules..."
if [ -d ".git" ]; then
    SUBMODULE_COUNT=$(git submodule status 2>/dev/null | wc -l | tr -d ' ')
    if [ "$SUBMODULE_COUNT" -gt 0 ]; then
        UNINITIALIZED=$(git submodule status 2>/dev/null | grep -c '^-' || true)
        if [ "$UNINITIALIZED" -eq 0 ]; then
            print_status 0 "All $SUBMODULE_COUNT submodules initialized"
        else
            print_warning "$UNINITIALIZED/$SUBMODULE_COUNT submodules not initialized"
            print_info "Initialize: git submodule update --init --recursive"
        fi
    else
        print_info "No git submodules found"
    fi
else
    print_warning "Not a git repository"
fi

# 10. Configuration Files
echo ""
echo "🔟  Checking Configuration..."
if [ -f "conf/local.yml" ]; then
    print_status 0 "Local config found: conf/local.yml"
else
    print_warning "No local.yml (will use default.yml)"
    print_info "Create custom config: cp conf/default.yml conf/local.yml"
fi

if [ -f "conf/default.yml" ]; then
    if grep -q "REPLACE_WITH_RANDOM_VALUE" conf/default.yml 2>/dev/null; then
        print_warning "Default encryption keys detected in conf/default.yml"
        print_info "⚠️  Change crypt_salt and encryption_key for production!"
    fi
    
    if grep -q "api_key_red: ADMIN123" conf/default.yml 2>/dev/null; then
        print_warning "Default API keys detected (ADMIN123)"
        print_info "⚠️  Change api_key_red and api_key_blue for production!"
    fi
fi

# 11. Python Module Import Test
echo ""
echo "1️⃣1️⃣  Testing Python Module Imports..."
if python3 -c "from app.service.app_svc import AppService; from app.objects.c_operation import Operation" 2>/dev/null; then
    print_status 0 "Core modules import successfully"
else
    print_status 1 "Core module import failed"
    print_info "Check dependencies: python scripts/check_dependencies.py"
fi

# 12. Dependency Checker Script
echo ""
echo "1️⃣2️⃣  Testing Dependency Checker..."
if [ -f "scripts/check_dependencies.py" ]; then
    print_status 0 "Dependency checker found"
    if [ -x "scripts/check_dependencies.py" ]; then
        print_status 0 "Dependency checker is executable"
    else
        print_warning "Dependency checker not executable"
        print_info "Fix: chmod +x scripts/check_dependencies.py"
    fi
else
    print_warning "Dependency checker not found (scripts/check_dependencies.py)"
fi

# 13. Data Directories
echo ""
echo "1️⃣3️⃣  Checking Data Directories..."
DATA_DIRS=("data" "data/abilities" "data/adversaries" "data/campaigns")

for dir in "${DATA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_status 0 "$dir exists"
    else
        print_warning "$dir missing (will be created on first run)"
    fi
done

# 14. Logs Directory
echo ""
echo "1️⃣4️⃣  Checking Logs Directory..."
if [ -d "logs" ]; then
    print_status 0 "logs directory exists"
else
    print_warning "logs directory missing (will be created on first run)"
fi

# Final Summary
echo ""
echo "======================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Setup validation passed!${NC}"
    echo ""
    echo "🚀 Ready to start CALDERA:"
    echo "   python server.py --insecure"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Review conf/default.yml configuration"
    echo "   2. Change default API keys and encryption keys"
    echo "   3. Run dependency checker: python scripts/check_dependencies.py"
    echo "   4. Start server and visit: http://localhost:8888"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Setup validation passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Server should start, but some features may be limited:"
    echo ""
    for warning in $(seq 1 $WARNINGS); do
        echo "  • Review warnings above"
    done
    echo ""
    echo "🚀 You can still start CALDERA:"
    echo "   python server.py --insecure"
    echo ""
    echo "💡 To resolve warnings:"
    echo "   • Install optional dependencies: pip install -r requirements-optional.txt"
    echo "   • Review configuration in conf/default.yml"
    echo "   • See docs/TROUBLESHOOTING.md for help"
    exit 0
else
    echo -e "${RED}❌ Setup validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "❗ Critical issues must be fixed before starting:"
    echo ""
    echo "Common fixes:"
    echo "  1. Install Python 3.10+: https://www.python.org/downloads/"
    echo "  2. Create virtual environment: python3 -m venv venv"
    echo "  3. Activate environment: source venv/bin/activate"
    echo "  4. Install dependencies: pip install -r requirements.txt"
    echo "  5. Run dependency check: python scripts/check_dependencies.py"
    echo ""
    echo "📚 For detailed help, see:"
    echo "   • docs/TROUBLESHOOTING.md"
    echo "   • GETTING_STARTED.md"
    echo "   • README.md"
    exit 1
fi
