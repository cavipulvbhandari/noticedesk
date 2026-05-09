"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]
AuthProvider = Literal["clerk", "dev"]
StorageBackend = Literal["s3", "local"]
WorkflowBackend = Literal["temporal", "inline"]


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

    # ---- Sprint 2: storage --------------------------------------------------
    storage_backend: StorageBackend = "local"
    aws_region: str = "ap-south-1"
    s3_documents_bucket: str | None = None
    local_storage_dir: str = "/tmp/noticedesk-storage"
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB

    # ---- Sprint 2: OCR ------------------------------------------------------
    ocr_provider_primary: str = "stub"
    ocr_provider_fallback: str | None = None

    google_doc_ai_project_id: str | None = None
    google_doc_ai_location: str | None = None
    google_doc_ai_processor_id: str | None = None

    azure_doc_intel_endpoint: str | None = None
    azure_doc_intel_api_key: str | None = None

    # ---- Sprint 2: workflows ------------------------------------------------
    workflow_backend: WorkflowBackend = "inline"
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "noticedesk-ocr"

    # ---- Sprint 2: email inbound -------------------------------------------
    email_inbound_webhook_secret: str | None = None
    email_inbound_domain: str = "noticedesk.in"

    @property
    def is_dev_auth_allowed(self) -> bool:
        return self.environment == "development" and self.auth_provider == "dev"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
