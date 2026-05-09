"""Abstract blob-storage interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass


class StorageError(Exception):
    """Raised on any storage backend failure."""


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    key: str
    size_bytes: int
    content_type: str | None
    sha256: str


class Storage(abc.ABC):
    """Async blob storage interface.

    All implementations must round-trip arbitrary bytes for any key the caller
    supplies. Keys are tenant-scoped by convention
    (``tenants/{tenant_id}/inbox/{inbox_id}/{filename}``); the storage layer
    itself is unaware of that prefix and treats the key as opaque.
    """

    @abc.abstractmethod
    async def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> ObjectMetadata:
        ...

    @abc.abstractmethod
    async def get(self, key: str) -> bytes:
        ...

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        ...
