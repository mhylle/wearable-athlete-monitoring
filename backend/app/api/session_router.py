"""Training session API router."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.session import (
    SessionCreateRequest,
    SessionDetailResponse,
    SessionListResponse,
    SessionMetricsResponse,
    SessionResponse,
)
from app.auth.dependencies import get_current_user, require_coach
from app.db import get_db
from app.models.user import User
from app.services import session_service

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreateRequest,
    coach: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Create a manual training session (coach only)."""
    session = await session_service.create_manual_session(
        db,
        body.model_dump(exclude_unset=True),
        coach_id=coach.id,
    )
    return SessionResponse.model_validate(session)


@router.get(
    "/athlete/{athlete_id}",
    response_model=SessionListResponse,
)
async def list_athlete_sessions(
    athlete_id: uuid.UUID,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session_type: str | None = Query(default=None),
    source: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List training sessions for an athlete (coach or self)."""
    if current_user.role != "coach" and current_user.id != athlete_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these sessions",
        )

    sessions = await session_service.list_sessions(
        db,
        athlete_id,
        start=start,
        end=end,
        session_type=session_type,
        source=source,
    )
    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        count=len(sessions),
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    """Get a training session with metrics (coach or session's athlete)."""
    result = await session_service.get_session_detail(db, session_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session = result["session"]
    if current_user.role != "coach" and current_user.id != session.athlete_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this session",
        )

    metrics_resp = None
    if result["metrics"] is not None:
        metrics_resp = SessionMetricsResponse.model_validate(result["metrics"])

    return SessionDetailResponse(
        session=SessionResponse.model_validate(session),
        metrics=metrics_resp,
    )
