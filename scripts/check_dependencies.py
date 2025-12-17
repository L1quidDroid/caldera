#!/usr/bin/env python3
"""
CALDERA Dependency Checker
Validates all required and optional dependencies before server start
"""
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple


# Plugin dependency matrix
PLUGIN_DEPENDENCIES = {
    'debrief': {
        'required': ['reportlab', 'svglib'],
        'optional': True,
        'install_hint': 'pip install reportlab svglib',
        'note': 'Legacy PDF reporting - consider using orchestrator plugin instead'
    },
    'emu': {
        'required': [],
        'optional': True,
        'install_hint': 'Requires git clone on startup - ensure internet connectivity',
        'note': 'CTID emulation plans - needs network access on first start'
    },
    'fieldmanual': {
        'required': ['sphinx', 'sphinx_rtd_theme', 'myst_parser'],
        'optional': False,
        'install_hint': 'Already in requirements.txt - run: pip install -r requirements.txt',
        'note': 'Documentation plugin'
    },
    'orchestrator': {
        'required': ['matplotlib', 'numpy', 'weasyprint'],
        'optional': False,
        'install_hint': 'Already in requirements.txt - run: pip install -r requirements.txt',
        'note': 'Campaign management and PDF reporting (Phase 3-6)'
    },
    'training': {
        'required': ['markdown'],
        'optional': False,
        'install_hint': 'Already in requirements.txt - run: pip install -r requirements.txt',
        'note': 'Training and certification plugin'
    },
    'enrollment': {
        'required': [],
        'optional': False,
        'install_hint': 'Uses core dependencies only',
        'note': 'Dynamic agent enrollment (Phase 5)'
    }
}


def check_module(module_name: str) -> bool:
    """Check if a Python module is installed."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def get_enabled_plugins(config_path: str = 'conf/default.yml') -> List[str]:
    """Parse config to get enabled plugins."""
    try:
        import yaml
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"⚠️  Config file not found: {config_path}")
            return []
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        return config.get('plugins', [])
    except Exception as e:
        print(f"⚠️  Error reading config: {e}")
        return []


def check_core_dependencies() -> Tuple[List[str], List[str]]:
    """Check core CALDERA dependencies."""
    core_deps = [
        'aiohttp',
        'aiohttp_jinja2',
        'aiohttp_session',
        'aiohttp_security',
        'jinja2',
        'yaml',
        'cryptography',
        'marshmallow'
    ]
    
    missing = []
    installed = []
    
    for dep in core_deps:
        if check_module(dep):
            installed.append(dep)
        else:
            missing.append(dep)
    
    return installed, missing


def main():
    """Main dependency checking logic."""
    print("🔍 CALDERA Dependency Checker")
    print("=" * 70)
    
    # Check core dependencies first
    print("\n📦 Checking Core Dependencies...")
    installed_core, missing_core = check_core_dependencies()
    
    if missing_core:
        print(f"\n❌ CRITICAL: Missing {len(missing_core)} core dependencies!")
        for dep in missing_core:
            print(f"   ✗ {dep}")
        print("\n💡 To fix: pip install -r requirements.txt")
        print("\nServer cannot start without core dependencies.")
        sys.exit(1)
    else:
        print(f"✅ All {len(installed_core)} core dependencies satisfied")
    
    # Check Python version
    print("\n🐍 Checking Python Version...")
    py_version = sys.version_info
    if py_version.major >= 3 and py_version.minor >= 10:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro} (>= 3.10 required)")
    else:
        print(f"❌ Python {py_version.major}.{py_version.minor}.{py_version.micro} (< 3.10)")
        print("💡 Upgrade Python: https://www.python.org/downloads/")
        sys.exit(1)
    
    # Get enabled plugins
    enabled_plugins = get_enabled_plugins()
    if not enabled_plugins:
        print("\n⚠️  No plugins found in conf/default.yml or file missing")
        print("Server will start with minimal functionality")
        return
    
    print(f"\n📋 Found {len(enabled_plugins)} enabled plugins in conf/default.yml")
    
    # Check plugin dependencies
    missing_deps = []
    warnings = []
    ok_plugins = []
    
    for plugin in enabled_plugins:
        if plugin not in PLUGIN_DEPENDENCIES:
            # Unknown plugin - assume no extra dependencies
            ok_plugins.append(plugin)
            continue
        
        deps = PLUGIN_DEPENDENCIES[plugin]
        
        if not deps['required']:
            # No dependencies needed
            ok_plugins.append(plugin)
            continue
        
        # Check each required dependency
        plugin_ok = True
        for dep in deps['required']:
            if not check_module(dep):
                plugin_ok = False
                if deps['optional']:
                    warnings.append({
                        'plugin': plugin,
                        'dependency': dep,
                        'hint': deps['install_hint'],
                        'note': deps.get('note', '')
                    })
                else:
                    missing_deps.append({
                        'plugin': plugin,
                        'dependency': dep,
                        'hint': deps['install_hint'],
                        'note': deps.get('note', '')
                    })
        
        if plugin_ok:
            ok_plugins.append(plugin)
    
    # Print results
    print("\n" + "=" * 70)
    
    if missing_deps:
        print(f"\n❌ CRITICAL: {len(missing_deps)} missing required dependencies!")
        print("\n📦 Missing Dependencies:")
        
        seen_hints = set()
        for dep in missing_deps:
            print(f"\n   Plugin: {dep['plugin']}")
            print(f"   Missing: {dep['dependency']}")
            if dep['note']:
                print(f"   Note: {dep['note']}")
            
            hint = dep['hint']
            if hint not in seen_hints:
                print(f"   Fix: {hint}")
                seen_hints.add(hint)
        
        print("\n💡 QUICK FIXES:")
        print("   Option 1: Install missing dependencies")
        for hint in seen_hints:
            print(f"      {hint}")
        
        print("\n   Option 2: Disable plugins in conf/default.yml")
        affected_plugins = sorted(set(d['plugin'] for d in missing_deps))
        for plugin in affected_plugins:
            print(f"      # - {plugin}  # Disabled - missing dependencies")
        
        print("\n   Then restart: python server.py --insecure")
        sys.exit(1)
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} optional dependencies missing")
        print("\n📦 Optional Dependencies:")
        
        for warn in warnings:
            print(f"\n   Plugin: {warn['plugin']} (optional)")
            print(f"   Missing: {warn['dependency']}")
            if warn['note']:
                print(f"   Note: {warn['note']}")
            print(f"   Hint: {warn['hint']}")
        
        print("\n💡 Server will start, but these plugins may have limited functionality")
        print("   To install: pip install -r requirements-optional.txt")
    
    if ok_plugins:
        print(f"\n✅ {len(ok_plugins)} plugins ready:")
        for plugin in sorted(ok_plugins):
            print(f"   • {plugin}")
    
    print("\n" + "=" * 70)
    print("✅ Dependency check complete!")
    print("\n🚀 Ready to start server: python server.py --insecure")
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Dependency check cancelled")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
