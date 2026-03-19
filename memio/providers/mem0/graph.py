# memio/providers/mem0/graph.py
from __future__ import annotations

from memio.exceptions import ProviderError
from memio.models import GraphResult, Triple


class Mem0GraphAdapter:
    def __init__(self, *, api_key: str | None = None, config: dict | None = None):
        try:
            from mem0 import AsyncMemory
        except ImportError:
            raise ImportError(
                "mem0 provider requires mem0ai: pip install memio[mem0]"
            )
        kwargs = {}
        if config:
            kwargs["config"] = config
        client = AsyncMemory(**kwargs)
        self._client = client
        self._graph = client.graph

    async def add(
        self,
        *,
        triples: list[Triple],
        user_id: str | None = None,
    ) -> None:
        try:
            # Serialize triples to natural language for mem0's LLM extraction
            data = "\n".join(
                f"{t.subject} {t.predicate} {t.object}" for t in triples
            )
            filters: dict = {}
            if user_id:
                filters["user_id"] = user_id
            else:
                filters["user_id"] = "user"
            self._graph.add(data, filters)
        except Exception as e:
            raise ProviderError("mem0", "add", e) from e

    async def get(
        self,
        *,
        entity: str,
        user_id: str | None = None,
    ) -> GraphResult:
        try:
            filters: dict = {"user_id": user_id or "user"}
            raw = self._graph.get_all(filters)
            # Filter to triples involving the entity
            triples = []
            nodes = set()
            for entry in raw:
                src = entry.get("source", "")
                dst = entry.get("destination", entry.get("target", ""))
                if entity in (src, dst):
                    triples.append(Triple(
                        subject=src,
                        predicate=entry.get("relationship", ""),
                        object=dst,
                    ))
                    nodes.add(src)
                    nodes.add(dst)
            return GraphResult(triples=triples, nodes=sorted(nodes))
        except Exception as e:
            raise ProviderError("mem0", "get", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> GraphResult:
        try:
            filters: dict = {"user_id": user_id or "user"}
            raw = self._graph.get_all(filters, limit=limit)
            return self._raw_to_graph_result(raw)
        except Exception as e:
            raise ProviderError("mem0", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        limit: int = 10,
    ) -> GraphResult:
        try:
            filters: dict = {"user_id": user_id or "user"}
            raw = self._graph.search(query, filters, limit=limit)
            return self._raw_to_graph_result(raw)
        except Exception as e:
            raise ProviderError("mem0", "search", e) from e

    async def delete(
        self,
        *,
        entity: str | None = None,
        triple_id: str | None = None,
    ) -> None:
        # mem0 does not support individual entity/relationship deletes
        raise ProviderError(
            "mem0", "delete",
            NotImplementedError("mem0 graph does not support individual deletes; use delete_all"),
        )

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            filters: dict = {"user_id": user_id or "user"}
            self._graph.delete_all(filters)
        except Exception as e:
            raise ProviderError("mem0", "delete_all", e) from e

    @staticmethod
    def _raw_to_graph_result(raw: list[dict]) -> GraphResult:
        triples = []
        nodes = set()
        for entry in raw:
            src = entry.get("source", "")
            dst = entry.get("destination", entry.get("target", ""))
            triples.append(Triple(
                subject=src,
                predicate=entry.get("relationship", ""),
                object=dst,
            ))
            nodes.add(src)
            nodes.add(dst)
        return GraphResult(triples=triples, nodes=sorted(nodes))
