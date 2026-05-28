import os
import shutil

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_FOLDER = os.path.join(BASE_DIR, "data", "Pdf_Folder")
DB_PATH = os.path.join(BASE_DIR, "chroma_db")


def load_pdfs():
    documents = []

    print("PDF folder:", PDF_FOLDER)

    for file_name in os.listdir(PDF_FOLDER):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file_name)

            print("Loading PDF:", pdf_path)

            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            for page in pages:
                page.metadata["source_file"] = file_name

            documents.extend(pages)

    if not documents:
        raise Exception("No PDF content loaded.")

    return documents


def create_vector_db():
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        print("Old vector DB deleted.")

    documents = load_pdfs()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=10
    )

    chunks = splitter.split_documents(documents)

    print("Total pages loaded:", len(documents))
    print("Total chunks created:", len(chunks))

    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    print("Vector DB created at:", DB_PATH)


if __name__ == "__main__":
    create_vector_db()