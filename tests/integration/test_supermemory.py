import asyncio
import os

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def supermemory_api_key():
    key = os.getenv("SUPERMEMORY_API_KEY")
    if not key:
        pytest.skip("SUPERMEMORY_API_KEY not set")
    return key


class TestSupermemoryFactIntegration:
    async def test_add_and_search(self, supermemory_api_key):
        from memio.providers.supermemory import SupermemoryFactAdapter

        adapter = SupermemoryFactAdapter(api_key=supermemory_api_key)
        fact = await adapter.add(
            content="integration test user likes python",
            user_id="test-user-integration",
        )
        assert fact.id is not None

        results = await adapter.search(
            query="python", user_id="test-user-integration",
        )
        assert isinstance(results, list)


class TestSupermemoryDocumentIntegration:
    async def test_add_get_delete(self, supermemory_api_key):
        from memio.providers.supermemory import SupermemoryDocumentAdapter

        adapter = SupermemoryDocumentAdapter(api_key=supermemory_api_key)
        doc = await adapter.add(
            content="integration test document for memio",
            metadata={"source": "test"},
        )
        assert doc.id is not None

        retrieved = await adapter.get(doc_id=doc.id)
        assert retrieved.id == doc.id

        # Supermemory processes documents asynchronously; wait for
        # processing to finish before deleting (409 otherwise).
        for _ in range(30):
            raw = await adapter._client.documents.get(doc.id)
            if raw.status == "done":
                break
            await asyncio.sleep(1)

        await adapter.delete(doc_id=doc.id)
