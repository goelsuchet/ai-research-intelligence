# 📋 Rebuild Plan — AI Research Intelligence Agent

> Status: **Phases 1–5 Shipped · Phase 6 Planned (not started)** · Last updated: 2026-06-09
>
> This plan turns the hackathon prototype into a portfolio-grade project. Phases 1–4 made it correct, complete, and demo-ready. Phase 5 added analyst voice, math depth, and contextual gap analysis. Phase 6 adds visuals and interactive what-if scenarios (experience). Each phase is independently shippable.

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

## ✅ Phase 1 — Stop the Bleeding — COMPLETE

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

**Completed:** All 9 tasks shipped and pushed to `main`. `requirements.txt` regenerated via `pip freeze` (UTF-8). Known Phase 2 carry-overs documented in CLAUDE.md.

---

## ✅ Phase 2 — Make All 7 Goals Work — COMPLETE

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

**Completed:** All 5 tasks shipped. All 7 goals return `(report_text, trace_dict)` with populated `computations`. Per-goal sample CSVs generated. `GOAL_MAPPING` centralized in `goal_library.py`. Synthesis prompt uses real section headers extracted from report output.

**Known carry-overs into Phase 3 (do not re-fix in isolation):**
- `brain.py:75` passes `[ERROR]` strings to the LLM — needs `if tool_output and not tool_output.startswith("[ERROR]"):` guard.
- `quant_engine.run_goal_2_analysis` funnel bottleneck relies on `value_counts()` coincidentally matching funnel order — Phase 3 should sort by explicit stage order before diffing.

---

## ✅ Phase 3 — Deliver Every README Promise — COMPLETE

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

**Completed:** All Phase 3 items shipped. Traceability (`trace_dict` + `[Source: <tool> on <file>]` citations), progressive disclosure (4 layers + layer buttons), clarity gate (`validator.py` wired), sequential goal queueing (explicit `[➡ Next]` button, GOAL_KEY routing fixed), and Vector RAG (`db_manager.py` ingestion + brain.py retrieval) are all live.

**Known carry-overs into Phase 4:**
- `data_intelligence/qual_engine.py` — stub methods not yet deleted (3e.1). Stub soup still present; delete or replace before shipping.
- `data_intelligence/synthesis_engine.py` — slated for deletion (3e.4), not confirmed removed.
- `data_intelligence/canonical_system.py` — slated for deletion (3e.5), not confirmed removed.
- Streaming not yet wired — `OutputManager` returns a full string; `st.write_stream` not called (Phase 4 item).

---

## ✅ Phase 4 — Polish & Demo-Readiness — COMPLETE

| # | File | Change |
|---|---|---|
| 4.1 | `frontend_ui/app.py` | Stream LLM tokens via `st.write_stream`. Added "📄 Export Brief (Markdown)" download button that packages the last response + JSON trace. Replaced `st.spinner` (closed before tokens arrived) with `st.empty()` status message that clears the instant streaming begins. |
| 4.2 | `agent_reasoning/brain.py` | `process_turn` now returns `response_stream` (lazy generator) instead of a full string. `output_manager.generate_response` uses `yield from self.llm.stream(...)` throughout all 4 layers. |
| 4.3 | `README.md` | Updated to match final architecture. Added "Run it in 60 seconds" quickstart. |
| 4.4 | **NEW** `tests/test_smoke.py` | `pytest` smoke tests parameterized over all 7 goals × their canonical sample CSVs. Each test asserts: no `[ERROR]`, trace contract (`tool`, `rows_analyzed > 0`), and **per-goal named section headers** (e.g., "Market Attractiveness" for Goal 1, "Retention Health" for Goal 4) derived directly from `quant_engine.py` — catches wrong routing and broken sections. |
| 4.5 | **NEW** `.github/workflows/ci.yml` | Runs on push/PR to `main`. Steps: checkout → Python 3.12 → install deps → `python generate_data.py --all` → `pytest tests/test_smoke.py -v`. The generate step is required because `samples/` is untracked. |
| 4.6 | `data_intelligence/` | Deleted `synthesis_engine.py` and `canonical_system.py`. Removed all hardcoded-stub methods from `qual_engine.py`; only `extract_core_problems` (KMeans clustering) and `score_pain_intensity` (TextBlob) remain. |

