---
title: "Pipeline over-engineering — implementation research master"
type: research
status: active
date: 2026-04-22
parents:
  - 2026-04-22-004-pipeline-overengineering-deep-research.md
  - 2026-04-22-005-pipeline-overengineering-second-pass.md
---

# Pipeline over-engineering — implementation research master

After 3 rounds of audit + 2 rounds of deep research produced 38 confident recommendations, JR asked: "figure out the optimal solutions and implementations for all of them before we write a plan." Five parallel research agents produced per-item implementation specs (approach options, chosen design, code sketches, edge cases, test strategy, effort estimates).

This document is the master synthesis. Per-item detail lives in the 5 cluster docs.

## Headline findings from the implementation research

### 2 honest withdrawals from the 38

Deep implementation work surfaced two recommendations that should NOT proceed as stated:

**W5: #19 (drop check_scope peer-filter) is UNSAFE as stated.**
The cluster 1+2 agent independently re-verified what the original F1.1 cluster doc already argued: the peer-filter is load-bearing under parallel execution. **Fixers** (not just commits) run concurrently across tracks. When track A's `check_scope` fires, track B's fixer may have uncommitted edits in the working tree; without the peer-filter, track A flags those as its own scope violations (false positive → A's fix rolls back). This is the exact bug the filter was introduced to fix. Revised verdict: **keep the filter; strengthen the comment at `safety.py:53-57`** explaining why it's load-bearing. Removing peer-filter requires per-track worktrees (F1.2), which is a separate larger change.

**W6: #17 (extract `graceful_kill` helper) is low leverage.**
Two ~18-LOC duplicated process-termination blocks across harness and autoresearch. 90-min refactor for ~18 LOC deduplication with no functional gain. Audit's proposed `src/shared/process.py` path is also incorrect — `src/` is product code; infra utility there muddies layering. Revised verdict: **defer** unless either file is touched for another reason; then do it as an incidental refactor (correct path: `harness/_process.py` with autoresearch importing).

### 4 of 5 audit-plan items already applied in R5

Per memory: audit plan was restructured to R5 today ("cache-backed SDK tools + prompt-mentions, no primitive_registry, no rubric_themes pivot"). Agent 2 verified against the current 1529-line plan:

- **#7 (Opus health score):** already applied at plan lines 583-592, 1118-1123, 1238. Residual gaps: `HealthScore` Pydantic model not yet drafted; `health_score.md` prompt body not drafted; 1-10 vs 0-100 scale drift needs a single call-out; rationale word cap not specified.
- **#8 (flat `report_section` enum):** already applied at plan lines 117-118, 466, 480, 485, 515, 585. Residual gaps: 7 per-agent rubric-checklist blocks not drafted; migration note for pre-R5 branches missing.
- **#9 (Finding schema trim to 6):** already applied at plan lines 485, 515. Residual gaps: Pydantic constraints (`min_length=1` on evidence_urls, `min_length=50` on recommendation) not shown; Jinja2 conditionals not explicit in template spec; per-section sort rule not specified.
- **#11 (cut Tier-2 wrappers):** applied MORE aggressively than my recommendation — R5 moved ~68 Tier-2 checks to agent prompt-mentions via WebFetch, not just deleted from `primitives.py`. Residual gaps: Tier-1 allowlist scattered across inventory table + U2.5 needs consolidation into one concrete block.
- **#22 (critique pass on recommendation):** partially applied. Per-agent evaluator-optimizer loop wired at Stage 2 (1-3 iterations, shared `critique.md` + `revision.md` prompts). Gaps: critique prompt's tactical-vs-strategic criteria + worked examples not drafted; cross-agent Stage-3 sweep NOT wired — recommend adding one Opus call for cross-boundary tactical-leakage detection.

**Cost correction on #22:** critique pass is ~14 Sonnet calls (7 agents × 2 iterations avg), not 36-72 Opus. Cost is ~$0.50 per audit, not $3-5. The per-finding estimate I gave earlier was wrong because the critique runs per-agent-iteration, not per-finding.

### Updated total after withdrawals

**38 → 36 active recommendations** (reject #19, defer #17).
**Implementation effort estimate:** ~40-60 engineering hours total across all 36 items. Biggest chunks: #21 test-pass-count delta (3-4h with careful rollout), #15 Pareto-constraint critique agent (1-1.5 days), #18 name safety tiers (1 day), #16 promote report_base.py (1 day), #39 summarizer agent (2 days).

## Optimal implementation patterns (themes across the research)

Three patterns recurred across agents:

### Pattern 1: "Option B beats Option A almost always"
For most items, the obvious first-cut implementation (Option A) had a flaw the research caught:
- **#13 hash check:** byte-hashing the variant's local file (A) is brittle; runtime introspection in isolated subprocess (B) catches shadows/monkeypatches.
- **#25 mistune AST:** line-by-line regex state machine (A) is today's code; mistune AST walk (B) is robust to whitespace.
- **#14 correlation telemetry:** strict schema for inner decisions (A) is brittle; fuzzy signal extraction from existing logs (B) works today.
- **#12 auto-regen structural doc:** AST parsing `structural.py` (A) is 100+ LOC of brittle walker; hand-maintained dict with a test that tracks code (B) is ~30+60 LOC and fails loud in CI.

**Lesson:** the cheap-first-cut mental model ("just do the simple thing") often picks the wrong primitive. The right implementation is usually one abstraction level higher than where you'd start.

### Pattern 2: Cache aggressively, cost matters
Every LLM-call recommendation came back with a caching-design requirement:
- **#39 summarizer:** `sha256(monitor_id + mention_set_hash + intent + schema_version)` → `~/.freddy/cache/monitor_summary/`. Neutralizes cost + latency on repeat calls.
- **#34 length-factor:** cache by input metadata hash (N competitors, K data-rich, client stage).
- **#22 critique:** cache keyed on (finding content, rubric-version hash). Critique is idempotent.
- **#38 ad-domain agent:** only call when near-match rate is high; persist decisions as training data.

**Lesson:** LLM calls in the inner loop need a cache key design at the same time as the prompt design. Research agents flagged this consistently without being asked.

### Pattern 3: Subprocess isolation for security boundaries
Two items (#13 hash check, #24 subprocess isolation) need tight coupling — both agents flagged this independently. #13 freezes the protected function bytes; #24 freezes the invocation environment. Shipping them separately leaves gaps; shipping together = belt + suspenders. Extend the same pattern to `freddy evaluate variant` if outer scorer gameability becomes a concern.

## Dependency graph (implementation order)

Based on per-item dependencies across all 5 research docs:

**Foundations (no deps, do first):**
- #12 auto-regen structural docs → enables honest inner-critique signal for #14
- #6 auto-derive _FIXER_REACHABLE
- #2 delete no-progress gate
- #25 mistune AST parser

**Measurement enablement (unblocks later work):**
- #14 correlation telemetry → unblocks #15 (can't safely simplify programs without drift visibility)

**Harness cleanups (parallel, independent):**
- #1 drop per-cycle smoke + litter
- #3 inventory breadcrumb
- #4 Verdict synonyms
- #5 tighten transient patterns
- #21 test-pass-count delta (needs flagged rollout)

**Cross-pipeline extractions (parallel):**
- #16 promote report_base.py → src/reporting/
- #18 name 3 safety tiers

**Security hardening (coupled pair, ship together):**
- #13 SHA256 hash check + #24 subprocess isolation

**Agentic replacements — autoresearch (after #14 telemetry running):**
- #15 Pareto-constraint critique agent (shadow mode for 3-5 cycles)
- #29 parent selection agent (keep formula as fallback)
- #30 alert thresholds agent (keep threshold rules as backstop)
- #31 geo_verify agent verdict

**Agentic replacements — evaluation (after F5.2 drift fix #12 landed):**
- #32 fuzzy_match → paraphrase agent
- #33 gradient evidence-gate → calibration judge
- #34 length-factor → agent or drop
- #35 drop 500-char/3-header gate
- #36 drop no_excessive_rework + synth ratio gates
- #37 digest-hallucination → claim-grounding agent
- #38 ad-domain agent fallback

**Agentic replacements — CLI:**
- #39 monitor summarizer agent (needs Anthropic SDK dep — JR decision)
- #40 evaluate.py YAML (classifier-agent Option B rejected as wrong tool)

**Audit plan residual gaps (plan edits only):**
- #7 draft HealthScore Pydantic + prompt body
- #8 draft 7 per-agent rubric-checklist blocks
- #9 add Pydantic constraints + Jinja2 conditionals
- #11 consolidate Tier-1 allowlist block
- #22 draft tactical-vs-strategic critique prompt + Stage-3 cross-agent sweep

**Withdrawn / deferred:**
- #17 graceful_kill extract: defer (low leverage)
- #19 drop peer-filter: reject (unsafe — load-bearing)
- #20 per-track worktrees: not decided yet (conditional on scaling)
- #23 rubric anchor refactor: deferred pending #14 telemetry evidence

**Documented non-actions (no implementation):**
- #10 ship 3 of 9 enrichments (product scope — plan edit)
- #26 plan finding_lib extraction for 3-4 weeks out
- #27 don't unify quality scorers (doc)
- #28 don't build orchestrator framework (doc)

## Open questions — RESOLVED (2026-04-22, JR decisions)

Per JR's "no caps, no limits — free-flowing agents produce best results" philosophy:

1. **#21 test-pass-count delta: WITHDRAWN.** It's a hard gate that rolls back on test-count decrease. The stated purpose (catch deletion-as-fix) is already covered by the verifier's adjacent-capability checks + the fixer prompt's no-tests-mod rule. Would cause false-positive rollbacks on legitimate test consolidation. New total: **35 active recommendations.**
2. **#22 Stage-3 cross-agent sweep: Sonnet** (not Opus). 4-criterion rubric is well-worded; Sonnet handles this tier. Escalate individual criteria to Opus only if observed misses.
3. **#39 SDK: Claude Code CLI subprocess** — same `claude -p ... --model sonnet --dangerously-skip-permissions` pattern as rest of autoresearch. No new SDK dep. Saves ~2h effort on #39.
4. **#13 hash scope:** include `HARD_FAIL_THRESHOLD`, `DEFAULT_PASS_THRESHOLD`, `compute_decision_threshold` — same bias-failures-low attack surface; trivial to add.
5. **#16 + #18 paths:** `src/shared/` umbrella for both → `src/shared/reporting/` + `src/shared/safety/`. Signals "infrastructure, not product code"; centralizes cross-pipeline infra.
6. **#15 Pareto constraint:** **soft-review ONLY, never hard-reject.** Critique flags prescription deltas; logs to `eval_digest.md` for next cycle's meta-agent + human review. No programmatic veto. Diff-only to start; escalate to parent-aware only if smuggling observed.
7. **#7 health score scale:** 0-100 throughout (matches Ahrefs / SEMrush / Moz industry pattern). Thread through Pydantic + prompt + template + print CSS uniformly. Fix any 1-10 references in R5 plan as part of closing #7's residual gaps.
8. **#19 peer-filter:** accept as load-bearing, **defer F1.2 per-track worktrees.** Current peer-filter works + has tests. F1.2 is 3-5 day refactor with unrelated complexity (per-track backends, cherry-pick consolidation, 3× disk). Revisit only if scaling >3 tracks / peer-filter bugs return / backend contention blocks throughput.

## Updated recommendation count

- **Pass 1:** 26 confident
- **Pass 2:** 12 HIGH promoted
- **Implementation research withdrawals:** −2 (W5 #19 keep peer-filter, W6 #17 defer graceful_kill)
- **JR philosophy withdrawal:** −1 (#21 test-pass-count delta is a cap)
- **Final total: 35 active recommendations**

## Surprises (things the research found that I didn't expect)

- **Audit plan R5 already did most of the work** I thought needed doing. The research confirms that opening issues like #7/#8/#9/#11 are now 4-8 hour plan-edit tasks, not multi-day plan rewrites. #10 is done (3-of-9 ship decision). The R5 restructure was more comprehensive than the memory note suggested.
- **#11 applied more aggressively than recommended.** R5 moved ~68 Tier-2 checks to agent prompt-mentions, not just the ~30 I suggested. No rollback needed; just document the Tier-1 allowlist more concretely.
- **#22 cost was wildly overestimated.** My earlier ~$3-5 per audit figure assumed per-finding Opus calls; actual design is per-agent-iteration Sonnet calls, ~$0.50 per audit. One-tenth the cost.
- **Agent 4 (pass 2 evaluation) found the F5.2 drift bug is worse than stated.** The 500-char-vs-100-char discrepancy surfaced as F5.2, but the full pattern is: `structural.py` has 14 content-shape gates, not just one. Agent recommends dropping or moving to rubrics en masse.
- **#40 classifier-agent option is honestly wrong.** Producer-owned YAML beats a classifier agent unambiguously. The research framework made me default to "agent wins" for qualitative work, but this item encodes declarative producer facts, not qualitative judgment. YAML is the right tool.

## Pointers to per-item detail

- [Cluster 1: harness (9 items)](2026-04-22-006-impl-cluster-1-harness.md)
- [Cluster 2: audit plan (5 items — mostly already in R5)](2026-04-22-006-impl-cluster-2-audit-plan.md)
- [Cluster 3: autoresearch pass 1 (6 items)](2026-04-22-006-impl-cluster-3-autoresearch.md)
- [Cluster 4: pass 2 autoresearch + evaluation (10 items)](2026-04-22-006-impl-cluster-4-pass2-ae.md)
- [Cluster 5: CLI + cross-pipeline (4 items)](2026-04-22-006-impl-cluster-5-cli-cross.md)

## What's next

Research phase is done. The implementation research covers 34 active items (36 minus the 2 non-implementation product/doc items) with per-item specs. Ready to write a sequenced implementation plan — the dependency graph above gives the right sequencing skeleton.

Before writing the plan, recommend JR resolve the 8 open questions above. Most are minor (naming, model choice) but a few (#21 budget, #39 SDK choice, #7 scale) affect downstream design.
