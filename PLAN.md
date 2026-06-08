# 📋 Rebuild Plan — AI Research Intelligence Agent

> Status: **Drafted** · Last updated: 2026-06-08
>
> This plan turns the hackathon prototype into a portfolio-grade project. It's organized into 4 phases; each phase is independently shippable. Phase 1 alone makes the demo not-embarrassing; Phases 1+2 give a working MVP; Phase 3 delivers every README promise; Phase 4 is polish.

---

## 🎯 The Vision

**Problem space:** Consumer / B2C market research is fragmented — researchers juggle survey CSVs + raw feedback text + competitor data in 5 different tools, then hand-stitch a story. Generic LLMs hallucinate numbers, so they aren't trusted for decisions.

**Our product:** A *Research-First Decision Support System* for consumer-product teams. The pitch is **"Bicameral AI"** — a deterministic Math Engine (Pandas/NumPy/stats) feeds a Reasoning Brain (LLM) that *only narrates verified numbers*. Every claim is traceable. The agent works through **7 fixed research workflows**. Demo target = B2C hair-care / FMCG / D2C brand research.

**Differentiators we will defend:**
- Bicameral architecture (math separated from LLM)
- 7 goal-anchored workflows
- Inline citations on every claim
- Progressive disclosure (summary → evidence → raw)
- Clarity-gated refusal to over-answer
- Multi-modal ingest (CSV + text → quant + qual + vector RAG)

---

## 🔎 Honest Audit of Current State

### What's wired and runs
```
Streamlit UI (app.py)
   └─ AgentBrain.process_turn(prompt)
        └─ ResearchTools.analyze_dataset(file, goal)
              └─ QuantInsightEngine.run_goal_N_analysis(df)
                    └─ LLM synthesizes a final reply
```
That's the **entire live path**. Everything else is dead code.

### Files that exist but are not wired in
| File | Status | Notes |
|---|---|---|
| `data_intelligence/tool_definitions.py` | 💀 **Broken** | Calls ~50 methods on `quant_engine` & `synthesis_engine` that don't exist. Only imported by `debug_setup.py`. |
| `debug_setup.py` | 💀 Broken | Imports the file above → always fails. Also prints API key (bad). |
| `agent_reasoning/validator.py` | 💀 **Never called** | The "4-Signal Clarity Check" the README brags about — fully written, zero wiring. |
| `agent_reasoning/output_manager.py` | 🟡 Half-dead | Handover/Summary/Evidence/Deep layers exist; only `summary` fires, and only on the empty fallback path. |
| `data_intelligence/qual_engine.py` | 🟡 Stub-soup | 30+ methods, ~5 do real work; the rest return hardcoded dicts. None called from main path. |
| `data_intelligence/synthesis_engine.py` | 🟡 Stub-soup | All methods return hardcoded dicts. Never called from main path. |
| `data_intelligence/canonical_system.py` | 🟡 Skeleton | Doesn't normalize anything meaningfully. Never instantiated. |
| `data_intelligence/db_manager.py` (ChromaDB) | 🟡 Skeleton | Class is fine, but DB is never populated and never queried. |
| `data_intelligence/__init__.py` | Empty | |

### Bugs in the live path
1. **Uploaded file silently dies.** `app.py:60` reads the upload but **never saves it to disk**. `brain.py:64` then `pd.read_csv("<bare-filename>.csv")` → file-not-found → falls back to demo CSV. Every upload analyzes the wrong file.
2. **"hairfall" keyword hardcoded.** `brain.py:63` — any prompt containing "hairfall" force-loads the demo CSV.
3. **Only Goal 1 produces real output on the demo CSV.** Goals 2–6 read columns (`retention_d30`, `effort_score`, `funnel_stage`, `churn_reason`, `impact_score`, `p_value`, `feature_name`) that don't exist in `hairfall_market_survey_demo.csv`. They print "N/A". Goal 7 is canned text.
4. **`[cite_start] … [cite: 122-131]` markers leak into user output** — paste-artifacts from the problem PDF showing up in every report.
5. **Goal routing is fragile.** `"1" in goal_key` matches any string containing "1".
6. **Synthesis prompt is hardcoded for Goal 1** ("Market, Pricing, Competition") regardless of which goal ran.
7. **`_apply_safety_check`** burns an extra LLM round-trip on every output.
8. **Validator's failure-path dict** is missing `escalation_type` → would `KeyError` if ever called.
9. **Excel claimed but not supported** — `load_data` only handles CSV.
10. **No streaming, no upload preview, no goal-specific sample data.**
11. **Requirements unpinned**; `spacy`, `langdetect`, `openpyxl` imported nowhere.

