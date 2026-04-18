# Autoresearch Gap Analysis

Compared against:
- **Meta-Harness** (Lee et al.) — arxiv.org/pdf/2603.28052 — End-to-end optimization of model harnesses
- **Hyperagents** (Zhang et al.) — arxiv.org/pdf/2603.19461 — Evolving AI agent architectures

**Total gaps: 33** | Scored 1-10 on impact | Sorted by score descending

**Score distribution:** 9×1 | 8×2 | 7×2 | 6×3 | 5×10 | 4×11 | 3×3 | 2×1

---

## Gaps Selected for Implementation

**Planned (11 gaps):**

| Phase | Gap | Score | Effort | Description |
|-------|-----|-------|--------|-------------|
| Before first evolution run | Gap 2 | 9 | Medium | Eval traces → meta agent |
| Before first evolution run | Gap 6 | 7 | Trivial | Enforce regression_floor |
| Before first evolution run | Gap 18 | 7 | Medium | Evaluation variance (2+ runs/fixture) |
| Before first evolution run | Gap 30 | 5 | Trivial | L1 import check (bundle with Gap 6) |
| Soon after first runs | Gap 1 | 8 | Medium | Production intelligence → evolution |
| Soon after first runs | Gap 3 | 8 | High | Expand fixture pool + rotation |
| Soon after first runs | Gap 28 | 5 | Medium | Eval caching for unchanged domains |
| Soon after first runs | Gap 26 | 5 | Trivial | Failure analysis digest (bundle with Gap 2) |
| As evolution matures | Gap 7 | 6 | Low | Evaluator drift protection |
| As evolution matures | Gap 4 | 6 | Medium | Cross-variant strategy extraction |
| As evolution matures | Gap 17 | 6 | Medium | Staged/cheap-first evaluation |

**Not addressed (22 gaps):** Gaps 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25, 27, 29, 31, 32, 33 — either have strong existing mitigations, only matter at scale, are efficiency concerns, or are research problems. Revisit Gap 12 (meta memory) if meta agent repeats failed strategies.

---

## Gap 2: Eval Session Traces Don't Reach the Meta Agent — Score: 9/10 — ADDRESSING

**Category:** Feedback
**Priority:** Do now (before first evolution campaign)

**Description:**
When `evaluate_variant.py` scores a variant, it runs full sessions that produce `results.jsonl`, evaluator feedback, rework counts, stall events. All discarded by `prepare_meta_workspace()` which excludes `sessions/`, `metrics/`, and `meta-session.log`.

**What the meta agent sees:**
- `index.json` — variant summaries with composite scores, changed_files, frontier membership
- `frontier.json` — Pareto frontier members
- Parent variant source code
- `lane-context.md` — editable boundaries
- `meta.md` rendered with archive path, iterations remaining, lane

**What the meta agent does NOT see:**
- Session traces (`results.jsonl`) with per-iteration data
- Per-fixture error messages and failure reasons
- Evaluation criterion feedback (per-criterion scores, reasoning, evidence)
- `dimension_scores`, `grounding_passed`, `structural_passed` per fixture
- Rework attempt counts per artifact
- Completion guard failure notes
- Watchdog stall events
- Per-fixture wall times and costs

**Code evidence:**
- `archive_index.py:18` — `IGNORED_DIRS` hardcodes `sessions` exclusion
- `archive_index.py:19-25` — `IGNORED_FILES` excludes `meta-session.log`, `mutation_plan.json`, `scores.json`
- `archive_index.py:102-109` — `_is_ignored()` implements the filtering
- `evaluate_variant.py:444-489` — sessions produce output in `variant_dir/sessions/{domain}/{client}/` — the excluded path
- `evaluate_variant.py:492-607` — `_score_session` returns `dimension_scores`, `grounding_passed`, `structural_passed`, `dqs_score`, stored in `scores.json` (also in IGNORED_FILES)
- `meta.md:46` — mentions "Raw traces such as `meta-session.log`, `sessions/**/session_summary.json`" as "may be useful evidence" but workspace preparation removes them — **a contradiction**

**Paper evidence:**
- **Meta-Harness**: Proposer accesses "execution traces (such as prompts, tool calls, model outputs, and state updates)" through grep/cat on filesystem. 40% of files read are execution traces.
- **Hyperagents** (Appendix A.4): "During self-modification, hyperagents have access to all evaluations across these tasks." In multi-domain: "Because the meta agent can inspect evaluations from any task, it can introduce shared mechanisms."
- **Hyperagents** (Appendix E.3.3): Develops "Automated Bias Detection and Correction" — tracking label distributions across generations. Requires per-task evaluation data, not just aggregate scores.

