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