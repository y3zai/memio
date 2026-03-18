# memio — Unified Memory Gateway for AI Agents

A Python SDK that provides a single, consistent API to access multiple agent memory systems (mem0, Zep, Chroma, etc.), similar to how OpenRouter unifies LLM access.

## Target User

Application developers building AI agents who want to swap or compose memory providers without rewriting code.

## Requirements

- Python >= 3.10 (uses PEP 604 `X | Y` union syntax)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python first, TypeScript later | AI/agent ecosystem is Python-first; mem0, Zep, Chroma all have Python SDKs |
| Memory types | Facts, History, Documents, Graph | Covers the distinct things providers call "memory"; each is a Protocol |
| Multi-provider | Composable — multiple providers behind one client | Real apps need different backends for different memory types |
| Architecture | Direct injection — no registry, no middleware | Simplest design; namespace boundary allows adding complexity later |
| Async | Async-first | Memory operations are I/O-bound; agent ecosystem is moving async |
| Client API | Namespaced: `m.facts.add(...)` | Uniform methods per namespace (add/search/update/delete); scales cleanly |
| Adapters | One class per memory type per provider | Avoids method name collisions; each class is small and focused |
| Dependencies | Zero core deps; provider SDKs as optional extras | Minimal footprint; install only what you use |
| Errors | MemioError + ProviderError (wraps provider exceptions) | Two exceptions total; YAGNI on per-operation error types |
| Initial providers | mem0 (facts, graph), Zep (facts, history, graph), Chroma (documents) | Three providers to validate the abstraction across all four memory types |

## Memory Types

Four distinct memory types, each representing a different way agents store and retrieve information:

**Facts** — short, structured knowledge about users/agents. Typically LLM-extracted from conversations. Examples: "Alice prefers dark mode", "Alice is a data scientist". Provider does extraction, deduplication, merging. Backed by vector search internally.

**History** — conversation message logs. Raw or summarized sequences of messages with roles, timestamps, and metadata. Used to maintain conversational context across sessions.

**Documents** — longer content chunks stored for retrieval (classic RAG). Developer ingests text directly; provider stores embeddings and retrieves by similarity. No LLM processing on ingest.

**Graph** — entities and their relationships as subject-predicate-object triples. Examples: ("Alice", "works_at", "Acme"), ("Acme", "is_a", "fintech startup"). Supports relationship-aware queries.

## Protocols

Each memory type is defined as a `runtime_checkable` Python `Protocol`. Providers implement whichever protocols they support. No base class inheritance required.

### FactStore

```python
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
```

### HistoryStore

```python
@runtime_checkable
class HistoryStore(Protocol):
    async def add(self, *, session_id: str, messages: list[Message]) -> None: ...
    async def get(self, *, session_id: str, limit: int = 50,
                  cursor: str | None = None) -> list[Message]: ...
    async def search(self, *, session_id: str, query: str,
                     limit: int = 10) -> list[Message]: ...
    async def delete(self, *, session_id: str) -> None: ...
```

### DocumentStore

```python
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
```

### GraphStore

```python
@runtime_checkable
class GraphStore(Protocol):
    async def add(self, *, triples: list[Triple]) -> None: ...
    async def get(self, *, entity: str) -> GraphResult: ...
    async def get_all(self, *, user_id: str | None = None,
                      limit: int = 100) -> GraphResult: ...
    async def search(self, *, query: str, user_id: str | None = None,
                     limit: int = 10) -> GraphResult: ...
    async def delete(self, *, entity: str | None = None,
                     triple_id: str | None = None) -> None: ...
    async def delete_all(self, *, user_id: str | None = None) -> None: ...
```

## Data Models

Dataclasses with no external dependencies (no Pydantic). Fields with `score` are only populated on search results.

```python
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
    role: str                          # "user", "assistant", "system"
    content: str
    metadata: dict | None = None
    timestamp: datetime | None = None
    name: str | None = None            # sender name

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

## Client

The `Memio` class wires namespaces to providers via direct injection. No registry, no auto-discovery.

```python
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

        # runtime_checkable Protocol validation
        if facts is not None and not isinstance(facts, FactStore):
            raise TypeError("facts must implement FactStore protocol")
        # ... same for history, documents, graph

        self.facts = facts
        self.history = history
        self.documents = documents
        self.graph = graph
```

Usage:

```python
from memio import Memio
from memio.providers.mem0 import Mem0FactAdapter, Mem0GraphAdapter
from memio.providers.zep import ZepHistoryAdapter
from memio.providers.chroma import ChromaDocumentAdapter

m = Memio(
    facts=Mem0FactAdapter(api_key="..."),
    history=ZepHistoryAdapter(api_key="..."),
    graph=Mem0GraphAdapter(api_key="..."),
    documents=ChromaDocumentAdapter(client=chroma_client, collection_name="docs"),
)

await m.facts.add(content="User prefers dark mode", user_id="alice")
results = await m.facts.search(query="preferences", user_id="alice")

await m.history.add(session_id="s1", messages=[...])
messages = await m.history.get(session_id="s1", limit=10)

