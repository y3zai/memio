# Adding a New Provider

This walkthrough covers all the steps required to contribute a new
provider adapter to memio. We will use a hypothetical provider called
`acme` as the running example.

For the simplest real-world reference, look at
`memio/providers/chroma/document.py` -- it implements `DocumentStore`
in about 100 lines.

---

## 1. Create the Provider Directory

```
memio/providers/acme/
├── __init__.py
└── fact.py          # one file per store type you implement
```

Each provider lives in its own package under `memio/providers/`.

## 2. Create `__init__.py` with Exports

Re-export every adapter class so users can import directly from the
package:

```python
# memio/providers/acme/__init__.py
from memio.providers.acme.fact import AcmeFactAdapter

__all__ = ["AcmeFactAdapter"]
```

## 3. Implement the Adapter Class

Follow the pattern used by existing adapters:

```python
# memio/providers/acme/fact.py
from __future__ import annotations

from memio.exceptions import ProviderError
from memio.models import Fact


class AcmeFactAdapter:
    def __init__(self, *, api_key: str):
        try:
            from acme_sdk import AcmeClient  # lazy import
        except ImportError:
            raise ImportError(
                "acme provider requires acme-sdk: pip install memio[acme]"
            )
        self._client = AcmeClient(api_key=api_key)

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            result = await self._client.create_fact(content, user_id=user_id)
            return Fact(id=result["id"], content=content, user_id=user_id)
        except Exception as e:
            raise ProviderError("acme", "add", e) from e

    # ... remaining methods: get, search, update, delete, delete_all, get_all
```

Key conventions:

- **Lazy SDK import** in `__init__` with a helpful `ImportError` message.
- **Keyword-only arguments** matching the protocol signatures in
  `memio/protocols.py`.
- **Return memio model objects** (`Fact`, `Document`, etc.), not raw
  SDK responses.

## 4. Wrap Every Exception in ProviderError

Every public method must follow this pattern:

```python
async def get(self, *, fact_id: str) -> Fact:
    try:
        result = await self._client.get(fact_id)
        return Fact(id=result["id"], content=result["text"])
    except Exception as e:
        raise ProviderError("acme", "get", e) from e
```

This ensures callers only need to catch `ProviderError`, regardless of
which provider is in use. Always use `from e` to preserve the original
traceback.

## 5. Add Unit Tests with Mocks

Create `tests/providers/test_acme_fact.py`. Mock the SDK client so
tests run without network access:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from memio.providers.acme.fact import AcmeFactAdapter
from memio.exceptions import ProviderError
from memio.models import Fact


@pytest.fixture
def adapter(monkeypatch):
    # Prevent real import of acme_sdk
    mock_module = MagicMock()
    monkeypatch.setitem(__import__("sys").modules, "acme_sdk", mock_module)

    adapter = AcmeFactAdapter(api_key="test-key")
    adapter._client = AsyncMock()
    return adapter


async def test_add_returns_fact(adapter):
    adapter._client.create_fact.return_value = {
        "id": "f-1",
        "text": "likes coffee",
    }
    fact = await adapter.add(content="likes coffee", user_id="alice")
    assert isinstance(fact, Fact)
    assert fact.id == "f-1"


async def test_add_wraps_error(adapter):
    adapter._client.create_fact.side_effect = RuntimeError("boom")
    with pytest.raises(ProviderError) as exc_info:
        await adapter.add(content="oops")
    assert exc_info.value.provider == "acme"
    assert exc_info.value.operation == "add"
```

Run with:

```bash
pytest tests/providers/test_acme_fact.py -v
```

## 6. Add an Integration Test

Create `tests/integration/test_acme.py`. Guard it with the
`integration` marker and skip when the API key is missing:

```python
import os
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def acme_api_key():
    key = os.environ.get("ACME_API_KEY")
    if not key:
        pytest.skip("ACME_API_KEY not set")
    return key


class TestAcmeFactIntegration:
    async def test_conformance(self, acme_api_key):
        from memio.providers.acme import AcmeFactAdapter
        from tests.conformance.fact_store import fact_store_conformance

        adapter = AcmeFactAdapter(api_key=acme_api_key)
        await fact_store_conformance(adapter)
```

The conformance suites in `tests/conformance/` exercise full CRUD
cycles, so you get thorough coverage with minimal test code.

## 7. Add the Optional Dependency

In `pyproject.toml`, add the SDK under `[project.optional-dependencies]`
and include it in the `all` extra:

```toml
[project.optional-dependencies]
mem0 = ["mem0ai"]
zep = ["zep-cloud"]
chroma = ["chromadb"]
acme = ["acme-sdk"]                                    # new
all = ["mem0ai", "zep-cloud", "chromadb", "acme-sdk"]  # updated
```

Users can then install with:

```bash
pip install memio[acme]
```

## 8. Add a Documentation Page

Create `docs/providers/acme.md` covering installation, initialization,
and a short usage example. Follow the structure of the existing provider
pages (e.g. `docs/providers/chroma.md`).

## 9. Update `mkdocs.yml` Navigation

Add the new provider to the `nav` section:

```yaml
nav:
  # ...
  - Providers:
      - Mem0: providers/mem0.md
      - Zep: providers/zep.md
      - Chroma: providers/chroma.md
      - Acme: providers/acme.md    # new
```

---

## Checklist

Before opening a pull request, verify that:

- [ ] Adapter class passes `isinstance()` check against its protocol
- [ ] All public methods wrap exceptions in `ProviderError`
- [ ] Unit tests pass: `pytest tests/providers/test_acme_fact.py -v`
- [ ] Integration test passes (if you have an API key):
      `ACME_API_KEY=... pytest tests/integration/test_acme.py -v`
- [ ] Optional dependency added to `pyproject.toml`
- [ ] Docs page created and `mkdocs.yml` updated
