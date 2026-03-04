"""Celery tasks for synchronizing data from Open Wearables."""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta

import redis

from app.config import settings
from app.tasks.celery_app import celery_app

# Redis client for sync status tracking
_redis: redis.Redis | None = None  # type: ignore[type-arg]


def _get_redis() -> redis.Redis:  # type: ignore[type-arg]
    """Get or create a Redis client for sync status."""
    global _redis  # noqa: PLW0603
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _set_sync_status(athlete_id: str, status: str, error: str | None = None) -> None:
    """Store sync status in Redis."""
    r = _get_redis()
    data = {
        "athlete_id": athlete_id,
        "status": status,
        "last_sync_at": datetime.now(UTC).isoformat(),
        "error": error,
    }
    r.set(f"sync:status:{athlete_id}", json.dumps(data), ex=86400)  # 24h TTL


def get_sync_status(athlete_id: str) -> dict | None:  # type: ignore[type-arg]
    """Retrieve sync status from Redis."""
    r = _get_redis()
    raw = r.get(f"sync:status:{athlete_id}")
    if raw is None:
        return None
    return json.loads(raw)  # type: ignore[no-any-return]


def get_all_sync_statuses() -> list[dict]:  # type: ignore[type-arg]
    """Retrieve all sync statuses from Redis."""
    r = _get_redis()
    keys = r.keys("sync:status:*")
    statuses = []
    for key in keys:
        raw = r.get(key)
        if raw:
            statuses.append(json.loads(raw))
    return statuses


async def _run_athlete_sync(athlete_id_str: str, start: datetime, end: datetime) -> dict:  # type: ignore[type-arg]
    """Run the actual sync operations asynchronously."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.models.user import User
    from app.services.ow_client import OWClient
    from app.services.ow_sync_service import (
        sync_athlete_sleep,
        sync_athlete_timeseries,
        sync_athlete_workouts,
    )

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        from sqlalchemy import select

        result = await db.execute(
            select(User).where(User.id == uuid.UUID(athlete_id_str))
        )
        athlete = result.scalar_one_or_none()
        if athlete is None:
            return {"error": "Athlete not found"}

        client = OWClient()
        try:
            ts_result = await sync_athlete_timeseries(athlete, start, end, client, db)
            wo_result = await sync_athlete_workouts(athlete, start, end, client, db)
            sl_result = await sync_athlete_sleep(athlete, start, end, client, db)
        finally:
            await client.close()

    await engine.dispose()

    return {
        "records_synced": ts_result.records_synced + wo_result.records_synced + sl_result.records_synced,
        "records_skipped": ts_result.records_skipped + wo_result.records_skipped + sl_result.records_skipped,
        "errors": ts_result.errors + wo_result.errors + sl_result.errors,
    }


@celery_app.task(
    bind=True,
    name="app.tasks.sync_tasks.sync_athlete_data_task",
    max_retries=3,
    default_retry_delay=60,
)
def sync_athlete_data_task(self, athlete_id: str, start_date: str | None = None, end_date: str | None = None) -> dict:  # type: ignore[type-arg]
    """Sync timeseries, workouts, and sleep for one athlete.

    Args:
        athlete_id: UUID string of the athlete
        start_date: ISO format start date (defaults to 24h ago)
        end_date: ISO format end date (defaults to now)
    """
    _set_sync_status(athlete_id, "in_progress")

    end = datetime.fromisoformat(end_date) if end_date else datetime.now(UTC)
    start = datetime.fromisoformat(start_date) if start_date else end - timedelta(hours=24)

    try:
        result = asyncio.run(_run_athlete_sync(athlete_id, start, end))
    except Exception as exc:
        _set_sync_status(athlete_id, "error", str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries)) from exc

    if result.get("errors"):
        _set_sync_status(athlete_id, "partial", "; ".join(result["errors"]))
    else:
        _set_sync_status(athlete_id, "completed")

    return result


async def _get_connected_athlete_ids() -> list[str]:
    """Fetch all Garmin-connected athlete IDs from the database."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.models.user import User

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        result = await db.execute(
            select(User.id).where(
                User.role == "athlete",
                User.ow_user_id.isnot(None),
                User.is_active.is_(True),
            )
        )
        ids = [str(row[0]) for row in result.all()]

    await engine.dispose()
    return ids


@celery_app.task(name="app.tasks.sync_tasks.sync_all_athletes_task")
def sync_all_athletes_task() -> dict:  # type: ignore[type-arg]
    """Discover all Garmin-connected athletes and dispatch individual sync tasks."""
    athlete_ids = asyncio.run(_get_connected_athlete_ids())

    for athlete_id in athlete_ids:
        sync_athlete_data_task.delay(athlete_id)

    return {"dispatched": len(athlete_ids), "athlete_ids": athlete_ids}
