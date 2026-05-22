import os

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chroma_db")


PROMPT = """
You are a strict RAG assistant.
Use ONLY the provided PDF context.
If the answer is not in the context, say exactly:
"The document does not provide this information."

Context:
{context}

Question:
{question}

Answer:
"""


def get_vector_db():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    return Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings
    )


def ask_question(question):
    vector_db = get_vector_db()

    results = vector_db.similarity_search_with_score(question, k=5)

    print("\nRetrieved chunk count:", len(results))

    if len(results) == 0:
        print("No chunks retrieved.")
        return

    context = ""

    for i, (doc, score) in enumerate(results, start=1):
        context += doc.page_content
        context += "\n"

    prompt = ChatPromptTemplate.from_template(PROMPT)

    llm = ChatOllama(
        model="llama3.2",
        temperature=0
    )

    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    print("\nAnswer:")
    print(response.content)

if __name__ == "__main__":
    print("Using vector DB:", DB_PATH)

    while True:
        question = input("\nAsk question from PDF or type exit: ")

        if question.lower() == "exit":
            break

        ask_question(question)