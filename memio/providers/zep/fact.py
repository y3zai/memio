# memio/providers/zep/fact.py
from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Fact


class ZepFactAdapter:
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
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"data": content, "type": "text"}
            if user_id:
                kwargs["user_id"] = user_id
            episode = await self._client.graph.add(**kwargs)
            return Fact(
                id=episode.uuid_,
                content=content,
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata,
            )
        except Exception as e:
            raise ProviderError("zep", "add", e) from e

    async def get(self, *, fact_id: str) -> Fact:
        try:
            edge = await self._client.graph.edge.get(fact_id)
            return self._edge_to_fact(edge)
        except Exception as e:
            raise ProviderError("zep", "get", e) from e

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
            kwargs: dict = {"query": query, "limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            results = await self._client.graph.search(**kwargs)
            facts = []
            for edge in results.edges or []:
                facts.append(self._edge_to_fact(edge))
            return facts
        except Exception as e:
            raise ProviderError("zep", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"fact": content}
            if metadata:
                kwargs["attributes"] = metadata
            edge = await self._client.graph.edge.update(fact_id, **kwargs)
            return self._edge_to_fact(edge)
        except Exception as e:
            raise ProviderError("zep", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        # Zep doesn't have direct edge delete in the public API
        # This is a limitation — raise clear error
        raise ProviderError(
            "zep", "delete",
            NotImplementedError("Zep does not support deleting individual facts"),
        )

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        try:
            if user_id:
                await self._client.user.delete(user_id)
        except Exception as e:
            raise ProviderError("zep", "delete_all", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        try:
            if user_id:
                edges = await self._client.graph.edge.get_by_user_id(
                    user_id, limit=limit,
                )
            else:
                edges = []
            return [self._edge_to_fact(edge) for edge in edges]
        except Exception as e:
            raise ProviderError("zep", "get_all", e) from e

    @staticmethod
    def _edge_to_fact(edge) -> Fact:
        created_at = None
        if hasattr(edge, "created_at") and edge.created_at:
            try:
                created_at = datetime.fromisoformat(str(edge.created_at))
            except (ValueError, TypeError):
                pass
        return Fact(
            id=edge.uuid_,
            content=edge.fact,
            metadata=getattr(edge, "attributes", None),
            score=getattr(edge, "score", None),
            created_at=created_at,
        )
