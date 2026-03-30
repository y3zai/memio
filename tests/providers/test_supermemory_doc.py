import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Document
from memio.exceptions import ProviderError


def _make_mock_list_entry(id, content=None, metadata=None, created_at=None, updated_at=None):
    """Create a mock entry matching supermemory's DocumentListResponse.Memory."""
    entry = MagicMock()
    entry.id = id
    entry.content = content
    entry.metadata = metadata
    entry.created_at = created_at or "2026-01-01T00:00:00Z"
    entry.updated_at = updated_at or "2026-01-01T00:00:00Z"
    return entry


def _make_mock_search_chunk(document_id, content, score=0.9):
    """Create a mock chunk matching supermemory's SearchDocumentsResponse result."""
    chunk = MagicMock()
    chunk.document_id = document_id
    chunk.content = content
    chunk.score = score
    return chunk


class TestSupermemoryDocumentAdapter:
    def _make_adapter(self, mock_client, container_tag=None):
        with patch.dict("sys.modules", {"supermemory": MagicMock()}):
            from memio.providers.supermemory.document import SupermemoryDocumentAdapter
            adapter = SupermemoryDocumentAdapter.__new__(SupermemoryDocumentAdapter)
            adapter._client = mock_client
            adapter._container_tag = container_tag
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.id = "doc-1"
        mock_response.status = "queued"
        mock_client.documents.add.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        doc = await adapter.add(content="hello world", metadata={"k": "v"})

        assert isinstance(doc, Document)
        assert doc.id == "doc-1"
        assert doc.content == "hello world"
        assert doc.metadata == {"k": "v"}
        mock_client.documents.add.assert_called_once_with(
            content="hello world", metadata={"k": "v"},
        )

    async def test_add_with_doc_id(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.id = "doc-1"
        mock_client.documents.add.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        doc = await adapter.add(content="hello", doc_id="custom-id")

        assert doc.id == "doc-1"
        mock_client.documents.add.assert_called_once_with(
            content="hello", custom_id="custom-id",
        )

    async def test_add_with_container_tag(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.id = "doc-1"
        mock_client.documents.add.return_value = mock_response
        adapter = self._make_adapter(mock_client, container_tag="project-1")

        await adapter.add(content="hello")

        mock_client.documents.add.assert_called_once_with(
            content="hello", container_tag="project-1",
        )

    async def test_get(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.id = "doc-1"
        mock_response.content = "hello world"
        mock_response.metadata = {"k": "v"}
        mock_response.created_at = "2026-01-01T00:00:00Z"
        mock_response.updated_at = "2026-01-02T00:00:00Z"
        mock_client.documents.get.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        doc = await adapter.get(doc_id="doc-1")

        assert doc.id == "doc-1"
        assert doc.content == "hello world"
        assert doc.metadata == {"k": "v"}
        assert doc.created_at is not None

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.memories = [
            _make_mock_list_entry("doc-1", content="doc one", metadata={"k": "1"}),
            _make_mock_list_entry("doc-2", content="doc two", metadata={"k": "2"}),
        ]
        mock_client.documents.list.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all(limit=10)

        assert len(results) == 2
        assert results[0].id == "doc-1"
        assert results[1].content == "doc two"

    async def test_get_all_with_container_tag(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.memories = []
        mock_client.documents.list.return_value = mock_response
        adapter = self._make_adapter(mock_client, container_tag="proj-1")

        await adapter.get_all()

        mock_client.documents.list.assert_called_once_with(
            limit=100, include_content=True, container_tags=["proj-1"],
        )

    async def test_search(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = [
            _make_mock_search_chunk("doc-1", "matching content", score=0.95),
            _make_mock_search_chunk("doc-2", "other content", score=0.80),
        ]
        mock_client.search.documents.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="test", limit=2)

        assert len(results) == 2
        assert results[0].id == "doc-1"
        assert results[0].content == "matching content"
        assert results[0].score == 0.95

    async def test_update(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        doc = await adapter.update(doc_id="doc-1", content="updated")

        assert doc.id == "doc-1"
        assert doc.content == "updated"
        mock_client.documents.update.assert_called_once_with(
            "doc-1", content="updated",
        )

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete(doc_id="doc-1")

        mock_client.documents.delete.assert_called_once_with("doc-1")

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.memories = [
            _make_mock_list_entry("doc-1"),
            _make_mock_list_entry("doc-2"),
        ]
        mock_client.documents.list.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all()

        mock_client.documents.delete_bulk.assert_called_once_with(
            ids=["doc-1", "doc-2"],
        )

    async def test_delete_all_empty(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.memories = []
        mock_client.documents.list.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all()

        mock_client.documents.delete_bulk.assert_not_called()

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.search.documents.side_effect = RuntimeError("connection lost")
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test")
        assert exc_info.value.provider == "supermemory"
        assert exc_info.value.operation == "search"
        assert isinstance(exc_info.value.cause, RuntimeError)
