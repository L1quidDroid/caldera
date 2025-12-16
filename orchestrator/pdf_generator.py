"""
PDF Generator for Caldera Campaign Reports

Generates professional PDF reports using WeasyPrint with Triskele Labs branding.
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("Warning: WeasyPrint not available. Install with: pip install weasyprint")

from orchestrator.report_aggregator import ReportAggregator
from orchestrator.attack_navigator import AttackNavigatorGenerator
from orchestrator.report_visualizations import ReportVisualizations


class PDFReportGenerator:
    """
    Generates comprehensive PDF reports for Caldera campaigns.
    """
    
    def __init__(
        self,
        caldera_url: str,
        api_key: str,
        template_dir: Optional[str] = None
    ):
        """
        Initialize PDF report generator.
        
        Args:
            caldera_url: Base URL of CALDERA server
            api_key: API key for authentication
            template_dir: Optional custom template directory
        """
        self.caldera_url = caldera_url
        self.api_key = api_key
        
        # Set up template directory
        if template_dir:
            self.template_dir = template_dir
        else:
            current_dir = Path(__file__).parent
            self.template_dir = current_dir / 'templates'
            
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Initialize components
        self.visualizations = ReportVisualizations(style='triskele')
        self.attack_nav = AttackNavigatorGenerator()
        
    async def generate_report(
        self,
        campaign_id: str,
        output_path: str,
        include_output: bool = False,
        include_facts: bool = True,
        attack_layer: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive PDF report for campaign.
        
        Args:
            campaign_id: Campaign identifier
            output_path: Output PDF file path
            include_output: Include full ability output (verbose)
            include_facts: Include agent facts
            attack_layer: Generate ATT&CK Navigator layer
            
        Returns:
            Dictionary with report metadata and file paths
        """
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not installed. Install with: pip install weasyprint")
            
        print(f"📊 Generating report for campaign: {campaign_id}")
        
        # Collect campaign data
        print("  ⏳ Collecting campaign data...")
        async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
            report_data = await aggregator.get_campaign_data(campaign_id)
            
        print(f"  ✅ Collected data for {report_data['summary']['total_operations']} operations")
        
        # Generate visualizations
        print("  📈 Generating charts...")
        charts = self._generate_charts(report_data)
        print(f"  ✅ Generated {len(charts)} charts")
        
        # Generate ATT&CK Navigator layer
        attack_layer_path = None
        if attack_layer and report_data['techniques']:
            print("  🎯 Generating ATT&CK Navigator layer...")
            attack_layer_path = self._generate_attack_layer(
                campaign_id, 
                report_data
            )
            print(f"  ✅ ATT&CK layer saved to: {attack_layer_path}")
            
        # Render HTML template
        print("  📝 Rendering HTML template...")
        html_content = self._render_template(
            report_data,
            charts,
            attack_layer_path,
            include_output,
            include_facts
        )
        
        # Generate PDF
        print("  📄 Generating PDF...")
        self._generate_pdf(html_content, output_path)
        
        # Calculate file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"  ✅ PDF report generated: {output_path} ({file_size_mb:.2f} MB)")
        
        return {
            'campaign_id': campaign_id,
            'pdf_path': output_path,
            'attack_layer_path': attack_layer_path,
            'generated_at': datetime.utcnow().isoformat(),
            'file_size_mb': round(file_size_mb, 2),
            'summary': report_data['summary'],
            'charts_generated': len(charts)
        }
        
    def _generate_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all visualization charts."""
        charts = {}
        
        # Success rate pie chart
        try:
            charts['success_rate'] = self.visualizations.generate_success_rate_chart(
                report_data['summary']
            )
        except Exception as e:
            print(f"    ⚠️ Could not generate success rate chart: {e}")
            
        # Platform distribution
        try:
            charts['platform_distribution'] = self.visualizations.generate_platform_distribution(
                report_data['statistics']
            )
        except Exception as e:
            print(f"    ⚠️ Could not generate platform distribution: {e}")
            
        # Technique heatmap
        try:
            charts['technique_heatmap'] = self.visualizations.generate_technique_heatmap(
                report_data['statistics']
            )
        except Exception as e:
            print(f"    ⚠️ Could not generate technique heatmap: {e}")
            
        # Timeline chart
        try:
            if report_data['timeline']:
                charts['timeline'] = self.visualizations.generate_timeline_chart(
                    report_data['timeline']
                )
        except Exception as e:
            print(f"    ⚠️ Could not generate timeline chart: {e}")
            
        return charts
        
    def _generate_attack_layer(
        self,
        campaign_id: str,
        report_data: Dict[str, Any]
    ) -> str:
        """Generate ATT&CK Navigator layer file."""
        # Prepare metadata
        metadata = {
            'agent_count': report_data['summary']['total_agents'],
            'operations_count': report_data['summary']['total_operations'],
            'duration_hours': report_data['summary']['duration_hours'],
            'total_abilities': report_data['summary']['total_abilities_executed'],
            'success_rate': report_data['summary']['success_rate']
        }
        
        # Generate layer
        layer = self.attack_nav.generate_layer(
            campaign_id=campaign_id,
            campaign_name=f"Campaign {campaign_id}",
            techniques=report_data['techniques'],
            operations=report_data['operations'],
            metadata=metadata
        )
        
        # Save layer
        output_path = f"data/reports/{campaign_id}_attack_layer.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.attack_nav.save_layer(layer, output_path)
        
        return output_path
        
    def _render_template(
        self,
        report_data: Dict[str, Any],
        charts: Dict[str, str],
        attack_layer_path: Optional[str],
        include_output: bool,
        include_facts: bool
    ) -> str:
        """Render HTML template with report data."""
        template = self.jinja_env.get_template('report_template.html')
        
        # Format generated_at timestamp
        generated_at = datetime.fromisoformat(report_data['generated_at'])
        formatted_date = generated_at.strftime('%B %d, %Y at %H:%M:%S UTC')
        
        html_content = template.render(
            campaign_id=report_data['campaign_id'],
            generated_at=formatted_date,
            summary=report_data['summary'],
            operations=report_data['operations'],
            agents=report_data['agents'],
            techniques=report_data['techniques'],
            timeline=report_data['timeline'],
            errors=report_data['errors'],
            statistics=report_data['statistics'],
            charts=charts,
            attack_layer_path=attack_layer_path,
            include_output=include_output,
            include_facts=include_facts
        )
        
        return html_content
        
    def _generate_pdf(self, html_content: str, output_path: str):
        """Generate PDF from HTML content using WeasyPrint."""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate PDF
        HTML(string=html_content, base_url=str(self.template_dir)).write_pdf(
            output_path,
            presentational_hints=True,
            optimize_size=('fonts', 'images')
        )
        
    async def generate_summary_report(
        self,
        campaign_ids: list,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Generate a summary report comparing multiple campaigns.
        
        Args:
            campaign_ids: List of campaign identifiers
            output_path: Output PDF file path
            
        Returns:
            Dictionary with report metadata
        """
        print(f"📊 Generating summary report for {len(campaign_ids)} campaigns")
        
        # Collect data for all campaigns
        campaigns_data = []
        
        async with ReportAggregator(self.caldera_url, self.api_key) as aggregator:
            for campaign_id in campaign_ids:
                print(f"  ⏳ Collecting data for {campaign_id}...")
                try:
                    data = await aggregator.get_campaign_data(campaign_id)
                    campaigns_data.append(data)
                except Exception as e:
                    print(f"    ⚠️ Could not collect data for {campaign_id}: {e}")
                    
        if not campaigns_data:
            raise ValueError("No campaign data collected")
            
        # Generate comparison ATT&CK layer
        print("  🎯 Generating comparison ATT&CK Navigator layer...")
        comparison_layer = self.attack_nav.generate_comparison_layer(campaigns_data)
        
        layer_path = f"data/reports/comparison_{len(campaign_ids)}_campaigns_attack_layer.json"
        os.makedirs(os.path.dirname(layer_path), exist_ok=True)
        self.attack_nav.save_layer(comparison_layer, layer_path)
        
        print(f"  ✅ Summary report generated: {output_path}")
        
        return {
            'campaign_count': len(campaigns_data),
            'campaigns': [c['campaign_id'] for c in campaigns_data],
            'attack_layer_path': layer_path,
            'generated_at': datetime.utcnow().isoformat()
        }


