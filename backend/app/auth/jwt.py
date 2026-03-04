"""JWT token creation and validation using PyJWT."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    team_id: uuid.UUID | None = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "team_id": str(team_id) if team_id else None,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a JWT refresh token."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, object]:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    result: dict[str, object] = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    return result
