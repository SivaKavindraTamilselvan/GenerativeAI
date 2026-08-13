# ============================================================
# 1. Import LLM - Ollama
# ============================================================

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2")


# ============================================================
# 2. Simple LLM Query
# ============================================================

response = llm.invoke(
    "Explain large language models in one sentence"
)

print("=== Simple LLM Response ===")
print(response)


# ============================================================
# 3. ChatOllama with Messages
# ============================================================

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from langchain_ollama import ChatOllama

chat = ChatOllama(
    model="llama3.2",
    temperature=0.3
)

messages = [
    SystemMessage(
        content="You are an expert data scientist"
    ),
    HumanMessage(
        content="Write a Python script that trains a neural network on simulated data"
    )
]

response = chat.invoke(messages)

print("\n=== ChatOllama Response ===")
print(response.content)


# ============================================================
# 4. PromptTemplate
# ============================================================

from langchain_core.prompts import PromptTemplate

template = """
You are an expert data scientist with expertise in building
deep learning models.

Explain the concept of {concept} in a couple of lines.
"""

prompt = PromptTemplate(
    input_variables=["concept"],
    template=template
)


# Format the prompt manually
formatted_prompt = prompt.format(
    concept="autoencoder"
)

print("\n=== Formatted Prompt ===")
print(formatted_prompt)


# Send formatted prompt to LLM
response = llm.invoke(formatted_prompt)

print("\n=== Prompt + LLM Response ===")
print(response)


# ============================================================
# 5. LCEL Chain
# ============================================================

chain = prompt | llm

response = chain.invoke(
    {
        "concept": "autoencoder"
    }
)

print("\n=== LCEL Chain Response ===")
print(response)


# ============================================================
# 6. Second Prompt
# ============================================================

second_prompt = PromptTemplate(
    input_variables=["ml_concept"],
    template="""
Turn the concept description of {ml_concept}
and explain it to me like I'm five in 500 words.
"""
)

chain_two = second_prompt | llm


# ============================================================
# 7. Sequential Chain
# ============================================================

# First chain:
#
# concept
#    ↓
# prompt
#    ↓
# LLM
#    ↓
# explanation
#
# Then we convert the string into:
#
# {"ml_concept": explanation}
#
# Then send it to chain_two.

overall_chain = (
    chain
    | (lambda explanation_text: {
        "ml_concept": explanation_text
    })
    | chain_two
)


explanation = overall_chain.invoke(
    {
        "concept": "autoencoder"
    }
)

print("\n=== Sequential Chain Response ===")
print(explanation)


# ============================================================
# 8. Text Splitting
# ============================================================

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=0
)

texts = text_splitter.create_documents(
    [explanation]
)

print("\n=== Text Chunks ===")

for i, text in enumerate(texts):
    print(f"\nChunk {i + 1}:")
    print(text.page_content)


# ============================================================
# 9. Ollama Embeddings
# ============================================================

from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)


# ============================================================
# 10. Create Embedding
# ============================================================

query_result = embeddings.embed_query(
    texts[0].page_content
)

print("\n=== Embedding ===")
print(query_result)

print("\nEmbedding dimensions:", len(query_result))

import os
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore


# Load .env
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "langchain-quickstart")


# Create Pinecone client
pc = Pinecone(
    api_key=PINECONE_API_KEY
)


# Check whether index exists
existing_indexes = [index.name for index in pc.list_indexes()]

if INDEX_NAME not in existing_indexes:

    pc.create_index(
        name=INDEX_NAME,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )


# Connect LangChain to Pinecone
vector_store = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=embeddings
)


# Add documents
vector_store.add_documents(texts)


# Similarity search
query = "What is magical about an autoencoder?"

results = vector_store.similarity_search(
    query,
    k=3
)


print("\n=== Search Results ===")

for i, result in enumerate(results):

    print(f"\nResult {i + 1}:")
    print(result.page_content)

from langchain_experimental.agents.agent_toolkits import create_python_agent
from langchain_experimental.tools import PythonREPLTool
from langchain_ollama import ChatOllama

tool = PythonREPLTool()

agent_executor = create_python_agent(
    llm=ChatOllama(model="llama3.2", temperature=0),
    tool=tool,
    verbose=True,
    max_iterations=5,
    early_stopping_method="generate",
    handle_parsing_errors=True,
    agent_executor_kwargs={"handle_parsing_errors": True}
)

agent_executor.run(
    "Find the roots (zeros) of the quadratic function 3*x**2 + 2*x - 1. "
    "Use sympy to compute the roots, and make sure to call print() on the "
    "final result so the output is visible. Do not just define variables — "
    "always print the answer."
)