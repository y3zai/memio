# tests/providers/test_zep_graph.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import GraphResult, Triple
from memio.exceptions import ProviderError


def _mock_zep_node(name, uuid_="n1", summary=""):
    node = MagicMock()
    node.name = name
    node.uuid_ = uuid_
    node.summary = summary
    return node


def _mock_zep_edge(fact, name, source_uuid, target_uuid, uuid_="e1"):
    edge = MagicMock()
    edge.uuid_ = uuid_
    edge.fact = fact
    edge.name = name
    edge.source_node_uuid = source_uuid
    edge.target_node_uuid = target_uuid
    return edge


class TestZepGraphAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {
            "zep_cloud": MagicMock(),
        }):
            from memio.providers.zep.graph import ZepGraphAdapter
            adapter = ZepGraphAdapter.__new__(ZepGraphAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.add_fact_triple = AsyncMock()
        adapter = self._make_adapter(mock_client)

        triples = [Triple(subject="Alice", predicate="works_at", object="Acme")]
        await adapter.add(triples=triples, user_id="u1")

        mock_client.graph.add_fact_triple.assert_called_once()

    async def test_search(self):
        mock_results = MagicMock()
        mock_results.edges = [
            _mock_zep_edge("Alice works at Acme", "WORKS_AT", "n1", "n2"),
        ]
        mock_results.nodes = [
            _mock_zep_node("Alice", "n1"),
            _mock_zep_node("Acme", "n2"),
        ]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        result = await adapter.search(query="Alice", user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1

    async def test_get_all(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.node = MagicMock()
        mock_client.graph.edge = MagicMock()
        mock_client.graph.node.get_by_user_id = AsyncMock(return_value=[
            _mock_zep_node("Alice", "n1"),
            _mock_zep_node("Acme", "n2"),
        ])
        mock_client.graph.edge.get_by_user_id = AsyncMock(return_value=[
            _mock_zep_edge("Alice works at Acme", "WORKS_AT", "n1", "n2"),
        ])
        adapter = self._make_adapter(mock_client)

        result = await adapter.get_all(user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1
        assert len(result.nodes) >= 1

    async def test_delete_all(self):
        mock_client = MagicMock()
        mock_client.user = MagicMock()
        mock_client.user.delete = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete_all(user_id="u1")

        mock_client.user.delete.assert_called_once_with("u1")

    async def test_provider_error_wrapping(self):
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(side_effect=RuntimeError("fail"))
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "zep"
