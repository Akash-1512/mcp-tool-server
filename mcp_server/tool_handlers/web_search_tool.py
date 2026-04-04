from __future__ import annotations

import json
import logging

from duckduckgo_search import DDGS

from mcp_server.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)

# LOCAL DEMO — DuckDuckGo free API, no key required
# Rate limit: ~1 request/sec safe. Do not hammer in tests.
_DEFAULT_MAX_RESULTS = 5
_MAX_RESULTS_CEILING = 10

# ─────────────────────────────────────────────────────────────────────────────
# [PRODUCTION] Azure Bing Search — uncomment to enable
# Requires: AZURE_BING_SEARCH_KEY in .env
# ─────────────────────────────────────────────────────────────────────────────
# import httpx, os
# async def _bing_search(query: str, max_results: int) -> list[dict]:
#     headers = {"Ocp-Apim-Subscription-Key": os.getenv("AZURE_BING_SEARCH_KEY")}
#     params = {"q": query, "count": max_results, "mkt": "en-US"}
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             "https://api.bing.microsoft.com/v7.0/search",
#             headers=headers,
#             params=params,
#             timeout=10.0,
#         )
#         response.raise_for_status()
#         data = response.json()
#         return [
#             {"title": r["name"], "url": r["url"], "snippet": r["snippet"]}
#             for r in data.get("webPages", {}).get("value", [])
#         ]


# ─── Handler ──────────────────────────────────────────────────────────────────

async def handle_web_search(arguments: dict) -> str:
    """Search the web via DuckDuckGo and return top results as JSON.

    Called by the MCP dispatch endpoint when tool name is 'web_search_tool'.
    Returns a JSON list of result objects, each with:
        - title: page title
        - url: page URL
        - snippet: short description excerpt

    Raises:
        ToolExecutionError: if query is missing/empty or DuckDuckGo call fails
    """
    query = arguments.get("query")
    if not query or not query.strip():
        raise ToolExecutionError(
            tool_name="web_search_tool",
            message="Required argument 'query' is missing or empty",
        )

    max_results = arguments.get("max_results", _DEFAULT_MAX_RESULTS)
    if not isinstance(max_results, int) or max_results < 1:
        max_results = _DEFAULT_MAX_RESULTS
    max_results = min(max_results, _MAX_RESULTS_CEILING)

    logger.info(
        "web_search_tool querying DuckDuckGo: '%s' (max_results=%d)",
        query,
        max_results,
    )

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        raise ToolExecutionError(
            tool_name="web_search_tool",
            message=f"DuckDuckGo search failed: {type(e).__name__}: {e}",
        ) from e

    web_search_results = [
        {
            "title": result.get("title", ""),
            "url": result.get("href", ""),
            "snippet": result.get("body", "")[:300],
        }
        for result in raw_results
    ]

    logger.info(
        "web_search_tool returned %d results for query '%s'",
        len(web_search_results),
        query,
    )

    return json.dumps(web_search_results)