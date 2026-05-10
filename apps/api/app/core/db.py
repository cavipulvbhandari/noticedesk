"""Async SQLAlchemy engine and session factory.

The engine is created lazily on first access so test fixtures can override
``DATABASE_URL`` via monkeypatch and call :func:`reset` to rebuild against
the test database. In production the engine is built once on first request
and reused for the process lifetime.

Call sites that need a session factory call :func:`session_local`, which
builds the engine the first time and returns the same factory thereafter.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine_singleton: Any = None
_session_local_singleton: async_sessionmaker[AsyncSession] | None = None


def _build() -> tuple[Any, async_sessionmaker[AsyncSession]]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, factory


def session_local() -> async_sessionmaker[AsyncSession]:
    """Return the AsyncSession factory, building the engine on first call."""
    global _engine_singleton, _session_local_singleton
    if _session_local_singleton is None:
        _engine_singleton, _session_local_singleton = _build()
    return _session_local_singleton


async def reset() -> None:
    """Dispose the engine so the next access rebuilds it.

    Used by test fixtures after monkeypatching ``DATABASE_URL``.
    """
    global _engine_singleton, _session_local_singleton
    if _engine_singleton is not None:
        await _engine_singleton.dispose()
    _engine_singleton = None
    _session_local_singleton = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an AsyncSession."""
    async with session_local()() as session:
        yield session


@asynccontextmanager
async def session_for_tenant(tenant_id: UUID | str) -> AsyncIterator[AsyncSession]:
    """Open a session bound to ``tenant_id``.

    Used by background workers (Temporal activities, the email webhook) that
    don't go through the request middleware. Caller is responsible for
    ``await session.commit()``.
    """
    async with session_local()() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        yield session
