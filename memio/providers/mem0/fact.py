"""Mem0 FactStore adapter.

Known quirks:
- Mem0's LLM may rephrase content (e.g. "likes coffee" → "User likes coffee")
- Adding duplicate content returns empty results (deduplicated automatically)
- Mem0 Cloud processes memories asynchronously; ``add`` polls until the
  memory is ready so callers always receive a usable Fact.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Fact

_POLL_INTERVAL = 1.0  # seconds between polls
_POLL_TIMEOUT = 60.0  # max seconds to wait for async processing


class Mem0FactAdapter:
    """FactStore implementation backed by Mem0.

    Args:
        api_key: Mem0 API key. If not provided, uses the default from environment.
        config: Optional Mem0 client configuration dict.
    """

    def __init__(self, *, api_key: str | None = None, config: dict | None = None):
        try:
            if api_key:
                from mem0 import AsyncMemoryClient
                self._client = AsyncMemoryClient(api_key=api_key)
                self._is_cloud = True
            else:
                from mem0 import AsyncMemory
                kwargs = {}
                if config:
                    kwargs["config"] = config
                self._client = AsyncMemory(**kwargs)
                self._is_cloud = False
        except ImportError:
            raise ImportError(
                "mem0 provider requires mem0ai: pip install memio[mem0]"
            )

    def _build_filters(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        extra: dict | None = None,
    ) -> dict:
        """Build a filters dict for the Mem0 Cloud v2 API."""
        f: dict = {}
        if user_id:
            f["user_id"] = user_id
        if agent_id:
            f["agent_id"] = agent_id
        if extra:
            f.update(extra)
        return f

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            kwargs: dict = {"messages": content}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if metadata:
                kwargs["metadata"] = metadata

            # Snapshot existing IDs so we can detect the new memory later.
            if self._is_cloud:
                existing_ids = {
                    f.id for f in await self.get_all(
                        user_id=user_id, agent_id=agent_id,
                    )
                }

            result = await self._client.add(**kwargs)
            entries = result.get("results", [])
            if not entries:
                raise ValueError(
                    "mem0 returned no results — the memory may already exist "
                    "(deduplicated)"
                )
            entry = entries[0]

            # Mem0 Cloud processes memories asynchronously — poll until
            # the new memory appears so we can return a real Fact.
            if self._is_cloud and entry.get("id") is None:
                return await self._poll_for_new_fact(
                    existing_ids=existing_ids,
                    user_id=user_id,
                    agent_id=agent_id,
                )

            return Fact(
                id=entry["id"],
                content=entry["memory"],
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata,
            )
        except Exception as e:
            raise ProviderError("mem0", "add", e) from e

    async def _poll_for_new_fact(
        self,
        *,
        existing_ids: set[str],
        user_id: str | None,
        agent_id: str | None,
    ) -> Fact:
        """Poll get_all until a memory with a new ID appears."""
        elapsed = 0.0
        while elapsed < _POLL_TIMEOUT:
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
            facts = await self.get_all(user_id=user_id, agent_id=agent_id)
            for fact in facts:
                if fact.id not in existing_ids:
                    return fact
        raise TimeoutError(
            f"Mem0 did not finish processing within {_POLL_TIMEOUT}s"
        )

    async def get(self, *, fact_id: str) -> Fact:
        try:
            result = await self._client.get(fact_id)
            if result is None:
                raise ValueError(f"fact {fact_id!r} not found")
            return self._to_fact(result)
        except Exception as e:
            raise ProviderError("mem0", "get", e) from e

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
            if self._is_cloud:
                kwargs["filters"] = self._build_filters(
                    user_id=user_id, agent_id=agent_id, extra=filters,
                )
            else:
                if user_id:
                    kwargs["user_id"] = user_id
                if agent_id:
                    kwargs["agent_id"] = agent_id
                if filters:
                    kwargs["filters"] = filters
            result = await self._client.search(**kwargs)
            return [self._to_fact(entry) for entry in result["results"]]
        except Exception as e:
            raise ProviderError("mem0", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            if self._is_cloud:
                await self._client.update(fact_id, text=content)
            else:
                await self._client.update(fact_id, data=content)
            return Fact(id=fact_id, content=content, metadata=metadata)
        except Exception as e:
            raise ProviderError("mem0", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        try:
            await self._client.delete(fact_id)
        except Exception as e:
            raise ProviderError("mem0", "delete", e) from e

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        try:
            kwargs: dict = {}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            await self._client.delete_all(**kwargs)
        except Exception as e:
            raise ProviderError("mem0", "delete_all", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        try:
            kwargs: dict = {"limit": limit}
            if self._is_cloud:
                kwargs["filters"] = self._build_filters(
                    user_id=user_id, agent_id=agent_id,
                )
            else:
                if user_id:
                    kwargs["user_id"] = user_id
                if agent_id:
                    kwargs["agent_id"] = agent_id
            result = await self._client.get_all(**kwargs)
            return [self._to_fact(entry) for entry in result["results"]]
        except Exception as e:
            raise ProviderError("mem0", "get_all", e) from e

    @staticmethod
    def _to_fact(entry: dict) -> Fact:
        created_at = None
        if entry.get("created_at"):
            try:
                created_at = datetime.fromisoformat(entry["created_at"])
            except (ValueError, TypeError):
                pass
        updated_at = None
        if entry.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(entry["updated_at"])
            except (ValueError, TypeError):
                pass
        return Fact(
            id=entry["id"],
            content=entry["memory"],
            user_id=entry.get("user_id"),
            agent_id=entry.get("agent_id"),
            metadata=entry.get("metadata"),
            score=entry.get("score"),
            created_at=created_at,
            updated_at=updated_at,
        )
