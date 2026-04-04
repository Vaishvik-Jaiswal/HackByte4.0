from groq import Groq
from app.config import get_settings

# 🔹 Load configuration
settings = get_settings()

if not settings.groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=settings.groq_api_key)


def classify_email(email_text: str) -> str:
    prompt = f"""
Classify the email into ONE category:

- Information
- Task
- Reminder
- Promotional/Spam
- Meeting/Schedule
- Confirmation/Thanks
- Authentication/Security

Return ONLY the category.

Email:
\"\"\"{email_text}\"\"\"
"""

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

