# Agentic AI — Concepts, Architectures & Frameworks

A conceptual reference covering the RAG Chatbot → Tool-Augmented Chatbot → Agentic AI progression, the control-vs-reliability trade-off, LangChain vs LangGraph, and worked examples (leave management, intern onboarding).

---

## 1. The Three Types of AI Systems

| Type | Reactive | Tool Use | Reasoning | Planning | Proactivity |
|---|---|---|---|---|---|
| **RAG Chatbot** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Tool-Augmented Chatbot** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Agentic AI** | ✅ | ✅ | ✅ | ✅ | ✅ |

This table is the backbone of the whole topic — each row is a **strict superset** of capabilities added to the one above it. Understanding *why* each capability is missing or present is more important than memorizing the checkmarks.

### 1.1 RAG Chatbot (Reactive only)

**What it is:** A system that only responds when asked, and its "intelligence" comes from retrieving relevant context from a knowledge base before generating an answer. It cannot act on the world — it can only read from a store and talk.

**How it works (pipeline from Image 4):**

```
Start → Documents Retrieval → Split Docs into Chunks → Vector DB → Retrieval → LLM → End
        (TextLoader)         (CharacterTextSplitter)   (FAISS)   (RetrievalQAWithSourcesChain)
```

Step by step:
1. **Documents Retrieval (`TextLoader`)** — raw source documents (PDFs, text files, web pages) are loaded into memory.
2. **Split Docs into Chunks (`CharacterTextSplitter`)** — long documents are broken into smaller overlapping chunks so they fit into the LLM's context window and so embeddings are more semantically focused.
3. **Vector DB (`FAISS`)** — each chunk is converted into an embedding (a numeric vector representing meaning) and stored in a vector database (FAISS, Chroma, Pinecone, etc.) for fast similarity search.
4. **Retrieval** — when a user asks a question, the question itself is embedded and the vector DB returns the top-K most similar chunks.
5. **LLM (`RetrievalQAWithSourcesChain`)** — the retrieved chunks are stuffed into the prompt as context, and the LLM generates an answer grounded in that context (often with source citations).

**Example from your notes:** *"Maximum number of leaves for a person"* — the leave policy document is loaded via a PDF loader, chunked, embedded, and stored in Chroma DB. When someone asks "how many leaves do I get?", the relevant policy chunk is retrieved and the LLM answers using only that text.

**Key limitation:** A RAG chatbot **cannot check your personal leave balance** or **apply for leave** — it only knows what's written in the documents. It has no access to live data (like a database of employee leave balances) and cannot perform actions.

**Use cases:** FAQ bots, documentation assistants, internal knowledge search, policy Q&A.

**Edge cases:**
- Poor chunking (too large/small) → irrelevant or fragmented context → hallucinated or wrong answers.
- Ambiguous queries with no matching chunk → LLM may hallucinate an answer instead of saying "I don't know."
- Stale vector DB (documents updated but embeddings not refreshed) → outdated answers.
- Multi-hop questions (answer needs combining 2+ unrelated document sections) → simple top-K retrieval often fails.

---

### 1.2 Tool-Augmented Chatbot (Reactive + Tool Use)

**What it is:** A chatbot that, in addition to reasoning over retrieved documents, can **call external tools/APIs** to fetch live, personalized, or actionable data. It still only reacts to a single user turn — it doesn't independently plan multi-step goals or act proactively.

**Example from your notes:** *"How many leaves do I have?"* and *"Apply for 2 days of leave"*
- The chatbot calls **one API** that has access to the HR database to fetch the user's real, live leave balance (not just the general policy text).
- To apply for leave, it calls a "create leave request" API endpoint.
- A PDF/document loader may still be used alongside this for policy questions — so this type effectively **combines** the RAG chatbot's retrieval with direct API/tool calls.

**Key difference from RAG chatbot:** RAG chatbot only *reads static documents*. Tool-Augmented chatbot can *read live/dynamic data and perform single actions* via API calls, but it's still just "one question → one tool call → one answer" — no multi-step reasoning chain, no autonomous planning across several tools.

**Use cases:** Customer support bots that check order status, banking bots that check balances, HR bots that check/apply for leave, weather bots that call a weather API.

**Edge cases:**
- Tool/API failure or timeout → chatbot must handle gracefully (retry, fallback, or say "service unavailable") rather than hallucinate a result.
- Ambiguous intent → does the user want to *check* leave or *apply* for leave? Misrouting to the wrong tool causes wrong actions.
- Authentication/authorization — the bot must ensure it's calling the API on behalf of the *correct* authenticated user (don't leak another employee's leave balance).
- Side-effect actions (like "apply for leave") need confirmation steps to avoid accidental irreversible actions.

---

### 1.3 Agentic AI (Reactive + Tool Use + Reasoning + Planning + Proactivity)

