"""Wellness repository for database operations."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wellness_entry import WellnessEntry


class WellnessRepository:
    """Database operations for WellnessEntry model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_entry(self, data: dict) -> WellnessEntry:
        """Create a new wellness entry."""
        entry = WellnessEntry(**data)
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_entry_by_id(self, entry_id: uuid.UUID) -> WellnessEntry | None:
        """Get a wellness entry by ID."""
        result = await self.db.execute(
            select(WellnessEntry).where(WellnessEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_entry_by_athlete_and_date(
        self, athlete_id: uuid.UUID, entry_date: date
    ) -> WellnessEntry | None:
        """Get a wellness entry for a specific athlete and date."""
        result = await self.db.execute(
            select(WellnessEntry).where(
                WellnessEntry.athlete_id == athlete_id,
                WellnessEntry.date == entry_date,
            )
        )
        return result.scalar_one_or_none()

    async def update_entry(
        self, entry: WellnessEntry, data: dict
    ) -> WellnessEntry:
        """Update a wellness entry."""
        for key, value in data.items():
            setattr(entry, key, value)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_latest_entry(self, athlete_id: uuid.UUID) -> WellnessEntry | None:
        """Get the most recent wellness entry for an athlete."""
        result = await self.db.execute(
            select(WellnessEntry)
            .where(WellnessEntry.athlete_id == athlete_id)
            .order_by(WellnessEntry.date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_entries(
        self,
        athlete_id: uuid.UUID,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> list[WellnessEntry]:
        """List wellness entries for an athlete with optional date range."""
        stmt = select(WellnessEntry).where(
            WellnessEntry.athlete_id == athlete_id
        )

        if start is not None:
            stmt = stmt.where(WellnessEntry.date >= start)
        if end is not None:
            stmt = stmt.where(WellnessEntry.date <= end)

        stmt = stmt.order_by(WellnessEntry.date.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
