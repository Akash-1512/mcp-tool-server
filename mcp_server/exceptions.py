from __future__ import annotations


# ─── Base Exception ───────────────────────────────────────────────────────────

class MCPToolServerError(Exception):
    """Root exception for all mcp-tool-server errors.

    Every exception in this codebase inherits from this so callers can
    catch MCPToolServerError to handle any known error, or catch a
    subclass to handle a specific condition.
    """

    def __init__(self, message: str, *, mcp_error_code: int = -32603) -> None:
        super().__init__(message)
        self.message = message
        # JSON-RPC error code attached to every exception so the FastAPI
        # error handler can build a compliant MCPErrorResponse without
        # needing to know which subclass it caught.
        self.mcp_error_code = mcp_error_code


# ─── Auth Exceptions ─────────────────────────────────────────────────────────

class AuthenticationError(MCPToolServerError):
    """Raised when a JWT token is missing, expired, or has invalid signature.

    Maps to HTTP 401 — not an MCP-level error, handled before MCP routing.
    """

    def __init__(self, message: str) -> None:
        # Auth errors don't use JSON-RPC error codes — they return HTTP 401
        super().__init__(message, mcp_error_code=-32600)


# ─── Registry Exceptions ──────────────────────────────────────────────────────

class RegistryLoadError(MCPToolServerError):
    """Raised when tool_registry.yaml fails to load or fails schema validation.

    This is a startup-time error — if the registry is invalid, the server
    should refuse to start rather than serve with broken tool definitions.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, mcp_error_code=-32603)

# ─── Tool Dispatch Exceptions ─────────────────────────────────────────────────

class ToolNotFoundError(MCPToolServerError):
    """Raised when tools/call receives a tool name not in the registry.

    Maps to JSON-RPC -32601 (method not found). Returns isError: true
    in the MCP response body — not an HTTP error code.
    """

    def __init__(self, tool_name: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' not found in registry",
            mcp_error_code=-32601,
        )
        self.tool_name = tool_name


class ToolInputValidationError(MCPToolServerError):
    """Raised when tool arguments fail schema validation.

    Maps to JSON-RPC -32602 (invalid params). The tool handler raises this
    before executing any logic — e.g. missing required field, wrong type.
    """

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(
            f"Invalid input for tool '{tool_name}': {message}",
            mcp_error_code=-32602,
        )
        self.tool_name = tool_name


class ToolExecutionError(MCPToolServerError):
    """Raised when a tool handler fails during execution.

    Distinct from ToolInputValidationError — input was valid but execution
    failed (e.g. SQLite query error, file not found, network timeout).
    Returns isError: true in MCP response — not HTTP 500.
    """

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' execution failed: {message}",
            mcp_error_code=-32603,
        )
        self.tool_name = tool_name


# ─── SQL Tool Exceptions ──────────────────────────────────────────────────────

class SQLQueryForbiddenError(ToolExecutionError):
    """Raised when sql_query_tool receives a non-SELECT statement.

    We only permit SELECT — no INSERT, UPDATE, DELETE, DROP.
    This is enforced before the query reaches SQLite.
    """

    def __init__(self, received_statement: str) -> None:
        super().__init__(
            tool_name="sql_query_tool",
            message=(
                f"Only SELECT statements are permitted. "
                f"Received: {received_statement[:50]}"
            ),
        )