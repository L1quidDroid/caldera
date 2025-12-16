"""
Enrollment Service - Core enrollment logic with JSON-based persistence
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from aiohttp import web


class EnrollmentService:
    """
    Manages agent enrollment requests with JSON-based storage.
    
    Provides:
    - Enrollment request tracking
    - Campaign association
    - Platform-specific bootstrap generation
    - Persistent storage to JSON file
    """
    
    def __init__(self, services: Dict, storage_path: Optional[str] = None):
        """
        Initialize enrollment service.
        
        Args:
            services: CALDERA core services dictionary
            storage_path: Path to JSON storage file (defaults to data/enrollment_requests.json)
        """
        self.services = services
        self.data_svc = services.get('data_svc')
        self.log = services.get('app_svc').get_logger()
        
        # Set storage path with fallback
        if storage_path is None:
            plugin_dir = Path(__file__).parent.parent
            self.storage_path = plugin_dir / 'data' / 'enrollment_requests.json'
        else:
            self.storage_path = Path(storage_path)
        
        # Ensure data directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of enrollment requests
        self.enrollment_requests: Dict[str, Dict] = {}
        
        # Load from disk
        self._load_from_disk()
        
        # Get Caldera URL from environment with localhost fallback
        self.caldera_url = os.getenv('CALDERA_URL', 'http://localhost:8888')
        
        self.log.info(f'Enrollment service initialized with storage at {self.storage_path}')
        self.log.info(f'Using Caldera URL: {self.caldera_url}')
    
    def _load_from_disk(self):
        """Load enrollment requests from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.enrollment_requests = json.load(f)
                self.log.info(f'Loaded {len(self.enrollment_requests)} enrollment requests from disk')
            except Exception as e:
                self.log.error(f'Error loading enrollment requests: {e}')
                self.enrollment_requests = {}
        else:
            self.log.info('No existing enrollment data found, starting fresh')
    
    def _save_to_disk(self):
        """Persist enrollment requests to JSON file."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.enrollment_requests, f, indent=2)
            self.log.debug(f'Saved {len(self.enrollment_requests)} enrollment requests to disk')
        except Exception as e:
            self.log.error(f'Error saving enrollment requests: {e}')
    
    def create_enrollment_request(
        self,
        platform: str,
        campaign_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        contact: str = 'http',
        hostname: Optional[str] = None
    ) -> Dict:
        """
        Create a new enrollment request.
        
        Args:
            platform: Target platform (windows, linux, darwin)
            campaign_id: Optional campaign ID for tracking
            tags: Optional list of agent tags
            contact: Contact method (default: http)
            hostname: Optional hostname for the agent
        
        Returns:
            Enrollment request dictionary with instructions
        """
        request_id = str(uuid.uuid4())
        
        # Generate platform-specific bootstrap command
        bootstrap_cmd = self._generate_bootstrap_command(
            platform=platform,
            campaign_id=campaign_id,
            tags=tags,
            contact=contact
        )
        
        # Create enrollment record
        enrollment = {
            'request_id': request_id,
            'platform': platform,
            'campaign_id': campaign_id,
            'tags': tags or [],
            'contact': contact,
            'hostname': hostname,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'bootstrap_command': bootstrap_cmd,
            'agent_download_url': f'{self.caldera_url}/file/download',
            'caldera_url': self.caldera_url
        }
        
        # Store and persist
        self.enrollment_requests[request_id] = enrollment
        self._save_to_disk()
        
        self.log.info(f'Created enrollment request {request_id} for platform={platform}, campaign={campaign_id}')
        
        return enrollment
    
    def _generate_bootstrap_command(
        self,
        platform: str,
        campaign_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        contact: str = 'http'
    ) -> str:
        """
        Generate platform-specific bootstrap command.
        
        Args:
            platform: Target platform
            campaign_id: Optional campaign ID
            tags: Optional agent tags
            contact: Contact method
        
        Returns:
            Bootstrap command string
        """
        # Build tag string
        tag_list = tags or []
        if campaign_id:
            tag_list.append(f'campaign:{campaign_id}')
        tag_str = ','.join(tag_list) if tag_list else ''
        
        if platform == 'windows':
            cmd = f'$url="{self.caldera_url}/file/download"; '
            cmd += '$output="sandcat.exe"; '
            cmd += 'Invoke-WebRequest -Uri $url -OutFile $output; '
            cmd += f'.\\sandcat.exe -server {self.caldera_url} -group red'
            if tag_str:
                cmd += f' -tags {tag_str}'
            return cmd
        
        elif platform in ['linux', 'darwin']:
            cmd = f'curl -sk {self.caldera_url}/file/download -o sandcat.go && '
            cmd += 'chmod +x sandcat.go && '
            cmd += f'./sandcat.go -server {self.caldera_url} -group red'
            if tag_str:
                cmd += f' -tags {tag_str}'
            cmd += ' &'
            return cmd
        
        else:
            return f'# Unsupported platform: {platform}'
    
    def get_enrollment_request(self, request_id: str) -> Optional[Dict]:
        """
        Retrieve enrollment request by ID.
        
        Args:
            request_id: Enrollment request UUID
        
        Returns:
            Enrollment request dictionary or None if not found
        """
        return self.enrollment_requests.get(request_id)
    
    def list_enrollment_requests(
        self,
        campaign_id: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        List enrollment requests with optional filters.
        
        Args:
            campaign_id: Filter by campaign ID
            platform: Filter by platform
            status: Filter by status
            limit: Maximum number of results
        
        Returns:
            List of enrollment request dictionaries
        """
        results = list(self.enrollment_requests.values())
        
        # Apply filters
        if campaign_id:
            results = [r for r in results if r.get('campaign_id') == campaign_id]
        if platform:
            results = [r for r in results if r.get('platform') == platform]
        if status:
            results = [r for r in results if r.get('status') == status]
        
        # Sort by created_at descending
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Limit results
        return results[:limit]
    
    def update_enrollment_status(self, request_id: str, status: str, agent_paw: Optional[str] = None):
        """
        Update enrollment request status.
        
        Args:
            request_id: Enrollment request UUID
            status: New status (pending, connected, failed)
            agent_paw: Optional agent PAW if connected
        """
        if request_id in self.enrollment_requests:
            self.enrollment_requests[request_id]['status'] = status
            self.enrollment_requests[request_id]['updated_at'] = datetime.utcnow().isoformat()
            
            if agent_paw:
                self.enrollment_requests[request_id]['agent_paw'] = agent_paw
            
            self._save_to_disk()
            self.log.info(f'Updated enrollment {request_id} status to {status}')
    
    async def get_campaign_agents(self, campaign_id: str) -> List[Dict]:
        """
        Get all agents associated with a campaign.
        
        Args:
            campaign_id: Campaign UUID
        
        Returns:
            List of agent dictionaries
        """
        # Get all agents from Caldera
        agents = await self.data_svc.locate('agents')
        
        # Filter by campaign tag
        campaign_agents = []
        for agent in agents:
            agent_tags = getattr(agent, 'tags', [])
            if f'campaign:{campaign_id}' in agent_tags:
                campaign_agents.append({
                    'paw': agent.paw,
                    'hostname': agent.hostname,
                    'platform': agent.platform,
                    'group': agent.group,
                    'tags': agent_tags,
                    'last_seen': agent.last_seen.isoformat() if agent.last_seen else None
                })
        
        return campaign_agents
