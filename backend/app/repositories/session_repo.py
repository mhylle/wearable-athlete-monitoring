"""Session repository for database operations."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_metrics import SessionMetrics
from app.models.training_session import TrainingSession


class SessionRepository:
    """Database operations for TrainingSession and SessionMetrics models."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, data: dict) -> TrainingSession:
        """Create a new training session."""
        session = TrainingSession(**data)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def create_metrics(self, data: dict) -> SessionMetrics:
        """Create metrics for a session."""
        metrics = SessionMetrics(**data)
        self.db.add(metrics)
        await self.db.commit()
        await self.db.refresh(metrics)
        return metrics

    async def get_session_by_id(self, session_id: uuid.UUID) -> TrainingSession | None:
        """Get a training session by ID."""
        result = await self.db.execute(
            select(TrainingSession).where(TrainingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_metrics_by_session_id(
        self, session_id: uuid.UUID
    ) -> SessionMetrics | None:
        """Get metrics for a session."""
        result = await self.db.execute(
            select(SessionMetrics).where(SessionMetrics.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        athlete_id: uuid.UUID,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        session_type: str | None = None,
        source: str | None = None,
    ) -> list[TrainingSession]:
        """List training sessions for an athlete with optional filters."""
        stmt = select(TrainingSession).where(
            TrainingSession.athlete_id == athlete_id
        )

        if start is not None:
            stmt = stmt.where(TrainingSession.start_time >= start)
        if end is not None:
            stmt = stmt.where(TrainingSession.start_time <= end)
        if session_type is not None:
            stmt = stmt.where(TrainingSession.session_type == session_type)
        if source is not None:
            stmt = stmt.where(TrainingSession.source == source)

        stmt = stmt.order_by(TrainingSession.start_time.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
