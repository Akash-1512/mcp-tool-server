from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State passed between nodes in the LangGraph agent graph.

    messages: full conversation history — add_messages reducer appends
              new messages rather than replacing the list.
    tool_call_trace: ordered list of MCP request/response pairs for
                     the Streamlit UI to display. Each entry is a dict
                     with keys: tool_name, arguments, result, is_error.
    discovered_tools: list of tool definitions received from /tools/list
                      at startup — stored in state for inspection/logging.
    """

    messages: Annotated[list, add_messages]
    tool_call_trace: list[dict[str, Any]]
    discovered_tools: list[dict[str, Any]]