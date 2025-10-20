# How multi-agent works with google-adk

## 🧩 1. Core Concept

The **Google ADK** is designed to let you create multiple AI agents — each specialized for a particular domain or task — and then **compose** them under a **root (or orchestrator) agent**.

Think of it like a company structure:

```
Root Agent (CEO)
│
├── Greeting Agent (welcomes users)
├── Farewell Agent (says goodbye)
└── Weather Agent (fetches weather info)
```

The root agent decides *which sub-agent* to delegate a query to, based on the user’s input and the descriptions you give to each agent.

---

## ⚙️ 2. Structure Overview

A multi-agent setup usually follows this pattern:

```python
from google.adk import Agent, Tool

# Define tools (functions that agents can use)
@Tool
def say_hello(name: str = None) -> str:
    return f"Hello, {name or 'there'}!"

@Tool
def get_weather(city: str) -> dict:
    if city.lower() == "new york":
        return {"status": "success", "report": "Sunny, 25°C"}
    return {"status": "error", "error_message": f"No info for {city}."}

# Create specialized sub-agents
greeting_agent = Agent(
    name="greeting_agent",
    model="gemini-2.0-flash",
    description="Handles greetings and introductions",
    tools=[say_hello],
)

farewell_agent = Agent(
    name="farewell_agent",
    model="gemini-2.0-flash",
    description="Handles goodbyes",
    tools=[],
)

weather_agent = Agent(
    name="weather_agent",
    model="gemini-2.0-flash",
    description="Provides weather information",
    tools=[get_weather],
)

# Create root agent and register sub-agents
root_agent = Agent(
    name="weather_agent_v2",
    model="gemini-2.0-flash",
    description="Main agent coordinating greeting, farewell, and weather agents.",
    subagents=[greeting_agent, farewell_agent, weather_agent],
)
```

---

## 🧠 3. How the Root Agent Works

When you send a query to the **root agent**, it goes through these internal steps:

1. **Intent Understanding**
   The root agent’s model (e.g. Gemini) analyzes the user message:

   > “What’s the weather in London?”
   > → detects it’s a *weather-related* query.

2. **Delegation / Routing**
   It looks at the available **sub-agent descriptions** (metadata you provided when defining them) and chooses the most relevant one — in this case, `weather_agent`.

3. **Execution**
   The root agent then forwards the query to the `weather_agent`, which may call one of its registered **tools** (like `get_weather()`).

4. **Aggregation & Response**
   Once the sub-agent returns a result, the root agent aggregates it into a final natural-language response and returns it to the user.

---

## 🧰 4. Tools vs Agents

* **Tools** are Python functions that perform concrete actions (e.g., fetch data, do math, call APIs).
* **Agents** are reasoning layers that *decide when and how* to call those tools — powered by a model like Gemini.

You can think of sub-agents as “smart wrappers” around groups of related tools.

---

## 🔗 5. Chaining Example

For instance, if you ask:

> “Hi, what’s the weather in New York?”

The call chain looks like this:

```
Root Agent (weather_agent_v2)
  ↳ Greeting Agent (say_hello) → "Hello there!"
  ↳ Weather Agent (get_weather) → "Sunny, 25°C"
Root Agent → combines both results → "Hello there! The weather in New York is sunny, 25°C."
```

The ADK handles this orchestration automatically through the Gemini model’s reasoning layer — you don’t have to manually route messages between agents.

---

## 🚀 6. Async Execution

All agent execution is **async** under the hood (`asyncio.run()` in your logs).
That’s why you see:

```
Executing using asyncio.run()...
```

This allows the root agent to delegate multiple tasks in parallel — for instance, querying multiple APIs simultaneously through different sub-agents.

---

## 🧩 7. Multi-Agent Design Benefits

| Benefit                    | Description                                                            |
| -------------------------- | ---------------------------------------------------------------------- |
| **Separation of concerns** | Each agent is focused on one domain (e.g., weather, shopping, travel). |
| **Scalability**            | You can easily add or remove sub-agents without touching the root.     |
| **Composability**          | Agents can collaborate — one agent’s output can feed another.          |
| **Explainability**         | Logs clearly show which agent handled which part of the query.         |

---

## 🧠 8. Optional: Hierarchical Agents

You can even create multi-level hierarchies:

```
Root Agent
  ├── Customer Service Agent
  │    ├── Billing Agent
  │    ├── Shipping Agent
  │    └── Returns Agent
  └── Product Info Agent
```

Each layer delegates further down as needed.
