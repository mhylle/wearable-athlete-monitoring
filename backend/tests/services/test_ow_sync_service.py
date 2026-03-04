"""Tests for the Open Wearables sync service."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.user import User
from app.services.ow_mapper import (
    map_ow_sleep_to_records,
    map_ow_timeseries_to_records,
    map_ow_workout_to_session,
)
from app.services.ow_schemas import (
    OWDataPoint,
    OWSleep,
    OWSleepDetails,
    OWWorkout,
    OWWorkoutDetails,
)
from app.services.ow_sync_service import (
    sync_athlete_sleep,
    sync_athlete_timeseries,
    sync_athlete_workouts,
)


def _make_athlete(ow_user_id: str | None = "ow-123") -> User:
    return User(
        id=uuid.uuid4(),
        email="athlete@test.com",
        hashed_password="hashed",
        role="athlete",
        full_name="Test Athlete",
        ow_user_id=ow_user_id,
    )


def _mock_db_no_existing() -> AsyncMock:
    """DB session mock that returns None for all existence checks."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()  # add() is sync, not async
    return mock_db


def _mock_db_always_exists() -> AsyncMock:
    """DB session mock that returns a truthy value for existence checks (dedup)."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = True
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()
    return mock_db


# --- Mapper tests ---


class TestMapOWWorkoutToSession:
    def test_maps_basic_workout(self) -> None:
        athlete_id = uuid.uuid4()
        workout = OWWorkout(
            id="w1",
            user_id="ow-123",
            sport="running",
            start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
            end_time=datetime(2026, 2, 28, 11, 0, 0, tzinfo=UTC),
            duration_seconds=3600,
        )
        session, metrics = map_ow_workout_to_session(workout, athlete_id)

        assert session.athlete_id == athlete_id
        assert session.source == "garmin"
        assert session.session_type == "training"
        assert session.duration_minutes == 60.0
        assert session.ow_event_id == "w1"
        assert metrics is None

    def test_maps_workout_with_details(self) -> None:
        athlete_id = uuid.uuid4()
        workout = OWWorkout(
            id="w2",
            user_id="ow-123",
            sport="running",
            start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
            duration_seconds=3600,
            details=OWWorkoutDetails(hr_avg=155.0, distance_m=10000.0, energy_kcal=650.0),
        )
        session, metrics = map_ow_workout_to_session(workout, athlete_id)

        assert metrics is not None
        assert metrics.hr_avg == 155.0
        assert metrics.distance_m == 10000.0

    def test_maps_gym_workout(self) -> None:
        athlete_id = uuid.uuid4()
        workout = OWWorkout(
            id="w3",
            user_id="ow-123",
            sport="strength_training",
            start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
            duration_seconds=2700,
        )
        session, _ = map_ow_workout_to_session(workout, athlete_id)
        assert session.session_type == "gym"


class TestMapOWTimeseriesToRecords:
    def test_maps_data_points(self) -> None:
        athlete_id = uuid.uuid4()
        data = [
            OWDataPoint(timestamp=datetime(2026, 2, 28, 7, 0, 0, tzinfo=UTC), type="resting_hr", value=52.0),
            OWDataPoint(timestamp=datetime(2026, 2, 28, 7, 0, 0, tzinfo=UTC), type="hrv_rmssd", value=45.0),
        ]
        records = map_ow_timeseries_to_records(data, athlete_id)

        assert len(records) == 2
        assert records[0].metric_type == "resting_hr"
        assert records[0].value == 52.0
        assert records[1].metric_type == "hrv_rmssd"

    def test_empty_data_returns_empty(self) -> None:
        records = map_ow_timeseries_to_records([], uuid.uuid4())
        assert records == []


class TestMapOWSleepToRecords:
    def test_maps_sleep_with_details(self) -> None:
        athlete_id = uuid.uuid4()
        sleep = OWSleep(
            id="s1",
            user_id="ow-123",
            start_time=datetime(2026, 2, 27, 22, 0, 0, tzinfo=UTC),
            end_time=datetime(2026, 2, 28, 6, 30, 0, tzinfo=UTC),
            duration_minutes=510.0,
            score=82.0,
            details=OWSleepDetails(deep_minutes=90.0, rem_minutes=100.0),
        )
        records = map_ow_sleep_to_records(sleep, athlete_id)

        types = {r.metric_type for r in records}
        assert "sleep_duration" in types
        assert "sleep_score" in types
        assert "sleep_deep_min" in types
        assert "sleep_rem_min" in types
        assert len(records) == 4

    def test_maps_sleep_without_details(self) -> None:
        athlete_id = uuid.uuid4()
        sleep = OWSleep(
            id="s2",
            user_id="ow-123",
            start_time=datetime(2026, 2, 27, 22, 0, 0, tzinfo=UTC),
            end_time=datetime(2026, 2, 28, 6, 30, 0, tzinfo=UTC),
            duration_minutes=510.0,
        )
        records = map_ow_sleep_to_records(sleep, athlete_id)
        assert len(records) == 1
        assert records[0].metric_type == "sleep_duration"


# --- Sync service tests ---


class TestSyncAthleteTimeseries:
    async def test_syncs_new_records(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_timeseries.return_value = [
            OWDataPoint(timestamp=datetime(2026, 2, 28, 7, 0, 0, tzinfo=UTC), type="resting_hr", value=52.0),
        ]
        mock_db = _mock_db_no_existing()
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_timeseries(athlete, start, end, mock_client, mock_db)

        assert result.records_synced == 1
        assert result.records_skipped == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_skips_duplicate_records(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_timeseries.return_value = [
            OWDataPoint(timestamp=datetime(2026, 2, 28, 7, 0, 0, tzinfo=UTC), type="resting_hr", value=52.0),
        ]
        mock_db = _mock_db_always_exists()
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_timeseries(athlete, start, end, mock_client, mock_db)

        assert result.records_synced == 0
        assert result.records_skipped == 1

    async def test_errors_when_no_ow_user(self) -> None:
        athlete = _make_athlete(ow_user_id=None)
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_timeseries(athlete, start, end, mock_client, mock_db)

        assert len(result.errors) == 1
        assert "not provisioned" in result.errors[0]

    async def test_handles_api_error(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_timeseries.side_effect = Exception("API error")
        mock_db = AsyncMock()
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_timeseries(athlete, start, end, mock_client, mock_db)

        assert len(result.errors) == 1
        assert "Failed to fetch" in result.errors[0]


class TestSyncAthleteWorkouts:
    async def test_syncs_new_workouts(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_workouts.return_value = [
            OWWorkout(
                id="w1",
                user_id="ow-123",
                sport="running",
                start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
                duration_seconds=3600,
            )
        ]
        mock_db = _mock_db_no_existing()
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_workouts(athlete, start, end, mock_client, mock_db)

        assert result.records_synced == 1
        mock_db.commit.assert_called_once()

    async def test_skips_duplicate_workouts(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_workouts.return_value = [
            OWWorkout(
                id="w1",
                user_id="ow-123",
                sport="running",
                start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
                duration_seconds=3600,
            )
        ]
        mock_db = _mock_db_always_exists()
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_workouts(athlete, start, end, mock_client, mock_db)

        assert result.records_synced == 0
        assert result.records_skipped == 1


class TestSyncAthleteSleep:
    async def test_syncs_new_sleep(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_sleep.return_value = [
            OWSleep(
                id="s1",
                user_id="ow-123",
                start_time=datetime(2026, 2, 27, 22, 0, 0, tzinfo=UTC),
                end_time=datetime(2026, 2, 28, 6, 30, 0, tzinfo=UTC),
                duration_minutes=510.0,
                score=82.0,
            )
        ]
        mock_db = _mock_db_no_existing()
        start = datetime(2026, 2, 27, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_sleep(athlete, start, end, mock_client, mock_db)

        # sleep_duration + sleep_score = 2 records
        assert result.records_synced == 2
        mock_db.commit.assert_called_once()

    async def test_skips_duplicate_sleep(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.get_sleep.return_value = [
            OWSleep(
                id="s1",
                user_id="ow-123",
                start_time=datetime(2026, 2, 27, 22, 0, 0, tzinfo=UTC),
                end_time=datetime(2026, 2, 28, 6, 30, 0, tzinfo=UTC),
                duration_minutes=510.0,
            )
        ]
        mock_db = _mock_db_always_exists()
        start = datetime(2026, 2, 27, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

        result = await sync_athlete_sleep(athlete, start, end, mock_client, mock_db)

        assert result.records_synced == 0
        assert result.records_skipped == 1
