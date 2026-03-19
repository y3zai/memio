import pytest
from tests.conformance.document_store import document_store_conformance

pytestmark = pytest.mark.integration


class TestChromaDocumentIntegration:
    async def test_conformance(self, tmp_path):
        """Uses local ephemeral Chroma — no API key needed."""
        try:
            import chromadb
        except ImportError:
            pytest.skip("chromadb not installed")
        client = chromadb.EphemeralClient()
        from memio.providers.chroma import ChromaDocumentAdapter
        adapter = ChromaDocumentAdapter(client=client, collection_name="test-integration")
        await document_store_conformance(adapter)
