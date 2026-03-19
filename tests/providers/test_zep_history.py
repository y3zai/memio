# tests/providers/test_zep_history.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Message
from memio.exceptions import ProviderError


def _mock_zep_message(role, content, created_at=None):
    msg = MagicMock()
    msg.role = role
    msg.role_type = role
    msg.content = content
    msg.created_at = created_at or "2026-01-01T00:00:00Z"
    msg.metadata = None
    msg.name = None
    return msg


class TestZepHistoryAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {
            "zep_cloud": MagicMock(),
            "zep_cloud.types": MagicMock(),
        }):
            from memio.providers.zep.history import ZepHistoryAdapter
            adapter = ZepHistoryAdapter.__new__(ZepHistoryAdapter)
            adapter._client = mock_client
        return adapter

    async def test_add(self):
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.create = AsyncMock()
        mock_client.thread.add_messages = AsyncMock()
        adapter = self._make_adapter(mock_client)

        messages = [
            Message(role="user", content="hello"),
            Message(role="assistant", content="hi"),
        ]
        await adapter.add(session_id="s1", messages=messages)

        mock_client.thread.add_messages.assert_called_once()

    async def test_get(self):
        mock_response = MagicMock()
        mock_response.messages = [
            _mock_zep_message("user", "hello"),
            _mock_zep_message("assistant", "hi"),
        ]
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.get = AsyncMock(return_value=mock_response)
        adapter = self._make_adapter(mock_client)

        messages = await adapter.get(session_id="s1", limit=10)

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "hello"

    async def test_search(self):
        mock_episode = MagicMock()
        mock_episode.thread_id = "s1"
        mock_episode.role = "user"
        mock_episode.content = "hello there"
        mock_results = MagicMock()
        mock_results.episodes = [mock_episode]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        messages = await adapter.search(session_id="s1", query="hello")

        assert len(messages) == 1
        assert messages[0].content == "hello there"

    async def test_search_filters_by_session(self):
        ep1 = MagicMock()
        ep1.thread_id = "s1"
        ep1.role = "user"
        ep1.content = "hello"
        ep2 = MagicMock()
        ep2.thread_id = "s2"
        ep2.role = "user"
        ep2.content = "other session"
        mock_results = MagicMock()
        mock_results.episodes = [ep1, ep2]
        mock_client = MagicMock()
        mock_client.graph = MagicMock()
        mock_client.graph.search = AsyncMock(return_value=mock_results)
        adapter = self._make_adapter(mock_client)

        messages = await adapter.search(session_id="s1", query="hello")

        assert len(messages) == 1
        assert messages[0].content == "hello"

    async def test_delete(self):
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.delete = AsyncMock()
        adapter = self._make_adapter(mock_client)

        await adapter.delete(session_id="s1")

        mock_client.thread.delete.assert_called_once_with("s1")

    async def test_provider_error_wrapping(self):
        mock_client = MagicMock()
        mock_client.thread = MagicMock()
        mock_client.thread.get = AsyncMock(side_effect=RuntimeError("api error"))
        adapter = self._make_adapter(mock_client)

        with pytest.raises(ProviderError) as exc_info:
            await adapter.get(session_id="s1")
        assert exc_info.value.provider == "zep"
