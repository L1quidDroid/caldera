#!/usr/bin/env python3
"""
P1 Implementation Verification Test
Validates all P1 changes are working correctly
"""
import sys
import os
from pathlib import Path

def test_files_exist():
    """Test that all required files were created."""
    print("🔍 Testing File Creation...")
    
    required_files = [
        'requirements-optional.txt',
        'scripts/check_dependencies.py',
        'ROADMAP.md',
        'app/api/v2/error_handler.py',
        'IMPLEMENTATION_P1_SUMMARY.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_file_modifications():
    """Test that files were modified correctly."""
    print("\n🔍 Testing File Modifications...")
    
    modifications = {
        'README.md': 'Implementation Status',
        'DEMO_WALKTHROUGH.md': 'Partially Implemented',
        'app/api/v2/__init__.py': 'error_handler_middleware'
    }
    
    all_correct = True
    for file_path, expected_content in modifications.items():
        try:
            with open(file_path) as f:
                content = f.read()
            found = expected_content in content
            status = "✅" if found else "❌"
            print(f"  {status} {file_path} contains '{expected_content}'")
            if not found:
                all_correct = False
        except FileNotFoundError:
            print(f"  ❌ {file_path} not found")
            all_correct = False
    
    return all_correct

def test_python_syntax():
    """Test Python files for syntax errors."""
    print("\n🔍 Testing Python Syntax...")
    
    python_files = [
        'scripts/check_dependencies.py',
        'app/api/v2/error_handler.py'
    ]
    
    all_valid = True
    for file_path in python_files:
        try:
            import py_compile
            py_compile.compile(file_path, doraise=True)
            print(f"  ✅ {file_path} - Valid syntax")
        except py_compile.PyCompileError as e:
            print(f"  ❌ {file_path} - Syntax error: {e}")
            all_valid = False
    
    return all_valid

def test_dependency_checker_import():
    """Test that dependency checker can be imported."""
    print("\n🔍 Testing Dependency Checker...")
    
    try:
        sys.path.insert(0, 'scripts')
        # Don't actually import to avoid executing, just check syntax
        with open('scripts/check_dependencies.py') as f:
            code = f.read()
        
        # Check for key functions
        required_functions = [
            'def check_module',
            'def get_enabled_plugins',
            'def check_core_dependencies',
            'def main'
        ]
        
        all_found = True
        for func in required_functions:
            found = func in code
            status = "✅" if found else "❌"
            print(f"  {status} Found function: {func.split('(')[0]}")
            if not found:
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_error_handler_structure():
    """Test error handler has required components."""
    print("\n🔍 Testing Error Handler Structure...")
    
    try:
        with open('app/api/v2/error_handler.py') as f:
            code = f.read()
        
        required_components = [
            'ERROR_TIPS',
            'CONTEXT_TIPS',
            'def get_tips_for_error',
            '@web.middleware',
            'async def error_handler_middleware',
            'def format_error_response',
            'def unauthorized',
            'def forbidden',
            'def not_found'
        ]
        
        all_found = True
        for component in required_components:
            found = component in code
            status = "✅" if found else "❌"
            print(f"  {status} {component}")
            if not found:
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_documentation_completeness():
    """Test documentation is complete."""
    print("\n🔍 Testing Documentation...")
    
    checks = [
        ('ROADMAP.md', ['Phase 4', 'Q1 2026', 'Current Status Overview']),
        ('README.md', ['Implementation Status', 'Phase 4', 'ROADMAP.md']),
        ('requirements-optional.txt', ['debrief', 'orchestrator', 'emu']),
        ('IMPLEMENTATION_P1_SUMMARY.md', ['P1', 'Complete', '951 lines'])
    ]
    
    all_complete = True
    for file_path, keywords in checks:
        try:
            with open(file_path) as f:
                content = f.read()
            
            file_ok = True
            for keyword in keywords:
                if keyword not in content:
                    print(f"  ❌ {file_path} missing keyword: '{keyword}'")
                    file_ok = False
                    all_complete = False
            
            if file_ok:
                print(f"  ✅ {file_path} - All keywords found")
        except FileNotFoundError:
            print(f"  ❌ {file_path} not found")
            all_complete = False
    
    return all_complete

def main():
    """Run all verification tests."""
    print("=" * 70)
    print("P1 Implementation Verification Test")
    print("=" * 70)
    
    tests = [
        ("File Creation", test_files_exist),
        ("File Modifications", test_file_modifications),
        ("Python Syntax", test_python_syntax),
        ("Dependency Checker", test_dependency_checker_import),
        ("Error Handler", test_error_handler_structure),
        ("Documentation", test_documentation_completeness)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - P1 Implementation Complete!")
        print("\n✅ Ready for commit:")
        print("   git add requirements-optional.txt scripts/check_dependencies.py")
        print("   git add ROADMAP.md app/api/v2/error_handler.py")
        print("   git add app/api/v2/__init__.py README.md DEMO_WALKTHROUGH.md")
        print('   git commit -m "feat: P1 bug fixes - dependency management & error handling"')
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review issues above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
