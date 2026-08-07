# Simple Gmail Agent — n8n Workflow

An AI agent built in n8n that chats with a user, understands natural language requests, and sends emails on their behalf through Gmail — using Groq as the LLM, a memory buffer for conversation context, and Gmail's API as a callable "tool."

---

## 1. What This Workflow Does

You type a message into the n8n chat window (e.g. "send an email to john@x.com about the meeting"). The **AI Agent** node reads your message, decides whether it has enough information, and if it does, calls the **Send Email** tool to actually send the Gmail message — then confirms back to you in chat. If information is missing (recipient, subject, or body), the agent asks for it instead of guessing.

---

## 2. Workflow Architecture (Node-by-Node)

```
[When chat message received] → [AI Agent] → [Edit Fields] → (output/end)
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              [Chat Model]     [Memory]         [Tool]
              Groq Chat Model  Simple Memory    Send Email (Gmail)
```

### 2.1 When chat message received (Trigger)
- This is a **Chat Trigger** node — it opens n8n's built-in chat window and starts the workflow every time you send a message.
- Output includes `chatInput` (your typed text) and a `sessionId` (a unique ID for that chat session, used for memory).

### 2.2 AI Agent (the brain)
This is the central **AI Agent** node (LangChain Agent type in n8n). It has three special connection types feeding into it, shown as dashed lines:

| Connection | Purpose |
|---|---|
| **Chat Model** | The LLM that powers reasoning — here, **Groq Chat Model** |
| **Memory** | Gives the agent short-term conversational memory — **Simple Memory** |
| **Tool** | An action the agent is *allowed* to call — **Send Email** (Gmail) |

The Agent node itself doesn't send the email — it *decides* when to call the Send Email tool, and *extracts* the right values (to/subject/body) from the conversation to pass into it.

### 2.3 Groq Chat Model (LLM connection)
- Connected to the Agent's **Chat Model** input.
- Requires a **Groq API credential** (API key from console.groq.com).
- This is the model doing the actual language understanding/reasoning — parsing your message, deciding what's missing, and formatting the tool call.
- You can swap this for OpenAI, Anthropic Claude, Gemini, etc. — n8n treats any of these as a pluggable "Chat Model" sub-node; the Agent logic doesn't change.

