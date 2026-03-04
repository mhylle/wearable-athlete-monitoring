"""Analytics API endpoints."""

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.analytics import (
    ACWRResponse,
    AnomalyResponse,
    AthleteACWRResponse,
    AthleteAnomaliesResponse,
    AthleteRecoveryResponse,
    DailyHRVResponse,
    DailyLoadResponse,
    HRVAnalysisResponse,
    HRVStatsResponse,
    RecoveryScoreResponse,
    SleepAnalysisResponse,
    SleepAverageResponse,
    SleepSummaryResponse,
    TeamACWROverviewResponse,
    TeamAnomaliesResponse,
    TeamRecoveryOverviewResponse,
    TrainingLoadSummaryResponse,
)
from app.auth.dependencies import get_current_user, require_coach
from app.db import get_db
from app.models.user import User
from app.services.recovery_service import (
    get_hrv_analysis,
    get_recovery_score,
    get_sleep_analysis,
    get_team_recovery_overview,
)
from app.services.training_load_service import (
    get_acwr,
    get_team_acwr_overview,
    get_training_load_summary,
)

analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _acwr_to_response(acwr_result) -> ACWRResponse:
    return ACWRResponse(
        acute_ewma=acwr_result.acute_ewma,
        chronic_ewma=acwr_result.chronic_ewma,
        acwr_value=acwr_result.acwr_value,
        zone=acwr_result.zone.value,
        date=acwr_result.date,
    )


