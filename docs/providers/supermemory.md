# Supermemory

[Supermemory](https://supermemory.ai) is a cloud-hosted memory API for AI
applications. It auto-extracts facts from content, maintains user profiles,
and provides hybrid search across memories and documents. memio provides two
adapters for Supermemory.

## Installation

```bash
pip install memio[supermemory]
```

This installs the `supermemory` Python SDK as a dependency.

## Setup

1. Create an account at [console.supermemory.ai](https://console.supermemory.ai).
2. Generate an API key from the dashboard.
3. Either pass the key directly or set the `SUPERMEMORY_API_KEY` environment
   variable.

## Supported stores

| Store | Adapter class |
|---|---|
| FactStore | `SupermemoryFactAdapter` |
| DocumentStore | `SupermemoryDocumentAdapter` |

## FactStore -- SupermemoryFactAdapter

### Initialization

```python
from memio.providers.supermemory import SupermemoryFactAdapter

facts = SupermemoryFactAdapter(api_key="sm_...")
```

If `api_key` is omitted, the SDK reads from the `SUPERMEMORY_API_KEY`
environment variable.

### Usage

```python
from memio import Memio
from memio.providers.supermemory import SupermemoryFactAdapter

client = Memio(facts=SupermemoryFactAdapter(api_key="sm_..."))

# Add a fact
fact = await client.facts.add(
    content="Alice likes espresso",
    user_id="alice",
)
print(fact.id, fact.content)

# Search facts
results = await client.facts.search(query="coffee", user_id="alice")
for f in results:
    print(f.content, f.score)

# Update a fact (creates a new version)
updated = await client.facts.update(fact_id=fact.id, content="Alice likes cortados")

# List all facts for a user
all_facts = await client.facts.get_all(user_id="alice")

# Delete a single fact (soft-delete via forget)
await client.facts.delete(fact_id=fact.id)
```

### Scoping with container tags

Supermemory scopes all data by **container tags**. The adapter maps memio's
`user_id` and `agent_id` parameters to a container tag:

| Parameters | Container tag |
|---|---|
| `user_id="alice"` | `"alice"` |
| `agent_id="bot-1"` | `"bot-1"` |
| `user_id="alice", agent_id="bot-1"` | `"alice--bot-1"` |

## DocumentStore -- SupermemoryDocumentAdapter

### Initialization

```python
from memio.providers.supermemory import SupermemoryDocumentAdapter

docs = SupermemoryDocumentAdapter(api_key="sm_...")

# Optionally scope all operations to a container tag
docs = SupermemoryDocumentAdapter(api_key="sm_...", container_tag="project-1")
```

### Usage

```python
from memio import Memio
from memio.providers.supermemory import SupermemoryDocumentAdapter

client = Memio(
    documents=SupermemoryDocumentAdapter(api_key="sm_..."),
)

# Add a document
doc = await client.documents.add(
    content="memio is a unified memory gateway for AI agents.",
    metadata={"source": "readme"},
)
print(doc.id, doc.content)

# Search documents
results = await client.documents.search(query="memory gateway", limit=5)
for d in results:
    print(d.content, d.score)

# Get a document by ID
doc = await client.documents.get(doc_id=doc.id)

# Update a document
updated = await client.documents.update(
    doc_id=doc.id,
    content="memio v0.2.0 -- now with Supermemory support.",
)

# List all documents
all_docs = await client.documents.get_all(limit=50)

# Delete a single document
await client.documents.delete(doc_id=doc.id)

# Delete all documents
await client.documents.delete_all()
```

## Known quirks

!!! warning "Async document processing"
    Supermemory processes documents asynchronously after `add()`. The document
    may still be in a processing state (queued, extracting, chunking, etc.)
    immediately after creation. Attempting to delete a document that is still
    processing returns a 409 error.

!!! warning "get() not supported on FactStore"
    `SupermemoryFactAdapter.get()` raises `NotSupportedError`. Supermemory
    has no endpoint to retrieve a single memory by ID. Use `search()` instead.

!!! warning "delete_all() not supported on FactStore"
    `SupermemoryFactAdapter.delete_all()` raises `NotSupportedError`.
    Supermemory has no bulk forget endpoint. Delete memories individually
    with `delete()`.

!!! warning "Soft deletes"
    `delete()` on the FactStore uses Supermemory's `forget()` API, which
    marks memories as forgotten rather than permanently deleting them.

!!! warning "Content rephrasing"
    Like Mem0, Supermemory auto-extracts facts from content via an LLM.
    The content you get back from search may not be the exact string you
    sent in.
