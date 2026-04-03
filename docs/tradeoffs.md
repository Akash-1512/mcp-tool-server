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

> TBD — added at Phase 2, Step 2.3

## Groq vs Azure OpenAI

> TBD — added at Phase 4