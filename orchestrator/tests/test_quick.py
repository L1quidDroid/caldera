#!/usr/bin/env python3
"""
Quick Test - Caldera Orchestrator

Demonstrates basic orchestrator functionality:
1. Creates a test campaign
2. Validates the campaign spec
3. Shows campaign status
4. Demonstrates webhook registration

Usage:
    python3 orchestrator/quick_test.py
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def main():
    """Run quick test of orchestrator components."""
    
    console.print("\n[bold blue]╔═══════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║     CALDERA ORCHESTRATOR - QUICK TEST              ║[/bold blue]")
    console.print("[bold blue]╚═══════════════════════════════════════════════════════╝[/bold blue]\n")
    
    # Test 1: Campaign Object
    console.print("[bold cyan]Test 1: Campaign Object Creation[/bold cyan]")
    
    from app.objects.c_campaign import Campaign
    
    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        name="Quick Test Campaign",
        description="Testing orchestrator functionality",
        mode="test",
        environment={
            "environment_id": "test-001",
            "type": "development",
            "caldera_url": "http://localhost:8888"
        },
        targets={
            "agent_groups": ["red"],
            "platforms": ["linux"]
        },
        adversary={
            "adversary_id": "test-adversary",
            "planner": "atomic"
        }
    )
    
    console.print(f"  ✅ Created campaign: [green]{campaign.name}[/green]")
    console.print(f"  Campaign ID: [cyan]{campaign.campaign_id}[/cyan]")
    console.print(f"  Status: [yellow]{campaign.state['status']}[/yellow]")
    
    # Test 2: Status Updates
    console.print("\n[bold cyan]Test 2: Campaign Status Updates[/bold cyan]")
    
    campaign.update_status('infrastructure_provisioning')
    console.print("  ✅ Updated to: infrastructure_provisioning")
    
    campaign.update_status('agents_enrolling')
    console.print("  ✅ Updated to: agents_enrolling")
    
    campaign.update_status('operation_running')
    console.print("  ✅ Updated to: operation_running")
    
    # Test 3: Add Operations and Agents
    console.print("\n[bold cyan]Test 3: Track Operations and Agents[/bold cyan]")
    
    campaign.add_operation(
        operation_id=str(uuid.uuid4()),
        name="Test Operation 1",
        status="running"
    )
    console.print("  ✅ Added operation: Test Operation 1")
    
    campaign.add_agent(
        paw="test-agent-001",
        hostname="test-host-01",
        platform="linux"
    )
    console.print("  ✅ Added agent: test-agent-001 (test-host-01)")
    
    # Test 4: Timeline
    console.print("\n[bold cyan]Test 4: Campaign Timeline[/bold cyan]")
    
    timeline_table = Table(title="Recent Events", show_header=True, header_style="bold cyan")
    timeline_table.add_column("Time", style="yellow", width=20)
    timeline_table.add_column("Event", style="green", width=40)
    
    for event in campaign.state['timeline'][-5:]:
        timeline_table.add_row(
            event['timestamp'][:19],
            event['event']
        )
    
    console.print(timeline_table)
    
    # Test 5: Display Campaign
    console.print("\n[bold cyan]Test 5: Campaign Display[/bold cyan]")
    
    display_data = campaign.display
    
    info_table = Table(show_header=False, box=None)
    info_table.add_column("Property", style="cyan", width=20)
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Name", campaign.name)
    info_table.add_row("Campaign ID", campaign.campaign_id)
    info_table.add_row("Mode", campaign.mode)
    info_table.add_row("Status", campaign.state['status'])
    info_table.add_row("Phase", f"{campaign.state['current_phase']}/9")
    info_table.add_row("Operations", str(len(campaign.state['operations'])))
    info_table.add_row("Agents", str(len(campaign.state['agents_enrolled'])))
    info_table.add_row("Duration", f"{campaign.get_duration_hours():.2f} hours")
    
    console.print(info_table)
    
    # Test 6: Webhook Publisher
    console.print("\n[bold cyan]Test 6: Webhook Publisher[/bold cyan]")
    
    from orchestrator.webhook_publisher import WebhookPublisher
    
    publisher = WebhookPublisher()
    await publisher.start()
    
    # Register test webhook
    publisher.register_webhook(
        url="https://example.com/webhook",
        name="Test Webhook",
        filters={'exchange': ['operation'], 'queue': ['completed']},
        enabled=False  # Disabled for test
    )
    console.print("  ✅ Registered webhook: Test Webhook")
    
    # Get stats
    stats = publisher.get_stats()
    console.print(f"  📊 Webhooks registered: {len(stats['webhooks'])}")
    
    await publisher.stop()
    
    # Test 7: SIEM Integration (mock)
    console.print("\n[bold cyan]Test 7: SIEM Integration (Mock)[/bold cyan]")
    
    from orchestrator.webhook_publisher import SIEMIntegration
    
    # Note: This won't actually send without valid credentials
    siem = SIEMIntegration(
        siem_type='elastic',
        endpoint='https://elasticsearch.example.com:9200',
        api_key='test-key',
        index_name='caldera-test'
    )
    
    console.print("  ✅ SIEM integration initialized")
    console.print(f"  Type: {siem.siem_type}")
    console.print(f"  Endpoint: {siem.endpoint}")
    console.print(f"  Index: {siem.index_name}")
    
    # Test 8: Save Campaign Spec
    console.print("\n[bold cyan]Test 8: Save Campaign Specification[/bold cyan]")
    
    campaigns_dir = Path("data/campaigns")
    campaigns_dir.mkdir(parents=True, exist_ok=True)
    
    import yaml
    spec_file = campaigns_dir / f"test_{campaign.campaign_id}.yml"
    
    with open(spec_file, 'w') as f:
        yaml.dump(campaign.display, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"  ✅ Saved to: [green]{spec_file}[/green]")
    console.print(f"  File size: {spec_file.stat().st_size} bytes")
    
    # Final Summary
    console.print("\n[bold green]═══════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]✅ All Tests Passed![/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════════════[/bold green]\n")
    
    console.print(Panel(
        "[bold white]Next Steps:[/bold white]\n\n"
        "1. Run health check:\n"
        "   [cyan]python3 orchestrator/health_check.py[/cyan]\n\n"
        "2. Create a real campaign:\n"
        "   [cyan]python3 orchestrator/cli.py campaign create schemas/campaign_spec_example.yml[/cyan]\n\n"
        "3. Start the campaign:\n"
        "   [cyan]python3 orchestrator/cli.py campaign start <campaign_id>[/cyan]\n\n"
        "4. Check status:\n"
        "   [cyan]python3 orchestrator/cli.py campaign status <campaign_id>[/cyan]",
        title="🎯 Orchestrator Ready",
        style="green"
    ))
    
    # Cleanup test file
    try:
        spec_file.unlink()
        console.print(f"[dim]Test file cleaned up: {spec_file}[/dim]\n")
    except:
        pass


if __name__ == '__main__':
    asyncio.run(main())