**What it is:** A system that can **reason** about a goal, **plan** a sequence of steps to achieve it, choose and orchestrate **multiple tools** across those steps, and act **proactively** — without being told the exact steps to follow. This is the full checklist, and it's what separates "agentic AI" from a chatbot.

**Example from your notes — New Intern Onboarding:**

> *Goal: "Onboard the new intern joining next Monday"* — the agent is given a high-level goal, not a script.

The agent reasons out and plans the sub-steps itself:
1. Schedule welcome meeting
2. Create intern profile in HR Management System
3. Raise an IT helpdesk ticket
4. Order a laptop
5. Generate an ID card

Each of these steps likely requires a **different tool/API** (calendar API, HRMS API, ITSM/helpdesk API, procurement system, ID-card system). The agent must:
- **Reason** about what "onboarding" actually entails (decompose a vague goal into concrete tasks).
- **Plan** the right order (e.g., HR profile might need to exist before the ID card can be generated).
- **Use tools** for each step.
- Be **proactive** — it doesn't wait for the user to ask "now create the profile," "now order the laptop" one at a time; it drives the whole workflow itself.
- Potentially **retry or replan** if a step fails (e.g., laptop out of stock → order alternate model or flag for manual approval).

**Definition (from your notes):** *"AI agent can make decisions and take actions on its own to achieve a goal without being told exactly what to do at every step."*

**Use cases:** Employee onboarding automation, autonomous research agents, multi-step customer issue resolution (diagnose → fix → notify), DevOps incident response agents, autonomous coding agents (plan → write code → test → fix → deploy).

**Edge cases:**
- **Error propagation** — a failure in step 2 (HRMS) shouldn't silently corrupt step 4 (ID card uses HRMS data); the agent needs error handling/rollback logic.
- **Infinite loops / runaway agents** — if a tool keeps failing, an agent without a step/retry limit can loop forever or spam an API.
- **Ambiguous goals** — "onboard the intern" doesn't specify department-specific steps; the agent may need to ask a clarifying question or default to a safe general process.
- **Order-dependent steps** — creating the ID card before the HR profile exists could produce inconsistent state; the agent's plan must respect dependencies.
- **Cost/safety of autonomy** — the more autonomous the agent, the higher the risk of an unintended or hard-to-reverse action (e.g., accidentally ordering 10 laptops). This is exactly the trade-off discussed in Section 2.

---

## 2. The Control vs. Reliability Trade-off

This is the concept from the "Reliability vs. Agent's level of control" diagrams (Images 2 & 3).

```
Reliability
   ▲
   |  [Simple Agent]
   |        \
   |         \___
   |             \___
   |                 \______
   |                        \___
   |                            \___[Autonomous Agent]
   |
   +--------------------------------------------------► Agent's level of control
```

**The core insight:** As you give an agent **more autonomy/control** (letting it decide its own steps, tools, and order — moving right on the x-axis), **reliability tends to drop** (moving down on the y-axis). This is because:
- More autonomous decisions = more points where the agent can make a wrong call.
- Fewer hard-coded guardrails = more unpredictable behavior.
- Long, self-directed chains of reasoning compound small errors ("error accumulation").

**Simple Agent** (top-left): Highly constrained, mostly deterministic, follows a fixed script or a single LLM call with a fixed set of next steps. Very reliable, but not flexible — it can only do what it was explicitly designed to do.

**Autonomous Agent** (bottom-right): Free to choose its own plan, tools, and sequence to achieve a goal. Very flexible and powerful, but reliability drops because there are many more ways for it to go wrong (bad tool choice, bad plan, misjudged sub-goal, etc.).

### 2.1 Where LangGraph fits (Image 3)

Image 3 adds a **purple dashed arrow** curving from the Autonomous Agent back up toward Simple Agent's reliability level, with **LangGraph** labeled as the force pulling it upward:

```
Reliability
   ▲
   | [Simple Agent] ← ← ← ← ← ← ← ← ← ← [Autonomous Agent]
   |        \          (LangGraph pulls          /
   |         \___        reliability back up)  /
   |             \___                      ___/
   |                 \______          ___/
   |                        \___  ___/
   |                            \/
   +--------------------------------------------------► Agent's level of control
```

**Interpretation:** LangGraph doesn't eliminate the control-vs-reliability trade-off, but it **mitigates** it. By giving the developer explicit structure — a graph of nodes and edges, defined state, conditional routing, retries, and checkpoints — LangGraph lets you build agents that are as flexible/autonomous as needed (right side of the x-axis) while regaining much of the reliability you'd normally lose (moving back up the y-axis). In short: **structured autonomy** rather than fully unconstrained autonomy.

---

## 3. Anatomy of an Agent Loop (Image 5)

```
Start → [LLM] ──► Step A ──► (loops back to LLM)
              ├──► Step B
              └──► [LLM] ──► Step C
                          ├──► Step D
                          └──► Step E
```