@analytics_router.get(
    "/athlete/{athlete_id}/acwr", response_model=ACWRResponse
)
async def get_athlete_acwr(
    athlete_id: uuid.UUID,
    as_of_date: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ACWRResponse:
    """Get ACWR for an athlete."""
    if as_of_date is None:
        as_of_date = date.today()
    result = await get_acwr(db, athlete_id, as_of_date)
    return _acwr_to_response(result)


@analytics_router.get(
    "/athlete/{athlete_id}/training-load",
    response_model=TrainingLoadSummaryResponse,
)
async def get_athlete_training_load(
    athlete_id: uuid.UUID,
    start: date = Query(default=None),
    end: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingLoadSummaryResponse:
    """Get full training load summary for an athlete."""
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=7)

    summary = await get_training_load_summary(db, athlete_id, start, end)
    return TrainingLoadSummaryResponse(
        acwr=_acwr_to_response(summary.acwr),
        monotony=summary.monotony,
        strain=summary.strain,
        daily_loads=[
            DailyLoadResponse(
                date=dl.date,
                total_load=dl.total_load,
                session_count=dl.session_count,
            )
            for dl in summary.daily_loads
        ],
        total_load=summary.total_load,
        avg_daily_load=summary.avg_daily_load,
    )


@analytics_router.get(
    "/team/acwr-overview", response_model=TeamACWROverviewResponse
)
async def get_team_acwr(
    as_of_date: date = Query(default=None),
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> TeamACWROverviewResponse:
    """Get ACWR overview for all athletes on the coach's team."""
    if as_of_date is None:
        as_of_date = date.today()
    if current_user.team_id is None:
        return TeamACWROverviewResponse(athletes=[], date=as_of_date)

    results = await get_team_acwr_overview(db, current_user.team_id, as_of_date)
    return TeamACWROverviewResponse(
        athletes=[
            AthleteACWRResponse(
                athlete_id=r.athlete_id,
                full_name=r.full_name,
                acwr=_acwr_to_response(r.acwr),
            )
            for r in results
        ],
        date=as_of_date,
    )


# ---------- HRV endpoints ----------


@analytics_router.get(
    "/athlete/{athlete_id}/hrv", response_model=HRVAnalysisResponse
)
async def get_athlete_hrv(
    athlete_id: uuid.UUID,
    start: date = Query(default=None),
    end: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HRVAnalysisResponse:
    """Get HRV trend analysis for an athlete."""
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=30)

    result = await get_hrv_analysis(db, athlete_id, start, end)
    return HRVAnalysisResponse(
        athlete_id=result["athlete_id"],
        start=result["start"],
        end=result["end"],
        daily_values=[
            DailyHRVResponse(date=dv["date"], rmssd=dv["rmssd"])
            for dv in result["daily_values"]
        ],
        stats=HRVStatsResponse(
            rolling_mean=result["stats"].rolling_mean,
            rolling_cv=result["stats"].rolling_cv,
            trend=result["stats"].trend.value,
            baseline_mean=result["stats"].baseline_mean,
        ),
    )


# ---------- Sleep endpoints ----------


@analytics_router.get(
    "/athlete/{athlete_id}/sleep", response_model=SleepAnalysisResponse
)
async def get_athlete_sleep(
    athlete_id: uuid.UUID,
    start: date = Query(default=None),
    end: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SleepAnalysisResponse:
    """Get sleep analysis for an athlete."""
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=7)

    result = await get_sleep_analysis(db, athlete_id, start, end)
    avg = result["average"]
    return SleepAnalysisResponse(
        athlete_id=result["athlete_id"],
        start=result["start"],
        end=result["end"],
        daily_summaries=[
            SleepSummaryResponse(
                date=s.date,
                total_minutes=s.total_minutes,
                deep_minutes=s.deep_minutes,
                rem_minutes=s.rem_minutes,
                light_minutes=s.light_minutes,
                awake_minutes=s.awake_minutes,
                efficiency=s.efficiency,
            )
            for s in result["daily_summaries"]
        ],
        average=SleepAverageResponse(
            days=avg.days,
            avg_total_minutes=avg.avg_total_minutes,
            avg_deep_minutes=avg.avg_deep_minutes,
            avg_rem_minutes=avg.avg_rem_minutes,
            avg_light_minutes=avg.avg_light_minutes,
            avg_awake_minutes=avg.avg_awake_minutes,
            avg_efficiency=avg.avg_efficiency,
        ),
    )


# ---------- Recovery endpoints ----------


@analytics_router.get(
    "/athlete/{athlete_id}/recovery", response_model=RecoveryScoreResponse
)
async def get_athlete_recovery(
    athlete_id: uuid.UUID,
    target_date: date = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecoveryScoreResponse:
    """Get recovery score for an athlete on a given date."""
    if target_date is None:
        target_date = date.today()

    score = await get_recovery_score(db, athlete_id, target_date)
    return RecoveryScoreResponse(
        total_score=score.total_score,
        hrv_component=score.hrv_component,
        sleep_component=score.sleep_component,
        load_component=score.load_component,
        subjective_component=score.subjective_component,
        available_components=score.available_components,
    )


@analytics_router.get(
    "/team/recovery-overview", response_model=TeamRecoveryOverviewResponse
)
async def get_team_recovery(
    as_of_date: date = Query(default=None),
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> TeamRecoveryOverviewResponse:
    """Get recovery overview for all athletes on the coach's team."""
    if as_of_date is None:
        as_of_date = date.today()
    if current_user.team_id is None:
        return TeamRecoveryOverviewResponse(athletes=[], date=as_of_date)

    results = await get_team_recovery_overview(db, current_user.team_id, as_of_date)
    return TeamRecoveryOverviewResponse(
        athletes=[
            AthleteRecoveryResponse(
                athlete_id=r["athlete_id"],
                full_name=r["full_name"],
                recovery_score=RecoveryScoreResponse(
                    total_score=r["recovery_score"].total_score,
                    hrv_component=r["recovery_score"].hrv_component,
                    sleep_component=r["recovery_score"].sleep_component,
                    load_component=r["recovery_score"].load_component,
                    subjective_component=r["recovery_score"].subjective_component,
                    available_components=r["recovery_score"].available_components,
                ),
            )
            for r in results
        ],
        date=as_of_date,
    )


# ---------- Anomaly endpoints ----------


@analytics_router.get(
    "/athlete/{athlete_id}/anomalies", response_model=AthleteAnomaliesResponse
)
async def get_athlete_anomalies(
    athlete_id: uuid.UUID,
    as_of_date: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteAnomaliesResponse:
    """Get anomalies detected for an athlete."""
    from app.services.anomaly_service import scan_athlete_anomalies

    if as_of_date is None:
        as_of_date = date.today()

    anomalies = await scan_athlete_anomalies(db, athlete_id, as_of_date)
    return AthleteAnomaliesResponse(
        athlete_id=athlete_id,
        anomalies=[
            AnomalyResponse(
                athlete_id=a.athlete_id,
                metric_type=a.metric_type,
                value=a.value,
                expected_median=a.expected_median,
                mad_score=a.mad_score,
                severity=a.severity,
                anomaly_type=a.anomaly_type,
                explanation=a.explanation,
                detected_at=a.detected_at,
            )
            for a in anomalies
        ],
        date=as_of_date,
    )


@analytics_router.get(
    "/team/anomalies", response_model=TeamAnomaliesResponse
)
async def get_team_anomalies(
    as_of_date: date = Query(default=None),
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> TeamAnomaliesResponse:
    """Get team-wide anomaly scan results."""
    from app.services.anomaly_service import scan_team_anomalies

    if as_of_date is None:
        as_of_date = date.today()
    if current_user.team_id is None:
        return TeamAnomaliesResponse(anomalies=[], date=as_of_date)

    anomalies = await scan_team_anomalies(db, current_user.team_id, as_of_date)
    return TeamAnomaliesResponse(
        anomalies=[
            AnomalyResponse(
                athlete_id=a.athlete_id,
                metric_type=a.metric_type,
                value=a.value,
                expected_median=a.expected_median,
                mad_score=a.mad_score,
                severity=a.severity,
                anomaly_type=a.anomaly_type,
                explanation=a.explanation,
                detected_at=a.detected_at,
            )
            for a in anomalies
        ],
        date=as_of_date,
    )
