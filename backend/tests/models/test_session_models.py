"""Tests for TrainingSession and SessionMetrics models."""

from app.models.session_metrics import SessionMetrics
from app.models.training_session import TrainingSession


class TestTrainingSessionModel:
    """Test TrainingSession model definition."""

    def test_table_name(self) -> None:
        assert TrainingSession.__tablename__ == "training_sessions"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in TrainingSession.__table__.columns}
        expected = {
            "id", "athlete_id", "source", "session_type",
            "start_time", "end_time", "duration_minutes",
            "ow_event_id", "notes", "created_by", "created_at",
        }
        assert expected.issubset(column_names)

    def test_athlete_id_foreign_key(self) -> None:
        col = TrainingSession.__table__.c.athlete_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_athlete_id_indexed(self) -> None:
        col = TrainingSession.__table__.c.athlete_id
        assert col.index

    def test_created_by_foreign_key(self) -> None:
        col = TrainingSession.__table__.c.created_by
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_ow_event_id_unique(self) -> None:
        col = TrainingSession.__table__.c.ow_event_id
        assert col.unique

    def test_start_time_not_nullable(self) -> None:
        col = TrainingSession.__table__.c.start_time
        assert not col.nullable

    def test_source_not_nullable(self) -> None:
        col = TrainingSession.__table__.c.source
        assert not col.nullable

    def test_fixture_garmin_source(self, sample_training_session: TrainingSession) -> None:
        assert sample_training_session.source == "garmin"
        assert sample_training_session.session_type == "training"
        assert sample_training_session.duration_minutes == 90.0

    def test_manual_source_session(self, user_id) -> None:  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime

        session = TrainingSession(
            athlete_id=user_id,
            source="manual",
            session_type="match",
            start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
        )
        assert session.source == "manual"
        assert session.session_type == "match"


class TestSessionMetricsModel:
    """Test SessionMetrics model definition."""

    def test_table_name(self) -> None:
        assert SessionMetrics.__tablename__ == "session_metrics"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in SessionMetrics.__table__.columns}
        expected = {
            "id", "session_id", "hr_avg", "hr_max", "hr_min",
            "distance_m", "energy_kcal", "steps", "max_speed_ms",
            "elevation_gain_m",
        }
        assert expected.issubset(column_names)

    def test_session_id_unique(self) -> None:
        col = SessionMetrics.__table__.c.session_id
        assert col.unique

    def test_session_id_foreign_key(self) -> None:
        col = SessionMetrics.__table__.c.session_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "training_sessions.id" in fk_targets

    def test_fixture_fields(self, sample_session_metrics: SessionMetrics) -> None:
        assert sample_session_metrics.hr_avg == 145.0
        assert sample_session_metrics.hr_max == 185.0
        assert sample_session_metrics.steps == 12000
