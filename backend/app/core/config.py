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
