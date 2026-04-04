from app.agents.tone_agent import suggest_tone
from data.past_emails import past_user_emails

# Test the raw response
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

past_emails_text = "\n\n".join([f"<EMAIL_{i+1}>\n{email}" for i, email in enumerate(past_user_emails)])

prompt = f"""
You are a Tone Intelligence Agent in an AI email system.

Your job is to understand the user's writing style from past emails and suggest an appropriate tone for replying to a new email.

---

## INPUT:

PAST USER EMAILS (for style understanding):
{past_emails_text}

INCOMING EMAIL:
Can we reschedule the meeting to tomorrow at 3 PM?

EMAIL SUMMARY:
The sender is requesting to reschedule a meeting to the next day at 3 PM.

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

Suggested Tone:
<short phrase like "professional and friendly", "concise and direct", etc.>

Reason:
<1–2 lines explaining why this tone fits>

---
"""

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)

from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

past_emails_text = "\n\n".join([f"<EMAIL_{i+1}>\n{email}" for i, email in enumerate(past_user_emails)])

prompt = f"""
You are a Tone Intelligence Agent in an AI email system.

Your job is to understand the user's writing style from past emails and suggest an appropriate tone for replying to a new email.

---

## INPUT:

PAST USER EMAILS (for style understanding):
{past_emails_text}

INCOMING EMAIL:
Can we reschedule the meeting to tomorrow at 3 PM?

EMAIL SUMMARY:
The sender is requesting to reschedule a meeting to the next day at 3 PM.

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
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)

output = response.choices[0].message.content.strip()
print("Raw output:")
print(repr(output))

# Parse
lines = [line.strip() for line in output.split('\n') if line.strip()]
suggested_tone = ""
reason = ""

i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith("Tone:") or line.startswith("## Tone:"):
        # Take the rest of the line after the colon
        tone_part = line.replace("Tone:", "").replace("## Tone:", "").strip()
        if tone_part:
            suggested_tone = tone_part
        elif i + 1 < len(lines):
            suggested_tone = lines[i + 1]
        i += 1
    elif line.startswith("Reason:") or line.startswith("## Reason:"):
        # Take the rest or next line
        reason_part = line.replace("Reason:", "").replace("## Reason:", "").strip()
        if reason_part:
            reason = reason_part
        elif i + 1 < len(lines):
            reason = lines[i + 1]
        i += 1
    i += 1

# Fallback
if not suggested_tone:
    suggested_tone = "professional and friendly"
if not reason:
    reason = "Default fallback tone for professional communication."

print("Parsed result:")
print({'suggested_tone': suggested_tone, 'reason': reason})