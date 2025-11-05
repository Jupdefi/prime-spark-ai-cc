"""
Authentication and Authorization System
JWT-based authentication with role-based access control
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config.settings import settings


# Password hashing using pbkdf2_sha256 (built-in, no external deps)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


class User(BaseModel):
    """User model"""
    username: str
    roles: list[str] = ["user"]
    is_active: bool = True


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: str
    roles: list[str]


class AuthManager:
    """Authentication and authorization manager"""

    def __init__(self):
        self.secret_key = settings.auth.jwt_secret
        self.algorithm = settings.auth.jwt_algorithm
        self.expiration_hours = settings.auth.jwt_expiration_hours

        # In-memory user store (replace with database in production)
        self.users = {
            settings.auth.admin_username: {
                "username": settings.auth.admin_username,
                "hashed_password": self.hash_password(settings.auth.admin_password),
                "roles": ["admin", "user"],
                "is_active": True
            }
        }

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        username: str,
        roles: list[str],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)

        to_encode = {
            "sub": username,
            "roles": roles,
            "exp": expire
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            roles: list[str] = payload.get("roles", [])

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )

            return TokenData(username=username, roles=roles)

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user_data = self.users.get(username)

        if not user_data:
            return None

        if not self.verify_password(password, user_data["hashed_password"]):
            return None

        return User(
            username=user_data["username"],
            roles=user_data["roles"],
            is_active=user_data["is_active"]
        )

    def create_user(
        self,
        username: str,
        password: str,
        roles: list[str] = ["user"]
    ) -> User:
        """Create a new user"""
        if username in self.users:
            raise ValueError("Username already exists")

        hashed_password = self.hash_password(password)

        self.users[username] = {
            "username": username,
            "hashed_password": hashed_password,
            "roles": roles,
            "is_active": True
        }

        return User(username=username, roles=roles, is_active=True)

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_data = self.users.get(username)

        if not user_data:
            return None

        return User(
            username=user_data["username"],
            roles=user_data["roles"],
            is_active=user_data["is_active"]
        )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> User:
        """FastAPI dependency to get current authenticated user"""
        token = credentials.credentials
        token_data = self.verify_token(token)

        user = self.get_user(token_data.username)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return user

    def require_role(self, required_role: str):
        """FastAPI dependency to require a specific role"""
        async def role_checker(user: User = Depends(self.get_current_user)) -> User:
            if required_role not in user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            return user

        return role_checker


# Global auth manager instance
auth_manager = AuthManager()


# Convenience dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user"""
    return await auth_manager.get_current_user(credentials)


def require_admin():
    """Require admin role"""
    return auth_manager.require_role("admin")
