#!/usr/bin/env python3
"""
Agent Enrollment Script Generator

Generates parameterized agent deployment scripts for Windows and Linux targets.
Integrates with campaign specifications for tagging and configuration.

Usage:
    python3 generate_agent_enrollment.py --campaign=<campaign_id> --platform=<windows|linux|darwin>
    python3 generate_agent_enrollment.py --output=enrollment_script.sh
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

try:
    import yaml
    import requests
    from rich.console import Console
    from rich.syntax import Syntax
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install requests pyyaml rich")
    sys.exit(1)

console = Console()


class ScriptValidator:
    """Validates generated enrollment scripts for syntax and security issues."""
    
    @staticmethod
    def validate_powershell(script: str) -> tuple[bool, list[str]]:
        """
        Validate PowerShell script syntax and security.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check for dangerous commands
        dangerous_patterns = [
            ('Invoke-Expression', 'Use of Invoke-Expression is dangerous'),
            ('iex ', 'Use of iex alias is dangerous'),
            ('DownloadString', 'Direct DownloadString without validation'),
            ('-EncodedCommand', 'Encoded commands may hide malicious content'),
        ]
        
        for pattern, message in dangerous_patterns:
            if pattern in script:
                errors.append(f"⚠️  Security: {message}")
        
        # Check for required elements
        required_elements = [
            ('$CALDERA_SERVER', 'Missing server configuration variable'),
            ('$CALDERA_PORT', 'Missing port configuration variable'),
            ('Write-Host', 'Missing user feedback messages'),
            ('-ForegroundColor', 'Missing colored output'),
        ]
        
        for element, message in required_elements:
            if element not in script:
                errors.append(f"❌ Missing: {message}")
        
        # Check for error handling
        if 'try {' not in script or 'catch {' not in script:
            errors.append("⚠️  Missing error handling (try/catch)")
        
        # Check for admin privilege warning
        if 'Administrator' not in script and 'isAdmin' not in script:
            errors.append("⚠️  Missing administrator privilege check")
        
        # Check script starts with comment header
        if not script.strip().startswith('#'):
            errors.append("❌ Script should start with comment header")
        
        # Basic syntax checks
        if script.count('{') != script.count('}'):
            errors.append("❌ Unbalanced curly braces")
        
        if script.count('(') != script.count(')'):
            errors.append("❌ Unbalanced parentheses")
        
        # Check for hardcoded secrets (except examples)
        if 'password=' in script.lower() or 'apikey=' in script.lower():
            if 'example' not in script.lower():
                errors.append("⚠️  Security: Possible hardcoded credentials")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_bash(script: str) -> tuple[bool, list[str]]:
        """
        Validate Bash script syntax and security.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check for dangerous commands
        dangerous_patterns = [
            ('eval ', 'Use of eval is dangerous'),
            ('curl | bash', 'Piping curl to bash is dangerous'),
            ('wget | sh', 'Piping wget to sh is dangerous'),
            ('chmod 777', 'Overly permissive permissions'),
        ]
        
        for pattern, message in dangerous_patterns:
            if pattern in script:
                errors.append(f"⚠️  Security: {message}")
        
        # Check for shebang
        if not script.strip().startswith('#!/bin/bash') and not script.strip().startswith('#!/usr/bin/env bash'):
            errors.append("❌ Missing shebang (#!/bin/bash)")
        
        # Check for required elements
        required_elements = [
            ('CALDERA_SERVER=', 'Missing server configuration variable'),
            ('CALDERA_PORT=', 'Missing port configuration variable'),
            ('echo ', 'Missing user feedback messages'),
            ('set -e', 'Missing error exit mode (set -e)'),
        ]
        
        for element, message in required_elements:
            if element not in script:
                errors.append(f"❌ Missing: {message}")
        
        # Check for error handling
        if 'if [ ' not in script and 'if [[ ' not in script:
            errors.append("⚠️  Missing conditional error checks")
        
        # Check for privilege warning
        if 'EUID' not in script and 'root' not in script.lower():
            errors.append("⚠️  Missing root privilege check")
        
        # Check script has comment header
        lines = script.strip().split('\n')
        if len(lines) < 2 or not lines[1].strip().startswith('#'):
            errors.append("❌ Script should have comment header after shebang")
        
        # Basic syntax checks
        single_quote_count = script.count("'")
        double_quote_count = script.count('"')
        
        if single_quote_count % 2 != 0:
            errors.append("❌ Unbalanced single quotes")
        
        if double_quote_count % 2 != 0:
            errors.append("❌ Unbalanced double quotes")
        
        # Check for proper variable quoting
        if '$CALDERA_SERVER' in script and '"$CALDERA_SERVER"' not in script and '"${CALDERA_SERVER}"' not in script:
            errors.append("⚠️  Variable should be quoted: $CALDERA_SERVER")
        
        # Check for hardcoded secrets
        if 'password=' in script.lower() or 'api_key=' in script.lower():
            if 'example' not in script.lower():
                errors.append("⚠️  Security: Possible hardcoded credentials")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_yaml(content: str) -> tuple[bool, list[str]]:
        """
        Validate YAML syntax.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"❌ YAML syntax error: {e}")
            return False, errors
        
        # Check for required docker-compose elements
        if 'version:' not in content:
            errors.append("❌ Missing version field in docker-compose")
        
        if 'services:' not in content:
            errors.append("❌ Missing services field in docker-compose")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_terraform(content: str) -> tuple[bool, list[str]]:
        """
        Validate Terraform configuration.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check for required Terraform elements
        required_elements = [
            ('resource "', 'Missing resource definitions'),
            ('variable "', 'Missing variable definitions'),
            ('output "', 'Missing output definitions'),
        ]
        
        for element, message in required_elements:
            if element not in content:
                errors.append(f"⚠️  {message}")
        
        # Check for security groups
        if 'aws_security_group' not in content:
            errors.append("⚠️  Missing AWS security group definition")
        
        # Check for hardcoded credentials
        if 'access_key' in content.lower() or 'secret_key' in content.lower():
            errors.append("⚠️  Security: Avoid hardcoding AWS credentials")
        
        # Basic syntax checks
        if content.count('{') != content.count('}'):
            errors.append("❌ Unbalanced curly braces")
        
        if content.count('[') != content.count(']'):
            errors.append("❌ Unbalanced square brackets")
        
        return len(errors) == 0, errors


class AgentEnrollmentGenerator:
    """Generate agent enrollment scripts for campaigns."""

    def __init__(
        self,
        caldera_url: str,
        api_key: str,
        campaign_spec: Optional[Dict] = None
    ):
        self.caldera_url = caldera_url.rstrip('/')
        self.api_key = api_key
        self.campaign_spec = campaign_spec or {}

    def get_deployment_commands(self) -> Dict[str, str]:
        """Fetch deployment commands from Caldera API."""
        url = f"{self.caldera_url}/api/v2/agents/deployment_commands"
        headers = {'KEY': self.api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            return {
                cmd['platform']: cmd['command']
                for cmd in response.json()
            }
        except Exception as e:
            console.print(f"[red]Failed to fetch deployment commands: {e}[/red]")
            return {}

    def generate_windows_script(
        self,
        base_command: str,
        group: str = "red",
        contact: str = "HTTP",
        sleep: int = 60,
        tags: Optional[Dict] = None
    ) -> str:
        """Generate Windows PowerShell enrollment script."""
        
        # Parse base command and customize
        server_url = self.caldera_url
        parsed = urlparse(server_url)
        server_host = parsed.hostname or "localhost"
        server_port = parsed.port or 8888
        
        campaign_id = self.campaign_spec.get('campaign_id', 'unknown')
        test_run_id = (self.campaign_spec.get('targets', {})
                      .get('tags', {})
                      .get('test_run_id', campaign_id[:8]))
        
        script = f'''# Caldera Agent Enrollment Script - Windows
# Campaign: {self.campaign_spec.get('name', 'Unknown')}
# Campaign ID: {campaign_id}
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Configuration
$CALDERA_SERVER = "{server_host}"
$CALDERA_PORT = {server_port}
$CALDERA_PROTOCOL = "{parsed.scheme or 'http'}"
$GROUP = "{group}"
$CONTACT = "{contact}"
$SLEEP_INTERVAL = {sleep}
$TEST_RUN_ID = "{test_run_id}"

# Campaign tags
$CAMPAIGN_TAGS = @{{
'''
        
        if tags:
            for key, value in tags.items():
                script += f'    "{key}" = "{value}"\n'
        
        script += f'''}}

Write-Host "[+] Caldera Agent Enrollment" -ForegroundColor Green
Write-Host "[*] Campaign: {self.campaign_spec.get('name', 'Unknown')}" -ForegroundColor Cyan
Write-Host "[*] Server: ${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}" -ForegroundColor Cyan
Write-Host "[*] Group: ${{GROUP}}" -ForegroundColor Cyan
Write-Host "[*] Test Run ID: ${{TEST_RUN_ID}}" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {{
    Write-Host "[!] Warning: Not running as Administrator. Some abilities may fail." -ForegroundColor Yellow
}}

# Download and execute Sandcat agent
$agentUrl = "${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}/file/download"
$agentPath = "$env:TEMP\\sandcat.exe"

Write-Host "[*] Downloading agent from ${{agentUrl}}..." -ForegroundColor Cyan

try {{
    # Download agent
    $params = @{{
        name = "sandcat.exe"
        platform = "windows"
    }}
    
    Invoke-WebRequest -Uri $agentUrl -Method Post -Body ($params | ConvertTo-Json) -ContentType "application/json" -OutFile $agentPath -UseBasicParsing
    
    Write-Host "[+] Agent downloaded successfully" -ForegroundColor Green
    
    # Execute agent with parameters
    Write-Host "[*] Starting agent..." -ForegroundColor Cyan
    
    $agentArgs = @(
        "-server", "${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}",
        "-group", $GROUP,
        "-v"
    )
    
    # Add custom facts for campaign tracking
    $env:CALDERA_CAMPAIGN_ID = "{campaign_id}"
    $env:CALDERA_TEST_RUN_ID = $TEST_RUN_ID
    
    Start-Process -FilePath $agentPath -ArgumentList $agentArgs -WindowStyle Hidden
    
    Write-Host "[+] Agent started successfully!" -ForegroundColor Green
    Write-Host "[*] Agent PID: $(Get-Process | Where-Object {{$_.Path -eq $agentPath}} | Select-Object -ExpandProperty Id)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[*] Agent will beacon every ${{SLEEP_INTERVAL}} seconds" -ForegroundColor Cyan
    Write-Host "[*] Monitor in Caldera UI: ${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}" -ForegroundColor Cyan
    
}} catch {{
    Write-Host "[!] Error: $_" -ForegroundColor Red
    exit 1
}}

Write-Host ""
Write-Host "[+] Enrollment complete!" -ForegroundColor Green
'''
        
        return script

    def generate_linux_script(
        self,
        base_command: str,
        group: str = "red",
        contact: str = "HTTP",
        sleep: int = 60,
        tags: Optional[Dict] = None
    ) -> str:
        """Generate Linux/macOS bash enrollment script."""
        
        server_url = self.caldera_url
        parsed = urlparse(server_url)
        server_host = parsed.hostname or "localhost"
        server_port = parsed.port or 8888
        
        campaign_id = self.campaign_spec.get('campaign_id', 'unknown')
        test_run_id = (self.campaign_spec.get('targets', {})
                      .get('tags', {})
                      .get('test_run_id', campaign_id[:8]))
        
        script = f'''#!/bin/bash
# Caldera Agent Enrollment Script - Linux/macOS
# Campaign: {self.campaign_spec.get('name', 'Unknown')}
# Campaign ID: {campaign_id}
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

set -e

# Configuration
CALDERA_SERVER="{server_host}"
CALDERA_PORT={server_port}
CALDERA_PROTOCOL="{parsed.scheme or 'http'}"
GROUP="{group}"
CONTACT="{contact}"
SLEEP_INTERVAL={sleep}
TEST_RUN_ID="{test_run_id}"

# Colors
GREEN='\\033[0;32m'
CYAN='\\033[0;36m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

echo -e "${{GREEN}}[+] Caldera Agent Enrollment${{NC}}"
echo -e "${{CYAN}}[*] Campaign: {self.campaign_spec.get('name', 'Unknown')}${{NC}}"
echo -e "${{CYAN}}[*] Server: ${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}${{NC}}"
echo -e "${{CYAN}}[*] Group: ${{GROUP}}${{NC}}"
echo -e "${{CYAN}}[*] Test Run ID: ${{TEST_RUN_ID}}${{NC}}"
echo ""

# Detect platform
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$PLATFORM" in
    linux)
        AGENT_NAME="sandcat-linux"
        ;;
    darwin)
        AGENT_NAME="sandcat-darwin"
        ;;
    *)
        echo -e "${{RED}}[!] Unsupported platform: $PLATFORM${{NC}}"
        exit 1
        ;;
esac

# Check privileges
if [ "$EUID" -ne 0 ]; then
    echo -e "${{YELLOW}}[!] Warning: Not running as root. Some abilities may fail.${{NC}}"
fi

# Download agent
AGENT_URL="${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}/file/download"
AGENT_PATH="/tmp/${{AGENT_NAME}}-${{TEST_RUN_ID}}"

echo -e "${{CYAN}}[*] Downloading agent from ${{AGENT_URL}}...${{NC}}"

curl -sk -X POST \\
    -H "Content-Type: application/json" \\
    -d '{{"name":"'$AGENT_NAME'","platform":"'$PLATFORM'"}}' \\
    "$AGENT_URL" \\
    -o "$AGENT_PATH"

if [ ! -f "$AGENT_PATH" ]; then
    echo -e "${{RED}}[!] Failed to download agent${{NC}}"
    exit 1
fi

chmod +x "$AGENT_PATH"
echo -e "${{GREEN}}[+] Agent downloaded successfully${{NC}}"

# Set campaign environment variables
export CALDERA_CAMPAIGN_ID="{campaign_id}"
export CALDERA_TEST_RUN_ID="$TEST_RUN_ID"

# Start agent
echo -e "${{CYAN}}[*] Starting agent...${{NC}}"

"$AGENT_PATH" \\
    -server "${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}" \\
    -group "$GROUP" \\
    -v &

AGENT_PID=$!

echo -e "${{GREEN}}[+] Agent started successfully!${{NC}}"
echo -e "${{CYAN}}[*] Agent PID: ${{AGENT_PID}}${{NC}}"
echo ""
echo -e "${{CYAN}}[*] Agent will beacon every ${{SLEEP_INTERVAL}} seconds${{NC}}"
echo -e "${{CYAN}}[*] Monitor in Caldera UI: ${{CALDERA_PROTOCOL}}://${{CALDERA_SERVER}}:${{CALDERA_PORT}}${{NC}}"
echo ""
echo -e "${{GREEN}}[+] Enrollment complete!${{NC}}"

# Save PID for cleanup
echo $AGENT_PID > "/tmp/caldera-agent-${{TEST_RUN_ID}}.pid"
echo -e "${{CYAN}}[*] PID saved to /tmp/caldera-agent-${{TEST_RUN_ID}}.pid${{NC}}"
'''
        
        return script

    def generate_docker_compose(self, include_red: bool = True, include_blue: bool = True) -> str:
        """Generate docker-compose.yml for infrastructure setup."""
        
        campaign_id = self.campaign_spec.get('campaign_id', 'unknown')
        
        compose = f'''# Docker Compose for Caldera Campaign Infrastructure
# Campaign: {self.campaign_spec.get('name', 'Unknown')}
# Campaign ID: {campaign_id}

version: '3.8'

services:
  caldera:
    image: mitre/caldera:latest
    container_name: caldera-server
    ports:
      - "8888:8888"
      - "7010:7010"  # SSH contact
      - "7011:7011"  # TCP contact
      - "7012:7012"  # UDP contact
    environment:
      - CALDERA_URL=http://localhost:8888
      - CAMPAIGN_ID={campaign_id}
    volumes:
      - ./data:/usr/src/app/data
      - ./plugins:/usr/src/app/plugins
      - ./conf:/usr/src/app/conf
    networks:
      - caldera_net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
        
        if include_red:
            compose += '''
  red-vm-01:
    image: ubuntu:22.04
    container_name: red-vm-01
    command: sleep infinity
    networks:
      - caldera_net
    environment:
      - CALDERA_CAMPAIGN_ID={campaign_id}
    restart: unless-stopped
'''.format(campaign_id=campaign_id)
        
        if include_blue:
            compose += '''
  blue-vm-01:
    image: ubuntu:22.04
    container_name: blue-vm-01
    command: sleep infinity
    networks:
      - caldera_net
    environment:
      - CALDERA_CAMPAIGN_ID={campaign_id}
    restart: unless-stopped
'''.format(campaign_id=campaign_id)
        
        compose += '''
networks:
  caldera_net:
    driver: bridge
    name: caldera_campaign_network

volumes:
  caldera_data:
    name: caldera_campaign_data
'''
        
        return compose

    def generate_terraform_aws(self) -> str:
        """Generate Terraform configuration for AWS infrastructure."""
        
        campaign_id = self.campaign_spec.get('campaign_id', 'unknown')
        campaign_name = self.campaign_spec.get('name', 'Unknown')
        
        terraform = f'''# Terraform AWS Infrastructure for Caldera Campaign
# Campaign: {campaign_name}
# Campaign ID: {campaign_id}

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

variable "aws_region" {{
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}}

variable "campaign_id" {{
  description = "Campaign identifier"
  type        = string
  default     = "{campaign_id}"
}}

variable "key_name" {{
  description = "SSH key pair name"
  type        = string
}}

# VPC for campaign
resource "aws_vpc" "caldera_vpc" {{
  cidr_block           = "10.50.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name        = "caldera-campaign-vpc"
    CampaignID  = var.campaign_id
    Environment = "purple-team"
  }}
}}

# Subnet
resource "aws_subnet" "caldera_subnet" {{
  vpc_id                  = aws_vpc.caldera_vpc.id
  cidr_block              = "10.50.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${{var.aws_region}}a"

  tags = {{
    Name       = "caldera-campaign-subnet"
    CampaignID = var.campaign_id
  }}
}}

# Internet Gateway
resource "aws_internet_gateway" "caldera_igw" {{
  vpc_id = aws_vpc.caldera_vpc.id

  tags = {{
    Name       = "caldera-campaign-igw"
    CampaignID = var.campaign_id
  }}
}}

# Route Table
resource "aws_route_table" "caldera_rt" {{
  vpc_id = aws_vpc.caldera_vpc.id

  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.caldera_igw.id
  }}

  tags = {{
    Name       = "caldera-campaign-rt"
    CampaignID = var.campaign_id
  }}
}}

resource "aws_route_table_association" "caldera_rta" {{
  subnet_id      = aws_subnet.caldera_subnet.id
  route_table_id = aws_route_table.caldera_rt.id
}}

# Security Group
resource "aws_security_group" "caldera_sg" {{
  name        = "caldera-campaign-sg"
  description = "Security group for Caldera campaign"
  vpc_id      = aws_vpc.caldera_vpc.id

  # Caldera web UI
  ingress {{
    from_port   = 8888
    to_port     = 8888
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  # SSH
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  # Egress
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  tags = {{
    Name       = "caldera-campaign-sg"
    CampaignID = var.campaign_id
  }}
}}

# Caldera Server EC2 Instance
resource "aws_instance" "caldera_server" {{
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"
  key_name      = var.key_name
  subnet_id     = aws_subnet.caldera_subnet.id
  vpc_security_group_ids = [aws_security_group.caldera_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose git python3-pip
              systemctl start docker
              systemctl enable docker
              
              # Clone Caldera
              git clone https://github.com/mitre/caldera.git /opt/caldera
              cd /opt/caldera
              
              # Install dependencies
              pip3 install -r requirements.txt
              
              # Start Caldera
              python3 server.py --insecure &
              
              echo "CAMPAIGN_ID={campaign_id}" > /etc/environment
              EOF

  tags = {{
    Name       = "caldera-server"
    CampaignID = var.campaign_id
    Role       = "c2-server"
  }}
}}

# Red Team VM
resource "aws_instance" "red_vm" {{
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.small"
  key_name      = var.key_name
  subnet_id     = aws_subnet.caldera_subnet.id
  vpc_security_group_ids = [aws_security_group.caldera_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              echo "CALDERA_CAMPAIGN_ID={campaign_id}" >> /etc/environment
              echo "CALDERA_ROLE=red" >> /etc/environment
              EOF

  tags = {{
    Name       = "red-vm-01"
    CampaignID = var.campaign_id
    Role       = "red-team"
  }}
}}

# Blue Team VM
resource "aws_instance" "blue_vm" {{
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.small"
  key_name      = var.key_name
  subnet_id     = aws_subnet.caldera_subnet.id
  vpc_security_group_ids = [aws_security_group.caldera_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              echo "CALDERA_CAMPAIGN_ID={campaign_id}" >> /etc/environment
              echo "CALDERA_ROLE=blue" >> /etc/environment
              EOF

  tags = {{
    Name       = "blue-vm-01"
    CampaignID = var.campaign_id
    Role       = "blue-team"
  }}
}}

# Latest Ubuntu AMI
data "aws_ami" "ubuntu" {{
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {{
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }}
}}

# Outputs
output "caldera_server_public_ip" {{
  value       = aws_instance.caldera_server.public_ip
  description = "Public IP of Caldera server"
}}

output "caldera_server_private_ip" {{
  value       = aws_instance.caldera_server.private_ip
  description = "Private IP of Caldera server"
}}

output "caldera_url" {{
  value       = "http://${{aws_instance.caldera_server.public_ip}}:8888"
  description = "Caldera web UI URL"
}}

output "red_vm_private_ip" {{
  value       = aws_instance.red_vm.private_ip
  description = "Private IP of red team VM"
}}

output "blue_vm_private_ip" {{
  value       = aws_instance.blue_vm.private_ip
  description = "Private IP of blue team VM"
}}
'''
        
        return terraform


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate agent enrollment scripts for Caldera campaigns'
    )
    
    parser.add_argument(
        '--campaign',
        help='Campaign ID (will load from data/campaigns/)'
    )
    parser.add_argument(
        '--campaign-spec',
        help='Path to campaign specification YAML file'
    )
    parser.add_argument(
        '--platform',
        choices=['windows', 'linux', 'darwin', 'docker', 'terraform-aws'],
        default='linux',
        help='Target platform'
    )
    parser.add_argument(
        '--caldera-url',
        default='http://localhost:8888',
        help='Caldera server URL'
    )
    parser.add_argument(
        '--api-key',
        default='ADMIN123',
        help='Caldera API key'
    )
    parser.add_argument(
        '--group',
        default='red',
        help='Agent group name'
    )
    parser.add_argument(
        '--output',
        help='Output file path'
    )
    
    args = parser.parse_args()
    
    # Load campaign spec
    campaign_spec = None
    if args.campaign:
        spec_path = Path(f"data/campaigns/{args.campaign}.yml")
        if spec_path.exists():
            with open(spec_path, 'r') as f:
                campaign_spec = yaml.safe_load(f)
    elif args.campaign_spec:
        with open(args.campaign_spec, 'r') as f:
            campaign_spec = yaml.safe_load(f)
    
    # Create generator
    generator = AgentEnrollmentGenerator(
        caldera_url=args.caldera_url,
        api_key=args.api_key,
        campaign_spec=campaign_spec
    )
    
    # Generate script based on platform
    validator = ScriptValidator()
    
    if args.platform == 'windows':
        script = generator.generate_windows_script(
            base_command="",
            group=args.group,
            tags=campaign_spec.get('targets', {}).get('tags') if campaign_spec else None
        )
        extension = "ps1"
        syntax = "powershell"
        is_valid, validation_errors = validator.validate_powershell(script)
    elif args.platform in ['linux', 'darwin']:
        script = generator.generate_linux_script(
            base_command="",
            group=args.group,
            tags=campaign_spec.get('targets', {}).get('tags') if campaign_spec else None
        )
        extension = "sh"
        syntax = "bash"
        is_valid, validation_errors = validator.validate_bash(script)
    elif args.platform == 'docker':
        script = generator.generate_docker_compose()
        extension = "yml"
        syntax = "yaml"
        is_valid, validation_errors = validator.validate_yaml(script)
    elif args.platform == 'terraform-aws':
        script = generator.generate_terraform_aws()
        extension = "tf"
        syntax = "terraform"
        is_valid, validation_errors = validator.validate_terraform(script)
    
    # Display validation results
    console.print(f"\n[bold cyan]🔍 Script Validation Results:[/bold cyan]\n")
    if is_valid:
        console.print("[green]✅ All validation checks passed![/green]")
    else:
        console.print(f"[yellow]⚠️  Found {len(validation_errors)} validation issue(s):[/yellow]")
        for error in validation_errors:
            console.print(f"  {error}")
        console.print()
    
    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(script)
        console.print(f"[green]✅ Script saved to: {output_path}[/green]")
    else:
        console.print(f"\n[bold cyan]Generated {args.platform.title()} Enrollment Script:[/bold cyan]\n")
        console.print(Syntax(script, syntax, theme="monokai", line_numbers=True))
    
    console.print()


if __name__ == '__main__':
    main()
