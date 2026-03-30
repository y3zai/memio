"""Exception-to-HTTP-response mapping for the memio REST API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from memio.exceptions import MemioError, NotFoundError, NotSupportedError, ProviderError


def register_error_handlers(app: FastAPI) -> None:
    """Attach memio exception handlers to the FastAPI app."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "detail": str(exc),
                "provider": None,
                "operation": None,
            },
        )

    @app.exception_handler(NotSupportedError)
    async def not_supported_handler(
        _request: Request, exc: NotSupportedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content={
                "error": "not_supported",
                "detail": str(exc),
                "provider": exc.provider,
                "operation": exc.operation,
            },
        )

    @app.exception_handler(ProviderError)
    async def provider_error_handler(
        _request: Request, exc: ProviderError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "error": "provider_error",
                "detail": str(exc),
                "provider": exc.provider,
                "operation": exc.operation,
            },
        )

    @app.exception_handler(MemioError)
    async def memio_error_handler(_request: Request, exc: MemioError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "memio_error",
                "detail": str(exc),
                "provider": None,
                "operation": None,
            },
        )
