"""
Enrollment API - REST endpoints following CALDERA patterns
"""

from aiohttp import web
import json
from typing import Optional


class EnrollmentAPI:
    """
    REST API endpoints for agent enrollment.
    
    Provides consistent JSON responses and error handling following
    CALDERA's REST API patterns.
    """
    
    def __init__(self, services):
        """
        Initialize API with enrollment service.
        
        Args:
            services: CALDERA core services dictionary
        """
        from plugins.enrollment.app.enrollment_svc import EnrollmentService
        
        self.services = services
        self.log = services.get('app_svc').get_logger()
        self.enrollment_svc = EnrollmentService(services)
    
    async def start(self):
        """Start the enrollment API service."""
        self.log.info('Enrollment API started')
    
    async def health_check(self, request):
        """
        Health check endpoint.
        
        GET /plugin/enrollment/health
        
        Returns:
            JSON response with service status
        """
        return web.json_response({
            'status': 'healthy',
            'service': 'enrollment',
            'caldera_url': self.enrollment_svc.caldera_url,
            'storage_path': str(self.enrollment_svc.storage_path),
            'total_requests': len(self.enrollment_svc.enrollment_requests)
        })
    
    async def enroll_agent(self, request):
        """
        Create new agent enrollment request.
        
        POST /plugin/enrollment/enroll
        
        Request body:
        {
            "platform": "linux|windows|darwin",
            "campaign_id": "optional-campaign-uuid",
            "tags": ["optional", "tags"],
            "contact": "http",
            "hostname": "optional-hostname"
        }
        
        Returns:
            JSON response with enrollment instructions
        """
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON in request body'},
                status=400
            )
        
        # Validate required fields
        platform = data.get('platform')
        if not platform:
            return web.json_response(
                {'error': 'Missing required field: platform'},
                status=400
            )
        
        if platform not in ['windows', 'linux', 'darwin']:
            return web.json_response(
                {'error': f'Invalid platform: {platform}. Must be windows, linux, or darwin'},
                status=400
            )
        
        # Extract optional fields
        campaign_id = data.get('campaign_id')
        tags = data.get('tags', [])
        contact = data.get('contact', 'http')
        hostname = data.get('hostname')
        
        # Create enrollment request
        try:
            enrollment = self.enrollment_svc.create_enrollment_request(
                platform=platform,
                campaign_id=campaign_id,
                tags=tags,
                contact=contact,
                hostname=hostname
            )
            
            self.log.info(f'Enrollment request created: {enrollment["request_id"]}')
            
            return web.json_response(enrollment, status=201)
        
        except Exception as e:
            self.log.error(f'Error creating enrollment: {e}')
            return web.json_response(
                {'error': f'Failed to create enrollment: {str(e)}'},
                status=500
            )
    
    async def get_enrollment_status(self, request):
        """
        Get enrollment request status.
        
        GET /plugin/enrollment/enroll/{request_id}
        
        Returns:
            JSON response with enrollment details
        """
        request_id = request.match_info.get('request_id')
        
        enrollment = self.enrollment_svc.get_enrollment_request(request_id)
        
        if not enrollment:
            return web.json_response(
                {'error': f'Enrollment request not found: {request_id}'},
                status=404
            )
        
        return web.json_response(enrollment)
    
    async def list_enrollment_requests(self, request):
        """
        List enrollment requests with optional filters.
        
        GET /plugin/enrollment/requests?campaign_id=xxx&platform=linux&status=pending&limit=50
        
        Returns:
            JSON response with list of enrollment requests
        """
        # Parse query parameters
        campaign_id = request.query.get('campaign_id')
        platform = request.query.get('platform')
        status = request.query.get('status')
        
        try:
            limit = int(request.query.get('limit', 100))
        except ValueError:
            limit = 100
        
        # Get filtered results
        results = self.enrollment_svc.list_enrollment_requests(
            campaign_id=campaign_id,
            platform=platform,
            status=status,
            limit=limit
        )
        
        return web.json_response({
            'total': len(results),
            'limit': limit,
            'requests': results
        })
    
    async def list_campaign_agents(self, request):
        """
        List all agents enrolled for a campaign.
        
        GET /plugin/enrollment/campaigns/{campaign_id}/agents
        
        Returns:
            JSON response with campaign agents
        """
        campaign_id = request.match_info.get('campaign_id')
        
        try:
            agents = await self.enrollment_svc.get_campaign_agents(campaign_id)
            
            return web.json_response({
                'campaign_id': campaign_id,
                'total_agents': len(agents),
                'agents': agents
            })
        
        except Exception as e:
            self.log.error(f'Error fetching campaign agents: {e}')
            return web.json_response(
                {'error': f'Failed to fetch campaign agents: {str(e)}'},
                status=500
            )
