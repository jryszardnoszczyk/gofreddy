---
title: Autoresearch second-pass — F-A.1..5 (parent selection, alerts, geo verify, frontier ties, regression classifier)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-005-pipeline-overengineering-second-pass.md
---

# Autoresearch Deep Audit — Agentification Candidates

## Executive summary

**Files audited (9):** `select_parent.py`, `frontier.py`, `compute_metrics.py`, `archive_index.py`, `evolve_ops.py`, `lane_runtime.py`, `lane_paths.py`, `geo_verify.py`, `archive_cli.py`.

**Correctly deterministic (no agentification candidates):**
- `lane_runtime.py` — manifest I/O, filesystem sync with protected-dir exclusions. Mechanical.
- `lane_paths.py` — hardcoded path-prefix ownership table. Deterministic is correct; agent judgment here would be destabilizing (ownership must be auditable).
- `archive_index.py` (most of it) — diffstat, file maps, workspace sanitization. Filesystem plumbing. One small exception flagged below.
- `evolve_ops.py` — thin RPC shims wrapping deterministic lineage reads/writes. No judgment happening here.
- `archive_cli.py` — read-only reporting over already-computed metrics. Correctly deterministic. The one decision it makes (top-k ordering, regression ranking) is pure math over already-scored data.

**Active agentification candidates found:** 5 (3 HIGH, 1 MEDIUM, 1 LOW).

**Pattern across files:** the genuinely suspicious code is concentrated in two places — the **selection/alert math layer** (`select_parent.py`, `compute_metrics.py`, `frontier.py::objective_score`) and the **verification reporter** (`geo_verify.py`). The plumbing files (`archive_index.py`, `lane_runtime.py`, `lane_paths.py`, `evolve_ops.py`, `archive_cli.py`) are doing correctly-deterministic work and shouldn't be touched.

Key meta-observation: the parent-selector, alert thresholds, and objective-score formula all share a single philosophical flaw — they reduce a multi-dimensional evolutionary signal (score, novelty, generalization, lane context, recent history) to a single scalar or threshold, then branch on it. That scalarization is exactly the place where a small amount of agent judgment buys a lot of quality. This is not an accident — it's the same gofreddy_health_score anti-pattern the master triage already flagged, just one abstraction layer down.

---

## Findings

### [F-A.1] — Parent selection uses hand-tuned sigmoid × novelty formula where an agent could reason about the evolution trajectory

- **File:line:** `autoresearch/select_parent.py:20-35, 42-75`
- **Today:** `select_parent` ranks eligible variants with `sigmoid(λ·(score−midpoint)) × exp(−(children/8)^3)`, where midpoint is the mean of the top-3 scores. Magic constants `SIGMOID_LAMBDA = 10.0`, `TOP_K_MIDPOINT = 3`, novelty divisor `8.0`, and cubic exponent are hardcoded. Then `random.choices` samples with those weights.
- **Why it's qualitative:** "Which parent should we evolve from next?" is the single most load-bearing decision in the whole evolution loop — it determines what the proposer sees. The sigmoid-novelty formula encodes a fixed exploit/explore tradeoff that ignores: (a) whether recent generations have been improving or plateauing, (b) whether a high-score variant has already been beaten on holdout, (c) whether the lane has stalled on a specific sub-domain, (d) the *shape* of the parent's failure modes visible in `scores.json`. The formula treats "score 0.82, 6 children" identically regardless of whether those 6 children all regressed or all improved.
- **Agentic redesign:** Pass the agent a structured summary of eligible variants — top-K by score with their `inner_metrics`, fixture_sd, children count, children's score deltas, and the last 3 generations' trajectory — and ask "which parent gives us the highest expected improvement this generation, and why?" Keep the current formula as a fallback when the agent times out or for cheap-mode runs.
- **Why agent wins:** Concrete advantages: (1) Can notice "parent X has 6 children all with composite 0.74±0.01 — we're stuck on a plateau, pick a lower-score but more-diverse parent" — the current formula just lowers novelty weight linearly. (2) Can read `max_fixture_sd` and deprioritize parents whose children overfit specific fixtures, which composite-score can't see. (3) Can prefer parents whose *failure modes differ* from the current frontier, rather than just novelty-by-birth-count. (4) A natural-language rationale lands in the lineage, making selection auditable — right now you can't answer "why this parent?" except by reproducing the RNG.
- **New risks:** Non-deterministic selection makes reproducibility harder (mitigation: log agent reasoning + seed to lineage). Agent latency per generation (~5-10s, negligible next to an evolution tick). Agent could collapse to always picking the top-score variant — mitigate with a prompt explicitly penalizing exploitation when children are converging.
- **Priority:** HIGH

