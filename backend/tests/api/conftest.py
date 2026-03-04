"""Test fixtures for API endpoint tests.

Uses an in-memory SQLite database for integration testing.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.db import get_db
from app.main import create_app
from app.models.athlete_profile import AthleteProfile
from app.models.base import Base
from app.models.team import Team
from app.models.user import User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_app(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden DB dependency."""
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def team(db_session: AsyncSession) -> Team:
    """Create a test team."""
    t = Team(id=uuid.uuid4(), name="Test FC", sport="football")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def coach_user(db_session: AsyncSession, team: Team) -> User:
    """Create a coach user assigned to the test team."""
    user = User(
        id=uuid.uuid4(),
        email="coach@test.com",
        hashed_password=hash_password("testpass123"),
        role="coach",
        full_name="Head Coach",
        team_id=team.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def athlete_user(db_session: AsyncSession, team: Team) -> User:
    """Create an athlete user assigned to the test team."""
    user = User(
        id=uuid.uuid4(),
        email="athlete@test.com",
        hashed_password=hash_password("testpass123"),
        role="athlete",
        full_name="Star Player",
        team_id=team.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def athlete_profile(db_session: AsyncSession, athlete_user: User) -> AthleteProfile:
    """Create an athlete profile for the test athlete."""
    profile = AthleteProfile(
        id=uuid.uuid4(),
        user_id=athlete_user.id,
        position="Forward",
        height_cm=180.0,
        weight_kg=75.0,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest.fixture
def coach_token(coach_user: User) -> str:
    """Generate a valid access token for the coach."""
    return create_access_token(coach_user.id, coach_user.role, coach_user.team_id)


@pytest.fixture
def athlete_token(athlete_user: User) -> str:
    """Generate a valid access token for the athlete."""
    return create_access_token(athlete_user.id, athlete_user.role, athlete_user.team_id)


def auth_header(token: str) -> dict[str, str]:
    """Build an Authorization header."""
    return {"Authorization": f"Bearer {token}"}
