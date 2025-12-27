#!/usr/bin/env python3
"""
Safety Validator - Test Mode Enforcement & Governance

Implements safety rails for Caldera operations:
- Test mode enforcement (prevents production operations by default)
- Mandatory scoping fields validation
- High-risk operation blocking
- Audit logging for all executions

Part of the governance module for purple team safety.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class RiskLevel(Enum):
    """Risk classification for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationResult(Enum):
    """Validation outcome."""
    APPROVED = "approved"
    BLOCKED = "blocked"
    WARNING = "warning"


@dataclass
class OperationScope:
    """
    Mandatory scoping fields for all operations.
    
    Required for production operations; optional for test mode.
    """
    environment: str  # 'lab', 'staging', 'production'
    ticket_id: Optional[str] = None  # Change ticket or approval ID
    owner: Optional[str] = None  # Person responsible for operation
    justification: Optional[str] = None  # Business justification
    expiry_time: Optional[str] = None  # ISO timestamp when approval expires
    approved_by: Optional[str] = None  # Approver name/email
    
    def is_complete(self) -> Tuple[bool, List[str]]:
        """Check if all required fields are populated."""
        missing = []
        
        if not self.environment:
            missing.append('environment')
        if self.environment == 'production':
            if not self.ticket_id:
                missing.append('ticket_id')
            if not self.owner:
                missing.append('owner')
            if not self.justification:
                missing.append('justification')
            if not self.approved_by:
                missing.append('approved_by')
        
        return len(missing) == 0, missing


