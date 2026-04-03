"""
MCP JSON-RPC 2.0 Router
------------------------
Handles all MCP protocol messages arriving at POST /mcp.

Methods implemented here:
  initialize                  — version negotiation, capability exchange
  notifications/initialized   — client ready confirmation (no response)
  tools/list                  — return tool manifest from registry
  tools/call                  — route to tool handler (v0.4.0+)

Wire format: JSON-RPC 2.0 over HTTP POST.
Every request body is a single JSON-RPC message object.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mcp_server.registry.registry_loader import get_registry

logger = logging.getLogger("mcp_server.router")

router = APIRouter()

# ── Protocol constants ───────────────────────────────────────────────────────
MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "mcp-tool-server", "version": "0.3.0"}


# ── JSON-RPC helpers ─────────────────────────────────────────────────────────


def ok(id: Any, result: dict) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": id,
            "result": result,
        }
    )


def error(id: Any, code: int, message: str, data: dict | None = None) -> JSONResponse:
    err: dict[str, Any] = {"code": code, "message": message}
    if data:
        err["data"] = data
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": id,
            "error": err,
        }
    )


def parse_error() -> JSONResponse:
    return error(None, -32700, "Parse error")


def invalid_request(id: Any, detail: str) -> JSONResponse:
    return error(id, -32600, "Invalid Request", {"detail": detail})


def method_not_found(id: Any, method: str) -> JSONResponse:
    return error(
        id,
        -32601,
        "Method not found",
        {"detail": f"'{method}' is not a supported MCP method."},
    )


# ── Main MCP endpoint ────────────────────────────────────────────────────────


@router.post("/mcp", tags=["mcp"])
async def mcp_endpoint(request: Request) -> JSONResponse:
    """
    Single entry point for all MCP JSON-RPC messages.
    Dispatches by 'method' field.
    """
    # Parse body
    try:
        body = await request.json()
    except Exception:
        return parse_error()

    # Validate envelope
    if not isinstance(body, dict):
        return parse_error()

    if body.get("jsonrpc") != "2.0":
        return invalid_request(
            body.get("id"),
            "jsonrpc field must be '2.0'",
        )

    method = body.get("method")
    msg_id = body.get("id")  # None for notifications
    params = body.get("params", {})

    if not method:
        return invalid_request(msg_id, "Missing 'method' field.")

    logger.info(f"MCP ← method={method} id={msg_id}")
    t0 = time.perf_counter()

    # Dispatch
    response = await _dispatch(method, msg_id, params)

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info(f"MCP → method={method} id={msg_id} elapsed={elapsed:.1f}ms")

    return response


# ── Method handlers ──────────────────────────────────────────────────────────


async def _dispatch(method: str, msg_id: Any, params: dict) -> JSONResponse:
    match method:
        case "initialize":
            return await _handle_initialize(msg_id, params)
        case "notifications/initialized":
            return await _handle_notifications_initialized()
        case "tools/list":
            return await _handle_tools_list(msg_id)
        case "tools/call":
            return await _handle_tools_call(msg_id, params)
        case _:
            return method_not_found(msg_id, method)


async def _handle_initialize(msg_id: Any, params: dict) -> JSONResponse:
    """
    Version negotiation and capability exchange.
    Client sends its protocol version; server responds with its own.
    If the client sends an unsupported version we still respond — it is
    the client's responsibility to abort if versions are incompatible.
    """
    client_version = params.get("protocolVersion", "unknown")
    client_info = params.get("clientInfo", {})

    logger.info(
        f"initialize: client={client_info.get('name', 'unknown')} "
        f"version={client_version}"
    )

    return ok(
        msg_id,
        {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": True,  # server can notify when tool list changes
                },
            },
            "serverInfo": SERVER_INFO,
        },
    )


async def _handle_notifications_initialized() -> JSONResponse:
    """
    Client confirms session is ready.
    Returns empty JSON object — keeps HTTP connection alive for subsequent requests.
    """
    logger.info("notifications/initialized received — session active.")
    return JSONResponse(content={}, status_code=200)


async def _handle_tools_list(msg_id: Any) -> JSONResponse:
    """
    Return the full tool manifest from the registry.
    Only enabled tools are included.
    This is the response the LangGraph agent uses to discover tools
    at runtime — the agent never has tool definitions hardcoded.
    """
    registry = get_registry()
    tools = registry.to_mcp_list()
    logger.info(f"tools/list: returning {len(tools)} tools")
    return ok(msg_id, {"tools": tools})


async def _handle_tools_call(msg_id: Any, params: dict) -> JSONResponse:
    """
    Tool execution — implemented fully in v0.4.0.
    Returns a clear not-implemented error for now so the handshake
    tests can run without blocking on tool handler code.
    """
    tool_name = params.get("name", "unknown")
    logger.warning(f"tools/call received for '{tool_name}' — not yet implemented.")
    return error(
        msg_id,
        -32601,
        "Method not fully implemented",
        {"detail": f"tools/call for '{tool_name}' will be available in v0.4.0."},
    )
