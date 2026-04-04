"""Environment-backed settings for embedding pipeline and FAISS paths."""

from __future__ import annotations

import os
from pathlib import Path

# backend/app/core/config.py → repo root is three levels up (for default data/faiss)
_REPO_ROOT = Path(__file__).resolve().parents[3]


def get_faiss_data_dir() -> Path:
    """Directory where the FAISS index is saved (default: <repo>/data/faiss)."""
    override = os.environ.get("FAISS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return _REPO_ROOT / "data" / "faiss"


def get_fireworks_api_key() -> str | None:
    return os.environ.get("FIREWORKS_API_KEY") or None


def get_fireworks_embedding_model() -> str:
    """
    Fireworks embeddings API expects IDs like ``fireworks/qwen3-embedding-8b``.
    If ``FIREWORKS_EMBEDDING_MODEL`` is set to the short name ``qwen3-embedding-8b``
    (no slash), we prepend ``fireworks/`` so the request matches the docs.
    """
    default = "fireworks/qwen3-embedding-8b"
    raw = (os.environ.get("FIREWORKS_EMBEDDING_MODEL") or default).strip()
    if not raw:
        return default
    # Shorthand from docs copy-paste without org prefix → BadRequest "not available"
    if "/" not in raw and raw.startswith("qwen3-embedding"):
        return f"fireworks/{raw}"
    return raw


# Token targets for chunking (300–500 range; overlap 50)
CHUNK_SIZE_TOKENS = int(os.environ.get("EMBED_CHUNK_SIZE_TOKENS", "400"))
CHUNK_OVERLAP_TOKENS = int(os.environ.get("EMBED_CHUNK_OVERLAP_TOKENS", "50"))

RETRIEVAL_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", "8"))
RETRIEVAL_TOP_THREADS = int(os.environ.get("RETRIEVAL_TOP_THREADS", "2"))


# --- Phase 5 — LLM: Groq OpenAI-compatible Chat Completions (https://console.groq.com) ---


def get_llm_api_key() -> str | None:
    """``GROQ_API_KEY`` only (Phase 5 chat)."""
    k = (os.environ.get("GROQ_API_KEY") or "").strip()
    return k or None


def get_llm_base_url() -> str:
    """Groq Chat Completions base; override with ``GROQ_BASE_URL`` or ``OPENAI_BASE_URL``."""
    explicit = (
        os.environ.get("GROQ_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or ""
    ).strip().rstrip("/")
    if explicit:
        return explicit
    return "https://api.groq.com/openai/v1"


def get_llm_model() -> str:
    """Chat model id; override with ``LLM_MODEL`` or ``GROQ_MODEL``."""
    raw = (
        os.environ.get("LLM_MODEL")
        or os.environ.get("GROQ_MODEL")
        or ""
    ).strip()
    if raw:
        return raw
    return "llama-3.3-70b-versatile"
