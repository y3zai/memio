"""Letta HistoryStore adapter.

Maps memio sessions to Letta conversations. Each session_id maps to a
Letta conversation. Messages are sent and retrieved via the conversations API.
"""

from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Message


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

    async def add(self, *, session_id: str, messages: list[Message]) -> None:
        try:
            conv_id = self._sessions.get(session_id)
            if conv_id is None:
                conv = await self._client.conversations.create(
                    agent_id=self._agent_id,
                )
                conv_id = conv.id
                self._sessions[session_id] = conv_id

            from letta_client import MessageCreate

            letta_messages = [
                MessageCreate(role=m.role, text=m.content, name=m.name)
                for m in messages
            ]
            await self._client.conversations.messages.create(
                conversation_id=conv_id,
                messages=letta_messages,
            )
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

            kwargs: dict = {"conversation_id": conv_id}
            if limit:
                kwargs["limit"] = limit
            if cursor:
                kwargs["after"] = cursor
            letta_messages = await self._client.conversations.messages.list(
                **kwargs
            )
            return [self._to_message(m) for m in letta_messages]
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

            letta_messages = await self._client.conversations.messages.list(
                conversation_id=conv_id,
            )
            query_lower = query.lower()
            results = [
                self._to_message(m)
                for m in letta_messages
                if query_lower in getattr(m, "text", "").lower()
            ]
            return results[:limit]
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise ProviderError("letta", "search", e) from e

    async def delete(self, *, session_id: str) -> None:
        try:
            conv_id = self._sessions.pop(session_id, None)
            if conv_id:
                await self._client.conversations.delete(
                    conversation_id=conv_id
                )
        except Exception as e:
            raise ProviderError("letta", "delete", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[str]:
        try:
            return list(self._sessions.keys())[:limit]
        except Exception as e:
            raise ProviderError("letta", "get_all", e) from e

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            for conv_id in list(self._sessions.values()):
                await self._client.conversations.delete(
                    conversation_id=conv_id
                )
            self._sessions.clear()
        except Exception as e:
            raise ProviderError("letta", "delete_all", e) from e

    @staticmethod
    def _to_message(letta_msg) -> Message:
        timestamp = None
        if hasattr(letta_msg, "created_at") and letta_msg.created_at:
            try:
                ts = letta_msg.created_at
                timestamp = (
                    ts
                    if isinstance(ts, datetime)
                    else datetime.fromisoformat(str(ts))
                )
            except (ValueError, TypeError):
                pass
        return Message(
            role=letta_msg.role,
            content=getattr(letta_msg, "text", "") or "",
            name=getattr(letta_msg, "name", None),
            timestamp=timestamp,
        )
