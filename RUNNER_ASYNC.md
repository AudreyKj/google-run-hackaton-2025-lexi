## 🧠 The Chain of Execution in call_agent_async

When you run:

```python
async for event in runner.run_async(
    user_id=user_id,
    session_id=session_id,
    new_message=content
):
```

This kicks off a **hierarchical process**:

---

### 1. `runner.run_async()` starts the *conversation session*

* The **runner** is like a conversation orchestrator.
* It manages sessions (`user_id`, `session_id`), stores context, and handles message passing.
* When called, it immediately forwards the new user message to the **root agent**.

---

### 2. The **root agent** receives the user message

* The root agent is your *top-level decision-maker*.
* It’s responsible for deciding *which sub-agent* or *tool* should handle this query.

For example:

```python
root_agent = adk.Agent(
    name="weather_agent_v2",
    model="gemini-2.0-flash",
    subagents=[greeting_agent, farewell_agent],
    tools=[get_weather],
)
```

When the user says:

> “What’s the weather in London?”

the root agent might reason like:

> “This looks like a weather-related question. Let’s use the `get_weather` tool.”

---

### 3. The **root agent delegates** the task

Depending on how it’s configured, the root agent can:

* Call one of its **subagents** (e.g., `greeting_agent`, `farewell_agent`)
* Or directly **invoke a tool** (like `get_weather(city)`)

This delegation happens via *function calls* that you see in logs:

```
Warning: there are non-text parts in the response: ['function_call']
--- Tool: get_weather called for city: London ---
```

The ADK framework handles these transitions automatically — you don’t explicitly code the logic to call subagents or tools; you just define their roles and capabilities.

---

### 4. The **sub-agent** handles its part

Let’s say the query was:

> “Hello, what’s the weather in New York?”

The flow might be:

```
Root agent receives "Hello, what’s the weather in New York?"
↓
Delegates "Hello" part to greeting_agent
↓
Delegates "weather" part to get_weather tool
↓
Combines responses
↓
Returns final answer
```

Each subagent acts like a specialized mini-model with its own purpose.

---

### 5. The **runner** streams all these steps back to you

As this whole process unfolds, `runner.run_async()` emits **events** like:

* `ToolCallEvent`
* `ToolResultEvent`
* `AgentResponseEvent`
* `FinalResponseEvent`

That’s what your loop is iterating over:

```python
async for event in runner.run_async(...):
```

You can inspect or log those events to see the decision chain in real time.

---

## 🧩 In short:

| Step | Who’s Acting               | What Happens                                              |
| ---- | -------------------------- | --------------------------------------------------------- |
| 1    | **Runner**                 | Sends user message to the root agent                      |
| 2    | **Root Agent**             | Interprets query and decides who handles it               |
| 3    | **Sub-Agent(s) / Tool(s)** | Perform specialized work (e.g., greeting, weather lookup) |
| 4    | **Root Agent**             | Collects and assembles results                            |
| 5    | **Runner**                 | Streams all events back as they occur                     |


