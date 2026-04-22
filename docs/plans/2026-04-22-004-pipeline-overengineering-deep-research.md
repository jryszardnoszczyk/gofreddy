---
title: "Pipeline over-engineering — deep-research triage"
type: research
status: active
date: 2026-04-22
related_plans:
  - 2026-04-20-002-feat-automated-audit-pipeline-plan.md
  - 2026-04-22-003-feat-harness-claude-support-and-parallelism-plan.md
prior_audit: ../../.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/memory/project-pipeline-overengineering-audit-2026-04-22.md
---

# Pipeline over-engineering — deep-research triage

Three rounds of audit identified ~25 over-engineering candidates across three pipelines (harness, audit pipeline plan, autoresearch). This document is the deep-research triage: per-finding analysis answering "should it be agentic / hybrid / deterministic? how should it work? what are the bottlenecks? would addressing this simplify a lot?" — with honest withdrawals where the audit was wrong.

## TL;DR

Of ~25 candidates, deep research yields:

- **8 KEEP** (load-bearing or correctly-sized)
- **9 SIMPLIFY** (mechanical reductions, low risk)
- **3 REDESIGN** (replace pattern, larger payoff)
- **3 DELETE** (clean removal)
- **2 STRENGTHEN** (add, don't subtract — autoresearch evaluator gap)
- **2 OBSOLETE-AS-AUDIT-ITEMS** (audit cited code that doesn't exist)

Net (estimated): ~600-800 LOC removed across pipelines + ~290 LOC of audit-plan code never written + 6-10 audit-plan bug-fix commits avoided + audit plan ships ~1 week faster.

## Honest withdrawals (audit was wrong about these)

The deep research surfaced four cases where prior audit rounds were incorrect or imprecise. Recording explicitly so we revise downstream.

### W1: `_capture_patch` (F1.3) — function does not exist
The function was deleted in the greenfield rewrite. Patch capture is now in `harness/prompts/fixer.md:55-62` — the agent runs `git diff HEAD > <path>` itself. Audit picked up the function name from old plan docs. The cited test `tests/harness/test_run.py:91-108` doesn't exist either. **Verdict: OBSOLETE as audit item.** The current shape (agent writes its own patch) is the right pattern. Optional: add a single line asserting patch file exists post-fix.

### W2: PR-body agent + 200-char floor (F2.4) — does not exist
There is no PR-body agent in the codebase. `harness/review.py:59-79` is a deterministic Python function; no 200-char floor anywhere. Audit conflated old plan with current code. **Verdict: OBSOLETE as audit item.** Current deterministic implementation is correct.

### W3: Stripe `payment_events` table (F4.3) — single-field doesn't survive reality
The audit suggested replacing the table with a `last_processed_event_id` field on state. But Stripe webhooks fire many event types per checkout (`checkout.session.completed`, `payment_intent.succeeded`, future refunds, future chargebacks). A single field can't dedupe across event types — those are legitimately distinct events. Table is also useful when prospects email "did my payment go through." **Verdict: KEEP table.** Withdrawal of the original audit-context flag.

### W4: F5.1 prescription-drift mechanism was wrong-shape
The audit said "rubric scores PROCESS so meta-agent converges on prescription." Reading `src/evaluation/rubrics.py:47-498` shows the rubrics ARE outcome-shaped on the scoring axis ("Can a reader state the central argument?"). The drift mechanism is different: each rubric's score-5 anchor *describes artifact shape* in detail (e.g., CI-1 score 5: "executive summary states a single strategic position. Every subsequent section provides evidence for, against, or nuance to that position"). Meta-agents transcribe shape descriptions forward as procedural rules. Token-count evidence: prescription tokens (`must|always|never|required`) went DOWN v001→current (19→8 for competitive), but skills-library mandates went UP (9 new Corey-Haines bullets in competitive). Drift moved from explicit-imperative to declarative-bullet form. **Verdict: SIMPLIFY remains right, but the fix is rubric-anchor refactor + program length cap + meta-agent constraint, NOT "outcome scoring."**

## Surprise discoveries

### S1: F5.2 has a LIVE DRIFT BUG — fix this independent of triage
Programs document `≥100 chars + ≥3 headers` as the structural validator (`competitive-session.md:142-144`, etc.). The actual gate at `src/evaluation/structural.py:101` requires `≥500 chars` and competitor-data parseability. Off by 5x. Comment at `structural.py:86-89` confirms team already discovered the audit's exact concern, fixed the gate, but **forgot to update the four program files**. An agent reading the program will optimize for 100 chars and score 0 catastrophically.

**Action: regenerate the program "Structural Validator Requirements" sections from `structural.py` source-of-truth.** Cheap, mechanical, urgent. Auto-generation script (~50 LOC) prevents re-drift.

### S2: F5.3 honor-system gap is explicit in code
`autoresearch/archive/current_runtime/programs/meta.md:70` literally tells the meta-agent: *"Do not modify `_build_critique_prompt` or `GRADIENT_CRITIQUE_TEMPLATE` ... the outer scorer's reward function has not been verified end-to-end against this attack vector — treat the inner critique prompt as a frozen interface, not a tunable input. **The lane infrastructure does not enforce this; the discipline is yours.**"*

This is honor-system enforcement in a system whose entire purpose is to evolve programs that maximize score — exactly the seam an evolution loop is designed to find. **Action: convert to capability restriction (SHA256 hash check at L1 validation in `evaluate_variant.py:384-411`) before any other autoresearch simplification lands.**

## The unifying insight (clearer now)

The deep research surfaced one structural fact that organizes everything:

**Over-engineering accretes around *integration points* between subsystems.**

- The audit pipeline's `rubric_themes.yaml` is the integration point between score, schema, agent split, and section split — pull it and four findings (F3.1, F3.2, F3.3, F3.4) collapse together.
- The harness's `SCOPE_ALLOWLIST` is the integration point between fixer scope, post-hoc check, leak detection, and rollback — same pattern; same opportunity if you redesign worktrees.
- The autoresearch `report_base.py` is the integration point between findings parsing and report rendering across 4+ domains.

Convergence opportunities at the cross-pipeline level follow the same logic: render_lib (pattern 6) is the integration point between three pipelines' reporting; finding_lib (patterns 1+2) between three envelope models. These are real wins.

But pipelines that solve genuinely different *questions* (quality scoring — pattern 3 is binary verifier vs. weighted health-score vs. geometric mean of LLM judges) should NOT converge. Three different math objects answer three different questions; forced convergence would damage all three.

The over-engineering pattern: **right primitives, accreted into integration ontologies that make every change cost 3-4x.** The fix is removing the ontology layer, not the primitives.

## Action plan by phase

### This week (cheap, independent, do now)

| # | Action | Pipeline | Effort | Saves |
|---|---|---|---|---|
| 1 | Regenerate program "Structural Validator Requirements" sections from `structural.py` source | autoresearch | 2 hrs | bug fix; eliminates 5x doc/code drift |
| 2 | Add SHA256 hash check on `_build_critique_prompt` + `GRADIENT_CRITIQUE_TEMPLATE` at L1 validation | autoresearch | 4 hrs | converts honor-system to capability restriction |
| 3 | Ship inner-vs-outer evaluator correlation telemetry (~30 LOC) | autoresearch | 1 day | enables every other autoresearch simplification (already on team's GAPS.md as Gap 7) |
| 4 | Drop per-cycle smoke check; keep preflight + tip; drop `smoke-cli-client-new` litter | harness | 2 hrs | ~10 LOC; eliminates filesystem litter; 2 fix commits worth of surface |
| 5 | Drop `_zero_high_conf_cycles >= 2` no-progress gate | harness | 1 hr | ~8 LOC; removes 3rd weaker termination signal |
| 6 | Tighten `_TRANSIENT_PATTERNS`; mirror `parse_rate_limit` JSON parse | harness | 2 hrs | eliminates `'"type":"error"'` false-positive class |
| 7 | Loosen `Verdict.parse` to accept `verified|pass|passed|ok` whitelist + update verifier prompt | harness | 1 hr | ~3 LOC; removes brittle envelope check |
| 8 | Auto-derive `_FIXER_REACHABLE` from `SCOPE_ALLOWLIST` | harness | 1 hr | ~5 LOC; removes sync burden |
| 9 | Promote `autoresearch/report_base.py` → `src/reporting/`; harness migrates `review.py` to use it | cross-pipeline | 1-2 days | ~290 LOC + audit plan ships ~1 week faster + visual consistency |
| 10 | Extract `graceful_kill` helper to `src/shared/process.py` | cross-pipeline | 2 hrs | ~30 LOC + makes pattern explicit |
| 11 | Name 3 safety tiers (A read-only / B sandboxed-write / C repo-write+rollback); document each pipeline's tier | cross-pipeline | 1 day | conceptual win + future read-only sub-agents have obvious pattern |

### Soon (cheap, blocked on something)

| # | Action | Blocked by | Effort | Saves |
|---|---|---|---|---|
| 12 | Replace `inventory.generate` with breadcrumb file; agents discover via Bash | none, but slightly invasive | 4 hrs | ~160 LOC (entire `inventory.py`) |
| 13 | Drop `gofreddy_health_score` deterministic rollup; let synthesis Opus produce score+rationale | audit plan U5 in design | 1 day | ~200 plan lines + calibration burden + `lens_weight_share` field becomes irrelevant |
| 14 | Delete `rubric_themes.yaml` pivot; flat `report_section` enum on Finding | audit plan U2 in design | 1 day | ~80-100 plan lines + 1 module + ~150 LOC |
| 15 | Trim Finding schema from 13 → 6 required fields | audit plan U2 in design | 4 hrs | ~30% Pydantic logic + agent-burden |
| 16 | Ship 3 of 9 R18-R26 enrichments day 1; defer the other 6 | audit plan U8 in design | 1 day plan edit | ~6 enrichment subdirs + 11 vendor adapters not built |
| 17 | Triage primitives → keep ~25 Tier-1 (paid API), drop ~30 Tier-2 (cheap web) for agent + WebFetch | audit plan U2 in design | 2-3 days plan edit | ~30 primitives × ~50 LOC + tests + registry |
| 18 | Refactor 32 rubric score-5 anchors to remove shape language | autoresearch F5.4 telemetry (#3) | 1 day | enables program length cap |
| 19 | SIMPLIFY F1.1 — drop `check_scope` peer-filter; require commits sequential under `commit_lock` | none | small | ~30 LOC across `safety.py`, `worktree.py` |

### Soon (after audit plan U2 lands)

| # | Action | Effort | Saves |
|---|---|---|---|
| 20 | Extract `finding_lib` (envelope spec + 2 parsers) to `src/findings/` | 2-3 days | ~150 LOC across pipelines + removes regex bug class |

### Medium-term (worth doing)

| # | Action | Effort | Saves |
|---|---|---|---|
| 21 | Per-track ephemeral worktrees redesign (replaces SCOPE_ALLOWLIST machinery) | 3-5 days | ~80-100 LOC + eliminates entire class of plan-2 correctness bugs |
| 22 | Cap autoresearch program length at ~80 lines (workspace + tools + format + Hard Rules + pointer to references) | 1 day | program shrinks from 165-197 LOC to ~80; per-cycle mutation surface drops ~60% |
| 23 | Replace `report_base.parse_findings` with mistune AST traversal | 4 hrs | ~70 LOC + parser robustness |

### Defer / never

- **Quality scoring convergence** — three genuinely different math objects (binary verifier vs. weighted health-score vs. geometric mean of LLM judges). Forced convergence damages all three.
- **Orchestrator framework** — three orchestrators look superficially similar but their state machines differ legitimately (track-queue draining vs. one-shot fan-out vs. generation-stepping). Worst kind of premature abstraction.
- **`finding_lib` parser unification** — share envelope spec (doc), not parser module. Three pipelines have legitimately different output requirements.

## Verdicts table

| ID | Title | Verdict | Effort | When |
|---|---|---|---|---|
| F1.1 | SCOPE_ALLOWLIST + check_scope + rollback_track_scope | SIMPLIFY (drop peer-filter logic) | small | this week (#19) |
| F1.2 | Per-track ephemeral worktrees | REDESIGN if scaling >3 tracks; KEEP otherwise | medium | next plan if expanding tracks |
| F1.3 | `_capture_patch` | OBSOLETE as audit item (W1) | none | done |
| F1.4 | HARNESS_ARTIFACTS + _FIXER_REACHABLE | SIMPLIFY (auto-derive _FIXER_REACHABLE) | trivial | this week (#8) |
| F2.1 | Per-cycle smoke check | SIMPLIFY (drop per-cycle, drop smoke-cli-client-new) | small | this week (#4) |
| F2.2 | _zero_high_conf_cycles >= 2 no-progress gate | DELETE | trivial | this week (#5) |
| F2.3 | inventory.generate pre-computation | REDESIGN (delete + breadcrumb file) | small | soon (#12) |
| F2.4 | PR-body agent + 200-char floor | OBSOLETE as audit item (W2) | none | done |
| F2.5 | Verdict.parse strict matching | SIMPLIFY (whitelist of synonyms) | trivial | this week (#7) |
| F2.6 | _TRANSIENT_PATTERNS substring matches | SIMPLIFY (proper JSON parse for stream events) | small | this week (#6) |
| F3.1 | gofreddy_health_score deterministic rollup | SIMPLIFY (Opus-led score in synthesis) | small | with audit plan U5 (#13) |
| F3.2 | rubric_themes.yaml pivot | DELETE | small | with audit plan U2/U4 (#14) |
| F3.3 | Finding schema with 13 required fields | SIMPLIFY (6 required + 7 optional) | trivial | with audit plan U2 (#15) |
| F3.4 | 9-section decoupling | KEEP concept; DELETE pivot expression | trivial | with F3.2 (#14) |
| F4.1 | ~83 primitives split | REDESIGN (keep ~25 Tier-1, drop ~30 Tier-2) | medium | with audit plan U2 (#17) |
| F4.2 | 9 conditional enrichments R18-R26 | SIMPLIFY (ship 3 day-1, defer 6) | small plan edit | with audit plan U8 (#16) |
| F4.3 | Stripe payment_events table | KEEP AS-IS (W3 withdrawal) | none | done |
| F5.1 | Universal prescription pattern | SIMPLIFY (rubric anchor refactor + program length cap + meta-agent constraint) | medium | after F5.4 (#18, #22) |
| F5.2 | Structural validator content checks | SIMPLIFY + fix live drift bug (S1) | small | this week (#1) |
| F5.3 | Two-evaluator architecture | STRENGTHEN (hash check at L1; per-criterion gating; sealed inner-critique) | medium | this week (#2) |
| F5.4 | Inner-vs-outer evaluator correlation telemetry | STRENGTHEN (ship now; ~30 LOC) | small | this week (#3) |
| F5.5 | report_base.py | SIMPLIFY within autoresearch; don't consolidate prematurely | small | medium-term (#23) |
| F6.1 | Three-implementations matrix | 2 GO / 1 helper / 2 STRATIFY / 1 KEEP DIVERGENT | varied | see phasing |
| F6.2 | Permissions/safety model | STRATIFY EXPLICITLY (3 tiers, share primitives, don't unify) | 1 day | this week (#11) |
| F6.3 | Convergence path | render_lib + graceful_kill + safety stratification this week; finding_lib in 4 weeks | varied | per plan |

## Order of operations: dependencies

Some findings unblock others. The right sequence:

1. **F5.4 (telemetry) → F5.3 (hardening) → F5.1 / F5.2 (program work)** — measurement first, then enforcement, then prescription cleanup. Without telemetry you can't safely simplify autoresearch programs because you can't see drift.
2. **F3.2 (delete pivot) → F3.1 / F3.3 / F3.4 (collapse with it)** — the pivot is the integration point; drop it first and the others fall out for free.
3. **render_lib (#9) → audit plan U7** — extract before audit plan ships its own deliverable rendering. Saves rebuilding.
4. **finding_lib (#20) ← audit plan U2** — wait for audit plan to set the schema, then back-port harness + autoresearch.

## Open questions for JR

1. **Per-track ephemeral worktrees (F1.2)** — REDESIGN if you're scaling >3 tracks, KEEP otherwise. Are you planning a 4th track? Different language/agent backend per track? If yes, REDESIGN now is cheaper than later (~80-100 LOC saved + entire class of plan-2 correctness bugs eliminated).

2. **Health score (F3.1) and rubric pivot (F3.2)** — biggest single simplification in the audit plan, but they touch the customer-facing deliverable. Comfortable letting Opus produce the headline score with rationale instead of a deterministic rollup? The Hero TL;DR template can keep the same shape; just changes the source of `health_score.overall`.

3. **9 enrichments (F4.2)** — recommend shipping 3 day-1. My pick: GSC (highest adoption, free) + budget (CSV + lookup, low risk) + assets (PDF + Opus pass, 20-40% expected). Defer the 6 highest-friction ones, especially R23 attach-demo (9 safety mitigations for 15-30% adoption). Agree?

4. **Quality scoring convergence (F6.1 row 3)** — recommendation is KEEP DIVERGENT (binary verifier / weighted health-score / geometric mean LLM judges). Confirm comfortable with three implementations of "agent output → number" because they answer three different questions?

5. **Cross-pipeline render_lib timing (#9)** — recommend doing this week so audit plan U7 adopts natively. ~290 LOC saved + audit plan ships ~1 week faster. Confirm priority?

6. **Autoresearch hardening sequencing (#1, #2, #3)** — telemetry first, hash check second, drift-bug doc-regen third. The hash check requires the telemetry to validate. Comfortable with this order, or do you want to ship the doc-regen drift-bug fix immediately as a hotfix since it's a live correctness issue?

## Pointers to deep analyses

Detailed per-finding analysis (today / why / what's wrong / right model / redesign / complexity removed / new risks / verdict) lives in companion docs:

- [Cluster 1+2: Harness scope/safety/gating](2026-04-22-004-research-cluster-1-2-harness.md)
- [Cluster 3+4: Audit pipeline rubric/primitives/enrichments](2026-04-22-004-research-cluster-3-4-audit-plan.md)
- [Cluster 5: Autoresearch programs](2026-04-22-004-research-cluster-5-autoresearch.md)
- [Cluster 6: Cross-pipeline convergence](2026-04-22-004-research-cluster-6-convergence.md)

## Sources

- Prior 3-round audit: `~/.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/memory/project-pipeline-overengineering-audit-2026-04-22.md`
- 4 parallel deep-research subagent runs, 2026-04-22, each producing structured per-finding analysis (today/why/wrong/right/redesign/complexity/risks/verdict). Total: ~24K words of analysis across 4 cluster files.
- Cross-references against:
  - `src/evaluation/rubrics.py` (revealed F5.1 mechanism mis-diagnosis)
  - `src/evaluation/structural.py` (revealed F5.2 live drift bug)
  - `autoresearch/archive/current_runtime/programs/meta.md` (revealed F5.3 explicit honor-system gap)
  - Git log of last 25 commits (provided empirical evidence for harness over-engineering pain)
