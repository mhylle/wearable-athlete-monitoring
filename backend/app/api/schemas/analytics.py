"""Analytics response schemas."""

import uuid
from datetime import date

from pydantic import BaseModel


class DailyLoadResponse(BaseModel):
    """A single day's training load."""

    date: date
    total_load: float
    session_count: int


class ACWRResponse(BaseModel):
    """ACWR computation result."""

    acute_ewma: float
    chronic_ewma: float
    acwr_value: float | None
    zone: str
    date: date


class TrainingLoadSummaryResponse(BaseModel):
    """Full training load summary."""

    acwr: ACWRResponse
    monotony: float
    strain: float
    daily_loads: list[DailyLoadResponse]
    total_load: float
    avg_daily_load: float


class AthleteACWRResponse(BaseModel):
    """ACWR summary for a single athlete."""

    athlete_id: uuid.UUID
    full_name: str
    acwr: ACWRResponse


class TeamACWROverviewResponse(BaseModel):
    """Team ACWR overview."""

    athletes: list[AthleteACWRResponse]
    date: date


# ---------- HRV schemas ----------


class DailyHRVResponse(BaseModel):
    """A single day's HRV reading."""

    date: date
    rmssd: float


class HRVStatsResponse(BaseModel):
    """Rolling HRV statistics."""

    rolling_mean: float
    rolling_cv: float
    trend: str
    baseline_mean: float


class HRVAnalysisResponse(BaseModel):
    """Full HRV analysis response."""

    athlete_id: uuid.UUID
    start: date
    end: date
    daily_values: list[DailyHRVResponse]
    stats: HRVStatsResponse


# ---------- Sleep schemas ----------


class SleepSummaryResponse(BaseModel):
    """Summary of one night's sleep."""

    date: date
    total_minutes: float
    deep_minutes: float
    rem_minutes: float
    light_minutes: float
    awake_minutes: float
    efficiency: float


class SleepAverageResponse(BaseModel):
    """Averaged sleep statistics."""

    days: int
    avg_total_minutes: float
    avg_deep_minutes: float
    avg_rem_minutes: float
    avg_light_minutes: float
    avg_awake_minutes: float
    avg_efficiency: float


class SleepAnalysisResponse(BaseModel):
    """Full sleep analysis response."""

    athlete_id: uuid.UUID
    start: date
    end: date
    daily_summaries: list[SleepSummaryResponse]
    average: SleepAverageResponse


# ---------- Recovery schemas ----------


class RecoveryScoreResponse(BaseModel):
    """Composite recovery score response."""

    total_score: float | None
    hrv_component: float | None = None
    sleep_component: float | None = None
    load_component: float | None = None
    subjective_component: float | None = None
    available_components: list[str]


class AthleteRecoveryResponse(BaseModel):
    """Recovery summary for a single athlete."""

    athlete_id: uuid.UUID
    full_name: str
    recovery_score: RecoveryScoreResponse


class TeamRecoveryOverviewResponse(BaseModel):
    """Team recovery overview."""

    athletes: list[AthleteRecoveryResponse]
    date: date


# ---------- Anomaly schemas ----------


class AnomalyResponse(BaseModel):
    """A single detected anomaly."""

    athlete_id: str
    metric_type: str
    value: float
    expected_median: float
    mad_score: float
    severity: str
    anomaly_type: str
    explanation: str
    detected_at: date


class AthleteAnomaliesResponse(BaseModel):
    """Anomalies for a single athlete."""

    athlete_id: uuid.UUID
    anomalies: list[AnomalyResponse]
    date: date


class TeamAnomaliesResponse(BaseModel):
    """Team-wide anomaly scan results."""

    anomalies: list[AnomalyResponse]
    date: date
