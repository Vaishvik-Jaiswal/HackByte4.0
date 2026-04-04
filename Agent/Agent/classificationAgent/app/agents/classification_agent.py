import os
from groq import Groq
from dotenv import load_dotenv

# 🔹 Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)


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
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

