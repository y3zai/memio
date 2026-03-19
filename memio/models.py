from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Fact:
    id: str
    content: str
    user_id: str | None = None
    agent_id: str | None = None
    metadata: dict | None = None
    score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Message:
    role: str
    content: str
    metadata: dict | None = None
    timestamp: datetime | None = None
    name: str | None = None


@dataclass
class Document:
    id: str
    content: str
    metadata: dict | None = None
    score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Triple:
    subject: str
    predicate: str
    object: str
    metadata: dict | None = None


@dataclass
class GraphResult:
    triples: list[Triple] = field(default_factory=list)
    nodes: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