### [F-A.2] — Alert thresholds in `compute_metrics.py` are fixed numbers that an agent should reason about in context

- **File:line:** `autoresearch/compute_metrics.py:29-31, 142-176`
- **Today:** Three magic constants: `INNER_OUTER_DRIFT_THRESHOLD = 0.35`, `UNEVEN_GENERALIZATION_FIXTURE_SD = 0.30`, `UNEVEN_GENERALIZATION_COMPOSITE = 0.6`. `check_alerts` fires `inner_outer_drift` when two consecutive gens have corr < 0.35, and fires `uneven_generalization` per-variant when `max_fixture_sd > 0.30 AND composite > 0.6`.
- **Why it's qualitative:** "Is this a real drift or normal gen-to-gen noise?" depends on the absolute values, trajectory, lane maturity, and fixture count. A correlation of 0.30 in a lane that's been at 0.90 for 10 gens is a real alarm; the same number in a brand-new lane with 3 data points is noise. `0.30 fixture_sd at 0.6 composite` is uneven generalization; `0.32 at 0.95` might just be that the top fixture is saturated. Fixed thresholds will either over-fire (alarm fatigue) or under-fire (silent drift) — they can't be both calibrated.
- **Agentic redesign:** After each generation, hand an agent the last N `generations.jsonl` rows plus the current row and ask "are we seeing drift, overfitting, or collapse worth flagging?" Let it return either a structured alert (`code`, `severity`, `explanation`) or `null`. Thresholds become prompt guidance, not hardcoded branches. For latency, only run this every generation (once), not per variant.
- **Why agent wins:** (1) Can distinguish "corr dropped 0.85 → 0.40 because we introduced a new fixture" (benign) from "corr dropped 0.85 → 0.40 with no other changes" (real drift). (2) Can write the `detail` string in English — currently it's `f"inner_outer_corr={corr} (prior={prior_corr})"` which requires a human to interpret. (3) Can catch alert patterns the hardcoded rules don't encode at all: "composite is rising but only because one fixture is saturating — the other three are flat." (4) Threshold calibration is a known failure mode of rule-based monitoring — this is a textbook agentic-supervision use case.
- **New risks:** False-negative drift if agent is too conservative — mitigate by keeping the threshold rules as a cheap backstop that always fires alongside the agent. Cost: one LLM call per generation completion, trivial.
- **Priority:** HIGH

### [F-A.3] — `geo_verify.py` reports raw JSON blobs with no judgment about whether verification passed

