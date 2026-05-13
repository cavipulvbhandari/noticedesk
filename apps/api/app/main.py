"""FastAPI application entrypoint."""

from __future__ import annotations

# Load apps/api/.env into os.environ BEFORE any SDK imports — Google
# Cloud's auth library, anthropic's client, and the AWS SDK all read their
# credentials from os.environ. pydantic-settings populates the Settings
# object but does NOT inject keys back into os.environ, so a partner who
# put GOOGLE_APPLICATION_CREDENTIALS in .env without also exporting it in
# the shell would see "default credentials not found" at first call.
# python-dotenv is already a transitive dep of pydantic-settings.
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

import sentry_sdk  # noqa: E402  (must follow load_dotenv to see SENTRY_DSN)
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.errors import install_error_handlers  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402
from app.routes import (  # noqa: E402
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
