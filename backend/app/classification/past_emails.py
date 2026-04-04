"""Load recent user-authored sent mail bodies for tone conditioning."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email


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
