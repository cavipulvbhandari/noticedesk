"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]
AuthProvider = Literal["clerk", "dev"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Environment = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://noticedesk:noticedesk@localhost:5432/noticedesk_dev"

    auth_provider: AuthProvider = "dev"
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None

    sentry_dsn: str | None = None

    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @property
    def is_dev_auth_allowed(self) -> bool:
        return self.environment == "development" and self.auth_provider == "dev"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
