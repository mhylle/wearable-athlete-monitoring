"""Training session service layer."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training_session import TrainingSession
from app.models.wellness_entry import WellnessEntry
from app.repositories.session_repo import SessionRepository


async def create_manual_session(
    db: AsyncSession,
    data: dict,
    coach_id: uuid.UUID,
) -> TrainingSession:
    """Create a manual training session."""
    repo = SessionRepository(db)
    session_data = {
        **data,
        "source": "manual",
        "created_by": coach_id,
    }
    return await repo.create_session(session_data)


async def list_sessions(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    session_type: str | None = None,
    source: str | None = None,
) -> list[TrainingSession]:
    """List training sessions for an athlete with optional filters."""
    repo = SessionRepository(db)
    return await repo.list_sessions(
        athlete_id,
        start=start,
        end=end,
        session_type=session_type,
        source=source,
    )


async def get_session_detail(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> dict | None:
    """Get a training session with its metrics."""
    repo = SessionRepository(db)
    session = await repo.get_session_by_id(session_id)
    if session is None:
        return None
    metrics = await repo.get_metrics_by_session_id(session_id)
    return {"session": session, "metrics": metrics}


def compute_session_load(
    session: TrainingSession,
    wellness: WellnessEntry | None,
) -> float | None:
    """Compute session load as sRPE x duration_minutes.

    Returns None if wellness entry or required fields are missing.
    """
    if wellness is None or wellness.srpe is None:
        return None
    if session.duration_minutes is None:
        return None
    return float(wellness.srpe * session.duration_minutes)
