## Project structure

```
lexi/
├── agents/
│   ├── clause_analysis/
│   │   ├── __init__.py
│   │   ├── extractor_agent.py
│   │   ├── comparison_agent.py
│   │   ├── risk_agent.py
│   │   ├── workflow_agent.py
│   │   └── standard_clauses.json         # Optional: your reference clauses
│   │
│   ├── question_answers/
│   │   ├── __init__.py
│   │   └── qna_agent.py
│   │
│   └── core_orchestrator.py              # Central orchestrator using ADK
│
├── api/
│   ├── __init__.py
│   └── main.py                           # FastAPI app + endpoints
│
├── requirements.txt
├── Dockerfile
├── adk_config.yaml                       # ADK agent definitions (optional)
├── README.md
└── .gitignore
```
