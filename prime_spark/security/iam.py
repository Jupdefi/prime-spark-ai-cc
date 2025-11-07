"""
Identity and Access Management (IAM)

Comprehensive identity and access management with role-based access control (RBAC),
attribute-based access control (ABAC), OAuth2, JWT, and multi-factor authentication.
"""

import logging
import hashlib
import secrets
import time
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    MFA = "mfa"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    API_KEY = "api_key"
    BIOMETRIC = "biometric"


class TokenType(Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    SESSION = "session"


@dataclass
class Permission:
    """Permission definition"""
    resource: str
    action: str
    conditions: Optional[Dict] = None


@dataclass
class Role:
    """Role definition with permissions"""
    role_id: str
    name: str
    description: str
    permissions: List[Permission]
    created_at: datetime
    parent_roles: List[str] = field(default_factory=list)


@dataclass
class User:
    """User account"""
    user_id: str
    username: str
    email: str
    password_hash: str
    salt: str
    roles: List[str]
    attributes: Dict
    mfa_enabled: bool
    mfa_secret: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    active: bool = True


@dataclass
class Token:
    """Authentication token"""
    token_id: str
    token_type: TokenType
    user_id: str
    issued_at: datetime
    expires_at: datetime
    scopes: List[str]
    metadata: Dict


@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    auth_method: AuthMethod
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    active: bool = True


class IdentityAccessManager:
    """
    Identity and Access Management System

    Features:
    - User authentication and authorization
    - Role-based access control (RBAC)
    - Attribute-based access control (ABAC)
    - Multi-factor authentication (MFA)
    - OAuth2 and JWT support
    - Session management
    - Password policies
    - Account lockout protection
    - Audit logging
    """

    def __init__(
        self,
        password_min_length: int = 12,
        password_require_special: bool = True,
        mfa_required: bool = False,
        session_timeout_minutes: int = 60,
        max_failed_logins: int = 5,
        lockout_duration_minutes: int = 30,
        token_expiry_minutes: int = 60,
    ):
        self.password_min_length = password_min_length
        self.password_require_special = password_require_special
        self.mfa_required = mfa_required
        self.session_timeout_minutes = session_timeout_minutes
        self.max_failed_logins = max_failed_logins
        self.lockout_duration_minutes = lockout_duration_minutes
        self.token_expiry_minutes = token_expiry_minutes

        # Data stores
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.tokens: Dict[str, Token] = {}
        self.sessions: Dict[str, Session] = {}

        # Audit log
        self.audit_log: List[Dict] = []

        # Initialize default roles
        self._initialize_default_roles()

        logger.info("Initialized IdentityAccessManager")

    def _initialize_default_roles(self) -> None:
        """Initialize default system roles"""
        # Admin role
        admin_role = Role(
            role_id="admin",
            name="Administrator",
            description="Full system access",
            permissions=[
                Permission(resource="*", action="*"),
            ],
            created_at=datetime.now(),
        )
        self.roles["admin"] = admin_role

        # User role
        user_role = Role(
            role_id="user",
            name="User",
            description="Standard user access",
            permissions=[
                Permission(resource="user_data/*", action="read"),
                Permission(resource="user_data/*", action="write"),
            ],
            created_at=datetime.now(),
        )
        self.roles["user"] = user_role

        # Read-only role
        readonly_role = Role(
            role_id="readonly",
            name="Read Only",
            description="Read-only access",
            permissions=[
                Permission(resource="*", action="read"),
            ],
            created_at=datetime.now(),
        )
        self.roles["readonly"] = readonly_role

        logger.info("Initialized default roles: admin, user, readonly")

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[str],
        attributes: Optional[Dict] = None,
    ) -> str:
        """
        Create a new user account

        Args:
            username: Username
            email: Email address
            password: Password
            roles: List of role IDs
            attributes: Additional user attributes

        Returns:
            User ID
        """
        # Validate password
        if not self._validate_password(password):
            raise ValueError(
                f"Password must be at least {self.password_min_length} characters "
                f"and contain special characters"
            )

        # Check if username exists
        if any(u.username == username for u in self.users.values()):
            raise ValueError(f"Username already exists: {username}")

        # Check if email exists
        if any(u.email == email for u in self.users.values()):
            raise ValueError(f"Email already exists: {email}")

        # Validate roles
        for role_id in roles:
            if role_id not in self.roles:
                raise ValueError(f"Invalid role: {role_id}")

        # Generate user ID
        user_id = f"user-{secrets.token_hex(16)}"

        # Hash password
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)

        # Create user
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            roles=roles,
            attributes=attributes or {},
            mfa_enabled=False,
            mfa_secret=None,
            created_at=datetime.now(),
            last_login=None,
        )

        self.users[user_id] = user

        # Audit log
        self._log_audit('user_created', user_id, {'username': username, 'email': email})

        logger.info(f"Created user: {username} (ID: {user_id})")
        return user_id

    def authenticate(
        self,
        username: str,
        password: str,
        mfa_code: Optional[str] = None,
        ip_address: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> Optional[Session]:
        """
        Authenticate user and create session

        Args:
            username: Username
            password: Password
            mfa_code: MFA code (if MFA enabled)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session object if successful, None otherwise
        """
        # Find user
        user = next((u for u in self.users.values() if u.username == username), None)

        if not user:
            self._log_audit('auth_failed', None, {'username': username, 'reason': 'user_not_found'})
            return None

        # Check if account is active
        if not user.active:
            self._log_audit('auth_failed', user.user_id, {'reason': 'account_inactive'})
            return None

        # Check if account is locked
        if user.locked_until and datetime.now() < user.locked_until:
            self._log_audit('auth_failed', user.user_id, {'reason': 'account_locked'})
            return None

        # Verify password
        password_hash = self._hash_password(password, user.salt)
        if password_hash != user.password_hash:
            user.failed_login_attempts += 1

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.max_failed_logins:
                user.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
                logger.warning(f"Account locked due to failed login attempts: {username}")

            self._log_audit('auth_failed', user.user_id, {'reason': 'invalid_password'})
            return None

        # Verify MFA if enabled
        if user.mfa_enabled or self.mfa_required:
            if not mfa_code:
                self._log_audit('auth_failed', user.user_id, {'reason': 'mfa_required'})
                return None

            if not self._verify_mfa(user, mfa_code):
                user.failed_login_attempts += 1
                self._log_audit('auth_failed', user.user_id, {'reason': 'invalid_mfa'})
                return None

        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()

        # Create session
        session = self._create_session(user, AuthMethod.PASSWORD, ip_address, user_agent)

        self._log_audit('auth_success', user.user_id, {'username': username})
        logger.info(f"User authenticated: {username}")

        return session

    def authorize(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict] = None,
    ) -> bool:
        """
        Authorize user action on resource

        Args:
            user_id: User ID
            resource: Resource identifier
            action: Action to perform
            context: Additional context for ABAC

        Returns:
            True if authorized, False otherwise
        """
        if user_id not in self.users:
            return False

        user = self.users[user_id]

        # Get all permissions from user's roles
        permissions = self._get_user_permissions(user)

        # Check if any permission allows the action
        for perm in permissions:
            if self._matches_permission(perm, resource, action):
                # Check conditions (ABAC)
                if perm.conditions:
                    if not self._evaluate_conditions(perm.conditions, user, context):
                        continue

                self._log_audit('authorization_granted', user_id, {
                    'resource': resource,
                    'action': action,
                })
                return True

        self._log_audit('authorization_denied', user_id, {
            'resource': resource,
            'action': action,
        })
        return False

    def _get_user_permissions(self, user: User) -> List[Permission]:
        """Get all permissions for a user (including inherited from roles)"""
        permissions = []

        for role_id in user.roles:
            if role_id in self.roles:
                role = self.roles[role_id]
                permissions.extend(role.permissions)

                # Include parent role permissions
                for parent_role_id in role.parent_roles:
                    if parent_role_id in self.roles:
                        permissions.extend(self.roles[parent_role_id].permissions)

        return permissions

    def _matches_permission(
        self,
        permission: Permission,
        resource: str,
        action: str,
    ) -> bool:
        """Check if permission matches resource and action"""
        # Wildcard matching
        resource_match = (
            permission.resource == "*" or
            permission.resource == resource or
            (permission.resource.endswith("*") and resource.startswith(permission.resource[:-1]))
        )

        action_match = permission.action == "*" or permission.action == action

        return resource_match and action_match

    def _evaluate_conditions(
        self,
        conditions: Dict,
        user: User,
        context: Optional[Dict],
    ) -> bool:
        """Evaluate ABAC conditions"""
        # Example conditions:
        # - user.department == "engineering"
        # - context.time_of_day in ["business_hours"]
        # - context.location in ["office"]

        for key, expected_value in conditions.items():
            if key.startswith("user."):
                attr = key[5:]
                if user.attributes.get(attr) != expected_value:
                    return False

            elif key.startswith("context.") and context:
                attr = key[8:]
                if context.get(attr) != expected_value:
                    return False

        return True

    def generate_token(
        self,
        user_id: str,
        token_type: TokenType = TokenType.ACCESS,
        scopes: Optional[List[str]] = None,
        expiry_minutes: Optional[int] = None,
    ) -> str:
        """
        Generate authentication token (JWT-like)

        Args:
            user_id: User ID
            token_type: Type of token
            scopes: Token scopes
            expiry_minutes: Expiration time in minutes

        Returns:
            Token string
        """
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")

        token_id = secrets.token_urlsafe(32)
        expiry = expiry_minutes or self.token_expiry_minutes

        token = Token(
            token_id=token_id,
            token_type=token_type,
            user_id=user_id,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=expiry),
            scopes=scopes or [],
            metadata={},
        )

        self.tokens[token_id] = token

        # In production, encode as JWT
        token_string = self._encode_token(token)

        self._log_audit('token_generated', user_id, {'token_type': token_type.value})
        return token_string

    def validate_token(self, token_string: str) -> Optional[Token]:
        """Validate and decode token"""
        try:
            token = self._decode_token(token_string)

            if token.token_id not in self.tokens:
                return None

            stored_token = self.tokens[token.token_id]

            # Check expiration
            if datetime.now() > stored_token.expires_at:
                del self.tokens[token.token_id]
                return None

            return stored_token

        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    def _encode_token(self, token: Token) -> str:
        """Encode token as base64 (simplified JWT)"""
        # In production, use proper JWT library
        payload = {
            'token_id': token.token_id,
            'user_id': token.user_id,
            'type': token.token_type.value,
            'iat': token.issued_at.timestamp(),
            'exp': token.expires_at.timestamp(),
            'scopes': token.scopes,
        }
        encoded = json.dumps(payload).encode('utf-8')
        return secrets.token_urlsafe(16) + '.' + encoded.hex()

    def _decode_token(self, token_string: str) -> Token:
        """Decode token from base64"""
        parts = token_string.split('.')
        if len(parts) != 2:
            raise ValueError("Invalid token format")

        payload = json.loads(bytes.fromhex(parts[1]).decode('utf-8'))

        return Token(
            token_id=payload['token_id'],
            token_type=TokenType(payload['type']),
            user_id=payload['user_id'],
            issued_at=datetime.fromtimestamp(payload['iat']),
            expires_at=datetime.fromtimestamp(payload['exp']),
            scopes=payload['scopes'],
            metadata={},
        )

    def _create_session(
        self,
        user: User,
        auth_method: AuthMethod,
        ip_address: str,
        user_agent: str,
    ) -> Session:
        """Create user session"""
        session_id = secrets.token_urlsafe(32)

        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            auth_method=auth_method,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=self.session_timeout_minutes),
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.sessions[session_id] = session
        return session

    def _validate_password(self, password: str) -> bool:
        """Validate password meets policy requirements"""
        if len(password) < self.password_min_length:
            return False

        if self.password_require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False

        return True

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

    def _verify_mfa(self, user: User, code: str) -> bool:
        """Verify MFA code (TOTP)"""
        # In production, use pyotp library
        # This is a simplified simulation
        if not user.mfa_secret:
            return False

        # Simulate TOTP verification
        expected_code = hashlib.sha256(
            (user.mfa_secret + str(int(time.time() / 30))).encode()
        ).hexdigest()[:6]

        return code == expected_code

    def _log_audit(self, event: str, user_id: Optional[str], details: Dict) -> None:
        """Log audit event"""
        self.audit_log.append({
            'timestamp': datetime.now(),
            'event': event,
            'user_id': user_id,
            'details': details,
        })

    def get_statistics(self) -> Dict:
        """Get IAM statistics"""
        active_sessions = sum(1 for s in self.sessions.values() if s.active)
        active_tokens = sum(
            1 for t in self.tokens.values()
            if datetime.now() < t.expires_at
        )

        # Recent authentication attempts
        recent_window = datetime.now() - timedelta(hours=1)
        recent_auth = [
            a for a in self.audit_log
            if a['timestamp'] > recent_window and a['event'].startswith('auth_')
        ]

        auth_success = sum(1 for a in recent_auth if a['event'] == 'auth_success')
        auth_failed = sum(1 for a in recent_auth if a['event'] == 'auth_failed')

        return {
            'total_users': len(self.users),
            'active_users': sum(1 for u in self.users.values() if u.active),
            'total_roles': len(self.roles),
            'active_sessions': active_sessions,
            'active_tokens': active_tokens,
            'recent_auth_attempts': len(recent_auth),
            'recent_auth_success': auth_success,
            'recent_auth_failed': auth_failed,
            'success_rate': (auth_success / len(recent_auth) * 100) if recent_auth else 0,
        }
