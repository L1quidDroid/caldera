"""Campaign object for managing multi-operation orchestration."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.utility.base_object import BaseObject


class Campaign(BaseObject):
    """
    Represents a multi-phase adversary emulation campaign.
    
    A campaign orchestrates multiple operations, agent enrollments,
    SIEM integration, notifications, and reporting across phases.
    """

    @property
    def unique(self):
        return self.hash(f"{self.campaign_id}")

    @property
    def display(self):
        return {
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'environment': self.environment,
            'mode': self.mode,
            'targets': self.targets,
            'adversary': self.adversary,
            'siem': self.siem,
            'notifications': self.notifications,
            'governance': self.governance,
            'state': self.state,
            'reporting': self.reporting,
            'metadata': self.metadata
        }

    @property
    def schema(self):
        return {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'title': 'Campaign',
            'type': 'object',
            'required': ['campaign_id', 'name', 'environment', 'mode'],
            'properties': {
                'campaign_id': {'type': 'string'},
                'name': {'type': 'string'},
                'description': {'type': 'string'},
                'environment': {'type': 'object'},
                'mode': {'type': 'string', 'enum': ['test', 'production', 'simulation', 'validation']},
                'targets': {'type': 'object'},
                'adversary': {'type': 'object'},
                'siem': {'type': 'object'},
                'notifications': {'type': 'object'},
                'governance': {'type': 'object'},
                'state': {'type': 'object'},
                'reporting': {'type': 'object'},
                'metadata': {'type': 'object'}
            }
        }

    def __init__(
        self,
        campaign_id: Optional[str] = None,
        name: str = None,
        description: str = None,
        environment: Dict = None,
        mode: str = 'test',
        targets: Dict = None,
        adversary: Dict = None,
        siem: Dict = None,
        notifications: Dict = None,
        governance: Dict = None,
        state: Dict = None,
        reporting: Dict = None,
        metadata: Dict = None
    ):
        super().__init__()
        self.campaign_id = campaign_id or str(uuid.uuid4())
        self.name = name
        self.description = description or ''
        self.environment = environment or {}
        self.mode = mode
        self.targets = targets or {}
        self.adversary = adversary or {}
        self.siem = siem or {'enabled': False}
        self.notifications = notifications or {}
        self.governance = governance or {}
        self.state = state or self._initialize_state()
        self.reporting = reporting or {
            'formats': ['json', 'pdf'],
            'include_output': False,
            'include_facts': True,
            'attack_navigator': True
        }
        self.metadata = metadata or self._initialize_metadata()

    def _initialize_state(self) -> Dict:
        """Initialize default state structure."""
        return {
            'status': 'created',
            'current_phase': 1,
            'operations': [],
            'agents_enrolled': [],
            'reports': {},
            'errors': [],
            'timeline': [
                {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'event': 'campaign_created',
                    'details': {}
                }
            ]
        }

    def _initialize_metadata(self) -> Dict:
        """Initialize default metadata structure."""
        now = datetime.utcnow().isoformat() + 'Z'
        return {
            'created_at': now,
            'updated_at': now,
            'created_by': 'orchestrator',
            'version': '1.0.0',
            'tags': [],
            'custom_fields': {}
        }

    def update_status(self, status: str, details: Optional[Dict] = None):
        """
        Update campaign status and log to timeline.
        
        Args:
            status: New status from valid state enum
            details: Optional details about the status change
        """
        valid_statuses = [
            'created', 'infrastructure_provisioning', 'infrastructure_ready',
            'agents_enrolling', 'agents_ready', 'operation_queued',
            'operation_running', 'operation_paused', 'operation_completed',
            'siem_tagging', 'reporting', 'pdf_ready', 'completed',
            'failed', 'cancelled'
        ]
        
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        self.state['status'] = status
        self.metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        self.add_timeline_event(
            event=f'status_changed_{status}',
            details=details or {'status': status}
        )

    def add_timeline_event(self, event: str, details: Optional[Dict] = None):
        """Add event to campaign timeline."""
        self.state['timeline'].append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event': event,
            'details': details or {}
        })
        self.metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'

    def add_operation(self, operation_id: str, name: str, status: str = 'queued'):
        """Add operation to campaign state."""
        self.state['operations'].append({
            'operation_id': operation_id,
            'name': name,
            'status': status,
            'start_time': None,
            'finish_time': None,
            'links_completed': 0,
            'links_failed': 0,
            'report_path': None
        })
        self.add_timeline_event(
            event='operation_added',
            details={'operation_id': operation_id, 'name': name}
        )

    def update_operation(self, operation_id: str, updates: Dict):
        """Update operation status in campaign state."""
        for op in self.state['operations']:
            if op['operation_id'] == operation_id:
                op.update(updates)
                self.metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                break

    def add_agent(self, paw: str, hostname: str, platform: str):
        """Add enrolled agent to campaign state."""
        self.state['agents_enrolled'].append({
            'paw': paw,
            'hostname': hostname,
            'platform': platform,
            'enrolled_at': datetime.utcnow().isoformat() + 'Z'
        })
        self.add_timeline_event(
            event='agent_enrolled',
            details={'paw': paw, 'hostname': hostname, 'platform': platform}
        )

    def add_error(self, phase: str, message: str, severity: str = 'error'):
        """Log error to campaign state."""
        self.state['errors'].append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'phase': phase,
            'message': message,
            'severity': severity
        })
        self.metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'

    def set_reports(self, json_path: str = None, pdf_path: str = None, csv_path: str = None):
        """Set report paths in campaign state."""
        self.state['reports'] = {
            'json_path': json_path,
            'pdf_path': pdf_path,
            'csv_path': csv_path,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
        self.add_timeline_event(
            event='reports_generated',
            details={'paths': self.state['reports']}
        )

    def get_operation_ids(self) -> List[str]:
        """Get list of all operation IDs in campaign."""
        return [op['operation_id'] for op in self.state['operations']]

    def get_agent_paws(self) -> List[str]:
        """Get list of all enrolled agent PAWs."""
        return [agent['paw'] for agent in self.state['agents_enrolled']]

    def is_completed(self) -> bool:
        """Check if campaign is in completed state."""
        return self.state['status'] in ['completed', 'failed', 'cancelled']

    def get_duration_hours(self) -> Optional[float]:
        """Calculate campaign duration in hours."""
        if not self.state['timeline']:
            return None
        
        start_time = datetime.fromisoformat(
            self.state['timeline'][0]['timestamp'].replace('Z', '+00:00')
        )
        
        if self.is_completed():
            end_time = datetime.fromisoformat(
                self.state['timeline'][-1]['timestamp'].replace('Z', '+00:00')
            )
        else:
            end_time = datetime.utcnow()
        
        duration = end_time - start_time
        return duration.total_seconds() / 3600

    def store(self, ram):
        """Store campaign in data service RAM."""
        if 'campaigns' not in ram:
            ram['campaigns'] = []
        
        existing = [c for c in ram['campaigns'] if c.campaign_id == self.campaign_id]
        if existing:
            ram['campaigns'].remove(existing[0])
        
        ram['campaigns'].append(self)
