from memio.models import Document
from memio.protocols import DocumentStore


async def document_store_conformance(store: DocumentStore) -> None:
    doc = await store.add(content="deployment guide for production", metadata={"type": "docs"})
    assert isinstance(doc, Document)
    assert doc.id is not None
    assert doc.content == "deployment guide for production"
    retrieved = await store.get(doc_id=doc.id)
    assert retrieved.id == doc.id
    assert retrieved.content == "deployment guide for production"
    results = await store.search(query="deployment")
    assert isinstance(results, list)
    assert any(d.id == doc.id for d in results)
    updated = await store.update(doc_id=doc.id, content="updated deployment guide")
    assert updated.content == "updated deployment guide"
    await store.delete(doc_id=doc.id)
    after_delete = await store.search(query="updated deployment")
    assert all(d.id != doc.id for d in after_delete)
