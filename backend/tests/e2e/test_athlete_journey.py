"""E2E test: athlete journey."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.auth.password import hash_password
from app.models.team import Team
from app.models.user import User
from tests.e2e.conftest import auth_header

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COACH_EMAIL = "coach@test.com"
COACH_PASSWORD = "CoachPass123!"
ATHLETE_EMAIL = "athlete@test.com"
ATHLETE_PASSWORD = "AthletePass123!"
OTHER_ATHLETE_EMAIL = "other@test.com"


async def _setup_team_and_coach(db: AsyncSession) -> tuple[str, str]:
    """Create a team and coach directly in DB. Returns (team_id, coach_id)."""
    team = Team(name="FC Test", sport="football")
    db.add(team)
    await db.commit()
    await db.refresh(team)

    coach = User(
        email=COACH_EMAIL,
        hashed_password=hash_password(COACH_PASSWORD),
        role="coach",
        full_name="Test Coach",
        team_id=team.id,
    )
    db.add(coach)
    await db.commit()
    await db.refresh(coach)
    return str(team.id), str(coach.id)


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _create_athlete_via_api(
    client: AsyncClient, coach_token: str, email: str, full_name: str
) -> str:
    resp = await client.post(
        "/api/v1/athletes/",
        headers=auth_header(coach_token),
        json={
            "email": email,
            "password": ATHLETE_PASSWORD,
            "full_name": full_name,
            "position": "midfielder",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAthleteJourney:
    """Athlete flow: login, submit wellness, view recovery, verify access control."""

    async def test_athlete_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        await _create_athlete_via_api(client, coach_token, ATHLETE_EMAIL, "Alice A")

        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)
        resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "athlete"

    async def test_submit_wellness(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.post(
            "/api/v1/wellness/",
            headers=auth_header(token),
            json={
                "date": "2024-06-01",
                "fatigue": 3,
                "soreness": 2,
                "mood": 4,
                "sleep_quality": 4,
                "srpe": 5,
                "notes": "Feeling good",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["athlete_id"] == athlete_id
        assert body["fatigue"] == 3
        assert body["mood"] == 4

    async def test_get_wellness_history(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        # Submit two entries
        for day in ("2024-06-01", "2024-06-02"):
            await client.post(
                "/api/v1/wellness/",
                headers=auth_header(token),
                json={"date": day, "fatigue": 3, "mood": 4},
            )

        resp = await client.get(
            f"/api/v1/wellness/athlete/{athlete_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    async def test_update_wellness(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        await _create_athlete_via_api(client, coach_token, ATHLETE_EMAIL, "Alice A")
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.post(
            "/api/v1/wellness/",
            headers=auth_header(token),
            json={"date": "2024-06-01", "fatigue": 3},
        )
        entry_id = resp.json()["id"]

        resp = await client.put(
            f"/api/v1/wellness/{entry_id}",
            headers=auth_header(token),
            json={"fatigue": 5, "mood": 2},
        )
        assert resp.status_code == 200
        assert resp.json()["fatigue"] == 5
        assert resp.json()["mood"] == 2

    async def test_view_own_sessions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        # Coach logs a session for the athlete
        await client.post(
            "/api/v1/sessions/",
            headers=auth_header(coach_token),
            json={
                "athlete_id": athlete_id,
                "session_type": "training",
                "start_time": datetime(
                    2024, 6, 1, 10, 0, tzinfo=UTC
                ).isoformat(),
                "duration_minutes": 60.0,
            },
        )

        # Athlete can view their own sessions
        resp = await client.get(
            f"/api/v1/sessions/athlete/{athlete_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    async def test_view_own_recovery(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.get(
            f"/api/v1/analytics/athlete/{athlete_id}/recovery",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total_score" in body

    async def test_403_for_other_athlete_wellness(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        await _create_athlete_via_api(
            client, coach_token, OTHER_ATHLETE_EMAIL, "Bob B"
        )

        # Login as the other athlete
        other_token = await _login(client, OTHER_ATHLETE_EMAIL, ATHLETE_PASSWORD)

        # Try to view Alice's wellness - should be forbidden
        resp = await client.get(
            f"/api/v1/wellness/athlete/{athlete_id}",
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403

    async def test_403_for_other_athlete_sessions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        await _create_athlete_via_api(
            client, coach_token, OTHER_ATHLETE_EMAIL, "Bob B"
        )
        other_token = await _login(client, OTHER_ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.get(
            f"/api/v1/sessions/athlete/{athlete_id}",
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403

    async def test_athlete_cannot_create_session(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.post(
            "/api/v1/sessions/",
            headers=auth_header(token),
            json={
                "athlete_id": athlete_id,
                "session_type": "training",
                "start_time": datetime(
                    2024, 6, 1, 10, 0, tzinfo=UTC
                ).isoformat(),
                "duration_minutes": 60.0,
            },
        )
        assert resp.status_code == 403

    async def test_athlete_cannot_list_all_athletes(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        await _create_athlete_via_api(client, coach_token, ATHLETE_EMAIL, "Alice A")
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.get("/api/v1/athletes/", headers=auth_header(token))
        assert resp.status_code == 403

    async def test_coach_can_view_athlete_wellness(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _setup_team_and_coach(db_session)
        coach_token = await _login(client, COACH_EMAIL, COACH_PASSWORD)
        athlete_id = await _create_athlete_via_api(
            client, coach_token, ATHLETE_EMAIL, "Alice A"
        )
        athlete_token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        # Athlete submits wellness
        await client.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json={"date": "2024-06-01", "fatigue": 4, "mood": 3},
        )

        # Coach can see it
        resp = await client.get(
            f"/api/v1/wellness/athlete/{athlete_id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
