#!/bin/bash
# Automated Phase 1-4 Test Runner

echo "╔════════════════════════════════════════════════╗"
echo "║   Phase 1-4 Automated Test Suite              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name ... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo "✅ PASS"
        ((PASSED++))
    else
        echo "❌ FAIL"
        ((FAILED++))
    fi
}

# Phase 1 Tests
echo "📦 Phase 1: Campaign Management"
run_test "Campaign schema" "test -f orchestrator/schemas/campaign_spec.schema.json"
run_test "Campaign example" "test -f orchestrator/schemas/campaign_spec_example.yml"
run_test "Campaign object" "test -f app/objects/c_campaign.py"
run_test "Data directory" "test -d data/campaigns || mkdir -p data/campaigns"

# Phase 2 Tests
echo ""
echo "🔧 Phase 2: CLI & Health Checks"
run_test "CLI main" "test -f orchestrator/cli/main.py"
run_test "CLI __init__" "test -f orchestrator/cli/__init__.py"
run_test "Health check" "test -f orchestrator/utils/health_check.py"
run_test "Enrollment generator" "test -f orchestrator/agents/enrollment_generator.py"
run_test "Orchestrator requirements" "test -f orchestrator/requirements.txt"

# Phase 3 Tests
echo ""
echo "📡 Phase 3: Webhooks & SIEM"
run_test "Webhook service" "test -f orchestrator/services/webhook_service.py"
run_test "Services __init__" "test -f orchestrator/services/__init__.py"
run_test "Orchestrator plugin" "test -f plugins/orchestrator/hook.py"
run_test "Orchestrator README" "test -f plugins/orchestrator/README.md"

# Phase 4 Tests
echo ""
echo "🎨 Phase 4: Branding"
run_test "Branding plugin" "test -f plugins/branding/hook.py"
run_test "Branding config" "test -f plugins/branding/branding_config.yml"
run_test "Theme CSS" "test -f plugins/branding/static/css/triskele_theme.css"
run_test "Logo SVG" "test -f plugins/branding/static/img/triskele_logo.svg"
run_test "Login template" "test -f plugins/branding/templates/login.html"
run_test "Admin template" "test -f plugins/branding/templates/branding_admin.html"
run_test "Branding README" "test -f plugins/branding/README.md"

# Documentation Tests
echo ""
echo "📚 Documentation"
run_test "Team presentation" "test -f docs/presentations/team-presentation.md"
run_test "Orchestration guide" "test -f docs/guides/orchestration-guide.md"
run_test "Migration complete" "test -f MIGRATION_COMPLETE.md"
run_test "Testing guide" "test -f TESTING_GUIDE.md"

# Summary
echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║   Test Summary                                 ║"
echo "╚════════════════════════════════════════════════╝"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed!"
    echo ""
    echo "Next steps:"
    echo "  1. Test imports: python3 -c 'import sys; sys.path.insert(0, \"orchestrator\"); from services.webhook_service import WebhookPublisher'"
    echo "  2. Run health check: python3 -m orchestrator.utils.health_check"
    echo "  3. Start Caldera: python3 server.py"
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Review output above."
    exit 1
fi
