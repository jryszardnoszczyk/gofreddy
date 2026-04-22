---
title: "refactor: Pipeline simplifications — 35 over-engineering fixes"
type: refactor
status: completed
date: 2026-04-22
origin: docs/plans/2026-04-22-006-pipeline-overengineering-implementation-research.md
---

# Pipeline Simplifications — 35 Over-Engineering Fixes

## Overview

Execute 35 agreed simplifications across three pipelines (harness, audit pipeline plan, autoresearch) plus cross-pipeline infrastructure. Built from six rounds of audit + deep implementation research. Goal: remove programmatic scaffolding where agents produce better results, harden integrity boundaries where deterministic is correct, consolidate shared patterns. Ordered into 15 implementation units across 6 phases, dependency-sequenced. Tests only where genuinely important (integrity boundaries, correctness-critical paths). Per JR's no-caps philosophy: no budgets, no cognitive limits, no quality auto-aborts; existing runaway-loop sentinels stay. Premise revisit: after 3 evolution cycles post-landing, re-examine the no-caps bet against Unit 3's inner-vs-outer correlation + the calibration judge's adjusted-vs-raw score distribution. If drift signals are persistent, reopen R-#21 (delta observability) and accelerate R-#23 (rubric-anchor refactor).

Per-item specs (today / why / approach / code / risks) live in the 5 cluster docs under `docs/plans/2026-04-22-006-impl-cluster-*.md`. This plan is the sequencing + decision record. Open the cluster docs for implementation detail.

## Requirements Trace

35 items grouped by surface. Full description per item in the referenced cluster doc.

**Harness (6 items):** R-#1 drop per-cycle smoke + `smoke-cli-client-new` litter · R-#2 delete no-progress gate · R-#3 replace `inventory.generate` with breadcrumb · R-#4 loosen `Verdict.parse` synonyms · R-#5 tighten `_TRANSIENT_PATTERNS` with JSON parse · R-#6 auto-derive `_FIXER_REACHABLE`. *(See cluster-1-harness.md.)*

**Audit plan residuals (5 items):** R-#7 `HealthScore` Pydantic + prompt (0-100 scale) · R-#8 7 per-agent rubric blocks + migration note · R-#9 Finding Pydantic constraints + per-section sort · R-#11 Tier-1 tool allowlist consolidation · R-#22 tactical-vs-strategic critique prompt + Stage-3 sweep. *(See cluster-2-audit-plan.md.)*

**Autoresearch hardening (6 items):** R-#12 regenerate structural-validator sections from `structural.py` (fixes live 5x drift bug) · R-#13 SHA256 hash check on critique prompt + threshold constants · R-#14 inner-vs-outer correlation telemetry · R-#15 Pareto-constraint critique agent (soft-review only) · R-#24 subprocess-isolate inner critique · R-#25 mistune AST parser for findings. *(See cluster-3-autoresearch.md.)*

**Autoresearch agentic replacements (3 items):** R-#29 parent-selection agent · R-#30 alert-thresholds agent · R-#31 `geo_verify.py` agent verdict. *(See cluster-4-pass2-ae.md.)*

**Evaluation + competitive (7 items):** R-#32 paraphrase-checking agent replaces `fuzzy_match` · R-#33 replace cap-at-3 gradient gate with calibration judge · R-#34 drop length-factor (rubrics cover proportionality) · R-#35 drop competitive 500-char/3-header structural gate · R-#36 drop rework-cap + synth-ratio gates · R-#37 claim-grounding agent replaces digest-hallucination regex · R-#38 agent fallback for ad-domain near-matches. *(See cluster-4-pass2-ae.md.)*

**CLI (2 items):** R-#39 monitor summarizer (Claude CLI subprocess) · R-#40 producer-owned `evaluation-scope.yaml` replacing `_DOMAIN_FILE_PATTERNS`. *(See cluster-5-cli-cross.md.)*

**Cross-pipeline (2 items):** R-#16 promote `autoresearch/report_base.py` → `src/shared/reporting/` · R-#18 name 3 safety tiers under `src/shared/safety/`. *(See cluster-5-cli-cross.md.)*

**Not in this plan (6 items):**
- *Already applied (1):* R-#10 (shipped in audit plan R5).
- *Deferred (2):* R-#20 per-track worktrees (conditional on scaling); R-#23 rubric anchor refactor (pending Unit 3 telemetry evidence — note: Unit 11 opens the gap R-#23 closes, so deferral is coupled, not independent).
- *Planned future (1):* R-#26 `finding_lib` extraction (3-4 weeks out, after audit plan U2 ships).
- *Non-actions (2):* R-#27 (don't unify scorers), R-#28 (don't build orchestrator framework).

