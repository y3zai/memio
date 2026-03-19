from datetime import datetime
from memio.models import Fact, Message, Document, Triple, GraphResult


class TestFact:
    def test_required_fields(self):
        fact = Fact(id="f1", content="likes coffee")
        assert fact.id == "f1"
        assert fact.content == "likes coffee"

    def test_optional_fields_default_none(self):
        fact = Fact(id="f1", content="likes coffee")
        assert fact.user_id is None
        assert fact.agent_id is None
        assert fact.metadata is None
        assert fact.score is None
        assert fact.created_at is None
        assert fact.updated_at is None

    def test_all_fields(self):
        now = datetime.now()
        fact = Fact(
            id="f1", content="likes coffee", user_id="u1",
            agent_id="a1", metadata={"source": "chat"},
            score=0.95, created_at=now, updated_at=now,
        )
        assert fact.user_id == "u1"
        assert fact.score == 0.95


class TestMessage:
    def test_required_fields(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_optional_fields_default_none(self):
        msg = Message(role="user", content="hello")
        assert msg.metadata is None
        assert msg.timestamp is None
        assert msg.name is None


class TestDocument:
    def test_required_fields(self):
        doc = Document(id="d1", content="deploy guide")
        assert doc.id == "d1"
        assert doc.content == "deploy guide"

    def test_optional_fields_default_none(self):
        doc = Document(id="d1", content="deploy guide")
        assert doc.metadata is None
        assert doc.score is None
        assert doc.created_at is None
        assert doc.updated_at is None


class TestTriple:
    def test_required_fields(self):
        t = Triple(subject="Alice", predicate="works_at", object="Acme")
        assert t.subject == "Alice"
        assert t.predicate == "works_at"
        assert t.object == "Acme"

    def test_optional_metadata(self):
        t = Triple(subject="A", predicate="B", object="C")
        assert t.metadata is None


class TestGraphResult:
    def test_defaults_empty(self):
        r = GraphResult()
        assert r.triples == []
        assert r.nodes == []
        assert r.scores == []

    def test_with_data(self):
        t = Triple(subject="A", predicate="B", object="C")
        r = GraphResult(triples=[t], nodes=["A", "C"], scores=[0.9])
        assert len(r.triples) == 1
        assert r.nodes == ["A", "C"]
