import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Document
from memio.exceptions import ProviderError


class TestQdrantDocumentAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"qdrant_client": MagicMock()}):
            from memio.providers.qdrant.document import QdrantDocumentAdapter
            adapter = QdrantDocumentAdapter(client=mock_client, collection_name="test")
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        doc = await adapter.add(content="hello world", metadata={"k": "v"})
        assert isinstance(doc, Document)
        assert doc.content == "hello world"
        assert doc.id is not None
        assert doc.metadata == {"k": "v"}
        mock_client.add.assert_called_once()

    async def test_add_with_explicit_id(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        doc = await adapter.add(content="hello", doc_id="custom-id")
        assert doc.id == "custom-id"

    async def test_get(self):
        mock_client = AsyncMock()
        mock_record = MagicMock()
        mock_record.id = "d1"
        mock_record.payload = {"document": "hello world", "k": "v"}
        mock_client.retrieve.return_value = [mock_record]
        adapter = self._make_adapter(mock_client)
        doc = await adapter.get(doc_id="d1")
        assert doc.id == "d1"
        assert doc.content == "hello world"
        assert doc.metadata == {"k": "v"}

    async def test_search(self):
        mock_client = AsyncMock()
        result1 = MagicMock()
        result1.id = "d1"
        result1.score = 0.95
        result1.document = "doc one"
        result1.metadata = {"document": "doc one", "k": "1"}
        result2 = MagicMock()
        result2.id = "d2"
        result2.score = 0.80
        result2.document = "doc two"
        result2.metadata = {"document": "doc two", "k": "2"}
        mock_client.query.return_value = [result1, result2]
        adapter = self._make_adapter(mock_client)
        results = await adapter.search(query="test", limit=2)
        assert len(results) == 2
        assert results[0].id == "d1"
        assert results[0].content == "doc one"
        assert results[0].score == 0.95
        assert results[1].id == "d2"
        assert results[1].score == 0.80

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_client.collection_exists.return_value = True
        rec1 = MagicMock()
        rec1.id = "d1"
        rec1.payload = {"document": "doc one", "k": "1"}
        rec2 = MagicMock()
        rec2.id = "d2"
        rec2.payload = {"document": "doc two", "k": "2"}
        mock_client.scroll.return_value = ([rec1, rec2], None)
        adapter = self._make_adapter(mock_client)
        results = await adapter.get_all(limit=10)
        assert len(results) == 2
        assert results[0].id == "d1"
        assert results[1].content == "doc two"

    async def test_update(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        doc = await adapter.update(doc_id="d1", content="updated")
        assert doc.id == "d1"
        assert doc.content == "updated"
        mock_client.add.assert_called_once()

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        await adapter.delete(doc_id="d1")
        mock_client.delete.assert_called_once_with(
            collection_name="test", points_selector=["d1"]
        )

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_client.collection_exists.return_value = True
        adapter = self._make_adapter(mock_client)
        with patch.dict("sys.modules", {
            "qdrant_client": MagicMock(),
            "qdrant_client.http": MagicMock(),
            "qdrant_client.http.models": MagicMock(),
        }):
            await adapter.delete_all()
        mock_client.delete.assert_called_once()

    async def test_delete_all_empty(self):
        mock_client = AsyncMock()
        mock_client.collection_exists.return_value = False
        adapter = self._make_adapter(mock_client)
        with patch.dict("sys.modules", {
            "qdrant_client": MagicMock(),
            "qdrant_client.http": MagicMock(),
            "qdrant_client.http.models": MagicMock(),
        }):
            await adapter.delete_all()
        # Collection doesn't exist, so delete should not be called
        mock_client.delete.assert_not_called()

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.query.side_effect = RuntimeError("connection lost")
        adapter = self._make_adapter(mock_client)
        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test")
        assert exc_info.value.provider == "qdrant"
        assert exc_info.value.operation == "search"
        assert isinstance(exc_info.value.cause, RuntimeError)
