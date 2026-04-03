#!/usr/bin/env python3
"""
Apply seed SQL (*seed*.sql). Run after db_migrate.py.
Loads backend/.env.

Usage (from repo root):
  backend/.venv/bin/python backend/scripts/db_seed.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_BACKEND_ROOT = _SCRIPTS.parent
sys.path.insert(0, str(_SCRIPTS))

from dotenv import load_dotenv

load_dotenv(_BACKEND_ROOT / ".env")

from db_common import list_seed_files


def main() -> None:
    try:
        import psycopg2
    except ImportError:
        print("Install deps: pip install -r backend/requirements.txt (inside backend venv).", file=sys.stderr)
        sys.exit(1)

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    files = list_seed_files()
    if not files:
        print("No seed files (*seed*.sql) found.", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(url)
        with conn.cursor() as cur:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                print(f"Seeding {path.name} ...")
                cur.execute(sql)
        conn.commit()
        print("db_seed: OK.")
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        print("Fix DATABASE_URL in backend/.env — see backend/.env.example.", file=sys.stderr)
        sys.exit(1)
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
