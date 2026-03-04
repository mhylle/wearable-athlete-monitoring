"""Tests for athlete management endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.api.conftest import auth_header


@pytest.mark.asyncio
class TestListAthletes:
    """Tests for GET /api/v1/athletes/."""

    async def test_list_athletes_as_coach(
        self,
        test_app: AsyncClient,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        resp = await test_app.get(
            "/api/v1/athletes/", headers=auth_header(coach_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["email"] == "athlete@test.com"

    async def test_list_athletes_without_auth(self, test_app: AsyncClient) -> None:
        resp = await test_app.get("/api/v1/athletes/")
        assert resp.status_code == 401

    async def test_list_athletes_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.get(
            "/api/v1/athletes/", headers=auth_header(athlete_token)
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestCreateAthlete:
    """Tests for POST /api/v1/athletes/."""

    async def test_create_athlete(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/athletes/",
            headers=auth_header(coach_token),
            json={
                "email": "newathlete@test.com",
                "password": "secret123",
                "full_name": "New Athlete",
                "position": "Midfielder",
                "height_cm": 175.0,
                "weight_kg": 70.0,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newathlete@test.com"
        assert data["full_name"] == "New Athlete"

    async def test_create_athlete_duplicate_email(
        self, test_app: AsyncClient, coach_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.post(
            "/api/v1/athletes/",
            headers=auth_header(coach_token),
            json={
                "email": "athlete@test.com",
                "password": "secret123",
                "full_name": "Duplicate",
            },
        )
        assert resp.status_code == 409

    async def test_create_athlete_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/athletes/",
            headers=auth_header(athlete_token),
            json={
                "email": "hack@test.com",
                "password": "secret123",
                "full_name": "Hacker",
            },
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestGetAthlete:
    """Tests for GET /api/v1/athletes/{athlete_id}."""

    async def test_get_athlete_as_coach(
        self, test_app: AsyncClient, coach_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{athlete_user.id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "athlete@test.com"

    async def test_get_athlete_as_self(
        self, test_app: AsyncClient, athlete_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{athlete_user.id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 200

    async def test_get_athlete_not_found(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{uuid.uuid4()}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 404

    async def test_get_other_athlete_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        """An athlete should not be able to see another athlete's details."""
        resp = await test_app.get(
            f"/api/v1/athletes/{uuid.uuid4()}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestUpdateAthlete:
    """Tests for PUT /api/v1/athletes/{athlete_id}."""

    async def test_update_athlete_as_coach(
        self, test_app: AsyncClient, coach_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/athletes/{athlete_user.id}",
            headers=auth_header(coach_token),
            json={"full_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    async def test_update_athlete_as_self(
        self, test_app: AsyncClient, athlete_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/athletes/{athlete_user.id}",
            headers=auth_header(athlete_token),
            json={"full_name": "Self Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Self Updated"


@pytest.mark.asyncio
class TestDeactivateAthlete:
    """Tests for DELETE /api/v1/athletes/{athlete_id}."""

    async def test_deactivate_athlete(
        self, test_app: AsyncClient, coach_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.delete(
            f"/api/v1/athletes/{athlete_user.id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 204

    async def test_deactivate_athlete_as_athlete(
        self, test_app: AsyncClient, athlete_token: str, athlete_user: User
    ) -> None:
        resp = await test_app.delete(
            f"/api/v1/athletes/{athlete_user.id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403

    async def test_deactivate_nonexistent(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.delete(
            f"/api/v1/athletes/{uuid.uuid4()}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 404
