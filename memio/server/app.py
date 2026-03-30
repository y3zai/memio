"""FastAPI app factory with lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

import memio
from memio.server.config import ServerConfig, build_memio_from_config, load_config
from memio.server.dependencies import get_memio, verify_api_key
from memio.server.errors import register_error_handlers
from memio.server.models import HealthResponse
from memio.server.routes import router as v1_router


def create_app(config: ServerConfig | None = None) -> FastAPI:
    """Create a configured FastAPI application."""
    if config is None:
        config = load_config()

    _config = config  # capture for lifespan closure

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = build_memio_from_config(_config)
        app.state.memio = client
        app.state.api_key = _config.api_key
        yield

    app = FastAPI(
        title="memio",
        description="Unified memory gateway for AI agents — REST API",
        version=memio.__version__,
        lifespan=lifespan,
        dependencies=[Depends(verify_api_key)],
    )

    register_error_handlers(app)
    app.include_router(v1_router)

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    async def health(client: memio.Memio = Depends(get_memio)) -> HealthResponse:
        return HealthResponse(
            stores={
                "facts": client.facts is not None,
                "history": client.history is not None,
                "documents": client.documents is not None,
                "graph": client.graph is not None,
            }
        )

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app
