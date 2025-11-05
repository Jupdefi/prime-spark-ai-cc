"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from auth.auth import auth_manager, get_current_user, User


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    roles: list[str] = ["user"]


@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Example:
    ```
    POST /api/auth/login
    {
        "username": "admin",
        "password": "your_password"
    }
    ```
    """
    user = auth_manager.authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = auth_manager.create_access_token(
        username=user.username,
        roles=user.roles
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_manager.expiration_hours * 3600,
        "user": {
            "username": user.username,
            "roles": user.roles
        }
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires: Valid JWT token in Authorization header.
    """
    return {
        "username": current_user.username,
        "roles": current_user.roles,
        "is_active": current_user.is_active
    }


@router.post("/users", dependencies=[Depends(auth_manager.require_role("admin"))])
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user.

    Requires: Admin role.
    """
    try:
        user = auth_manager.create_user(
            username=request.username,
            password=request.password,
            roles=request.roles
        )

        return {
            "username": user.username,
            "roles": user.roles,
            "is_active": user.is_active
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{username}", dependencies=[Depends(auth_manager.require_role("admin"))])
async def get_user(username: str):
    """
    Get user information.

    Requires: Admin role.
    """
    user = auth_manager.get_user(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "username": user.username,
        "roles": user.roles,
        "is_active": user.is_active
    }
