import os
import streamlit as st

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

@st.cache_resource
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

    for (doc, score) in results:
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

    return response.content,results


st.title("Chat")
st.write("Ask question from the pdf uploaded")
st.sidebar.header("Vector DB")
st.sidebar.subheader("The project implement the basic RAG concepts")
st.sidebar.write("Used Ollama model for this purpose")
st.sidebar.write("The Pdf is basic need for a library management")
question = st.text_input("What is your question?")

if st.button("Ask question"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Loading vectors..."):
            answers ,result = ask_question(question)

        st.subheader(f"Answer: {answers}")
        st.write(answers)

        st.subheader("Retrieved chunk count:")

        for i, (doc, score) in enumerate(result, start=1):
            with st.expander(f"Chunk #{i}"):
                st.write(doc.page_content)
