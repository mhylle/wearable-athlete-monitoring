"""Shared fixtures for model tests."""

import uuid
from datetime import UTC, date, datetime

import pytest

from app.models import (
    AthleteProfile,
    MetricRecord,
    SessionMetrics,
    Team,
    TrainingSession,
    User,
    WellnessEntry,
)


@pytest.fixture
def team_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_team(team_id: uuid.UUID) -> Team:
    return Team(
        id=team_id,
        name="Test FC",
        sport="football",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_user(user_id: uuid.UUID, team_id: uuid.UUID) -> User:
    return User(
        id=user_id,
        email="athlete@test.com",
        hashed_password="hashed_pw",
        role="athlete",
        full_name="Test Athlete",
        team_id=team_id,
        ow_user_id=None,
        is_active=True,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_athlete_profile(user_id: uuid.UUID) -> AthleteProfile:
    return AthleteProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        date_of_birth=date(2000, 1, 15),
        position="midfielder",
        height_cm=180.0,
        weight_kg=75.0,
        garmin_connected=False,
        ow_connection_id=None,
    )


@pytest.fixture
def sample_training_session(user_id: uuid.UUID, session_id: uuid.UUID) -> TrainingSession:
    return TrainingSession(
        id=session_id,
        athlete_id=user_id,
        source="garmin",
        session_type="training",
        start_time=datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
        end_time=datetime(2026, 2, 28, 11, 30, 0, tzinfo=UTC),
        duration_minutes=90.0,
        ow_event_id=None,
        notes=None,
        created_by=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_session_metrics(session_id: uuid.UUID) -> SessionMetrics:
    return SessionMetrics(
        id=uuid.uuid4(),
        session_id=session_id,
        hr_avg=145.0,
        hr_max=185.0,
        hr_min=60.0,
        distance_m=10500.0,
        energy_kcal=650.0,
        steps=12000,
        max_speed_ms=8.5,
        elevation_gain_m=45.0,
    )


@pytest.fixture
def sample_wellness_entry(user_id: uuid.UUID) -> WellnessEntry:
    return WellnessEntry(
        id=uuid.uuid4(),
        athlete_id=user_id,
        date=date(2026, 2, 28),
        srpe=7,
        srpe_duration_min=90.0,
        soreness=4,
        fatigue=5,
        mood=4,
        sleep_quality=3,
        notes=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_metric_record(user_id: uuid.UUID) -> MetricRecord:
    return MetricRecord(
        athlete_id=user_id,
        metric_type="resting_hr",
        recorded_at=datetime(2026, 2, 28, 7, 0, 0, tzinfo=UTC),
        value=52.0,
        source="garmin",
        ow_series_id=None,
    )
