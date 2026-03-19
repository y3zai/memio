from memio.models import Message
from memio.protocols import HistoryStore


async def history_store_conformance(store: HistoryStore) -> None:
    msgs = [
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
    ]
    await store.add(session_id="test-session", messages=msgs)
    retrieved = await store.get(session_id="test-session")
    assert isinstance(retrieved, list)
    assert len(retrieved) >= 2
    results = await store.search(session_id="test-session", query="hello")
    assert isinstance(results, list)
    await store.delete(session_id="test-session")
    after_delete = await store.get(session_id="test-session")
    assert len(after_delete) == 0
