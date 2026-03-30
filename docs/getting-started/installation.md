# Installation

## Requirements

- Python **>= 3.10**

## Core install

Install the memio core package (no provider dependencies):

```bash
pip install memio
```

The core package has **zero production dependencies**. It provides the `Memio` client, all data models (`Fact`, `Message`, `Document`, `Triple`, `GraphResult`), the store protocols, and the exception classes.

## Provider extras

Each memory provider is an optional extra. Install only what you need:

=== "Chroma"

    ```bash
    pip install memio[chroma]
    ```

    Installs `chromadb`. Runs locally with no API key required.

=== "Mem0"

    ```bash
    pip install memio[mem0]
    ```

    Installs `mem0ai`. Requires a Mem0 API key.

=== "Zep"

    ```bash
    pip install memio[zep]
    ```

    Installs `zep-cloud`. Requires a Zep API key.

=== "Supermemory"

    ```bash
    pip install memio[supermemory]
    ```

    Installs `supermemory`. Requires a Supermemory API key.

=== "All providers"

    ```bash
    pip install memio[all]
    ```

    Installs all four providers at once.

## Development install

To contribute or run tests locally:

```bash
git clone https://github.com/y3zai/memio.git
cd memio
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
```

This installs all providers plus the test dependencies (`pytest`, `pytest-asyncio`, `pytest-mock`).

## Verify installation

```bash
python -c "import memio; print('memio installed')"
```

You should see:

```
memio installed
```

To verify a specific provider is available:

```bash
python -c "from memio.providers.chroma import ChromaDocumentAdapter; print('chroma ready')"
python -c "from memio.providers.mem0 import Mem0FactAdapter; print('mem0 ready')"
python -c "from memio.providers.zep import ZepHistoryAdapter; print('zep ready')"
python -c "from memio.providers.supermemory import SupermemoryFactAdapter; print('supermemory ready')"
```

## Next steps

Once installed, head to the [Quick Start](quickstart.md) for working examples.