**Withdrawn:** R-#17 graceful_kill extract (low leverage), R-#19 drop check_scope peer-filter (unsafe — load-bearing under parallel execution; comment strengthened instead), R-#21 test-pass-count delta (withdrawn to honor no-caps philosophy; note deltas *observe* while caps *prevent* — Unit 3's `|delta| > 0.15` is an observation, not a cap; if the no-caps premise revisit reopens R-#21, it returns as observability, not a gate).

## Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| No caps/limits | Applied throughout | "Free-flowing agents produce best results." Withdraws R-#21; softens R-#15 to soft-review-only. **Runaway-loop backstops stay untouched** — `max_walltime=14400` (harness), `META_AGENT_TIMEOUT=1800` (autoresearch), `max_turns=500/800` (audit plan SDK sentinel), `jwt_envelope_padding=600`. These are not cognitive caps; they're "something is genuinely broken" ceilings at 5-10× expected normal. |
| Agent runtime | Claude Code CLI subprocess (`claude -p …`) for R-#30, #31, #38, #39 and Unit 11/12 calls; **AsyncOpenAI + Pydantic for R-#29** | Claude CLI is the default pattern (no new SDK dep). R-#29 is the single exception because `select_parent.py` is already a Python module (not a shelled agent); AsyncOpenAI sidesteps `claude -p` shell-quoting and matches the closer in-process pattern. |
| Judgment model | Sonnet | Handles structured critique at this tier; Opus only on observed misses. |
| Hash-check scope | Include threshold constants | `HARD_FAIL_THRESHOLD` / `DEFAULT_PASS_THRESHOLD` / `compute_decision_threshold` share attack surface. |
| Shared infra path | `src/shared/` umbrella | Signals "infra, not product code"; future `finding_lib` lands there. |
| Pareto critic mode | Soft-review only, diff-only | Never rejects; logs to `eval_digest.md`. |
| Health score scale | 0-100 | Matches Ahrefs / SEMrush / Moz industry pattern. |
| Peer-filter | Keep, defer per-track worktrees (F1.2) | Load-bearing under parallel fixers; F1.2 is a 3-5d refactor for a problem not currently binding. |

## Implementation Units

Ordered by dependency. Phase boundaries are checkpoints; units within a phase can run in parallel.

### Phase 1 — Foundations

