"""
ingest.py
---------
Vectorizes HR policy docs into a local Chroma store using Ollama's
embedding model (nomic-embed-text) — fully local, no API key.

Run once, and again whenever HR docs change:
    python ingest.py
"""

import os
from dotenv import load_dotenv

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

load_dotenv()

HR_DOCS_DIR = os.environ.get("HR_DOCS_DIR", "../data/hr_policies")
PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_store")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def load_documents():
    loaders = [
        DirectoryLoader(HR_DOCS_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
        DirectoryLoader(HR_DOCS_DIR, glob="**/*.docx", loader_cls=UnstructuredWordDocumentLoader),
        DirectoryLoader(HR_DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader),
    ]
    docs = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"Skipped a loader due to: {e}")
    return docs


def build_vectorstore():
    print(f"Loading HR policy docs from {HR_DOCS_DIR} ...")
    raw_docs = load_documents()
    print(f"Loaded {len(raw_docs)} raw documents.")

    if not raw_docs:
        print("No documents found — add files to data/hr_policies/ first.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)
    print(f"Split into {len(chunks)} chunks.")

    embeddings = OllamaEmbeddings(model=EMBED_MODEL)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="hr_policies",
    )
    vectorstore.persist()
    print(f"Vector store persisted to {PERSIST_DIR}")


if __name__ == "__main__":
    build_vectorstore()
