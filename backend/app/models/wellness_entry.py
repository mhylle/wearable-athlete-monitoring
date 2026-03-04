"""Wellness entry model."""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class WellnessEntry(UUIDMixin, TimestampMixin, Base):
    """Daily wellness self-report from an athlete."""

    __tablename__ = "wellness_entries"
    __table_args__ = (
        UniqueConstraint("athlete_id", "date", name="uq_wellness_athlete_date"),
    )

    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    srpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    srpe_duration_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    soreness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fatigue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
