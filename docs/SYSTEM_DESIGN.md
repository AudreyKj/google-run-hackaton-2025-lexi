## Hackathon System design-

## 🧠 Overview

- **Lexi** = AI Legal Assistant
- Goal: Read a **contract** (PDF/text), **analyze** its clauses, and **explain** the risks.
- Aim: make legal work accessible + fun 
- Improves a process = Accelerates legal document understanding
- Final app: app demo mode


---

## 🧩 Architecture Diagram (Agents + API + UI)

```
                           ┌───────────────────────────────┐
                           │          Frontend (React)      │
                           │  - Upload contract (PDF/Text)  │
                           │  - View clause analysis        │
                           │  - Ask follow-up questions     │
                           └──────────────┬─────────────────┘
                                          │ JSON POST /analyze-contract
                                          ▼
                            ┌───────────────────────────────┐
                            │         FastAPI Backend       │
                            │  (Runs on Cloud Run)          │
                            │-------------------------------│
                            │ 1️⃣ Receives contract payload  │
                            │ 2️⃣ Extracts text (if PDF)     │
                            │ 3️⃣ Sends to CoreOrchestrator  │
                            │ 4️⃣ Returns structured JSON     │
                            └──────────────┬─────────────────┘
                                           │
                                           ▼
                     ┌────────────────────────────────────────────┐
                     │       Google ADK Agent System (Vertex AI)  │
                     │--------------------------------------------│
                     │  🧭 CoreOrchestrator (LLM)                 │
                     │     ├── ClauseAnalysisWorkflow (Sequential)│
                     │     │     ├─ ClauseExtractorAgent (LLM)    │
                     │     │     ├─ ClauseComparisonAgent (Embed) │
                     │     │     └─ RiskAnalysisAgent (LLM)       │
                     │     └── QuestionAnswerAgent (LLM)          │
                     └────────────────────────────────────────────┘
                                           │
                                           ▼
                           JSON response → FastAPI → React
```

---

## 🧩 Agent Descriptions + Flow

### 🧭 **CoreOrchestrator (LLM Agent)**

* **Type:** LLM Agent
* **Role:** The brain — understands user intent and routes requests.
* **Logic:**

  * If user uploaded a contract → run `ClauseAnalysisWorkflow`.
  * If user asks a question → run `QuestionAnswerAgent`.

**Input:** user payload `{ contract_text | question }`
**Output:** structured JSON (clauses, analysis, etc.)

---

### ⚙️ **ClauseAnalysisWorkflow (Sequential Agent)**

* **Type:** Sequential Agent
* **Role:** Executes the full workflow:

  ```
  Extract → Compare → Analyze
  ```
* **Sub-Agents:**

  1. **ClauseExtractorAgent**
  2. **ClauseComparisonAgent**
  3. **RiskAnalysisAgent**

**Input:** raw contract text
**Output:** JSON report combining clause details + risk analysis.

---

### 📑 **ClauseExtractorAgent (LLM Agent)**

* **Type:** LLM Agent
* **Purpose:** Extracts clauses, section titles, and terms.

**Input:** raw contract text
**Output:**

```json
{
  "clauses": [
    {"title": "Termination", "text": "Either party may terminate..."},
    {"title": "Confidentiality", "text": "The parties agree..."}
  ]
}
```

---

### 🧭 **ClauseComparisonAgent (Embedding Agent)**

* **Type:** Embedding Agent (Vertex AI Embeddings)
* **Purpose:** Compare extracted clauses to **standard templates**.
* **Uses:** Vector similarity (cosine similarity)

**Input:** extracted clauses
**Output:**

```json
{
  "comparisons": [
    {
      "clause": "Termination",
      "similarity": 0.84,
      "deviation": "Missing notice period",
    }
  ]
}
```

---

### ⚖️ **RiskAnalysisAgent (LLM Agent)**

* **Type:** LLM Agent
* **Purpose:** Assess risk level and summarize recommendations.

**Input:** comparison results
**Output:**

```json
{
  "analysis": [
    {
      "clause": "Termination",
      "risk": "Medium",
      "reasoning": "No mutual termination clause.",
      "recommendation": "Add bilateral termination condition."
    }
  ]
}
```

---

