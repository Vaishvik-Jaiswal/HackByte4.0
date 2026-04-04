#!/usr/bin/env python3
"""
Phase 2 — Build FAISS index from PostgreSQL emails.

Loads backend/.env. Requires FIREWORKS_API_KEY and DATABASE_URL.

Usage (from repo root):
  backend/.venv/bin/pip install -r backend/requirements.txt
  backend/.venv/bin/python backend/scripts/embed_pipeline.py

Or from backend/ with venv active:
  python scripts/embed_pipeline.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_BACKEND_ROOT = _SCRIPTS.parent
sys.path.insert(0, str(_BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(_BACKEND_ROOT / ".env")


def main() -> None:
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


if __name__ == "__main__":
    main()
