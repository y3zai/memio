from __future__ import annotations

import uuid
from datetime import datetime, timezone

from memio.exceptions import ProviderError
from memio.models import Document


class ChromaDocumentAdapter:
    def __init__(self, *, client, collection_name: str):
        try:
            import chromadb  # noqa: F401
        except ImportError:
            raise ImportError(
                "chroma provider requires chromadb: pip install memio[chroma]"
            )
        self._collection = client.get_or_create_collection(name=collection_name)

    async def add(self, *, content: str, doc_id: str | None = None,
                  metadata: dict | None = None) -> Document:
        try:
            doc_id = doc_id or str(uuid.uuid4())
            kwargs: dict = {"ids": [doc_id], "documents": [content]}
            if metadata is not None:
                kwargs["metadatas"] = [metadata]
            self._collection.add(**kwargs)
            return Document(id=doc_id, content=content, metadata=metadata,
                          created_at=datetime.now(timezone.utc))
        except Exception as e:
            raise ProviderError("chroma", "add", e) from e

    async def get(self, *, doc_id: str) -> Document:
        try:
            result = self._collection.get(ids=[doc_id])
            return Document(
                id=result["ids"][0],
                content=result["documents"][0],
                metadata=result["metadatas"][0] if result["metadatas"] else None,
            )
        except Exception as e:
            raise ProviderError("chroma", "get", e) from e

    async def search(self, *, query: str, limit: int = 10,
                     filters: dict | None = None) -> list[Document]:
        try:
            kwargs: dict = {"query_texts": [query], "n_results": limit}
            if filters is not None:
                kwargs["where"] = filters
            result = self._collection.query(**kwargs)
            docs = []
            for i, doc_id in enumerate(result["ids"][0]):
                distance = result["distances"][0][i] if result.get("distances") else None
                score = 1.0 / (1.0 + distance) if distance is not None else None
                docs.append(Document(
                    id=doc_id,
                    content=result["documents"][0][i],
                    metadata=result["metadatas"][0][i] if result.get("metadatas") else None,
                    score=score,
                ))
            return docs
        except Exception as e:
            raise ProviderError("chroma", "search", e) from e

    async def update(self, *, doc_id: str, content: str,
                     metadata: dict | None = None) -> Document:
        try:
            kwargs: dict = {"ids": [doc_id], "documents": [content]}
            if metadata is not None:
                kwargs["metadatas"] = [metadata]
            self._collection.update(**kwargs)
            return Document(id=doc_id, content=content, metadata=metadata,
                          updated_at=datetime.now(timezone.utc))
        except Exception as e:
            raise ProviderError("chroma", "update", e) from e

    async def delete(self, *, doc_id: str) -> None:
        try:
            self._collection.delete(ids=[doc_id])
        except Exception as e:
            raise ProviderError("chroma", "delete", e) from e

    async def get_all(self, *, limit: int = 100,
                      filters: dict | None = None) -> list[Document]:
        try:
            kwargs: dict = {"limit": limit}
            if filters is not None:
                kwargs["where"] = filters
            result = self._collection.get(**kwargs)
            docs = []
            for i, doc_id in enumerate(result["ids"]):
                docs.append(Document(
                    id=doc_id,
                    content=result["documents"][i],
                    metadata=result["metadatas"][i] if result.get("metadatas") else None,
                ))
            return docs
        except Exception as e:
            raise ProviderError("chroma", "get_all", e) from e

    async def delete_all(self) -> None:
        try:
            result = self._collection.get()
            if result["ids"]:
                self._collection.delete(ids=result["ids"])
        except Exception as e:
            raise ProviderError("chroma", "delete_all", e) from e
