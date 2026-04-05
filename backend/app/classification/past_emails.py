"""Load recent user-authored sent mail bodies for tone conditioning."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email


def format_sent_bodies_for_prompt(
    bodies: list[str],
    *,
    empty_message: str = (
        "(No prior sent emails in database yet — use a balanced professional tone.)"
    ),
) -> str:
    """Format stored sent-mail bodies for LLM prompts (tone + reply style)."""
    cleaned = [b.strip() for b in bodies if b and str(b).strip()]
    if not cleaned:
        return empty_message
    return "\n\n".join(
        f"<EMAIL_{i + 1}>\n{text}" for i, text in enumerate(cleaned)
    )


async def fetch_recent_sent_bodies(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 8
) -> list[str]:
    q = (
        select(Email.body_text)
        .where(Email.user_id == user_id, Email.is_inbox.is_(False))
        .order_by(Email.date.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.scalars().all()
    out: list[str] = []
    for body in rows:
        if body and str(body).strip():
            out.append(str(body).strip())
    return out
