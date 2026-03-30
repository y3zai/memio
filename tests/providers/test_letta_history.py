import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Message
from memio.exceptions import ProviderError

_mock_letta_module = MagicMock()


class TestLettaHistoryAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"letta_client": _mock_letta_module}):
            from memio.providers.letta.history import LettaHistoryAdapter
            adapter = LettaHistoryAdapter.__new__(LettaHistoryAdapter)
            adapter._client = mock_client
            adapter._agent_id = "agent-1"
            adapter._sessions = {}
        return adapter

    async def test_add(self):
        mock_client = AsyncMock()
        mock_conv = MagicMock()
        mock_conv.id = "conv-1"
        mock_client.conversations.create.return_value = mock_conv
        mock_client.conversations.messages.create.return_value = MagicMock()
        adapter = self._make_adapter(mock_client)

        messages = [Message(role="user", content="hello")]
        with patch.dict("sys.modules", {"letta_client": _mock_letta_module}):
            await adapter.add(session_id="s1", messages=messages)

        mock_client.conversations.messages.create.assert_called_once()

    async def test_add_reuses_existing_conversation(self):
        mock_client = AsyncMock()
        mock_client.conversations.messages.create.return_value = MagicMock()
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-existing"}

        messages = [Message(role="user", content="hello again")]
        with patch.dict("sys.modules", {"letta_client": _mock_letta_module}):
            await adapter.add(session_id="s1", messages=messages)

        mock_client.conversations.create.assert_not_called()

    async def test_get(self):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.text = "hello"
        mock_msg.name = None
        mock_msg.created_at = None
        mock_client.conversations.messages.list.return_value = [mock_msg]
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        results = await adapter.get(session_id="s1")

        assert len(results) == 1
        assert results[0].role == "user"
        assert results[0].content == "hello"

    async def test_get_unknown_session(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        results = await adapter.get(session_id="unknown")

        assert results == []

    async def test_search(self):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.text = "coffee preference"
        mock_msg.name = None
        mock_msg.created_at = None
        mock_client.conversations.messages.list.return_value = [mock_msg]
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        results = await adapter.search(session_id="s1", query="coffee")

        assert len(results) == 1

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        await adapter.delete(session_id="s1")

        mock_client.conversations.delete.assert_called_once_with(
            conversation_id="conv-1"
        )
        assert "s1" not in adapter._sessions

    async def test_get_all(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1", "s2": "conv-2"}

        results = await adapter.get_all(user_id="u1")

        assert len(results) == 2

    async def test_delete_all(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1", "s2": "conv-2"}

        await adapter.delete_all(user_id="u1")

        assert mock_client.conversations.delete.call_count == 2
        assert adapter._sessions == {}

    async def test_provider_error_wrapping(self):
        mock_client = AsyncMock()
        mock_client.conversations.messages.list.side_effect = RuntimeError(
            "api error"
        )
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        with pytest.raises(ProviderError) as exc_info:
            await adapter.get(session_id="s1")
        assert exc_info.value.provider == "letta"
