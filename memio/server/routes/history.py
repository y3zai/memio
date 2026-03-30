"""History store endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from memio.models import Message
from memio.protocols import HistoryStore
from memio.server.dependencies import require_history
from memio.server.models import (
    HistoryAdd,
    HistorySearch,
    MessageResponse,
    SessionListResponse,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.post("/sessions/{session_id}/messages", status_code=204)
async def add_messages(
    session_id: str,
    body: HistoryAdd,
    store: HistoryStore = Depends(require_history),
) -> Response:
    messages = [Message(**m.model_dump()) for m in body.messages]
    await store.add(session_id=session_id, messages=messages, user_id=body.user_id)
    return Response(status_code=204)


@router.get(
    "/sessions/{session_id}/messages", response_model=list[MessageResponse]
)
async def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=1000),
    cursor: str | None = Query(None),
    store: HistoryStore = Depends(require_history),
) -> list[MessageResponse]:
    messages = await store.get(session_id=session_id, limit=limit, cursor=cursor)
    return [MessageResponse.model_validate(m, from_attributes=True) for m in messages]


@router.get("/sessions", response_model=SessionListResponse)
async def get_all_sessions(
    user_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    store: HistoryStore = Depends(require_history),
) -> SessionListResponse:
    sessions = await store.get_all(user_id=user_id, limit=limit)
    return SessionListResponse(sessions=sessions)


@router.post(
    "/sessions/{session_id}/search", response_model=list[MessageResponse]
)
async def search_session(
    session_id: str,
    body: HistorySearch,
    store: HistoryStore = Depends(require_history),
) -> list[MessageResponse]:
    messages = await store.search(
        session_id=session_id, query=body.query, limit=body.limit
    )
    return [MessageResponse.model_validate(m, from_attributes=True) for m in messages]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    store: HistoryStore = Depends(require_history),
) -> Response:
    await store.delete(session_id=session_id)
    return Response(status_code=204)


@router.delete("/sessions", status_code=204)
async def delete_all_sessions(
    user_id: str | None = Query(None),
    store: HistoryStore = Depends(require_history),
) -> Response:
    await store.delete_all(user_id=user_id)
    return Response(status_code=204)
