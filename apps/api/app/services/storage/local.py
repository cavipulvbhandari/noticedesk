"""Filesystem-backed storage for dev and test."""

from __future__ import annotations

import hashlib
from pathlib import Path

import anyio

from app.services.storage.base import ObjectMetadata, Storage, StorageError


class LocalStorage(Storage):
    """Stores objects under ``root_dir/<key>``.

    Used in development and CI; production uses :class:`S3Storage`. We
    deliberately never accept absolute paths or keys with ``..`` components so
    a malicious caller can't escape the root.
    """

    def __init__(self, root_dir: str | Path) -> None:
        self._root = Path(root_dir).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        if not key or key.startswith("/") or ".." in Path(key).parts:
            raise StorageError(f"unsafe key: {key!r}")
        return self._root / key

    async def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> ObjectMetadata:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with await anyio.open_file(path, "wb") as f:
            await f.write(data)
        return ObjectMetadata(
            key=key,
            size_bytes=len(data),
            content_type=content_type,
            sha256=hashlib.sha256(data).hexdigest(),
        )

    async def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise StorageError(f"object not found: {key}")
        async with await anyio.open_file(path, "rb") as f:
            return await f.read()

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()
