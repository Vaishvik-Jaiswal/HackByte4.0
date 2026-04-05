from app.classification.groq_client import get_groq_client
from app.classification.past_emails import format_sent_bodies_for_prompt
from app.core.config import settings


def suggest_tone(past_emails: list[str], incoming_email: str, summary: str) -> dict:
    """
    Suggests reply tone based on the user's past sent-mail style and the incoming message.
    Returns dict with 'suggested_tone' and 'reason'.
    """
    client = get_groq_client()
    past_emails_text = format_sent_bodies_for_prompt(past_emails)

    prompt = f"""
You are a Tone Intelligence Agent in an AI email system.

Your job is to understand the user's writing style from past emails and suggest an appropriate tone for replying to a new email.

---

## INPUT:

PAST USER EMAILS (for style understanding):
{past_emails_text}

INCOMING EMAIL:
{incoming_email}

EMAIL SUMMARY:
{summary}

---

## TASK:

1. Carefully observe the past emails to understand the user's natural tone, including:
   * level of formality
   * sentence structure
   * politeness
   * directness
   * emotional style

2. Analyze the incoming email and its context.

3. Suggest a reply tone that:
   * aligns with the user's natural writing style
   * fits the context of the incoming email
   * improves clarity and effectiveness

---

## OUTPUT:

Tone: <short phrase like "professional and friendly", "concise and direct", etc.>

Reason: <1–2 lines explaining why this tone fits>

---
"""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    output = response.choices[0].message.content.strip()

    lines = [line.strip() for line in output.split("\n") if line.strip()]
    suggested_tone = ""
    reason = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Tone:") or line.startswith("## Tone:"):
            tone_part = line.replace("Tone:", "").replace("## Tone:", "").strip()
            if tone_part:
                suggested_tone = tone_part
            elif i + 1 < len(lines):
                suggested_tone = lines[i + 1]
            i += 1
        elif line.startswith("Reason:") or line.startswith("## Reason:"):
            reason_part = line.replace("Reason:", "").replace("## Reason:", "").strip()
            if reason_part:
                reason = reason_part
            elif i + 1 < len(lines):
                reason = lines[i + 1]
            i += 1
        i += 1

    if not suggested_tone:
        suggested_tone = "professional and friendly"
    if not reason:
        reason = "Default fallback tone for professional communication."

    return {"suggested_tone": suggested_tone, "reason": reason}
