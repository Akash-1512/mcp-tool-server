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