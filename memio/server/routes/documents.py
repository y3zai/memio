"""Document store endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from memio.protocols import DocumentStore
from memio.server.dependencies import require_documents
from memio.server.models import (
    DocumentCreate,
    DocumentResponse,
    DocumentSearch,
    DocumentUpdate,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def add_document(
    body: DocumentCreate,
    store: DocumentStore = Depends(require_documents),
) -> DocumentResponse:
    doc = await store.add(
        content=body.content,
        doc_id=body.doc_id,
        metadata=body.metadata,
    )
    return DocumentResponse.model_validate(doc, from_attributes=True)


@router.get("", response_model=list[DocumentResponse])
async def get_all_documents(
    limit: int = Query(100, ge=1, le=1000),
    filters: str | None = Query(None, description="JSON-encoded metadata filters"),
    store: DocumentStore = Depends(require_documents),
) -> list[DocumentResponse]:
    import json as _json

    parsed_filters: dict | None = None
    if filters:
        try:
            parsed_filters = _json.loads(filters)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="filters must be valid JSON")
        if not isinstance(parsed_filters, dict):
            raise HTTPException(status_code=400, detail="filters must be a JSON object")
    docs = await store.get_all(limit=limit, filters=parsed_filters)
    return [DocumentResponse.model_validate(d, from_attributes=True) for d in docs]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    store: DocumentStore = Depends(require_documents),
) -> DocumentResponse:
    doc = await store.get(doc_id=doc_id)
    return DocumentResponse.model_validate(doc, from_attributes=True)


@router.post("/search", response_model=list[DocumentResponse])
async def search_documents(
    body: DocumentSearch,
    store: DocumentStore = Depends(require_documents),
) -> list[DocumentResponse]:
    docs = await store.search(
        query=body.query,
        limit=body.limit,
        filters=body.filters,
    )
    return [DocumentResponse.model_validate(d, from_attributes=True) for d in docs]


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    body: DocumentUpdate,
    store: DocumentStore = Depends(require_documents),
) -> DocumentResponse:
    doc = await store.update(
        doc_id=doc_id,
        content=body.content,
        metadata=body.metadata,
    )
    return DocumentResponse.model_validate(doc, from_attributes=True)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    store: DocumentStore = Depends(require_documents),
) -> Response:
    await store.delete(doc_id=doc_id)
    return Response(status_code=204)


@router.delete("", status_code=204)
async def delete_all_documents(
    store: DocumentStore = Depends(require_documents),
) -> Response:
    await store.delete_all()
    return Response(status_code=204)
