"""Supermemory DocumentStore adapter.

Supermemory's document API maps nearly 1:1 to the DocumentStore protocol.
Documents are processed asynchronously — after add(), the document may
still be in a processing state (queued/extracting/chunking/embedding).
"""

from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Document


class SupermemoryDocumentAdapter:
    """DocumentStore implementation backed by Supermemory.

    Args:
        api_key: Supermemory API key. If not provided, reads from
            ``SUPERMEMORY_API_KEY`` environment variable.
        container_tag: Optional default container tag to scope all
            document operations. Maps to a user, project, or other
            grouping identifier.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        container_tag: str | None = None,
    ):
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
        self._container_tag = container_tag

    async def add(
        self,
        *,
        content: str,
        doc_id: str | None = None,
        metadata: dict | None = None,
    ) -> Document:
        try:
            kwargs: dict = {"content": content}
            if doc_id:
                kwargs["custom_id"] = doc_id
            if metadata:
                kwargs["metadata"] = metadata
            if self._container_tag:
                kwargs["container_tag"] = self._container_tag
            result = await self._client.documents.add(**kwargs)
            return Document(
                id=result.id,
                content=content,
                metadata=metadata,
            )
        except Exception as e:
            raise ProviderError("supermemory", "add", e) from e

    async def get(self, *, doc_id: str) -> Document:
        try:
            result = await self._client.documents.get(doc_id)
            metadata = None
            if isinstance(result.metadata, dict):
                metadata = result.metadata
            return Document(
                id=result.id,
                content=result.content or "",
                metadata=metadata,
                created_at=_parse_dt(result.created_at),
                updated_at=_parse_dt(result.updated_at),
            )
        except Exception as e:
            raise ProviderError("supermemory", "get", e) from e

    async def get_all(
        self,
        *,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list[Document]:
        try:
            kwargs: dict = {"limit": limit, "include_content": True}
            if filters:
                kwargs["filters"] = filters
            if self._container_tag:
                kwargs["container_tags"] = [self._container_tag]
            result = await self._client.documents.list(**kwargs)
            return [self._to_document(m) for m in result.memories]
        except Exception as e:
            raise ProviderError("supermemory", "get_all", e) from e

    async def search(
        self,
        *,
        query: str,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[Document]:
        try:
            kwargs: dict = {"q": query, "limit": limit}
            if filters:
                kwargs["filters"] = filters
            if self._container_tag:
                kwargs["container_tags"] = [self._container_tag]
            result = await self._client.search.documents(**kwargs)
            docs = []
            for chunk in result.results:
                docs.append(Document(
                    id=chunk.document_id,
                    content=chunk.content,
                    score=chunk.score,
                ))
            return docs
        except Exception as e:
            raise ProviderError("supermemory", "search", e) from e

    async def update(
        self,
        *,
        doc_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> Document:
        try:
            kwargs: dict = {"content": content}
            if metadata:
                kwargs["metadata"] = metadata
            if self._container_tag:
                kwargs["container_tag"] = self._container_tag
            await self._client.documents.update(doc_id, **kwargs)
            return Document(id=doc_id, content=content, metadata=metadata)
        except Exception as e:
            raise ProviderError("supermemory", "update", e) from e

    async def delete(self, *, doc_id: str) -> None:
        try:
            await self._client.documents.delete(doc_id)
        except Exception as e:
            raise ProviderError("supermemory", "delete", e) from e

    async def delete_all(self) -> None:
        try:
            kwargs: dict = {}
            if self._container_tag:
                kwargs["container_tags"] = [self._container_tag]
            result = await self._client.documents.list(**kwargs)
            ids = [m.id for m in result.memories]
            if ids:
                await self._client.documents.delete_bulk(ids=ids)
        except Exception as e:
            raise ProviderError("supermemory", "delete_all", e) from e

    @staticmethod
    def _to_document(entry) -> Document:
        metadata = None
        if isinstance(entry.metadata, dict):
            metadata = entry.metadata
        return Document(
            id=entry.id,
            content=entry.content or "",
            metadata=metadata,
            created_at=_parse_dt(getattr(entry, "created_at", None)),
            updated_at=_parse_dt(getattr(entry, "updated_at", None)),
        )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
