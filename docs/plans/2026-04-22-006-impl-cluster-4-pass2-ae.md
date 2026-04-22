---
title: Pass-2 autoresearch + evaluation implementation research (10 items)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-006-pipeline-overengineering-implementation-research.md
---

# Pass-2 HIGH findings — implementation research (10 items)

Research for 10 confirmed pass-2 HIGH findings across `autoresearch/` (F-A.1–3), `src/evaluation/` (F-E.1, E.2, E.4, E.5, E.6, E.7), and `src/competitive/` (F-E.10). Each item specs the optimal implementation — minimally-invasive, fits existing patterns (async judges + `cost_recorder`, Claude CLI subprocess via `harness/agent.py`, structured JSON via `GradientScore`/`ChecklistScore` Pydantic models), low-risk, high-leverage.

Codebase conventions in play:
- LLM calls from `src/` use `AsyncOpenAI` or `google.genai` with a Pydantic response schema + `cost_recorder.record(...)` + retry-with-backoff (`JudgeError` pattern in `src/evaluation/judges/gemini.py` and `openai.py`).
- Agent-style calls from `autoresearch/` shell out to `claude -p` or `codex exec` via `harness/agent.py::_agent_command` (stateful working-dir + stdout log).
- Model routing table: `src/common/model_router.py` maps task name → model. New agent tasks should land in that table, not hardcoded strings.
- Caching is deterministic: SHA-256 of inputs → `content_hash` keyed in Postgres. For new agent calls, reuse the same pattern.

---

## #29 (F-A.1) — Parent selection agent — replace sigmoid × novelty formula

**Summary:** Replace the hand-tuned `sigmoid(λ·(score−midpoint)) × exp(−(children/8)^3)` in `autoresearch/select_parent.py` with an agent that sees top-K eligible variants + their trajectory and picks the parent. Keep the formula as a fast fallback for cheap-mode / timeout. One call per generation; cost negligible next to a 30-min evolution tick.

**Current state:** `autoresearch/select_parent.py:20-35` (constants + `_selection_weight`), `:42-75` (`select_parent` main). Called from `autoresearch/evolve.py:863-867` once per generation.

**Target state:** `select_parent()` builds a structured summary of top-K eligible variants and calls an agent that returns `{parent_id, rationale}`. Rationale is written to `lineage.jsonl` as a new `selection_rationale` field on the *child* entry (created right after). Formula fallback preserved behind `AUTORESEARCH_SELECTION=formula` env var and triggered automatically on agent timeout/parse failure.

**Implementation approach:**
  - **Option A — Claude CLI subprocess** (matches `autoresearch/harness/agent.py`, no new SDK). Short 30-60s call with a schema-constrained prompt.
  - **Option B — Direct `AsyncOpenAI` call** via GPT-5.4 with JSON schema (matches `src/evaluation/judges/openai.py`). Tighter latency; no subprocess plumbing.
  - **Recommended:** **Option B**. `select_parent.py` is a Python module already (not a shelled agent), so reusing `AsyncOpenAI` + Pydantic schema matches the closer pattern and sidesteps the `claude -p` shell-quoting surface. Keep `autoresearch/` provider imports isolated in a tiny new helper `autoresearch/agent_calls.py` so we don't leak `src/common/` into `autoresearch/`.
  - **Justification:** The decision is single-turn structured output, not a multi-step agent needing Bash/Read. JSON-schema OpenAI call gives us deterministic field names, retry policy identical to judges, and cost recording for free.

**Prompt design:**
```
You are selecting the next parent variant for autoresearch evolution, lane={lane}.

Candidates (top {K} by objective_score):
{for v in candidates:}
- id={v.id} score={v.score} children={v.children}
  inner_metrics.mean_keep={v.mean_keep} max_fixture_sd={v.max_fixture_sd}
  children_deltas={v.children_deltas}  # list of composite deltas for each child
  best_child_score={v.best_child_score}
  status={v.status}  # new|exploited|stalled

Recent trajectory (last 3 generations):
{gen_rows}  # mean_composite, inner_outer_corr, mean_keep

Pick ONE parent. Prefer: (a) parents with rising trajectory, (b) diverse
failure modes vs. current frontier, (c) parents whose children under-explored
the space. Penalize: (a) plateau children (composite variance < 0.01 across
≥4 children), (b) high max_fixture_sd at high composite.

Return JSON: {"parent_id": str, "rationale": str (1-3 sentences),
"confidence": "high"|"medium"|"low"}.
```
Word count ~150. Top-K = 8 is sufficient (current eligible pool is rarely larger post-discard).

**Model choice:** **Sonnet 4.5** via `AsyncOpenAI`→OpenRouter OR **GPT-5.4 low reasoning**. This is a judgment-over-structured-data call, not a reasoning marathon. Haiku is too weak for reading trajectory patterns ("3 children all at 0.74 = plateau"). Opus is overkill and adds 5-10s latency per gen. Sonnet 4.5 or GPT-5.4 low hits the sweet spot (~$0.02/call).

**Caching strategy:** Per-call: no cache (each generation has new state). Result memoization: hash `(archive_snapshot_id, lane, suite_id)` to short-circuit duplicate calls within a tick — safeguards against double-select if the evolve loop retries. Write the rationale into `lineage.jsonl` so it's permanently auditable without re-running.

**Specific code changes:**
- New `autoresearch/agent_calls.py`:
  ```python
  async def select_parent_agent(candidates: list[dict], gen_rows: list[dict],
                                 lane: str, timeout: int = 30) -> dict:
      # AsyncOpenAI call with Pydantic schema ParentSelection
      # Returns {"parent_id": ..., "rationale": ..., "confidence": ...}
  ```
- `autoresearch/select_parent.py`: top-level `select_parent` gets a new `use_agent: bool = None` param (default `os.getenv("AUTORESEARCH_SELECTION", "agent") == "agent"`). If agent path, call helper, record rationale via new optional arg. On exception or `parent_id not in eligible`, fall through to current formula. Keep formula helpers unchanged.
- `autoresearch/evolve.py:863-867`: plumb returned rationale into `lineage.jsonl` append site.

**Dependencies:** Requires `OPENAI_API_KEY` in the autoresearch environment (already in `_CLAUDE_ENV_KEYS` allowlist at `evolve.py:46-50`). No new packages — `openai` already in `src/`.

**Edge cases:**
1. Agent picks an ID not in the eligible set → fall through to formula.
2. Agent returns malformed JSON → retry once, then formula.
3. Zero-eligible lane → existing "baseline seed fallback" path (`select_parent.py:52-66`) unchanged.
4. Agent consistently picks the top score (exploitation collapse) → mitigated via prompt ("penalize plateau children"); monitor by logging selection diversity per 10 gens.
5. Cold start (< 3 trajectory rows) → pass `gen_rows=[]`; prompt degrades gracefully to "use current snapshot only."

**Test strategy:**
- Unit: `tests/autoresearch/test_select_parent.py` (new) — mock agent helper, assert formula fallback on exception, on malformed JSON, on out-of-set `parent_id`. Assert rationale plumbed to lineage.
- Integration: replay three historical generation snapshots; agent must not pick discarded variants.
- Shadow mode first (see Rollout).

