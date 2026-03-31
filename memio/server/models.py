"""Pydantic request/response schemas for the memio REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Facts ─────────────────────────────────────────────────────────────


class FactCreate(BaseModel):
    content: str
    user_id: str | None = None
    agent_id: str | None = None
    metadata: dict[str, Any] | None = None


class FactUpdate(BaseModel):
    content: str
    metadata: dict[str, Any] | None = None


class FactSearch(BaseModel):
    query: str
    user_id: str | None = None
    agent_id: str | None = None
    limit: int = Field(default=10, ge=1, le=1000)
    filters: dict[str, Any] | None = None


class FactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    user_id: str | None = None
    agent_id: str | None = None
    metadata: dict[str, Any] | None = None
    score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── History ───────────────────────────────────────────────────────────


class MessageBody(BaseModel):
    role: str
    content: str
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None
    name: str | None = None


class HistoryAdd(BaseModel):
    messages: list[MessageBody]
    user_id: str | None = None


class HistorySearch(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=1000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None
    name: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[str]


# ── Documents ─────────────────────────────────────────────────────────


class DocumentCreate(BaseModel):
    content: str
    doc_id: str | None = None
    metadata: dict[str, Any] | None = None


class DocumentUpdate(BaseModel):
    content: str
    metadata: dict[str, Any] | None = None


class DocumentSearch(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=1000)
    filters: dict[str, Any] | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    metadata: dict[str, Any] | None = None
    score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Graph ─────────────────────────────────────────────────────────────


class TripleBody(BaseModel):
    subject: str
    predicate: str
    object: str
    metadata: dict[str, Any] | None = None


class GraphAdd(BaseModel):
    triples: list[TripleBody]
    user_id: str | None = None


class GraphSearch(BaseModel):
    query: str
    user_id: str | None = None
    limit: int = Field(default=10, ge=1, le=1000)


class GraphResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    triples: list[TripleBody] = []
    nodes: list[str] = []
    scores: list[float] = []


# ── Common ────────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    error: str
    detail: str
    provider: str | None = None
    operation: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    stores: dict[str, bool]
