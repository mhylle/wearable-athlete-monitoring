"""Tests for Health Connect data ingest API endpoints."""

import uuid
from datetime import datetime, timezone

from httpx import AsyncClient

from app.models.athlete_profile import AthleteProfile
from app.models.user import User
from tests.api.conftest import auth_header


class TestSyncHealthData:
    """Test POST /api/v1/health-data/sync."""

    async def test_athlete_can_sync_metrics(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        payload = {
            "metrics": [
                {
                    "metric_type": "heart_rate",
                    "value": 72.0,
                    "recorded_at": "2026-03-02T10:00:00Z",
                },
                {
                    "metric_type": "steps",
                    "value": 5000.0,
                    "recorded_at": "2026-03-02T10:00:00Z",
                },
            ],
            "exercise_sessions": [],
        }
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics_synced"] == 2
        assert data["metrics_skipped"] == 0

    async def test_duplicate_metrics_are_skipped(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        payload = {
            "metrics": [
                {
                    "metric_type": "heart_rate",
                    "value": 72.0,
                    "recorded_at": "2026-03-02T11:00:00Z",
                },
            ],
            "exercise_sessions": [],
        }
        # First sync
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        assert response.json()["metrics_synced"] == 1

        # Second sync with same data
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        assert response.json()["metrics_synced"] == 0
        assert response.json()["metrics_skipped"] == 1

    async def test_athlete_can_sync_exercise_sessions(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        payload = {
            "metrics": [],
            "exercise_sessions": [
                {
                    "exercise_type": "running",
                    "start_time": "2026-03-02T08:00:00Z",
                    "end_time": "2026-03-02T08:45:00Z",
                    "duration_minutes": 45.0,
                    "hr_avg": 155.0,
                    "hr_max": 178.0,
                    "distance_m": 7500.0,
                    "energy_kcal": 450.0,
                    "hc_record_id": "hc-session-001",
                },
            ],
        }
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sessions_synced"] == 1
        assert data["sessions_skipped"] == 0

    async def test_duplicate_sessions_are_skipped(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        payload = {
            "metrics": [],
            "exercise_sessions": [
                {
                    "exercise_type": "cycling",
                    "start_time": "2026-03-02T09:00:00Z",
                    "end_time": "2026-03-02T10:00:00Z",
                    "duration_minutes": 60.0,
                    "hc_record_id": "hc-session-002",
                },
            ],
        }
        # First sync
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.json()["sessions_synced"] == 1

        # Second sync with same hc_record_id
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.json()["sessions_synced"] == 0
        assert response.json()["sessions_skipped"] == 1

    async def test_mixed_sync(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        payload = {
            "metrics": [
                {
                    "metric_type": "hrv",
                    "value": 45.0,
                    "recorded_at": "2026-03-02T07:00:00Z",
                },
                {
                    "metric_type": "resting_heart_rate",
                    "value": 55.0,
                    "recorded_at": "2026-03-02T07:00:00Z",
                },
            ],
            "exercise_sessions": [
                {
                    "exercise_type": "yoga",
                    "start_time": "2026-03-02T06:00:00Z",
                    "end_time": "2026-03-02T06:30:00Z",
                    "duration_minutes": 30.0,
                },
            ],
        }
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics_synced"] == 2
        assert data["sessions_synced"] == 1

    async def test_empty_sync_succeeds(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        payload = {"metrics": [], "exercise_sessions": []}
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics_synced"] == 0
        assert data["sessions_synced"] == 0

    async def test_coach_cannot_sync(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        payload = {"metrics": [], "exercise_sessions": []}
        response = await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(coach_token),
        )
        assert response.status_code == 403

    async def test_unauthenticated_rejected(self, test_app: AsyncClient) -> None:
        payload = {"metrics": [], "exercise_sessions": []}
        response = await test_app.post("/api/v1/health-data/sync", json=payload)
        assert response.status_code in (401, 403)


class TestGetHealthDataStatus:
    """Test GET /api/v1/health-data/status."""

    async def test_athlete_gets_status(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        response = await test_app.get(
            "/api/v1/health-data/status",
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["last_sync_at"] is None

    async def test_status_updated_after_sync(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
        athlete_profile: AthleteProfile,
    ) -> None:
        # Sync some data first
        payload = {
            "metrics": [
                {
                    "metric_type": "heart_rate",
                    "value": 72.0,
                    "recorded_at": "2026-03-02T12:00:00Z",
                },
            ],
            "exercise_sessions": [],
        }
        await test_app.post(
            "/api/v1/health-data/sync",
            json=payload,
            headers=auth_header(athlete_token),
        )

        # Check status
        response = await test_app.get(
            "/api/v1/health-data/status",
            headers=auth_header(athlete_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["last_sync_at"] is not None

    async def test_coach_cannot_get_status(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        response = await test_app.get(
            "/api/v1/health-data/status",
            headers=auth_header(coach_token),
        )
        assert response.status_code == 403
