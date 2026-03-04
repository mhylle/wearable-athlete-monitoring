"""Create all tables.

Revision ID: 002_create_all_tables
Revises: 001_enable_timescaledb
Create Date: 2026-02-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_create_all_tables"
down_revision: Union[str, None] = "001_enable_timescaledb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all application tables."""
    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sport", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("ow_user_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- athlete_profiles ---
    op.create_table(
        "athlete_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("garmin_connected", sa.Boolean(), default=False),
        sa.Column("ow_connection_id", sa.String(255), nullable=True),
    )

    # --- training_sessions ---
    op.create_table(
        "training_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("athlete_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("session_type", sa.String(20), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("ow_event_id", sa.String(255), nullable=True, unique=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- session_metrics ---
    op.create_table(
        "session_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id", UUID(as_uuid=True), sa.ForeignKey("training_sessions.id"), nullable=False, unique=True
        ),
        sa.Column("hr_avg", sa.Float(), nullable=True),
        sa.Column("hr_max", sa.Float(), nullable=True),
        sa.Column("hr_min", sa.Float(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("energy_kcal", sa.Float(), nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("max_speed_ms", sa.Float(), nullable=True),
        sa.Column("elevation_gain_m", sa.Float(), nullable=True),
    )

    # --- wellness_entries ---
    op.create_table(
        "wellness_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("athlete_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("srpe", sa.Integer(), nullable=True),
        sa.Column("srpe_duration_min", sa.Float(), nullable=True),
        sa.Column("soreness", sa.Integer(), nullable=True),
        sa.Column("fatigue", sa.Integer(), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=True),
        sa.Column("sleep_quality", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("athlete_id", "date", name="uq_wellness_athlete_date"),
    )

    # --- metric_records (TimescaleDB hypertable) ---
    op.create_table(
        "metric_records",
        sa.Column("athlete_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("metric_type", sa.String(50), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("source", sa.String(20), nullable=True),
        sa.Column("ow_series_id", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("athlete_id", "metric_type", "recorded_at"),
    )

    # Convert metric_records to a TimescaleDB hypertable
    op.execute("SELECT create_hypertable('metric_records', 'recorded_at')")


def downgrade() -> None:
    """Drop all tables in reverse FK order."""
    op.drop_table("metric_records")
    op.drop_table("wellness_entries")
    op.drop_table("session_metrics")
    op.drop_table("training_sessions")
    op.drop_table("athlete_profiles")
    op.drop_table("users")
    op.drop_table("teams")
