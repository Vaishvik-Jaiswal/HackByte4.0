"""
Bring legacy `processed_emails` tables in line with current SQLAlchemy models.

`Base.metadata.create_all()` only creates missing tables; it does not add new columns.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)


async def patch_processed_emails_postgres(conn: AsyncConnection) -> None:
    """Add missing columns on PostgreSQL (idempotent)."""
    await conn.execute(
        text(
            """
DO $patch$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'processed_emails'
  ) THEN
    RETURN;
  END IF;

  -- user_id (required for current app code)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'user_id'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN user_id UUID REFERENCES users(id);
    UPDATE processed_emails pe
    SET user_id = e.user_id
    FROM emails e
    WHERE pe.email_id = e.id;
    DELETE FROM processed_emails WHERE user_id IS NULL;
    ALTER TABLE processed_emails ALTER COLUMN user_id SET NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_processed_emails_user_id ON processed_emails (user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'thread_id'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN thread_id VARCHAR;
    UPDATE processed_emails pe SET thread_id = e.thread_id FROM emails e WHERE pe.email_id = e.id;
    UPDATE processed_emails SET thread_id = '' WHERE thread_id IS NULL;
    ALTER TABLE processed_emails ALTER COLUMN thread_id SET NOT NULL;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'category'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN category VARCHAR;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'summary'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN summary TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'tone'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN tone VARCHAR;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'tone_reason'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN tone_reason TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'suggested_reply'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN suggested_reply TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'reply_needed'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN reply_needed BOOLEAN NOT NULL DEFAULT true;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'processed_emails' AND column_name = 'relay_applied'
  ) THEN
    ALTER TABLE processed_emails ADD COLUMN relay_applied BOOLEAN NOT NULL DEFAULT false;
  END IF;
END
$patch$;
"""
        )
    )
    logger.info("Schema patch applied: processed_emails columns verified.")
