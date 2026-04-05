from __future__ import annotations

import importlib
import logging
import pathlib
from typing import Any, Callable

import yaml

from mcp_server.exceptions import RegistryLoadError
from mcp_server.registry.schemas import RegistryToolEntry, ToolRegistry

logger = logging.getLogger(__name__)

# Path to the YAML file — relative to this file's location
_REGISTRY_PATH = pathlib.Path(__file__).parent / "tool_registry.yaml"

# Runtime registry — populated once at startup by load_registry()
# Maps tool name → (RegistryToolEntry, handler callable)
_registry: dict[str, tuple[RegistryToolEntry, Callable[..., Any]]] = {}


def load_registry() -> None:
    """Load and validate tool_registry.yaml, import all handler functions.

    Called once at FastAPI startup. Raises RegistryLoadError if:
    - YAML file is missing or unparseable
    - YAML content fails Pydantic schema validation
    - Any handler function cannot be imported

    After this returns, get_tool() and list_tools() are safe to call.
    """
    global _registry

    logger.info("Loading tool registry from %s", _REGISTRY_PATH)

    # ── Step 1: Read and parse YAML ──────────────────────────────────────────
    try:
        raw_yaml = _REGISTRY_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise RegistryLoadError(f"tool_registry.yaml not found at {_REGISTRY_PATH}") from e

    try:
        raw_data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        logger.error("tool_registry.yaml is invalid YAML: %s", e)
        raise RegistryLoadError(f"Invalid YAML in tool registry: {e}") from e

    # ── Step 2: Validate against Pydantic schema ──────────────────────────────
    # TODO: add per-tool validation errors with tool name context
    try:
        tool_registry = ToolRegistry(**raw_data)
    except Exception as e:
        raise RegistryLoadError(f"Tool registry schema validation failed: {e}") from e

    logger.info("Registry YAML valid — %d tools found", len(tool_registry.tools))

    # ── Step 3: Import each handler function by dotted path ───────────────────
    new_registry: dict[str, tuple[RegistryToolEntry, Callable[..., Any]]] = {}

    for tool_entry in tool_registry.tools:
        handler_callable = _import_handler(tool_entry.handler, tool_entry.name)
        new_registry[tool_entry.name] = (tool_entry, handler_callable)
        logger.info("Registered tool '%s' → %s", tool_entry.name, tool_entry.handler)

    _registry = new_registry
    logger.info("Tool registry loaded — %d tools active", len(_registry))


def _import_handler(dotted_path: str, tool_name: str) -> Callable[..., Any]:
    """Resolve a dotted Python path string to a callable.

    Example: 'mcp_server.tool_handlers.sql_tool.handle_sql_query'
    → imports mcp_server.tool_handlers.sql_tool
    → returns the handle_sql_query attribute

    Raises RegistryLoadError if the module or attribute cannot be found.
    This is intentionally strict — a missing handler is a startup failure,
    not a runtime error.
    """
    try:
        module_path, function_name = dotted_path.rsplit(".", 1)
    except ValueError as e:
        raise RegistryLoadError(
            f"Tool '{tool_name}' handler path '{dotted_path}' is not a valid "
            f"dotted path — expected 'module.path.function_name'"
        ) from e

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        raise RegistryLoadError(
            f"Tool '{tool_name}' handler module '{module_path}' not found: {e}"
        ) from e

    try:
        handler_callable = getattr(module, function_name)
    except AttributeError as e:
        raise RegistryLoadError(
            f"Tool '{tool_name}' handler function '{function_name}' "
            f"not found in module '{module_path}'"
        ) from e

    if not callable(handler_callable):
        raise RegistryLoadError(f"Tool '{tool_name}' handler '{dotted_path}' is not callable")

    return handler_callable


# ─── Public API ───────────────────────────────────────────────────────────────


def get_tool(tool_name: str) -> tuple[RegistryToolEntry, Callable[..., Any]]:
    """Return the (RegistryToolEntry, handler) pair for a given tool name.

    Raises KeyError if tool_name is not in the registry.
    Callers should catch KeyError and raise ToolNotFoundError.
    """
    if tool_name not in _registry:
        raise KeyError(tool_name)
    return _registry[tool_name]


def list_tools() -> list[RegistryToolEntry]:
    """Return all registered tool entries — used by the tools/list endpoint."""
    return [entry for entry, _ in _registry.values()]
