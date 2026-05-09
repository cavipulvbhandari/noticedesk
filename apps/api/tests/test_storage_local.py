from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.services.storage.base import StorageError
from app.services.storage.local import LocalStorage


@pytest.mark.asyncio
async def test_round_trip(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    payload = b"hello world"
    meta = await storage.put("tenants/x/inbox/y/file.pdf", payload, content_type="application/pdf")
    assert meta.size_bytes == len(payload)
    assert meta.sha256 == hashlib.sha256(payload).hexdigest()
    assert meta.content_type == "application/pdf"

    got = await storage.get("tenants/x/inbox/y/file.pdf")
    assert got == payload
    assert await storage.exists("tenants/x/inbox/y/file.pdf") is True
    assert await storage.exists("missing") is False


@pytest.mark.asyncio
async def test_rejects_path_traversal(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    for bad in ["../escape", "/abs/path", "tenants/../../etc/passwd"]:
        with pytest.raises(StorageError):
            await storage.put(bad, b"x")


@pytest.mark.asyncio
async def test_get_missing_raises(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    with pytest.raises(StorageError):
        await storage.get("not/there.pdf")
