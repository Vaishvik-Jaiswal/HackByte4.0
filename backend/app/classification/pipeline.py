"""Run Groq agents on unprocessed inbox rows and persist `processed_emails`."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.classification.agents import (
    classify_email,
    generate_reply,
    summarize_email,
    suggest_tone,
)
from app.classification.agents.context_mapping import (
    extract_briefing_from_email,
    format_relay_prompt_block,
    select_matching_relay_context,
)
from app.classification.groq_client import groq_configured
from app.classification.past_emails import fetch_recent_sent_bodies
from app.classification.reply_policy import compute_reply_needed
from app.models.email import Email
from app.models.processed_email import ProcessedEmail
from app.models.relay_context import RelayContext

logger = logging.getLogger(__name__)


@dataclass
class InboxAIResult:
    category: str
    summary: str
    tone: str
    tone_reason: str
    reply_needed: bool
    suggested_reply: str | None
    relay_applied: bool


def _classify_summarize_tone_sync(
    body: str, past_sent_bodies: list[str]
) -> tuple[str, str, str, str, bool]:
    """Classification + summary + tone + whether a reply is generally needed."""
    category = classify_email(body)
    summary = summarize_email(body)
    tone_data = suggest_tone(past_sent_bodies, body, summary)
    tone = tone_data.get("suggested_tone") or "professional"
    tone_reason = tone_data.get("reason") or ""
    reply_needed = compute_reply_needed(category, summary)
    return category, summary, tone, tone_reason, reply_needed


def _generate_reply_with_relay_sync(
    category: str,
    summary: str,
    tone: str,
    past_sent_bodies: list[str],
    reply_needed: bool,
    relay_block: str | None,
) -> str | None:
    if not reply_needed:
        return None
    return generate_reply(
        category,
        summary,
        tone,
        past_sent_bodies,
        relay_context=relay_block,
    )


async def _active_relay_contexts_for_matching(
    db: AsyncSession, user_id: uuid.UUID, current_email_id: int
) -> list[RelayContext]:
    """Prior briefings only — exclude the current message so we never match a mail to its own briefing."""
    q = (
        select(RelayContext)
        .where(
            RelayContext.user_id == user_id,
            RelayContext.status == "active",
        )
        .order_by(desc(RelayContext.created_at))
        .limit(20)
    )
    result = await db.execute(q)
    rows = list(result.scalars().all())
    return [r for r in rows if r.source_email_id != current_email_id]


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
            # 1) If this mail is a "briefing" (e.g. manager: client will ask about X — tell them Y), store it.
            try:
                briefing = None
                if len(body) >= 40:
                    briefing = await asyncio.to_thread(
                        extract_briefing_from_email, body, email.subject
                    )
                if (
                    briefing
                    and briefing.is_briefing
                    and briefing.topic
                    and briefing.tell_them
                ):
                    db.add(
                        RelayContext(
                            user_id=user_id,
                            source_email_id=email.id,
                            topic=briefing.topic,
                            relay_instruction=briefing.tell_them,
                            status="active",
                        )
                    )
                    await db.flush()
            except Exception:
                logger.exception("Briefing extraction failed for email id=%s", email.id)

            category, summary, tone, tone_reason, reply_needed = await asyncio.to_thread(
                _classify_summarize_tone_sync, body, past
            )

            relay_block: str | None = None
            if reply_needed:
                ctx_rows = await _active_relay_contexts_for_matching(
                    db, user_id, email.id
                )
                stored = [(c.id, c.topic, c.relay_instruction) for c in ctx_rows]
                if stored:
                    try:
                        match_id = await asyncio.to_thread(
                            select_matching_relay_context,
                            stored,
                            body,
                            summary,
                        )
                        if match_id is not None:
                            matched = next(
                                (c for c in ctx_rows if c.id == match_id), None
                            )
                            if matched:
                                relay_block = format_relay_prompt_block(
                                    matched.topic, matched.relay_instruction
                                )
                    except Exception:
                        logger.exception(
                            "Relay context matching failed for email id=%s", email.id
                        )

            suggested_reply = await asyncio.to_thread(
                _generate_reply_with_relay_sync,
                category,
                summary,
                tone,
                past,
                reply_needed,
                relay_block,
            )

            ai = InboxAIResult(
                category=category,
                summary=summary,
                tone=tone,
                tone_reason=tone_reason,
                reply_needed=reply_needed,
                suggested_reply=suggested_reply,
                relay_applied=bool(relay_block),
            )
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
                reply_needed=ai.reply_needed,
                suggested_reply=ai.suggested_reply,
                relay_applied=ai.relay_applied,
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
