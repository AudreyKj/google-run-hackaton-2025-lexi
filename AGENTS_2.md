Here’s a crisp recap you can keep by your desk. 👇

# Agent Types & What They Do

| Agent type          | Core role                                                                           | When to use (in your legal assistant)                                                                             | Typical inputs → outputs                                                                                                                  | Sub-agents / tools                                                                                          | Stop condition                                                         | Notes                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **LlmAgent**        | LLM-powered specialist that reads/writes session state and (optionally) calls tools | Conversational router (orchestrator), clause explanation, compliance reasoning, rewrite generation, evaluation/QA | State + prompt + (optional) tool calls → a concrete state update (e.g., `explanations[cid]`, `compliance_findings[cid]`, `rewrites[cid]`) | Legal tools: `split_into_clauses`, `explain_clause`, `check_against_standard`, `suggest_rewrite`, retrieval | Finishes when its prompt step is done                                  | Your “brains” at each step. Keep prompts short and deterministic; name an `output_key`. |
| **SequentialAgent** | Runs a fixed pipeline A → B → C with shared state                                   | Ingestion (normalize doc → clauses), Explain flow, Rewrite flow                                                   | E.g., contract bytes → text → clauses → metadata                                                                                          | Sub-agents are usually LlmAgents (and/or simple tool-callers)                                               | When last sub-agent completes                                          | Great for predictable, one-pass processes.                                              |
| **LoopAgent**       | Repeats a mini-pipeline until pass/fail or max iterations                           | Compliance deep-dive (check → evaluate → refine); optional rewrite validation                                     | Findings → evaluated feedback (+ follow-up queries) → refined findings                                                                    | Typically 3 sub-agents: Checker (LlmAgent) → Evaluator (LlmAgent) → Refiner (LlmAgent)                      | **Escalation** event (e.g., evaluator says “pass”) or `max_iterations` | Use where quality bars matter; cap iterations to keep costs bounded.                    |
| **BaseAgent**       | Abstract base; implement `_run_async_impl` yourself                                 | Rare—only for custom control (e.g., EscalationChecker)                                                            | Reads session state → emits control Events                                                                                                | None (your code)                                                                                            | When your custom logic says so                                         | Handy for routing/stop logic without invoking an LLM.                                   |
| **AgentTool**       | Wraps an agent so it can be invoked like a tool                                     | Let the orchestrator call pipelines (ingestion, explain, compare, rewrite)                                        | Tool call → triggers the wrapped agent                                                                                                    | The wrapped agent                                                                                           | When the wrapped agent finishes                                        | Clean way to expose pipelines behind a single callable.                                 |

---

# How to Structure Your Legal Assistant

## 1) Orchestrator (conversation brain)

* **Type:** `LlmAgent` (no loop)
* **Name:** `LegalOrchestratorAgent`
* **Job:** Detect intent (Ingest / Explain / Compare / Rewrite / Search), maintain `state.user_preferences`, delegate to pipelines via **AgentTool**.

## 2) Ingestion pipeline (one-time per upload)

* **Type:** `SequentialAgent` → deterministic steps
* **Sub-agents:**

  1. `DocumentLoaderAgent` (choose `pdf_to_text`/`docx_to_text`)
  2. `ClauseSegmenterAgent` (`split_into_clauses`, optional embeddings)
  3. `DocAnnotatorAgent` (entities, governing law, dates)
* **Outputs:** `contract_text`, `clauses[]`, `doc_metadata`.

## 3) Explain pipeline

* **Type:** `SequentialAgent`
* **Sub-agents:** `ClauseResolverAgent` → `ClauseExplainerAgent` (calls `explain_clause`)
* **Outputs:** `explanations[cid]`.

## 4) Compliance pipeline

* **Type:** `SequentialAgent` that contains a **LoopAgent**
* **Flow:** `ClauseResolverAgent` → `ComplianceLoop`

  * **`ComplianceLoop` (LoopAgent):**

    * `ComplianceCheckerAgent` (calls `check_against_standard`)
    * `ComplianceEvaluatorAgent` (grades pass/fail, suggests follow-up checks)
    * `ComplianceRefinerAgent` (runs follow-ups; merges findings)
* **Outputs:** `compliance_findings[cid]` (+ citations/provenance if available).

## 5) Rewrite pipeline

* **Type:** `SequentialAgent` (+ optional mini LoopAgent for “safety checks”)
* **Sub-agents:** `ClauseResolverAgent` → `RephrasingAgent` (calls `suggest_rewrite`) → *(optional)* `RewriteVerifierAgent` (semantic diff/obligations preserved)
* **Outputs:** `rewrites[cid][style]`, optional `rewrite_diffs[cid]`.

## 6) Citations / provenance (optional but recommended)

* Add a callback like `collect_clause_sources_callback` to harvest source URLs/IDs from tools and store:

  * `state.sources[srcN] = {title, url, supported_claims[]}`
* If you compose full reports, use the `<cite source="src-N" />` → Markdown replacement pattern.

---

## Minimal wiring sketch (pseudo-code)

```python
# Pipelines wrapped as tools so the orchestrator can call them.
ingest_tool   = AgentTool(ingestion_pipeline)     # SequentialAgent
explain_tool  = AgentTool(explain_pipeline)       # SequentialAgent
compare_tool  = AgentTool(compliance_pipeline)    # SequentialAgent with LoopAgent inside
rewrite_tool  = AgentTool(rewrite_pipeline)       # SequentialAgent (+ optional LoopAgent)

legal_orchestrator = LlmAgent(
  name="LegalOrchestratorAgent",
  model=config.worker_model,
  instruction="""
  Detect user intent from the message and current state.
  - If no clauses but file present → call IngestionPipeline.
  - If 'explain' intent → ExplainPipeline.
  - If 'compare'/'GDPR'/'standard' → CompliancePipeline.
  - If 'rewrite'/'safer wording' → RewritePipeline.
  Maintain state.user_preferences (tone, jurisdiction).
  """,
  tools=[ingest_tool, explain_tool, compare_tool, rewrite_tool, retrieve_clause_tool],
  sub_agents=[],
)

root_agent = legal_orchestrator
```

---

## Practical tips

* **Keep prompts tight** and forbid agents from mutating unrelated state.
* **Name output keys** explicitly (e.g., `output_key="compliance_findings"`).
* **Bound loops** (`max_iterations`) and use an **Escalation** action from the evaluator to stop early.
* **Deterministic tools** for parsing/splitting; **LLM** for interpretation and rephrasing.
* **ClauseResolver** should accept IDs (“c7”), headings (“Indemnity”), or natural queries (“termination”) via retrieval over clause embeddings.

If you want, I can turn this into a skeleton repo layout (`agents/`, `pipelines/`, `tools/`, `callbacks/`) with ready-to-fill stubs.