- [x] **Unit 1: Harness micro-cleanups (R-#1, #2, #4, #5, #6)**
  - Modify: `harness/run.py`, `harness/engine.py`, `harness/safety.py`, `harness/SMOKE.md`, `harness/prompts/verifier.md`.
  - Approach: one commit bundling the following, attributed to the correct module:
    - *harness/run.py* — remove cycle-start smoke call; delete `RunState.zero_high_conf_cycles` field (line 38) and the no-progress gate at lines 155-157; sweep `_print_summary` / `exit_reason` consumers for remaining `"no-progress"` string references.
    - *harness/engine.py* — introduce `_VERIFIED_TOKENS = frozenset({"verified","pass","passed","ok"})` membership check in `Verdict.parse`; split `_TRANSIENT_PATTERNS` (line 31) into prose substrings + word-bounded regexes; add `_has_error_event` mirroring `parse_rate_limit` (line 173) — this *replaces* the existing `"\"type\":\"error\""` entry in `_TRANSIENT_PATTERNS`, not augments it.
    - *harness/safety.py* — auto-derive `_FIXER_REACHABLE = re.compile("|".join(p.pattern for p in SCOPE_ALLOWLIST.values()))`; strengthen the "Under parallel execution" paragraph inside `check_scope`'s docstring (lines 56-65) explaining the peer-filter is load-bearing.
    - *harness/SMOKE.md* + *harness/prompts/verifier.md* — drop the `smoke-cli-client-new` block; list verifier synonyms.
  - Tests: existing `tests/harness/test_engine.py` + `test_safety.py` cover the changed surfaces; no new tests needed.

- [x] **Unit 2: Autoresearch foundations (R-#12, #25)**
  - Modify: `src/evaluation/structural.py` (append `STRUCTURAL_DOC_FACTS` dict per domain), `autoresearch/evolve.py` (call regen after clone — single entry point; `runtime_bootstrap.py` edit dropped because it `execv`s per session and would fire regen inside the frozen variant), `autoresearch/report_base.py:82-149` (replace `parse_findings` state machine with mistune AST walk).
  - Create: `autoresearch/regen_program_docs.py` — rewrites `## Structural Validator Requirements` section in each `programs/<domain>-session.md` wrapped in autogen markers (`<!-- AUTOGEN:STRUCTURAL:START -->` / `<!-- AUTOGEN:STRUCTURAL:END -->`). Handles both in-place replacement (competitive-session.md line 138; monitoring-session.md line 77) and first-time creation (geo-session.md + storyboard-session.md currently lack the section — insert immediately before `## Notes` if present, else end-of-file).
  - **Agent-edit discipline:** add a preamble line to each `*-session.md` (and to `meta.md`'s edit guidelines): *"Do not edit content between `<!-- AUTOGEN:STRUCTURAL:START -->` and `<!-- AUTOGEN:STRUCTURAL:END -->` — it is regenerated from `structural.py` on every variant clone; hand-edits are overwritten."* Without this, agents that rewrite program docs in the meta-loop overwrite the regenerated section and re-introduce the drift this unit fixes.
  - Scope of initial `STRUCTURAL_DOC_FACTS`: include only the gates surviving Unit 12's deletions (so CI doesn't red the day Unit 12 lands). Gates removed in Unit 12 (`<500 chars` + `<3 headers`, `no_excessive_rework`, `synth_matches_stories`, digest-hallucination regex) are *not* entered in the dict.
  - One-time: `python3 -m autoresearch.regen_program_docs autoresearch/archive/current_runtime/programs` to fix today's drifted docs.
  - Tests: `tests/autoresearch/test_structural_doc_facts.py` paired test — **bidirectional**: every `STRUCTURAL_DOC_FACTS` bullet maps to a gate function, AND every gate function in `structural.py` has a bullet. Catches both doc-ahead-of-code (the live bug) and code-ahead-of-doc drift. Justified because doc-code drift is the live bug this unit fixes.

- [x] **Unit 3: Inner-vs-outer correlation telemetry (R-#14)**
  - Modify: `autoresearch/evaluate_variant.py` — add `_extract_inner_pass_rate(session_dir)`; thread `inner_pass_rate`, `outer_pass_rate`, `pass_rate_delta` into `_score_session` return; aggregate `mean_pass_rate_delta` in `_aggregate_suite_results`. `autoresearch/archive_index.py:public_entry_summary` — surface to `index.json`. Log WARN at `|delta| > 0.15`; append to `eval_digest.md`.
  - Approach: fuzzy signal extraction from existing `results.jsonl` — `KEEP_TOKENS`/`REWORK_TOKENS` sets filtered by phase (`analyze|synthesize|verify|session_eval|evaluate`) so gather/done noise doesn't dominate.
  - Validation: run against 2-3 archived sessions; spot-check that the computed `pass_rate_delta` matches a human read of inner-vs-outer agreement on those sessions. If correlation looks noisy, tighten phase filters or token sets before merging. (Unit 11's calibration judge is the primary drift detector; this telemetry is secondary observation for the no-caps premise revisit.)
  - Tests: none needed — output lands in `scores.json`; validated via the archived-session spot-check above.

### Phase 2 — Inventory replacement

- [x] **Unit 4: Replace `inventory.generate` with breadcrumb (R-#3)**
  - Create: `harness/INVENTORY.md` — ~25-line pointer file (`freddy --help`, `curl /openapi.json`, `frontend/src/lib/routes.ts`, `ls autoresearch/*.py`).
  - Modify: `harness/run.py:76` — replace `inventory.generate(...)` with `shutil.copy(wt.path / "harness" / "INVENTORY.md", run_dir / "inventory.md")`.
  - Delete: `harness/inventory.py`.

### Phase 3 — Shared infrastructure (parallel within phase)

- [x] **Unit 5: Promote `autoresearch/report_base.py` → `src/shared/reporting/` (R-#16)**
  - Move: `autoresearch/report_base.py` (577 LOC) wholesale to `src/shared/reporting/report_base.py`. Do NOT split into parsers/renderers/scaffold/pdf/cli now — deferred until audit plan Stage 5 actually needs the categorical separation. (Splitting before a second consumer reveals which categories are real is framework-ahead-of-need.)
  - Extract: `scrub` + `SECRET_PATTERNS` into `src/shared/reporting/scrub.py` — this IS load-bearing (two consumers today: autoresearch and `harness/review.py`'s local `_SECRET_PATTERNS`). Lift the stronger harness patterns; autoresearch's weaker set is subsumed.
  - Create `src/shared/reporting/__init__.py` with an **enumerated `__all__`** (not star re-export) listing exported symbols — star-import silently drops underscore-prefixed helpers that consumers may rely on. Enumerate: load_json, load_jsonl, load_markdown, parse_findings, render_findings, render_session_log, render_logs_appendix, render_session_summary, render_report_md, unavailable_banner, build_html_document, BASE_CSS, BADGE_COLORS, esc, truncate, md_to_html, find_chrome, html_to_pdf, common_argparse, scrub, SECRET_PATTERNS.
  - Replace: `autoresearch/report_base.py` with a shim that emits `DeprecationWarning` on import naming the new path + re-exports by-name from `src.shared.reporting` + `src.shared.reporting.scrub`.
  - Modify: `harness/review.py` — drop local `_SECRET_PATTERNS` + `_scrub`; `from src.shared.reporting.scrub import scrub, SECRET_PATTERNS`.
  - Variant runtime PYTHONPATH: confirm frozen variants can import `src.shared.reporting`. If they can't, ship the `scrub` utility at an autoresearch-local path and let harness import from there.
  - `jinja.py` deferred — audit plan adds when Stage 5 actually needs template rendering; no speculative infrastructure.
  - Tests: no new test file. `scrub` is a lift-and-shift of existing regexes; existing consumers passing is sufficient coverage.

- [x] **Unit 6: Co-locate safety primitives → `src/shared/safety/` (R-#18)**
  - Create: `src/shared/safety/tier_a.py` (`build_scoped_toolbelt`, `per_action_confirm` — net-new for audit plan, no production consumer yet), `tier_b.py` (port `path_owned_by_lane` + lane-prefix logic from `autoresearch/lane_paths.py` + `_sync_filtered` from `autoresearch/lane_runtime.py:90`), `tier_c.py` (port `snapshot_dirty` / `working_tree_changes` / `check_scope` / `check_no_leak` from `harness/safety.py`; parameterize BOTH the scope allowlist AND the artifacts-ignore regex — harness passes `{scope: SCOPE_ALLOWLIST, artifacts: HARNESS_ARTIFACTS}`; autoresearch passes its own pair).
  - `__init__.py` — 2-3 paragraph module docstring naming each tier's mechanism + threat model. **No `SafetyTier = Literal[...]` type alias**; no `SAFETY_TIER` constants added to `harness/config.py` / `autoresearch/runtime_bootstrap.py`. The Literal has no dispatcher and the constants have no callers — pure naming ceremony. Add only if/when a caller dispatches on tier.
  - Replace: `harness/safety.py` with shim that emits `DeprecationWarning` on import + re-exports from `src.shared.safety.tier_c` with harness-specific allowlist bound; move the harness allowlist definition into `harness/config.py` so the shim is a *pure* re-export (mixed-logic shims fossilize).
  - Replace: `autoresearch/lane_paths.py` with shim that emits `DeprecationWarning` + forwards to `src.shared.safety.tier_b` with autoresearch lane prefixes bound.
  - Tests: net-new `tests/shared/safety/test_tier_a.py` **deferred** into the audit plan's own implementation where `tier_a` has a real consumer. Existing harness/autoresearch tests cover tier_b/tier_c via their existing suites.

### Phase 4 — Integrity hardening (ship as pair)

- [x] **Unit 7: SHA256 hash check + subprocess isolation (R-#13, #24)**
  - Threat model: autoresearch is a self-modifying meta-loop — variants rewrite their own `programs/*.md`. The honor-system note at `current_runtime/meta.md:70` ("Do not modify `_build_critique_prompt`") is social, not enforced. The concern is *integrity drift*, not a remote attacker: a variant tampering with the critique prompt to score itself higher escapes the evaluator silently. The hash check + subprocess isolation convert the honor system into a gated invariant.
  - *Canonical module location:* `build_critique_prompt`, `GRADIENT_CRITIQUE_TEMPLATE`, `HARD_FAIL_THRESHOLD`, `DEFAULT_PASS_THRESHOLD`, `compute_decision_threshold` all live in `autoresearch/harness/session_evaluator.py` (thresholds line 22, template line 31, builder line 52). `scripts/evaluate_session.py` only imports them. Hash source + subprocess entrypoint both point at `session_evaluator.py`.
  - Create: `autoresearch/critique_manifest.py` — `compute_expected_hashes()` hashes the five symbols above from `autoresearch.harness.session_evaluator` via runtime introspection.
  - Modify: `autoresearch/evolve.py` — write `critique_manifest.json` per variant at clone; `autoresearch/evaluate_variant.py:413-453` (`layer1_validate`) — load manifest + run introspection in `python3 -I` subprocess with explicit `PYTHONPATH`; fail L1 on hash mismatch. Hash check runs at the top of `layer1_validate` before `py_compile` / `bash -n` so tampered variants fail fast.
  - Create: `autoresearch/harness/prompt_builder_entrypoint.py` — isolated subprocess entrypoint (imports `build_critique_prompt` from `autoresearch.harness.session_evaluator`, reads criteria from stdin, returns prompts on stdout, asserts `sys.modules` allowlist).
  - Modify: `autoresearch/archive/current_runtime/scripts/evaluate_session.py` — replace in-process `build_critique_prompt` call with `subprocess.run` via `python3 -I -m autoresearch.harness.prompt_builder_entrypoint`, `cwd=/tmp/autoresearch-frozen-<rand>`.
  - Modify: `autoresearch/archive/current_runtime/meta.md:70` (note: plain `meta.md`, not under `programs/`) — update note text to reference the enforced gate, and correct the `scripts/evaluate_session.py` mislocation (the builder is defined in `autoresearch/harness/session_evaluator.py`; `scripts/evaluate_session.py` only imports it).
  - One-time: `autoresearch/scripts/rebuild_manifests.py` — backfill existing variants with a **grace manifest** (records today's hashes; L1 accepts pre-Unit-7-era variants without hash-match). Explicit policy: backfill does NOT attempt to detect retroactive tampering — that's out of scope.
  - Tests: `tests/autoresearch/test_critique_manifest.py` (stable hash + tamper detection), `tests/autoresearch/test_layer1_validate.py` (tampered variant fails L1), `tests/autoresearch/test_prompt_builder_isolation.py` (polluted `PYTHONPATH` doesn't win). Integrity boundary — tests earn their place.

### Phase 5 — Audit plan residual gaps (plan edits only)

- [x] **Unit 8: Close audit plan R5 residuals (R-#7, #8, #9, #11, #22)**
  - Modify: `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`.
  - Specific content to add per cluster doc `2026-04-22-006-impl-cluster-2-audit-plan.md`:
    - `HealthScore` Pydantic (0-100 throughout; band derived deterministically from overall — no validator, no retry).
    - 7 per-agent rubric blocks naming `report_section` values the agent picks from.
    - Finding Pydantic constraints: `evidence_urls: list[HttpUrl] = Field(min_length=1)` (keep — structural, not cognitive). Drop `min_length` on `recommendation` — that would be a cap; the `#22` critique pass enforces quality instead.
    - Per-section sort rule: `(severity desc, confidence_rank desc, has_reach desc, reach desc, title asc)`.
    - Tier-1 tool allowlist consolidation block (~15 handlers) in U2.5.
    - `RECOMMENDATION_CRITIQUE_PROMPT` per cluster doc + Stage-3 cross-agent Sonnet sweep.
  - Migration note: pre-R5 branches delete both `rubric_themes.yaml` and `rubric_theme`/`lens_weight_share` fields; no data migration (no audit has shipped).

### Phase 6 — Agentic replacements (parallel within phase, after Units 1-3)

**Pre-Phase-6 gate — rubric-coverage verification result (2026-04-22):**

- **Unit 11 length-factor claim verified partially wrong.** MON-8 ("Concision — Word count proportional to importance. High insight-to-word ratio. ~2,500 words target") DOES measure length proportionality for monitoring digests. **CI-8 does NOT** — actual CI-8 text is "Data gaps as findings — What you don't have is stated and analyzed. Missing data is a finding, not papered over with speculation." No CI-* criterion measures length. Same gap for SB-* and geo rubrics. **Decision:** proceed with Unit 11 dropping length-factor. The R-#33 calibration judge (same unit) is the cross-domain safety net — it sees full output text and can flag egregious length failures during evidence verification. If monitoring degrades in the first 3 evolution cycles we know MON-8 handles it; if competitive/storyboard/geo degrade, add an explicit CI-9/SB-9/GEO-9 "Proportionality" criterion rather than re-introducing the Python multiplier.
- **Unit 12 rework + synth-ratio rationale corrected.** MON-2 (severity classification) and MON-8 (concision) do not cover process-efficiency signals. The honest rationale: `no_excessive_rework` and `synth_matches_stories` were PROCESS gates, not OUTPUT quality measures. Good output that takes thoughtful rework is fine; a high synth/story ratio can indicate either over-iteration or thorough exploration. **Decision:** drop the process gates because process efficiency isn't a quality signal, not because rubrics absorb the signals. Output quality is judged by the gradient + calibration judges on the final artifact.


- [x] **Unit 9: Pareto-constraint critique agent (R-#15)**
  - Create: `autoresearch/program_prescription_critic.py` — loads (old, new) program pair; calls `freddy evaluate critique` with a prompt distinguishing PRESCRIPTION from DESCRIPTION (full prompt in cluster-3 research doc). Returns `{verdict, reasoning}` — logged to `variant_dir/critic_reviews.md`. Never rejects.
  - Modify: `autoresearch/evolve.py` — insert call after `evolve_ops.sync_meta_workspace` (around line 936).
  - Env escape: `EVOLVE_SKIP_PRESCRIPTION_CRITIC=1`.
  - Tests: contract-level only — schema-valid JSON return shape (`verdict ∈ {advise, no-change}`, `reasoning` non-empty). Advisory output otherwise validated by observation on 3 evolution cycles; no behavioral mocks.

- [x] **Unit 10: Autoresearch agentic replacements (R-#29, #30, #31)**
  - Modify: `autoresearch/select_parent.py` — agent picks parent from top-K eligible variants + trajectory context; rationale lands in lineage. No sigmoid fallback: agent failure = generation failure, meta-agent retries next cycle. **Runtime: AsyncOpenAI + Pydantic** (`select_parent.py` is already a Python module; AsyncOpenAI matches the closer in-process pattern and sidesteps `claude -p` shell-quoting). Create `autoresearch/agent_calls.py` housing the AsyncOpenAI helper with Pydantic schema. **Prompt must carry exploration-vs-exploitation intent forward** — not "pick the best variant" but "pick to balance exploration (novel directions, under-explored prompt modifications) against exploitation (fit, pass-rate gains); justify the balance struck." Without this, the loop risks mode collapse toward safe-looking variants. Reference cluster-4 doc for full prompt text.
  - Modify: `autoresearch/compute_metrics.py:142-176` — agent judges whether drift/uneven-generalization worth flagging from last N `generations.jsonl` rows. No threshold backstop. Runtime: Claude CLI subprocess.
  - Modify: `autoresearch/geo_verify.py:122-158` — agent produces `{per_query_verdict, aggregate_verdict, evidence_strings, regression_flags}` replacing boilerplate footer. Runtime: Claude CLI subprocess. *Output-shape compatibility:* Unit 3 reads inner-evaluation signals from `results.jsonl` via `KEEP_TOKENS`/`REWORK_TOKENS` filtered by phase — verify the new verdict shape still emits those token markers, or update Unit 3's extraction before Unit 10 lands.
  - Claude CLI subprocess pattern reference: `harness/engine.py:_build_claude_cmd`. No caching — these are infrequent calls.
  - Tests: contract-level assertions per agent (schema valid, non-empty rationale, picked parent is in top-K eligibility set, verdict in expected enum). No behavioral mocks; behavior validated on archived sessions for 3 evolution cycles.

- [x] **Unit 11: Evaluation judge replacements (R-#32, #33, #34)**
  - Modify: `src/evaluation/judges/__init__.py:71-85` — replace `fuzzy_match` token-overlap with paraphrase-checking Sonnet call. **Batching shape (required — naive per-quote calls would add ~200 LLM calls per variant evaluation across 4 domains × 8 criteria × 2 judges × ~3 quotes):** one Sonnet call per criterion per output carrying all evidence quotes together, returning per-quote verdicts. Cache keyed on `(criterion_id, sha256(output_text), sha256(quote))` so adjacent fixtures scoring the same variant dedupe. Include `PROMPT_VERSION` constant in cache key so prompt edits self-invalidate.
  - Modify: `src/evaluation/judges/__init__.py:124-130` — **replace the cap-at-3 gradient gate with a calibration judge** (R-#33 resolved: per research recommendation, not a silent drop). One Sonnet call per criterion: takes the gradient judge's score + the evidence set the judge cited; verifies the evidence actually supports the claimed score band (e.g., "claimed 5/5 but evidence only supports 3/5"); returns adjusted score + reasoning. Cost: ~one additional Sonnet call per criterion per judge (~$0.50 per variant evaluation at current Sonnet pricing). This preserves the safety net the cap-at-3 heuristic provided without the mathematical cliff (cliff dropped scores from 5 → 3; calibration judge scales smoothly).
  - Modify: `src/evaluation/service.py:77-114` + `_WORD_RANGES:30` — delete length-factor entirely. MON-8 covers monitoring proportionality; other domains have no explicit length criterion, so the R-#33 calibration judge (same unit) is the cross-domain safety net — it sees full output text during evidence verification and can flag egregious length failures. Observe monitoring/competitive/storyboard/geo for 3 cycles; if quality degrades in non-monitoring domains, add CI-9/SB-9/GEO-9 "Proportionality" criterion rather than re-introducing the Python multiplier.
  - Patterns: follow `src/evaluation/judges/gemini.py` integration style + `src/common/cost_recorder.py`.
  - Tests: contract-level only — paraphrase judge returns `{quote_id: bool}` with keys matching input quote set; calibration judge returns `{score, reasoning}` with `score ∈ [0, 5]` and non-empty reasoning; length-factor removal covered by existing judge tests.

- [x] **Unit 12: Evaluation structural gate removals (R-#35, #36, #37)**
  - Modify: `src/evaluation/structural.py` — delete the competitive-brief `<500 chars` + `<3 headers` checks (around lines 101-108); keep file-exists + `>50 chars` non-whitespace floor.
  - Modify: `src/evaluation/structural.py` — delete by-symbol (not by-line) the `synth_matches_stories` `_assert` block (both the `if story_files:` branch and the `else has_digest` branch) and the `no_excessive_rework` `_assert`. Preserve `_attempt_int` helper if other assertions still reference it; otherwise inline-delete. These were PROCESS gates, not output-quality measures — good output that took thoughtful rework is fine, and the final artifact is judged by the gradient + calibration judges. Process efficiency isn't a quality signal.
  - Modify: `src/evaluation/structural.py` — replace the regex digest-hallucination guard (around lines 276-281) with a claim-grounding Sonnet call: extracts side-effect claims from `session.md`, verifies each against outputs bundle with evidence-span requirement.
  - **Coordination with Unit 2:** in the SAME commit, remove the corresponding bullets from `STRUCTURAL_DOC_FACTS` (if present) and re-run `regen_program_docs` so the paired test and program docs stay aligned. This is the first drift event after Unit 2 lands; the paired test is designed to catch it if missed.

- [x] **Unit 13: Ad-domain agent fallback (R-#38)**
  - Modify: `src/competitive/service.py:40-53` — `_ad_domain_matches` keeps fast-path for exact hostname. On near-match, batched Sonnet call with `(brand, queried_domain, ad_copy, image, link_url)` → `YES|NO|UNSURE`. Persist decisions to a simple dict cache keyed on `(brand, queried_domain, landing_domain)` to avoid repeat calls.

- [x] **Unit 14: Monitor summarizer (R-#39)**
  - Modify: `cli/freddy/commands/monitor.py:120-170` — `_build_summary` keeps deterministic aggregates (source counts, language counts, total, fetched) as raw floor. Delegates `top_mentions`, `themes`, `source_mix` to Sonnet via Claude CLI subprocess (`harness/engine.py:_build_claude_cmd` pattern).
  - Output schema (pinned — validate with Pydantic at the CLI boundary; shape regressions fail loud):
    - `top_mentions: list[{mention_id: str, relevance_rank: int, reason: str}]`
    - `themes: list[{theme: str, representative_quotes: list[str]}]`
    - `source_mix: list[{source: str, sample: list[{mention_id: str, headline: str}]}]` where `sample` size is 1/3/5 by volume tier.
  - Prompt asks for relevance-ranked mentions + semantic themes with representative quotes + volume-adaptive source-mix.
  - Cache key: `sha256(PROMPT_VERSION + monitor_id + sorted(str(m) for m in mention_ids))` → `~/.freddy/cache/monitor_summary/<hash>.json`, 24h TTL. `PROMPT_VERSION` is a constant bumped on every prompt edit — stale entries become unreachable by construction, no manual flush.
  - On subprocess failure (timeout, non-zero exit): fall back to existing deterministic aggregates with warning. No `--summary-intent` flag (single purpose); no `--format=summary-raw` alias.
  - **Pre-land gate:** grep consumers of `monitor` CLI JSON before merging — especially `autoresearch/archive/current_runtime/programs/monitoring-session.md` and other agent prompts — for `recent_by_source` / `themes` shape parsing. Update callers or add narrow key aliases only for real consumers that exist.

- [x] **Unit 15: Producer-owned evaluation-scope YAML (R-#40)**
  - Create: `autoresearch/archive/current_runtime/programs/<domain>-evaluation-scope.yaml` — **flat layout**, one file per domain (geo, competitive, monitoring, storyboard), co-located alongside existing `<domain>-session.md` files. Matches current flat `programs/` structure; avoids cascading restructure through evolve.py clone logic and `layer1_validate`'s program-path expectation.
  - Schema: `{domain, outputs: [path, ...], source_data: [path, ...], transient: [path, ...], notes: str}`. The one `_client_baseline.json` exception handled inline in the loader (not a generalized `except:` mechanism). No `schema_version` field; no `required_count` expression language.
  - Modify: `cli/freddy/commands/evaluate.py` — delete `_DOMAIN_FILE_PATTERNS`. Add `_load_evaluation_scope(domain)` reading the YAML via `lane_runtime.resolve_runtime_dir`; fail loud on missing. Replace `_read_files` logic with glob walking.
  - Update each agent's `*-session.md` prompt — "When you emit a new artifact type, update `<domain>-evaluation-scope.yaml`."
  - One-PR cutover: no shim/fallback period. The migration is 4 small YAMLs + a loader swap.

## Phased Delivery

| Phase | Units | Effort | Blocks |
|---|---|---|---|
| 1 — Foundations | 1, 2, 3 | ~1 day (parallel) | Everything downstream |
| 2 — Inventory | 4 | ~30 min | — |
| 3 — Shared infra | 5, 6 | ~2 days (parallel) | — |
| 4 — Integrity pair | 7 | ~1 day | — |
| 5 — Audit plan edits | 8 | ~2-3 days | Audit plan implementation (separate effort) |
| 6 — Agentic replacements | 9, 10, 11, 12, 13, 14, 15 | ~7-10 days (parallel within) | — |

Total: ~14-18 engineering days across 15 units.

## System-Wide Impact

- **Shared infrastructure:** Unit 5 (`src/shared/reporting/`) and Unit 6 (`src/shared/safety/`) add a new `src/shared/` root. Existing consumers preserved via shims in `autoresearch/report_base.py`, `harness/safety.py`, `autoresearch/lane_paths.py`. **Shim policy:** each shim emits a `DeprecationWarning` on import naming the new path; removal target is 4 weeks after Phase 3 lands (tracked as follow-up issue created when Phase 3 merges). `harness/safety.py` shim is kept as a *pure* re-export by moving the harness allowlist definition into `harness/config.py` — mixed-logic shims fossilize, pure shims are cheap to delete.
- **Agent-call failures:** Units 10-14 agent calls fail the operation loudly on subprocess error (Unit 14 is the single exception: CLI user-facing, deterministic fallback with warning). No silent-fallback paths elsewhere; trust the agent or fail. **Single-point-of-failure note:** a Claude outage or rate-limit event simultaneously breaks parent-selection, evaluation, geo-verify, ad-domain matching, and claim-grounding across both harness and autoresearch. No aggregate budget or retry-sharing across units; `cost_recorder` surfaces frequency; if common in practice, investigate root cause before adding fallbacks.
- **Audit plan sequencing:** Unit 8 assumes R5 plan is current; read the plan chunk-by-chunk before each edit in case further restructuring has happened.
- **Withdrawn safeguards:** Per-cycle smoke (Unit 1), no-progress gate (Unit 1), length-factor (Unit 11), 500-char structural gate (Unit 12), rework cap (Unit 12), digest-hallucination regex (Unit 12), `_DOMAIN_FILE_PATTERNS` (Unit 15) are all removed — their coverage moves to rubrics, judges, or producer-owned config. **Cap-at-3 gradient replaced, not removed** — Unit 11's calibration judge takes over the safety-net role without the mathematical cliff.

## Risks

| Risk | Mitigation |
|---|---|
| Audit plan R5 has changed since analysis | Unit 8 re-reads the plan before each edit |
| Agent-call failures become common operational noise | Telemetry + cost_recorder surface frequency; if common, investigate root cause (Claude availability, prompt quality) before adding fallbacks |
| Structural gate removals (Unit 12) surface previously-hidden output quality issues | Expected — that's why the rubrics exist. Monitor judge scores for first 3 evolution cycles |
| `STRUCTURAL_DOC_FACTS` silently drifts from `structural.py` checks | Paired test (Unit 2) fails loud in CI on drift |
| Unit 11 calibration judge has systematic bias (judges the judge, so double-calibration could amplify rather than correct errors) | Unit 3's inner-vs-outer correlation telemetry acts as a cross-check; if the calibration judge's adjusted scores correlate poorly with inner evaluator, tune the calibration prompt before broad rollout. Deferred R-#23 rubric-anchor refactor remains the long-term fix for shape-based scoring. |
| Unit 14 changes `monitor ... --format=summary` output shape; removes `recent_by_source` key alias and `--format=summary-raw` escape hatch | Before landing Unit 14, grep consumers of `monitor` CLI JSON (especially `autoresearch/archive/current_runtime/programs/monitoring-session.md` and any other agent prompts) for `recent_by_source` / `themes` shape parsing; update callers or add aliases only for real consumers that exist |

## Sources

- **Origin:** `docs/plans/2026-04-22-006-pipeline-overengineering-implementation-research.md`
- **Per-item implementation specs:** `docs/plans/2026-04-22-006-impl-cluster-{1-harness, 2-audit-plan, 3-autoresearch, 4-pass2-ae, 5-cli-cross}.md`
- **Audit plan being patched:** `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`
- **Project memory:** `~/.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/memory/project-pipeline-overengineering-audit-2026-04-22.md`

**Precedence rule on conflict:** this plan is source of truth for sequencing, unit scope, and decisions; cluster docs are source of truth for per-item research detail (full prompts, alternatives considered, risk analysis). When the two disagree, this plan wins on "what lands and when"; cluster docs win on "how the Sonnet prompt is worded." If an implementer finds a contradiction beyond that split, surface it before proceeding.

## Decisions (resolved 2026-04-22)

Both decisions previously flagged as pending are now resolved. Preserved here for traceability.

- **R-#29 — runtime for `select_parent` agent:** **AsyncOpenAI + Pydantic** (per cluster-4 research). Rationale: `select_parent.py` is already a Python module (not a shelled agent); AsyncOpenAI + Pydantic matches the closer in-process pattern and sidesteps `claude -p` shell-quoting. R-#30 (`compute_metrics`) and R-#31 (`geo_verify`) stay as Claude CLI subprocess.
- **R-#33 — gradient evidence-gate:** **replace cap-at-3 with calibration judge** (per cluster-4 research; not dropped). One Sonnet call per criterion verifies evidence supports the claimed score band; returns adjusted score + reasoning. Smooth calibration replaces the cliff-at-3 heuristic; one cheap Sonnet call per criterion per judge keeps cost trivial.
