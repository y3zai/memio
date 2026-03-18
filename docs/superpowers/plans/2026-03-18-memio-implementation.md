# memio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python SDK that provides a unified API to access multiple agent memory systems (mem0, Zep, Chroma) through protocol-based adapters.

**Architecture:** Protocol-based with direct injection. Four memory type protocols (FactStore, HistoryStore, DocumentStore, GraphStore) define the contract. Provider adapters implement whichever protocols they support. The Memio client wires adapters to namespaces at init time.

**Tech Stack:** Python 3.10+, pytest + pytest-asyncio for testing, dataclasses for models, typing.Protocol for interfaces.

**Spec:** `docs/superpowers/specs/2026-03-18-memio-design.md`

---

## File Structure

```
memio/
├── __init__.py              # Public API exports
├── client.py                # Memio class
├── protocols.py             # FactStore, HistoryStore, DocumentStore, GraphStore protocols
├── models.py                # Fact, Message, Document, Triple, GraphResult dataclasses
├── exceptions.py            # MemioError, ProviderError
├── py.typed                 # PEP 561 marker
├── providers/
│   ├── __init__.py          # Empty
│   ├── mem0/
│   │   ├── __init__.py      # Exports Mem0FactAdapter, Mem0GraphAdapter
│   │   ├── fact.py          # Mem0FactAdapter (FactStore)
│   │   └── graph.py         # Mem0GraphAdapter (GraphStore)
│   ├── zep/
│   │   ├── __init__.py      # Exports ZepFactAdapter, ZepHistoryAdapter, ZepGraphAdapter
│   │   ├── fact.py          # ZepFactAdapter (FactStore)
│   │   ├── history.py       # ZepHistoryAdapter (HistoryStore)
│   │   └── graph.py         # ZepGraphAdapter (GraphStore)
│   └── chroma/
│       ├── __init__.py      # Exports ChromaDocumentAdapter
│       └── document.py      # ChromaDocumentAdapter (DocumentStore)
tests/
├── conftest.py              # Shared fixtures
├── test_models.py           # Data model tests
├── test_protocols.py        # Protocol conformance checking tests
├── test_exceptions.py       # Exception tests
├── test_client.py           # Memio client tests
├── conformance/
│   ├── __init__.py
│   ├── fact_store.py        # Reusable FactStore conformance suite
│   ├── history_store.py     # Reusable HistoryStore conformance suite
│   ├── document_store.py    # Reusable DocumentStore conformance suite
│   └── graph_store.py       # Reusable GraphStore conformance suite
├── providers/
│   ├── __init__.py
│   ├── test_mem0_fact.py    # Mem0FactAdapter unit tests (mocked SDK)
│   ├── test_mem0_graph.py   # Mem0GraphAdapter unit tests (mocked SDK)
│   ├── test_zep_fact.py     # ZepFactAdapter unit tests (mocked SDK)
│   ├── test_zep_history.py  # ZepHistoryAdapter unit tests (mocked SDK)
│   ├── test_zep_graph.py    # ZepGraphAdapter unit tests (mocked SDK)
│   └── test_chroma_doc.py   # ChromaDocumentAdapter unit tests (mocked SDK)
pyproject.toml               # Package config, dependencies, pytest config
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `memio/__init__.py` (empty placeholder)
- Create: `memio/py.typed` (empty marker)
- Create: `tests/conftest.py` (empty placeholder)

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "memio"
version = "0.1.0"
description = "Unified memory gateway for AI agents"
requires-python = ">=3.10"
license = "MIT"
dependencies = []

[project.optional-dependencies]
mem0 = ["mem0ai"]
zep = ["zep-cloud"]
chroma = ["chromadb"]
all = ["mem0ai", "zep-cloud", "chromadb"]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23", "pytest-mock>=3.12"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: requires real provider API keys",
]
```

- [ ] **Step 2: Create directory structure and placeholder files**

```bash
mkdir -p memio/providers/mem0 memio/providers/zep memio/providers/chroma
mkdir -p tests/conformance tests/providers
touch memio/__init__.py memio/py.typed
touch memio/providers/__init__.py
touch memio/providers/mem0/__init__.py memio/providers/zep/__init__.py memio/providers/chroma/__init__.py
touch tests/__init__.py tests/conftest.py
touch tests/conformance/__init__.py tests/providers/__init__.py
```

- [ ] **Step 3: Install dev dependencies and verify pytest runs**

```bash
pip install -e ".[dev]"
pytest --collect-only
```

Expected: 0 tests collected, no errors.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml memio/ tests/
git commit -m "feat: project scaffolding with directory structure and dev tooling"
```

---

### Task 2: Data Models

**Files:**
- Create: `memio/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for data models**

```python
# tests/test_models.py
from datetime import datetime
from memio.models import Fact, Message, Document, Triple, GraphResult


class TestFact:
    def test_required_fields(self):
        fact = Fact(id="f1", content="likes coffee")
        assert fact.id == "f1"
        assert fact.content == "likes coffee"

    def test_optional_fields_default_none(self):
        fact = Fact(id="f1", content="likes coffee")
        assert fact.user_id is None
        assert fact.agent_id is None
        assert fact.metadata is None
        assert fact.score is None
        assert fact.created_at is None
        assert fact.updated_at is None

    def test_all_fields(self):
        now = datetime.now()
        fact = Fact(
            id="f1", content="likes coffee", user_id="u1",
            agent_id="a1", metadata={"source": "chat"},
            score=0.95, created_at=now, updated_at=now,
        )
        assert fact.user_id == "u1"
        assert fact.score == 0.95


class TestMessage:
    def test_required_fields(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_optional_fields_default_none(self):
        msg = Message(role="user", content="hello")
        assert msg.metadata is None
        assert msg.timestamp is None
        assert msg.name is None


class TestDocument:
    def test_required_fields(self):
        doc = Document(id="d1", content="deploy guide")
        assert doc.id == "d1"
        assert doc.content == "deploy guide"

    def test_optional_fields_default_none(self):
        doc = Document(id="d1", content="deploy guide")
        assert doc.metadata is None
        assert doc.score is None
        assert doc.created_at is None
        assert doc.updated_at is None


class TestTriple:
    def test_required_fields(self):
        t = Triple(subject="Alice", predicate="works_at", object="Acme")
        assert t.subject == "Alice"
        assert t.predicate == "works_at"
        assert t.object == "Acme"

    def test_optional_metadata(self):
        t = Triple(subject="A", predicate="B", object="C")
        assert t.metadata is None


class TestGraphResult:
    def test_defaults_empty(self):
        r = GraphResult()
        assert r.triples == []
        assert r.nodes == []
        assert r.scores == []

    def test_with_data(self):
        t = Triple(subject="A", predicate="B", object="C")
        r = GraphResult(triples=[t], nodes=["A", "C"], scores=[0.9])
        assert len(r.triples) == 1
        assert r.nodes == ["A", "C"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'memio.models'`

- [ ] **Step 3: Implement data models**

```python
# memio/models.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add memio/models.py tests/test_models.py
git commit -m "feat: add data models (Fact, Message, Document, Triple, GraphResult)"
```

---

### Task 3: Protocols

**Files:**
- Create: `memio/protocols.py`
- Create: `tests/test_protocols.py`

- [ ] **Step 1: Write failing tests for protocol type checking**

