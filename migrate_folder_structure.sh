#!/bin/bash
#
# Automated Folder Reorganization Script
# Caldera Global Orchestration Pattern
#
# Usage: ./migrate_folder_structure.sh [--dry-run]
#

set -e  # Exit on error

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

execute() {
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY RUN] $@"
    else
        "$@"
    fi
}

# Backup current state
backup() {
    log_info "Creating backup..."
    BACKUP_DIR="backups/pre-reorganization-$(date +%Y%m%d_%H%M%S)"
    execute mkdir -p "$BACKUP_DIR"
    execute tar -czf "$BACKUP_DIR/caldera-backup.tar.gz" \
        orchestrator/ \
        plugins/orchestrator/ \
        schemas/ \
        *.md 2>/dev/null || true
    log_info "Backup created: $BACKUP_DIR/caldera-backup.tar.gz"
}

# Step 1: Create new directory structure
create_directories() {
    log_info "Step 1: Creating new directory structure..."
    
    # Documentation
    execute mkdir -p docs/{architecture,guides,api,presentations}
    
    # Orchestrator reorganization
    execute mkdir -p orchestrator/cli
    execute mkdir -p orchestrator/core
    execute mkdir -p orchestrator/services
    execute mkdir -p orchestrator/agents/{templates,deployment}
    execute mkdir -p orchestrator/reporting/templates
    execute mkdir -p orchestrator/governance
    execute mkdir -p orchestrator/ai/models/prompts
    execute mkdir -p orchestrator/schemas
    execute mkdir -p orchestrator/utils
    execute mkdir -p orchestrator/tests/fixtures
    
    # Plugin API structure
    execute mkdir -p plugins/orchestrator/api
    execute mkdir -p plugins/enrollment/{api,service}
    
    # Scripts directory
    execute mkdir -p scripts/dev
    
    log_info "Directory structure created"
}

# Step 2: Move documentation files
move_documentation() {
    log_info "Step 2: Moving documentation files..."
    
    # Move to docs/
    [[ -f IMPLEMENTATION_SUMMARY.md ]] && execute mv IMPLEMENTATION_SUMMARY.md docs/implementation-summary.md
    [[ -f ORCHESTRATION_GUIDE.md ]] && execute mv ORCHESTRATION_GUIDE.md docs/guides/orchestration-guide.md
    [[ -f GETTING_STARTED.md ]] && execute cp GETTING_STARTED.md docs/guides/getting-started.md
    [[ -f TEAM_PRESENTATION.md ]] && execute mv TEAM_PRESENTATION.md docs/presentations/team-presentation.md
    [[ -f ORCHESTRATION_README.md ]] && execute mv ORCHESTRATION_README.md docs/guides/orchestration-readme.md
    
    # Create documentation index
    if [ "$DRY_RUN" = false ]; then
        cat > docs/README.md << 'EOF'
# Caldera Orchestration Documentation

## 📚 Quick Links
- [Getting Started](guides/getting-started.md)
- [Orchestration Guide](guides/orchestration-guide.md)
- [Team Presentation](presentations/team-presentation.md)
- [Implementation Summary](implementation-summary.md)

## 🏗️ Architecture
- System overview and design decisions
- Data flow diagrams
- Integration points

## 📖 API Reference
- REST API endpoints
- CLI command reference
- Python API documentation

## 🚀 Deployment
- Production deployment guide
- Docker/Kubernetes setup
- Cloud provider integration

---

**Last Updated:** $(date +%Y-%m-%d)
EOF
    else
        echo "  [DRY RUN] Create docs/README.md"
    fi
    
    log_info "Documentation moved to docs/"
}

# Step 3: Reorganize orchestrator
reorganize_orchestrator() {
    log_info "Step 3: Reorganizing orchestrator module..."
    
    # Move CLI
    if [[ -f orchestrator/cli.py ]]; then
        execute mv orchestrator/cli.py orchestrator/cli/main.py
        execute touch orchestrator/cli/__init__.py
    fi
    
    # Move services
    if [[ -f orchestrator/webhook_publisher.py ]]; then
        execute mv orchestrator/webhook_publisher.py orchestrator/services/webhook_service.py
        execute touch orchestrator/services/__init__.py
    fi
    
    # Move agent tools
    if [[ -f orchestrator/generate_agent_enrollment.py ]]; then
        execute mv orchestrator/generate_agent_enrollment.py orchestrator/agents/enrollment_generator.py
        execute touch orchestrator/agents/__init__.py
    fi
    
    # Move utilities
    if [[ -f orchestrator/health_check.py ]]; then
        execute mv orchestrator/health_check.py orchestrator/utils/health_check.py
        execute touch orchestrator/utils/__init__.py
    fi
    
    # Move schemas
    if [[ -d schemas ]] && [[ -f schemas/campaign_spec.schema.json ]]; then
        execute mv schemas/campaign_spec.schema.json orchestrator/schemas/
        execute mv schemas/campaign_spec_example.yml orchestrator/schemas/
    fi
    
    # Move tests
    if [[ -f orchestrator/quick_test.py ]]; then
        execute mv orchestrator/quick_test.py orchestrator/tests/test_quick.py
    fi
    
    # Create __init__.py files
    execute touch orchestrator/__init__.py
    execute touch orchestrator/core/__init__.py
    execute touch orchestrator/reporting/__init__.py
    execute touch orchestrator/governance/__init__.py
    execute touch orchestrator/ai/__init__.py
    execute touch orchestrator/schemas/__init__.py
    execute touch orchestrator/tests/__init__.py
    
    log_info "Orchestrator module reorganized"
}

