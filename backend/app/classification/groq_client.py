"""Shared Groq client; avoids import-time failure when API key is absent."""

from __future__ import annotations

from functools import lru_cache

from groq import Groq

from app.core.config import settings


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")
    return Groq(api_key=settings.GROQ_API_KEY)


def groq_configured() -> bool:
    return bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())
