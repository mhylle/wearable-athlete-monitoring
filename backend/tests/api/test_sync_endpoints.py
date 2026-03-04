"""Tests for sync API endpoints."""

import uuid
from unittest.mock import MagicMock, patch

from httpx import AsyncClient

from tests.api.conftest import auth_header


class TestTriggerAthleteSync:
    """Test POST /api/v1/sync/athlete/{athlete_id}."""

    @patch("app.api.sync_router.sync_athlete_data_task")
    async def test_coach_can_trigger_sync(
        self, mock_task: MagicMock, test_app: AsyncClient, coach_token: str
    ) -> None:
        athlete_id = str(uuid.uuid4())
        response = await test_app.post(
            f"/api/v1/sync/athlete/{athlete_id}",
            headers=auth_header(coach_token),
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["athlete_id"] == athlete_id
        mock_task.delay.assert_called_once_with(athlete_id)

    async def test_athlete_cannot_trigger_sync(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        athlete_id = str(uuid.uuid4())
        response = await test_app.post(
            f"/api/v1/sync/athlete/{athlete_id}",
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 403

    async def test_unauthenticated_rejected(self, test_app: AsyncClient) -> None:
        athlete_id = str(uuid.uuid4())
        response = await test_app.post(f"/api/v1/sync/athlete/{athlete_id}")
        assert response.status_code in (401, 403)


class TestTriggerTeamSync:
    """Test POST /api/v1/sync/team."""

    @patch("app.api.sync_router.sync_all_athletes_task")
    async def test_coach_can_trigger_team_sync(
        self, mock_task: MagicMock, test_app: AsyncClient, coach_token: str
    ) -> None:
        response = await test_app.post(
            "/api/v1/sync/team",
            headers=auth_header(coach_token),
        )
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        mock_task.delay.assert_called_once()

    async def test_athlete_cannot_trigger_team_sync(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        response = await test_app.post(
            "/api/v1/sync/team",
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 403


class TestGetSyncStatuses:
    """Test GET /api/v1/sync/status."""

    @patch("app.api.sync_router.get_all_sync_statuses")
    async def test_coach_can_get_statuses(
        self, mock_statuses: MagicMock, test_app: AsyncClient, coach_token: str
    ) -> None:
        mock_statuses.return_value = [
            {"athlete_id": "a1", "status": "completed", "last_sync_at": "2026-02-28T08:00:00"},
            {"athlete_id": "a2", "status": "error", "error": "API timeout"},
        ]
        response = await test_app.get(
            "/api/v1/sync/status",
            headers=auth_header(coach_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["status"] == "completed"

    async def test_athlete_cannot_get_statuses(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        response = await test_app.get(
            "/api/v1/sync/status",
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 403


class TestGetAthleteStatus:
    """Test GET /api/v1/sync/status/{athlete_id}."""

    @patch("app.api.sync_router.get_sync_status")
    async def test_returns_status_for_synced_athlete(
        self, mock_status: MagicMock, test_app: AsyncClient, coach_token: str
    ) -> None:
        athlete_id = str(uuid.uuid4())
        mock_status.return_value = {
            "athlete_id": athlete_id,
            "status": "completed",
            "last_sync_at": "2026-02-28T08:00:00",
        }
        response = await test_app.get(
            f"/api/v1/sync/status/{athlete_id}",
            headers=auth_header(coach_token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @patch("app.api.sync_router.get_sync_status")
    async def test_returns_never_synced_for_unknown(
        self, mock_status: MagicMock, test_app: AsyncClient, coach_token: str
    ) -> None:
        athlete_id = str(uuid.uuid4())
        mock_status.return_value = None
        response = await test_app.get(
            f"/api/v1/sync/status/{athlete_id}",
            headers=auth_header(coach_token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "never_synced"
