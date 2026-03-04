"""Tests for the GET /api/v1/auth/me endpoint."""

from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.models.user import User


class TestMeEndpoint:
    """Test the /me endpoint for retrieving current user info."""

    async def test_me_with_valid_token(
        self, test_app: AsyncClient, registered_user: User
    ) -> None:
        token = create_access_token(registered_user.id, registered_user.role)
        response = await test_app.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user.email
        assert data["role"] == registered_user.role
        assert data["full_name"] == registered_user.full_name

    async def test_me_without_token(self, test_app: AsyncClient) -> None:
        response = await test_app.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    async def test_me_with_invalid_token(self, test_app: AsyncClient) -> None:
        response = await test_app.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
