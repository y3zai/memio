# Documentation Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MkDocs Material documentation site with auto-generated API reference, deployed to GitHub Pages.

**Architecture:** MkDocs Material for static site generation, mkdocstrings for API reference from docstrings, GitHub Actions for deployment to GitHub Pages on push to main.

**Tech Stack:** mkdocs-material, mkdocstrings[python], GitHub Actions

---

## File Structure

### New files
- `mkdocs.yml` — MkDocs configuration (theme, nav, plugins)
- `.github/workflows/docs.yml` — GitHub Actions workflow for GitHub Pages
- `docs/index.md` — Home page
- `docs/getting-started/installation.md` — Install instructions
- `docs/getting-started/quickstart.md` — First working example
- `docs/concepts/architecture.md` — Protocols, adapters, composability
- `docs/providers/mem0.md` — Mem0 provider guide
- `docs/providers/zep.md` — Zep provider guide
- `docs/providers/chroma.md` — Chroma provider guide
- `docs/guides/custom-providers.md` — How to build your own adapter
- `docs/api/client.md` — mkdocstrings directive for Memio class
- `docs/api/models.md` — mkdocstrings directives for all models
- `docs/api/protocols.md` — mkdocstrings directives for all protocols
- `docs/api/exceptions.md` — mkdocstrings directives for exceptions
- `docs/contributing/development.md` — Dev setup guide
- `docs/contributing/adding-providers.md` — New provider walkthrough

### Modified files
- `pyproject.toml` — add `docs` optional dependency
- `memio/client.py` — add docstrings
- `memio/models.py` — add docstrings
- `memio/protocols.py` — add docstrings
- `memio/exceptions.py` — add docstrings

---

### Task 1: Add docs dependencies and MkDocs config

**Files:**
- Modify: `pyproject.toml`
- Create: `mkdocs.yml`

- [ ] **Step 1: Add docs dependency to pyproject.toml**

Add to `[project.optional-dependencies]`:

```toml
docs = ["mkdocs-material", "mkdocstrings[python]"]
```

- [ ] **Step 2: Create mkdocs.yml**

```yaml
site_name: memio
site_url: https://y3zai.github.io/memio/
site_description: Unified memory gateway for AI agents
repo_url: https://github.com/y3zai/memio
repo_name: y3zai/memio

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.sections
    - navigation.expand
    - content.code.copy
    - search.highlight

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: false
            show_root_heading: true
            heading_level: 3
            docstring_style: google
            show_signature_annotations: true
            separate_signature: true

markdown_extensions:
  - admonition
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - toc:
      permalink: true

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

- [ ] **Step 3: Install docs dependencies**

Run: `pip install -e ".[docs]"`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml mkdocs.yml
git commit -m "build: add MkDocs Material config and docs dependencies"
```

---

### Task 2: Add docstrings to source modules

**Files:**
- Modify: `memio/models.py`
- Modify: `memio/client.py`
- Modify: `memio/protocols.py`
- Modify: `memio/exceptions.py`

- [ ] **Step 1: Add docstrings to models.py**

Add Google-style docstrings to all dataclasses:

```python
@dataclass
class Fact:
    """A stored piece of knowledge about a user or agent.

    Attributes:
        id: Unique identifier for the fact.
        content: The fact content as text.
        user_id: ID of the user this fact belongs to.
        agent_id: ID of the agent this fact belongs to.
        metadata: Arbitrary key-value metadata.
        score: Relevance score from search results.
        created_at: When the fact was created.
        updated_at: When the fact was last updated.
    """
```

```python
@dataclass
class Message:
    """A conversation message in a session.

    Attributes:
        role: The message role (e.g. "user", "assistant", "system").
        content: The message content as text.
        metadata: Arbitrary key-value metadata.
        timestamp: When the message was sent.
        name: Optional display name of the sender.
    """
```

```python
@dataclass
class Document:
    """A stored document with optional metadata.

    Attributes:
        id: Unique identifier for the document.
        content: The document content as text.
        metadata: Arbitrary key-value metadata.
        score: Relevance score from search results.
        created_at: When the document was created.
        updated_at: When the document was last updated.
    """
```

```python
@dataclass
class Triple:
    """A knowledge graph triple representing a relationship.

    Attributes:
        subject: The source entity.
        predicate: The relationship type.
        object: The target entity.
        metadata: Arbitrary key-value metadata.
    """
```

