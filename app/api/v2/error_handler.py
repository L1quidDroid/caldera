"""
Enhanced Error Handler with Actionable Troubleshooting Tips
Provides user-friendly error messages with specific guidance for common issues
"""
import json
import logging
import traceback
from aiohttp import web

logger = logging.getLogger('error_handler')

# Error code to troubleshooting tips mapping
ERROR_TIPS = {
    401: [
        "💡 Check your API key in the request header: KEY: ADMIN123",
        "💡 Verify conf/default.yml has correct api_key_red/api_key_blue values",
        "💡 Try logging in via web UI first: http://localhost:8888",
        "💡 For session auth, ensure cookies are enabled in your client"
    ],
    403: [
        "💡 Your account lacks permissions for this operation",
        "💡 Check conf/default.yml user group assignments (red vs blue teams)",
        "💡 Try using the RED API key (api_key_red) for admin operations",
        "💡 Verify your user is in the correct permission group"
    ],
    404: [
        "💡 Double-check the resource ID/name in your request",
        "💡 List available resources: GET /api/v2/{resource_type}",
        "💡 Some resources only appear after server restart",
        "💡 Verify the resource hasn't been deleted"
    ],
    500: [
        "💡 Check server logs: tail -f logs/caldera.log",
        "💡 Verify all plugins started: GET /api/v2/plugins",
        "💡 Try restarting server: python server.py --insecure",
        "💡 Run dependency check: python scripts/check_dependencies.py"
    ],
    503: [
        "💡 Server is starting up - wait 30 seconds and try again",
        "💡 Check if all plugins loaded: GET /api/v2/health",
        "💡 Review server startup logs for plugin errors",
        "💡 Verify database is accessible and not corrupted"
    ]
}

# Context-specific error tips
CONTEXT_TIPS = {
    'connection_refused': [
        "💡 Is the server running? python server.py --insecure",
        "💡 Check the port: netstat -an | grep 8888",
        "💡 Review server startup logs for errors",
        "💡 Verify no firewall blocking localhost:8888"
    ],
    'plugin_load_error': [
        "💡 Missing dependencies? Run: python scripts/check_dependencies.py",
        "💡 Disable problematic plugins in conf/default.yml",
        "💡 Check plugin README for specific requirements",
        "💡 Install optional dependencies: pip install -r requirements-optional.txt"
    ],
    'agent_unreachable': [
        "💡 Agent may be blocked by firewall/antivirus",
        "💡 Check beacon interval: agent may be sleeping",
        "💡 Verify network connectivity to C2 server",
        "💡 Review agent logs on target system",
        "💡 Confirm agent platform matches ability requirements"
    ],
    'operation_failed': [
        "💡 Check agent status: GET /api/v2/agents",
        "💡 Review operation logs for specific ability failures",
        "💡 Verify target platform matches ability requirements",
        "💡 Check agent output: include --include-output flag",
        "💡 Ensure agents are trusted: set trusted=1 if needed"
    ],
    'campaign_error': [
        "💡 Validate campaign YAML syntax",
        "💡 Check campaign exists: python orchestrator/cli.py campaign list",
        "💡 Verify campaign file in data/campaigns/",
        "💡 Review campaign schema: schemas/campaign_spec.schema.json"
    ],
    'enrollment_error': [
        "💡 Check enrollment plugin is enabled in conf/default.yml",
        "💡 Test enrollment API health: GET /plugin/enrollment/health",
        "💡 Verify bootstrap script syntax (PowerShell/Bash)",
        "💡 Check target can reach C2 server on port 8888"
    ]
}


def get_tips_for_error(status_code: int, error_message: str = "", request_path: str = "") -> list:
    """
    Get contextual troubleshooting tips based on error details.
    
    Args:
        status_code: HTTP status code
        error_message: Error message text
        request_path: Request URL path
        
    Returns:
        List of troubleshooting tips
    """
    tips = ERROR_TIPS.get(status_code, []).copy()
    
    # Add context-specific tips based on error message or path
    error_lower = error_message.lower()
    
    if 'connection' in error_lower and 'refused' in error_lower:
        tips.extend(CONTEXT_TIPS['connection_refused'])
    elif 'plugin' in error_lower:
        tips.extend(CONTEXT_TIPS['plugin_load_error'])
    elif 'agent' in error_lower and ('unreachable' in error_lower or 'timeout' in error_lower):
        tips.extend(CONTEXT_TIPS['agent_unreachable'])
    elif 'operation' in error_lower and 'fail' in error_lower:
        tips.extend(CONTEXT_TIPS['operation_failed'])
    elif '/campaign' in request_path or 'campaign' in error_lower:
        tips.extend(CONTEXT_TIPS['campaign_error'])
    elif '/enrollment' in request_path or 'enrollment' in error_lower:
        tips.extend(CONTEXT_TIPS['enrollment_error'])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tips = []
    for tip in tips:
        if tip not in seen:
            seen.add(tip)
            unique_tips.append(tip)
    
    return unique_tips[:5]  # Limit to 5 most relevant tips


