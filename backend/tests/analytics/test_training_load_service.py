"""Tests for the training load service (integration with mocked DB)."""

import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.analytics.acwr import ACWRZone
from app.services.training_load_service import (
    get_acwr,
    get_team_acwr_overview,
    get_training_load_summary,
)


def _make_session(athlete_id, day_offset, duration=60.0, source="manual"):
    """Create a mock training session object."""
    mock = AsyncMock()
    mock.id = uuid.uuid4()
    mock.athlete_id = athlete_id
    mock.source = source
    mock.session_type = "training"
    mock.start_time = datetime(2026, 1, 28, 10, 0, tzinfo=UTC) - timedelta(
        days=day_offset
    )
    mock.end_time = mock.start_time + timedelta(minutes=duration)
    mock.duration_minutes = duration
    mock.ow_event_id = None
    mock.notes = None
    mock.created_by = None
    return mock


def _make_wellness(athlete_id, day_offset, srpe=5):
    """Create a mock wellness entry object."""
    mock = AsyncMock()
    mock.id = uuid.uuid4()
    mock.athlete_id = athlete_id
    mock.date = date(2026, 1, 28) - timedelta(days=day_offset)
    mock.srpe = srpe
    mock.srpe_duration_min = 60.0
    mock.soreness = 3
    mock.fatigue = 3
    mock.mood = 4
    mock.sleep_quality = 4
    mock.notes = None
    return mock


@pytest.mark.asyncio
class TestGetACWR:
    """Tests for get_acwr service function."""

    async def test_computes_acwr_from_sessions(self) -> None:
        """Service fetches sessions and wellness, computes ACWR."""
        athlete_id = uuid.uuid4()
        as_of_date = date(2026, 1, 28)

        # Create sessions for 28 days with constant load
        sessions = [_make_session(athlete_id, i) for i in range(28)]
        wellness = [_make_wellness(athlete_id, i, srpe=5) for i in range(28)]

        db = AsyncMock()

        with (
            patch(
                "app.services.training_load_service.SessionRepository"
            ) as mock_session_repo_cls,
            patch(
                "app.services.training_load_service.WellnessRepository"
            ) as mock_wellness_repo_cls,
        ):
            mock_session_repo = mock_session_repo_cls.return_value
            mock_session_repo.list_sessions = AsyncMock(return_value=sessions)

            mock_wellness_repo = mock_wellness_repo_cls.return_value
            mock_wellness_repo.list_entries = AsyncMock(return_value=wellness)

            result = await get_acwr(db, athlete_id, as_of_date)

        assert result.date == as_of_date
        assert result.acwr_value is not None
        # Constant load should produce ACWR near 1.0 (in optimal zone)
        assert result.zone == ACWRZone.OPTIMAL

    async def test_no_sessions_returns_undertraining(self) -> None:
        athlete_id = uuid.uuid4()
        as_of_date = date(2026, 1, 28)

        db = AsyncMock()

        with (
            patch(
                "app.services.training_load_service.SessionRepository"
            ) as mock_session_repo_cls,
            patch(
                "app.services.training_load_service.WellnessRepository"
            ) as mock_wellness_repo_cls,
        ):
            mock_session_repo = mock_session_repo_cls.return_value
            mock_session_repo.list_sessions = AsyncMock(return_value=[])

            mock_wellness_repo = mock_wellness_repo_cls.return_value
            mock_wellness_repo.list_entries = AsyncMock(return_value=[])

            result = await get_acwr(db, athlete_id, as_of_date)

        assert result.acwr_value is None
        assert result.zone == ACWRZone.UNDERTRAINING


@pytest.mark.asyncio
class TestGetTrainingLoadSummary:
    """Tests for get_training_load_summary service function."""

    async def test_returns_full_summary(self) -> None:
        athlete_id = uuid.uuid4()
        end = date(2026, 1, 28)
        start = end - timedelta(days=6)

        sessions = [_make_session(athlete_id, i) for i in range(35)]
        wellness = [_make_wellness(athlete_id, i, srpe=5) for i in range(35)]

        db = AsyncMock()

        with (
            patch(
                "app.services.training_load_service.SessionRepository"
            ) as mock_session_repo_cls,
            patch(
                "app.services.training_load_service.WellnessRepository"
            ) as mock_wellness_repo_cls,
        ):
            mock_session_repo = mock_session_repo_cls.return_value
            mock_session_repo.list_sessions = AsyncMock(return_value=sessions)

            mock_wellness_repo = mock_wellness_repo_cls.return_value
            mock_wellness_repo.list_entries = AsyncMock(return_value=wellness)

            result = await get_training_load_summary(db, athlete_id, start, end)

        assert result.acwr is not None
        assert result.total_load > 0
        assert result.avg_daily_load > 0
        assert len(result.daily_loads) == 7


@pytest.mark.asyncio
class TestGetTeamACWROverview:
    """Tests for get_team_acwr_overview service function."""

    async def test_returns_overview_for_team(self) -> None:
        team_id = uuid.uuid4()
        athlete1_id = uuid.uuid4()
        athlete2_id = uuid.uuid4()
        as_of_date = date(2026, 1, 28)

        mock_athlete1 = AsyncMock()
        mock_athlete1.id = athlete1_id
        mock_athlete1.full_name = "Player One"

        mock_athlete2 = AsyncMock()
        mock_athlete2.id = athlete2_id
        mock_athlete2.full_name = "Player Two"

        db = AsyncMock()

        with (
            patch(
                "app.services.training_load_service.UserRepository"
            ) as mock_user_repo_cls,
            patch(
                "app.services.training_load_service.SessionRepository"
            ) as mock_session_repo_cls,
            patch(
                "app.services.training_load_service.WellnessRepository"
            ) as mock_wellness_repo_cls,
        ):
            mock_user_repo = mock_user_repo_cls.return_value
            mock_user_repo.list_athletes = AsyncMock(
                return_value=[mock_athlete1, mock_athlete2]
            )

            mock_session_repo = mock_session_repo_cls.return_value
            mock_session_repo.list_sessions = AsyncMock(return_value=[])

            mock_wellness_repo = mock_wellness_repo_cls.return_value
            mock_wellness_repo.list_entries = AsyncMock(return_value=[])

            results = await get_team_acwr_overview(db, team_id, as_of_date)

        assert len(results) == 2
        assert results[0].full_name == "Player One"
        assert results[1].full_name == "Player Two"
        assert results[0].acwr is not None
