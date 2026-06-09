# CLAUDE.md

Project conventions and architecture notes for AI assistants working in this repo.
Read this *before* editing code so we don't reintroduce hackathon-era mistakes.

---

## 🎯 Project Vision

**AI Research Intelligence Agent** — a Research-First Decision Support System for B2C / consumer-product market researchers.

- **The thesis:** Generic LLMs hallucinate numbers, so business teams can't trust them. We split the system into a deterministic **Math Engine** (Pandas/NumPy, no LLM) and a **Reasoning Brain** (LLM, never invents data — only narrates what the engine returned). Every claim must be traceable to a tool + source file.
- **Target user:** Product managers, market researchers, founders evaluating B2C ideas (FMCG, D2C, SaaS-for-consumers).
- **Demo domain:** Hair-care / FMCG market surveys (see `samples/hairfall_market_survey_demo.csv`). Sample CSVs for other goals live under `samples/`.

The user-facing differentiators we promise (and must keep honest):
1. **Bicameral architecture** — math is deterministic, LLM only narrates.
2. **7 fixed research goals** — Launch / Performance / UX / Retention / Hypothesis / Roadmap / Executive. See `agent_reasoning/prompts/goal_library.py`.
3. **Traceable citations** — every claim ends with `[Source: <tool> on <file>]`.
4. **Progressive disclosure** — handover → summary → evidence → deep data.
5. **4-Signal Clarity Check** — agent refuses to over-answer if data is thin.
6. **Sequential goal queueing** — handles multi-part questions one goal at a time.

If you remove a feature, **also update the README and this file** — they are the contract.

---

## 🏛️ Architecture (Live Path)

```
frontend_ui/app.py (Streamlit)
   └─ state_manager.initialize_session_state()
        └─ AgentBrain.process_turn(canonical_prompt)
              ├─ ResearchTools.analyze_dataset(file, goal)   # routes to quant
              │     └─ QuantInsightEngine.run_goal_N_analysis(df) → (report, trace)
              ├─ QualEvidenceEngine (only if text column present)
              ├─ VectorDBManager (ChromaDB) for verbatim retrieval
              ├─ ClarityValidator.check_clarity(...)  # gates output
              └─ OutputManager.generate_response(layer=...)  # progressive disclosure
```

Everything outside this graph is either dead code or a bug. **Don't add code that isn't called from this graph.**

---

## 📁 File Responsibilities

| File | Role |
|---|---|
| `frontend_ui/app.py` | Streamlit UI. Owns goal picker, file upload (saves to temp path!), chat loop, layer buttons, trace expander. |
| `frontend_ui/state_manager.py` | Loads `.env`, instantiates `AgentBrain` once per session, manages chat history. |
| `agent_reasoning/brain.py` | Orchestrator. Parses metadata → runs tools → validates → renders. **Single place that calls the LLM for synthesis.** |
| `agent_reasoning/tools.py` | Thin router. Goal string → correct `quant_engine.run_goal_N_analysis`. No business logic. |
| `agent_reasoning/validator.py` | `ClarityValidator` — 4-signal gate. Returns `{is_clear, escalation_needed, escalation_type, reason}`. |
| `agent_reasoning/output_manager.py` | Renders the 4 disclosure layers (handover / summary / evidence / deep_research). Safety rules are **inline in prompts**, no extra LLM round-trip. |
| `agent_reasoning/prompts/*` | Static prompt templates and the 7-goal definition library. Source of truth for goal metadata. |
| `data_intelligence/quant_engine.py` | The math. Per-goal analyses on a `DataFrame`. Every `run_goal_N` returns `(markdown_report, trace_dict)`. **No LLM calls here.** |
| `data_intelligence/qual_engine.py` | Real NLP only: SentenceTransformer clustering + TextBlob sentiment. **Do not add hardcoded-dict stub methods.** |
| `data_intelligence/db_manager.py` | ChromaDB persistent client. Populated on upload if a text column exists; queried by brain for verbatim quotes. |
| `samples/` | Per-goal demo CSVs. Each goal must have at least one credible sample. |
| `generate_data.py` | Regenerates all sample CSVs deterministically. |

---

## ✅ Conventions

