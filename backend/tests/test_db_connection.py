"""Tests for database connection and TimescaleDB extension."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_connection_succeeds(db_session: AsyncSession) -> None:
    """Database connection should succeed."""
    result = await db_session.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1


@pytest.mark.asyncio
async def test_timescaledb_extension_available(db_session: AsyncSession) -> None:
    """TimescaleDB extension should be loaded in the database."""
    result = await db_session.execute(
        text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
    )
    row = result.fetchone()
    assert row is not None
    assert row[0] == "timescaledb"
