"""Letta DocumentStore adapter.

Maps memio documents to Letta archival passages (agent-scoped).
Uses the same passages API as FactStore but oriented toward longer content.
"""

from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Document


class LettaDocumentAdapter:
    """DocumentStore implementation backed by Letta archival passages.

    Args:
        agent_id: The Letta agent whose archival memory stores documents.
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
        doc_id: str | None = None,
        metadata: dict | None = None,
    ) -> Document:
        try:
            passage = await self._client.agents.passages.insert(
                agent_id=self._agent_id,
                text=content,
            )
            return self._to_document(passage)
        except Exception as e:
            raise ProviderError("letta", "add", e) from e

    async def get(self, *, doc_id: str) -> Document:
        try:
            passages = await self._client.agents.passages.list(
                agent_id=self._agent_id,
            )
            for p in passages:
                if p.id == doc_id:
                    return self._to_document(p)
            raise ValueError(f"document {doc_id!r} not found")
        except Exception as e:
            raise ProviderError("letta", "get", e) from e

    async def get_all(
        self,
        *,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list[Document]:
        try:
            passages = await self._client.agents.passages.list(
                agent_id=self._agent_id,
            )
            return [self._to_document(p) for p in passages[:limit]]
        except Exception as e:
            raise ProviderError("letta", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Document]:
        try:
            passages = await self._client.agents.passages.search(
                agent_id=self._agent_id,
                query=query,
            )
            return [self._to_document(p) for p in passages[:limit]]
        except Exception as e:
            raise ProviderError("letta", "search", e) from e

    async def update(
        self,
        *,
        doc_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Document:
        try:
            passage = await self._client.agents.passages.update(
                agent_id=self._agent_id,
                passage_id=doc_id,
                text=content,
            )
            return self._to_document(passage)
        except Exception as e:
            raise ProviderError("letta", "update", e) from e

    async def delete(self, *, doc_id: str) -> None:
        try:
            await self._client.agents.passages.delete(
                agent_id=self._agent_id,
                passage_id=doc_id,
            )
        except Exception as e:
            raise ProviderError("letta", "delete", e) from e

    async def delete_all(self) -> None:
        try:
            passages = await self._client.agents.passages.list(
                agent_id=self._agent_id,
            )
            for p in passages:
                await self._client.agents.passages.delete(
                    agent_id=self._agent_id,
                    passage_id=p.id,
                )
        except Exception as e:
            raise ProviderError("letta", "delete_all", e) from e

    @staticmethod
    def _to_document(passage) -> Document:
        created_at = None
        if hasattr(passage, "created_at") and passage.created_at:
            try:
                ts = passage.created_at
                created_at = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts))
            except (ValueError, TypeError):
                pass
        return Document(
            id=passage.id,
            content=passage.text,
            metadata=getattr(passage, "metadata_", None),
            score=getattr(passage, "score", None),
            created_at=created_at,
        )
