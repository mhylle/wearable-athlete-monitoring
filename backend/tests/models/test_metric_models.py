"""Tests for the MetricRecord model."""

from datetime import UTC, datetime

from app.models.metric_record import MetricRecord


class TestMetricRecordModel:
    """Test MetricRecord model definition."""

    def test_table_name(self) -> None:
        assert MetricRecord.__tablename__ == "metric_records"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in MetricRecord.__table__.columns}
        expected = {"athlete_id", "metric_type", "recorded_at", "value", "source", "ow_series_id"}
        assert expected.issubset(column_names)

    def test_composite_primary_key(self) -> None:
        pk_col_names = {c.name for c in MetricRecord.__table__.primary_key.columns}
        assert pk_col_names == {"athlete_id", "metric_type", "recorded_at"}

    def test_athlete_id_foreign_key(self) -> None:
        col = MetricRecord.__table__.c.athlete_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_value_not_nullable(self) -> None:
        col = MetricRecord.__table__.c.value
        assert not col.nullable

    def test_recorded_at_not_nullable(self) -> None:
        col = MetricRecord.__table__.c.recorded_at
        assert not col.nullable

    def test_source_nullable(self) -> None:
        col = MetricRecord.__table__.c.source
        assert col.nullable

    def test_fixture_fields(self, sample_metric_record: MetricRecord) -> None:
        assert sample_metric_record.metric_type == "resting_hr"
        assert sample_metric_record.value == 52.0
        assert sample_metric_record.source == "garmin"

    def test_timestamp_ordering(self, user_id) -> None:  # type: ignore[no-untyped-def]
        """Verify that records can represent time-ordered data."""
        r1 = MetricRecord(
            athlete_id=user_id,
            metric_type="resting_hr",
            recorded_at=datetime(2026, 2, 27, 7, 0, 0, tzinfo=UTC),
            value=54.0,
        )

        r2 = MetricRecord(
            athlete_id=user_id,
            metric_type="resting_hr",
            recorded_at=datetime(2026, 2, 28, 7, 0, 0, tzinfo=UTC),
            value=52.0,
        )

        assert r1.recorded_at < r2.recorded_at
        assert r1.value > r2.value
