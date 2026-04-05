from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_server.auth.jwt_middleware import extract_bearer_token, verify_token
from mcp_server.exceptions import (
    AuthenticationError,
    MCPToolServerError,
    ToolExecutionError,
    ToolNotFoundError,
)
from mcp_server.models import (
    MCPError,
    MCPErrorResponse,
    ToolDefinition,
    ToolInputSchema,
    ToolResultContent,
    ToolsCallRequest,
    ToolsCallResponse,
    ToolsCallResult,
    ToolsListResponse,
    ToolsListResult,
)
from mcp_server.registry.registry_loader import get_tool, list_tools, load_registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MCP Tool Server starting up...")
    try:
        load_registry()
        logger.info("Tool registry loaded — server ready")
    except MCPToolServerError as e:
        logger.error("STARTUP FAILED — tool registry could not be loaded: %s", e)
        raise
    yield
    logger.info("MCP Tool Server shutting down")


app = FastAPI(
    title="MCP Enterprise Tool Orchestration Server",
    description=(
        "Implements the Model Context Protocol (MCP) to expose enterprise tools "
        "via a discoverable, JWT-authenticated API consumed by LangGraph agents."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse(content={"status": "ok", "service": "mcp-tool-server"})


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
    )


@app.exception_handler(ToolNotFoundError)
async def tool_not_found_handler(request: Request, exc: ToolNotFoundError) -> JSONResponse:
    mcp_error_response = MCPErrorResponse(
        id=None,
        error=MCPError(code=exc.mcp_error_code, message=exc.message),
    )
    return JSONResponse(status_code=200, content=mcp_error_response.model_dump())


@app.exception_handler(MCPToolServerError)
async def mcp_tool_server_error_handler(request: Request, exc: MCPToolServerError) -> JSONResponse:
    mcp_error_response = MCPErrorResponse(
        id=None,
        error=MCPError(code=exc.mcp_error_code, message=exc.message),
    )
    return JSONResponse(status_code=200, content=mcp_error_response.model_dump())


@app.post("/tools/list")
async def tools_list(request: Request) -> JSONResponse:
    token = extract_bearer_token(request)
    verify_token(token)
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


@app.post("/tools/call")
async def tools_call(request: ToolsCallRequest, request_raw: Request) -> JSONResponse:
    token = extract_bearer_token(request_raw)
    verify_token(token)
    tool_name = request.params.name
    tool_arguments = request.params.arguments

    try:
        _tool_entry, handler = get_tool(tool_name)
    except KeyError:
        raise ToolNotFoundError(tool_name)

    try:
        tool_result_text = await handler(tool_arguments)
    except ToolExecutionError as e:
        tool_call_response = ToolsCallResponse(
            id=request.id,
            result=ToolsCallResult(
                content=[ToolResultContent(type="text", text=e.message)],
                isError=True,
            ),
        )
        return JSONResponse(content=tool_call_response.model_dump())
    except Exception as e:
        # FIXME: add structured logging with request id and tool name here
        logger.error("Unexpected error in tool '%s': %s: %s", tool_name, type(e).__name__, e)
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

    tool_call_response = ToolsCallResponse(
        id=request.id,
        result=ToolsCallResult(
            content=[ToolResultContent(type="text", text=tool_result_text)],
            isError=False,
        ),
    )
    return JSONResponse(content=tool_call_response.model_dump())
