# Chroma

[Chroma](https://www.trychroma.com) is an open-source embedding database that
runs locally or in-memory. memio provides one adapter for Chroma.

## Installation

```bash
pip install memio[chroma]
```

This installs the `chromadb` package as a dependency.

## Setup

No API key is needed. You create a `chromadb` client yourself and pass it to
the adapter. Chroma offers two client types:

| Client | Use case |
|---|---|
| `chromadb.EphemeralClient()` | In-memory storage. Data is lost when the process exits. Best for testing. |
| `chromadb.PersistentClient(path="./data")` | On-disk storage. Data survives restarts. Best for production. |

## Supported stores

| Store | Adapter class |
|---|---|
| DocumentStore | `ChromaDocumentAdapter` |

## DocumentStore -- ChromaDocumentAdapter

### Initialization

The adapter requires a `chromadb` client and a collection name:

```python
import chromadb
from memio.providers.chroma import ChromaDocumentAdapter

# Ephemeral (in-memory) -- good for tests
client = chromadb.EphemeralClient()
docs = ChromaDocumentAdapter(client=client, collection_name="test-docs")

# Persistent (on-disk) -- good for production
client = chromadb.PersistentClient(path="./chroma_data")
docs = ChromaDocumentAdapter(client=client, collection_name="my-docs")
```

The adapter calls `client.get_or_create_collection()` internally, so the
collection is created automatically if it does not exist.

### Usage with EphemeralClient (testing)

```python
import chromadb
from memio import Memio
from memio.providers.chroma import ChromaDocumentAdapter

client = Memio(
    documents=ChromaDocumentAdapter(
        client=chromadb.EphemeralClient(),
        collection_name="test-docs",
    ),
)

# Add a document
doc = await client.documents.add(
    content="memio is a unified memory gateway for AI agents.",
    metadata={"source": "readme", "version": "0.1.0"},
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
    content="memio v0.2.0 -- now with graph support.",
    metadata={"source": "readme", "version": "0.2.0"},
)

# List all documents
all_docs = await client.documents.get_all(limit=50)

# Delete a single document
await client.documents.delete(doc_id=doc.id)

# Delete all documents in the collection
await client.documents.delete_all()
```

### Usage with PersistentClient (production)

```python
import chromadb
from memio import Memio
from memio.providers.chroma import ChromaDocumentAdapter

chroma_client = chromadb.PersistentClient(path="./chroma_data")

client = Memio(
    documents=ChromaDocumentAdapter(
        client=chroma_client,
        collection_name="knowledge-base",
    ),
)

# Add documents
await client.documents.add(
    content="Quarterly revenue increased by 15%.",
    metadata={"type": "report", "quarter": "Q1"},
)
await client.documents.add(
    content="New product launch scheduled for March.",
    metadata={"type": "announcement", "quarter": "Q1"},
)

# Search with metadata filtering
results = await client.documents.search(
    query="revenue",
    limit=10,
    filters={"type": "report"},
)
for d in results:
    print(d.content, d.score, d.metadata)
```

## Score calculation

Chroma returns a **distance** value for each search result (lower distance
means more similar). The adapter converts this to a **similarity score**
between 0 and 1 using the formula:

```
similarity = 1.0 / (1.0 + distance)
```

A score of `1.0` means an exact match. Scores closer to `0.0` indicate less
similarity.

## Metadata filtering

The `search` and `get_all` methods accept an optional `filters` parameter.
This is passed directly to Chroma as a `where` clause. Chroma supports
filtering on metadata fields using its
[where filter syntax](https://docs.trychroma.com/docs/collections/filter):

```python
# Exact match
results = await client.documents.search(
    query="revenue",
    filters={"type": "report"},
)

# Comparison operators
results = await client.documents.search(
    query="revenue",
    filters={"quarter": {"$in": ["Q1", "Q2"]}},
)

# Get all documents matching a filter
all_reports = await client.documents.get_all(
    filters={"type": "report"},
)
```
