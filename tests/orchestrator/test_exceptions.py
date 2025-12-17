"""
Unit tests for orchestrator exception classes.

Tests custom exception hierarchy, error messages, and contextual details.
"""

import pytest
from orchestrator.exceptions import (
    OrchestratorError,
    APIConnectionError,
    APIRequestError,
    CampaignNotFoundError,
    OperationNotFoundError,
    AgentDeploymentError,
    ReportGenerationError,
    DataValidationError,
    TemplateRenderError,
    PDFGenerationError,
    AttackNavigatorError,
    ConfigurationError
)


class TestOrchestratorError:
    """Test base OrchestratorError class."""
    
    def test_basic_message(self):
        """Test error with just a message."""
        error = OrchestratorError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}
    
    def test_with_details(self):
        """Test error with additional details."""
        error = OrchestratorError(
            "Operation failed",
            details={'operation_id': '123', 'reason': 'timeout'}
        )
        assert "operation_id=123" in str(error)
        assert "reason=timeout" in str(error)
        assert error.details['operation_id'] == '123'


class TestAPIConnectionError:
    """Test API connection error."""
    
    def test_basic_connection_error(self):
        """Test error with URL only."""
        error = APIConnectionError(url="http://localhost:8888/api/v2/operations")
        assert "localhost:8888" in str(error)
        assert error.url == "http://localhost:8888/api/v2/operations"
    
    def test_with_status_code(self):
        """Test error with HTTP status."""
        error = APIConnectionError(
            url="http://localhost:8888/api/v2/agents",
            status=503,
            reason="Service Unavailable"
        )
        assert "HTTP 503" in str(error)
        assert error.status == 503
        assert error.reason == "Service Unavailable"
    
    def test_inherits_from_orchestrator_error(self):
        """Test inheritance hierarchy."""
        error = APIConnectionError(url="http://test.com")
        assert isinstance(error, OrchestratorError)


class TestAPIRequestError:
    """Test API request error."""
    
    def test_api_request_failure(self):
        """Test failed API request."""
        error = APIRequestError(
            endpoint="/api/v2/operations",
            status=400,
            response_body='{"error": "Bad Request"}'
        )
        assert "/api/v2/operations" in str(error)
        assert "400" in str(error)
        assert error.status == 400
        assert error.response_body == '{"error": "Bad Request"}'
    
    def test_truncates_long_response(self):
        """Test that long response bodies are truncated."""
        long_response = "x" * 300
        error = APIRequestError(
            endpoint="/api/test",
            status=500,
            response_body=long_response
        )
        # Should truncate to 200 chars in details
        assert len(error.details['response']) == 200


class TestCampaignNotFoundError:
    """Test campaign not found error."""
    
    def test_campaign_not_found(self):
        """Test campaign not found message."""
        error = CampaignNotFoundError(campaign_id="test_campaign_123")
        assert "test_campaign_123" in str(error)
        assert "not found" in str(error)
        assert error.campaign_id == "test_campaign_123"


class TestOperationNotFoundError:
    """Test operation not found error."""
    
    def test_operation_not_found(self):
        """Test operation not found message."""
        error = OperationNotFoundError(operation_id="op_456")
        assert "op_456" in str(error)
        assert error.operation_id == "op_456"


class TestAgentDeploymentError:
    """Test agent deployment error."""
    
    def test_deployment_failure(self):
        """Test agent deployment failure."""
        error = AgentDeploymentError(
            agent_name="sandcat",
            platform="windows",
            reason="Payload not found"
        )
        assert "sandcat" in str(error)
        assert "windows" in str(error)
        assert "Payload not found" in str(error)
        assert error.agent_name == "sandcat"
        assert error.platform == "windows"


class TestReportGenerationError:
    """Test report generation error."""
    
    def test_report_generation_failure(self):
        """Test report generation failure."""
        error = ReportGenerationError(
            report_type="pdf",
            campaign_id="campaign_789",
            reason="Template not found"
        )
        assert "pdf" in str(error)
        assert "campaign_789" in str(error)
        assert "Template not found" in str(error)


