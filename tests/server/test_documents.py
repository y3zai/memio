"""Tests for /v1/documents endpoints."""

from httpx import AsyncClient


class TestDocumentEndpoints:
    async def test_add_document(self, client: AsyncClient):
        resp = await client.post("/v1/documents", json={"content": "memio docs"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "memio docs"
        assert data["id"] is not None

    async def test_get_document(self, client: AsyncClient):
        create = await client.post("/v1/documents", json={"content": "test"})
        doc_id = create.json()["id"]
        resp = await client.get(f"/v1/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == doc_id

    async def test_get_document_not_found(self, client: AsyncClient):
        resp = await client.get("/v1/documents/nonexistent")
        assert resp.status_code == 404

    async def test_get_all_documents(self, client: AsyncClient):
        await client.post("/v1/documents", json={"content": "a"})
        await client.post("/v1/documents", json={"content": "b"})
        resp = await client.get("/v1/documents")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_search_documents(self, client: AsyncClient):
        await client.post("/v1/documents", json={"content": "memio guide"})
        await client.post("/v1/documents", json={"content": "other stuff"})
        resp = await client.post("/v1/documents/search", json={"query": "memio"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_update_document(self, client: AsyncClient):
        create = await client.post("/v1/documents", json={"content": "old"})
        doc_id = create.json()["id"]
        resp = await client.put(
            f"/v1/documents/{doc_id}", json={"content": "new"}
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "new"

    async def test_delete_document(self, client: AsyncClient):
        create = await client.post("/v1/documents", json={"content": "bye"})
        doc_id = create.json()["id"]
        resp = await client.delete(f"/v1/documents/{doc_id}")
        assert resp.status_code == 204

    async def test_delete_all_documents(self, client: AsyncClient):
        await client.post("/v1/documents", json={"content": "a"})
        resp = await client.delete("/v1/documents")
        assert resp.status_code == 204
        get_resp = await client.get("/v1/documents")
        assert len(get_resp.json()) == 0
