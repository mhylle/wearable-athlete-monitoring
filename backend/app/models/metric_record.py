"""Metric record model (TimescaleDB hypertable)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MetricRecord(Base):
    """Time-series metric data point, stored as a TimescaleDB hypertable."""

    __tablename__ = "metric_records"

    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
        nullable=False,
    )
    metric_type: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False,
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ow_series_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
