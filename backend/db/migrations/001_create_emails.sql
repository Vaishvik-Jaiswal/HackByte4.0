-- Inbox Copilot — Phase 1: emails table
-- Run against your PostgreSQL database (e.g. psql or migration runner).

CREATE TABLE IF NOT EXISTS emails (
    id BIGSERIAL PRIMARY KEY,
    thread_id TEXT NOT NULL,
    gmail_msg_id TEXT NOT NULL,
    from_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    to_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    subject TEXT NOT NULL DEFAULT '',
    body_text TEXT NOT NULL DEFAULT '',
    date TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails (thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_date ON emails (date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_emails_gmail_msg_id ON emails (gmail_msg_id);

COMMENT ON TABLE emails IS 'Email messages for Inbox Copilot retrieval and threading';
