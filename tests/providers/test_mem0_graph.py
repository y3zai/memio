# tests/providers/test_mem0_graph.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import GraphResult, Triple
from memio.exceptions import NotSupportedError, ProviderError


class TestMem0GraphAdapter:
    def _make_adapter(self, mock_client, mock_graph):
        with patch.dict("sys.modules", {"mem0": MagicMock()}):
            from memio.providers.mem0.graph import Mem0GraphAdapter
            adapter = Mem0GraphAdapter.__new__(Mem0GraphAdapter)
            adapter._client = mock_client
            adapter._graph = mock_graph
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.add.return_value = {"added_entities": ["Alice", "Acme"]}
        adapter = self._make_adapter(mock_client, mock_graph)

        triples = [Triple(subject="Alice", predicate="works_at", object="Acme")]
        await adapter.add(triples=triples, user_id="u1")

        mock_graph.add.assert_called_once()

    async def test_search(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.search.return_value = [
            {"source": "Alice", "relationship": "works_at", "destination": "Acme"},
        ]
        adapter = self._make_adapter(mock_client, mock_graph)

        result = await adapter.search(query="Alice", user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1
        assert result.triples[0].subject == "Alice"
        assert result.triples[0].predicate == "works_at"
        assert result.triples[0].object == "Acme"

    async def test_get(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.get_all.return_value = [
            {"source": "Alice", "relationship": "works_at", "destination": "Acme"},
            {"source": "Bob", "relationship": "knows", "destination": "Alice"},
        ]
        adapter = self._make_adapter(mock_client, mock_graph)

        result = await adapter.get(entity="Alice", user_id="u1")

        assert isinstance(result, GraphResult)
        # Should filter to triples involving "Alice"
        for t in result.triples:
            assert "Alice" in (t.subject, t.object)

    async def test_get_all(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.get_all.return_value = [
            {"source": "Alice", "relationship": "works_at", "destination": "Acme"},
        ]
        adapter = self._make_adapter(mock_client, mock_graph)

        result = await adapter.get_all(user_id="u1")

        assert isinstance(result, GraphResult)
        assert len(result.triples) == 1

    async def test_delete_raises_not_supported(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        adapter = self._make_adapter(mock_client, mock_graph)

        with pytest.raises(NotSupportedError) as exc_info:
            await adapter.delete(entity="Alice")
        assert exc_info.value.provider == "mem0"
        assert exc_info.value.operation == "delete"

    async def test_delete_all(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        adapter = self._make_adapter(mock_client, mock_graph)

        await adapter.delete_all(user_id="u1")

        mock_graph.delete_all.assert_called_once()

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.search.side_effect = RuntimeError("graph error")
        adapter = self._make_adapter(mock_client, mock_graph)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.search(query="test", user_id="u1")
        assert exc_info.value.provider == "mem0"
