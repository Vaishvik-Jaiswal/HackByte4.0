from app.classification.groq_client import get_groq_client
from app.core.config import settings


def classify_email(email_text: str) -> str:
    client = get_groq_client()
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
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()
