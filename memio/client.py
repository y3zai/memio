from __future__ import annotations

from memio.protocols import DocumentStore, FactStore, GraphStore, HistoryStore


class Memio:
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
