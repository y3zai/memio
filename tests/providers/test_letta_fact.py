import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Fact
from memio.exceptions import NotFoundError, NotSupportedError, ProviderError


class TestLettaFactAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"letta_client": MagicMock()}):
            from memio.providers.letta.fact import LettaFactAdapter
            adapter = LettaFactAdapter.__new__(LettaFactAdapter)
            adapter._client = mock_client
            adapter._agent_id = "agent-1"
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "p1"
        mock_passage.text = "likes coffee"
        mock_passage.metadata = {"source": "test"}
        mock_passage.created_at = None
        mock_client.agents.passages.create.return_value = [mock_passage]
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(content="likes coffee", user_id="u1")

        assert isinstance(fact, Fact)
        assert fact.id == "p1"
        assert fact.content == "likes coffee"
        mock_client.agents.passages.create.assert_called_once()

    async def test_get(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "p1"
        mock_passage.text = "likes coffee"
        mock_passage.metadata = None
        mock_passage.created_at = None
        mock_client.agents.passages.list.return_value = [mock_passage]
        adapter = self._make_adapter(mock_client)

        fact = await adapter.get(fact_id="p1")

        assert fact.id == "p1"
        assert fact.content == "likes coffee"

    async def test_get_not_found(self):
        mock_client = AsyncMock()
        mock_client.agents.passages.list.return_value = []
        adapter = self._make_adapter(mock_client)

        with pytest.raises(NotFoundError) as exc_info:
            await adapter.get(fact_id="nonexistent")
        assert exc_info.value.resource == "fact"
        assert exc_info.value.resource_id == "nonexistent"

    async def test_search(self):
        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.id = "p1"
        mock_result.content = "likes coffee"
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_client.agents.passages.search.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee")

        assert len(results) == 1
        assert results[0].id == "p1"
        assert results[0].content == "likes coffee"

    async def test_search_with_user_id_raises(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(NotSupportedError) as exc_info:
            await adapter.search(query="coffee", user_id="u1")
        assert exc_info.value.provider == "letta"
        assert exc_info.value.operation == "search"

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_p1 = MagicMock()
        mock_p1.id = "p1"
        mock_p1.text = "fact one"
        mock_p1.metadata = None
        mock_p1.created_at = None
        mock_p2 = MagicMock()
        mock_p2.id = "p2"
        mock_p2.text = "fact two"
        mock_p2.metadata = None
        mock_p2.created_at = None
        mock_client.agents.passages.list.return_value = [mock_p1, mock_p2]
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all()

        assert len(results) == 2

    async def test_get_all_with_user_id_raises(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(NotSupportedError) as exc_info:
            await adapter.get_all(user_id="u1")
        assert exc_info.value.provider == "letta"
        assert exc_info.value.operation == "get_all"

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete(fact_id="p1")

        mock_client.agents.passages.delete.assert_called_once_with(
            "p1", agent_id="agent-1",
        )

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_p1 = MagicMock()
        mock_p1.id = "p1"
        mock_p2 = MagicMock()
        mock_p2.id = "p2"
        mock_client.agents.passages.list.return_value = [mock_p1, mock_p2]
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all()

        assert mock_client.agents.passages.delete.call_count == 2

    async def test_delete_all_with_user_id_raises(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(NotSupportedError) as exc_info:
            await adapter.delete_all(user_id="u1")
        assert exc_info.value.provider == "letta"
        assert exc_info.value.operation == "delete_all"

    async def test_update_emulates_via_delete_and_create(self):
        mock_client = AsyncMock()
        mock_passage = MagicMock()
        mock_passage.id = "p2"
        mock_passage.text = "likes tea"
        mock_passage.metadata = None
        mock_passage.created_at = None
        mock_client.agents.passages.create.return_value = [mock_passage]
        adapter = self._make_adapter(mock_client)

        fact = await adapter.update(fact_id="p1", content="likes tea")

        assert fact.content == "likes tea"
        mock_client.agents.passages.delete.assert_called_once_with(
            "p1", agent_id="agent-1",
        )
        mock_client.agents.passages.create.assert_called_once()

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.agents.passages.search.side_effect = RuntimeError("api error")
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "letta"
