# tests/providers/test_zep_fact.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Fact
from memio.exceptions import ProviderError


def _mock_zep_edge(uuid_, fact, name, source_uuid, target_uuid, created_at=None):
    edge = MagicMock()
    edge.uuid_ = uuid_
    edge.fact = fact
    edge.name = name
    edge.source_node_uuid = source_uuid
    edge.target_node_uuid = target_uuid
    edge.created_at = created_at or "2026-01-01T00:00:00Z"
    edge.attributes = None
    edge.score = 0.9
    return edge


class TestZepFactAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {
            "zep_cloud": MagicMock(),
            "zep_cloud.types": MagicMock(),
        }):
            from memio.providers.zep.fact import ZepFactAdapter
            adapter = ZepFactAdapter.__new__(ZepFactAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_episode = MagicMock()
        mock_episode.uuid_ = "ep1"
        mock_episode.content = "likes coffee"
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.add = AsyncMock(return_value=mock_episode)
        mock_client.user = MagicMock()
        mock_client.user.add = AsyncMock()
        adapter = self._make_adapter(mock_client)

        fact = await adapter.add(content="likes coffee", user_id="u1")

        assert isinstance(fact, Fact)
        assert fact.id == "ep1"
        assert fact.content == "likes coffee"

    async def test_search(self):
        mock_results = MagicMock()
        mock_results.edges = [
            _mock_zep_edge("e1", "likes coffee", "LIKES", "n1", "n2"),
        ]
        mock_results.nodes = []
        mock_results.episodes = []
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        results = await adapter.search(query="coffee", user_id="u1")

        assert len(results) == 1
        assert results[0].content == "likes coffee"

    async def test_get(self):
        mock_edge = _mock_zep_edge("e1", "likes coffee", "LIKES", "n1", "n2")
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.edge.get = AsyncMock(return_value=mock_edge)
        adapter = self._make_adapter(mock_client)

        fact = await adapter.get(fact_id="e1")

        assert fact.id == "e1"
        assert fact.content == "likes coffee"

    async def test_update(self):
        mock_edge = _mock_zep_edge("e1", "likes tea", "LIKES", "n1", "n2")
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.edge.update = AsyncMock(return_value=mock_edge)
        adapter = self._make_adapter(mock_client)

        fact = await adapter.update(fact_id="e1", content="likes tea")

        assert fact.content == "likes tea"

    async def test_delete_raises_not_implemented(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.delete(fact_id="e1")
        assert isinstance(exc_info.value.cause, NotImplementedError)

    async def test_delete_all(self):
        mock_client = MagicMock()
        mock_client.user = MagicMock()
        mock_client.user.delete = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all(user_id="u1")

        mock_client.user.delete.assert_called_once_with("u1")

    async def test_get_all(self):
        mock_edges = [
            _mock_zep_edge("e1", "likes coffee", "LIKES", "n1", "n2"),
            _mock_zep_edge("e2", "prefers dark mode", "PREFERS", "n1", "n3"),
        ]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.edge.get_by_user_id = AsyncMock(return_value=mock_edges)
        adapter = self._make_adapter(mock_client)

        results = await adapter.get_all(user_id="u1")

        assert len(results) == 2

    async def test_provider_error_wrapping(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(side_effect=RuntimeError("fail"))
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "zep"
