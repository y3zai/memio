"""FastAPI dependencies — Memio client, auth, and store guards.

State is stored on ``app.state`` (not module globals) so multiple app
instances in the same process do not interfere with each other.
"""

from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException, Request

from memio.client import Memio
from memio.protocols import DocumentStore, FactStore, GraphStore, HistoryStore


# ── Memio from app state ─────────────────────────────────────────────


def get_memio(request: Request) -> Memio:
    client: Memio | None = getattr(request.app.state, "memio", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Memio client not initialised")
    return client


# ── Auth ─────────────────────────────────────────────────────────────


async def verify_api_key(request: Request) -> None:
    """Validate the Bearer token if auth is enabled."""
    api_key: str | None = getattr(request.app.state, "api_key", None)
    if api_key is None:
        return  # auth disabled
    authorization: str | None = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    token = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")


# ── Store guards ─────────────────────────────────────────────────────


async def require_facts(memio: Memio = Depends(get_memio)) -> FactStore:
    if memio.facts is None:
        raise HTTPException(
            status_code=501,
            detail="FactStore is not configured on this server",
        )
    return memio.facts


async def require_history(memio: Memio = Depends(get_memio)) -> HistoryStore:
    if memio.history is None:
        raise HTTPException(
            status_code=501,
            detail="HistoryStore is not configured on this server",
        )
    return memio.history


async def require_documents(memio: Memio = Depends(get_memio)) -> DocumentStore:
    if memio.documents is None:
        raise HTTPException(
            status_code=501,
            detail="DocumentStore is not configured on this server",
        )
    return memio.documents


async def require_graph(memio: Memio = Depends(get_memio)) -> GraphStore:
    if memio.graph is None:
        raise HTTPException(
            status_code=501,
            detail="GraphStore is not configured on this server",
        )
    return memio.graph
