"""Fact store endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from memio.protocols import FactStore
from memio.server.dependencies import require_facts
from memio.server.models import FactCreate, FactResponse, FactSearch, FactUpdate

router = APIRouter(prefix="/facts", tags=["facts"])


@router.post("", response_model=FactResponse, status_code=201)
async def add_fact(
    body: FactCreate,
    store: FactStore = Depends(require_facts),
) -> FactResponse:
    fact = await store.add(
        content=body.content,
        user_id=body.user_id,
        agent_id=body.agent_id,
        metadata=body.metadata,
    )
    return FactResponse.model_validate(fact, from_attributes=True)


@router.get("", response_model=list[FactResponse])
async def get_all_facts(
    user_id: str | None = Query(None),
    agent_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    store: FactStore = Depends(require_facts),
) -> list[FactResponse]:
    facts = await store.get_all(user_id=user_id, agent_id=agent_id, limit=limit)
    return [FactResponse.model_validate(f, from_attributes=True) for f in facts]


@router.get("/{fact_id}", response_model=FactResponse)
async def get_fact(
    fact_id: str,
    store: FactStore = Depends(require_facts),
) -> FactResponse:
    fact = await store.get(fact_id=fact_id)
    return FactResponse.model_validate(fact, from_attributes=True)


@router.post("/search", response_model=list[FactResponse])
async def search_facts(
    body: FactSearch,
    store: FactStore = Depends(require_facts),
) -> list[FactResponse]:
    facts = await store.search(
        query=body.query,
        user_id=body.user_id,
        agent_id=body.agent_id,
        limit=body.limit,
        filters=body.filters,
    )
    return [FactResponse.model_validate(f, from_attributes=True) for f in facts]


@router.put("/{fact_id}", response_model=FactResponse)
async def update_fact(
    fact_id: str,
    body: FactUpdate,
    store: FactStore = Depends(require_facts),
) -> FactResponse:
    fact = await store.update(
        fact_id=fact_id,
        content=body.content,
        metadata=body.metadata,
    )
    return FactResponse.model_validate(fact, from_attributes=True)


@router.delete("/{fact_id}", status_code=204)
async def delete_fact(
    fact_id: str,
    store: FactStore = Depends(require_facts),
) -> Response:
    await store.delete(fact_id=fact_id)
    return Response(status_code=204)


@router.delete("", status_code=204)
async def delete_all_facts(
    user_id: str | None = Query(None),
    agent_id: str | None = Query(None),
    store: FactStore = Depends(require_facts),
) -> Response:
    await store.delete_all(user_id=user_id, agent_id=agent_id)
    return Response(status_code=204)
