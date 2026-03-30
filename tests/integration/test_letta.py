"""Integration tests for Letta provider adapters.

Requires a running Letta server or valid LETTA_API_KEY.
Set LETTA_AGENT_ID to the agent to use for testing.

Run with: pytest tests/integration/test_letta.py -m integration

Note: Letta's passages API has no native update, so update is emulated
via delete+create. This means the passage ID changes on update, making
the generic conformance tests incompatible. These tests account for that.
"""

import os

import pytest

from memio.models import Document, Fact, Message

pytestmark = pytest.mark.integration


@pytest.fixture
def letta_kwargs():
    kwargs = {}
    api_key = os.getenv("LETTA_API_KEY")
    base_url = os.getenv("LETTA_BASE_URL")
    agent_id = os.getenv("LETTA_AGENT_ID")
    if not agent_id:
        pytest.skip("LETTA_AGENT_ID not set")
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    kwargs["agent_id"] = agent_id
    return kwargs


class TestLettaFactIntegration:
    async def test_add_get_search_delete(self, letta_kwargs):
        from memio.providers.letta import LettaFactAdapter
        store = LettaFactAdapter(**letta_kwargs)

        await store.delete_all()

        fact = await store.add(content="likes coffee")
        assert isinstance(fact, Fact)
        assert fact.id is not None
        assert "coffee" in fact.content.lower()

        retrieved = await store.get(fact_id=fact.id)
        assert retrieved.id == fact.id
        assert "coffee" in retrieved.content.lower()

        results = await store.search(query="coffee")
        assert isinstance(results, list)
        assert len(results) >= 1

        all_facts = await store.get_all()
        assert isinstance(all_facts, list)
        assert any(f.id == fact.id for f in all_facts)

        await store.delete(fact_id=fact.id)
        after_delete = await store.get_all()
        assert all(f.id != fact.id for f in after_delete)

    async def test_update_emulates_via_delete_create(self, letta_kwargs):
        from memio.providers.letta import LettaFactAdapter
        store = LettaFactAdapter(**letta_kwargs)

        fact = await store.add(content="likes coffee", user_id="test-user")
        updated = await store.update(fact_id=fact.id, content="likes tea")
        # Update creates a new passage, so ID changes
        assert "tea" in updated.content.lower()
        assert updated.id != fact.id

        # Clean up
        await store.delete(fact_id=updated.id)

    async def test_delete_all(self, letta_kwargs):
        from memio.providers.letta import LettaFactAdapter
        store = LettaFactAdapter(**letta_kwargs)

        await store.add(content="bulk fact one")
        await store.add(content="bulk fact two")
        await store.delete_all()
        remaining = await store.get_all()
        assert len(remaining) == 0


class TestLettaDocumentIntegration:
    async def test_add_get_search_delete(self, letta_kwargs):
        from memio.providers.letta import LettaDocumentAdapter
        store = LettaDocumentAdapter(**letta_kwargs)

        await store.delete_all()

        doc = await store.add(content="deployment guide for production")
        assert isinstance(doc, Document)
        assert doc.id is not None

        retrieved = await store.get(doc_id=doc.id)
        assert retrieved.id == doc.id
        assert "deployment" in retrieved.content.lower()

        results = await store.search(query="deployment")
        assert isinstance(results, list)
        assert len(results) >= 1

        all_docs = await store.get_all()
        assert isinstance(all_docs, list)
        assert any(d.id == doc.id for d in all_docs)

        await store.delete(doc_id=doc.id)
        after_delete = await store.get_all()
        assert all(d.id != doc.id for d in after_delete)

    async def test_update_emulates_via_delete_create(self, letta_kwargs):
        from memio.providers.letta import LettaDocumentAdapter
        store = LettaDocumentAdapter(**letta_kwargs)

        doc = await store.add(content="original doc")
        updated = await store.update(doc_id=doc.id, content="updated doc")
        assert "updated" in updated.content.lower()
        assert updated.id != doc.id

        await store.delete(doc_id=updated.id)

    async def test_delete_all(self, letta_kwargs):
        from memio.providers.letta import LettaDocumentAdapter
        store = LettaDocumentAdapter(**letta_kwargs)

        await store.add(content="bulk doc one")
        await store.add(content="bulk doc two")
        await store.delete_all()
        remaining = await store.get_all()
        assert len(remaining) == 0


class TestLettaHistoryIntegration:
    async def test_add_get_delete(self, letta_kwargs):
        from memio.providers.letta import LettaHistoryAdapter
        store = LettaHistoryAdapter(**letta_kwargs)

        msgs = [Message(role="user", content="hello")]
        await store.add(
            session_id="test-session", messages=msgs, user_id="test-user",
        )

        retrieved = await store.get(session_id="test-session")
        assert isinstance(retrieved, list)
        assert len(retrieved) >= 1

        all_sessions = await store.get_all(user_id="test-user")
        assert isinstance(all_sessions, list)
        assert "test-session" in all_sessions

        await store.delete(session_id="test-session")
        after_delete = await store.get(session_id="test-session")
        assert len(after_delete) == 0
