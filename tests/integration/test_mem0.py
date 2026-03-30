import asyncio
import os
import uuid
import pytest
from memio.models import Fact

pytestmark = pytest.mark.integration


@pytest.fixture
def mem0_api_key():
    key = os.environ.get("MEM0_API_KEY")
    if not key:
        pytest.skip("MEM0_API_KEY not set")
    return key


def _unique(prefix: str) -> str:
    """Return a unique string to avoid Mem0 deduplication."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TestMem0FactIntegration:
    """Mem0 Cloud processes memories asynchronously, so we cannot use the
    generic fact_store_conformance helper (which assumes synchronous CRUD).
    Instead we test each operation with polling where needed.
    """

    async def test_add_search_get_update_delete(self, mem0_api_key):
        from memio.providers.mem0 import Mem0FactAdapter

        adapter = Mem0FactAdapter(api_key=mem0_api_key)
        user = "test-user-integration"
        unique_content = _unique("likes coffee")

        # Clean up from any previous run
        await adapter.delete_all(user_id=user)
        await asyncio.sleep(2)

        # --- add (async processing) ---
        fact = await adapter.add(content=unique_content, user_id=user)
        assert isinstance(fact, Fact)
        assert fact.id is not None

        # Poll until the memory appears (async processing)
        real_id = None
        for _ in range(20):
            await asyncio.sleep(2)
            all_facts = await adapter.get_all(user_id=user)
            if all_facts:
                real_id = all_facts[0].id
                break
        assert real_id is not None, "memory never appeared after add"

        # --- get ---
        retrieved = await adapter.get(fact_id=real_id)
        assert retrieved.id == real_id
        assert "coffee" in retrieved.content.lower()

        # --- search ---
        results = await adapter.search(query="coffee", user_id=user)
        assert isinstance(results, list)
        assert any(f.id == real_id for f in results)

        # --- update ---
        updated = await adapter.update(fact_id=real_id, content="likes tea")
        assert "tea" in updated.content.lower()

        # --- delete ---
        await adapter.delete(fact_id=real_id)
        await asyncio.sleep(2)
        after_delete = await adapter.search(query="tea", user_id=user)
        assert all(f.id != real_id for f in after_delete)

    async def test_delete_all(self, mem0_api_key):
        from memio.providers.mem0 import Mem0FactAdapter

        adapter = Mem0FactAdapter(api_key=mem0_api_key)
        user = "test-user-bulk"

        await adapter.delete_all(user_id=user)

        await adapter.add(content=_unique("bulk fact one"), user_id=user)
        await adapter.add(content=_unique("bulk fact two"), user_id=user)

        # Wait for async processing
        for _ in range(15):
            await asyncio.sleep(2)
            all_facts = await adapter.get_all(user_id=user)
            if len(all_facts) >= 2:
                break

        # Delete all and retry — async processing may create stragglers
        for _ in range(3):
            await adapter.delete_all(user_id=user)
            await asyncio.sleep(2)
            remaining = await adapter.get_all(user_id=user)
            if len(remaining) == 0:
                break
        assert len(remaining) == 0
