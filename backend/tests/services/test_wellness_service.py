"""Tests for the wellness service."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.user import User
from app.services import wellness_service


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def athlete(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="athlete@test.com",
        hashed_password="hashed",
        role="athlete",
        full_name="Test Athlete",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestSubmitWellness:
    async def test_creates_wellness_entry(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        data = {
            "date": today,
            "srpe": 7,
            "soreness": 4,
            "fatigue": 5,
            "mood": 3,
            "sleep_quality": 4,
        }
        entry = await wellness_service.submit_wellness(
            db_session, athlete.id, data
        )
        assert entry.athlete_id == athlete.id
        assert entry.srpe == 7
        assert entry.soreness == 4
        assert entry.date == today

    async def test_duplicate_date_returns_409(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        data = {"date": today, "srpe": 5}
        await wellness_service.submit_wellness(db_session, athlete.id, data)

        with pytest.raises(HTTPException) as exc_info:
            await wellness_service.submit_wellness(db_session, athlete.id, data)
        assert exc_info.value.status_code == 409


class TestUpdateWellness:
    async def test_updates_entry(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        entry = await wellness_service.submit_wellness(
            db_session, athlete.id, {"date": today, "srpe": 5}
        )
        updated = await wellness_service.update_wellness(
            db_session, entry.id, athlete.id, {"srpe": 8}
        )
        assert updated.srpe == 8

    async def test_update_nonexistent_returns_404(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await wellness_service.update_wellness(
                db_session, uuid.uuid4(), athlete.id, {"srpe": 5}
            )
        assert exc_info.value.status_code == 404

    async def test_update_other_athletes_entry_returns_403(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        entry = await wellness_service.submit_wellness(
            db_session, athlete.id, {"date": today, "srpe": 5}
        )
        other_athlete_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await wellness_service.update_wellness(
                db_session, entry.id, other_athlete_id, {"srpe": 8}
            )
        assert exc_info.value.status_code == 403


class TestGetWellnessHistory:
    async def test_returns_entries(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        for i in range(3):
            await wellness_service.submit_wellness(
                db_session,
                athlete.id,
                {"date": today - timedelta(days=i), "srpe": 5 + i},
            )
        entries = await wellness_service.get_wellness_history(
            db_session, athlete.id
        )
        assert len(entries) == 3

    async def test_filters_by_date_range(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        for i in range(5):
            await wellness_service.submit_wellness(
                db_session,
                athlete.id,
                {"date": today - timedelta(days=i), "srpe": 5},
            )
        entries = await wellness_service.get_wellness_history(
            db_session,
            athlete.id,
            start=today - timedelta(days=2),
            end=today,
        )
        assert len(entries) == 3


class TestGetLatestWellness:
    async def test_returns_latest(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        today = date.today()
        await wellness_service.submit_wellness(
            db_session,
            athlete.id,
            {"date": today - timedelta(days=1), "srpe": 5},
        )
        await wellness_service.submit_wellness(
            db_session,
            athlete.id,
            {"date": today, "srpe": 8},
        )
        entry = await wellness_service.get_latest_wellness(
            db_session, athlete.id
        )
        assert entry is not None
        assert entry.srpe == 8
        assert entry.date == today

    async def test_returns_none_when_no_entries(
        self, db_session: AsyncSession, athlete: User
    ) -> None:
        entry = await wellness_service.get_latest_wellness(
            db_session, athlete.id
        )
        assert entry is None
