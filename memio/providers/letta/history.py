"""Letta HistoryStore adapter.

Maps memio sessions to Letta conversations. Each session_id maps to a
Letta conversation. Messages are sent and retrieved via the conversations API.

Known quirks:
- conversations.messages.create sends messages to the agent and triggers
  processing (returns a stream). The agent may generate additional messages.
- Messages returned from list are polymorphic (UserMessage, AssistantMessage,
  etc.) with a message_type discriminator.
- Message content field is ``content`` (not ``text``), timestamp is ``date``.
"""

from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Message


_USER_VISIBLE_TYPES = {"user_message", "assistant_message"}


class LettaHistoryAdapter:
    """HistoryStore implementation backed by Letta conversations.

    Maintains a session_id -> conversation_id mapping. Creates a new
    Letta conversation on first add for each session.

    Args:
        agent_id: The Letta agent that owns the conversations.
        api_key: Letta Cloud API key. Mutually exclusive with base_url.
        base_url: URL of a self-hosted Letta server.
    """

    def __init__(
        self,
        *,
        agent_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        try:
            from letta_client import AsyncLetta
        except ImportError:
            raise ImportError(
                "letta provider requires letta-client: pip install memio[letta]"
            )
        kwargs: dict = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncLetta(**kwargs)
        self._agent_id = agent_id
        self._sessions: dict[str, str] = {}  # session_id -> conversation_id
        self._session_owners: dict[str, str] = {}  # session_id -> user_id

    async def add(self, *, session_id: str, messages: list[Message],
                  user_id: str | None = None) -> None:
        try:
            conv_id = self._sessions.get(session_id)
            if conv_id is None:
                conv = await self._client.conversations.create(
                    agent_id=self._agent_id,
                )
                conv_id = conv.id
                self._sessions[session_id] = conv_id
            if user_id is not None:
                self._session_owners[session_id] = user_id

            letta_messages = [
                {"role": m.role, "content": m.content, "name": m.name}
                for m in messages
            ]
            stream = await self._client.conversations.messages.create(
                conv_id,
                messages=letta_messages,
            )
            # Consume the stream to complete the request
            async for _ in stream:
                pass
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError("letta", "add", e) from e

    async def get(
        self,
        *,
        session_id: str,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[Message]:
        try:
            conv_id = self._sessions.get(session_id)
            if conv_id is None:
                return []

            kwargs: dict = {"limit": limit}
            if cursor:
                kwargs["after"] = cursor
            page = await self._client.conversations.messages.list(
                conv_id, **kwargs
            )
            items = page.items if hasattr(page, "items") else list(page)
            return [
                self._to_message(m) for m in items
                if getattr(m, "message_type", None) in _USER_VISIBLE_TYPES
            ]
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise ProviderError("letta", "get", e) from e

    async def search(
        self,
        *,
        session_id: str,
        query: str,
        limit: int = 10,
    ) -> list[Message]:
        try:
            conv_id = self._sessions.get(session_id)
            if conv_id is None:
                return []

            page = await self._client.conversations.messages.list(conv_id)
            items = page.items if hasattr(page, "items") else list(page)
            query_lower = query.lower()
            results = []
            for m in items:
                if getattr(m, "message_type", None) not in _USER_VISIBLE_TYPES:
                    continue
                content = self._extract_content(m)
                if query_lower in content.lower():
                    results.append(self._to_message(m))
            return results[:limit]
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise ProviderError("letta", "search", e) from e

    async def delete(self, *, session_id: str) -> None:
        try:
            conv_id = self._sessions.pop(session_id, None)
            self._session_owners.pop(session_id, None)
            if conv_id:
                await self._client.conversations.delete(conv_id)
        except Exception as e:
            raise ProviderError("letta", "delete", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[str]:
        try:
            if user_id is not None:
                return [
                    sid for sid, uid in self._session_owners.items()
                    if uid == user_id
                ][:limit]
            return list(self._sessions.keys())[:limit]
        except Exception as e:
            raise ProviderError("letta", "get_all", e) from e

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            if user_id is not None:
                to_delete = [
                    sid for sid, uid in self._session_owners.items()
                    if uid == user_id
                ]
            else:
                to_delete = list(self._sessions.keys())
            for sid in to_delete:
                conv_id = self._sessions.pop(sid, None)
                self._session_owners.pop(sid, None)
                if conv_id:
                    await self._client.conversations.delete(conv_id)
        except Exception as e:
            raise ProviderError("letta", "delete_all", e) from e

    @staticmethod
    def _extract_content(letta_msg) -> str:
        content = getattr(letta_msg, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if hasattr(item, "text"):
                    parts.append(item.text)
                elif isinstance(item, str):
                    parts.append(item)
            return " ".join(parts)
        return str(content) if content else ""

    @classmethod
    def _to_message(cls, letta_msg) -> Message:
        timestamp = None
        if hasattr(letta_msg, "date") and letta_msg.date:
            try:
                ts = letta_msg.date
                timestamp = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts))
            except (ValueError, TypeError):
                pass

        msg_type = getattr(letta_msg, "message_type", "")
        if msg_type == "user_message":
            role = "user"
        elif msg_type == "assistant_message":
            role = "assistant"
        else:
            role = "system"

        return Message(
            role=role,
            content=cls._extract_content(letta_msg),
            name=getattr(letta_msg, "name", None),
            timestamp=timestamp,
        )
