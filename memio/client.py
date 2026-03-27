from __future__ import annotations

from memio.protocols import DocumentStore, FactStore, GraphStore, HistoryStore


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

    def __init__(
        self,
        *,
        facts: FactStore | None = None,
        history: HistoryStore | None = None,
        documents: DocumentStore | None = None,
        graph: GraphStore | None = None,
    ):
        if not any([facts, history, documents, graph]):
            raise ValueError("At least one memory store must be provided")

        if facts is not None and not isinstance(facts, FactStore):
            raise TypeError("facts must implement FactStore protocol")
        if history is not None and not isinstance(history, HistoryStore):
            raise TypeError("history must implement HistoryStore protocol")
        if documents is not None and not isinstance(documents, DocumentStore):
            raise TypeError("documents must implement DocumentStore protocol")
        if graph is not None and not isinstance(graph, GraphStore):
            raise TypeError("graph must implement GraphStore protocol")

        self.facts = facts
        self.history = history
        self.documents = documents
        self.graph = graph
