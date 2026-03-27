import os
import pytest
from tests.conformance.history_store import history_store_conformance

pytestmark = pytest.mark.integration


@pytest.fixture
def zep_api_key():
    key = os.environ.get("ZEP_API_KEY")
    if not key:
        pytest.skip("ZEP_API_KEY not set")
    return key


class TestZepHistoryIntegration:
    async def test_conformance(self, zep_api_key):
        from memio.providers.zep import ZepHistoryAdapter
        adapter = ZepHistoryAdapter(api_key=zep_api_key)
        await history_store_conformance(adapter)


class TestZepFactIntegration:
    """Zep-specific fact tests.

    Zep's graph API is eventually consistent — graph.add sends text to an
    LLM that asynchronously extracts structured facts (edges). This means:
    - add() returns an episode ID, not an edge ID
    - Edges may take seconds to minutes to appear, or may not appear at all
      for very short content
    - The generic fact_store_conformance (synchronous add→get-by-id) does
      not apply

    These tests verify the adapter's API calls work correctly against the
    real Zep service.
    """

    async def test_add_returns_fact(self, zep_api_key):
        from memio.providers.zep import ZepFactAdapter
        from memio.models import Fact
        adapter = ZepFactAdapter(api_key=zep_api_key)

        # Clean up
        await adapter.delete_all(user_id="test-user-zep-fact")

        fact = await adapter.add(
            content="The user prefers dark roast coffee over light roast",
            user_id="test-user-zep-fact",
        )
        assert isinstance(fact, Fact)
        assert fact.id is not None
        assert "coffee" in fact.content.lower()

        # Clean up
        await adapter.delete_all(user_id="test-user-zep-fact")

    async def test_search(self, zep_api_key):
        from memio.providers.zep import ZepFactAdapter
        adapter = ZepFactAdapter(api_key=zep_api_key)

        results = await adapter.search(
            query="coffee", user_id="test-user-zep-fact",
        )
        assert isinstance(results, list)

    async def test_get_all(self, zep_api_key):
        from memio.providers.zep import ZepFactAdapter
        adapter = ZepFactAdapter(api_key=zep_api_key)

        results = await adapter.get_all(user_id="test-user-zep-fact")
        assert isinstance(results, list)

    async def test_delete_all_idempotent(self, zep_api_key):
        from memio.providers.zep import ZepFactAdapter
        adapter = ZepFactAdapter(api_key=zep_api_key)

        # Should not raise even if user doesn't exist
        await adapter.delete_all(user_id="nonexistent-user-zep-test")
