# Qdrant

[Qdrant](https://qdrant.tech/) is a vector database for similarity search. memio's Qdrant adapter implements the `DocumentStore` protocol using qdrant-client's built-in fastembed integration for automatic embedding generation.

## Installation

```bash
pip install memio[qdrant]
```

This installs `qdrant-client[fastembed]`, which includes the fastembed library for local embedding generation.

## Setup

Qdrant supports multiple deployment modes. You create a client and pass it to the adapter:

### In-memory (no persistence, great for testing)

```python
from qdrant_client import AsyncQdrantClient
from memio import Memio
from memio.providers.qdrant import QdrantDocumentAdapter

client = AsyncQdrantClient(":memory:")
memio_client = Memio(
    documents=QdrantDocumentAdapter(client=client, collection_name="my-docs"),
)
```

### On-disk (persistent, no server needed)

```python
client = AsyncQdrantClient(path="./qdrant_data")
```

### Qdrant Cloud

```python
client = AsyncQdrantClient(
    url="https://your-cluster.cloud.qdrant.io:6333",
    api_key="your-api-key",
)
```

### Self-hosted server

```python
client = AsyncQdrantClient(host="localhost", port=6333)
```

## Supported stores

| Store | Adapter |
|-------|---------|
| `DocumentStore` | `QdrantDocumentAdapter` |

## Usage

```python
import asyncio
from qdrant_client import AsyncQdrantClient
from memio import Memio
from memio.providers.qdrant import QdrantDocumentAdapter

async def main():
    client = AsyncQdrantClient(":memory:")
    memio_client = Memio(
        documents=QdrantDocumentAdapter(client=client, collection_name="docs"),
    )

    # Add a document
    doc = await memio_client.documents.add(
        content="Qdrant is a vector database for similarity search",
        metadata={"source": "docs"},
    )

    # Search
    results = await memio_client.documents.search(query="vector database", limit=5)
    for r in results:
        print(f"{r.content} (score: {r.score})")

    # Search with metadata filter
    results = await memio_client.documents.search(
        query="vector", filters={"source": "docs"},
    )

    # Get all documents
    all_docs = await memio_client.documents.get_all()

    # Get by ID
    retrieved = await memio_client.documents.get(doc_id=doc.id)

    # Update
    updated = await memio_client.documents.update(
        doc_id=doc.id, content="Updated content",
    )

    # Delete
    await memio_client.documents.delete(doc_id=doc.id)

    # Delete all
    await memio_client.documents.delete_all()

    await client.close()

asyncio.run(main())
```

## Embedding model

By default, Qdrant uses the `BAAI/bge-small-en` embedding model (384 dimensions) via fastembed. The model is downloaded automatically on first use.

To use a different model:

```python
client = AsyncQdrantClient(":memory:")
client.set_model("sentence-transformers/all-MiniLM-L6-v2")
```

## Known quirks

- **Auto-collection creation**: Collections are created automatically on first `add()` call. No manual setup needed.
- **UUID IDs**: When no `doc_id` is provided, a UUID is generated automatically.
- **Scores**: Search scores are returned directly from Qdrant's similarity scoring (higher = more similar).
- **Metadata filtering**: The `filters` parameter in `search()` and `get_all()` supports exact-match filtering on payload fields.
