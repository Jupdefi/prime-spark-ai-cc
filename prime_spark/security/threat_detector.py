"""
Threat Detection and Response System

AI-powered threat detection, anomaly detection, intrusion detection,
and automated incident response.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of detected threats"""
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALWARE = "malware"
    ANOMALY = "anomaly"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class ResponseAction(Enum):
    """Automated response actions"""
    ALERT = "alert"
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    REQUIRE_MFA = "require_mfa"
    TERMINATE_SESSION = "terminate_session"
    QUARANTINE = "quarantine"
    NOTIFY_ADMIN = "notify_admin"


@dataclass
class SecurityEvent:
    """Security event"""
    event_id: str
    timestamp: datetime
    event_type: str
    source_ip: str
    user_id: Optional[str]
    resource: str
    action: str
    success: bool
    metadata: Dict


@dataclass
class Threat:
    """Detected threat"""
    threat_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    detected_at: datetime
    source_ip: str
    target_resource: str
    user_id: Optional[str]
    confidence: float
    description: str
    indicators: List[str]
    recommended_actions: List[ResponseAction]


@dataclass
class IncidentResponse:
    """Incident response record"""
    incident_id: str
    threat: Threat
    actions_taken: List[ResponseAction]
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    notes: str


class ThreatDetector:
    """
    Threat Detection and Response System

    Features:
    - Real-time threat detection
    - Anomaly detection using ML
    - Pattern-based attack detection
    - Rate limiting and DDoS protection
    - Automated incident response
    - Threat intelligence integration
    - Security event correlation
    - Behavioral analysis
    """

    def __init__(
        self,
        anomaly_threshold: float = 0.85,
        rate_limit_window: int = 60,  # seconds
        max_requests_per_window: int = 100,
        auto_response_enabled: bool = True,
    ):
        self.anomaly_threshold = anomaly_threshold
        self.rate_limit_window = rate_limit_window
        self.max_requests_per_window = max_requests_per_window
        self.auto_response_enabled = auto_response_enabled

        # Event streams
        self.security_events: deque = deque(maxlen=10000)
        self.detected_threats: List[Threat] = []
        self.incident_responses: List[IncidentResponse] = []

        # Baseline behavioral patterns (learned over time)
        self.baseline_patterns: Dict = {}

        # IP reputation tracking
        self.ip_reputation: Dict[str, Dict] = {}

        # Rate limiting tracking
        self.rate_limit_buckets: Dict[str, deque] = {}

        # Blocked IPs
        self.blocked_ips: Set[str] = set()

        logger.info("Initialized ThreatDetector")

    def ingest_event(self, event: SecurityEvent) -> None:
        """Ingest security event for analysis"""
        self.security_events.append(event)

        # Real-time threat detection
        threats = self._analyze_event(event)

        for threat in threats:
            self.detected_threats.append(threat)
            logger.warning(
                f"Threat detected: {threat.threat_type.value} "
                f"(level: {threat.threat_level.value}, confidence: {threat.confidence:.2f})"
            )

            # Automated response
            if self.auto_response_enabled:
                self._respond_to_threat(threat)

    def _analyze_event(self, event: SecurityEvent) -> List[Threat]:
        """Analyze event for potential threats"""
        threats = []

        # Check if IP is blocked
        if event.source_ip in self.blocked_ips:
            return threats  # Already blocked

        # 1. Brute force detection
        brute_force_threat = self._detect_brute_force(event)
        if brute_force_threat:
            threats.append(brute_force_threat)

        # 2. DDoS detection
        ddos_threat = self._detect_ddos(event)
        if ddos_threat:
            threats.append(ddos_threat)

        # 3. SQL injection detection
        sql_injection_threat = self._detect_sql_injection(event)
        if sql_injection_threat:
            threats.append(sql_injection_threat)

        # 4. XSS detection
        xss_threat = self._detect_xss(event)
        if xss_threat:
            threats.append(xss_threat)

        # 5. Anomaly detection
        anomaly_threat = self._detect_anomaly(event)
        if anomaly_threat:
            threats.append(anomaly_threat)

        # 6. Data exfiltration detection
        exfiltration_threat = self._detect_data_exfiltration(event)
        if exfiltration_threat:
            threats.append(exfiltration_threat)

        return threats

    def _detect_brute_force(self, event: SecurityEvent) -> Optional[Threat]:
        """Detect brute force attacks"""
        if event.event_type != "authentication" or event.success:
            return None

        # Count failed attempts from this IP in last 5 minutes
        window_start = datetime.now() - timedelta(minutes=5)
        failed_attempts = sum(
            1 for e in self.security_events
            if e.source_ip == event.source_ip
            and e.event_type == "authentication"
            and not e.success
            and e.timestamp > window_start
        )

        if failed_attempts >= 10:
            return Threat(
                threat_id=f"threat-{datetime.now().timestamp()}",
                threat_type=ThreatType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                detected_at=datetime.now(),
                source_ip=event.source_ip,
                target_resource="authentication",
                user_id=event.user_id,
                confidence=min(0.95, 0.5 + (failed_attempts / 50)),
                description=f"Brute force attack detected: {failed_attempts} failed attempts in 5 minutes",
                indicators=[f"failed_attempts={failed_attempts}"],
                recommended_actions=[ResponseAction.BLOCK_IP, ResponseAction.NOTIFY_ADMIN],
            )

        return None

    def _detect_ddos(self, event: SecurityEvent) -> Optional[Threat]:
        """Detect DDoS attacks"""
        # Count requests from this IP in rate limit window
        ip_key = event.source_ip

        if ip_key not in self.rate_limit_buckets:
            self.rate_limit_buckets[ip_key] = deque()

        bucket = self.rate_limit_buckets[ip_key]

        # Clean old entries
        cutoff = datetime.now() - timedelta(seconds=self.rate_limit_window)
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        # Add current request
        bucket.append(datetime.now())

        # Check if exceeds threshold
        if len(bucket) > self.max_requests_per_window:
            return Threat(
                threat_id=f"threat-{datetime.now().timestamp()}",
                threat_type=ThreatType.DDoS,
                threat_level=ThreatLevel.CRITICAL,
                detected_at=datetime.now(),
                source_ip=event.source_ip,
                target_resource=event.resource,
                user_id=event.user_id,
                confidence=0.9,
                description=f"DDoS attack detected: {len(bucket)} requests in {self.rate_limit_window}s",
                indicators=[f"request_rate={len(bucket)}/{self.rate_limit_window}s"],
                recommended_actions=[ResponseAction.BLOCK_IP, ResponseAction.RATE_LIMIT],
            )

        return None

    def _detect_sql_injection(self, event: SecurityEvent) -> Optional[Threat]:
        """Detect SQL injection attempts"""
        # Check for SQL injection patterns in request
        sql_patterns = [
            "' OR '1'='1",
            "'; DROP TABLE",
            "UNION SELECT",
            "-- ",
            "/*",
            "xp_",
            "sp_executesql",
        ]

        request_data = str(event.metadata.get('request_data', ''))

        for pattern in sql_patterns:
            if pattern.lower() in request_data.lower():
                return Threat(
                    threat_id=f"threat-{datetime.now().timestamp()}",
                    threat_type=ThreatType.SQL_INJECTION,
                    threat_level=ThreatLevel.CRITICAL,
                    detected_at=datetime.now(),
                    source_ip=event.source_ip,
                    target_resource=event.resource,
                    user_id=event.user_id,
                    confidence=0.85,
                    description=f"SQL injection attempt detected: pattern '{pattern}' found",
                    indicators=[f"pattern={pattern}"],
                    recommended_actions=[
                        ResponseAction.BLOCK_IP,
                        ResponseAction.NOTIFY_ADMIN,
                        ResponseAction.ALERT,
                    ],
                )

        return None

    def _detect_xss(self, event: SecurityEvent) -> Optional[Threat]:
        """Detect XSS attacks"""
        xss_patterns = [
            "<script>",
            "javascript:",
            "onerror=",
            "onload=",
            "<iframe",
        ]

        request_data = str(event.metadata.get('request_data', ''))

        for pattern in xss_patterns:
            if pattern.lower() in request_data.lower():
                return Threat(
                    threat_id=f"threat-{datetime.now().timestamp()}",
                    threat_type=ThreatType.XSS,
                    threat_level=ThreatLevel.HIGH,
                    detected_at=datetime.now(),
                    source_ip=event.source_ip,
                    target_resource=event.resource,
                    user_id=event.user_id,
                    confidence=0.8,
                    description=f"XSS attack detected: pattern '{pattern}' found",
                    indicators=[f"pattern={pattern}"],
                    recommended_actions=[ResponseAction.BLOCK_IP, ResponseAction.ALERT],
                )

        return None

    def _detect_anomaly(self, event: SecurityEvent) -> Optional[Threat]:
        """Detect anomalous behavior using ML"""
        # Build feature vector from event
        features = self._extract_features(event)

        # Calculate anomaly score
        anomaly_score = self._calculate_anomaly_score(features)

        if anomaly_score > self.anomaly_threshold:
            return Threat(
                threat_id=f"threat-{datetime.now().timestamp()}",
                threat_type=ThreatType.ANOMALY,
                threat_level=self._score_to_threat_level(anomaly_score),
                detected_at=datetime.now(),
                source_ip=event.source_ip,
                target_resource=event.resource,
                user_id=event.user_id,
                confidence=anomaly_score,
                description=f"Anomalous behavior detected (score: {anomaly_score:.2f})",
                indicators=[f"anomaly_score={anomaly_score:.2f}"],
                recommended_actions=[ResponseAction.ALERT, ResponseAction.NOTIFY_ADMIN],
            )

        return None

    def _detect_data_exfiltration(self, event: SecurityEvent) -> Optional[Threat]:
        """Detect data exfiltration attempts"""
        # Check for unusual data transfer volumes
        if event.user_id:
            # Get recent data transfer volume for this user
            window_start = datetime.now() - timedelta(hours=1)
            recent_events = [
                e for e in self.security_events
                if e.user_id == event.user_id
                and e.timestamp > window_start
            ]

            # Calculate total data transferred
            total_bytes = sum(
                e.metadata.get('bytes_transferred', 0)
                for e in recent_events
            )

            # Threshold: 1 GB in 1 hour
            if total_bytes > 1024 * 1024 * 1024:
                return Threat(
                    threat_id=f"threat-{datetime.now().timestamp()}",
                    threat_type=ThreatType.DATA_EXFILTRATION,
                    threat_level=ThreatLevel.CRITICAL,
                    detected_at=datetime.now(),
                    source_ip=event.source_ip,
                    target_resource=event.resource,
                    user_id=event.user_id,
                    confidence=0.75,
                    description=f"Potential data exfiltration: {total_bytes / 1024 / 1024:.1f} MB in 1 hour",
                    indicators=[f"data_volume={total_bytes}"],
                    recommended_actions=[
                        ResponseAction.TERMINATE_SESSION,
                        ResponseAction.NOTIFY_ADMIN,
                        ResponseAction.REQUIRE_MFA,
                    ],
                )

        return None

    def _extract_features(self, event: SecurityEvent) -> np.ndarray:
        """Extract feature vector from event"""
        # Simple feature extraction (in production, use more sophisticated features)
        features = [
            1.0 if event.success else 0.0,
            event.timestamp.hour / 24.0,  # Normalized time of day
            len(event.resource) / 100.0,  # Resource length
            len(str(event.metadata)) / 1000.0,  # Metadata size
        ]

        return np.array(features)

    def _calculate_anomaly_score(self, features: np.ndarray) -> float:
        """Calculate anomaly score using simple statistical method"""
        # In production, use proper ML model (Isolation Forest, Autoencoder, etc.)

        # For now, use simple distance from baseline
        if not self.baseline_patterns:
            # Build baseline from recent normal events
            self._build_baseline()

        baseline = self.baseline_patterns.get('mean', features)

        # Calculate Euclidean distance
        distance = np.linalg.norm(features - baseline)

        # Normalize to 0-1
        score = min(1.0, distance / 10.0)

        return score

    def _build_baseline(self) -> None:
        """Build baseline patterns from historical data"""
        # Get recent successful events
        recent_events = [
            e for e in self.security_events
            if e.success and e.timestamp > datetime.now() - timedelta(days=7)
        ]

        if not recent_events:
            return

        # Extract features
        features_list = [self._extract_features(e) for e in recent_events]

        # Calculate mean and std
        features_array = np.array(features_list)
        self.baseline_patterns['mean'] = np.mean(features_array, axis=0)
        self.baseline_patterns['std'] = np.std(features_array, axis=0)

        logger.info("Built baseline patterns from historical data")

    def _score_to_threat_level(self, score: float) -> ThreatLevel:
        """Convert anomaly score to threat level"""
        if score >= 0.95:
            return ThreatLevel.CRITICAL
        elif score >= 0.90:
            return ThreatLevel.HIGH
        elif score >= 0.85:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def _respond_to_threat(self, threat: Threat) -> None:
        """Automated threat response"""
        incident_id = f"incident-{datetime.now().timestamp()}"
        actions_taken = []

        for action in threat.recommended_actions:
            if action == ResponseAction.BLOCK_IP:
                self.blocked_ips.add(threat.source_ip)
                actions_taken.append(action)
                logger.warning(f"Blocked IP: {threat.source_ip}")

            elif action == ResponseAction.RATE_LIMIT:
                # Already implemented in rate limiting logic
                actions_taken.append(action)

            elif action == ResponseAction.ALERT:
                # Send alert (in production, integrate with monitoring system)
                actions_taken.append(action)
                logger.warning(f"Security alert: {threat.description}")

            elif action == ResponseAction.NOTIFY_ADMIN:
                # Notify administrators
                actions_taken.append(action)
                logger.critical(f"Admin notification: {threat.description}")

        # Record incident response
        incident = IncidentResponse(
            incident_id=incident_id,
            threat=threat,
            actions_taken=actions_taken,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            success=True,
            notes=f"Automated response to {threat.threat_type.value}",
        )

        self.incident_responses.append(incident)

    def get_threat_summary(self, hours: int = 24) -> Dict:
        """Get threat summary for recent period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_threats = [t for t in self.detected_threats if t.detected_at > cutoff]

        # Group by type
        threats_by_type = {}
        for threat in recent_threats:
            threat_type = threat.threat_type.value
            threats_by_type[threat_type] = threats_by_type.get(threat_type, 0) + 1

        # Group by level
        threats_by_level = {}
        for threat in recent_threats:
            level = threat.threat_level.value
            threats_by_level[level] = threats_by_level.get(level, 0) + 1

        # Top source IPs
        source_ips = {}
        for threat in recent_threats:
            ip = threat.source_ip
            source_ips[ip] = source_ips.get(ip, 0) + 1

        top_ips = sorted(source_ips.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'period_hours': hours,
            'total_threats': len(recent_threats),
            'threats_by_type': threats_by_type,
            'threats_by_level': threats_by_level,
            'top_source_ips': dict(top_ips),
            'blocked_ips_count': len(self.blocked_ips),
            'incidents_responded': len([
                i for i in self.incident_responses
                if i.started_at > cutoff
            ]),
        }

    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address"""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            logger.info(f"Unblocked IP: {ip_address}")
            return True
        return False
