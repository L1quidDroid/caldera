#!/usr/bin/env python3
"""
Caldera Health Check Script

Verifies that Caldera services are operational and ready for campaign execution.

Checks:
- Caldera web UI reachable
- REST API v2 responds correctly
- Required plugins are loaded
- API keys are valid
- Environment configuration is correct

Usage:
    python3 health_check.py [--url=http://localhost:8888] [--api-key=ADMIN123]
    python3 health_check.py --environment=<campaign_spec.yml>
"""

import argparse
import os
import sys
import json
from typing import Dict, List, Tuple
from pathlib import Path

try:
    import requests
    import yaml
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install requests pyyaml rich")
    sys.exit(1)

console = Console()


def get_ssl_verify() -> bool:
    """Get SSL verification setting from environment."""
    ssl_verify = os.getenv('SSL_VERIFY', 'true').lower()
    return ssl_verify not in ('false', '0', 'no', 'off')


class CalderaHealthCheck:
    """Comprehensive health check for Caldera instance."""

    def __init__(
        self,
        caldera_url: str = "http://localhost:8888",
        api_key_red: str = "ADMIN123",
        api_key_blue: str = "BLUEADMIN123",
        timeout: int = 10,
        ssl_verify: bool = None
    ):
        self.caldera_url = caldera_url.rstrip('/')
        self.api_key_red = api_key_red
        self.api_key_blue = api_key_blue
        self.timeout = timeout
        # Use environment variable if not explicitly set
        self.ssl_verify = ssl_verify if ssl_verify is not None else get_ssl_verify()
        self.results: List[Tuple[str, str, bool, str]] = []
        
        if not self.ssl_verify:
            console.print("[yellow]⚠️  SSL verification disabled - use only in development[/yellow]")

    def _make_request(
        self,
        endpoint: str,
        api_key: str = None,
        method: str = 'GET'
    ) -> Tuple[bool, Dict, str]:
        """
        Make HTTP request to Caldera.
        
        Returns:
            (success, data, error_message)
        """
        url = f"{self.caldera_url}{endpoint}"
        headers = {}
        
        if api_key:
            headers['KEY'] = api_key
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout, verify=self.ssl_verify)
            else:
                response = requests.request(method, url, headers=headers, timeout=self.timeout, verify=self.ssl_verify)
            
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    return True, response.json(), ""
                except json.JSONDecodeError:
                    return True, {}, ""
            else:
                return False, {}, f"HTTP {response.status_code}: {response.text[:100]}"
        
        except requests.exceptions.Timeout:
            return False, {}, "Request timed out"
        except requests.exceptions.ConnectionError:
            return False, {}, "Connection failed - service may be down"
        except Exception as e:
            return False, {}, f"Error: {str(e)}"

    def check_web_ui(self) -> bool:
        """Check if web UI is accessible."""
        console.print("[cyan]Checking web UI...[/cyan]")
        
        success, _, error = self._make_request('/')
        
        if success:
            self.results.append(("Web UI", self.caldera_url, True, "Accessible"))
            console.print("  ✅ Web UI is accessible")
            return True
        else:
            self.results.append(("Web UI", self.caldera_url, False, error))
            console.print(f"  ❌ Web UI failed: {error}")
            return False

    def check_rest_api(self) -> bool:
        """Check REST API v2 endpoint."""
        console.print("[cyan]Checking REST API v2...[/cyan]")
        
        success, data, error = self._make_request('/api/v2/config', self.api_key_red)
        
        if success:
            self.results.append(("REST API v2", f"{self.caldera_url}/api/v2", True, "Responding"))
            console.print("  ✅ REST API v2 is responding")
            return True
        else:
            self.results.append(("REST API v2", f"{self.caldera_url}/api/v2", False, error))
            console.print(f"  ❌ REST API v2 failed: {error}")
            return False

    def check_api_keys(self) -> bool:
        """Verify API keys are valid."""
        console.print("[cyan]Checking API keys...[/cyan]")
        
        # Check red team key
        success_red, _, error_red = self._make_request('/api/v2/config', self.api_key_red)
        
        if success_red:
            self.results.append(("API Key (Red)", "***", True, "Valid"))
            console.print("  ✅ Red team API key is valid")
        else:
            self.results.append(("API Key (Red)", "***", False, error_red))
            console.print(f"  ❌ Red team API key failed: {error_red}")
        
        # Check blue team key
        success_blue, _, error_blue = self._make_request('/api/v2/config', self.api_key_blue)
        
        if success_blue:
            self.results.append(("API Key (Blue)", "***", True, "Valid"))
            console.print("  ✅ Blue team API key is valid")
        else:
            self.results.append(("API Key (Blue)", "***", False, error_blue))
            console.print(f"  ❌ Blue team API key failed: {error_blue}")
        
        return success_red and success_blue

    def check_plugins(self, required_plugins: List[str] = None) -> bool:
        """Check loaded plugins."""
        console.print("[cyan]Checking plugins...[/cyan]")
        
        # Try v2 API first, fallback to REST API
        success, data, error = self._make_request('/api/rest?index=plugins', self.api_key_red)
        
        if not success:
            self.results.append(("Plugins", "", False, error))
            console.print(f"  ❌ Failed to retrieve plugins: {error}")
            return False
        
        plugins = data if isinstance(data, list) else []
        plugin_names = [p.get('name', 'Unknown') for p in plugins if p.get('enabled', True)]
        
        console.print(f"  ✅ {len(plugin_names)} plugins loaded: {', '.join(plugin_names)}")
        self.results.append(("Plugins", f"{len(plugin_names)} loaded", True, ", ".join(plugin_names)))
        
        # Check required plugins if specified
        if required_plugins:
            missing = [p for p in required_plugins if p not in plugin_names]
            if missing:
                console.print(f"  ⚠️  Missing required plugins: {', '.join(missing)}")
                self.results.append(("Required Plugins", ", ".join(required_plugins), False, f"Missing: {', '.join(missing)}"))
                return False
            else:
                console.print(f"  ✅ All required plugins present")
        
        return True

    def check_agents(self) -> bool:
        """Check agent connectivity."""
        console.print("[cyan]Checking agents...[/cyan]")
        
        success, data, error = self._make_request('/api/v2/agents', self.api_key_red)
        
        if not success:
            self.results.append(("Agents", "", False, error))
            console.print(f"  ❌ Failed to retrieve agents: {error}")
            return False
        
        agents = data if isinstance(data, list) else []
        agent_count = len(agents)
        
        if agent_count == 0:
            console.print("  ⚠️  No agents connected (this may be expected)")
            self.results.append(("Agents", "0 connected", True, "No agents (may be expected)"))
        else:
            platforms = {}
            for agent in agents:
                platform = agent.get('platform', 'unknown')
                platforms[platform] = platforms.get(platform, 0) + 1
            
            platform_summary = ", ".join([f"{count} {platform}" for platform, count in platforms.items()])
            console.print(f"  ✅ {agent_count} agents connected: {platform_summary}")
            self.results.append(("Agents", f"{agent_count} connected", True, platform_summary))
        
        return True

    def check_adversaries(self) -> bool:
        """Check available adversary profiles."""
        console.print("[cyan]Checking adversary profiles...[/cyan]")
        
        success, data, error = self._make_request('/api/v2/adversaries', self.api_key_red)
        
        if not success:
            self.results.append(("Adversaries", "", False, error))
            console.print(f"  ❌ Failed to retrieve adversaries: {error}")
            return False
        
        adversaries = data if isinstance(data, list) else []
        adv_count = len(adversaries)
        
        if adv_count == 0:
            console.print("  ⚠️  No adversary profiles found")
            self.results.append(("Adversaries", "0 profiles", False, "No profiles available"))
            return False
        else:
            adv_names = [a.get('name', 'Unknown') for a in adversaries[:5]]
            console.print(f"  ✅ {adv_count} adversary profiles available")
            if adv_count > 5:
                console.print(f"     First 5: {', '.join(adv_names)}, ...")
            else:
                console.print(f"     Profiles: {', '.join(adv_names)}")
            self.results.append(("Adversaries", f"{adv_count} profiles", True, ", ".join(adv_names[:3])))
        
        return True

    def check_abilities(self) -> bool:
        """Check available abilities (TTPs)."""
        console.print("[cyan]Checking abilities...[/cyan]")
        
        success, data, error = self._make_request('/api/v2/abilities', self.api_key_red)
        
        if not success:
            self.results.append(("Abilities", "", False, error))
            console.print(f"  ❌ Failed to retrieve abilities: {error}")
            return False
        
        abilities = data if isinstance(data, list) else []
        ability_count = len(abilities)
        
        if ability_count == 0:
            console.print("  ⚠️  No abilities found")
            self.results.append(("Abilities", "0 TTPs", False, "No abilities available"))
            return False
        else:
            # Count by tactic
            tactics = {}
            for ability in abilities:
                tactic = ability.get('tactic', 'unknown')
                tactics[tactic] = tactics.get(tactic, 0) + 1
            
            console.print(f"  ✅ {ability_count} abilities available")
            console.print(f"     Tactics: {', '.join([f'{t}({c})' for t, c in tactics.items()])}")
            self.results.append(("Abilities", f"{ability_count} TTPs", True, f"{len(tactics)} tactics"))
        
        return True

    def check_operations(self) -> bool:
        """Check existing operations."""
        console.print("[cyan]Checking operations...[/cyan]")
        
        success, data, error = self._make_request('/api/v2/operations', self.api_key_red)
        
        if not success:
            self.results.append(("Operations", "", False, error))
            console.print(f"  ❌ Failed to retrieve operations: {error}")
            return False
        
        operations = data if isinstance(data, list) else []
        op_count = len(operations)
        
        if op_count == 0:
            console.print("  ℹ️  No operations exist")
            self.results.append(("Operations", "0 operations", True, "None (expected for new setup)"))
        else:
            # Count by state
            states = {}
            for op in operations:
                state = op.get('state', 'unknown')
                states[state] = states.get(state, 0) + 1
            
            state_summary = ", ".join([f"{count} {state}" for state, count in states.items()])
            console.print(f"  ℹ️  {op_count} operations exist: {state_summary}")
            self.results.append(("Operations", f"{op_count} operations", True, state_summary))
        
        return True

    def check_environment_metadata(self, campaign_spec: Dict) -> bool:
        """Validate campaign environment configuration."""
        console.print("[cyan]Checking campaign environment...[/cyan]")
        
        env = campaign_spec.get('environment', {})
        
        # Check environment ID
        env_id = env.get('environment_id')
        if not env_id:
            console.print("  ⚠️  No environment_id specified")
            self.results.append(("Environment ID", "", False, "Not specified"))
        else:
            console.print(f"  ✅ Environment ID: {env_id}")
            self.results.append(("Environment ID", env_id, True, env.get('type', 'unknown')))
        
        # Check Caldera URL matches
        spec_url = env.get('caldera_url', '').rstrip('/')
        if spec_url and spec_url != self.caldera_url:
            console.print(f"  ⚠️  Campaign URL ({spec_url}) differs from target ({self.caldera_url})")
            self.results.append(("Caldera URL", spec_url, False, "URL mismatch"))
        elif spec_url:
            console.print(f"  ✅ Caldera URL matches: {spec_url}")
            self.results.append(("Caldera URL", spec_url, True, "Matches"))
        
        return True

    def run_all_checks(self, campaign_spec: Dict = None, required_plugins: List[str] = None) -> bool:
        """
        Run all health checks.
        
        Returns:
            True if all critical checks pass
        """
        console.print("\n[bold blue]╔═══════════════════════════════════════════════════════════╗[/bold blue]")
        console.print("[bold blue]║          CALDERA HEALTH CHECK - PHASE 1                 ║[/bold blue]")
        console.print("[bold blue]╚═══════════════════════════════════════════════════════════╝[/bold blue]\n")
        
        console.print(f"[bold]Target:[/bold] {self.caldera_url}\n")
        
        # Run checks
        checks = [
            self.check_web_ui(),
            self.check_rest_api(),
            self.check_api_keys(),
            self.check_plugins(required_plugins),
            self.check_agents(),
            self.check_adversaries(),
            self.check_abilities(),
            self.check_operations()
        ]
        
        # Campaign environment check if provided
        if campaign_spec:
            checks.append(self.check_environment_metadata(campaign_spec))
        
        # Display summary table
        console.print("\n[bold blue]Summary:[/bold blue]\n")
        
        table = Table(title="Health Check Results", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="white", width=20)
        table.add_column("Details", style="cyan", width=30)
        table.add_column("Status", style="green", width=10)
        table.add_column("Notes", style="yellow")
        
        for component, details, success, notes in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            status_style = "green" if success else "red"
            table.add_row(component, details, status, notes)
        
        console.print(table)
        console.print()
        
        # Final verdict
        all_passed = all(checks)
        critical_failures = [r for r in self.results if not r[2] and r[0] in ["Web UI", "REST API v2", "API Key (Red)"]]
        
        if all_passed:
            console.print(Panel(
                "[bold green]✅ ALL CHECKS PASSED[/bold green]\n\nCaldera is ready for campaign execution.",
                style="green",
                title="Success"
            ))
            return True
        elif critical_failures:
            console.print(Panel(
                "[bold red]❌ CRITICAL FAILURES DETECTED[/bold red]\n\nCaldera is not operational. Fix critical issues before proceeding.",
                style="red",
                title="Critical Failure"
            ))
            return False
        else:
            console.print(Panel(
                "[bold yellow]⚠️  WARNINGS PRESENT[/bold yellow]\n\nCaldera is operational but some components need attention.",
                style="yellow",
                title="Warning"
            ))
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Caldera Health Check - Verify services are ready',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:8888',
        help='Caldera base URL (default: http://localhost:8888)'
    )
    parser.add_argument(
        '--api-key-red',
        default='ADMIN123',
        help='Red team API key (default: ADMIN123)'
    )
    parser.add_argument(
        '--api-key-blue',
        default='BLUEADMIN123',
        help='Blue team API key (default: BLUEADMIN123)'
    )
    parser.add_argument(
        '--environment',
        help='Path to campaign specification YAML file'
    )
    parser.add_argument(
        '--required-plugins',
        help='Comma-separated list of required plugin names'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    # Load campaign spec if provided
    campaign_spec = None
    if args.environment:
        env_path = Path(args.environment)
        if not env_path.exists():
            console.print(f"[red]Error: Campaign spec not found: {env_path}[/red]")
            sys.exit(1)
        
        with open(env_path, 'r') as f:
            campaign_spec = yaml.safe_load(f)
        
        # Override URL and keys from campaign spec
        env = campaign_spec.get('environment', {})
        args.url = env.get('caldera_url', args.url)
        args.api_key_red = env.get('api_key_red', args.api_key_red)
        args.api_key_blue = env.get('api_key_blue', args.api_key_blue)
    
    # Parse required plugins
    required_plugins = None
    if args.required_plugins:
        required_plugins = [p.strip() for p in args.required_plugins.split(',')]
    
    # Run health check
    checker = CalderaHealthCheck(
        caldera_url=args.url,
        api_key_red=args.api_key_red,
        api_key_blue=args.api_key_blue,
        timeout=args.timeout
    )
    
    success = checker.run_all_checks(campaign_spec, required_plugins)
    
    # JSON output
    if args.json:
        output = {
            'success': success,
            'caldera_url': args.url,
            'timestamp': str(Path(__file__).stat().st_mtime),
            'results': [
                {
                    'component': r[0],
                    'details': r[1],
                    'success': r[2],
                    'notes': r[3]
                }
                for r in checker.results
            ]
        }
        console.print_json(data=output)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