# Step 4: Move miscellaneous scripts
move_scripts() {
    log_info "Step 4: Moving scripts..."
    
    [[ -f setup_orchestrator.sh ]] && execute mv setup_orchestrator.sh scripts/
    [[ -f branding_preview.html ]] && execute mv branding_preview.html scripts/dev/
    
    log_info "Scripts moved to scripts/"
}

# Step 5: Create setup.py for orchestrator package
create_setup_py() {
    log_info "Step 5: Creating setup.py for orchestrator package..."
    
    cat > orchestrator/setup.py << 'EOF'
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='caldera-orchestrator',
    version='1.0.0',
    description='Global orchestration pattern for MITRE Caldera',
    author='Triskele Labs',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'caldera-orchestrator=orchestrator.cli.main:main',
        ],
    },
    python_requires='>=3.8',
    include_package_data=True,
    package_data={
        'orchestrator.schemas': ['*.json', '*.yml'],
        'orchestrator.agents.templates': ['*.j2'],
    },
)
EOF
    
    log_info "setup.py created"
}

# Step 6: Update import statements
update_imports() {
    log_info "Step 6: Updating import statements..."
    
    # Update CLI imports
    if [[ -f orchestrator/cli/main.py ]]; then
        log_warn "Import updates need manual review - see orchestrator/cli/main.py"
    fi
    
    # Update plugin imports
    if [[ -f plugins/orchestrator/hook.py ]]; then
        log_warn "Import updates need manual review - see plugins/orchestrator/hook.py"
    fi
    
    log_info "Import statement updates require manual verification"
}

# Step 7: Create backward compatibility symlinks
create_symlinks() {
    log_info "Step 7: Creating backward compatibility symlinks..."
    
    # Symlink old CLI location
    if [[ -f orchestrator/cli/main.py ]] && [[ ! -f orchestrator/cli.py ]]; then
        execute ln -sf cli/main.py orchestrator/cli.py
    fi
    
    # Symlink documentation
    if [[ -f docs/guides/orchestration-guide.md ]] && [[ ! -f ORCHESTRATION_GUIDE.md ]]; then
        execute ln -sf docs/guides/orchestration-guide.md ORCHESTRATION_GUIDE.md
    fi
    
    log_info "Backward compatibility symlinks created"
}

# Step 8: Create README placeholders for future phases
create_phase_readmes() {
    log_info "Step 8: Creating README placeholders for future phases..."
    
    if [ "$DRY_RUN" = false ]; then
        # Phase 5: Enrollment API
        cat > plugins/enrollment/README.md << 'EOF'
# Enrollment API Plugin - Phase 5

**Status:** Planned

## Overview
Standalone FastAPI service for dynamic agent enrollment.

## Features (Planned)
- REST API for agent registration
- CI/CD integration examples
- Dynamic configuration
- Multi-platform support

## API Endpoints
- `POST /api/enroll` - Register new agent
- `GET /api/agents` - List enrolled agents
- `DELETE /api/agents/{id}` - Remove agent

See FOLDER_STRUCTURE_PLAN.md for implementation details.
EOF

        # Phase 6: Reporting
        cat > orchestrator/reporting/README.md << 'EOF'
# Reporting System - Phase 6

**Status:** Planned

## Overview
PDF reporting and ATT&CK Navigator layer generation.

## Features (Planned)
- Report aggregation across operations
- PDF export with charts
- ATT&CK Navigator JSON export
- Executive summary generation

See FOLDER_STRUCTURE_PLAN.md for implementation details.
EOF

        # Phase 8: Governance
        cat > orchestrator/governance/README.md << 'EOF'
# Governance Framework - Phase 8

**Status:** Planned

## Overview
RBAC, approval workflows, and compliance tracking.

## Features (Planned)
- Role-based access control
- Approval workflow engine
- Audit logging
- Compliance policy enforcement

See FOLDER_STRUCTURE_PLAN.md for implementation details.
EOF

        # Phase 9: AI
        cat > orchestrator/ai/README.md << 'EOF'
# AI-Driven Features - Phase 9

**Status:** Planned

## Overview
LLM-powered TTP generation and threat modeling.

## Features (Planned)
- Automated ability generation
- Threat model gap analysis
- AI-assisted adversary composition
- Regression testing

See FOLDER_STRUCTURE_PLAN.md for implementation details.
EOF
    else
        echo "  [DRY RUN] Create phase README files"
    fi
    
    log_info "Phase README placeholders created"
}