---

## 🏛️ Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit UI (app.py)                                      │
│  - Goal picker  - File uploader (CSV/XLSX/TXT)              │
│  - Streaming chat  - Layer tabs (Summary | Evidence | Raw)  │
│  - "Try sample data" dropdown per goal                      │
└──────────────┬──────────────────────────────────────────────┘
               │ Canonical Input (goal, file_path, text, query)
┌──────────────▼──────────────────────────────────────────────┐
│  AgentBrain (orchestrator)                                  │
│   1. Ingest → resolve file_path, detect columns             │
│   2. Route  → ToolRouter picks goal-appropriate tools       │
│   3. Run    → QuantEngine (+ QualEngine if text present)    │
│   4. Trace  → accumulate tool_trace + citations             │
│   5. Validate → ClarityValidator (4-signal gate)            │
│   6. Render  → OutputManager (handover/summary/evidence)    │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│  Data Intelligence Layer                                    │
│   QuantEngine   — pandas stats per goal (all 7 working)     │
│   QualEngine    — sentiment + theme clusters on text col    │
│   VectorDB      — ChromaDB index of verbatims for RAG       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Phase 1 — Stop the Bleeding (4–6 hrs)

**Goal:** App works correctly on Goal 1, no broken code in the repo, uploads don't lie.

### File-by-file changes

| # | File | Change | Effect |
|---|---|---|---|
| 1.1 | `frontend_ui/app.py` | Save uploaded file to `tempfile.NamedTemporaryFile(delete=False, suffix=".csv")`. Pass the temp path in metadata instead of `uploaded_file.name`. Add `st.dataframe(df.head())` preview after upload. | Uploads actually get analyzed. |
| 1.2 | `agent_reasoning/brain.py` | Remove `"hairfall" in user_input.lower()` keyword check. Trust the metadata `UPLOADED_FILE` path verbatim. Raise a clear error (not silent fallback) if path missing/invalid. | No more wrong-file analysis. |
| 1.3 | `data_intelligence/quant_engine.py` | Strip every `[cite_start]` / `[cite: NNN-NNN]` marker from all 7 report templates. | No PDF paste-artifacts leaking. |
| 1.4 | `agent_reasoning/tools.py` | Replace substring matching with explicit `GOAL_KEY → function` dict driven by `GOAL_DEFINITIONS`. | No substring collisions. |
| 1.5 | `data_intelligence/tool_definitions.py` | **Delete.** | Removes broken dead code. |
| 1.6 | `debug_setup.py` | **Delete** or rewrite to: load brain → run on demo CSV → print first 200 chars of response. Never print API key. | Diagnostic that actually diagnoses. |
| 1.7 | `requirements.txt` | Pin versions (`pip freeze` from clean install). Remove `spacy`, `langdetect`, `faiss-cpu` for now (not used). | Reproducible installs. |
| 1.8 | `.gitignore` | Add `data_intelligence/vector_db/`, `*.tmp`, `.streamlit/secrets.toml`, `samples/.cache/`. | Don't commit ChromaDB state or secrets. |
| 1.9 | `README.md` | Update "File Structure" section to reflect reality (no `vector_store.py`, etc.). | Stop misleading reviewers. |

### Deliverable
- `streamlit run frontend_ui/app.py` → upload `hairfall_market_survey_demo.csv` → run Goal 1 → get a clean, citation-free, real analysis.
- No file in the repo crashes on import.

---

## 🛠️ Phase 2 — Make All 7 Goals Work (1–2 days)

**Goal:** Every goal produces real numbers on real input. No more "N/A" / "Unknown" placeholder reports.

**Strategy:** Two-pronged. (a) Make `quant_engine` *resilient to missing columns* — fall back to defensible derived analyses. (b) Add small per-goal demo CSVs so reviewers can click through every goal.

### File-by-file changes

