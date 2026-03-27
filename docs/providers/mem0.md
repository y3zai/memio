# Mem0

[Mem0](https://mem0.ai) is a managed memory service that uses an LLM to
extract, deduplicate, and manage facts from natural language input. memio
provides two adapters for Mem0.

## Installation

```bash
pip install memio[mem0]
```

This installs the `mem0ai` SDK as a dependency.

## Setup

1. Create an account at [mem0.ai](https://mem0.ai).
2. Generate an API key from the dashboard.
3. Either pass the key directly or set the environment variable that the
   `mem0ai` SDK reads (see Mem0's own docs for the env var name).

## Supported stores

| Store | Adapter class |
|---|---|
| FactStore | `Mem0FactAdapter` |
| GraphStore | `Mem0GraphAdapter` |

## FactStore -- Mem0FactAdapter

### Initialization

```python
from memio.providers.mem0 import Mem0FactAdapter

facts = Mem0FactAdapter(api_key="m0-...")
```

You can also pass a `config` dict for advanced Mem0 configuration:

```python
facts = Mem0FactAdapter(config={"api_key": "m0-...", ...})
```

### Usage

```python
from memio import Memio
from memio.providers.mem0 import Mem0FactAdapter

client = Memio(facts=Mem0FactAdapter(api_key="m0-..."))

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

# Get a specific fact
fact = await client.facts.get(fact_id=fact.id)

# Update a fact
updated = await client.facts.update(fact_id=fact.id, content="Alice likes cortados")

# List all facts for a user
all_facts = await client.facts.get_all(user_id="alice")

# Delete a single fact
await client.facts.delete(fact_id=fact.id)

# Delete all facts for a user
await client.facts.delete_all(user_id="alice")
```

## GraphStore -- Mem0GraphAdapter

### Initialization

```python
from memio.providers.mem0 import Mem0GraphAdapter

graph = Mem0GraphAdapter(api_key="m0-...")
```

### Usage

```python
from memio import Memio, Triple
from memio.providers.mem0 import Mem0GraphAdapter

client = Memio(graph=Mem0GraphAdapter(api_key="m0-..."))

# Add triples
await client.graph.add(
    triples=[
        Triple(subject="Alice", predicate="works_at", object="Acme Corp"),
        Triple(subject="Alice", predicate="knows", object="Bob"),
    ],
    user_id="alice",
)

# Get triples for an entity
result = await client.graph.get(entity="Alice", user_id="alice")
for t in result.triples:
    print(f"{t.subject} -> {t.predicate} -> {t.object}")

# Search the graph
result = await client.graph.search(query="where does Alice work", user_id="alice")

# Get all triples
result = await client.graph.get_all(user_id="alice")

# Delete all graph data for a user
await client.graph.delete_all(user_id="alice")
```

## Known quirks

!!! warning "Content rephrasing"
    Mem0's LLM may rephrase the content you provide. The `fact.content` you
    get back from `add` or `get` may not be the exact string you sent in.

!!! warning "Automatic deduplication"
    If you add content that Mem0 considers a duplicate of an existing fact,
    `add` returns an empty result set. The adapter raises a `ProviderError`
    wrapping a `ValueError` in this case, because there is no new fact to
    return.

!!! warning "No individual graph deletes"
    `Mem0GraphAdapter.delete()` is **not supported**. Calling it raises a
    `ProviderError` wrapping `NotImplementedError`. To remove graph data,
    use `delete_all(user_id=...)` instead, which clears all triples for
    the given user.