### 💬 **QuestionAnswerAgent (LLM Agent)**

* **Type:** LLM Agent
* **Purpose:** Answer follow-up questions about the contract.
* **Called on demand** by the frontend after analysis.

**Input:**

```json
{
  "question": "Does this contract allow early termination?",
  "context": { "clauses": [...], "analysis": [...] }
}
```

**Output:**

```json
{
  "answer": "Yes. Clause 9 (Termination) allows early termination with 30 days' notice."
}
```

---

## ⚙️ Data Flow (End-to-End)

1. **Frontend**

   * User uploads contract (PDF or text).
   * Sends POST request to `/analyze-contract`.

2. **FastAPI Backend**

   * Extracts text (if PDF).
   * Builds ADK content object.
   * Sends to `core_orchestrator` using `adk.run()`.
   * Waits for final structured response.
   * Returns JSON to frontend.

3. **Agents Workflow**

   * `core_orchestrator` → runs `ClauseAnalysisWorkflow`.
   * Workflow executes:

     1. `ClauseExtractorAgent`
     2. `ClauseComparisonAgent`
     3. `RiskAnalysisAgent`
   * Response aggregated and sent back.

4. **Frontend**

   * Renders clause cards with risks & recommendations.
   * Allows user to click “Ask a question” → calls `/ask-question`.

---

## 🧱 FastAPI Layer — API Example

### 🔹 Endpoint 1 — Analyze Contract

```python
from fastapi import FastAPI, Request
from adk import types
from my_agents import core_orchestrator  # your ADK orchestrator

app = FastAPI()

@app.post("/analyze-contract")
async def analyze_contract(request: Request):
    data = await request.json()
    contract_text = data.get("contract_text")
    if not contract_text:
        return {"error": "Missing contract_text"}

    content = types.Content(role="user", parts=[types.Part(text=contract_text)])

    # Run ADK workflow
    async for result in core_orchestrator.run(content):
        final_response = result

    return {"analysis": final_response.result}
```

---

### 🔹 Endpoint 2 — Ask Follow-Up Question

```python
@app.post("/ask-question")
async def ask_question(request: Request):
    data = await request.json()
    question = data.get("question")
    context = data.get("context")  # previous clauses + analysis

    if not question or not context:
        return {"error": "Missing question or context"}

    content = types.Content(
        role="user",
        parts=[types.Part(text=f"Question: {question}\nContext: {context}")]
    )

    async for result in question_answer_agent.run(content):
        final_response = result

    return {"answer": final_response.result}
```

---

### 🧾 Example Frontend Payload (POST `/analyze-contract`)

```json
{
  "contract_text": "This Agreement may be terminated by either party upon 30 days notice..."
}
```

### 🔄 Example Response

```json
{
  "analysis": {
    "clauses": [
      {"title": "Termination", "risk": "Medium", "recommendation": "Add bilateral termination rights."},
      {"title": "Confidentiality", "risk": "Low"}
    ],
    "overall_risk": "Moderate"
  }
}
```

---

## 🚀 Deployment Flow (for Hackathon)

| Step | Description                                                                   |
| ---- | ----------------------------------------------------------------------------- |
| 1️⃣  | Containerize FastAPI backend + ADK agents                                     |
| 2️⃣  | Deploy to **Google Cloud Run**                                                |
| 3️⃣  | Configure **Vertex AI API keys + credentials**                                |
| 4️⃣  | Connect **React frontend** (also deployable on Cloud Run or Firebase Hosting) |
| 5️⃣  | Demo: upload sample NDA → real-time agent analysis + question answering       |

---

## ✅ Summary of Roles

| Agent                      | Type       | Function                                |
| -------------------------- | ---------- | --------------------------------------- |
| **CoreOrchestrator**       | LLM        | Directs workflow / routing              |
| **ClauseAnalysisWorkflow** | Sequential | Runs Extract → Compare → Analyze        |
| **ClauseExtractorAgent**   | LLM        | Extracts clauses                        |
| **ClauseComparisonAgent**  | Embedding  | Compares with legal standards           |
| **RiskAnalysisAgent**      | LLM        | Assesses risk and suggests improvements |
| **QuestionAnswerAgent**    | LLM        | Answers user follow-up questions        |
