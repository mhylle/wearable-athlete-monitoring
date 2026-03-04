"""Tests for athlete profile endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.athlete_profile import AthleteProfile
from app.models.user import User
from tests.api.conftest import auth_header


@pytest.mark.asyncio
class TestGetAthleteProfile:
    """Tests for GET /api/v1/athletes/{athlete_id}/profile."""

    async def test_get_profile_as_coach(
        self,
        test_app: AsyncClient,
        coach_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{athlete_user.id}/profile",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["position"] == "Forward"
        assert data["height_cm"] == 180.0
        assert data["weight_kg"] == 75.0

    async def test_get_profile_as_self(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{athlete_user.id}/profile",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 200
        assert resp.json()["position"] == "Forward"

    async def test_get_profile_not_found(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{uuid.uuid4()}/profile",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 404

    async def test_get_profile_other_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/athletes/{uuid.uuid4()}/profile",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestUpdateAthleteProfile:
    """Tests for PUT /api/v1/athletes/{athlete_id}/profile."""

    async def test_update_profile_as_coach(
        self,
        test_app: AsyncClient,
        coach_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/athletes/{athlete_user.id}/profile",
            headers=auth_header(coach_token),
            json={"position": "Goalkeeper", "weight_kg": 80.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["position"] == "Goalkeeper"
        assert data["weight_kg"] == 80.0

    async def test_update_profile_as_self(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/athletes/{athlete_user.id}/profile",
            headers=auth_header(athlete_token),
            json={"height_cm": 182.0},
        )
        assert resp.status_code == 200
        assert resp.json()["height_cm"] == 182.0

    async def test_update_profile_other_athlete(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/athletes/{uuid.uuid4()}/profile",
            headers=auth_header(athlete_token),
            json={"position": "Hack"},
        )
        assert resp.status_code == 403

    async def test_update_profile_not_found(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/athletes/{uuid.uuid4()}/profile",
            headers=auth_header(coach_token),
            json={"position": "Hack"},
        )
        assert resp.status_code == 404
