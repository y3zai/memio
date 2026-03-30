# Quick Start

All memio operations are **async**. The examples below use `asyncio.run()` to run from a script. If you are already inside an async context (e.g., inside an agent framework), you can call `await` directly.

## 1. Simplest example -- Chroma DocumentStore

Chroma runs locally and needs no API key, making it the fastest way to try memio.

```bash
pip install memio[chroma]
```

```python
import asyncio
import chromadb
from memio import Memio
from memio.providers.chroma import ChromaDocumentAdapter

async def main():
    # Create an in-memory Chroma client
    chroma_client = chromadb.EphemeralClient()

    # Build a Memio client with a document store
    client = Memio(
        documents=ChromaDocumentAdapter(
            client=chroma_client,
            collection_name="my-docs",
        ),
    )

    # Add a document
    doc = await client.documents.add(
        content="memio is a unified memory gateway for AI agents",
        metadata={"source": "readme"},
    )
    print(f"Added document: {doc.id}")

    # Search by semantic similarity
    results = await client.documents.search(query="memory for agents")
    for r in results:
        print(f"  [{r.score:.3f}] {r.content}")

    # Retrieve by ID
    same_doc = await client.documents.get(doc_id=doc.id)
    print(f"Retrieved: {same_doc.content}")

    # Delete
    await client.documents.delete(doc_id=doc.id)
    print("Document deleted")

asyncio.run(main())
```

## 2. Multi-provider example

memio shines when you compose multiple providers into one client. Here, Mem0 handles facts, Zep handles conversation history, and Chroma handles documents:

```bash
pip install memio[all]
```

```python
import asyncio
import chromadb
from memio import Memio, Message
from memio.providers.mem0 import Mem0FactAdapter
from memio.providers.zep import ZepHistoryAdapter
from memio.providers.chroma import ChromaDocumentAdapter

async def main():
    client = Memio(
        facts=Mem0FactAdapter(api_key="your-mem0-key"),
        history=ZepHistoryAdapter(api_key="your-zep-key"),
        documents=ChromaDocumentAdapter(
            client=chromadb.EphemeralClient(),
            collection_name="my-docs",
        ),
    )

    # --- Facts (Mem0) ---
    fact = await client.facts.add(
        content="prefers dark mode",
        user_id="alice",
    )
    results = await client.facts.search(query="preferences", user_id="alice")
    print(f"Found {len(results)} facts about Alice's preferences")

    # --- History (Zep) ---
    await client.history.add(
        session_id="session-1",
        messages=[
            Message(role="user", content="What's the weather like?"),
            Message(role="assistant", content="It's sunny and 72F."),
        ],
    )
    messages = await client.history.get(session_id="session-1")
    print(f"Session has {len(messages)} messages")

    # --- Documents (Chroma) ---
    doc = await client.documents.add(content="memio is a memory gateway")
    results = await client.documents.search(query="memory")
    print(f"Found {len(results)} matching documents")

asyncio.run(main())
```

Each store is accessed through its attribute on the client: `client.facts`, `client.history`, `client.documents`, and `client.graph`.

## 3. All four store types

memio defines four store protocols. Here is a brief example of each one's key operations.

### FactStore

Store structured facts about users or agents.

```python
# Add a fact
fact = await client.facts.add(content="likes coffee", user_id="alice")

# Search facts
results = await client.facts.search(query="coffee", user_id="alice")

# Get a specific fact by ID
fact = await client.facts.get(fact_id=fact.id)

# Update a fact
updated = await client.facts.update(fact_id=fact.id, content="likes tea")

# List all facts for a user
all_facts = await client.facts.get_all(user_id="alice")

# Delete
await client.facts.delete(fact_id=fact.id)
await client.facts.delete_all(user_id="alice")
```

**Providers:** Mem0 (`Mem0FactAdapter`), Zep (`ZepFactAdapter`), Supermemory (`SupermemoryFactAdapter`)

### HistoryStore

Manage conversation message history by session.

```python
from memio import Message

# Add messages to a session
await client.history.add(
    session_id="session-1",
    messages=[
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
    ],
)

# Get messages from a session
messages = await client.history.get(session_id="session-1", limit=50)

# Search within a session
results = await client.history.search(session_id="session-1", query="hello")

# List all sessions for a user
sessions = await client.history.get_all(user_id="alice")

# Delete a session
await client.history.delete(session_id="session-1")
await client.history.delete_all(user_id="alice")
```

**Provider:** Zep (`ZepHistoryAdapter`)

### DocumentStore

Store and search documents by semantic similarity.

```python
# Add a document with metadata
doc = await client.documents.add(
    content="some text",
    metadata={"source": "wiki"},
)

# Search by query
results = await client.documents.search(query="text", limit=10)

# Get by ID
doc = await client.documents.get(doc_id=doc.id)

# Update content
updated = await client.documents.update(doc_id=doc.id, content="updated text")

# List all documents
all_docs = await client.documents.get_all(limit=100)

# Delete
await client.documents.delete(doc_id=doc.id)
await client.documents.delete_all()
```

**Providers:** Chroma (`ChromaDocumentAdapter`), Supermemory (`SupermemoryDocumentAdapter`)

### GraphStore

Store and query knowledge graph triples.

```python
from memio import Triple

# Add triples
await client.graph.add(
    triples=[Triple(subject="Alice", predicate="likes", object="coffee")],
    user_id="alice",
)

# Get triples for an entity
result = await client.graph.get(entity="Alice", user_id="alice")
for t in result.triples:
    print(f"{t.subject} --{t.predicate}--> {t.object}")

# Search the graph
result = await client.graph.search(query="coffee", user_id="alice")

# Delete all graph data for a user
await client.graph.delete_all(user_id="alice")
```

**Providers:** Mem0 (`Mem0GraphAdapter`), Zep (`ZepGraphAdapter`)

## Error handling

All provider errors are wrapped in `ProviderError`, which tells you exactly what went wrong:

```python
from memio import ProviderError

try:
    await client.facts.search(query="test", user_id="alice")
except ProviderError as e:
    print(e.provider)   # "mem0", "zep", etc.
    print(e.operation)  # "search", "add", etc.
    print(e.cause)      # the original exception
```

## Next steps

- [Architecture](../concepts/architecture.md) -- understand protocols and how memio validates providers
- [Custom Providers](../guides/custom-providers.md) -- implement your own memory store
- [API Reference](../api/client.md) -- complete API documentation
