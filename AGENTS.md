## Agents system design 

# 1) What you’ll store (data model)

**Standards Corpus (vector index + metadata):**

* `clause_id`: stable ID
* `text`: canonical clause text
* `doc_source`: e.g., “SaaS MSA v3.2 (OneNDA)”
* `framework_tags`: `["GDPR", "SaaS", "DPA", "Indemnity"]`
* `jurisdiction`: `["EU"]` (multi-valued OK)
* `version`: semantic version or date
* `normative_strength`: `{"required" | "recommended" | "optional"}`
* `explanation`: short rationale (“Mutual indemnity with cap aligns with X”)
* `citations`: URLs / section refs
* `embedding`: vector (L2 or cosine-normalized)

Optional:

* **Subclause spans** (e.g., carve-outs), **negation flags**, **quantitative caps** (`cap_multiple_of_fees`, `cap_absolute`), **party bias** (`vendor-tilt`, `customer-tilt`).

# 2) How to embed (and chunk) clauses

* **Chunking:** Use **clause-level** chunks. If a clause is very long, split into logical subclauses (headings/bullets), but keep a “parent” clause_id to re-aggregate scores.
* **Embedding model:** Use a **legal-tuned sentence embedding** if available; otherwise a strong general retrieval model (e.g., “all-MiniLM-L6-v2”-class) + **reranking** (see §4).
* **Normalization:** L2-normalize vectors and use cosine similarity. Store pre-normalized vectors to speed scoring.

# 3) Retrieval & comparison pipeline (at inference)

**Goal:** Given `user_clause_text`, return (a) most similar standard clauses, (b) a **compliance verdict** with reasoned diffs, (c) actionable flags.

**Steps (fast path + careful checks):**

1. **Embed** `user_clause_text`.
2. **Vector search** top-K (e.g., K=20) by cosine similarity in your standards index, **filtered** by:

   * `jurisdiction` (user preference or doc metadata),
   * `framework_tags` (e.g., only “GDPR” when checking data-processing),
   * `version` (latest unless user specifies).
3. **Rerank** the K hits with a **cross-encoder** (LLM or bi-encoder reranker) on pairs `(user_clause, candidate_clause)`. This reduces false positives for tricky legal language (negations, carve-outs).
4. **Semantic diff** (LLM): extract **key obligations** and **risk-bearing phrases** from both user clause and top-1/top-3 standards; align differences.
5. **Heuristics / rules overlay (optional but recommended):**

   * Quant caps present? mutuality? scope of liability? termination triggers? subcontractor controls?
   * Simple regex/DSL checks complement embeddings (e.g., look for “unlimited”, “indirect”, “consequential”).
6. **Score & label**:

   * `similarity_score` (0–1 from reranker)
   * `coverage_score` (how many key elements match)
   * **Verdict**: `STANDARD`, `NON_STANDARD`, or `RISK_FLAGGED`
7. **Explainability**: show closest standard text snippet, highlight **diff** spans, attach **provenance** (doc/version) and **citations**.

# 4) Why add a reranker?

Embeddings retrieve semantically close text, but legal nuances (negation, carve-outs) are subtle. A small **cross-encoder** or LLM-based pairwise scorer drastically improves precision:

* Input: `"[CLS] user_clause [SEP] standard_clause"`
* Output: relevance score.
  Use it to rerank top-K vectors before scoring/labeling.

# 5) Scoring rubric (simple, defensible)

| Condition                                                                          | Label            | Guidance to user                                                                                     |
| ---------------------------------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| `sim ≥ 0.83` and `coverage ≥ 0.8` and no rule violations                           | **STANDARD**     | “Matches standard wording with minor stylistic differences.”                                         |
| `0.72 ≤ sim < 0.83` or `coverage 0.5–0.8`                                          | **NON_STANDARD** | “Meaning differs in X/Y. Consider aligning with standard variant below.”                             |
| Any hard rule hit (e.g., unlimited liability, broad indemnity) or `coverage < 0.5` | **RISK_FLAGGED** | “Potential overexposure: unlimited liability + unilateral indemnity. Suggested safer rewrite below.” |

Tune thresholds with validation data; keep a feature flag to adjust.

# 6) Where this fits in your **CompliancePipeline**

* Keep your earlier **LoopAgent**: `Checker → Evaluator → Refiner`.
* The **Checker** implements the embedding retrieval, reranking, heuristics, and emits structured findings.
* The **Evaluator** (LlmAgent) inspects coverage and gaps; if **fail**, it emits follow-up probes (e.g., “look for data export restrictions; check subprocessor audit rights”).
* The **Refiner** runs targeted searches or alternate standards (e.g., sector-specific) and merges results.

**Checker output (state) example:**

