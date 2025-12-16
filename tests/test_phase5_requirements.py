#!/usr/bin/env python3
"""
Phase 5 Enrollment API Test Suite

Comprehensive test cases to verify all Phase 5 requirements are met.
Tests the enrollment plugin integration, REST API, JSON storage,
environment configuration, and documentation completeness.
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'


class Phase5TestSuite:
    """Test suite for Phase 5 Enrollment API requirements."""
    
    def __init__(self, caldera_url: str = "http://localhost:8888"):
        self.caldera_url = caldera_url
        self.api_base = f"{caldera_url}/plugin/enrollment"
        self.project_root = Path(__file__).parent.parent.parent
        self.plugin_dir = self.project_root / "plugins" / "enrollment"
        self.examples_dir = self.project_root / "examples" / "enrollment"
        
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results: List[Dict] = []
    
    def print_header(self, text: str):
        """Print a test section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.NC}\n")
    
    def print_test(self, name: str):
        """Print test name."""
        print(f"{Colors.BLUE}→ Testing: {name}{Colors.NC}")
    
    def assert_test(self, condition: bool, test_name: str, message: str = ""):
        """Assert a test condition and record result."""
        if condition:
            self.tests_passed += 1
            status = f"{Colors.GREEN}✓ PASS{Colors.NC}"
            print(f"  {status}: {test_name}")
            if message:
                print(f"    {Colors.GREEN}{message}{Colors.NC}")
            self.test_results.append({"test": test_name, "status": "PASS", "message": message})
        else:
            self.tests_failed += 1
            status = f"{Colors.RED}✗ FAIL{Colors.NC}"
            print(f"  {status}: {test_name}")
            if message:
                print(f"    {Colors.RED}{message}{Colors.NC}")
            self.test_results.append({"test": test_name, "status": "FAIL", "message": message})
    
    def test_requirement_1_plugin_structure(self):
        """
        Requirement 1: Enrollment plugin with CALDERA integration
        - Plugin directory exists
        - hook.py implements proper plugin interface
        - Plugin integrates with CALDERA services
        """
        self.print_header("Requirement 1: Plugin Structure & Integration")
        
        # Test 1.1: Plugin directory exists
        self.print_test("Plugin directory structure")
        plugin_exists = self.plugin_dir.exists()
        self.assert_test(
            plugin_exists,
            "Plugin directory exists at plugins/enrollment/",
            f"Found: {self.plugin_dir}"
        )
        
        # Test 1.2: hook.py exists and has required elements
        self.print_test("hook.py plugin integration")
        hook_file = self.plugin_dir / "hook.py"
        hook_exists = hook_file.exists()
        
        if hook_exists:
            hook_content = hook_file.read_text()
            has_name = "name = 'Enrollment'" in hook_content or 'name = "Enrollment"' in hook_content
            has_enable = "async def enable(services):" in hook_content
            has_routes = "app.router.add_route" in hook_content
            
            self.assert_test(
                has_name and has_enable and has_routes,
                "hook.py implements plugin interface",
                f"name={has_name}, enable()={has_enable}, routes={has_routes}"
            )
        else:
            self.assert_test(False, "hook.py exists", "File not found")
        
        # Test 1.3: Service modules exist
        self.print_test("Service module files")
        app_dir = self.plugin_dir / "app"
        enrollment_svc = app_dir / "enrollment_svc.py"
        enrollment_api = app_dir / "enrollment_api.py"
        
        self.assert_test(
            enrollment_svc.exists() and enrollment_api.exists(),
            "Service modules exist",
            f"enrollment_svc.py={enrollment_svc.exists()}, enrollment_api.py={enrollment_api.exists()}"
        )
    
    def test_requirement_2_rest_api_endpoints(self):
        """
        Requirement 2: REST API for dynamic agent registration
        - POST /plugin/enrollment/enroll
        - GET /plugin/enrollment/enroll/{id}
        - GET /plugin/enrollment/requests
        - GET /plugin/enrollment/campaigns/{id}/agents
        - GET /plugin/enrollment/health
        """
        self.print_header("Requirement 2: REST API Endpoints")
        
        # Test 2.1: Health endpoint
        self.print_test("Health check endpoint")
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            health_works = response.status_code == 200
            health_data = response.json() if health_works else {}
            
            self.assert_test(
                health_works and health_data.get('status') == 'healthy',
                "GET /plugin/enrollment/health returns 200",
                f"Status: {health_data.get('status')}, Total requests: {health_data.get('total_requests')}"
            )
        except Exception as e:
            self.assert_test(False, "Health endpoint accessible", str(e))
            return  # Can't test other endpoints if health fails
        
        # Test 2.2: POST enroll endpoint
        self.print_test("Create enrollment endpoint")
        try:
            enroll_payload = {
                "platform": "linux",
                "campaign_id": "test-phase5-validation",
                "tags": ["phase5-test", "automated"],
                "hostname": "phase5-test-host"
            }
            response = requests.post(
                f"{self.api_base}/enroll",
                json=enroll_payload,
                timeout=5
            )
            
            enroll_success = response.status_code == 201
            enroll_data = response.json() if enroll_success else {}
            request_id = enroll_data.get('request_id')
            
            self.assert_test(
                enroll_success and request_id,
                "POST /plugin/enrollment/enroll creates enrollment",
                f"Status: {response.status_code}, Request ID: {request_id[:20]}..." if request_id else ""
            )
            
            # Store request_id for subsequent tests
            self.test_request_id = request_id
            
            # Validate response structure
            has_bootstrap = 'bootstrap_command' in enroll_data
            has_download_url = 'agent_download_url' in enroll_data
            has_status = enroll_data.get('status') == 'pending'
            
            self.assert_test(
                has_bootstrap and has_download_url and has_status,
                "Enrollment response includes required fields",
                f"bootstrap={has_bootstrap}, download_url={has_download_url}, status={has_status}"
            )
            
        except Exception as e:
            self.assert_test(False, "POST /enroll endpoint", str(e))
            self.test_request_id = None
        
        # Test 2.3: GET enrollment status
        self.print_test("Get enrollment status endpoint")
        if self.test_request_id:
            try:
                response = requests.get(
                    f"{self.api_base}/enroll/{self.test_request_id}",
                    timeout=5
                )
                status_works = response.status_code == 200
                status_data = response.json() if status_works else {}
                
                self.assert_test(
                    status_works and status_data.get('request_id') == self.test_request_id,
                    "GET /plugin/enrollment/enroll/{id} retrieves enrollment",
                    f"Status: {response.status_code}, Matches: {status_data.get('request_id') == self.test_request_id}"
                )
            except Exception as e:
                self.assert_test(False, "GET enrollment status", str(e))
        else:
            self.assert_test(False, "GET enrollment status", "No request_id from previous test")
        
        # Test 2.4: List enrollment requests
        self.print_test("List enrollments endpoint")
        try:
            response = requests.get(f"{self.api_base}/requests", timeout=5)
            list_works = response.status_code == 200
            list_data = response.json() if list_works else {}
            
            has_total = 'total' in list_data
            has_requests = 'requests' in list_data
            
            self.assert_test(
                list_works and has_total and has_requests,
                "GET /plugin/enrollment/requests lists enrollments",
                f"Total: {list_data.get('total')}, Requests array: {len(list_data.get('requests', []))}"
            )
            
            # Test filtering
            response = requests.get(
                f"{self.api_base}/requests?campaign_id=test-phase5-validation",
                timeout=5
            )
            filter_data = response.json() if response.status_code == 200 else {}
            
            self.assert_test(
                response.status_code == 200,
                "Query parameter filtering works",
                f"Filtered results: {filter_data.get('total')}"
            )
        except Exception as e:
            self.assert_test(False, "List enrollments", str(e))
        
        # Test 2.5: List campaign agents
        self.print_test("List campaign agents endpoint")
        try:
            response = requests.get(
                f"{self.api_base}/campaigns/test-phase5-validation/agents",
                timeout=5
            )
            campaign_works = response.status_code == 200
            campaign_data = response.json() if campaign_works else {}
            
            self.assert_test(
                campaign_works and 'agents' in campaign_data,
                "GET /plugin/enrollment/campaigns/{id}/agents works",
                f"Campaign: {campaign_data.get('campaign_id')}, Agents: {campaign_data.get('total_agents', 0)}"
            )
        except Exception as e:
            self.assert_test(False, "List campaign agents", str(e))
        
        # Test 2.6: Error handling
        self.print_test("API error handling")
        try:
            # Test missing required field
            response = requests.post(
                f"{self.api_base}/enroll",
                json={},
                timeout=5
            )
            self.assert_test(
                response.status_code == 400,
                "Returns 400 for missing required fields",
                f"Status: {response.status_code}"
            )
            
            # Test invalid platform
            response = requests.post(
                f"{self.api_base}/enroll",
                json={"platform": "invalid-os"},
                timeout=5
            )
            self.assert_test(
                response.status_code == 400,
                "Returns 400 for invalid platform",
                f"Status: {response.status_code}"
            )
            
            # Test not found
            response = requests.get(
                f"{self.api_base}/enroll/nonexistent-id",
                timeout=5
            )
            self.assert_test(
                response.status_code == 404,
                "Returns 404 for nonexistent resources",
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.assert_test(False, "Error handling", str(e))
    
    def test_requirement_3_json_storage(self):
        """
        Requirement 3: JSON-based persistent storage
        - Data stored in JSON file
        - Survives service restarts
        - Proper file structure
        """
        self.print_header("Requirement 3: JSON Persistent Storage")
        
        # Test 3.1: Storage file exists
        self.print_test("JSON storage file")
        storage_file = self.plugin_dir / "data" / "enrollment_requests.json"
        
        self.assert_test(
            storage_file.exists(),
            "enrollment_requests.json file exists",
            f"Location: {storage_file}"
        )
        
        # Test 3.2: Valid JSON structure
        if storage_file.exists():
            self.print_test("JSON file structure")
            try:
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                
                is_dict = isinstance(data, dict)
                self.assert_test(
                    is_dict,
                    "Storage file contains valid JSON object",
                    f"Type: {type(data).__name__}, Entries: {len(data) if is_dict else 0}"
                )
                
                # Validate entry structure
                if is_dict and data:
                    sample_entry = next(iter(data.values()))
                    has_request_id = 'request_id' in sample_entry
                    has_platform = 'platform' in sample_entry
                    has_status = 'status' in sample_entry
                    has_created_at = 'created_at' in sample_entry
                    
                    self.assert_test(
                        has_request_id and has_platform and has_status and has_created_at,
                        "Enrollment entries have required fields",
                        f"Fields present: request_id={has_request_id}, platform={has_platform}, status={has_status}, created_at={has_created_at}"
                    )
            except json.JSONDecodeError as e:
                self.assert_test(False, "Valid JSON format", str(e))
            except Exception as e:
                self.assert_test(False, "Read JSON storage", str(e))
        
        # Test 3.3: Data persists in storage
        self.print_test("Data persistence")
        if self.test_request_id and storage_file.exists():
            try:
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                
                self.assert_test(
                    self.test_request_id in data,
                    "Created enrollment persisted to JSON",
                    f"Request {self.test_request_id[:20]}... found in storage"
                )
            except Exception as e:
                self.assert_test(False, "Verify persistence", str(e))
    
    def test_requirement_4_bootstrap_generation(self):
        """
        Requirement 4: Platform-specific bootstrap generation
        - Windows PowerShell commands
        - Linux/macOS bash commands
        - Campaign tagging included
        """
        self.print_header("Requirement 4: Bootstrap Command Generation")
        
        platforms = ["windows", "linux", "darwin"]
        
        for platform in platforms:
            self.print_test(f"Bootstrap for {platform}")
            try:
                response = requests.post(
                    f"{self.api_base}/enroll",
                    json={
                        "platform": platform,
                        "campaign_id": "bootstrap-test",
                        "tags": ["test-tag"]
                    },
                    timeout=5
                )
                
                if response.status_code == 201:
                    data = response.json()
                    bootstrap = data.get('bootstrap_command', '')
                    
                    # Platform-specific validation
                    if platform == "windows":
                        has_powershell = "Invoke-WebRequest" in bootstrap or "$url=" in bootstrap
                        has_exe = ".exe" in bootstrap
                        is_valid = has_powershell and has_exe
                        msg = f"PowerShell syntax={has_powershell}, .exe={has_exe}"
                    else:  # linux or darwin
                        has_curl = "curl" in bootstrap
                        has_chmod = "chmod" in bootstrap
                        is_valid = has_curl and has_chmod
                        msg = f"curl={has_curl}, chmod={has_chmod}"
                    
                    # Check campaign tag included
                    has_campaign_tag = "campaign:bootstrap-test" in bootstrap
                    has_custom_tag = "test-tag" in bootstrap
                    
                    self.assert_test(
                        is_valid and has_campaign_tag and has_custom_tag,
                        f"{platform.capitalize()} bootstrap command generated correctly",
                        f"{msg}, campaign_tag={has_campaign_tag}, custom_tag={has_custom_tag}"
                    )
                else:
                    self.assert_test(False, f"Generate {platform} bootstrap", f"Status: {response.status_code}")
            except Exception as e:
                self.assert_test(False, f"Generate {platform} bootstrap", str(e))
    
    def test_requirement_5_environment_config(self):
        """
        Requirement 5: Environment variable configuration
        - CALDERA_URL environment variable support
        - Localhost fallback
        - Configuration reflected in responses
        """
        self.print_header("Requirement 5: Environment Configuration")
        
        # Test 5.1: Health check shows configuration
        self.print_test("Environment configuration in health check")
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                has_caldera_url = 'caldera_url' in health
                caldera_url = health.get('caldera_url', '')
                
                self.assert_test(
                    has_caldera_url and caldera_url,
                    "Health check exposes CALDERA_URL configuration",
                    f"Configured URL: {caldera_url}"
                )
                
                # Verify it's using environment variable or fallback
                expected = os.getenv('CALDERA_URL', 'http://localhost:8888')
                self.assert_test(
                    caldera_url == expected or caldera_url == self.caldera_url,
                    "Uses CALDERA_URL or localhost fallback",
                    f"Expected: {expected}, Got: {caldera_url}"
                )
        except Exception as e:
            self.assert_test(False, "Environment configuration", str(e))
        
        # Test 5.2: Enrollment responses include caldera_url
        self.print_test("CALDERA_URL in enrollment responses")
        try:
            response = requests.post(
                f"{self.api_base}/enroll",
                json={"platform": "linux"},
                timeout=5
            )
            if response.status_code == 201:
                data = response.json()
                has_url = 'caldera_url' in data
                has_download_url = 'agent_download_url' in data
                
                self.assert_test(
                    has_url and has_download_url,
                    "Enrollment includes CALDERA URLs",
                    f"caldera_url={has_url}, agent_download_url={has_download_url}"
                )
        except Exception as e:
            self.assert_test(False, "CALDERA_URL in responses", str(e))
    
    def test_requirement_6_testing_examples(self):
        """
        Requirement 6: Local testing examples
        - Bash test script
        - Python client example
        - .env configuration template
        """
        self.print_header("Requirement 6: Testing Examples")
        
        # Test 6.1: Bash script exists and is executable
        self.print_test("Bash testing script")
        bash_script = self.examples_dir / "test_enrollment_api.sh"
        
        exists = bash_script.exists()
        is_executable = os.access(bash_script, os.X_OK) if exists else False
        
        self.assert_test(
            exists and is_executable,
            "test_enrollment_api.sh exists and is executable",
            f"Path: {bash_script}, Executable: {is_executable}"
        )
        
        # Validate script content
        if exists:
            content = bash_script.read_text()
            has_curl = "curl" in content
            has_jq = "jq" in content
            has_tests = "Test" in content and "echo" in content
            
            self.assert_test(
                has_curl and has_jq and has_tests,
                "Bash script contains proper test commands",
                f"curl={has_curl}, jq={has_jq}, tests={has_tests}"
            )
        
        # Test 6.2: Python example exists and is executable
        self.print_test("Python client example")
        python_script = self.examples_dir / "enroll_from_python.py"
        
        exists = python_script.exists()
        is_executable = os.access(python_script, os.X_OK) if exists else False
        
        self.assert_test(
            exists and is_executable,
            "enroll_from_python.py exists and is executable",
            f"Path: {python_script}, Executable: {is_executable}"
        )
        
        # Validate Python script content
        if exists:
            content = python_script.read_text()
            has_class = "class EnrollmentClient" in content
            has_requests = "import requests" in content
            has_main = "def main():" in content
            has_example = "if __name__" in content
            
            self.assert_test(
                has_class and has_requests and has_main and has_example,
                "Python script is a complete working example",
                f"class={has_class}, requests={has_requests}, main={has_main}, runnable={has_example}"
            )
        
        # Test 6.3: .env example exists
        self.print_test("Environment configuration template")
        env_example = self.examples_dir / ".env.example"
        
        self.assert_test(
            env_example.exists(),
            ".env.example configuration template exists",
            f"Path: {env_example}"
        )
        
        if env_example.exists():
            content = env_example.read_text()
            has_caldera_url = "CALDERA_URL" in content
            
            self.assert_test(
                has_caldera_url,
                ".env.example includes CALDERA_URL",
                f"Contains CALDERA_URL: {has_caldera_url}"
            )
    
    def test_requirement_7_documentation(self):
        """
        Requirement 7: Comprehensive documentation
        - Plugin README
        - API documentation
        - Updated orchestration guide
        """
        self.print_header("Requirement 7: Comprehensive Documentation")
        
        # Test 7.1: Plugin README exists
        self.print_test("Plugin README documentation")
        readme = self.plugin_dir / "docs" / "README.md"
        
        exists = readme.exists()
        self.assert_test(exists, "Plugin README.md exists", f"Path: {readme}")
        
        if exists:
            content = readme.read_text()
            size = len(content)
            
            has_overview = "Overview" in content or "overview" in content
            has_quickstart = "Quick Start" in content or "quickstart" in content.lower()
            has_api_ref = "API" in content or "endpoint" in content.lower()
            has_examples = "example" in content.lower()
            has_troubleshooting = "troubleshoot" in content.lower()
            
            self.assert_test(
                has_overview and has_quickstart and has_examples,
                "README includes essential sections",
                f"Size: {size} bytes, Overview={has_overview}, QuickStart={has_quickstart}, Examples={has_examples}, Troubleshooting={has_troubleshooting}"
            )
            
            self.assert_test(
                size > 3000,
                "README is comprehensive (>3000 bytes)",
                f"Size: {size} bytes"
            )
        
        # Test 7.2: API documentation exists
        self.print_test("API reference documentation")
        api_doc = self.plugin_dir / "docs" / "API.md"
        
        exists = api_doc.exists()
        self.assert_test(exists, "API.md documentation exists", f"Path: {api_doc}")
        
        if exists:
            content = api_doc.read_text()
            size = len(content)
            
            # Check for all endpoints documented
            has_health = "/health" in content
            has_enroll = "/enroll" in content
            has_requests = "/requests" in content
            has_campaigns = "/campaigns" in content
            
            self.assert_test(
                has_health and has_enroll and has_requests and has_campaigns,
                "API.md documents all endpoints",
                f"health={has_health}, enroll={has_enroll}, requests={has_requests}, campaigns={has_campaigns}"
            )
            
            # Check for examples
            has_curl = "curl" in content
            has_examples = "example" in content.lower()
            has_responses = "response" in content.lower()
            
            self.assert_test(
                has_curl and has_examples and has_responses,
                "API.md includes examples and responses",
                f"curl={has_curl}, examples={has_examples}, responses={has_responses}"
            )
            
            self.assert_test(
                size > 5000,
                "API documentation is comprehensive (>5000 bytes)",
                f"Size: {size} bytes"
            )
        
        # Test 7.3: Orchestration guide updated
        self.print_test("Orchestration guide updated")
        guide = self.project_root / "ORCHESTRATION_GUIDE.md"
        
        if guide.exists():
            content = guide.read_text()
            
            has_phase5 = "Phase 5" in content
            has_enrollment = "Enrollment" in content or "enrollment" in content
            has_completed = "✅" in content or "Completed" in content
            
            self.assert_test(
                has_phase5 and has_enrollment,
                "ORCHESTRATION_GUIDE.md mentions Phase 5 Enrollment",
                f"Phase5={has_phase5}, Enrollment={has_enrollment}, Completed={has_completed}"
            )
            
            # Check for API endpoints documented
            has_endpoint_doc = "/plugin/enrollment" in content
            
            self.assert_test(
                has_endpoint_doc,
                "Guide documents enrollment endpoints",
                f"Endpoints documented: {has_endpoint_doc}"
            )
    
    def test_requirement_8_cli_separation(self):
        """
        Requirement 8: CLI and API are separate
        - Orchestrator CLI exists independently
        - Enrollment API works independently
        - Both can be used together
        """
        self.print_header("Requirement 8: CLI/API Separation")
        
        # Test 8.1: Orchestrator CLI exists
        self.print_test("Orchestrator CLI independence")
        cli_path = self.project_root / "orchestrator" / "cli.py"
        
        self.assert_test(
            cli_path.exists(),
            "Orchestrator CLI exists independently",
            f"Path: {cli_path}"
        )
        
        # Test 8.2: API works without CLI
        self.print_test("API works independently")
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            self.assert_test(
                response.status_code == 200,
                "Enrollment API accessible without CLI",
                "API responds to direct HTTP requests"
            )
        except Exception as e:
            self.assert_test(False, "API independence", str(e))
        
        # Test 8.3: Documentation clarifies separation
        readme = self.plugin_dir / "docs" / "README.md"
        if readme.exists():
            content = readme.read_text()
            mentions_cli = "CLI" in content or "cli.py" in content
            mentions_separate = "separate" in content.lower() or "independent" in content.lower()
            
            self.assert_test(
                mentions_cli and mentions_separate,
                "Documentation clarifies CLI/API separation",
                f"Mentions CLI: {mentions_cli}, Mentions separation: {mentions_separate}"
            )
    
    def print_summary(self):
        """Print test summary."""
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.NC}")
        print(f"{Colors.BOLD}{'='*70}{Colors.NC}\n")
        
        print(f"Total Tests:  {total}")
        print(f"{Colors.GREEN}Passed:       {self.tests_passed}{Colors.NC}")
        print(f"{Colors.RED}Failed:       {self.tests_failed}{Colors.NC}")
        print(f"Pass Rate:    {pass_rate:.1f}%\n")
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL PHASE 5 REQUIREMENTS MET{Colors.NC}\n")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SOME REQUIREMENTS NOT MET{Colors.NC}\n")
            print(f"{Colors.YELLOW}Failed Tests:{Colors.NC}")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}")
                    if result['message']:
                        print(f"    {result['message']}")
            print()
            return 1
    
    def run_all_tests(self):
        """Run all test requirements."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║         PHASE 5 ENROLLMENT API - REQUIREMENTS VALIDATION         ║")
        print("║                                                                  ║")
        print(f"║  Caldera URL: {self.caldera_url:46} ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.NC}")
        
        try:
            self.test_requirement_1_plugin_structure()
            self.test_requirement_2_rest_api_endpoints()
            self.test_requirement_3_json_storage()
            self.test_requirement_4_bootstrap_generation()
            self.test_requirement_5_environment_config()
            self.test_requirement_6_testing_examples()
            self.test_requirement_7_documentation()
            self.test_requirement_8_cli_separation()
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.NC}\n")
            return 130
        except Exception as e:
            print(f"\n\n{Colors.RED}Unexpected error: {e}{Colors.NC}\n")
            return 1
        
        return self.print_summary()


def main():
    """Main entry point."""
    # Get Caldera URL from environment
    caldera_url = os.getenv('CALDERA_URL', 'http://localhost:8888')
    
    # Check if Caldera is accessible
    print(f"Checking Caldera availability at {caldera_url}...")
    try:
        response = requests.get(f"{caldera_url}/plugin/enrollment/health", timeout=5)
        if response.status_code != 200:
            print(f"{Colors.RED}Warning: Caldera enrollment plugin may not be enabled{Colors.NC}")
            print(f"Response status: {response.status_code}")
            print()
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}Error: Cannot connect to Caldera at {caldera_url}{Colors.NC}")
        print(f"Error: {e}")
        print()
        print("Make sure:")
        print("  1. Caldera server is running: ./venv/bin/python server.py")
        print("  2. Enrollment plugin is enabled in conf/local.yml")
        print("  3. CALDERA_URL environment variable is correct")
        print()
        return 1
    
    # Run test suite
    suite = Phase5TestSuite(caldera_url)
    return suite.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