```python
# tests/test_protocols.py
from memio.protocols import FactStore, HistoryStore, DocumentStore, GraphStore
from memio.models import Fact, Message, Document, Triple, GraphResult


class FakeFactStore:
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


class FakeHistoryStore:
    async def add(self, *, session_id: str, messages: list[Message]) -> None: ...
    async def get(self, *, session_id: str, limit: int = 50,
                  cursor: str | None = None) -> list[Message]: ...
    async def search(self, *, session_id: str, query: str,
                     limit: int = 10) -> list[Message]: ...
    async def delete(self, *, session_id: str) -> None: ...


class FakeDocumentStore:
    async def add(self, *, content: str, doc_id: str | None = None,
                  metadata: dict | None = None) -> Document: ...
    async def get(self, *, doc_id: str) -> Document: ...
    async def search(self, *, query: str, limit: int = 10,
                     filters: dict | None = None) -> list[Document]: ...
    async def update(self, *, doc_id: str, content: str,
                     metadata: dict | None = None) -> Document: ...
    async def delete(self, *, doc_id: str) -> None: ...


class FakeGraphStore:
    async def add(self, *, triples: list[Triple], user_id: str | None = None) -> None: ...
    async def get(self, *, entity: str, user_id: str | None = None) -> GraphResult: ...
    async def get_all(self, *, user_id: str | None = None,
                      limit: int = 100) -> GraphResult: ...
    async def search(self, *, query: str, user_id: str | None = None,
                     limit: int = 10) -> GraphResult: ...
    async def delete(self, *, entity: str | None = None,
                     triple_id: str | None = None) -> None: ...
    async def delete_all(self, *, user_id: str | None = None) -> None: ...


class NotAStore:
    pass


class TestProtocolChecking:
    def test_fact_store_isinstance(self):
        assert isinstance(FakeFactStore(), FactStore)

    def test_history_store_isinstance(self):
        assert isinstance(FakeHistoryStore(), HistoryStore)

    def test_document_store_isinstance(self):
        assert isinstance(FakeDocumentStore(), DocumentStore)

    def test_graph_store_isinstance(self):
        assert isinstance(FakeGraphStore(), GraphStore)

    def test_non_conforming_class_fails(self):
        assert not isinstance(NotAStore(), FactStore)
        assert not isinstance(NotAStore(), HistoryStore)
        assert not isinstance(NotAStore(), DocumentStore)
        assert not isinstance(NotAStore(), GraphStore)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_protocols.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'memio.protocols'`

- [ ] **Step 3: Implement protocols**

```python
# memio/protocols.py
from __future__ import annotations

from typing import Protocol, runtime_checkable

from memio.models import Document, Fact, GraphResult, Message, Triple


@runtime_checkable
class FactStore(Protocol):
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
    async def add(self, *, session_id: str, messages: list[Message]) -> None: ...

    async def get(self, *, session_id: str, limit: int = 50,
                  cursor: str | None = None) -> list[Message]: ...

    async def search(self, *, session_id: str, query: str,
                     limit: int = 10) -> list[Message]: ...

    async def delete(self, *, session_id: str) -> None: ...


@runtime_checkable
class DocumentStore(Protocol):
    async def add(self, *, content: str, doc_id: str | None = None,
                  metadata: dict | None = None) -> Document: ...

    async def get(self, *, doc_id: str) -> Document: ...

    async def search(self, *, query: str, limit: int = 10,
                     filters: dict | None = None) -> list[Document]: ...

    async def update(self, *, doc_id: str, content: str,
                     metadata: dict | None = None) -> Document: ...

    async def delete(self, *, doc_id: str) -> None: ...


@runtime_checkable
class GraphStore(Protocol):
    async def add(self, *, triples: list[Triple], user_id: str | None = None) -> None: ...

    async def get(self, *, entity: str, user_id: str | None = None) -> GraphResult: ...

    async def get_all(self, *, user_id: str | None = None,
                      limit: int = 100) -> GraphResult: ...

    async def search(self, *, query: str, user_id: str | None = None,
                     limit: int = 10) -> GraphResult: ...

    async def delete(self, *, entity: str | None = None,
                     triple_id: str | None = None) -> None: ...

    async def delete_all(self, *, user_id: str | None = None) -> None: ...
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_protocols.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add memio/protocols.py tests/test_protocols.py
git commit -m "feat: add memory type protocols (FactStore, HistoryStore, DocumentStore, GraphStore)"
```

---

### Task 4: Exceptions

**Files:**
- Create: `memio/exceptions.py`
- Create: `tests/test_exceptions.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_exceptions.py
from memio.exceptions import MemioError, ProviderError


class TestMemioError:
    def test_is_exception(self):
        assert issubclass(MemioError, Exception)

    def test_message(self):
        e = MemioError("something broke")
        assert str(e) == "something broke"


class TestProviderError:
    def test_inherits_memio_error(self):
        assert issubclass(ProviderError, MemioError)

    def test_attributes(self):
        cause = ValueError("bad input")
        e = ProviderError(provider="mem0", operation="add", cause=cause)
        assert e.provider == "mem0"
        assert e.operation == "add"
        assert e.cause is cause

    def test_message_format(self):
        cause = RuntimeError("timeout")
        e = ProviderError(provider="zep", operation="search", cause=cause)
        assert "[zep] search failed: timeout" == str(e)

    def test_can_be_caught_as_memio_error(self):
        cause = RuntimeError("fail")
        e = ProviderError(provider="mem0", operation="add", cause=cause)
        try:
            raise e
        except MemioError as caught:
            assert caught is e
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_exceptions.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'memio.exceptions'`

- [ ] **Step 3: Implement exceptions**

```python
# memio/exceptions.py


class MemioError(Exception):
    """Base exception for all memio errors."""
    pass


class ProviderError(MemioError):
    """Wraps provider SDK exceptions."""

    def __init__(self, provider: str, operation: str, cause: Exception):
        self.provider = provider
        self.operation = operation
        self.cause = cause
        super().__init__(f"[{provider}] {operation} failed: {cause}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_exceptions.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add memio/exceptions.py tests/test_exceptions.py
git commit -m "feat: add MemioError and ProviderError exceptions"
```

---

### Task 5: Memio Client

**Files:**
- Create: `memio/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_client.py
import pytest
from memio.client import Memio
from memio.protocols import FactStore, HistoryStore, DocumentStore, GraphStore
from memio.models import Fact, Message, Document, Triple, GraphResult


# Minimal fake implementations that satisfy protocols
class FakeFactStore:
    async def add(self, *, content, user_id=None, agent_id=None, metadata=None):
        return Fact(id="f1", content=content)
    async def search(self, *, query, user_id=None, agent_id=None, limit=10, filters=None):
        return []
    async def update(self, *, fact_id, content, metadata=None):
        return Fact(id=fact_id, content=content)
    async def get(self, *, fact_id):
        return Fact(id=fact_id, content="test")
    async def delete(self, *, fact_id):
        pass
    async def delete_all(self, *, user_id=None, agent_id=None):
        pass
    async def get_all(self, *, user_id=None, agent_id=None, limit=100):
        return []


class FakeHistoryStore:
    async def add(self, *, session_id, messages):
        pass
    async def get(self, *, session_id, limit=50, cursor=None):
        return []
    async def search(self, *, session_id, query, limit=10):
        return []
    async def delete(self, *, session_id):
        pass


class FakeDocumentStore:
    async def add(self, *, content, doc_id=None, metadata=None):
        return Document(id="d1", content=content)
    async def get(self, *, doc_id):
        return Document(id=doc_id, content="test")
    async def search(self, *, query, limit=10, filters=None):
        return []
    async def update(self, *, doc_id, content, metadata=None):
        return Document(id=doc_id, content=content)
    async def delete(self, *, doc_id):
        pass


class FakeGraphStore:
    async def add(self, *, triples, user_id=None):
        pass
    async def get(self, *, entity, user_id=None):
        return GraphResult()
    async def get_all(self, *, user_id=None, limit=100):
        return GraphResult()
    async def search(self, *, query, user_id=None, limit=10):
        return GraphResult()
    async def delete(self, *, entity=None, triple_id=None):
        pass
    async def delete_all(self, *, user_id=None):
        pass


class TestMemioInit:
    def test_single_provider(self):
        m = Memio(facts=FakeFactStore())
        assert m.facts is not None
        assert m.history is None
        assert m.documents is None
        assert m.graph is None

    def test_all_providers(self):
        m = Memio(
            facts=FakeFactStore(),
            history=FakeHistoryStore(),
            documents=FakeDocumentStore(),
            graph=FakeGraphStore(),
        )
        assert m.facts is not None
        assert m.history is not None
        assert m.documents is not None
        assert m.graph is not None

    def test_no_providers_raises(self):
        with pytest.raises(ValueError, match="At least one memory store"):
            Memio()

    def test_invalid_facts_type_raises(self):
        with pytest.raises(TypeError, match="facts must implement FactStore"):
            Memio(facts="not a store")

    def test_invalid_history_type_raises(self):
        with pytest.raises(TypeError, match="history must implement HistoryStore"):
            Memio(history="not a store")

    def test_invalid_documents_type_raises(self):
        with pytest.raises(TypeError, match="documents must implement DocumentStore"):
            Memio(documents="not a store")

    def test_invalid_graph_type_raises(self):
        with pytest.raises(TypeError, match="graph must implement GraphStore"):
            Memio(graph="not a store")


class TestMemioUsage:
    async def test_facts_namespace(self):
        m = Memio(facts=FakeFactStore())
        fact = await m.facts.add(content="likes coffee", user_id="u1")
        assert fact.content == "likes coffee"

    async def test_history_namespace(self):
        m = Memio(history=FakeHistoryStore())
        msgs = await m.history.get(session_id="s1")
        assert msgs == []

    async def test_documents_namespace(self):
        m = Memio(documents=FakeDocumentStore())
        doc = await m.documents.add(content="guide")
        assert doc.content == "guide"

    async def test_graph_namespace(self):
        m = Memio(graph=FakeGraphStore())
        result = await m.graph.search(query="Alice")
        assert isinstance(result, GraphResult)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_client.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'memio.client'`

