"""Integration tests for Letta provider adapters.

Requires a running Letta server or valid LETTA_API_KEY.
Set LETTA_AGENT_ID to the agent to use for testing.

Run with: pytest tests/integration/test_letta.py -m integration
"""

import os

import pytest

from tests.conformance.fact_store import fact_store_conformance
from tests.conformance.document_store import document_store_conformance
from tests.conformance.history_store import history_store_conformance

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


async def test_letta_fact_store(letta_kwargs):
    from memio.providers.letta import LettaFactAdapter
    store = LettaFactAdapter(**letta_kwargs)
    await fact_store_conformance(store)


async def test_letta_document_store(letta_kwargs):
    from memio.providers.letta import LettaDocumentAdapter
    store = LettaDocumentAdapter(**letta_kwargs)
    await document_store_conformance(store)


async def test_letta_history_store(letta_kwargs):
    from memio.providers.letta import LettaHistoryAdapter
    store = LettaHistoryAdapter(**letta_kwargs)
    await history_store_conformance(store)