**Known carry-overs / future work (to discuss next session):**
- No current known bugs. Next priorities → **Phase 5 (Report Depth & Analyst Voice)** and **Phase 6 (Visuals & Interactive What-Ifs)**, below.

---

## ✅ Phase 5 — Report Depth & Analyst Voice — COMPLETE

**Goal:** Kill the corporate-email tone, and make answers *teach the user something they didn't already know*. Today the agent reads three numbers back in a business letter. After Phase 5 it should read like a senior analyst's briefing: longer, interpreted, with practical scenarios and grounded "what-if" reasoning — every claim still traceable, still no LLM-invented numbers.

### The two root causes (diagnosed from the live demo)

1. **Email tone.** `output_manager._generate_handover` literally instructs the LLM to *"Write a brief, professional 'Handover Message'"*. The model reads "message/handover" as a business letter and emits `Subject:` / `Dear [User]` / `Best regards` / `[Your Position]`. Nothing in `system_persona.py` bans salutations or sign-offs.
2. **Thin substance.** (a) The quant engine computes only a handful of aggregates per goal — Goal 1 returns sample size, competitor count, avg WTP, and nothing else. (b) The output prompts then truncate even that (`data[:500] / [:1500] / [:3000]`) and ask for a "summary," so the LLM can only restate three numbers the user already knew. The LLM can never be deeper than the engine feeds it.
3. **No gap awareness.** In the demo the user priced at **₹1200**; the engine reported a viable band of **₹150–₹999** and avg WTP **₹508** — and never noticed that ₹1200 sits *above the entire surveyed market*. The user's own context (price, audience, hypothesis) from the notes box is never fed into the analysis.

### File-by-file changes

#### 5a. Analyst voice — eliminate the email format

| # | File | Change | Effect |
|---|---|---|---|
| 5a.1 | `agent_reasoning/prompts/system_persona.py` | Add a **VOICE & FORMAT** block: "You are a senior research analyst briefing a colleague directly. NEVER use email/letter scaffolding — no `Subject:` line, no `Dear …`, no `Best regards`, no `[Your Name]` / `[Your Position]` signature, no salutation or sign-off. Open with the single most important finding (BLUF). Write in direct second person ('your ₹1200 price point…')." Include one ❌-email / ✅-briefing example pair. | Bans the letter format at the persona level. |
| 5a.2 | `agent_reasoning/output_manager.py` | Rewrite every layer template (`_generate_handover`, `_generate_layer_1/2`). Replace the phrase "Handover Message" with "readout / briefing"; drop "Write a … message to the user." Inline the no-email rule into each prompt as a hard constraint. Prepend `SYSTEM_INSTRUCTIONS` as a real `SystemMessage` (currently the layers send only a `HumanMessage`, so the persona's rules don't reach them). | Tone fixed at every layer, not just persona. |

#### 5b. Deeper deterministic analysis (still zero LLM in the engine)

| # | File | Change | Effect |
|---|---|---|---|
| 5b.1 | `data_intelligence/quant_engine.py` | For **every** goal, expand beyond means: add **distribution & percentiles** (p25/median/p75, not just mean), **segmentation** (group-by any categorical present — e.g., WTP by `age_group` / `city_tier` / `gender`), **top-N breakdowns**, and **derived ratios**. Each new number lands in `trace_dict["computations"]` so it stays traceable. | Engine has real depth to narrate. |
| 5b.2 | `data_intelligence/quant_engine.py` | Add a **gap-analysis** step that uses user context (see 5b.4): compare the user's stated price / target against the computed band and report the gap explicitly (e.g., `price_vs_market`: "₹1200 is above p95 WTP of ₹950; ~8% of respondents reachable"). | Surfaces the non-obvious insight the demo missed. |
| 5b.3 | `data_intelligence/quant_engine.py` | Add a deterministic **scenario block** per goal — a small computed table the narration (and Phase 6 charts) consume. Goal 1: a **price→reach curve** (`% of respondents with WTP ≥ price` across a price sweep). Goal 2/3: funnel drop at each stage. Goal 4: retention-decay curve. Goal 5: variant lift + confidence. Goal 6: RICE ranking table. Stored under `trace_dict["scenarios"]`. **No LLM, no charts here — just numbers.** | Foundation for what-ifs (narrative now, interactive in Phase 6). |
| 5b.4 | `agent_reasoning/brain.py` | Parse the `USER_NOTES` block (already captured by `app.py`) into a `context` dict — extract a price figure (regex on `₹\d+` / "priced at"), target-audience phrase, and hypothesis text. Pass `context` into `QuantInsightEngine(context=…)` and forward it into the synthesis prompt. | Analysis becomes tailored to *this* user's plan, not generic. |

