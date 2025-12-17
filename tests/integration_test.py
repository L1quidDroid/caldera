#!/usr/bin/env python3
"""
CALDERA Integration Test Suite

Tests the complete user journey end-to-end:
- Server health check
- API v2 endpoints
- Plugin functionality
- Orchestrator CLI
- Enrollment API
- Webhook publishing

Usage:
    python3 tests/integration_test.py
    python3 tests/integration_test.py --server http://localhost:8888
    python3 tests/integration_test.py --quick  # Skip long-running tests
"""

import argparse
import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("Error: requests package not installed")
    print("Run: pip install requests")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class IntegrationTest:
    """CALDERA integration test runner."""
    
    def __init__(self, server_url: str, api_key: str, quick_mode: bool = False):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.quick_mode = quick_mode
        self.session = requests.Session()
        self.session.headers.update({'KEY': api_key})
        self.session.verify = False
        
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
    def print_header(self, text: str):
        """Print formatted section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    def print_test(self, name: str, status: str, message: str = ""):
        """Print test result."""
        if status == "PASS":
            icon = f"{Colors.GREEN}✅"
            self.passed += 1
        elif status == "FAIL":
            icon = f"{Colors.RED}❌"
            self.failed += 1
        elif status == "SKIP":
            icon = f"{Colors.YELLOW}⏭️"
            self.skipped += 1
        else:
            icon = "❓"
        
        print(f"{icon} {name:<50} [{status}]{Colors.END}")
        if message:
            print(f"   {Colors.YELLOW}{message}{Colors.END}")
    
    def test_server_health(self) -> bool:
        """Test 1: Server health check."""
        self.print_header("Phase 1: Server Health")
        
        try:
            response = self.session.get(f"{self.server_url}/api/v2/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Server health endpoint", "PASS", f"Version: {data.get('version', 'unknown')}")
                return True
            else:
                self.print_test("Server health endpoint", "FAIL", f"Status: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_test("Server health endpoint", "FAIL", "Connection refused - is server running?")
            return False
        except Exception as e:
            self.print_test("Server health endpoint", "FAIL", str(e))
            return False
    
    def test_api_v2_endpoints(self) -> bool:
        """Test 2: API v2 core endpoints."""
        self.print_header("Phase 2: API v2 Endpoints")
        
        endpoints = [
            ("GET", "/api/v2/agents", "List agents"),
            ("GET", "/api/v2/operations", "List operations"),
            ("GET", "/api/v2/abilities", "List abilities"),
            ("GET", "/api/v2/adversaries", "List adversaries"),
            ("GET", "/api/v2/objectives", "List objectives"),
            ("GET", "/api/v2/planners", "List planners"),
            ("GET", "/api/v2/sources", "List sources"),
            ("GET", "/api/v2/contacts", "List contacts"),
        ]
        
        all_passed = True
        
        for method, endpoint, description in endpoints:
            try:
                url = urljoin(self.server_url, endpoint)
                response = self.session.request(method, url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 1
                    self.print_test(description, "PASS", f"Found {count} item(s)")
                elif response.status_code == 401:
                    self.print_test(description, "FAIL", "Authentication failed - check API key")
                    all_passed = False
                else:
                    self.print_test(description, "FAIL", f"Status: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.print_test(description, "FAIL", str(e))
                all_passed = False
        
        return all_passed
    
    def test_plugins_loaded(self) -> bool:
        """Test 3: Verify plugins are loaded."""
        self.print_header("Phase 3: Plugin System")
        
        # Check which plugins should be loaded from conf/default.yml
        conf_path = Path("conf/default.yml")
        expected_plugins = ["access", "atomic", "orchestrator", "enrollment"]
        
        all_passed = True
        
        # Test orchestrator plugin
        try:
            response = self.session.get(f"{self.server_url}/plugin/orchestrator/health", timeout=5)
            if response.status_code == 200:
                self.print_test("Orchestrator plugin loaded", "PASS")
            else:
                self.print_test("Orchestrator plugin loaded", "FAIL", f"Status: {response.status_code}")
                all_passed = False
        except Exception as e:
            self.print_test("Orchestrator plugin loaded", "FAIL", str(e))
            all_passed = False
        
        # Test enrollment plugin
        try:
            response = self.session.get(f"{self.server_url}/plugin/enrollment/health", timeout=5)
            if response.status_code == 200:
                self.print_test("Enrollment plugin loaded", "PASS")
            else:
                self.print_test("Enrollment plugin loaded", "FAIL", f"Status: {response.status_code}")
                all_passed = False
        except Exception as e:
            self.print_test("Enrollment plugin loaded", "FAIL", str(e))
            all_passed = False
        
        return all_passed
    
    def test_orchestrator_cli(self) -> bool:
        """Test 4: Orchestrator CLI functionality."""
        self.print_header("Phase 4: Orchestrator CLI")
        
        if self.quick_mode:
            self.print_test("Campaign list command", "SKIP", "Quick mode enabled")
            return True
        
        all_passed = True
        
        # Test campaign list
        try:
            result = subprocess.run(
                ["python3", "orchestrator/cli.py", "campaign", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.print_test("Campaign list command", "PASS")
            else:
                self.print_test("Campaign list command", "FAIL", result.stderr[:100])
                all_passed = False
                
        except subprocess.TimeoutExpired:
            self.print_test("Campaign list command", "FAIL", "Command timeout")
            all_passed = False
        except Exception as e:
            self.print_test("Campaign list command", "FAIL", str(e))
            all_passed = False
        
        return all_passed
    
    def test_enrollment_api(self) -> bool:
        """Test 5: Enrollment API functionality."""
        self.print_header("Phase 5: Enrollment API")
        
        all_passed = True
        
        # Test enrollment health
        try:
            response = self.session.get(f"{self.server_url}/plugin/enrollment/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test("Enrollment health endpoint", "PASS", 
                              f"Requests: {data.get('requests_count', 0)}")
            else:
                self.print_test("Enrollment health endpoint", "FAIL", f"Status: {response.status_code}")
                all_passed = False
        except Exception as e:
            self.print_test("Enrollment health endpoint", "FAIL", str(e))
            all_passed = False
        
        # Test enrollment request creation (if not quick mode)
        if not self.quick_mode:
            try:
                payload = {
                    "platform": "darwin",
                    "campaign_id": "integration-test",
                    "tags": ["integration-test"],
                    "hostname": "test-host",
                    "description": "Integration test enrollment"
                }
                
                response = self.session.post(
                    f"{self.server_url}/plugin/enrollment/enroll",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    enrollment_id = data.get('id')
                    self.print_test("Create enrollment request", "PASS", f"ID: {enrollment_id}")
                    
                    # Clean up - delete the test enrollment
                    if enrollment_id:
                        self.session.delete(f"{self.server_url}/plugin/enrollment/enroll/{enrollment_id}")
                else:
                    self.print_test("Create enrollment request", "FAIL", f"Status: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.print_test("Create enrollment request", "FAIL", str(e))
                all_passed = False
        else:
            self.print_test("Create enrollment request", "SKIP", "Quick mode enabled")
        
        return all_passed
    
    def test_webhook_system(self) -> bool:
        """Test 6: Webhook registration and listing."""
        self.print_header("Phase 6: Webhook System")
        
        all_passed = True
        
        # Test webhook listing
        try:
            response = self.session.get(f"{self.server_url}/plugin/orchestrator/webhooks", timeout=5)
            if response.status_code == 200:
                webhooks = response.json()
                count = len(webhooks) if isinstance(webhooks, list) else 0
                self.print_test("List webhooks", "PASS", f"Found {count} webhook(s)")
            else:
                self.print_test("List webhooks", "FAIL", f"Status: {response.status_code}")
                all_passed = False
        except Exception as e:
            self.print_test("List webhooks", "FAIL", str(e))
            all_passed = False
        
        # Test webhook registration (if not quick mode)
        if not self.quick_mode:
            try:
                test_webhook = {
                    "url": "https://webhook.site/integration-test",
                    "exchanges": ["operation"],
                    "queues": ["*"]
                }
                
                response = self.session.post(
                    f"{self.server_url}/plugin/orchestrator/webhooks",
                    json=test_webhook,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    self.print_test("Register webhook", "PASS")
                    
                    # Clean up - unregister the test webhook
                    time.sleep(1)
                    list_response = self.session.get(f"{self.server_url}/plugin/orchestrator/webhooks")
                    if list_response.status_code == 200:
                        webhooks = list_response.json()
                        for wh in webhooks:
                            if wh.get('url') == test_webhook['url']:
                                webhook_id = wh.get('id')
                                if webhook_id:
                                    self.session.delete(f"{self.server_url}/plugin/orchestrator/webhooks/{webhook_id}")
                else:
                    self.print_test("Register webhook", "FAIL", f"Status: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.print_test("Register webhook", "FAIL", str(e))
                all_passed = False
        else:
            self.print_test("Register webhook", "SKIP", "Quick mode enabled")
        
        return all_passed
    
    def test_error_handling(self) -> bool:
        """Test 7: Error handling and helpful messages."""
        self.print_header("Phase 7: Error Handling")
        
        all_passed = True
        
        # Test 404 error
        try:
            response = self.session.get(f"{self.server_url}/api/v2/nonexistent", timeout=5)
            if response.status_code == 404:
                self.print_test("404 Not Found handling", "PASS")
            else:
                self.print_test("404 Not Found handling", "FAIL", f"Expected 404, got {response.status_code}")
                all_passed = False
        except Exception as e:
            self.print_test("404 Not Found handling", "FAIL", str(e))
            all_passed = False
        
        # Test 401 error (wrong API key)
        try:
            bad_session = requests.Session()
            bad_session.headers.update({'KEY': 'INVALID_KEY'})
            bad_session.verify = False
            
            response = bad_session.get(f"{self.server_url}/api/v2/agents", timeout=5)
            if response.status_code == 401:
                self.print_test("401 Unauthorized handling", "PASS")
            else:
                self.print_test("401 Unauthorized handling", "FAIL", f"Expected 401, got {response.status_code}")
                all_passed = False
        except Exception as e:
            self.print_test("401 Unauthorized handling", "FAIL", str(e))
            all_passed = False
        
        return all_passed
    
    def test_dependencies(self) -> bool:
        """Test 8: Dependency checker script."""
        self.print_header("Phase 8: Dependency Validation")
        
        script_path = Path("scripts/check_dependencies.py")
        
        if not script_path.exists():
            self.print_test("Dependency checker exists", "FAIL", "Script not found")
            return False
        
        self.print_test("Dependency checker exists", "PASS")
        
        # Run dependency check (if not quick mode)
        if not self.quick_mode:
            try:
                result = subprocess.run(
                    ["python3", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if "✅" in result.stdout or "All core dependencies satisfied" in result.stdout:
                    self.print_test("Dependency check passes", "PASS")
                    return True
                else:
                    self.print_test("Dependency check passes", "FAIL", "Missing dependencies")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.print_test("Dependency check passes", "FAIL", "Timeout")
                return False
            except Exception as e:
                self.print_test("Dependency check passes", "FAIL", str(e))
                return False
        else:
            self.print_test("Dependency check passes", "SKIP", "Quick mode enabled")
            return True
    
    def run_all_tests(self) -> int:
        """Run all integration tests."""
        print(f"\n{Colors.BOLD}CALDERA Integration Test Suite{Colors.END}")
        print(f"Server: {self.server_url}")
        print(f"Mode: {'Quick' if self.quick_mode else 'Full'}")
        
        # Run tests in sequence
        tests = [
            self.test_server_health,
            self.test_api_v2_endpoints,
            self.test_plugins_loaded,
            self.test_orchestrator_cli,
            self.test_enrollment_api,
            self.test_webhook_system,
            self.test_error_handling,
            self.test_dependencies,
        ]
        
        for test in tests:
            try:
                test()
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
                break
            except Exception as e:
                print(f"\n{Colors.RED}Unexpected error in {test.__name__}: {e}{Colors.END}")
        
        # Print summary
        self.print_header("Test Summary")
        
        total = self.passed + self.failed + self.skipped
        
        print(f"{Colors.GREEN}✅ Passed:  {self.passed}/{total}{Colors.END}")
        print(f"{Colors.RED}❌ Failed:  {self.failed}/{total}{Colors.END}")
        print(f"{Colors.YELLOW}⏭️  Skipped: {self.skipped}/{total}{Colors.END}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed{Colors.END}\n")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run CALDERA integration tests'
    )
    
    parser.add_argument(
        '--server',
        default='http://localhost:8888',
        help='CALDERA server URL (default: http://localhost:8888)'
    )
    parser.add_argument(
        '--api-key',
        default='ADMIN123',
        help='API key for authentication (default: ADMIN123)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Skip long-running tests'
    )
    
    args = parser.parse_args()
    
    tester = IntegrationTest(
        server_url=args.server,
        api_key=args.api_key,
        quick_mode=args.quick
    )
    
    return tester.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
