"""
ATT&CK Navigator Layer Generator for Caldera Campaigns

Generates MITRE ATT&CK Navigator layer JSON files from campaign execution data.
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class AttackNavigatorGenerator:
    """
    Generates ATT&CK Navigator layer files from campaign technique coverage.
    """
    
    # Color scheme for technique status
    COLORS = {
        'success': '#48CFA0',      # Triskele green for successful techniques
        'failed': '#EF4444',        # Red for failed techniques
        'partial': '#F59E0B',       # Amber for partially successful
        'not_executed': '#E5E7EB'   # Light gray for not executed
    }
    
    def __init__(self):
        """Initialize the ATT&CK Navigator generator."""
        self.version = '4.9'  # ATT&CK Navigator layer format version
        
    def generate_layer(
        self,
        campaign_id: str,
        campaign_name: str,
        techniques: Dict[str, Any],
        operations: List[Dict],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate ATT&CK Navigator layer JSON.
        
        Args:
            campaign_id: Campaign identifier
            campaign_name: Human-readable campaign name
            techniques: Technique execution data from report aggregator
            operations: List of operations in campaign
            metadata: Optional metadata (agent count, duration, etc.)
            
        Returns:
            ATT&CK Navigator layer JSON as dictionary
        """
        # Build technique list with colors and metadata
        technique_list = []
        
        for technique_id, data in techniques.items():
            if not technique_id or technique_id == 'unknown':
                continue
                
            # Determine color based on success rate
            success_rate = data['success'] / data['count'] if data['count'] > 0 else 0
            
            if success_rate == 1.0:
                color = self.COLORS['success']
                comment = f"✅ All {data['count']} executions successful"
            elif success_rate > 0:
                color = self.COLORS['partial']
                comment = f"⚠️ {data['success']}/{data['count']} executions successful"
            else:
                color = self.COLORS['failed']
                comment = f"❌ All {data['count']} executions failed"
                
            technique_list.append({
                'techniqueID': technique_id,
                'color': color,
                'comment': comment,
                'enabled': True,
                'score': data['success'],
                'metadata': [
                    {
                        'name': 'Executions',
                        'value': str(data['count'])
                    },
                    {
                        'name': 'Success Rate',
                        'value': f"{success_rate * 100:.1f}%"
                    },
                    {
                        'name': 'Abilities',
                        'value': ', '.join([ab['name'] for ab in data['abilities'][:3]])
                    }
                ]
            })
            
        # Build layer structure
        layer = {
            'name': f"{campaign_name} - Technique Coverage",
            'versions': {
                'attack': '14',  # ATT&CK v14
                'navigator': self.version,
                'layer': '4.5'
            },
            'domain': 'enterprise-attack',
            'description': self._build_description(campaign_id, metadata),
            'filters': {
                'platforms': self._extract_platforms(operations)
            },
            'sorting': 0,
            'layout': {
                'layout': 'side',
                'aggregateFunction': 'average',
                'showID': True,
                'showName': True,
                'showAggregateScores': False,
                'countUnscored': False
            },
            'hideDisabled': False,
            'techniques': technique_list,
            'gradient': {
                'colors': [
                    self.COLORS['failed'],
                    self.COLORS['partial'],
                    self.COLORS['success']
                ],
                'minValue': 0,
                'maxValue': 100
            },
            'legendItems': [
                {
                    'label': 'Fully Successful',
                    'color': self.COLORS['success']
                },
                {
                    'label': 'Partially Successful',
                    'color': self.COLORS['partial']
                },
                {
                    'label': 'Failed',
                    'color': self.COLORS['failed']
                }
            ],
            'metadata': [
                {
                    'name': 'Campaign ID',
                    'value': campaign_id
                },
                {
                    'name': 'Generated',
                    'value': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
                },
                {
                    'name': 'Generator',
                    'value': 'Caldera Orchestrator - Triskele Labs'
                }
            ],
            'showTacticRowBackground': True,
            'tacticRowBackground': '#020816',  # Triskele dark blue
            'selectTechniquesAcrossTactics': True
        }
        
        # Add optional metadata
        if metadata:
            if 'agent_count' in metadata:
                layer['metadata'].append({
                    'name': 'Agents',
                    'value': str(metadata['agent_count'])
                })
            if 'duration_hours' in metadata:
                layer['metadata'].append({
                    'name': 'Duration',
                    'value': f"{metadata['duration_hours']:.1f} hours"
                })
            if 'operations_count' in metadata:
                layer['metadata'].append({
                    'name': 'Operations',
                    'value': str(metadata['operations_count'])
                })
                
        return layer
        
    def _build_description(self, campaign_id: str, metadata: Dict[str, Any]) -> str:
        """Build layer description text."""
        description_parts = [
            f"ATT&CK technique coverage for campaign: {campaign_id}",
            "",
            "This layer visualizes the MITRE ATT&CK techniques executed during the campaign.",
            ""
        ]
        
        if metadata:
            description_parts.append("Campaign Summary:")
            if 'agent_count' in metadata:
                description_parts.append(f"- {metadata['agent_count']} agents deployed")
            if 'operations_count' in metadata:
                description_parts.append(f"- {metadata['operations_count']} operations executed")
            if 'total_abilities' in metadata:
                description_parts.append(f"- {metadata['total_abilities']} abilities run")
            if 'success_rate' in metadata:
                description_parts.append(f"- {metadata['success_rate']:.1f}% success rate")
                
        description_parts.extend([
            "",
            "Color Legend:",
            f"🟢 Green ({self.COLORS['success']}): All executions successful",
            f"🟠 Amber ({self.COLORS['partial']}): Partially successful",
            f"🔴 Red ({self.COLORS['failed']}): All executions failed",
            "",
            "Generated by Caldera Global Orchestration (Triskele Labs)"
        ])
        
        return "\n".join(description_parts)
        
    def _extract_platforms(self, operations: List[Dict]) -> List[str]:
        """Extract unique platforms from operations."""
        platforms = set()
        
        for op in operations:
            for link in op.get('chain', []):
                platform = link.get('platform', '').lower()
                if platform:
                    # Map CALDERA platforms to ATT&CK platforms
                    if platform == 'darwin':
                        platforms.add('macOS')
                    elif platform in ['windows', 'linux']:
                        platforms.add(platform.capitalize())
                        
        return sorted(list(platforms))
        
    def save_layer(self, layer: Dict[str, Any], output_path: str):
        """
        Save layer to JSON file.
        
        Args:
            layer: Layer dictionary
            output_path: Output file path
        """
        with open(output_path, 'w') as f:
            json.dump(layer, f, indent=2)
            
    def generate_comparison_layer(
        self,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a comparison layer showing multiple campaigns.
        
        Args:
            campaigns: List of campaign data dictionaries with techniques
            
        Returns:
            ATT&CK Navigator layer comparing campaigns
        """
        # Collect all unique techniques across campaigns
        all_techniques = {}
        
        for campaign in campaigns:
            campaign_id = campaign['campaign_id']
            techniques = campaign['techniques']
            
            for tech_id, data in techniques.items():
                if tech_id not in all_techniques:
                    all_techniques[tech_id] = {
                        'campaigns': [],
                        'total_count': 0,
                        'total_success': 0
                    }
                    
                all_techniques[tech_id]['campaigns'].append({
                    'id': campaign_id,
                    'name': campaign.get('name', campaign_id),
                    'count': data['count'],
                    'success': data['success']
                })
                all_techniques[tech_id]['total_count'] += data['count']
                all_techniques[tech_id]['total_success'] += data['success']
                
        # Build comparison layer
        technique_list = []
        
        for tech_id, data in all_techniques.items():
            if not tech_id or tech_id == 'unknown':
                continue
                
            avg_success_rate = data['total_success'] / data['total_count'] if data['total_count'] > 0 else 0
            
            if avg_success_rate >= 0.8:
                color = self.COLORS['success']
            elif avg_success_rate >= 0.5:
                color = self.COLORS['partial']
            else:
                color = self.COLORS['failed']
                
            campaign_summary = ", ".join([
                f"{c['name']}({c['success']}/{c['count']})"
                for c in data['campaigns']
            ])
            
            technique_list.append({
                'techniqueID': tech_id,
                'color': color,
                'comment': f"Executed across {len(data['campaigns'])} campaigns: {campaign_summary}",
                'enabled': True,
                'score': data['total_success'],
                'metadata': [
                    {
                        'name': 'Total Executions',
                        'value': str(data['total_count'])
                    },
                    {
                        'name': 'Average Success Rate',
                        'value': f"{avg_success_rate * 100:.1f}%"
                    },
                    {
                        'name': 'Campaigns',
                        'value': str(len(data['campaigns']))
                    }
                ]
            })
            
        layer = {
            'name': f"Campaign Comparison - {len(campaigns)} Campaigns",
            'versions': {
                'attack': '14',
                'navigator': self.version,
                'layer': '4.5'
            },
            'domain': 'enterprise-attack',
            'description': f"Comparison of technique coverage across {len(campaigns)} campaigns",
            'techniques': technique_list,
            'gradient': {
                'colors': [
                    self.COLORS['failed'],
                    self.COLORS['partial'],
                    self.COLORS['success']
                ],
                'minValue': 0,
                'maxValue': 100
            },
            'legendItems': [
                {
                    'label': 'High Success (80%+)',
                    'color': self.COLORS['success']
                },
                {
                    'label': 'Medium Success (50-80%)',
                    'color': self.COLORS['partial']
                },
                {
                    'label': 'Low Success (<50%)',
                    'color': self.COLORS['failed']
                }
            ],
            'metadata': [
                {
                    'name': 'Campaign Count',
                    'value': str(len(campaigns))
                },
                {
                    'name': 'Generated',
                    'value': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
                },
                {
                    'name': 'Generator',
                    'value': 'Caldera Orchestrator - Triskele Labs'
                }
            ]
        }
        
        return layer