| # | File | Change | Effect |
|---|---|---|---|
| 2.1 | `data_intelligence/quant_engine.py` | Rewrite each `run_goal_N_analysis(df)` to: (1) introspect `df.columns`; (2) compute what's possible (e.g., Goal 4 derives "intent to repurchase" from `satisfaction_score` when `retention_d30` missing); (3) explicitly emit `"Data gap identified: <col>"` for what isn't there. Return `(report, trace_dict)`. | Goals 2–7 stop being decorative. |
| 2.2 | **NEW** `samples/` folder | Move `hairfall_market_survey_demo.csv` here. Add: `app_funnel_demo.csv` (Goal 2/3: sessions × funnel_stage × time_on_step × acquisition_cost), `subscription_retention_demo.csv` (Goal 4: user_id × week × is_active × login_frequency × churn_reason), `ab_test_demo.csv` (Goal 5: variant × conversion × p_value × sample_size), `feature_backlog_demo.csv` (Goal 6: feature_name × reach × impact_score × effort_score × confidence_score). | Every goal has credible demo data. |
| 2.3 | `generate_data.py` | Expand: a `--goal N` flag that regenerates one file, or run-all generates them all into `samples/`. | Reproducibility. |
| 2.4 | `frontend_ui/app.py` | Add a "📁 Try sample data" `st.selectbox` whose options change based on the selected goal. Selecting a sample auto-loads it. | Recruiter can click through all 7 goals in 60 seconds. |
| 2.5 | `agent_reasoning/brain.py` | Replace the hardcoded "Market, Pricing, Competition" synthesis prompt with a goal-aware template that pulls expected output sections from `GOAL_DEFINITIONS[active_goal]["tools_required"]`. | LLM narration matches the goal being run. |

### Deliverable
- All 7 goals produce real, data-driven reports.
- Sample CSVs work without surprises.

---

## 🛠️ Phase 3 — Deliver Every README Promise (3–5 days)

**Goal:** The features in the README actually exist in the code. This is where the architectural story becomes real.

### 3a. Traceability & Citations

| # | File | Change |
|---|---|---|
| 3a.1 | `data_intelligence/quant_engine.py` | Each goal returns `(report_text, trace_dict)` where `trace_dict = {"tool": "scan_kpi_health", "source_file": "<csv>", "columns_used": [...], "rows_analyzed": N, "computations": [...]}`. |
| 3a.2 | `agent_reasoning/brain.py` | Pass `trace_dict` into synthesis prompt with strict instruction: "Every numeric claim MUST end with `[Source: <tool> on <file>]`." |
| 3a.3 | `frontend_ui/app.py` | Render an expandable `st.expander("🔍 Trace")` under every assistant message showing the trace JSON. |

### 3b. Progressive Disclosure

| # | File | Change |
|---|---|---|
| 3b.1 | `agent_reasoning/brain.py` | After tool run, FIRST call `output_manager.generate_response(layer="handover")` and return that. Track conversation state: user's next message triggers `summary`, then `evidence` on request, then `deep_research`. |
| 3b.2 | `agent_reasoning/output_manager.py` | Drop the separate `_apply_safety_check` LLM round-trip; inline the safety rules into each layer's prompt template. |
| 3b.3 | `frontend_ui/app.py` | Add three buttons under each assistant turn: `[📊 Show Evidence]` `[📁 Show Raw Data]` `[➡ Next Question]`. |

### 3c. 4-Signal Clarity Check

| # | File | Change |
|---|---|---|
| 3c.1 | `agent_reasoning/brain.py` | After synthesizing draft, call `validator.check_clarity(goal, findings, user_input)`. If `escalation_needed`, switch mode (prioritization OR summary) instead of returning the draft. |
| 3c.2 | `agent_reasoning/validator.py` | Add `escalation_type: None` to the failure-path dict so it never `KeyError`s. Add one retry on `PydanticOutputParser` failure. |
| 3c.3 | `frontend_ui/app.py` | Show a yellow banner when escalation fires: "⚠️ Clarity gate: \<reason>. Switching to \<mode>." |

### 3d. Sequential Goal Queueing

| # | File | Change |
|---|---|---|
| 3d.1 | `agent_reasoning/brain.py` | Move `_detect_goals` / `_update_queue` into the main path. When a user message classifies as multi-goal (LLM call), enqueue them; finish one before starting the next. |
| 3d.2 | `frontend_ui/app.py` | Render `st.progress` for the queue. Show "Currently analyzing: \<goal\> · Up next: \<goal\>". |

### 3e. Qualitative + Vector RAG path