This diagram illustrates the **decision loop** at the heart of an agent:
1. **Start** feeds into the first **LLM** call — this is the "brain" that decides what to do next given the goal and current state.
2. The LLM doesn't just answer — it **outputs a decision**: which of several possible next steps (Step A, Step B, or delegate to another LLM call) to take.
3. Some branches (like Step A) **loop back** to the LLM — meaning the agent re-evaluates after taking an action, incorporating the result before deciding the next step. This is the classic **"reason → act → observe → reason again"** cycle (similar to the ReAct pattern).
4. A second **LLM** node further downstream can branch into even more specific steps (C, D, E) — showing that agent workflows can be **nested/hierarchical**, not just a single flat decision tree.

**Why this matters:** This is what "planning" and "proactivity" look like mechanically — the LLM isn't just generating text, it's repeatedly making routing decisions ("what should happen next?") based on evolving state, which is exactly what distinguishes Agentic AI from a single-shot chatbot response.

---

## 4. LangChain vs. LangGraph

| Feature | LangChain | LangGraph |
|---|---|---|
| **Purpose** | Toolkit to build LLM apps (chains, tools, agents) | Framework to manage complex workflows with state |
| **Style** | Linear or reactive chains | Graph-based; supports loops, retries, memory |
| **Best Use Case** | Simple chatbots, RAG apps, tool usage | Multi-step workflows, agents with memory, conditional paths |
| **State Handling** | Stateless or partially stateful | Fully stateful — remembers and transitions based on logic |
| **Example Use** | "Book a flight" using a flight API | "Plan a vacation" (ask budget → choose flights → book hotel → loop if error) |

### 4.1 Why this distinction matters

- **LangChain** is ideal when your task is basically a **pipeline**: input → (maybe retrieve context) → (maybe call one tool) → output. This maps directly to the **RAG Chatbot** and **Tool-Augmented Chatbot** rows in Section 1 — mostly linear, reactive flows.
- **LangGraph** is built for when the task has **branches, loops, retries, and needs to remember state across many steps** — this maps directly to **Agentic AI**. The intern onboarding example (schedule meeting → create HR profile → raise IT ticket → order laptop → generate ID card, possibly retrying failed steps) is a textbook LangGraph use case: it's a graph of dependent nodes, not a straight line.

### 4.2 Practical rule of thumb

- Single tool call, single retrieval, no branching → **LangChain** is enough (simpler, less overhead).
- Multiple tools, conditional logic ("if this fails, do that instead"), need to retain and update state across many steps, or need loops until a goal is satisfied → **LangGraph**.

**Edge cases for this decision:**
- Starting a project in plain LangChain and later needing loops/conditionals often forces a rewrite — worth evaluating early if the workflow *might* grow branches.
- LangGraph's explicit state graph adds development overhead (defining nodes, edges, state schema) — overkill for a simple single-step chatbot.
- Debugging LangGraph flows can be harder because state mutates across many nodes — good logging/checkpointing is essential.

---

## 5. Summary Table — Tying It All Together

| Concept | RAG Chatbot | Tool-Augmented Chatbot | Agentic AI |
|---|---|---|---|
| Data source | Static documents (vector DB) | Documents + live API/DB | Documents + multiple APIs/systems |
| Action capability | None (read-only) | Single action per turn | Multi-step, multi-tool actions |
| Decision-making | None — retrieve & answer | Route to one tool | Plan, sequence, and adapt across many tools |
| Typical framework | LangChain | LangChain (+ tool/function calling) | LangGraph (or LangChain agents + graph orchestration) |
| Reliability | High | High–Medium | Medium–Lower (unless structured, e.g. via LangGraph) |
| Example | "What's the leave policy?" | "How many leaves do I have? Apply for 2 days." | "Onboard the new intern joining Monday." |

---

## 6. Consolidated Edge Cases & Failure Modes to Remember

1. **RAG-specific:** stale embeddings, bad chunking, hallucination when no relevant chunk is found, multi-hop questions.
2. **Tool-Augmented-specific:** intent misclassification (check vs. act), API failures, authorization/identity leakage, missing confirmation before side-effect actions.
3. **Agentic-specific:** runaway loops, step-order/dependency violations, partial-failure state corruption, ambiguous goal decomposition, higher unpredictability as autonomy increases (Section 2's core trade-off).
4. **Cross-cutting:** cost control (more autonomous agents can make many more LLM/tool calls per task — budget/limit this), observability (logging every decision an agent makes is essential for debugging and trust), and human-in-the-loop checkpoints for high-stakes or irreversible actions (e.g., ordering hardware, applying for leave, financial transactions).

---

*This document consolidates whiteboard/course notes covering: the RAG vs Tool-Augmented vs Agentic AI capability matrix, the control-vs-reliability trade-off and LangGraph's role in mitigating it, the LLM decision-loop diagram, the RAG ingestion pipeline, and the LangChain vs LangGraph comparison table.*


LangGraph
- the simple graph consist of the nodes and edges