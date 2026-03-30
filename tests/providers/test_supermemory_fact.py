import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Fact
from memio.exceptions import NotSupportedError, ProviderError


def _make_mock_result(id, memory, similarity=0.9, updated_at=None, metadata=None):
    """Create a mock search result matching supermemory's Result model."""
    result = MagicMock()
    result.id = id
    result.memory = memory
    result.similarity = similarity
    result.updated_at = updated_at or "2026-01-01T00:00:00Z"
    result.metadata = metadata
    return result


class TestSupermemoryFactAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"supermemory": MagicMock()}):
            from memio.providers.supermemory.fact import SupermemoryFactAdapter
            adapter = SupermemoryFactAdapter.__new__(SupermemoryFactAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_add_response = MagicMock()
        mock_add_response.id = "sm-1"
        mock_add_response.status = "queued"
        mock_client.add.return_value = mock_add_response
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(content="likes coffee", user_id="u1")

        assert isinstance(fact, Fact)
        assert fact.id == "sm-1"
        assert fact.content == "likes coffee"
        assert fact.user_id == "u1"
        mock_client.add.assert_called_once_with(
            content="likes coffee", container_tag="u1",
        )

    async def test_add_with_agent_id(self):
        mock_client = AsyncMock()
        mock_add_response = MagicMock()
        mock_add_response.id = "sm-2"
        mock_client.add.return_value = mock_add_response
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(
            content="prefers dark mode", user_id="u1", agent_id="a1",
        )

        assert fact.agent_id == "a1"
        mock_client.add.assert_called_once_with(
            content="prefers dark mode", container_tag="u1--a1",
        )

    async def test_add_with_metadata(self):
        mock_client = AsyncMock()
        mock_add_response = MagicMock()
        mock_add_response.id = "sm-3"
        mock_client.add.return_value = mock_add_response
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(
            content="test", user_id="u1", metadata={"source": "chat"},
        )

        assert fact.metadata == {"source": "chat"}
        mock_client.add.assert_called_once_with(
            content="test", container_tag="u1", metadata={"source": "chat"},
        )

    async def test_get_raises_not_supported(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(NotSupportedError) as exc_info:
            await adapter.get(fact_id="sm-1")
        assert exc_info.value.provider == "supermemory"
        assert exc_info.value.operation == "get"

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = [
            _make_mock_result("sm-1", "likes coffee"),
            _make_mock_result("sm-2", "prefers dark mode"),
        ]
        mock_client.search.memories.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all(user_id="u1")

        assert len(results) == 2
        assert results[0].id == "sm-1"
        assert results[0].content == "likes coffee"
        mock_client.search.memories.assert_called_once_with(
            q="", limit=100, search_mode="memories", container_tag="u1",
        )

    async def test_search(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = [
            _make_mock_result("sm-1", "likes coffee", similarity=0.95),
            _make_mock_result("sm-2", "drinks espresso", similarity=0.80),
        ]
        mock_client.search.memories.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee", user_id="u1")

        assert len(results) == 2
        assert results[0].score == 0.95
        assert results[1].content == "drinks espresso"
        mock_client.search.memories.assert_called_once_with(
            q="coffee", limit=10, search_mode="memories", container_tag="u1",
        )

    async def test_search_with_filters(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = []
        mock_client.search.memories.return_value = mock_response
        adapter = self._make_adapter(mock_client)

        await adapter.search(
            query="test", user_id="u1", filters={"source": "chat"},
        )

        mock_client.search.memories.assert_called_once_with(
            q="test", limit=10, search_mode="memories",
            container_tag="u1", filters={"source": "chat"},
        )

    async def test_update(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        fact = await adapter.update(fact_id="sm-1", content="likes tea")

        assert fact.id == "sm-1"
        assert fact.content == "likes tea"
        mock_client.memories.update_memory.assert_called_once_with(
            id="sm-1", new_content="likes tea", container_tag="",
        )

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete(fact_id="sm-1")

        mock_client.memories.forget.assert_called_once_with(
            container_tag="", id="sm-1",
        )

    async def test_delete_all_raises_not_supported(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(NotSupportedError) as exc_info:
            await adapter.delete_all(user_id="u1")
        assert exc_info.value.provider == "supermemory"
        assert exc_info.value.operation == "delete_all"

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.search.memories.side_effect = RuntimeError("api error")
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "supermemory"
        assert exc_info.value.operation == "search"
        assert isinstance(exc_info.value.cause, RuntimeError)
