"""LLM analysis SSE endpoints."""

import json
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.llm import LLMCacheDeleteResponse
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.user import User
from app.services.llm_analysis_service import (
    analyze_athlete,
    analyze_athlete_all,
    invalidate_cache,
)
from app.services.llm_prompts import ANALYSIS_TYPES

llm_router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


async def _sse_single(db: AsyncSession, athlete_id: uuid.UUID, analysis_type: str):
    """Generate SSE events for a single analysis."""
    yield f"event: analysis_start\ndata: {json.dumps({'type': analysis_type})}\n\n"

    full_result: list[str] = []
    async for chunk in analyze_athlete(db, athlete_id, analysis_type):
        full_result.append(chunk)
        yield f"event: analysis_chunk\ndata: {json.dumps({'type': analysis_type, 'chunk': chunk})}\n\n"

    result_text = "".join(full_result)
    yield f"event: analysis_complete\ndata: {json.dumps({'type': analysis_type, 'result': result_text})}\n\n"


async def _sse_all(db: AsyncSession, athlete_id: uuid.UUID):
    """Generate SSE events for all analyses."""
    async for event in analyze_athlete_all(db, athlete_id):
        yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"


@llm_router.get("/athlete/{athlete_id}/analyze")
async def analyze_single(
    athlete_id: uuid.UUID,
    type: str = Query(default="recovery_analysis"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a single LLM analysis via SSE."""
    if type not in ANALYSIS_TYPES:
        valid = ", ".join(ANALYSIS_TYPES.keys())
        return {"error": f"Invalid analysis type. Valid types: {valid}"}

    return StreamingResponse(
        _sse_single(db, athlete_id, type),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@llm_router.get("/athlete/{athlete_id}/analyze-all")
async def analyze_all(
    athlete_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream all LLM analyses via SSE (5 types + combined summary)."""
    return StreamingResponse(
        _sse_all(db, athlete_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@llm_router.delete(
    "/athlete/{athlete_id}/cache",
    response_model=LLMCacheDeleteResponse,
)
async def delete_cache(
    athlete_id: uuid.UUID,
    target_date: date = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
):
    """Invalidate cached LLM results for an athlete."""
    deleted = await invalidate_cache(athlete_id, target_date)
    return LLMCacheDeleteResponse(
        deleted_keys=deleted,
        message=f"Deleted {deleted} cached analysis results",
    )
