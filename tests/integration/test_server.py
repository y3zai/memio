"""Integration tests for the REST API server with real providers.

Requires MEM0_API_KEY and ZEP_API_KEY in .env.
Run with: pytest -m integration tests/integration/test_server.py -v
"""

import asyncio
import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from memio.server.app import create_app
from memio.server.config import ServerConfig, StoreConfig, build_memio_from_config

pytestmark = pytest.mark.integration


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mem0_api_key():
    key = os.environ.get("MEM0_API_KEY")
    if not key:
        pytest.skip("MEM0_API_KEY not set")
    return key


@pytest.fixture
def zep_api_key():
    key = os.environ.get("ZEP_API_KEY")
    if not key:
        pytest.skip("ZEP_API_KEY not set")
    return key


@pytest.fixture
async def facts_client(mem0_api_key):
    """Server with Mem0 fact store."""
    config = ServerConfig(
        stores={
            "facts": StoreConfig(provider="mem0", config={"api_key": mem0_api_key}),
        }
    )
    client = build_memio_from_config(config)
    app = create_app(config=config)
    app.state.memio = client
    app.state.api_key = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def history_client(zep_api_key):
    """Server with Zep history store."""
    config = ServerConfig(
        stores={
            "history": StoreConfig(provider="zep", config={"api_key": zep_api_key}),
        }
    )
    client = build_memio_from_config(config)
    app = create_app(config=config)
    app.state.memio = client
    app.state.api_key = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestServerFactsIntegration:
    """End-to-end: HTTP → FastAPI → Mem0FactAdapter → Mem0 Cloud."""

    async def test_add_search_delete(self, facts_client: AsyncClient):
        user_id = f"server-test-{uuid.uuid4().hex[:6]}"
        content = _unique("likes espresso")

        # Clean slate
        await facts_client.delete("/v1/facts", params={"user_id": user_id})
        await asyncio.sleep(2)

        # Add
        resp = await facts_client.post("/v1/facts", json={
            "content": content,
            "user_id": user_id,
        })
        assert resp.status_code == 201, resp.text
        fact = resp.json()
        assert fact["id"] is not None
        fact_id = fact["id"]

        # Get
        resp = await facts_client.get(f"/v1/facts/{fact_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == fact_id

        # Search
        resp = await facts_client.post("/v1/facts/search", json={
            "query": "espresso",
            "user_id": user_id,
        })
        assert resp.status_code == 200
        ids = [f["id"] for f in resp.json()]
        assert fact_id in ids

        # Delete
        resp = await facts_client.delete(f"/v1/facts/{fact_id}")
        assert resp.status_code == 204

        # Clean up
        await facts_client.delete("/v1/facts", params={"user_id": user_id})

    async def test_not_found(self, facts_client: AsyncClient):
        resp = await facts_client.get("/v1/facts/nonexistent-id-xyz")
        # Mem0 returns None for unknown IDs → 404
        assert resp.status_code in (404, 502)

    async def test_health_shows_facts_enabled(self, facts_client: AsyncClient):
        resp = await facts_client.get("/health")
        assert resp.status_code == 200
        stores = resp.json()["stores"]
        assert stores["facts"] is True
        assert stores["history"] is False


class TestServerHistoryIntegration:
    """End-to-end: HTTP → FastAPI → ZepHistoryAdapter → Zep Cloud."""

    async def test_add_get_delete(self, history_client: AsyncClient):
        session_id = f"server-test-{uuid.uuid4().hex[:6]}"

        # Add messages
        resp = await history_client.post(
            f"/v1/history/sessions/{session_id}/messages",
            json={
                "messages": [
                    {"role": "user", "content": "What is memio?"},
                    {"role": "assistant", "content": "A memory gateway for AI agents."},
                ],
            },
        )
        assert resp.status_code == 204

        # Give Zep a moment to process
        await asyncio.sleep(2)

        # Get messages
        resp = await history_client.get(
            f"/v1/history/sessions/{session_id}/messages"
        )
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) >= 2
        roles = [m["role"] for m in messages]
        assert "user" in roles
        assert "assistant" in roles

        # Delete session
        resp = await history_client.delete(
            f"/v1/history/sessions/{session_id}"
        )
        assert resp.status_code == 204

    async def test_unconfigured_store_returns_501(self, history_client: AsyncClient):
        """Facts store is not configured on this server → 501."""
        resp = await history_client.get("/v1/facts/anything")
        assert resp.status_code == 501
