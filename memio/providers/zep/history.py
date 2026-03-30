# memio/providers/zep/history.py
from __future__ import annotations

from datetime import datetime

from memio.exceptions import ProviderError
from memio.models import Message


def _unwrap(response):
    """Unwrap AsyncHttpResponse to get the underlying data."""
    if hasattr(type(response), "data") and isinstance(
        getattr(type(response), "data"), property
    ):
        return response.data
    return response


class ZepHistoryAdapter:
    """HistoryStore implementation backed by Zep threads.

    Maps session IDs to Zep threads. Automatically creates users and threads
    on first message add. Returns empty lists (not errors) for non-existent
    sessions or users.

    Args:
        api_key: Zep Cloud API key.
        client: Pre-initialized AsyncZep client (overrides api_key).
    """

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
        self._session_owners: dict[str, str] = {}  # session_id -> user_id

    async def add(self, *, session_id: str, messages: list[Message],
                  user_id: str | None = None) -> None:
        try:
            # Use explicit user_id when provided, fall back to session_id
            owner = user_id or session_id
            self._session_owners[session_id] = owner
            # Ensure user and thread exist
            try:
                await self._client.user.add(user_id=owner)
            except Exception:
                pass  # User may already exist
            try:
                await self._client.thread.create(thread_id=session_id, user_id=owner)
            except Exception:
                pass  # Thread may already exist

            from zep_cloud.types import Message as ZepMessage
            zep_messages = [
                ZepMessage(role=m.role, content=m.content)
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
            response = _unwrap(await self._client.thread.get(**kwargs))
            messages = response.messages or []
            return [self._to_message(m) for m in messages]
        except Exception as e:
            # Thread not found after deletion — return empty list
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise ProviderError("zep", "get", e) from e

    async def search(
        self,
        *,
        session_id: str,
        query: str,
        limit: int = 10,
    ) -> list[Message]:
        try:
            owner = self._session_owners.get(session_id)
            if owner is None:
                # Derive owner from Zep thread metadata when cache misses
                try:
                    thread = _unwrap(
                        await self._client.thread.get(thread_id=session_id)
                    )
                    owner = getattr(thread, "user_id", None) or session_id
                    self._session_owners[session_id] = owner
                except Exception:
                    owner = session_id
            response = _unwrap(await self._client.graph.search(
                query=query, user_id=owner, limit=limit,
            ))
            results = []
            for episode in response.episodes or []:
                if getattr(episode, "thread_id", None) == session_id:
                    results.append(Message(
                        role=getattr(episode, "role", "user"),
                        content=episode.content,
                    ))
            return results[:limit]
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise ProviderError("zep", "search", e) from e

    async def delete(self, *, session_id: str) -> None:
        try:
            self._session_owners.pop(session_id, None)
            await self._client.thread.delete(session_id)
        except Exception as e:
            raise ProviderError("zep", "delete", e) from e

    async def get_all(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[str]:
        try:
            if not user_id:
                return []
            response = _unwrap(
                await self._client.user.get_threads(user_id)
            )
            threads = response if isinstance(response, list) else list(response or [])
            return [
                getattr(t, "thread_id", None) or getattr(t, "uuid_", None) or str(t)
                for t in threads[:limit]
            ]
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise ProviderError("zep", "get_all", e) from e

    async def delete_all(self, *, user_id: str | None = None) -> None:
        try:
            if user_id:
                # Remove cached owners for sessions belonging to this user
                to_remove = [
                    sid for sid, uid in self._session_owners.items()
                    if uid == user_id
                ]
                for sid in to_remove:
                    self._session_owners.pop(sid, None)
                try:
                    await self._client.user.delete(user_id)
                except Exception as inner:
                    if "404" not in str(inner) and "not found" not in str(inner).lower():
                        raise
        except Exception as e:
            raise ProviderError("zep", "delete_all", e) from e

    @staticmethod
    def _to_message(zep_msg) -> Message:
        timestamp = None
        if hasattr(zep_msg, "created_at") and zep_msg.created_at:
            try:
                timestamp = datetime.fromisoformat(str(zep_msg.created_at))
            except (ValueError, TypeError):
                pass
        return Message(
            role=getattr(zep_msg, "role_type", None) or zep_msg.role or "user",
            content=zep_msg.content,
            metadata=getattr(zep_msg, "metadata", None),
            timestamp=timestamp,
            name=getattr(zep_msg, "name", None),
        )