**Rollout:**
1. Feature flag `AUTORESEARCH_SELECTION={agent,formula}` default `formula` for first week.
2. Shadow mode: run agent, log choice + rationale, but use formula pick. 3-5 gens of ground truth.
3. Flip default to `agent`. Keep `formula` available indefinitely for cheap replays.
4. No backfill — purely forward-looking.

**Estimated effort:** 1 day (4h impl + 2h tests + 2h shadow-mode tooling).

**Cost impact:** 1 call per generation × ~$0.02 = ~$0.02/gen. A typical evolution run (50 gens) = $1. Negligible vs. meta-agent cost (~$20/gen).

**Open questions:**
- Should `--cheap-mode` (manual override) force formula, or just use Haiku/Flash-Lite for the selection call? JR pick.
- Should rationale be *shown* to the next meta-agent as context ("we picked you because…"), or kept private to avoid self-justification bias? Recommend private-only for v1.

---

## #30 (F-A.2) — Alert thresholds agent — context-judged alerts replace fixed constants

**Summary:** Replace the fixed thresholds in `autoresearch/compute_metrics.py:29-31` (`INNER_OUTER_DRIFT_THRESHOLD=0.35`, `UNEVEN_GENERALIZATION_FIXTURE_SD=0.30`, `UNEVEN_GENERALIZATION_COMPOSITE=0.6`) with an agent that sees the last N generation rows + current and returns a structured alert or `null`. Keep the threshold rules as a cheap backstop — they fire independently alongside the agent.

**Current state:** `autoresearch/compute_metrics.py:142-176` (`check_alerts` with hardcoded if-branches); called from `record_generation()` once per generation completion (line 187).

