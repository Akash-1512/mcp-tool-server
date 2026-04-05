# MCP Enterprise Tool Orchestration Server

## Why This Exists

LangChain tools are hardcoded at agent build time — adding a tool means
redeploying the agent. MCP (Model Context Protocol) solves this by
standardising how agents discover tools at runtime from a live server.
This project implements a production-grade MCP server exposing real enterprise
tools (SQL, filesystem, web search), consumed by a LangGraph agent that builds
its tool list dynamically from the running server — no redeploy needed.

## Architecture

```
┌─────────────────┐     JWT + JSON-RPC      ┌──────────────────────┐
│  LangGraph      │ ──── /tools/list ──────▶ │  MCP Server          │
│  Agent          │ ◀─── tool definitions ── │  (FastAPI)           │
│                 │                          │                      │
│  Runtime tool   │ ──── /tools/call ──────▶ │  Tool Registry       │
│  discovery      │ ◀─── tool result ─────── │  (YAML-driven)       │
└─────────────────┘                          └──────────┬───────────┘
                                                        │
                                          ┌─────────────┼─────────────┐
                                          ▼             ▼             ▼
                                       SQLite      Filesystem    DuckDuckGo
                                      (IT Assets)   (files/)     (web search)
```

## Quick Start (Local Demo — zero cost)

```bash
# 1. Clone and install
git clone https://github.com/Akash-1512/mcp-tool-server.git
cd mcp-tool-server
pip install -r requirements.txt

# 2. Copy env template and fill GROQ_API_KEY and JWT_SECRET
cp .env.example .env

# 3. Seed the database
python -c "import sqlite3, pathlib; conn = sqlite3.connect('data/enterprise.db'); \
conn.executescript(pathlib.Path('data/seed.sql').read_text()); conn.commit(); conn.close()"

# 4. Start MCP server
uvicorn mcp_server.main:app --port 8003

# 5. In a second terminal — run the Streamlit UI
streamlit run ui/chat_ui.py
```

## Stack

| Layer | Local Demo | Production |
|---|---|---|
| LLM | Groq llama-3.1-8b-instant (free) | Azure OpenAI GPT-4o |
| Database | SQLite | Azure SQL |
| File store | Local filesystem | Azure Blob Storage |
| Web search | DuckDuckGo (no key) | Azure Bing Search |
| Auth | PyJWT HS256 | Azure AD OAuth 2.0 |
| Deploy | Docker local | Azure Container Apps |

## Project Status

| Milestone | Version | Status |
|---|---|---|
| Repo scaffold | v0.1.0 | ✅ |
| IT Asset seed data | v0.2.0 | ✅ |
| MCP server core | v0.3.0 | ✅ |
| sql_query_tool | v0.4.0 | ✅ |
| file_search_tool | v0.5.0 | ✅ |
| web_search_tool | v0.6.0 | ✅ |
| JWT auth | v0.7.0 | ✅ |
| LangGraph agent | v0.8.0 | ✅ |
| Streamlit UI | v0.9.0 | ✅ |
| CI/CD + docs | v1.0.0 | ✅ |

## Known Limitations

- DuckDuckGo rate-limits aggressively on repeated calls from the same IP.
  The retry logic handles transient limits but sustained testing requires
  Azure Bing Search (production path commented in code).
- SQLite has no concurrent write support — WAL mode noted as FIXME in sql_tool.py.
- llama-3.1-8b-instant requires explicit schema + example query in system
  prompt to generate correct JOIN syntax. GPT-4o does not have this limitation.
- tool_call_trace in AgentState is not yet populated — UI trace panel
  shows empty. Planned for next iteration.

## Tradeoffs Made

See [docs/tradeoffs.md](docs/tradeoffs.md) for full tradeoff documentation.

- **SQLite vs Azure SQL:** Zero infrastructure for demo, seed.sql ensures
  reproducibility. WAL mode needed for concurrent reads at scale.
- **PyJWT HS256 vs Azure AD:** Symmetric key fine for demo. Production
  requires RS256 with Azure AD JWKS endpoint verification.
- **DuckDuckGo vs Azure Bing:** Free, no key. Unreliable under load —
  Azure Bing has SLA and proper rate limits.
- **llama-3.1-8b-instant vs GPT-4o:** Free tier, fast. Requires more
  explicit prompting for correct SQL generation.

## What I Tried That Didn't Work

- **DuckDuckGo retry with same session:** Reusing a DDGS() instance after
  RatelimitException poisons the internal state. Fixed by creating a fresh
  instance for retry — still blocked by IP-level throttling during sustained
  development testing.
- **llama3-8b-8192:** Decommissioned by Groq mid-build. Switched to
  llama-3.1-8b-instant.
- **StructuredTool without args_schema:** LangChain sends empty arguments
  to tools without an explicit Pydantic schema. Fixed by building a dynamic
  schema via create_model() from the MCP inputSchema properties.
- **Agent looping without synthesize node:** Small models call tools
  repeatedly without producing a final answer. Fixed with a dedicated
  synthesize node that forces answer generation after 3 tool calls.