- [ ] **Step 3: Implement the Memio client**

```python
# memio/client.py
from __future__ import annotations

from memio.protocols import DocumentStore, FactStore, GraphStore, HistoryStore


class Memio:
    def __init__(
        self,
        *,
        facts: FactStore | None = None,
        history: HistoryStore | None = None,
        documents: DocumentStore | None = None,
        graph: GraphStore | None = None,
    ):
        if not any([facts, history, documents, graph]):
            raise ValueError("At least one memory store must be provided")

        if facts is not None and not isinstance(facts, FactStore):
            raise TypeError("facts must implement FactStore protocol")
        if history is not None and not isinstance(history, HistoryStore):
            raise TypeError("history must implement HistoryStore protocol")
        if documents is not None and not isinstance(documents, DocumentStore):
            raise TypeError("documents must implement DocumentStore protocol")
        if graph is not None and not isinstance(graph, GraphStore):
            raise TypeError("graph must implement GraphStore protocol")

        self.facts = facts
        self.history = history
        self.documents = documents
        self.graph = graph
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_client.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add memio/client.py tests/test_client.py
git commit -m "feat: add Memio client with protocol validation and namespace wiring"
```

---

### Task 6: Package Exports

**Files:**
- Modify: `memio/__init__.py`

- [ ] **Step 1: Write the __init__.py with public exports**

```python
# memio/__init__.py
from memio.client import Memio
from memio.exceptions import MemioError, ProviderError
from memio.models import Document, Fact, GraphResult, Message, Triple
from memio.protocols import DocumentStore, FactStore, GraphStore, HistoryStore

__all__ = [
    "Memio",
    "FactStore",
    "HistoryStore",
    "DocumentStore",
    "GraphStore",
    "Fact",
    "Message",
    "Document",
    "Triple",
    "GraphResult",
    "MemioError",
    "ProviderError",
]
```

- [ ] **Step 2: Verify imports work**

```bash
python -c "from memio import Memio, Fact, FactStore, MemioError, ProviderError; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add memio/__init__.py
git commit -m "feat: add public API exports to memio package"
```

---

### Task 7: Conformance Test Suites

**Files:**
- Create: `tests/conformance/fact_store.py`
- Create: `tests/conformance/history_store.py`
- Create: `tests/conformance/document_store.py`
- Create: `tests/conformance/graph_store.py`

These are reusable test functions (not test classes) that any adapter can run against.

- [ ] **Step 1: Write FactStore conformance suite**

```python
# tests/conformance/fact_store.py
from memio.models import Fact
from memio.protocols import FactStore


async def fact_store_conformance(store: FactStore) -> None:
    """Run full CRUD conformance against a FactStore implementation."""
    # add
    fact = await store.add(content="likes coffee", user_id="test-user")
    assert isinstance(fact, Fact)
    assert fact.id is not None
    assert fact.content == "likes coffee"

    # get
    retrieved = await store.get(fact_id=fact.id)
    assert retrieved.id == fact.id
    assert retrieved.content == "likes coffee"

    # search
    results = await store.search(query="coffee", user_id="test-user")
    assert isinstance(results, list)
    assert any(f.id == fact.id for f in results)

    # update
    updated = await store.update(fact_id=fact.id, content="likes tea")
    assert updated.content == "likes tea"

    # get_all
    all_facts = await store.get_all(user_id="test-user")
    assert isinstance(all_facts, list)
    assert any(f.id == fact.id for f in all_facts)

    # delete
    await store.delete(fact_id=fact.id)
    after_delete = await store.search(query="tea", user_id="test-user")
    assert all(f.id != fact.id for f in after_delete)

    # delete_all
    await store.add(content="fact1", user_id="test-user-bulk")
    await store.add(content="fact2", user_id="test-user-bulk")
    await store.delete_all(user_id="test-user-bulk")
    remaining = await store.get_all(user_id="test-user-bulk")
    assert len(remaining) == 0
```

- [ ] **Step 2: Write HistoryStore conformance suite**

```python
# tests/conformance/history_store.py
from memio.models import Message
from memio.protocols import HistoryStore


async def history_store_conformance(store: HistoryStore) -> None:
    """Run full conformance against a HistoryStore implementation."""
    msgs = [
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
    ]

    # add
    await store.add(session_id="test-session", messages=msgs)

    # get
    retrieved = await store.get(session_id="test-session")
    assert isinstance(retrieved, list)
    assert len(retrieved) >= 2

    # search
    results = await store.search(session_id="test-session", query="hello")
    assert isinstance(results, list)

    # delete
    await store.delete(session_id="test-session")
    after_delete = await store.get(session_id="test-session")
    assert len(after_delete) == 0
```

- [ ] **Step 3: Write DocumentStore conformance suite**

```python
# tests/conformance/document_store.py
from memio.models import Document
from memio.protocols import DocumentStore


async def document_store_conformance(store: DocumentStore) -> None:
    """Run full CRUD conformance against a DocumentStore implementation."""
    # add
    doc = await store.add(content="deployment guide for production", metadata={"type": "docs"})
    assert isinstance(doc, Document)
    assert doc.id is not None
    assert doc.content == "deployment guide for production"

    # get
    retrieved = await store.get(doc_id=doc.id)
    assert retrieved.id == doc.id
    assert retrieved.content == "deployment guide for production"

    # search
    results = await store.search(query="deployment")
    assert isinstance(results, list)
    assert any(d.id == doc.id for d in results)

    # update
    updated = await store.update(doc_id=doc.id, content="updated deployment guide")
    assert updated.content == "updated deployment guide"

    # delete
    await store.delete(doc_id=doc.id)
    after_delete = await store.search(query="updated deployment")
    assert all(d.id != doc.id for d in after_delete)
```

- [ ] **Step 4: Write GraphStore conformance suite**

```python
# tests/conformance/graph_store.py
from memio.models import GraphResult, Triple
from memio.protocols import GraphStore


async def graph_store_conformance(store: GraphStore) -> None:
    """Run full conformance against a GraphStore implementation."""
    triples = [
        Triple(subject="Alice", predicate="works_at", object="Acme"),
        Triple(subject="Acme", predicate="is_a", object="startup"),
    ]

    # add
    await store.add(triples=triples, user_id="test-user")

    # search
    results = await store.search(query="Alice", user_id="test-user")
    assert isinstance(results, GraphResult)

    # get
    result = await store.get(entity="Alice", user_id="test-user")
    assert isinstance(result, GraphResult)

    # get_all
    all_results = await store.get_all(user_id="test-user")
    assert isinstance(all_results, GraphResult)

    # delete_all
    await store.delete_all(user_id="test-user")
    after_delete = await store.get_all(user_id="test-user")
    assert len(after_delete.triples) == 0
```

