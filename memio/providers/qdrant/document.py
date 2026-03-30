"""Qdrant DocumentStore adapter.

Uses qdrant-client's fastembed integration for automatic embedding generation.
Supports in-memory, on-disk, and cloud deployments.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from memio.exceptions import ProviderError
from memio.models import Document


class QdrantDocumentAdapter:
    """DocumentStore implementation backed by Qdrant.

    Uses qdrant-client's fastembed integration for automatic embedding.
    Scores are returned directly from Qdrant's similarity search.

    Args:
        client: An AsyncQdrantClient instance.
        collection_name: Name of the Qdrant collection to use.
    """

    def __init__(self, *, client, collection_name: str):
        try:
            import qdrant_client  # noqa: F401
        except ImportError:
            raise ImportError(
                "qdrant provider requires qdrant-client: pip install memio[qdrant]"
            )
        self._client = client
        self._collection_name = collection_name

    async def add(self, *, content: str, doc_id: str | None = None,
                  metadata: dict | None = None) -> Document:
        try:
            doc_id = doc_id or str(uuid.uuid4())
            await self._client.add(
                collection_name=self._collection_name,
                documents=[content],
                ids=[doc_id],
                metadata=[metadata or {}],
            )
            return Document(id=doc_id, content=content, metadata=metadata,
                          created_at=datetime.now(timezone.utc))
        except Exception as e:
            raise ProviderError("qdrant", "add", e) from e

    async def get(self, *, doc_id: str) -> Document:
        try:
            records = await self._client.retrieve(
                collection_name=self._collection_name,
                ids=[doc_id],
                with_payload=True,
            )
            payload = records[0].payload
            content = payload["document"]
            metadata = {k: v for k, v in payload.items() if k != "document"} or None
            return Document(id=records[0].id, content=content, metadata=metadata)
        except Exception as e:
            raise ProviderError("qdrant", "get", e) from e

    async def search(self, *, query: str, limit: int = 10,
                     filters: dict | None = None) -> list[Document]:
        try:
            results = await self._client.query(
                collection_name=self._collection_name,
                query_text=query,
                limit=limit,
            )
            docs = []
            for result in results:
                content = result.document
                meta = {k: v for k, v in result.metadata.items()
                        if k != "document"} or None
                docs.append(Document(
                    id=result.id,
                    content=content,
                    metadata=meta,
                    score=result.score,
                ))
            return docs
        except Exception as e:
            raise ProviderError("qdrant", "search", e) from e

    async def get_all(self, *, limit: int = 100,
                      filters: dict | None = None) -> list[Document]:
        try:
            if not await self._client.collection_exists(self._collection_name):
                return []

            records, _ = await self._client.scroll(
                collection_name=self._collection_name,
                limit=limit,
                with_payload=True,
            )
            docs = []
            for record in records:
                payload = record.payload
                content = payload["document"]
                metadata = {k: v for k, v in payload.items() if k != "document"} or None
                docs.append(Document(
                    id=record.id,
                    content=content,
                    metadata=metadata,
                ))
            return docs
        except Exception as e:
            raise ProviderError("qdrant", "get_all", e) from e

    async def update(self, *, doc_id: str, content: str,
                     metadata: dict | None = None) -> Document:
        try:
            await self._client.add(
                collection_name=self._collection_name,
                documents=[content],
                ids=[doc_id],
                metadata=[metadata or {}],
            )
            return Document(id=doc_id, content=content, metadata=metadata,
                          updated_at=datetime.now(timezone.utc))
        except Exception as e:
            raise ProviderError("qdrant", "update", e) from e

    async def delete(self, *, doc_id: str) -> None:
        try:
            await self._client.delete(
                collection_name=self._collection_name,
                points_selector=[doc_id],
            )
        except Exception as e:
            raise ProviderError("qdrant", "delete", e) from e

    async def delete_all(self) -> None:
        try:
            from qdrant_client.http.models import Filter, FilterSelector

            # Collection may not exist yet (e.g. first call before any add).
            if not await self._client.collection_exists(self._collection_name):
                return

            await self._client.delete(
                collection_name=self._collection_name,
                points_selector=FilterSelector(filter=Filter()),
            )
        except Exception as e:
            raise ProviderError("qdrant", "delete_all", e) from e
