"""
Phase 2 — Postgres → chunk → Fireworks embeddings → FAISS save.

Phase 3 — load FAISS, query → embedding → top-K chunk search → group by thread_id
→ rank threads (similarity, hit count, recency) → top 1–2 threads.

Phase 4 — given thread_id: load all emails from Postgres (date ASC), format as a
readable conversation string for LLM / display.

Phase 5 — Grounded LLM answer via Groq OpenAI-compatible API (``openai`` client). Returns ``LLMAnswer``.

Phase 6 — FastAPI ``POST /ask``: query → FAISS → thread → LLM JSON.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, Field, model_validator

import tiktoken
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_fireworks import FireworksEmbeddings
from psycopg2.extras import RealDictCursor

from app.core.config import (
    CHUNK_OVERLAP_TOKENS,
    CHUNK_SIZE_TOKENS,
    RETRIEVAL_TOP_K,
    RETRIEVAL_TOP_THREADS,
    get_faiss_data_dir,
    get_fireworks_api_key,
    get_fireworks_embedding_model,
    get_llm_api_key,
    get_llm_base_url,
    get_llm_model,
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


# --- Phase 5 — LLM: grounded answer from formatted thread ---


ANSWER_SYSTEM_PROMPT = """You are Inbox Copilot. You receive a USER QUESTION and an EMAIL THREAD. The thread is the ONLY source of facts.

Rules:
1. Use ONLY text that appears in the EMAIL THREAD. Do not use outside knowledge, URLs you invent, or assumptions.
2. If scheduling or details change across emails, trust the LATEST email (by date shown in the thread) over older ones.
3. If the thread does not contain enough information to answer, say so plainly in "answer" and set "confidence" low (e.g. 0.2–0.4).
4. "supporting_email" MUST be an exact contiguous quote copied from the EMAIL THREAD (from Subject line or body as written). If nothing fits, use an empty string "".
5. Respond with valid JSON only: one object, no markdown fences, no text before or after.

