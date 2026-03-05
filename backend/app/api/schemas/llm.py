"""Pydantic schemas for LLM analysis endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class LLMAnalysisRequest(BaseModel):
    """Request for a specific LLM analysis type."""

    type: str = "recovery_analysis"


class LLMCacheDeleteResponse(BaseModel):
    """Response after cache invalidation."""

    deleted_keys: int
    message: str
