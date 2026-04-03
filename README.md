# MCP Enterprise Tool Orchestration Server

A production-grade implementation of an **MCP (Model Context Protocol) server**
that exposes enterprise tools — SQL query, REST search, filesystem search, web
search — as MCP-compatible endpoints, consumed by a LangGraph agent with runtime
tool discovery.

---

## What is MCP?

Model Context Protocol (MCP) is an open standard (introduced by Anthropic, 2024)
that defines how AI models discover and call external tools in a structured,
transport-agnostic way. Think of it as **OpenAPI for agent tool use** — but with
first-class support for resources, prompts, and streaming.

### The Problem MCP Solves

| Pain Point | Without MCP | With MCP |
|---|---|---|
| Tool definitions | Hardcoded per agent | Declared once, discovered at runtime |
| Transport | HTTP only | HTTP, stdio, WebSocket |
| Schema | Ad hoc JSON | Strongly typed JSON Schema |
| Discovery | Manual import | `tools/list` handshake |
| Versioning | None | Protocol version negotiation |

### Core Concepts

**Tools** — Callable functions with typed inputs/outputs. Agents invoke these.
Example: `sql_query`, `web_search`.

**Resources** — Read-only data sources the model can reference (files, DB rows).
Example: `resource://schema/customers`.

**Prompts** — Reusable prompt templates stored server-side, parameterised by the
client. Example: `prompt://summarise-query-result`.

### The MCP Discovery Handshake

Every MCP session begins with a two-message handshake:

**1. Client → Server: `initialize`**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "tools": {}, "resources": {} },
    "clientInfo": { "name": "langgraph-agent", "version": "1.0.0" }
  }
}
```

**2. Server → Client: `initialize` response**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "tools": { "listChanged": true } },
    "serverInfo": { "name": "mcp-tool-server", "version": "0.1.0" }
  }
}
```

**3. Client → Server: `tools/list`**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**4. Server → Client: tool manifest**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "sql_query",
        "description": "Execute a read-only SQL query against the enterprise database.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": { "type": "string", "description": "SQL SELECT statement" }
          },
          "required": ["query"]
        }
      }
    ]
  }
}
```

**5. Agent calls a tool: `tools/call`**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "sql_query",
    "arguments": { "query": "SELECT * FROM orders WHERE status = 'pending' LIMIT 10" }
  }
}
```

### MCP vs OpenAPI vs LangChain Tools

| Dimension | OpenAPI | LangChain Tools | MCP |
|---|---|---|---|
| Discovery | Static spec file | Import at build time | Runtime handshake |
| Transport | HTTP only | In-process | HTTP, stdio, WS |
| Tool schema | OAS 3.x | Pydantic class | JSON Schema |
| Auth | Per-spec | Per-tool | Middleware layer |
| Streaming | Limited | No | Native |
| Standard body | OpenAPI consortium | LangChain internal | Anthropic + community |

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full Mermaid diagram.

---

## Tool Registry

Tools are declared declaratively in [`mcp_server/registry/tool_registry.yaml`](mcp_server/registry/tool_registry.yaml).
See [`docs/tool_registry.md`](docs/tool_registry.md) for full schema documentation.

---

## Quick Start
```bash
cp .env.example .env          # fill in your secrets
docker-compose up --build     # starts db, mcp-server, agent
```

---

## Milestones

| Tag | Description |
|---|---|
| v0.1.0 | Repo init, docker skeleton |
| v0.2.0 | YAML tool registry |
| v0.3.0 | MCP discovery handshake |
| v0.4.0 | SQL query tool |
| v0.5.0 | JWT auth middleware |
| v0.6.0 | LangGraph agent with runtime discovery |
| v0.7.0 | All tools + integration tests |
| v0.8.0 | Streamlit UI |
| v1.0.0 | Azure Container Apps deployment |

---

## License

MIT