Required JSON shape (all keys required):
{
  "answer": "<string>",
  "supporting_email": "<string>",
  "summary": "<one short sentence>",
  "confidence": <number from 0.0 to 1.0>
}
"""


@dataclass(frozen=True)
class LLMAnswer:
    """Structured LLM output for Phase 5 (and later /ask API)."""

    answer: str
    supporting_email: str
    summary: str
    confidence: float


def build_answer_user_message(user_query: str, thread_text: str) -> str:
    """User message body: question + thread text for the chat completion."""
    q = (user_query or "").strip()
    t = (thread_text or "").strip()
    return (
        "USER QUESTION:\n"
        f"{q}\n\n"
        "EMAIL THREAD (sole source; messages are ordered oldest → newest):\n"
        f"{t}"
    )


def _strip_json_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _parse_llm_answer_json(content: str) -> LLMAnswer:
    """Parse model JSON; tolerate minor issues and clamp confidence."""
    text = _strip_json_fence(content)
    if not text:
        return LLMAnswer(
            answer="",
            supporting_email="",
            summary="Empty model response.",
            confidence=0.0,
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return LLMAnswer(
            answer=text[:2000],
            supporting_email="",
            summary="Could not parse JSON from the model.",
            confidence=0.0,
        )
    if not isinstance(data, dict):
        return LLMAnswer(
            answer=str(data)[:2000],
            supporting_email="",
            summary="Model returned non-object JSON.",
            confidence=0.0,
        )

    def _s(key: str, default: str = "") -> str:
        v = data.get(key)
        if v is None:
            return default
        return str(v).strip() if isinstance(v, str) else str(v)

    conf_raw = data.get("confidence", 0.0)
    try:
        c = float(conf_raw)
    except (TypeError, ValueError):
        c = 0.0
    c = max(0.0, min(1.0, c))

    return LLMAnswer(
        answer=_s("answer"),
        supporting_email=_s("supporting_email"),
        summary=_s("summary") or _s("answer")[:200],
        confidence=c,
    )


def _generate_answer_groq(
    user_query: str,
    thread_text: str,
    *,
    temperature: float,
) -> LLMAnswer:
    """Chat Completions on Groq (OpenAI-compatible)."""
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("Install openai: pip install openai") from e

    api_key = get_llm_api_key()
    if not api_key:
        raise RuntimeError(
            "Set GROQ_API_KEY for Phase 5 (https://console.groq.com)."
        )

    t = (thread_text or "").strip()
    if not t:
        return LLMAnswer(
            answer="No email thread was provided.",
            supporting_email="",
            summary="Missing thread context.",
            confidence=0.0,
        )

    client = OpenAI(api_key=api_key, base_url=get_llm_base_url())
    user_content = build_answer_user_message(user_query, t)

    messages = [
        {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    model = get_llm_model()

    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        response_format={"type": "json_object"},
    )

    raw = ""
    if completion.choices:
        raw = completion.choices[0].message.content or ""
    return _parse_llm_answer_json(raw)


def generate_answer_from_thread(
    user_query: str,
    thread_text: str,
    *,
    temperature: float = 0.2,
) -> LLMAnswer:
    """
    Grounded JSON ``LLMAnswer`` from the email thread.

    Requires ``GROQ_API_KEY``. Optional: ``GROQ_BASE_URL`` (default Groq OpenAI-compatible
    base), ``LLM_MODEL`` / ``GROQ_MODEL`` (default ``llama-3.3-70b-versatile``).
    """
    return _generate_answer_groq(user_query, thread_text, temperature=temperature)


# --- Phase 6 — full pipeline + FastAPI ---

_cached_faiss_store: FAISS | None = None


def get_faiss_store_cached() -> FAISS:
    """Lazy-load FAISS + embeddings (shared by CLI ``ask`` and ``POST /ask``)."""
    global _cached_faiss_store
    if _cached_faiss_store is None:
        emb = build_fireworks_embeddings()
        _cached_faiss_store = load_faiss_local(get_faiss_data_dir(), emb)
    return _cached_faiss_store


def run_ask_pipeline(
    query: str,
    *,
    store: FAISS | None = None,
    top_k: int | None = None,
    top_threads: int | None = None,
) -> dict[str, Any]:
    """
    Retrieval → Postgres thread → grounded LLM answer. Raises:
    ``ValueError`` (empty query), ``LookupError`` (no retrieval hits),
    ``RuntimeError`` (missing ``DATABASE_URL``, empty thread text, missing LLM key).
    """
    try:
        import psycopg2
    except ImportError as e:
        raise RuntimeError("Install psycopg2-binary: pip install psycopg2-binary") from e

    q = (query or "").strip()
    if not q:
        raise ValueError("query must not be empty")

    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set (e.g. in backend/.env).")

    k = RETRIEVAL_TOP_K if top_k is None else top_k
    nt = RETRIEVAL_TOP_THREADS if top_threads is None else top_threads

    faiss_store = store if store is not None else get_faiss_store_cached()
    threads = retrieve_ranked_threads(faiss_store, q, top_k=k, top_threads=nt)
    if not threads:
        raise LookupError("No matching threads from retrieval.")

    top = threads[0]
    conn = psycopg2.connect(url)
    try:
        thread_text = build_thread_conversation(conn, top.thread_id)
    finally:
        conn.close()

    if not (thread_text or "").strip():
        raise RuntimeError(f"Thread text empty for thread_id={top.thread_id!r}")

    llm = generate_answer_from_thread(q, thread_text)

    return {
        "query": q,
        "thread_id": top.thread_id,
        "retrieval": {
            "best_similarity": round(top.best_similarity, 6),
            "hit_count": top.hit_count,
            "threads": [
                {
                    "thread_id": t.thread_id,
                    "best_similarity": round(t.best_similarity, 6),
                    "hit_count": t.hit_count,
                }
                for t in threads
            ],
        },
        "answer": {
            "answer": llm.answer,
            "supporting_email": llm.supporting_email,
            "summary": llm.summary,
            "confidence": llm.confidence,
        },
    }


def _email_row_to_api_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Serialize one DB row for GET /threads (Phase 7–8 UI timeline)."""
    d = row.get("date")
    date_str = d.isoformat() if hasattr(d, "isoformat") else str(d or "")
    return {
        "id": int(row["id"]),
        "thread_id": str(row.get("thread_id") or ""),
        "gmail_msg_id": str(row.get("gmail_msg_id") or ""),
        "from_json": row.get("from_json"),
        "to_json": row.get("to_json"),
        "subject": str(row.get("subject") or ""),
        "body_text": str(row.get("body_text") or ""),
        "date": date_str,
        "sender_display": _sender_display(row.get("from_json")),
    }


