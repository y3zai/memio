"""Graph store endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from memio.models import Triple
from memio.protocols import GraphStore
from memio.server.dependencies import require_graph
from memio.server.models import GraphAdd, GraphResultResponse, GraphSearch, TripleBody

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/triples", status_code=204)
async def add_triples(
    body: GraphAdd,
    store: GraphStore = Depends(require_graph),
) -> Response:
    triples = [Triple(**t.model_dump()) for t in body.triples]
    await store.add(triples=triples, user_id=body.user_id)
    return Response(status_code=204)


@router.get("/triples", response_model=GraphResultResponse)
async def get_all_triples(
    user_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    store: GraphStore = Depends(require_graph),
) -> GraphResultResponse:
    result = await store.get_all(user_id=user_id, limit=limit)
    return _to_response(result)


@router.get("/entities/{entity}", response_model=GraphResultResponse)
async def get_entity(
    entity: str,
    user_id: str | None = Query(None),
    store: GraphStore = Depends(require_graph),
) -> GraphResultResponse:
    result = await store.get(entity=entity, user_id=user_id)
    return _to_response(result)


@router.post("/search", response_model=GraphResultResponse)
async def search_graph(
    body: GraphSearch,
    store: GraphStore = Depends(require_graph),
) -> GraphResultResponse:
    result = await store.search(
        query=body.query, user_id=body.user_id, limit=body.limit
    )
    return _to_response(result)


@router.delete("/entities/{entity}", status_code=204)
async def delete_entity(
    entity: str,
    store: GraphStore = Depends(require_graph),
) -> Response:
    await store.delete(entity=entity)
    return Response(status_code=204)


@router.delete("/triples/{triple_id}", status_code=204)
async def delete_triple(
    triple_id: str,
    store: GraphStore = Depends(require_graph),
) -> Response:
    await store.delete(triple_id=triple_id)
    return Response(status_code=204)


@router.delete("", status_code=204)
async def delete_all_graph(
    user_id: str | None = Query(None),
    store: GraphStore = Depends(require_graph),
) -> Response:
    await store.delete_all(user_id=user_id)
    return Response(status_code=204)


def _to_response(result: object) -> GraphResultResponse:
    """Convert a GraphResult dataclass to the response model."""
    triples = [
        TripleBody(
            subject=t.subject,
            predicate=t.predicate,
            object=t.object,
            metadata=t.metadata,
        )
        for t in result.triples  # type: ignore[attr-defined]
    ]
    return GraphResultResponse(
        triples=triples,
        nodes=result.nodes,  # type: ignore[attr-defined]
        scores=result.scores,  # type: ignore[attr-defined]
    )
