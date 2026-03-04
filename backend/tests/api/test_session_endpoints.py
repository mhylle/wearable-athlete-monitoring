"""Tests for training session endpoints."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_metrics import SessionMetrics
from app.models.training_session import TrainingSession
from app.models.user import User
from tests.api.conftest import auth_header


@pytest.mark.asyncio
class TestCreateSession:
    """Tests for POST /api/v1/sessions/."""

    async def test_coach_creates_session(
        self,
        test_app: AsyncClient,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        resp = await test_app.post(
            "/api/v1/sessions/",
            headers=auth_header(coach_token),
            json={
                "athlete_id": str(athlete_user.id),
                "session_type": "training",
                "start_time": now,
                "duration_minutes": 90.0,
                "notes": "Good session",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == "manual"
        assert data["session_type"] == "training"
        assert data["duration_minutes"] == 90.0
        assert data["notes"] == "Good session"
        assert data["athlete_id"] == str(athlete_user.id)

    async def test_athlete_cannot_create_session(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        resp = await test_app.post(
            "/api/v1/sessions/",
            headers=auth_header(athlete_token),
            json={
                "athlete_id": str(athlete_user.id),
                "session_type": "training",
                "start_time": now,
            },
        )
        assert resp.status_code == 403

    async def test_create_session_without_auth(
        self, test_app: AsyncClient
    ) -> None:
        resp = await test_app.post(
            "/api/v1/sessions/",
            json={
                "athlete_id": str(uuid.uuid4()),
                "session_type": "training",
                "start_time": datetime.now(UTC).isoformat(),
            },
        )
        assert resp.status_code == 401

    async def test_invalid_session_type_rejected(
        self,
        test_app: AsyncClient,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        resp = await test_app.post(
            "/api/v1/sessions/",
            headers=auth_header(coach_token),
            json={
                "athlete_id": str(athlete_user.id),
                "session_type": "invalid_type",
                "start_time": now,
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestListSessions:
    """Tests for GET /api/v1/sessions/athlete/{athlete_id}."""

    async def test_coach_lists_sessions(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        coach_user: User,
        athlete_user: User,
    ) -> None:
        # Create sessions directly in DB
        now = datetime.now(UTC)
        for i in range(3):
            session = TrainingSession(
                id=uuid.uuid4(),
                athlete_id=athlete_user.id,
                source="manual",
                session_type="training",
                start_time=now - timedelta(days=i),
                created_by=coach_user.id,
            )
            db_session.add(session)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/athlete/{athlete_user.id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert len(data["sessions"]) == 3

    async def test_athlete_lists_own_sessions(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        athlete_token: str,
        athlete_user: User,
        coach_user: User,
    ) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            source="manual",
            session_type="match",
            start_time=datetime.now(UTC),
            created_by=coach_user.id,
        )
        db_session.add(session)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/athlete/{athlete_user.id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    async def test_athlete_cannot_list_other_athlete_sessions(
        self,
        test_app: AsyncClient,
        athlete_token: str,
    ) -> None:
        other_id = uuid.uuid4()
        resp = await test_app.get(
            f"/api/v1/sessions/athlete/{other_id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403

    async def test_filter_by_session_type(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        coach_user: User,
        athlete_user: User,
    ) -> None:
        now = datetime.now(UTC)
        for st in ["training", "match", "training"]:
            session = TrainingSession(
                id=uuid.uuid4(),
                athlete_id=athlete_user.id,
                source="manual",
                session_type=st,
                start_time=now,
                created_by=coach_user.id,
            )
            db_session.add(session)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/athlete/{athlete_user.id}",
            headers=auth_header(coach_token),
            params={"session_type": "match"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["sessions"][0]["session_type"] == "match"


@pytest.mark.asyncio
class TestGetSessionDetail:
    """Tests for GET /api/v1/sessions/{session_id}."""

    async def test_get_session_with_metrics(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        coach_user: User,
        athlete_user: User,
    ) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            source="garmin",
            session_type="training",
            start_time=datetime.now(UTC),
            duration_minutes=60.0,
            created_by=coach_user.id,
        )
        db_session.add(session)
        await db_session.flush()

        metrics = SessionMetrics(
            id=uuid.uuid4(),
            session_id=session.id,
            hr_avg=145.0,
            hr_max=180.0,
            distance_m=8500.0,
        )
        db_session.add(metrics)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/{session.id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session"]["id"] == str(session.id)
        assert data["metrics"]["hr_avg"] == 145.0
        assert data["metrics"]["hr_max"] == 180.0
        assert data["metrics"]["distance_m"] == 8500.0

    async def test_get_session_without_metrics(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        coach_user: User,
        athlete_user: User,
    ) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            source="manual",
            session_type="recovery",
            start_time=datetime.now(UTC),
            created_by=coach_user.id,
        )
        db_session.add(session)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/{session.id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session"]["id"] == str(session.id)
        assert data["metrics"] is None

    async def test_session_not_found(
        self, test_app: AsyncClient, coach_token: str
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/sessions/{uuid.uuid4()}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 404

    async def test_athlete_can_view_own_session(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        athlete_token: str,
        athlete_user: User,
        coach_user: User,
    ) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            source="manual",
            session_type="gym",
            start_time=datetime.now(UTC),
            created_by=coach_user.id,
        )
        db_session.add(session)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/{session.id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 200

    async def test_athlete_cannot_view_other_session(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        athlete_token: str,
        coach_user: User,
    ) -> None:
        other_athlete_id = uuid.uuid4()
        # Create a user for the other athlete first
        other_athlete = User(
            id=other_athlete_id,
            email="other_athlete@test.com",
            hashed_password="hashed",
            role="athlete",
            full_name="Other Athlete",
            is_active=True,
        )
        db_session.add(other_athlete)
        await db_session.flush()

        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=other_athlete_id,
            source="manual",
            session_type="training",
            start_time=datetime.now(UTC),
            created_by=coach_user.id,
        )
        db_session.add(session)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/sessions/{session.id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403
