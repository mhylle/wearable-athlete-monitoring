"""Create continuous aggregates and indexes for metric_records.

Revision ID: 004_create_continuous_aggregates
Revises: 003_create_anomaly_records
Create Date: 2026-02-28
"""

from alembic import op
from sqlalchemy import text

revision = "004_create_continuous_aggregates"
down_revision = "003_create_anomaly_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for common query patterns (runs fine inside a transaction)
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_metric_records_athlete_type_time "
            "ON metric_records (athlete_id, metric_type, recorded_at)"
        )
    )

    # TimescaleDB continuous aggregates cannot be created inside a transaction block.
    # Explicitly commit the current transaction, run the DDL, then re-enter a transaction.
    conn = op.get_bind()
    conn.execute(text("COMMIT"))

    # Daily metric rollup continuous aggregate
    conn.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metric_agg
        WITH (timescaledb.continuous) AS
        SELECT athlete_id,
               metric_type,
               time_bucket('1 day', recorded_at) AS bucket,
               AVG(value) AS avg_value,
               MIN(value) AS min_value,
               MAX(value) AS max_value,
               COUNT(*) AS sample_count
        FROM metric_records
        GROUP BY athlete_id, metric_type, bucket
        WITH NO DATA;
    """))

    # Weekly training load rollup continuous aggregate
    conn.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS weekly_load_agg
        WITH (timescaledb.continuous) AS
        SELECT athlete_id,
               time_bucket('1 week', recorded_at) AS bucket,
               SUM(value) AS total_load,
               AVG(value) AS avg_daily_load,
               COUNT(*) AS session_count
        FROM metric_records
        WHERE metric_type = 'training_load'
        GROUP BY athlete_id, bucket
        WITH NO DATA;
    """))

    # Refresh policies - refresh data older than 1 hour, look back 30 days
    conn.execute(text("""
        SELECT add_continuous_aggregate_policy('daily_metric_agg',
            start_offset => INTERVAL '30 days',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => true);
    """))
    conn.execute(text("""
        SELECT add_continuous_aggregate_policy('weekly_load_agg',
            start_offset => INTERVAL '30 days',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => true);
    """))

    # Re-enter a transaction for Alembic's version bookkeeping
    conn.execute(text("BEGIN"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("COMMIT"))
    conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS weekly_load_agg CASCADE;"))
    conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS daily_metric_agg CASCADE;"))
    conn.execute(text("BEGIN"))
    op.execute(text("DROP INDEX IF EXISTS ix_metric_records_athlete_type_time;"))
