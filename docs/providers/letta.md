# Letta

[Letta](https://letta.com) (formerly MemGPT) is a platform for building stateful
AI agents with persistent memory. memio provides three adapters for Letta.

## Installation

```bash
pip install memio[letta]
```

This installs the `letta-client` package as a dependency.

## Setup

Letta supports two deployment modes:

| Mode | Setup |
|---|---|
| **Letta Cloud** | Sign up at [app.letta.com](https://app.letta.com), get an API key at [app.letta.com/api-keys](https://app.letta.com/api-keys). |
| **Self-hosted** | Run `docker run -p 8283:8283 -e OPENAI_API_KEY=... letta/letta:latest`. No Letta API key needed. |

All adapters require an `agent_id`. Create an agent via the SDK:

```python
from letta_client import Letta

# Cloud
client = Letta(api_key="your-letta-api-key")
# Self-hosted
# client = Letta(base_url="http://localhost:8283")

agent = client.agents.create(
    model="openai/gpt-4.1",
    memory_blocks=[{"label": "human", "value": "Name: user"}],
)
print(agent.id)  # use this as agent_id
```

## Supported stores

| Store | Adapter class |
|---|---|
| FactStore | `LettaFactAdapter` |
| HistoryStore | `LettaHistoryAdapter` |
| DocumentStore | `LettaDocumentAdapter` |

GraphStore is not supported — Letta has no knowledge graph.

## FactStore -- LettaFactAdapter

Maps memio facts to Letta archival passages (agent-scoped).

```python
from memio import Memio
from memio.providers.letta import LettaFactAdapter

client = Memio(
    facts=LettaFactAdapter(api_key="letta-xxx", agent_id="agent-123"),
)

fact = await client.facts.add(content="likes coffee", user_id="alice")
results = await client.facts.search(query="coffee", user_id="alice")
await client.facts.delete(fact_id=fact.id)
```

### Update behavior

Letta's passages API has no native update. The adapter emulates update via
delete + create. This means the passage ID changes after an update:

```python
updated = await client.facts.update(fact_id=fact.id, content="likes tea")
assert updated.id != fact.id  # new ID assigned
```

## HistoryStore -- LettaHistoryAdapter

Maps memio sessions to Letta conversations. Sending messages triggers the
agent to process and respond.

```python
from memio import Memio, Message
from memio.providers.letta import LettaHistoryAdapter

client = Memio(
    history=LettaHistoryAdapter(api_key="letta-xxx", agent_id="agent-123"),
)

await client.history.add(
    session_id="session-1",
    user_id="alice",
    messages=[Message(role="user", content="hello")],
)
messages = await client.history.get(session_id="session-1")
```

The adapter filters messages to only return user and assistant messages,
excluding internal types (reasoning, tool calls, system messages).

## DocumentStore -- LettaDocumentAdapter

Maps memio documents to Letta archival passages, the same underlying API
as FactStore but oriented toward longer content.

```python
from memio import Memio
from memio.providers.letta import LettaDocumentAdapter

client = Memio(
    documents=LettaDocumentAdapter(api_key="letta-xxx", agent_id="agent-123"),
)

doc = await client.documents.add(content="deployment guide for production")
results = await client.documents.search(query="deployment")
await client.documents.delete(doc_id=doc.id)
```

Update behavior is the same as FactStore (delete + create, ID changes).

## Self-hosted example

```python
from memio import Memio
from memio.providers.letta import LettaFactAdapter, LettaHistoryAdapter, LettaDocumentAdapter

kwargs = {"base_url": "http://localhost:8283", "agent_id": "agent-123"}

client = Memio(
    facts=LettaFactAdapter(**kwargs),
    history=LettaHistoryAdapter(**kwargs),
    documents=LettaDocumentAdapter(**kwargs),
)
```
