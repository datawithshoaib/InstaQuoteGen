"""FastAPI application factory.

Run locally with:  uv run uvicorn app.main:app --reload
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.ai.llm import build_llm
from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, request_id_var
from app.db.engine import get_engine, init_db
from app.db.seed import seed_quotes
from app.services.images import BackgroundService

logger = logging.getLogger("app")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.ensure_dirs()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_db()
        with Session(get_engine()) as session:
            seed_quotes(session, settings.seed_file)
        # Tests may pre-populate these with fakes before startup.
        if not hasattr(app.state, "llm"):
            app.state.llm = build_llm(settings)
        if not hasattr(app.state, "backgrounds"):
            app.state.backgrounds = BackgroundService(settings)
        logger.info(
            "Ready. LLM: %s | images: %s",
            app.state.llm.model_name if app.state.llm else "off (library fallback)",
            "unsplash" if settings.unsplash_enabled else "gradients",
        )
        yield

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Writes, reviews and renders Instagram quote posts with a LangGraph pipeline.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex[:12]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        if request.url.path.startswith(settings.api_prefix):
            logger.info(
                "%s %s -> %s (%d ms)",
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - started) * 1000,
            )
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    # Only the two media folders are public. Nothing else on disk is served.
    app.mount("/media/posts", StaticFiles(directory=settings.posts_dir), name="posts")
    app.mount("/media/backgrounds", StaticFiles(directory=settings.backgrounds_dir), name="backgrounds")

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "docs": "/docs", "api": settings.api_prefix}

    return app


app = create_app()
