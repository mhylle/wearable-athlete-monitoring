"""E2E test: full coach journey."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.models.team import Team
from tests.e2e.conftest import auth_header

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COACH_EMAIL = "coach@test.com"
COACH_PASSWORD = "CoachPass123!"
COACH_NAME = "Test Coach"

ATHLETES = [
    {"email": "alice@test.com", "password": "Pass123!", "full_name": "Alice A"},
    {"email": "bob@test.com", "password": "Pass123!", "full_name": "Bob B"},
    {"email": "carol@test.com", "password": "Pass123!", "full_name": "Carol C"},
]


async def _register_coach(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": COACH_EMAIL,
            "password": COACH_PASSWORD,
            "full_name": COACH_NAME,
            "role": "coach",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _create_team_and_assign(db: AsyncSession, coach_id: str) -> str:
    """Create a team directly in the DB and assign the coach to it."""
    from sqlalchemy import select

    from app.models.user import User

    team = Team(name="FC Test", sport="football")
    db.add(team)
    await db.commit()
    await db.refresh(team)

    result = await db.execute(select(User).where(User.id == uuid.UUID(coach_id)))
    coach = result.scalar_one()
    coach.team_id = team.id
    await db.commit()

    return str(team.id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCoachJourney:
    """Full coach journey: register, login, team, athletes, sessions, analytics."""

    async def test_register_coach(self, client: AsyncClient) -> None:
        data = await _register_coach(client)
        assert data["role"] == "coach"
        assert data["email"] == COACH_EMAIL

    async def test_login_and_get_me(self, client: AsyncClient) -> None:
        await _register_coach(client)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "coach"

    async def test_team_not_found_before_creation(
        self, client: AsyncClient
    ) -> None:
        await _register_coach(client)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.get("/api/v1/team/", headers=auth_header(token))
        assert resp.status_code == 404

    async def test_update_team(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        await _create_team_and_assign(db_session, coach_data["id"])

        # Re-login to get fresh token with team_id
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.put(
            "/api/v1/team/",
            headers=auth_header(token),
            json={"name": "FC Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "FC Updated"

    async def test_get_team(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.get("/api/v1/team/", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["name"] == "FC Test"
        assert resp.json()["sport"] == "football"

    async def test_add_athletes(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        athlete_ids = []
        for ath in ATHLETES:
            resp = await client.post(
                "/api/v1/athletes/",
                headers=auth_header(token),
                json=ath,
            )
            assert resp.status_code == 201, resp.text
            body = resp.json()
            assert body["full_name"] == ath["full_name"]
            athlete_ids.append(body["id"])

        assert len(athlete_ids) == 3

    async def test_list_athletes(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        for ath in ATHLETES:
            resp = await client.post(
                "/api/v1/athletes/", headers=auth_header(token), json=ath
            )
            assert resp.status_code == 201

        resp = await client.get("/api/v1/athletes/", headers=auth_header(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_log_session_for_athlete(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        # Create one athlete
        resp = await client.post(
            "/api/v1/athletes/",
            headers=auth_header(token),
            json=ATHLETES[0],
        )
        athlete_id = resp.json()["id"]

        # Log a training session
        resp = await client.post(
            "/api/v1/sessions/",
            headers=auth_header(token),
            json={
                "athlete_id": athlete_id,
                "session_type": "training",
                "start_time": datetime(2024, 6, 1, 10, 0, tzinfo=UTC).isoformat(),
                "end_time": datetime(2024, 6, 1, 11, 30, tzinfo=UTC).isoformat(),
                "duration_minutes": 90.0,
                "notes": "Morning training",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["athlete_id"] == athlete_id
        assert body["session_type"] == "training"
        assert body["source"] == "manual"

    async def test_list_athlete_sessions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.post(
            "/api/v1/athletes/",
            headers=auth_header(token),
            json=ATHLETES[0],
        )
        athlete_id = resp.json()["id"]

        # Log two sessions
        for i in range(2):
            await client.post(
                "/api/v1/sessions/",
                headers=auth_header(token),
                json={
                    "athlete_id": athlete_id,
                    "session_type": "training",
                    "start_time": datetime(
                        2024, 6, 1 + i, 10, 0, tzinfo=UTC
                    ).isoformat(),
                    "duration_minutes": 60.0,
                },
            )

        resp = await client.get(
            f"/api/v1/sessions/athlete/{athlete_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    async def test_acwr_endpoint_returns_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.post(
            "/api/v1/athletes/",
            headers=auth_header(token),
            json=ATHLETES[0],
        )
        athlete_id = resp.json()["id"]

        # ACWR should still return (possibly zeros) even without data
        resp = await client.get(
            f"/api/v1/analytics/athlete/{athlete_id}/acwr",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "acwr_value" in body
        assert "zone" in body

    async def test_team_acwr_overview(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.get(
            "/api/v1/analytics/team/acwr-overview",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "athletes" in body
        assert "date" in body

    async def test_team_recovery_overview(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        coach_data = await _register_coach(client)
        await _create_team_and_assign(db_session, coach_data["id"])
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        resp = await client.get(
            "/api/v1/analytics/team/recovery-overview",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "athletes" in body

    async def test_duplicate_email_rejected(self, client: AsyncClient) -> None:
        await _register_coach(client)
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": COACH_EMAIL,
                "password": "AnotherPass1!",
                "full_name": "Duplicate",
                "role": "coach",
            },
        )
        assert resp.status_code == 409

    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/athletes/")
        assert resp.status_code == 401
