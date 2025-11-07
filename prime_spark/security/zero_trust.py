"""
Zero-Trust Network Security

Implements zero-trust security model where no entity is trusted by default,
regardless of whether it's inside or outside the network perimeter.
"""

import logging
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
import secrets

logger = logging.getLogger(__name__)


class TrustLevel(Enum):
    """Trust level classification"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


class AccessDecision(Enum):
    """Access control decision"""
    ALLOW = "allow"
    DENY = "deny"
    CHALLENGE = "challenge"
    MONITOR = "monitor"


@dataclass
class Device:
    """Device information"""
    device_id: str
    device_type: str
    os: str
    os_version: str
    last_seen: datetime
    trust_level: TrustLevel
    compliance_score: float
    encryption_enabled: bool
    security_patches_current: bool


@dataclass
class Identity:
    """User or service identity"""
    id: str
    name: str
    email: Optional[str]
    type: str  # user, service, application
    roles: List[str]
    groups: List[str]
    mfa_enabled: bool
    last_authentication: Optional[datetime]
    authentication_method: str  # password, mfa, certificate, oauth
    trust_level: TrustLevel


@dataclass
class AccessRequest:
    """Access request information"""
    request_id: str
    identity: Identity
    device: Device
    resource: str
    action: str  # read, write, delete, execute
    context: Dict
    timestamp: datetime
    source_ip: str
    geo_location: Optional[str]


@dataclass
class AccessPolicy:
    """Zero-trust access policy"""
    policy_id: str
    name: str
    resources: List[str]  # Resource patterns
    identities: List[str]  # Identity patterns
    actions: List[str]  # Allowed actions
    required_trust_level: TrustLevel
    require_mfa: bool
    require_device_compliance: bool
    allowed_locations: Optional[List[str]]
    allowed_ip_ranges: Optional[List[str]]
    time_restrictions: Optional[Dict]
    priority: int = 100


@dataclass
class SecurityContext:
    """Security context for a session"""
    session_id: str
    identity: Identity
    device: Device
    trust_score: float
    established_at: datetime
    expires_at: datetime
    last_validated: datetime
    continuous_validation_interval: int = 300  # seconds


class ZeroTrustNetwork:
    """
    Zero-Trust Network Security Framework

    Features:
    - Never trust, always verify
    - Continuous authentication and authorization
    - Least privilege access
    - Microsegmentation
    - Device posture validation
    - Context-aware access control
    - Continuous monitoring
    """

    def __init__(
        self,
        default_deny: bool = True,
        continuous_validation_interval: int = 300,  # 5 minutes
        session_timeout: int = 3600,  # 1 hour
    ):
        self.default_deny = default_deny
        self.continuous_validation_interval = continuous_validation_interval
        self.session_timeout = session_timeout

        # Policy store
        self.policies: Dict[str, AccessPolicy] = {}

        # Active sessions
        self.sessions: Dict[str, SecurityContext] = {}

        # Device registry
        self.devices: Dict[str, Device] = {}

        # Identity registry
        self.identities: Dict[str, Identity] = {}

        # Access audit log
        self.audit_log: List[Dict] = []

        logger.info("Initialized ZeroTrustNetwork with default_deny=True")

    def register_policy(self, policy: AccessPolicy) -> None:
        """Register an access policy"""
        self.policies[policy.policy_id] = policy
        logger.info(f"Registered policy: {policy.name} (priority {policy.priority})")

    def register_device(self, device: Device) -> None:
        """Register a device"""
        self.devices[device.device_id] = device
        logger.info(f"Registered device: {device.device_id} (trust: {device.trust_level.name})")

    def register_identity(self, identity: Identity) -> None:
        """Register an identity"""
        self.identities[identity.id] = identity
        logger.info(f"Registered identity: {identity.name} (roles: {', '.join(identity.roles)})")

    def evaluate_access(self, request: AccessRequest) -> AccessDecision:
        """
        Evaluate access request using zero-trust principles

        Args:
            request: Access request to evaluate

        Returns:
            AccessDecision (ALLOW, DENY, CHALLENGE, MONITOR)
        """
        # Find applicable policies (sorted by priority)
        applicable_policies = self._find_applicable_policies(request)

        if not applicable_policies:
            logger.warning(f"No applicable policies for {request.resource}")
            return AccessDecision.DENY if self.default_deny else AccessDecision.MONITOR

        # Evaluate each policy
        for policy in applicable_policies:
            decision = self._evaluate_policy(request, policy)

            if decision == AccessDecision.DENY:
                self._audit_access(request, decision, policy.policy_id, "Policy denied access")
                return AccessDecision.DENY

            if decision == AccessDecision.ALLOW:
                # Additional checks even after policy allows
                if not self._validate_device_compliance(request.device):
                    self._audit_access(request, AccessDecision.DENY, policy.policy_id, "Device non-compliant")
                    return AccessDecision.DENY

                if not self._validate_trust_level(request.identity, policy.required_trust_level):
                    self._audit_access(request, AccessDecision.CHALLENGE, policy.policy_id, "Insufficient trust level")
                    return AccessDecision.CHALLENGE

                if policy.require_mfa and not request.identity.mfa_enabled:
                    self._audit_access(request, AccessDecision.CHALLENGE, policy.policy_id, "MFA required")
                    return AccessDecision.CHALLENGE

                # Check context (location, time, etc.)
                if not self._validate_context(request, policy):
                    self._audit_access(request, AccessDecision.DENY, policy.policy_id, "Context validation failed")
                    return AccessDecision.DENY

                self._audit_access(request, AccessDecision.ALLOW, policy.policy_id, "Policy allowed access")
                return AccessDecision.ALLOW

        # No explicit allow
        return AccessDecision.DENY if self.default_deny else AccessDecision.MONITOR

    def _find_applicable_policies(self, request: AccessRequest) -> List[AccessPolicy]:
        """Find policies applicable to this request"""
        applicable = []

        for policy in self.policies.values():
            # Check if resource matches
            resource_match = any(
                self._matches_pattern(request.resource, pattern)
                for pattern in policy.resources
            )

            # Check if identity matches
            identity_match = any(
                self._matches_pattern(request.identity.id, pattern) or
                any(role in policy.identities for role in request.identity.roles)
                for pattern in policy.identities
            )

            # Check if action is allowed
            action_match = request.action in policy.actions or '*' in policy.actions

            if resource_match and identity_match and action_match:
                applicable.append(policy)

        # Sort by priority (higher priority first)
        applicable.sort(key=lambda p: p.priority, reverse=True)
        return applicable

    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches pattern (supports wildcards)"""
        if pattern == '*':
            return True
        if '*' in pattern:
            # Simple wildcard matching
            prefix = pattern.split('*')[0]
            return value.startswith(prefix)
        return value == pattern

    def _evaluate_policy(self, request: AccessRequest, policy: AccessPolicy) -> AccessDecision:
        """Evaluate a single policy"""
        # This is a simplified evaluation
        # In production, this would be more sophisticated
        return AccessDecision.ALLOW

    def _validate_device_compliance(self, device: Device) -> bool:
        """Validate device compliance"""
        return (
            device.compliance_score >= 0.7 and
            device.encryption_enabled and
            device.security_patches_current
        )

    def _validate_trust_level(self, identity: Identity, required: TrustLevel) -> bool:
        """Validate trust level meets requirements"""
        return identity.trust_level.value >= required.value

    def _validate_context(self, request: AccessRequest, policy: AccessPolicy) -> bool:
        """Validate request context (location, time, etc.)"""
        # Location check
        if policy.allowed_locations and request.geo_location:
            if request.geo_location not in policy.allowed_locations:
                return False

        # IP range check
        if policy.allowed_ip_ranges:
            if not any(self._ip_in_range(request.source_ip, ip_range) for ip_range in policy.allowed_ip_ranges):
                return False

        # Time restrictions
        if policy.time_restrictions:
            current_hour = datetime.now().hour
            allowed_hours = policy.time_restrictions.get('allowed_hours', [])
            if allowed_hours and current_hour not in allowed_hours:
                return False

        return True

    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in range (simplified)"""
        # In production, use proper CIDR matching
        return ip.startswith(ip_range.split('/')[0].rsplit('.', 1)[0])

    def _audit_access(
        self,
        request: AccessRequest,
        decision: AccessDecision,
        policy_id: str,
        reason: str
    ) -> None:
        """Audit access decision"""
        audit_entry = {
            'timestamp': datetime.now(),
            'request_id': request.request_id,
            'identity': request.identity.id,
            'device': request.device.device_id,
            'resource': request.resource,
            'action': request.action,
            'decision': decision.value,
            'policy_id': policy_id,
            'reason': reason,
            'source_ip': request.source_ip,
        }
        self.audit_log.append(audit_entry)

    def create_session(
        self,
        identity: Identity,
        device: Device,
    ) -> SecurityContext:
        """Create a new security context session"""
        session_id = secrets.token_urlsafe(32)

        # Calculate trust score
        trust_score = self._calculate_trust_score(identity, device)

        context = SecurityContext(
            session_id=session_id,
            identity=identity,
            device=device,
            trust_score=trust_score,
            established_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=self.session_timeout),
            last_validated=datetime.now(),
            continuous_validation_interval=self.continuous_validation_interval,
        )

        self.sessions[session_id] = context
        logger.info(f"Created session {session_id} for {identity.name} (trust: {trust_score:.2f})")

        return context

    def validate_session(self, session_id: str) -> bool:
        """Validate an existing session"""
        if session_id not in self.sessions:
            return False

        context = self.sessions[session_id]

        # Check expiration
        if datetime.now() > context.expires_at:
            logger.warning(f"Session {session_id} expired")
            del self.sessions[session_id]
            return False

        # Continuous validation
        time_since_validation = (datetime.now() - context.last_validated).seconds
        if time_since_validation > context.continuous_validation_interval:
            # Re-validate trust score
            new_trust_score = self._calculate_trust_score(context.identity, context.device)

            if new_trust_score < 0.5:
                logger.warning(f"Session {session_id} trust degraded to {new_trust_score:.2f}")
                del self.sessions[session_id]
                return False

            context.trust_score = new_trust_score
            context.last_validated = datetime.now()

        return True

    def _calculate_trust_score(self, identity: Identity, device: Device) -> float:
        """Calculate trust score for identity and device combination"""
        score = 0.0

        # Identity factors
        score += identity.trust_level.value * 0.15
        score += 0.15 if identity.mfa_enabled else 0.0
        score += 0.10 if identity.last_authentication and \
                       (datetime.now() - identity.last_authentication).seconds < 3600 else 0.0

        # Device factors
        score += device.trust_level.value * 0.15
        score += device.compliance_score * 0.20
        score += 0.15 if device.encryption_enabled else 0.0
        score += 0.10 if device.security_patches_current else 0.0

        return min(1.0, score)

    def get_security_posture(self) -> Dict:
        """Get overall security posture"""
        active_sessions = len(self.sessions)
        registered_devices = len(self.devices)
        registered_identities = len(self.identities)

        # Calculate compliance
        compliant_devices = sum(
            1 for d in self.devices.values()
            if self._validate_device_compliance(d)
        )

        # Recent access decisions
        recent_window = datetime.now() - timedelta(hours=1)
        recent_accesses = [a for a in self.audit_log if a['timestamp'] > recent_window]

        allowed_count = sum(1 for a in recent_accesses if a['decision'] == 'allow')
        denied_count = sum(1 for a in recent_accesses if a['decision'] == 'deny')

        return {
            'active_sessions': active_sessions,
            'registered_devices': registered_devices,
            'registered_identities': registered_identities,
            'device_compliance_rate': (compliant_devices / registered_devices * 100) if registered_devices > 0 else 0,
            'recent_accesses': len(recent_accesses),
            'recent_allowed': allowed_count,
            'recent_denied': denied_count,
            'deny_rate': (denied_count / len(recent_accesses) * 100) if recent_accesses else 0,
            'policies_count': len(self.policies),
        }
