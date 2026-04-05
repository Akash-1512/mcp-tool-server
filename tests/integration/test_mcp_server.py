"""Integration tests — require live MCP server on localhost:8003."""
from __future__ import annotations

import pytest
import httpx

from mcp_server.auth.token_generator import generate_token, generate_expired_token


BASE_URL = "http://localhost:8003"


def valid_headers() -> dict:
    return {"Authorization": f"Bearer {generate_token()}"}


def test_health_endpoint_returns_200():
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tools_list_returns_three_tools_with_valid_token():
    response = httpx.post(
        f"{BASE_URL}/tools/list",
        headers=valid_headers(),
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "sql_query_tool" in tool_names
    assert "file_search_tool" in tool_names
    assert "web_search_tool" in tool_names


def test_tools_list_returns_401_with_no_token():
    response = httpx.post(
        f"{BASE_URL}/tools/list",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert response.status_code == 401


def test_tools_list_returns_401_with_expired_token():
    headers = {"Authorization": f"Bearer {generate_expired_token()}"}
    response = httpx.post(
        f"{BASE_URL}/tools/list",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_sql_tool_returns_available_assets():
    response = httpx.post(
        f"{BASE_URL}/tools/call",
        headers=valid_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "sql_query_tool",
                "arguments": {
                    "query": "SELECT name, status FROM assets WHERE status = 'available'"
                },
            },
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is False
    import json
    rows = json.loads(result["content"][0]["text"])
    assert len(rows) == 3
    assert all(r["status"] == "available" for r in rows)


def test_sql_tool_rejects_non_select_statement():
    response = httpx.post(
        f"{BASE_URL}/tools/call",
        headers=valid_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "sql_query_tool",
                "arguments": {"query": "DROP TABLE assets"},
            },
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is True


def test_sql_tool_returns_empty_list_when_no_rows_match():
    response = httpx.post(
        f"{BASE_URL}/tools/call",
        headers=valid_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "sql_query_tool",
                "arguments": {
                    "query": "SELECT name FROM assets WHERE status = 'nonexistent_status'"
                },
            },
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is False
    import json
    rows = json.loads(result["content"][0]["text"])
    assert rows == []


def test_tools_call_returns_error_for_unknown_tool():
    response = httpx.post(
        f"{BASE_URL}/tools/call",
        headers=valid_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {},
            },
        },
    )
    assert response.status_code == 200
    assert "error" in response.json()


def test_file_search_tool_returns_results_for_known_keyword():
    response = httpx.post(
        f"{BASE_URL}/tools/call",
        headers=valid_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "file_search_tool",
                "arguments": {"keyword": "license"},
            },
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is False
    import json
    matches = json.loads(result["content"][0]["text"])
    assert len(matches) > 0


def test_file_search_tool_returns_empty_for_unknown_keyword():
    response = httpx.post(
        f"{BASE_URL}/tools/call",
        headers=valid_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "file_search_tool",
                "arguments": {"keyword": "zzznomatchkeywordzzz"},
            },
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is False
    import json
    matches = json.loads(result["content"][0]["text"])
    assert matches == []