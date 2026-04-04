from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

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


settings = Settings()
