#!/usr/bin/env python3
"""
Phase 2 — Build FAISS index from PostgreSQL emails.
Phase 3 — Smoke-test retrieval: `retrieve "<query>"`.

Loads backend/.env. Build needs FIREWORKS_API_KEY + DATABASE_URL; retrieve needs
FIREWORKS_API_KEY + existing index under data/faiss (default). Phase 4 thread
reconstruction needs DATABASE_URL only.

Usage (from repo root):
  backend/.venv/bin/pip install -r backend/requirements.txt
  backend/.venv/bin/python backend/scripts/embed_pipeline.py
  backend/.venv/bin/python backend/scripts/embed_pipeline.py retrieve "When is my NVIDIA test?"
  backend/.venv/bin/python backend/scripts/embed_pipeline.py thread thread-nvidia-onsite-2025

Or from backend/ with venv active:
  python scripts/embed_pipeline.py
  python scripts/embed_pipeline.py retrieve "reschedule assessment"
  python scripts/embed_pipeline.py thread thread-nvidia-onsite-2025
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_BACKEND_ROOT = _SCRIPTS.parent
sys.path.insert(0, str(_BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(_BACKEND_ROOT / ".env")


def cmd_build() -> None:
    try:
        import psycopg2
    except ImportError:
        print("Install deps: pip install -r backend/requirements.txt", file=sys.stderr)
        sys.exit(1)

    from app.core.config import get_faiss_data_dir
    from app.embedding_index import (
        build_faiss_index,
        build_fireworks_embeddings,
        fetch_all_emails_ordered,
        rows_to_embedding_documents,
        save_faiss_local,
    )

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set in backend/.env.", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(url)
        rows = fetch_all_emails_ordered(conn)
    except Exception as e:
        print(f"Failed to load emails: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()

    if not rows:
        print("No rows in emails table. Run db_migrate.py and db_seed.py first.", file=sys.stderr)
        sys.exit(1)

    documents = rows_to_embedding_documents(rows)
    print(f"Built {len(documents)} chunk documents from {len(rows)} emails.")

    embeddings = build_fireworks_embeddings()
    store = build_faiss_index(documents, embeddings)

    out_dir = get_faiss_data_dir()
    save_faiss_local(store, out_dir, index_name="inbox_emails")
    print(f"Saved FAISS index to {out_dir} (index_name=inbox_emails).")


def cmd_retrieve(query: str) -> None:
    """Phase 3 — load FAISS, run `retrieve_ranked_threads`, print JSON for demo."""
    from app.core.config import (
        RETRIEVAL_TOP_K,
        RETRIEVAL_TOP_THREADS,
        get_faiss_data_dir,
    )
    from app.embedding_index import (
        build_fireworks_embeddings,
        load_faiss_local,
        retrieve_ranked_threads,
    )

    embeddings = build_fireworks_embeddings()
    store = load_faiss_local(get_faiss_data_dir(), embeddings)
    threads = retrieve_ranked_threads(
        store,
        query,
        top_k=RETRIEVAL_TOP_K,
        top_threads=RETRIEVAL_TOP_THREADS,
    )
    payload = [
        {
            "thread_id": t.thread_id,
            "best_similarity": round(t.best_similarity, 6),
            "hit_count": t.hit_count,
            "latest_hit_date": t.latest_hit_date.isoformat(),
            "best_email_id": t.best_email_id,
            "best_chunk_preview": (t.best_chunk_text[:240] + "…")
            if len(t.best_chunk_text) > 240
            else t.best_chunk_text,
        }
        for t in threads
    ]
    print(json.dumps({"query": query, "top_threads": payload}, indent=2))


def cmd_thread(thread_id: str) -> None:
    """Phase 4 — fetch thread from Postgres and print formatted conversation."""
    try:
        import psycopg2
    except ImportError:
        print("Install deps: pip install -r backend/requirements.txt", file=sys.stderr)
        sys.exit(1)

    from app.embedding_index import build_thread_conversation

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set in backend/.env.", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(url)
        text = build_thread_conversation(conn, thread_id)
    except Exception as e:
        print(f"Failed to load thread: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()

    if not text.strip():
        print(f"No emails found for thread_id={thread_id!r}.", file=sys.stderr)
        sys.exit(1)
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS index or run Phase 3 retrieval.")
    sub = parser.add_subparsers(dest="command", required=False)

    sub.add_parser("build", help="Rebuild FAISS from PostgreSQL (default if no subcommand).")

    p_ret = sub.add_parser("retrieve", help="Phase 3: query → FAISS → ranked threads (JSON).")
    p_ret.add_argument("query", nargs="+", help="Natural language question")

    p_thread = sub.add_parser("thread", help="Phase 4: print formatted thread text from Postgres.")
    p_thread.add_argument("thread_id", help="e.g. thread-nvidia-onsite-2025")

    args = parser.parse_args()

    if args.command == "retrieve":
        cmd_retrieve(" ".join(args.query))
        return
    if args.command == "thread":
        cmd_thread(args.thread_id)
        return

    # Default and explicit `build`
    cmd_build()


if __name__ == "__main__":
    main()
