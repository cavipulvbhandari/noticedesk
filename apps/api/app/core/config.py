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

    # Non-superuser role so RLS actually filters. The 'noticedesk' superuser
    # is reserved for migrations and schema tests — superusers bypass RLS
    # even with FORCE.
    database_url: str = "postgresql+asyncpg://noticedesk_app:noticedesk_app@localhost:5432/noticedesk_dev"

    auth_provider: AuthProvider = "dev"
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None

    sentry_dsn: str | None = None

    # Stored as a plain string in env so Pydantic-Settings doesn't try to
    # JSON-decode it (a list-typed env var would force JSON, which breaks
    # the natural ``ALLOWED_ORIGINS=http://localhost:3000`` form). Parsed
    # into a list via :meth:`allowed_origins`.
    allowed_origins_raw: str = Field(
        default="http://localhost:3000",
        validation_alias="ALLOWED_ORIGINS",
    )

    @property
    def allowed_origins(self) -> list[str]:
        s = (self.allowed_origins_raw or "").strip()
        if not s:
            return []
        if s.startswith("["):
            import json

            try:
                parsed = json.loads(s)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        return [item.strip() for item in s.split(",") if item.strip()]

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
