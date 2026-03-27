# Architecture

memio is a unified memory gateway for AI agents. It lets you connect any
combination of memory providers behind a single client, so your agent code
never depends on a specific vendor SDK.

This page explains the design decisions that make that possible.

## Protocol-based design

memio defines four store **protocols** using Python's `@runtime_checkable`
`Protocol` from the `typing` module:

| Protocol | Purpose |
|---|---|
| `FactStore` | Structured facts scoped to a user or agent |
| `HistoryStore` | Conversation message history grouped by session |
| `DocumentStore` | Documents with semantic search and metadata filtering |
| `GraphStore` | Knowledge graph triples (subject-predicate-object) |

Because these are protocols -- not base classes -- any class that provides the
right async methods satisfies the contract. No inheritance is required. The
`Memio` client validates each store with `isinstance()` at init time and raises
`TypeError` if the check fails.

```python
from memio import Memio
from memio.providers.mem0 import Mem0FactAdapter

# Mem0FactAdapter has no base class -- it just implements
# the same async methods that FactStore declares.
client = Memio(facts=Mem0FactAdapter(api_key="..."))
```

## The adapter pattern

Each provider ships one or more **adapter** classes. An adapter translates
memio's protocol methods into the provider's own SDK calls and normalizes
responses into memio's data models:

| Model | Fields |
|---|---|
| `Fact` | id, content, user_id, agent_id, metadata, score, created_at, updated_at |
| `Message` | role, content, metadata, timestamp, name |
| `Document` | id, content, metadata, score, created_at, updated_at |
| `Triple` | subject, predicate, object, metadata |
| `GraphResult` | triples, nodes, scores |

Your agent code works exclusively with these models. If you swap providers,
you change one import and one constructor call -- the rest of your code stays
the same.

## Architecture diagram

```
Your AI Agent
     |
     v
   Memio Client
     |
     |-- facts     -> Mem0FactAdapter      -> Mem0 Cloud API
     |-- history   -> ZepHistoryAdapter     -> Zep Cloud API
     |-- documents -> ChromaDocumentAdapter -> Local Chroma
     |-- graph     -> ZepGraphAdapter       -> Zep Cloud API
```

## Composability

You can mix providers freely. The `Memio` client accepts any combination of
stores -- use whichever provider is strongest for each memory type:

```python
from memio import Memio
from memio.providers.mem0 import Mem0FactAdapter
from memio.providers.zep import ZepHistoryAdapter
from memio.providers.chroma import ChromaDocumentAdapter

import chromadb

client = Memio(
    facts=Mem0FactAdapter(api_key="mem0-key"),
    history=ZepHistoryAdapter(api_key="zep-key"),
    documents=ChromaDocumentAdapter(
        client=chromadb.PersistentClient(path="./chroma_data"),
        collection_name="docs",
    ),
)
```

At least one store must be provided. Stores you do not need can be omitted --
accessing an omitted store attribute returns `None`.

### Provider support matrix

| Store | Mem0 | Zep | Chroma |
|---|---|---|---|
| FactStore | Mem0FactAdapter | ZepFactAdapter | -- |
| HistoryStore | -- | ZepHistoryAdapter | -- |
| DocumentStore | -- | -- | ChromaDocumentAdapter |
| GraphStore | Mem0GraphAdapter | ZepGraphAdapter | -- |

## Error handling

Every adapter wraps provider SDK exceptions in a single error type:

```python
from memio.exceptions import ProviderError

try:
    fact = await client.facts.add(content="likes coffee", user_id="alice")
except ProviderError as e:
    print(e.provider)   # "mem0"
    print(e.operation)  # "add"
    print(e.cause)      # the original SDK exception
```

`ProviderError` always carries three attributes:

- **`provider`** -- the name of the provider (`"mem0"`, `"zep"`, `"chroma"`).
- **`operation`** -- the protocol method that failed (`"add"`, `"search"`, etc.).
- **`cause`** -- the original exception from the provider SDK.

This means your error-handling code never needs to import provider-specific
exception types.

## Async-first

All store operations are `async`/`await`. Every method on every protocol is
declared `async def`, and every adapter implements them as coroutines:

```python
# Every call goes through await
fact = await client.facts.add(content="likes coffee", user_id="alice")
results = await client.facts.search(query="coffee", user_id="alice")
await client.facts.delete(fact_id=fact.id)
```

This makes memio a natural fit for async frameworks, LLM tool-calling loops,
and any agent runtime that uses `asyncio`.

## Multi-tenancy

`FactStore` and `GraphStore` support **`user_id`** and **`agent_id`**
parameters for scoped data access. This lets a single memio deployment serve
multiple users or agents without data leaking across boundaries:

```python
# Facts scoped to a specific user
await client.facts.add(
    content="prefers dark mode",
    user_id="alice",
)

# Search only returns facts for this user
results = await client.facts.search(
    query="UI preferences",
    user_id="alice",
)

# Graph triples scoped to a user
await client.graph.add(
    triples=[Triple(subject="Alice", predicate="works_at", object="Acme")],
    user_id="alice",
)
```

`HistoryStore` scopes data by **`session_id`**, with `get_all` accepting a
`user_id` to list all sessions for a given user.
