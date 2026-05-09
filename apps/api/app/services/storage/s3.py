"""AWS S3 storage backend, pinned to ap-south-1 (Mumbai) for DPDP residency."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from app.services.storage.base import ObjectMetadata, Storage, StorageError


class S3Storage(Storage):
    """boto3-backed S3 client.

    boto3 is sync; we run each call in the default thread pool to keep the
    interface async. For Sprint 2 this is fine — uploads happen from a
    background workflow, not the request hot path.
    """

    def __init__(
        self,
        *,
        bucket: str,
        region: str = "ap-south-1",
        client: Any | None = None,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._client = client  # injected for tests; created lazily otherwise

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as e:
            raise StorageError(
                "boto3 is required for S3Storage; install boto3 or switch STORAGE_BACKEND=local"
            ) from e
        if self._region != "ap-south-1":
            raise StorageError(
                f"S3 bucket region must be ap-south-1 (DPDP residency); got {self._region!r}"
            )
        self._client = boto3.client("s3", region_name=self._region)
        return self._client

    async def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> ObjectMetadata:
        client = self._ensure_client()
        kwargs: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": key,
            "Body": data,
            "ServerSideEncryption": "AES256",
        }
        if content_type:
            kwargs["ContentType"] = content_type

        def _put() -> None:
            client.put_object(**kwargs)

        try:
            await asyncio.to_thread(_put)
        except Exception as e:  # noqa: BLE001
            raise StorageError(f"S3 put_object failed for {key!r}: {e}") from e

        return ObjectMetadata(
            key=key,
            size_bytes=len(data),
            content_type=content_type,
            sha256=hashlib.sha256(data).hexdigest(),
        )

    async def get(self, key: str) -> bytes:
        client = self._ensure_client()

        def _get() -> bytes:
            resp = client.get_object(Bucket=self._bucket, Key=key)
            return resp["Body"].read()

        try:
            return await asyncio.to_thread(_get)
        except Exception as e:  # noqa: BLE001
            raise StorageError(f"S3 get_object failed for {key!r}: {e}") from e

    async def exists(self, key: str) -> bool:
        client = self._ensure_client()

        def _head() -> bool:
            try:
                client.head_object(Bucket=self._bucket, Key=key)
                return True
            except client.exceptions.ClientError:
                return False

        return await asyncio.to_thread(_head)