**Score rationale:** Strongest paper evidence of any gap. Meta-Harness proposer reads 40% traces. Immediately actionable (data exists during every eval run but is thrown away). The meta.md contradiction (referencing filtered-out traces) confirms this was intended but not implemented.

**Suggested fix:** After `score_variant_search()`, extract a structured failure digest — which fixtures failed, which phases, which evaluation criteria, rework counts — include as `eval_digest.md` in meta workspace. Add `{eval_digest}` substitution to `meta.md`.

---

## Gap 1: Production Session Intelligence Doesn't Feed Evolution — Score: 8/10 — ADDRESSING

**Category:** Feedback
**Priority:** Do soon (after production sessions exist)

**Description:**
`run.sh` (production) and `evolve.sh` (evolution) are hermetically sealed. Production sessions produce the richest signal in the system — real clients, real failures, real rework patterns, accumulated findings, session summaries with quality metrics — and the evolution loop never touches any of it.

**What production sessions produce:**
- `results.jsonl` — per-iteration event log with before/after deltas, status, phase types
- `findings.md` — confirmed/disproved learnings per client (ground truth about what works)
- `session_summary.json` — aggregated metrics (avg_delta, iterations, cost, quality)
- Evaluator feedback per artifact with per-criterion scores and reasoning
- Rework counts, stall events, completion guard notes
- Domain-specific artifacts (pages, competitors, stories, digests)

**What evolution sees instead:** Composite score (e.g., "geo: 0.45"), api_cost, wall_time. No diagnostics.

**Code evidence:**
- `evolve.sh:319-333` — `score_variant_search` calls `evaluate_variant.py` on benchmark fixtures only; no code path ingests production session data
- `archive_index.py:18` — `IGNORED_DIRS = {"__pycache__", "sessions", "metrics", "runs"}` explicitly excludes sessions from meta workspace
- `archive_index.py:219-226` — `prepare_meta_workspace` copies variant dirs through filtering that excludes sessions/metrics
- `evolve.sh:998-1088` — main evolution loop contains no reference to production runs or `run.sh` outputs
- `meta.md:28` — archive context described as "Redacted search-only archive"

**Paper evidence:**
- **Meta-Harness**: Proposer "accesses the source code, scores, and execution traces of all prior candidates through a filesystem" — reads "a median of 82 files per iteration" with "41% harness source code and 40% execution traces"
- **Hyperagents** (Appendix E.3.1): Meta agent receives "the location of previous evaluation results" and autonomously develops `_analyze_evaluations()` methods that "systematically process evaluation data"

**Score rationale:** Highest ceiling of any gap — production sessions test diverse real clients, unlike the 12 benchmark fixtures. Scored below Gap 2 because: (a) production data doesn't exist yet (system is on v001), (b) papers actually feed eval traces (Gap 2), not production traces — this goes beyond what either paper describes.

**Suggested fix:** Synthesize a `production_intelligence.md` from the last N production runs — rework rates by phase, common evaluation failures, stall patterns, cross-domain observations — and include it in the meta agent workspace.

---

## Gap 3: Small, Static Search Suite — Score: 8/10 — ADDRESSING

**Category:** Evaluation
**Priority:** Do soon (expand after first runs show overfitting)

**Description:**
12 fixtures total across 4 domains, same every run, no rotation:
- **geo**: 3 (semrush, ahrefs, moz) — 6 max_iter, 300s timeout
- **competitive**: 3 (figma, canva, miro) — 3 max_iter, 300s timeout
- **monitoring**: 3 (shopify, lululemon, notion) — 3 max_iter, 300s timeout, pinned to 2026-W12
- **storyboard**: 3 (gossip-goblin, techreview, cookingdaily) — 3 max_iter, 300s timeout

All in `eval_suites/search-v1.json`. All tagged "hard". All `input_mode: "live"`.

**Code evidence:**
- `eval_suites/search-v1.json:1-160` — exactly 12 fixtures, no rotation mechanism
- `evaluate_variant.py:365-377` — `_suite_fixtures` reads all fixtures and runs all of them; no sampling or rotation logic
- `evaluate_variant.py:610-665` — `_aggregate_suite_results` averages all fixture scores; every fixture always runs, always contributes equally
- `evolve.sh:155-187` — suite path loaded once from policy, remains static

**Paper evidence:**
- **Meta-Harness**: Uses 60-250 search tasks per domain
- **Hyperagents** (Section 4.2): Coding: 60 train + 165 test. Paper review: 100 train + 100 val + 100 test. Math: 100 train + 100 val + 100 test.

