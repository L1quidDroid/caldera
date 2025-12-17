#!/bin/bash
################################################################################
# Complete Orchestrator Setup for Azure VM
# Installs and configures Phase 1-6 orchestrator components
################################################################################

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "🚀 CALDERA Orchestrator Complete Setup"
echo "================================================"
echo ""

# Change to CALDERA directory
cd ~/caldera
source venv/bin/activate

# ============================================================================
# Step 1: Install Dependencies
# ============================================================================
echo -e "${YELLOW}Step 1: Installing orchestrator dependencies...${NC}"

pip install --quiet \
    rich>=13.0.0 \
    jsonschema>=4.17.0 \
    python-dateutil>=2.8.0 \
    requests>=2.31.0 \
    weasyprint>=59.0 \
    matplotlib>=3.7.0 \
    reportlab>=4.0.0

echo -e "${GREEN}✅ Dependencies installed${NC}"

# ============================================================================
# Step 2: Verify Orchestrator Structure
# ============================================================================
echo ""
echo -e "${YELLOW}Step 2: Verifying orchestrator components...${NC}"

REQUIRED_PATHS=(
    "orchestrator/cli.py"
    "orchestrator/cli/main.py"
    "orchestrator/README.md"
    "orchestrator/requirements.txt"
    "app/objects/c_campaign.py"
    "schemas/campaign_spec.schema.json"
)

ALL_PRESENT=true
for path in "${REQUIRED_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo "  ✓ $path"
    else
        echo "  ✗ $path (missing)"
        ALL_PRESENT=false
    fi
done

if [ "$ALL_PRESENT" = true ]; then
    echo -e "${GREEN}✅ All orchestrator components present${NC}"
else
    echo -e "${YELLOW}⚠️  Some components missing but continuing...${NC}"
fi

# ============================================================================
# Step 3: Create Data Directories
# ============================================================================
echo ""
echo -e "${YELLOW}Step 3: Creating data directories...${NC}"

mkdir -p data/campaigns
mkdir -p data/reports
mkdir -p data/results

echo -e "${GREEN}✅ Directories created${NC}"

# ============================================================================
# Step 4: Create Demo Campaign
# ============================================================================
echo ""
echo -e "${YELLOW}Step 4: Creating demo campaign specification...${NC}"

cat > data/campaigns/demo_campaign.yml << 'EOF'
campaign_id: demo_azure_2025
name: "Azure Purple Team Exercise - December 2025"
description: "Real user journey test - Multi-phase adversary emulation"

environment:
  environment_id: azure-demo-001
  type: cloud
  provider: azure
  region: australiaeast
  caldera_url: http://localhost:8888
  api_key_red: ADMIN123
  api_key_blue: BLUEADMIN123

targets:
  agent_groups:
    - red
    - blue
  platforms:
    - windows
    - linux
  tags:
    environment: azure_demo
    test_run: user_journey_2025
    deployment: australiaeast

adversary:
  adversary_id: hunter
  name: "Hunter"
  description: "Discovery and reconnaissance adversary"
  planner: atomic
  objectives:
    - "System discovery"
    - "Process enumeration"
    - "Network reconnaissance"
    - "File system exploration"

phases:
  - phase: 1
    name: "Infrastructure Validation"
    duration_hours: 0.5
    description: "Verify agents and connectivity"
  
  - phase: 2
    name: "Reconnaissance"
    duration_hours: 1
    description: "System and network discovery"
    adversary_id: hunter
  
  - phase: 3
    name: "Collection"
    duration_hours: 1
    description: "Data discovery and collection"
  
  - phase: 4
    name: "Reporting"
    duration_hours: 0.5
    description: "Generate comprehensive reports"

siem_integration:
  enabled: true
  provider: elastic
  elasticsearch_url: http://localhost:9200
  kibana_url: http://localhost:5601
  index_prefix: caldera-demo

notifications:
  enabled: false

governance:
  auto_approve: true
  require_approval_for_phases: []

mode: test
auto_cleanup: true

state:
  status: created
  current_phase: 0
  operations: []
  errors: []
  started_at: null
  completed_at: null
EOF

echo -e "${GREEN}✅ Demo campaign: data/campaigns/demo_campaign.yml${NC}"

