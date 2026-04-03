"""
MCP Tool Server — FastAPI entry point
-------------------------------------
Starts the MCP server, initialises the tool registry, and mounts
the MCP JSON-RPC router. All MCP messages arrive at POST /mcp.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_server.registry.registry_loader import init_registry, get_registry
from mcp_server.routers.mcp_router import router as mcp_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("mcp_server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load and validate tool registry. Fail fast on errors."""
    registry_path = os.getenv(
        "TOOL_REGISTRY_PATH",
        "mcp_server/registry/tool_registry.yaml",
    )
    registry = init_registry(registry_path)
    logger.info(f"Tool registry loaded: {registry}")
    logger.info(f"Enabled tools: {[t.name for t in registry.list_enabled()]}")
    yield
    logger.info("MCP server shutting down.")


app = FastAPI(
    title="MCP Enterprise Tool Orchestration Server",
    version="0.3.0",
    description=(
        "Production MCP server exposing enterprise tools — SQL query, "
        "web search, filesystem search, REST API — via JSON-RPC 2.0."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(mcp_router)


@app.get("/health", tags=["ops"])
async def health():
    """Health check endpoint — used by CI and docker-compose healthcheck."""
    registry = get_registry()
    return {
        "status": "ok",
        "server_version": "0.3.0",
        "registry_version": registry.version,
        "enabled_tools": [t.name for t in registry.list_enabled()],
    }
