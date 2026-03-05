"""Async client for Ollama API (local LLM inference)."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.config import settings


async def generate_stream(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
) -> AsyncIterator[str]:
    """Stream a response from Ollama's generate endpoint.

    Yields text chunks as they arrive.
    """
    model = model or settings.OLLAMA_MODEL
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(
        base_url=settings.OLLAMA_BASE_URL,
        timeout=httpx.Timeout(120.0, connect=10.0),
    ) as client:
        async with client.stream("POST", "/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                data = json.loads(line)
                if chunk := data.get("response", ""):
                    yield chunk
                if data.get("done", False):
                    break


async def generate(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
) -> str:
    """Non-streaming generation. Returns the full response text."""
    parts: list[str] = []
    async for chunk in generate_stream(prompt, model, system):
        parts.append(chunk)
    return "".join(parts)