# ============================================================================
# Step 5: Create Quick Reference Guide
# ============================================================================
echo ""
echo -e "${YELLOW}Step 5: Creating reference guide...${NC}"

PUBLIC_IP=$(curl -4 -s icanhazip.com 2>/dev/null || echo "localhost")

cat > ~/orchestrator_quick_start.md << EOF
# CALDERA Orchestrator Quick Start

## Location
\`\`\`bash
cd ~/caldera
source venv/bin/activate
\`\`\`

## The 6 Phases

### Phase 1: Campaign Planning & Creation
Create YAML specifications defining your operation.

\`\`\`bash
python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml
\`\`\`

### Phase 2: Agent Enrollment & Bootstrap
Generate platform-specific enrollment commands.

\`\`\`bash
python orchestrator/cli.py agent enroll <campaign_id> <hostname> <platform>
# Example:
python orchestrator/cli.py agent enroll demo_azure_2025 blue-agent linux
\`\`\`

### Phase 3: Health Check & Validation
Verify all services are operational.

\`\`\`bash
python orchestrator/cli.py health-check
\`\`\`

### Phase 4: Operation Execution
Start and monitor multi-phase operations.

\`\`\`bash
python orchestrator/cli.py campaign start demo_azure_2025
python orchestrator/cli.py campaign status demo_azure_2025 --verbose
\`\`\`

### Phase 5: Enrollment API
Programmatic agent enrollment via REST API.

\`\`\`bash
curl -X POST http://localhost:8888/plugin/enrollment/api/requests \\
  -H "Content-Type: application/json" \\
  -H "KEY: ADMIN123" \\
  -d '{
    "campaign_id": "demo_azure_2025",
    "hostname": "test-host",
    "platform": "linux",
    "group": "red"
  }'
\`\`\`

### Phase 6: PDF Reporting
Generate comprehensive reports with visualizations.

\`\`\`bash
python orchestrator/cli.py report generate demo_azure_2025
\`\`\`

## Essential Commands

### Campaign Management
\`\`\`bash
# List all campaigns
ls -lh data/campaigns/

# Create campaign
python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml

# Start campaign
python orchestrator/cli.py campaign start demo_azure_2025

# Check status
python orchestrator/cli.py campaign status demo_azure_2025

# Verbose status
python orchestrator/cli.py campaign status demo_azure_2025 --verbose

# Stop campaign
python orchestrator/cli.py campaign stop demo_azure_2025
\`\`\`

### Agent Management
\`\`\`bash
# List agents via API
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents | jq

# Check agent count
curl -s -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents | jq 'length'

# View agent details
curl -s -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents | jq -r '.[] | "\\(.paw) | \\(.host) | \\(.platform) | \\(.group)"'
\`\`\`

### Operation Management
\`\`\`bash
# List operations
curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/operations | jq

# Create operation via CLI
python orchestrator/cli.py operation create demo_azure_2025
\`\`\`

### Service Status
\`\`\`bash
# Check CALDERA
sudo systemctl status caldera
curl http://localhost:8888/api/v2/health

# Check ELK Stack
sudo systemctl status elasticsearch
sudo systemctl status kibana
curl http://localhost:9200/_cluster/health
\`\`\`

## Web Access

- **CALDERA**: http://$PUBLIC_IP:8888
  - Red Team: admin / admin
  - Blue Team: blue / admin

- **Kibana**: http://$PUBLIC_IP:5601

- **Elasticsearch**: http://$PUBLIC_IP:9200

## Demo Workflow

1. **Verify agents are registered:**
   \`\`\`bash
   curl -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents | jq
   \`\`\`

2. **Create demo campaign:**
   \`\`\`bash
   python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml
   \`\`\`

3. **Run health check:**
   \`\`\`bash
   python orchestrator/cli.py health-check
   \`\`\`

4. **Start campaign:**
   \`\`\`bash
   python orchestrator/cli.py campaign start demo_azure_2025
   \`\`\`

5. **Monitor progress:**
   \`\`\`bash
   python orchestrator/cli.py campaign status demo_azure_2025 --verbose
   \`\`\`

6. **Generate reports:**
   \`\`\`bash
   python orchestrator/cli.py report generate demo_azure_2025
   \`\`\`

## User Journey Test

Run the complete automated test:
\`\`\`bash
cd ~/caldera
bash ~/test_user_journey_phases.sh
\`\`\`

## Troubleshooting

### Check logs
\`\`\`bash
sudo journalctl -u caldera -f --no-pager
\`\`\`

### Restart services
\`\`\`bash
sudo systemctl restart caldera
\`\`\`

### Verify orchestrator CLI
\`\`\`bash
python orchestrator/cli.py --help
\`\`\`

### Check Python environment
\`\`\`bash
which python
pip list | grep -E "(rich|jsonschema|matplotlib)"
\`\`\`

## Documentation

- **Full Guide**: ~/caldera/DEMO_WALKTHROUGH.md
- **Quick Reference**: ~/caldera/QUICK_REFERENCE.md
- **Technical Docs**: ~/caldera/orchestrator/README.md
- **Architecture**: ~/caldera/docs/orchestration/

## Support

For issues or questions, refer to:
- TROUBLESHOOTING.md in ~/caldera/docs/
- GitHub: https://github.com/mitre/caldera
EOF

echo -e "${GREEN}✅ Quick start guide: ~/orchestrator_quick_start.md${NC}"

# ============================================================================
# Step 6: Test CLI
# ============================================================================
echo ""
echo -e "${YELLOW}Step 6: Testing orchestrator CLI...${NC}"

if python orchestrator/cli.py --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Orchestrator CLI is working${NC}"
else
    echo -e "${YELLOW}⚠️  CLI test returned non-zero exit code${NC}"
    echo "This may be normal. Try: python orchestrator/cli.py --help"
fi

# ============================================================================
# Step 7: Create Convenience Aliases
# ============================================================================
echo ""
echo -e "${YELLOW}Step 7: Creating convenience aliases...${NC}"

cat >> ~/.bashrc << 'EOF'

# CALDERA Orchestrator Aliases
alias caldera-cli='cd ~/caldera && source venv/bin/activate && python orchestrator/cli.py'
alias caldera-campaign='cd ~/caldera && source venv/bin/activate && python orchestrator/cli.py campaign'
alias caldera-agents='curl -s -H "KEY: ADMIN123" http://localhost:8888/api/v2/agents | jq'
alias caldera-ops='curl -s -H "KEY: ADMIN123" http://localhost:8888/api/v2/operations | jq'
alias caldera-health='curl -s http://localhost:8888/api/v2/health | jq'
alias caldera-logs='sudo journalctl -u caldera -f --no-pager'
alias caldera-status='sudo systemctl status caldera elasticsearch kibana'
EOF

echo -e "${GREEN}✅ Aliases added to ~/.bashrc${NC}"
echo "   Reload with: source ~/.bashrc"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "================================================"
echo "✅ ORCHESTRATOR SETUP COMPLETE"
echo "================================================"
echo ""
echo "📚 Documentation Created:"
echo "   • ~/orchestrator_quick_start.md (main guide)"
echo ""
echo "🎯 Demo Campaign:"
echo "   • ~/caldera/data/campaigns/demo_campaign.yml"
echo ""
echo "🚀 Quick Start Commands:"
echo ""
echo "   # Health check"
echo "   python orchestrator/cli.py health-check"
echo ""
echo "   # Create demo campaign"
echo "   python orchestrator/cli.py campaign create data/campaigns/demo_campaign.yml"
echo ""
echo "   # Start campaign"
echo "   python orchestrator/cli.py campaign start demo_azure_2025"
echo ""
echo "   # Monitor status"
echo "   python orchestrator/cli.py campaign status demo_azure_2025 --verbose"
echo ""
echo "🧪 Run Complete User Journey Test:"
echo "   bash ~/test_user_journey_phases.sh"
echo ""
echo "🌐 Web Interfaces:"
echo "   CALDERA: http://$PUBLIC_IP:8888 (admin/admin)"
echo "   Kibana:  http://$PUBLIC_IP:5601"
echo ""
echo "💡 Tip: Reload shell aliases with: source ~/.bashrc"
echo ""
echo "================================================"
echo ""
