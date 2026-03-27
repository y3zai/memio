from memio.models import Document
from memio.protocols import DocumentStore


async def document_store_conformance(store: DocumentStore) -> None:
    # Clean up leftover data from previous runs
    await store.delete_all()

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

    # Test get_all
    all_docs = await store.get_all()
    assert isinstance(all_docs, list)
    assert any(d.id == doc.id for d in all_docs)

    await store.delete(doc_id=doc.id)
    after_delete = await store.search(query="updated deployment")
    assert all(d.id != doc.id for d in after_delete)

    # Test delete_all
    await store.add(content="bulk doc one")
    await store.add(content="bulk doc two")
    await store.delete_all()
    remaining = await store.get_all()
    assert len(remaining) == 0
