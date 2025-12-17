#!/usr/bin/env python3
"""
Test P2 (Medium Priority) Implementation

Verifies:
1. Setup validation script exists and is executable
2. Troubleshooting documentation exists and is comprehensive
3. Webhook examples added to user journey
4. Script validation functions in enrollment generator
"""

import os
import re
from pathlib import Path

# Base path
BASE_PATH = Path(__file__).parent.parent


def test_setup_check_script_exists():
    """Verify setup_check.sh exists and is executable."""
    script_path = BASE_PATH / "scripts" / "setup_check.sh"
    
    assert script_path.exists(), "setup_check.sh not found"
    assert script_path.is_file(), "setup_check.sh is not a file"
    
    # Check if executable (Unix-like systems)
    if os.name != 'nt':
        assert os.access(script_path, os.X_OK), "setup_check.sh is not executable"
    
    # Check script content
    content = script_path.read_text()
    
    # Should have shebang
    assert content.startswith("#!/bin/bash"), "Missing bash shebang"
    
    # Should have key validation checks
    required_checks = [
        "Checking Python",
        "Checking Virtual Environment",
        "Checking Core Dependencies",
        "Checking File Structure",
        "Checking Port",
    ]
    
    for check in required_checks:
        assert check in content, f"Missing check: {check}"
    
    # Should have colored output
    assert "\\033[" in content, "Missing colored output codes"
    
    # Should have proper exit codes
    assert "exit 0" in content, "Missing success exit code"
    assert "exit 1" in content, "Missing error exit code"
    
    print("✅ Test 1 passed: setup_check.sh is valid")


def test_troubleshooting_guide_exists():
    """Verify comprehensive troubleshooting guide exists."""
    guide_path = BASE_PATH / "docs" / "TROUBLESHOOTING.md"
    
    assert guide_path.exists(), "TROUBLESHOOTING.md not found"
    assert guide_path.is_file(), "TROUBLESHOOTING.md is not a file"
    
    content = guide_path.read_text()
    
    # Check comprehensive sections
    required_sections = [
        "Server Won't Start",
        "Agent Connection Issues",
        "Operation Failures",
        "API Errors",
        "Plugin Problems",
        "Performance Issues",
        "Debug Mode",
    ]
    
    for section in required_sections:
        assert section in content, f"Missing section: {section}"
    
    # Check for specific error scenarios
    required_errors = [
        "ModuleNotFoundError",
        "Address already in use",
        "401 Unauthorized",
        "404 Not Found",
        "500 Internal Server Error",
    ]
    
    for error in required_errors:
        assert error in content, f"Missing error documentation: {error}"
    
    # Check for code examples
    assert "```bash" in content, "Missing bash code examples"
    assert "curl" in content, "Missing curl examples"
    
    # Check for troubleshooting tables
    assert "|" in content and "---" in content, "Missing markdown tables"
    
    # Verify reasonable length (should be comprehensive)
    assert len(content) > 10000, "TROUBLESHOOTING.md seems too short"
    
    print("✅ Test 2 passed: TROUBLESHOOTING.md is comprehensive")


def test_webhook_examples_added():
    """Verify webhook verification examples added to user journey."""
    journey_path = BASE_PATH / "END_TO_END_USER_JOURNEY.md"
    
    assert journey_path.exists(), "END_TO_END_USER_JOURNEY.md not found"
    
    content = journey_path.read_text()
    
    # Check for webhook verification step
    assert "Step 3.4: Verify Webhook Functionality" in content, \
        "Missing Step 3.4 for webhook verification"
    
    # Check for webhook.site example
    assert "webhook.site" in content, "Missing webhook.site example"
    
    # Check for local test server option
    assert "Local Test Server" in content, "Missing local test server option"
    
    # Check for webhook receiver example
    assert "webhook_receiver.py" in content, "Missing webhook receiver script"
    
    # Check for troubleshooting section
    assert "Webhook Troubleshooting" in content, "Missing webhook troubleshooting"
    
    # Check for event type documentation
    assert "Common Webhook Event Types" in content, "Missing event types table"
    
    # Check for practical examples
    webhook_examples = [
        "operation.created",
        "operation.updated",
        "campaign.started",
        "agent.connected",
    ]
    
    for example in webhook_examples:
        assert example in content, f"Missing webhook event example: {example}"
    
    print("✅ Test 3 passed: Webhook verification examples added")


def test_enrollment_generator_validation():
    """Verify script validation added to enrollment_generator.py."""
    generator_path = BASE_PATH / "orchestrator" / "agents" / "enrollment_generator.py"
    
    assert generator_path.exists(), "enrollment_generator.py not found"
    
    content = generator_path.read_text()
    
    # Check for ScriptValidator class
    assert "class ScriptValidator:" in content, "Missing ScriptValidator class"
    
    # Check for validation methods
    validation_methods = [
        "validate_powershell",
        "validate_bash",
        "validate_yaml",
        "validate_terraform",
    ]
    
    for method in validation_methods:
        assert f"def {method}" in content, f"Missing validation method: {method}"
    
    # Check for security checks
    security_checks = [
        "dangerous_patterns",
        "Invoke-Expression",
        "eval ",
        "hardcoded credentials",
    ]
    
    for check in security_checks:
        assert check in content, f"Missing security check: {check}"
    
    # Check for validation in main function
    assert "validator = ScriptValidator()" in content, \
        "ScriptValidator not instantiated in main"
    
    assert "validation_errors" in content, \
        "Validation results not captured"
    
    assert "Script Validation Results" in content, \
        "Validation results not displayed to user"
    
    # Check for proper error messages
    assert "❌" in content or "✅" in content, \
        "Missing validation status indicators"
    
    print("✅ Test 4 passed: Script validation functions added")


def test_implementation_summary():
    """Verify P2 implementation is documented."""
    # Check for any P2 implementation documentation
    possible_docs = [
        BASE_PATH / "IMPLEMENTATION_P2_SUMMARY.md",
        BASE_PATH / "BUGFIX_PLAN.md",
    ]
    
    found_docs = [doc for doc in possible_docs if doc.exists()]
    assert len(found_docs) > 0, "No implementation documentation found"
    
    # Check BUGFIX_PLAN.md has P2 tasks marked
    bugfix_plan = BASE_PATH / "BUGFIX_PLAN.md"
    if bugfix_plan.exists():
        content = bugfix_plan.read_text()
        assert "P2" in content or "Medium Priority" in content, \
            "No P2 priority tasks documented"
    
    print("✅ Test 5 passed: Implementation documented")


def test_p2_files_structure():
    """Verify all P2 files are in correct locations."""
    expected_files = [
        "scripts/setup_check.sh",
        "docs/TROUBLESHOOTING.md",
        "orchestrator/agents/enrollment_generator.py",
        "END_TO_END_USER_JOURNEY.md",
    ]
    
    for file_path in expected_files:
        full_path = BASE_PATH / file_path
        assert full_path.exists(), f"Missing expected file: {file_path}"
    
    print("✅ Test 6 passed: All P2 files in correct locations")


def main():
    """Run all tests."""
    print("=" * 60)
    print("P2 Implementation Verification Test")
    print("=" * 60)
    print()
    
    tests = [
        test_setup_check_script_exists,
        test_troubleshooting_guide_exists,
        test_webhook_examples_added,
        test_enrollment_generator_validation,
        test_implementation_summary,
        test_p2_files_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            print()
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
