"""Storage factory keyed off ``STORAGE_BACKEND``."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.base import Storage, StorageError
from app.services.storage.local import LocalStorage
from app.services.storage.s3 import S3Storage


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    settings = get_settings()
    backend = settings.storage_backend
    if backend == "local":
        return LocalStorage(root_dir=settings.local_storage_dir)
    if backend == "s3":
        if not settings.s3_documents_bucket:
            raise StorageError("S3_DOCUMENTS_BUCKET must be set when STORAGE_BACKEND=s3")
        return S3Storage(
            bucket=settings.s3_documents_bucket,
            region=settings.aws_region,
        )
    raise StorageError(f"unknown STORAGE_BACKEND: {backend!r}")
