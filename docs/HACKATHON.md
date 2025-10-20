## 🧩 1. Overview

Your system will:

1. Allow users to upload or input a **contract** (text or PDF).
2. Use **multi-agents** to:

   * **Extract clauses**.
   * **Compare clauses** to **standard templates** using embeddings.
   * **Generate analysis and recommendations**.
3. Use **Google ADK (Agent Development Kit)** to orchestrate communication between agents.
4. Optionally use **Vertex AI** for embeddings and LLM reasoning.

---

## ⚙️ 2. Architecture Diagram (conceptual)

```
 ┌─────────────────────────────┐
 │           Frontend          │
 │  - Web UI / Streamlit / CLI │
 │  - Upload contract           │
 │  - Show analysis             │
 └─────────────┬───────────────┘
               │
               ▼
 ┌─────────────────────────────┐
 │         Root Agent          │
 │ (via Google ADK Runner)     │
 │ - Receives query            │
 │ - Coordinates sub-agents    │
 └─────┬───────────────────────┘
       │
 ┌─────┼──────────────────────┐
 │     │                      │
 ▼     ▼                      ▼
 │ Clause Extraction Agent    │
 │ - Extracts key clauses     │
 │ - Uses LLM or regex        │
 └───────────────┬────────────┘
                 │
                 ▼
 ┌─────────────────────────────┐
 │ Embedding Comparison Agent  │
 │ - Uses Vertex AI embeddings │
 │ - Computes similarity vs    │
 │   standard clauses          │
 └───────────────┬────────────┘
                 │
                 ▼
 ┌─────────────────────────────┐
 │ Report Generation Agent     │
 │ - Summarizes analysis       │
 │ - Generates improvement tips│
 └─────────────────────────────┘

```

---

## 🧠 3. Components

### **A. Agents (Google ADK)**

| Agent                          | Responsibility                                        | Tools                    |
| ------------------------------ | ----------------------------------------------------- | ------------------------ |
| **Root Agent**                 | Receives user request, orchestrates other agents.     | ADK runner               |
| **Clause Extraction Agent**    | Splits text into clauses (LLM, regex).                | LLM                      |
| **Embedding Comparison Agent** | Generates embeddings, compares with standards.        | Vertex AI Embeddings API |
| **Report Agent**               | Summarizes differences, creates user-friendly report. | LLM                      |

---

### **B. Data Layer**

| Type               | Description                                 | Storage                                                        |
| ------------------ | ------------------------------------------- | -------------------------------------------------------------- |
| Standard clauses   | Reference documents (JSON or text).         | Firestore / local JSON                                         |
| Uploaded contracts | User input contracts.                       | Cloud Storage / local                                          |
| Embeddings         | Precomputed embeddings of standard clauses. | Firestore / vector DB (e.g., Pinecone, Vertex Matching Engine) |

---

### **C. Vertex AI Integration**

| Purpose                        | Vertex Component              |
| ------------------------------ | ----------------------------- |
| Text embedding                 | `textembedding-gecko`         |
| Text summarization             | `gemini-pro`                  |
| Text classification (optional) | Vertex AI Model Garden models |

---

## 🚀 4. Data Flow

1. User uploads a contract.
2. Root agent triggers **Clause Extraction Agent**.
3. Extracted clauses are sent to **Embedding Comparison Agent**.
4. Embeddings are generated via **Vertex AI** and compared to standard clause embeddings.
5. **Report Agent** compiles differences and recommendations.
6. Root agent returns the consolidated output.

---

## 📅 5. 1-Week Plan

| Day       | Task                                                               |
| --------- | ------------------------------------------------------------------ |
| **Day 1** | Set up structure, agents, + test the **Root Agent** and **Runner**.|
| **Day 2** | Implement **Clause Extraction Agent** (LLM-based).                 |
| **Day 3** | Precompute embeddings for standard clauses with Vertex AI.         |
| **Day 4** | Implement **Embedding Comparison Agent**.                          |
| **Day 5** | Implement **Report Generation Agent** and end-to-end testing.      |
| **Day 6** | UI polish + error handling + deploy demo (Cloud Run or Streamlit). |

Day 7: prepare video + hackathon submission
+ add tests for backend/frontend

---

## ☁️ 6. Deployment Options

| Component        | Recommended Service        |
| ---------------- | -------------------------- |
| Backend (agents) | Cloud Run                  |
| Data storage     | Firestore or Cloud Storage |
| LLM / embeddings | Vertex AI                  |
| UI               | Streamlit / simple web app |