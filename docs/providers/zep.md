# Zep

[Zep](https://www.getzep.com) is a memory service for AI assistants that
provides conversation history, fact extraction, and knowledge graph
capabilities. memio provides three adapters for Zep.

## Installation

```bash
pip install memio[zep]
```

This installs the `zep-cloud` SDK as a dependency.

## Setup

1. Create an account at [getzep.com](https://www.getzep.com).
2. Generate an API key from the dashboard.
3. Pass the key when constructing any Zep adapter.

## Supported stores

| Store | Adapter class |
|---|---|
| FactStore | `ZepFactAdapter` |
| HistoryStore | `ZepHistoryAdapter` |
| GraphStore | `ZepGraphAdapter` |

## FactStore -- ZepFactAdapter

Zep represents facts as graph **edges**. The adapter maps memio's `Fact` model
to Zep's edge concept, using `graph.add` to create facts and `graph.edge.*`
methods to retrieve and update them.

### Initialization

```python
from memio.providers.zep import ZepFactAdapter

facts = ZepFactAdapter(api_key="z_...")
```

You can also pass a pre-configured `AsyncZep` client:

```python
from zep_cloud import AsyncZep
from memio.providers.zep import ZepFactAdapter

zep_client = AsyncZep(api_key="z_...")
facts = ZepFactAdapter(client=zep_client)
```

### Usage

```python
from memio import Memio
from memio.providers.zep import ZepFactAdapter

client = Memio(facts=ZepFactAdapter(api_key="z_..."))

# Add a fact
fact = await client.facts.add(
    content="Alice prefers dark mode",
    user_id="alice",
)
print(fact.id, fact.content)

# Search facts
results = await client.facts.search(query="UI preferences", user_id="alice")
for f in results:
    print(f.content, f.score)

# Get a specific fact by ID
fact = await client.facts.get(fact_id=fact.id)

# Update a fact
updated = await client.facts.update(fact_id=fact.id, content="Alice prefers light mode")

# List all facts for a user
all_facts = await client.facts.get_all(user_id="alice")

# Delete all facts for a user (deletes the user in Zep)
await client.facts.delete_all(user_id="alice")
```

## HistoryStore -- ZepHistoryAdapter

Zep stores conversation history in **threads** associated with users. The
adapter automatically creates users and threads as needed.

### Initialization

```python
from memio.providers.zep import ZepHistoryAdapter

history = ZepHistoryAdapter(api_key="z_...")
```

### Usage

```python
from memio import Memio, Message
from memio.providers.zep import ZepHistoryAdapter

client = Memio(history=ZepHistoryAdapter(api_key="z_..."))

# Add messages to a session
await client.history.add(
    session_id="session-1",
    user_id="alice",
    messages=[
        Message(role="user", content="What is memio?"),
        Message(role="assistant", content="A unified memory gateway."),
    ],
)

# Get messages from a session
messages = await client.history.get(session_id="session-1", limit=50)
for m in messages:
    print(f"{m.role}: {m.content}")

# Search within a session
results = await client.history.search(
    session_id="session-1",
    query="memory gateway",
)

# List all session IDs for a user
sessions = await client.history.get_all(user_id="alice")

# Delete a single session (thread)
await client.history.delete(session_id="session-1")

# Delete all sessions for a user (deletes the user in Zep)
await client.history.delete_all(user_id="alice")
```

## GraphStore -- ZepGraphAdapter

Zep's graph store uses `graph.add_fact_triple` to create explicit
subject-predicate-object relationships. Nodes and edges are retrieved via
user-scoped queries.

### Initialization

```python
from memio.providers.zep import ZepGraphAdapter

graph = ZepGraphAdapter(api_key="z_...")
```

### Usage

```python
from memio import Memio, Triple
from memio.providers.zep import ZepGraphAdapter

client = Memio(graph=ZepGraphAdapter(api_key="z_..."))

# Add triples
await client.graph.add(
    triples=[
        Triple(subject="Alice", predicate="works_at", object="Acme Corp"),
        Triple(subject="Bob", predicate="reports_to", object="Alice"),
    ],
    user_id="alice",
)

# Get triples for a specific entity
result = await client.graph.get(entity="Alice", user_id="alice")
for t in result.triples:
    print(f"{t.subject} -> {t.predicate} -> {t.object}")
print("Nodes:", result.nodes)

# Search the graph
result = await client.graph.search(query="who works at Acme", user_id="alice")

# Get all triples for a user
result = await client.graph.get_all(user_id="alice")

# Delete all graph data for a user (deletes the user in Zep)
await client.graph.delete_all(user_id="alice")
```

## Known quirks

!!! warning "Graph operations are eventually consistent"
    When you call `graph.add` on the `ZepFactAdapter`, Zep sends the input
    text to an LLM for asynchronous fact extraction. The extracted facts may
    not appear immediately in `search` or `get_all` results. If you need to
    verify that data was ingested, add a short delay before querying.

!!! warning "AsyncHttpResponse unwrapping"
    The Zep SDK wraps many responses in an `AsyncHttpResponse` object. The
    memio adapters handle this automatically -- you always receive plain
    memio models. You do not need to unwrap anything yourself.

!!! warning "No individual fact or triple deletion"
    `ZepFactAdapter.delete()` and `ZepGraphAdapter.delete()` are **not
    supported**. Calling either raises a `ProviderError` wrapping
    `NotImplementedError`. To remove data, use `delete_all(user_id=...)`
    instead, which deletes the entire user and all associated data in Zep.

!!! info "Auto-created users"
    When you call `add` on any Zep adapter with a `user_id`, the adapter
    automatically creates the user in Zep if it does not already exist. You
    do not need to manage users separately.

!!! info "Empty results for non-existent users"
    `get`, `search`, `get_all`, and similar read operations return empty
    lists (not errors) when called with a `user_id` that does not exist in
    Zep. The adapters catch the 404 responses from the SDK and normalize
    them to empty results.