**Score rationale:** 5-20x fewer fixtures than either paper. 3 fixtures per domain is small enough for the LLM to memorize domain-specific patterns (e.g., semrush page structure). Holdout provides partial protection but may also be small.

**Suggested fix:** Fixture rotation — larger pool (20-30/domain), randomly sample subset each evaluation. Or stratified: 2 "anchor" fixtures + 1-2 random. Consider Hyperagents' staged protocol.

---

## Gap 18: No Evaluation Variance Measurement — Score: 7/10 — ADDRESSING

**Category:** Evaluation
**Priority:** Do soon (single-run scores are noisy)

**Description:**
Each fixture evaluated exactly once. LLM outputs are stochastic — same variant on same fixture produces different quality across runs. Single-run scores treated as ground truth for promotion, frontier, parent selection.

**Code evidence:**
- `evaluate_variant.py:1213-1218` — each fixture runs once via `_run_fixture_session()`. No repetition, no confidence intervals
- `_aggregate_suite_results()` (line 610) — simple mean of single-run scores

**Paper evidence:**
- **Meta-Harness**: "Robust evaluation protocol — multiple evaluation runs with variance measurement to account for stochasticity"
- **Hyperagents**: Runs "each method 5 times" and reports "95% bootstrap confidence intervals"

**Score rationale:** Fundamental measurement quality issue. Every downstream decision (parent selection, frontier, promotion) is based on noisy single-run scores. Compound variance from stochastic sessions + stochastic LLM evaluator makes the noise band probably ±0.1 on composite scores. Averaging across 12 fixtures helps but doesn't fully compensate. Both papers explicitly address this.

**Suggested fix:** Run each fixture 2-3 times, use median. Or at minimum, flag fixtures with high variance for re-evaluation before promotion.

---

## Gap 6: regression_floor Defined But Never Enforced — Score: 7/10 — ADDRESSING

**Category:** Evaluation
**Priority:** Do now (trivial fix, ~20 lines of Python)

**Description:**
Every fixture in `search-v1.json` defines `regression_floor` (0.02-0.03), but `evaluate_variant.py` never checks it. This is a clear bug — the field is parsed, stored, and completely ignored.

**Code evidence:**
- `eval_suites/search-v1.json:18,29,39,52,63,73,88,100,112,133,143,153` — every fixture defines `regression_floor`
- `evaluate_variant.py:359` — `regression_floor` parsed into `Fixture` dataclass
- `evaluate_variant.py:514,564,603` — stored in scored results
- `evaluate_variant.py` — `_search_promotion_summary()` checks ONLY `require_holdout` flag. **No per-fixture comparison, no regression_floor check.**
- `evaluate_variant.py:610-665` — `_aggregate_suite_results()` averages fixture scores, masking individual regressions

**Paper evidence:**
- **Meta-Harness**: "When multiple objectives are relevant, we evaluate candidates under Pareto dominance" — per-task regressions affect dominance
- **Hyperagents** (Appendix E.3.3): Autonomously develops per-task bias detection and flagging

**Score rationale:** Clear bug — code designed to use this field but doesn't. Per-fixture regressions compound across promotions (death by a thousand cuts). With only 3 fixtures/domain, a regression on 1 fixture is masked by the other 2. The holdout catches gross aggregate regressions but not per-fixture drift. Trivial fix.

**Suggested fix:** In `_search_promotion_summary()`, compare per-fixture scores against parent. Block if any regresses below `regression_floor`.

---

## Gap 7: Adversarial Evaluator Drift Risk — Score: 6/10 — ADDRESSING

**Category:** Evaluation
**Priority:** Do now (cheap insurance)

**Description:**
`scripts/evaluate_session.py` lives inside the variant. Core-lane meta agent CAN modify it. Lenient evaluator → less rework → lower cost → Pareto frontier REWARDS this.

**Code evidence:**
- `archive/v001/scripts/evaluate_session.py:1-351` — full evaluator inside variant
- `evaluate_session.py:37` — `DEFAULT_PASS_THRESHOLD = 0.5` (evolvable)
- `evaluate_session.py:293-294` — rework threshold `math.ceil(evaluated_count * 3/8)` (evolvable)
- `meta.md:26` — "evaluate_session.py | Evolvable session-time critique" — explicitly labeled evolution target
- `meta.md:53` — "scripts/evaluate_session.py is a legitimate evolution target. You may change its rubric, aggregation, thresholds, prompts, or invocation strategy"

