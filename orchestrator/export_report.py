#!/usr/bin/env python3
"""
Export Report CLI

Standalone command-line tool for generating and exporting Caldera campaign reports.
Supports PDF, HTML, JSON, and ATT&CK Navigator layer exports.

Usage:
    python export_report.py --campaign-id <camp_id> --format pdf
    python export_report.py --operation-id <op_id> --format json --output ./reports
    python export_report.py --campaign-id <camp_id> --format all --publish-github
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


class ExportReportCLI:
    """
    Command-line interface for report generation and export.
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
        
    async def generate_pdf(
        self,
        campaign_id: str,
        include_output: bool = False,
        include_facts: bool = True,
        attack_layer: bool = True
    ) -> Optional[str]:
        """Generate PDF report using PDFReportGenerator."""
        try:
            from orchestrator.pdf_generator import PDFReportGenerator
            
            generator = PDFReportGenerator(
                caldera_url=self.caldera_url,
                api_key=self.api_key
            )
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"report_{campaign_id[:8]}_{timestamp}.pdf"
            
            result = await generator.generate_report(
                campaign_id=campaign_id,
                output_path=str(output_path),
                include_output=include_output,
                include_facts=include_facts,
                attack_layer=attack_layer
            )
            
            return str(output_path)
            
        except ImportError as e:
            print(f"⚠️  PDF generation requires WeasyPrint: pip install weasyprint")
            return None
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None
    
    async def generate_html(self, campaign_id: str) -> Optional[str]:
        """Generate HTML report."""
        try:
            from orchestrator.pdf_generator import PDFReportGenerator
            from orchestrator.report_aggregator import ReportAggregator
            
            # Get campaign data
            async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
                report_data = await aggregator.get_campaign_data(campaign_id)
            
            # Generate HTML using template
            generator = PDFReportGenerator(
                caldera_url=self.caldera_url,
                api_key=self.api_key
            )
            
            # Render template
            template = generator.jinja_env.get_template('report_template.html')
            html_content = template.render(
                report=report_data,
                generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                charts={}
            )
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"report_{campaign_id[:8]}_{timestamp}.html"
            
            with open(output_path, 'w') as f:
                f.write(html_content)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ HTML generation failed: {e}")
            return None
    
    async def generate_json(self, campaign_id: str) -> Optional[str]:
        """Generate JSON report with full campaign data."""
        try:
            from orchestrator.report_aggregator import ReportAggregator
            
            async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
                report_data = await aggregator.get_campaign_data(campaign_id)
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"report_{campaign_id[:8]}_{timestamp}.json"
            
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ JSON generation failed: {e}")
            return None
    
    async def generate_navigator_layer(self, campaign_id: str) -> Optional[str]:
        """Generate ATT&CK Navigator layer."""
        try:
            from orchestrator.attack_navigator import AttackNavigatorGenerator
            from orchestrator.report_aggregator import ReportAggregator
            
            async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
                report_data = await aggregator.get_campaign_data(campaign_id)
            
            # Extract techniques from operations
            techniques_data = []
            for op in report_data.get('operations', []):
                for link in op.get('chain', []):
                    ability = link.get('ability', {})
                    if ability.get('technique_id'):
                        status = 'success' if link.get('status', -1) == 0 else 'failed'
                        techniques_data.append({
                            'techniqueID': ability.get('technique_id'),
                            'score': 100 if status == 'success' else 50,
                            'color': '#48CFA0' if status == 'success' else '#FF6B6B',
                            'comment': f"Ability: {ability.get('name', 'Unknown')}"
                        })
            
            # Generate layer
            nav = AttackNavigatorGenerator()
            layer = nav.create_layer(
                name=f"Campaign: {report_data.get('summary', {}).get('campaign_id', campaign_id)[:8]}",
                description=f"ATT&CK coverage from Caldera campaign",
                techniques=techniques_data
            )
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"navigator_{campaign_id[:8]}_{timestamp}.json"
            
            with open(output_path, 'w') as f:
                json.dump(layer, f, indent=2)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Navigator layer generation failed: {e}")
            return None
    
    async def publish_to_github(
        self,
        file_path: str,
        github_token: str,
        github_repo: str,
        branch: str = 'gh-pages'
    ) -> bool:
        """Publish report to GitHub Pages."""
        import base64
        import aiohttp
        
        report_file = Path(file_path)
        if not report_file.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        # Read file content
        with open(report_file, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        
        filename = report_file.name
        api_url = f"https://api.github.com/repos/{github_repo}/contents/reports/{filename}"
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'message': f"Add report: {filename}",
            'content': content,
            'branch': branch
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(api_url, json=payload, headers=headers) as resp:
                if resp.status in (200, 201):
                    print(f"✅ Published to GitHub: https://github.com/{github_repo}/blob/{branch}/reports/{filename}")
                    return True
                else:
                    error = await resp.text()
                    print(f"❌ GitHub publish failed: {resp.status} - {error[:200]}")
                    return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate and export Caldera campaign reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PDF report
  python export_report.py --campaign-id abc123 --format pdf
  
  # Generate all formats
  python export_report.py --campaign-id abc123 --format all
  
  # Generate and publish to GitHub Pages
  python export_report.py --campaign-id abc123 --format pdf --publish-github
  
  # Custom output directory
  python export_report.py --campaign-id abc123 --format json --output ./custom-reports
        """
    )
    
    # Target selection
    parser.add_argument('--campaign-id', '-c', required=True, help='Campaign ID to export')
    
    # Format options
    parser.add_argument('--format', '-f', 
                        choices=['pdf', 'html', 'json', 'navigator', 'all'],
                        default='pdf',
                        help='Export format (default: pdf)')
    
    # Output options
    parser.add_argument('--output', '-o', default='./reports', help='Output directory')
    parser.add_argument('--include-output', action='store_true', 
                        help='Include full ability output in PDF (verbose)')
    parser.add_argument('--include-facts', action='store_true', default=True,
                        help='Include agent facts in report')
    parser.add_argument('--no-attack-layer', action='store_true',
                        help='Skip ATT&CK Navigator layer generation')
    
    # GitHub publishing
    parser.add_argument('--publish-github', action='store_true',
                        help='Publish report to GitHub Pages')
    parser.add_argument('--github-token', default=os.getenv('GITHUB_TOKEN'),
                        help='GitHub Personal Access Token')
    parser.add_argument('--github-repo', default=os.getenv('GITHUB_REPO'),
                        help='GitHub repository (owner/repo)')
    parser.add_argument('--github-branch', default='gh-pages',
                        help='GitHub Pages branch')
    
    # Connection settings
    parser.add_argument('--caldera-url', 
                        default=os.getenv('CALDERA_URL', 'http://localhost:8888'),
                        help='Caldera server URL')
    parser.add_argument('--api-key', 
                        default=os.getenv('CALDERA_API_KEY_RED', ''),
                        help='Caldera API key')
    
    # Verbosity
    parser.add_argument('--quiet', '-q', action='store_true', 
                        help='Suppress output except errors')
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        print("Error: API key required. Set CALDERA_API_KEY_RED environment variable or use --api-key")
        sys.exit(1)
    
    # Validate GitHub settings if publishing
    if args.publish_github:
        if not args.github_token:
            print("Error: GitHub token required for publishing. Set GITHUB_TOKEN or use --github-token")
            sys.exit(1)
        if not args.github_repo:
            print("Error: GitHub repo required for publishing. Set GITHUB_REPO or use --github-repo")
            sys.exit(1)
    
    # Initialize CLI
    cli = ExportReportCLI(
        caldera_url=args.caldera_url,
        api_key=args.api_key,
        output_dir=args.output
    )
    
    async def run():
        outputs = []
        
        if not args.quiet:
            print(f"\n📊 Generating report for campaign: {args.campaign_id}")
            print("-" * 60)
        
        # Generate requested formats
        if args.format in ('pdf', 'all'):
            if not args.quiet:
                print("  📄 Generating PDF...")
            path = await cli.generate_pdf(
                args.campaign_id,
                include_output=args.include_output,
                include_facts=args.include_facts,
                attack_layer=not args.no_attack_layer
            )
            if path:
                outputs.append(('PDF', path))
        
        if args.format in ('html', 'all'):
            if not args.quiet:
                print("  🌐 Generating HTML...")
            path = await cli.generate_html(args.campaign_id)
            if path:
                outputs.append(('HTML', path))
        
        if args.format in ('json', 'all'):
            if not args.quiet:
                print("  📋 Generating JSON...")
            path = await cli.generate_json(args.campaign_id)
            if path:
                outputs.append(('JSON', path))
        
        if args.format in ('navigator', 'all'):
            if not args.quiet:
                print("  🗺️  Generating Navigator layer...")
            path = await cli.generate_navigator_layer(args.campaign_id)
            if path:
                outputs.append(('Navigator', path))
        
        # Print results
        if not args.quiet:
            print("-" * 60)
            print("📁 OUTPUT FILES:")
            for fmt, path in outputs:
                print(f"  ✅ {fmt}: {path}")
        
        # Publish to GitHub if requested
        if args.publish_github and outputs:
            if not args.quiet:
                print("\n🚀 Publishing to GitHub Pages...")
            
            for fmt, path in outputs:
                success = await cli.publish_to_github(
                    path,
                    args.github_token,
                    args.github_repo,
                    args.github_branch
                )
                if not success and not args.quiet:
                    print(f"  ⚠️  Failed to publish {fmt}")
        
        if not args.quiet:
            print("\n✨ Export complete!\n")
    
    # Run async main
    asyncio.run(run())


if __name__ == '__main__':
    main()
