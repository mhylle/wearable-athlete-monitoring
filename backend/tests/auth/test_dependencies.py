"""Tests for FastAPI authentication dependencies."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.auth.dependencies import get_current_user, require_athlete, require_coach
from app.auth.jwt import create_access_token, create_refresh_token
from app.config import settings
from app.models.user import User


def _make_credentials(token: str) -> MagicMock:
    """Create a mock HTTPAuthorizationCredentials."""
    creds = MagicMock()
    creds.credentials = token
    return creds


def _make_user(role: str = "coach", is_active: bool = True) -> User:
    """Create a User instance for testing."""
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        role=role,
        full_name="Test User",
        is_active=is_active,
    )


def _make_db_session(user: User | None) -> AsyncMock:
    """Create a mock async db session that returns the given user."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    return mock_session


class TestGetCurrentUser:
    """Test the get_current_user dependency."""

    async def test_valid_token_returns_user(self) -> None:
        user = _make_user("coach")
        token = create_access_token(user.id, user.role)
        creds = _make_credentials(token)
        db = _make_db_session(user)

        result = await get_current_user(credentials=creds, db=db)
        assert result.id == user.id

    async def test_invalid_token_raises_401(self) -> None:
        creds = _make_credentials("invalid.token.here")
        db = _make_db_session(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    async def test_expired_token_raises_401(self) -> None:
        payload = {
            "sub": str(uuid.uuid4()),
            "role": "coach",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = pyjwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        creds = _make_credentials(token)
        db = _make_db_session(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    async def test_refresh_token_type_raises_401(self) -> None:
        user = _make_user("coach")
        token = create_refresh_token(user.id)
        creds = _make_credentials(token)
        db = _make_db_session(user)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401
        assert "token type" in exc_info.value.detail.lower()

    async def test_inactive_user_raises_401(self) -> None:
        user = _make_user("coach", is_active=False)
        token = create_access_token(user.id, user.role)
        creds = _make_credentials(token)
        db = _make_db_session(user)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    async def test_nonexistent_user_raises_401(self) -> None:
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "coach")
        creds = _make_credentials(token)
        db = _make_db_session(None)  # User not found

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401


class TestRequireCoach:
    """Test the require_coach dependency."""

    async def test_coach_allowed(self) -> None:
        user = _make_user("coach")
        result = await require_coach(current_user=user)
        assert result.role == "coach"

    async def test_athlete_rejected(self) -> None:
        user = _make_user("athlete")
        with pytest.raises(HTTPException) as exc_info:
            await require_coach(current_user=user)
        assert exc_info.value.status_code == 403


class TestRequireAthlete:
    """Test the require_athlete dependency."""

    async def test_athlete_allowed(self) -> None:
        user = _make_user("athlete")
        result = await require_athlete(current_user=user)
        assert result.role == "athlete"

    async def test_coach_rejected(self) -> None:
        user = _make_user("coach")
        with pytest.raises(HTTPException) as exc_info:
            await require_athlete(current_user=user)
        assert exc_info.value.status_code == 403
