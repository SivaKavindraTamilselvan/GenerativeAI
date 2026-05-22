import uuid
from pathlib import Path
from typing import List

import chromadb
import numpy as np
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


# =========================================================
# STEP 1 — LOAD PDF DOCUMENTS
# =========================================================

def process_all_pdfs(pdf_directory: str):
    """
    Load all PDF files recursively
    """

    all_documents = []

    pdf_dir = Path(pdf_directory)

    # Find all PDF files
    pdf_files = list(pdf_dir.glob("**/*.pdf"))

    print(f"Found {len(pdf_files)} PDF files to process")

    for pdf_file in pdf_files:

        print(f"\nProcessing: {pdf_file.name}")

        try:
            # Load PDF
            loader = PyMuPDFLoader(str(pdf_file))

            documents = loader.load()

            # Add metadata
            for doc in documents:
                doc.metadata["source_file"] = pdf_file.name
                doc.metadata["file_type"] = "pdf"

            all_documents.extend(documents)

            print(f"✓ Loaded {len(documents)} pages")

        except Exception as e:

            print(f"✗ Error processing {pdf_file.name}: {e}")

    print(f"\nTotal documents loaded: {len(all_documents)}")

    return all_documents


# =========================================================
# STEP 2 — SPLIT DOCUMENTS INTO CHUNKS
# =========================================================

def split_documents(
        documents,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
):
    """
    Split documents into smaller chunks
    """

    text_splitter = RecursiveCharacterTextSplitter(

        chunk_size=chunk_size,

        chunk_overlap=chunk_overlap,

        length_function=len,

        separators=[
            "\n\n",
            "\n",
            " ",
            ""
        ]
    )

    split_docs = text_splitter.split_documents(documents)

    print(f"\nSplit {len(documents)} documents into {len(split_docs)} chunks")

    # Example chunk preview
    if split_docs:

        print("\nExample Chunk:")
        print("-" * 50)

        print(split_docs[0].page_content[:300])

        print("\nMetadata:")
        print(split_docs[0].metadata)

    return split_docs


# =========================================================
# STEP 3 — EMBEDDING MANAGER
# =========================================================

class EmbeddingManager:

    def __init__(
            self,
            model_name: str = "all-MiniLM-L6-v2"
    ):

        self.model_name = model_name

        self.model = None

        self._load_model()

    def _load_model(self):

        try:

            print(f"\nLoading embedding model: {self.model_name}")

            self.model = SentenceTransformer(self.model_name)

            dimension = self.model.get_sentence_embedding_dimension()

            print("✓ Model loaded successfully")

            print(f"Embedding Dimension: {dimension}")

        except Exception as e:

            print(f"Error loading model: {e}")

            raise

    def generate_embeddings(
            self,
            texts: List[str]
    ) -> np.ndarray:

        if not self.model:
            raise ValueError("Embedding model not loaded")

        print(f"\nGenerating embeddings for {len(texts)} texts...")

        embeddings = self.model.encode(
            texts,
            show_progress_bar=True
        )

        print("✓ Embeddings generated successfully")

        print(f"Embeddings Shape: {embeddings.shape}")

        return embeddings


# =========================================================
# STEP 4 — CHROMADB VECTOR STORE
# =========================================================

class ChromaVectorStore:

    def __init__(
            self,
            persist_directory: str = "vector_db",
            collection_name: str = "rag_collection"
    ):

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        print("\n✓ ChromaDB initialized")

    def add_documents(
            self,
            chunks,
            embeddings
    ):

        print(f"\nStoring {len(chunks)} chunks in ChromaDB...")

        ids = []
        documents = []
        metadatas = []
        embedding_list = []

        for i, chunk in enumerate(chunks):

            ids.append(str(uuid.uuid4()))

            documents.append(chunk.page_content)

            metadatas.append(chunk.metadata)

            embedding_list.append(
                embeddings[i].tolist()
            )

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embedding_list
        )

        print("✓ Documents stored successfully")

    def search(
            self,
            query_embedding,
            n_results: int = 3
    ):

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

        return results


# =========================================================
# MAIN FUNCTION
# =========================================================

def main():

    print("\n" + "=" * 60)
    print("RAG PDF INGESTION PIPELINE")
    print("=" * 60)

    # -------------------------------------------------
    # STEP 1 — LOAD DOCUMENTS
    # -------------------------------------------------

    documents = process_all_pdfs(
        "data/Pdf_Folder"
    )

    if not documents:
        print("No PDF documents found")
        return

    # -------------------------------------------------
    # STEP 2 — SPLIT DOCUMENTS
    # -------------------------------------------------

    chunks = split_documents(
        documents,
        chunk_size=1000,
        chunk_overlap=200
    )

    # -------------------------------------------------
    # STEP 3 — CREATE EMBEDDINGS
    # -------------------------------------------------

    embedding_manager = EmbeddingManager()

    chunk_texts = [
        chunk.page_content
        for chunk in chunks
    ]

    embeddings = embedding_manager.generate_embeddings(
        chunk_texts
    )

    # -------------------------------------------------
    # STEP 4 — STORE IN CHROMADB
    # -------------------------------------------------

    vector_store = ChromaVectorStore()

    vector_store.add_documents(
        chunks,
        embeddings
    )

    # -------------------------------------------------
    # STEP 5 — INTERACTIVE QUESTION ANSWERING
    # -------------------------------------------------

    print("\n" + "=" * 60)
    print("RAG QUESTION ANSWERING")
    print("=" * 60)

    while True:

        query = input("\nAsk a question (or type 'exit'): ")

        if query.lower() == "exit":

            print("\nExiting RAG system...")

            break

        # Generate query embedding
        query_embedding = embedding_manager.generate_embeddings(
            [query]
        )[0]

        # Search vector database
        results = vector_store.search(
            query_embedding,
            n_results=3
        )

        print("\nTop Relevant Chunks:")
        print("-" * 60)

        retrieved_docs = results["documents"][0]

        retrieved_metadata = results["metadatas"][0]

        for i, doc in enumerate(retrieved_docs):

            print(f"\nResult {i + 1}")
            print("-" * 40)

            print(doc[:700])

            print("\nMetadata:")
            print(retrieved_metadata[i])

            print("-" * 60)


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    main()