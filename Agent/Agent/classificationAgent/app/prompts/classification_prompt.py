from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


def get_prompt(format_instructions: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an email classification engine for a production workflow.

Classify the email into exactly one category from this closed set:
{allowed_categories}

Identify exactly one intent from this closed set:
{allowed_intents}

Rules:
- Return valid JSON only.
- Do not include markdown, commentary, or extra keys.
- If multiple labels seem possible, choose the single best label.
- Keep the output deterministic and grounded in the email text.
- confidence must be a number from 0.0 to 1.0.

{format_instructions}
""".strip(),
            ),
            (
                "human",
                "Email ID: {email_id}\nEmail Content:\n{email}",
            ),
        ]
    ).partial(
        format_instructions=format_instructions,
        allowed_categories="Information, Task, Reminder, Promotional, Meeting/Schedule, Confirmation, Security",
        allowed_intents="Inform, Request Action, Remind, Promote, Schedule, Confirm, Authenticate",
    )
