"""Tests for /v1/facts endpoints."""

from httpx import AsyncClient


class TestFactEndpoints:
    async def test_add_fact(self, client: AsyncClient):
        resp = await client.post("/v1/facts", json={
            "content": "likes coffee", "user_id": "alice",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "likes coffee"
        assert data["user_id"] == "alice"
        assert data["id"] is not None

    async def test_get_fact(self, client: AsyncClient):
        create = await client.post("/v1/facts", json={"content": "test"})
        fact_id = create.json()["id"]
        resp = await client.get(f"/v1/facts/{fact_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == fact_id

    async def test_get_fact_not_found(self, client: AsyncClient):
        resp = await client.get("/v1/facts/nonexistent")
        assert resp.status_code == 404
        assert "not_found" in resp.json()["error"]

    async def test_get_all_facts(self, client: AsyncClient):
        await client.post("/v1/facts", json={"content": "a"})
        await client.post("/v1/facts", json={"content": "b"})
        resp = await client.get("/v1/facts")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_get_all_facts_with_limit(self, client: AsyncClient):
        await client.post("/v1/facts", json={"content": "a"})
        await client.post("/v1/facts", json={"content": "b"})
        resp = await client.get("/v1/facts", params={"limit": 1})
        assert len(resp.json()) == 1

    async def test_search_facts(self, client: AsyncClient):
        await client.post("/v1/facts", json={"content": "likes coffee"})
        await client.post("/v1/facts", json={"content": "likes tea"})
        resp = await client.post("/v1/facts/search", json={"query": "coffee"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert "coffee" in resp.json()[0]["content"]

    async def test_update_fact(self, client: AsyncClient):
        create = await client.post("/v1/facts", json={"content": "old"})
        fact_id = create.json()["id"]
        resp = await client.put(f"/v1/facts/{fact_id}", json={"content": "new"})
        assert resp.status_code == 200
        assert resp.json()["content"] == "new"

    async def test_delete_fact(self, client: AsyncClient):
        create = await client.post("/v1/facts", json={"content": "to delete"})
        fact_id = create.json()["id"]
        resp = await client.delete(f"/v1/facts/{fact_id}")
        assert resp.status_code == 204

    async def test_delete_all_facts(self, client: AsyncClient):
        await client.post("/v1/facts", json={"content": "a"})
        resp = await client.delete("/v1/facts")
        assert resp.status_code == 204
        get_resp = await client.get("/v1/facts")
        assert len(get_resp.json()) == 0
