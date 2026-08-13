import asyncio
import os

import streamlit as st
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from rag.rag_tool import hr_policy_search
from tools.web_search_tool import web_search

load_dotenv()

OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2")

SYSTEM_PROMPT = """You are Presidio's Internal Research Agent.

You have three tools:
- list_insurance_docs, read_insurance_doc, search_insurance_docs (Google Docs
  tools): the ONLY source of truth for insurance questions (health insurance,
  life insurance, claims process). ANY question mentioning "insurance",
  "policy coverage", or "claims" MUST start by calling list_insurance_docs,
  then read_insurance_doc or search_insurance_docs on the relevant doc.
  Do NOT answer insurance questions from web_search or general knowledge.
- hr_policy_search: the ONLY source for HR/compliance/data-handling questions
  (e.g. AI data handling, leave policy). Do NOT answer these from web_search.
- web_search: ONLY for external benchmarks, market trends, or regulatory
  updates that are NOT about Presidio's own internal insurance or HR policies.

Rules:
- Always ground your answer in tool output; cite which tool/source you used.
- NEVER invent URLs, links, or sources that were not returned by a tool call.
  If you don't have a real link from a tool result, don't include one.
- NEVER describe or narrate calling a tool without actually calling it, and
  NEVER invent what a tool "would" return. If you need information from a
  tool, call it for real and wait for its actual result before answering.
- If a query needs both internal policy AND external benchmark data
  (e.g. "compare our hiring trend with industry benchmarks"), call BOTH
  the relevant internal tool and web_search, then synthesize a comparison.
- If no tool has relevant info, say so plainly rather than guessing.
- Keep answers structured and actionable (bullet points / short sections).
"""

DEMO_QUESTIONS = [
    "Find relevant compliance policies related to AI data handling.",
    "Compare our current hiring trend with industry benchmarks.",
    "What does our health insurance policy cover?",
]


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Streamlit reruns the script in the same thread but the default event
    loop can get closed between reruns in some environments, so keep one
    dedicated loop in session_state and reuse it."""
    if "event_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        st.session_state.event_loop = loop
    return st.session_state.event_loop


async def _init_agent():
    """Start the MCP client, fetch tools, and build the ReAct agent.

    The MultiServerMCPClient is an async context manager. We enter it
    manually (instead of `async with`) so the stdio subprocess and
    connection stay alive for the lifetime of the Streamlit session,
    rather than being torn down after a single call.
    """
    mcp_client = MultiServerMCPClient(
        {
            "presidio_gdocs": {
                "command": "python",
                "args": ["mcp_server/gdocs_mcp_server.py"],
                "transport": "stdio",
            }
        }
    )
    await mcp_client.__aenter__()

    mcp_tools = mcp_client.get_tools()
    all_tools = mcp_tools + [hr_policy_search, web_search]

    llm = ChatOllama(model=OLLAMA_CHAT_MODEL, temperature=0)
    agent = create_react_agent(llm, all_tools, state_modifier=SYSTEM_PROMPT)

    return mcp_client, agent, [t.name for t in mcp_tools]


def get_agent():
    """Build (once) and cache the agent + mcp client in session_state."""
    if "agent" not in st.session_state:
        loop = get_event_loop()
        with st.spinner("Starting MCP server and loading tools..."):
            mcp_client, agent, mcp_tool_names = loop.run_until_complete(_init_agent())
        st.session_state.mcp_client = mcp_client
        st.session_state.agent = agent
        st.session_state.mcp_tool_names = mcp_tool_names
    return st.session_state.agent


def run_query(agent, question: str) -> str:
    loop = get_event_loop()
    result = loop.run_until_complete(agent.ainvoke({"messages": [("user", question)]}))
    final_message = result["messages"][-1]
    return final_message.content


def main():
    st.set_page_config(page_title="Presidio Internal Research Agent", page_icon="🔎", layout="wide")
    st.title("🔎 Presidio Internal Research Agent")
    st.caption(f"LLM: Ollama · {OLLAMA_CHAT_MODEL}")

    agent = get_agent()

    with st.sidebar:
        st.subheader("Loaded MCP tools")
        for name in st.session_state.get("mcp_tool_names", []):
            st.write(f"- {name}")
        st.write("- hr_policy_search")
        st.write("- web_search")

        st.divider()
        st.subheader("Demo questions")
        for q in DEMO_QUESTIONS:
            if st.button(q, use_container_width=True):
                st.session_state.pending_query = q

        st.divider()
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pending_query = st.session_state.pop("pending_query", None)
    typed_query = st.chat_input("Ask about insurance, HR/compliance policy, or benchmarks...")
    query = pending_query or typed_query

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = run_query(agent, query)
                except Exception as e:
                    answer = f"Error while running agent: {e}"
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()