- [ ] **Step 5: Commit**

```bash
git add tests/conformance/
git commit -m "feat: add protocol conformance test suites for all memory types"
```

---

### Task 8: Chroma Document Adapter

**Files:**
- Create: `memio/providers/chroma/document.py`
- Modify: `memio/providers/chroma/__init__.py`
- Create: `tests/providers/test_chroma_doc.py`

- [ ] **Step 1: Write failing unit tests (mocked Chroma SDK)**

```python
# tests/providers/test_chroma_doc.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Document
from memio.exceptions import ProviderError


class TestChromaDocumentAdapter:
    def _make_adapter(self, mock_collection):
        """Create adapter with a mocked Chroma collection."""
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            from memio.providers.chroma.document import ChromaDocumentAdapter
            adapter = ChromaDocumentAdapter(client=mock_client, collection_name="test")
        return adapter

    async def test_add(self):
        mock_col = MagicMock()
        mock_col.add = MagicMock()
        adapter = self._make_adapter(mock_col)

        doc = await adapter.add(content="hello world", metadata={"k": "v"})

        assert isinstance(doc, Document)
        assert doc.content == "hello world"
        assert doc.id is not None
        mock_col.add.assert_called_once()

    async def test_add_with_explicit_id(self):
        mock_col = MagicMock()
        mock_col.add = MagicMock()
        adapter = self._make_adapter(mock_col)

        doc = await adapter.add(content="hello", doc_id="custom-id")

        assert doc.id == "custom-id"

    async def test_get(self):
        mock_col = MagicMock()
        mock_col.get.return_value = {
            "ids": ["d1"],
            "documents": ["hello world"],
            "metadatas": [{"k": "v"}],
        }
        adapter = self._make_adapter(mock_col)

        doc = await adapter.get(doc_id="d1")

        assert doc.id == "d1"
        assert doc.content == "hello world"
        assert doc.metadata == {"k": "v"}

    async def test_search(self):
        mock_col = MagicMock()
        mock_col.query.return_value = {
            "ids": [["d1", "d2"]],
            "documents": [["doc one", "doc two"]],
            "metadatas": [[{"k": "1"}, {"k": "2"}]],
            "distances": [[0.1, 0.5]],
        }
        adapter = self._make_adapter(mock_col)

        results = await adapter.search(query="test", limit=2)

        assert len(results) == 2
        assert results[0].id == "d1"
        assert results[0].content == "doc one"
        assert results[0].score is not None

    async def test_update(self):
        mock_col = MagicMock()
        mock_col.update = MagicMock()
        adapter = self._make_adapter(mock_col)

        doc = await adapter.update(doc_id="d1", content="updated")

        assert doc.id == "d1"
        assert doc.content == "updated"
        mock_col.update.assert_called_once()

    async def test_delete(self):
        mock_col = MagicMock()
        mock_col.delete = MagicMock()
        adapter = self._make_adapter(mock_col)

        await adapter.delete(doc_id="d1")

        mock_col.delete.assert_called_once_with(ids=["d1"])

    async def test_provider_error_wrapping(self):
        mock_col = MagicMock()
        mock_col.query.side_effect = RuntimeError("connection lost")
        adapter = self._make_adapter(mock_col)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test")
        assert exc_info.value.provider == "chroma"
        assert exc_info.value.operation == "search"
        assert isinstance(exc_info.value.cause, RuntimeError)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/providers/test_chroma_doc.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement ChromaDocumentAdapter**

```python
# memio/providers/chroma/document.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from memio.exceptions import ProviderError
from memio.models import Document


