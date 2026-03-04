"""E2E test: sync journey (mocked Celery + Redis)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from app.auth.password import hash_password
from app.models.metric_record import MetricRecord
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


async def _setup_team_coach_athlete(
    db: AsyncSession,
) -> tuple[str, str, str]:
    """Create team, coach, and athlete in DB. Returns (team_id, coach_id, athlete_id)."""
    team = Team(name="FC Sync", sport="football")
    db.add(team)
    await db.commit()
    await db.refresh(team)

    coach = User(
        email=COACH_EMAIL,
        hashed_password=hash_password(COACH_PASSWORD),
        role="coach",
        full_name="Coach Smith",
        team_id=team.id,
    )
    db.add(coach)
    await db.commit()
    await db.refresh(coach)

    athlete = User(
        email=ATHLETE_EMAIL,
        hashed_password=hash_password(ATHLETE_PASSWORD),
        role="athlete",
        full_name="Alice Runner",
        team_id=team.id,
        ow_user_id="ow-test-123",
    )
    db.add(athlete)
    await db.commit()
    await db.refresh(athlete)

    return str(team.id), str(coach.id), str(athlete.id)


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _insert_metric_records(
    db: AsyncSession,
    athlete_id: str,
    metric_type: str,
    values: list[tuple[datetime, float]],
) -> None:
    """Insert metric records for testing analytics endpoints."""
    for recorded_at, value in values:
        record = MetricRecord(
            athlete_id=uuid.UUID(athlete_id),
            metric_type=metric_type,
            recorded_at=recorded_at,
            value=value,
            source="open_wearables",
        )
        db.add(record)
    await db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSyncJourney:
    """Sync flow: trigger sync (mocked), verify status, verify analytics endpoints."""

    @patch("app.api.sync_router.sync_athlete_data_task")
    async def test_trigger_athlete_sync(
        self,
        mock_task: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        mock_task.delay = MagicMock()

        resp = await client.post(
            f"/api/v1/sync/athlete/{athlete_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["athlete_id"] == athlete_id
        mock_task.delay.assert_called_once_with(athlete_id)

    @patch("app.api.sync_router.sync_all_athletes_task")
    async def test_trigger_team_sync(
        self,
        mock_task: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        mock_task.delay = MagicMock()

        resp = await client.post(
            "/api/v1/sync/team",
            headers=auth_header(token),
        )
        assert resp.status_code == 202
        assert resp.json()["status"] == "accepted"
        mock_task.delay.assert_called_once()

    @patch("app.api.sync_router.get_sync_status")
    async def test_get_sync_status(
        self,
        mock_status: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        mock_status.return_value = {
            "athlete_id": athlete_id,
            "status": "completed",
            "last_sync_at": "2024-06-01T12:00:00+00:00",
            "error": None,
        }

        resp = await client.get(
            f"/api/v1/sync/status/{athlete_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    @patch("app.api.sync_router.get_sync_status")
    async def test_get_sync_status_never_synced(
        self,
        mock_status: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        mock_status.return_value = None

        resp = await client.get(
            f"/api/v1/sync/status/{athlete_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "never_synced"

    @patch("app.api.sync_router.get_all_sync_statuses")
    async def test_get_all_sync_statuses(
        self,
        mock_statuses: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        mock_statuses.return_value = [
            {
                "athlete_id": athlete_id,
                "status": "completed",
                "last_sync_at": "2024-06-01T12:00:00+00:00",
                "error": None,
            }
        ]

        resp = await client.get(
            "/api/v1/sync/status",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_metric_records_available_after_insert(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Simulate synced metrics and verify analytics endpoint can read them."""
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        # Insert metric records as if sync had happened
        base_dt = datetime(2024, 6, 1, 8, 0, tzinfo=UTC)
        await _insert_metric_records(
            db_session,
            athlete_id,
            "training_load",
            [(base_dt.replace(day=d), 100.0 + d * 5) for d in range(1, 8)],
        )

        # ACWR endpoint should reflect the inserted data
        resp = await client.get(
            f"/api/v1/analytics/athlete/{athlete_id}/acwr",
            headers=auth_header(token),
            params={"as_of_date": "2024-06-07"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "acwr_value" in body

    async def test_hrv_analytics_with_metrics(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Verify HRV analysis endpoint with inserted metrics."""
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        base_dt = datetime(2024, 6, 1, 7, 0, tzinfo=UTC)
        await _insert_metric_records(
            db_session,
            athlete_id,
            "hrv_rmssd",
            [(base_dt.replace(day=d), 45.0 + d) for d in range(1, 15)],
        )

        resp = await client.get(
            f"/api/v1/analytics/athlete/{athlete_id}/hrv",
            headers=auth_header(token),
            params={"start": "2024-06-01", "end": "2024-06-14"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["daily_values"]) > 0

    async def test_recovery_endpoint_with_metrics(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Verify recovery score with inserted metrics."""
        _, _, athlete_id = await _setup_team_coach_athlete(db_session)
        token = await _login(client, COACH_EMAIL, COACH_PASSWORD)

        base_dt = datetime(2024, 6, 1, 7, 0, tzinfo=UTC)
        # Insert HRV data
        await _insert_metric_records(
            db_session,
            athlete_id,
            "hrv_rmssd",
            [(base_dt.replace(day=d), 50.0) for d in range(1, 8)],
        )

        resp = await client.get(
            f"/api/v1/analytics/athlete/{athlete_id}/recovery",
            headers=auth_header(token),
            params={"date": "2024-06-07"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total_score" in body
        assert isinstance(body["available_components"], list)

    @patch("app.api.sync_router.sync_athlete_data_task")
    async def test_athlete_cannot_trigger_sync(
        self,
        mock_task: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Athletes should not be able to trigger sync (coach-only)."""
        await _setup_team_coach_athlete(db_session)
        token = await _login(client, ATHLETE_EMAIL, ATHLETE_PASSWORD)

        resp = await client.post(
            "/api/v1/sync/team",
            headers=auth_header(token),
        )
        assert resp.status_code == 403
