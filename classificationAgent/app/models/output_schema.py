from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal[
    "Information",
    "Task",
    "Reminder",
    "Promotional",
    "Meeting/Schedule",
    "Confirmation",
    "Security",
]

Intent = Literal[
    "Inform",
    "Request Action",
    "Remind",
    "Promote",
    "Schedule",
    "Confirm",
    "Authenticate",
]


class EmailAnalysis(BaseModel):
    """Structured email classification returned by the agent."""

    model_config = ConfigDict(extra="forbid")

    category: Category = Field(description="One allowed email category.")
    intent: Intent = Field(description="One allowed email intent.")
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> float:
        if isinstance(value, str):
            value = value.strip()
        return round(float(value), 2)