class ChromaDocumentAdapter:
    def __init__(self, *, client, collection_name: str):
        try:
            import chromadb  # noqa: F401
        except ImportError:
            raise ImportError(
                "chroma provider requires chromadb: pip install memio[chroma]"
            )
        self._collection = client.get_or_create_collection(name=collection_name)

    async def add(
        self,
        *,
        content: str,
        doc_id: str | None = None,
        metadata: dict | None = None,
    ) -> Document:
        try:
            doc_id = doc_id or str(uuid.uuid4())
            kwargs: dict = {"ids": [doc_id], "documents": [content]}
            if metadata is not None:
                kwargs["metadatas"] = [metadata]
            self._collection.add(**kwargs)
            return Document(
                id=doc_id,
                content=content,
                metadata=metadata,
                created_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            raise ProviderError("chroma", "add", e) from e

    async def get(self, *, doc_id: str) -> Document:
        try:
            result = self._collection.get(ids=[doc_id])
            return Document(
                id=result["ids"][0],
                content=result["documents"][0],
                metadata=result["metadatas"][0] if result["metadatas"] else None,
            )
        except Exception as e:
            raise ProviderError("chroma", "get", e) from e

    async def search(
        self,
        *,
        query: str,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Document]:
        try:
            kwargs: dict = {"query_texts": [query], "n_results": limit}
            if filters is not None:
                kwargs["where"] = filters
            result = self._collection.query(**kwargs)
            docs = []
            for i, doc_id in enumerate(result["ids"][0]):
                distance = result["distances"][0][i] if result.get("distances") else None
                score = 1.0 / (1.0 + distance) if distance is not None else None
                docs.append(Document(
                    id=doc_id,
                    content=result["documents"][0][i],
                    metadata=result["metadatas"][0][i] if result.get("metadatas") else None,
                    score=score,
                ))
            return docs
        except Exception as e:
            raise ProviderError("chroma", "search", e) from e

    async def update(
        self,
        *,
        doc_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Document:
        try:
            kwargs: dict = {"ids": [doc_id], "documents": [content]}
            if metadata is not None:
                kwargs["metadatas"] = [metadata]
            self._collection.update(**kwargs)
            return Document(
                id=doc_id,
                content=content,
                metadata=metadata,
                updated_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            raise ProviderError("chroma", "update", e) from e

    async def delete(self, *, doc_id: str) -> None:
        try:
            self._collection.delete(ids=[doc_id])
        except Exception as e:
            raise ProviderError("chroma", "delete", e) from e
```

- [ ] **Step 4: Update provider __init__.py**

```python
# memio/providers/chroma/__init__.py
from memio.providers.chroma.document import ChromaDocumentAdapter

__all__ = ["ChromaDocumentAdapter"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/providers/test_chroma_doc.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add memio/providers/chroma/ tests/providers/test_chroma_doc.py
git commit -m "feat: add ChromaDocumentAdapter with DocumentStore implementation"
```

---

### Task 9: mem0 Fact Adapter

**Files:**
- Create: `memio/providers/mem0/fact.py`
- Modify: `memio/providers/mem0/__init__.py`
- Create: `tests/providers/test_mem0_fact.py`

- [ ] **Step 1: Write failing unit tests (mocked mem0 SDK)**

```python
# tests/providers/test_mem0_fact.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Fact
from memio.exceptions import ProviderError


def _mock_mem0_module():
    """Create a mock mem0 module for import patching."""
    mock_module = MagicMock()
    mock_async_memory = MagicMock()
    mock_module.AsyncMemory = mock_async_memory
    return mock_module, mock_async_memory


class TestMem0FactAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"mem0": MagicMock()}):
            from memio.providers.mem0.fact import Mem0FactAdapter
            adapter = Mem0FactAdapter.__new__(Mem0FactAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_client.add.return_value = {
            "results": [{"id": "m1", "memory": "likes coffee", "event": "ADD"}]
        }
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(content="likes coffee", user_id="u1")

        assert isinstance(fact, Fact)
        assert fact.id == "m1"
        assert fact.content == "likes coffee"
        mock_client.add.assert_called_once()

    async def test_get(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "m1",
            "memory": "likes coffee",
            "user_id": "u1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "metadata": None,
        }
        adapter = self._make_adapter(mock_client)

        fact = await adapter.get(fact_id="m1")

        assert fact.id == "m1"
        assert fact.content == "likes coffee"

    async def test_search(self):
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "results": [
                {"id": "m1", "memory": "likes coffee", "score": 0.95},
                {"id": "m2", "memory": "prefers dark mode", "score": 0.80},
            ]
        }
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee", user_id="u1")

        assert len(results) == 2
        assert results[0].score == 0.95

    async def test_update(self):
        mock_client = AsyncMock()
        mock_client.update.return_value = {"message": "Memory updated successfully!"}
        adapter = self._make_adapter(mock_client)

        fact = await adapter.update(fact_id="m1", content="likes tea")

        assert fact.id == "m1"
        assert fact.content == "likes tea"

    async def test_delete(self):
        mock_client = AsyncMock()
        mock_client.delete.return_value = {"message": "Memory deleted successfully!"}
        adapter = self._make_adapter(mock_client)

        await adapter.delete(fact_id="m1")

        mock_client.delete.assert_called_once_with("m1")

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_client.delete_all.return_value = {"message": "Memories deleted successfully!"}
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all(user_id="u1")

        mock_client.delete_all.assert_called_once_with(user_id="u1")

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_client.get_all.return_value = {
            "results": [
                {"id": "m1", "memory": "likes coffee"},
                {"id": "m2", "memory": "prefers dark mode"},
            ]
        }
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all(user_id="u1")

        assert len(results) == 2

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.search.side_effect = RuntimeError("api error")
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "mem0"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/providers/test_mem0_fact.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement Mem0FactAdapter**

```python
# memio/providers/mem0/fact.py
from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Fact


class Mem0FactAdapter:
    def __init__(self, *, api_key: str | None = None, config: dict | None = None):
        try:
            from mem0 import AsyncMemory
        except ImportError:
            raise ImportError(
                "mem0 provider requires mem0ai: pip install memio[mem0]"
            )
        kwargs = {}
        if config:
            kwargs["config"] = config
        self._client = AsyncMemory(**kwargs)

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"messages": content}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if metadata:
                kwargs["metadata"] = metadata
            result = await self._client.add(**kwargs)
            entry = result["results"][0]
            return Fact(
                id=entry["id"],
                content=entry["memory"],
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata,
            )
        except Exception as e:
            raise ProviderError("mem0", "add", e) from e

    async def get(self, *, fact_id: str) -> Fact:
        try:
            result = await self._client.get(fact_id)
            return self._to_fact(result)
        except Exception as e:
            raise ProviderError("mem0", "get", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Fact]:
        try:
            kwargs: dict = {"query": query, "limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if filters:
                kwargs["filters"] = filters
            result = await self._client.search(**kwargs)
            return [self._to_fact(entry) for entry in result["results"]]
        except Exception as e:
            raise ProviderError("mem0", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            await self._client.update(fact_id, data=content)
            return Fact(id=fact_id, content=content, metadata=metadata)
        except Exception as e:
            raise ProviderError("mem0", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        try:
            await self._client.delete(fact_id)
        except Exception as e:
            raise ProviderError("mem0", "delete", e) from e

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        try:
            kwargs: dict = {}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            await self._client.delete_all(**kwargs)
        except Exception as e:
            raise ProviderError("mem0", "delete_all", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        try:
            kwargs: dict = {"limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            result = await self._client.get_all(**kwargs)
            return [self._to_fact(entry) for entry in result["results"]]
        except Exception as e:
            raise ProviderError("mem0", "get_all", e) from e

    @staticmethod
    def _to_fact(entry: dict) -> Fact:
        created_at = None
        if entry.get("created_at"):
            try:
                created_at = datetime.fromisoformat(entry["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if entry.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(entry["updated_at"])
            except (ValueError, TypeError):
                pass
        return Fact(
            id=entry["id"],
            content=entry["memory"],
            user_id=entry.get("user_id"),
            agent_id=entry.get("agent_id"),
            metadata=entry.get("metadata"),
            score=entry.get("score"),
            created_at=created_at,
            updated_at=updated_at,
        )
```

- [ ] **Step 4: Update provider __init__.py**

```python
# memio/providers/mem0/__init__.py
from memio.providers.mem0.fact import Mem0FactAdapter

__all__ = ["Mem0FactAdapter"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/providers/test_mem0_fact.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add memio/providers/mem0/ tests/providers/test_mem0_fact.py
git commit -m "feat: add Mem0FactAdapter with FactStore implementation"
```

---

### Task 10: mem0 Graph Adapter

**Files:**
- Create: `memio/providers/mem0/graph.py`
- Modify: `memio/providers/mem0/__init__.py`
- Create: `tests/providers/test_mem0_graph.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/providers/test_mem0_graph.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import GraphResult, Triple
from memio.exceptions import ProviderError


class TestMem0GraphAdapter:
    def _make_adapter(self, mock_client, mock_graph):
        with patch.dict("sys.modules", {"mem0": MagicMock()}):
            from memio.providers.mem0.graph import Mem0GraphAdapter
            adapter = Mem0GraphAdapter.__new__(Mem0GraphAdapter)
            adapter._client = mock_client
            adapter._graph = mock_graph
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.add.return_value = {"added_entities": ["Alice", "Acme"]}
        adapter = self._make_adapter(mock_client, mock_graph)

        triples = [Triple(subject="Alice", predicate="works_at", object="Acme")]
        await adapter.add(triples=triples, user_id="u1")

        mock_graph.add.assert_called_once()

    async def test_search(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.search.return_value = [
            {"source": "Alice", "relationship": "works_at", "destination": "Acme"},
        ]
        adapter = self._make_adapter(mock_client, mock_graph)

        result = await adapter.search(query="Alice", user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1
        assert result.triples[0].subject == "Alice"
        assert result.triples[0].predicate == "works_at"
        assert result.triples[0].object == "Acme"

    async def test_get(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.get_all.return_value = [
            {"source": "Alice", "relationship": "works_at", "destination": "Acme"},
            {"source": "Bob", "relationship": "knows", "destination": "Alice"},
        ]
        adapter = self._make_adapter(mock_client, mock_graph)

        result = await adapter.get(entity="Alice", user_id="u1")

        assert isinstance(result, GraphResult)
        # Should filter to triples involving "Alice"
        for t in result.triples:
            assert "Alice" in (t.subject, t.object)

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.get_all.return_value = [
            {"source": "Alice", "relationship": "works_at", "destination": "Acme"},
        ]
        adapter = self._make_adapter(mock_client, mock_graph)

        result = await adapter.get_all(user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        adapter = self._make_adapter(mock_client, mock_graph)

        await adapter.delete_all(user_id="u1")

        mock_graph.delete_all.assert_called_once()

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.search.side_effect = RuntimeError("graph error")
        adapter = self._make_adapter(mock_client, mock_graph)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "mem0"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/providers/test_mem0_graph.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement Mem0GraphAdapter**

```python
# memio/providers/mem0/graph.py
from __future__ import annotations

from memio.exceptions import ProviderError
from memio.models import GraphResult, Triple


class Mem0GraphAdapter:
    def __init__(self, *, api_key: str | None = None, config: dict | None = None):
        try:
            from mem0 import AsyncMemory
        except ImportError:
            raise ImportError(
                "mem0 provider requires mem0ai: pip install memio[mem0]"
            )
        kwargs = {}
        if config:
            kwargs["config"] = config
        client = AsyncMemory(**kwargs)
        self._client = client
        self._graph = client.graph

    async def add(
        self,
        *,
        triples: list[Triple],
        user_id: str | None = None,
    ) -> None:
        try:
            # Serialize triples to natural language for mem0's LLM extraction
            data = "\n".join(
                f"{t.subject} {t.predicate} {t.object}" for t in triples
            )
            filters: dict = {}
            if user_id:
                filters["user_id"] = user_id
            else:
                filters["user_id"] = "user"
            self._graph.add(data, filters)
        except Exception as e:
            raise ProviderError("mem0", "add", e) from e

    async def get(
        self,
        *,
        entity: str,
        user_id: str | None = None,
    ) -> GraphResult:
        try:
            filters: dict = {"user_id": user_id or "user"}
            raw = self._graph.get_all(filters)
            # Filter to triples involving the entity
            triples = []
            nodes = set()
            for entry in raw:
                src = entry.get("source", "")
                dst = entry.get("destination", entry.get("target", ""))
                if entity in (src, dst):
                    triples.append(Triple(
                        subject=src,
                        predicate=entry.get("relationship", ""),
                        object=dst,
                    ))
                    nodes.add(src)
                    nodes.add(dst)
            return GraphResult(triples=triples, nodes=sorted(nodes))
        except Exception as e:
            raise ProviderError("mem0", "get", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> GraphResult:
        try:
            filters: dict = {"user_id": user_id or "user"}
            raw = self._graph.get_all(filters, limit=limit)
            return self._raw_to_graph_result(raw)
        except Exception as e:
            raise ProviderError("mem0", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        limit: int = 10,
    ) -> GraphResult:
        try:
            filters: dict = {"user_id": user_id or "user"}
            raw = self._graph.search(query, filters, limit=limit)
            return self._raw_to_graph_result(raw)
        except Exception as e:
            raise ProviderError("mem0", "search", e) from e

    async def delete(
        self,
        *,
        entity: str | None = None,
        triple_id: str | None = None,
    ) -> None:
        # mem0 does not support individual entity/relationship deletes
        raise ProviderError(
            "mem0", "delete",
            NotImplementedError("mem0 graph does not support individual deletes; use delete_all"),
        )

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            filters: dict = {"user_id": user_id or "user"}
            self._graph.delete_all(filters)
        except Exception as e:
            raise ProviderError("mem0", "delete_all", e) from e

    @staticmethod
    def _raw_to_graph_result(raw: list[dict]) -> GraphResult:
        triples = []
        nodes = set()
        for entry in raw:
            src = entry.get("source", "")
            dst = entry.get("destination", entry.get("target", ""))
            triples.append(Triple(
                subject=src,
                predicate=entry.get("relationship", ""),
                object=dst,
            ))
            nodes.add(src)
            nodes.add(dst)
        return GraphResult(triples=triples, nodes=sorted(nodes))
```

- [ ] **Step 4: Update provider __init__.py**

```python
# memio/providers/mem0/__init__.py
from memio.providers.mem0.fact import Mem0FactAdapter
from memio.providers.mem0.graph import Mem0GraphAdapter

__all__ = ["Mem0FactAdapter", "Mem0GraphAdapter"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/providers/test_mem0_graph.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add memio/providers/mem0/ tests/providers/test_mem0_graph.py
git commit -m "feat: add Mem0GraphAdapter with GraphStore implementation"
```

---

### Task 11: Zep History Adapter

**Files:**
- Create: `memio/providers/zep/history.py`
- Modify: `memio/providers/zep/__init__.py`
- Create: `tests/providers/test_zep_history.py`

- [ ] **Step 1: Write failing unit tests (mocked Zep SDK)**

```python
# tests/providers/test_zep_history.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Message
from memio.exceptions import ProviderError


def _mock_zep_message(role, content, created_at=None):
    msg = MagicMock()
    msg.role = role
    msg.role_type = role
    msg.content = content
    msg.created_at = created_at or "2026-01-01T00:00:00Z"
    msg.metadata = None
    msg.name = None
    return msg


class TestZepHistoryAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {
            "zep_cloud": MagicMock(),
            "zep_cloud.types": MagicMock(),
        }):
            from memio.providers.zep.history import ZepHistoryAdapter
            adapter = ZepHistoryAdapter.__new__(ZepHistoryAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.create = AsyncMock()
        mock_client.thread.add_messages = AsyncMock()
        adapter = self._make_adapter(mock_client)

        messages = [
            Message(role="user", content="hello"),
            Message(role="assistant", content="hi"),
        ]
        await adapter.add(session_id="s1", messages=messages)

        mock_client.thread.add_messages.assert_called_once()

    async def test_get(self):
        mock_response = MagicMock()
        mock_response.messages = [
            _mock_zep_message("user", "hello"),
            _mock_zep_message("assistant", "hi"),
        ]
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.get = AsyncMock(return_value=mock_response)
        adapter = self._make_adapter(mock_client)

        messages = await adapter.get(session_id="s1", limit=10)

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "hello"

    async def test_search(self):
        mock_episode = MagicMock()
        mock_episode.thread_id = "s1"
        mock_episode.role = "user"
        mock_episode.content = "hello there"
        mock_results = MagicMock()
        mock_results.episodes = [mock_episode]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        messages = await adapter.search(session_id="s1", query="hello")

        assert len(messages) == 1
        assert messages[0].content == "hello there"

    async def test_search_filters_by_session(self):
        ep1 = MagicMock()
        ep1.thread_id = "s1"
        ep1.role = "user"
        ep1.content = "hello"
        ep2 = MagicMock()
        ep2.thread_id = "s2"
        ep2.role = "user"
        ep2.content = "other session"
        mock_results = MagicMock()
        mock_results.episodes = [ep1, ep2]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        messages = await adapter.search(session_id="s1", query="hello")

        assert len(messages) == 1
        assert messages[0].content == "hello"

    async def test_delete(self):
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.delete = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete(session_id="s1")

        mock_client.thread.delete.assert_called_once_with("s1")

    async def test_provider_error_wrapping(self):
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.get = AsyncMock(side_effect=RuntimeError("api error"))
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.get(session_id="s1")
        assert exc_info.value.provider == "zep"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/providers/test_zep_history.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement ZepHistoryAdapter**

```python
# memio/providers/zep/history.py
from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Message


class ZepHistoryAdapter:
    def __init__(self, *, api_key: str | None = None, client=None):
        try:
            from zep_cloud import AsyncZep
        except ImportError:
            raise ImportError(
                "zep provider requires zep-cloud: pip install memio[zep]"
            )
        if client is not None:
            self._client = client
        else:
            self._client = AsyncZep(api_key=api_key)

    async def add(self, *, session_id: str, messages: list[Message]) -> None:
        try:
            from zep_cloud.types import Message as ZepMessage

            # Ensure thread exists
            try:
                await self._client.thread.create(thread_id=session_id, user_id=session_id)
            except Exception:
                pass  # Thread may already exist

            zep_messages = [
                ZepMessage(role=m.role, content=m.content, role_type=m.role)
                for m in messages
            ]
            await self._client.thread.add_messages(
                thread_id=session_id, messages=zep_messages,
            )
        except Exception as e:
            raise ProviderError("zep", "add", e) from e

    async def get(
        self,
        *,
        session_id: str,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[Message]:
        try:
            kwargs: dict = {"thread_id": session_id, "limit": limit}
            if cursor:
                kwargs["cursor"] = cursor
            response = await self._client.thread.get(**kwargs)
            messages = response.messages or []
            return [self._to_message(m) for m in messages]
        except Exception as e:
            raise ProviderError("zep", "get", e) from e

    async def search(
        self,
        *,
        session_id: str,
        query: str,
        limit: int = 10,
    ) -> list[Message]:
        try:
            response = await self._client.graph.search(
                query=query, limit=limit,
            )
            results = []
            for episode in response.episodes or []:
                if getattr(episode, "thread_id", None) == session_id:
                    results.append(Message(
                        role=getattr(episode, "role", "user"),
                        content=episode.content,
                    ))
            return results[:limit]
        except Exception as e:
            raise ProviderError("zep", "search", e) from e

    async def delete(self, *, session_id: str) -> None:
        try:
            await self._client.thread.delete(session_id)
        except Exception as e:
            raise ProviderError("zep", "delete", e) from e

    @staticmethod
    def _to_message(zep_msg) -> Message:
        timestamp = None
        if hasattr(zep_msg, "created_at") and zep_msg.created_at:
            try:
                timestamp = datetime.fromisoformat(str(zep_msg.created_at))
            except (ValueError, TypeError):
                pass
        return Message(
            role=zep_msg.role_type or zep_msg.role or "user",
            content=zep_msg.content,
            metadata=getattr(zep_msg, "metadata", None),
            timestamp=timestamp,
            name=getattr(zep_msg, "name", None),
        )
```

- [ ] **Step 4: Update provider __init__.py**

```python
# memio/providers/zep/__init__.py
from memio.providers.zep.history import ZepHistoryAdapter

__all__ = ["ZepHistoryAdapter"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/providers/test_zep_history.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add memio/providers/zep/ tests/providers/test_zep_history.py
git commit -m "feat: add ZepHistoryAdapter with HistoryStore implementation"
```

---

### Task 12: Zep Fact Adapter

**Files:**
- Create: `memio/providers/zep/fact.py`
- Modify: `memio/providers/zep/__init__.py`
- Create: `tests/providers/test_zep_fact.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/providers/test_zep_fact.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Fact
from memio.exceptions import ProviderError


def _mock_zep_edge(uuid_, fact, name, source_uuid, target_uuid, created_at=None):
    edge = MagicMock()
    edge.uuid_ = uuid_
    edge.fact = fact
    edge.name = name
    edge.source_node_uuid = source_uuid
    edge.target_node_uuid = target_uuid
    edge.created_at = created_at or "2026-01-01T00:00:00Z"
    edge.attributes = None
    edge.score = 0.9
    return edge


class TestZepFactAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {
            "zep_cloud": MagicMock(),
            "zep_cloud.types": MagicMock(),
        }):
            from memio.providers.zep.fact import ZepFactAdapter
            adapter = ZepFactAdapter.__new__(ZepFactAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_episode = MagicMock()
        mock_episode.uuid_ = "ep1"
        mock_episode.content = "likes coffee"
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.add = AsyncMock(return_value=mock_episode)
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(content="likes coffee", user_id="u1")

        assert isinstance(fact, Fact)
        assert fact.content == "likes coffee"

    async def test_search(self):
        mock_results = MagicMock()
        mock_results.edges = [
            _mock_zep_edge("e1", "likes coffee", "LIKES", "n1", "n2"),
        ]
        mock_results.nodes = []
        mock_results.episodes = []
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee", user_id="u1")

        assert len(results) == 1
        assert results[0].content == "likes coffee"

    async def test_get(self):
        mock_edge = _mock_zep_edge("e1", "likes coffee", "LIKES", "n1", "n2")
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.edge.get = AsyncMock(return_value=mock_edge)
        adapter = self._make_adapter(mock_client)

        fact = await adapter.get(fact_id="e1")

        assert fact.id == "e1"
        assert fact.content == "likes coffee"

    async def test_update(self):
        mock_edge = _mock_zep_edge("e1", "likes tea", "LIKES", "n1", "n2")
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.edge.update = AsyncMock(return_value=mock_edge)
        adapter = self._make_adapter(mock_client)

        fact = await adapter.update(fact_id="e1", content="likes tea")

        assert fact.content == "likes tea"

    async def test_delete_raises_not_implemented(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.delete(fact_id="e1")
        assert isinstance(exc_info.value.cause, NotImplementedError)

    async def test_delete_all(self):
        mock_client = MagicMock()
        mock_client.user = MagicMock()
        mock_client.user.delete = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all(user_id="u1")

        mock_client.user.delete.assert_called_once_with("u1")

    async def test_get_all(self):
        mock_edges = [
            _mock_zep_edge("e1", "likes coffee", "LIKES", "n1", "n2"),
            _mock_zep_edge("e2", "prefers dark mode", "PREFERS", "n1", "n3", uuid_="e2"),
        ]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.edge.get_by_user_id = AsyncMock(return_value=mock_edges)
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all(user_id="u1")

        assert len(results) == 2

    async def test_provider_error_wrapping(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(side_effect=RuntimeError("fail"))
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "zep"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/providers/test_zep_fact.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement ZepFactAdapter**

```python
# memio/providers/zep/fact.py
from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Fact


class ZepFactAdapter:
    def __init__(self, *, api_key: str | None = None, client=None):
        try:
            from zep_cloud import AsyncZep
        except ImportError:
            raise ImportError(
                "zep provider requires zep-cloud: pip install memio[zep]"
            )
        if client is not None:
            self._client = client
        else:
            self._client = AsyncZep(api_key=api_key)

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"data": content, "type": "text"}
            if user_id:
                kwargs["user_id"] = user_id
            episode = await self._client.graph.add(**kwargs)
            return Fact(
                id=episode.uuid_,
                content=content,
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata,
            )
        except Exception as e:
            raise ProviderError("zep", "add", e) from e

    async def get(self, *, fact_id: str) -> Fact:
        try:
            edge = await self._client.graph.edge.get(fact_id)
            return self._edge_to_fact(edge)
        except Exception as e:
            raise ProviderError("zep", "get", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Fact]:
        try:
            kwargs: dict = {"query": query, "limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            results = await self._client.graph.search(**kwargs)
            facts = []
            for edge in results.edges or []:
                facts.append(self._edge_to_fact(edge))
            return facts
        except Exception as e:
            raise ProviderError("zep", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"fact": content}
            if metadata:
                kwargs["attributes"] = metadata
            edge = await self._client.graph.edge.update(fact_id, **kwargs)
            return self._edge_to_fact(edge)
        except Exception as e:
            raise ProviderError("zep", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        # Zep doesn't have direct edge delete in the public API
        # This is a limitation — raise clear error
        raise ProviderError(
            "zep", "delete",
            NotImplementedError("Zep does not support deleting individual facts"),
        )

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        try:
            if user_id:
                await self._client.user.delete(user_id)
        except Exception as e:
            raise ProviderError("zep", "delete_all", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        try:
            if user_id:
                edges = await self._client.graph.edge.get_by_user_id(
                    user_id, limit=limit,
                )
            else:
                edges = []
            return [self._edge_to_fact(edge) for edge in edges]
        except Exception as e:
            raise ProviderError("zep", "get_all", e) from e

    @staticmethod
    def _edge_to_fact(edge) -> Fact:
        created_at = None
        if hasattr(edge, "created_at") and edge.created_at:
            try:
                created_at = datetime.fromisoformat(str(edge.created_at))
            except (ValueError, TypeError):
                pass
        return Fact(
            id=edge.uuid_,
            content=edge.fact,
            metadata=getattr(edge, "attributes", None),
            score=getattr(edge, "score", None),
            created_at=created_at,
        )
```

- [ ] **Step 4: Update provider __init__.py**

```python
# memio/providers/zep/__init__.py
from memio.providers.zep.fact import ZepFactAdapter
from memio.providers.zep.history import ZepHistoryAdapter

__all__ = ["ZepFactAdapter", "ZepHistoryAdapter"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/providers/test_zep_fact.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add memio/providers/zep/ tests/providers/test_zep_fact.py
git commit -m "feat: add ZepFactAdapter with FactStore implementation"
```

---

### Task 13: Zep Graph Adapter

**Files:**
- Create: `memio/providers/zep/graph.py`
- Modify: `memio/providers/zep/__init__.py`
- Create: `tests/providers/test_zep_graph.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/providers/test_zep_graph.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import GraphResult, Triple
from memio.exceptions import ProviderError


def _mock_zep_node(name, uuid_="n1", summary=""):
    node = MagicMock()
    node.name = name
    node.uuid_ = uuid_
    node.summary = summary
    return node


def _mock_zep_edge(fact, name, source_uuid, target_uuid, uuid_="e1"):
    edge = MagicMock()
    edge.uuid_ = uuid_
    edge.fact = fact
    edge.name = name
    edge.source_node_uuid = source_uuid
    edge.target_node_uuid = target_uuid
    return edge


class TestZepGraphAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {
            "zep_cloud": MagicMock(),
        }):
            from memio.providers.zep.graph import ZepGraphAdapter
            adapter = ZepGraphAdapter.__new__(ZepGraphAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.add_fact_triple = AsyncMock()
        adapter = self._make_adapter(mock_client)

        triples = [Triple(subject="Alice", predicate="works_at", object="Acme")]
        await adapter.add(triples=triples, user_id="u1")

        mock_client.graph.add_fact_triple.assert_called_once()

    async def test_search(self):
        mock_results = MagicMock()
        mock_results.edges = [
            _mock_zep_edge("Alice works at Acme", "WORKS_AT", "n1", "n2"),
        ]
        mock_results.nodes = [
            _mock_zep_node("Alice", "n1"),
            _mock_zep_node("Acme", "n2"),
        ]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        result = await adapter.search(query="Alice", user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1

    async def test_get_all(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.node = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.node.get_by_user_id = AsyncMock(return_value=[
            _mock_zep_node("Alice", "n1"),
            _mock_zep_node("Acme", "n2"),
        ])
        mock_client.graph.edge.get_by_user_id = AsyncMock(return_value=[
            _mock_zep_edge("Alice works at Acme", "WORKS_AT", "n1", "n2"),
        ])
        adapter = self._make_adapter(mock_client)

        result = await adapter.get_all(user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1
        assert len(result.nodes) >= 1

    async def test_delete_all(self):
        mock_client = MagicMock()
        mock_client.user = MagicMock()
        mock_client.user.delete = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all(user_id="u1")

        mock_client.user.delete.assert_called_once_with("u1")

    async def test_provider_error_wrapping(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(side_effect=RuntimeError("fail"))
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "zep"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/providers/test_zep_graph.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement ZepGraphAdapter**

```python
# memio/providers/zep/graph.py
from __future__ import annotations

from memio.exceptions import ProviderError
from memio.models import GraphResult, Triple


class ZepGraphAdapter:
    def __init__(self, *, api_key: str | None = None, client=None):
        try:
            from zep_cloud import AsyncZep
        except ImportError:
            raise ImportError(
                "zep provider requires zep-cloud: pip install memio[zep]"
            )
        if client is not None:
            self._client = client
        else:
            self._client = AsyncZep(api_key=api_key)

    async def add(
        self,
        *,
        triples: list[Triple],
        user_id: str | None = None,
    ) -> None:
        try:
            for t in triples:
                kwargs: dict = {
                    "fact": f"{t.subject} {t.predicate} {t.object}",
                    "fact_name": t.predicate.upper().replace(" ", "_"),
                    "source_node_name": t.subject,
                    "target_node_name": t.object,
                }
                if t.metadata:
                    kwargs["edge_attributes"] = t.metadata
                if user_id:
                    kwargs["user_id"] = user_id
                await self._client.graph.add_fact_triple(**kwargs)
        except Exception as e:
            raise ProviderError("zep", "add", e) from e

    async def get(
        self,
        *,
        entity: str,
        user_id: str | None = None,
    ) -> GraphResult:
        try:
            # Get all nodes/edges for user, filter by entity name
            all_result = await self.get_all(user_id=user_id)
            filtered_triples = [
                t for t in all_result.triples
                if entity in (t.subject, t.object)
            ]
            nodes = set()
            for t in filtered_triples:
                nodes.add(t.subject)
                nodes.add(t.object)
            return GraphResult(triples=filtered_triples, nodes=sorted(nodes))
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError("zep", "get", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> GraphResult:
        try:
            kwargs: dict = {"limit": limit}
            if user_id:
                nodes_raw = await self._client.graph.node.get_by_user_id(
                    user_id, **kwargs,
                )
                edges_raw = await self._client.graph.edge.get_by_user_id(
                    user_id, **kwargs,
                )
            else:
                nodes_raw = []
                edges_raw = []

            # Build node name lookup
            node_names: dict[str, str] = {}
            for n in nodes_raw:
                node_names[n.uuid_] = n.name

            triples = []
            for e in edges_raw:
                src = node_names.get(e.source_node_uuid, e.source_node_uuid)
                dst = node_names.get(e.target_node_uuid, e.target_node_uuid)
                triples.append(Triple(
                    subject=src,
                    predicate=e.name,
                    object=dst,
                ))

            return GraphResult(
                triples=triples,
                nodes=sorted(node_names.values()),
            )
        except Exception as e:
            raise ProviderError("zep", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        limit: int = 10,
    ) -> GraphResult:
        try:
            kwargs: dict = {"query": query, "limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            results = await self._client.graph.search(**kwargs)

            # Build node name lookup from search results
            node_names: dict[str, str] = {}
            for n in results.nodes or []:
                node_names[n.uuid_] = n.name

            triples = []
            for e in results.edges or []:
                src = node_names.get(e.source_node_uuid, e.source_node_uuid)
                dst = node_names.get(e.target_node_uuid, e.target_node_uuid)
                triples.append(Triple(
                    subject=src,
                    predicate=e.name,
                    object=dst,
                ))

            return GraphResult(
                triples=triples,
                nodes=sorted(node_names.values()),
            )
        except Exception as e:
            raise ProviderError("zep", "search", e) from e

    async def delete(
        self,
        *,
        entity: str | None = None,
        triple_id: str | None = None,
    ) -> None:
        # Zep doesn't have direct entity/edge delete in a way that maps cleanly
        raise ProviderError(
            "zep", "delete",
            NotImplementedError("Zep does not support individual entity/triple deletes; use delete_all"),
        )

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            if user_id:
                await self._client.user.delete(user_id)
        except Exception as e:
            raise ProviderError("zep", "delete_all", e) from e
```

- [ ] **Step 4: Update provider __init__.py**

```python
# memio/providers/zep/__init__.py
from memio.providers.zep.fact import ZepFactAdapter
from memio.providers.zep.graph import ZepGraphAdapter
from memio.providers.zep.history import ZepHistoryAdapter

__all__ = ["ZepFactAdapter", "ZepGraphAdapter", "ZepHistoryAdapter"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/providers/test_zep_graph.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add memio/providers/zep/ tests/providers/test_zep_graph.py
git commit -m "feat: add ZepGraphAdapter with GraphStore implementation"
```

---

### Task 14: Full Test Suite Verification

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

```bash
pytest -v
```

Expected: All tests PASS across all test files.

- [ ] **Step 2: Verify package imports end-to-end**

```bash
python -c "
from memio import Memio, Fact, Message, Document, Triple, GraphResult
from memio import FactStore, HistoryStore, DocumentStore, GraphStore
from memio import MemioError, ProviderError
print('Core imports OK')
"
```

Expected: `Core imports OK`

- [ ] **Step 3: Verify provider imports (will warn if SDKs not installed)**

```bash
python -c "
try:
    from memio.providers.chroma import ChromaDocumentAdapter
    print('chroma OK')
except ImportError as e:
    print(f'chroma: {e}')

try:
    from memio.providers.mem0 import Mem0FactAdapter, Mem0GraphAdapter
    print('mem0 OK')
except ImportError as e:
    print(f'mem0: {e}')

try:
    from memio.providers.zep import ZepFactAdapter, ZepHistoryAdapter, ZepGraphAdapter
    print('zep OK')
except ImportError as e:
    print(f'zep: {e}')
"
```

Expected: Either `OK` or clear `ImportError` with install instructions for each.

- [ ] **Step 4: Final commit with all passing**

```bash
git add -A
git commit -m "feat: complete memio v0.1 — all tests passing"
```
