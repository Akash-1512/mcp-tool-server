# Tradeoffs Made — Design Decisions

> Every infrastructure tradeoff documented here so it can be
> discussed authoritatively in senior AI engineer interviews.

## SQLite vs PostgreSQL / Azure SQL

**Chose:** SQLite for local demo
**Reason:** Zero infrastructure, reproducible via seed.sql, enough for demo queries
**Production path:** Azure SQL — connection string swap, no query changes needed
**What you give up:** No concurrent writes, no row-level locking at scale

## PyJWT HS256 vs Azure AD OAuth 2.0

> TBD — added at Phase 3

## DuckDuckGo vs Azure Bing Search

**Chose:** DuckDuckGo free API for local demo
**Reason:** Zero cost, no API key, no Azure subscription needed for demo
**Production path:** Azure Bing Search — AZURE_BING_SEARCH_KEY swap, no logic changes
**What you give up:** No SLA, aggressive IP-level rate limiting during development,
primp browser impersonation profiles missing in duckduckgo-search v6.4.2 causing
random UA selection which contributes to throttling

## Groq vs Azure OpenAI

**Chose:** Groq free tier (llama3-8b-8192) for local demo
**Reason:** Zero cost, fast inference, no Azure subscription needed
**Production path:** Azure OpenAI GPT-4o — uncomment block in agent/langgraph_agent.py
**What you give up:** Groq free tier has rate limits and no guaranteed uptime SLA