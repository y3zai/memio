# Building a Custom Provider

memio is designed around Python protocols. You don't need to subclass
anything -- just write a class whose async methods match the protocol
signature and plug it in.

This guide walks through building a fully functional in-memory
`FactStore` from scratch.

---

## 1. Pick a Protocol

memio defines four store protocols in `memio.protocols`:

| Protocol | Purpose |
|---|---|
| `FactStore` | Short structured facts scoped to a user or agent |
| `HistoryStore` | Conversation messages grouped by session |
| `DocumentStore` | Documents with semantic search |
| `GraphStore` | Knowledge-graph triples (subject-predicate-object) |

Each protocol is decorated with `@runtime_checkable`, so `isinstance()`
works at runtime.  Choose the one that matches the kind of data your
backend stores.

For this guide we will implement **FactStore**.

---

## 2. Implement All Methods

A `FactStore` requires seven async methods: `add`, `get`, `search`,
`update`, `delete`, `delete_all`, and `get_all`.

Here is a complete, working in-memory implementation:

```python
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from memio.exceptions import ProviderError
from memio.models import Fact


class InMemoryFactStore:
    """A FactStore backed by a plain dictionary.

    Useful for testing or as a starting point for a real adapter.
    """

    def __init__(self) -> None:
        self._store: dict[str, Fact] = {}

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            fact = Fact(
                id=str(uuid.uuid4()),
                content=content,
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata,
                created_at=datetime.now(timezone.utc),
            )
            self._store[fact.id] = fact
            return fact
        except Exception as e:
            raise ProviderError("in-memory", "add", e) from e

    async def get(self, *, fact_id: str) -> Fact:
        try:
            return self._store[fact_id]
        except Exception as e:
            raise ProviderError("in-memory", "get", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Fact]:
        try:
            results = []
            for fact in self._store.values():
                if user_id and fact.user_id != user_id:
                    continue
                if agent_id and fact.agent_id != agent_id:
                    continue
                if query.lower() in fact.content.lower():
                    results.append(fact)
            return results[:limit]
        except Exception as e:
            raise ProviderError("in-memory", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            existing = self._store[fact_id]
            updated = Fact(
                id=existing.id,
                content=content,
                user_id=existing.user_id,
                agent_id=existing.agent_id,
                metadata=metadata if metadata is not None else existing.metadata,
                created_at=existing.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            self._store[fact_id] = updated
            return updated
        except Exception as e:
            raise ProviderError("in-memory", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        try:
            del self._store[fact_id]
        except Exception as e:
            raise ProviderError("in-memory", "delete", e) from e

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        try:
            if user_id is None and agent_id is None:
                self._store.clear()
                return
            to_remove = [
                fid
                for fid, f in self._store.items()
                if (user_id is None or f.user_id == user_id)
                and (agent_id is None or f.agent_id == agent_id)
            ]
            for fid in to_remove:
                del self._store[fid]
        except Exception as e:
            raise ProviderError("in-memory", "delete_all", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        try:
            results = []
            for fact in self._store.values():
                if user_id and fact.user_id != user_id:
                    continue
                if agent_id and fact.agent_id != agent_id:
                    continue
                results.append(fact)
            return results[:limit]
        except Exception as e:
            raise ProviderError("in-memory", "get_all", e) from e
```

Every method is `async` and uses keyword-only arguments, matching the
`FactStore` protocol exactly.

---

## 3. Wrap Errors

Every public method should catch exceptions and re-raise them as
`ProviderError`.  This gives callers a single, predictable error type
regardless of which backend is in use.

```python
from memio.exceptions import ProviderError

try:
    # ... your backend call ...
except Exception as e:
    raise ProviderError("my-provider", "add", e) from e
```

`ProviderError` takes three arguments:

| Argument | Description |
|---|---|
| `provider` | A short name for your backend (e.g. `"redis"`, `"sqlite"`) |
| `operation` | The method that failed (e.g. `"add"`, `"search"`) |
| `cause` | The original exception |

The `from e` clause preserves the full traceback so debugging stays easy.

---

## 4. Use It with Memio

Pass your store to the `Memio` client just like any built-in adapter:

```python
import asyncio
from memio import Memio

async def main():
    client = Memio(facts=InMemoryFactStore())

    fact = await client.facts.add(
        content="prefers dark mode",
        user_id="alice",
    )
    print(fact)

    results = await client.facts.search(query="dark", user_id="alice")
    print(results)

asyncio.run(main())
```

You can combine custom and built-in stores in the same client:

```python
from memio.providers.chroma import ChromaDocumentAdapter

client = Memio(
    facts=InMemoryFactStore(),
    documents=ChromaDocumentAdapter(client=chroma_client, collection_name="docs"),
)
```

---

## 5. Runtime Protocol Checking

When you instantiate `Memio`, it validates each store with `isinstance()`
against the corresponding protocol.  If your class is missing a method
or has a wrong signature, you will get a `TypeError` immediately:

```python
class BrokenStore:
    async def add(self, *, content: str) -> Fact: ...
    # missing get, search, update, delete, delete_all, get_all

Memio(facts=BrokenStore())
# TypeError: facts must implement FactStore protocol
```

This check runs at init time -- not at call time -- so you find problems
early.

!!! tip
    Because the protocols use `@runtime_checkable`, you can also test
    conformance in your own code:

    ```python
    from memio.protocols import FactStore

    store = InMemoryFactStore()
    assert isinstance(store, FactStore)
    ```
