"""
Registry loader tests.
These run without a live server — pure unit tests on the loader logic.
"""

from mcp_server.registry.registry_loader import ToolRegistry, init_registry


REGISTRY_PATH = "mcp_server/registry/tool_registry.yaml"


def test_registry_loads_without_error():
    registry = ToolRegistry.load(REGISTRY_PATH)
    assert registry is not None


def test_registry_version_is_set():
    registry = ToolRegistry.load(REGISTRY_PATH)
    assert registry.version == "1.0"


def test_all_four_tools_present():
    registry = ToolRegistry.load(REGISTRY_PATH)
    names = {t.name for t in registry.list_enabled()}
    assert names == {"sql_query", "web_search", "filesystem_search", "rest_api_search"}


def test_mcp_list_shape():
    """Each tool in tools/list must have name, description, inputSchema."""
    registry = ToolRegistry.load(REGISTRY_PATH)
    for tool in registry.to_mcp_list():
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


def test_get_known_tool():
    registry = ToolRegistry.load(REGISTRY_PATH)
    tool = registry.get("sql_query")
    assert tool is not None
    assert tool.auth_required is True
    assert tool.metadata.category == "sql"


def test_get_unknown_tool_returns_none():
    registry = ToolRegistry.load(REGISTRY_PATH)
    assert registry.get("nonexistent_tool") is None


def test_singleton_init():
    registry = init_registry(REGISTRY_PATH)
    from mcp_server.registry.registry_loader import get_registry

    assert get_registry() is registry
