"""Tests for the POST /api/v1/auth/refresh endpoint."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from httpx import AsyncClient

from app.auth.jwt import create_access_token, create_refresh_token
from app.config import settings
from app.models.user import User


class TestRefreshEndpoint:
    """Test token refresh."""

    async def test_refresh_with_valid_token(
        self, test_app: AsyncClient, registered_user: User
    ) -> None:
        refresh_token = create_refresh_token(registered_user.id)
        response = await test_app.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_expired_token(self, test_app: AsyncClient) -> None:
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        expired_token = pyjwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        response = await test_app.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token},
        )
        assert response.status_code == 401

    async def test_refresh_with_access_token_rejected(
        self, test_app: AsyncClient, registered_user: User
    ) -> None:
        access_token = create_access_token(registered_user.id, registered_user.role)
        response = await test_app.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401

    async def test_refresh_with_invalid_token(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_refresh_for_nonexistent_user(self, test_app: AsyncClient) -> None:
        fake_token = create_refresh_token(uuid.uuid4())
        response = await test_app.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": fake_token},
        )
        assert response.status_code == 401