- **File:line:** `autoresearch/geo_verify.py:122-158, 150-154`
- **Today:** After re-running visibility queries on a completed session, the script dumps each query's raw JSON response into a markdown report and appends the boilerplate: *"Verification complete. Compare results above with baseline in competitors/visibility.json."* No comparison, no verdict, no diff — the human has to manually compare dozens of JSON blobs to a baseline file.
- **Why it's qualitative:** The whole point of post-implementation verification is to answer "did our GEO changes actually improve visibility?" That requires comparing the re-run results to a baseline, identifying which queries improved/regressed/held, weighting them by strategic importance (brand queries matter more than long-tail), and summarizing. This is qualitative synthesis over structured data — classic agent territory. The current script is doing ~20% of the job (collect the data) and punting the other 80% to a human.
- **Agentic redesign:** After `run_visibility_checks` collects the results, load `competitors/visibility.json` as baseline, pass both plus the session's `results.jsonl` (so the agent knows *what was changed*) to an agent with the prompt "write a verification verdict: PASS / PARTIAL / FAIL with evidence per query category, and flag any regression." Write that verdict into the report instead of the boilerplate summary.
- **Why agent wins:** (1) Eliminates a manual comparison step that's almost certainly being skipped in practice (verification reports that demand 30min of human diffing tend to be read as "done" and closed). (2) Can weight improvements by query intent — top-of-funnel brand queries vs bottom-of-funnel long-tail. (3) Can catch "improved on 8 queries, regressed on 2 critical ones" which a per-query dump obscures. (4) The verdict becomes grep-able for downstream automation (dashboards, alerts).
- **New risks:** Agent could hallucinate a PASS verdict — mitigate with structured output (JSON schema: `per_query_verdict`, `aggregate_verdict`, `evidence_strings`) and keep the raw JSON appended below for human spot-check. Baseline might be stale, in which case the verdict is meaningful regression detection regardless.
- **Priority:** HIGH

### [F-A.4] — `frontier.py::objective_score` hardcodes "core = composite, workflow = domain" dispatch

- **File:line:** `autoresearch/frontier.py:76-86`
- **Today:** `objective_score` is a two-line dispatch: if lane is `"core"`, return `composite_score`; otherwise return `domain_score(entry, lane)`. This scalar drives `best_variant_in_lane` → frontier finalization → promotion candidates.
- **Why it's qualitative:** The *dispatch itself* is fine — that's just config. The issue is that "how do we rank variants within a lane?" collapses to a single scalar (`composite` or `domain_score`). A variant that scores 0.82 composite but has terrible fixture_sd generalization is ranked strictly above a variant at 0.80 with even performance — even though on holdout the second one usually wins. The Phase 2 comment acknowledges this was a deliberate simplification from a 3-objective Pareto, but the simplification throws away fixture_sd, inner/outer correlation, and wall_time.
- **Agentic redesign:** Keep `objective_score` as the cheap primary ordering, but when `best_variant_in_lane` has ≥2 candidates within ε (say, 0.02) of the top, escalate to an agent: "these variants are numerically tied — pick the best one considering fixture_sd, inner/outer correlation, diff size, and likely holdout performance." Only pay the agent cost on actual ties (which is where the signal matters).
- **Why agent wins:** (1) Captures the 3-objective intuition without rebuilding Pareto machinery. (2) The tie-break is the place where the information *matters most* and where the single-scalar definitely loses. (3) Very cheap — agent call only when top variants are close. (4) Provides natural-language "chose X over Y because Z" that lands in frontier.json alongside the numbers.
- **New risks:** Non-deterministic ranking in the tie zone — acceptable because by definition the variants are numerically close. Mitigate with logged rationale. Could be confusing if different reviewers see different "best" — solve by caching the decision in frontier.json.
- **Priority:** MEDIUM — real tradeoff; the current scalar is legitimate, the ask is "don't be blind in ties."

### [F-A.5] — `cmd_regressions` in archive_cli mechanically ranks worst-domain-delta, loses the "is this a real regression" signal

