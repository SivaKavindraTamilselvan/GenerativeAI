"""
Multi-Agent Support System using LangGraph
============================================

Architecture
------------
                        +------------------+
                        |  Supervisor Agent |
                        |  (classifies as   |
                        |   IT or Finance)  |
                        +---------+--------+
                                  |
                 +----------------+----------------+
                 |                                 |
           +-----v-----+                    +------v------+
           | IT Agent  |                    | Finance Agent|
           +-----------+                    +-------------+
                                              tools: ReadFile,
                                                     WebSearch

Agent 1 - Supervisor Agent
    Purpose: Classifies the incoming user query as "IT" or "Finance"
    Action : Routes the query to the matching specialist agent node.

Agent 2 - IT Agent
    Handles queries such as VPN setup, approved software, laptop requests.

Agent 3 - Finance Agent
    Handles queries such as reimbursements, budget reports, payroll timing.
    Tools:
        - ReadFile  : reads internal finance docs (local text/markdown files)
        - WebSearch : looks up public finance information (DuckDuckGo, no API key)

Requirements
------------
    pip install langgraph langchain-core langchain-ollama duckduckgo-search python-dotenv

Setup (Ollama - local, free, no API key needed)
------------------------------------------------
    1. Install Ollama: https://ollama.com/download
    2. Pull a model:   ollama pull llama3.1
    3. Make sure the Ollama server is running (it usually starts automatically,
       or run `ollama serve` manually).

Environment
-----------
    Optionally create a .env file next to this script to choose a model:

        OLLAMA_MODEL=llama3.1

    If no .env is present, it defaults to "llama3.1".

Run
---
    python multi_agent_support_system.py
"""

from __future__ import annotations

import os
from typing import Literal, TypedDict, Optional

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

load_dotenv()

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")


# ---------------------------------------------------------------------------
# 1. Shared graph state
# ---------------------------------------------------------------------------
class SupportState(TypedDict):
    query: str                     # original user query
    category: Optional[str]        # "IT" or "Finance", set by the Supervisor
    response: Optional[str]        # final answer produced by a specialist agent


# ---------------------------------------------------------------------------
# 2. LLM instance (shared by all agents)
# ---------------------------------------------------------------------------
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)


# ---------------------------------------------------------------------------
# 3. Tools used by the Finance Agent
# ---------------------------------------------------------------------------
FINANCE_DOCS_DIR = os.path.join(os.path.dirname(__file__), "finance_docs")


@tool
def ReadFile(filename: str) -> str:
    """Read an internal finance document by filename (e.g. 'budget_report.md',
    'reimbursement_policy.md', 'payroll_schedule.md') and return its contents.
    Use this for questions about internal company finance policies or reports.
    """
    path = os.path.join(FINANCE_DOCS_DIR, filename)
    if not os.path.exists(path):
        available = ", ".join(os.listdir(FINANCE_DOCS_DIR)) if os.path.isdir(FINANCE_DOCS_DIR) else "none"
        return f"File '{filename}' not found. Available files: {available}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@tool
def WebSearch(query: str) -> str:
    """Search the public web for finance-related information that is not
    contained in internal documents (e.g. general finance definitions,
    market data, public tax rules). Returns a short text summary of results.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "No web results found."
        return "\n\n".join(
            f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nURL: {r.get('href')}"
            for r in results
        )
    except Exception as exc:  # keep the demo runnable even without internet
        return f"WebSearch unavailable ({exc}). Simulated result for '{query}'."


FINANCE_TOOLS = [ReadFile, WebSearch]
llm_with_finance_tools = llm.bind_tools(FINANCE_TOOLS)


# ---------------------------------------------------------------------------
# 4. Agent 1 - Supervisor Agent
# ---------------------------------------------------------------------------
SUPERVISOR_SYSTEM_PROMPT = """You are a Supervisor Agent for an internal support system.
Classify the user's query into exactly one category: "IT" or "Finance".

IT covers: VPN/network setup, hardware/laptop requests, approved software,
account/access issues, printers, general tech troubleshooting.