class TestDataValidationError:
    """Test data validation error."""
    
    def test_validation_failure(self):
        """Test data validation failure."""
        error = DataValidationError(
            field="campaign_id",
            value="",
            constraint="must be non-empty"
        )
        assert "campaign_id" in str(error)
        assert "must be non-empty" in str(error)
        assert error.field == "campaign_id"
        assert error.value == ""
    
    def test_with_complex_value(self):
        """Test validation with complex value types."""
        error = DataValidationError(
            field="operation_count",
            value={"nested": "dict"},
            constraint="must be integer"
        )
        # Should convert value to string
        assert "field" in error.details
        assert isinstance(error.details['value'], str)


class TestTemplateRenderError:
    """Test template render error."""
    
    def test_template_render_failure(self):
        """Test template rendering failure."""
        error = TemplateRenderError(
            template_name="report_template.html",
            reason="Missing variable: campaign_name"
        )
        assert "report_template.html" in str(error)
        assert "Missing variable" in str(error)


class TestPDFGenerationError:
    """Test PDF generation error."""
    
    def test_pdf_generation_failure(self):
        """Test PDF generation failure."""
        error = PDFGenerationError(
            campaign_id="pdf_test",
            reason="WeasyPrint not installed"
        )
        assert "pdf" in str(error)
        assert "pdf_test" in str(error)
        assert "WeasyPrint" in str(error)
        assert error.report_type == "pdf"
    
    def test_with_html_path(self):
        """Test PDF error with HTML path preserved."""
        error = PDFGenerationError(
            campaign_id="test",
            reason="Conversion failed",
            html_path="/tmp/report.html"
        )
        assert error.html_path == "/tmp/report.html"
        assert "html_path" in error.details
    
    def test_inherits_from_report_generation_error(self):
        """Test inheritance from ReportGenerationError."""
        error = PDFGenerationError(
            campaign_id="test",
            reason="Test"
        )
        assert isinstance(error, ReportGenerationError)
        assert isinstance(error, OrchestratorError)


class TestAttackNavigatorError:
    """Test ATT&CK Navigator error."""
    
    def test_navigator_failure(self):
        """Test ATT&CK Navigator layer generation failure."""
        error = AttackNavigatorError(
            reason="Invalid technique ID: T9999",
            technique_count=42
        )
        assert "Invalid technique ID" in str(error)
        assert error.technique_count == 42
    
    def test_default_technique_count(self):
        """Test default technique count."""
        error = AttackNavigatorError(reason="Test error")
        assert error.technique_count == 0


class TestConfigurationError:
    """Test configuration error."""
    
    def test_config_error(self):
        """Test configuration error."""
        error = ConfigurationError(
            config_key="caldera.api_url",
            reason="Missing required configuration"
        )
        assert "caldera.api_url" in str(error)
        assert "Missing required" in str(error)
        assert error.config_key == "caldera.api_url"


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance."""
    
    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from OrchestratorError."""
        exceptions = [
            APIConnectionError("http://test.com"),
            APIRequestError("/test", 400),
            CampaignNotFoundError("test"),
            OperationNotFoundError("test"),
            AgentDeploymentError("agent", "platform", "reason"),
            ReportGenerationError("pdf", "campaign", "reason"),
            DataValidationError("field", "value", "constraint"),
            TemplateRenderError("template", "reason"),
            PDFGenerationError("campaign", "reason"),
            AttackNavigatorError("reason"),
            ConfigurationError("key", "reason")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, OrchestratorError)
            assert isinstance(exc, Exception)
    
    def test_can_catch_with_base_class(self):
        """Test that all exceptions can be caught with base class."""
        try:
            raise APIConnectionError("http://test.com")
        except OrchestratorError as e:
            assert isinstance(e, APIConnectionError)
            assert True  # Successfully caught
        else:
            assert False, "Should have caught exception"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
