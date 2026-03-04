"""Create anomaly_records table.

Revision ID: 003_create_anomaly_records
Revises: 002_create_all_tables
Create Date: 2026-02-28
"""

import sqlalchemy as sa

from alembic import op

revision = "003_create_anomaly_records"
down_revision = "002_create_all_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anomaly_records",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "athlete_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("metric_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("expected_median", sa.Float, nullable=False),
        sa.Column("mad_score", sa.Float, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("anomaly_type", sa.String(20), nullable=False),
        sa.Column("explanation", sa.String(500), nullable=False),
        sa.Column("detected_at", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_anomaly_records_athlete_detected",
        "anomaly_records",
        ["athlete_id", "detected_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_anomaly_records_athlete_detected", table_name="anomaly_records")
    op.drop_table("anomaly_records")
