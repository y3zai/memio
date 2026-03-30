# tests/providers/test_mem0_fact.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Fact
from memio.exceptions import ProviderError


def _mock_mem0_module():
    """Create a mock mem0 module for import patching."""
    mock_module = MagicMock()
    mock_async_memory = MagicMock()
    mock_module.AsyncMemory = mock_async_memory
    return mock_module, mock_async_memory


class TestMem0FactAdapter:
    def _make_adapter(self, mock_client, *, is_cloud=False):
        with patch.dict("sys.modules", {"mem0": MagicMock()}):
            from memio.providers.mem0.fact import Mem0FactAdapter
            adapter = Mem0FactAdapter.__new__(Mem0FactAdapter)
            adapter._client = mock_client
            adapter._is_cloud = is_cloud
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_client.add.return_value = {
            "results": [{"id": "m1", "memory": "likes coffee", "event": "ADD"}]
        }
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(content="likes coffee", user_id="u1")

        assert isinstance(fact, Fact)
        assert fact.id == "m1"
        assert fact.content == "likes coffee"
        mock_client.add.assert_called_once()

    async def test_get(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "m1",
            "memory": "likes coffee",
            "user_id": "u1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "metadata": None,
        }
        adapter = self._make_adapter(mock_client)

        fact = await adapter.get(fact_id="m1")

        assert fact.id == "m1"
        assert fact.content == "likes coffee"

    async def test_search(self):
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "results": [
                {"id": "m1", "memory": "likes coffee", "score": 0.95},
                {"id": "m2", "memory": "prefers dark mode", "score": 0.80},
            ]
        }
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee", user_id="u1")

        assert len(results) == 2
        assert results[0].score == 0.95

    async def test_update(self):
        mock_client = AsyncMock()
        mock_client.update.return_value = {"message": "Memory updated successfully!"}
        adapter = self._make_adapter(mock_client)

        fact = await adapter.update(fact_id="m1", content="likes tea")

        assert fact.id == "m1"
        assert fact.content == "likes tea"

    async def test_delete(self):
        mock_client = AsyncMock()
        mock_client.delete.return_value = {"message": "Memory deleted successfully!"}
        adapter = self._make_adapter(mock_client)

        await adapter.delete(fact_id="m1")

        mock_client.delete.assert_called_once_with("m1")

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_client.delete_all.return_value = {"message": "Memories deleted successfully!"}
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all(user_id="u1")

        mock_client.delete_all.assert_called_once_with(user_id="u1")

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_client.get_all.return_value = {
            "results": [
                {"id": "m1", "memory": "likes coffee"},
                {"id": "m2", "memory": "prefers dark mode"},
            ]
        }
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all(user_id="u1")

        assert len(results) == 2

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.search.side_effect = RuntimeError("api error")
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "mem0"
