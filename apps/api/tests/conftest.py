"""Shared pytest fixtures.

Each test gets a fresh engine + dispatcher + cached singletons so the
DATABASE_URL one test patches doesn't leak into the next.
"""

from __future__ import annotations

import uuid

import pytest


def _clear_caches() -> None:
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
    except ImportError:
        pass
    try:
        from app.services.storage.factory import get_storage

        get_storage.cache_clear()
    except ImportError:
        pass
    try:
        from app.services.ocr.factory import get_ocr_provider

        get_ocr_provider.cache_clear()
    except ImportError:
        pass
    try:
        from app.workflows.dispatcher import get_dispatcher

        get_dispatcher.cache_clear()
    except ImportError:
        pass


@pytest.fixture(autouse=True)
async def _isolate_engine_and_workflows():
    # Setup: dispose any engine left over from a previous test so the next
    # access rebuilds against whatever DATABASE_URL the test set.
    try:
        from app.core import db as _db

        await _db.reset()
    except ImportError:
        pass
    _clear_caches()

    yield

    # Teardown: drain any in-flight inline-dispatcher tasks so they don't
    # leak into the next test's event loop and surface as "Task pending".
    try:
        from app.workflows.dispatcher import get_dispatcher

        try:
            dispatcher = get_dispatcher()
            await dispatcher.drain()
        except Exception:  # noqa: BLE001
            pass
    except ImportError:
        pass

    try:
        from app.core import db as _db

        await _db.reset()
    except ImportError:
        pass
    _clear_caches()


def unique_suffix() -> str:
    """Short random suffix for tenant names / slugs in integration tests."""
    return uuid.uuid4().hex[:8]
