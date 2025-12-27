#!/usr/bin/env python3
"""
ATT&CK Coverage CLI

Standalone command-line tool for generating ATT&CK coverage reports from Caldera operations.
Wraps existing report_aggregator and attack_navigator modules.

Usage:
    python attck_coverage.py --operation-id <op_id> --output json
    python attck_coverage.py --campaign-id <camp_id> --output pdf --format detailed
    python attck_coverage.py --list-operations
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.report_aggregator import ReportAggregator
from orchestrator.attack_navigator import AttackNavigatorGenerator


class ATTCKCoverageCLI:
    """
    Command-line interface for ATT&CK coverage reporting.
    """
    
    def __init__(
        self,
        caldera_url: str,
        api_key: str,
        output_dir: str = './reports'
    ):
        self.caldera_url = caldera_url.rstrip('/')
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.nav_generator = AttackNavigatorGenerator()
        
    async def list_operations(self) -> List[Dict]:
        """List all operations from Caldera."""
        async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
            operations = await aggregator.api_request('GET', '/api/v2/operations')
            return operations or []
    
    async def get_operation_coverage(self, operation_id: str) -> Dict[str, Any]:
        """
        Get ATT&CK coverage for a specific operation.
        
        Returns:
            Dictionary with coverage metrics and technique details
        """
        async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
            # Get operation details
            operation = await aggregator.api_request('GET', f'/api/v2/operations/{operation_id}')
            if not operation:
                raise ValueError(f"Operation not found: {operation_id}")
            
            # Get links (executed abilities)
            links = await aggregator.api_request('GET', f'/api/v2/operations/{operation_id}/links')
            links = links or []
            
            # Extract techniques
            techniques = []
            tactics = {}
            
            for link in links:
                ability = link.get('ability', {})
                technique_id = ability.get('technique_id', '')
                technique_name = ability.get('technique_name', '')
                tactic = ability.get('tactic', 'unknown')
                
                if technique_id:
                    tech_info = {
                        'technique_id': technique_id,
                        'technique_name': technique_name,
                        'tactic': tactic,
                        'ability_id': ability.get('ability_id', ''),
                        'ability_name': ability.get('name', ''),
                        'status': 'success' if link.get('status', -1) == 0 else 'failed',
                        'status_code': link.get('status', -1),
                        'paw': link.get('paw', ''),
                        'finish': link.get('finish', '')
                    }
                    techniques.append(tech_info)
                    
                    # Group by tactic
                    if tactic not in tactics:
                        tactics[tactic] = []
                    tactics[tactic].append(tech_info)
            
            # Calculate metrics
            total = len(techniques)
            successful = sum(1 for t in techniques if t['status'] == 'success')
            
            return {
                'operation_id': operation_id,
                'operation_name': operation.get('name', 'Unknown'),
                'adversary': operation.get('adversary', {}).get('name', 'Unknown'),
                'state': operation.get('state', ''),
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'summary': {
                    'total_techniques': total,
                    'successful': successful,
                    'failed': total - successful,
                    'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
                    'unique_techniques': len(set(t['technique_id'] for t in techniques)),
                    'unique_tactics': len(tactics)
                },
                'tactics': {
                    tactic: {
                        'count': len(techs),
                        'successful': sum(1 for t in techs if t['status'] == 'success'),
                        'techniques': techs
                    }
                    for tactic, techs in tactics.items()
                },
                'techniques': techniques,
                'technique_ids': list(set(t['technique_id'] for t in techniques)),
                'framework': 'MITRE ATT&CK Enterprise v14'
            }
    
    async def get_campaign_coverage(self, campaign_id: str) -> Dict[str, Any]:
        """Get ATT&CK coverage for an entire campaign."""
        async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
            report_data = await aggregator.get_campaign_data(campaign_id)
            
            # Aggregate techniques across all operations
            all_techniques = []
            for op in report_data.get('operations', []):
                links = op.get('chain', [])
                for link in links:
                    ability = link.get('ability', {})
                    if ability.get('technique_id'):
                        all_techniques.append({
                            'technique_id': ability.get('technique_id'),
                            'technique_name': ability.get('technique_name'),
                            'tactic': ability.get('tactic'),
                            'status': 'success' if link.get('status', -1) == 0 else 'failed',
                            'operation_id': op.get('id'),
                            'operation_name': op.get('name')
                        })
            
            # Calculate metrics
            total = len(all_techniques)
            successful = sum(1 for t in all_techniques if t['status'] == 'success')
            
            return {
                'campaign_id': campaign_id,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'summary': report_data.get('summary', {}),
                'coverage': {
                    'total_techniques': total,
                    'successful': successful,
                    'failed': total - successful,
                    'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
                    'unique_techniques': len(set(t['technique_id'] for t in all_techniques))
                },
                'techniques': all_techniques,
                'technique_ids': list(set(t['technique_id'] for t in all_techniques)),
                'framework': 'MITRE ATT&CK Enterprise v14'
            }
    
    def generate_navigator_layer(
        self,
        coverage: Dict[str, Any],
        layer_name: str = None
    ) -> Dict[str, Any]:
        """Generate ATT&CK Navigator layer JSON from coverage data."""
        techniques_data = []
        
        for tech in coverage.get('techniques', []):
            techniques_data.append({
                'techniqueID': tech['technique_id'],
                'score': 100 if tech['status'] == 'success' else 50,
                'color': '#48CFA0' if tech['status'] == 'success' else '#FF6B6B',
                'comment': f"Status: {tech['status']}"
            })
        
        layer = self.nav_generator.create_layer(
            name=layer_name or f"Coverage - {coverage.get('operation_id', 'Unknown')[:8]}",
            description=f"ATT&CK coverage from Caldera operation",
            techniques=techniques_data
        )
        
        return layer
    
    def export_json(self, coverage: Dict[str, Any], filename: str = None) -> str:
        """Export coverage report as JSON."""
        if not filename:
            op_id = coverage.get('operation_id', coverage.get('campaign_id', 'unknown'))
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"coverage_{op_id[:8]}_{timestamp}.json"
        
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(coverage, f, indent=2)
        
        return str(output_path)
    
    def export_csv(self, coverage: Dict[str, Any], filename: str = None) -> str:
        """Export coverage report as CSV."""
        import csv
        
        if not filename:
            op_id = coverage.get('operation_id', coverage.get('campaign_id', 'unknown'))
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"coverage_{op_id[:8]}_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Technique ID', 'Technique Name', 'Tactic', 
                'Status', 'Ability ID', 'Agent PAW'
            ])
            
            for tech in coverage.get('techniques', []):
                writer.writerow([
                    tech.get('technique_id', ''),
                    tech.get('technique_name', ''),
                    tech.get('tactic', ''),
                    tech.get('status', ''),
                    tech.get('ability_id', ''),
                    tech.get('paw', '')
                ])
        
        return str(output_path)
    
    def export_navigator_layer(self, coverage: Dict[str, Any], filename: str = None) -> str:
        """Export ATT&CK Navigator layer JSON."""
        if not filename:
            op_id = coverage.get('operation_id', coverage.get('campaign_id', 'unknown'))
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"navigator_{op_id[:8]}_{timestamp}.json"
        
        output_path = self.output_dir / filename
        layer = self.generate_navigator_layer(coverage)
        
        with open(output_path, 'w') as f:
            json.dump(layer, f, indent=2)
        
        return str(output_path)
    
    def print_summary(self, coverage: Dict[str, Any]):
        """Print coverage summary to console."""
        summary = coverage.get('summary', {})
        
        print("\n" + "=" * 60)
        print("🎯 ATT&CK COVERAGE REPORT")
        print("=" * 60)
        print(f"Operation: {coverage.get('operation_name', coverage.get('campaign_id', 'Unknown'))}")
        print(f"Generated: {coverage.get('generated_at', 'Unknown')}")
        print("-" * 60)
        print(f"Total Techniques:  {summary.get('total_techniques', 0)}")
        print(f"  ✅ Successful:   {summary.get('successful', 0)}")
        print(f"  ❌ Failed:       {summary.get('failed', 0)}")
        print(f"  📊 Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Unique Techniques: {summary.get('unique_techniques', len(coverage.get('technique_ids', [])))}")
        print(f"Tactics Covered:   {summary.get('unique_tactics', 0)}")
        print("-" * 60)
        
        # Print tactics breakdown
        tactics = coverage.get('tactics', {})
        if tactics:
            print("\n📋 TACTICS BREAKDOWN:")
            for tactic, data in sorted(tactics.items()):
                count = data.get('count', len(data.get('techniques', [])))
                successful = data.get('successful', sum(1 for t in data.get('techniques', []) if t.get('status') == 'success'))
                print(f"  {tactic}: {successful}/{count} successful")
        
        # Print technique list
        print("\n🔬 TECHNIQUES EXECUTED:")
        for tech in coverage.get('techniques', [])[:20]:
            status_icon = "✅" if tech.get('status') == 'success' else "❌"
            print(f"  {status_icon} {tech.get('technique_id', 'N/A')} - {tech.get('technique_name', 'Unknown')}")
        
        if len(coverage.get('techniques', [])) > 20:
            print(f"  ... and {len(coverage['techniques']) - 20} more")
        
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Generate ATT&CK coverage reports from Caldera operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all operations
  python attck_coverage.py --list-operations
  
  # Generate JSON coverage report for an operation
  python attck_coverage.py --operation-id abc123 --output json
  
  # Generate CSV export with summary
  python attck_coverage.py --operation-id abc123 --output csv --summary
  
  # Generate ATT&CK Navigator layer
  python attck_coverage.py --operation-id abc123 --output navigator
  
  # Campaign-wide coverage
  python attck_coverage.py --campaign-id camp123 --output json
        """
    )
    
    # Target selection
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument('--operation-id', '-o', help='Operation ID to analyze')
    target_group.add_argument('--campaign-id', '-c', help='Campaign ID to analyze')
    target_group.add_argument('--list-operations', '-l', action='store_true', help='List all operations')
    
    # Output options
    parser.add_argument('--output', '-O', choices=['json', 'csv', 'navigator', 'all'], 
                        default='json', help='Output format (default: json)')
    parser.add_argument('--output-dir', '-d', default='./reports', help='Output directory')
    parser.add_argument('--filename', '-f', help='Custom output filename')
    parser.add_argument('--summary', '-s', action='store_true', help='Print summary to console')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output except errors')
    
    # Connection settings
    parser.add_argument('--caldera-url', default=os.getenv('CALDERA_URL', 'http://localhost:8888'),
                        help='Caldera server URL')
    parser.add_argument('--api-key', default=os.getenv('CALDERA_API_KEY_RED', ''),
                        help='Caldera API key')
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key and not args.list_operations:
        print("Error: API key required. Set CALDERA_API_KEY_RED environment variable or use --api-key")
        sys.exit(1)
    
    # Initialize CLI
    cli = ATTCKCoverageCLI(
        caldera_url=args.caldera_url,
        api_key=args.api_key,
        output_dir=args.output_dir
    )
    
    async def run():
        # List operations
        if args.list_operations:
            operations = await cli.list_operations()
            print("\n📋 CALDERA OPERATIONS:")
            print("-" * 80)
            for op in operations:
                state = op.get('state', 'unknown')
                state_icon = {'running': '🟢', 'finished': '✅', 'paused': '⏸️'}.get(state, '⚪')
                print(f"  {state_icon} {op.get('id', 'N/A')[:8]}... | {op.get('name', 'Unnamed'):<30} | {state}")
            print("-" * 80)
            print(f"Total: {len(operations)} operations\n")
            return
        
        # Get coverage data
        if args.operation_id:
            coverage = await cli.get_operation_coverage(args.operation_id)
        elif args.campaign_id:
            coverage = await cli.get_campaign_coverage(args.campaign_id)
        else:
            print("Error: Specify --operation-id, --campaign-id, or --list-operations")
            sys.exit(1)
        
        # Print summary if requested
        if args.summary or not args.quiet:
            cli.print_summary(coverage)
        
        # Export based on format
        outputs = []
        
        if args.output in ('json', 'all'):
            path = cli.export_json(coverage, args.filename if args.output == 'json' else None)
            outputs.append(('JSON', path))
        
        if args.output in ('csv', 'all'):
            path = cli.export_csv(coverage)
            outputs.append(('CSV', path))
        
        if args.output in ('navigator', 'all'):
            path = cli.export_navigator_layer(coverage)
            outputs.append(('Navigator Layer', path))
        
        # Print output paths
        if not args.quiet:
            print("📁 OUTPUT FILES:")
            for fmt, path in outputs:
                print(f"  {fmt}: {path}")
    
    # Run async main
    asyncio.run(run())


if __name__ == '__main__':
    main()