# CLI usage helper
async def generate_campaign_report_cli(
    campaign_id: str,
    caldera_url: str = "http://localhost:8888",
    api_key: str = "ADMIN123",
    output_path: Optional[str] = None,
    attack_layer: bool = True
):
    """
    CLI helper function to generate campaign report.
    
    Args:
        campaign_id: Campaign identifier
        caldera_url: CALDERA server URL
        api_key: API key for authentication
        output_path: Optional output path (defaults to data/reports/)
        attack_layer: Generate ATT&CK Navigator layer
    """
    if not output_path:
        output_path = f"data/reports/{campaign_id}_report.pdf"
        
    generator = PDFReportGenerator(caldera_url, api_key)
    
    result = await generator.generate_report(
        campaign_id=campaign_id,
        output_path=output_path,
        attack_layer=attack_layer
    )
    
    print("\n" + "="*60)
    print("📊 REPORT GENERATION COMPLETE")
    print("="*60)
    print(f"Campaign ID:      {result['campaign_id']}")
    print(f"PDF Report:       {result['pdf_path']}")
    if result['attack_layer_path']:
        print(f"ATT&CK Layer:     {result['attack_layer_path']}")
    print(f"File Size:        {result['file_size_mb']} MB")
    print(f"Operations:       {result['summary']['total_operations']}")
    print(f"Agents:           {result['summary']['total_agents']}")
    print(f"Abilities:        {result['summary']['total_abilities_executed']}")
    print(f"Success Rate:     {result['summary']['success_rate']:.1f}%")
    print("="*60)
    
    return result


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_generator.py <campaign_id> [caldera_url] [api_key]")
        sys.exit(1)
        
    campaign_id = sys.argv[1]
    caldera_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8888"
    api_key = sys.argv[3] if len(sys.argv) > 3 else "ADMIN123"
    
    asyncio.run(generate_campaign_report_cli(campaign_id, caldera_url, api_key))
