"""
Enrollment API Plugin for CALDERA

Provides a REST API for dynamic agent enrollment, enabling CI/CD integration
and automated agent deployment workflows.
"""

from plugins.enrollment.app.enrollment_api import EnrollmentAPI


name = 'Enrollment'
description = 'Dynamic agent enrollment API for CI/CD integration'
address = None
access = None


async def enable(services):
    """
    Enable the Enrollment plugin by starting the enrollment API service.
    
    Args:
        services: Dictionary of CALDERA core services
    """
    app = services.get('app_svc').application
    enrollment_api = EnrollmentAPI(services)
    await enrollment_api.start()
    
    # Register API routes with the main application
    app.router.add_route('GET', '/plugin/enrollment/health', enrollment_api.health_check)
    app.router.add_route('POST', '/plugin/enrollment/enroll', enrollment_api.enroll_agent)
    app.router.add_route('GET', '/plugin/enrollment/enroll/{request_id}', enrollment_api.get_enrollment_status)
    app.router.add_route('GET', '/plugin/enrollment/requests', enrollment_api.list_enrollment_requests)
    app.router.add_route('GET', '/plugin/enrollment/campaigns/{campaign_id}/agents', enrollment_api.list_campaign_agents)
    
    # Store reference to service for cleanup
    services['enrollment_api'] = enrollment_api
    
    services.get('app_svc').get_logger().info('Enrollment plugin enabled with API endpoints')