await m.documents.add(content="Deploy guide: ...", metadata={"type": "docs"})
docs = await m.documents.search(query="how to deploy", limit=5)
```

Accessing an unconfigured namespace raises `AttributeError` on `None` — no custom exception needed.

## Provider Adapters

One adapter class per memory type per provider. Adapters from the same provider can share a client instance.

### Provider-to-Protocol Mapping

| Provider | FactStore | HistoryStore | DocumentStore | GraphStore |
|----------|-----------|-------------|---------------|------------|
| mem0 | Mem0FactAdapter | - | - | Mem0GraphAdapter |
| Zep | ZepFactAdapter | ZepHistoryAdapter | - | ZepGraphAdapter |
| Chroma | - | - | ChromaDocumentAdapter | - |

### API Translation

**mem0 FactStore mapping:**
- `add(content, user_id)` -> `memory.add(messages=content, user_id=user_id)` -> translate response to `Fact`
- `get(fact_id)` -> `memory.get(memory_id=fact_id)` -> translate `MemoryItem` to `Fact`
- `search(query, user_id, limit)` -> `memory.search(query=query, user_id=user_id, limit=limit)` -> translate `MemoryItem` list to `list[Fact]`
- `update(fact_id, content)` -> `memory.update(memory_id=fact_id, data=content)` -> translate to `Fact`
- `delete(fact_id)` -> `memory.delete(memory_id=fact_id)`
- `delete_all(user_id)` -> `memory.delete_all(user_id=user_id)`
- `get_all(user_id)` -> `memory.get_all(user_id=user_id)` -> translate to `list[Fact]`

**mem0 GraphStore mapping:**
- `add(triples)` -> `graph.add(data=..., filters={user_id: ...})` — mem0's graph LLM extracts entities from text, so triples are serialized to natural language
- `get(entity)` -> `graph.get_all(filters={user_id: ...})` filtered by entity name -> translate to `GraphResult`
- `get_all(user_id)` -> `graph.get_all(filters={user_id: ...})` -> translate to `GraphResult`
- `search(query, user_id)` -> `graph.search(query=query, filters={user_id: ...})` -> translate to `GraphResult`
- `delete(entity)` -> not directly supported; `delete_all` is the available granularity
- `delete_all(user_id)` -> `graph.delete_all(filters={user_id: ...})`
- Note: mem0's graph store does not support individual entity/relationship updates or deletes. The `add()` method uses LLM-driven merge logic to implicitly update existing relationships.

**Zep HistoryStore mapping:**
- `add(session_id, messages)` -> Zep thread API `add_messages(thread_id=session_id, messages=...)` (auto-create thread if needed)
- `get(session_id, limit)` -> Zep thread API `get(thread_id=session_id, limit=limit)` -> translate to `list[Message]`
- `search(session_id, query)` -> `client.graph.search(query=query)` filtered to session -> translate to `list[Message]`
- `delete(session_id)` -> Zep thread API `delete(thread_id=session_id)`
- Note: Zep's thread client may require separate instantiation from the main `AsyncZep` client. The adapter should handle this internally.

**Zep FactStore mapping:**
- `add(content, user_id)` -> `client.graph.add(data=content, user_id=user_id, type="text")` -> translate to `Fact`
- `search(query, user_id, limit)` -> `client.graph.search(query=query, user_id=user_id, limit=limit)` -> translate edges to `list[Fact]`

**Zep GraphStore mapping:**
- `add(triples)` -> `client.graph.add_fact_triple(...)` per triple. Translation: `Triple.subject` -> `source_node_name`, `Triple.predicate` -> `fact_name` (UPPERCASE_SNAKE_CASE), `Triple.object` -> `target_node_name`, `Triple.metadata` -> `edge_attributes`
- `get(entity)` -> `client.graph.node.get_by_user_id(...)` filtered by entity name -> translate to `GraphResult`
- `get_all(user_id)` -> `client.graph.node.get_by_user_id(user_id)` + `client.graph.edge.get_by_user_id(user_id)` -> translate to `GraphResult`
- `search(query, user_id)` -> `client.graph.search(query=query, user_id=user_id)` -> translate to `GraphResult`
- `delete(entity)` -> delete via node/edge API
- `delete_all(user_id)` -> `client.graph.delete(graph_id)` or delete user's graph

**Chroma DocumentStore mapping:**
- `add(content, doc_id, metadata)` -> `collection.add(ids=[doc_id], documents=[content], metadatas=[metadata])`
- `get(doc_id)` -> `collection.get(ids=[doc_id])` -> translate to `Document`
- `search(query, limit, filters)` -> `collection.query(query_texts=[query], n_results=limit, where=filters)` -> translate to `list[Document]`
- `update(doc_id, content, metadata)` -> `collection.update(ids=[doc_id], documents=[content], metadatas=[metadata])`
- `delete(doc_id)` -> `collection.delete(ids=[doc_id])`

### Shared Client Pattern

Adapters from the same provider accept a shared client to avoid duplicate connections:

```python
from zep_cloud import AsyncZep

