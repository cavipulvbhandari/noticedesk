"""FastAPI application entrypoint."""

from __future__ import annotations

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging
from app.routes import (
    clients,
    demo,
    documents,
    documents_matters,
    drafts,
    email,
    health,
    notices,
    registrations,
    routing,
    search,
    session,
)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )

    app = FastAPI(title="NoticeDesk API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_error_handlers(app)

    app.include_router(health.router, prefix="/v1")
    app.include_router(session.router, prefix="/v1")
    app.include_router(documents.router, prefix="/v1")
    app.include_router(email.router, prefix="/v1")
    app.include_router(routing.router, prefix="/v1")
    app.include_router(clients.router, prefix="/v1")
    app.include_router(registrations.router, prefix="/v1")
    app.include_router(notices.router, prefix="/v1")
    app.include_router(drafts.router, prefix="/v1")
    app.include_router(documents_matters.router, prefix="/v1")
    app.include_router(search.router, prefix="/v1")
    app.include_router(demo.router, prefix="/v1")

    return app


app = create_app()
