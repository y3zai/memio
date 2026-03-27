from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Fact:
    """A stored piece of knowledge about a user or agent.

    Attributes:
        id: Unique identifier for the fact.
        content: The textual content of the fact.
        user_id: Optional user scope for the fact.
        agent_id: Optional agent scope for the fact.
        metadata: Optional dictionary of extra metadata.
        score: Optional relevance score from search.
        created_at: Timestamp when the fact was created.
        updated_at: Timestamp when the fact was last updated.
    """

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
    """A conversation message in a session.

    Attributes:
        role: The role of the message sender (e.g. "user", "assistant").
        content: The textual content of the message.
        metadata: Optional dictionary of extra metadata.
        timestamp: Optional timestamp when the message was created.
        name: Optional display name of the sender.
    """

    role: str
    content: str
    metadata: dict | None = None
    timestamp: datetime | None = None
    name: str | None = None


@dataclass
class Document:
    """A stored document with optional metadata.

    Attributes:
        id: Unique identifier for the document.
        content: The textual content of the document.
        metadata: Optional dictionary of extra metadata.
        score: Optional relevance score from search.
        created_at: Timestamp when the document was created.
        updated_at: Timestamp when the document was last updated.
    """

    id: str
    content: str
    metadata: dict | None = None
    score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Triple:
    """A knowledge graph triple representing a relationship.

    Attributes:
        subject: The subject entity of the triple.
        predicate: The relationship between subject and object.
        object: The object entity of the triple.
        metadata: Optional dictionary of extra metadata.
    """

    subject: str
    predicate: str
    object: str
    metadata: dict | None = None


@dataclass
class GraphResult:
    """Result from a knowledge graph query.

    Attributes:
        triples: List of triples returned by the query.
        nodes: List of node identifiers in the result.
        scores: List of relevance scores for the results.
    """

    triples: list[Triple] = field(default_factory=list)
    nodes: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
