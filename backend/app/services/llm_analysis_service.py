"""LLM analysis service — gathers data, builds prompts, streams from Ollama, caches in Redis."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.fitness_service import compute_athlete_fitness
from app.services.llm_prompts import (
    ANALYSIS_TYPES,
    SYSTEM_PROMPT,
    build_combined_prompt,
    build_prompt,
)
from app.services.ollama_client import generate, generate_stream
from app.services.recovery_service import (
    get_hrv_analysis,
    get_recovery_score,
    get_sleep_analysis,
)

logger = logging.getLogger(__name__)

# Try to import redis; it's optional for dev without Redis
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None  # type: ignore[assignment]


async def _get_redis():
    """Get a Redis connection or None if unavailable."""
    if aioredis is None:
        return None
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None


def _cache_key(athlete_id, analysis_type: str, target_date: date) -> str:
    return f"llm:{athlete_id}:{analysis_type}:{target_date.isoformat()}"


async def _get_cached(athlete_id, analysis_type: str, target_date: date) -> str | None:
    """Check Redis cache for a previous result."""
    r = await _get_redis()
    if r is None:
        return None
    try:
        key = _cache_key(athlete_id, analysis_type, target_date)
        result = await r.get(key)
        await r.aclose()
        return result
    except Exception:
        return None


async def _set_cached(athlete_id, analysis_type: str, target_date: date, result: str) -> None:
    """Store result in Redis cache with TTL."""
    r = await _get_redis()
    if r is None:
        return
    try:
        key = _cache_key(athlete_id, analysis_type, target_date)
        await r.setex(key, settings.LLM_CACHE_TTL_SECONDS, result)
        await r.aclose()
    except Exception:
        pass


async def invalidate_cache(athlete_id, target_date: date | None = None) -> int:
    """Invalidate cached LLM results for an athlete. Returns count of deleted keys."""
    r = await _get_redis()
    if r is None:
        return 0
    try:
        if target_date:
            pattern = f"llm:{athlete_id}:*:{target_date.isoformat()}"
        else:
            pattern = f"llm:{athlete_id}:*"
        keys = []
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
        deleted = 0
        if keys:
            deleted = await r.delete(*keys)
        await r.aclose()
        return deleted
    except Exception:
        return 0


async def _gather_athlete_data(
    db: AsyncSession,
    athlete_id,
    target_date: date,
) -> dict:
    """Gather all relevant data for building LLM prompts."""
    end = target_date
    start = end - timedelta(days=28)

    data: dict = {"athlete_id": str(athlete_id), "date": target_date.isoformat()}

    # Recovery score
    try:
        recovery = await get_recovery_score(db, athlete_id, target_date)
        data["recovery_score"] = {
            "total": recovery.total_score,
            "hrv_component": recovery.hrv_component,
            "sleep_component": recovery.sleep_component,
            "load_component": recovery.load_component,
            "subjective_component": recovery.subjective_component,
            "available_components": recovery.available_components,
        }
    except Exception as e:
        logger.warning("Failed to get recovery score: %s", e)

    # HRV analysis
    try:
        hrv = await get_hrv_analysis(db, athlete_id, start, end)
        data["hrv"] = {
            "rolling_mean": hrv["stats"].rolling_mean if hrv.get("stats") else None,
            "trend": hrv["stats"].trend.value if hrv.get("stats") else None,
            "baseline_mean": hrv["stats"].baseline_mean if hrv.get("stats") else None,
            "daily_count": len(hrv.get("daily_values", [])),
        }
    except Exception as e:
        logger.warning("Failed to get HRV analysis: %s", e)

    # Sleep analysis
    try:
        sleep = await get_sleep_analysis(db, athlete_id, end - timedelta(days=7), end)
        summaries = sleep.get("daily_summaries", [])
        data["sleep"] = {
            "days": len(summaries),
            "recent_summaries": [
                {
                    "date": str(s.date),
                    "total_min": round(s.total_minutes, 1),
                    "deep_min": round(s.deep_minutes, 1),
                    "rem_min": round(s.rem_minutes, 1),
                    "efficiency": round(s.efficiency, 3),
                }
                for s in summaries[-7:]
            ],
        }
    except Exception as e:
        logger.warning("Failed to get sleep analysis: %s", e)

    # Fitness score + trends
    try:
        fitness = await compute_athlete_fitness(db, athlete_id, target_date)
        fs = fitness["fitness_score"]
        data["fitness"] = {
            "total": fs.total,
            "components": fs.components,
        }
        data["trends"] = [
            {"metric": t.metric_type, "direction": t.direction, "z_score": t.z_score}
            for t in fitness["trends"]
        ]
    except Exception as e:
        logger.warning("Failed to get fitness score: %s", e)

    # Wellness entries
    try:
        from app.models.wellness_entry import WellnessEntry

        stmt = (
            select(WellnessEntry)
            .where(
                WellnessEntry.athlete_id == athlete_id,
                WellnessEntry.date >= start,
                WellnessEntry.date <= end,
            )
            .order_by(WellnessEntry.date.desc())
            .limit(14)
        )
        result = await db.execute(stmt)
        entries = list(result.scalars().all())
        data["wellness"] = [
            {
                "date": str(e.date),
                "mood": e.mood,
                "fatigue": e.fatigue,
                "soreness": e.soreness,
                "srpe": e.srpe,
                "sleep_quality": e.sleep_quality,
            }
            for e in entries
        ]
    except Exception as e:
        logger.warning("Failed to get wellness entries: %s", e)

    return data


async def analyze_athlete(
    db: AsyncSession,
    athlete_id,
    analysis_type: str,
    target_date: date | None = None,
) -> AsyncIterator[str]:
    """Stream a single analysis type for an athlete.

    Checks cache first, falls back to Ollama.
    Yields text chunks.
    """
    if target_date is None:
        target_date = date.today()

    # Check cache
    cached = await _get_cached(athlete_id, analysis_type, target_date)
    if cached is not None:
        yield cached
        return

    # Gather data and build prompt
    data = await _gather_athlete_data(db, athlete_id, target_date)
    prompt = build_prompt(analysis_type, data)

    # Stream from Ollama and collect full result
    full_result: list[str] = []
    async for chunk in generate_stream(prompt, system=SYSTEM_PROMPT):
        full_result.append(chunk)
        yield chunk

    # Cache the complete result
    result_text = "".join(full_result)
    if result_text:
        await _set_cached(athlete_id, analysis_type, target_date, result_text)


async def analyze_athlete_all(
    db: AsyncSession,
    athlete_id,
    target_date: date | None = None,
) -> AsyncIterator[dict]:
    """Run all analysis types sequentially, yielding SSE-compatible events.

    Events:
        {"event": "analysis_start", "data": {"type": "..."}}
        {"event": "analysis_chunk", "data": {"type": "...", "chunk": "..."}}
        {"event": "analysis_complete", "data": {"type": "...", "result": "...", "cached": bool}}
        {"event": "all_complete", "data": {"summary": "..."}}
    """
    if target_date is None:
        target_date = date.today()

    completed_results: dict[str, str] = {}

    for analysis_type in ANALYSIS_TYPES:
        yield {"event": "analysis_start", "data": {"type": analysis_type}}

        # Check cache
        cached = await _get_cached(athlete_id, analysis_type, target_date)
        if cached is not None:
            yield {
                "event": "analysis_complete",
                "data": {"type": analysis_type, "result": cached, "cached": True},
            }
            completed_results[analysis_type] = cached
            continue

        # Gather data (reuses same data for all types - could optimize with single fetch)
        data = await _gather_athlete_data(db, athlete_id, target_date)
        prompt = build_prompt(analysis_type, data)

        full_result: list[str] = []
        async for chunk in generate_stream(prompt, system=SYSTEM_PROMPT):
            full_result.append(chunk)
            yield {
                "event": "analysis_chunk",
                "data": {"type": analysis_type, "chunk": chunk},
            }

        result_text = "".join(full_result)
        if result_text:
            await _set_cached(athlete_id, analysis_type, target_date, result_text)

        yield {
            "event": "analysis_complete",
            "data": {"type": analysis_type, "result": result_text, "cached": False},
        }
        completed_results[analysis_type] = result_text

    # Combined summary
    if completed_results:
        yield {"event": "analysis_start", "data": {"type": "combined_summary"}}

        cached_summary = await _get_cached(athlete_id, "combined_summary", target_date)
        if cached_summary is not None:
            yield {
                "event": "analysis_complete",
                "data": {"type": "combined_summary", "result": cached_summary, "cached": True},
            }
        else:
            combined_prompt = build_combined_prompt(completed_results)
            summary_parts: list[str] = []
            async for chunk in generate_stream(combined_prompt, system=SYSTEM_PROMPT):
                summary_parts.append(chunk)
                yield {
                    "event": "analysis_chunk",
                    "data": {"type": "combined_summary", "chunk": chunk},
                }

            summary_text = "".join(summary_parts)
            if summary_text:
                await _set_cached(athlete_id, "combined_summary", target_date, summary_text)

            yield {
                "event": "analysis_complete",
                "data": {"type": "combined_summary", "result": summary_text, "cached": False},
            }

    yield {"event": "all_complete", "data": {"summary": completed_results.get("combined_summary", "")}}
