from memio.models import GraphResult, Triple
from memio.protocols import GraphStore


async def graph_store_conformance(store: GraphStore) -> None:
    triples = [
        Triple(subject="Alice", predicate="works_at", object="Acme"),
        Triple(subject="Acme", predicate="is_a", object="startup"),
    ]
    await store.add(triples=triples, user_id="test-user")
    results = await store.search(query="Alice", user_id="test-user")
    assert isinstance(results, GraphResult)
    result = await store.get(entity="Alice", user_id="test-user")
    assert isinstance(result, GraphResult)
    all_results = await store.get_all(user_id="test-user")
    assert isinstance(all_results, GraphResult)
    await store.delete_all(user_id="test-user")
    after_delete = await store.get_all(user_id="test-user")
    assert len(after_delete.triples) == 0
