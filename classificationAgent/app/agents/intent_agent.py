from groq import Groq
from app.config import get_settings

# Load configuration
settings = get_settings()

client = Groq(api_key=settings.groq_api_key)


def detect_intent(email_text: str) -> str:
    prompt = f"""
Identify the PRIMARY intent of the email.

Possible intents:
- Inform
- Request Action
- Remind
- Promote
- Schedule
- Confirm
- Authenticate

Return ONLY the intent.

Email:
\"\"\"{email_text}\"\"\"
"""

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()