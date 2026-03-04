"""Authentication and authorization module."""

from app.auth.dependencies import get_current_user, require_athlete, require_coach
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, verify_password

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "hash_password",
    "require_athlete",
    "require_coach",
    "verify_password",
]
