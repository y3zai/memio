# memio

**Unified memory gateway for AI agents.**

memio lets you swap between memory backends -- Mem0, Zep, Chroma, and Qdrant -- without changing your application code. Define what memory capabilities you need (facts, conversation history, documents, knowledge graphs) and plug in any supported provider.

## Why memio?

AI agents need memory, but every memory provider has a different API. memio gives you a single, consistent interface so you can pick the best provider for each job and swap them out later without rewriting your agent.

## Features

- **Protocol-based architecture** -- providers implement Python protocols, so you can mix and match or bring your own
- **Async-first** -- all operations are `async`/`await`
- **Zero production dependencies** -- install only the providers you need
- **Composable** -- use Mem0 for facts, Zep for history, and Chroma for documents in the same client
- **Multi-tenant** -- scope data by `user_id` or `agent_id`
- **Consistent error handling** -- all provider errors wrapped in `ProviderError` with context

## Install

```bash
pip install memio
```

## Quick example

The simplest way to get started is with Chroma, which runs locally and needs no API key:

```bash
pip install memio[chroma]
```

```python
import asyncio
import chromadb
from memio import Memio
from memio.providers.chroma import ChromaDocumentAdapter

async def main():
    # Create a Chroma client (in-memory, no setup needed)
    chroma_client = chromadb.EphemeralClient()

    # Create a Memio client with a Chroma document store
    client = Memio(
        documents=ChromaDocumentAdapter(
            client=chroma_client,
            collection_name="my-docs",
        ),
    )

    # Add a document
    doc = await client.documents.add(content="memio is a memory gateway for AI agents")

    # Search for it
    results = await client.documents.search(query="memory gateway")
    print(results[0].content)  # "memio is a memory gateway for AI agents"

    # Retrieve by ID
    same_doc = await client.documents.get(doc_id=doc.id)

    # Clean up
    await client.documents.delete(doc_id=doc.id)

asyncio.run(main())
```

## Memory stores

memio defines four memory store protocols. Each provider implements one or more:

| Store | Purpose | Mem0 | Zep | Chroma | Qdrant |
|-------|---------|------|-----|--------|--------|
| `FactStore` | Structured facts about users/agents | yes | yes | -- | -- |
| `HistoryStore` | Conversation message history | -- | yes | -- | -- |
| `DocumentStore` | Document storage with semantic search | -- | -- | yes | yes |
| `GraphStore` | Knowledge graph triples | yes | yes | -- | -- |

## Next steps

- [Installation](getting-started/installation.md) -- install memio and provider extras
- [Quick Start](getting-started/quickstart.md) -- full working examples with all store types
- [Architecture](concepts/architecture.md) -- understand protocols and composability
- [Providers](providers/mem0.md) -- provider-specific configuration and notes
- [API Reference](api/client.md) -- complete API documentation
