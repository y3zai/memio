"""Supermemory FactStore adapter.

Known quirks:
- Supermemory auto-extracts facts from content via LLM (may rephrase)
- get() is not supported — Supermemory has no get-by-memory-ID endpoint
- get_all() uses a broad search query as an approximation
- delete() soft-deletes via forget() (memory marked forgotten, not purged)
- delete_all() is not supported — no bulk forget endpoint
- container_tag maps to user_id; agent_id is not directly supported
"""

from __future__ import annotations

from datetime import datetime

from memio.exceptions import NotSupportedError, ProviderError
from memio.models import Fact


class SupermemoryFactAdapter:
    """FactStore implementation backed by Supermemory.

    Args:
        api_key: Supermemory API key. If not provided, reads from
            ``SUPERMEMORY_API_KEY`` environment variable.
    """

    def __init__(self, *, api_key: str | None = None):
        try:
            from supermemory import AsyncSupermemory
        except ImportError:
            raise ImportError(
                "supermemory provider requires supermemory: "
                "pip install memio[supermemory]"
            )
        kwargs: dict = {}
        if api_key:
            kwargs["api_key"] = api_key
        self._client = AsyncSupermemory(**kwargs)

    def _container_tag(
        self, user_id: str | None, agent_id: str | None,
    ) -> str | None:
        if user_id and agent_id:
            return f"{user_id}--{agent_id}"
        return user_id or agent_id

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"content": content}
            tag = self._container_tag(user_id, agent_id)
            if tag:
                kwargs["container_tag"] = tag
            if metadata:
                kwargs["metadata"] = metadata
            result = await self._client.add(**kwargs)
            return Fact(
                id=result.id,
                content=content,
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata,
            )
        except Exception as e:
            raise ProviderError("supermemory", "add", e) from e

    async def get(self, *, fact_id: str) -> Fact:
        raise NotSupportedError(
            "supermemory", "get",
            hint="Supermemory has no get-by-ID endpoint for memories; "
                 "use search() instead",
        )

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        try:
            kwargs: dict = {"q": "", "limit": limit, "search_mode": "memories"}
            tag = self._container_tag(user_id, agent_id)
            if tag:
                kwargs["container_tag"] = tag
            result = await self._client.search.memories(**kwargs)
            return [self._to_fact(r, user_id, agent_id) for r in result.results]
        except Exception as e:
            raise ProviderError("supermemory", "get_all", e) from e

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
            kwargs: dict = {
                "q": query, "limit": limit, "search_mode": "memories",
            }
            tag = self._container_tag(user_id, agent_id)
            if tag:
                kwargs["container_tag"] = tag
            if filters:
                kwargs["filters"] = filters
            result = await self._client.search.memories(**kwargs)
            return [self._to_fact(r, user_id, agent_id) for r in result.results]
        except Exception as e:
            raise ProviderError("supermemory", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {
                "id": fact_id,
                "new_content": content,
                "container_tag": "",
            }
            if metadata:
                kwargs["metadata"] = metadata
            await self._client.memories.update_memory(**kwargs)
            return Fact(id=fact_id, content=content, metadata=metadata)
        except Exception as e:
            raise ProviderError("supermemory", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        try:
            await self._client.memories.forget(
                container_tag="", id=fact_id,
            )
        except Exception as e:
            raise ProviderError("supermemory", "delete", e) from e

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        raise NotSupportedError(
            "supermemory", "delete_all",
            hint="Supermemory has no bulk forget endpoint; "
                 "delete memories individually with delete()",
        )

    @staticmethod
    def _to_fact(
        entry, user_id: str | None, agent_id: str | None,
    ) -> Fact:
        updated_at = None
        if getattr(entry, "updated_at", None):
            try:
                updated_at = datetime.fromisoformat(entry.updated_at)
            except (ValueError, TypeError):
                pass
        return Fact(
            id=entry.id,
            content=entry.memory or "",
            user_id=user_id,
            agent_id=agent_id,
            metadata=dict(entry.metadata) if entry.metadata else None,
            score=entry.similarity if hasattr(entry, "similarity") else None,
            updated_at=updated_at,
        )
