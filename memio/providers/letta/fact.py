"""Letta FactStore adapter.

Maps memio facts to Letta archival passages (agent-scoped).
Passages are vector-embedded text chunks stored in the agent's archival memory.

Known quirks:
- Letta passages API has no update method; update is emulated via delete + create.
- Search results use a different shape than list results (content vs text).
- The delete method takes memory_id as a positional arg.
"""

from __future__ import annotations

from datetime import datetime

from memio.exceptions import NotSupportedError, ProviderError
from memio.models import Fact


class LettaFactAdapter:
    """FactStore implementation backed by Letta archival passages.

    Args:
        agent_id: The Letta agent whose archival memory stores facts.
        api_key: Letta Cloud API key. Mutually exclusive with base_url.
        base_url: URL of a self-hosted Letta server.
    """

    def __init__(
        self,
        *,
        agent_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        try:
            from letta_client import AsyncLetta
        except ImportError:
            raise ImportError(
                "letta provider requires letta-client: pip install memio[letta]"
            )
        kwargs: dict = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncLetta(**kwargs)
        self._agent_id = agent_id

    async def add(
        self,
        *,
        content: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            passages = await self._client.agents.passages.create(
                self._agent_id,
                text=content,
            )
            passage = passages[0]
            return self._to_fact(passage, user_id=user_id, agent_id=agent_id)
        except Exception as e:
            raise ProviderError("letta", "add", e) from e

    async def get(self, *, fact_id: str) -> Fact:
        try:
            passages = await self._client.agents.passages.list(
                self._agent_id,
            )
            for p in passages:
                if p.id == fact_id:
                    return self._to_fact(p)
            raise ValueError(f"fact {fact_id!r} not found")
        except Exception as e:
            raise ProviderError("letta", "get", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        if user_id is not None or agent_id is not None:
            raise NotSupportedError(
                "letta", "get_all",
                hint="Letta passages are agent-scoped at the adapter level; "
                     "user_id/agent_id filtering is not supported. "
                     "Omit both to list all passages.",
            )
        try:
            passages = await self._client.agents.passages.list(
                self._agent_id,
                limit=limit,
            )
            return [self._to_fact(p) for p in passages]
        except Exception as e:
            raise ProviderError("letta", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Fact]:
        if user_id is not None or agent_id is not None:
            raise NotSupportedError(
                "letta", "search",
                hint="Letta passages are agent-scoped at the adapter level; "
                     "user_id/agent_id filtering is not supported. "
                     "Omit both to search all passages.",
            )
        try:
            response = await self._client.agents.passages.search(
                self._agent_id,
                query=query,
                top_k=limit,
            )
            return [self._search_result_to_fact(r) for r in response.results]
        except Exception as e:
            raise ProviderError("letta", "search", e) from e

    async def update(
        self,
        *,
        fact_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Fact:
        try:
            await self._client.agents.passages.delete(
                fact_id, agent_id=self._agent_id,
            )
            passages = await self._client.agents.passages.create(
                self._agent_id,
                text=content,
            )
            return self._to_fact(passages[0])
        except Exception as e:
            raise ProviderError("letta", "update", e) from e

    async def delete(self, *, fact_id: str) -> None:
        try:
            await self._client.agents.passages.delete(
                fact_id, agent_id=self._agent_id,
            )
        except Exception as e:
            raise ProviderError("letta", "delete", e) from e

    async def delete_all(
        self,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        if user_id is not None or agent_id is not None:
            raise NotSupportedError(
                "letta", "delete_all",
                hint="Letta passages are agent-scoped at the adapter level; "
                     "user_id/agent_id filtering is not supported. "
                     "Omit both to delete all passages for this agent.",
            )
        try:
            passages = await self._client.agents.passages.list(
                self._agent_id,
            )
            for p in passages:
                await self._client.agents.passages.delete(
                    p.id, agent_id=self._agent_id,
                )
        except Exception as e:
            raise ProviderError("letta", "delete_all", e) from e

    @staticmethod
    def _to_fact(
        passage, *, user_id: str | None = None, agent_id: str | None = None
    ) -> Fact:
        created_at = None
        if hasattr(passage, "created_at") and passage.created_at:
            try:
                ts = passage.created_at
                created_at = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts))
            except (ValueError, TypeError):
                pass
        return Fact(
            id=passage.id,
            content=passage.text,
            user_id=user_id,
            agent_id=agent_id,
            metadata=getattr(passage, "metadata", None),
            created_at=created_at,
        )

    @staticmethod
    def _search_result_to_fact(result) -> Fact:
        return Fact(
            id=result.id,
            content=result.content,
        )
