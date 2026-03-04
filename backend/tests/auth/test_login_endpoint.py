"""Tests for the POST /api/v1/auth/login endpoint."""

from httpx import AsyncClient

from app.models.user import User


class TestLoginEndpoint:
    """Test user login and token issuance."""

    async def test_login_valid_credentials(
        self, test_app: AsyncClient, registered_user: User
    ) -> None:
        response = await test_app.post(
            "/api/v1/auth/login",
            json={"email": "coach@test.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, test_app: AsyncClient, registered_user: User
    ) -> None:
        response = await test_app.post(
            "/api/v1/auth/login",
            json={"email": "coach@test.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.com", "password": "testpass123"},
        )
        assert response.status_code == 401

    async def test_login_invalid_email_format(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "testpass123"},
        )
        assert response.status_code == 422
