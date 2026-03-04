"""Tests for JWT token creation and validation."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.config import settings


class TestAccessToken:
    """Test access token creation and decoding."""

    def test_create_access_token(self) -> None:
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "coach")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_claims(self) -> None:
        user_id = uuid.uuid4()
        team_id = uuid.uuid4()
        token = create_access_token(user_id, "coach", team_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "coach"
        assert payload["team_id"] == str(team_id)
        assert payload["type"] == "access"

    def test_access_token_without_team_id(self) -> None:
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "athlete")
        payload = decode_token(token)
        assert payload["team_id"] is None
        assert payload["role"] == "athlete"

    def test_access_token_has_expiry(self) -> None:
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "coach")
        payload = decode_token(token)
        assert "exp" in payload
        assert "iat" in payload


class TestRefreshToken:
    """Test refresh token creation and decoding."""

    def test_create_refresh_token(self) -> None:
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        assert isinstance(token, str)

    def test_refresh_token_contains_claims(self) -> None:
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_refresh_token_has_no_role(self) -> None:
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert "role" not in payload


class TestDecodeToken:
    """Test token decoding edge cases."""

    def test_expired_token_rejected(self) -> None:
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = pyjwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)

    def test_invalid_token_rejected(self) -> None:
        with pytest.raises(pyjwt.PyJWTError):
            decode_token("not.a.valid.token")

    def test_wrong_secret_rejected(self) -> None:
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(pyjwt.InvalidSignatureError):
            decode_token(token)
