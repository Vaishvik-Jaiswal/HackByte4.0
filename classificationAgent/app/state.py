from __future__ import annotations

from typing import NotRequired, TypedDict


class EmailInput(TypedDict):
    id: str
    content: str


class EmailResult(TypedDict):
    id: str
    category: str
    intent: str
    confidence: float


class EmailState(TypedDict):
    email: EmailInput
    result: NotRequired[EmailResult]
    raw_output: NotRequired[str]
    error: NotRequired[str]
