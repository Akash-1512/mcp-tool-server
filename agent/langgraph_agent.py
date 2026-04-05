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
    model="llama-3.1-8b-instant",
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
    tool_name = tool_definition["name"]
    tool_description = tool_definition["description"]
    input_schema = tool_definition.get("inputSchema", {})
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    # Build a dynamic Pydantic model so LangChain passes correct args to LLM
    from pydantic import BaseModel, Field, create_model
    field_definitions = {}
    for param_name, param_info in properties.items():
        description = param_info.get("description", "")
        if param_name in required:
            field_definitions[param_name] = (str, Field(description=description))
        else:
            field_definitions[param_name] = (str, Field(default="", description=description))

    DynamicArgsSchema = create_model(f"{tool_name}_args", **field_definitions)

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

    return StructuredTool.from_function(
        func=call_mcp_tool,
        name=tool_name,
        description=tool_description,
        args_schema=DynamicArgsSchema,
    )


def build_agent():
    """Discover tools from MCP server and build the LangGraph agent."""
    tool_definitions = discover_tools()
    mcp_tools = [_build_mcp_tool(td) for td in tool_definitions]
    llm_with_tools = agent_llm.bind_tools(mcp_tools)

    from langchain_core.messages import SystemMessage

    system_message = SystemMessage(content=(
        "You are an IT asset management assistant with access to a SQLite database.\n\n"
        "EXACT TABLE SCHEMAS:\n"
        "employees(employee_id, name, department, location, email, manager_id)\n"
        "assets(asset_id, name, category, status, assigned_to, purchase_date, cost_usd)\n"
        "licenses(license_id, software_name, vendor, seats_total, seats_used, expiry_date, cost_usd)\n"
        "support_tickets(ticket_id, asset_id, raised_by, priority, status, issue, created_at, resolved_at)\n\n"
        "EXAMPLE CORRECT JOIN QUERY:\n"
        "SELECT employees.name, employees.department, support_tickets.priority, support_tickets.status\n"
        "FROM support_tickets\n"
        "JOIN employees ON support_tickets.raised_by = employees.employee_id\n"
        "WHERE support_tickets.priority = 'high' AND support_tickets.status = 'open'\n\n"
        "RULES:\n"
        "1. Always write full table.column names in JOINs — never use short aliases like t. or e.\n"
        "2. After getting results, answer directly in plain English.\n"
        "3. Only SELECT statements allowed.\n"
    ))

    def agent_node(state: AgentState) -> dict:
        messages = [system_message] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {
            "messages": [response],
            "tool_call_count": state.get("tool_call_count", 0) + 1,
        }

    def synthesize_node(state: AgentState) -> dict:
        """Force a final answer from the LLM without tools."""
        from langchain_core.messages import ToolMessage
        # Collect tool results from message history for context
        tool_results = [
            msg.content for msg in state["messages"]
            if isinstance(msg, ToolMessage) and msg.content
        ]
        tool_context = "\n".join(tool_results) if tool_results else "No tool results available."

        synthesis_prompt = SystemMessage(content=(
            f"You are an IT asset management assistant. "
            f"The following data was retrieved from the database:\n\n{tool_context}\n\n"
            f"Using ONLY this data, answer the user's question directly and concisely. "
            f"Do not call any tools. Do not say you cannot answer."
        ))
        response = agent_llm.invoke([synthesis_prompt] + state["messages"])
        return {"messages": [response]}
    
    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if state.get("tool_call_count", 0) >= 3:
            return "synthesize"
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(mcp_tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("synthesize", synthesize_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", should_continue,
        {"tools": "tools", "synthesize": "synthesize", END: END}
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=None), tool_definitions


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Building agent — discovering tools from MCP server...")
    agent, discovered = build_agent()
    print(f"Agent ready with {len(discovered)} tools: {[t['name'] for t in discovered]}")

    query = "Which assets are currently available for assignment?"
    print(f"\nQuery: {query}\n")

    result = agent.invoke(
        {
            "messages": [HumanMessage(content=query)],
            "tool_call_trace": [],
            "discovered_tools": discovered,
            "tool_call_count": 0,
        },
        config={"recursion_limit": 25},
    )

    final_message = result["messages"][-1]
    print("Agent response:")
    print(final_message.content)