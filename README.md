# MCP Enterprise Tool Orchestration Server

## Why This Exists

LangChain tools are hardcoded at agent build time — if you add a new tool,
you redeploy the agent. MCP (Model Context Protocol) solves this by
standardising how agents *discover* tools at runtime from a live server.
This project implements a production-grade MCP server exposing real enterprise
tools (SQL, filesystem, web search), consumed by a LangGraph agent that builds
its tool list dynamically from the running server — no redeploy needed.

## Architecture

> Diagram added at v0.3.0 — see docs/architecture.md

## Quick Start (Local Demo — zero cost)
```bash
# 1. Copy env template
cp .env.example .env
# Fill GROQ_API_KEY and JWT_SECRET in .env

# 2. Seed the database
make seed-db

# 3. Start the MCP server
make run-local

# 4. In a second terminal — run the agent
make run-agent-local

# 5. In a third terminal — open the UI
make run-ui
```

## Stack

| Layer | Local Demo | Production |
|---|---|---|
| LLM | Groq llama3-8b (free) | Azure OpenAI GPT-4o |
| Database | SQLite | Azure SQL |
| File store | Local filesystem | Azure Blob Storage |
| Web search | DuckDuckGo (no key) | Azure Bing Search |
| Auth | PyJWT HS256 | Azure AD OAuth 2.0 |
| Deploy | Docker local | Azure Container Apps |

## Known Limitations

> To be filled as real limits are discovered during build.
> Placeholder — will not leave this empty at v1.0.0.

- [ ] TBD

## Tradeoffs Made

> Explicit tradeoffs documented here so they can be discussed in interviews.

- [ ] TBD

## What I Tried That Didn't Work

- **DuckDuckGo retry with same session:** First retry attempt reused the same
  DDGS() instance after a RatelimitException. The internal state is poisoned
  after a rate limit hit — the library raises DuckDuckGoSearchException on the
  next call regardless of sleep duration. Fixed by creating a fresh DDGS()
  instance for the retry. Still blocked by IP-level throttling during sustained
  development testing — production path is Azure Bing Search.