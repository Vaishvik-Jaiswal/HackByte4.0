from __future__ import annotations

import os
from functools import lru_cache
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
from urllib.parse import quote

load_dotenv()

# Build DB URL from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Lisha@15")  # Default password, should be overridden in production
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "auth_system")

# URL-encode the password to handle special characters like @
DB_PASSWORD_ENCODED = quote(DB_PASSWORD, safe='')
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

class Settings(BaseModel):
    """Runtime configuration loaded from environment variables."""
   
    model_config = ConfigDict(frozen=True)

    groq_api_key: str | None = Field(default=os.getenv("GROQ_API_KEY"))
    groq_base_url: str = Field(default=os.getenv("GROQ_BASE_URL", "https://api.groq.com"))
    groq_model: str = Field(default=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
    request_timeout: int = Field(default=int(os.getenv("GROQ_TIMEOUT_SECONDS", "30")))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


GROQ_API_KEY = get_settings().groq_api_key
