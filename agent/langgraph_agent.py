from __future__ import annotations

import json
import logging
import os

import httpx
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from agent.tool_discovery import MCP_SERVER_URL, discover_tools
from mcp_server.auth.token_generator import generate_token

logger = logging.getLogger(__name__)

# LOCAL DEMO — Groq free tier
agent_llm = ChatGroq(
    model="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_retries=2,
)

# ─────────────────────────────────────────────────────────────────────────────
# [PRODUCTION] Azure OpenAI — uncomment to enable
# Requires: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
#           AZURE_OPENAI_DEPLOYMENT_NAME in .env
# ─────────────────────────────────────────────────────────────────────────────
# from langchain_openai import AzureChatOpenAI
# agent_llm = AzureChatOpenAI(
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#     api_key=os.getenv("AZURE_OPENAI_KEY"),
#     azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
#     api_version="2024-02-01",
#     temperature=0,
# )


def _build_mcp_tool(tool_definition: dict) -> StructuredTool:
    """Build a LangChain StructuredTool from an MCP tool definition.

    The tool's __call__ sends a tools/call request to the MCP server
    and returns the result text. This is how the agent executes tools
    without knowing their implementation details.
    """
    tool_name = tool_definition["name"]
    tool_description = tool_definition["description"]
    input_schema = tool_definition.get("inputSchema", {})
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    def call_mcp_tool(**kwargs) -> str:
        token = generate_token(subject="langgraph-agent")
        headers = {"Authorization": f"Bearer {token}"}
        mcp_request_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": kwargs},
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{MCP_SERVER_URL}/tools/call",
                    headers=headers,
                    json=mcp_request_payload,
                )
        except httpx.ConnectError:
            return f"Error: Cannot connect to MCP server at {MCP_SERVER_URL}"

        if response.status_code == 401:
            return "Error: MCP server rejected agent token"

        mcp_response = response.json()
        result = mcp_response.get("result", {})
        content = result.get("content", [])
        is_error = result.get("isError", False)

        result_text = content[0].get("text", "") if content else ""

        if is_error:
            return f"Tool error: {result_text}"
        return result_text

    # Build args schema from MCP inputSchema properties
    from langchain_core.tools import tool as tool_decorator
    args_schema_fields = {}
    for param_name, param_info in properties.items():
        args_schema_fields[param_name] = (
            str,
            param_info.get("description", ""),
        )

    return StructuredTool.from_function(
        func=call_mcp_tool,
        name=tool_name,
        description=tool_description,
    )


def build_agent():
    """Discover tools from MCP server and build the LangGraph agent."""
    tool_definitions = discover_tools()
    mcp_tools = [_build_mcp_tool(td) for td in tool_definitions]
    llm_with_tools = agent_llm.bind_tools(mcp_tools)

    def agent_node(state: AgentState) -> dict:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(mcp_tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile(), tool_definitions


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Building agent — discovering tools from MCP server...")
    agent, discovered = build_agent()
    print(f"Agent ready with {len(discovered)} tools: {[t['name'] for t in discovered]}")

    query = "Which assets are currently available for assignment?"
    print(f"\nQuery: {query}\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=query)],
        "tool_call_trace": [],
        "discovered_tools": discovered,
    })

    final_message = result["messages"][-1]
    print("Agent response:")
    print(final_message.content)