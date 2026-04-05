"""Extract manager-style briefings and match later mail to stored relay instructions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.classification.groq_client import get_groq_client
from app.core.config import settings


@dataclass
class BriefingExtraction:
    is_briefing: bool
    topic: str | None
    tell_them: str | None


def _parse_json_obj(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None
    return None


def extract_briefing_from_email(body: str, subject: str | None) -> BriefingExtraction:
    """
    Detect emails that instruct the user about a future contact and what to say/do
    (e.g. client will reach out about pricing — tell them we're flexible on terms).
    """
    client = get_groq_client()
    subj = (subject or "").strip()
    prompt = f"""Analyze the email. Does it tell the recipient about someone ELSE who will contact them later,
and what the recipient should say or do when that happens? Examples:
- "The client will email you about the contract — tell them we can extend the deadline."
- "When they reach out about invoices, mention we already sent the PDF."

If YES, extract:
- topic: a short label for what the future conversation will be about (the reason/subject).
- tell_them: the concrete points to convey, offer, or remember (quotes/intent), not generic advice.

If NO (normal request, FYI, no future third-party contact briefing), set is_briefing false.

Return ONLY valid JSON:
{{"is_briefing": true/false, "topic": string or null, "tell_them": string or null}}

Subject: {subj}

Email body:
\"\"\"
{body}
\"\"\"
"""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    data = _parse_json_obj(raw) or {}
    if not data.get("is_briefing"):
        return BriefingExtraction(False, None, None)
    topic = (data.get("topic") or "").strip() or None
    tell = (data.get("tell_them") or "").strip() or None
    if not topic or not tell:
        return BriefingExtraction(False, None, None)
    return BriefingExtraction(True, topic, tell)


def _significant_terms(text: str) -> list[str]:
    """Lowercase tokens (letters/digits) long enough to anchor a topic; drop very common fillers."""
    stop = frozenset(
        "the and for that this with from your you will they them when about what "
        "have been were are was out our can may not but how all any get got just "
        "also like want need know time week days soon today please team hello hi "
        "thanks thank email message mail following update question meeting call "
        "quick touch base reach write hope well regards best".split()
    )
    raw = re.findall(r"[a-z0-9][a-z0-9]+", (text or "").lower())
    return [t for t in raw if len(t) >= 4 and t not in stop]


def _incoming_covers_briefing_topic(topic: str, incoming_body: str, incoming_summary: str) -> bool:
    """
    Hard gate: the incoming text must mention enough of the briefing *topic* wording.
    Stops the model from attaching one stale briefing to unrelated mail.
    """
    terms = _significant_terms(topic)
    if not terms:
        terms = [t for t in re.findall(r"[a-z0-9]{3,}", (topic or "").lower()) if len(t) >= 3]
    if not terms:
        return False

    hay = f"{incoming_summary} {incoming_body}".lower()
    hits = sum(1 for t in terms if t in hay)
    # One strong term is enough for a short topic; more terms → need stronger overlap.
    if len(terms) <= 2:
        return hits >= 1
    return hits >= max(2, (len(terms) + 1) // 2)


def select_matching_relay_context(
    stored: list[tuple[int, str, str]],
    incoming_body: str,
    incoming_summary: str,
) -> int | None:
    """
    `stored` is list of (id, topic, relay_instruction).
    Returns the id of the best match only when confidence is high and text supports the topic.
    """
    if not stored:
        return None
    client = get_groq_client()
    lines = []
    for rid, topic, instr in stored:
        lines.append(f"ID {rid} — Topic: {topic}\nWhat to relay: {instr}")
    catalog = "\n\n".join(lines)
    prompt = f"""You decide whether the INCOMING email is actually about ONE of the stored briefings.

STORED BRIEFINGS:
{catalog}

INCOMING EMAIL SUMMARY:
{incoming_summary}

INCOMING EMAIL (excerpt):
\"\"\"
{incoming_body[:6000]}
\"\"\"

Critical rules:
- **Default is NO match.** Return match_id null unless the incoming message is *unambiguously* about the same matter as exactly one stored topic (same concrete subject: same project, same question, same thread of business).
- If there is only one stored briefing but this email is about something else (different person, different project, social chat, admin, unrelated question), you MUST return null. **Do not pick the only briefing out of convenience.**
- Generic emails ("hi", "thanks", "following up", "quick question" with no shared specifics) MUST NOT match.
- **match_confidence** must be exactly "high" only when you would bet the user expects this briefing applied; otherwise use "none" and match_id null.

Return ONLY valid JSON:
{{"match_id": <integer or null>, "match_confidence": "high" or "none", "reason": "<one short phrase>"}}
"""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    data = _parse_json_obj(raw) or {}
    conf = (data.get("match_confidence") or data.get("confidence") or "").strip().lower()
    if conf != "high":
        return None

    mid = data.get("match_id")
    if mid is None:
        return None
    if isinstance(mid, str):
        s = mid.strip().lower()
        if s in ("null", "none", ""):
            return None
    try:
        mid = int(mid)
    except (TypeError, ValueError):
        return None
    valid_ids = {s[0] for s in stored}
    if mid not in valid_ids:
        return None

    topic_for_row = next((t for i, t, _ in stored if i == mid), "")
    if not _incoming_covers_briefing_topic(topic_for_row, incoming_body, incoming_summary):
        return None
    return mid


def format_relay_prompt_block(topic: str, relay_instruction: str) -> str:
    return (
        f"Topic (what the contact is about): {topic}\n"
        f"Points to convey (from an earlier message you received): {relay_instruction}"
    )
