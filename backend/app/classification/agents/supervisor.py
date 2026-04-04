"""Draft a suggested reply from classification outputs (Groq)."""

from app.classification.groq_client import get_groq_client
from app.core.config import settings


def generate_reply(category: str, summary: str, tone: str) -> str:
    """Return a short draft reply appropriate for the category and tone."""
    client = get_groq_client()
    prompt = f"""
You draft email replies for the user. Write ONLY the body text of a suggested reply (no subject line).

- Category: {category}
- Summary of what the incoming email is about: {summary}
- Desired tone: {tone}

Keep it concise and actionable. If a reply doesn't make sense (e.g. pure spam), give a brief polite dismissal or no-reply note.

Suggested reply:
"""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
