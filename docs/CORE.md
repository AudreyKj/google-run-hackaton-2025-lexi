## 🌐 1. High-Level Concept

**App Name:** `ai-legal-assistant`
**Goal:** Help users analyze contracts interactively:

* Explain complex clauses in plain English
* Compare clauses against industry standards
* Suggest safer or fairer rephrasings

---

## 🧠 2. Agent Architecture (Multi-Agent Structure)

We’ll use **4 agents** communicating through the ADK runner:

| Agent                                         | Purpose                                                                             | Tools                                   | Key Behavior                                         |
| --------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------- | ---------------------------------------------------- |
| 🏛️ **Root Agent (“LegalOrchestratorAgent”)** | Main conductor — decides which sub-agent to invoke based on user intent             | Delegates, manages session state        | Routes between agents; keeps track of document state |
| 📄 **ClauseAnalyzerAgent**                    | Breaks contract text into clauses, identifies key legal terms, and explains meaning | `extract_clauses()`, `explain_clause()` | Summarizes clauses in simple terms                   |
| ⚖️ **ComplianceCheckerAgent**                 | Compares clauses against a standards dataset (GDPR, SaaS templates, etc.)           | `check_against_standard()`              | Flags unusual or risky clauses                       |
| ✍️ **RephrasingAgent**                        | Suggests improved or safer rephrasings for clauses                                  | `suggest_rewrite()`                     | Uses LLM to rewrite with user tone preference        |

Optional (for UX):
🗣️ **UI/Interaction Agent** (in your web app) that reformats responses into conversational summaries.

---

## 🧩 3. Flow Overview

```
User -> Root Agent
          |
          ├── ClauseAnalyzerAgent
          |       ↳ extract_clauses(), explain_clause()
          |
          ├── ComplianceCheckerAgent
          |       ↳ check_against_standard()
          |
          └── RephrasingAgent
                  ↳ suggest_rewrite()
```

---

## ⚙️ 4. State & Memory Design

Use the same **`InMemorySessionService`** for now (for Cloud Run demo), or replace with **Firestore / Redis** later.

### Example state structure:

```python
{
  "user_name": "Audrey",
  "uploaded_contract_text": "...",
  "current_clause_index": 0,
  "clauses_explained": [],
  "compliance_flags": [],
  "rephrasing_suggestions": [],
  "user_preference_tone": "professional"
}
```

State flows naturally through each tool call via `tool_context.state`.

---

## 🔧 5. Tools per Agent

Here’s an example set of **core tools**:

```python
def extract_clauses(contract_text: str) -> list[str]:
    """Splits contract into clauses based on numbered or bullet patterns."""
    # Simple heuristic for prototype
    return re.split(r'\n\d+\.|\n•|\n-', contract_text)

def explain_clause(clause: str) -> str:
    """Explains a legal clause in plain English."""
    return f"This clause means that {LLM_EXPLANATION}"

def check_against_standard(clause: str) -> dict:
    """Compares a clause against standard contract data."""
    return {"status": "risky", "reason": "Clause limits user’s termination rights"}

def suggest_rewrite(clause: str, tone: str) -> str:
    """Suggests safer or fairer rephrasing of a clause."""
    return f"Suggested rewrite ({tone} tone): {LLM_REWRITE}"
```

Each of these tools can be wrapped with ADK’s `FunctionTool`.

---

## 🧩 6. Agent Definitions

```python
clause_analyzer_agent = Agent(
    name="clause_analyzer",
    model=LiteLlm(model="gemini-2.0-flash"),
    instruction="Extract and explain contract clauses in plain English using provided tools.",
    tools=[extract_clauses, explain_clause]
)

compliance_checker_agent = Agent(
    name="compliance_checker",
    model=LiteLlm(model="gemini-2.0-flash"),
    instruction="Check clauses against legal standards and flag risky terms.",
    tools=[check_against_standard]
)

rephrasing_agent = Agent(
    name="rephrasing_agent",
    model=LiteLlm(model="gemini-2.0-flash"),
    instruction="Suggest safer or fairer rewordings for legal clauses.",
    tools=[suggest_rewrite]
)

root_agent = Agent(
    name="legal_orchestrator",
    model=LiteLlm(model="gemini-2.0-flash"),
    instruction=(
        "You are the Legal Orchestrator Agent. Based on the user query, decide whether "
        "to analyze, check compliance, or suggest rephrasing. Delegate accordingly."
    ),
    sub_agents=[clause_analyzer_agent, compliance_checker_agent, rephrasing_agent],
    tools=[],
    output_key="latest_response"
)
```

---

## 🏃 7. Runner + Session Service

```python
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="ai_legal_assistant",
    session_service=session_service
)
```

---

## 💬 8. User Interaction Example

```python
async def main():
    await session_service.create_session(
        app_name="ai_legal_assistant",
        user_id="user1",
        session_id="session1",
        state={"user_preference_tone": "friendly"}
    )

    await call_agent_async(
        "Can you analyze this contract and explain it simply?",
        runner,
        user_id="user1",
        session_id="session1"
    )

    await call_agent_async(
        "Compare clause 3 with standard SaaS terms.",
        runner,
        user_id="user1",
        session_id="session1"
    )

    await call_agent_async(
        "Can you rewrite clause 4 in a friendlier tone?",
        runner,
        user_id="user1",
        session_id="session1"
    )
```

---

## ☁️ 9. Deployment to Google Cloud Run

**Step-by-step:**

1. **Add requirements.txt**

   ```
   google-adk
   fastapi
   uvicorn
   ```
2. **Add FastAPI entrypoint** for Cloud Run:

```python
from fastapi import FastAPI, Request
import asyncio

app = FastAPI()

@app.post("/query")
async def query(request: Request):
    body = await request.json()
    query = body.get("query", "")
    response = await call_agent_async(query, runner, "user1", "session1")
    return {"response": response}
```

3. **Dockerfile**

   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

4. **Deploy:**

   ```bash
   gcloud run deploy ai-legal-assistant \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

---

## 🛡️ 10. Guardrails (Optional)

You can reuse your existing callback pattern to enforce legal domain safety:

* Block certain jurisdictions (“Do not analyze EU contracts”)
* Filter sensitive PII (“Remove names before processing”)

Attach these via:

```python
before_model_callback=block_keyword_guardrail,
before_tool_callback=block_paris_tool_guardrail
```

---

## 🎯 Summary

✅ **4 agents** working together
✅ **Stateful orchestration**
✅ **Explain + compare + rewrite workflow**
✅ **Deployable on Cloud Run**
✅ **Easily demoable in < 5 min**
