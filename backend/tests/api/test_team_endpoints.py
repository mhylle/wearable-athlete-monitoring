"""Tests for team management endpoints."""

import pytest
from httpx import AsyncClient

from app.models.team import Team
from tests.api.conftest import auth_header


@pytest.mark.asyncio
class TestGetTeam:
    """Tests for GET /api/v1/team/."""

    async def test_get_team_as_coach(
        self, test_app: AsyncClient, coach_token: str, team: Team
    ) -> None:
        resp = await test_app.get("/api/v1/team/", headers=auth_header(coach_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test FC"
        assert data["sport"] == "football"
        assert data["id"] == str(team.id)

    async def test_get_team_without_auth(self, test_app: AsyncClient) -> None:
        resp = await test_app.get("/api/v1/team/")
        assert resp.status_code == 401

    async def test_get_team_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.get("/api/v1/team/", headers=auth_header(athlete_token))
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestUpdateTeam:
    """Tests for PUT /api/v1/team/."""

    async def test_update_team_name(
        self, test_app: AsyncClient, coach_token: str, team: Team
    ) -> None:
        resp = await test_app.put(
            "/api/v1/team/",
            headers=auth_header(coach_token),
            json={"name": "Updated FC"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated FC"
        assert data["sport"] == "football"

    async def test_update_team_sport(
        self, test_app: AsyncClient, coach_token: str, team: Team
    ) -> None:
        resp = await test_app.put(
            "/api/v1/team/",
            headers=auth_header(coach_token),
            json={"sport": "basketball"},
        )
        assert resp.status_code == 200
        assert resp.json()["sport"] == "basketball"

    async def test_update_team_without_auth(self, test_app: AsyncClient) -> None:
        resp = await test_app.put("/api/v1/team/", json={"name": "Hack"})
        assert resp.status_code == 401

    async def test_update_team_as_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.put(
            "/api/v1/team/",
            headers=auth_header(athlete_token),
            json={"name": "Hack"},
        )
        assert resp.status_code == 403