#### 5c. Richer, longer narration

| # | File | Change | Effect |
|---|---|---|---|
| 5c.1 | `agent_reasoning/output_manager.py` | **Remove the `[:500] / [:1500] / [:3000]` truncations.** Pass the full report + full `trace_dict` (incl. `scenarios`) to the LLM. | LLM stops being starved of data. |
| 5c.2 | `agent_reasoning/output_manager.py` | Restructure the **evidence** layer prompt to demand a long-form brief with named sections: **(1) Bottom line · (2) What the numbers say — *and why each one matters* · (3) Practical scenarios (2–3 concrete situations grounded in the data) · (4) What-if analysis (read from `trace_dict["scenarios"]`) · (5) Risks & data gaps · (6) What to investigate next.** Instruct: interpret every number ("what does this imply for the decision?"), never merely restate it. Keep `[Source: …]` citations and safety rules. | Output that adds knowledge, not just echoes it. |
| 5c.3 | `agent_reasoning/output_manager.py` | Keep `handover` short (it's the "I'm ready" ping) but make `summary` a tight 5–7 sentence verdict and `evidence` the full long-form brief from 5c.2. Preserve progressive disclosure — depth lives behind the **Show Evidence** button, not dumped at once. | Honors the progressive-disclosure contract while adding depth. |

### Design decisions
- **Detailed is the default.** The evidence layer is always the full multi-section brief (6 sections per 5c.2) — no concise mode, no depth toggle. Progressive disclosure is preserved by keeping `handover` short and `summary` tight, with the full depth behind the **Show Evidence** button.
- **Context parsing stays deterministic** (regex/keyword in `brain.py`), not a separate LLM call — cheap and predictable. If a price isn't found, gap analysis is simply skipped (emit a data-gap note, never invent one).
- **Engine stays LLM-free.** All new depth (percentiles, segments, scenarios, gap) is pandas/numpy. The LLM only narrates.

### Deliverable
- Upload the hairfall demo, price at ₹1200 → the agent opens with something like *"At ₹1200 you'd reach only ~8% of surveyed buyers — your price sits above the ₹150–₹999 band where 92% of demand lives [Source: …]."* No `Subject:`, no `Dear`, no sign-off. Evidence layer is a multi-section brief with practical scenarios and what-ifs.
- All 7 goals return enriched `trace_dict` with `computations`, `scenarios`, and (where context allows) `gap` keys.

---

## 🟪 Phase 6 — Visuals & Interactive What-Ifs — PLANNED

**Goal:** Turn the numbers into pictures and let the user *play* with them. Phase 5 makes the agent describe a price→reach curve in words; Phase 6 draws it and gives the user a slider to drag. Charts and what-ifs are computed deterministically (pandas), rendered in the UI — **the LLM never generates a chart or a number.**

### File-by-file changes

#### 6a. Chart-ready specs from the engine (deterministic)

| # | File | Change | Effect |
|---|---|---|---|
| 6a.1 | `data_intelligence/quant_engine.py` | Each goal appends `trace_dict["visuals"] = [ {"type": "bar"\|"hist"\|"line"\|"funnel"\|"scatter", "title": …, "x": [...], "y": [...], "x_label":…, "y_label":…} ]`. Pure data, no rendering. Driven off the same computations/scenarios from Phase 5 (e.g., Goal 1: WTP histogram, price→reach line, competitor-share bar; Goal 2: funnel; Goal 4: retention-decay line; Goal 5: variant-conversion bar; Goal 6: impact-vs-effort RICE scatter). | One source of truth for every chart; still traceable. |

#### 6b. Render visuals in the UI

| # | File | Change | Effect |
|---|---|---|---|
| 6b.1 | **NEW** `frontend_ui/charts.py` | A pure `spec → plotly.graph_objects.Figure` mapper (`render_visual(spec)`). One small function per chart type. No Streamlit, no engine imports — easy to unit-test. | Rendering decoupled from data. |
| 6b.2 | `frontend_ui/app.py` | After each assistant turn, if `trace.get("visuals")`, render them with `st.plotly_chart(render_visual(spec), use_container_width=True)` inside a `📈 Visuals` expander. Resilient: skip silently if absent/malformed. | Every goal shows charts. |
| 6b.3 | `requirements.txt` | Add `plotly` (and `kaleido` for static PNG export in 6d). Pin versions. | Reproducible installs. |

#### 6c. Interactive what-if controls

| # | File | Change | Effect |
|---|---|---|---|
| 6c.1 | `data_intelligence/quant_engine.py` | Expose small **pure recompute functions** the UI can call live without re-running the whole goal — e.g., `reach_at_price(df, price) → float`, `projected_revenue(df, price) → float`, `rice_at(reach, impact, conf, effort)`. Deterministic, no LLM. | Sliders can recompute instantly. |
| 6c.2 | **NEW** `frontend_ui/scenarios.py` + `app.py` | Goal-aware what-if panel: e.g., Goal 1 shows a **price `st.slider`** that live-updates "At ₹X, Y% of surveyed market reachable · projected reach Z" plus a marker on the price→reach chart. Goal 6 shows effort/impact sliders re-ranking RICE. No LLM round-trip — calls 6c.1 directly. | The headline "what-if" feature, made tactile. |

#### 6d. Richer export

| # | File | Change | Effect |
|---|---|---|---|
| 6d.1 | `frontend_ui/app.py` | Extend "📄 Export Brief": embed charts as PNG (via `kaleido`) into the exported document and append the scenario tables. Add an "include charts" toggle; markdown stays the default. | Export reflects what the user saw on screen. |

#### 6e. Tests + docs (the contract)

| # | File | Change | Effect |
|---|---|---|---|
| 6e.1 | `tests/test_smoke.py` | Assert each goal's `trace["visuals"]` is present and well-formed (type in allowed set, `len(x)==len(y)`). Assert recompute functions return sane shapes (e.g., `reach_at_price` is monotonically non-increasing in price). Add a **no-email** regression assert: output contains no `Subject:` / `Best regards` / `Dear `. | Locks in Phase 5 + 6 behavior. |
| 6e.2 | `README.md` + `CLAUDE.md` | Document the new differentiators (visual layer, interactive what-ifs, analyst voice). Add the convention "engine emits `trace_dict['visuals']` / `['scenarios']`; UI renders, engine never draws" and the anti-pattern "no email/letter scaffolding in any output." | Docs match shipped reality (per the repo contract). |

### Design decisions
- **Plotly** over Streamlit-native charts: interactive hover/zoom and a polished look for a portfolio demo, with a clean `spec → figure` seam.
- **What-ifs are interactive sliders backed by deterministic recompute**, not LLM narration — instant, reproducible, and impossible to hallucinate.

### Deliverable
- Every goal renders charts under a `📈 Visuals` expander; Goal 1 (and ≥2 others) have a live what-if slider; export embeds the charts. CI stays green with the new asserts.

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
| Analyst voice (no email tone) | ❌ Letter format | 🟦 P5 | system_persona.py, output_manager.py |
| Report depth (segments, percentiles, gap) | ❌ 3 aggregates | 🟦 P5 | quant_engine.py, brain.py |
| Practical scenarios + what-ifs (narrative) | ❌ None | 🟦 P5 | quant_engine.py (scenarios), output_manager.py |
| Visual representations (charts) | ❌ None | 🟪 P6 | quant_engine.py, charts.py, app.py |
| Interactive what-if sliders | ❌ None | 🟪 P6 | quant_engine.py, scenarios.py, app.py |

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
