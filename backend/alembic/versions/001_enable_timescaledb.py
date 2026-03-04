"""Enable TimescaleDB extension.

Revision ID: 001_enable_timescaledb
Revises: None
Create Date: 2026-02-28
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_enable_timescaledb"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable the TimescaleDB extension."""
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")


def downgrade() -> None:
    """Remove TimescaleDB extension."""
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