```python
@dataclass
class GraphResult:
    """Result from a knowledge graph query.

    Attributes:
        triples: List of matching triples.
        nodes: List of entity names.
        scores: Relevance scores for each result.
    """
```

- [ ] **Step 2: Add docstrings to client.py**

```python
class Memio:
    """Unified memory gateway for AI agents.

    Composes one or more memory stores into a single client. Each store
    is validated against its protocol at initialization.

    Args:
        facts: A FactStore implementation for structured facts.
        history: A HistoryStore implementation for conversation history.
        documents: A DocumentStore implementation for document storage.
        graph: A GraphStore implementation for knowledge graphs.

    Raises:
        ValueError: If no memory stores are provided.
        TypeError: If a store does not implement its expected protocol.

    Example:
        ```python
        from memio import Memio
        from memio.providers.mem0 import Mem0FactAdapter

        client = Memio(facts=Mem0FactAdapter(api_key="..."))
        fact = await client.facts.add(content="likes coffee", user_id="alice")
        ```
    """
```

- [ ] **Step 3: Add docstrings to protocols.py**

```python
@runtime_checkable
class FactStore(Protocol):
    """Protocol for storing and retrieving structured facts.

    Facts are short pieces of knowledge scoped to a user or agent.
    Implementations must provide all methods as async.
    """
```

```python
@runtime_checkable
class HistoryStore(Protocol):
    """Protocol for storing and retrieving conversation history.

    Messages are grouped by session ID. Implementations must provide
    all methods as async.
    """
```

```python
@runtime_checkable
class DocumentStore(Protocol):
    """Protocol for storing and searching documents.

    Documents support semantic search and optional metadata filtering.
    Implementations must provide all methods as async.
    """
```

```python
@runtime_checkable
class GraphStore(Protocol):
    """Protocol for storing and querying knowledge graph triples.

    Triples represent subject-predicate-object relationships.
    Implementations must provide all methods as async.
    """
```

- [ ] **Step 4: Add docstrings to exceptions.py**

```python
class MemioError(Exception):
    """Base exception for all memio errors."""

class ProviderError(MemioError):
    """Wraps provider SDK exceptions with context.

    Attributes:
        provider: Name of the provider (e.g. "mem0", "zep", "chroma").
        operation: Name of the operation that failed (e.g. "add", "search").
        cause: The original exception from the provider SDK.
    """
```

- [ ] **Step 5: Run unit tests to verify docstrings didn't break anything**

Run: `.venv/bin/python -m pytest tests/ -m 'not integration' -v`
Expected: 80 passed

- [ ] **Step 6: Commit**

```bash
git add memio/models.py memio/client.py memio/protocols.py memio/exceptions.py
git commit -m "docs: add docstrings to core modules for mkdocstrings"
```

---

### Task 3: Create documentation pages — Home, Getting Started

**Files:**
- Create: `docs/index.md`
- Create: `docs/getting-started/installation.md`
- Create: `docs/getting-started/quickstart.md`

- [ ] **Step 1: Create docs/index.md**

Home page with project overview, feature list, and quick install. Adapted from README but formatted for the docs site. Include a brief code example and links to the Getting Started section.

- [ ] **Step 2: Create docs/getting-started/installation.md**

Cover: pip install (core, per-provider extras, all, dev), Python version requirement (>=3.10), verifying installation with `python -c "import memio"`.

- [ ] **Step 3: Create docs/getting-started/quickstart.md**

Full working example: create a Memio client with Chroma (no API key needed), add a document, search, retrieve. Then show a multi-provider example with Mem0 + Zep + Chroma.

- [ ] **Step 4: Commit**

```bash
git add docs/index.md docs/getting-started/
git commit -m "docs: add home page and getting started guides"
```

---

### Task 4: Create documentation pages — Concepts, Providers

**Files:**
- Create: `docs/concepts/architecture.md`
- Create: `docs/providers/mem0.md`
- Create: `docs/providers/zep.md`
- Create: `docs/providers/chroma.md`

- [ ] **Step 1: Create docs/concepts/architecture.md**

Cover: protocol-based design, how adapters work, composability (mix providers), error wrapping pattern, async-first design, multi-tenancy via user_id/agent_id. Include a diagram showing the layered architecture (text-based).

- [ ] **Step 2: Create docs/providers/mem0.md**

Cover: install (`pip install memio[mem0]`), setup (API key from mem0.ai), supported stores (FactStore, GraphStore), usage examples for each, known quirks (LLM rephrasing, deduplication, individual graph delete not supported).

