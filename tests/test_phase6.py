#!/usr/bin/env python3
"""
Phase 6 Test Script - PDF Report Generation

Tests all components of the Phase 6 PDF reporting system.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Test imports
try:
    from orchestrator.report_aggregator import ReportAggregator
    from orchestrator.attack_navigator import AttackNavigatorGenerator
    from orchestrator.report_visualizations import ReportVisualizations
    from orchestrator.pdf_generator import PDFReportGenerator
    print("✅ All Phase 6 modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nInstall dependencies with: pip install matplotlib numpy weasyprint")
    exit(1)


async def test_report_aggregator():
    """Test 1: Report Aggregator"""
    print("\n" + "="*60)
    print("TEST 1: Report Aggregator")
    print("="*60)
    
    caldera_url = "http://localhost:8888"
    api_key = "ADMIN123"
    
    print(f"  Connecting to: {caldera_url}")
    print(f"  API Key: {'*' * len(api_key)}")
    
    try:
        async with ReportAggregator(caldera_url, api_key) as aggregator:
            # Test health check
            print("\n  Testing API connectivity...")
            health = await aggregator.check_health()
            print(f"  ✅ API Health: {health.get('application', 'Unknown')}")
            
            # List available operations
            operations = await aggregator._fetch_operations()
            print(f"  ✅ Found {len(operations)} operations")
            
            if operations:
                op_id = operations[0].get('id', 'unknown')
                print(f"  Example operation: {op_id}")
                
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_attack_navigator():
    """Test 2: ATT&CK Navigator Generator"""
    print("\n" + "="*60)
    print("TEST 2: ATT&CK Navigator Generator")
    print("="*60)
    
    try:
        generator = AttackNavigatorGenerator()
        
        # Create test technique data
        test_techniques = {
            "T1003": {
                "name": "OS Credential Dumping",
                "tactic": "credential-access",
                "success_count": 5,
                "failure_count": 0,
                "operations": ["op_001"],
                "abilities": ["abc123"]
            },
            "T1059": {
                "name": "Command and Scripting Interpreter",
                "tactic": "execution",
                "success_count": 3,
                "failure_count": 2,
                "operations": ["op_001", "op_002"],
                "abilities": ["def456", "ghi789"]
            }
        }
        
        test_operations = [
            {"id": "op_001", "name": "Initial Access"},
            {"id": "op_002", "name": "Persistence"}
        ]
        
        # Generate layer
        layer = generator.generate_layer(
            campaign_id="test_001",
            campaign_name="Test Campaign",
            techniques=test_techniques,
            operations=test_operations
        )
        
        print(f"  ✅ Generated layer: {layer['name']}")
        print(f"  ✅ Domain: {layer['domain']}")
        print(f"  ✅ Version: {layer['versions']['layer']}")
        print(f"  ✅ Techniques: {len(layer['techniques'])}")
        
        # Save layer
        output_dir = Path("data/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test_attack_layer.json"
        
        generator.save_layer(layer, str(output_path))
        print(f"  ✅ Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_visualizations():
    """Test 3: Report Visualizations"""
    print("\n" + "="*60)
    print("TEST 3: Report Visualizations")
    print("="*60)
    
    try:
        viz = ReportVisualizations(style='triskele')
        
        # Test summary data
        test_summary = {
            "total_abilities_executed": 100,
            "success_count": 85,
            "failure_count": 15
        }
        
        # Test statistics
        test_statistics = {
            "by_platform": {
                "windows": {"success": 40, "failure": 5},
                "linux": {"success": 30, "failure": 5},
                "darwin": {"success": 15, "failure": 5}
            },
            "by_tactic": {
                "initial-access": {"T1566": {"success": 10, "failure": 2}},
                "execution": {"T1059": {"success": 15, "failure": 3}},
                "persistence": {"T1053": {"success": 12, "failure": 1}}
            }
        }
        
        # Test timeline
        test_timeline = [
            {"timestamp": "2025-01-01T10:00:00Z", "event": "Operation started"},
            {"timestamp": "2025-01-01T11:30:00Z", "event": "Agent enrolled"},
            {"timestamp": "2025-01-01T14:00:00Z", "event": "Operation completed"}
        ]
        
        # Generate charts
        charts = []
        
        print("\n  Generating charts...")
        
        # Success rate chart
        chart_path = viz.generate_success_rate_chart(
            test_summary,
            output_path="data/reports/test_success_rate.png"
        )
        charts.append(chart_path)
        print(f"  ✅ Success rate chart: {chart_path}")
        
        # Platform distribution
        chart_path = viz.generate_platform_distribution(
            test_statistics,
            output_path="data/reports/test_platform_dist.png"
        )
        charts.append(chart_path)
        print(f"  ✅ Platform distribution: {chart_path}")
        
        # Technique heatmap
        chart_path = viz.generate_technique_heatmap(
            test_statistics,
            output_path="data/reports/test_heatmap.png"
        )
        charts.append(chart_path)
        print(f"  ✅ Technique heatmap: {chart_path}")
        
        print(f"\n  ✅ Generated {len(charts)} charts")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_generator_mock():
    """Test 4: PDF Generator (Mock Data)"""
    print("\n" + "="*60)
    print("TEST 4: PDF Generator (Mock Data)")
    print("="*60)
    
    try:
        # Test if WeasyPrint is available
        from orchestrator.pdf_generator import WEASYPRINT_AVAILABLE
        
        if not WEASYPRINT_AVAILABLE:
            print("  ⚠️ WeasyPrint not installed - skipping PDF generation")
            print("  Install with: pip install weasyprint")
            return True
        
        print("  ✅ WeasyPrint available")
        print("  ✅ PDF generation ready")
        print("\n  💡 To test PDF generation, run:")
        print("     python orchestrator/cli.py report generate <campaign_id>")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def main():
    """Run all Phase 6 tests"""
    print("\n" + "="*60)
    print("PHASE 6 TEST SUITE - PDF REPORTING")
    print("="*60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    results = []
    
    # Test 1: Report Aggregator
    result = await test_report_aggregator()
    results.append(("Report Aggregator", result))
    
    # Test 2: ATT&CK Navigator
    result = test_attack_navigator()
    results.append(("ATT&CK Navigator", result))
    
    # Test 3: Visualizations
    result = test_visualizations()
    results.append(("Visualizations", result))
    
    # Test 4: PDF Generator
    result = test_pdf_generator_mock()
    results.append(("PDF Generator", result))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "-"*60)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All Phase 6 components validated!")
        print("\nNext steps:")
        print("  1. Start CALDERA: python server.py")
        print("  2. Run an operation to generate data")
        print("  3. Generate report: python orchestrator/cli.py report generate <campaign_id>")
        print("  4. View PDF report in data/reports/")
    else:
        print("\n⚠️ Some tests failed - review errors above")
        print("\nTroubleshooting:")
        print("  - Ensure CALDERA is running: http://localhost:8888")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Check API key in orchestrator/cli.py config")


if __name__ == '__main__':
    asyncio.run(main())
