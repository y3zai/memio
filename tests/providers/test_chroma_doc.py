import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Document
from memio.exceptions import ProviderError


class TestChromaDocumentAdapter:
    def _make_adapter(self, mock_collection):
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            from memio.providers.chroma.document import ChromaDocumentAdapter
            adapter = ChromaDocumentAdapter(client=mock_client, collection_name="test")
        return adapter

    async def test_add(self):
        mock_col = MagicMock()
        mock_col.add = MagicMock()
        adapter = self._make_adapter(mock_col)
        doc = await adapter.add(content="hello world", metadata={"k": "v"})
        assert isinstance(doc, Document)
        assert doc.content == "hello world"
        assert doc.id is not None
        mock_col.add.assert_called_once()

    async def test_add_with_explicit_id(self):
        mock_col = MagicMock()
        mock_col.add = MagicMock()
        adapter = self._make_adapter(mock_col)
        doc = await adapter.add(content="hello", doc_id="custom-id")
        assert doc.id == "custom-id"

    async def test_get(self):
        mock_col = MagicMock()
        mock_col.get.return_value = {
            "ids": ["d1"],
            "documents": ["hello world"],
            "metadatas": [{"k": "v"}],
        }
        adapter = self._make_adapter(mock_col)
        doc = await adapter.get(doc_id="d1")
        assert doc.id == "d1"
        assert doc.content == "hello world"
        assert doc.metadata == {"k": "v"}

    async def test_search(self):
        mock_col = MagicMock()
        mock_col.query.return_value = {
            "ids": [["d1", "d2"]],
            "documents": [["doc one", "doc two"]],
            "metadatas": [[{"k": "1"}, {"k": "2"}]],
            "distances": [[0.1, 0.5]],
        }
        adapter = self._make_adapter(mock_col)
        results = await adapter.search(query="test", limit=2)
        assert len(results) == 2
        assert results[0].id == "d1"
        assert results[0].content == "doc one"
        assert results[0].score is not None

    async def test_update(self):
        mock_col = MagicMock()
        mock_col.update = MagicMock()
        adapter = self._make_adapter(mock_col)
        doc = await adapter.update(doc_id="d1", content="updated")
        assert doc.id == "d1"
        assert doc.content == "updated"
        mock_col.update.assert_called_once()

    async def test_delete(self):
        mock_col = MagicMock()
        mock_col.delete = MagicMock()
        adapter = self._make_adapter(mock_col)
        await adapter.delete(doc_id="d1")
        mock_col.delete.assert_called_once_with(ids=["d1"])

    async def test_get_all(self):
        mock_col = MagicMock()
        mock_col.get.return_value = {
            "ids": ["d1", "d2"],
            "documents": ["doc one", "doc two"],
            "metadatas": [{"k": "1"}, {"k": "2"}],
        }
        adapter = self._make_adapter(mock_col)
        results = await adapter.get_all(limit=10)
        assert len(results) == 2
        assert results[0].id == "d1"
        assert results[1].content == "doc two"

    async def test_delete_all(self):
        mock_col = MagicMock()
        mock_col.get.return_value = {"ids": ["d1", "d2"]}
        mock_col.delete = MagicMock()
        adapter = self._make_adapter(mock_col)
        await adapter.delete_all()
        mock_col.delete.assert_called_once_with(ids=["d1", "d2"])

    async def test_delete_all_empty(self):
        mock_col = MagicMock()
        mock_col.get.return_value = {"ids": []}
        mock_col.delete = MagicMock()
        adapter = self._make_adapter(mock_col)
        await adapter.delete_all()
        mock_col.delete.assert_not_called()

    async def test_provider_error_wrapping(self):
        mock_col = MagicMock()
        mock_col.query.side_effect = RuntimeError("connection lost")
        adapter = self._make_adapter(mock_col)
        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test")
        assert exc_info.value.provider == "chroma"
        assert exc_info.value.operation == "search"
        assert isinstance(exc_info.value.cause, RuntimeError)