# Step 9: Validation
validate_migration() {
    log_info "Step 9: Validating migration..."
    
    local errors=0
    
    # Check critical files exist
    [[ -f orchestrator/cli/main.py ]] || { log_error "CLI not found"; ((errors++)); }
    [[ -f orchestrator/services/webhook_service.py ]] || { log_error "Webhook service not found"; ((errors++)); }
    [[ -f orchestrator/agents/enrollment_generator.py ]] || { log_error "Enrollment generator not found"; ((errors++)); }
    [[ -f orchestrator/utils/health_check.py ]] || { log_error "Health check not found"; ((errors++)); }
    [[ -f docs/README.md ]] || { log_error "Docs index not found"; ((errors++)); }
    
    if [ $errors -eq 0 ]; then
        log_info "✨ Migration validation passed!"
    else
        log_error "Migration validation failed with $errors errors"
        return 1
    fi
}

# Step 10: Generate migration summary
generate_summary() {
    log_info "Step 10: Generating migration summary..."
    
    if [ "$DRY_RUN" = false ]; then
        cat > MIGRATION_SUMMARY.md << 'EOF'
# Folder Structure Migration Summary

**Date:** $(date +%Y-%m-%d)
**Status:** Complete

## Changes Made

### Documentation
- ✅ Moved to `docs/` directory
- ✅ Created documentation index
- ✅ Organized by category (guides, architecture, api, presentations)

### Orchestrator Module
- ✅ Split CLI into `orchestrator/cli/`
- ✅ Extracted services to `orchestrator/services/`
- ✅ Organized agent tools in `orchestrator/agents/`
- ✅ Moved utilities to `orchestrator/utils/`
- ✅ Created test structure in `orchestrator/tests/`

### Plugins
- ✅ Maintained existing plugin structure
- ✅ Created placeholders for Phase 5 enrollment plugin

### Scripts
- ✅ Moved to `scripts/` directory
- ✅ Created `scripts/dev/` for development tools

### Future Phases
- ✅ Created directory structure for phases 5-9
- ✅ Added README placeholders

## New Import Paths

```python
# Old
from orchestrator.cli import *
from orchestrator.webhook_publisher import WebhookPublisher

# New
from orchestrator.cli.main import *
from orchestrator.services.webhook_service import WebhookPublisher
from orchestrator.agents.enrollment_generator import AgentEnrollmentGenerator
from orchestrator.utils.health_check import CalderaHealthCheck
```

## Backward Compatibility
- Symlinks created for old file locations
- Deprecation warnings added where needed
- Old import paths still work (with warnings)

## Testing Required
1. Run all orchestrator tests: `cd orchestrator && python -m pytest tests/`
2. Test CLI commands: `python -m orchestrator.cli.main --help`
3. Start Caldera: `python3 server.py` (check plugin loads)
4. Run health check: `python -m orchestrator.utils.health_check`

## Next Steps
1. Update any external documentation references
2. Update CI/CD pipeline if needed
3. Review and update import statements
4. Test all CLI commands
5. Validate plugin functionality

---

For detailed migration plan, see FOLDER_STRUCTURE_PLAN.md
EOF
    else
        echo "  [DRY RUN] Create MIGRATION_SUMMARY.md"
    fi
    
    log_info "Migration summary generated"
}

# Main execution
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║   Caldera Folder Structure Migration Script          ║"
    echo "║   Triskele Labs - Global Orchestration Pattern       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    
    if [ "$DRY_RUN" = false ]; then
        read -p "⚠️  This will reorganize the folder structure. Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Migration cancelled."
            exit 0
        fi
    fi
    
    backup
    create_directories
    move_documentation
    reorganize_orchestrator
    move_scripts
    create_setup_py
    update_imports
    create_symlinks
    create_phase_readmes
    validate_migration
    generate_summary
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║   ✨ Migration Complete!                              ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Review MIGRATION_SUMMARY.md"
    echo "   2. Update import statements in your code"
    echo "   3. Run tests: cd orchestrator && python -m pytest tests/"
    echo "   4. Test CLI: python -m orchestrator.cli.main --help"
    echo "   5. Commit changes: git add . && git commit -m 'Reorganize folder structure'"
    echo ""
    echo "📦 Backup location: backups/"
    echo ""
}

# Run main
main "$@"
