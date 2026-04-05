from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ToolParameterSchema(BaseModel):
    """Schema for a single parameter inside a tool's input definition."""

    type: str = Field(description="JSON Schema type: string, integer, boolean, array")
    description: str = Field(description="Parameter description shown to the LLM")
    enum: list[str] | None = Field(
        default=None,
        description="Optional allowed values — restricts input to this set",
    )


class ToolInputDefinition(BaseModel):
    """The input schema block for a tool as defined in tool_registry.yaml."""

    properties: dict[str, ToolParameterSchema] = Field(
        description="Map of parameter name to its schema"
    )
    required: list[str] = Field(
        default_factory=list,
        description="Parameter names that must be present in every call",
    )

    @field_validator("required")
    @classmethod
    def required_fields_must_exist_in_properties(cls, required: list[str], info: any) -> list[str]:
        properties = info.data.get("properties", {})
        missing = [f for f in required if f not in properties]
        if missing:
            raise ValueError(f"Required fields {missing} not found in properties")
        return required


class RegistryToolEntry(BaseModel):
    """A single tool entry as it appears in tool_registry.yaml.

    The 'handler' field is the dotted Python path to the async handler
    function — e.g. 'mcp_server.tool_handlers.sql_tool.handle_sql_query'.
    The registry loader resolves this string to a callable at startup.
    """

    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Human-readable description for the LLM")
    handler: str = Field(description="Dotted Python path to the async handler function")
    input: ToolInputDefinition = Field(description="Input schema defining accepted parameters")


class ToolRegistry(BaseModel):
    """Root schema for tool_registry.yaml."""

    tools: list[RegistryToolEntry] = Field(
        description="List of all registered tools",
        min_length=1,
    )
