# Development

How to set up a local development environment and run the test suite.

---

## Clone the Repository

```bash
git clone https://github.com/y3zai/memio.git
cd memio
```

## Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

The `all` extra pulls in every provider SDK. The `dev` extra adds
pytest and related tooling.

```bash
pip install -e ".[all,dev]"
```

---

## Running Tests

### Unit Tests

Unit tests use mocks and do not require API keys. They run by default:

```bash
pytest
```

Integration tests are excluded automatically (see `addopts` in
`pyproject.toml`).

### Integration Tests

Integration tests hit real provider APIs. Set the required environment
variables and select the `integration` marker:

```bash
MEM0_API_KEY=... ZEP_API_KEY=... pytest -m integration -v
```

Chroma integration tests use a local ephemeral client and do not require
an API key.

---

## Project Structure

```
memio/
├── memio/                   # Library source
│   ├── __init__.py          # Public API exports
│   ├── client.py            # Memio gateway class
│   ├── models.py            # Dataclasses (Fact, Message, Document, Triple, GraphResult)
│   ├── protocols.py         # Store protocols (FactStore, HistoryStore, etc.)
│   ├── exceptions.py        # MemioError and ProviderError
│   └── providers/           # Provider adapters
│       ├── mem0/            # Mem0 adapters (fact, graph)
│       ├── zep/             # Zep adapters (fact, history, graph)
│       └── chroma/          # Chroma adapter (document)
├── tests/
│   ├── test_client.py       # Client unit tests
│   ├── test_models.py       # Model unit tests
│   ├── test_protocols.py    # Protocol conformance checks
│   ├── test_exceptions.py   # Exception unit tests
│   ├── providers/           # Per-adapter unit tests (mocked)
│   ├── integration/         # Integration tests (real APIs)
│   └── conformance/         # Reusable conformance suites per store type
├── docs/                    # MkDocs documentation source
├── pyproject.toml           # Build config, dependencies, pytest settings
└── mkdocs.yml               # Documentation site configuration
```

### Key directories

- **`memio/`** -- The library itself. Every public symbol is re-exported
  from `memio/__init__.py`.
- **`memio/providers/`** -- Each subdirectory contains adapter classes
  that wrap a third-party SDK and expose one or more store protocols.
- **`tests/providers/`** -- Unit tests for individual adapters. Each test
  file mocks the underlying SDK so tests run without network access.
- **`tests/integration/`** -- End-to-end tests that call real provider
  APIs. Guarded by `@pytest.mark.integration` and skipped when the
  required API key is not set.
- **`tests/conformance/`** -- Shared test helpers (e.g.
  `fact_store_conformance`) that exercise the full CRUD cycle against
  any store implementation. Used by both unit and integration tests.

---

## Code Style

- **Async-first.** All store methods are `async`. Provider adapters
  must not block the event loop.
- **Keyword-only arguments.** Public method signatures use `*` to
  enforce keyword arguments, matching the protocol definitions.
- **Error wrapping.** Every public method in a provider adapter must
  catch exceptions and wrap them in `ProviderError`. Callers should
  never see raw SDK exceptions.
- **Type hints.** Use `from __future__ import annotations` and
  standard library types (`str | None` rather than `Optional[str]`).
