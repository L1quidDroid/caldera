"""
Simple test runner for exception classes without pytest dependency.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

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


def test_orchestrator_error():
    """Test base OrchestratorError class."""
    print("Testing OrchestratorError...")
    
    # Test basic message
    error = OrchestratorError("Something went wrong")
    assert str(error) == "Something went wrong"
    assert error.message == "Something went wrong"
    assert error.details == {}
    
    # Test with details
    error = OrchestratorError(
        "Operation failed",
        details={'operation_id': '123', 'reason': 'timeout'}
    )
    assert "operation_id=123" in str(error)
    assert "reason=timeout" in str(error)
    
    print("  ✓ OrchestratorError tests passed")


def test_api_connection_error():
    """Test API connection error."""
    print("Testing APIConnectionError...")
    
    error = APIConnectionError(url="http://localhost:8888/api/v2/operations")
    assert "localhost:8888" in str(error)
    assert error.url == "http://localhost:8888/api/v2/operations"
    
    error = APIConnectionError(
        url="http://localhost:8888/api/v2/agents",
        status=503,
        reason="Service Unavailable"
    )
    assert "HTTP 503" in str(error)
    assert error.status == 503
    assert isinstance(error, OrchestratorError)
    
    print("  ✓ APIConnectionError tests passed")


def test_api_request_error():
    """Test API request error."""
    print("Testing APIRequestError...")
    
    error = APIRequestError(
        endpoint="/api/v2/operations",
        status=400,
        response_body='{"error": "Bad Request"}'
    )
    assert "/api/v2/operations" in str(error)
    assert "400" in str(error)
    assert error.status == 400
    
    # Test truncation
    long_response = "x" * 300
    error = APIRequestError(
        endpoint="/api/test",
        status=500,
        response_body=long_response
    )
    assert len(error.details['response']) == 200
    
    print("  ✓ APIRequestError tests passed")


def test_campaign_not_found_error():
    """Test campaign not found error."""
    print("Testing CampaignNotFoundError...")
    
    error = CampaignNotFoundError(campaign_id="test_campaign_123")
    assert "test_campaign_123" in str(error)
    assert "not found" in str(error)
    assert error.campaign_id == "test_campaign_123"
    
    print("  ✓ CampaignNotFoundError tests passed")


def test_agent_deployment_error():
    """Test agent deployment error."""
    print("Testing AgentDeploymentError...")
    
    error = AgentDeploymentError(
        agent_name="sandcat",
        platform="windows",
        reason="Payload not found"
    )
    assert "sandcat" in str(error)
    assert "windows" in str(error)
    assert "Payload not found" in str(error)
    assert error.agent_name == "sandcat"
    
    print("  ✓ AgentDeploymentError tests passed")


def test_data_validation_error():
    """Test data validation error."""
    print("Testing DataValidationError...")
    
    error = DataValidationError(
        field="campaign_id",
        value="",
        constraint="must be non-empty"
    )
    assert "campaign_id" in str(error)
    assert "must be non-empty" in str(error)
    assert error.field == "campaign_id"
    
    # Test with complex value
    error = DataValidationError(
        field="operation_count",
        value={"nested": "dict"},
        constraint="must be integer"
    )
    assert isinstance(error.details['value'], str)
    
    print("  ✓ DataValidationError tests passed")


def test_pdf_generation_error():
    """Test PDF generation error."""
    print("Testing PDFGenerationError...")
    
    error = PDFGenerationError(
        campaign_id="pdf_test",
        reason="WeasyPrint not installed"
    )
    assert "pdf" in str(error)
    assert "pdf_test" in str(error)
    assert error.report_type == "pdf"
    
    # Test inheritance
    assert isinstance(error, ReportGenerationError)
    assert isinstance(error, OrchestratorError)
    
    print("  ✓ PDFGenerationError tests passed")


def test_exception_hierarchy():
    """Test exception hierarchy."""
    print("Testing exception hierarchy...")
    
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
    
    # Test catching with base class
    try:
        raise APIConnectionError("http://test.com")
    except OrchestratorError as e:
        assert isinstance(e, APIConnectionError)
    
    print("  ✓ Exception hierarchy tests passed")


def run_all_tests():
    """Run all test functions."""
    print("="*60)
    print("Running Orchestrator Exception Tests")
    print("="*60)
    
    tests = [
        test_orchestrator_error,
        test_api_connection_error,
        test_api_request_error,
        test_campaign_not_found_error,
        test_agent_deployment_error,
        test_data_validation_error,
        test_pdf_generation_error,
        test_exception_hierarchy
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
