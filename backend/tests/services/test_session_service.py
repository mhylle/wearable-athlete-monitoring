"""Tests for the session service."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.training_session import TrainingSession
from app.models.user import User
from app.models.wellness_entry import WellnessEntry
from app.services import session_service


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
async def coach(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="coach@test.com",
        hashed_password="hashed",
        role="coach",
        full_name="Test Coach",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


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


class TestCreateManualSession:
    async def test_creates_session_with_manual_source(
        self, db_session: AsyncSession, coach: User, athlete: User
    ) -> None:
        now = datetime.now(UTC)
        data = {
            "athlete_id": athlete.id,
            "session_type": "training",
            "start_time": now,
            "duration_minutes": 90.0,
        }
        result = await session_service.create_manual_session(
            db_session, data, coach_id=coach.id
        )
        assert result.source == "manual"
        assert result.created_by == coach.id
        assert result.athlete_id == athlete.id
        assert result.session_type == "training"
        assert result.duration_minutes == 90.0

    async def test_creates_session_with_notes(
        self, db_session: AsyncSession, coach: User, athlete: User
    ) -> None:
        now = datetime.now(UTC)
        data = {
            "athlete_id": athlete.id,
            "session_type": "match",
            "start_time": now,
            "notes": "First team match",
        }
        result = await session_service.create_manual_session(
            db_session, data, coach_id=coach.id
        )
        assert result.notes == "First team match"
        assert result.session_type == "match"


class TestListSessions:
    async def test_lists_sessions_for_athlete(
        self, db_session: AsyncSession, coach: User, athlete: User
    ) -> None:
        now = datetime.now(UTC)
        for i in range(3):
            await session_service.create_manual_session(
                db_session,
                {
                    "athlete_id": athlete.id,
                    "session_type": "training",
                    "start_time": now - timedelta(days=i),
                },
                coach_id=coach.id,
            )

        sessions = await session_service.list_sessions(db_session, athlete.id)
        assert len(sessions) == 3

    async def test_filters_by_session_type(
        self, db_session: AsyncSession, coach: User, athlete: User
    ) -> None:
        now = datetime.now(UTC)
        await session_service.create_manual_session(
            db_session,
            {
                "athlete_id": athlete.id,
                "session_type": "training",
                "start_time": now,
            },
            coach_id=coach.id,
        )
        await session_service.create_manual_session(
            db_session,
            {
                "athlete_id": athlete.id,
                "session_type": "match",
                "start_time": now - timedelta(hours=2),
            },
            coach_id=coach.id,
        )

        sessions = await session_service.list_sessions(
            db_session, athlete.id, session_type="match"
        )
        assert len(sessions) == 1
        assert sessions[0].session_type == "match"

    async def test_filters_by_date_range(
        self, db_session: AsyncSession, coach: User, athlete: User
    ) -> None:
        now = datetime.now(UTC)
        await session_service.create_manual_session(
            db_session,
            {
                "athlete_id": athlete.id,
                "session_type": "training",
                "start_time": now,
            },
            coach_id=coach.id,
        )
        await session_service.create_manual_session(
            db_session,
            {
                "athlete_id": athlete.id,
                "session_type": "training",
                "start_time": now - timedelta(days=10),
            },
            coach_id=coach.id,
        )

        sessions = await session_service.list_sessions(
            db_session,
            athlete.id,
            start=now - timedelta(days=1),
        )
        assert len(sessions) == 1


class TestGetSessionDetail:
    async def test_returns_session_with_no_metrics(
        self, db_session: AsyncSession, coach: User, athlete: User
    ) -> None:
        now = datetime.now(UTC)
        session = await session_service.create_manual_session(
            db_session,
            {
                "athlete_id": athlete.id,
                "session_type": "training",
                "start_time": now,
            },
            coach_id=coach.id,
        )

        result = await session_service.get_session_detail(db_session, session.id)
        assert result is not None
        assert result["session"].id == session.id
        assert result["metrics"] is None

    async def test_returns_none_for_unknown_session(
        self, db_session: AsyncSession
    ) -> None:
        result = await session_service.get_session_detail(
            db_session, uuid.uuid4()
        )
        assert result is None


class TestComputeSessionLoad:
    def test_computes_load(self) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=uuid.uuid4(),
            source="manual",
            session_type="training",
            start_time=datetime.now(UTC),
            duration_minutes=90.0,
        )
        wellness = WellnessEntry(
            id=uuid.uuid4(),
            athlete_id=session.athlete_id,
            date=datetime.now(UTC).date(),
            srpe=7,
        )
        load = session_service.compute_session_load(session, wellness)
        assert load == 630.0  # 7 * 90

    def test_returns_none_without_wellness(self) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=uuid.uuid4(),
            source="manual",
            session_type="training",
            start_time=datetime.now(UTC),
            duration_minutes=90.0,
        )
        load = session_service.compute_session_load(session, None)
        assert load is None

    def test_returns_none_without_duration(self) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=uuid.uuid4(),
            source="manual",
            session_type="training",
            start_time=datetime.now(UTC),
            duration_minutes=None,
        )
        wellness = WellnessEntry(
            id=uuid.uuid4(),
            athlete_id=session.athlete_id,
            date=datetime.now(UTC).date(),
            srpe=7,
        )
        load = session_service.compute_session_load(session, wellness)
        assert load is None

    def test_returns_none_without_srpe(self) -> None:
        session = TrainingSession(
            id=uuid.uuid4(),
            athlete_id=uuid.uuid4(),
            source="manual",
            session_type="training",
            start_time=datetime.now(UTC),
            duration_minutes=90.0,
        )
        wellness = WellnessEntry(
            id=uuid.uuid4(),
            athlete_id=session.athlete_id,
            date=datetime.now(UTC).date(),
            srpe=None,
        )
        load = session_service.compute_session_load(session, wellness)
        assert load is None
