import os
from groq import Groq
from dotenv import load_dotenv

# 🔹 Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)


def summarize_email(email_text: str) -> str:
    prompt = f"""
Summarize the email in 2-3 sentences, capturing the main points and key details.

Email:
\"\"\"{email_text}\"\"\"

Summary:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()