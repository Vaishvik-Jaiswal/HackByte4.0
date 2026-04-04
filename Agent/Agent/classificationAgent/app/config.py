from __future__ import annotations

import os
from functools import lru_cache
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()

DB_URL = "postgresql://postgres:ayu5hika@localhost:5432/email_ai_systems"
engine = create_engine(DB_URL)

class Settings(BaseModel):
    """Runtime configuration loaded from environment variables."""
   
    model_config = ConfigDict(frozen=True)

    groq_api_key: str | None = Field(default=os.getenv("GROQ_API_KEY"))
    groq_base_url: str = Field(default=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    groq_model: str = Field(default=os.getenv("GROQ_MODEL", "llama3-70b-8192"))
    request_timeout: int = Field(default=int(os.getenv("GROQ_TIMEOUT_SECONDS", "30")))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


GROQ_API_KEY = get_settings().groq_api_key
