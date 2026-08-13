"""
agent.py
--------
Internal Research Agent for Presidio — fully local LLM via Ollama.

Wires together:
  1. MCP Tool     -> Google Docs insurance Q&A (via gdocs_mcp_server.py)
  2. RAG Tool     -> HR policy vector search (via rag/rag_tool.py)
  3. Web Search   -> live industry/regulatory info (via tools/web_search_tool.py)

Run:
    python agent.py
"""

import asyncio
import os
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


async def build_and_run():
    mcp_client = MultiServerMCPClient(
        {
            "presidio_gdocs": {
                "command": "python",
                "args": ["mcp_server/gdocs_mcp_server.py"],
                "transport": "stdio",
            }
        }
    )

    async with mcp_client:
        mcp_tools = mcp_client.get_tools()
        print("MCP tools loaded:", [t.name for t in mcp_tools])

        all_tools = mcp_tools + [hr_policy_search, web_search]

        llm = ChatOllama(model=OLLAMA_CHAT_MODEL, temperature=0)
        agent = create_react_agent(llm, all_tools, state_modifier=SYSTEM_PROMPT)

        demo_questions = [
            "Find relevant compliance policies related to AI data handling.",
            "Compare our current hiring trend with industry benchmarks.",
            "What does our health insurance policy cover?",
        ]

        for q in demo_questions:
            print(f"\n\n### QUERY: {q}")
            result = await agent.ainvoke({"messages": [("user", q)]})
            final_message = result["messages"][-1]
            print("\n=== ANSWER ===")
            print(final_message.content)


if __name__ == "__main__":
    asyncio.run(build_and_run())