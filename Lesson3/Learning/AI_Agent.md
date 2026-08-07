# AI Agents & Tool Calling — Complete Concept Guide

A reference document explaining how LLM-powered AI agents decide which tools to call, what happens when tools are missing, and how to write good tool descriptions — with real examples drawn from an e-commerce agent (`GetProduct`, `DownloadImage`, `ValidateProduct`, `CancelOrder`, `RefundPayment`).

---

## Table of Contents

1. [The Core Idea: The LLM Is the Brain](#1-the-core-idea-the-llm-is-the-brain)
2. [Walkthrough: Validating a Product](#2-walkthrough-validating-a-product)
3. [Where Does This Reasoning Come From?](#3-where-does-this-reasoning-come-from)
4. [Is the LLM Actually "Thinking"?](#4-is-the-llm-actually-thinking)
5. [Traditional Program vs AI Agent](#5-traditional-program-vs-ai-agent)
6. [What If the LLM Makes a Bad Decision?](#6-what-if-the-llm-makes-a-bad-decision)
7. [Scenarios: What Happens When a Tool Is Missing](#7-scenarios-what-happens-when-a-tool-is-missing)
8. [Should You Tell the LLM What to Do?](#8-should-you-tell-the-llm-what-to-do)
9. [Case Study: Cancel Order vs Refund Payment](#9-case-study-cancel-order-vs-refund-payment)
10. [Writing Good Tool Descriptions](#10-writing-good-tool-descriptions)
11. [Business Rules: Description vs Backend Code](#11-business-rules-description-vs-backend-code)
12. [Best-Practice Template for Any Tool](#12-best-practice-template-for-any-tool)
13. [Key Takeaways / Cheat Sheet](#13-key-takeaways--cheat-sheet)

---

## 1. The Core Idea: The LLM Is the Brain

In an AI agent system, the **LLM is the decision-maker**. Your application code is the **executor**. The LLM never directly touches your database, APIs, or files — it only *decides* what should happen next. Your code is responsible for actually doing it, safely.

```
User asks something
        │
        ▼
  LLM reads the request
        │
        ▼
     LLM thinks
        │
        ▼
    LLM decides
  "I need Tool A"
        │
        ▼
   Tool executes
        │
        ▼
  LLM gets result
        │
        ▼
    LLM decides
  "I now need Tool B"
        │
        ▼
     Continue...
        │
        ▼
    Final answer
```

**Key point:** nobody hard-codes *"always call Tool A first, then Tool B."* The LLM figures out the sequence dynamically, based on the user's goal and the tools it has access to.

---

## 2. Walkthrough: Validating a Product

Imagine your agent has these tools:

| Tool | Purpose |
|---|---|
| `GetProduct(productId)` | Fetches product details |
| `DownloadImage(imageUrl)` | Downloads an image from a URL |
| `ValidateProduct(image, description)` | Checks if the image matches the description |
| `SendEmail()` | Sends an email |

**User:** *"Validate product 101."*

### Step-by-step reasoning

```
Step 1 — User Prompt
  "Validate product 101"
  LLM thinks: "I don't know anything about product 101.
               There's a GetProduct tool. I'll use it."

Step 2 — Tool Executes
  GetProduct(101) → { Name: "Nike Shoes", Image: "shoe.png",
                       Description: "Running shoes" }

Step 3 — LLM Thinks Again
  "I have the image URL, but I can't 'see' URLs directly.
   There's a DownloadImage tool. I'll call it."

Step 4 — Tool Executes
  DownloadImage("shoe.png") → image bytes

Step 5 — LLM Thinks Again
  "Now I have both description and image.
   There's a ValidateProduct tool. I'll call it."

Step 6 — Tool Executes
  ValidateProduct(image, description) → { Match: 98%, Issues: none }

Step 7 — LLM Concludes
  "Goal completed. I'll explain the result."
  → "The product matches its image. Confidence: 98%."
```

### Full Flow Diagram

```
                User
                  │
                  ▼
        "Validate Product 101"
                  │
                  ▼
          LLM (Brain)
                  │
      Reads available tools
                  │
                  ▼
     Decides: GetProduct()
                  │
                  ▼
        Application runs tool
                  │
                  ▼
         Returns product data
                  │
                  ▼
          LLM reasons again
                  │
                  ▼
     Decides: DownloadImage()
                  │
                  ▼
        Application runs tool
                  │
                  ▼
           Returns image
                  │
                  ▼
          LLM reasons again
                  │
                  ▼
     Decides: ValidateProduct()
                  │
                  ▼
        Application runs tool
                  │
                  ▼
        Returns validation
                  │
                  ▼
      LLM explains the result
```

---

## 3. Where Does This Reasoning Come From?

During training, LLMs are exposed to enormous amounts of text and code containing recurring goal → action patterns, such as:

```
Need weather          →  Use Weather API
Need customer details →  Query database
Need email             →  Use email service
Need calculation       →  Use calculator
```

The model doesn't memorize one fixed workflow per task. Instead, it learns a general skill: **connect a goal, the tools currently available, and the most plausible next action.** That's why it can generalize to tools and situations it has never seen before, as long as the tool descriptions are clear.

---

## 4. Is the LLM Actually "Thinking"?

Not in the human sense — there's no consciousness or intention involved. What the LLM actually does, mechanically, is:

1. Understand the user's request.
2. Read the available tool descriptions.
3. Predict the most appropriate next action, based on patterns learned during training.
4. Repeat this after every tool result comes back.

This repeated *predict → observe → predict again* loop produces behavior that **looks like planning**, even though it's really just next-step prediction conditioned on everything seen so far.

---

## 5. Traditional Program vs AI Agent

### Traditional Program (hard-coded)

```
User
  │
  ▼
if request == "Validate"
  │
  ▼
GetProduct()
  │
  ▼
DownloadImage()
  │
  ▼
Validate()
  │
  ▼
Return
```
The developer wrote the exact sequence in advance. It never changes, regardless of context.

### AI Agent (dynamic)

```
User
  │
  ▼
LLM
  │
  ▼
"I need GetProduct."
  │
  ▼
Tool runs
  │
  ▼
LLM
  │
  ▼
"Now I need DownloadImage."
  │
  ▼
Tool runs
  │
  ▼
LLM
  │
  ▼
"Now I need Validate."
  │
  ▼
Tool runs
  │
  ▼
LLM
  │
  ▼
Goal complete.
```

| | Traditional Program | AI Agent |
|---|---|---|
| Who decides the sequence? | Developer (fixed at code time) | LLM (decided at runtime) |
| Adapts to new phrasing/context? | No | Yes |
| Can skip unnecessary steps? | No | Yes, if goal is already satisfied |
| Can combine tools in new ways? | No | Yes |
| Risk of unpredictable behavior? | Low | Higher — needs guardrails |

---

## 6. What If the LLM Makes a Bad Decision?

This can genuinely happen — especially with vague tool names/descriptions.

**Example — dangerous ambiguity:**

Tools available: `GetWeather()`, `SendEmail()`, `DeleteDatabase()`

User: *"What's the weather today?"*

If tool descriptions are confusing or poorly scoped, a poorly guided LLM could pick the wrong tool. This is a real risk in agent systems, not a hypothetical.

### How developers reduce this risk

- Write **clear, specific** tool names and descriptions.
- **Restrict** which tools are available for a given context (principle of least privilege).
- Add explicit **system instructions**, e.g. *"Never delete data unless the user explicitly requests it."*
- **Validate** tool inputs and outputs in the application layer — never trust the LLM's call blindly.

---

## 7. Scenarios: What Happens When a Tool Is Missing

A very common question: *"If the tool it needs isn't available, does the LLM rethink using what it has, or do I need to explicitly tell it?"*

**Answer:** The LLM automatically reasons using only the tools it's been given. It cannot invent capabilities it doesn't have — but it *can* substitute a different available tool if that tool's description indicates it can achieve the same goal.

### Scenario 1 — Required tool exists ✅

Tools: `GetProduct()`, `DownloadImage()`, `ValidateProduct()`

```
Need product   → GetProduct()
Need image     → DownloadImage()
Need validation→ ValidateProduct()
```
Everything works as expected.

### Scenario 2 — A required tool is missing ⚠️

Tools: `GetProduct()`, `ValidateProduct()` — **no** `DownloadImage()`

```
Need product → GetProduct()
Need image   → "I don't have a tool to download images."
```

Possible outcomes:
- The LLM tells the user it cannot complete the task (missing capability).
- It asks the user to upload the image directly.
- If `ValidateProduct()`'s description says it accepts an image **URL** directly (no download needed), it may just pass the URL straight through.

The outcome depends entirely on how the tools are described.

### Scenario 3 — A different tool can substitute ✅

Tools: `GetProduct()`, `FetchFile()`, `ValidateProduct()` — no `DownloadImage()`, but `FetchFile()` is described as *"Downloads any file from a URL."*

```
Need image → No DownloadImage tool
           → But FetchFile can download files
           → Use FetchFile instead
```

The LLM reasons by capability, not by exact tool name — as long as the description makes the capability clear.

### Scenario 4 — No alternative exists at all ❌

Tools: `GetProduct()`, `SendEmail()`, `Calculator()`

User: *"Translate this PDF into French."*

```
Need translation → no tool
Need PDF reader   → no tool
→ Cannot invent a translation tool.
→ Must say it lacks the capability, or ask user for the content in a usable form.
```

### Analogy: The Chef in the Kitchen

| Situation | What the chef does |
|---|---|
| All ingredients (flour, eggs, butter) available | Makes the cake normally |
| Butter missing, but oil available | Substitutes oil, *if* it's a reasonable, known substitute |
| No suitable substitute exists | Says: *"I can't make this cake with what I have"* — doesn't fake it |

The LLM behaves the same way: it examines available tools, picks the best one (or combination), and if nothing fits, it **explains the limitation instead of fabricating a result.**

---

## 8. Should You Tell the LLM What to Do?

**Yes — but not by hardcoding steps.** Instead of scripting the exact sequence, guide the LLM with two things:

### A. Good tool descriptions

| Bad ❌ | Good ✅ |
|---|---|
| `Tool: Tool1` — no description | `Tool: FetchFile` — *"Downloads a file from a URL and returns its contents."* |

A vague description gives the LLM nothing to reason with. A precise one tells it exactly when the tool is applicable.

### B. General behavioral rules (not fixed workflows)

Example system instruction:

```
If the required tool is unavailable:
1. Look for another tool that provides equivalent functionality.
2. If none exists, ask the user for the missing information
   or explain the limitation.
3. Never invent tool results.
```

These are **rules of behavior**, not a rigid step-by-step script — the LLM still decides how to apply them in context.

---

## 9. Case Study: Cancel Order vs Refund Payment

This is a critical real-world example, because confusing these two tools could cause serious business/financial errors.

**Tools:**
- `GetOrder()`
- `RefundPayment()`
- `SendNotification()`
- (no `CancelOrder()` in this version)

User: *"Cancel my order."*

```
Need CancelOrder()
    │
    ▼
Not available.
    │
    ▼
Can RefundPayment() substitute? → NO.
Refunding money ≠ cancelling an order.
    │
    ▼
Correct response:
"I don't have a tool available to cancel orders."
```

**Critical rule:** the LLM must **never pretend** an order was cancelled just because a superficially "related" tool (`RefundPayment`) exists. Semantic similarity is not the same as functional equivalence — this is exactly why **descriptions must be precise about what a tool does and does NOT do.**

### Now with `CancelOrder()` added

Tools:
- `CancelOrder()` — *"Cancels an order if its status is Pending or Processing. Returns the updated order status."*
- `RefundPayment()` — *"Refunds the customer's payment. Only use after an order has been cancelled or when a refund is approved."*

User: *"Cancel order #100."*

```
Need cancellation
       │
       ▼
   Use CancelOrder()
       │
       ▼
   Order cancelled
       │
       ▼
 Was payment already made?
       │
       ▼
        Yes
       │
       ▼
  Use RefundPayment()
       │
       ▼
       Done
```

Notice: the LLM chains **two** tools together correctly, purely because the descriptions told it the relationship between them ("only use after order has been cancelled").

---

## 10. Writing Good Tool Descriptions

If a tool has an important **side effect** (charges money, deletes data, sends communications, changes order state), its description must make that side effect explicit — otherwise the LLM is reasoning blind.

### Bad Description ❌
```
Tool Name: RefundPayment
Description: Handles orders.
```
Problems this causes — the LLM doesn't know:
- Does it cancel the order?
- Does it only refund money?
- Does it update the database?
- Does it notify the customer?

### Better Description ✅
```
Tool Name: RefundPayment
Description:
  Refunds the payment for an eligible order.
  Does NOT cancel the order.
  Should only be used after the order has been cancelled
  or when a refund has been approved.
```

With this description, when the user says *"Cancel my order,"* the LLM reasons:

```
Need to cancel the order.
I have RefundPayment.
Its description says: it does NOT cancel orders.
→ I should NOT use it.
```

This is exactly the correct, safe behavior.

---

## 11. Business Rules: Description vs Backend Code

A key design question: *"Should every business rule go into the tool description?"*

**Answer: rules related to *when/how to use the tool* go in the description. But the rule must ALSO be enforced in your backend code — always, no exceptions.**

### In the description (guides the LLM's decision)

```
RefundPayment

Description:
  Refunds the customer's payment.

Rules:
  - Only for Paid orders.
  - Do not use for Cash on Delivery orders.
  - Do not use before the order is cancelled.
```

### In the application code (enforces the rule regardless of LLM behavior)

```csharp
RefundPayment(orderId)
{
    if (order.Status != Cancelled)
        throw new Exception("Order must be cancelled first.");

    if (order.PaymentStatus != Paid)
        throw new Exception("No payment to refund.");

    // Process refund
}
```

### Why both layers matter

Think of it like instructing an employee:

> "Use the refund system only after the order has been cancelled."

That's the *guidance*. But the refund **system itself** should also reject invalid requests, independent of whether the employee (or LLM) followed the instruction correctly.

```
   Tool Description                Application Logic
  (guides the LLM)                (enforces safety)
        │                                │
        ▼                                ▼
  "Only use after            if (order.Status != Cancelled)
   order is cancelled"            throw Exception(...)
        │                                │
        └──────────► Both layers work together ◄──────────┘
```

> **Even if the LLM makes a mistake, your backend prevents an invalid action from actually happening.** The LLM decides *what* to attempt; your code decides *whether it's allowed* and *how it's carried out safely.*

---

## 12. Best-Practice Template for Any Tool

Use this checklist every time you define a new tool for an agent:

```
Name:            <ToolName>
Purpose:         <One-sentence description of what it does>
When to use:     <Preconditions / appropriate context>
When NOT to use: <Explicit exclusions, common confusions>
Inputs:          <Parameters and types>
Output:          <What is returned, including error format>
Side effects:    <Money movement, data deletion, notifications, etc.>
Backend safety:  <What the application layer re-validates,
                  regardless of what the LLM decided>
```

**Example — filled in for RefundPayment:**

```
Name:            RefundPayment
Purpose:         Refunds a customer's payment for an order.
When to use:     After an order has been cancelled, or when a
                 refund has been explicitly approved.
When NOT to use: Do NOT use to cancel orders.
                 Do NOT use for unpaid / Cash on Delivery orders.
Inputs:          orderId
Output:          Refund status, or an error if preconditions fail.
Side effects:    Moves money out of the merchant account;
                 may trigger a customer notification.
Backend safety:  Reject if order.Status != Cancelled.
                 Reject if order.PaymentStatus != Paid.
```

---

## 13. Key Takeaways / Cheat Sheet

- **The LLM is the brain, your code is the hands.** The LLM decides *what* to do next; the application executes it and enforces the rules.
- **No hard-coded workflow.** The LLM chooses tool order dynamically based on the goal and what's currently available — this is what makes it "agentic" rather than a simple if/else script.
- **Reasoning comes from patterns learned in training** — goal → tool → next goal → next tool — generalized to new situations via tool descriptions, not memorized scripts.
- **The LLM isn't conscious.** It predicts the most plausible next action step by step; the illusion of "planning" emerges from repeating that loop.
- **Missing tools ≠ broken agent.** The LLM will: (1) use an existing tool if it fits, (2) substitute a different tool if its description supports the needed capability, or (3) explicitly say it lacks the capability. It should **never fabricate** having done something it couldn't do.
- **Similar-sounding tools are not interchangeable.** `RefundPayment` is not `CancelOrder` — descriptions must make functional boundaries explicit to prevent dangerous mix-ups.
- **Descriptions are your main steering wheel.** Precise names, clear purpose, explicit "when to use / when NOT to use," and documented side effects directly shape agent reliability.
- **Defense in depth:** put usage guidance in the tool description (guides the LLM) **and** enforce the same rule in backend code (guarantees safety even if the LLM errs). Never rely on the LLM alone for anything with real-world consequences (money, data deletion, irreversible actions).
- **General rules > rigid scripts.** Give behavioral principles ("if no tool fits, ask the user or explain the limitation; never invent results") rather than trying to hardcode every possible path.

---

### Quick Reference: Decision Flow for "Tool Missing?"

```
                    Need a capability
                          │
                          ▼
              Is there an exact-match tool?
                    │            │
                   Yes           No
                    │            │
                    ▼            ▼
                Use it.   Does another available tool's
                          description cover this capability?
                                │            │
                               Yes           No
                                │            │
                                ▼            ▼
                          Use that tool   Tell the user the
                          as substitute.  capability is missing,
                                          or ask for what's needed.
                                          NEVER fabricate a result.
```



# AI Agents — Workflow vs Tools, Developer vs LLM Responsibilities & Full Working Code

A companion guide to `AI-Agents-Tool-Calling-Concepts.md`. That file covered *how the LLM picks a tool and what happens when a tool is missing*. This file covers a different, equally important layer: **who is responsible for what** when you build an agent, and a complete, runnable Python example — with tool descriptions, the agent loop, and the LLM decision logic all laid out separately so you can see exactly where each piece lives.

---

## Table of Contents

1. [Fixed Workflow vs AI Agent — The Core Distinction](#1-fixed-workflow-vs-ai-agent--the-core-distinction)
2. [Functions/Tools ≠ Workflow](#2-functionstools--workflow)
3. [The Trade-off: Why Not Just Hard-Code Everything?](#3-the-trade-off-why-not-just-hard-code-everything)
4. [What the Developer Provides vs What the LLM Decides](#4-what-the-developer-provides-vs-what-the-llm-decides)
5. [The Chef Analogy](#5-the-chef-analogy)
6. [Important Clarification: "Workflow" Has Two Meanings](#6-important-clarification-workflow-has-two-meanings)
7. [Full Working Example — Flight Booking Agent](#7-full-working-example--flight-booking-agent)
   - [Folder Structure](#folder-structure)
   - [tools.py — The Capabilities](#toolspy--the-capabilities)
   - [prompt.py — The Tool Descriptions](#promptpy--the-tool-descriptions)
   - [llm.py — The Decision Logic (Simulated Brain)](#llmpy--the-decision-logic-simulated-brain)
   - [agent.py — The Agent Loop](#agentpy--the-agent-loop)
   - [main.py — Entry Point](#mainpy--entry-point)
8. [Tracing the Execution Step by Step](#8-tracing-the-execution-step-by-step)
9. [Where Exactly Is the Description Used?](#9-where-exactly-is-the-description-used)
10. [From Simulation to a Real LLM](#10-from-simulation-to-a-real-llm)
11. [How Real Frameworks (OpenAI SDK, LangChain) Hide This](#11-how-real-frameworks-openai-sdk-langchain-hide-this)
12. [Key Takeaways / Cheat Sheet](#12-key-takeaways--cheat-sheet)

---

## 1. Fixed Workflow vs AI Agent — The Core Distinction

### Case 1: Normal Python Functions (NOT an AI Agent)

```python
def book_ticket():
    flights = search_flights()
    booking = book_flight(flights[0])
    payment = make_payment(booking["price"])
    send_email()
```

```
search_flights()
      │
      ▼
book_flight()
      │
      ▼
make_payment()
      │
      ▼
send_email()
```

**Who decided this order? → You, the developer.** This is a fixed, hard-coded workflow. It runs the exact same sequence every single time, regardless of what the user actually asked for. It is not an AI agent — it's a normal program that happens to call some functions.

### Case 2: AI Agent

You provide the **same kind of functions**, plus a couple more:

```python
def search_flights(): ...
def book_flight(): ...
def make_payment(): ...
def send_email(): ...
def cancel_booking(): ...
```

But this time you **do not** write the calling sequence yourself. You hand the functions to the LLM and let it decide.

**User A:** *"Book the cheapest flight."*

```
Need flights   → search_flights()
Need booking   → book_flight()
Need payment   → make_payment()
Need email     → send_email()
```

**User B:** *"Cancel my ticket and refund my money."*

```
cancel_booking()
      │
      ▼
refund_payment()
      │
      ▼
send_email()
```

**Same toolbox. Two completely different sequences** — because the LLM read the goal and reasoned about which tools apply, in what order, for *that specific request*.

---

## 2. Functions/Tools ≠ Workflow

This is where a lot of beginners get confused: they assume *"the functions themselves are the workflow."* They aren't.

| Concept | Definition |
|---|---|
| **Functions / Tools** | What the AI is *capable* of doing — the raw building blocks. |
| **Workflow** | The specific *order* in which those functions get executed for a given goal. |
| **Fixed Workflow** | The developer decides the sequence, once, at code-writing time. |
| **AI Agent** | The LLM decides the sequence dynamically, at run time, based on the user's goal. |

Visually — the same five tools support two entirely different workflows:

```
Available Functions
────────────────────
search_flights()
book_flight()
cancel_booking()
refund_payment()
send_email()


Workflow 1 (goal: book a flight)      Workflow 2 (goal: cancel a flight)
─────────────────────────────         ─────────────────────────────
search_flights()                      cancel_booking()
       │                                     │
       ▼                                     ▼
book_flight()                         refund_payment()
       │                                     │
       ▼                                     ▼
make_payment()                        send_email()
       │
       ▼
send_email()
```

The tools didn't change. **The workflow changed because the goal changed** — and the LLM is the one re-deriving that workflow every time.

---

## 3. The Trade-off: Why Not Just Hard-Code Everything?

This is the practical trade-off between the two approaches from Case 1 vs Case 2 above:

| | Fixed Workflow (traditional code) | AI Agent (LLM-decided) |
|---|---|---|
| **Predictability** | 100% predictable — same input, same steps, every time | Less predictable — the LLM can choose a different path for a phrasing you didn't anticipate |
| **Flexibility** | Zero — a new type of request (e.g. "cancel my ticket") needs a brand-new function written by hand | High — the same toolbox can handle brand-new *combinations* of requests without new code, as long as suitable tools already exist |
| **Development effort per new scenario** | You must write and wire a new sequence for every new use case | Often nothing — the LLM composes existing tools in a new order |
| **Debuggability** | Easy — you can read the code and know exactly what will happen | Harder — you must log/trace what the LLM actually decided at runtime |
| **Safety / correctness guarantees** | Strong — nothing happens that you didn't explicitly write | Weaker on its own — needs backend validation, restricted tool sets, and clear descriptions to stay safe (see the companion doc's section on backend enforcement) |
| **Best suited for** | Narrow, well-defined, repetitive processes where the steps never change (e.g. a nightly batch job) | Open-ended, conversational, multi-intent situations where the *user's exact goal* varies request to request |

**In short:** a fixed workflow trades flexibility for predictability. An AI agent trades some predictability for the ability to handle goals you never explicitly coded for — *as long as the right tools exist in the toolbox and their descriptions are precise.* This is exactly why, in practice, most production systems use a **hybrid**: critical, fixed sequences (payment processing, refunds) stay as hard-coded, validated backend logic, while the *decision of when to invoke them* is left to the LLM.

---

## 4. What the Developer Provides vs What the LLM Decides

### Everything below is written by YOU, the developer

```
                 Developer
                     │
──────────────────────────────────
 1. Choose the LLM (e.g. GPT-5, Claude)
 2. Create the tools (functions)
 3. Write tool descriptions
 4. Connect APIs / databases
 5. Write the system prompt
 6. Build the agent loop
──────────────────────────────────
```

**1. The LLM**
```python
model = GPT-5()
```
Without a model, there is no reasoning at all.

**2. Tools**
```python
def search_flights(): ...
def book_flight(): ...
def cancel_booking(): ...
def refund(): ...
def send_email(): ...
```
The AI cannot write these itself — it can only *call* what you give it.

**3. Tool Descriptions**
```
search_flights
Description: Search available flights between two cities.

book_flight
Description: Books a selected flight.
```
This is the text the LLM actually reads to decide *when* a tool applies.

**4. System Prompt**
```
You are a flight booking assistant.
Always search for flights before booking.
Never book without user confirmation.
Use the available tools whenever required.
```
This sets behavioral guardrails and priorities.

**5. Agent Loop**
```python
while not finished:
    ask LLM
    execute tool
    send result back
    repeat
```
This control structure is entirely your code — the LLM never writes or manages it.

**6. APIs / Database connections**
```
search_flights()
      │
      ▼
   IndiGo API
      │
      ▼
 Air India API
      │
      ▼
 SpiceJet API
```
The LLM cannot reach these systems on its own; your functions are the only bridge.

### Everything below is decided by the LLM at runtime

```
User Goal
    │
    ▼
Understand Goal
    │
    ▼
Choose Tool
    │
    ▼
Observe Result
    │
    ▼
Choose Next Tool
    │
    ▼
Repeat
    │
    ▼
Return Answer
```

### Side-by-side summary

| Developer Provides | AI Agent (LLM) Decides |
|---|---|
| LLM / model | Which tool to use |
| Tools / functions | When to use the tool |
| Tool descriptions | Order of tool execution (dynamic workflow) |
| APIs & database connections | Whether another tool is needed |
| System prompt | When the goal is complete |
| Agent loop / framework | Final response to the user |

### One important limit

The LLM **cannot invent new tools.** If a user asks for something with no matching capability —

```
User: "Book a train ticket."

Available tools:
  search_flights()
  book_flight()
  cancel_booking()

LLM reasons:
  "I need a train search tool..."
  → doesn't exist
  → "I don't have access to a train booking tool."
```

It will never silently fabricate a `search_trains()` function. Only the developer can add that.

---

## 5. The Chef Analogy

```
You (Developer) provide:          Chef (LLM) decides:
──────────────────────            ────────────────────
🍳 Kitchen                        Cut vegetables
🔪 Knife                          Boil water
🍲 Stove                          Add spices
🥘 Ingredients                    Cook rice
📖 Rules                          Serve
```

You never told the chef the exact sequence of knife-cuts and stove-timings. You gave them a kitchen, tools, ingredients, and rules — and the chef (LLM) figured out the steps to reach the goal ("make dinner").

---

## 6. Important Clarification: "Workflow" Has Two Meanings

It's tempting to say *"the AI decides the workflow"* — but that phrase can be misleading. There are two very different senses of "workflow":

1. **Architectural pattern** (e.g. Prompt Chaining, Parallelization, Routing, Orchestrator-Worker) — **the developer still decides this.** You choose the overall shape of the system in advance.
2. **Sequence of tool calls within the agent's execution loop** — **the LLM decides this**, dynamically, per request.

```
Developer decides (architecture level):
  "This system will use a single agent with a loop
   that can call any of these 5 tools."

LLM decides (execution level):
  "For THIS specific user request, I will call
   tool A, then tool C, then tool B."
```

So the accurate statement is:

> The LLM decides the **sequence of actions (tool calls)** needed to achieve the user's goal — not the overall **architectural pattern** the agent runs inside of. That distinction is the key to understanding AI agents correctly.

---

## 7. Full Working Example — Flight Booking Agent

This is a complete, framework-free, beginner-friendly implementation so you can see every moving part with nothing hidden. Later, real frameworks (OpenAI Agents SDK, LangChain) automate steps 2–4 below, but the underlying mechanics are identical.

### Folder Structure

```
flight_agent/
│── main.py
│── tools.py
│── agent.py
│── llm.py
│── prompt.py
```

### `tools.py` — The Capabilities

These are the actual capabilities the agent can execute. The LLM does not know these exist yet — this file is pure logic, no AI involved.

```python
# tools.py

def search_flights(source, destination, date):
    """Searches available flights between two cities on a given date."""
    print("Searching flights...")

    return [
        {
            "flight_id": 101,
            "airline": "IndiGo",
            "price": 4500
        },
        {
            "flight_id": 102,
            "airline": "Air India",
            "price": 5200
        }
    ]


def book_flight(flight_id):
    """Books a flight using its flight_id and returns a booking confirmation."""
    print("Booking flight...")

    return {
        "booking_id": "BK12345",
        "price": 4500
    }


def make_payment(amount):
    """Processes payment for the given amount."""
    print("Processing payment...")

    return {
        "status": "Success"
    }


def send_email(booking_id):
    """Sends a booking confirmation email."""
    print("Sending email...")

    return {
        "status": "Email Sent"
    }


def cancel_booking(booking_id):
    """Cancels an existing booking using its booking_id."""
    print("Cancelling booking...")

    return {
        "booking_id": booking_id,
        "status": "Cancelled"
    }


def refund_payment(booking_id):
    """Refunds the payment associated with a cancelled booking."""
    print("Refunding payment...")

    return {
        "booking_id": booking_id,
        "status": "Refunded"
    }
```

### `prompt.py` — The Tool Descriptions

**This is the piece that answers "where does the description live?"** The LLM cannot read your Python source code — it only ever sees text. So every tool needs a plain-English description that gets sent to the model alongside the user's request.

```python
# prompt.py

TOOLS = [
    {
        "name": "search_flights",
        "description": "Search available flights between two cities on a given date.",
        "parameters": ["source", "destination", "date"]
    },
    {
        "name": "book_flight",
        "description": "Book a flight using the flight id returned by search_flights.",
        "parameters": ["flight_id"]
    },
    {
        "name": "make_payment",
        "description": "Pay the booking amount for a confirmed flight booking.",
        "parameters": ["amount"]
    },
    {
        "name": "send_email",
        "description": "Send a confirmation email after a booking or cancellation is completed.",
        "parameters": ["booking_id"]
    },
    {
        "name": "cancel_booking",
        "description": "Cancel an existing booking using its booking id. Does NOT process a refund.",
        "parameters": ["booking_id"]
    },
    {
        "name": "refund_payment",
        "description": "Refund the payment for a booking. Only use this AFTER the booking has been cancelled.",
        "parameters": ["booking_id"]
    }
]


SYSTEM_PROMPT = """
You are a flight booking assistant.

Rules:
- Always search for flights before booking.
- Never book without knowing the flight price.
- If the user wants to cancel, call cancel_booking BEFORE refund_payment.
- Only use tools that are explicitly listed below.
- If no suitable tool exists for the user's request, say so — never invent a result.

Available Tools:
""" + "\n".join(
    f"- {t['name']}: {t['description']}" for t in TOOLS
)
```

Notice the description for `cancel_booking` explicitly says *"Does NOT process a refund"* and `refund_payment` says *"Only use this AFTER the booking has been cancelled"* — this is exactly the disambiguation technique from the companion document (Section 9, Cancel Order vs Refund Payment) applied here.

### `llm.py` — The Decision Logic (Simulated Brain)

In a real system, GPT/Claude would read `SYSTEM_PROMPT` + `TOOLS` + the conversation `history`, and generate the next action itself. Here we **simulate** that reasoning with plain `if` statements so you can see the decision pattern clearly before plugging in a real model.

```python
# llm.py

def decide_next_action(history):
    """
    Simulates what an LLM would decide, given the conversation history so far.
    In a real agent, this function is replaced by an actual API call to
    GPT / Claude, which reads SYSTEM_PROMPT + TOOLS + history and returns
    the next tool to call (or a finish signal).
    """

    last = history[-1]

    # First decision — right after the user's request
    if last["type"] == "user":
        user_text = last["content"].lower()

        if "cancel" in user_text:
            return {
                "tool": "cancel_booking",
                "arguments": {"booking_id": "BK12345"}
            }

        return {
            "tool": "search_flights",
            "arguments": {
                "source": "Chennai",
                "destination": "Delhi",
                "date": "Tomorrow"
            }
        }

    # Booking flow
    if last["tool"] == "search_flights":
        cheapest = min(last["result"], key=lambda f: f["price"])
        return {
            "tool": "book_flight",
            "arguments": {"flight_id": cheapest["flight_id"]}
        }

    if last["tool"] == "book_flight":
        return {
            "tool": "make_payment",
            "arguments": {"amount": last["result"]["price"]}
        }

    if last["tool"] == "make_payment":
        return {
            "tool": "send_email",
            "arguments": {"booking_id": "BK12345"}
        }

    # Cancellation flow
    if last["tool"] == "cancel_booking":
        return {
            "tool": "refund_payment",
            "arguments": {"booking_id": last["result"]["booking_id"]}
        }

    if last["tool"] == "refund_payment":
        return {
            "tool": "send_email",
            "arguments": {"booking_id": last["result"]["booking_id"]}
        }

    # Either flow finishes after send_email
    if last["tool"] == "send_email":
        return {
            "finish": True,
            "message": "Task completed successfully."
        }
```

> ⚠️ **Important:** This file stands in for what an LLM would normally do. In a real AI agent, an actual model generates these decisions by reading the tool descriptions and conversation history — there are no hardcoded `if` statements. We use them here purely to make the *flow* visible and debuggable before adding real AI.

### `agent.py` — The Agent Loop

This is the heart of every AI agent — the piece the developer builds once, and which then drives *any* goal the LLM decides to pursue using the available tools.

```python
# agent.py

from tools import (
    search_flights,
    book_flight,
    make_payment,
    send_email,
    cancel_booking,
    refund_payment,
)
from llm import decide_next_action


tool_map = {
    "search_flights": search_flights,
    "book_flight": book_flight,
    "make_payment": make_payment,
    "send_email": send_email,
    "cancel_booking": cancel_booking,
    "refund_payment": refund_payment,
}


def run_agent(user_input):
    history = []

    history.append({
        "type": "user",
        "content": user_input
    })

    while True:
        # Ask the "LLM" what to do next
        action = decide_next_action(history)

        if action.get("finish"):
            print(f"\n✅ {action['message']}")
            break

        tool_name = action["tool"]
        arguments = action["arguments"]

        print(f"\nAI chose tool: {tool_name}({arguments})")

        tool = tool_map[tool_name]
        result = tool(**arguments)

        history.append({
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        })
```

### `main.py` — Entry Point

```python
# main.py

from agent import run_agent

# Example 1: booking flow
run_agent("Book me the cheapest flight from Chennai to Delhi tomorrow.")

print("\n" + "=" * 50 + "\n")

# Example 2: cancellation flow — same tools, different workflow
run_agent("Cancel my ticket and refund my money.")
```

Running `python main.py` produces two entirely different tool-call sequences from the exact same toolbox, purely because `decide_next_action` (standing in for the LLM) read the *goal* differently each time.

---

## 8. Tracing the Execution Step by Step

### Booking request: *"Book me the cheapest flight..."*

```
User
 │
 ▼
Book cheapest flight
 │
 ▼
Agent Loop starts
 │
 ▼
LLM thinks → search_flights()
 │
 ▼
Result: [IndiGo ₹4500, Air India ₹5200]
 │
 ▼
LLM thinks again → book_flight(101)
 │
 ▼
Result: booking_id BK12345, price 4500
 │
 ▼
LLM thinks again → make_payment(4500)
 │
 ▼
Result: Success
 │
 ▼
LLM thinks again → send_email(BK12345)
 │
 ▼
Result: Email Sent
 │
 ▼
LLM: "Task completed successfully."
```

### Cancellation request: *"Cancel my ticket and refund my money."*

```
User
 │
 ▼
Cancel ticket + refund
 │
 ▼
Agent Loop starts
 │
 ▼
LLM thinks → cancel_booking(BK12345)
 │
 ▼
Result: Cancelled
 │
 ▼
LLM thinks again → refund_payment(BK12345)
 │
 ▼
Result: Refunded
 │
 ▼
LLM thinks again → send_email(BK12345)
 │
 ▼
Result: Email Sent
 │
 ▼
LLM: "Task completed successfully."
```

Same `tool_map`, same `run_agent()` loop, same six functions — **two different workflows**, purely driven by what the user asked for.

---

## 9. Where Exactly Is the Description Used?

This is the detail that trips up most beginners. The descriptions in `prompt.py` are **not executed as code.** They are plain text that gets bundled into the prompt sent to the LLM. Something like this actually gets sent to GPT/Claude behind the scenes:

```
You are a Flight Booking Assistant.

Available Tools:

Tool: search_flights
Description: Search available flights between two cities.

Tool: book_flight
Description: Book a flight using flight id.

Tool: make_payment
Description: Pay booking amount.

Tool: send_email
Description: Send booking confirmation.

Tool: cancel_booking
Description: Cancel an existing booking. Does NOT process a refund.

Tool: refund_payment
Description: Refund payment. Only use AFTER cancel_booking.

User:
Book me the cheapest flight.
```

The LLM reads this whole block as **plain natural language** and reasons over it:

```
Need flights.
      │
      ▼
"search_flights" description matches best.
      │
      ▼
Call it.
```

**Key insight:** the description text lives in the *prompt*, not in the function body. `tools.py` contains the logic that actually runs; `prompt.py` contains the explanation the LLM uses to decide *when* to run it. These are two separate concerns, kept in two separate files on purpose.

---

## 10. From Simulation to a Real LLM

To turn `llm.py` from a simulation into a real reasoning engine, you'd replace `decide_next_action()` with an actual API call — e.g. using the Anthropic API with tool use:

```python
# llm.py (real version, conceptual)

import anthropic
from prompt import TOOLS, SYSTEM_PROMPT

client = anthropic.Anthropic()

def decide_next_action(history):
    # Convert TOOLS (our simple dicts) into the API's tool schema
    api_tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": {
                "type": "object",
                "properties": {p: {"type": "string"} for p in t["parameters"]},
                "required": t["parameters"],
            },
        }
        for t in TOOLS
    ]

    messages = build_messages_from_history(history)  # convert history → API message format

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        tools=api_tools,
        messages=messages,
    )

    # Look for a tool_use block in the response
    for block in response.content:
        if block.type == "tool_use":
            return {"tool": block.name, "arguments": block.input}

    # No tool call → the model considers the task finished
    return {"finish": True, "message": response.content[0].text}
```

Everything else — `tools.py`, `agent.py`, `main.py` — **stays exactly the same.** That's the whole point of separating concerns this way: the agent loop and the tools don't care whether the "brain" is a simulated `if` chain or a real model.

---

## 11. How Real Frameworks (OpenAI SDK, LangChain) Hide This

In production frameworks, you don't write `decide_next_action`, `tool_map`, or the `while True` loop by hand. You typically just annotate functions:

```python
@tool
def search_flights(source, destination, date):
    """Search available flights between two cities."""
    ...

@tool
def book_flight(flight_id):
    """Book a flight using the flight id."""
    ...
```

The framework then automatically:

```
1. Reads each function's docstring/signature → becomes the "description"
2. Sends tool names + descriptions to the LLM
3. Receives the LLM's chosen tool + arguments
4. Calls the actual Python function
5. Sends the result back to the LLM
6. Repeats until the LLM signals it's finished
```

This is **exactly** the `tools.py` + `prompt.py` + `llm.py` + `agent.py` structure you just built — just automated and hidden behind decorators and a managed loop. Understanding the manual version first makes it much easier to debug what a framework is doing when something goes wrong.

---

## 12. Key Takeaways / Cheat Sheet

- **Tools ≠ Workflow.** Tools are what the agent *can* do; workflow is the *order* it does them in for a specific goal.
- **Fixed code = developer decides the order, once, forever.** **AI agent = the LLM decides the order, dynamically, per request** — using the exact same toolbox.
- **Trade-off:** fixed workflows are predictable and safe but inflexible; AI agents are flexible and handle novel goal combinations, but need descriptions, system prompts, and backend validation to stay safe and correct.
- **Developer responsibility:** LLM choice, tool functions, tool descriptions, system prompt, the agent loop, and all API/database connections.
- **LLM responsibility:** which tool to call, when, in what order, whether another call is needed, and when the goal is complete.
- **The LLM cannot invent tools.** If nothing in the toolbox fits, it must say so — never fabricate a result (see companion doc, Section 7).
- **Descriptions live in the prompt, not in the function body.** `tools.py` (logic) and `prompt.py` (descriptions) are intentionally separate files/concerns.
- **"Workflow" is ambiguous** — architectural pattern (developer-chosen, fixed at design time) vs sequence of tool calls (LLM-chosen, dynamic at run time). Keep these two senses separate when reasoning about "who decided what."
- **Frameworks don't change the architecture** — they just automate the wiring between your functions, their descriptions, and the model's tool-use API, using the same loop shape you built by hand here.