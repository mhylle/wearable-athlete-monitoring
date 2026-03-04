"""Test fixtures for auth endpoint tests.

Uses an in-memory SQLite database for integration testing without
requiring a real PostgreSQL instance.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.password import hash_password
from app.db import get_db
from app.main import create_app
from app.models.base import Base
from app.models.user import User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # SQLite needs special handling for UUID columns
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
async def registered_user(db_session: AsyncSession) -> User:
    """Create a pre-registered user in the test DB."""
    user = User(
        id=uuid.uuid4(),
        email="coach@test.com",
        hashed_password=hash_password("testpass123"),
        role="coach",
        full_name="Test Coach",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def registered_athlete(db_session: AsyncSession) -> User:
    """Create a pre-registered athlete in the test DB."""
    user = User(
        id=uuid.uuid4(),
        email="athlete@test.com",
        hashed_password=hash_password("testpass123"),
        role="athlete",
        full_name="Test Athlete",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
