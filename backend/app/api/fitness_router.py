"""Fitness score and trend detection API endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.fitness import (
    AthleteFitnessResponse,
    AthleteTrendsResponse,
    FitnessScoreResponse,
    TeamAthleteFitnessResponse,
    TeamFitnessResponse,
    TrendResultResponse,
)
from app.auth.dependencies import get_current_user, require_coach
from app.db import get_db
from app.models.user import User
from app.services.fitness_service import compute_athlete_fitness, compute_team_fitness

fitness_router = APIRouter(prefix="/api/v1/fitness", tags=["fitness"])


def _fitness_to_response(result: dict) -> AthleteFitnessResponse:
    fs = result["fitness_score"]
    return AthleteFitnessResponse(
        athlete_id=result["athlete_id"],
        fitness_score=FitnessScoreResponse(
            total=fs.total,
            components=fs.components,
            available_components=fs.available_components,
            computed_at=fs.computed_at,
        ),
        trends=[
            TrendResultResponse(
                metric_type=t.metric_type,
                direction=t.direction,
                z_score=t.z_score,
                is_anomaly=t.is_anomaly,
                window_days=t.window_days,
            )
            for t in result["trends"]
        ],
        date=result["date"],
    )


@fitness_router.get(
    "/athlete/{athlete_id}",
    response_model=AthleteFitnessResponse,
)
async def get_athlete_fitness(
    athlete_id: uuid.UUID,
    target_date: date = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteFitnessResponse:
    """Get fitness score and trends for an athlete."""
    result = await compute_athlete_fitness(db, athlete_id, target_date)
    return _fitness_to_response(result)


@fitness_router.get(
    "/athlete/{athlete_id}/trends",
    response_model=AthleteTrendsResponse,
)
async def get_athlete_trends(
    athlete_id: uuid.UUID,
    target_date: date = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteTrendsResponse:
    """Get trend results only for an athlete."""
    result = await compute_athlete_fitness(db, athlete_id, target_date)
    return AthleteTrendsResponse(
        athlete_id=result["athlete_id"],
        trends=[
            TrendResultResponse(
                metric_type=t.metric_type,
                direction=t.direction,
                z_score=t.z_score,
                is_anomaly=t.is_anomaly,
                window_days=t.window_days,
            )
            for t in result["trends"]
        ],
        date=result["date"],
    )


@fitness_router.get(
    "/team/{team_id}",
    response_model=TeamFitnessResponse,
)
async def get_team_fitness(
    team_id: uuid.UUID,
    target_date: date = Query(default=None, alias="date"),
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> TeamFitnessResponse:
    """Get team-wide fitness summary."""
    if target_date is None:
        target_date = date.today()

    results = await compute_team_fitness(db, team_id, target_date)
    return TeamFitnessResponse(
        athletes=[
            TeamAthleteFitnessResponse(
                athlete_id=r["athlete_id"],
                full_name=r["full_name"],
                fitness_score=FitnessScoreResponse(
                    total=r["fitness_score"].total,
                    components=r["fitness_score"].components,
                    available_components=r["fitness_score"].available_components,
                    computed_at=r["fitness_score"].computed_at,
                ),
                trends=[
                    TrendResultResponse(
                        metric_type=t.metric_type,
                        direction=t.direction,
                        z_score=t.z_score,
                        is_anomaly=t.is_anomaly,
                        window_days=t.window_days,
                    )
                    for t in r["trends"]
                ],
            )
            for r in results
        ],
        date=target_date,
    )