- [ ] **Step 3: Create docs/providers/zep.md**

Cover: install (`pip install memio[zep]`), setup (API key from getzep.com), supported stores (FactStore, HistoryStore, GraphStore), usage examples, known quirks (eventual consistency for graph, AsyncHttpResponse unwrapping, individual fact/triple delete not supported, user auto-creation).

- [ ] **Step 4: Create docs/providers/chroma.md**

Cover: install (`pip install memio[chroma]`), setup (EphemeralClient vs PersistentClient), supported stores (DocumentStore), usage examples, score calculation (1/(1+distance)), no API key needed.

- [ ] **Step 5: Commit**

```bash
git add docs/concepts/ docs/providers/
git commit -m "docs: add architecture concepts and provider guides"
```

---

### Task 5: Create documentation pages — Guides, Contributing

**Files:**
- Create: `docs/guides/custom-providers.md`
- Create: `docs/contributing/development.md`
- Create: `docs/contributing/adding-providers.md`

- [ ] **Step 1: Create docs/guides/custom-providers.md**

Step-by-step guide: pick a protocol, implement all methods, wrap errors in ProviderError, pass it to Memio. Full working example implementing a minimal in-memory FactStore. Explain runtime protocol checking.

- [ ] **Step 2: Create docs/contributing/development.md**

Cover: clone, venv, install dev deps, running unit tests, running integration tests with API keys, project structure overview (what each directory contains).

- [ ] **Step 3: Create docs/contributing/adding-providers.md**

Walkthrough: create a `memio/providers/<name>/` directory, implement adapter classes, add unit tests with mocks, add integration tests, add optional dependency to pyproject.toml, add provider docs page. Reference existing adapters as examples.

- [ ] **Step 4: Commit**

```bash
git add docs/guides/ docs/contributing/
git commit -m "docs: add custom provider guide and contributing docs"
```

---

### Task 6: Create API reference pages

**Files:**
- Create: `docs/api/client.md`
- Create: `docs/api/models.md`
- Create: `docs/api/protocols.md`
- Create: `docs/api/exceptions.md`

- [ ] **Step 1: Create docs/api/client.md**

```markdown
# Client

The `Memio` class is the main entry point for using memio.

::: memio.client.Memio
```

- [ ] **Step 2: Create docs/api/models.md**

```markdown
# Models

Data models used across all providers.

::: memio.models.Fact

::: memio.models.Message

::: memio.models.Document

::: memio.models.Triple

::: memio.models.GraphResult
```

- [ ] **Step 3: Create docs/api/protocols.md**

```markdown
# Protocols

Store protocols that providers must implement.

::: memio.protocols.FactStore

::: memio.protocols.HistoryStore

::: memio.protocols.DocumentStore

::: memio.protocols.GraphStore
```

- [ ] **Step 4: Create docs/api/exceptions.md**

```markdown
# Exceptions

::: memio.exceptions.MemioError

::: memio.exceptions.ProviderError
```

- [ ] **Step 5: Commit**

```bash
git add docs/api/
git commit -m "docs: add auto-generated API reference pages"
```

---

### Task 7: Build and verify locally

- [ ] **Step 1: Build the docs site locally**

Run: `mkdocs serve`

Open http://127.0.0.1:8000 in a browser. Verify:
- Navigation works (all pages load)
- API reference pages render docstrings correctly
- Code examples have syntax highlighting and copy buttons
- Dark/light mode toggle works
- Search works

- [ ] **Step 2: Fix any build warnings or rendering issues**

Check the terminal output from `mkdocs serve` for warnings. Fix any issues.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "docs: fix build warnings"
```

---

### Task 8: Add GitHub Actions deployment workflow

**Files:**
- Create: `.github/workflows/docs.yml`

- [ ] **Step 1: Create .github/workflows/docs.yml**

```yaml
name: Deploy docs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install mkdocs-material "mkdocstrings[python]"
      - run: mkdocs gh-deploy --force
```

- [ ] **Step 2: Commit and push**

```bash
git add .github/workflows/docs.yml
git commit -m "ci: add GitHub Actions workflow for docs deployment"
git push
```

- [ ] **Step 3: Enable GitHub Pages**

In the GitHub repo settings, go to Pages and set source to "Deploy from a branch", branch `gh-pages`, root `/`. The workflow creates this branch automatically on first run.

- [ ] **Step 4: Verify deployment**

Check GitHub Actions to confirm the workflow ran successfully. Visit https://y3zai.github.io/memio/ to verify the site is live.
