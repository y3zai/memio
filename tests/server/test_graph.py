"""Tests for /v1/graph endpoints."""

from httpx import AsyncClient


class TestGraphEndpoints:
    async def test_add_triples(self, client: AsyncClient):
        resp = await client.post("/v1/graph/triples", json={
            "triples": [
                {"subject": "Alice", "predicate": "knows", "object": "Bob"},
            ],
        })
        assert resp.status_code == 204

    async def test_get_all_triples(self, client: AsyncClient):
        await client.post("/v1/graph/triples", json={
            "triples": [
                {"subject": "Alice", "predicate": "knows", "object": "Bob"},
            ],
        })
        resp = await client.get("/v1/graph/triples")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["triples"]) == 1
        assert data["triples"][0]["subject"] == "Alice"

    async def test_get_entity(self, client: AsyncClient):
        await client.post("/v1/graph/triples", json={
            "triples": [
                {"subject": "Alice", "predicate": "knows", "object": "Bob"},
                {"subject": "Charlie", "predicate": "knows", "object": "Dan"},
            ],
        })
        resp = await client.get("/v1/graph/entities/Alice")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["triples"]) == 1
        assert "Alice" in data["nodes"]

    async def test_search_graph(self, client: AsyncClient):
        await client.post("/v1/graph/triples", json={
            "triples": [
                {"subject": "Alice", "predicate": "likes", "object": "coffee"},
                {"subject": "Bob", "predicate": "likes", "object": "tea"},
            ],
        })
        resp = await client.post("/v1/graph/search", json={"query": "coffee"})
        assert resp.status_code == 200
        assert len(resp.json()["triples"]) == 1

    async def test_delete_entity(self, client: AsyncClient):
        await client.post("/v1/graph/triples", json={
            "triples": [
                {"subject": "Alice", "predicate": "knows", "object": "Bob"},
            ],
        })
        resp = await client.delete("/v1/graph/entities/Alice")
        assert resp.status_code == 204
        get_resp = await client.get("/v1/graph/triples")
        assert len(get_resp.json()["triples"]) == 0

    async def test_delete_all_graph(self, client: AsyncClient):
        await client.post("/v1/graph/triples", json={
            "triples": [
                {"subject": "A", "predicate": "r", "object": "B"},
            ],
        })
        resp = await client.delete("/v1/graph")
        assert resp.status_code == 204
        get_resp = await client.get("/v1/graph/triples")
        assert len(get_resp.json()["triples"]) == 0
