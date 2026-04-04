"""
Phase 2 — Postgres → chunk → Fireworks embeddings → FAISS save.

Phase 3 — load FAISS, query → embedding → top-K chunk search → group by thread_id
→ rank threads (similarity, hit count, recency) → top 1–2 threads.

Phase 4 — given thread_id: load all emails from Postgres (date ASC), format as a
readable conversation string for LLM / display.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
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


def fetch_emails_for_thread(conn, thread_id: str) -> list[dict[str, Any]]:
    """All emails in one thread, oldest first (Phase 4)."""
    tid = (thread_id or "").strip()
    if not tid:
        return []
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, thread_id, gmail_msg_id, from_json, to_json,
                   subject, body_text, date
            FROM emails
            WHERE thread_id = %s
            ORDER BY date ASC, id ASC
            """,
            (tid,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def _sender_display(from_json: Any) -> str:
    """Human-readable sender line from JSONB `from_json`."""
    if isinstance(from_json, dict):
        name = str(from_json.get("name") or "").strip()
        email = str(from_json.get("email") or "").strip()
        if name and email:
            return f"{name} <{email}>"
        return name or email or "unknown"
    return str(from_json or "unknown")


def format_thread_conversation(rows: list[Mapping[str, Any]]) -> str:
    """
    Turn ordered email rows into a readable thread (Phase 4).

    Example block per message::
        [Email 1 | 2025-03-10T18:00:00+00:00 | Name <email>]
        Subject: ...
        Body...
    """
    blocks: list[str] = []
    for i, row in enumerate(rows, start=1):
        date_val = row.get("date")
        date_str = (
            date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val or "")
        )
        sender = _sender_display(row.get("from_json"))
        subject = (row.get("subject") or "").strip()
        body = (row.get("body_text") or "").strip()
        lines = [f"[Email {i} | {date_str} | {sender}]"]
        if subject:
            lines.append(f"Subject: {subject}")
        lines.append(body)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_thread_conversation(conn, thread_id: str) -> str:
    """
    Phase 4 thread builder: fetch by `thread_id`, format. Returns \"\" if no rows.
    """
    rows = fetch_emails_for_thread(conn, thread_id)
    if not rows:
        return ""
    return format_thread_conversation(rows)


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


# --- Phase 3 — load index + retrieve ranked threads ---


def load_faiss_local(
    directory: Path,
    embeddings,
    *,
    index_name: str = "inbox_emails",
) -> FAISS:
    """Load a FAISS store built with the same embedding model as `build_fireworks_embeddings`."""
    faiss_path = directory / f"{index_name}.faiss"
    if not faiss_path.is_file():
        raise FileNotFoundError(f"Missing FAISS index: {faiss_path}")
    return FAISS.load_local(
        str(directory),
        embeddings,
        index_name=index_name,
        allow_dangerous_deserialization=True,
    )


def _l2_distance_to_similarity(distance: float) -> float:
    """Map FAISS L2 distance to a higher-is-better score in (0, 1]."""
    if distance < 0:
        distance = 0.0
    return 1.0 / (1.0 + float(distance))


def _parse_iso_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    s = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class ThreadRank:
    """One thread after grouping FAISS hits and applying the Phase 3 ranking."""

    thread_id: str
    best_similarity: float
    hit_count: int
    latest_hit_date: datetime
    best_chunk_text: str
    best_email_id: str


def retrieve_ranked_threads(
    store: FAISS,
    query: str,
    *,
    top_k: int = 8,
    top_threads: int = 2,
) -> list[ThreadRank]:
    """
    Embed `query`, search FAISS for `top_k` chunks, group by `thread_id`, then rank threads by:
    1) best chunk similarity (higher first),
    2) number of chunks hit in the result set (more first),
    3) recency — latest `date` among hits in that thread (newer first).

    Returns up to `top_threads` threads (Phase 3: typically 1–2).
    """
    q = (query or "").strip()
    if not q:
        return []

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if top_threads <= 0:
        raise ValueError("top_threads must be positive")

    # LangChain FAISS: score is L2 distance (lower is closer).
    hits = store.similarity_search_with_score(q, k=top_k)

    # thread_id -> aggregated stats
    agg: dict[str, dict[str, Any]] = {}
    for doc, distance in hits:
        meta = doc.metadata or {}
        tid = str(meta.get("thread_id") or "").strip()
        if not tid:
            continue
        sim = _l2_distance_to_similarity(distance)
        chunk_text = str(meta.get("chunk_text") or doc.page_content or "")
        email_id = str(meta.get("email_id") or "")
        hit_dt = _parse_iso_datetime(str(meta.get("date") or ""))

        if tid not in agg:
            agg[tid] = {
                "best_similarity": sim,
                "hit_count": 0,
                "latest_hit_date": hit_dt,
                "best_chunk_text": chunk_text,
                "best_email_id": email_id,
            }
        a = agg[tid]
        a["hit_count"] += 1
        if hit_dt > a["latest_hit_date"]:
            a["latest_hit_date"] = hit_dt
        if sim > a["best_similarity"]:
            a["best_similarity"] = sim
            a["best_chunk_text"] = chunk_text
            a["best_email_id"] = email_id

    ranked = sorted(
        agg.items(),
        key=lambda item: (
            -item[1]["best_similarity"],
            -item[1]["hit_count"],
            -item[1]["latest_hit_date"].timestamp(),
        ),
    )

    out: list[ThreadRank] = []
    for tid, a in ranked[:top_threads]:
        out.append(
            ThreadRank(
                thread_id=tid,
                best_similarity=float(a["best_similarity"]),
                hit_count=int(a["hit_count"]),
                latest_hit_date=a["latest_hit_date"],
                best_chunk_text=str(a["best_chunk_text"] or ""),
                best_email_id=str(a["best_email_id"] or ""),
            )
        )
    return out
