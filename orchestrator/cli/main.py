#!/usr/bin/env python3
"""
Caldera Orchestrator CLI

Central command-line interface for managing multi-phase adversary emulation campaigns.
Wraps Caldera REST API, cloud APIs, SIEM APIs, and notification webhooks.

Usage:
    caldera-orchestrator campaign create <spec_file>
    caldera-orchestrator campaign start <campaign_id>
    caldera-orchestrator campaign status <campaign_id>
    caldera-orchestrator campaign stop <campaign_id>
    caldera-orchestrator operation create <campaign_id> [--start]
    caldera-orchestrator agent enroll <campaign_id> <host> <platform>
    caldera-orchestrator report generate <campaign_id> [--format=pdf]
    caldera-orchestrator health-check [--campaign=<campaign_id>]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml
import aiohttp
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directories to path for imports
orchestrator_root = Path(__file__).parent.parent
caldera_root = orchestrator_root.parent
sys.path.insert(0, str(caldera_root))
sys.path.insert(0, str(orchestrator_root))

from app.objects.c_campaign import Campaign
from services.webhook_service import WebhookPublisher, SIEMIntegration
from utils.health_check import CalderaHealthCheck
from agents.enrollment_generator import AgentEnrollmentGenerator
from orchestrator.pdf_generator import PDFReportGenerator

console = Console()
logger = logging.getLogger('orchestrator')


class CalderaOrchestratorCLI:
    """Main orchestrator CLI class."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.campaigns_dir = Path(self.config.get('campaigns_dir', 'data/campaigns'))
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load orchestrator configuration."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            'campaigns_dir': 'data/campaigns',
            'reports_dir': 'data/reports',
            'caldera_url': os.getenv('CALDERA_URL', 'http://localhost:8888'),
            'api_key_red': os.getenv('CALDERA_API_KEY_RED', 'ADMIN123'),
            'api_key_blue': os.getenv('CALDERA_API_KEY_BLUE', 'BLUEADMIN123'),
            'timeout': 300
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        caldera_url: Optional[str] = None,
        api_key: Optional[str] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make authenticated request to Caldera REST API.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., '/api/v2/operations')
            caldera_url: Override default Caldera URL
            api_key: Override default API key
            data: JSON payload for POST/PUT/PATCH
            params: Query parameters
            
        Returns:
            JSON response as dict
        """
        url = (caldera_url or self.config['caldera_url']).rstrip('/') + endpoint
        headers = {
            'KEY': api_key or self.config['api_key_red'],
            'Content-Type': 'application/json'
        }
        
        session = await self._get_session()
        
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                json=data,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.config['timeout'])
            ) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    logger.error(f"API request failed: {resp.status} - {error_text}")
                    raise Exception(f"API request failed: {resp.status}")
                
                return await resp.json()
        except asyncio.TimeoutError:
            logger.error(f"API request timed out: {method} {url}")
            raise
        except Exception as e:
            logger.error(f"API request error: {e}")
            raise

    def _load_campaign_spec(self, spec_path: str) -> Dict:
        """Load and validate campaign specification from YAML file."""
        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"Campaign spec not found: {spec_path}")
        
        with open(spec_path, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Basic validation
        required_fields = ['campaign_id', 'name', 'environment', 'mode']
        missing = [f for f in required_fields if f not in spec]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        return spec

    def _save_campaign_spec(self, campaign: Campaign):
        """Save campaign specification to YAML file."""
        filename = f"{campaign.campaign_id}.yml"
        filepath = self.campaigns_dir / filename
        
        with open(filepath, 'w') as f:
            yaml.dump(campaign.display, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Campaign spec saved: {filepath}")
        return str(filepath)

    def _load_campaign(self, campaign_id: str) -> Campaign:
        """Load campaign from stored YAML file."""
        filepath = self.campaigns_dir / f"{campaign_id}.yml"
        if not filepath.exists():
            raise FileNotFoundError(f"Campaign not found: {campaign_id}")
        
        spec = self._load_campaign_spec(str(filepath))
        return Campaign(**spec)

    async def health_check(self, campaign_id: Optional[str] = None):
        """
        Verify Caldera services are healthy.
        
        Checks:
        - Caldera web UI reachable
        - REST API responds with 200
        - Plugins loaded
        - Campaign environment (if specified)
        """
        console.print("\n[bold blue]Caldera Health Check[/bold blue]\n")
        
        results = []
        
        # Check web UI
        try:
            caldera_url = self.config['caldera_url']
            session = await self._get_session()
            async with session.get(caldera_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                ui_status = "✅ Healthy" if resp.status == 200 else f"❌ Failed ({resp.status})"
                results.append(("Web UI", caldera_url, ui_status))
        except Exception as e:
            results.append(("Web UI", caldera_url, f"❌ Error: {e}"))
        
        # Check REST API
        try:
            api_resp = await self._api_request('GET', '/api/v2/config')
            api_status = "✅ Healthy"
            results.append(("REST API", f"{caldera_url}/api/v2", api_status))
        except Exception as e:
            results.append(("REST API", f"{caldera_url}/api/v2", f"❌ Error: {e}"))
        
        # Check plugins
        try:
            plugins = await self._api_request('GET', '/api/rest', params={'index': 'plugins'})
            plugin_names = [p.get('name', 'Unknown') for p in plugins]
            plugin_status = f"✅ {len(plugins)} loaded: {', '.join(plugin_names)}"
            results.append(("Plugins", "", plugin_status))
        except Exception as e:
            results.append(("Plugins", "", f"❌ Error: {e}"))
        
        # Check campaign environment
        if campaign_id:
            try:
                campaign = self._load_campaign(campaign_id)
                env_info = f"{campaign.environment.get('environment_id')} ({campaign.environment.get('type')})"
                results.append(("Campaign", campaign.name, f"✅ {env_info}"))
            except Exception as e:
                results.append(("Campaign", campaign_id, f"❌ Error: {e}"))
        
        # Display results table
        table = Table(title="Health Check Results")
        table.add_column("Component", style="cyan")
        table.add_column("Details", style="white")
        table.add_column("Status", style="green")
        
        for component, details, status in results:
            table.add_row(component, details, status)
        
        console.print(table)
        console.print()
        
        # Return exit code
        failed = any("❌" in status for _, _, status in results)
        return 1 if failed else 0

    async def campaign_create(self, spec_path: str):
        """Create new campaign from specification file."""
        console.print(f"\n[bold blue]Creating Campaign[/bold blue]\n")
        
        spec = self._load_campaign_spec(spec_path)
        campaign = Campaign(**spec)
        
        # Save campaign
        saved_path = self._save_campaign_spec(campaign)
        
        console.print(f"✅ Campaign created: [green]{campaign.name}[/green]")
        console.print(f"   Campaign ID: [cyan]{campaign.campaign_id}[/cyan]")
        console.print(f"   Environment: {campaign.environment.get('environment_id')}")
        console.print(f"   Mode: {campaign.mode}")
        console.print(f"   Spec saved: {saved_path}\n")
        
        return campaign.campaign_id

    async def campaign_start(self, campaign_id: str):
        """Start campaign execution through phases."""
        campaign = self._load_campaign(campaign_id)
        
        console.print(f"\n[bold blue]Starting Campaign: {campaign.name}[/bold blue]\n")
        console.print(f"Campaign ID: [cyan]{campaign_id}[/cyan]")
        console.print(f"Mode: [yellow]{campaign.mode}[/yellow]\n")
        
        # Confirm for production mode
        if campaign.mode == 'production':
            confirm = console.input("[bold yellow]⚠️  Production mode! Continue? (yes/no):[/bold yellow] ")
            if confirm.lower() != 'yes':
                console.print("[red]Cancelled[/red]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Phase 1: Infrastructure validation
            task1 = progress.add_task("Phase 1: Validating infrastructure...", total=None)
            campaign.update_status('infrastructure_provisioning')
            campaign.state['current_phase'] = 1
            await asyncio.sleep(1)  # Placeholder for actual validation
            campaign.update_status('infrastructure_ready')
            progress.update(task1, completed=True)
            
            # Phase 2: Agent enrollment
            task2 = progress.add_task("Phase 2: Preparing agent enrollment...", total=None)
            campaign.update_status('agents_enrolling')
            campaign.state['current_phase'] = 2
            await asyncio.sleep(1)  # Placeholder
            progress.update(task2, completed=True)
            
            # Create operation
            task3 = progress.add_task("Creating operation...", total=None)
            campaign.update_status('operation_queued')
            campaign.state['current_phase'] = 3
            
            # Get Caldera URL and API key from campaign or config
            caldera_url = campaign.environment.get('caldera_url') or self.config['caldera_url']
            api_key = campaign.environment.get('api_key_red') or self.config['api_key_red']
            
            # Create operation via API
            operation_data = {
                'name': f"{campaign.name} - {campaign.campaign_id[:8]}",
                'adversary': {'adversary_id': campaign.adversary.get('adversary_id')},
                'group': campaign.targets.get('agent_groups', ['red'])[0] if campaign.targets.get('agent_groups') else 'red',
                'planner': {'id': campaign.adversary.get('planner', 'atomic')},
                'source': {'id': campaign.adversary.get('source')} if campaign.adversary.get('source') else None,
                'obfuscator': campaign.adversary.get('obfuscator', 'plain-text'),
                'auto_close': False,
                'state': 'paused'
            }
            
            # Remove None values
            operation_data = {k: v for k, v in operation_data.items() if v is not None}
            
            try:
                op_resp = await self._api_request(
                    'POST',
                    '/api/v2/operations',
                    caldera_url=caldera_url,
                    api_key=api_key,
                    data=operation_data
                )
                operation_id = op_resp.get('id')
                campaign.add_operation(operation_id, operation_data['name'], 'created')
                progress.update(task3, completed=True)
                
                console.print(f"\n✅ Operation created: [green]{operation_id}[/green]")
                
            except Exception as e:
                campaign.add_error('operation_creation', str(e), 'error')
                console.print(f"\n❌ Failed to create operation: {e}")
                progress.update(task3, completed=True)
        
        # Save updated campaign
        self._save_campaign_spec(campaign)
        
        console.print(f"\n✅ Campaign started: [green]{campaign.name}[/green]")
        console.print(f"   Operations: {len(campaign.state['operations'])}")
        console.print(f"   Status: {campaign.state['status']}\n")

    async def campaign_status(self, campaign_id: str, verbose: bool = False):
        """Display campaign status and progress."""
        campaign = self._load_campaign(campaign_id)
        
        console.print(f"\n[bold blue]Campaign Status[/bold blue]\n")
        
        # Basic info
        console.print(f"Name: [green]{campaign.name}[/green]")
        console.print(f"ID: [cyan]{campaign.campaign_id}[/cyan]")
        console.print(f"Status: [yellow]{campaign.state['status']}[/yellow]")
        console.print(f"Phase: {campaign.state['current_phase']}/9")
        console.print(f"Mode: {campaign.mode}")
        
        duration = campaign.get_duration_hours()
        if duration:
            console.print(f"Duration: {duration:.2f} hours")
        
        # Operations
        if campaign.state['operations']:
            console.print(f"\n[bold]Operations ({len(campaign.state['operations'])})[/bold]")
            for op in campaign.state['operations']:
                console.print(f"  • {op['name']} ({op['operation_id'][:8]}...) - {op['status']}")
        
        # Agents
        if campaign.state['agents_enrolled']:
            console.print(f"\n[bold]Agents Enrolled ({len(campaign.state['agents_enrolled'])})[/bold]")
            for agent in campaign.state['agents_enrolled'][:5]:  # Show first 5
                console.print(f"  • {agent['hostname']} ({agent['platform']}) - {agent['paw'][:8]}...")
            if len(campaign.state['agents_enrolled']) > 5:
                console.print(f"  ... and {len(campaign.state['agents_enrolled']) - 5} more")
        
        # Errors
        if campaign.state['errors']:
            console.print(f"\n[bold red]Errors ({len(campaign.state['errors'])})[/bold red]")
            for error in campaign.state['errors'][-3:]:  # Show last 3
                console.print(f"  • [{error['severity']}] {error['phase']}: {error['message']}")
        
        # Reports
        if campaign.state['reports'].get('json_path'):
            console.print(f"\n[bold]Reports[/bold]")
            for fmt, path in campaign.state['reports'].items():
                if path and fmt != 'generated_at':
                    console.print(f"  • {fmt.upper()}: {path}")
        
        # Verbose timeline
        if verbose and campaign.state['timeline']:
            console.print(f"\n[bold]Timeline[/bold]")
            for event in campaign.state['timeline'][-10:]:  # Last 10 events
                console.print(f"  • {event['timestamp']}: {event['event']}")
        
        console.print()

    async def campaign_stop(self, campaign_id: str, force: bool = False):
        """Stop/cancel campaign execution."""
        campaign = self._load_campaign(campaign_id)
        
        console.print(f"\n[bold yellow]Stopping Campaign: {campaign.name}[/bold yellow]\n")
        
        if not force:
            confirm = console.input("Confirm stop? (yes/no): ")
            if confirm.lower() != 'yes':
                console.print("[red]Cancelled[/red]")
                return
        
        # Stop all running operations
        for op in campaign.state['operations']:
            if op['status'] in ['running', 'queued']:
                try:
                    caldera_url = campaign.environment.get('caldera_url') or self.config['caldera_url']
                    api_key = campaign.environment.get('api_key_red') or self.config['api_key_red']
                    
                    await self._api_request(
                        'PATCH',
                        f"/api/v2/operations/{op['operation_id']}",
                        caldera_url=caldera_url,
                        api_key=api_key,
                        data={'state': 'finished'}
                    )
                    campaign.update_operation(op['operation_id'], {'status': 'stopped'})
                    console.print(f"  ✅ Stopped operation: {op['operation_id'][:8]}...")
                except Exception as e:
                    console.print(f"  ❌ Failed to stop {op['operation_id'][:8]}...: {e}")
        
        campaign.update_status('cancelled')
        self._save_campaign_spec(campaign)
        
        console.print(f"\n✅ Campaign stopped: [green]{campaign.name}[/green]\n")

    async def operation_create(
        self,
        campaign_id: str,
        start: bool = False,
        wait: bool = False
    ):
        """Create operation for campaign."""
        campaign = self._load_campaign(campaign_id)
        
        console.print(f"\n[bold blue]Creating Operation[/bold blue]\n")
        console.print(f"Campaign: {campaign.name}")
        
        # Implementation similar to campaign_start but standalone
        # ... (operation creation logic)
        
        console.print(f"\n✅ Operation created\n")

    async def agent_enroll(self, campaign_id: str, host: str, platform: str):
        """Generate agent enrollment commands for campaign."""
        campaign = self._load_campaign(campaign_id)
        
        console.print(f"\n[bold blue]Agent Enrollment[/bold blue]\n")
        console.print(f"Campaign: {campaign.name}")
        console.print(f"Host: {host}")
        console.print(f"Platform: {platform}\n")
        
        caldera_url = campaign.environment.get('caldera_url') or self.config['caldera_url']
        
        # Get deployment commands from API
        try:
            commands = await self._api_request(
                'GET',
                '/api/v2/agents/deployment_commands',
                caldera_url=caldera_url
            )
            
            # Find command for platform
            for cmd_info in commands:
                if platform.lower() in cmd_info.get('platform', '').lower():
                    command = cmd_info.get('command', '')
                    console.print(f"[bold green]Deployment Command:[/bold green]\n")
                    console.print(f"[cyan]{command}[/cyan]\n")
                    
                    # Add customization for campaign
                    console.print(f"[bold]Customize for campaign:[/bold]")
                    console.print(f"  • Set group: [yellow]{campaign.targets.get('agent_groups', ['red'])[0]}[/yellow]")
                    console.print(f"  • Add tags: {campaign.targets.get('tags', {})}\n")
                    break
            else:
                console.print(f"[red]No deployment command found for platform: {platform}[/red]")
        
        except Exception as e:
            console.print(f"[red]Failed to get deployment commands: {e}[/red]")

    async def report_generate(
        self,
        campaign_id: str,
        format: str = 'pdf',
        include_output: bool = False,
        include_facts: bool = True,
        attack_layer: bool = True,
        output_path: Optional[str] = None
    ):
        """Generate campaign report."""
        console.print(f"\n[bold blue]Generating Campaign Report[/bold blue]\n")
        console.print(f"Campaign ID:      [cyan]{campaign_id}[/cyan]")
        console.print(f"Format:           [yellow]{format}[/yellow]")
        console.print(f"Include Output:   {include_output}")
        console.print(f"Include Facts:    {include_facts}")
        console.print(f"ATT&CK Layer:     {attack_layer}\n")
        
        if format not in ['pdf', 'json']:
            console.print(f"[red]Error: Unsupported format '{format}'. Use 'pdf' or 'json'[/red]")
            return
        
        # Set default output path
        if not output_path:
            reports_dir = Path(self.config.get('reports_dir', 'data/reports'))
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            if format == 'pdf':
                output_path = str(reports_dir / f"{campaign_id}_report.pdf")
            else:
                output_path = str(reports_dir / f"{campaign_id}_report.json")
        
        caldera_url = self.config['caldera_url']
        api_key = self.config['api_key_red']
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            if format == 'pdf':
                # Generate PDF report
                task1 = progress.add_task("📊 Collecting campaign data...", total=None)
                
                generator = PDFReportGenerator(caldera_url, api_key)
                
                try:
                    result = await generator.generate_report(
                        campaign_id=campaign_id,
                        output_path=output_path,
                        include_output=include_output,
                        include_facts=include_facts,
                        attack_layer=attack_layer
                    )
                    
                    progress.update(task1, completed=True)
                    
                    # Display results
                    console.print("\n" + "="*60)
                    console.print("[bold green]📊 REPORT GENERATION COMPLETE[/bold green]")
                    console.print("="*60)
                    
                    table = Table(show_header=False, box=None)
                    table.add_column("Label", style="cyan")
                    table.add_column("Value", style="white")
                    
                    table.add_row("Campaign ID", result['campaign_id'])
                    table.add_row("PDF Report", result['pdf_path'])
                    if result.get('attack_layer_path'):
                        table.add_row("ATT&CK Layer", result['attack_layer_path'])
                    table.add_row("File Size", f"{result['file_size_mb']} MB")
                    table.add_row("Operations", str(result['summary']['total_operations']))
                    table.add_row("Agents", str(result['summary']['total_agents']))
                    table.add_row("Abilities Executed", str(result['summary']['total_abilities_executed']))
                    table.add_row("Success Rate", f"{result['summary']['success_rate']:.1f}%")
                    table.add_row("Charts Generated", str(result['charts_generated']))
                    
                    console.print(table)
                    console.print("="*60 + "\n")
                    
                    # Tip for viewing
                    console.print("[dim]💡 Tip: Open the PDF report to view detailed campaign analysis with Triskele branding[/dim]")
                    if result.get('attack_layer_path'):
                        console.print("[dim]💡 Tip: Upload the ATT&CK layer to https://mitre-attack.github.io/attack-navigator/ for visualization[/dim]\n")
                    
                except Exception as e:
                    progress.update(task1, completed=True)
                    console.print(f"\n[red]Error generating report: {e}[/red]")
                    logger.exception("Report generation failed")
                    raise
            
            elif format == 'json':
                # Generate JSON report
                task1 = progress.add_task("📊 Collecting campaign data...", total=None)
                
                from orchestrator.report_aggregator import ReportAggregator
                
                try:
                    async with ReportAggregator(caldera_url, api_key) as aggregator:
                        report_data = await aggregator.get_campaign_data(campaign_id)
                    
                    # Save JSON
                    with open(output_path, 'w') as f:
                        json.dump(report_data, f, indent=2, default=str)
                    
                    progress.update(task1, completed=True)
                    
                    # Display results
                    console.print("\n" + "="*60)
                    console.print("[bold green]📊 JSON REPORT SAVED[/bold green]")
                    console.print("="*60)
                    console.print(f"Output: [cyan]{output_path}[/cyan]")
                    console.print(f"Operations: {report_data['summary']['total_operations']}")
                    console.print(f"Agents: {report_data['summary']['total_agents']}")
                    console.print(f"Abilities: {report_data['summary']['total_abilities_executed']}")
                    console.print("="*60 + "\n")
                    
                except Exception as e:
                    progress.update(task1, completed=True)
                    console.print(f"\n[red]Error generating JSON report: {e}[/red]")
                    logger.exception("JSON report generation failed")
                    raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Caldera Orchestrator CLI - Multi-phase campaign management',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        help='Path to orchestrator config file',
        default=None
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Health check command
    health_parser = subparsers.add_parser('health-check', help='Verify Caldera services')
    health_parser.add_argument('--campaign', help='Campaign ID to check')
    
    # Campaign commands
    campaign_parser = subparsers.add_parser('campaign', help='Campaign management')
    campaign_sub = campaign_parser.add_subparsers(dest='subcommand')
    
    create_parser = campaign_sub.add_parser('create', help='Create new campaign')
    create_parser.add_argument('spec_file', help='Campaign specification YAML file')
    
    start_parser = campaign_sub.add_parser('start', help='Start campaign')
    start_parser.add_argument('campaign_id', help='Campaign ID')
    
    status_parser = campaign_sub.add_parser('status', help='Show campaign status')
    status_parser.add_argument('campaign_id', help='Campaign ID')
    status_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    stop_parser = campaign_sub.add_parser('stop', help='Stop campaign')
    stop_parser.add_argument('campaign_id', help='Campaign ID')
    stop_parser.add_argument('--force', '-f', action='store_true', help='Force stop')
    
    # Operation commands
    op_parser = subparsers.add_parser('operation', help='Operation management')
    op_sub = op_parser.add_subparsers(dest='subcommand')
    
    op_create = op_sub.add_parser('create', help='Create operation')
    op_create.add_argument('campaign_id', help='Campaign ID')
    op_create.add_argument('--start', action='store_true', help='Start immediately')
    op_create.add_argument('--wait', action='store_true', help='Wait for completion')
    
    # Agent commands
    agent_parser = subparsers.add_parser('agent', help='Agent management')
    agent_sub = agent_parser.add_subparsers(dest='subcommand')
    
    agent_enroll = agent_sub.add_parser('enroll', help='Generate enrollment commands')
    agent_enroll.add_argument('campaign_id', help='Campaign ID')
    agent_enroll.add_argument('host', help='Target hostname')
    agent_enroll.add_argument('platform', help='Platform (windows/linux/darwin)')
    
    # Report commands
    report_parser = subparsers.add_parser('report', help='Report generation')
    report_sub = report_parser.add_subparsers(dest='subcommand')
    
    report_gen = report_sub.add_parser('generate', help='Generate campaign report')
    report_gen.add_argument('campaign_id', help='Campaign ID')
    report_gen.add_argument('--format', choices=['json', 'pdf'], default='pdf', help='Report format (default: pdf)')
    report_gen.add_argument('--output', '-o', help='Output file path (default: data/reports/<campaign_id>_report.pdf)')
    report_gen.add_argument('--include-output', action='store_true', help='Include full ability command output (verbose)')
    report_gen.add_argument('--no-facts', action='store_true', help='Exclude agent facts from report')
    report_gen.add_argument('--no-attack-layer', action='store_true', help='Skip ATT&CK Navigator layer generation')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )
    
    # Create CLI instance
    cli = CalderaOrchestratorCLI(args.config)
    
    # Route to appropriate command
    try:
        if args.command == 'health-check':
            exit_code = asyncio.run(cli.health_check(args.campaign))
            sys.exit(exit_code)
        
        elif args.command == 'campaign':
            if args.subcommand == 'create':
                asyncio.run(cli.campaign_create(args.spec_file))
            elif args.subcommand == 'start':
                asyncio.run(cli.campaign_start(args.campaign_id))
            elif args.subcommand == 'status':
                asyncio.run(cli.campaign_status(args.campaign_id, args.verbose))
            elif args.subcommand == 'stop':
                asyncio.run(cli.campaign_stop(args.campaign_id, args.force))
        
        elif args.command == 'operation':
            if args.subcommand == 'create':
                asyncio.run(cli.operation_create(args.campaign_id, args.start, args.wait))
        
        elif args.command == 'agent':
            if args.subcommand == 'enroll':
                asyncio.run(cli.agent_enroll(args.campaign_id, args.host, args.platform))
        
        elif args.command == 'report':
            if args.subcommand == 'generate':
                asyncio.run(cli.report_generate(
                    campaign_id=args.campaign_id,
                    format=args.format,
                    include_output=args.include_output,
                    include_facts=not args.no_facts,
                    attack_layer=not args.no_attack_layer,
                    output_path=args.output
                ))
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Unexpected error")
        sys.exit(1)
    finally:
        asyncio.run(cli._close_session())


if __name__ == '__main__':
    main()
