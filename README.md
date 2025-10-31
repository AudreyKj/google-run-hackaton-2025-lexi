
📘 Lexi — Multi-Agent Legal Document Assistant

## Table of Contents

- [Features](#features)
- [Multi-Agent System Overview](#multi-agent-system-overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Inspiration](#inspiration)
- [What it does](#what-it-does)
- [How we built it](#how-we-built-it)
- [Challenges we ran into](#challenges-we-ran-into)
- [Accomplishments that we’re proud of](#accomplishments-that-were-proud-of)
- [What we learned](#what-we-learned)
- [What’s next for Lexi](#whats-next-for-lexi)

Lexi is an intelligent multi-agent platform designed to democratize access to legal document analysis for individuals. 

Built for the Google Cloud Run Hackathon, Lexi offers clause-by-clause contract analysis, risk detection, plain-language explanations, and real-time streaming — simulating the experience of a legal expert, but powered entirely by AI.

## Features
✍️ AI-powered Clause Analysis  
Analyzes each contract clause for meaning, risk, and compliance.

📚 Standard Clause Comparison  
Compares your clauses to reference legal standards using embeddings.

🧪 Risk Detection & Explanation  
Highlights potential risks and explains them in plain, human-friendly language.

🧩 Multi-Agent Orchestration  
Specialized agents for extraction, comparison, and risk analysis, coordinated by a root orchestrator.

🎓 Plain-Language Summaries  
Translates legalese into clear, actionable insights.

🎥 Real-Time Streaming UI  
Frontend streams analysis results as they’re generated for a smooth, interactive experience.

🗣️ No Data Stored  
All processing is in-memory — your documents and data are never saved.

📈 Guardrails for Safety  
Built-in protections against malicious or unsafe inputs.

📈 Rate limiting for the API
Prevents from abuse

📤 Seamless Frontend Delivery  
Clean React UI, deployed on Google Cloud Run.

## Architecture diagram

                           ┌───────────────────────────────┐
                           │        Frontend (React)       │
                           │-------------------------------│
                           │ • Upload contract (PDF/Text)  │
                           │ • View clause analysis (live) │
                           │                               │
                           └──────────────┬────────────────┘
                                          │
                        JSON POST /contracts/analyze
                                          │
                                          ▼
                            ┌───────────────────────────────┐
                            │         FastAPI Backend       │
                            │        (Runs on Cloud Run)    │
                            │-------------------------------│
                            │ 1️⃣ Receives contract payload  │
                            │ 2️⃣ Extracts text (if PDF)     │
                            │ 3️⃣ Sends to CoreOrchestrator  │
                            │ 4️⃣ Streams structured JSON     │
                            │     chunks back to frontend   │
                            └──────────────┬────────────────┘
                                           │
                                           ▼
                     ┌────────────────────────────────────────────┐
                     │       Google ADK Agent System (Vertex AI)  │
                     │--------------------------------------------│
                     │ 🧭 CoreOrchestrator (LLM)                  │
                     │     ├─ ClauseAnalysisWorkflow (Sequential) │
                     │     │    ├─ ClauseExtractorAgent (LLM)     │
                     │     │    ├─ StandardClauseRetriever (Embed)│
                     │     │    ├─ ClauseComparisonAgent (LLM)    │
                     │     │    └─ RiskAnalysisAgent (LLM)        │
                     │                                            │
                     └────────────────────────────────────────────┘
                                           │
                                           ▼
                           Streamed JSON → FastAPI → React (UI updates)

- Frontend: React (Google Cloud Run)  
- Backend: FastAPI (Google Cloud Run)  
- Storage: Firestore (for embeddings)  
- LLMs: gemini-embedding-001, gemini-2.0-flash  
- OCR: PDF text extraction (in-memory)
- Docker for containerization
- Cloud Run for deployment

## Multi-agent system overview

| Agent                      | Role                                                      |
|----------------------------|-----------------------------------------------------------|            |
| RootOrchestratorAgent      | Coordinates all specialized agents                        |
| SequentialAgent            | Ensures agents process clauses in the correct order        |
| ClauseExtractorAgent       | Identifies and extracts each clause from the document      |
| StandardClauseRetriever    | Finds reference clauses using Firestore embeddings         |
| ComparisonAgent            | Detects deviations from standard clauses                   |
| RiskAnalysisAgent          | Explains potential issues in plain language    

🧭 Agents work collaboratively via an orchestrator and shared state.

🏃‍♀️ Installation
To run the agents, clone the repository and install the dependencies:

```bash
pip install -r requirements.txt
```

Then, start the FastAPI server:

```bash
uvicorn api.main:app --reload --port 8080
```

## 🚧 Challenges

* Integrating **ADK**, **FastAPI**, and **embeddings** in a single workflow.
* Learning how to use **Firestore** effectively for storing and retrieving clause embeddings.
* Deploying a multi-agent system seamlessly on **Google Cloud Run**.

## 🏆 Accomplishments

* Successfully building a complete pipeline using **ADK**, **FastAPI**, **Firestore**
* Implementing a multi-agent orchestration system for clause analysis.
* Learning and applying **Google ADK** — a new and powerful framework for AI agents.

## 📚 What we learned

* How to orchestrate and deploy multi-agent systems on **Google Cloud Run**.
* How to build end-to-end applications powered by **AI agents** to improve real-world processes.
* How to use **Firestore embeddings** for clause retrieval and semantic comparisons.

## 🚀 What’s next for Lexi

* Expand support for more document types (e.g. leases, terms of service) and countries.
* Add conversational follow-ups — allowing users to ask Lexi specific legal questions.
* Integrate more languages to make legal understanding accessible globally.
* Explore secure user authentication for saved sessions and history.
