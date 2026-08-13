
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

load_dotenv()

_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


@tool("web_search")
def web_search(query: str) -> str:
    """
    Search the live web for current information — industry benchmarks,
    hiring/market trends, regulatory or compliance updates (e.g. new AI
    data-privacy laws) — anything not contained in Presidio's internal
    documents.

    Args:
        query: The search query, e.g. "2026 tech industry attrition rate benchmark".
    """
    results = _client.search(query=query, max_results=5, search_depth="advanced")
    items = results.get("results", [])
    if not items:
        return "No web results found."

    formatted = []
    for r in items:
        formatted.append(f"- {r['title']} ({r['url']})\n  {r['content'][:300]}")
    return "\n\n".join(formatted)
