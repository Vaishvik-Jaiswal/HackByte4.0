import os
from groq import Groq
from dotenv import load_dotenv

# 🔹 Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)


def generate_reply(category: str, summary: str, tone: str) -> str:
    prompt = f"""
Based on the email classification: {category}
And the summary: {summary}
Suggested tone: {tone}

Generate an appropriate reply email that matches the suggested tone. Keep it professional and concise.

Reply:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()