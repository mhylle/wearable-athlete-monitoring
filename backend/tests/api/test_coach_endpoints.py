"""Tests for coach management endpoints."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.api.conftest import auth_header


@pytest.mark.asyncio
class TestListCoaches:
    """Tests for GET /api/v1/coaches/."""

    async def test_list_coaches(
        self, test_app: AsyncClient, coach_token: str, coach_user: User
    ) -> None:
        resp = await test_app.get(
            "/api/v1/coaches/", headers=auth_header(coach_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["email"] == "coach@test.com"

    async def test_list_coaches_without_auth(self, test_app: AsyncClient) -> None:
        resp = await test_app.get("/api/v1/coaches/")
        assert resp.status_code == 401

    async def test_list_coaches_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.get(
            "/api/v1/coaches/", headers=auth_header(athlete_token)
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestInviteCoach:
    """Tests for POST /api/v1/coaches/invite."""

    async def test_invite_coach(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/coaches/invite",
            headers=auth_header(coach_token),
            json={
                "email": "newcoach@test.com",
                "full_name": "Assistant Coach",
                "password": "secret123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newcoach@test.com"
        assert data["full_name"] == "Assistant Coach"

    async def test_invite_duplicate_email(
        self, test_app: AsyncClient, coach_token: str, coach_user: User
    ) -> None:
        resp = await test_app.post(
            "/api/v1/coaches/invite",
            headers=auth_header(coach_token),
            json={
                "email": "coach@test.com",
                "full_name": "Duplicate",
                "password": "secret123",
            },
        )
        assert resp.status_code == 409

    async def test_invite_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/coaches/invite",
            headers=auth_header(athlete_token),
            json={
                "email": "hack@test.com",
                "full_name": "Hacker",
                "password": "secret123",
            },
        )
        assert resp.status_code == 403