Finance covers: reimbursements, expense reports, budget reports, payroll,
invoices, purchase orders, tax/accounting questions.

Respond with only a single word: IT or Finance."""


def supervisor_node(state: SupportState) -> SupportState:
    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=state["query"]),
    ]
    result = llm.invoke(messages)
    category = result.content.strip().lower()
    category = "Finance" if "finance" in category else "IT"
    return {**state, "category": category}


def route_after_supervisor(state: SupportState) -> Literal["it_agent", "finance_agent"]:
    return "finance_agent" if state["category"] == "Finance" else "it_agent"


# ---------------------------------------------------------------------------
# 5. Agent 2 - IT Agent
# ---------------------------------------------------------------------------
IT_SYSTEM_PROMPT = """You are the IT Support Agent. Answer employee IT questions
clearly and concisely, e.g. VPN setup, approved software lists, and how to
request new laptops or equipment. If you don't have a definitive internal
answer, give sensible general best-practice guidance and suggest opening an
IT ticket for anything account-specific."""


def it_agent_node(state: SupportState) -> SupportState:
    messages = [
        SystemMessage(content=IT_SYSTEM_PROMPT),
        HumanMessage(content=state["query"]),
    ]
    result = llm.invoke(messages)
    return {**state, "response": result.content}


# ---------------------------------------------------------------------------
# 6. Agent 3 - Finance Agent (with ReadFile + WebSearch tools)
# ---------------------------------------------------------------------------
FINANCE_SYSTEM_PROMPT = """You are the Finance Support Agent. Answer employee
finance questions such as reimbursement filing, budget reports, and payroll
schedules.

You have two tools:
- ReadFile: use this first for anything that might be documented internally
  (reimbursement policy, budget reports, payroll schedule).
- WebSearch: use this for general/public finance information not covered by
  internal docs.

IMPORTANT: After a tool returns a result, you MUST use that result to give a
final, complete answer to the ORIGINAL user question. Do not ask the user a
follow-up question. Do not repeat or rephrase their question back to them.
Just answer it directly using the information from the tool output."""


def finance_agent_node(state: SupportState) -> SupportState:
    messages = [
        SystemMessage(content=FINANCE_SYSTEM_PROMPT),
        HumanMessage(content=state["query"]),
    ]
    ai_msg = llm_with_finance_tools.invoke(messages)
    messages.append(ai_msg)

    # Simple tool-execution loop (handles chained tool calls)
    while getattr(ai_msg, "tool_calls", None):
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            selected_tool = {"ReadFile": ReadFile, "WebSearch": WebSearch}[tool_name]
            tool_output = selected_tool.invoke(tool_args)
            messages.append(
                {
                    "role": "tool",
                    "content": str(tool_output),
                    "tool_call_id": tool_call["id"],
                }
            )
        ai_msg = llm_with_finance_tools.invoke(messages)
        messages.append(ai_msg)

    return {**state, "response": ai_msg.content}


# ---------------------------------------------------------------------------
# 7. Build the LangGraph
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("it_agent", it_agent_node)
    graph.add_node("finance_agent", finance_agent_node)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"it_agent": "it_agent", "finance_agent": "finance_agent"},
    )
    graph.add_edge("it_agent", END)
    graph.add_edge("finance_agent", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# 8. Demo / entry point
# ---------------------------------------------------------------------------
def run_query(app, query: str) -> None:
    result = app.invoke({"query": query, "category": None, "response": None})
    print(f"\nQuery   : {query}")
    print(f"Routed  : {result['category']} Agent")
    print(f"Response: {result['response']}")


if __name__ == "__main__":
    print(f"Using local Ollama model: {OLLAMA_MODEL} (make sure Ollama is running: `ollama serve`)")

    app = build_graph()

    print("\nMulti-Agent Support System (Supervisor -> IT / Finance Agent)")
    print("Type your query and press Enter. Type 'exit' or 'quit' to stop.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in ("exit", "quit", ""):
            print("Goodbye!")
            break
        run_query(app, query)
        print()