@web.middleware
async def error_handler_middleware(request, handler):
    """
    Middleware to catch exceptions and provide helpful error messages.
    
    This middleware:
    1. Catches all exceptions during request processing
    2. Adds troubleshooting tips to error responses
    3. Logs errors with full context
    4. Provides consistent error response format
    """
    try:
        response = await handler(request)
        
        # Enhance error responses with tips (4xx and 5xx status codes)
        if response.status >= 400:
            # Try to add tips to JSON responses
            if response.content_type == 'application/json' and hasattr(response, 'body'):
                try:
                    body = json.loads(response.body.decode('utf-8'))
                    
                    # Add troubleshooting tips if not already present
                    if 'troubleshooting_tips' not in body:
                        error_msg = body.get('error', body.get('message', ''))
                        tips = get_tips_for_error(response.status, error_msg, request.path)
                        if tips:
                            body['troubleshooting_tips'] = tips
                            response.body = json.dumps(body).encode('utf-8')
                            response.content_length = len(response.body)
                except (json.JSONDecodeError, AttributeError):
                    # Can't parse body, leave it as-is
                    pass
        
        return response
        
    except web.HTTPException as ex:
        # HTTP exceptions are expected (redirects, client errors, etc.)
        # Add tips if it's an error status
        if ex.status >= 400:
            logger.warning(f"{ex.status} {ex.reason}: {request.method} {request.path}")
            
            # Try to add tips to JSON error responses
            if hasattr(ex, 'text') and ex.text:
                try:
                    body = json.loads(ex.text)
                    if 'troubleshooting_tips' not in body:
                        tips = get_tips_for_error(ex.status, ex.reason, request.path)
                        if tips:
                            body['troubleshooting_tips'] = tips
                            ex.text = json.dumps(body)
                except (json.JSONDecodeError, AttributeError):
                    pass
        
        raise
        
    except Exception as ex:
        # Unexpected errors - log and return helpful 500 response
        logger.error(f"Unhandled error in {request.method} {request.path}", exc_info=True)
        
        # Build helpful error response
        error_detail = {
            'error': type(ex).__name__,
            'message': str(ex),
            'path': request.path,
            'method': request.method,
            'status': 500
        }
        
        # Add troubleshooting tips
        tips = get_tips_for_error(500, str(ex), request.path)
        if tips:
            error_detail['troubleshooting_tips'] = tips
        
        # Add traceback in debug mode
        app = request.app
        if app.get('debug', False) or app.get('log_level') == 'DEBUG':
            error_detail['traceback'] = traceback.format_exc().split('\n')
        
        return web.json_response(error_detail, status=500)


def format_error_response(status: int, message: str, request_path: str = None, 
                         error_type: str = None, **kwargs) -> web.Response:
    """
    Create a consistent error response format with troubleshooting tips.
    
    Args:
        status: HTTP status code
        message: Error message
        request_path: Optional path where error occurred
        error_type: Optional error type/code
        **kwargs: Additional fields to include in response
    
    Returns:
        JSON response with error details and troubleshooting tips
    """
    response = {
        'error': True,
        'status': status,
        'message': message
    }
    
    if error_type:
        response['error_type'] = error_type
    
    if request_path:
        response['path'] = request_path
    
    # Add any additional fields
    response.update(kwargs)
    
    # Add troubleshooting tips
    tips = get_tips_for_error(status, message, request_path or '')
    if tips:
        response['troubleshooting_tips'] = tips
    
    return web.json_response(response, status=status)


# Convenience functions for common error responses
def bad_request(message: str, **kwargs) -> web.Response:
    """Return 400 Bad Request with tips."""
    return format_error_response(400, message, error_type='bad_request', **kwargs)


def unauthorized(message: str = "Authentication required", **kwargs) -> web.Response:
    """Return 401 Unauthorized with tips."""
    return format_error_response(401, message, error_type='unauthorized', **kwargs)


def forbidden(message: str = "Insufficient permissions", **kwargs) -> web.Response:
    """Return 403 Forbidden with tips."""
    return format_error_response(403, message, error_type='forbidden', **kwargs)


def not_found(message: str, **kwargs) -> web.Response:
    """Return 404 Not Found with tips."""
    return format_error_response(404, message, error_type='not_found', **kwargs)


def server_error(message: str, **kwargs) -> web.Response:
    """Return 500 Internal Server Error with tips."""
    return format_error_response(500, message, error_type='server_error', **kwargs)
