from __future__ import annotations

from typing import Protocol, runtime_checkable

from memio.models import Document, Fact, GraphResult, Message, Triple


@runtime_checkable
class FactStore(Protocol):
    """Protocol for storing and retrieving structured facts.

    Facts are short pieces of knowledge scoped to a user or agent.
    Implementations must provide all methods as async.
    """

    async def add(self, *, content: str, user_id: str | None = None,
                  agent_id: str | None = None, metadata: dict | None = None) -> Fact: ...
    async def search(self, *, query: str, user_id: str | None = None,
                     agent_id: str | None = None, limit: int = 10,
                     filters: dict | None = None) -> list[Fact]: ...
    async def update(self, *, fact_id: str, content: str,
                     metadata: dict | None = None) -> Fact: ...
    async def get(self, *, fact_id: str) -> Fact: ...
    async def delete(self, *, fact_id: str) -> None: ...
    async def delete_all(self, *, user_id: str | None = None,
                         agent_id: str | None = None) -> None: ...
    async def get_all(self, *, user_id: str | None = None,
                      agent_id: str | None = None, limit: int = 100) -> list[Fact]: ...


@runtime_checkable
class HistoryStore(Protocol):
    """Protocol for storing and retrieving conversation history.

    Messages are grouped by session ID. Implementations must provide
    all methods as async.
    """

    async def add(self, *, session_id: str, messages: list[Message]) -> None: ...
    async def get(self, *, session_id: str, limit: int = 50,
                  cursor: str | None = None) -> list[Message]: ...
    async def search(self, *, session_id: str, query: str,
                     limit: int = 10) -> list[Message]: ...
    async def delete(self, *, session_id: str) -> None: ...
    async def get_all(self, *, user_id: str | None = None,
                      limit: int = 100) -> list[str]: ...
    async def delete_all(self, *, user_id: str | None = None) -> None: ...


@runtime_checkable
class DocumentStore(Protocol):
    """Protocol for storing and searching documents.

    Documents support semantic search and optional metadata filtering.
    Implementations must provide all methods as async.
    """

    async def add(self, *, content: str, doc_id: str | None = None,
                  metadata: dict | None = None) -> Document: ...
    async def get(self, *, doc_id: str) -> Document: ...
    async def search(self, *, query: str, limit: int = 10,
                     filters: dict | None = None) -> list[Document]: ...
    async def update(self, *, doc_id: str, content: str,
                     metadata: dict | None = None) -> Document: ...
    async def delete(self, *, doc_id: str) -> None: ...
    async def get_all(self, *, limit: int = 100,
                      filters: dict | None = None) -> list[Document]: ...
    async def delete_all(self) -> None: ...


@runtime_checkable
class GraphStore(Protocol):
    """Protocol for storing and querying knowledge graph triples.

    Triples represent subject-predicate-object relationships.
    Implementations must provide all methods as async.
    """

    async def add(self, *, triples: list[Triple], user_id: str | None = None) -> None: ...
    async def get(self, *, entity: str, user_id: str | None = None) -> GraphResult: ...
    async def get_all(self, *, user_id: str | None = None,
                      limit: int = 100) -> GraphResult: ...
    async def search(self, *, query: str, user_id: str | None = None,
                     limit: int = 10) -> GraphResult: ...
    async def delete(self, *, entity: str | None = None,
                     triple_id: str | None = None) -> None: ...
    async def delete_all(self, *, user_id: str | None = None) -> None: ...
