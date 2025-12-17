"""
Custom exceptions for CALDERA Orchestrator module.

Provides specific exception types for better error handling and debugging
across campaign orchestration, reporting, and agent deployment operations.
"""

from typing import Optional


class OrchestratorError(Exception):
    """Base exception class for all orchestrator-related errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize orchestrator exception.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation including details if present."""
        if self.details:
            details_str = ', '.join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class APIConnectionError(OrchestratorError):
    """Raised when unable to connect to CALDERA API server."""
    
    def __init__(self, url: str, status: Optional[int] = None, reason: Optional[str] = None):
        """
        Initialize API connection error.
        
        Args:
            url: The API endpoint URL that failed
            status: HTTP status code if received
            reason: Additional error reason/message
        """
        details = {'url': url}
        if status:
            details['status'] = status
        if reason:
            details['reason'] = reason
        
        message = f"Failed to connect to CALDERA API at {url}"
        if status:
            message += f" (HTTP {status})"
        
        super().__init__(message, details)
        self.url = url
        self.status = status
        self.reason = reason


class APIRequestError(OrchestratorError):
    """Raised when API request fails with error response."""
    
    def __init__(self, endpoint: str, status: int, response_body: Optional[str] = None):
        """
        Initialize API request error.
        
        Args:
            endpoint: The API endpoint that returned an error
            status: HTTP status code
            response_body: Response body text if available
        """
        details = {'endpoint': endpoint, 'status': status}
        if response_body:
            details['response'] = response_body[:200]  # Truncate long responses
        
        message = f"API request to {endpoint} failed with status {status}"
        super().__init__(message, details)
        self.endpoint = endpoint
        self.status = status
        self.response_body = response_body


class CampaignNotFoundError(OrchestratorError):
    """Raised when specified campaign cannot be found."""
    
    def __init__(self, campaign_id: str):
        """
        Initialize campaign not found error.
        
        Args:
            campaign_id: The campaign ID that was not found
        """
        message = f"Campaign '{campaign_id}' not found"
        super().__init__(message, {'campaign_id': campaign_id})
        self.campaign_id = campaign_id


class OperationNotFoundError(OrchestratorError):
    """Raised when specified operation cannot be found."""
    
    def __init__(self, operation_id: str):
        """
        Initialize operation not found error.
        
        Args:
            operation_id: The operation ID that was not found
        """
        message = f"Operation '{operation_id}' not found"
        super().__init__(message, {'operation_id': operation_id})
        self.operation_id = operation_id


class AgentDeploymentError(OrchestratorError):
    """Raised when agent deployment fails."""
    
    def __init__(self, agent_name: str, platform: str, reason: str):
        """
        Initialize agent deployment error.
        
        Args:
            agent_name: Name of agent that failed to deploy
            platform: Target platform (windows, linux, darwin)
            reason: Reason for deployment failure
        """
        message = f"Failed to deploy agent '{agent_name}' on {platform}: {reason}"
        details = {'agent': agent_name, 'platform': platform, 'reason': reason}
        super().__init__(message, details)
        self.agent_name = agent_name
        self.platform = platform
        self.reason = reason


class ReportGenerationError(OrchestratorError):
    """Raised when report generation fails."""
    
    def __init__(self, report_type: str, campaign_id: str, reason: str):
        """
        Initialize report generation error.
        
        Args:
            report_type: Type of report (pdf, json, html, etc.)
            campaign_id: Campaign the report was for
            reason: Reason for generation failure
        """
        message = f"Failed to generate {report_type} report for campaign '{campaign_id}': {reason}"
        details = {'report_type': report_type, 'campaign_id': campaign_id, 'reason': reason}
        super().__init__(message, details)
        self.report_type = report_type
        self.campaign_id = campaign_id
        self.reason = reason


class DataValidationError(OrchestratorError):
    """Raised when campaign or operation data fails validation."""
    
    def __init__(self, field: str, value: any, constraint: str):
        """
        Initialize data validation error.
        
        Args:
            field: Name of the field that failed validation
            value: The invalid value
            constraint: Description of the validation constraint
        """
        message = f"Validation failed for '{field}': {constraint}"
        details = {'field': field, 'value': str(value), 'constraint': constraint}
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.constraint = constraint


class TemplateRenderError(OrchestratorError):
    """Raised when report template rendering fails."""
    
    def __init__(self, template_name: str, reason: str):
        """
        Initialize template render error.
        
        Args:
            template_name: Name of the template that failed to render
            reason: Reason for rendering failure
        """
        message = f"Failed to render template '{template_name}': {reason}"
        details = {'template': template_name, 'reason': reason}
        super().__init__(message, details)
        self.template_name = template_name
        self.reason = reason


class PDFGenerationError(ReportGenerationError):
    """Raised when PDF report generation fails specifically."""
    
    def __init__(self, campaign_id: str, reason: str, html_path: Optional[str] = None):
        """
        Initialize PDF generation error.
        
        Args:
            campaign_id: Campaign the PDF was for
            reason: Reason for PDF generation failure
            html_path: Path to HTML file if PDF conversion failed
        """
        super().__init__('pdf', campaign_id, reason)
        if html_path:
            self.details['html_path'] = html_path
        self.html_path = html_path


class AttackNavigatorError(OrchestratorError):
    """Raised when ATT&CK Navigator layer generation fails."""
    
    def __init__(self, reason: str, technique_count: int = 0):
        """
        Initialize ATT&CK Navigator error.
        
        Args:
            reason: Reason for layer generation failure
            technique_count: Number of techniques attempted to process
        """
        message = f"Failed to generate ATT&CK Navigator layer: {reason}"
        details = {'reason': reason, 'technique_count': technique_count}
        super().__init__(message, details)
        self.reason = reason
        self.technique_count = technique_count


class ConfigurationError(OrchestratorError):
    """Raised when orchestrator configuration is invalid or missing."""
    
    def __init__(self, config_key: str, reason: str):
        """
        Initialize configuration error.
        
        Args:
            config_key: Configuration key that is invalid/missing
            reason: Description of the configuration issue
        """
        message = f"Configuration error for '{config_key}': {reason}"
        details = {'config_key': config_key, 'reason': reason}
        super().__init__(message, details)
        self.config_key = config_key
        self.reason = reason
