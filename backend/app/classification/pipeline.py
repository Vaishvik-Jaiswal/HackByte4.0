"""Run Groq agents on unprocessed inbox rows and persist `processed_emails`."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.classification.agents import (
    classify_email,
    generate_reply,
    summarize_email,
    suggest_tone,
)
from app.classification.groq_client import groq_configured
from app.classification.past_emails import fetch_recent_sent_bodies
from app.models.email import Email
from app.models.processed_email import ProcessedEmail

logger = logging.getLogger(__name__)


@dataclass
class InboxAIResult:
    category: str
    summary: str
    tone: str
    tone_reason: str
    suggested_reply: str


def _run_inbox_pipeline_sync(body: str, past_sent_bodies: list[str]) -> InboxAIResult:
    """Blocking Groq calls — invoked via asyncio.to_thread."""
    category = classify_email(body)
    summary = summarize_email(body)
    tone_data = suggest_tone(past_sent_bodies, body, summary)
    tone = tone_data.get("suggested_tone") or "professional"
    tone_reason = tone_data.get("reason") or ""
    suggested_reply = generate_reply(category, summary, tone)
    return InboxAIResult(
        category=category,
        summary=summary,
        tone=tone,
        tone_reason=tone_reason,
        suggested_reply=suggested_reply,
    )


async def process_pending_emails_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    """
    For the given user: mark sent mail as processed without AI.
    For inbox mail: classify, summarize, tone + reason, suggested reply → `processed_emails`.
    """
    if not groq_configured():
        logger.warning("GROQ_API_KEY missing — skipping AI email processing")
        return {"status": "skipped", "reason": "groq_not_configured", "inbox_processed": 0}

    # IS NOT TRUE matches false and null (legacy rows) so nothing is stuck unprocessed.
    q = (
        select(Email)
        .where(Email.user_id == user_id, Email.is_processed.is_not(True))
        .order_by(Email.id.asc())
    )
    result = await db.execute(q)
    pending = result.scalars().all()
    logger.info(
        "Email AI: %d pending row(s) for user (is_processed is not true)",
        len(pending),
    )

    inbox_done = 0
    sent_done = 0

    for email in pending:
        if not email.is_inbox:
            email.is_processed = True
            sent_done += 1
            await db.commit()
            continue

        body = (email.body_text or "").strip()
        past = await fetch_recent_sent_bodies(db, user_id, limit=8)

        try:
            ai = await asyncio.to_thread(_run_inbox_pipeline_sync, body, past)
        except Exception:
            logger.exception("AI pipeline failed for email id=%s", email.id)
            await db.rollback()
            raise

        db.add(
            ProcessedEmail(
                email_id=email.id,
                user_id=user_id,
                thread_id=email.thread_id,
                category=ai.category,
                summary=ai.summary,
                tone=ai.tone,
                tone_reason=ai.tone_reason,
                suggested_reply=ai.suggested_reply,
            )
        )
        email.is_processed = True
        await db.commit()
        inbox_done += 1

    return {
        "status": "ok",
        "inbox_processed": inbox_done,
        "sent_marked_processed": sent_done,
    }
