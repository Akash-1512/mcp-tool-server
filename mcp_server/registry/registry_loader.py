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
        raise RegistryLoadError(
            f"tool_registry.yaml not found at {_REGISTRY_PATH}"
        ) from e

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