### Data flow
- **Brain never reads files directly.** It receives a file path from the UI; only `quant_engine.load_data` does I/O.
- **Quant engine never calls the LLM.** Numbers must be reproducible.
- **Every quant function returns `(report_text, trace_dict)`** where `trace_dict = {"tool": ..., "source_file": ..., "columns_used": [...], "rows_analyzed": N, "computations": {...}}`.
- **LLM prompts always receive the trace** and are instructed to cite it inline.

### Goal routing
- Use the explicit enum keys from `GOAL_DEFINITIONS` (e.g., `GOAL_1_LAUNCH`). **Never** match goals via substring like `"1" in goal_key` — collision-prone.

### Missing columns
- If a goal expects a column the user's CSV doesn't have, **don't print "N/A"**. Either compute a defensible proxy, OR emit `"Data gap identified: <column>"` (per `system_persona.py`) and continue with what's available.

### Streamlit file uploads
- **Always save uploads to a temp path** (`tempfile.NamedTemporaryFile(delete=False, suffix=".csv")`) and pass the path through metadata. The brain `pd.read_csv`s a path, not a buffer.
- **Gate on `uploaded_file.file_id`** to avoid re-writing the same temp file on every Streamlit rerun. Store the active path in `st.session_state.temp_file_path`.

### LLM cost
- Use `gpt-4o-mini` for synthesis / safety scrubbing (fast, cheap).
- Reserve `gpt-4-turbo` for the validator (low-volume, high-stakes).
- Stream responses to the UI via `st.write_stream`.

### Secrets
- API keys live in `.env` (gitignored). Never `print()` keys, even truncated.
- Don't commit `.streamlit/secrets.toml` or `data_intelligence/vector_db/`.

---

## 🚫 Anti-Patterns (Don't Reintroduce)

These bit us during the hackathon — if you find yourself doing one, stop.

1. **No hardcoded data-source keywords in brain.** E.g., `if "hairfall" in user_input.lower(): load_demo_csv()`. The brain decides what to load purely from metadata.
2. **No `[cite_start]` / `[cite: NNN-NNN]` markers** in any user-facing string. Those are paste-artifacts from the problem-statement PDF. Hunt and kill on sight.
3. **No bundler files like `tool_definitions.py`** that wrap every engine method as a LangChain tool — we use direct calls. The old file referenced ~50 nonexistent methods and was a maintenance trap.
4. **No hardcoded-return stubs in engines.** If a method always returns `{"foo": "bar"}` without reading inputs, delete it. Stubs lie about coverage.
5. **No extra LLM round-trip for safety scrubbing.** Inline the safety rules into the generating prompt; don't post-process with a second call.
6. **No silent fallback to demo CSV** when an upload fails. Raise a clear error.
7. **No goal-1-only synthesis prompts.** The synthesis template must pull expected sections from `GOAL_DEFINITIONS[active_goal]`.
8. **Don't print the API key** for "diagnostics". Even the first 8 chars are enough to leak in a screen-share.

---

## 🧪 Running & Testing

```powershell
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Smoke test (no UI)
python test_backend.py

# UI
streamlit run frontend_ui/app.py
```

Smoke tests live in `tests/` (pytest). Each goal × each sample CSV must run without exceptions and the output must contain the expected section headers.

---

## 📚 Where the Plan Lives

`PLAN.md` at the repo root has the phased rebuild plan (Phases 1–4) with per-file deltas. When in doubt about scope, check there before refactoring.

**Current status:** Phases 1–5 complete (demo-ready + analyst voice + math depth). **Phase 6 planned, not started** — Phase 6 = visual charts + interactive what-if sliders. See `PLAN.md`.

**What Phase 4 delivered:**
- Streaming via `yield from self.llm.stream(...)` in `OutputManager`; `brain.py` returns `response_stream` generator; `app.py` consumes with `st.write_stream`.
- `st.empty()` status message replaces `st.spinner` so the loading indicator stays visible until the first token arrives.
- "📄 Export Brief (Markdown)" download button in the UI.
- `tests/test_smoke.py` with per-goal section-header assertions covering all 7 goals.
- `.github/workflows/ci.yml` running `generate_data.py --all` before pytest on every push to `main`.
- `synthesis_engine.py`, `canonical_system.py` deleted; `qual_engine.py` stub methods removed.

**Next session:** Execute Phase 5 (voice + depth), then Phase 6 (visuals + what-ifs). Update README + this file when each ships.