**Paper evidence:**
- **Meta-Harness** (Section 5): Uses "regex-based audits for task-specific string leakage" — explicit gaming detection
- **Hyperagents** (Appendix E.3.3): Generation 66 showed 94% accept rate — evaluator gaming IS a real failure mode. System caught/corrected via autonomous bias detection.
- **Hyperagents** (Section 7): Outer evaluation intentionally NOT subject to modification

**Score rationale:** Real risk backed by Hyperagents evidence. But the external evaluator (`freddy evaluate variant`) is a strong safety net: lenient inner evaluator → lower quality artifacts → lower external scores → variant not promoted. The risk is subtle — it requires the cost savings from less rework to outweigh the quality drop on the Pareto frontier. Scored 6 not 7 because of this mitigation.

**Suggested fix:** Hash/structural invariant check on `evaluate_session.py` before scoring. Or track rework rates and flag variants where rework dropped suspiciously.

---

## Gap 4: No Cross-Variant Strategy Extraction — Score: 6/10 — ADDRESSING

**Category:** Feedback
**Priority:** Do soon (after 15-20+ variants in lineage)

**Description:**
`index.json` shows `changed_files` and `diffstat` per variant, but no mechanism correlates what types of changes drove improvements.

**Code evidence:**
- `archive_index.py:150-180` — `summarize_variant_diff` computes changed_files/diffstat per variant (descriptive only)
- `archive_index.py:287-328` — `public_entry_summary` has all needed raw data, but no cross-variant analysis
- `archive_index.py:369-402` — `refresh_archive_outputs` rebuilds index.json/frontier.json but performs NO cross-variant correlation
- `select_parent.py:24-35` — selection uses score and child count only

**Paper evidence:**
- **Hyperagents** (Appendix E.3.6): Autonomously develops multi-generation tracking with structured `IMPROVEMENTS.md` — "Problem Identified," "Root Cause Analysis," "Solution Implemented"
- **Meta-Harness**: Proposer "references over 20 prior candidates per step" and forms "explicit diagnosis of why early candidates failed"

**Score rationale:** Only matters once lineage has 15-20+ variants (currently v001). Also, fixing Gap 2 (trace access) partially addresses this — the meta agent could implicitly learn patterns from traces. Scored 6 not 7 because of these mitigations.

**Suggested fix:** Generate `strategy_analysis.md` during `refresh_archive_outputs()` correlating changed_files with score deltas. Feed to meta workspace.

---

## Gap 17: No Staged/Cheap-First Evaluation — Score: 6/10 — ADDRESSING

**Category:** Evaluation / Efficiency
**Priority:** Do soon (saves significant compute)

**Description:**
Every variant runs the full 12-fixture evaluation suite even if early fixtures reveal catastrophic failures. No early-exit mechanism.

**Code evidence:**
- `evaluate_variant.py:1209-1248` — `evaluate_search()` runs ALL fixtures sequentially with no early-exit. If first 3 fixtures score 0.0, remaining 9 still execute
- `smoke_summary` computed after all fixtures, used only for reporting, never for gating

**Paper evidence:**
- **Hyperagents** (Section 4.2): "first evaluate agents on a small subset... Only agents that demonstrate sufficient performance are subsequently evaluated on remaining tasks"
- **Meta-Harness**: "Efficient evaluation caching" and "staged optimization pipeline"

**Score rationale:** Both papers directly support staged evaluation. Real compute savings (~50%+ for bad variants). But this is an efficiency gap, not a quality gap — it doesn't make evolution better when it IS running, just cheaper. Scored 6 not 7 for this reason.

**Suggested fix:** Run 2-3 canary fixtures first. If all score below threshold, abort remaining.

---

## Gap 5: No Recombination / Crossover — Score: 5/10

**Category:** Search
**Priority:** Do when mature (needs diverse variants)

**Description:**
`select_parent.py` picks one parent. Clone and mutate. No multi-parent combination.

**Code evidence:**
- `select_parent.py:42-62` — `select_parent()` returns a single path via `random.choices(..., k=1)[0]`
- `evolve.sh:1005-1016` — selects one parent, clones it, meta agent mutates that clone
- `meta.md:54` — "You may inspect and transplant ideas from any archive variant" — closest thing to crossover

**Paper evidence:**
- **Meta-Harness**: Proposer "autonomously combined two successful lineages" — emergent recombination from archive access
- **Hyperagents** (Algorithm 1): `a' <- a.Modify(a, A)` — full archive as context. But formal operator is single-parent mutation.
- **Both papers** use single-parent mutation as the formal operator.

