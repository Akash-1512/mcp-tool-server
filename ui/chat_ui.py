from __future__ import annotations

import json
import logging
import os

import streamlit as st
from langchain_core.messages import HumanMessage

import sys
import pathlib
# Add project root to path so 'agent' and 'mcp_server' modules are importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Must be first Streamlit call
st.set_page_config(
    page_title="MCP Enterprise Tool Server",
    page_icon="🔧",
    layout="wide",
)

logging.basicConfig(level=logging.INFO)

# ─── Session State Initialisation ────────────────────────────────────────────

if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.discovered_tools = []
    st.session_state.chat_history = []  # list of {role, content, trace}
    st.session_state.agent_error = None

# ─── Agent Initialisation ─────────────────────────────────────────────────────

@st.cache_resource
def load_agent():
    """Load the LangGraph agent once — cached across reruns."""
    os.environ.setdefault("MCP_SERVER_URL", "http://localhost:8003")
    from agent.langgraph_agent import build_agent
    return build_agent()


def initialise_agent():
    try:
        agent, discovered = load_agent()
        st.session_state.agent = agent
        st.session_state.discovered_tools = discovered
    except RuntimeError as e:
        st.session_state.agent_error = str(e)


if st.session_state.agent is None and st.session_state.agent_error is None:
    with st.spinner("Connecting to MCP server and discovering tools..."):
        initialise_agent()

# ─── Sidebar — Tool Discovery Panel ──────────────────────────────────────────

with st.sidebar:
    st.title("🔧 MCP Tool Server")
    st.markdown("---")

    if st.session_state.agent_error:
        st.error(f"Connection failed: {st.session_state.agent_error}")
    elif st.session_state.discovered_tools:
        st.success(f"✅ Connected — {len(st.session_state.discovered_tools)} tools discovered")
        st.markdown("### Available Tools")
        for tool_def in st.session_state.discovered_tools:
            with st.expander(f"🛠 {tool_def['name']}"):
                st.markdown(f"**Description:** {tool_def['description'][:200]}...")
                st.json(tool_def.get("inputSchema", {}))
    else:
        st.warning("Connecting to MCP server...")

    st.markdown("---")
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# ─── Main Chat Interface ──────────────────────────────────────────────────────

st.title("MCP Enterprise Tool Orchestration")
st.caption("Ask questions about IT assets, licenses, support tickets, or search the web.")

# Render chat history
for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])
        if entry.get("trace"):
            with st.expander("🔍 Tool Call Trace", expanded=False):
                for i, call in enumerate(entry["trace"], 1):
                    st.markdown(f"**Call {i}: `{call.get('tool_name', 'unknown')}`**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Arguments:**")
                        st.json(call.get("arguments", {}))
                    with col2:
                        st.markdown("**Result:**")
                        try:
                            result_data = json.loads(call.get("result", "{}"))
                            st.json(result_data)
                        except (json.JSONDecodeError, TypeError):
                            st.text(str(call.get("result", ""))[:500])
                    if call.get("is_error"):
                        st.error("Tool returned an error")
                    st.markdown("---")

# Chat input
if prompt := st.chat_input("Ask about your IT assets..."):
    if st.session_state.agent is None:
        st.error("Agent not connected. Is the MCP server running?")
    else:
        # Show user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "trace": [],
        })
        with st.chat_message("user"):
            st.markdown(prompt)

        # Run agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.agent.invoke(
                        {
                            "messages": [HumanMessage(content=prompt)],
                            "tool_call_trace": [],
                            "discovered_tools": st.session_state.discovered_tools,
                            "tool_call_count": 0,
                        },
                        config={"recursion_limit": 25},
                    )

                    # Find last message with non-empty content
                    response_text = ""
                    for msg in reversed(result["messages"]):
                        content = getattr(msg, "content", "")
                        if content and isinstance(content, str) and content.strip():
                            response_text = content
                            break
                    if not response_text:
                        # Fallback — extract tool results directly from messages
                        from langchain_core.messages import ToolMessage
                        tool_texts = [
                            msg.content for msg in result["messages"]
                            if isinstance(msg, ToolMessage) and msg.content
                        ]
                        if tool_texts:
                            response_text = "**Tool results:**\n" + "\n\n".join(tool_texts)
                        else:
                            response_text = "Agent completed but produced no text response."
                    tool_trace = result.get("tool_call_trace", [])

                    st.markdown(response_text)

                    if tool_trace:
                        with st.expander("🔍 Tool Call Trace", expanded=True):
                            for i, call in enumerate(tool_trace, 1):
                                st.markdown(f"**Call {i}: `{call.get('tool_name', 'unknown')}`**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**Arguments:**")
                                    st.json(call.get("arguments", {}))
                                with col2:
                                    st.markdown("**Result:**")
                                    try:
                                        result_data = json.loads(call.get("result", "{}"))
                                        st.json(result_data)
                                    except (json.JSONDecodeError, TypeError):
                                        st.text(str(call.get("result", ""))[:500])

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "trace": tool_trace,
                    })

                except Exception as e:
                    error_msg = f"Agent error: {type(e).__name__}: {e}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg,
                        "trace": [],
                    })