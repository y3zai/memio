from memio.models import Message
from memio.protocols import HistoryStore


async def history_store_conformance(store: HistoryStore) -> None:
    # Clean up leftover data from previous runs
    await store.delete_all(user_id="test-user")

    msgs = [
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
    ]
    await store.add(session_id="test-session", messages=msgs, user_id="test-user")
    retrieved = await store.get(session_id="test-session")
    assert isinstance(retrieved, list)
    assert len(retrieved) >= 2
    results = await store.search(session_id="test-session", query="hello")
    assert isinstance(results, list)

    all_sessions = await store.get_all(user_id="test-user")
    assert isinstance(all_sessions, list)
    assert "test-session" in all_sessions

    await store.delete(session_id="test-session")
    after_delete = await store.get(session_id="test-session")
    assert len(after_delete) == 0

    # Test delete_all scoped to user
    await store.add(
        session_id="test-session-bulk", messages=msgs, user_id="test-user",
    )
    await store.delete_all(user_id="test-user")
    after_bulk = await store.get(session_id="test-session-bulk")
    assert len(after_bulk) == 0
