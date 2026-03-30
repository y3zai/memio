# REST API Server

memio includes an optional REST API server that exposes all memory stores over HTTP.
This lets **any language** (JavaScript, TypeScript, Go, Rust, etc.) use memio — not just Python.

## Installation

```bash
pip install memio[server]
```

This adds FastAPI, Uvicorn, and PyYAML. You also need the providers you want to use:

```bash
pip install memio[server,mem0,zep,chroma]
```

## Quick Start

1. Create a config file `memio-server.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 8080

stores:
  facts:
    provider: mem0
    config:
      api_key: "${MEM0_API_KEY}"

  documents:
    provider: chroma
    config:
      collection_name: "my-docs"
```

2. Start the server:

```bash
# Set provider API keys
export MEM0_API_KEY=your-key

# Start
python -m memio.server
# or
memio-server
```

3. Open [http://localhost:8080/docs](http://localhost:8080/docs) for interactive API docs.

## Configuration

### Config file

The server reads `memio-server.yaml` by default. Override with the `MEMIO_CONFIG` env var:

```bash
MEMIO_CONFIG=/path/to/config.yaml memio-server
```

String values support `${ENV_VAR}` interpolation. **Unresolved variables cause a startup error** (fail-fast).

### Environment variable overrides

| Env var | Overrides | Default |
|---------|-----------|---------|
| `MEMIO_HOST` | `server.host` | `127.0.0.1` |
| `MEMIO_PORT` | `server.port` | `8080` |
| `MEMIO_API_KEY` | `auth.api_key` | disabled |
| `MEMIO_CONFIG` | config file path | `memio-server.yaml` |

### Authentication

Set `MEMIO_API_KEY` to enable Bearer token auth:

```bash
export MEMIO_API_KEY=my-secret-key
```

Clients must include `Authorization: Bearer my-secret-key` in every request.
When unset, auth is disabled.

!!! warning "Security"
    The default host is `127.0.0.1` (localhost only). If you bind to `0.0.0.0` for
    network access, put the server behind a **TLS-terminating reverse proxy**
    (nginx, Caddy, cloud load balancer).

## API Endpoints

All endpoints are under `/v1`. Interactive docs are at `/docs`.

### Facts — `/v1/facts`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/facts` | Create a fact |
| `GET` | `/v1/facts` | List facts |
| `GET` | `/v1/facts/{fact_id}` | Get a fact |
| `PUT` | `/v1/facts/{fact_id}` | Update a fact |
| `DELETE` | `/v1/facts/{fact_id}` | Delete a fact |
| `DELETE` | `/v1/facts` | Delete all facts |
| `POST` | `/v1/facts/search` | Semantic search |

### History — `/v1/history`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/history/sessions/{sid}/messages` | Add messages |
| `GET` | `/v1/history/sessions/{sid}/messages` | Get messages |
| `GET` | `/v1/history/sessions` | List sessions |
| `POST` | `/v1/history/sessions/{sid}/search` | Search session |
| `DELETE` | `/v1/history/sessions/{sid}` | Delete session |
| `DELETE` | `/v1/history/sessions` | Delete all sessions |

### Documents — `/v1/documents`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/documents` | Create a document |
| `GET` | `/v1/documents` | List documents |
| `GET` | `/v1/documents/{doc_id}` | Get a document |
| `PUT` | `/v1/documents/{doc_id}` | Update a document |
| `DELETE` | `/v1/documents/{doc_id}` | Delete a document |
| `DELETE` | `/v1/documents` | Delete all documents |
| `POST` | `/v1/documents/search` | Semantic search |

### Graph — `/v1/graph`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/graph/triples` | Add triples |
| `GET` | `/v1/graph/triples` | List all triples |
| `GET` | `/v1/graph/entities/{entity}` | Get entity triples |
| `POST` | `/v1/graph/search` | Semantic search |
| `DELETE` | `/v1/graph/entities/{entity}` | Delete by entity |
| `DELETE` | `/v1/graph/triples/{triple_id}` | Delete by triple ID |
| `DELETE` | `/v1/graph` | Delete all graph data |

## Usage from JavaScript/TypeScript

```typescript
const MEMIO_URL = "http://localhost:8080";

// Add a fact
const fact = await fetch(`${MEMIO_URL}/v1/facts`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    content: "prefers dark mode",
    user_id: "alice",
  }),
}).then(r => r.json());

// Search facts
const results = await fetch(`${MEMIO_URL}/v1/facts/search`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query: "preferences", user_id: "alice" }),
}).then(r => r.json());

// Add conversation history
await fetch(`${MEMIO_URL}/v1/history/sessions/session-1/messages`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [
      { role: "user", content: "hello" },
      { role: "assistant", content: "hi there" },
    ],
  }),
});
```

## Error Responses

| HTTP Status | Meaning |
|-------------|---------|
| 404 | Resource not found |
| 422 | Validation error (bad request body) |
| 501 | Store not configured, or operation not supported by provider |
| 502 | Upstream provider failed |

All error responses have this shape:

```json
{
  "error": "not_found",
  "detail": "fact 'xyz' not found",
  "provider": null,
  "operation": null
}
```

## Docker

```bash
docker build -t memio-server .
docker run -p 8080:8080 \
  -e MEM0_API_KEY=your-key \
  -e MEMIO_HOST=0.0.0.0 \
  -v ./memio-server.yaml:/app/memio-server.yaml \
  memio-server
```
