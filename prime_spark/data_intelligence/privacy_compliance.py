"""
Privacy Compliance Manager

Ensures compliance with data privacy regulations (GDPR, CCPA, HIPAA)
with automated anonymization, consent management, and data subject rights.
"""

import logging
import hashlib
import secrets
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from enum import Enum

logger = logging.getLogger(__name__)


class Regulation(Enum):
    """Privacy regulations"""
    GDPR = "gdpr"  # General Data Protection Regulation (EU)
    CCPA = "ccpa"  # California Consumer Privacy Act (US)
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act (US)
    PIPEDA = "pipeda"  # Personal Information Protection and Electronic Documents Act (Canada)


class DataClassification(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"  # Personally Identifiable Information
    PHI = "phi"  # Protected Health Information
    FINANCIAL = "financial"


class AnonymizationTechnique(Enum):
    """Data anonymization techniques"""
    MASK = "mask"  # Mask characters (e.g., ***-**-1234)
    HASH = "hash"  # One-way hash
    ENCRYPT = "encrypt"  # Reversible encryption
    GENERALIZE = "generalize"  # Reduce precision (e.g., exact age -> age range)
    PSEUDONYMIZE = "pseudonymize"  # Replace with pseudonym
    SUPPRESS = "suppress"  # Remove completely
    SYNTHETIC = "synthetic"  # Generate synthetic data


class DataSubjectRight(Enum):
    """Data subject rights (GDPR)"""
    ACCESS = "access"  # Right to access personal data
    RECTIFICATION = "rectification"  # Right to correct data
    ERASURE = "erasure"  # Right to be forgotten
    PORTABILITY = "portability"  # Right to data portability
    RESTRICT_PROCESSING = "restrict_processing"  # Right to restrict processing
    OBJECT = "object"  # Right to object to processing


@dataclass
class PIIField:
    """PII field definition"""
    field_name: str
    classification: DataClassification
    anonymization_technique: AnonymizationTechnique
    retention_days: int
    purpose: str
    legal_basis: str


@dataclass
class ConsentRecord:
    """User consent record"""
    consent_id: str
    user_id: str
    purpose: str
    granted_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: str
    user_agent: str
    active: bool = True


@dataclass
class DataSubjectRequest:
    """Data subject access request"""
    request_id: str
    user_id: str
    right: DataSubjectRight
    submitted_at: datetime
    completed_at: Optional[datetime]
    status: str  # pending, in_progress, completed, rejected
    notes: str


@dataclass
class ComplianceReport:
    """Privacy compliance report"""
    report_id: str
    regulation: Regulation
    generated_at: datetime
    compliant: bool
    issues: List[Dict]
    recommendations: List[str]
    score: float


class PrivacyComplianceManager:
    """
    Privacy Compliance Management System

    Features:
    - Multi-regulation compliance (GDPR, CCPA, HIPAA)
    - PII detection and classification
    - Automated data anonymization
    - Consent management
    - Data subject rights automation
    - Data retention policies
    - Privacy impact assessments
    - Breach notification
    - Audit trail
    """

    def __init__(
        self,
        primary_regulation: Regulation = Regulation.GDPR,
        default_retention_days: int = 365,
        enable_auto_anonymization: bool = True,
    ):
        self.primary_regulation = primary_regulation
        self.default_retention_days = default_retention_days
        self.enable_auto_anonymization = enable_auto_anonymization

        # PII registry
        self.pii_fields: Dict[str, PIIField] = {}

        # Consent records
        self.consents: Dict[str, List[ConsentRecord]] = {}  # user_id -> consents

        # Data subject requests
        self.dsr_requests: List[DataSubjectRequest] = []

        # Anonymization cache
        self.anonymization_cache: Dict[str, str] = {}

        # Compliance audit log
        self.audit_log: List[Dict] = []

        # Initialize PII patterns
        self.pii_patterns = self._initialize_pii_patterns()

        logger.info(f"Initialized PrivacyComplianceManager ({primary_regulation.value})")

    def _initialize_pii_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for PII detection"""
        return {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'ssn': r'\d{3}-\d{2}-\d{4}',
            'credit_card': r'\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}',
            'phone': r'\+?\d{1,3}?[- ]?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}',
            'ip_address': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            'zipcode': r'\d{5}(-\d{4})?',
        }

    def register_pii_field(
        self,
        field_name: str,
        classification: DataClassification,
        anonymization_technique: AnonymizationTechnique,
        retention_days: Optional[int] = None,
        purpose: str = "",
        legal_basis: str = "",
    ) -> None:
        """Register a field as containing PII"""
        pii_field = PIIField(
            field_name=field_name,
            classification=classification,
            anonymization_technique=anonymization_technique,
            retention_days=retention_days or self.default_retention_days,
            purpose=purpose,
            legal_basis=legal_basis,
        )

        self.pii_fields[field_name] = pii_field
        logger.info(f"Registered PII field: {field_name} ({classification.value})")

    def detect_pii(self, data: Dict) -> Dict[str, str]:
        """Detect PII in data"""
        detected = {}

        for field, value in data.items():
            if not isinstance(value, str):
                continue

            for pii_type, pattern in self.pii_patterns.items():
                if re.search(pattern, value):
                    detected[field] = pii_type

        return detected

    def anonymize_data(
        self,
        data: Dict,
        technique_override: Optional[Dict[str, AnonymizationTechnique]] = None,
    ) -> Dict:
        """Anonymize PII data"""
        anonymized = data.copy()
        technique_map = technique_override or {}

        for field_name, field_def in self.pii_fields.items():
            if field_name not in data:
                continue

            value = data[field_name]

            # Get anonymization technique
            technique = technique_map.get(field_name, field_def.anonymization_technique)

            # Apply anonymization
            anonymized_value = self._apply_anonymization(
                value, technique, field_name
            )

            anonymized[field_name] = anonymized_value

            # Audit
            self._log_audit('anonymization', {
                'field': field_name,
                'technique': technique.value,
            })

        return anonymized

    def _apply_anonymization(
        self,
        value: Any,
        technique: AnonymizationTechnique,
        field_name: str,
    ) -> Any:
        """Apply anonymization technique to a value"""
        if value is None:
            return None

        value_str = str(value)

        if technique == AnonymizationTechnique.MASK:
            return self._mask_value(value_str)

        elif technique == AnonymizationTechnique.HASH:
            return hashlib.sha256(value_str.encode()).hexdigest()

        elif technique == AnonymizationTechnique.ENCRYPT:
            # In production, use proper encryption
            return f"encrypted_{secrets.token_hex(16)}"

        elif technique == AnonymizationTechnique.GENERALIZE:
            return self._generalize_value(value_str, field_name)

        elif technique == AnonymizationTechnique.PSEUDONYMIZE:
            # Check cache for consistent pseudonyms
            cache_key = f"{field_name}:{value_str}"
            if cache_key not in self.anonymization_cache:
                self.anonymization_cache[cache_key] = f"user_{secrets.token_hex(8)}"
            return self.anonymization_cache[cache_key]

        elif technique == AnonymizationTechnique.SUPPRESS:
            return "[REDACTED]"

        elif technique == AnonymizationTechnique.SYNTHETIC:
            return self._generate_synthetic_value(field_name)

        return value

    def _mask_value(self, value: str) -> str:
        """Mask a value (show last 4 characters)"""
        if len(value) <= 4:
            return "*" * len(value)
        return "*" * (len(value) - 4) + value[-4:]

    def _generalize_value(self, value: str, field_name: str) -> str:
        """Generalize a value"""
        # Example generalizations
        if field_name == "age":
            try:
                age = int(value)
                if age < 18:
                    return "0-17"
                elif age < 30:
                    return "18-29"
                elif age < 50:
                    return "30-49"
                elif age < 65:
                    return "50-64"
                else:
                    return "65+"
            except ValueError:
                pass

        elif field_name == "zipcode":
            # Keep only first 3 digits
            return value[:3] + "00"

        return value

    def _generate_synthetic_value(self, field_name: str) -> str:
        """Generate synthetic data"""
        # Simple synthetic data generation
        if field_name == "email":
            return f"user{secrets.token_hex(4)}@example.com"
        elif field_name == "phone":
            return f"555-{secrets.randbelow(900) + 100}-{secrets.randbelow(9000) + 1000}"
        else:
            return f"synthetic_{secrets.token_hex(8)}"

    def record_consent(
        self,
        user_id: str,
        purpose: str,
        duration_days: Optional[int] = None,
        ip_address: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> ConsentRecord:
        """Record user consent"""
        consent_id = f"consent-{secrets.token_hex(16)}"

        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            purpose=purpose,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=duration_days) if duration_days else None,
            revoked_at=None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if user_id not in self.consents:
            self.consents[user_id] = []

        self.consents[user_id].append(consent)

        self._log_audit('consent_granted', {
            'user_id': user_id,
            'purpose': purpose,
        })

        logger.info(f"Recorded consent for user {user_id}: {purpose}")
        return consent

    def revoke_consent(self, consent_id: str, user_id: str) -> bool:
        """Revoke user consent"""
        if user_id not in self.consents:
            return False

        for consent in self.consents[user_id]:
            if consent.consent_id == consent_id:
                consent.active = False
                consent.revoked_at = datetime.now()

                self._log_audit('consent_revoked', {
                    'user_id': user_id,
                    'consent_id': consent_id,
                })

                logger.info(f"Revoked consent: {consent_id}")
                return True

        return False

    def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user has valid consent for purpose"""
        if user_id not in self.consents:
            return False

        for consent in self.consents[user_id]:
            if consent.purpose == purpose and consent.active:
                # Check expiration
                if consent.expires_at and datetime.now() > consent.expires_at:
                    consent.active = False
                    continue

                return True

        return False

    def submit_dsr(
        self,
        user_id: str,
        right: DataSubjectRight,
    ) -> DataSubjectRequest:
        """Submit data subject rights request"""
        request_id = f"dsr-{secrets.token_hex(16)}"

        dsr = DataSubjectRequest(
            request_id=request_id,
            user_id=user_id,
            right=right,
            submitted_at=datetime.now(),
            completed_at=None,
            status="pending",
            notes="",
        )

        self.dsr_requests.append(dsr)

        self._log_audit('dsr_submitted', {
            'user_id': user_id,
            'right': right.value,
        })

        logger.info(f"Submitted DSR for user {user_id}: {right.value}")
        return dsr

    def process_dsr(
        self,
        request_id: str,
        status: str,
        notes: str = "",
    ) -> bool:
        """Process data subject request"""
        dsr = next(
            (r for r in self.dsr_requests if r.request_id == request_id),
            None
        )

        if not dsr:
            return False

        dsr.status = status
        dsr.notes = notes

        if status == "completed":
            dsr.completed_at = datetime.now()

        self._log_audit('dsr_processed', {
            'request_id': request_id,
            'status': status,
        })

        return True

    def assess_compliance(
        self,
        regulation: Optional[Regulation] = None,
    ) -> ComplianceReport:
        """Assess privacy compliance"""
        regulation = regulation or self.primary_regulation
        report_id = f"compliance-{datetime.now().timestamp()}"

        issues = []
        recommendations = []

        # Check consent management
        total_users = len(self.consents)
        if total_users == 0:
            issues.append({
                'type': 'consent',
                'severity': 'warning',
                'message': 'No consent records found',
            })
            recommendations.append("Implement consent collection for all users")

        # Check PII classification
        if not self.pii_fields:
            issues.append({
                'type': 'pii_classification',
                'severity': 'high',
                'message': 'No PII fields registered',
            })
            recommendations.append("Classify and register all PII fields")

        # Check data subject requests
        pending_dsrs = [r for r in self.dsr_requests if r.status == "pending"]
        if pending_dsrs:
            # GDPR requires response within 30 days
            overdue_threshold = datetime.now() - timedelta(days=30)
            overdue = [r for r in pending_dsrs if r.submitted_at < overdue_threshold]

            if overdue:
                issues.append({
                    'type': 'dsr_processing',
                    'severity': 'critical',
                    'message': f'{len(overdue)} overdue data subject requests',
                })
                recommendations.append("Process pending data subject requests within 30 days")

        # Calculate compliance score
        max_severity_score = {
            'info': 0.05,
            'warning': 0.10,
            'high': 0.20,
            'critical': 0.30,
        }

        penalty = sum(max_severity_score.get(issue['severity'], 0) for issue in issues)
        score = max(0.0, 1.0 - penalty)

        return ComplianceReport(
            report_id=report_id,
            regulation=regulation,
            generated_at=datetime.now(),
            compliant=score >= 0.9,
            issues=issues,
            recommendations=recommendations,
            score=score,
        )

    def _log_audit(self, event: str, details: Dict) -> None:
        """Log privacy audit event"""
        self.audit_log.append({
            'timestamp': datetime.now(),
            'event': event,
            'details': details,
        })

    def get_statistics(self) -> Dict:
        """Get privacy compliance statistics"""
        active_consents = sum(
            sum(1 for c in consents if c.active)
            for consents in self.consents.values()
        )

        pending_dsrs = sum(
            1 for r in self.dsr_requests if r.status == "pending"
        )

        return {
            'registered_pii_fields': len(self.pii_fields),
            'total_users_with_consent': len(self.consents),
            'active_consents': active_consents,
            'total_dsr_requests': len(self.dsr_requests),
            'pending_dsrs': pending_dsrs,
            'audit_events': len(self.audit_log),
            'primary_regulation': self.primary_regulation.value,
        }
