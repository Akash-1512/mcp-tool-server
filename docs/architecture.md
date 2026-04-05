# System Architecture

## Component Status

| Component | Status |
|---|---|
| MCP Server (FastAPI) | ✅ v0.3.0 |
| Tool Registry (YAML) | ✅ v0.3.0 |
| sql_query_tool | ✅ v0.4.0 |
| file_search_tool | ✅ v0.5.0 |
| web_search_tool | ✅ v0.6.0 |
| JWT Auth Middleware | ✅ v0.7.0 |
| LangGraph Agent | ✅ v0.8.0 |
| Streamlit UI | ✅ v0.9.0 |
| Docker + CI/CD | ✅ v1.0.0 |

## MCP Protocol Flow

```
Agent startup:
  POST /tools/list → {jsonrpc, id, method, params:{}}
  ← {result: {tools: [{name, description, inputSchema}]}}

Agent tool call:
  POST /tools/call → {jsonrpc, id, method, params:{name, arguments}}
  ← {result: {content:[{type,text}], isError:bool}}

Auth: every request carries Authorization: Bearer <JWT>
JWT: HS256 signed, verified on every request before routing
```

## Data Flow

```
User query → Streamlit UI
  → LangGraph agent_node (Groq LLM decides tool call)
  → call_mcp_tool() (HTTP POST /tools/call with JWT)
  → MCP dispatcher (get_tool() → handler)
  → sql_tool / file_search_tool / web_search_tool
  → real SQLite / filesystem / DuckDuckGo
  → result back up the chain
  → synthesize_node (Groq LLM generates final answer)
  → Streamlit UI displays response
```