zep_client = AsyncZep(api_key="...")
m = Memio(
    facts=ZepFactAdapter(client=zep_client),
    history=ZepHistoryAdapter(client=zep_client),
    graph=ZepGraphAdapter(client=zep_client),
)
```

## Error Handling

Two exception classes total.

```python
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

Every adapter wraps its SDK calls in try/except and raises `ProviderError` with the original exception preserved in `.cause`.

## Package Structure

```
memio/
├── __init__.py          # exports Memio, protocols, data models
├── client.py            # Memio class
├── protocols.py         # FactStore, HistoryStore, DocumentStore, GraphStore
├── models.py            # Fact, Message, Document, Triple, GraphResult
├── exceptions.py        # MemioError, ProviderError
├── providers/
│   ├── __init__.py
│   ├── mem0/
│   │   ├── __init__.py  # exports Mem0FactAdapter, Mem0GraphAdapter
│   │   ├── fact.py
│   │   └── graph.py
│   ├── zep/
│   │   ├── __init__.py  # exports ZepFactAdapter, ZepHistoryAdapter, ZepGraphAdapter
│   │   ├── fact.py
│   │   ├── history.py
│   │   └── graph.py
│   └── chroma/
│       ├── __init__.py  # exports ChromaDocumentAdapter
│       └── document.py
└── py.typed             # PEP 561 marker
```

## Dependencies

```toml
[project]
dependencies = []  # zero core dependencies

[project.optional-dependencies]
mem0 = ["mem0ai"]
zep = ["zep-cloud"]
chroma = ["chromadb"]
all = ["mem0ai", "zep-cloud", "chromadb"]
```

Each adapter does a lazy import of its SDK and raises `ImportError` with install instructions if missing:

```python
class Mem0FactAdapter:
    def __init__(self, **kwargs):
        try:
            from mem0 import AsyncMemory
        except ImportError:
            raise ImportError("mem0 provider requires mem0ai: pip install memio[mem0]")
```

## Testing Strategy

Three layers:

**1. Protocol conformance tests** — generic test suite any adapter must pass:

```python
async def fact_store_conformance(store: FactStore):
    fact = await store.add(content="likes coffee", user_id="test-user")
    assert fact.id is not None
    assert fact.content == "likes coffee"

    retrieved = await store.get(fact_id=fact.id)
    assert retrieved.id == fact.id
    assert retrieved.content == "likes coffee"

    results = await store.search(query="coffee", user_id="test-user")
    assert any(f.id == fact.id for f in results)

    updated = await store.update(fact_id=fact.id, content="likes tea")
    assert updated.content == "likes tea"

    await store.delete(fact_id=fact.id)
    results = await store.search(query="tea", user_id="test-user")
    assert all(f.id != fact.id for f in results)
```

Same pattern for HistoryStore, DocumentStore, GraphStore. New providers run these tests to prove compatibility.

**2. Adapter unit tests** — mock provider SDKs, test translation logic (memio calls -> provider calls, provider responses -> memio data models).

**3. Integration tests** — hit real provider APIs. Gated behind `pytest -m integration` and environment variables for API keys.

## Future Extensibility (not in v0.1)

The protocol-based architecture naturally supports two future directions:

### Custom/Native Provider Adapters

Third parties can implement adapters for any backend without forking memio. Because protocols use structural subtyping (duck typing), any class that implements the right method signatures works — no base class inheritance or registration required.

```python
# Example: a community-built neo4j adapter (e.g., published as memio-neo4j)
class Neo4jGraphAdapter:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = neo4j.AsyncDriver(uri, auth=(user, password))

    async def add(self, *, triples: list[Triple]) -> None: ...
    async def get(self, *, entity: str) -> GraphResult: ...
    async def get_all(self, *, user_id: str | None = None, limit: int = 100) -> GraphResult: ...
    async def search(self, *, query: str, user_id: str | None = None, limit: int = 10) -> GraphResult: ...
    async def delete(self, *, entity: str | None = None, triple_id: str | None = None) -> None: ...
    async def delete_all(self, *, user_id: str | None = None) -> None: ...

# Plug it in — no changes to memio core
m = Memio(graph=Neo4jGraphAdapter(uri="bolt://localhost:7687", ...))
```

### Hosted/Commercial Offering (MemioCloud)

A future managed service where users get one API key and memio handles provider selection, hosting, and infrastructure. This is a thin wrapper that composes cloud-hosted adapters behind the same API surface:

```python
# Cloud: one API key, same interface
m = MemioCloud(api_key="mk-...")
await m.facts.add(content="User prefers dark mode", user_id="alice")

# Identical API to self-hosted:
m = Memio(facts=Mem0FactAdapter(...), history=ZepHistoryAdapter(...))
await m.facts.add(content="User prefers dark mode", user_id="alice")
```

`MemioCloud` internally instantiates cloud-backed adapters that implement the same protocols. No changes to the core library, protocols, or data models are needed — the commercial layer sits on top.
