# MCP Protocol Reference Notes

## Transport Layer

MCP is transport-agnostic. The three supported transports are:

| Transport | Use case |
|---|---|
| **stdio** | Local tool servers launched as subprocesses (Claude Desktop) |
| **HTTP + SSE** | Remote servers, containerised deployments (this project) |
| **WebSocket** | Bidirectional streaming (future) |

This project uses **HTTP + SSE** (Server-Sent Events for streaming responses).

## JSON-RPC 2.0 Envelope

Every MCP message is a JSON-RPC 2.0 object:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": { ... }
}
```

Responses:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { ... }
}
```

Errors:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": { "detail": "..." }
  }
}
```

## Standard Error Codes

| Code | Meaning |
|---|---|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

## Protocol Version

Current stable version: `2024-11-05`

The client sends its supported version in `initialize`. The server responds
with the version it will use. If versions are incompatible, the server
returns an error and closes the session.

## Full Handshake Sequence
```
Client                          Server
  |                               |
  |---- initialize -------------->|
  |<--- initialize result --------|
  |                               |
  |---- notifications/initialized>|  (client confirms ready)
  |                               |
  |---- tools/list -------------->|
  |<--- tools/list result --------|
  |                               |
  |---- tools/call --------------->|
  |<--- tools/call result ---------|
```

## Tool Input Schema Constraints

- Must be valid JSON Schema Draft 7
- Top-level type must be `object`
- `required` array must list all non-optional fields
- Descriptions are passed verbatim to the LLM — write them as instructions

## Key Difference from LangChain Tool Calling

In LangChain, tools are Python classes imported at agent build time.
The agent has no way to pick up new tools without a code change and redeploy.

In MCP, the server is the source of truth for tool definitions. The agent
calls `tools/list` at runtime and dynamically constructs callable wrappers.
New tools can be added to the registry YAML and the agent picks them up on
next session — zero agent code changes required.