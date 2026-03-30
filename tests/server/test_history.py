"""Tests for /v1/history endpoints."""

from httpx import AsyncClient


class TestHistoryEndpoints:
    async def test_add_messages(self, client: AsyncClient):
        resp = await client.post(
            "/v1/history/sessions/s1/messages",
            json={
                "messages": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi"},
                ],
            },
        )
        assert resp.status_code == 204

    async def test_get_messages(self, client: AsyncClient):
        await client.post(
            "/v1/history/sessions/s1/messages",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        resp = await client.get("/v1/history/sessions/s1/messages")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["role"] == "user"

    async def test_get_messages_with_limit(self, client: AsyncClient):
        await client.post(
            "/v1/history/sessions/s1/messages",
            json={"messages": [
                {"role": "user", "content": "a"},
                {"role": "user", "content": "b"},
            ]},
        )
        resp = await client.get("/v1/history/sessions/s1/messages", params={"limit": 1})
        assert len(resp.json()) == 1

    async def test_get_all_sessions(self, client: AsyncClient):
        await client.post(
            "/v1/history/sessions/s1/messages",
            json={"messages": [{"role": "user", "content": "a"}]},
        )
        await client.post(
            "/v1/history/sessions/s2/messages",
            json={"messages": [{"role": "user", "content": "b"}]},
        )
        resp = await client.get("/v1/history/sessions")
        assert resp.status_code == 200
        assert set(resp.json()["sessions"]) == {"s1", "s2"}

    async def test_search_session(self, client: AsyncClient):
        await client.post(
            "/v1/history/sessions/s1/messages",
            json={"messages": [
                {"role": "user", "content": "I like coffee"},
                {"role": "user", "content": "I like tea"},
            ]},
        )
        resp = await client.post(
            "/v1/history/sessions/s1/search",
            json={"query": "coffee"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_delete_session(self, client: AsyncClient):
        await client.post(
            "/v1/history/sessions/s1/messages",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        resp = await client.delete("/v1/history/sessions/s1")
        assert resp.status_code == 204

    async def test_delete_all_sessions(self, client: AsyncClient):
        await client.post(
            "/v1/history/sessions/s1/messages",
            json={"messages": [{"role": "user", "content": "a"}]},
        )
        resp = await client.delete("/v1/history/sessions")
        assert resp.status_code == 204
        get_resp = await client.get("/v1/history/sessions")
        assert len(get_resp.json()["sessions"]) == 0
