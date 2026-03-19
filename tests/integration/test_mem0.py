import os
import pytest
from tests.conformance.fact_store import fact_store_conformance

pytestmark = pytest.mark.integration


@pytest.fixture
def mem0_api_key():
    key = os.environ.get("MEM0_API_KEY")
    if not key:
        pytest.skip("MEM0_API_KEY not set")
    return key


class TestMem0FactIntegration:
    async def test_conformance(self, mem0_api_key):
        from memio.providers.mem0 import Mem0FactAdapter
        adapter = Mem0FactAdapter(api_key=mem0_api_key)
        await fact_store_conformance(adapter)
