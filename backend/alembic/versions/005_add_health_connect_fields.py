"""Add health_connect_connected and last_health_connect_sync_at to athlete_profiles.

Revision ID: 005_add_health_connect_fields
Revises: 004_create_continuous_aggregates
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

revision = "005_add_health_connect_fields"
down_revision = "004_create_continuous_aggregates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "athlete_profiles",
        sa.Column("health_connect_connected", sa.Boolean, server_default="false", nullable=False),
    )
    op.add_column(
        "athlete_profiles",
        sa.Column("last_health_connect_sync_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("athlete_profiles", "last_health_connect_sync_at")
    op.drop_column("athlete_profiles", "health_connect_connected")
