import pytest
from tests.conformance.document_store import document_store_conformance

pytestmark = pytest.mark.integration


class TestQdrantDocumentIntegration:
    async def test_conformance(self):
        """Uses in-memory Qdrant — no API key needed."""
        try:
            from qdrant_client import AsyncQdrantClient
        except ImportError:
            pytest.skip("qdrant-client not installed")
        client = AsyncQdrantClient(":memory:")
        from memio.providers.qdrant import QdrantDocumentAdapter
        adapter = QdrantDocumentAdapter(client=client, collection_name="test-integration")
        await document_store_conformance(adapter)
        await client.close()
