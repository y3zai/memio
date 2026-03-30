import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from memio.models import Message
from memio.exceptions import ProviderError


class TestLettaHistoryAdapter:
    def _make_adapter(self, mock_client):
        with patch.dict("sys.modules", {"letta_client": MagicMock()}):
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

        async def _fake_stream():
            yield MagicMock()
        mock_client.conversations.messages.create.return_value = _fake_stream()
        adapter = self._make_adapter(mock_client)

        messages = [Message(role="user", content="hello")]
        await adapter.add(session_id="s1", messages=messages)

        mock_client.conversations.messages.create.assert_called_once()
        assert adapter._sessions["s1"] == "conv-1"

    async def test_add_reuses_existing_conversation(self):
        mock_client = AsyncMock()

        async def _fake_stream():
            yield MagicMock()
        mock_client.conversations.messages.create.return_value = _fake_stream()
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-existing"}

        messages = [Message(role="user", content="hello again")]
        await adapter.add(session_id="s1", messages=messages)

        mock_client.conversations.create.assert_not_called()

    async def test_get(self):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.message_type = "user_message"
        mock_msg.content = "hello"
        mock_msg.name = None
        mock_msg.date = None
        mock_page = MagicMock()
        mock_page.items = [mock_msg]
        mock_client.conversations.messages.list.return_value = mock_page
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        results = await adapter.get(session_id="s1")

        assert len(results) == 1
        assert results[0].role == "user"
        assert results[0].content == "hello"

    async def test_get_filters_non_user_messages(self):
        mock_client = AsyncMock()
        mock_user = MagicMock()
        mock_user.message_type = "user_message"
        mock_user.content = "hello"
        mock_user.name = None
        mock_user.date = None
        mock_tool = MagicMock()
        mock_tool.message_type = "tool_call_message"
        mock_page = MagicMock()
        mock_page.items = [mock_user, mock_tool]
        mock_client.conversations.messages.list.return_value = mock_page
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        results = await adapter.get(session_id="s1")

        assert len(results) == 1

    async def test_get_unknown_session(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)

        results = await adapter.get(session_id="unknown")

        assert results == []

    async def test_search(self):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.message_type = "user_message"
        mock_msg.content = "coffee preference"
        mock_msg.name = None
        mock_msg.date = None
        mock_page = MagicMock()
        mock_page.items = [mock_msg]
        mock_client.conversations.messages.list.return_value = mock_page
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        results = await adapter.search(session_id="s1", query="coffee")

        assert len(results) == 1

    async def test_delete(self):
        mock_client = AsyncMock()
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        await adapter.delete(session_id="s1")

        mock_client.conversations.delete.assert_called_once_with("conv-1")
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
        mock_client.conversations.messages.list.side_effect = RuntimeError("api error")
        adapter = self._make_adapter(mock_client)
        adapter._sessions = {"s1": "conv-1"}

        with pytest.raises(ProviderError) as exc_info:
            await adapter.get(session_id="s1")
        assert exc_info.value.provider == "letta"
