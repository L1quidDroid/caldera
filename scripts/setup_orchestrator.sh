#!/bin/bash
# Setup script for Caldera Orchestrator
# Creates virtual environment and installs dependencies

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Caldera Orchestrator - Setup                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install Caldera requirements
if [ -f "requirements.txt" ]; then
    echo "Installing Caldera requirements..."
    pip install -r requirements.txt --quiet
    echo "✓ Caldera requirements installed"
fi

# Install orchestrator requirements
if [ -f "orchestrator/requirements.txt" ]; then
    echo "Installing orchestrator requirements..."
    pip install -r orchestrator/requirements.txt --quiet
    echo "✓ Orchestrator requirements installed"
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x orchestrator/*.py
echo "✓ Scripts are executable"

# Create directories
echo "Creating directories..."
mkdir -p data/campaigns
mkdir -p data/reports
echo "✓ Directories created"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Setup Complete!                                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start Caldera (in a separate terminal):"
echo "   python3 server.py --insecure"
echo ""
echo "3. Run health check:"
echo "   python3 orchestrator/health_check.py"
echo ""
echo "4. Run quick test:"
echo "   python3 orchestrator/quick_test.py"
echo ""
echo "5. Create your first campaign:"
echo "   python3 orchestrator/cli.py campaign create schemas/campaign_spec_example.yml"
echo ""
