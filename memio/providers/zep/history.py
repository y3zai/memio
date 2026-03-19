# memio/providers/zep/history.py
from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Message


class ZepHistoryAdapter:
    def __init__(self, *, api_key: str | None = None, client=None):
        try:
            from zep_cloud import AsyncZep
        except ImportError:
            raise ImportError(
                "zep provider requires zep-cloud: pip install memio[zep]"
            )
        if client is not None:
            self._client = client
        else:
            self._client = AsyncZep(api_key=api_key)

    async def add(self, *, session_id: str, messages: list[Message]) -> None:
        try:
            # Ensure thread exists
            try:
                await self._client.thread.create(thread_id=session_id, user_id=session_id)
            except Exception:
                pass  # Thread may already exist

            try:
                from zep_cloud.types import Message as ZepMessage
                zep_messages = [
                    ZepMessage(role=m.role, content=m.content, role_type=m.role)
                    for m in messages
                ]
            except ImportError:
                zep_messages = [
                    {"role": m.role, "content": m.content, "role_type": m.role}
                    for m in messages
                ]
            await self._client.thread.add_messages(
                thread_id=session_id, messages=zep_messages,
            )
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError("zep", "add", e) from e

    async def get(
        self,
        *,
        session_id: str,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[Message]:
        try:
            kwargs: dict = {"thread_id": session_id, "limit": limit}
            if cursor:
                kwargs["cursor"] = cursor
            response = await self._client.thread.get(**kwargs)
            messages = response.messages or []
            return [self._to_message(m) for m in messages]
        except Exception as e:
            raise ProviderError("zep", "get", e) from e

    async def search(
        self,
        *,
        session_id: str,
        query: str,
        limit: int = 10,
    ) -> list[Message]:
        try:
            response = await self._client.graph.search(
                query=query, limit=limit,
            )
            results = []
            for episode in response.episodes or []:
                if getattr(episode, "thread_id", None) == session_id:
                    results.append(Message(
                        role=getattr(episode, "role", "user"),
                        content=episode.content,
                    ))
            return results[:limit]
        except Exception as e:
            raise ProviderError("zep", "search", e) from e

    async def delete(self, *, session_id: str) -> None:
        try:
            await self._client.thread.delete(session_id)
        except Exception as e:
            raise ProviderError("zep", "delete", e) from e

    @staticmethod
    def _to_message(zep_msg) -> Message:
        timestamp = None
        if hasattr(zep_msg, "created_at") and zep_msg.created_at:
            try:
                timestamp = datetime.fromisoformat(str(zep_msg.created_at))
            except (ValueError, TypeError):
                pass
        return Message(
            role=zep_msg.role_type or zep_msg.role or "user",
            content=zep_msg.content,
            metadata=getattr(zep_msg, "metadata", None),
            timestamp=timestamp,
            name=getattr(zep_msg, "name", None),
        )
