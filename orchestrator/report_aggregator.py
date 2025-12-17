"""
Report Aggregator for Caldera Campaigns

Collects and aggregates data from CALDERA operations, agents, abilities, and facts
to generate comprehensive campaign reports.
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

from .exceptions import (
    APIConnectionError,
    APIRequestError,
    CampaignNotFoundError,
    DataValidationError
)

# Configure logger
logger = logging.getLogger(__name__)


class ReportAggregator:
    """
    Aggregates campaign data from CALDERA REST API for report generation.
    """
    
    def __init__(self, caldera_url: str, api_key: str):
        """
        Initialize the report aggregator.
        
        Args:
            caldera_url: Base URL of CALDERA server (e.g., http://localhost:8888)
            api_key: API key for authentication
        """
        self.caldera_url = caldera_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={'KEY': self.api_key},
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def _get(self, endpoint: str) -> Any:
        """
        Make GET request to CALDERA API.
        
        Args:
            endpoint: API endpoint (e.g., /api/v2/operations)
            
        Returns:
            JSON response data
            
        Raises:
            APIConnectionError: If unable to connect to API
            APIRequestError: If API returns error status
        """
        url = f"{self.caldera_url}{endpoint}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    logger.error(f"API request failed: {response.status} {url}")
                    raise APIRequestError(
                        endpoint=endpoint,
                        status=response.status,
                        response_body=response_text
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to CALDERA API at {url}: {e}")
            raise APIConnectionError(url=url, reason=str(e))
        except Exception as e:
            if isinstance(e, (APIConnectionError, APIRequestError)):
                raise
            logger.error(f"Unexpected error during API request to {url}: {e}")
            raise APIConnectionError(url=url, reason=f"Unexpected error: {str(e)}")
                
    async def get_campaign_data(self, campaign_id: str) -> Dict[str, Any]:
        """
        Aggregate all campaign data.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary containing all aggregated campaign data
        """
        # Fetch all required data in parallel
        operations_task = self._get('/api/v2/operations')
        agents_task = self._get('/api/v2/agents')
        adversaries_task = self._get('/api/v2/adversaries')
        abilities_task = self._get('/api/v2/abilities')
        
        operations, agents, adversaries, abilities = await asyncio.gather(
            operations_task, agents_task, adversaries_task, abilities_task
        )
        
        # Filter operations for this campaign
        campaign_operations = [
            op for op in operations 
            if self._belongs_to_campaign(op, campaign_id)
        ]
        
        # Filter agents for this campaign
        campaign_agents = [
            agent for agent in agents
            if self._agent_in_campaign(agent, campaign_id)
        ]
        
        # Build comprehensive report data
        report_data = {
            'campaign_id': campaign_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': self._build_summary(campaign_operations, campaign_agents),
            'operations': await self._aggregate_operations(campaign_operations, abilities),
            'agents': self._aggregate_agents(campaign_agents),
            'techniques': self._aggregate_techniques(campaign_operations, abilities),
            'timeline': self._build_timeline(campaign_operations),
            'errors': self._collect_errors(campaign_operations),
            'statistics': self._calculate_statistics(campaign_operations, campaign_agents)
        }
        
        return report_data
        
    def _belongs_to_campaign(self, operation: Dict, campaign_id: str) -> bool:
        """Check if operation belongs to campaign."""
        # Check operation name or tags for campaign ID
        op_name = operation.get('name', '').lower()
        return campaign_id.lower() in op_name
        
    def _agent_in_campaign(self, agent: Dict, campaign_id: str) -> bool:
        """Check if agent is part of campaign."""
        # Check agent tags for campaign ID
        tags = agent.get('tags', [])
        for tag in tags:
            if f'campaign_id:{campaign_id}' in tag:
                return True
        return False
        
    def _build_summary(self, operations: List[Dict], agents: List[Dict]) -> Dict:
        """Build executive summary."""
        total_links = sum(len(op.get('chain', [])) for op in operations)
        successful_links = sum(
            len([link for link in op.get('chain', []) if link.get('status') == 0])
            for op in operations
        )
        
        return {
            'total_operations': len(operations),
            'total_agents': len(agents),
            'total_abilities_executed': total_links,
            'successful_abilities': successful_links,
            'failed_abilities': total_links - successful_links,
            'success_rate': (successful_links / total_links * 100) if total_links > 0 else 0,
            'platforms': list(set(agent.get('platform', 'unknown') for agent in agents)),
            'duration_hours': self._calculate_duration(operations)
        }
        
    async def _aggregate_operations(self, operations: List[Dict], abilities: Dict) -> List[Dict]:
        """Aggregate detailed operation data."""
        aggregated = []
        
        for op in operations:
            op_data = {
                'id': op.get('id'),
                'name': op.get('name'),
                'adversary': op.get('adversary', {}).get('name', 'Unknown'),
                'state': op.get('state', 'unknown'),
                'start_time': op.get('start'),
                'finish_time': op.get('finish'),
                'chain': self._process_chain(op.get('chain', []), abilities),
                'agent_count': len(op.get('agents', [])),
                'planner': op.get('planner', {}).get('name', 'Unknown')
            }
            aggregated.append(op_data)
            
        return aggregated
        
    def _process_chain(self, chain: List[Dict], abilities: Dict) -> List[Dict]:
        """Process operation chain with ability details."""
        processed = []
        
        for link in chain:
            ability_id = link.get('ability', {}).get('ability_id')
            
            processed.append({
                'id': link.get('id'),
                'ability_id': ability_id,
                'ability_name': link.get('ability', {}).get('name', 'Unknown'),
                'technique_id': link.get('ability', {}).get('technique_id'),
                'tactic': link.get('ability', {}).get('tactic', 'unknown'),
                'executor': link.get('executor', 'unknown'),
                'platform': link.get('platform', 'unknown'),
                'status': link.get('status', -1),
                'score': link.get('score', 0),
                'command': link.get('command', ''),
                'output': link.get('output', ''),
                'decide': link.get('decide'),
                'finish': link.get('finish')
            })
            
        return processed
        
    def _aggregate_agents(self, agents: List[Dict]) -> List[Dict]:
        """Aggregate agent information."""
        return [
            {
                'paw': agent.get('paw'),
                'hostname': agent.get('host'),
                'platform': agent.get('platform'),
                'architecture': agent.get('architecture'),
                'username': agent.get('username'),
                'group': agent.get('group'),
                'last_seen': agent.get('last_seen'),
                'created': agent.get('created'),
                'tags': agent.get('tags', [])
            }
            for agent in agents
        ]
        
    def _aggregate_techniques(self, operations: List[Dict], abilities: Dict) -> Dict:
        """Aggregate ATT&CK technique coverage."""
        technique_map = defaultdict(lambda: {'count': 0, 'success': 0, 'failed': 0, 'abilities': []})
        
        for op in operations:
            for link in op.get('chain', []):
                technique_id = link.get('ability', {}).get('technique_id')
                if technique_id:
                    technique_map[technique_id]['count'] += 1
                    technique_map[technique_id]['abilities'].append({
                        'name': link.get('ability', {}).get('name'),
                        'id': link.get('ability', {}).get('ability_id')
                    })
                    
                    if link.get('status') == 0:
                        technique_map[technique_id]['success'] += 1
                    else:
                        technique_map[technique_id]['failed'] += 1
                        
        return dict(technique_map)
        
    def _build_timeline(self, operations: List[Dict]) -> List[Dict]:
        """Build chronological timeline of events."""
        timeline = []
        
        for op in operations:
            # Operation start
            if op.get('start'):
                timeline.append({
                    'timestamp': op['start'],
                    'event': 'operation_started',
                    'operation_id': op['id'],
                    'operation_name': op['name']
                })
                
            # Operation finish
            if op.get('finish'):
                timeline.append({
                    'timestamp': op['finish'],
                    'event': 'operation_finished',
                    'operation_id': op['id'],
                    'operation_name': op['name'],
                    'state': op.get('state')
                })
                
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline
        
    def _collect_errors(self, operations: List[Dict]) -> List[Dict]:
        """Collect all errors and failures."""
        errors = []
        
        for op in operations:
            for link in op.get('chain', []):
                if link.get('status') != 0:  # Failed link
                    errors.append({
                        'operation_id': op['id'],
                        'operation_name': op['name'],
                        'ability': link.get('ability', {}).get('name'),
                        'ability_id': link.get('ability', {}).get('ability_id'),
                        'technique_id': link.get('ability', {}).get('technique_id'),
                        'platform': link.get('platform'),
                        'status_code': link.get('status'),
                        'timestamp': link.get('finish'),
                        'command': link.get('command', ''),
                        'output': link.get('output', '')[:500]  # Truncate long output
                    })
                    
        return errors
        
    def _calculate_statistics(self, operations: List[Dict], agents: List[Dict]) -> Dict:
        """Calculate detailed statistics."""
        stats = {
            'by_platform': defaultdict(lambda: {'agents': 0, 'abilities': 0, 'success': 0}),
            'by_tactic': defaultdict(lambda: {'count': 0, 'success': 0}),
            'by_technique': defaultdict(lambda: {'count': 0, 'success': 0})
        }
        
        # Platform statistics
        for agent in agents:
            platform = agent.get('platform', 'unknown')
            stats['by_platform'][platform]['agents'] += 1
            
        # Ability and technique statistics
        for op in operations:
            for link in op.get('chain', []):
                platform = link.get('platform', 'unknown')
                tactic = link.get('ability', {}).get('tactic', 'unknown')
                technique = link.get('ability', {}).get('technique_id', 'unknown')
                
                stats['by_platform'][platform]['abilities'] += 1
                if link.get('status') == 0:
                    stats['by_platform'][platform]['success'] += 1
                    
                stats['by_tactic'][tactic]['count'] += 1
                if link.get('status') == 0:
                    stats['by_tactic'][tactic]['success'] += 1
                    
                stats['by_technique'][technique]['count'] += 1
                if link.get('status') == 0:
                    stats['by_technique'][technique]['success'] += 1
                    
        return {
            'by_platform': dict(stats['by_platform']),
            'by_tactic': dict(stats['by_tactic']),
            'by_technique': dict(stats['by_technique'])
        }
        
    def _calculate_duration(self, operations: List[Dict]) -> float:
        """Calculate total campaign duration in hours."""
        if not operations:
            return 0
            
        start_times = [op.get('start') for op in operations if op.get('start')]
        finish_times = [op.get('finish') for op in operations if op.get('finish')]
        
        if not start_times or not finish_times:
            return 0
            
        earliest = min(start_times)
        latest = max(finish_times)
        
        try:
            start_dt = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
            finish_dt = datetime.fromisoformat(latest.replace('Z', '+00:00'))
            duration = (finish_dt - start_dt).total_seconds() / 3600
            return round(duration, 2)
        except:
            return 0