**Target state:** After each generation, call an agent with `recent_rows` + `current_row`. Agent returns 0–N structured alerts (`code`, `severity`, `lane`, `gen_id`, `detail`, `confidence`). These are written to `alerts.jsonl` alongside any threshold-rule alerts (both paths preserved — agent doesn't replace, it augments).

**Implementation approach:**
  - **Option A — Run both paths, tag source:** Thresholds fire as today; agent also fires; both write to `alerts.jsonl` with `source: "rule"|"agent"` field.
  - **Option B — Agent veto/endorse the rule alert:** Rules pre-fire, agent sees them and can suppress as noise.
  - **Recommended:** **Option A**. Keeping them independent is the safer path — we don't lose the deterministic safety net, and we can retire the rules later once the agent has 30+ gens of demonstrated non-regression. Option B couples failure modes.
  - **Justification:** The existing threshold code is 20 lines and has a known false-positive problem (not a false-negative one). Running both paths surfaces the disagreement, which is the data we need to eventually drop one.

**Prompt design:**
```
You are a drift/overfitting monitor for autoresearch evolution, lane={lane}.

Current gen {gen_id}:
  n={n} variants  mean_composite={mean_composite}  mean_keep={mean_keep}
  inner_outer_corr={corr}
  per_variant: [{id, composite, max_fixture_sd, mean_keep}, ...]

Recent trajectory (last 5 gens, oldest→newest):
{rows}

Return a JSON array of alerts (0 to 3). Alert schema:
{"code": "inner_outer_drift"|"uneven_generalization"|"plateau"|
         "collapse"|"overfitting"|"novelty_exhausted",
 "severity": "low"|"medium"|"high",
 "variant_id": str|null,  # null for lane-level alerts
 "detail": str,  # 1-2 sentence plain-English explanation
 "confidence": "high"|"medium"|"low"}

Rules: flag drift only when clearly non-noise (e.g. corr fell and also
mean_composite or mean_keep regressed). Flag uneven_generalization only
when max_fixture_sd is high AND accompanied by implausibly high composite
(possible fixture saturation). Return [] if nothing worth flagging.
```

**Model choice:** **Haiku 3.5** or **GPT-5.4 nano / Flash-Lite**. This is low-stakes pattern matching over ~30 numbers. Sonnet is fine if latency budget permits; Haiku is cheaper and sufficient. Per `src/common/model_router.py` conventions, this slots in as `task="drift_alerting"` → Flash-Lite.

**Caching strategy:** None. Each gen completion is a new state. If the same `gen_id` is re-run (resume), keep the newer row.

**Specific code changes:**
- `autoresearch/compute_metrics.py`: add `async def _agent_alerts(row, recent)` using the same helper module `autoresearch/agent_calls.py` introduced in #29. Call it in `check_alerts` alongside existing rules. Emit alerts with `"source": "agent"` or `"source": "rule"`.
- Add `severity` field to existing rule alerts (`"high"` for both current rules — keeps consumers simple).

**Dependencies:** `autoresearch/agent_calls.py` helper (shared with #29). Runs concurrently with / after `record_generation` — must be awaitable if `record_generation` is invoked from sync code; add a thin `asyncio.run()` wrapper if needed (current `check_alerts` is sync).

**Edge cases:**
1. Agent returns malformed JSON → log, skip (rules still fire).
2. Agent hallucinates a `variant_id` not in the row → drop that alert, keep the others.
3. Fresh lane, <3 history rows → prompt tells agent to be conservative; often returns `[]`.
4. Agent produces 15 alerts (alarm fatigue) → schema caps to 3 in validation; prompt also explicit.
5. Network unavailable → graceful skip, rules alone.

**Test strategy:**
- Unit: mock agent returning fixed alerts, assert dedup + storage in alerts.jsonl.
- Golden: feed 10 historical generations.jsonl rows through rules + agent; snapshot diff.
- Alert-fatigue budget test: assert no more than `N` alerts / 10 gens on historical replay.

**Rollout:**
1. Agent runs in shadow for 1 week — alerts written with `source=agent` but nothing consumes them yet.
2. Compare agent vs. rule alerts; review with JR.
3. Flip downstream consumers (if any) to union.

**Estimated effort:** 0.5 day.

**Cost impact:** 1 Haiku/Flash-Lite call per gen × ~$0.002 = ~$0.10 for a 50-gen run.

**Open questions:**
- Should we drop the rule-based thresholds once agent has demonstrated coverage? Recommend keep indefinitely as dirt-cheap backstop.
- Do we want alert-on-alerts (second-order: "three consecutive medium drift alerts = high")? Probably not in v1 — let the agent see `recent` and detect patterns itself.

---

## #31 (F-A.3) — `geo_verify.py` verification verdict agent

**Summary:** After `run_visibility_checks` collects post-implementation visibility results, an agent compares them to `competitors/visibility.json` baseline and `results.jsonl` (what was changed). Produces a structured PASS/PARTIAL/FAIL verdict with per-query evidence + regression flags. Replaces the current "Compare results above with baseline in competitors/visibility.json" boilerplate footer.

**Current state:** `autoresearch/geo_verify.py:122-158` (`write_report` — dumps JSON in markdown + appends boilerplate summary). `:150-154` is the exact boilerplate footer to replace.

**Target state:** `write_report` generates the verdict section via agent; raw JSON still appended below for spot-check. Verdict is grep-able and has machine-readable JSON: `verification-verdict.json` sibling file.

**Implementation approach:**
  - **Option A — Single Claude CLI call** (consistent with `geo_verify.py` being a CLI script and being invoked from shell). Simpler, no Python SDK import in this file.
  - **Option B — `AsyncOpenAI` with schema** (consistent with judges).
  - **Recommended:** **Option A — `claude -p` subprocess.** `geo_verify.py` is already a shell-invoked script, and the verdict needs to see multi-file context (baseline JSON, results.jsonl, raw responses). Passing that via stdin/args is natural for the CLI path. Also: this is the *easiest* HIGH win per the master triage (low-risk, high-visibility).
  - **Justification:** The file is self-contained (200 lines, no SDK deps), and `claude -p --output-format=json` gives us a JSON response without needing to wire OpenAI/Anthropic SDKs into the autoresearch tool chain.

**Prompt design:**
```
You are verifying a completed GEO session's post-implementation visibility.

Baseline (pre-change):
<untrusted_input>{baseline_visibility_json}</untrusted_input>

What was changed (results.jsonl):
<untrusted_input>{results_jsonl_summary}</untrusted_input>
# ^ filtered to competitive + optimized entries, truncated to 20KB

Post-change visibility results:
<untrusted_input>{results_list}</untrusted_input>
# ^ list of (query, json_response) tuples from run_visibility_checks

For each query, determine whether visibility improved, regressed, or held,
relative to baseline. Brand/navigational queries weight higher than long-tail.
Produce a structured verdict:

{"aggregate_verdict": "PASS"|"PARTIAL"|"FAIL",
 "summary": str (2-3 sentences),
 "per_query_verdict": [
   {"query": str, "verdict": "improved"|"regressed"|"held"|"unknown",
    "evidence": str (one-line explanation with quoted fragment from result)},
   ...
 ],
 "regressions": [str (query names of any regressions worth flagging)],
 "confidence": "high"|"medium"|"low"}

PASS = majority improved, no critical regressions.
PARTIAL = mixed, or improved but with any brand regression.
FAIL = majority regressed or no improvement on any critical query.
```

**Model choice:** **Sonnet 4.5**. Multi-file synthesis over long context (baseline + results + deltas). Haiku would miss nuance on "this regression is OK because…". Opus is overkill. Sonnet 4.5 ≈ $0.10/verification; these run once per GEO session (≤ 10/day).

**Caching strategy:** Per-session cache: `(session_dir, hash(baseline, results))` → verdict JSON. Identical re-runs skip the call. Write `verification-verdict.json` alongside the markdown report.

**Specific code changes:**
- `autoresearch/geo_verify.py`:
  - New function `compute_verdict(session_dir, baseline, results) -> dict` that shells out to `claude -p --output-format=json --model sonnet` with the prompt above.
  - `write_report` takes the new verdict dict and renders a "## Verdict" section at the top; keeps raw-JSON dump under "## Raw Query Results" below.
  - Write sibling `verification-verdict.json` for machine consumption.
  - Keep current boilerplate as fallback when agent call fails (exit non-zero or invalid JSON).

**Dependencies:** `claude` binary on PATH (already required for autoresearch per `harness/agent.py:41-48`). Baseline file must exist — if it doesn't, verdict = `"UNKNOWN_NO_BASELINE"`.

**Edge cases:**
1. No baseline file → verdict `UNKNOWN_NO_BASELINE`, no agent call.
2. All queries failed (captured as `{"error": "query failed"}`) → verdict `FAIL` with explanation, no agent call.
3. Agent returns malformed JSON → retry once, then fall back to current boilerplate.
4. Baseline is stale (older than session start) → note in verdict summary; still meaningful.
5. Agent hallucinates `query` names not present → validate against input list, drop offending entries.

**Test strategy:**
- Unit: mock `subprocess.run` returning fixed JSON, assert verdict parsed + rendered.
- Snapshot: one historical session replayed end-to-end; snapshot the markdown verdict section.
- Missing-baseline test: assert `UNKNOWN_NO_BASELINE` path works.

**Rollout:** Drop-in — no flag needed. `geo_verify.py` is invoked manually post-session; adding a verdict block is strictly additive. Keep the raw JSON dump so anyone who wanted the old output still sees it.

**Estimated effort:** 0.5 day.

**Cost impact:** ~$0.10 per GEO session verification. Sessions are rare (≤10/day).

**Open questions:**
- Should the verdict feed back into lineage/metrics as an evolution signal? I'd say *yes* eventually — a FAILED verification is a strong signal the variant regressed holdout — but for v1, just make it a human-readable artifact.

---

## #32 (F-E.1) — `fuzzy_match` → paraphrase-checking agent

**Summary:** Replace `src/evaluation/judges/__init__.py:71-85` (50% word-set overlap) with an LLM call per judge response that verifies each evidence quote actually paraphrases something in the text. Batch all quotes for one judge-response into a single call. Use Haiku/Flash-Lite — this is the simplest agent call in the set.

**Current state:** `src/evaluation/judges/__init__.py:71-85` (`fuzzy_match`), called from `_parse_gradient:121` and `_parse_checklist:157`. Threshold 0.5; was 0.8, dropped because paraphrases failed.

**Target state:** A new helper `verify_evidence_batch(quotes: list[str], output_text: str) -> list[EvidenceVerdict]` runs one LLM call per judge response, returning `[{quote, matches, span}]` for each quote. `_parse_gradient` and `_parse_checklist` consume that instead of per-quote `fuzzy_match`.

**Implementation approach:**
  - **Option A — Gemini Flash-Lite** (reuses existing genai client infra in `judges/gemini.py`).
  - **Option B — OpenAI GPT-5.4 nano** (reuses `AsyncOpenAI` in `judges/openai.py`).
  - **Recommended:** **Option A — Flash-Lite**. Routed via `model_router.py` as `task="evidence_paraphrase_check"`. Cheapest and fast (<1s typical). The judge that produced the response is already hitting Gemini or OpenAI — one more Gemini call is essentially free to add.
  - **Justification:** Paraphrase detection is a textbook tiny-LLM task. 1–4 quotes per criterion × 8 criteria per eval = 8–32 quotes total. Batch per criterion (not per-quote), keep under 500 tokens each.

**Prompt design:**
```
For each numbered claim below, decide whether it is a paraphrase of, or
direct quote from, something actually stated in the text. Return JSON.

Text:
<text>{output_text}</text>

Claims:
1. {quote_1}
2. {quote_2}
...

Return: {"verdicts": [{"idx": int, "supported": bool,
                       "span": str (quoted fragment from text, or ""),
                       "reason": str (short)}, ...]}

"supported" = the claim's meaning is present in the text (paraphrase counts).
"span" = the exact span from the text that supports it, ≤ 25 words.
Return supported=false if the claim has no grounding; don't guess.
```

**Model choice:** **Gemini Flash-Lite** — `src/common/gemini_models.py::GEMINI_FLASH_LITE`. Task name: `evidence_paraphrase_check`. Cost ~$0.0003/criterion batch.

**Caching strategy:** Hash `(output_text, sorted_quotes)` → verdict list. A re-run of the same judge (replicate ensembling) can reuse. Store in-memory `lru_cache` within the evaluation request (clear on new request).

**Specific code changes:**
- `src/evaluation/judges/__init__.py`:
  - New `async def verify_evidence_batch(quotes, output_text, model=GEMINI_FLASH_LITE) -> list[EvidenceVerdict]`.
  - `_parse_gradient` and `_parse_checklist` become `async def` and await verification instead of calling `fuzzy_match`.
  - `parse_judge_response` becomes `async def`; call sites in `gemini.py:185` and `openai.py:124` add `await`.
  - Keep `fuzzy_match` as a deprecated fallback for offline tests / when `EVAL_EVIDENCE_AGENT=off`.

**Dependencies:** Existing `google.genai` client already imported in `judges/gemini.py`. Factor a small shared `_paraphrase_client` to avoid constructing a Gemini client per criterion.

**Edge cases:**
1. Empty quote list → return empty verdicts, skip call.
2. Agent returns fewer verdicts than claims → treat missing as `supported=false`.
3. Agent hallucinates a `span` not in the text → validate span substring-presence; if absent, flip `supported=false`.
4. Agent rate-limited → fall through to `fuzzy_match(threshold=0.5)` as deterministic backstop (log at WARN).
5. Very long output_text (> 30k tokens) → truncate to relevant 20k (first 10k + last 10k); note in prompt.

**Test strategy:**
- Unit: mock Gemini response, assert verdicts plumbed into `DimensionResult.evidence` + sub-question `evidence_verified` flag.
- Golden: replay 5 historical judge responses through both `fuzzy_match` and the agent; compare agreement rate. Agent should flip obvious false-negatives (paraphrases) to supported without flipping true hallucinations to supported.
- Offline/CI test: set `EVAL_EVIDENCE_AGENT=off`, assert `fuzzy_match` path still works.

**Rollout:**
1. Land with `EVAL_EVIDENCE_AGENT={on,off}` env flag, default `off`.
2. Shadow mode: run both, log disagreement rate, for 3 days across evaluation runs.
3. Review disagreements with JR. Flip default to `on`. Keep `off` for CI/offline.
4. Bump `RUBRIC_VERSION` (evidence gate is part of scoring) so cache invalidates once-only.

**Estimated effort:** 1 day (2h core + 4h async plumbing through `parse_judge_response` + 2h tests).

**Cost impact:** ~$0.002–0.005 per evaluation (8 criteria × one batch each, Flash-Lite). Versus ~$0.30 total eval cost → +1–2%.

**Open questions:**
- Should verification run *before* the cap-at-3 gate (#33) or be merged with it? If #33 lands, the `supported` verdicts feed directly into the calibration judge and the count gate disappears. Coordinate rollout.
- Should we cache verdicts across ensemble replicates of the same judge? Yes — same (output_text, quote) will get the same answer.

---

## #33 (F-E.2) — Gradient evidence-gate → calibration judge

**Summary:** Replace the cliff at `src/evaluation/judges/__init__.py:124-130` (`if score > 3 and len(verified_evidence) < 2: score = 3`) with a small calibration-judge agent that sees `(reasoning, evidence)` *blind to the score* and returns whether the reasoning is supported. The aggregator then decides how to combine the primary score with calibration.

**Current state:** `src/evaluation/judges/__init__.py:110-142` (`_parse_gradient`). Cap-at-3 hardcoded; applies to every gradient criterion regardless of domain.

**Target state:** After primary judge scores, a calibration judge receives `(criterion_id, rubric_prompt, reasoning, evidence_verdicts_from_#32)` and returns `{supported: bool, confidence: float 0-1, notes: str}`. Aggregator uses `confidence` to adjust the score continuously: `adjusted = score × (0.4 + 0.6 × confidence)` — no cliff. Or simpler: cap-at-`primary_score × confidence + (1-confidence) × 3`.

**Implementation approach:**
  - **Option A — Full calibration judge per criterion:** +8 LLM calls per eval.
  - **Option B — Only calibrate gradient criteria with score > 3:** today's trigger condition, agent-based instead of cliff. Avoids 50% of the cost.
  - **Option C — Batch all gradient criteria into one calibration call:** cheapest, but single failure = 4 criteria affected.
  - **Recommended:** **Option B with Haiku**. Trigger-on-high-score preserves the "verify claims of high quality" intent; Haiku+blinding is cheap enough that we can flip to Option C later if we want fewer calls.
  - **Justification:** The current cliff fires rarely (only on gradient > 3 with < 2 evidence). Replacing only those cases keeps cost minimal while fixing the mathematical ugliness (5 with 1 evidence → 3; 3 with 0 evidence → 3).

**Prompt design:**
```
You are a blinded calibration checker. Without seeing the numerical score,
evaluate whether the judge's reasoning + evidence are well-supported for
this rubric criterion.

Criterion: {criterion_id} — {short_criterion_description}

Rubric (what's being measured):
{rubric_prompt_trimmed_to_500_chars}

Judge's reasoning:
<reasoning>{reasoning}</reasoning>

Judge's cited evidence (with paraphrase-verification verdicts):
{for q in evidence: "- [supported={q.supported}] {q.quote}"}

Return JSON:
{"supported": bool,  # is the reasoning reasonable given the evidence?
 "confidence": float (0.0-1.0),  # how well-supported?
 "issues": [str] (flags like "reasoning overreaches evidence",
                  "evidence is thin", "reasoning contradicts evidence"),
 "notes": str (1-2 sentences)}

DO NOT re-evaluate the criterion itself. Only assess whether the reasoning
is internally consistent with the evidence provided.
```

**Model choice:** **Haiku 3.5** or **GPT-5.4 nano**. Meta-reasoning about a short passage of reasoning is a tractable small-model task. Sonnet would be overkill.

**Caching strategy:** Hash `(criterion_id, reasoning, evidence_tuple)` → calibration verdict. Cached within evaluation request + across ensemble replicates.

**Specific code changes:**
- `src/evaluation/judges/__init__.py`:
  - New `async def calibrate_judgment(criterion_id, rubric_prompt, reasoning, evidence_verdicts) -> CalibrationResult`.
  - `_parse_gradient`: if `score > 3` and raw evidence count is thin, await calibrate. Compute `adjusted_score = score * (0.4 + 0.6 * confidence)` when `supported=False`; else leave untouched. Persist `calibration` field on `DimensionResult`.
  - Drop the hard cap at line 125-130; calibration subsumes it.
- `src/evaluation/models.py`: add optional `calibration: CalibrationResult | None` on `DimensionResult`.

**Dependencies:** #32 (evidence verdicts) — calibration judge sees the per-quote verdicts. Otherwise it's blind to paraphrase grounding. Order: land #32 first, then #33.

**Edge cases:**
1. Calibration timeout → leave score untouched, record `calibration: null` (degrade to permissive, not restrictive — failure should not penalize).
2. Calibration returns confidence=0 with no issues → suspicious; log WARN and apply conservative floor of 0.5.
3. Calibration repeatedly disagrees with primary judge across criteria → alert (possible rubric-drift or judge misconfiguration).
4. Applied to ensemble median: calibrate only the representative sample, not all replicates (saves 2–3x calls).
5. Checklist scores — out of scope for v1 (checklist already has per-sub-question evidence gating via #32).

**Test strategy:**
- Unit: mock calibration returning (supported=False, confidence=0.3), assert score adjusted downward continuously (no cliff).
- Golden: replay 20 historical gradient>3 cases; agreement rate between cliff and calibration.
- Regression test: high-quality response with 1 evidence quote should *not* be capped to 3 if the calibration confirms the reasoning is well-supported from the quote alone (criterion-dependent).

**Rollout:**
1. `EVAL_CALIBRATION={on,off}` default `off`.
2. Shadow mode: calibrate in parallel to the cliff, log both, don't change the persisted score. Compare distributions.
3. JR review. Flip default `on`. Bump `RUBRIC_VERSION`.

**Estimated effort:** 1.5 days (1 day impl + 0.5 day shadow analysis).

**Cost impact:** +~$0.01–0.02 per evaluation (2–4 Haiku calls × $0.002). ~5% of eval total.

**Open questions:**
- Continuous vs. capped score adjustment — formula TBD after shadow data lands. Recommend starting with the capped form `min(score, 3 + round(2 * confidence))` to keep behavior close to today.
- Should checklist sub-questions be calibrated too? Not in v1.

---

## #34 (F-E.4) — Length-factor: agent-picked range vs. drop entirely

**Summary:** Evaluate two target paths for `src/evaluation/service.py:77-114` length factor. Option A: agent picks word range from input metadata (N competitors, data-tier counts, client stage). Option B: drop length-factor entirely — MON-8 and CI-8 already judge proportionality. **Recommended: Option B.** Simpler, eliminates a scoring primitive, shifts judgment to the rubrics where it belongs.

**Current state:** `src/evaluation/service.py:77-114` (`compute_length_factor`) + `_WORD_RANGES` at line 30. Fixed per-domain ranges: geo=(800,2000), competitive=(2000,5000), monitoring=(1500,4000), storyboard=(300,800). Used at line 228-229 to multiply `domain_score`.

**Target state:**
- **Option A:** `compute_length_factor` derives `(min, max)` per evaluation from input metadata (competitor count, data-tier distribution, client stage). Small agent call or deterministic function from `source_data`.
- **Option B:** `domain_score = geometric_mean(dimensions)` — no length_factor multiplier. Remove `_WORD_RANGES`, `compute_length_factor`, and call site at line 228-229. Rubrics MON-8 (proportionality) and CI-8 (data-gap acknowledgment) already judge whether the output length matches the input richness.

**Implementation approach:**
  - **Option A — deterministic function from source_data metadata:** derive `(min,max)` as `base_range × f(competitor_count, data_tier_ratio)`. No LLM call, but still a heuristic.
  - **Option A' — agent-picked range:** one call per evaluation, returns `(min, max)`.
  - **Option B — drop entirely:** delete the multiplier.
  - **Recommended: Option B.** The rubrics explicitly cover this ground; length_factor is a double-penalty for sparse-data briefs (hit by length-factor AND by CI-8 for not acknowledging the gap). Eliminating it simplifies the scoring pipeline and returns judgment to the rubrics.
  - **Justification:** Option A or A' adds complexity (an agent to configure a floor to multiply a rubric output) to fix a problem already fixed in the rubrics. The 2nd-pass research doc explicitly flags this: *"Current system double-penalizes … an agent sees the data-tier distribution and sets the expected range"* — but a deterministic multiplier here is fighting the rubrics, not complementing them.

**Prompt design:** N/A (recommend drop).

**Model choice:** N/A.

**Caching strategy:** N/A.

**Specific code changes:** (Option B)
- `src/evaluation/service.py`:
  - Delete `_WORD_RANGES` (line 30) and `compute_length_factor` (line 77-114).
  - `evaluate_domain`: remove line 218-229 (the length_factor computation and multiplication). `domain_score = geometric_mean([d.normalized_score for d in dimension_results])`.
  - `DomainResult.length_factor` stays as a field (set to `1.0`) for DB schema compatibility; mark deprecated in comment.
- Bump `RUBRIC_VERSION` (score math changed).

**Dependencies:** None. Self-contained change.

**Edge cases:**
1. Historical evaluations have `length_factor != 1.0` stored — leave untouched (they're immutable). New ones = 1.0 going forward.
2. If MON-8 or CI-8 regresses in scoring quality post-change, restore length_factor as a *rubric signal* (make word count visible to judges), not a multiplier.
3. Very-long output (30k words of padding) — now caught only by rubrics; monitor MON-8 false-positive rate in shadow.

**Test strategy:**
- Unit: remove `test_length_factor` tests; add assertion that `domain_score == geometric_mean(dimensions)` exactly.
- Golden: replay 10 historical evaluations with length_factor < 1.0; recompute without it; expect domain_score up by the length_factor amount. JR review whether new scores look right (rubrics should already be penalizing the truly bad cases).

**Rollout:**
1. Deploy with `EVAL_LENGTH_FACTOR={on,off}` default `on` initially.
2. Flip to `off` in a canary branch; run 20 evaluations; compare rubric scores (they should be stable — rubrics don't see length_factor).
3. Flip default to `off` after a week. Remove the flag + dead code after a month.

**Estimated effort:** 0.5 day (impl + test delete + shadow run).

**Cost impact:** Negative (removing a multiplier = zero LLM spend, no agent call).

**Open questions:**
- What if JR wants the safety net of a hard lower floor ("briefs under 100 words are always sus")? Could be added as a rule in `structural_gate` — but I'd argue rubrics already catch this via CI-1 (thesis clarity) too.

---

## #35 (F-E.5) — Drop competitive 500-char + 3-header structural gate

**Summary:** Remove the 500-char and 3-header checks in `src/evaluation/structural.py:101-108`. Replace with a minimal "non-empty content" floor (>50 chars of non-whitespace). Rubrics CI-1 (thesis clarity) and CI-8 (data-gap acknowledgment) already judge substance; the current gate pre-empts their judgment with a worse heuristic.

**Current state:** `src/evaluation/structural.py:101-108` — rejects `brief_content < 500 chars` or `< 3 markdown headers`.

**Target state:** Keep brief-file-existence + JSON-parse-of-competitor-files checks. Drop char count + header count. Minimal floor: > 50 non-whitespace chars (catches empty-string / single-word briefs that waste judge tokens).

**Implementation approach:** Single code change — replace the two rejection conditions with one minimal-content check.

**Recommended:** Land this alongside #34 — both are simplifications in the evaluation surface. Single `RUBRIC_VERSION` bump covers them.

**Justification:** Gate is acknowledged in comments (line 84-89) as content-judgment trying to avoid content-judgment. 500 chars is ~80 words — not "substantive" by any human measure. A 600-char placeholder with 3 fake headers passes; a 450-char low-data brief with 2 headers fails. Both outcomes are wrong.

**Prompt design:** N/A.

**Model choice:** N/A.

**Caching strategy:** N/A.

**Specific code changes:**
- `src/evaluation/structural.py:101-108`:
  ```python
  # Before
  if not brief_content or len(brief_content.strip()) < 500:
      failures.append("Brief content too short (<500 chars)")
      return StructuralResult(passed=False, failures=failures)
  headers = re.findall(r"^#{1,3}\s+.+", brief_content, re.MULTILINE)
  if len(headers) < 3:
      failures.append(f"Brief has only {len(headers)} section headers (need ≥3)")

  # After
  if not brief_content or len(brief_content.strip()) < 50:
      failures.append("Brief content missing or empty")
      return StructuralResult(passed=False, failures=failures)
  ```
- Update docstring at line 82-90 to reflect the reduced scope.

**Dependencies:** Depends on rubric reliability — CI-1 / CI-8 must be doing their job. The master triage notes F5.2 (doc-regen fix) as a prerequisite. If F5.2 hasn't landed, wait.

**Edge cases:**
1. Empty-string brief → still fails at 50-char floor.
2. Single-paragraph "no data available" brief (~200 chars) → passes structural, judged by CI-8 (should score OK if properly-caveated).
3. 1000-char placeholder brief with no real content → passes structural, judged by CI-1 (should score 1–2).
4. Very long padded brief → structural passes, rubrics should catch.

**Test strategy:**
- Unit: remove the 500-char and 3-header pass/fail tests in `tests/test_evaluation_structural.py`. Add test asserting 50-char floor.
- Golden: replay 20 historical briefs that failed structural today; confirm they now pass to judges and the judges score them low (i.e., the rubrics do their job).

**Rollout:**
1. Land as a single PR with #34. Bump `RUBRIC_VERSION` once for both.
2. Monitor for one week — any "low-quality brief reached judges" alert indicates rubrics need work.

**Estimated effort:** 2 hours (impl + test updates).

**Cost impact:** Slightly more judge calls on previously-rejected briefs — negligible (<$1/week).

**Open questions:** None that require JR. If JR wants a higher floor (say, 200 chars for "real content"), trivial to bump.

---

## #36 (F-E.6) — Drop `no_excessive_rework` + `synth_matches_stories` gates

**Summary:** Remove the two DQS assertions at `src/evaluation/structural.py:207-213` (synth_matches_stories ≥ 50%) and `:217-231` (no_excessive_rework >3 attempts). Move the signals into the monitoring rubric context (MON-2 + MON-8 judge prompts can reference them) or keep as observability metrics without pass/fail effect.

**Current state:** `src/evaluation/structural.py:217-231` — assertion 11 fails when >3 synthesize attempts on any story. `:207-213` — assertion 10 fails when <50% of stories have a synthesized counterpart. Both contribute to DQS score.

**Target state:** Assertions stripped from `_validate_monitoring`. Counts (`attempts_per_story`, `synth_ratio`) become contextual metadata available to MON-2 and MON-8 judges via `source_text`. No DQS penalty for rework or low synth ratio.

**Implementation approach:**
  - **Option A — Pure removal:** delete the assertions, let rubrics judge.
  - **Option B — Demote to monitoring metrics:** keep the computation, write to a new `_metrics` sidecar that observability consumes, do not gate evaluation.
  - **Option C — Include in judge source_text:** add `{"synthesize_attempts": [...], "synth_ratio": 0.4}` to source data so MON-2/MON-8 can reason about it.
  - **Recommended:** **Option B + C combined.** Drop from DQS pass/fail; preserve counts as observability (value for debugging agent thrashing); expose to rubrics as context.
  - **Justification:** Per research: "an agent that rewrote story 7 four times because the first three pushed back incorrectly on sentiment-scoring nuances is doing *better* work." Process-efficiency gates kill good output that took rework. But the signal is still useful for humans — hence Option B's observability path.

**Prompt design:** Minor addition to MON-2 and MON-8 rubric prompts (in `rubrics.py`):
```
Process context (informational only — do not penalize purely for rework):
- synthesize_attempts_per_story: {attempts_json}
- synth_ratio: {ratio}  # synthesized / stories

If rework produced demonstrably better synthesis (e.g., later attempts
correctly flagged nuance), that's a positive signal. Blind rework with
no improvement should be weighted negatively only if it degrades output.
```

**Model choice:** N/A (no new LLM call; rubrics already call existing judges).

**Caching strategy:** N/A.

**Specific code changes:**
- `src/evaluation/structural.py`: delete lines 207-216 (synth_matches_stories assertion), 217-231 (no_excessive_rework assertion). Recount `assertions_total` ↓2.
- New `_compute_monitoring_context(outputs, results) -> dict` returns `{attempts_per_story, synth_ratio}` — called from `service.py` and added to `source_data` for MON-2/MON-8 judge calls only.
- `src/evaluation/rubrics.py`: append the process-context paragraph to MON-2 and MON-8 prompts. Bump `RUBRIC_VERSION`.
- `src/evaluation/models.py`: `StructuralResult.dqs_score` semantics now use 11 assertions instead of 13 — document in docstring.

**Dependencies:** None. Self-contained.

**Edge cases:**
1. Agent with 20 attempts on one story — structural now passes. MON-8 rubric should flag it if output quality is degraded. Shadow-mode validation required.
2. Zero stories, zero synth — already handled by existing `has_digest` escape hatch, no change.
3. Rubric prompts get noticeably longer — within budget (rubrics are already 500–1500 chars each).
4. Historical DQS scores differ from new (different denominator); document the regime change.
5. Observability consumers of DQS may need to pin to the old formula — note in migration.

**Test strategy:**
- Unit: `tests/test_evaluation_structural.py` — drop tests for those assertions; update DQS denominator expectations.
- Rubric tests (`tests/test_ci_prompts.py` analog for monitoring): assert the process-context paragraph is present.
- Golden: replay 10 monitoring evaluations where the gate fired; confirm rubrics now produce reasonable scores.

**Rollout:**
1. Single PR, `RUBRIC_VERSION` bump.
2. Shadow for 3 days — comparing old DQS vs new on live sessions.
3. If MON-8 score drops aggregate > 5% post-change, pause and review; otherwise ship.

**Estimated effort:** 0.5 day.

**Cost impact:** Zero (no new calls; slightly longer prompts add <1% tokens).

**Open questions:**
- Does JR want `attempts_per_story` surfaced in the monitoring dashboard? Trivial to add.
- Keep DQS score as 11/13 assertions, or renumber to 1/11 fresh? Recommend keep codes, drop two — preserves telemetry continuity.

---

## #37 (F-E.7) — Claim-grounding agent replaces digest-hallucination regex

**Summary:** Replace `src/evaluation/structural.py:276-281` (literal `"Digest persisted" in session_md` regex) with a small "claim-grounding checker" agent that extracts side-effect claims from `session.md` and verifies each against the outputs bundle. Broader coverage, one abstraction, paraphrase-invariant.

**Current state:** `src/evaluation/structural.py:276-281` — if `session.md` contains the string `"Digest persisted"`, require `synthesized/digest-meta.json` to exist.

**Target state:** New "claim-grounding" check in `_validate_monitoring` (and, with same shape, potentially in other validators). Agent reads `session.md`, extracts claims like "ran X command", "persisted to Y", "wrote Z file", and verifies each against the outputs dict. Returns list of `{claim, evidence_span_in_session, claimed_artifact, actually_present, verdict}`. Assertion fires per-claim-that-fails.

**Implementation approach:**
  - **Option A — Haiku/Flash-Lite direct call:** single structured call per session.md.
  - **Option B — Claude CLI subprocess with Bash/Read tools:** agent can grep the outputs bundle itself. Overkill; the outputs dict is already in memory.
  - **Recommended:** **Option A.** The outputs dict has the full filename list — that's all the agent needs to verify claims. No filesystem access required.
  - **Justification:** Regex catches one phrasing out of infinite variants. Agent at ~$0.002/session catches paraphrases. One call per evaluation.

**Prompt design:**
```
Extract side-effect claims from the session log and verify each against
the actual artifacts produced.

session.md:
<untrusted_input>
{session_md}
</untrusted_input>

Artifacts actually produced (file list):
{sorted_output_filenames}

A side-effect claim is a statement that the agent did something with an
external effect: ran a command that wrote a file, persisted data,
published output, called an API with state change.

Return JSON:
{"claims": [
  {"claim": str (the exact claim, quoted from session.md),
   "claimed_artifact": str|null (filename the claim implies, or null),
   "verified": bool,
   "reason": str}
  ...
]}

Claims: list EVERY side-effect assertion — don't summarize. Verified=true
only if the claimed artifact is in the file list. Verified=false only
when the claim NAMES a specific artifact and that artifact is missing.
Narrative claims without a verifiable artifact → verified=null (skip).
```

**Model choice:** **Haiku 3.5** or **Gemini Flash-Lite**. Claim extraction + set-membership check over ~100 files is a small-model task. Task name in model_router: `claim_grounding_check`.

**Caching strategy:** Hash `(session_md, sorted_output_filenames)` → result. Per-request LRU cache.

**Specific code changes:**
- `src/evaluation/structural.py`:
  - Delete lines 276-281 (digest-hallucination regex).
  - New `async def _check_claim_grounding(session_md, outputs) -> list[ClaimVerdict]` — calls Flash-Lite.
  - `_validate_monitoring` (and potentially others) becomes `async def`; calls `_check_claim_grounding`; emits one `claim_grounded` assertion failure per unverified claim.
- `src/evaluation/service.py`: `structural_gate` becomes `async def` (ripple through one level).

**Dependencies:** Async ripple through `structural_gate`. None external.

**Edge cases:**
1. No session.md → skip check (not every domain has one).
2. Agent extracts zero claims → pass.
3. Agent hallucinates a claim not in session.md → validate `claim` substring-presence in session_md; drop if absent.
4. Agent marks a claim `verified=false` but `claimed_artifact` exists under a slight name variation (e.g. `synthesized/digest.json` vs `synthesized/digest-meta.json`) → accept `verified=unknown` (soft pass). Prompt explicitly excludes paraphrased filenames from false-negatives.
5. Agent timeout → degrade to old regex as backstop + log WARN.

**Test strategy:**
- Unit: mock Flash-Lite returning synthetic claim lists, assert assertion failures plumbed.
- Golden: replay 10 historical monitoring sessions; compare regex vs. agent catch rate. Agent should be strict superset.
- Paraphrase test: synthesize sessions with "Digest saved", "Successfully persisted", "Ran freddy digest persist" (no actual file). Agent should flag all three; regex catches only the first.

**Rollout:**
1. Feature flag `EVAL_CLAIM_GROUNDING={on,off}` default `off`.
2. Shadow mode: run both paths, log agreement. 3 days.
3. Flip default `on`. Bump `RUBRIC_VERSION`.
4. Delete regex in a follow-up PR after 2 weeks of stable agent path.

**Estimated effort:** 1 day (0.5 day impl + 0.5 day async ripple + tests).

**Cost impact:** ~$0.002 per monitoring evaluation. <1% total.

**Open questions:**
- Apply to other domains' session.md files too? (competitive, storyboard have them.) Recommend yes, low marginal cost.
- Should the agent also extract and verify *negative* claims ("I did NOT run X")? Not in v1 — scope to positive side-effect claims.

---

## #38 (F-E.10) — Agent fallback for `_ad_domain_matches` near-matches

**Summary:** When `_ad_domain_matches` at `src/competitive/service.py:40-53` rejects an ad due to non-exact host mismatch, and the cumulative drop rate for a search is ≥ 10%, invoke a lightweight Haiku/Flash-Lite agent with `(queried brand, queried domain, ad copy, image, link_url)` to decide YES/NO/UNSURE. Exact matches bypass the agent (fast path).

**Current state:** `src/competitive/service.py:40-53` (`_ad_domain_matches`), called from `search_ads:137`. Drops ads silently when hostname != queried domain.

**Target state:** `_ad_domain_matches` still runs first (fast path). When it returns False, collect the rejected ads. After all ads fetched, if drop_rate ≥ 10% of the total, batch the dropped ads through an agent call. Agent restores the genuine ones. Fast path (exact match) never hits the agent.

**Implementation approach:**
  - **Option A — Per-ad agent call:** 1 call per dropped ad. Expensive, unnecessary.
  - **Option B — Batch all dropped ads into one call:** cheap, one decision surface.
  - **Option C — Two-stage:** batch call, but only triggered when drop rate ≥ threshold.
  - **Recommended:** **Option C.** Ads that match exactly (the common case) are free. Unusual query patterns trigger the recovery path. Batched recovery is one call per search.
  - **Justification:** Most queries have 0% or <5% drop; the cost budget flows only to genuinely ambiguous cases.

**Prompt design:**
```
Decide which of these ads belong to the queried advertiser.

Queried brand/domain: {brand_or_domain}  # e.g. "sketch.com"
(Optional) Known aliases/subdomains: {aliases}  # from CompetitiveSettings

Ads (numbered, with link_url hostname mismatching the query):
{for i, ad in enumerate(ads):
  f"{i}. link_url={ad.link_url} (host={hostname(ad.link_url)})\n"
  f"   headline={ad.headline[:120]}\n"
  f"   body_text={ad.body_text[:160]}\n"
  f"   image_url={ad.image_url}"}

For each ad, decide: YES (this is the queried advertiser's ad),
NO (unrelated, false positive), UNSURE (insufficient signal).

Common legitimate cases:
- Ad-network redirect URLs (bit.ly, tracked parameters) where landing page is the advertiser's.
- Multi-domain brands where ad lands on a campaign-specific subdomain.
- Affiliate/co-marketing creative that legitimately promotes the brand.

Return JSON: {"verdicts": [{"idx": int, "verdict": "YES"|"NO"|"UNSURE",
                            "reason": str}, ...]}

Default conservatively: UNSURE beats YES. Only say YES when the ad copy,
brand name, or redirect chain strongly identifies the advertiser.
```

**Model choice:** **Gemini Flash-Lite** or **Haiku**. Classification over ~10 short text fragments. Task: `ad_domain_disambiguation`.

**Caching strategy:** Hash `(queried_domain, ad.link_url, ad.headline, ad.body_text)` → verdict. TTL cache 7 days (brand ownership is stable). Within same search, dedup identical link_urls before calling.

**Specific code changes:**
- `src/competitive/service.py:search_ads`:
  - After pre-filter at line 136-137, split into `matched` and `dropped_candidates`.
  - Compute `drop_rate = len(dropped_candidates) / pre_filter_count`.
  - If `drop_rate >= 0.10` and `len(dropped_candidates) > 0`, call new `_recover_dropped_ads(dropped_candidates, domain) -> list[dict]` which returns only `verdict == "YES"` entries.
  - Merge `matched + recovered` into final results.
  - Log: `ad_domain_filter: drop_rate=X%, recovered N/M`.
- New `_recover_dropped_ads` helper builds the batch prompt, calls Flash-Lite, parses verdicts.

**Dependencies:** Existing Gemini client config. Add `CompetitiveSettings.ad_domain_recovery_enabled: bool = False` (feature flag).

**Edge cases:**
1. Agent says YES but ad is clearly unrelated (bad call) → accept v1; monitor recovered-ad CTR / engagement downstream to auto-calibrate.
2. Agent says NO to a genuine ad → same as today's silent-drop (no regression).
3. Threshold: 10% is a guess; expose as `ad_domain_recovery_threshold` setting.
4. Very high drop rate (e.g. 90%) is a signal the query itself is wrong — log WARN, still call.
5. Agent rate-limited → fall through to current behavior (drop all).
6. link_url is nil — current code keeps; no change.

**Test strategy:**
- Unit: mock Flash-Lite returning synthetic verdicts, assert recovered ads flow through.
- Golden: replay historical `search_ads` calls where drop rate was high (sketch.com → mangasketch.com case); confirm legitimate-subdomain ads recovered.
- False-positive test: synthesize 10 clearly-wrong ads (random advertisers), assert agent rejects all.
- Threshold test: verify the 10% gate prevents cost on low-drop queries.

**Rollout:**
1. `ad_domain_recovery_enabled=False` default.
2. Enable for one high-ambiguity query pattern (multi-word brand names); observe drop recovery rate + false-positives for 3 days.
3. Enable globally. Consider adjusting threshold from 10% down based on data.

**Estimated effort:** 1 day.

**Cost impact:** Flash-Lite batch at ~$0.003/call. Fires on ~5–10% of ad searches (those with >10% drop rate). ~$0.001 per average search overall.

**Open questions:**
- Do we want to persist agent decisions back into a `known_brand_domains` table for long-run calibration? Recommend yes for v2 — short-run: hit the LLM each time but cache.
- Should the agent also see the *exact-match* ads as disambiguators ("here's what the real ads look like — is #4 from the same brand?")? Yes, include top 3 matched ads in the prompt for stylistic comparison. Adds ~200 tokens.

---

## Summary table

| # | File | Model | Cost / eval | Effort | Rollout |
|---|------|-------|-------------|--------|---------|
| 29 | `autoresearch/select_parent.py` | Sonnet 4.5 | ~$0.02/gen | 1 day | Shadow→flip |
| 30 | `autoresearch/compute_metrics.py` | Haiku/Flash-Lite | ~$0.002/gen | 0.5 day | Shadow→union |
| 31 | `autoresearch/geo_verify.py` | Sonnet 4.5 | ~$0.10/session | 0.5 day | Drop-in |
| 32 | `src/evaluation/judges/__init__.py` | Flash-Lite | ~$0.003/eval | 1 day | Shadow→flip |
| 33 | `src/evaluation/judges/__init__.py` | Haiku | ~$0.015/eval | 1.5 days | Shadow→flip |
| 34 | `src/evaluation/service.py` | **None (drop)** | -negative | 0.5 day | Canary→flip |
| 35 | `src/evaluation/structural.py` | None (drop) | ≈0 | 2h | Bundle w/ #34 |
| 36 | `src/evaluation/structural.py` + rubrics | None (drop+rubrics) | ≈0 | 0.5 day | Single PR |
| 37 | `src/evaluation/structural.py` | Flash-Lite | ~$0.002/eval | 1 day | Shadow→flip |
| 38 | `src/competitive/service.py` | Flash-Lite | ~$0.001/search | 1 day | Canary→flip |

**Total effort:** ~7.5 days of implementation + 3 weeks of rollout/shadow time.

**Total cost impact per evaluation:** ~$0.02 additional LLM spend. Baseline is ~$0.30/eval → +7%. Offset by: removed length_factor math (#34) + simpler structural gates (#35, #36).

## Parallelization / batching opportunities

- **#29 + #30:** Both use `autoresearch/agent_calls.py` helper — build it once.
- **#32 + #33:** `calibrate_judgment` (#33) consumes `verify_evidence_batch` output (#32) — must land in order, but the two changes share async plumbing in `parse_judge_response`. Do them together.
- **#34 + #35:** Both simplifications to `src/evaluation/service.py` and `structural.py`. Single PR with single `RUBRIC_VERSION` bump.
- **#36 + #37:** Both touch `structural.py`, both bump `RUBRIC_VERSION`. Single PR.
- **#31 + #38:** Independent. Can run in parallel to everything else.

Suggested PR order: (#31) → (#34+#35) → (#36+#37) → (#32+#33) → (#29+#30) → (#38). First three are low-risk and unlock shadow-data for the riskier ones.

## Global open questions for JR

1. **Agent backend for autoresearch calls (#29, #30, #31):** `claude -p` subprocess (matches `harness/agent.py`) vs. `AsyncOpenAI` (matches judges). I've recommended different answers for different items based on whether they need shell context vs. pure structured output. Confirm this split is OK.
2. **Shadow-mode budget:** most items recommend a 3-day shadow. Is JR willing to run evaluations with `SHADOW=1` for that period and review the agreement/disagreement logs?
3. **`RUBRIC_VERSION` bumps:** 3 separate bumps in this batch (#34+35, #36+37, #32+33). Each invalidates eval cache. Acceptable, but worth batching into 1–2 bumps if we can land groups simultaneously.
4. **Feature-flag discipline:** I've proposed env flags per item. We should probably unify under `configs/evaluation.toml` or similar to avoid env-var sprawl.
5. **Cost monitor:** Add a `cost_recorder` dashboard line per new task name (`parent_selection`, `drift_alerting`, `evidence_paraphrase_check`, `claim_grounding_check`, `ad_domain_disambiguation`, `calibration_check`) so we can watch spend from day 1.
