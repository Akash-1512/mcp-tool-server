from __future__ import annotations

import logging
import os

import httpx

from mcp_server.auth.token_generator import generate_token

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8003")


def discover_tools() -> list[dict]:
    """Call the MCP server's /tools/list endpoint and return tool definitions.

    Called once at agent startup — not on every query. The returned list
    is stored in AgentState.discovered_tools and used to build LangChain
    tool wrappers dynamically.

    Returns:
        List of tool definition dicts, each with keys:
        name, description, inputSchema

    Raises:
        RuntimeError: if the server is unreachable or returns non-200
    """
    token = generate_token(subject="langgraph-agent")
    headers = {"Authorization": f"Bearer {token}"}

    logger.info("Discovering tools from MCP server at %s", MCP_SERVER_URL)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{MCP_SERVER_URL}/tools/list",
                headers=headers,
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            )
    except httpx.ConnectError as e:
        raise RuntimeError(
            f"Cannot connect to MCP server at {MCP_SERVER_URL}. "
            "Is the server running? Run: python -m uvicorn mcp_server.main:app --port 8003"
        ) from e
    except httpx.TimeoutException as e:
        raise RuntimeError(
            f"MCP server at {MCP_SERVER_URL} timed out during tool discovery"
        ) from e

    if response.status_code == 401:
        raise RuntimeError(
            "MCP server rejected agent token during discovery — check JWT_SECRET"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"MCP /tools/list returned unexpected status {response.status_code}: "
            f"{response.text[:200]}"
        )

    discovery_response = response.json()
    tool_definitions = discovery_response.get("result", {}).get("tools", [])

    logger.info("Discovered %d tools from MCP server", len(tool_definitions))
    for tool_def in tool_definitions:
        logger.info("  → %s", tool_def.get("name"))

    return tool_definitions