"""Shared paths and file listing for SQL migrations vs seeds."""

from __future__ import annotations

import re
from pathlib import Path

# This file lives in backend/scripts/ — backend root is one level up.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = BACKEND_ROOT / "db" / "migrations"

_MIGRATION_NAME = re.compile(r"^\d{3}_.+\.sql$", re.IGNORECASE)


def list_migration_files() -> list[Path]:
    """Numbered *.sql files, excluding *seed* (schema-only migrations)."""
    if not MIGRATIONS_DIR.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(MIGRATIONS_DIR.iterdir()):
        if not p.is_file():
            continue
        if not _MIGRATION_NAME.match(p.name):
            continue
        if "seed" in p.name.lower():
            continue
        out.append(p)
    return out


def list_seed_files() -> list[Path]:
    """*seed*.sql files in migrations folder."""
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted(
        p
        for p in MIGRATIONS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() == ".sql" and "seed" in p.name.lower()
    )
