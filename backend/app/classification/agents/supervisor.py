"""Draft a suggested reply from classification outputs (Groq)."""

from app.classification.groq_client import get_groq_client
from app.classification.past_emails import format_sent_bodies_for_prompt
from app.core.config import settings


def generate_reply(
    category: str,
    summary: str,
    tone: str,
    past_sent_bodies: list[str],
    *,
    relay_context: str | None = None,
) -> str:
    """Return a draft reply that mirrors the user's sent-mail style when samples exist."""
    client = get_groq_client()
    style_samples = format_sent_bodies_for_prompt(
        past_sent_bodies,
        empty_message=(
            "(No prior sent emails — match the stated tone with clear, professional prose.)"
        ),
    )
    relay_section = ""
    if relay_context:
        relay_section = f"""
## Prior briefing you must honor (from an earlier message in your inbox)
Someone (e.g. a manager or teammate) asked you to handle a future conversation. When the current email matches that situation, naturally weave in these points — do not ignore them.
{relay_context}

"""
    prompt = f"""
You draft email replies on behalf of the user. Write ONLY the body text (no Subject line, no markdown fences).

## User's past sent emails (match this person's voice — greeting/sign-off habits, formality, length, punctuation, and phrasing):
{style_samples}
{relay_section}
## Incoming message context
- Category: {category}
- Summary: {summary}
- Target tone label (refine wording but stay faithful to the samples above): {tone}

## Rules
1. Primary goal: the reply must read as if the same person who wrote the samples wrote it. Reuse their patterns (e.g. "Hi" vs "Hello", "Thanks" vs "Thank you", closing line style).
2. If samples are missing, fall back to the tone label and a concise professional reply.
3. If a prior briefing is provided and applies to this message, include those talking points clearly and politely — merged into the reply, not as a bullet list of orders unless that matches the user's usual style.
4. Stay concise and actionable. For spam or nonsense, give a brief polite dismissal or a note that no reply is needed.

Suggested reply body:
"""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
