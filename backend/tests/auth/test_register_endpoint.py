"""Tests for the POST /api/v1/auth/register endpoint."""

from httpx import AsyncClient

from app.models.user import User


class TestRegisterEndpoint:
    """Test user registration."""

    async def test_register_creates_user(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "securepass",
                "full_name": "New User",
                "role": "athlete",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["full_name"] == "New User"
        assert data["role"] == "athlete"
        assert "id" in data

    async def test_register_coach(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/register",
            json={
                "email": "coach@example.com",
                "password": "securepass",
                "full_name": "New Coach",
                "role": "coach",
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == "coach"

    async def test_register_duplicate_email(
        self, test_app: AsyncClient, registered_user: User
    ) -> None:
        response = await test_app.post(
            "/api/v1/auth/register",
            json={
                "email": registered_user.email,
                "password": "securepass",
                "full_name": "Dup User",
                "role": "athlete",
            },
        )
        assert response.status_code == 409

    async def test_register_missing_fields(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/register",
            json={"email": "partial@example.com"},
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepass",
                "full_name": "Bad Email",
                "role": "athlete",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_role(self, test_app: AsyncClient) -> None:
        response = await test_app.post(
            "/api/v1/auth/register",
            json={
                "email": "bad@example.com",
                "password": "securepass",
                "full_name": "Bad Role",
                "role": "admin",
            },
        )
        assert response.status_code == 422
