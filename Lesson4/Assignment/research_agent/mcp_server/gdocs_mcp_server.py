"""
gdocs_mcp_server.py
--------------------
MCP server (FastMCP) exposing Presidio's insurance-related Google Docs
as tools an LLM agent can call. Same pattern as the sticky-notes example:
@mcp.tool() decorators, docstrings become the tool descriptions the LLM reads.

Test standalone:
    mcp dev mcp_server/gdocs_mcp_server.py
"""

import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/documents.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]

CLIENT_SECRET_FILE = os.environ.get("GOOGLE_CLIENT_SECRET_FILE", "credentials.json")
TOKEN_FILE = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")

# Replace these with real Google Doc IDs (the long string in the doc URL)
INSURANCE_DOCS = {
    "health_insurance_policy": "1I8pCU9DY0jOe1xkdf3AulwdUKeHB-9_quzx8st3qrE0",
    "life_insurance_policy": "1U1ACrAmTNyqfW-B7CNnF9FhZtJYAmD2wfZuN2oND7hw",
    "claims_process_guide": "1VaEP9YCHlY4i3xzbwHmI4KBPwuYTQ1gR6OjW__q-liE",
}


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def _extract_text(doc: dict) -> str:
    text_parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for run in paragraph.get("elements", []):
            text_run = run.get("textRun")
            if text_run:
                text_parts.append(text_run.get("content", ""))
    return "".join(text_parts)


mcp = FastMCP("Presidio Insurance Docs")


@mcp.tool()
def list_insurance_docs() -> str:
    """
    List the Google Docs available for insurance-related queries.

    Returns:
        str: A newline-separated list of friendly doc names the agent
             can pass to `read_insurance_doc` or `search_insurance_docs`.
    """
    return "\n".join(INSURANCE_DOCS.keys())


@mcp.tool()
def read_insurance_doc(doc_name: str) -> str:
    """
    Fetch and return the full text of a named insurance Google Doc.

    Args:
        doc_name (str): One of the keys returned by list_insurance_docs(),
                         e.g. "health_insurance_policy".

    Returns:
        str: The plain-text content of the document, or an error message
             if the name isn't recognized.
    """
    if doc_name not in INSURANCE_DOCS:
        return f"Unknown doc '{doc_name}'. Call list_insurance_docs() to see options."

    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    doc = service.documents().get(documentId=INSURANCE_DOCS[doc_name]).execute()
    return _extract_text(doc)


@mcp.tool()
def search_insurance_docs(query: str) -> str:
    """
    Naive keyword search across all registered insurance docs.
    For semantic search over large doc sets, prefer the RAG tool instead —
    this MCP tool is best for small, curated, frequently-updated docs.

    Args:
        query (str): Keyword or phrase to search for.

    Returns:
        str: Matching doc names with a short snippet of surrounding context.
    """
    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)
    results: List[str] = []

    for name, doc_id in INSURANCE_DOCS.items():
        doc = service.documents().get(documentId=doc_id).execute()
        text = _extract_text(doc)
        idx = text.lower().find(query.lower())
        if idx != -1:
            start = max(0, idx - 100)
            end = min(len(text), idx + 200)
            snippet = text[start:end].replace("\n", " ")
            results.append(f"[{name}] ...{snippet}...")

    return "\n\n".join(results) if results else f"No matches for '{query}'."


if __name__ == "__main__":
    mcp.run()