### 2.4 Simple Memory (Memory buffer connection)
- Connected to the Agent's **Memory** input.
- Type: **Simple Memory (Buffer Window Memory)** — keeps the last N exchanges of the conversation in memory so the agent remembers earlier turns (e.g., recalling "my name is Siva Kavindra" a few messages later).
- Key settings:
  - **Session ID → "Session Key From Previous Node"**: uses `{{ $json.sessionId }}` from the Chat Trigger, so each chat session has its own isolated memory (two different users/chats won't mix up context).
  - **Context Window Length**: number of past message pairs to retain and send to the model on each turn. Larger = more context but more tokens used per call.
- Note (as n8n shows): the session is scoped to *this* memory node only. If you had multiple memory nodes and wanted them to share history, you'd switch to "Define Below" and hardcode the same session key in each.

### 2.5 Send Email (Tool connection → Gmail node used as a Tool)
- Connected to the Agent's **Tool** input — this turns a normal Gmail node into something the *agent* can call automatically, not something that runs unconditionally every execution.
- Node settings:
  - **Credential**: Gmail OAuth2 credential (see Section 4 — requires Gmail API enabled in Google Cloud).
  - **Resource**: Message
  - **Operation**: Send
  - **To**: `{{ $fromAI("emailAddress") }}`
  - **Subject**: `{{ $fromAI("subject") }}`
  - **Message**: `{{ $fromAI("message") }}`
  - **Append n8n Attribution**: optional footer toggle (can be turned off for cleaner client emails).
- `$fromAI(...)` is a special n8n expression: instead of you hardcoding a value, it tells the LLM "you decide what value belongs here, based on the conversation," and the Agent fills it in automatically at runtime when it decides to call this tool.
- **Tool Description** (optional field) helps the LLM understand *when* to use this tool versus not — useful if you add more tools later (e.g., "use this tool only to send emails, not to read them").

### 2.6 Edit Fields (post-processing, optional)
- A simple **Set** node placed after the Agent.
- Used here to manually shape/rename the final output fields before the workflow ends (e.g., cleaning up what gets returned to the chat UI or logged). Not required for the agent to function — it's a convenience/formatting step.

---

## 3. The System Message (Agent's Instructions)

This is the most important configuration on the AI Agent node — it's the persistent instruction set the LLM follows on every single turn:

```
You are an email-sending assistant. Your only job is to send an email using the "Send Email" tool available to you.
You will receive:
- A recipient email address
- A subject or topic for the email
- The content or message to include
Your task:
1. Call the "Send Email" tool with the correct "to", "subject", and "body" fields.
2. Write the body in a clear, professional tone based on the information given.
3. Always include a greeting and a short closing line.
4. Do not invent information that wasn't provided to you — only use what's given in the input.
5. After sending, respond with a short confirmation: who the email was sent to and the subject line used.
Do not do anything other than compose and send the email.
```

Why each rule matters:
- **Rule 1** — forces tool use instead of the LLM just *pretending* to send an email in chat text.
- **Rule 2–3** — controls tone/formatting so emails look human-written and professional, not robotic.
- **Rule 4** — prevents hallucination (e.g., the LLM must not invent a fake email address or make up content you never gave it).
- **Rule 5** — gives you a predictable, parseable confirmation message after every send.
- **Final line** — scopes the agent narrowly so it doesn't wander into unrelated tasks (a common agent-design best practice: single responsibility).

Other Agent node fields visible in your screenshots:
- **Source for Prompt (User Message)** → set to expression, using `{{ $json.chatInput }}` (whatever the user typed becomes the "user message" sent to the LLM each turn).
- **Require Specific Output Format** — off here (not using structured/JSON output).
- **Enable Fallback Model** — off here, but useful in production to auto-switch to a backup LLM if Groq is down or rate-limited.

---

## 4. Enabling Gmail API in Google Cloud (Required Setup)

Before the Send Email node will work, you need OAuth2 credentials tied to a Google Cloud project with the Gmail API turned on:

1. Go to **console.cloud.google.com** and create (or select) a project.
2. Navigate to **APIs & Services → Library**, search for **Gmail API**, and click **Enable**.
3. Go to **APIs & Services → OAuth consent screen**:
   - Choose **External** (or Internal if using Google Workspace).
   - Fill in app name, support email, and add your Gmail address as a **test user** (required while the app is in "Testing" mode).
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**.
   - Add n8n's OAuth redirect URI (found inside the Gmail credential screen in n8n, e.g. `https://<your-n8n-domain>/rest/oauth2-credential/callback`).
   - Save the **Client ID** and **Client Secret**.
5. In n8n, create a new **Gmail OAuth2** credential, paste in the Client ID/Secret, and click **Sign in with Google** — authorize access to your Gmail account.
6. Attach this credential to the **Send Email** node.

Common pitfalls (matches issues you've hit before in your other integrations):
- Forgetting to add yourself as a test user → "Access blocked" error.
- Wrong or missing redirect URI → OAuth callback fails silently.
- Gmail API not enabled on the *same* project the OAuth client belongs to.

---

## 5. Testing the Agent (Walkthrough of Your Screenshots)

Your test conversation shows the memory and reasoning working correctly:

| Turn | User Input | Agent Behavior | What It Proves |
|---|---|---|---|
| 1 | *(opens chat)* | Agent greets and asks for recipient, subject, message | System message is being followed — agent won't act without full info |
| 2 | "my name is siva kavindra" | Agent acknowledges name, still asks for the 3 required fields | Agent correctly ignores irrelevant info and stays on-task (per Rule 4/5) |
| 3 | "what is my name" | Agent correctly answers "Siva Kavindra" | **Simple Memory is working** — it recalled a fact from 2 turns earlier via the buffered session |

In the n8n **Logs** panel (right side), you can inspect exactly what happened on each Agent execution:
- **INPUT** tab shows the raw values passed into the Agent: `action: sendMessage`, `sessionId`, and `chatInput`.
- **OUTPUT** tab shows the Agent's generated response, confirming it processed memory + chat model correctly (here: 1,248 tokens used, success in 1.431s).
- The **Simple Memory** node shows "2 items" — confirming two prior exchanges were stored and retrieved for context.

To fully test the *email-sending* path (not shown yet in your screenshots), you'd continue the conversation with something like:
```
Send an email to test@example.com, subject "Project Update", 
saying the capstone deployment is complete.
```
The Agent should then: extract `to`/`subject`/`message` → call the Send Email tool via `$fromAI()` → Gmail sends it → Agent replies with a confirmation line.

---

## 6. Key n8n Concepts Demonstrated in This Workflow

- **Agent vs. Tool nodes**: Only nodes connected to the Agent's dashed "Tool" input are *optionally* invoked by the LLM's own reasoning — they don't run automatically like normal linear workflow nodes.
- **`$fromAI()` expression**: Lets the LLM populate a field dynamically at runtime instead of you hardcoding static values — this is what makes the Gmail node "AI-callable" rather than a fixed action.
- **Session-scoped memory**: Using `{{ $json.sessionId }}` keeps each chat conversation's memory isolated, which matters once multiple users/chats hit the same workflow.
- **System Message as guardrails**: The single most powerful lever for controlling agent behavior — narrow, explicit, numbered instructions reduce hallucination and scope creep.

---

## 7. Possible Extensions

- Add a **second tool** (e.g., "Search Gmail" or "Get Contacts") so the agent can look up an email address by name instead of requiring you to type it.
- Add **Require Specific Output Format** with a JSON schema if you want to log every sent email to a database/sheet alongside the chat.
- Add an **Enable Fallback Model** (e.g., OpenAI or Claude) so the workflow doesn't break if Groq is rate-limited.
- Swap the Chat Trigger for a **Gmail Trigger** to make this fully autonomous (auto-reply/auto-send based on incoming mail) rather than manually chat-driven.