"""Tests for wellness endpoints."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wellness_entry import WellnessEntry
from tests.api.conftest import auth_header


@pytest.mark.asyncio
class TestSubmitWellness:
    """Tests for POST /api/v1/wellness/."""

    async def test_athlete_submits_wellness(
        self,
        test_app: AsyncClient,
        athlete_token: str,
        athlete_user: User,
    ) -> None:
        today = date.today().isoformat()
        resp = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json={
                "date": today,
                "srpe": 7,
                "soreness": 4,
                "fatigue": 5,
                "mood": 3,
                "sleep_quality": 4,
                "notes": "Feeling good",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["srpe"] == 7
        assert data["soreness"] == 4
        assert data["fatigue"] == 5
        assert data["mood"] == 3
        assert data["sleep_quality"] == 4
        assert data["notes"] == "Feeling good"
        assert data["athlete_id"] == str(athlete_user.id)

    async def test_duplicate_date_returns_409(
        self,
        test_app: AsyncClient,
        athlete_token: str,
    ) -> None:
        today = date.today().isoformat()
        payload = {"date": today, "srpe": 5}
        resp1 = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json=payload,
        )
        assert resp1.status_code == 201

        resp2 = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json=payload,
        )
        assert resp2.status_code == 409

    async def test_coach_cannot_submit_wellness(
        self,
        test_app: AsyncClient,
        coach_token: str,
    ) -> None:
        resp = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(coach_token),
            json={"date": date.today().isoformat(), "srpe": 5},
        )
        assert resp.status_code == 403

    async def test_submit_without_auth(self, test_app: AsyncClient) -> None:
        resp = await test_app.post(
            "/api/v1/wellness/",
            json={"date": date.today().isoformat(), "srpe": 5},
        )
        assert resp.status_code == 401

    async def test_srpe_validation_too_high(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json={"date": date.today().isoformat(), "srpe": 11},
        )
        assert resp.status_code == 422

    async def test_srpe_validation_too_low(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json={"date": date.today().isoformat(), "srpe": 0},
        )
        assert resp.status_code == 422

    async def test_mood_validation_too_high(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json={"date": date.today().isoformat(), "mood": 6},
        )
        assert resp.status_code == 422

    async def test_sleep_quality_validation_too_high(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.post(
            "/api/v1/wellness/",
            headers=auth_header(athlete_token),
            json={"date": date.today().isoformat(), "sleep_quality": 6},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestUpdateWellness:
    """Tests for PUT /api/v1/wellness/{entry_id}."""

    async def test_athlete_updates_own_entry(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        athlete_token: str,
        athlete_user: User,
    ) -> None:
        entry = WellnessEntry(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            date=date.today(),
            srpe=5,
            soreness=3,
        )
        db_session.add(entry)
        await db_session.commit()

        resp = await test_app.put(
            f"/api/v1/wellness/{entry.id}",
            headers=auth_header(athlete_token),
            json={"srpe": 8, "soreness": 6},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["srpe"] == 8
        assert data["soreness"] == 6

    async def test_update_nonexistent_entry(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.put(
            f"/api/v1/wellness/{uuid.uuid4()}",
            headers=auth_header(athlete_token),
            json={"srpe": 5},
        )
        assert resp.status_code == 404

    async def test_coach_cannot_update_wellness(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        entry = WellnessEntry(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            date=date.today(),
            srpe=5,
        )
        db_session.add(entry)
        await db_session.commit()

        resp = await test_app.put(
            f"/api/v1/wellness/{entry.id}",
            headers=auth_header(coach_token),
            json={"srpe": 8},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestGetWellnessHistory:
    """Tests for GET /api/v1/wellness/athlete/{athlete_id}."""

    async def test_coach_gets_athlete_history(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        today = date.today()
        for i in range(3):
            entry = WellnessEntry(
                id=uuid.uuid4(),
                athlete_id=athlete_user.id,
                date=today - timedelta(days=i),
                srpe=5 + i,
            )
            db_session.add(entry)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{athlete_user.id}",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert len(data["entries"]) == 3

    async def test_athlete_gets_own_history(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        athlete_token: str,
        athlete_user: User,
    ) -> None:
        entry = WellnessEntry(
            id=uuid.uuid4(),
            athlete_id=athlete_user.id,
            date=date.today(),
            srpe=7,
        )
        db_session.add(entry)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{athlete_user.id}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    async def test_athlete_cannot_view_other_history(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{uuid.uuid4()}",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403

    async def test_filter_by_date_range(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        today = date.today()
        for i in range(5):
            entry = WellnessEntry(
                id=uuid.uuid4(),
                athlete_id=athlete_user.id,
                date=today - timedelta(days=i),
                srpe=5,
            )
            db_session.add(entry)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{athlete_user.id}",
            headers=auth_header(coach_token),
            params={
                "start": (today - timedelta(days=2)).isoformat(),
                "end": today.isoformat(),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3


@pytest.mark.asyncio
class TestGetLatestWellness:
    """Tests for GET /api/v1/wellness/athlete/{athlete_id}/latest."""

    async def test_returns_latest_entry(
        self,
        test_app: AsyncClient,
        db_session: AsyncSession,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        today = date.today()
        for i in range(3):
            entry = WellnessEntry(
                id=uuid.uuid4(),
                athlete_id=athlete_user.id,
                date=today - timedelta(days=i),
                srpe=5 + i,
            )
            db_session.add(entry)
        await db_session.commit()

        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{athlete_user.id}/latest",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["date"] == today.isoformat()
        assert data["srpe"] == 5

    async def test_returns_null_when_no_entries(
        self,
        test_app: AsyncClient,
        coach_token: str,
        athlete_user: User,
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{athlete_user.id}/latest",
            headers=auth_header(coach_token),
        )
        assert resp.status_code == 200
        assert resp.json() is None

    async def test_athlete_cannot_view_other_latest(
        self, test_app: AsyncClient, athlete_token: str
    ) -> None:
        resp = await test_app.get(
            f"/api/v1/wellness/athlete/{uuid.uuid4()}/latest",
            headers=auth_header(athlete_token),
        )
        assert resp.status_code == 403
