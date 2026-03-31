"""Tests for API key authentication."""

from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from memio.client import Memio
from memio.server.app import create_app
from memio.server.config import ServerConfig
from tests.server.conftest import FakeFactStore


@pytest.fixture
async def auth_client() -> AsyncIterator[AsyncClient]:
    """Client with auth enabled (api_key = 'test-secret')."""
    config = ServerConfig(api_key="test-secret")
    app = create_app(config=config)
    fake = Memio(facts=FakeFactStore())
    app.state.memio = fake
    app.state.api_key = "test-secret"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestAuth:
    async def test_no_auth_required_when_disabled(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_missing_token_returns_401(self, auth_client: AsyncClient):
        resp = await auth_client.get("/health")
        assert resp.status_code == 401

    async def test_invalid_token_returns_403(self, auth_client: AsyncClient):
        resp = await auth_client.get(
            "/health", headers={"Authorization": "Bearer wrong"}
        )
        assert resp.status_code == 403

    async def test_valid_token_succeeds(self, auth_client: AsyncClient):
        resp = await auth_client.get(
            "/health", headers={"Authorization": "Bearer test-secret"}
        )
        assert resp.status_code == 200
