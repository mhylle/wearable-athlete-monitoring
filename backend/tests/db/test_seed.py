"""Tests for the seed script."""

import uuid
from datetime import date

from app.db.seed import (
    FIRST_NAMES,
    LAST_NAMES,
    NUM_ATHLETES,
    NUM_DAYS,
    POSITIONS,
    TEAM_NAME,
    _build_periodized_load,
    _generate_athlete_metrics,
    _generate_training_sessions,
    _generate_wellness_entries,
)


class TestSeedConfiguration:
    """Test seed script constants and config."""

    def test_has_enough_names(self) -> None:
        assert len(FIRST_NAMES) >= NUM_ATHLETES
        assert len(LAST_NAMES) >= NUM_ATHLETES
        assert len(POSITIONS) >= NUM_ATHLETES

    def test_team_name(self) -> None:
        assert TEAM_NAME == "FC Demo"

    def test_num_athletes(self) -> None:
        assert NUM_ATHLETES == 25

    def test_num_days(self) -> None:
        assert NUM_DAYS == 90


class TestPeriodizedLoad:
    """Test the periodization function."""

    def test_build_phase_higher_than_recovery(self) -> None:
        build_loads = [_build_periodized_load(d, 500.0) for d in range(21)]
        recovery_loads = [_build_periodized_load(d, 500.0) for d in range(21, 28)]
        # Build phase average should be higher than recovery average
        assert sum(build_loads) / len(build_loads) > sum(recovery_loads) / len(recovery_loads)

    def test_positive_load(self) -> None:
        for d in range(28):
            load = _build_periodized_load(d, 500.0)
            assert load > 0


class TestGenerateAthleteMetrics:
    """Test metric record generation."""

    def test_generates_five_metrics_per_day(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        records = _generate_athlete_metrics(aid, start, set(), profile_seed=42)
        # 5 metric types x NUM_DAYS
        assert len(records) == 5 * NUM_DAYS

    def test_all_metric_types_present(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        records = _generate_athlete_metrics(aid, start, set(), profile_seed=42)
        types = {r.metric_type for r in records}
        assert types == {"resting_hr", "hrv_rmssd", "sleep_duration", "training_load", "body_battery"}

    def test_values_are_reasonable(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        records = _generate_athlete_metrics(aid, start, set(), profile_seed=42)
        for r in records:
            if r.metric_type == "resting_hr":
                assert 30 < r.value < 120
            elif r.metric_type == "hrv_rmssd":
                assert r.value >= 10
            elif r.metric_type == "sleep_duration":
                assert r.value >= 120
            elif r.metric_type == "body_battery":
                assert 5 <= r.value <= 100

    def test_anomaly_days_create_outliers(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        # Run with and without anomalies, seeded the same
        normal = _generate_athlete_metrics(aid, start, set(), profile_seed=100)
        anomaly = _generate_athlete_metrics(aid, start, {25, 50}, profile_seed=100)
        # At least some values should differ on anomaly days
        normal_vals = {(r.recorded_at, r.metric_type): r.value for r in normal}
        anomaly_vals = {(r.recorded_at, r.metric_type): r.value for r in anomaly}
        diffs = sum(
            1 for k in normal_vals if k in anomaly_vals and normal_vals[k] != anomaly_vals[k]
        )
        assert diffs > 0


class TestGenerateTrainingSessions:
    """Test training session generation."""

    def test_generates_sessions(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        sessions, metrics = _generate_training_sessions(aid, start)
        assert len(sessions) > 0
        assert len(sessions) == len(metrics)

    def test_has_matches(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        sessions, _ = _generate_training_sessions(aid, start)
        types = {s.session_type for s in sessions}
        assert "match" in types
        assert "training" in types


class TestGenerateWellnessEntries:
    """Test wellness entry generation."""

    def test_generates_entries(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        entries = _generate_wellness_entries(aid, start)
        # Most days should have entries (90% expected)
        assert len(entries) > NUM_DAYS * 0.7

    def test_values_in_range(self) -> None:
        aid = uuid.uuid4()
        start = date(2026, 1, 1)
        entries = _generate_wellness_entries(aid, start)
        for e in entries:
            assert 1 <= e.fatigue <= 5
            assert 1 <= e.soreness <= 4
            assert 1 <= e.mood <= 5
            assert 1 <= e.sleep_quality <= 5


class TestSeedImport:
    """Test that the seed function can be imported."""

    def test_seed_database_importable(self) -> None:
        from app.db.seed import seed_database
        assert callable(seed_database)
