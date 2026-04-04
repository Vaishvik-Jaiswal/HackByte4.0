from groq import Groq
from app.config import get_settings

# 🔹 Load configuration
settings = get_settings()

if not settings.groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=settings.groq_api_key)


def summarize_email(email_text: str) -> str:
    prompt = f"""
Summarize the email in 2-3 sentences, capturing the main points and key details.

Email:
\"\"\"{email_text}\"\"\"

Summary:
"""

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()