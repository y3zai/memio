import pytest
from memio.client import Memio
from memio.protocols import FactStore, HistoryStore, DocumentStore, GraphStore
from memio.models import Fact, Message, Document, Triple, GraphResult


class FakeFactStore:
    async def add(self, *, content, user_id=None, agent_id=None, metadata=None):
        return Fact(id="f1", content=content)
    async def search(self, *, query, user_id=None, agent_id=None, limit=10, filters=None):
        return []
    async def update(self, *, fact_id, content, metadata=None):
        return Fact(id=fact_id, content=content)
    async def get(self, *, fact_id):
        return Fact(id=fact_id, content="test")
    async def delete(self, *, fact_id):
        pass
    async def delete_all(self, *, user_id=None, agent_id=None):
        pass
    async def get_all(self, *, user_id=None, agent_id=None, limit=100):
        return []


class FakeHistoryStore:
    async def add(self, *, session_id, messages):
        pass
    async def get(self, *, session_id, limit=50, cursor=None):
        return []
    async def search(self, *, session_id, query, limit=10):
        return []
    async def delete(self, *, session_id):
        pass


class FakeDocumentStore:
    async def add(self, *, content, doc_id=None, metadata=None):
        return Document(id="d1", content=content)
    async def get(self, *, doc_id):
        return Document(id=doc_id, content="test")
    async def search(self, *, query, limit=10, filters=None):
        return []
    async def update(self, *, doc_id, content, metadata=None):
        return Document(id=doc_id, content=content)
    async def delete(self, *, doc_id):
        pass


class FakeGraphStore:
    async def add(self, *, triples, user_id=None):
        pass
    async def get(self, *, entity, user_id=None):
        return GraphResult()
    async def get_all(self, *, user_id=None, limit=100):
        return GraphResult()
    async def search(self, *, query, user_id=None, limit=10):
        return GraphResult()
    async def delete(self, *, entity=None, triple_id=None):
        pass
    async def delete_all(self, *, user_id=None):
        pass


class TestMemioInit:
    def test_single_provider(self):
        m = Memio(facts=FakeFactStore())
        assert m.facts is not None
        assert m.history is None
        assert m.documents is None
        assert m.graph is None

    def test_all_providers(self):
        m = Memio(
            facts=FakeFactStore(),
            history=FakeHistoryStore(),
            documents=FakeDocumentStore(),
            graph=FakeGraphStore(),
        )
        assert m.facts is not None
        assert m.history is not None
        assert m.documents is not None
        assert m.graph is not None

    def test_no_providers_raises(self):
        with pytest.raises(ValueError, match="At least one memory store"):
            Memio()

    def test_invalid_facts_type_raises(self):
        with pytest.raises(TypeError, match="facts must implement FactStore"):
            Memio(facts="not a store")

    def test_invalid_history_type_raises(self):
        with pytest.raises(TypeError, match="history must implement HistoryStore"):
            Memio(history="not a store")

    def test_invalid_documents_type_raises(self):
        with pytest.raises(TypeError, match="documents must implement DocumentStore"):
            Memio(documents="not a store")

    def test_invalid_graph_type_raises(self):
        with pytest.raises(TypeError, match="graph must implement GraphStore"):
            Memio(graph="not a store")


class TestMemioUsage:
    async def test_facts_namespace(self):
        m = Memio(facts=FakeFactStore())
        fact = await m.facts.add(content="likes coffee", user_id="u1")
        assert fact.content == "likes coffee"

    async def test_history_namespace(self):
        m = Memio(history=FakeHistoryStore())
        msgs = await m.history.get(session_id="s1")
        assert msgs == []

    async def test_documents_namespace(self):
        m = Memio(documents=FakeDocumentStore())
        doc = await m.documents.add(content="guide")
        assert doc.content == "guide"

    async def test_graph_namespace(self):
        m = Memio(graph=FakeGraphStore())
        result = await m.graph.search(query="Alice")
        assert isinstance(result, GraphResult)
