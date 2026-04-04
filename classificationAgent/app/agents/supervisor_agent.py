from groq import Groq
from app.config import get_settings

# 🔹 Load configuration
settings = get_settings()

if not settings.groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=settings.groq_api_key)


def generate_reply(category: str, summary: str, tone: str) -> str:
    prompt = f"""
Based on the email classification: {category}
And the summary: {summary}
Suggested tone: {tone}

Generate an appropriate reply email that matches the suggested tone. Keep it professional and concise.

Reply:
"""

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()