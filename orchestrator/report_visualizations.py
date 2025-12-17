"""
Report Visualizations for Caldera Campaigns

Generates charts and visualizations for PDF reports using matplotlib
with Triskele Labs branding.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
from typing import Dict, List, Any, Optional
from io import BytesIO
import base64


class ReportVisualizations:
    """
    Generates charts and visualizations with Triskele Labs branding.
    """
    
    # Triskele Labs color palette
    COLORS = {
        'primary': '#48CFA0',      # Triskele green
        'dark': '#020816',         # Dark blue
        'success': '#48CFA0',      # Green
        'warning': '#F59E0B',      # Amber
        'error': '#EF4444',        # Red
        'neutral_100': '#F3F4F6',  # Light gray
        'neutral_300': '#D1D5DB',  # Medium gray
        'neutral_600': '#4B5563',  # Dark gray
        'neutral_800': '#1F2937'   # Very dark gray
    }
    
    def __init__(self, style: str = 'triskele'):
        """
        Initialize visualization generator.
        
        Args:
            style: Visualization style ('triskele' or 'minimal')
        """
        self.style = style
        self._setup_matplotlib_style()
        
    def _setup_matplotlib_style(self):
        """Configure matplotlib with Triskele branding."""
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans'],
            'font.size': 10,
            'axes.facecolor': 'white',
            'axes.edgecolor': self.COLORS['neutral_300'],
            'axes.labelcolor': self.COLORS['neutral_800'],
            'axes.titlesize': 12,
            'axes.titleweight': 'bold',
            'axes.titlecolor': self.COLORS['dark'],
            'figure.facecolor': 'white',
            'figure.edgecolor': 'white',
            'grid.color': self.COLORS['neutral_300'],
            'grid.linestyle': '--',
            'grid.linewidth': 0.5,
            'xtick.color': self.COLORS['neutral_600'],
            'ytick.color': self.COLORS['neutral_600'],
            'text.color': self.COLORS['neutral_800']
        })
        
    def generate_success_rate_chart(
        self,
        summary: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate pie chart showing success/failure rates.
        
        Args:
            summary: Campaign summary data
            output_path: Optional file path to save chart
            
        Returns:
            Base64 encoded PNG image or file path
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Data
        successful = summary.get('successful_abilities', 0)
        failed = summary.get('failed_abilities', 0)
        
        if successful == 0 and failed == 0:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
        else:
            sizes = [successful, failed]
            labels = [f'Successful\n({successful})', f'Failed\n({failed})']
            colors = [self.COLORS['success'], self.COLORS['error']]
            # Slightly separate success slice for emphasis
            PIE_EXPLODE_SUCCESS = 0.05
            explode = (PIE_EXPLODE_SUCCESS, 0)
            
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct='%1.1f%%',
                explode=explode,
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            
            # Style percentage text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                
        ax.set_title('Ability Execution Success Rate', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        return self._save_or_encode(fig, output_path)
        
    def generate_platform_distribution(
        self,
        statistics: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate bar chart showing agent and ability distribution by platform.
        
        Args:
            statistics: Campaign statistics
            output_path: Optional file path to save chart
            
        Returns:
            Base64 encoded PNG image or file path
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        by_platform = statistics.get('by_platform', {})
        
        if not by_platform:
            for ax in [ax1, ax2]:
                ax.text(0.5, 0.5, 'No data available', 
                       ha='center', va='center', fontsize=14)
                ax.axis('off')
        else:
            platforms = list(by_platform.keys())
            agent_counts = [data['agents'] for data in by_platform.values()]
            ability_counts = [data['abilities'] for data in by_platform.values()]
            success_counts = [data['success'] for data in by_platform.values()]
            
            x = np.arange(len(platforms))
            # Bar width for side-by-side charts (0.35 leaves spacing between bars)
            BAR_WIDTH = 0.35
            
            # Chart styling constants
            BAR_ALPHA = 0.8  # Bar transparency
            GRID_ALPHA = 0.3  # Grid line transparency
            
            # Agent distribution
            bars1 = ax1.bar(x, agent_counts, BAR_WIDTH,
                          color=self.COLORS['primary'], alpha=BAR_ALPHA)
            ax1.set_ylabel('Agent Count', fontweight='bold')
            ax1.set_title('Agents by Platform', fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(platforms, rotation=45, ha='right')
            ax1.grid(axis='y', alpha=GRID_ALPHA)            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}',
                            ha='center', va='bottom', fontweight='bold')
            
            # Ability distribution (successful vs total)
            bars2 = ax2.bar(x - BAR_WIDTH/2, ability_counts, BAR_WIDTH, 
                          label='Total', color=self.COLORS['neutral_300'], alpha=BAR_ALPHA)
            bars3 = ax2.bar(x + BAR_WIDTH/2, success_counts, BAR_WIDTH, 
                          label='Successful', color=self.COLORS['success'], alpha=BAR_ALPHA)
            
            ax2.set_ylabel('Ability Count', fontweight='bold')
            ax2.set_title('Abilities Executed by Platform', fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels(platforms, rotation=45, ha='right')
            ax2.legend(loc='upper right')
            ax2.grid(axis='y', alpha=0.3)
            
        plt.tight_layout()
        return self._save_or_encode(fig, output_path)
        
    def generate_technique_heatmap(
        self,
        statistics: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate heatmap of technique execution by tactic.
        
        Args:
            statistics: Campaign statistics
            output_path: Optional file path to save chart
            
        Returns:
            Base64 encoded PNG image or file path
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        by_tactic = statistics.get('by_tactic', {})
        
        if not by_tactic:
            ax.text(0.5, 0.5, 'No technique data available', 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
        else:
            tactics = list(by_tactic.keys())
            counts = [data['count'] for data in by_tactic.values()]
            success_rates = [
                (data['success'] / data['count'] * 100) if data['count'] > 0 else 0
                for data in by_tactic.values()
            ]
            
            # Create color map based on success rate
            colors = [self._get_success_color(rate) for rate in success_rates]
            
            bars = ax.barh(tactics, counts, color=colors, alpha=0.8)
            
            # Add success rate labels
            for i, (bar, rate) in enumerate(zip(bars, success_rates)):
                width = bar.get_width()
                if width > 0:
                    ax.text(width, bar.get_y() + bar.get_height()/2,
                           f' {rate:.0f}%',
                           va='center', fontweight='bold',
                           color=self.COLORS['dark'])
                    
            ax.set_xlabel('Technique Count', fontweight='bold')
            ax.set_title('Technique Execution by Tactic (with Success Rate)', 
                        fontweight='bold', pad=15)
            ax.grid(axis='x', alpha=0.3)
            
            # Add legend
            legend_elements = [
                mpatches.Patch(color=self.COLORS['success'], 
                             label='80-100% Success', alpha=0.8),
                mpatches.Patch(color=self.COLORS['warning'], 
                             label='50-80% Success', alpha=0.8),
                mpatches.Patch(color=self.COLORS['error'], 
                             label='<50% Success', alpha=0.8)
            ]
            ax.legend(handles=legend_elements, loc='lower right')
            
        plt.tight_layout()
        return self._save_or_encode(fig, output_path)
        
    def generate_timeline_chart(
        self,
        timeline: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate timeline visualization of campaign events.
        
        Args:
            timeline: List of timeline events
            output_path: Optional file path to save chart
            
        Returns:
            Base64 encoded PNG image or file path
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        if not timeline:
            ax.text(0.5, 0.5, 'No timeline data available', 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
        else:
            from datetime import datetime
            
            # Parse timestamps
            events = []
            for event in timeline:
                try:
                    ts = event['timestamp']
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    events.append({
                        'time': dt,
                        'event': event['event'],
                        'name': event.get('operation_name', 'Unknown')
                    })
                except:
                    continue
                    
            if not events:
                ax.text(0.5, 0.5, 'No valid timeline data', 
                       ha='center', va='center', fontsize=14)
                ax.axis('off')
            else:
                # Sort by time
                events.sort(key=lambda x: x['time'])
                
                # Group by event type
                start_events = [e for e in events if 'started' in e['event']]
                finish_events = [e for e in events if 'finished' in e['event']]
                
                # Plot start events
                if start_events:
                    times = [e['time'] for e in start_events]
                    y_pos = [1] * len(times)
                    ax.scatter(times, y_pos, c=self.COLORS['primary'], 
                             s=100, alpha=0.8, label='Operations Started', 
                             zorder=3, marker='^')
                    
                # Plot finish events
                if finish_events:
                    times = [e['time'] for e in finish_events]
                    y_pos = [0.5] * len(times)
                    ax.scatter(times, y_pos, c=self.COLORS['success'], 
                             s=100, alpha=0.8, label='Operations Finished', 
                             zorder=3, marker='v')
                    
                ax.set_ylim(0, 1.5)
                ax.set_yticks([])
                ax.set_xlabel('Time', fontweight='bold')
                ax.set_title('Campaign Timeline', fontweight='bold', pad=15)
                ax.legend(loc='upper right')
                ax.grid(axis='x', alpha=0.3)
                
                # Rotate x-axis labels
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                
        plt.tight_layout()
        return self._save_or_encode(fig, output_path)
        
    def generate_summary_dashboard(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive summary dashboard.
        
        Args:
            report_data: Complete report data
            output_path: Optional file path to save chart
            
        Returns:
            Base64 encoded PNG image or file path
        """
        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)
        
        summary = report_data.get('summary', {})
        statistics = report_data.get('statistics', {})
        
        # Title
        fig.suptitle(f"Campaign Dashboard: {report_data.get('campaign_id', 'Unknown')}", 
                    fontsize=16, fontweight='bold', y=0.98)
        
        # Top row: Key metrics
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_key_metrics(ax1, summary)
        
        # Middle row: Success rate and platform distribution
        ax2 = fig.add_subplot(gs[1, 0])
        self._plot_success_pie(ax2, summary)
        
        ax3 = fig.add_subplot(gs[1, 1:])
        self._plot_platform_bars(ax3, statistics)
        
        # Bottom row: Tactic distribution
        ax4 = fig.add_subplot(gs[2, :])
        self._plot_tactic_bars(ax4, statistics)
        
        plt.tight_layout()
        return self._save_or_encode(fig, output_path)
        
    def _plot_key_metrics(self, ax, summary: Dict):
        """Plot key metrics as text."""
        ax.axis('off')
        
        metrics = [
            ('Operations', summary.get('total_operations', 0)),
            ('Agents', summary.get('total_agents', 0)),
            ('Abilities Executed', summary.get('total_abilities_executed', 0)),
            ('Success Rate', f"{summary.get('success_rate', 0):.1f}%"),
            ('Duration', f"{summary.get('duration_hours', 0):.1f}h")
        ]
        
        x_positions = np.linspace(0.1, 0.9, len(metrics))
        
        for x, (label, value) in zip(x_positions, metrics):
            # Value
            ax.text(x, 0.6, str(value), ha='center', va='center',
                   fontsize=20, fontweight='bold', 
                   color=self.COLORS['primary'])
            # Label
            ax.text(x, 0.3, label, ha='center', va='center',
                   fontsize=10, color=self.COLORS['neutral_600'])
                   
    def _plot_success_pie(self, ax, summary: Dict):
        """Plot success rate pie chart."""
        successful = summary.get('successful_abilities', 0)
        failed = summary.get('failed_abilities', 0)
        
        if successful > 0 or failed > 0:
            sizes = [successful, failed]
            colors = [self.COLORS['success'], self.COLORS['error']]
            ax.pie(sizes, colors=colors, autopct='%1.1f%%', startangle=90,
                  textprops={'fontsize': 9, 'weight': 'bold', 'color': 'white'})
        ax.set_title('Success Rate', fontsize=11, fontweight='bold')
        
    def _plot_platform_bars(self, ax, statistics: Dict):
        """Plot platform distribution."""
        by_platform = statistics.get('by_platform', {})
        
        if by_platform:
            platforms = list(by_platform.keys())
            counts = [data['abilities'] for data in by_platform.values()]
            colors_list = [self.COLORS['primary']] * len(platforms)
            
            ax.barh(platforms, counts, color=colors_list, alpha=0.8)
            ax.set_xlabel('Abilities', fontsize=9)
            ax.set_title('Abilities by Platform', fontsize=11, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
    def _plot_tactic_bars(self, ax, statistics: Dict):
        """Plot tactic distribution."""
        by_tactic = statistics.get('by_tactic', {})
        
        if by_tactic:
            tactics = list(by_tactic.keys())
            counts = [data['count'] for data in by_tactic.values()]
            success_rates = [
                (data['success'] / data['count']) if data['count'] > 0 else 0
                for data in by_tactic.values()
            ]
            colors_list = [self._get_success_color(rate * 100) for rate in success_rates]
            
            ax.barh(tactics, counts, color=colors_list, alpha=0.8)
            ax.set_xlabel('Technique Count', fontsize=9)
            ax.set_title('Techniques by Tactic', fontsize=11, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
    def _get_success_color(self, success_rate: float) -> str:
        """Get color based on success rate."""
        if success_rate >= 80:
            return self.COLORS['success']
        elif success_rate >= 50:
            return self.COLORS['warning']
        else:
            return self.COLORS['error']
            
    def _save_or_encode(self, fig, output_path: Optional[str]) -> str:
        """Save figure to file or encode as base64."""
        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            return output_path
        else:
            # Encode as base64 for embedding in HTML
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            return f"data:image/png;base64,{image_base64}"
