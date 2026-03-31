"""Shared fixtures for server tests — fake stores + httpx async client."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from memio.client import Memio
from memio.exceptions import NotFoundError
from memio.models import Document, Fact, GraphResult, Message, Triple
from memio.server.app import create_app
from memio.server.config import ServerConfig


# ── Fake stores ──────────────────────────────────────────────────────

_NOW = datetime(2025, 1, 1, tzinfo=timezone.utc)


class FakeFactStore:
    def __init__(self) -> None:
        self._facts: dict[str, Fact] = {}

    async def add(
        self, *, content: str, user_id: str | None = None,
        agent_id: str | None = None, metadata: dict | None = None,
    ) -> Fact:
        fid = f"f{len(self._facts) + 1}"
        fact = Fact(id=fid, content=content, user_id=user_id, agent_id=agent_id,
                    metadata=metadata, created_at=_NOW)
        self._facts[fid] = fact
        return fact

    async def get(self, *, fact_id: str) -> Fact:
        if fact_id not in self._facts:
            raise NotFoundError("fact", fact_id)
        return self._facts[fact_id]

    async def get_all(
        self, *, user_id: str | None = None,
        agent_id: str | None = None, limit: int = 100,
    ) -> list[Fact]:
        return list(self._facts.values())[:limit]

    async def search(
        self, *, query: str, user_id: str | None = None,
        agent_id: str | None = None, limit: int = 10,
        filters: dict | None = None,
    ) -> list[Fact]:
        return [f for f in self._facts.values() if query in f.content][:limit]

    async def update(
        self, *, fact_id: str, content: str, metadata: dict | None = None,
    ) -> Fact:
        if fact_id not in self._facts:
            raise NotFoundError("fact", fact_id)
        f = self._facts[fact_id]
        self._facts[fact_id] = Fact(
            id=f.id, content=content, user_id=f.user_id, agent_id=f.agent_id,
            metadata=metadata or f.metadata, updated_at=_NOW,
        )
        return self._facts[fact_id]

    async def delete(self, *, fact_id: str) -> None:
        self._facts.pop(fact_id, None)

    async def delete_all(
        self, *, user_id: str | None = None, agent_id: str | None = None,
    ) -> None:
        self._facts.clear()


class FakeHistoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[Message]] = {}

    async def add(
        self, *, session_id: str, messages: list[Message],
        user_id: str | None = None,
    ) -> None:
        self._sessions.setdefault(session_id, []).extend(messages)

    async def get(
        self, *, session_id: str, limit: int = 50, cursor: str | None = None,
    ) -> list[Message]:
        return self._sessions.get(session_id, [])[:limit]

    async def get_all(
        self, *, user_id: str | None = None, limit: int = 100,
    ) -> list[str]:
        return list(self._sessions.keys())[:limit]

    async def search(
        self, *, session_id: str, query: str, limit: int = 10,
    ) -> list[Message]:
        msgs = self._sessions.get(session_id, [])
        return [m for m in msgs if query in m.content][:limit]

    async def delete(self, *, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def delete_all(self, *, user_id: str | None = None) -> None:
        self._sessions.clear()


class FakeDocumentStore:
    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}

    async def add(
        self, *, content: str, doc_id: str | None = None,
        metadata: dict | None = None,
    ) -> Document:
        did = doc_id or f"d{len(self._docs) + 1}"
        doc = Document(id=did, content=content, metadata=metadata, created_at=_NOW)
        self._docs[did] = doc
        return doc

    async def get(self, *, doc_id: str) -> Document:
        if doc_id not in self._docs:
            raise NotFoundError("document", doc_id)
        return self._docs[doc_id]

    async def get_all(
        self, *, limit: int = 100, filters: dict | None = None,
    ) -> list[Document]:
        return list(self._docs.values())[:limit]

    async def search(
        self, *, query: str, limit: int = 10, filters: dict | None = None,
    ) -> list[Document]:
        return [d for d in self._docs.values() if query in d.content][:limit]

    async def update(
        self, *, doc_id: str, content: str, metadata: dict | None = None,
    ) -> Document:
        if doc_id not in self._docs:
            raise NotFoundError("document", doc_id)
        d = self._docs[doc_id]
        self._docs[doc_id] = Document(
            id=d.id, content=content, metadata=metadata or d.metadata,
            updated_at=_NOW,
        )
        return self._docs[doc_id]

    async def delete(self, *, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    async def delete_all(self) -> None:
        self._docs.clear()


class FakeGraphStore:
    def __init__(self) -> None:
        self._triples: list[Triple] = []

    async def add(
        self, *, triples: list[Triple], user_id: str | None = None,
    ) -> None:
        self._triples.extend(triples)

    async def get(
        self, *, entity: str, user_id: str | None = None,
    ) -> GraphResult:
        matched = [t for t in self._triples if t.subject == entity or t.object == entity]
        nodes = list({t.subject for t in matched} | {t.object for t in matched})
        return GraphResult(triples=matched, nodes=nodes)

    async def get_all(
        self, *, user_id: str | None = None, limit: int = 100,
    ) -> GraphResult:
        triples = self._triples[:limit]
        nodes = list({t.subject for t in triples} | {t.object for t in triples})
        return GraphResult(triples=triples, nodes=nodes)

    async def search(
        self, *, query: str, user_id: str | None = None, limit: int = 10,
    ) -> GraphResult:
        matched = [
            t for t in self._triples
            if query in t.subject or query in t.predicate or query in t.object
        ][:limit]
        nodes = list({t.subject for t in matched} | {t.object for t in matched})
        return GraphResult(triples=matched, nodes=nodes)

    async def delete(
        self, *, entity: str | None = None, triple_id: str | None = None,
    ) -> None:
        if entity:
            self._triples = [
                t for t in self._triples
                if t.subject != entity and t.object != entity
            ]

    async def delete_all(self, *, user_id: str | None = None) -> None:
        self._triples.clear()


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def fake_memio() -> Memio:
    return Memio(
        facts=FakeFactStore(),
        history=FakeHistoryStore(),
        documents=FakeDocumentStore(),
        graph=FakeGraphStore(),
    )


@pytest.fixture
async def client(fake_memio: Memio) -> AsyncIterator[AsyncClient]:
    config = ServerConfig()
    app = create_app(config=config)
    # Set state directly so lifespan isn't needed for tests
    app.state.memio = fake_memio
    app.state.api_key = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
