# Documentation Site Design

**Date:** 2026-03-26
**Status:** Approved
**Stack:** MkDocs Material + mkdocstrings + GitHub Pages

## Overview

A documentation website for memio covering both user-facing guides and contributor documentation. API reference is auto-generated from Python docstrings via mkdocstrings.

## Site Structure

```
docs/
├── index.md                  # Home — what memio is, quick install
├── getting-started/
│   ├── installation.md       # Install options (core, providers, dev)
│   └── quickstart.md         # First working example
├── concepts/
│   └── architecture.md       # Protocols, adapters, composability, error handling
├── providers/
│   ├── mem0.md               # Mem0 setup, supported stores, quirks
│   ├── zep.md                # Zep setup, eventual consistency notes
│   └── chroma.md             # Chroma setup, local/persistent usage
├── guides/
│   └── custom-providers.md   # How to implement your own adapter
├── api/                      # Auto-generated from docstrings
│   ├── client.md             # Memio class
│   ├── models.md             # Fact, Message, Document, Triple, GraphResult
│   ├── protocols.md          # FactStore, HistoryStore, DocumentStore, GraphStore
│   └── exceptions.md         # MemioError, ProviderError
└── contributing/
    ├── development.md        # Dev setup, running tests, project structure
    └── adding-providers.md   # Step-by-step guide for new provider adapters
```

## Navigation

```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
  - Concepts:
    - Architecture: concepts/architecture.md
  - Providers:
    - Mem0: providers/mem0.md
    - Zep: providers/zep.md
    - Chroma: providers/chroma.md
  - Guides:
    - Custom Providers: guides/custom-providers.md
  - API Reference:
    - Client: api/client.md
    - Models: api/models.md
    - Protocols: api/protocols.md
    - Exceptions: api/exceptions.md
  - Contributing:
    - Development: contributing/development.md
    - Adding Providers: contributing/adding-providers.md
```

## Auto-Generated API Reference

API reference pages use mkdocstrings directives to pull documentation from source code:

```markdown
# Models

::: memio.models.Fact

::: memio.models.Message
```

This requires docstrings in the source modules: `client.py`, `models.py`, `protocols.py`, `exceptions.py`.

## Deployment

GitHub Actions workflow (`.github/workflows/docs.yml`) deploys to GitHub Pages on push to `main`. Uses `mkdocs gh-deploy`.

## Dependencies

Added to `pyproject.toml` under `[project.optional-dependencies]`:

```toml
docs = ["mkdocs-material", "mkdocstrings[python]"]
```

## Files to Create/Modify

### New files
- `mkdocs.yml` — MkDocs configuration
- `docs/**/*.md` — all documentation pages (14 files)
- `.github/workflows/docs.yml` — GitHub Pages deployment workflow

### Modified files
- `pyproject.toml` — add `docs` optional dependency
- `memio/client.py` — add docstrings
- `memio/models.py` — add docstrings
- `memio/protocols.py` — add docstrings
- `memio/exceptions.py` — add docstrings

## Content Guidelines

- Narrative docs are hand-written markdown
- API docs are auto-generated from docstrings — keep docstrings accurate
- Code examples should be copy-pasteable
- Provider pages should cover: install, setup, supported stores, known quirks/limitations