@dataclass
class AuditEntry:
    """Audit log entry for operation executions."""
    timestamp: str
    operation_id: str
    operation_name: str
    action: str  # 'start', 'complete', 'blocked', 'warning'
    user: str
    scope: Dict[str, Any]
    validation_result: str
    risk_level: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class SafetyValidator:
    """
    Safety validator for Caldera operations.
    
    Enforces:
    - Test mode by default (TEST_MODE=true)
    - Mandatory scoping for production operations
    - High-risk technique blocking
    - Comprehensive audit logging
    """
    
    # Techniques considered high-risk and require explicit override
    HIGH_RISK_TECHNIQUES = {
        'T1485': 'Data Destruction',
        'T1486': 'Data Encrypted for Impact',
        'T1490': 'Inhibit System Recovery',
        'T1489': 'Service Stop',
        'T1561': 'Disk Wipe',
        'T1495': 'Firmware Corruption',
        'T1529': 'System Shutdown/Reboot',
        'T1531': 'Account Access Removal',
    }
    
    # Techniques that require additional approval
    ELEVATED_RISK_TECHNIQUES = {
        'T1003': 'OS Credential Dumping',
        'T1098': 'Account Manipulation',
        'T1136': 'Create Account',
        'T1531': 'Account Access Removal',
        'T1070': 'Indicator Removal',
        'T1562': 'Impair Defenses',
        'T1556': 'Modify Authentication Process',
    }
    
    def __init__(
        self,
        test_mode: bool = None,
        audit_log_path: str = './logs/audit.jsonl',
        config_path: str = None
    ):
        """
        Initialize safety validator.
        
        Args:
            test_mode: Force test mode (overrides environment). None = use env var.
            audit_log_path: Path to audit log file
            config_path: Optional path to governance config YAML
        """
        self.log = logging.getLogger('safety_validator')
        
        # Determine test mode
        if test_mode is not None:
            self.test_mode = test_mode
        else:
            self.test_mode = os.getenv('TEST_MODE', 'true').lower() in ('true', '1', 'yes')
        
        # Set up audit logging
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load config if provided
        self.config = self._load_config(config_path) if config_path else {}
        
        # Override lists from config
        if self.config.get('high_risk_techniques'):
            self.HIGH_RISK_TECHNIQUES.update(self.config['high_risk_techniques'])
        
        self.log.info(f"SafetyValidator initialized (test_mode={self.test_mode})")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load governance configuration from YAML."""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.log.warning(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def validate_operation(
        self,
        operation_id: str,
        operation_name: str,
        adversary_name: str,
        techniques: List[str],
        scope: OperationScope,
        user: str = 'system',
        force_override: bool = False
    ) -> Tuple[ValidationResult, str, Dict[str, Any]]:
        """
        Validate an operation before execution.
        
        Args:
            operation_id: Unique operation identifier
            operation_name: Human-readable operation name
            adversary_name: Adversary profile being used
            techniques: List of ATT&CK technique IDs to execute
            scope: Operation scoping information
            user: User initiating the operation
            force_override: Force execution despite warnings (requires approval)
        
        Returns:
            Tuple of (ValidationResult, message, details)
        """
        details = {
            'test_mode': self.test_mode,
            'techniques_count': len(techniques),
            'high_risk_blocked': [],
            'elevated_risk_warning': [],
            'scope_validation': {}
        }
        
        # Check 1: Test mode enforcement
        if self.test_mode:
            if scope.environment == 'production':
                self._audit(
                    operation_id, operation_name, 'blocked', user, scope,
                    ValidationResult.BLOCKED, RiskLevel.HIGH,
                    {'reason': 'Production operations blocked in test mode'}
                )
                return (
                    ValidationResult.BLOCKED,
                    "❌ TEST MODE ACTIVE: Production operations are blocked. "
                    "Set TEST_MODE=false to enable production operations.",
                    details
                )
        
        # Check 2: Scope validation
        scope_valid, missing_fields = scope.is_complete()
        details['scope_validation'] = {
            'valid': scope_valid,
            'missing_fields': missing_fields
        }
        
        if not scope_valid and scope.environment == 'production':
            self._audit(
                operation_id, operation_name, 'blocked', user, scope,
                ValidationResult.BLOCKED, RiskLevel.HIGH,
                {'reason': 'Incomplete scope for production', 'missing': missing_fields}
            )
            return (
                ValidationResult.BLOCKED,
                f"❌ SCOPE INCOMPLETE: Production operations require: {', '.join(missing_fields)}",
                details
            )
        
        # Check 3: High-risk techniques
        high_risk_found = []
        for tech_id in techniques:
            if tech_id in self.HIGH_RISK_TECHNIQUES:
                high_risk_found.append({
                    'id': tech_id,
                    'name': self.HIGH_RISK_TECHNIQUES[tech_id]
                })
        
        details['high_risk_blocked'] = high_risk_found
        
        if high_risk_found and not force_override:
            self._audit(
                operation_id, operation_name, 'blocked', user, scope,
                ValidationResult.BLOCKED, RiskLevel.CRITICAL,
                {'reason': 'High-risk techniques require override', 'techniques': high_risk_found}
            )
            return (
                ValidationResult.BLOCKED,
                f"❌ HIGH-RISK TECHNIQUES BLOCKED: {[t['id'] for t in high_risk_found]}. "
                "Use --force-override with explicit approval to proceed.",
                details
            )
        
        # Check 4: Elevated risk warnings
        elevated_found = []
        for tech_id in techniques:
            if tech_id in self.ELEVATED_RISK_TECHNIQUES:
                elevated_found.append({
                    'id': tech_id,
                    'name': self.ELEVATED_RISK_TECHNIQUES[tech_id]
                })
        
        details['elevated_risk_warning'] = elevated_found
        
        if elevated_found:
            self._audit(
                operation_id, operation_name, 'warning', user, scope,
                ValidationResult.WARNING, RiskLevel.MEDIUM,
                {'reason': 'Elevated risk techniques present', 'techniques': elevated_found}
            )
            
            if not force_override:
                return (
                    ValidationResult.WARNING,
                    f"⚠️ ELEVATED RISK: Operation includes sensitive techniques: "
                    f"{[t['id'] for t in elevated_found]}. Proceeding with enhanced logging.",
                    details
                )
        
        # All checks passed
        risk_level = RiskLevel.LOW
        if elevated_found:
            risk_level = RiskLevel.MEDIUM
        if high_risk_found:
            risk_level = RiskLevel.HIGH
        
        self._audit(
            operation_id, operation_name, 'approved', user, scope,
            ValidationResult.APPROVED, risk_level,
            details
        )
        
        return (
            ValidationResult.APPROVED,
            f"✅ Operation approved (environment={scope.environment}, "
            f"techniques={len(techniques)}, risk={risk_level.value})",
            details
        )
    
    def validate_scope(self, scope: OperationScope) -> Tuple[bool, List[str]]:
        """Validate operation scope completeness."""
        return scope.is_complete()
    
    def classify_risk(self, techniques: List[str]) -> RiskLevel:
        """Classify overall risk level based on techniques."""
        has_critical = any(t in self.HIGH_RISK_TECHNIQUES for t in techniques)
        has_elevated = any(t in self.ELEVATED_RISK_TECHNIQUES for t in techniques)
        
        if has_critical:
            return RiskLevel.CRITICAL
        elif has_elevated:
            return RiskLevel.HIGH
        elif len(techniques) > 10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _audit(
        self,
        operation_id: str,
        operation_name: str,
        action: str,
        user: str,
        scope: OperationScope,
        result: ValidationResult,
        risk_level: RiskLevel,
        details: Dict[str, Any] = None
    ):
        """Write audit log entry."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            operation_id=operation_id,
            operation_name=operation_name,
            action=action,
            user=user,
            scope=asdict(scope),
            validation_result=result.value,
            risk_level=risk_level.value,
            details=details or {}
        )
        
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(entry.to_json() + '\n')
        except Exception as e:
            self.log.error(f"Failed to write audit log: {e}")
    
    def get_audit_log(
        self,
        operation_id: str = None,
        user: str = None,
        action: str = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Retrieve audit log entries with optional filters."""
        entries = []
        
        try:
            with open(self.audit_log_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        
                        # Apply filters
                        if operation_id and data.get('operation_id') != operation_id:
                            continue
                        if user and data.get('user') != user:
                            continue
                        if action and data.get('action') != action:
                            continue
                        
                        entries.append(data)
                        
                        if len(entries) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return entries
    
    def check_test_mode(self) -> bool:
        """Check if test mode is active."""
        return self.test_mode
    
    def get_status(self) -> Dict[str, Any]:
        """Get current validator status."""
        return {
            'test_mode': self.test_mode,
            'audit_log_path': str(self.audit_log_path),
            'high_risk_techniques_count': len(self.HIGH_RISK_TECHNIQUES),
            'elevated_risk_techniques_count': len(self.ELEVATED_RISK_TECHNIQUES),
            'config_loaded': bool(self.config)
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI for safety validator testing and audit log queries."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Safety Validator CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show validator status')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate an operation')
    validate_parser.add_argument('--operation-id', required=True)
    validate_parser.add_argument('--operation-name', default='Test Operation')
    validate_parser.add_argument('--adversary', default='test-adversary')
    validate_parser.add_argument('--techniques', nargs='+', default=['T1059'])
    validate_parser.add_argument('--environment', default='lab')
    validate_parser.add_argument('--ticket-id')
    validate_parser.add_argument('--owner')
    validate_parser.add_argument('--force-override', action='store_true')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Query audit log')
    audit_parser.add_argument('--operation-id')
    audit_parser.add_argument('--user')
    audit_parser.add_argument('--action')
    audit_parser.add_argument('--limit', type=int, default=10)
    
    args = parser.parse_args()
    
    validator = SafetyValidator()
    
    if args.command == 'status':
        status = validator.get_status()
        print("\n🛡️  SAFETY VALIDATOR STATUS")
        print("-" * 40)
        for key, value in status.items():
            print(f"  {key}: {value}")
        print()
    
    elif args.command == 'validate':
        scope = OperationScope(
            environment=args.environment,
            ticket_id=args.ticket_id,
            owner=args.owner
        )
        
        result, message, details = validator.validate_operation(
            operation_id=args.operation_id,
            operation_name=args.operation_name,
            adversary_name=args.adversary,
            techniques=args.techniques,
            scope=scope,
            force_override=args.force_override
        )
        
        print(f"\n{message}")
        print(f"\nDetails: {json.dumps(details, indent=2)}\n")
    
    elif args.command == 'audit':
        entries = validator.get_audit_log(
            operation_id=args.operation_id,
            user=args.user,
            action=args.action,
            limit=args.limit
        )
        
        print(f"\n📋 AUDIT LOG ({len(entries)} entries)")
        print("-" * 60)
        for entry in entries:
            print(f"  {entry.get('timestamp')} | {entry.get('action'):<10} | "
                  f"{entry.get('operation_name', 'N/A')[:20]} | {entry.get('validation_result')}")
        print()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
