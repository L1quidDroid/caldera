#!/bin/bash
################################################################################
# Verify Triskele Labs Branding Installation
# Run this on the CALDERA VM to check branding configuration
################################################################################

echo "=========================================================================="
echo "🎨 Triskele Labs Branding Verification Script"
echo "=========================================================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

function check_pass() {
    echo "   ✅ $1"
    ((PASS_COUNT++))
}

function check_fail() {
    echo "   ❌ $1"
    ((FAIL_COUNT++))
}

function check_warn() {
    echo "   ⚠️  $1"
    ((WARN_COUNT++))
}

echo "1️⃣  Plugin Files Check"
echo "-------------------------------------------"
if [ -d ~/caldera/plugins/branding ]; then
    check_pass "Branding plugin directory exists"
    
    # Check key files
    [ -f ~/caldera/plugins/branding/hook.py ] && check_pass "hook.py present" || check_fail "hook.py missing"
    [ -f ~/caldera/plugins/branding/branding_config.yml ] && check_pass "branding_config.yml present" || check_fail "Config missing"
    [ -f ~/caldera/plugins/branding/static/css/triskele_theme.css ] && check_pass "triskele_theme.css present" || check_fail "Theme CSS missing"
    [ -f ~/caldera/plugins/branding/static/css/override.css ] && check_pass "override.css present" || check_fail "Override CSS missing"
    [ -f ~/caldera/plugins/branding/static/img/triskele_logo.svg ] && check_pass "Logo SVG present" || check_fail "Logo missing"
else
    check_fail "Branding plugin directory not found at ~/caldera/plugins/branding"
fi

echo ""
echo "2️⃣  Plugin Configuration Check"
echo "-------------------------------------------"

# Check if branding is in default.yml
if grep -q "^plugins:" ~/caldera/conf/default.yml 2>/dev/null; then
    if grep -A 20 "^plugins:" ~/caldera/conf/default.yml | grep -q "- branding"; then
        check_pass "Branding plugin in default.yml"
    else
        check_fail "Branding plugin not in default.yml plugins list"
    fi
else
    check_warn "Could not find plugins section in default.yml"
fi

# Check if local.yml exists and has branding
if [ -f ~/caldera/conf/local.yml ]; then
    if grep -q "branding" ~/caldera/conf/local.yml; then
        check_pass "Branding referenced in local.yml"
    fi
else
    check_warn "local.yml does not exist (optional)"
fi

echo ""
echo "3️⃣  CALDERA Service Check"
echo "-------------------------------------------"

if systemctl is-active --quiet caldera; then
    check_pass "CALDERA service is running"
    
    # Check if branding plugin loaded in logs
    if sudo journalctl -u caldera -n 100 --no-pager | grep -q "Enabled plugin: branding"; then
        check_pass "Branding plugin loaded in CALDERA"
        
        # Check for theme confirmation
        if sudo journalctl -u caldera -n 100 --no-pager | grep -q "Branding plugin enabled with theme"; then
            THEME=$(sudo journalctl -u caldera -n 100 --no-pager | grep "Branding plugin enabled with theme" | tail -1 | sed -n 's/.*theme: \(\S*\)/\1/p')
            check_pass "Theme active: $THEME"
        fi
    else
        check_fail "Branding plugin not loaded in CALDERA logs"
    fi
else
    check_fail "CALDERA service is not running"
fi

echo ""
echo "4️⃣  Magma Frontend Integration Check"
echo "-------------------------------------------"

MAGMA_DIST_HTML="$HOME/caldera/plugins/magma/dist/index.html"
MAGMA_DEV_HTML="$HOME/caldera/plugins/magma/index.html"

if [ -f "$MAGMA_DIST_HTML" ]; then
    if grep -q "branding.*css" "$MAGMA_DIST_HTML"; then
        BRANDING_LINKS=$(grep -c "branding.*css" "$MAGMA_DIST_HTML")
        check_pass "Magma dist/index.html has branding CSS ($BRANDING_LINKS links)"
        
        # Check for cache-busting
        if grep -q "branding.*css?v=" "$MAGMA_DIST_HTML"; then
            check_pass "Cache-busting version parameter present"
        else
            check_warn "No cache-busting version in CSS links"
        fi
    else
        check_fail "Magma dist/index.html missing branding CSS links"
    fi
else
    check_fail "Magma dist/index.html not found"
fi

if [ -f "$MAGMA_DEV_HTML" ]; then
    if grep -q "branding.*css" "$MAGMA_DEV_HTML"; then
        check_pass "Magma dev index.html has branding CSS"
    else
        check_warn "Magma dev index.html missing branding CSS (dev only)"
    fi
fi

echo ""
echo "5️⃣  HTTP Accessibility Check"
echo "-------------------------------------------"

