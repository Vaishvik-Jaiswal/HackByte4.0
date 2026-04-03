#!/usr/bin/env python3
"""
Apply schema migrations (numbered SQL, excluding *seed*).
Loads backend/.env. Requires: pip install -r backend/requirements.txt (inside backend venv).

Usage (from repo root):
  backend/.venv/bin/python backend/scripts/db_migrate.py
Or from backend/ with venv active:
  python scripts/db_migrate.py
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

from db_common import list_migration_files


def main() -> None:
    try:
        import psycopg2
    except ImportError:
        print("Install deps: cd backend && python -m venv .venv && ... pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set. Copy backend/.env.example to backend/.env.", file=sys.stderr)
        sys.exit(1)

    files = list_migration_files()
    if not files:
        print("No migration files found.", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(url)
        with conn.cursor() as cur:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                print(f"Applying {path.name} ...")
                cur.execute(sql)
        conn.commit()
        print("db_migrate: OK.")
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        print(
            "Fix DATABASE_URL in backend/.env (user/password must match your Postgres).\n"
            "  See backend/.env.example — e.g. createdb HackByte, then set DATABASE_URL.",
            file=sys.stderr,
        )
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
