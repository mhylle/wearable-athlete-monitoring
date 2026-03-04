"""Pydantic schemas for authentication."""

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request payload."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request payload."""

    email: EmailStr
    password: str
    full_name: str
    role: str = "athlete"


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str
    role: str
    team_id: str | None = None
    type: str = "access"


class UserResponse(BaseModel):
    """Public user information response."""

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    team_id: uuid.UUID | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}
