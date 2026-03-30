"""Tests for exception-to-HTTP mapping."""

import pytest
from httpx import ASGITransport, AsyncClient

from memio.client import Memio
from memio.exceptions import NotFoundError, NotSupportedError, ProviderError
from memio.server.app import create_app
from memio.server.config import ServerConfig
from tests.server.conftest import FakeDocumentStore, FakeFactStore


class _ErrorFactStore(FakeFactStore):
    """A fake fact store where we can inject exceptions."""

    def __init__(self, error: Exception | None = None):
        super().__init__()
        self._error = error

    async def get(self, *, fact_id: str):
        if self._error:
            raise self._error
        return await super().get(fact_id=fact_id)


class TestErrorHandlers:
    async def _make_client(self, error: Exception):
        store = _ErrorFactStore(error=error)
        config = ServerConfig()
        app = create_app(config=config)
        fake = Memio(facts=store)
        app.state.memio = fake
        app.state.api_key = None
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    async def test_not_found_returns_404(self):
        async with await self._make_client(NotFoundError("fact", "xyz")) as c:
            resp = await c.get("/v1/facts/xyz")
        assert resp.status_code == 404
        assert resp.json()["error"] == "not_found"

    async def test_not_supported_returns_501(self):
        async with await self._make_client(NotSupportedError("test", "get")) as c:
            resp = await c.get("/v1/facts/xyz")
        assert resp.status_code == 501
        assert resp.json()["error"] == "not_supported"
        assert resp.json()["provider"] == "test"

    async def test_provider_error_returns_502(self):
        err = ProviderError("test", "get", RuntimeError("boom"))
        async with await self._make_client(err) as c:
            resp = await c.get("/v1/facts/xyz")
        assert resp.status_code == 502
        assert resp.json()["error"] == "provider_error"

    async def test_unconfigured_store_returns_501(self):
        config = ServerConfig()
        app = create_app(config=config)
        fake = Memio(documents=FakeDocumentStore())
        app.state.memio = fake
        app.state.api_key = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/v1/facts/anything")
        assert resp.status_code == 501
        assert "not configured" in resp.json()["detail"]
