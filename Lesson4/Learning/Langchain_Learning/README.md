# LangChain — Complete Guide

A comprehensive reference on what LangChain is, why it exists, its core components, and how it fits together with RAG, Agents, LangGraph, n8n, and real-world architectures like SQL chatbots and ecommerce assistants.

---

## Table of Contents

1. [What is LangChain?](#1-what-is-langchain)
2. [Why do we need LangChain?](#2-why-do-we-need-langchain)
3. [LangChain is NOT an LLM](#3-langchain-is-not-an-llm)
4. [What can LangChain connect?](#4-what-can-langchain-connect)
5. [Basic LangChain Architecture](#5-basic-langchain-architecture)
6. [Core Concepts](#6-core-concepts)
   - [Model](#model)
   - [Prompt](#prompt)
   - [Chain](#chain)
   - [Output Parser](#output-parser)
   - [Runnable](#runnable)
7. [Retrieval-Augmented Generation (RAG)](#7-retrieval-augmented-generation-rag)
   - [Embeddings](#embeddings)
   - [Vector Database](#vector-database)
   - [Retriever](#retriever)
   - [Full RAG Architecture](#full-rag-architecture)
8. [Tools](#8-tools)
9. [Agents](#9-agents)
   - [Agent vs Chain](#agent-vs-chain)
   - [Agent vs Workflow](#agent-vs-workflow)
10. [Memory / State](#10-memory--state)
11. [Document Loaders & Text Splitters](#11-document-loaders--text-splitters)
12. [Embedding Models](#12-embedding-models)
13. [Example Stacks](#13-example-stacks)
    - [Chroma + LangChain (RAG)](#chroma--langchain-rag)
    - [LangChain + Streamlit](#langchain--streamlit)
    - [LangChain + SQL Database](#langchain--sql-database)
    - [LangChain + APIs](#langchain--apis)
    - [LangChain + Python Stack](#langchain--python-stack)
14. [LangChain Package Structure](#14-langchain-package-structure)
15. [Execution Methods: invoke() / stream()](#15-execution-methods-invoke--stream)
16. [LangChain vs LangGraph](#16-langchain-vs-langgraph)
17. [LangChain vs n8n](#17-langchain-vs-n8n)
18. [Key Distinctions Cheat Sheet](#18-key-distinctions-cheat-sheet)
19. [Complete Real-World Example (Ecommerce Assistant)](#19-complete-real-world-example-ecommerce-assistant)
20. [The Core Mental Model](#20-the-core-mental-model)
21. [Recommended Learning Path](#21-recommended-learning-path)
22. [One-Sentence Summary](#22-one-sentence-summary)

---

## 1. What is LangChain?

LangChain is a **framework/library** used to build applications powered by **Large Language Models (LLMs)** such as GPT, Claude, Gemini, and Llama.

The simplest mental model:

```
LLM       = the brain
LangChain = the framework that connects the brain to data, tools, memory, and workflows
```

An LLM by itself cannot know things like your company's database contents. LangChain provides the plumbing to connect a model to external systems and orchestrate multi-step interactions:

```
User
  ↓
LangChain Application
  ↓
LLM
  ↓
Tool / Database / API / Documents
  ↓
Result
  ↓
LLM
  ↓
Answer
```

---

## 2. Why do we need LangChain?

Example: an ecommerce chatbot is asked *"How many orders did we receive yesterday?"*

```
Orders
--------------------------------
OrderId | Amount | Date
1       | 500    | 2026-08-10
2       | 800    | 2026-08-10
3       | 300    | 2026-08-09
```

A plain LLM has no access to this table. Without a framework, you'd manually wire together:

```
User question
      ↓
Your Python code
      ↓
Understand question
      ↓
Generate SQL
      ↓
Execute SQL
      ↓
Get result
      ↓
Send result to LLM
      ↓
Generate answer
```

LangChain provides ready-made components (prompts, chains, retrievers, SQL tools, etc.) so you don't have to build this glue code from scratch every time.

---

## 3. LangChain is NOT an LLM

This distinction matters a lot.

**Models** (GPT, Claude, Gemini, Llama) — perform understanding, generation, reasoning, summarization, classification, code generation.

**LangChain** — a framework that connects those models with other components. It does not replace the model; it **orchestrates** it.

```
User → LangChain → LLM
```

---

## 4. What can LangChain connect?

| Category | Examples |
|---|---|
| **LLMs** | OpenAI, Anthropic, Google Gemini, Ollama, Hugging Face |
| **Documents** | PDF, TXT, CSV, Word, Web pages |
| **Vector Databases** | Chroma, FAISS, Pinecone, Weaviate, Milvus |
| **Databases** | PostgreSQL, MySQL, SQL Server, SQLite |
| **APIs** | Weather, Payment, Flight, Shipping, CRM |
| **Tools** | Calculator, DB query, web search, email, Python, API calls |
| **Agents** | Decide *what* to do and *which tool* to use to answer a question |

---

## 5. Basic LangChain Architecture

```
                    USER
                      │
                      ↓
              ┌───────────────┐
              │   LangChain   │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │     Prompt    │
              └───────┬───────┘
                      │
                      ↓
                  ┌───────┐
                  │  LLM  │
                  └───┬───┘
                      │
            ┌─────────┼─────────┐
            ↓         ↓         ↓
         Database   Vector     API
                    DB
            │         │         │
            └─────────┼─────────┘
                      ↓
                    LLM
                      ↓
                    Answer
```

---

## 6. Core Concepts

The essential building blocks: **Model, Prompt, Messages, Output Parser, Chain, Runnable, Retriever, Vector Store, Tool, Agent, Memory/State.**

### Model

The LLM that actually understands and generates language.

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.1")

response = llm.invoke("What is LangChain?")
print(response.content)
```

```
LangChain → ChatOllama → Llama
```

LangChain provides a **standardized interface** across different model providers.

### Prompt

Tells the LLM how it should behave. Supports variables that get filled in at runtime.

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(
    """
    You are an ecommerce assistant.

    Answer the user's question based only
    on the provided context.

    Context:
    {context}

    Question:
    {question}
    """
)
```

`{context}` and `{question}` are variables filled with actual values before being sent to the model.

### Chain

Connecting multiple steps together — one of the most important LangChain concepts.

```
Question → Prompt → LLM → Answer
```

```python
chain = prompt | llm

response = chain.invoke({
    "context": "Product A costs ₹500.",
    "question": "What is the price?"
})
```

The `|` operator represents **composition** of components. Chains can include more steps:

```python
chain = prompt | llm | parser
```

```
User Input → Prompt → LLM → Parser → Final Result
```

### Output Parser

LLMs normally return natural language. An output parser converts that into a structured format (e.g., JSON / Python object) so your application can consume it programmatically.

```
LLM → Output Parser → Python object / JSON
```

Example target structure:

```json
{
  "product": "iPhone",
  "price": 80000,
  "available": true
}
```

### Runnable

Modern LangChain represents almost everything (Prompt, LLM, Parser, Retriever) as a **Runnable** — something that receives an input and produces an output, and can be chained together.

```
Runnable = a component that can be executed as part of a pipeline
```

This is what makes `chain = prompt | llm | parser` work consistently across component types.

---

## 7. Retrieval-Augmented Generation (RAG)

RAG lets an LLM answer using **your own data** instead of guessing.

Example: you have `company_policy.pdf` and want to ask *"What is our leave policy?"*

```
PDF
 ↓
Split into chunks
 ↓
Create embeddings
 ↓
Store in vector database
 ↓
User asks question
 ↓
Search relevant chunks
 ↓
Send chunks to LLM
 ↓
Answer
```

### Embeddings

An embedding converts text into a numeric vector representing its **semantic meaning**.

```
"How much does the product cost?"  → [0.21, -0.73, 0.45, 0.91, ...]
"What is the price of this item?"  → a similar vector
```

This enables **meaning-based search**, not just exact keyword matching.

### Vector Database

Stores embeddings so they can be searched by similarity.

```
Documents → Embeddings → Chroma
```

When a user asks a question, it's converted to an embedding, compared against stored vectors, and the closest matches are retrieved:

```
Question → Embedding → Vector search → Relevant documents → LLM → Answer
```

### Retriever

Responsible for finding relevant information from the vector store.

```python
retriever = vectorstore.as_retriever()

docs = retriever.invoke("What is the refund policy?")
```

### Full RAG Architecture

```
                    DOCUMENTS
                        │
                        ↓
                 Document Loader
                        │
                        ↓
                   Text Splitter
                        │
                        ↓
                    Embeddings
                        │
                        ↓
                  Vector Database
                     (Chroma)
                        │
                        │
                        │
USER ──→ Question ──────┘
                        │
                        ↓
                    Retriever
                        │
                        ↓
                Relevant Chunks
                        │
                        ↓
                     Prompt
                        │
                        ↓
                       LLM
                        │
                        ↓
                     Answer
```

This is one of the most common real-world LangChain use cases.

---

## 8. Tools

Beyond reading documents, an LLM can be given the ability to **perform actions** by exposing Python functions as tools.

```python
def get_order_status(order_id):
    # Query database
    return "Shipped"
```

```
Tool
 └── get_order_status()
```

The LLM (via an agent) determines *when* it needs to call that tool. Other tool examples: calculate price, query database, send email, call API, search website, book flight, create support ticket.

---

## 9. Agents

### Agent vs Chain

| | Chain | Agent |
|---|---|---|
| Workflow | **Predefined**, fixed sequence | **Dynamic** — LLM decides what to do |
| Example | `Input → Prompt → LLM → Parser → Output` | LLM picks which tool to call based on the task |

Example agent reasoning:

```
User: "What's the status of order 1234?"

I need order information.
        ↓
Use get_order_status()
        ↓
Get result
        ↓
Answer user
```

```
User: "Calculate the total cost of 5 products at ₹500 each."

I need calculation.
       ↓
Use calculator
       ↓
2500
       ↓
Answer
```

**Important:** an agent doesn't magically know everything. It can only use the tools you explicitly give it.

```
                 AGENT
                   │
          ┌────────┼────────┐
          ↓        ↓        ↓
       Database Calculator  API
```

If you don't provide a tool for your bank, database, or email system, the agent cannot access them.

### Agent vs Workflow

**Traditional (fixed) workflow** — e.g., flight booking:

```
Search Flights → Select Flight → Enter Passenger Details → Payment → Booking Confirmation
```

**Agent-driven** — e.g., *"Find me a flight from Chennai to Delhi tomorrow under ₹8,000 and book it."*

```
1. Search flights
        ↓
2. Filter price
        ↓
3. Check availability
        ↓
4. Ask user for missing information
        ↓
5. Book flight
```

The agent decides the sequence dynamically based on available tools and instructions, rather than following a hardcoded path.

Simplified agent architecture:

```
                    USER
                      │
                      ↓
                  AI AGENT
                      │
            ┌─────────┼─────────┐
            ↓         ↓         ↓
         Search     Database   Calculator
          Tool        Tool       Tool
            │         │         │
            └─────────┼─────────┘
                      ↓
                     LLM
                      ↓
                   Decision
                      ↓
                  Next Tool
                      ↓
                    Result
                      ↓
                    User
```

The LLM handles reasoning/decision-making; LangChain provides the infrastructure connecting models and tools.

---

## 10. Memory / State

Needed for conversational continuity:

```
User: My name is Siva.
...
User: What is my name?
Assistant: Your name is Siva.
```

Modern LangChain apps typically manage this via **application/agent state** rather than a single "magic memory" component.

```
Message 1 → State → Message 2 → State → Message 3
```

For advanced agents, state can include: messages, tool results, user information, workflow state, intermediate results.

---

## 11. Document Loaders & Text Splitters

**Document Loaders** bring external content (PDFs, etc.) into your application:

```
PDF → Document Loader → Documents
```

**Text Splitters** break large documents into smaller chunks (since sending an entire 100-page PDF each time is inefficient):

```
Document → Chunk 1, Chunk 2, Chunk 3, ... Chunk 500
```

Only the relevant chunks are retrieved for a given question:

```
Question: "What is the refund period?"
Retriever → Chunk 127, Chunk 128, Chunk 129
```

---

## 12. Embedding Models

Converts text into vectors for semantic search. Example using Ollama with `nomic-embed-text`:

```python
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

```
Text → Embedding Model → Vector
```

These vectors are then stored in a vector database like Chroma.

---

## 13. Example Stacks

### Chroma + LangChain (RAG)

```
                 Documents
                     │
                     ↓
              Ollama Embeddings
              nomic-embed-text
                     │
                     ↓
                  Chroma
                     │
                     ↓
                Retriever
                     │
                     ↓
                   Prompt
                     │
                     ↓
                ChatOllama
                     │
                     ↓
                  Streamlit
```

### LangChain + Streamlit

Provides a chat-style UI on top of a RAG pipeline:

```
┌─────────────────────────────────┐
│       Company RAG Assistant     │
├─────────────────────────────────┤
│ User: What is our leave policy? │
│ AI: Employees are entitled to.. │
│ ┌─────────────────────────────┐ │
│ │ Ask a question...           │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

```
Streamlit → LangChain → Retriever → Chroma → Relevant Documents → Prompt → Ollama → Answer
```

### LangChain + SQL Database

Natural-language-to-SQL chatbot:

```
User → LangChain → LLM → Generate SQL → SQL Server → Query Result → LLM → Natural Language Answer
```

Example:

```
User: "How many orders were placed yesterday?"
LLM generates: SELECT COUNT(*) FROM Orders WHERE OrderDate = ...
SQL Server → 127 orders
LLM → "You received 127 orders yesterday."
```

### LangChain + APIs

Ecommerce assistant with exposed functions:

```
get_product()
check_inventory()
get_order_status()
calculate_shipping()
create_return()
```

```
User: "Where is my order 1001?"
Agent: get_order_status(1001) → "Shipped"
Agent → User: "Your order has been shipped."
```

### LangChain + Python Stack

```
Python
 │
 ├── LangChain
 ├── LLM
 ├── Vector DB
 ├── Database
 └── APIs
```

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.1")
response = llm.invoke("Explain RAG in simple terms")
print(response.content)
```

---

## 14. LangChain Package Structure

LangChain's ecosystem is **modular** — integrations are split into separate packages:

```
langchain-core
      │
      ├── Prompts
      ├── Messages
      ├── Runnables
      └── Output parsing

langchain-openai   → OpenAI integration
langchain-ollama   → Ollama integration
langchain-chroma   → Chroma integration
langchain-community → Broader community integrations
```

This lets each integration be maintained and versioned independently.

---

## 15. Execution Methods: invoke() / stream()

`.invoke()` is the common execution interface across components:

```python
llm.invoke("Hello")
prompt.invoke(...)
retriever.invoke(...)
chain.invoke(...)
```

Meaning: *"Execute this component with this input."*

`.stream()` returns output progressively instead of waiting for the full response — useful for chat UIs where text appears incrementally:

```
Hello
Hello, how
Hello, how can
Hello, how can I
Hello, how can I help?
```

There's also `.batch()` for running multiple inputs at once.

---

## 16. LangChain vs LangGraph

| | LangChain | LangGraph |
|---|---|---|
| Purpose | Building blocks & integrations for LLM apps (Model, Prompt, Retriever, Tools, Agents) | Complex, stateful, controllable **agent workflows** |
| Best for | Straightforward chains, RAG, tool calling | Branching, loops, persistent state, human approval, multi-agent systems, durable execution |

Example LangGraph-style flow:

```
START
  ↓
Classify request
  ↓
 ┌───────────────┐
 ↓               ↓
SQL Agent      RAG Agent
 ↓               ↓
Validate       Retrieve
 ↓               ↓
 └───────┬───────┘
         ↓
       Answer
```

Mental model:

```
LangChain  → Building blocks for LLM apps
LangGraph  → Stateful graph/workflow orchestration
```

---

## 17. LangChain vs n8n

| | n8n | LangChain |
|---|---|---|
| Type | Visual workflow automation | Code-oriented LLM application framework |
| Flow | Trigger → Gmail → HTTP → Database → Slack | User → LLM → Retriever → Tools → Agent → Answer |

They can be **combined**:

```
n8n
 ↓
Trigger workflow
 ↓
Call Python API
 ↓
LangChain
 ↓
AI Agent
 ↓
Database/API
 ↓
n8n
 ↓
Send email
```

---

## 18. Key Distinctions Cheat Sheet

> **LangChain ≠ RAG.** RAG is an architecture/technique; LangChain is a framework that helps *implement* RAG.
>
> **Agent ≠ LangChain.** An agent is a type of AI application/architecture; LangChain provides tools/components for building agents.
>
> **LangChain ≠ LLM.** LangChain is the orchestration framework; the LLM is the underlying model.

| Component | Meaning |
|---|---|
| GPT / Claude / Gemini / Llama | LLM |
| Ollama | Local model runtime |
| LangChain | LLM application framework |
| Chroma | Vector database |
| Streamlit | UI framework |
| RAG | Application architecture (retrieval + generation) |
| Agent | AI system that can choose actions |
| LangGraph | Stateful agent/workflow framework |

---

## 19. Complete Real-World Example (Ecommerce Assistant)

Given a stack with:

```
SQL Server
   │
   ├── Products
   ├── Orders
   ├── Customers
   └── Payments

Product Documentation → Chroma
```

User asks: *"Why hasn't my order arrived yet?"*

```
                      USER
                        │
                        ↓
                  AI ASSISTANT
                        │
                        ↓
                      AGENT
                        │
            ┌───────────┼───────────┐
            ↓           ↓           ↓
       Order Tool   Product Tool  RAG Tool
            │           │           │
            ↓           ↓           ↓
        SQL Server    SQL Server   Chroma
            │           │           │
            └───────────┼───────────┘
                        ↓
                       LLM
                        ↓
                     Answer
```

Agent reasoning trace:

```
User wants order information
       ↓
Call get_order_status()
       ↓
Order = Shipped
       ↓
Call shipping API
       ↓
Expected delivery = tomorrow
       ↓
Answer user
```

This is what distinguishes a genuine **AI application** from simply calling an LLM once.

---

## 20. The Core Mental Model

```
                 LANGCHAIN
                     │
        ┌────────────┼────────────┐
        │            │            │
        ↓            ↓            ↓
      Models       Tools       Retrieval
        │            │            │
        ↓            ↓            ↓
      GPT        Database      Chroma
      Claude     API           Vector DB
      Gemini     Python        Documents
      Llama      Search
        │            │            │
        └────────────┼────────────┘
                     ↓
                   Agent
                     ↓
                  Application
```

---

## 21. Recommended Learning Path

| Level | Focus | Key Ideas |
|---|---|---|
| **1** | Basic LLM | `LLM → invoke() → response` |
| **2** | Prompting | `ChatPromptTemplate`, messages, variables, system/user roles |
| **3** | Chains / Runnables | `chain = prompt \| llm`, `invoke()`, `stream()`, `batch()` |
| **4** | RAG *(priority — builds on Chroma + Ollama + embeddings experience)* | Document → Loader → Splitter → Embedding → Vector DB → Retriever → Prompt → LLM |
| **5** | Tools | Expose functions like `get_order()`, `calculate()`, `search()`, `query_database()` |
| **6** | Agents | `User → Agent → LLM decides → Tool → Result → LLM → Answer` |
| **7** | LangGraph | State, Nodes, Edges, conditional routing, loops, human approval, multi-agent workflows |

---

## 22. One-Sentence Summary

> **LangChain is a framework that helps you build applications around LLMs by connecting models with prompts, data, retrieval systems, databases, APIs, tools, and agents.**

Key distinctions to remember:

```
LLM       → Brain
LangChain → Building blocks / orchestration
RAG       → Give the LLM relevant external knowledge
Tool      → Give the LLM an ability
Agent     → LLM decides which ability to use
Vector DB → Stores/searches semantic embeddings
LangGraph → Builds complex stateful agent workflows
```

If you understand these 7 things, you have the foundation needed to start building real LangChain applications.