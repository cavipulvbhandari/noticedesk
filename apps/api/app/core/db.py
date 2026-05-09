"""Async SQLAlchemy engine and session factory."""

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


def _build_engine() -> Any:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )


_engine = _build_engine()
_SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an AsyncSession."""
    async with _SessionLocal() as session:
        yield session


@asynccontextmanager
async def session_for_tenant(tenant_id: UUID | str) -> AsyncIterator[AsyncSession]:
    """Open a session bound to ``tenant_id``.

    Used by background workers (Temporal activities, the email webhook) that
    don't go through the request middleware. Caller is responsible for
    ``await session.commit()``.
    """
    async with _SessionLocal() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        yield session
