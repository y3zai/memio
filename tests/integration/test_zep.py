import os
import pytest
from tests.conformance.fact_store import fact_store_conformance
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
    async def test_conformance(self, zep_api_key):
        from memio.providers.zep import ZepFactAdapter
        adapter = ZepFactAdapter(api_key=zep_api_key)
        await fact_store_conformance(adapter)
