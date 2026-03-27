from memio.models import Fact
from memio.protocols import FactStore


async def fact_store_conformance(store: FactStore) -> None:
    """Run full CRUD conformance against a FactStore implementation.

    Content assertions use case-insensitive keyword checks because some
    providers (e.g. Mem0) rephrase content through an LLM.
    """
    # Clean up leftover data from previous runs to avoid dedup issues
    await store.delete_all(user_id="test-user")
    await store.delete_all(user_id="test-user-bulk")

    fact = await store.add(content="likes coffee", user_id="test-user")
    assert isinstance(fact, Fact)
    assert fact.id is not None
    assert "coffee" in fact.content.lower()

    retrieved = await store.get(fact_id=fact.id)
    assert retrieved.id == fact.id
    assert "coffee" in retrieved.content.lower()

    results = await store.search(query="coffee", user_id="test-user")
    assert isinstance(results, list)
    assert any(f.id == fact.id for f in results)

    updated = await store.update(fact_id=fact.id, content="likes tea")
    assert "tea" in updated.content.lower()

    all_facts = await store.get_all(user_id="test-user")
    assert isinstance(all_facts, list)
    assert any(f.id == fact.id for f in all_facts)

    await store.delete(fact_id=fact.id)
    after_delete = await store.search(query="tea", user_id="test-user")
    assert all(f.id != fact.id for f in after_delete)

    await store.add(content="fact1", user_id="test-user-bulk")
    await store.add(content="fact2", user_id="test-user-bulk")
    await store.delete_all(user_id="test-user-bulk")
    remaining = await store.get_all(user_id="test-user-bulk")
    assert len(remaining) == 0
