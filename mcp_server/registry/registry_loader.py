"""
Registry Loader
---------------
Loads and validates the tool registry YAML at server startup.
Provides a typed ToolDefinition model and a singleton registry instance
that the MCP server queries to build its tools/list response.

Design decision: Pydantic v2 for validation — schema errors surface at
startup (fail-fast) rather than at first tool call (fail-silent).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Pydantic models — strict schema validation at load time
# ---------------------------------------------------------------------------


class ToolMetadata(BaseModel):
    category: str
    timeout_seconds: int = 10
    rate_limit_per_min: int = 0
    read_only: bool = False
    sandbox_path: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    enabled: bool = True
    auth_required: bool = True
    handler: (
        str  # dotted Python path — e.g. mcp_server.tool_handlers.sql_tool.run_sql_query
    )
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: ToolMetadata

    @field_validator("name")
    @classmethod
    def name_must_be_snake_case(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Tool name '{v}' must be snake_case alphanumeric.")
        return v

    @field_validator("input_schema")
    @classmethod
    def input_schema_must_be_object(cls, v: dict) -> dict:
        if v.get("type") != "object":
            raise ValueError("input_schema top-level type must be 'object'.")
        if "properties" not in v:
            raise ValueError("input_schema must have a 'properties' key.")
        return v

    @field_validator("handler")
    @classmethod
    def handler_must_be_dotted_path(cls, v: str) -> str:
        parts = v.split(".")
        if len(parts) < 3:
            raise ValueError(
                f"Handler '{v}' must be a fully-qualified dotted path "
                "(e.g. mcp_server.tool_handlers.sql_tool.run_sql_query)."
            )
        return v

    def to_mcp_tool_dict(self) -> dict[str, Any]:
        """
        Serialise to the exact shape required by the MCP tools/list response.
        The 'inputSchema' key name is mandated by the MCP spec (camelCase).
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class RegistryFile(BaseModel):
    version: str
    tools: list[ToolDefinition]

    @model_validator(mode="after")
    def no_duplicate_names(self) -> "RegistryFile":
        names = [t.name for t in self.tools]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise ValueError(f"Duplicate tool names in registry: {duplicates}")
        return self


# ---------------------------------------------------------------------------
# ToolRegistry — singleton, loaded once at startup
# ---------------------------------------------------------------------------


class ToolRegistry:
    """
    Singleton registry loaded from tool_registry.yaml.

    Usage:
        registry = ToolRegistry.load(path="mcp_server/registry/tool_registry.yaml")
        tools = registry.list_enabled()               # for tools/list response
        tool  = registry.get("sql_query")             # for tools/call routing
    """

    def __init__(self, registry_file: RegistryFile, source_path: str) -> None:
        self._registry = registry_file
        self._source_path = source_path
        self._loaded_at = time.time()
        self._index: dict[str, ToolDefinition] = {
            t.name: t for t in registry_file.tools
        }

    @classmethod
    def load(cls, path: str | Path) -> "ToolRegistry":
        """
        Load and validate the registry YAML.
        Raises ValueError on schema violations — server should refuse to start.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Tool registry not found at: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError("Registry YAML must be a mapping at the top level.")

        registry_file = RegistryFile.model_validate(raw)
        return cls(registry_file=registry_file, source_path=str(path))

    def list_enabled(self) -> list[ToolDefinition]:
        """Return all tools where enabled=True."""
        return [t for t in self._registry.tools if t.enabled]

    def list_all(self) -> list[ToolDefinition]:
        """Return all tools including disabled ones."""
        return self._registry.tools

    def get(self, name: str) -> ToolDefinition | None:
        """Look up a tool by name. Returns None if not found or disabled."""
        tool = self._index.get(name)
        if tool and tool.enabled:
            return tool
        return None

    def to_mcp_list(self) -> list[dict[str, Any]]:
        """
        Build the tools/list response payload.
        Only enabled tools are included.
        """
        return [t.to_mcp_tool_dict() for t in self.list_enabled()]

    @property
    def loaded_at(self) -> float:
        return self._loaded_at

    @property
    def source_path(self) -> str:
        return self._source_path

    @property
    def version(self) -> str:
        return self._registry.version

    def __repr__(self) -> str:
        enabled = len(self.list_enabled())
        total = len(self.list_all())
        return f"<ToolRegistry version={self.version} tools={enabled}/{total} enabled>"


# ---------------------------------------------------------------------------
# Module-level singleton — imported by main.py
# ---------------------------------------------------------------------------

_registry_instance: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Return the loaded registry singleton. Raises if not initialised."""
    if _registry_instance is None:
        raise RuntimeError(
            "ToolRegistry has not been initialised. "
            "Call init_registry() before calling get_registry()."
        )
    return _registry_instance


def init_registry(path: str | Path) -> ToolRegistry:
    """
    Initialise the singleton registry from a YAML path.
    Called once at server startup — fail-fast on any schema error.
    """
    global _registry_instance
    _registry_instance = ToolRegistry.load(path)
    return _registry_instance
