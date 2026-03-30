# memio

[![PyPI](https://img.shields.io/pypi/v/memio)](https://pypi.org/project/memio/)
[![Docs](https://img.shields.io/badge/docs-y3z.ai%2Fmemio-blue)](https://y3z.ai/memio/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Unified memory gateway for AI agents. One interface, multiple memory providers.

memio lets you swap between memory backends (Mem0, Zep, Chroma) without changing your application code. Define what memory capabilities you need — facts, conversation history, documents, knowledge graphs — and plug in any supported provider.

## Features

- **Protocol-based architecture** — providers implement Python protocols, so you can mix and match or bring your own
- **Async-first** — all operations are `async`/`await`
- **Zero production dependencies** — install only the providers you need
- **Composable** — use Mem0 for facts, Zep for history, and Chroma for documents in the same client
- **Multi-tenant** — scope data by `user_id` or `agent_id`
- **Consistent error handling** — all provider errors wrapped in `ProviderError` with context

## Install

```bash
pip install memio
```

Install with providers:

```bash
pip install memio[mem0]      # Mem0 provider
pip install memio[zep]       # Zep provider
pip install memio[chroma]    # Chroma provider
pip install memio[all]       # All providers
```

## Quick start

```python
from memio import Memio
from memio.providers.mem0 import Mem0FactAdapter
from memio.providers.zep import ZepHistoryAdapter
from memio.providers.chroma import ChromaDocumentAdapter
import chromadb

client = Memio(
    facts=Mem0FactAdapter(api_key="your-mem0-key"),
    history=ZepHistoryAdapter(api_key="your-zep-key"),
    documents=ChromaDocumentAdapter(
        client=chromadb.EphemeralClient(),
        collection_name="my-docs",
    ),
)

# Store and retrieve facts
fact = await client.facts.add(content="likes coffee", user_id="alice")
results = await client.facts.search(query="coffee", user_id="alice")

# Manage conversation history
from memio import Message

await client.history.add(
    session_id="session-1",
    messages=[
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
    ],
)
messages = await client.history.get(session_id="session-1")

# Store and search documents
doc = await client.documents.add(content="memio is a memory gateway")
results = await client.documents.search(query="memory")
```

## Memory stores

memio defines four memory store protocols. Each provider implements one or more:

| Store | Purpose | Mem0 | Zep | Chroma |
|-------|---------|------|-----|--------|
| `FactStore` | Structured facts about users/agents | yes | yes | - |
| `HistoryStore` | Conversation message history | - | yes | - |
| `DocumentStore` | Document storage with semantic search | - | - | yes |
| `GraphStore` | Knowledge graph triples | yes | yes | - |

### FactStore

```python
fact = await store.add(content="prefers dark mode", user_id="alice")
fact = await store.get(fact_id=fact.id)
results = await store.search(query="preferences", user_id="alice")
updated = await store.update(fact_id=fact.id, content="prefers light mode")
all_facts = await store.get_all(user_id="alice")
await store.delete(fact_id=fact.id)
await store.delete_all(user_id="alice")
```

### HistoryStore

```python
await store.add(session_id="s1", messages=[Message(role="user", content="hello")])
messages = await store.get(session_id="s1", limit=50)
results = await store.search(session_id="s1", query="hello")
sessions = await store.get_all(user_id="alice")
await store.delete(session_id="s1")
await store.delete_all(user_id="alice")
```

### DocumentStore

```python
doc = await store.add(content="some text", metadata={"source": "wiki"})
doc = await store.get(doc_id=doc.id)
results = await store.search(query="text", limit=10)
all_docs = await store.get_all(limit=100)
updated = await store.update(doc_id=doc.id, content="updated text")
await store.delete(doc_id=doc.id)
await store.delete_all()
```

### GraphStore

```python
from memio import Triple

await store.add(
    triples=[Triple(subject="Alice", predicate="likes", object="coffee")],
    user_id="alice",
)
result = await store.get(entity="Alice", user_id="alice")
result = await store.search(query="coffee", user_id="alice")
await store.delete_all(user_id="alice")
```

## Data models

```python
from memio import Fact, Message, Document, Triple, GraphResult

# Fact — a stored piece of knowledge
Fact(id, content, user_id, agent_id, metadata, score, created_at, updated_at)

# Message — a conversation message
Message(role, content, metadata, timestamp, name)

# Document — a stored document
Document(id, content, metadata, score, created_at, updated_at)

# Triple — a knowledge graph triple
Triple(subject, predicate, object, metadata)

# GraphResult — result from graph queries
GraphResult(triples, nodes, scores)
```

## Custom providers

Implement any protocol to create your own provider:

```python
from memio import Memio, DocumentStore, Document

class MyDocumentStore:
    async def add(self, *, content, doc_id=None, metadata=None):
        # your implementation
        return Document(id="...", content=content, metadata=metadata)

    async def get(self, *, doc_id):
        ...

    async def search(self, *, query, limit=10, filters=None):
        ...

    async def update(self, *, doc_id, content, metadata=None):
        ...

    async def delete(self, *, doc_id):
        ...

    async def get_all(self, *, limit=100, filters=None):
        ...

    async def delete_all(self):
        ...

# memio validates the protocol at runtime
client = Memio(documents=MyDocumentStore())
```

## Error handling

All provider errors are wrapped in `ProviderError`:

```python
from memio import ProviderError, NotSupportedError, MemioError

try:
    await client.facts.delete(fact_id="123")
except NotSupportedError as e:
    print(e.hint)        # "use delete_all"
except ProviderError as e:
    print(e.provider)    # "mem0", "zep", etc.
    print(e.operation)   # "search", "add", etc.
    print(e.cause)       # original exception
except MemioError:
    # base class for all memio errors
    ...
```

`NotSupportedError` is a subclass of `ProviderError`, raised when a provider doesn't support a specific operation (e.g., individual delete on Zep). It includes an optional `hint` suggesting what to do instead. Unlike other `ProviderError` subclasses, its `cause` is a `NotImplementedError` (not an underlying SDK exception).

## Provider notes

**Mem0** — content may be rephrased by Mem0's LLM. Duplicate content is deduplicated automatically.

**Zep** — graph operations are eventually consistent. `graph.add` sends text to an LLM for asynchronous fact extraction. Individual fact/triple deletion is not supported; use `delete_all` instead.

**Chroma** — uses a local client you provide. No API key required for ephemeral or persistent local usage.

## Development

```bash
git clone https://github.com/y3zai/memio.git
cd memio
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"

# Run unit tests
pytest

# Put OPENAI_API_KEY, MEM0_API_KEY, and ZEP_API_KEY in .env, then run integration tests
pytest -m integration -v
```

Pytest loads `.env` automatically from the repository root for local test runs.

## License

MIT
