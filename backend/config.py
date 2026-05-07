from __future__ import annotations

from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # OpenAI
    openai_api_key: str = "set-me"
    openai_model: str = "gpt-4.1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./automation.db"

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # App
    secret_key: str = "change-me-in-production"
    debug: bool = False
    cors_origins: List[str] = ["http://localhost:3000"]

    # Playwright
    browser_headless: bool = True
    browser_timeout: int = 30000
    screenshot_dir: str = "./screenshots"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "./logs"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> List[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v  # type: ignore[return-value]


settings = Settings()