```json
{
  "compliance_findings": {
    "c17": {
      "verdict": "RISK_FLAGGED",
      "similarity_score": 0.69,
      "coverage_score": 0.48,
      "top_matches": [
        {"clause_id":"std-msa-44", "sim":0.82, "doc_source":"SaaS-MSA v3.2", "jurisdiction":["EU"], "version":"3.2"},
        {"clause_id":"std-nda-12", "sim":0.77, "doc_source":"OneNDA 1.1", "jurisdiction":["EU","US"], "version":"1.1"}
      ],
      "key_diffs": [
        {"facet":"liability_cap","user":"unlimited","standard":"12 months fees"},
        {"facet":"mutuality","user":"unilateral indemnity","standard":"mutual"}
      ],
      "citations": ["src-12","src-19"]
    }
  }
}
```

# 7) Minimal code sketch (indexing & query)

**Indexing (FAISS-like pseudo):**

```python
# Build
std_texts, meta = load_standard_clauses()  # returns list[str], list[dict]
std_emb = embedder.encode(std_texts, normalize=True)  # shape: [N, D]
index = faiss.IndexFlatIP(D)                # cosine with normalized vectors
index.add(std_emb)

# Persist
save(index, meta)
```

**Query:**

```python
def compare_clause(user_text, jurisdiction=None, tags=None, top_k=20):
    vec = embedder.encode([user_text], normalize=True)
    # Filter metadata first (jurisdiction/tags) to a subset of vectors
    cand_ids = filter_by_meta(meta, jurisdiction=jurisdiction, tags=tags)
    sub_index = make_view(index, cand_ids)  # or keep parallel small indexes per bucket
    sims, idxs = sub_index.search(vec, top_k)
    candidates = [(cand_ids[i], float(sims[0][j])) for j,i in enumerate(idxs[0])]

    # Rerank with cross-encoder
    pairs = [(user_text, std_texts[i]) for i,_ in candidates]
    rerank_scores = cross_encoder.score(pairs)
    reranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)

    # Take top-3 for diffing
    top = reranked[:3]
    analyses = [semantic_diff(user_text, std_texts[i], meta[i]) for ((i, sim), rer) in top]
    coverage = compute_coverage(analyses)
    verdict = decide_verdict(reranked[0][1], coverage, analyses)  # uses thresholds + heuristics

    return {
        "verdict": verdict,
        "similarity_score": reranked[0][1],
        "coverage_score": coverage,
        "top_matches": [{"clause_id": meta[i]["clause_id"], "sim": s, **meta[i]} for ((i, s), _) in top],
        "key_diffs": extract_key_diffs(analyses),
        "citations": collect_citations(analyses)
    }
```

# 8) Making it robust (gotchas & upgrades)

* **Jurisdiction & vertical buckets:** Keep **separate indexes** per jurisdiction/vertical (EU/US; Fintech/Health) to reduce spurious matches.
* **Versioning:** Always include `version` and default to the latest; allow users to pin a baseline (“compare against SaaS-MSA v3.1”).
* **Negation traps:** Add a tiny **rule engine** for red flags (unlimited liability, unilateral indemnity, data export without safeguards).
* **Numeric normalization:** Extract and normalize numbers (caps, days, periods) to compare semantically (“12 months” ≈ “one year”).
* **Explainability:** Always show the matched standard snippet and a **bullet diff**; add citations to authoritative sources (e.g., GDPR articles, standard templates).
* **Evaluation set:** Build a test set of clauses with hand labels (`STANDARD / NON_STANDARD / RISK_FLAGGED`) and run **threshold calibration** and **A/B tests** per clause type.
* **Privacy:** If contracts are sensitive, isolate indexing per tenant, encrypt at rest, and avoid leaking user text into shared global indexes.
* **Latency:** Cache embeddings; pre-compute embeddings for the uploaded contract’s **all clauses** so explain/compare is instant on click.

# 9) Where each agent fits

| Agent                                           | Role in embeddings flow                                      | Notes                                                             |
| ----------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------- |
| **ClauseResolverAgent** (LlmAgent)              | Map a user reference (“termination”) to clause IDs           | Uses clause embeddings for retrieval over the uploaded contract   |
| **ComplianceCheckerAgent** (LlmAgent/tooling)** | Run the pipeline in §3/§7; emit scores, diffs, verdict       | Core place embeddings + reranker live                             |
| **ComplianceEvaluatorAgent** (LlmAgent)         | QA: is coverage complete? missing sub-issues?                | If `fail`, produce follow-up checks (e.g., export, subprocessors) |
| **ComplianceRefinerAgent** (LlmAgent/tooling)** | Execute follow-ups; add secondary standards, niche verticals | Merges results; loop stops when evaluator passes                  |
| **LegalOrchestratorAgent** (LlmAgent)           | Routes user → CompliancePipeline; passes jurisdiction prefs  | Summarizes findings back to user with citations                   |

(**tooling** = your deterministic functions for embed/search/diff that the LlmAgent calls)