**Score rationale:** Lowered from 6 to 5. Neither paper implements formal crossover — both rely on emergent recombination through archive access, which autoresearch already partially provides via `meta.md:54`. The real bottleneck is Gap 2 (trace access), not a missing crossover operator.

---

## Gap 26: No Discarded-Variant Failure Analysis — Score: 5/10 — ADDRESSING

**Category:** Feedback / Search
**Priority:** Do soon (bundle with Gap 2)

**Description:**
When variants fail L1 validation or produce zero output, they're discarded with minimal logging. Failure patterns never analyzed or fed back to the meta agent.

**Code evidence:**
- `evolve.sh:1052-1055` — syntax failure logged minimally to `failures.log`, variant dir immediately deleted
- `evaluate_variant.py:1176-1185` — `_ensure_failure_logged()` writes minimal record
- `archive_cli.py:139-153` — `cmd_failures` lists failures, but evolution loop never reads it

**Paper evidence:**
- **Meta-Harness**: "Failure mode tracking — guides subsequent mutations away from known problem areas"
- **Hyperagents**: Persistent memory stores "causal hypotheses" about failures

**Score rationale:** Impact depends on actual failure rates (unknown — system hasn't run). If 5% of variants fail L1, this is negligible. If 40% fail, it's critical. Easy fix regardless.

---

## Gap 27: No Quality-Diversity / Novelty Objective — Score: 5/10

**Category:** Search
**Priority:** Do when mature

**Description:**
Parent selection has `1/(1+children)` novelty term, but no explicit behavioral diversity objective. System tracks HOW WELL variants score, not WHAT they do differently.

**Code evidence:**
- `select_parent.py:30-35` — novelty term is weak proxy (child count, not behavioral diversity)
- `frontier.py` — Pareto on score/cost/time but not behavioral dimensions

**Paper evidence:**
- **Meta-Harness**: "Population diversity maintenance" and "Novelty-seeking mechanisms"
- **Hyperagents**: Ablation "DGM-H w/o open-ended exploration fails to achieve meaningful improvement"

**Score rationale:** Hyperagents ablation is strong evidence, but autoresearch has two mitigations: (a) child-count penalty discourages over-selecting popular parents, (b) LLM meta agents produce inherently diverse mutations. The Hyperagents ablation removes the entire archive/open-ended component, which is more drastic than lacking a diversity metric.

---

## Gap 28: No Evaluation Caching for Unchanged Fixtures — Score: 5/10 — ADDRESSING

**Category:** Efficiency
**Priority:** Do soon

**Description:**
When a workflow-lane mutation changes only `programs/geo-session.md`, all 12 fixtures still run across all 4 domains. The 9 unchanged-domain fixtures produce redundant results.

**Code evidence:**
- `evaluate_variant.py:1213-1218` — iterates ALL active domains unconditionally
- `_suite_fixtures()` (line 365) — loads all fixtures; no affected-domain detection
- `archive_index.py:150-180` — computes `changed_files` AFTER evaluation (could be moved before)

**Paper evidence:**
- **Meta-Harness**: "Efficient evaluation caching — reusing evaluation results for identical configurations"

**Score rationale:** Saves ~75% compute for workflow-lane mutations. But efficiency only — doesn't improve evolution quality. LLM stochasticity means cached parent scores are no less valid than fresh noisy evaluations of unchanged code.

---

## Gap 19: No Convergence / Plateau Detection — Score: 5/10

**Category:** Search / Operations
**Priority:** Do when mature

**Description:**
Evolution runs for fixed `MAX_ITERATIONS` with no detection of stalled progress.

**Code evidence:**
- `evolve.sh:998` — `for ((i=1; i<=MAX_ITERATIONS; i++))` — blind countdown, no adaptive stopping

**Paper evidence:**
- **Meta-Harness**: "Early stopping on convergence," "Plateau detection," "Diversity-based termination"
- **Hyperagents**: Tracks improvement trends via PerformanceTracker

**Score rationale:** Saves money but doesn't improve quality when evolution IS running. Theoretical until the system has been through multiple campaigns.

---

## Gap 8: No Post-Promotion Canary or Automated Rollback — Score: 5/10

**Category:** Operations
**Priority:** Do when mature

**Description:**
`evolve.sh promote` updates `current.json`. No A/B comparison, no production quality monitoring, no circuit-breaker.

**Code evidence:**
- `evolve.sh:758-784` — promote: `mark_promoted` → `set_current_head` → `refresh_archive` → done
- `evolve.sh:821-828` — rollback is manual only

**Paper evidence:**
- Neither paper addresses production deployment. Both operate in pure benchmark settings.

**Score rationale:** Holdout gate provides pre-promotion protection. This is a production-operations concern unique to autoresearch, not addressed by either paper. Only matters once promoting frequently at scale.

---

## Gap 10: Single Evaluation Model, No Ensemble — Score: 5/10

**Category:** Evaluation
**Priority:** Do when mature

**Description:**
All scoring through `codex/gpt-5.4/high`. Same model for search AND holdout evaluation.

**Code evidence:**
- `eval_suites/search-v1.json:4-8` — single `eval_target`
- `evaluate_variant.py:143-172` — `_require_eval_target` enforces single model

**Paper evidence:**
- Neither paper uses ensemble judges. Meta-Harness tests transfer to "five held-out models." Hyperagents constructs validation subsets as Goodhart mitigation.

**Score rationale:** Neither paper does better. Holdout partially mitigates, though using the same model for both search and holdout means model-specific biases persist through both gates.

---

## Gap 11: Fixed External Evaluator (Goodhart Risk) — Score: 5/10

**Category:** Evaluation
**Priority:** Do when mature

**Description:**
`freddy evaluate variant` never changes. Over generations, variants optimize for evaluator's biases.

**Code evidence:**
- `evaluate_variant.py:520-530` — `freddy evaluate variant` is external, fixed
- `meta.md:32-38` — acknowledges this: "The only reliable strategy is to make outputs genuinely better for a human operator"

**Paper evidence:**
- **Meta-Harness** (Section 5): Uses "regex-based audits for task-specific string leakage"
- **Hyperagents** (Appendix E.3.3): Generation 66 — concrete evaluator gaming example
- **Hyperagents** (Section 7): Keeps evaluation protocols fixed for safety

**Score rationale:** Inherent limitation shared with both papers. Meta-Harness keeps proposer fixed; Hyperagents keeps outer loop fixed. The meta.md instruction to optimize for human quality is a reasonable soft mitigation.

---

## Gap 12: Meta Agent Has No Memory Across Iterations — Score: 5/10

**Category:** Search
**Priority:** Consider

**Description:**
Each mutation launches a fresh meta agent. Workspace destroyed after each iteration. Meta agent can't build on its own reasoning.

**Code evidence:**
- `evolve.sh:861-898` — fresh `claude -p` or `codex exec` each time
- `evolve.sh:1020-1041` — fresh workspace, deleted at line 1041
- `meta.md:14-17` — archive as "external memory" is read-only scores

**Paper evidence:**
- **Hyperagents** (Appendix E.3.7): DGM-H autonomously develops `MemoryTool` with `store()`, `retrieve()`, `list_keys()`. Memory "actively consulted during subsequent self-modification steps."
- **Meta-Harness**: Proposer has access to complete history including prior meta-session logs

**Score rationale:** Hyperagents evidence is compelling (MemoryTool developed autonomously), but Meta-Harness achieves strong results using archive as implicit memory. Autoresearch archive provides indirect signal through scores and changed_files.

---

## Gap 30: L1 Validation Is Shallow — Score: 5/10 — ADDRESSING

**Category:** Safety / Evaluation
**Priority:** Do soon (bundle with Gap 6)

**Description:**
Layer 1 only checks Python syntax (`py_compile`) and shell syntax (`bash -n`). Doesn't check imports or basic executability.

**Code evidence:**
- `evaluate_variant.py:384-411` — `layer1_validate()` runs `py_compile.compile()` and `bash -n`. No import check.
- `evolve.sh:1043-1056` — additional syntax check with same approach

**Paper evidence:**
- **Hyperagents**: Validates code compiles AND executes basic functionality before full evaluation

**Score rationale:** Mutation adding `from nonexistent_module import foo` passes L1, crashes at runtime, wastes ~30 min of L2/L3 evaluation. Quick fix (`python3 -c "import run"`) catches most import failures in seconds.

---

## Gap 20: No Adaptive Mutation Rate / Intensity — Score: 4/10

**Category:** Search
**Priority:** Probably skip

**Description:**
Meta agent receives identical `meta.md` regardless of evolutionary progress. No signal to be more/less aggressive.

**Code evidence:**
- `evolve.sh:1026-1030` — template substitution identical every iteration: only `{archive_path}`, `{iterations_remaining}`, `{lane}`
- `meta.md:1-66` — fixed instructions

**Paper evidence:**
- **Meta-Harness**: "Adaptive mutation rates — adjusting intensity based on recent progress"
- **Hyperagents** (Appendix E.3.2): Develops "compute-aware optimization" autonomously

**Score rationale:** `{iterations_remaining}` provides some implicit signal. The meta agent can observe score trends in `index.json`. Partial mitigation exists.

---

## Gap 23: No Sandbox Isolation Between Evaluation Fixtures — Score: 4/10

**Category:** Safety / Evaluation
**Priority:** Probably skip

**Description:**
All fixtures run sequentially in the same variant directory. Shared state could leak between fixtures.

**Code evidence:**
- `evaluate_variant.py:1213-1218` — fixtures run sequentially in same `variant_dir`
- Session output goes to separate `sessions/{domain}/{client}` dirs, providing partial isolation

**Paper evidence:**
- **Hyperagents** (Section 6): "carefully sandboxed environments with enforced resource limits"

**Score rationale:** Theoretical risk. Sessions write to separate subdirectories. Cross-fixture contamination would require a mutation that writes to shared paths, which is an edge case.

---

## Gap 24: Cost Estimation Is Time-Based Proxy — Score: 4/10

**Category:** Evaluation
**Priority:** Probably skip

**Description:**
[RESOLVED by Unit 7 (R17)] Fake cost tracking (`_estimate_cost_usd`, `DEFAULT_COST_PER_MINUTE`, `api_cost_estimate`) deleted. Replaced with `max_wall_time_seconds` in `WorkflowConfig` for session time-bounding. Wall-time is the only resource metric now tracked.

---

## Gap 32: Metacognitive Self-Modification Limited — Score: 4/10

**Category:** Architecture
**Priority:** Skip (overlaps Gap 16)

**Description:**
`meta.md` is editable but outer shell invocation (timeout, tools, sandbox, workspace prep, parent selection, evaluation) is hardcoded.

**Code evidence:**
- `evolve.sh:861-898` — `run_meta_agent()` hardcodes: 1800s timeout, fixed tool set, fixed sandbox
- `meta.md:10` — mentions "this prompt itself" as mutation target, but shell parameters are frozen

**Paper evidence:**
- **Hyperagents** core thesis: "the meta-level modification procedure is itself editable"
- **Hyperagents** (Appendix E.5): DGM-H modifies its own parent selection

**Score rationale:** Overlaps Gap 16. Both papers acknowledge practical limits — Meta-Harness keeps proposer fixed, Hyperagents keeps outer loop components fixed.

---

## Gap 13: No Cost-Aware Mutation Guidance — Score: 4/10

**Category:** Search
**Priority:** Probably skip

**Description:**
Pareto frontier tracks cost, but meta agent doesn't know about cost as an optimization objective.

**Code evidence:**
- `frontier.py:165-172` — cost is a min objective in frontier
- `select_parent.py:24-27` — parent selection uses only score, NOT cost
- `meta.md:1-67` — no mention of cost

**Paper evidence:**
- **Meta-Harness**: "improves by 7.7 points while using 4x fewer context tokens"
- **Hyperagents** (Appendix E.3.2): Develops "compute-aware optimization" autonomously

**Score rationale:** Pareto frontier handles cost at the selection level. Cheaper variants that score well are naturally favored. The meta agent doesn't need to explicitly optimize for cost — selection pressure does this.

---

## Gap 14: evolve.sh Is 1090 Lines of Bash — Score: 4/10

**Category:** Operations
**Priority:** Probably skip

**Description:**
Core orchestration in bash with inline Python heredocs.

**Code evidence:**
- `evolve.sh:1-1091` — includes inline Python for lineage manipulation
- `finalize_candidate_ids` (lines 573-629) — 55-line Python program inside bash heredoc

**Score rationale:** Operational maintainability concern, not an algorithmic gap. Doesn't affect evolution quality. Rewrite when it actively blocks feature development.

---

## Gap 15: No Warm-Start / Cross-Domain Transfer — Score: 4/10

**Category:** Architecture
**Priority:** Skip (research problem)

**Description:**
New domain starts from v001 with zero transfer. Lane system prevents cross-pollination.

**Code evidence:**
- `select_parent.py:50-51` — filters by lane; cross-lane parents only as fallback
- `archive_index.py:236-245` — lane scoping removes cross-lane files

**Paper evidence:**
- **Hyperagents** (Section 5.2): Transfer hyperagents achieve imp@50 of 0.630 on unseen domain (vs 0.0 for initial agent)
- **Hyperagents** (Section 5.3): Transferable improvements include memory, tracking, bias detection

**Score rationale:** Hyperagents transfer results are compelling but this is a research problem. Only relevant when adding new domains. Current 5 lanes all start from same v001.

---

## Gap 33: No Sensitivity/Ablation Analysis — Score: 4/10

**Category:** Feedback / Search
**Priority:** Skip

**Description:**
When a variant changes multiple files, no mechanism determines which change drove the improvement.

**Code evidence:**
- `archive_index.py:150-180` — records WHAT changed but not WHICH change helped

**Paper evidence:**
- **Meta-Harness**: "Sensitivity analysis" and "Ablation study integration"

**Score rationale:** Expensive to implement (requires running partial variants). Marginal benefit at current scale.

---

## Gap 22: Parent Selection Snapshot Stale Within Cycle — Score: 4/10

**Category:** Search
**Priority:** Skip

**Description:**
Within an iteration, all candidates selected from a stale lineage snapshot. 2nd and 3rd candidates can't benefit from 1st's results.

**Code evidence:**
- `evolve.sh:1002-1003` — snapshot copied once per iteration, not refreshed between candidates

**Score rationale:** Minor with default 3 candidates/iteration. Would matter more with higher parallelism.

---

## Gap 9: Monitoring Fixtures Temporally Frozen — Score: 4/10

**Category:** Evaluation
**Priority:** Fix when expanding fixtures (ties into Gap 3)

**Description:**
All three monitoring fixtures pinned to 2026-W12.

**Code evidence:**
- `eval_suites/search-v1.json:90-93,104-107,118-121` — identical week pins
- `evaluate_variant.py:414-431` — no dynamic week selection

**Score rationale:** Subset of Gap 3 (small suite). Fixing Gap 3 naturally addresses this. Domain-specific to monitoring only (1 of 4 domains). Neither paper addresses temporal variation.

---

## Gap 16: No Structural Evolution of Session Architecture — Score: 4/10

**Category:** Architecture
**Priority:** Skip

**Description:**
Meta agent can edit code within variant but not fundamental architecture (phase state machine, results.jsonl schema, two-layer evaluation).

**Code evidence:**
- `evaluate_variant.py:444-457` — runner invocation hardcodes `--strategy fresh --domain ...` pattern
- `evaluate_session.py:60-302` — two-layer pipeline structure is architecturally fixed

**Paper evidence:**
- **Hyperagents**: "meta-level modification procedure is itself editable"
- **Meta-Harness**: Proposer architecture fixed. Both acknowledge practical limits.

**Score rationale:** Far more headroom from better mutations within the existing structure than from reinventing the structure.

---

## Gap 21: lineage.jsonl Unbounded Growth — Score: 3/10

**Category:** Operations / Scalability
**Priority:** Skip

**Description:**
Append-only JSONL with full entry re-appended on every update.

**Code evidence:**
- `archive_index.py:90-99` — only appends
- `load_latest_lineage()` (line 78) — reads ALL lines, deduplicates in memory

**Score rationale:** At moderate scale (50-100 variants), this is 1-2 seconds of parsing. Performance issue, not a quality issue. Won't matter for hundreds of variants.

---

## Gap 31: Monitoring Placeholder Context Fragility — Score: 3/10

**Category:** Evaluation / Safety
**Priority:** Skip

**Description:**
Monitoring fixtures use env var references that RuntimeError if unset.

**Code evidence:**
- `eval_suites/search-v1.json:84-121` — `${AUTORESEARCH_SEARCH_MONITORING_*_CONTEXT}` references
- `evaluate_variant.py:175-186` — `_expand_manifest_value()` raises RuntimeError

**Score rationale:** Deployment config issue, not an evolution architecture gap.

---

## Gap 25: Meta Agent Environment Over-Sanitized — Score: 3/10

**Category:** Safety / Feedback
**Priority:** Skip

**Description:**
Meta agent launched with `env -i` clearing all context.

**Code evidence:**
- `evolve.sh:867-878` — claude backend uses `env -i` with explicit whitelist

**Score rationale:** Partially intentional (anti-gaming). Providing safe non-secret context (eval target model) could help, but the security rationale is sound.

---

## Gap 29: Holdout Baseline Re-Evaluation Redundancy — Score: 2/10

**Category:** Efficiency
**Priority:** Skip

**Description:**
First finalization in a cycle re-evaluates baseline holdout. Subsequent finalists hit cache.

**Code evidence:**
- `evaluate_variant.py:1145-1173` — baseline check correctly caches after first call

**Score rationale:** Correctly implemented. Only the first call in a cycle pays the cost. Negligible.
