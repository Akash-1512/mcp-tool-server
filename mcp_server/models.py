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