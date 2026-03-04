"""Celery tasks for anomaly detection."""

import asyncio
from datetime import date

from app.tasks.celery_app import celery_app


async def _run_daily_scan() -> dict:  # type: ignore[type-arg]
    """Run the daily anomaly scan for all active athletes."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.models.user import User
    from app.services.anomaly_service import persist_anomalies, scan_athlete_anomalies

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    today = date.today()
    total_anomalies = 0

    async with session_factory() as db:
        from sqlalchemy import select

        result = await db.execute(
            select(User.id).where(
                User.role == "athlete",
                User.is_active.is_(True),
            )
        )
        athlete_ids = [row[0] for row in result.all()]

        for athlete_id in athlete_ids:
            anomalies = await scan_athlete_anomalies(db, athlete_id, today)
            if anomalies:
                await persist_anomalies(db, anomalies)
                total_anomalies += len(anomalies)

    await engine.dispose()
    return {"athletes_scanned": len(athlete_ids), "anomalies_found": total_anomalies}


@celery_app.task(name="app.tasks.anomaly_tasks.run_daily_anomaly_scan_task")
def run_daily_anomaly_scan_task() -> dict:  # type: ignore[type-arg]
    """Celery task: scan all athletes for anomalies after daily sync."""
    return asyncio.run(_run_daily_scan())
