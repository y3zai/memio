# memio/providers/zep/graph.py
from __future__ import annotations

from memio.exceptions import NotSupportedError, ProviderError
from memio.models import GraphResult, Triple


class ZepGraphAdapter:
    """GraphStore implementation backed by Zep's graph API.

    Stores triples as fact-triples with predicate-based relationship names.
    Individual entity/triple deletion is not supported; use `delete_all` instead.

    Args:
        api_key: Zep Cloud API key.
        client: Pre-initialized AsyncZep client (overrides api_key).
    """

    def __init__(self, *, api_key: str | None = None, client=None):
        try:
            from zep_cloud import AsyncZep
        except ImportError:
            raise ImportError(
                "zep provider requires zep-cloud: pip install memio[zep]"
            )
        if client is not None:
            self._client = client
        else:
            self._client = AsyncZep(api_key=api_key)

    async def add(
        self,
        *,
        triples: list[Triple],
        user_id: str | None = None,
    ) -> None:
        try:
            for t in triples:
                kwargs: dict = {
                    "fact": f"{t.subject} {t.predicate} {t.object}",
                    "fact_name": t.predicate.upper().replace(" ", "_"),
                    "source_node_name": t.subject,
                    "target_node_name": t.object,
                }
                if t.metadata:
                    kwargs["edge_attributes"] = t.metadata
                if user_id:
                    kwargs["user_id"] = user_id
                await self._client.graph.add_fact_triple(**kwargs)
        except Exception as e:
            raise ProviderError("zep", "add", e) from e

    async def get(
        self,
        *,
        entity: str,
        user_id: str | None = None,
    ) -> GraphResult:
        try:
            # Get all nodes/edges for user, filter by entity name
            all_result = await self.get_all(user_id=user_id)
            filtered_triples = [
                t for t in all_result.triples
                if entity in (t.subject, t.object)
            ]
            nodes = set()
            for t in filtered_triples:
                nodes.add(t.subject)
                nodes.add(t.object)
            return GraphResult(triples=filtered_triples, nodes=sorted(nodes))
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError("zep", "get", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> GraphResult:
        try:
            kwargs: dict = {"limit": limit}
            if user_id:
                nodes_raw = await self._client.graph.node.get_by_user_id(
                    user_id, **kwargs,
                )
                edges_raw = await self._client.graph.edge.get_by_user_id(
                    user_id, **kwargs,
                )
            else:
                nodes_raw = []
                edges_raw = []

            # Build node name lookup
            node_names: dict[str, str] = {}
            for n in nodes_raw:
                node_names[n.uuid_] = n.name

            triples = []
            for e in edges_raw:
                src = node_names.get(e.source_node_uuid, e.source_node_uuid)
                dst = node_names.get(e.target_node_uuid, e.target_node_uuid)
                triples.append(Triple(
                    subject=src,
                    predicate=e.name,
                    object=dst,
                ))

            return GraphResult(
                triples=triples,
                nodes=sorted(node_names.values()),
            )
        except Exception as e:
            raise ProviderError("zep", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        limit: int = 10,
    ) -> GraphResult:
        try:
            kwargs: dict = {"query": query, "limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            results = await self._client.graph.search(**kwargs)

            # Build node name lookup from search results
            node_names: dict[str, str] = {}
            for n in results.nodes or []:
                node_names[n.uuid_] = n.name

            triples = []
            for e in results.edges or []:
                src = node_names.get(e.source_node_uuid, e.source_node_uuid)
                dst = node_names.get(e.target_node_uuid, e.target_node_uuid)
                triples.append(Triple(
                    subject=src,
                    predicate=e.name,
                    object=dst,
                ))

            return GraphResult(
                triples=triples,
                nodes=sorted(node_names.values()),
            )
        except Exception as e:
            raise ProviderError("zep", "search", e) from e

    async def delete(
        self,
        *,
        entity: str | None = None,
        triple_id: str | None = None,
    ) -> None:
        raise NotSupportedError("zep", "delete")

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            if user_id:
                await self._client.user.delete(user_id)
        except Exception as e:
            raise ProviderError("zep", "delete_all", e) from e
