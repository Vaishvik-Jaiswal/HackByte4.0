"""
Phase 2 — one module: load emails from Postgres, chunk, embed (Fireworks), save FAISS.

Phase 3+ can import the same helpers for retrieval (load FAISS elsewhere when needed).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import tiktoken
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_fireworks import FireworksEmbeddings
from psycopg2.extras import RealDictCursor

from app.core.config import (
    CHUNK_OVERLAP_TOKENS,
    CHUNK_SIZE_TOKENS,
    get_fireworks_api_key,
    get_fireworks_embedding_model,
)


# --- PostgreSQL ---


def fetch_all_emails_ordered(conn) -> list[dict[str, Any]]:
    """All `emails` rows, ordered by thread then date."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, thread_id, gmail_msg_id, from_json, to_json,
                   subject, body_text, date
            FROM emails
            ORDER BY thread_id ASC, date ASC, id ASC
            """
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


# --- Text + chunking ---


def _json_pretty(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False)
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except TypeError:
        return str(value)


def email_row_to_embed_text(row: Mapping[str, Any]) -> str:
    """Subject, metadata, and body as one string for embedding."""
    subject = (row.get("subject") or "").strip()
    body = (row.get("body_text") or "").strip()
    thread_id = (row.get("thread_id") or "").strip()
    date = row.get("date")
    date_str = date.isoformat() if hasattr(date, "isoformat") else str(date or "")
    parts = [
        f"Subject: {subject}",
        f"Thread: {thread_id}",
        f"Date: {date_str}",
        f"From: {_json_pretty(row.get('from_json'))}",
        f"To: {_json_pretty(row.get('to_json'))}",
        "",
        body,
    ]
    return "\n".join(parts).strip()


def chunk_text_by_tokens(
    text: str,
    *,
    chunk_size: int = 400,
    overlap: int = 50,
    encoding_name: str = "cl100k_base",
) -> list[str]:
    """Sliding token windows (tiktoken); stable proxy for chunk size."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text or "")
    if not tokens:
        return []

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(enc.decode(tokens[start:end]))
        if end >= len(tokens):
            break
        start += step
    return chunks


def rows_to_embedding_documents(rows: list[dict[str, Any]]) -> list[Document]:
    """Each email → token chunks → Documents with thread_id, email_id, chunk_text, date."""
    documents: list[Document] = []
    for row in rows:
        full_text = email_row_to_embed_text(row)
        chunks = chunk_text_by_tokens(
            full_text,
            chunk_size=CHUNK_SIZE_TOKENS,
            overlap=CHUNK_OVERLAP_TOKENS,
        )
        if not chunks:
            chunks = [full_text] if full_text else [""]

        email_id = row.get("id")
        thread_id = str(row.get("thread_id") or "")
        date_val = row.get("date")
        date_iso = date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val or "")

        for i, chunk_text in enumerate(chunks):
            meta = {
                "thread_id": thread_id,
                "email_id": str(email_id),
                "chunk_text": chunk_text,
                "date": date_iso,
                "chunk_index": str(i),
            }
            documents.append(Document(page_content=chunk_text, metadata=meta))
    return documents


# --- Embeddings + FAISS ---


def build_fireworks_embeddings() -> FireworksEmbeddings:
    api_key = get_fireworks_api_key()
    if not api_key:
        raise RuntimeError(
            "FIREWORKS_API_KEY is not set. Add it to backend/.env for the embedding pipeline."
        )
    model = get_fireworks_embedding_model()
    return FireworksEmbeddings(model=model, fireworks_api_key=api_key)


def build_faiss_index(documents: list[Document], embeddings) -> FAISS:
    if not documents:
        raise ValueError("No documents to index.")
    return FAISS.from_documents(documents, embeddings)


def save_faiss_local(store: FAISS, directory: Path, index_name: str = "inbox_emails") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    store.save_local(str(directory), index_name=index_name)