| # | File | Change |
|---|---|---|
| 3e.1 | `data_intelligence/qual_engine.py` | Delete every hardcoded-stub method. Keep only `extract_core_problems`, `score_pain_intensity`, embedding helpers. |
| 3e.2 | `data_intelligence/db_manager.py` | On file upload, if any text column exists (`feedback_text`, `verbatim`, `review`, `comment`), embed each row into ChromaDB with metadata `{goal, source_file, row_id, segment}`. |
| 3e.3 | `agent_reasoning/brain.py` | After quant run, if vector DB has rows, query it for 3 verbatims relevant to the user query and include them in the synthesis prompt as "Evidence quotes:". |
| 3e.4 | `data_intelligence/synthesis_engine.py` | **Delete.** Replace any of-value concepts with system-prompt sections in `output_manager.py`. |
| 3e.5 | `data_intelligence/canonical_system.py` | **Delete.** Move column-detection helpers into a small utility in `quant_engine.py`. |

### Deliverable
- Every claim in the README is true in the code.
- Project is portfolio-defensible in an interview.

---

## 🛠️ Phase 4 — Polish & Demo-Readiness (1 day)

| # | File | Change |
|---|---|---|
| 4.1 | `frontend_ui/app.py` | Stream LLM tokens via `st.write_stream`. Add "📄 Export Brief (Markdown)" button that downloads the current trace+report. |
| 4.2 | `agent_reasoning/brain.py` | Switch synthesis to `gpt-4o-mini` (cheap/fast); keep `gpt-4-turbo` for the validator only. Wire `langchain` streaming callbacks. |
| 4.3 | `README.md` | Update screenshots. Regenerate demo GIF/video. Refresh "Run it in 60 seconds" quickstart. Drop the outdated `vector_store.py` reference. |
| 4.4 | **NEW** `tests/` | Add `pytest` smoke tests: each goal × each sample CSV → no exceptions, output contains expected section headers. |
| 4.5 | **NEW** `.github/workflows/ci.yml` | Run smoke tests on push to `main`. |

---

## 📌 Feature → File Impact Matrix

| Headline Feature | Today | After plan | Files touched |
|---|---|---|---|
| Bicameral (math vs LLM) | ✅ Partial | ✅ Real | brain.py, quant_engine.py |
| 7 Goals | 🟡 Only G1 works | ✅ All 7 | quant_engine.py, samples/ |
| Traceability / citations | ❌ Fake `[cite_start]` markers | ✅ Real trace dict + inline cites | quant_engine.py, brain.py, app.py |
| Progressive disclosure | ❌ Layers unused | ✅ Wired (4 layers) | brain.py, output_manager.py, app.py |
| 4-Signal Clarity Check | ❌ Never called | ✅ Gates output | brain.py, validator.py |
| Sequential goal queue | ❌ Stub | ✅ Multi-goal Q&A | brain.py, app.py |
| Handover mechanism | ❌ Never fires | ✅ First response after upload | brain.py, output_manager.py |
| Vector DB / RAG | ❌ Never populated | ✅ Verbatim quotes in answers | db_manager.py, brain.py, qual_engine.py |
| Multi-modal input | 🟡 CSV-only, text ignored | ✅ CSV+XLSX+text | quant_engine.py, app.py |
| Safety scrubbing | 🟡 Extra LLM call | ✅ Inline in prompts | output_manager.py |

---

## 🗑️ Files to DELETE

- `data_intelligence/tool_definitions.py` — broken, unused
- `data_intelligence/synthesis_engine.py` — all stubs, replaced by prompts
- `data_intelligence/canonical_system.py` — does nothing, logic moves to quant_engine
- `debug_setup.py` — rewrite or delete; never print API key
- Tracked `__pycache__/` dirs — add to `.gitignore`, untrack from index

---

## 🚨 One-Time Cleanup Before Phase 1

- **Rotate the OpenAI API key** in `.env` (visible to anyone who had repo access, even though `.env` is gitignored).
- Confirm `.env` is in `.gitignore` (it is) and was never committed (it wasn't).
- Wipe `__pycache__/` directories: `git rm -r --cached **/__pycache__/`.

---

## 🎬 Execution Order

1. **Phase 1 first** — surgical, ~half a day, immediately makes the project not-embarrassing.
2. **Phase 2 next** — without it, 6/7 goals are demo-broken.
3. **Phase 3** — only if we want the README to be honest end-to-end. This is the work that makes it a portfolio piece.
4. **Phase 4** — final polish before sharing with recruiters.

Hard rule: **don't start a later phase until the earlier one is committed and demoable.** Hackathon energy = many half-done things; we want the opposite this time.

---

## 📚 Related Docs

- `CLAUDE.md` — conventions and anti-patterns for AI assistants and humans editing this repo.
- `README.md` — user-facing pitch. Update at the end of each phase to match shipped reality.