# Check if CALDERA is listening
if ss -tlnp 2>/dev/null | grep -q ":8888"; then
    check_pass "CALDERA listening on port 8888"
    
    # Test CSS file accessibility
    HTTP_THEME=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/plugin/branding/static/css/triskele_theme.css 2>/dev/null)
    if [ "$HTTP_THEME" = "200" ]; then
        SIZE_THEME=$(curl -s http://localhost:8888/plugin/branding/static/css/triskele_theme.css 2>/dev/null | wc -c)
        check_pass "triskele_theme.css accessible (HTTP 200, ${SIZE_THEME} bytes)"
    else
        check_fail "triskele_theme.css not accessible (HTTP $HTTP_THEME)"
    fi
    
    HTTP_OVERRIDE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/plugin/branding/static/css/override.css 2>/dev/null)
    if [ "$HTTP_OVERRIDE" = "200" ]; then
        SIZE_OVERRIDE=$(curl -s http://localhost:8888/plugin/branding/static/css/override.css 2>/dev/null | wc -c)
        check_pass "override.css accessible (HTTP 200, ${SIZE_OVERRIDE} bytes)"
    else
        check_fail "override.css not accessible (HTTP $HTTP_OVERRIDE)"
    fi
    
    # Test logo
    HTTP_LOGO=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/plugin/branding/static/img/triskele_logo.svg 2>/dev/null)
    if [ "$HTTP_LOGO" = "200" ]; then
        check_pass "Logo SVG accessible (HTTP 200)"
    else
        check_fail "Logo SVG not accessible (HTTP $HTTP_LOGO)"
    fi
    
    # Test main page includes branding
    if curl -s http://localhost:8888/ 2>/dev/null | grep -q "branding.*css"; then
        check_pass "Main page HTML includes branding CSS links"
    else
        check_fail "Main page HTML does not include branding CSS"
    fi
    
else
    check_fail "CALDERA not listening on port 8888"
fi

echo ""
echo "6️⃣  CSS Content Validation"
echo "-------------------------------------------"

if [ -f ~/caldera/plugins/branding/static/css/triskele_theme.css ]; then
    if grep -q ":root" ~/caldera/plugins/branding/static/css/triskele_theme.css; then
        check_pass "CSS variables defined in triskele_theme.css"
    fi
    
    if grep -q "triskele-primary-dark" ~/caldera/plugins/branding/static/css/triskele_theme.css; then
        check_pass "Triskele color variables present"
    fi
fi

if [ -f ~/caldera/plugins/branding/static/css/override.css ]; then
    IMPORTANT_COUNT=$(grep -c "!important" ~/caldera/plugins/branding/static/css/override.css)
    check_pass "Override rules with !important: $IMPORTANT_COUNT"
    
    if grep -q "#navigation" ~/caldera/plugins/branding/static/css/override.css; then
        check_pass "Navigation styling overrides present"
    fi
fi

echo ""
echo "=========================================================================="
echo "📊 Verification Summary"
echo "=========================================================================="
echo ""
echo "   ✅ Passed: $PASS_COUNT"
echo "   ❌ Failed: $FAIL_COUNT"
echo "   ⚠️  Warnings: $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 All critical checks passed!"
    echo ""
    echo "🌐 Access CALDERA with Triskele Labs branding:"
    VM_IP=$(hostname -I | awk '{print $1}')
    echo "   http://$VM_IP:8888"
    echo "   Username: admin"
    echo "   Password: admin"
    echo ""
    echo "Expected Appearance:"
    echo "   • Navy blue background (#020816)"
    echo "   • Cyan/teal accents (#48CFA0)"
    echo "   • Purple navigation highlights (#8b5cf6)"
    echo "   • Triskele Labs logo"
    echo ""
    echo "💡 If branding not visible in browser:"
    echo "   1. Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)"
    echo "   2. Clear browser cache or use incognito/private window"
    echo "   3. Check browser DevTools Console (F12) for CSS errors"
    exit 0
else
    echo "⚠️  Some checks failed. Review the results above."
    echo ""
    echo "🔧 Common Fixes:"
    echo ""
    if [ ! -d ~/caldera/plugins/branding ]; then
        echo "   Missing plugin files:"
        echo "   → Re-upload branding plugin from local machine"
        echo "   → Run: ./upload_branding_plugin.sh <vm-ip>"
    fi
    
    if [ $FAIL_COUNT -gt 0 ]; then
        echo ""
        echo "   To re-integrate branding into Magma:"
        echo "   → Run: ~/caldera/integrate_branding.sh"
        echo "   → Then: sudo systemctl restart caldera"
    fi
    
    echo ""
    echo "   For detailed troubleshooting:"
    echo "   → Check CALDERA logs: sudo journalctl -u caldera -n 100"
    echo "   → Verify plugin loaded: sudo journalctl -u caldera | grep branding"
    echo "   → Check CSS accessibility: curl -I http://localhost:8888/plugin/branding/static/css/triskele_theme.css"
    exit 1
fi
