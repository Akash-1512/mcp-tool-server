from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ─── Tool Input Schema ────────────────────────────────────────────────────────
# Represents the JSON Schema object nested inside a tool definition.
# MCP spec requires "type": "object" with "properties" and "required".
class ToolInputSchema(BaseModel):
    type: str = Field(default="object", description="Always 'object' per MCP spec")
    properties: dict[str, dict[str, Any]] = Field(
        description="Map of parameter name to JSON Schema property definition"
    )
    required: list[str] = Field(
        default_factory=list,
        description="List of required parameter names",
    )


# ─── Tool Definition ──────────────────────────────────────────────────────────
# A single tool entry as returned by the tools/list discovery endpoint.
# This is what the agent reads to understand what tools are available.
class ToolDefinition(BaseModel):
    name: str = Field(description="Unique tool identifier — matches registry key")
    description: str = Field(description="Human-readable description for the LLM")
    inputSchema: ToolInputSchema = Field(  # noqa: N815 — MCP spec uses camelCase
        description="JSON Schema defining the tool's accepted parameters"
    )

    # TODO: MCP spec also supports 'annotations' for tool metadata (e.g. readOnly)
    # Not implemented — see https://spec.modelcontextprotocol.io/specification/tools

# ─── MCP Request Models ───────────────────────────────────────────────────────

class ToolsListRequest(BaseModel):
    """Incoming JSON-RPC request for tools/list discovery endpoint."""
    jsonrpc: str = Field(default="2.0")
    id: int | str = Field(description="JSON-RPC request ID — echoed back in response")
    method: str = Field(default="tools/list")
    params: dict[str, Any] = Field(default_factory=dict)


class ToolsCallRequest(BaseModel):
    """Incoming JSON-RPC request for tools/call dispatch endpoint."""
    jsonrpc: str = Field(default="2.0")
    id: int | str = Field(description="JSON-RPC request ID — echoed back in response")
    method: str = Field(default="tools/call")
    params: ToolsCallParams = Field(description="Tool name and arguments")


class ToolsCallParams(BaseModel):
    """The params block inside a tools/call request."""
    name: str = Field(description="Tool name — must match a registered tool")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value arguments matching the tool's inputSchema",
    )


# ─── MCP Response Models ──────────────────────────────────────────────────────

class ToolResultContent(BaseModel):
    """A single content block inside a tool result."""
    type: str = Field(default="text")
    text: str = Field(description="Tool output as a string — JSON-serialised if structured")


class ToolsListResponse(BaseModel):
    """Response returned by the tools/list discovery endpoint."""
    jsonrpc: str = Field(default="2.0")
    id: int | str
    result: ToolsListResult


class ToolsListResult(BaseModel):
    tools: list[ToolDefinition]


class ToolsCallResponse(BaseModel):
    """Response returned by the tools/call dispatch endpoint."""
    jsonrpc: str = Field(default="2.0")
    id: int | str
    result: ToolsCallResult


class ToolsCallResult(BaseModel):
    content: list[ToolResultContent]
    isError: bool = Field(default=False)  # noqa: N815 — MCP spec uses camelCase


# ─── MCP Error Response ───────────────────────────────────────────────────────
# Used for JSON-RPC level errors (malformed request, unknown method).
# Auth failures (401) bypass this — they return HTTP 401 directly.
class MCPErrorResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: int | str | None = None
    error: MCPError


class MCPError(BaseModel):
    code: int = Field(description="JSON-RPC error code")
    message: str = Field(description="Human-readable error description")

    # JSON-RPC standard error codes we use:
    # -32600 invalid request
    # -32601 method not found
    # -32602 invalid params
    # -32603 internal error