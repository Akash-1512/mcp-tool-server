"""
MCP Handshake Integration Tests
--------------------------------
These tests call the LIVE server — no mocks.
Run after: docker-compose up mcp-server -d
Or locally: uvicorn mcp_server.main:app --port 8000
"""

import os
import pytest
import httpx

BASE_URL = os.getenv("CI_MCP_SERVER_URL", "http://localhost:8000")
MCP_URL = f"{BASE_URL}/mcp"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


# ── Health ───────────────────────────────────────────────────────────────────


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "enabled_tools" in body
    assert len(body["enabled_tools"]) == 4


# ── Initialize handshake ─────────────────────────────────────────────────────


def test_initialize_returns_protocol_version(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "0.1"},
        },
    }
    r = client.post("/mcp", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == 1
    assert body["result"]["protocolVersion"] == "2024-11-05"
    assert "serverInfo" in body["result"]
    assert body["result"]["serverInfo"]["name"] == "mcp-tool-server"


def test_initialize_returns_tools_capability(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.1"},
        },
    }
    r = client.post("/mcp", json=payload)
    body = r.json()
    assert body["result"]["capabilities"]["tools"]["listChanged"] is True


# ── Notifications ────────────────────────────────────────────────────────────


def test_notifications_initialized_returns_200(client):
    payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    r = client.post("/mcp", json=payload)
    assert r.status_code == 200
    assert r.json() == {}


# ── Tools list ───────────────────────────────────────────────────────────────


def test_tools_list_returns_four_tools(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/list",
        "params": {},
    }
    r = client.post("/mcp", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 3
    tools = body["result"]["tools"]
    assert len(tools) == 4


def test_tools_list_schema_shape(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/list",
        "params": {},
    }
    r = client.post("/mcp", json=payload)
    tools = r.json()["result"]["tools"]
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


def test_tools_list_contains_sql_query(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/list",
        "params": {},
    }
    r = client.post("/mcp", json=payload)
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "sql_query" in names
    assert "web_search" in names
    assert "filesystem_search" in names
    assert "rest_api_search" in names


# ── Error handling ───────────────────────────────────────────────────────────


def test_unknown_method_returns_method_not_found(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/execute",
        "params": {},
    }
    r = client.post("/mcp", json=payload)
    body = r.json()
    assert body["error"]["code"] == -32601


def test_missing_jsonrpc_field_returns_invalid_request(client):
    payload = {"id": 7, "method": "tools/list", "params": {}}
    r = client.post("/mcp", json=payload)
    body = r.json()
    assert body["error"]["code"] == -32600


def test_invalid_json_returns_parse_error(client):
    r = client.post(
        "/mcp",
        content=b"not valid json",
        headers={"Content-Type": "application/json"},
    )
    body = r.json()
    assert body["error"]["code"] == -32700
