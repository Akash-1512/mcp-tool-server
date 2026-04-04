from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from mcp_server.exceptions import RegistryLoadError
from mcp_server.registry.registry_loader import load_registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
# FastAPI lifespan replaces deprecated @app.on_event("startup").
# load_registry() runs before the server accepts any requests.
# If it raises, uvicorn exits — better than serving with a broken registry.

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MCP Tool Server starting up...")
    try:
        load_registry()
        logger.info("Tool registry loaded — server ready")
    except RegistryLoadError as e:
        logger.error("STARTUP FAILED — tool registry could not be loaded: %s", e)
        raise
    yield
    logger.info("MCP Tool Server shutting down")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MCP Enterprise Tool Orchestration Server",
    description=(
        "Implements the Model Context Protocol (MCP) to expose enterprise tools "
        "via a discoverable, JWT-authenticated API consumed by LangGraph agents."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ─── Health Endpoint ──────────────────────────────────────────────────────────
# Used by Docker healthcheck and CI to verify server is alive.
# Returns 200 only after lifespan startup completes successfully.

@app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse(content={"status": "ok", "service": "mcp-tool-server"})

# ─── Exception Handlers ───────────────────────────────────────────────────────
# These catch exceptions raised anywhere in the request lifecycle and convert
# them into correct MCP or HTTP responses.

from fastapi import Request
from mcp_server.exceptions import (
    AuthenticationError,
    MCPToolServerError,
    ToolNotFoundError,
)
from mcp_server.models import MCPError, MCPErrorResponse


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    # Auth errors return HTTP 401 — not an MCP-level error response
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
    )


@app.exception_handler(ToolNotFoundError)
async def tool_not_found_handler(
    request: Request, exc: ToolNotFoundError
) -> JSONResponse:
    mcp_error_response = MCPErrorResponse(
        id=None,
        error=MCPError(
            code=exc.mcp_error_code,
            message=exc.message,
        ),
    )
    return JSONResponse(
        status_code=200,  # MCP errors return HTTP 200 — error is in the body
        content=mcp_error_response.model_dump(),
    )


@app.exception_handler(MCPToolServerError)
async def mcp_tool_server_error_handler(
    request: Request, exc: MCPToolServerError
) -> JSONResponse:
    # Catches any MCPToolServerError not handled by a more specific handler above
    mcp_error_response = MCPErrorResponse(
        id=None,
        error=MCPError(
            code=exc.mcp_error_code,
            message=exc.message,
        ),
    )
    return JSONResponse(
        status_code=200,
        content=mcp_error_response.model_dump(),
    )

# ─── MCP Tool Discovery Endpoint ─────────────────────────────────────────────
# Called by the LangGraph agent at startup to discover all available tools.
# Returns the full MCP-compliant tools/list response.

from mcp_server.models import (
    ToolDefinition,
    ToolInputSchema,
    ToolsListResponse,
    ToolsListResult,
)
from mcp_server.registry.registry_loader import list_tools


@app.post("/tools/list")
async def tools_list() -> JSONResponse:
    """MCP tools/list discovery endpoint.

    Returns all registered tools with their names, descriptions, and
    input schemas. The LangGraph agent calls this once at startup and
    builds its tool list from the response — no hardcoded tool names
    anywhere in the agent code.

    Auth middleware applied in Step 3.4 — not yet active.
    """
    registry_entries = list_tools()

    tool_definitions = [
        ToolDefinition(
            name=entry.name,
            description=entry.description,
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    param_name: {
                        "type": param_schema.type,
                        "description": param_schema.description,
                        **({"enum": param_schema.enum} if param_schema.enum else {}),
                    }
                    for param_name, param_schema in entry.input.properties.items()
                },
                required=entry.input.required,
            ),
        )
        for entry in registry_entries
    ]

    discovery_response = ToolsListResponse(
        id=1,
        result=ToolsListResult(tools=tool_definitions),
    )

    return JSONResponse(content=discovery_response.model_dump())

# ─── MCP Tool Dispatch Endpoint ───────────────────────────────────────────────
# Called by the agent to execute a specific tool with given arguments.
# Looks up the handler in the registry, calls it, returns MCP result.

from mcp_server.exceptions import ToolExecutionError, ToolNotFoundError
from mcp_server.models import (
    ToolResultContent,
    ToolsCallRequest,
    ToolsCallResponse,
    ToolsCallResult,
)
from mcp_server.registry.registry_loader import get_tool


@app.post("/tools/call")
async def tools_call(request: ToolsCallRequest) -> JSONResponse:
    """MCP tools/call dispatch endpoint.

    Receives a tool name and arguments, looks up the registered handler,
    executes it with the provided arguments, and returns an MCP-compliant
    ToolsCallResponse.

    Tool execution errors are returned as isError: true in the response
    body — not as HTTP error codes. This is required by the MCP spec.

    Auth middleware applied in Step 3.4 — not yet active.
    """
    tool_name = request.params.name
    tool_arguments = request.params.arguments

    # ── Lookup ────────────────────────────────────────────────────────────────
    try:
        _tool_entry, handler = get_tool(tool_name)
    except KeyError:
        raise ToolNotFoundError(tool_name)

    # ── Execute ───────────────────────────────────────────────────────────────
    try:
        tool_result_text = await handler(tool_arguments)
    except ToolExecutionError as e:
        # Known execution error — return as MCP isError response
        tool_call_response = ToolsCallResponse(
            id=request.id,
            result=ToolsCallResult(
                content=[ToolResultContent(type="text", text=e.message)],
                isError=True,
            ),
        )
        return JSONResponse(content=tool_call_response.model_dump())
    except Exception as e:
        # Unexpected error from handler — log and return as MCP isError
        # FIXME: add structured logging with request id and tool name here
        logger.error(
            "Unexpected error in tool '%s': %s: %s",
            tool_name,
            type(e).__name__,
            e,
        )
        tool_call_response = ToolsCallResponse(
            id=request.id,
            result=ToolsCallResult(
                content=[
                    ToolResultContent(
                        type="text",
                        text=f"Unexpected error in tool '{tool_name}': {type(e).__name__}",
                    )
                ],
                isError=True,
            ),
        )
        return JSONResponse(content=tool_call_response.model_dump())

    # ── Success ───────────────────────────────────────────────────────────────
    tool_call_response = ToolsCallResponse(
        id=request.id,
        result=ToolsCallResult(
            content=[ToolResultContent(type="text", text=tool_result_text)],
            isError=False,
        ),
    )
    return JSONResponse(content=tool_call_response.model_dump())