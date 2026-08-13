"""
rag_tool.py
-----------
Wraps the persisted Chroma vector store (built by ingest.py) as a
LangChain @tool. Uses the same Ollama embedding model as ingestion —
this MUST match ingest.py's model or similarity search breaks.
"""

import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

load_dotenv()

PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./rag/chroma_store")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

_embeddings = OllamaEmbeddings(model=EMBED_MODEL)
_vectorstore = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=_embeddings,
    collection_name="hr_policies",
)
_retriever = _vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})


@tool("hr_policy_search")
def hr_policy_search(query: str) -> str:
    """
    Search Presidio's HR policy documents (leave policy, compliance policies,
    data handling / AI usage guidelines, benefits, etc.) and return the most
    relevant excerpts with their source document.

    Use this for questions like "what is our AI data handling policy" or
    "how many leave days do employees get".

    Args:
        query: The user's HR/compliance-related question.
    """
    docs = _retriever.invoke(query)
    if not docs:
        return "No relevant HR policy content found."

    formatted = []
    for d in docs:
        source = d.metadata.get("source", "unknown source")
        page = d.metadata.get("page")
        loc = f"{source} (page {page})" if page is not None else source
        formatted.append(f"[Source: {loc}]\n{d.page_content}")

    return "\n\n---\n\n".join(formatted)
