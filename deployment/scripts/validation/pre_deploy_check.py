#!/usr/bin/env python3
"""
Pre-Deployment Validation Script

Validates Caldera project configuration, schemas, and dependencies before deployment.
Run this script before provisioning infrastructure to catch configuration issues early.

Usage:
    python3 pre_deploy_check.py [--config=conf/local.yml] [--verbose]
    python3 pre_deploy_check.py --check-all
    
Exit codes:
    0 - All checks passed
    1 - Critical errors found (deployment will fail)
    2 - Warnings found (deployment may have issues)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not installed. Schema validation will be skipped.")
    print("Run: pip install jsonschema")


# ANSI colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class PreDeployValidator:
    """Comprehensive pre-deployment validation for Caldera project."""

    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.errors: List[Tuple[str, str]] = []  # (category, message)
        self.warnings: List[Tuple[str, str]] = []
        self.passed: List[Tuple[str, str]] = []

    def log(self, level: str, category: str, message: str):
        """Log a validation result."""
        if level == 'error':
            self.errors.append((category, message))
            print(f"  {Colors.RED}✗{Colors.RESET} {message}")
        elif level == 'warning':
            self.warnings.append((category, message))
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} {message}")
        elif level == 'pass':
            self.passed.append((category, message))
            if self.verbose:
                print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")

    def section(self, title: str):
        """Print section header."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}▸ {title}{Colors.RESET}")

    # =========================================================================
    # CONFIGURATION VALIDATION
    # =========================================================================

    def check_config_files(self) -> bool:
        """Validate Caldera configuration files."""
        self.section("Configuration Files")
        
        configs = {
            'default.yml': self.project_root / 'conf' / 'default.yml',
            'local.yml': self.project_root / 'conf' / 'local.yml',
            'agents.yml': self.project_root / 'conf' / 'agents.yml',
        }
        
        for name, path in configs.items():
            if not path.exists():
                if name == 'local.yml':
                    self.log('warning', 'config', f"Missing {name} - using default.yml only")
                else:
                    self.log('error', 'config', f"Missing required config: {name}")
                continue
            
            try:
                with open(path) as f:
                    config = yaml.safe_load(f)
                self.log('pass', 'config', f"{name} is valid YAML")
                
                # Check for default credentials
                if name in ('default.yml', 'local.yml'):
                    self._check_credentials(config, name)
                    
            except yaml.YAMLError as e:
                self.log('error', 'config', f"Invalid YAML in {name}: {e}")
        
        return len([e for e in self.errors if e[0] == 'config']) == 0

    def _check_credentials(self, config: Dict, filename: str):
        """Check for insecure default credentials."""
        insecure_defaults = {
            'api_key_red': ['ADMIN123', 'admin', 'test', 'changeme'],
            'api_key_blue': ['BLUEADMIN123', 'admin', 'test', 'changeme'],
            'encryption_key': ['ADMIN123', 'admin', 'test', 'changeme', ''],
            'crypt_salt': ['REPLACE_WITH_RANDOM_VALUE', 'changeme', ''],
        }
        
        for key, bad_values in insecure_defaults.items():
            value = config.get(key, '')
            if value in bad_values:
                if filename == 'default.yml':
                    self.log('warning', 'security', 
                             f"Insecure default for {key} in {filename} (OK if overridden in local.yml)")
                else:
                    self.log('error', 'security', 
                             f"Insecure credential: {key} in {filename} - generate a secure random value")
            else:
                self.log('pass', 'security', f"Secure {key} in {filename}")

    # =========================================================================
    # PLUGIN VALIDATION
    # =========================================================================

    def check_plugins(self) -> bool:
        """Validate plugin configuration and existence."""
        self.section("Plugin Configuration")
        
        local_config_path = self.project_root / 'conf' / 'local.yml'
        default_config_path = self.project_root / 'conf' / 'default.yml'
        
        # Load active config
        config_path = local_config_path if local_config_path.exists() else default_config_path
        
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            self.log('error', 'plugins', f"Cannot read config: {e}")
            return False
        
        enabled_plugins = config.get('plugins', [])
        plugins_dir = self.project_root / 'plugins'
        
        # Required custom plugins
        required_plugins = ['enrollment', 'orchestrator']
        for plugin in required_plugins:
            if plugin not in enabled_plugins:
                self.log('warning', 'plugins', 
                         f"Custom plugin '{plugin}' not in enabled plugins list")
            else:
                self.log('pass', 'plugins', f"Custom plugin '{plugin}' is enabled")
        
        # Verify plugin directories exist
        for plugin in enabled_plugins:
            plugin_path = plugins_dir / plugin
            if not plugin_path.exists():
                self.log('error', 'plugins', f"Plugin directory not found: {plugin}")
            elif not (plugin_path / 'hook.py').exists() and not (plugin_path / '__init__.py').exists():
                self.log('error', 'plugins', f"Plugin missing hook.py or __init__.py: {plugin}")
            else:
                self.log('pass', 'plugins', f"Plugin '{plugin}' structure valid")
        
        return len([e for e in self.errors if e[0] == 'plugins']) == 0

    # =========================================================================
    # SCHEMA VALIDATION
    # =========================================================================

    def check_schemas(self) -> bool:
        """Validate YAML/JSON files against schemas."""
        self.section("Schema Validation")
        
        if not HAS_JSONSCHEMA:
            self.log('warning', 'schemas', "jsonschema not installed - skipping schema validation")
            return True
        
        # Load campaign schema
        schema_path = self.project_root / 'orchestrator' / 'schemas' / 'campaign_spec.schema.json'
        if not schema_path.exists():
            self.log('warning', 'schemas', "Campaign schema not found")
            return True
        
        try:
            with open(schema_path) as f:
                campaign_schema = json.load(f)
            self.log('pass', 'schemas', "Campaign schema loaded successfully")
        except Exception as e:
            self.log('error', 'schemas', f"Invalid campaign schema: {e}")
            return False
        
        # Validate example campaign specs
        examples_dir = self.project_root / 'orchestrator' / 'examples'
        if examples_dir.exists():
            for spec_file in examples_dir.glob('*.yml'):
                self._validate_against_schema(spec_file, campaign_schema, 'campaign')
            for spec_file in examples_dir.glob('*.yaml'):
                self._validate_against_schema(spec_file, campaign_schema, 'campaign')
        
        return len([e for e in self.errors if e[0] == 'schemas']) == 0

    def _validate_against_schema(self, file_path: Path, schema: Dict, schema_type: str):
        """Validate a YAML/JSON file against a schema."""
        try:
            with open(file_path) as f:
                if file_path.suffix in ('.yml', '.yaml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            validate(instance=data, schema=schema)
            self.log('pass', 'schemas', f"{file_path.name} validates against {schema_type} schema")
            
        except ValidationError as e:
            self.log('error', 'schemas', 
                     f"{file_path.name} schema error: {e.message} at {'/'.join(str(p) for p in e.absolute_path)}")
        except Exception as e:
            self.log('warning', 'schemas', f"Cannot validate {file_path.name}: {e}")

    # =========================================================================
    # ABILITY & ADVERSARY VALIDATION
    # =========================================================================

    def check_abilities(self) -> bool:
        """Validate ability YAML files for MITRE ATT&CK format."""
        self.section("Abilities & Adversaries")
        
        abilities_dir = self.project_root / 'data' / 'abilities'
        stockpile_abilities = self.project_root / 'plugins' / 'stockpile' / 'data' / 'abilities'
        
        ability_count = 0
        
        for abilities_path in [abilities_dir, stockpile_abilities]:
            if not abilities_path.exists():
                continue
            
            for ability_file in abilities_path.rglob('*.yml'):
                ability_count += 1
                self._validate_ability(ability_file)
        
        if ability_count == 0:
            self.log('warning', 'abilities', "No ability files found - using plugin defaults")
        else:
            self.log('pass', 'abilities', f"Found {ability_count} ability files")
        
        return len([e for e in self.errors if e[0] == 'abilities']) == 0

    def _validate_ability(self, file_path: Path):
        """Validate a single ability YAML file."""
        try:
            with open(file_path) as f:
                abilities = yaml.safe_load(f)
            
            if not abilities:
                return
            
            # Handle list of abilities or single ability
            if isinstance(abilities, dict):
                abilities = [abilities]
            
            for ability in abilities:
                if not isinstance(ability, dict):
                    continue
                
                # Check required fields
                required = ['id', 'name', 'tactic', 'technique']
                for field in required:
                    if field not in ability:
                        self.log('warning', 'abilities', 
                                 f"{file_path.name}: missing '{field}' field")
                
                # Validate technique ID format (T1xxx or T1xxx.xxx)
                technique_id = ability.get('technique', {})
                if isinstance(technique_id, dict):
                    technique_id = technique_id.get('attack_id', '')
                
                if technique_id and not re.match(r'^T\d{4}(\.\d{3})?$', str(technique_id)):
                    self.log('warning', 'abilities',
                             f"{file_path.name}: invalid technique ID format: {technique_id}")
                
                # Check executors
                executors = ability.get('executors', [])
                valid_platforms = ['windows', 'linux', 'darwin']
                for executor in executors:
                    platform = executor.get('platform', '')
                    if platform and platform not in valid_platforms:
                        self.log('warning', 'abilities',
                                 f"{file_path.name}: unknown platform: {platform}")
                
        except yaml.YAMLError as e:
            self.log('error', 'abilities', f"Invalid YAML in {file_path.name}: {e}")
        except Exception as e:
            self.log('warning', 'abilities', f"Cannot validate {file_path.name}: {e}")

    # =========================================================================
    # DOCKER VALIDATION
    # =========================================================================

    def check_docker(self) -> bool:
        """Validate Docker configuration."""
        self.section("Docker Configuration")
        
        # Check Dockerfile
        dockerfile = self.project_root / 'Dockerfile'
        if not dockerfile.exists():
            self.log('error', 'docker', "Dockerfile not found")
        else:
            self.log('pass', 'docker', "Dockerfile exists")
            
            with open(dockerfile) as f:
                content = f.read()
            
            # Check for security concerns
            if '--insecure' in content:
                self.log('warning', 'docker', "Dockerfile contains --insecure flag")
            
            if 'COPY . .' in content or 'ADD . .' in content:
                self.log('pass', 'docker', "Copies full context (includes custom plugins)")
        
        # Check docker-compose.yml
        compose = self.project_root / 'docker-compose.yml'
        if compose.exists():
            try:
                with open(compose) as f:
                    compose_config = yaml.safe_load(f)
                self.log('pass', 'docker', "docker-compose.yml is valid YAML")
                
                # Check for environment variable usage
                services = compose_config.get('services', {})
                for svc_name, svc_config in services.items():
                    env_vars = svc_config.get('environment', [])
                    if env_vars:
                        self.log('pass', 'docker', f"Service '{svc_name}' uses environment variables")
                    
            except Exception as e:
                self.log('error', 'docker', f"Invalid docker-compose.yml: {e}")
        
        return len([e for e in self.errors if e[0] == 'docker']) == 0

    # =========================================================================
    # ENVIRONMENT VALIDATION
    # =========================================================================

    def check_environment(self) -> bool:
        """Check environment configuration."""
        self.section("Environment Configuration")
        
        # Check for .env file
        env_file = self.project_root / '.env'
        env_template = self.project_root / '.env.template'
        
        if env_template.exists():
            self.log('pass', 'env', ".env.template exists for reference")
        
        if not env_file.exists():
            self.log('warning', 'env', 
                     "No .env file found - ensure environment variables are set for production")
        else:
            self.log('pass', 'env', ".env file exists")
            
            # Check if it's a copy of template (all empty values)
            with open(env_file) as f:
                content = f.read()
            
            empty_count = content.count('=\n') + content.count('=""')
            if empty_count > 5:
                self.log('warning', 'env', 
                         f".env has {empty_count} empty values - ensure secrets are configured")
        
        # Check critical environment variables
        critical_vars = [
            'CALDERA_API_KEY_RED',
            'CALDERA_API_KEY_BLUE',
            'CALDERA_ENCRYPTION_KEY',
        ]
        
        for var in critical_vars:
            value = os.getenv(var, '')
            if not value:
                self.log('warning', 'env', f"Environment variable {var} not set")
            elif value in ['ADMIN123', 'changeme', 'test']:
                self.log('error', 'env', f"Insecure value for {var}")
            else:
                self.log('pass', 'env', f"{var} is set")
        
        return len([e for e in self.errors if e[0] == 'env']) == 0

    # =========================================================================
    # DEPLOYMENT SCRIPTS VALIDATION
    # =========================================================================

    def check_deployment_scripts(self) -> bool:
        """Validate deployment scripts."""
        self.section("Deployment Scripts")
        
        bicep_dir = self.project_root / 'bicep'
        scripts_dir = bicep_dir / 'scripts'
        
        if not bicep_dir.exists():
            self.log('warning', 'deploy', "No bicep directory found")
            return True
        
        # Check Bicep files
        main_bicep = bicep_dir / 'main.bicep'
        if main_bicep.exists():
            self.log('pass', 'deploy', "main.bicep exists")
            
            with open(main_bicep) as f:
                content = f.read()
            
            # Check for @secure() on sensitive params
            if 'param adminPassword string' in content and '@secure()' not in content:
                self.log('warning', 'deploy', "adminPassword parameter should use @secure()")
            else:
                self.log('pass', 'deploy', "Bicep uses @secure() for sensitive parameters")
        
        # Check parameter files
        params_dir = bicep_dir / 'parameters'
        if params_dir.exists():
            for param_file in params_dir.glob('*.json'):
                with open(param_file) as f:
                    try:
                        params = json.load(f)
                        # Check for hardcoded secrets
                        params_str = json.dumps(params)
                        if 'password' in params_str.lower():
                            self.log('warning', 'deploy', 
                                     f"{param_file.name} may contain hardcoded passwords - use Key Vault references")
                        else:
                            self.log('pass', 'deploy', f"{param_file.name} validated")
                    except Exception as e:
                        self.log('error', 'deploy', f"Invalid JSON in {param_file.name}: {e}")
        
        # Check deployment scripts
        if scripts_dir.exists():
            for script in scripts_dir.glob('*.sh'):
                with open(script) as f:
                    content = f.read()
                
                if 'set -e' in content or 'set -euo pipefail' in content:
                    self.log('pass', 'deploy', f"{script.name} uses strict error handling")
                else:
                    self.log('warning', 'deploy', f"{script.name} missing strict error handling (set -e)")
        
        return len([e for e in self.errors if e[0] == 'deploy']) == 0

    # =========================================================================
    # MAIN RUNNER
    # =========================================================================

    def run_all_checks(self) -> int:
        """Run all validation checks."""
        print(f"\n{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"{Colors.BOLD}  Caldera Pre-Deployment Validation{Colors.RESET}")
        print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"  Project: {self.project_root}")
        
        self.check_config_files()
        self.check_plugins()
        self.check_schemas()
        self.check_abilities()
        self.check_docker()
        self.check_environment()
        self.check_deployment_scripts()
        
        # Summary
        print(f"\n{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"{Colors.BOLD}  Summary{Colors.RESET}")
        print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.RESET}")
        
        print(f"  {Colors.GREEN}✓ Passed:{Colors.RESET}   {len(self.passed)}")
        print(f"  {Colors.YELLOW}⚠ Warnings:{Colors.RESET} {len(self.warnings)}")
        print(f"  {Colors.RED}✗ Errors:{Colors.RESET}   {len(self.errors)}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Critical issues found - deployment may fail:{Colors.RESET}")
            for category, msg in self.errors:
                print(f"  [{category}] {msg}")
            return 1
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings found - review before deployment{Colors.RESET}")
            return 2
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}All checks passed! Ready for deployment.{Colors.RESET}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Pre-deployment validation for Caldera project'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path(__file__).parent.parent.parent.parent,
        help='Path to Caldera project root'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show all passed checks'
    )
    parser.add_argument(
        '--check-all',
        action='store_true',
        help='Run all checks (default)'
    )
    
    args = parser.parse_args()
    
    # Resolve project root
    project_root = args.project_root.resolve()
    
    # Verify it's a Caldera project
    if not (project_root / 'server.py').exists():
        print(f"Error: {project_root} does not appear to be a Caldera project")
        print("Expected to find server.py in project root")
        sys.exit(1)
    
    validator = PreDeployValidator(project_root, verbose=args.verbose)
    exit_code = validator.run_all_checks()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
