"""FastAPI app — núcleo do backend Maestro."""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.config import get_settings
from app.logging import configure_logging, get_logger, set_correlation_id
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    log = get_logger("maestro.startup")
    log.info(
        "app.start",
        env=settings.env,
        backend_port=settings.backend_port,
        db_url=settings.resolved_db_url(),
    )
    yield
    log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Maestro",
        version="0.1.0",
        description="Assistente local-first de Engineering Management",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next) -> Response:
        cid = request.headers.get("x-correlation-id") or uuid4().hex[:12]
        set_correlation_id(cid)
        response = await call_next(request)
        response.headers["x-correlation-id"] = cid
        return response

    app.include_router(health.router, prefix="")
    return app


app = create_app()
