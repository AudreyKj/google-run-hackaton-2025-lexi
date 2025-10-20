## 🧩 **System Overview: Multi-Agent Contract Analyzer**

| Agent                             | Responsibility                                                                                                                        | Tools                                 |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| 🧠 **Root Agent**                 | Entry point for the user’s request. Orchestrates the workflow by routing tasks to specialized agents and aggregating their responses. | Google ADK `Runner`, FastAPI endpoint |
| ✂️ **Clause Extraction Agent**    | Processes the raw contract text to extract meaningful clauses using LLM reasoning and/or regex heuristics.                            | `LLM` (Gemini 2.0 / Gemini 1.5 Pro)   |
| 🧮 **Embedding Comparison Agent** | Generates embeddings for each clause, compares them with pre-stored “standard” clause embeddings to find deviations.                  | **Vertex AI Text Embeddings API**     |
| 📊 **Report Agent**               | Interprets comparison results, scores the risks, and creates a **structured, visual-friendly report** for the frontend.               | `LLM` (Gemini)                        |

---

## ⚙️ **Workflow**

1. **User uploads or pastes contract text** → API sends it to the **Root Agent**.
2. **Root Agent** delegates:

   * Step 1 → `Clause Extraction Agent`
   * Step 2 → `Embedding Comparison Agent`
   * Step 3 → `Report Agent`
3. The agents communicate asynchronously via the ADK runner (so you can trace logs like `--- Tool: compare_embeddings called ---`).
4. **Final JSON** is returned to the UI, ready for visualization (e.g. colored highlights, icons).

---

### 🔁 Example Orchestration Flow

```text
User → Root Agent
        ├── Clause Extraction Agent → Extracted Clauses
        ├── Embedding Comparison Agent → Clause Scores
        └── Report Agent → Final JSON Report
```

### 🧠 Example of Returned Report

```json
[
  {
    "clause": "Confidentiality",
    "similarity": 0.92,
    "risk": "low",
    "feedback": "Clause matches standard template."
  },
  {
    "clause": "Termination",
    "similarity": 0.48,
    "risk": "high",
    "feedback": "Missing early termination clause."
  }
]
```

---

## 🧠 **Why This Is Great for the Hackathon**

| Criteria                           | How Your Design Excels                                                                                                                    |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Technical Implementation (40%)** | Each agent has a clear single responsibility. Uses **LLM** + **Vertex Embeddings API** + **ADK orchestration**.                           |
| **Demo & Presentation (40%)**      | Easy to visualize: show contract → highlight differences → display concise report. No need for chatbot UI.                                |
| **Innovation & Creativity (20%)**  | Tackles a real-world pain point (contract review) in an *interactive, AI-assisted* way. Multi-agent reasoning is natural and explainable. |

---

## ☁️ **Deployment Architecture (Cloud Run)**

```
                     ┌────────────────────────────┐
                     │        Frontend (React)    │
                     │  - Upload file             │
                     │  - Display results visually│
                     └────────────┬───────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │   Cloud Run Backend    │
                      │   (FastAPI + ADK)      │
                      │                        │
                      │  Root Agent            │
                      │   ├─ Clause Agent      │
                      │   ├─ Embedding Agent   │
                      │   └─ Report Agent      │
                      └──────────┬─────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │        Google Cloud Services        │
              │-------------------------------------│
              │  Vertex AI Embeddings               │
              │  Firestore (standard clause store)  │
              │  Cloud Storage (contract uploads)   │
              └─────────────────────────────────────┘
```

---

## 💡 Next Steps

To get this production-ready (and demo-ready in 1 week):

1. **Day 1–2:**

   * Build FastAPI endpoint
   * Implement Root Agent orchestration
   * Mock sub-agents’ responses for testing

2. **Day 3:**

   * Implement Clause Extraction Agent (LLM + regex fallback)

3. **Day 4:**

   * Implement Embedding Comparison Agent using Vertex AI Embeddings
   * Prepare reference clause embeddings (JSON or Firestore)

4. **Day 5:**

   * Implement Report Agent (LLM summarization + risk levels)

5. **Day 6:**

   * Integrate everything + deploy to **Cloud Run**

6. **Day 7:**

   * Polish presentation + logs + demo flow
