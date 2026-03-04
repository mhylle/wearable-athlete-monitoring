"""Tests for continuous aggregate migration and repo functions."""

import importlib.util
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.repositories.metric_agg_repo import (
    AthleteMetric,
    DailyMetric,
    WeeklyLoad,
)

_MIGRATION_PATH = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "004_create_continuous_aggregates.py"


def _load_migration() -> ModuleType:
    """Load migration module from file path."""
    spec = importlib.util.spec_from_file_location(
        "migration_004", _MIGRATION_PATH,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestMigrationStructure:
    """Verify migration file has correct structure."""

    def test_migration_file_exists(self) -> None:
        mod = _load_migration()
        assert hasattr(mod, "upgrade")
        assert hasattr(mod, "downgrade")

    def test_migration_revision_chain(self) -> None:
        mod = _load_migration()
        assert mod.revision == "004_create_continuous_aggregates"
        assert mod.down_revision == "003_create_anomaly_records"

    def test_upgrade_contains_daily_aggregate(self) -> None:
        import inspect

        mod = _load_migration()
        source = inspect.getsource(mod.upgrade)
        assert "daily_metric_agg" in source
        assert "time_bucket" in source
        assert "AVG(value)" in source
        assert "MIN(value)" in source
        assert "MAX(value)" in source

    def test_upgrade_contains_weekly_aggregate(self) -> None:
        import inspect

        mod = _load_migration()
        source = inspect.getsource(mod.upgrade)
        assert "weekly_load_agg" in source
        assert "SUM(value)" in source
        assert "training_load" in source

    def test_upgrade_contains_refresh_policies(self) -> None:
        import inspect

        mod = _load_migration()
        source = inspect.getsource(mod.upgrade)
        assert "add_continuous_aggregate_policy" in source
        assert "1 hour" in source

    def test_upgrade_contains_composite_index(self) -> None:
        import inspect

        mod = _load_migration()
        source = inspect.getsource(mod.upgrade)
        assert "ix_metric_records_athlete_type_time" in source

    def test_downgrade_drops_views(self) -> None:
        import inspect

        mod = _load_migration()
        source = inspect.getsource(mod.downgrade)
        assert "daily_metric_agg" in source
        assert "weekly_load_agg" in source
        assert "DROP" in source


class TestDailyMetricDataclass:
    """Test DailyMetric dataclass."""

    def test_creation(self) -> None:
        dm = DailyMetric(
            athlete_id=uuid.uuid4(),
            metric_type="resting_hr",
            bucket=date(2026, 2, 1),
            avg_value=62.5,
            min_value=58.0,
            max_value=67.0,
            sample_count=24,
        )
        assert dm.metric_type == "resting_hr"
        assert dm.avg_value == 62.5
        assert dm.sample_count == 24

    def test_frozen(self) -> None:
        dm = DailyMetric(
            athlete_id=uuid.uuid4(),
            metric_type="resting_hr",
            bucket=date(2026, 2, 1),
            avg_value=62.5,
            min_value=58.0,
            max_value=67.0,
            sample_count=24,
        )
        with pytest.raises(AttributeError):
            dm.avg_value = 99.0  # type: ignore[misc]


class TestWeeklyLoadDataclass:
    """Test WeeklyLoad dataclass."""

    def test_creation(self) -> None:
        wl = WeeklyLoad(
            athlete_id=uuid.uuid4(),
            bucket=date(2026, 2, 1),
            total_load=3500.0,
            avg_daily_load=500.0,
            session_count=7,
        )
        assert wl.total_load == 3500.0
        assert wl.session_count == 7


class TestAthleteMetricDataclass:
    """Test AthleteMetric dataclass."""

    def test_creation(self) -> None:
        am = AthleteMetric(
            athlete_id=uuid.uuid4(),
            full_name="Test Athlete",
            value=62.0,
            recorded_at=datetime(2026, 2, 28, 8, 0, 0, tzinfo=UTC),
        )
        assert am.full_name == "Test Athlete"
        assert am.value == 62.0


class TestRepoFallbackLogic:
    """Test that repo functions handle missing continuous aggregates gracefully."""

    async def test_get_daily_metrics_fallback(self) -> None:
        """When continuous aggregate doesn't exist, fallback is used."""
        from unittest.mock import AsyncMock

        from app.repositories.metric_agg_repo import get_daily_metrics

        aid = uuid.uuid4()
        mock_db = AsyncMock()
        # Simulate text() query failing (no TimescaleDB), triggering fallback
        mock_db.execute.side_effect = [
            Exception("relation daily_metric_agg does not exist"),
            # Fallback query returns empty
            MagicMock(all=MagicMock(return_value=[])),
        ]

        result = await get_daily_metrics(
            mock_db, aid, "resting_hr", date(2026, 1, 1), date(2026, 1, 31)
        )
        assert result == []

    async def test_get_weekly_loads_fallback(self) -> None:
        """When continuous aggregate doesn't exist, fallback is used."""
        from unittest.mock import AsyncMock

        from app.repositories.metric_agg_repo import get_weekly_loads

        aid = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            Exception("relation weekly_load_agg does not exist"),
            MagicMock(all=MagicMock(return_value=[])),
        ]

        result = await get_weekly_loads(
            mock_db, aid, date(2026, 1, 1), date(2026, 1, 31)
        )
        assert result == []
