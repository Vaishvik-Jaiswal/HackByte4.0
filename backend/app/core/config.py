from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Always load backend/.env even if uvicorn is started from the repo root.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"
load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Modern Auth System"
    API_V1_STR: str = "/api"

    JWT_SECRET: str = Field(default="supersecret123", validation_alias="JWT_ACCESS_SECRET")
    JWT_REFRESH_SECRET: str = Field(default="superrefresh123")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str | None = None

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = Field(default="", validation_alias="GOOGLE_CALLBACK_URL")

    FRONTEND_URL: str = "http://localhost:3000"

    # Groq (email classification / summarization / tone)
    GROQ_API_KEY: str | None = None
    GROQ_BASE_URL: str = "https://api.groq.com"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TIMEOUT_SECONDS: int = 30


settings = Settings()
