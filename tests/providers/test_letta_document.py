import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Document
from memio.exceptions import ProviderError


class TestLettaDocumentAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"letta_client": MagicMock()}):
            from memio.providers.letta.document import LettaDocumentAdapter
            adapter = LettaDocumentAdapter.__new__(LettaDocumentAdapter)
            adapter._client = mock_client
            adapter._agent_id = "agent-1"
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "d1"
        mock_passage.text = "document content"
        mock_passage.metadata_ = None
        mock_passage.created_at = None
        mock_client.agents.passages.insert.return_value = mock_passage
        adapter = self._make_adapter(mock_client)

        doc = await adapter.add(content="document content")

        assert isinstance(doc, Document)
        assert doc.id == "d1"
        assert doc.content == "document content"

    async def test_get(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "d1"
        mock_passage.text = "document content"
        mock_passage.metadata_ = {"key": "val"}
        mock_passage.created_at = None
        mock_client.agents.passages.list.return_value = [mock_passage]
        adapter = self._make_adapter(mock_client)

        doc = await adapter.get(doc_id="d1")

        assert doc.id == "d1"
        assert doc.metadata == {"key": "val"}

    async def test_get_not_found(self):
        mock_client = AsyncMock()
        mock_client.agents.passages.list.return_value = []
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.get(doc_id="nonexistent")
        assert exc_info.value.provider == "letta"

    async def test_search(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "d1"
        mock_passage.text = "coffee guide"
        mock_passage.metadata_ = None
        mock_passage.created_at = None
        mock_passage.score = 0.9
        mock_client.agents.passages.search.return_value = [mock_passage]
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee")

        assert len(results) == 1
        assert results[0].id == "d1"

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_p1 = MagicMock()
        mock_p1.id = "d1"
        mock_p1.text = "doc one"
        mock_p1.metadata_ = None
        mock_p1.created_at = None
        mock_p2 = MagicMock()
        mock_p2.id = "d2"
        mock_p2.text = "doc two"
        mock_p2.metadata_ = None
        mock_p2.created_at = None
        mock_client.agents.passages.list.return_value = [mock_p1, mock_p2]
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all()

        assert len(results) == 2

    async def test_update(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "d1"
        mock_passage.text = "updated content"
        mock_passage.metadata_ = None
        mock_passage.created_at = None
        mock_client.agents.passages.update.return_value = mock_passage
        adapter = self._make_adapter(mock_client)

        doc = await adapter.update(doc_id="d1", content="updated content")

        assert doc.content == "updated content"

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete(doc_id="d1")

        mock_client.agents.passages.delete.assert_called_once()

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_p1 = MagicMock()
        mock_p1.id = "d1"
        mock_p2 = MagicMock()
        mock_p2.id = "d2"
        mock_client.agents.passages.list.return_value = [mock_p1, mock_p2]
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all()

        assert mock_client.agents.passages.delete.call_count == 2

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.agents.passages.search.side_effect = RuntimeError("api error")
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test")
        assert exc_info.value.provider == "letta"
