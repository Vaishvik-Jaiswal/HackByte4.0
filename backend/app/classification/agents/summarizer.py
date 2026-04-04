from app.classification.groq_client import get_groq_client
from app.core.config import settings


def summarize_email(email_text: str) -> str:
    client = get_groq_client()
    prompt = f"""
Summarize the email in 2-3 sentences, capturing the main points and key details.

Email:
\"\"\"{email_text}\"\"\"

Summary:
"""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()