def fetch_thread_api_payload(thread_id: str) -> dict[str, Any]:
    """
    Load all emails for ``thread_id`` (date ASC). Returns ``{"thread_id", "emails"}``.
    Raises ``ValueError`` if ``thread_id`` empty; ``RuntimeError`` if DB URL missing.
    """
    try:
        import psycopg2
    except ImportError as e:
        raise RuntimeError("Install psycopg2-binary: pip install psycopg2-binary") from e

    tid = (thread_id or "").strip()
    if not tid:
        raise ValueError("thread_id must not be empty")

    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set (e.g. in backend/.env).")

    conn = psycopg2.connect(url)
    try:
        rows = fetch_emails_for_thread(conn, tid)
    finally:
        conn.close()

    return {
        "thread_id": tid,
        "emails": [_email_row_to_api_dict(r) for r in rows],
    }


# --- Phase 6 — API models (module-level: nested classes break FastAPI /openapi.json) ---


class AskBody(BaseModel):
    """
    POST /ask JSON body. Send ``{"question": "..."}``. A legacy key ``query`` is
    merged in ``mode='before'`` so ``{"query": "..."}`` still works without a
    ``query`` field in the OpenAPI schema (avoids ambiguity with query params).
    """

    question: str = Field(..., min_length=1, description="Question about your emails")

    @model_validator(mode="before")
    @classmethod
    def _merge_query_alias(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        def _s(val: Any) -> str:
            if val is None:
                return ""
            return str(val).strip()

        q_text = _s(data.get("question"))
        legacy_text = _s(data.get("query"))
        merged = q_text or legacy_text
        if merged:
            return {"question": merged}
        return data


class AnswerOut(BaseModel):
    answer: str
    supporting_email: str
    summary: str
    confidence: float


class RetrievalThreadOut(BaseModel):
    thread_id: str
    best_similarity: float
    hit_count: int


class RetrievalOut(BaseModel):
    best_similarity: float
    hit_count: int
    threads: list[RetrievalThreadOut]


class AskResponseOut(BaseModel):
    query: str
    thread_id: str
    retrieval: RetrievalOut
    answer: AnswerOut


class EmailThreadRowOut(BaseModel):
    """One message in a thread (for timeline / source grounding UI)."""

    id: int
    thread_id: str
    gmail_msg_id: str
    from_json: Any
    to_json: Any
    subject: str
    body_text: str
    date: str
    sender_display: str


class ThreadDetailOut(BaseModel):
    thread_id: str
    emails: list[EmailThreadRowOut]


class HealthOut(BaseModel):
    status: str
    database_configured: bool
    fireworks_configured: bool
    llm_configured: bool


def _create_app() -> Any:
    """Build FastAPI app (import fastapi lazily for clearer optional-deps errors)."""
    from contextlib import asynccontextmanager

    from dotenv import load_dotenv
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    @asynccontextmanager
    async def lifespan(_app: Any):
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)
        yield

    api = FastAPI(
        title="Inbox Copilot API",
        version="0.1.0",
        lifespan=lifespan,
    )
    _origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
    api.add_middleware(
        CORSMiddleware,
        allow_origins=_origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/health", response_model=HealthOut)
    def health() -> HealthOut:
        db_ok = bool((os.environ.get("DATABASE_URL") or "").strip())
        llm_ok = bool(get_llm_api_key())
        fw_ok = bool(get_fireworks_api_key())
        return HealthOut(
            status="ok",
            database_configured=db_ok,
            fireworks_configured=fw_ok,
            llm_configured=llm_ok,
        )

    @api.post("/ask", response_model=AskResponseOut)
    def ask(payload: AskBody) -> AskResponseOut:
        try:
            raw = run_ask_pipeline(payload.question.strip())
            return AskResponseOut.model_validate(raw)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=503,
                detail="FAISS index missing. Build it with embed_pipeline.py build.",
            ) from e
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {e!s}",
            ) from e

    @api.get("/threads/{thread_id}", response_model=ThreadDetailOut)
    def get_thread(thread_id: str) -> ThreadDetailOut:
        """Phase 7–8: full thread for timeline / grounding UI."""
        try:
            raw = fetch_thread_api_payload(thread_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        if not raw.get("emails"):
            raise HTTPException(
                status_code=404,
                detail="Thread not found or has no emails.",
            )
        return ThreadDetailOut.model_validate(raw)

    return api


app = _create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "app.embedding_index:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=port,
        reload=True,
    )