- **File:line:** `autoresearch/archive_cli.py:96-126`
- **Today:** For each parent-child pair, computes per-domain delta, picks `min(delta)` as `worst_domain`, sorts globally by `worst_delta`. So if a child loses 0.05 on geo but gains 0.10 on competitive, it's ranked as a -0.05 geo regression — the compensating gain is invisible.
- **Why it's qualitative:** "What are our worst regressions?" is the kind of question a human asks when they want to know *what to fix*. The current output buries real regressions (net-negative, trend-confirming) under noise regressions (single-domain dip that was the tradeoff for a bigger gain). A human scanning the top-10 gets a high-noise list. An agent could look at the same delta dict and say "this is a real regression: child is net -0.08 and the loss is in the primary lane" vs "this is a tradeoff: child net +0.05, just dipped on one fixture."
- **Agentic redesign:** Keep the deterministic computation as-is (it's fast, correct, and gives the agent raw material). After sorting, pass the top-20 candidates through an agent: "classify each as real_regression / tradeoff / noise, and return the top-N real_regressions for display." Default CLI output shows classified list; `--raw` flag preserves current behavior.
- **Why agent wins:** (1) The CLI output becomes actionable instead of requiring human triage. (2) "Tradeoff vs regression" is exactly the kind of categorical judgment humans make in seconds and code struggles with. (3) Lineage / audit trail captures *why* each was classified — helpful when you come back in 2 weeks asking "why didn't we fix this?"
- **New risks:** Lowest-impact of the findings — this is a CLI reporting tool, not a decision point. Agent cost is a once-per-invocation call. Low priority because the CLI is used infrequently by humans who can re-interpret the raw output.
- **Priority:** LOW

---

## Non-findings — why the other code is correctly deterministic

**`archive_index.py`** — The `_is_ignored`, `_variant_file_map`, `_diffstat_for_pair`, `sync_variant_workspace`, `prepare_meta_workspace` functions are pure filesystem plumbing. They answer "which files changed" and "copy these files here while excluding those." Any agentification here would be cosplay — deterministic is the right tool. `public_entry_summary` and `refresh_archive_outputs` are aggregators over already-computed scores; they don't make judgments.

**`lane_runtime.py`** — Pure manifest CRUD plus protected-dir-aware filesystem sync. `_sync_filtered` is mechanical. `initialize_current_heads` is bootstrap logic. No qualitative decisions.

**`lane_paths.py`** — Hardcoded `_WORKFLOW_PREFIXES` table plus prefix matching. This is *deliberately* deterministic: lane ownership is a security/auditability invariant. Any agent judgment here would be a footgun — it could shift ownership based on fuzzy reasoning and the proposer would edit the wrong lane. Correctly rigid.

**`evolve_ops.py`** — 90% of functions are Python RPC shims (`ensure_lane_heads`, `current_head_variant_id`, `set_current_head`, `baseline_seeded`, `holdout_configured`, `mark_promoted`, `previous_promoted_variant`, `variant_in_lineage`). They read or write lineage entries and compare them to known-good values. Zero qualitative judgment — these are correctly deterministic. `finalize_candidate_ids` delegates to `best_variant_in_lane` which inherits F-A.4's limitation, not a separate finding.

**`archive_cli.py::cmd_frontier / cmd_topk / cmd_show / cmd_diff / cmd_traces / cmd_failures`** — Read-only reports. `cmd_diff` shells out to `git diff --stat`, which is the right tool. Only `cmd_regressions` has a minor agentic improvement opportunity (F-A.5).

---

## Priority summary

| Finding | File | Priority |
|---------|------|----------|
| F-A.1 | select_parent.py — sigmoid×novelty → agent-ranked parent selection | HIGH |
| F-A.2 | compute_metrics.py — fixed alert thresholds → agent-judged alerts | HIGH |
| F-A.3 | geo_verify.py — raw JSON dump → agent verification verdict | HIGH |
| F-A.4 | frontier.py — scalar ranking → agent tie-break | MEDIUM |
| F-A.5 | archive_cli.py — worst-delta sort → agent regression classifier | LOW |

**The consistent pattern:** each HIGH finding is a place where the codebase currently reduces a nuanced evaluative question ("which parent", "is this alarming", "did verification pass") to a fixed scalar or threshold. These are exactly the fixed-formula anti-patterns the master triage flagged at the pipeline level — F-A.1 through F-A.3 are the evolution-loop versions of the same mistake.

**If you only act on one:** F-A.3 (geo_verify). It's the lowest-risk, highest-user-visible change — the script is currently producing reports that a human has to manually compare to a baseline, which means in practice those reports are being read as rubber stamps. Adding an agent verdict converts a theater-of-verification into real verification for a single LLM call per session.
