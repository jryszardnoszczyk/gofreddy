# External Absorptions Plan (Stream C) — LEAN

**Date:** 2026-05-11
**Author:** Jan + Claude (after three-agent research thread + Stream A shipping evidence + completeness audit + JR's "no deferrals" pressure-test)
**Status:** Sequential after Stream B v2 lands (per JR's 2026-05-11 decision: A → B → C). Awaiting v2 substrate completion (Stream B U10 + U13).
**Scope:** 5 units, ~620 LOC, ~2-3 weeks. **All units target v2 architecture (`autoresearch_v2/tools/`), not v1 (`autoresearch/evolve.py`).**
**Companion plans:**
- `2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md` (Stream B — v2 substrate simplification)
- `2026-05-11-002-eval-pipeline-bug-fixes-plan.md` (Stream A — eval pipeline bug fixes)

## 1. Goal

Absorb only the external improvements that address concrete observed problems in gofreddy autoresearch or represent mathematically correct upgrades. Reject all speculative defense-in-depth and panel-of-N infrastructure. Vendor patterns and code snippets with explicit license compliance; keep gofreddy's `judges/server.py` and `autoresearch/evolve.py` as the substrate.

## 2. Non-goals

- Panel-of-3 frontier judges (Stream A evidence: judge noise wasn't the bottleneck; variant output failures were)
- Bandit-based judge ensemble selection (no panel → no bandit)
- Bias regression test suite (no observed bias incidents to motivate the 400 LOC + 200 hand-crafted pairs)
- Preference leakage measurement (needs human-judged baseline we don't have)
- SEPL rollback verbs (no observed rollback scenarios; `ensure_materialized_runtime()` provides implicit rollback)
- Style canonicalization (style bias wasn't the observed failure mode)
- Two-file persistence schema migration (replaces working sprawl with cleaner sprawl)
- Island parent sampler / headless CLI provider (diversity not a current problem)
- Editable meta-mutator (speculative)
- Hedge controller for operator selection (premature optimization)
- Policy Invariance audit gate (holdout already provides anti-gaming)
- Anti-Goodhart axis rotation (defense without observed gaming)
- J/ΔJ shared-calibration diagnostic (speculative failure mode)
- Verdict DSL pattern (solves composition problem we don't have)
- Stage IntEnum state machine (overlaps Stream B substrate)
- pi-autoresearch hook contract (replaces working code)
- Finalize skill (workflow nicety, not correctness)
- KS-stability detection (panel-tied)
- Autogenesis RML versioned interfaces (covered by C4-lean's rubric_hash)
- CDRRM synthetic-rubric training (locked out by frontier-only judge decision)

Total rejected from research catalog: **24 units, ~3,390 LOC of work avoided.** Research notes preserved at `memory/project-external-additions-research-complete-2026-05-11.md`.

## 3. Decisions (locked)

| ID | Decision | Rationale |
|---|---|---|
| D1 | Frontier-only judges (single judge, not panel) | Stream A evidence: per-axis collapse was aggregator bug, not judge bug. Holdout works. Judge noise isn't the bottleneck. |
| D2 | Vendor patterns over taking deps | ShinkaEvolve novelty + AutoResearchClaw sentinel are cleanly vendor-able; no framework imports |
| D3 | Apache-2.0 and MIT only | Two source repos: ShinkaEvolve Apache-2.0, AutoResearchClaw MIT |
| D4 | Every unit behind env-var feature flag | Reversibility via `unset` + `git revert` |
| D5 | No deferrals — keep or reject | Each unit is in scope OR out; no "phase 6 backlog"; rejection is final unless explicit new decision |
| D6 | Address observed problems, not hypothetical ones | The 24 rejected units protect against scenarios we have no evidence of |
| D7 | C5 RaR tier weights kept despite no observed incident | Exception to D6: tier weights are mathematically correct rubric composition, not insurance. Uniform weighting of varied axes (post Stream A axis fix) is incorrect by construction. |

## 4. Evidence base

### Observed problems each unit addresses

| Unit | Evidence (from MEMORY + Stream A audit) |
|---|---|
| C1 Novelty rejection | Judge spend on duplicate mutants is real recurring cost; ShinkaEvolve ICLR 2026 field-validates 30%+ rejection rate |
| C4-lean Hash + evidence | Agent C audit found copy-pasted feedback strings across MA-1..MA-8 axes — direct evidence of judge hallucinating supporting reasoning. `RUBRIC_VERSION` exists at `src/evaluation/rubrics.py:1437` but never propagated. |
| C5 RaR tier weights | Mathematical correctness: post Stream A axis fix, axes vary; uniform-weight composite is wrong by construction. Not "observed incident" — observed correctness gap. |
| C16 Sentinel watchdog | "Evolve died at 99% disk mid-sweep" — MEMORY 2026-05-08 incident report |
| C21 Degenerate-cycle detection | "Mon REGRESSED 8.12→3.41 from meta-agent's MON-1+5 calibration" — MEMORY 2026-05-08 incident report; stagnant calibration cycles damage baselines |

### OSS sources verified

| Source | Repo | License | Star count | Commit SHA |
|---|---|---|---|---|
| ShinkaEvolve | `SakanaAI/ShinkaEvolve` | Apache-2.0 (no NOTICE file) | 1,137★ | `5aadedaa940be9da9fdfe6cecc710f307f0817e2` |
| AutoResearchClaw | `aiming-lab/AutoResearchClaw` | MIT, © Aiming Lab 2026 | 12,052★ | HEAD as of 2026-04-23 |

### Papers cited (no code vendor)

| Paper | arXiv | Used by |
|---|---|---|
| Rulers (rubric hashing + extractive evidence) | 2601.08654 | C4-lean |
| Rubrics as Rewards (RaR) | 2507.17746 | C5 |

## 5. Units

| # | Unit | LOC | Source | License | Reversible |
|---|---|---|---|---|---|
| 1 | **C1** Novelty-rejection sampling | ~230 | ShinkaEvolve `shinka/core/novelty_judge.py` vendor | Apache-2.0 | env flag |
| 2 | **C4-lean** Rubric hash propagation + extractive evidence | ~80 | Paper-derived (Rulers) + existing `RUBRIC_VERSION` | n/a | env flag |
| 3 | **C5** RaR weighted checklist (Essential/Important/Optional/Pitfall) | ~80 | Paper-derived (RaR) | n/a | env flag |
| 4 | **C16** Sentinel heartbeat watchdog (VENDOR VERBATIM) | ~150 | AutoResearchClaw `sentinel.sh` | MIT | `systemctl disable` |
| 5 | **C21** Degenerate-cycle detection | ~80 | AutoResearchClaw `_analysis.py:737-880` (pattern port) | MIT | env flag |

**Total: ~620 LOC, ~2-3 weeks wall time.**

## 6. Unit detail

### C1 — Novelty-rejection sampling

**Goal:** Reject mutants too similar to recent siblings before judge spend.

**Files:**
- `vendor/shinka_evolve/novelty_judge.py` (~230 LOC vendored verbatim from upstream)
- `vendor/shinka_evolve/LICENSE` (Apache-2.0 from upstream)
- `vendor/shinka_evolve/ATTRIBUTION.md` (commit SHA + modification notes)
- `autoresearch_v2/tools/check_novelty.py` (~80 LOC — agent-callable tool wrapping NoveltyJudge; replaces v1 evolve.py:cmd_run wiring per sequential-after-v2 decision)
- `autoresearch_v2/embed_client.py` (~80 LOC — wraps `openai.embeddings.create(model="text-embedding-3-small")`)

**Implementation notes:**
- **API surface:** `NoveltyJudge.assess_novelty_with_rejection_sampling(exec_fname, code_embedding, parent_program, database) -> (bool, dict)` — method on class, constructor takes `similarity_threshold=1.0, max_novelty_attempts=3`
- **Embedding model:** `text-embedding-3-small` ($0.02/1M tokens — cheap); novelty_judge consumes `List[float]`, no model binding
- **Database adapter:** implement `compute_similarity(emb, island_idx) -> List[float]` and `get_most_similar_program(emb, island_idx) -> Program | None` on gofreddy's variant store
- **Wiring:** v2 architecture — agent calls `tools/check_novelty.py` BEFORE `tools/run_experiment.py`; if novelty score below threshold, agent decides whether to proceed or resample. Cleaner than v1 hard-coded gate.
- **Cost gate:** novelty embedding ~$0.0001/mutant vs ~$1/mutant judge spend — at 30% duplication rate, saves ~$0.30/mutant

**License compliance (Apache-2.0 §4):**
- Drop full `LICENSE` in `vendor/shinka_evolve/`
- Add `ATTRIBUTION.md`:
  ```
  Vendored from SakanaAI/ShinkaEvolve (Apache-2.0)
  Source: https://github.com/SakanaAI/ShinkaEvolve
  Commit: 5aadedaa940be9da9fdfe6cecc710f307f0817e2
  Modifications: removed Program type binding, replaced with gofreddy.evolve.Variant duck-type
  ```

**Test gate:**
- Unit: two identical code blocks → similarity=1.0 → reject
- Unit: two genuinely different blocks → accept
- Integration: ≥1 mutant rejected on a fresh geo sweep
- Performance: novelty check adds <200ms per mutant

**Reversibility:** `unset AUTORESEARCH_NOVELTY_REJECTION` returns to current "accept all mutants" behavior.

**Depends on:** Stream B U2 (`tools/run_experiment.py` exists so check_novelty.py has a known sibling).

---

### C4-lean — Rubric hash propagation + extractive evidence requirement

**Goal:** Propagate the existing `RUBRIC_VERSION` hash through every judge response (with mismatch validation), and require judges to quote source text per criterion (with score-cap when evidence missing).

**Files:**
- `judges/evolution/agents/variant_scorer.py` — inject `RUBRIC_VERSION` into payload; validate on response (judges/ unchanged by v2)
- `judges/evolution/prompts/scorer.md` — add extractive evidence requirement (prompts unchanged by v2)
- `autoresearch_v2/tools/score_holdout.py` — parse `evidence` array; cap score at 2 when count < required; validate `rubric_hash` against `RUBRIC_VERSION` (v2 attach point added by Stream B's U3 revision)
- `autoresearch_v2/tools/log_experiment.py` — invalidate cached scores when `rubric_hash` differs (v2 replaces v1's `_load_parent_scores` invalidation)

**Implementation notes:**
- **Hash already exists:** `RUBRIC_VERSION = sha256(...)` at `src/evaluation/rubrics.py:1437` — never propagated to judge service. C4-lean is **wiring, not invention.** v2 plan U3 already includes the rubric_hash attach point (`Rubric hash hook (added 2026-05-11 #4 for Stream C C4-lean integration)`); this unit consumes that attach point.
- **Evidence schema:** each criterion in `per_criterion` JSON gets `evidence: [{quote: "...", source_anchor: "..."}]` array; min count via per-criterion `evidence_min`
- **Score cap:** if `len(evidence) < evidence_min` for any criterion, that criterion's score → 2.0 max (0-5 scale) + `capped_no_evidence: true` flag in aggregate
- **Hash mismatch:** raise `JudgeRubricMismatch` exception (new in `autoresearch/judges/promotion_judge.py`); never silent re-anchor
- **Cache invalidation:** `tools/log_experiment.py` rejects parent-score cache entries where `cached_rubric_hash != current RUBRIC_VERSION` (v2 replaces v1's `_load_parent_scores`)

**Test gate:**
- Unit: stale cached score with old `rubric_hash` → raises `JudgeRubricMismatch` on read
- Unit: judge response with `evidence=[]` for an evidence-required criterion → that criterion's score clipped to ≤2.0
- Unit: cache invalidation purges entries on rubric version bump

**Reversibility:** `unset AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT` returns to current prompt-only path (no hash check, no evidence cap).

**Depends on:** Stream A's A2 (per-axis collapse fix, already merged); Stream B U3 ships the `rubric_hash` attach point in `tools/score_holdout.py`.

---

### C5 — RaR weighted checklist (Essential/Important/Optional/Pitfall)

**Goal:** Replace uniform-weight composite with RaR tier-weighted composite. Without this, gofreddy treats every criterion equally; with it, Essential criteria dominate.

**Files:**
- `src/evaluation/rubrics.py` (1,460 → ~1,540) — add `tier:` field per criterion + weighted aggregation formula
- `data/rubrics/{lane}.yaml` (NEW per lane × 7 lanes) — tier assignments per criterion
- `judges/evolution/prompts/scorer.md` — explain tier weights to the judge

**Implementation notes:**
- **Tier weights (verbatim from RaR paper):**
  - `essential`: 1.0
  - `important`: 0.7
  - `optional`: 0.3
  - `pitfall`: 0.8 (penalty when violated)
- **Formula:** `score_0_5 = 5 * Σ(w_i · c_i) / Σ(w_i)` where `c_i ∈ {0, 1}` per pass/fail
- **Pitfall behavior:** when violated, contributes `0` to numerator (penalty); when avoided, contributes its weight (reward)
- **Initial tagging:** 1-2 hours per lane × 7 lanes = ~1 day's effort to assign tiers across all existing criteria. Default: at least 1 Essential anchor per axis; rest by judgment.
- **No 0-5 vs 0-10 switch in this unit:** keep current scale; tier weights operate independently of scale choice

**Test gate:**
- Unit: all-essential-pass → 5.0
- Unit: all-essential-fail → 0.0
- Unit: pitfall violation contributes 0 even if other tiers pass
- Integration: geo lane composite under v2 schema within ±0.5 of v1 baseline on deterministic fixture (sanity check that tagging didn't perturb scores wildly)

**Reversibility:** `unset AUTORESEARCH_RAR_TIER_WEIGHTS` falls back to uniform-weight composite; YAML files stay but are ignored.

**Depends on:** C4-lean (rubric_hash propagation — tier weights are part of the rubric and change the hash).

---

### C16 — AutoResearchClaw `sentinel.sh` heartbeat watchdog (VENDOR VERBATIM)

**Goal:** Auto-restart evolve loop on stalls (e.g., the "evolve died at 99% disk mid-sweep" class from MEMORY 2026-05-08).

**Files:**
- `autoresearch_v2/scripts/sentinel.sh` (~145 LOC VENDORED VERBATIM from upstream)
- `autoresearch_v2/scripts/LICENSE-AUTORESEARCHCLAW` (MIT verbatim from upstream)
- `autoresearch_v2/scripts/ATTRIBUTION-AUTORESEARCHCLAW.md`
- `autoresearch_v2/tools/run_experiment.py` — emit heartbeat file every ~30s during subprocess wait (small additive Edit; replaces v1 evolve.py heartbeat wiring per sequential-after-v2 decision)
- `/etc/systemd/system/autoresearch-sentinel.service` (optional, production)

**Implementation notes:**
- **Single modification to upstream script:** replace `python -m researchclaw run --resume` with `freddy autoresearch run --resume` (v2 wrapper supports `--resume` per Stream B U10 success criteria)
- **Three non-obvious correctness choices preserved verbatim:**
  - `has_active_children` via `pgrep -P` prevents killing during long subprocess runs even when parent looks dead
  - Cooldown after 3 consecutive failures avoids restart-storm
  - Heartbeat staleness AND PID-dead AND no-active-children all required (3-of-3, not 1-of-3)
- **Heartbeat emission:** `autoresearch_v2/tools/run_experiment.py` writes `{"timestamp": "..."}` to `runs/active/heartbeat.json` every ~30s during subprocess wait. Single touchpoint (replaces scattered v1 hooks).
- **MAX_RETRIES:** upstream default 5; tune per gofreddy operational experience

**Test gate:**
- Unit: stale heartbeat + dead PID + no children → triggers restart_pipeline
- Unit: stale heartbeat + dead PID + active children → does NOT trigger (correct wait)
- Production: kill evolve mid-run; verify sentinel restarts within 5 minutes

**Reversibility:** `systemctl disable autoresearch-sentinel` or simply don't run the script.

**License compliance (MIT):** Drop `LICENSE-AUTORESEARCHCLAW` verbatim. `ATTRIBUTION.md`:
```
Vendored from aiming-lab/AutoResearchClaw (MIT)
Source: https://github.com/aiming-lab/AutoResearchClaw
File: sentinel.sh (HEAD as of 2026-04-23)
Modifications: replaced `python -m researchclaw run --resume` with `freddy autoresearch run --resume`
```

**Depends on:** Stream B's U10 (sentinel needs stable run-resume; v2 wrapper must support `--resume` semantics).

---

### C21 — Degenerate-cycle detection

**Goal:** Pure-function detectors that flag when an evolve loop is in a degenerate REFINE cycle. Inject deterministic system warnings into the meta-agent decision prompt so it can break out. Hard cap `MAX_DECISION_PIVOTS=2`.

**Files:**
- `autoresearch_v2/tools/check_cycle.py` (~80 LOC — agent-callable tool wrapping the three pure-function detectors; replaces v1 evolve.py hard-coded loop logic per sequential-after-v2 decision)
- `autoresearch_v2/lanes/<lane>.md` — add prose advice: "If your last 3 attempts saturated or repeated, call `check_cycle` for a deterministic recommendation"
- `autoresearch_v2/tools/log_experiment.py` — hard cap `MAX_DECISION_PIVOTS = 2` on consecutive REFINE-status rows

**Implementation notes:**
- **Three pure-function detectors (pattern from upstream `_analysis.py:737-880`):**
  ```python
  def detect_saturated_metrics(history: list[float]) -> bool:
      """Returns True if all values <= 0.001 or all >= 0.999."""
      return all(m <= 0.001 or m >= 0.999 for m in history if m is not None)

  def detect_identical_iterations(history: list[float]) -> bool:
      """Returns True if all non-None values are equal and ≥2 exist."""
      vs = [m for m in history if m is not None]
      return len(set(vs)) <= 1 and len(vs) >= 2

  def detect_trivial_ablations(summary, threshold=0.02) -> tuple[int, int]:
      """Returns (n_trivial, n_total). Trivial = <2% diff from baseline."""
      trivial = sum(1 for a in summary["ablations"] if abs(a["delta"]) < threshold)
      return (trivial, len(summary["ablations"]))
  ```
- **v2 architecture: agent-callable, not prompt-injection.** The agent calls `tools/check_cycle.py` when it detects stagnation; the tool returns a deterministic recommendation. The three detectors become tools the agent uses, not hard-coded loop logic injected into prompts.
- **Recommendation strings returned by `check_cycle.py`:**
  - If `detect_saturated_metrics` fires → inject *"Further REFINE cycles CANNOT fix this — the underlying benchmark design is too easy/hard. You SHOULD choose PROCEED with a quality caveat."*
  - If `detect_identical_iterations` fires → inject *"If the same issues persist after 2+ REFINE cycles, choose PROCEED with appropriate quality caveats."*
  - If `>50%` ablations trivial → inject *"STRONG RECOMMENDATION: Choose REFINE. The ablation design is broken."*
- **`_parse_decision(text)` port DROPPED** in v2 — the agent makes the decision, not regex over LLM output. The detectors return structured `(recommendation, reason)` tuples directly.
- **Hard cap:** `MAX_DECISION_PIVOTS = 2` prevents infinite loops even when soft hints fail

**Test gate:**
- Unit tests for each detector with synthetic histories
- Integration: simulated saturated lane receives PROCEED-with-caveat decision injection
- Regression: replay v006 monitoring 8.12→3.41 history with detectors active; verify PROCEED-with-caveat would have triggered

**Reversibility:** `unset AUTORESEARCH_DEGENERATE_DETECTORS` reverts to no-detector behavior.

**License compliance (MIT):** Attribution in `autoresearch/cycle_detectors.py` header:
```python
"""Degenerate-cycle detection.

Pattern ported from aiming-lab/AutoResearchClaw (MIT)
Source: https://github.com/aiming-lab/AutoResearchClaw
File: researchclaw/pipeline/stage_impls/_analysis.py:737-880
"""
```

**Depends on:** Stream B U2 + U4 (`tools/run_experiment.py` and `tools/log_experiment.py` exist; check_cycle is a sibling tool).

---

## 7. Phases (sequential after Stream B v2 lands)

| Phase | Units | Wall time | Gates |
|---|---|---|---|
| **P1** Rubric-quality | C4-lean, C5 | 1 week | Stream B U10+U13 done (v2 score_holdout.py + rubric_hash attach points exist) |
| **P2** Agent-callable tools | C1, C21 | 1 week | Stream B U2+U4 done (v2 tools/ pattern exists; sibling tools to check_novelty / check_cycle) |
| **P3** Reliability | C16 | 3-4 days | Stream B U10 done (v2 wrapper supports `--resume`) |

**Total: ~2-3 weeks** sequential after v2. All three phases can be parallelized once v2 exists (different files, no overlap). Sequence within Stream C: P1 → P2 → P3 minimizes risk; parallel is fine if execution discipline is good.

## 8. Hard gates

- **G0 — Pre-everything:** Stream B v2 substrate landed AND stable for ≥1 week (per sequential-after-v2 decision)
- **G1 — Pre-P1:** Stream B U3 shipped (rubric_hash attach point in `tools/score_holdout.py` exists)
- **G2 — Pre-P2:** Stream B U2 + U4 shipped (sibling tools/ exist for check_novelty + check_cycle to fit alongside)
- **G3 — Pre-C5:** C4-lean shipped (tier weights are part of the rubric; changing them must bump rubric_hash)
- **G4 — Pre-C16:** Stream B U10 geo spike passes (v2 wrapper supports `--resume`)
- **G5 — Pre-everything (Stream A): A6 α data lands** — confirms judges are stable enough that single-judge is fine; if not, Stream C scope re-opens

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| C1 novelty rejection rate too aggressive (rejects good mutants) | Medium | Start `similarity_threshold=1.0` (strict — only true near-duplicates rejected); tune down only if false-positive rate observable |
| C4-lean evidence requirement too strict (too many capped scores) | Medium | Set `evidence_min=1` initially; monitor `capped_no_evidence: true` rate per axis; relax per-axis if >30% capping |
| C5 tier-tagging effort exceeds 1 day per lane | Medium | Pilot on geo first (4-8 criteria); if effort > 4 hours, document blocker before tagging remaining 6 lanes |
| C5 weighted composite drifts >0.5 from v1 baseline on production fixtures | High | Integration test gates before rollout; if drift is large, the tagging needs revision — not the formula |
| C16 sentinel auto-restart masks an underlying bug (loops on same failure) | Medium | Upstream cooldown + 5-retry cap; add observability alert if sentinel restart count exceeds 2/day |
| C21 false-positive degenerate-cycle injection (incorrectly tells meta-agent to PROCEED) | Medium | Hard cap `MAX_DECISION_PIVOTS=2` is the safety net; detectors only inject **hints**, never force decisions |
| Stream A's A6 α data shows judges are unreliable → panel-of-3 becomes necessary after all | Low (α likely ≥0.7 per Stream A's per-axis fix changing the picture) | Plan can be re-opened to add C0/C6 if data demands it; this is a NEW decision, not a deferral |
| LOC budgets drift > 25% per unit | Low (units are small and well-scoped) | Honest accounting |

## 10. Reversibility

| Unit | Revert path |
|---|---|
| C1 | `unset AUTORESEARCH_NOVELTY_REJECTION` + `git revert <commit>`; vendor files stay passive |
| C4-lean | `unset AUTORESEARCH_RUBRIC_HASH_ENFORCEMENT` reverts to prompt-only path |
| C5 | `unset AUTORESEARCH_RAR_TIER_WEIGHTS` reverts to uniform composite; YAML stays but is ignored |
| C16 | `systemctl disable autoresearch-sentinel` |
| C21 | `unset AUTORESEARCH_DEGENERATE_DETECTORS` reverts to no-detector behavior |

All 5 units individually reversible. No data-destructive operations.

## 11. License compliance summary

| Source | License | Compliance action |
|---|---|---|
| ShinkaEvolve (C1) | Apache-2.0, no NOTICE | Drop `LICENSE` + `ATTRIBUTION.md` in `vendor/shinka_evolve/` with commit SHA + modification notes |
| AutoResearchClaw (C16 verbatim, C21 pattern) | MIT, © Aiming Lab 2026 | `vendor/autoresearchclaw/LICENSE` + `ATTRIBUTION.md`; file header in C21's `autoresearch/cycle_detectors.py` |
| Rulers paper (C4-lean inspiration) | n/a (paper) | Cite arXiv 2601.08654 in file header |
| RaR paper (C5 tier weights) | n/a (paper) | Cite arXiv 2507.17746 in `src/evaluation/rubrics.py` header |

## 12. Success criteria

Stream C is complete when:

1. ✅ C1: Novelty-rejection rejects ≥20% of mutants on a fresh geo sweep
2. ✅ C1: Novelty check adds < 200ms per mutant
3. ✅ C4-lean: Stale cached score with old `rubric_hash` raises `JudgeRubricMismatch` on read
4. ✅ C4-lean: Judge response with `evidence=[]` for an evidence-required criterion caps that criterion's score at ≤2.0 on 0-5 scale
5. ✅ C5: All-essential-pass yields 5.0 on a deterministic fixture
6. ✅ C5: Pitfall violation contributes 0 even when other tiers pass
7. ✅ C5: Geo lane composite under tier-weighted schema within ±0.5 of pre-C5 baseline
8. ✅ C16: Sentinel auto-restarts evolve within 5 minutes of kill in production test
9. ✅ C21: All three detectors pass synthetic-history unit tests
10. ✅ C21: Replay of v006 monitoring 8.12→3.41 history triggers PROCEED-with-caveat injection
11. ✅ All vendored files have correct license headers + LICENSE files + ATTRIBUTION.md

## 13. Cross-references

- v2 simplification plan: `docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md` — Stream B's U10 gates C16
- Eval pipeline bug fixes: `docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md` — Stream A's A2 gates C4-lean and C21
- Research catalog (what was considered + rejected): `memory/project-external-additions-research-complete-2026-05-11.md`
- Judge decisions: `memory/project-judge-decisions-2026-05-11.md` — D1 frontier-only lock (single judge, not panel)
- Lean-decision rationale: this document supersedes the bloated 2026-05-11 #2 version (29 units, ~4,010 LOC); the rejected 24 units are documented in §2 Non-goals with one-line reject reasons

## 14. What changed from prior plan versions

- **2026-05-11 #1:** 15 units, ~2,330 LOC. Pre-completeness-audit baseline.
- **2026-05-11 #2:** 29 units, ~4,010 LOC. Added during JR's "did you include everything?" completeness audit.
- **2026-05-11 #3:** 29 units, math fixed (LOC counts and unit counts now consistent).
- **2026-05-11 #4:** 5 units, ~620 LOC. After JR's "this is overengineered" pressure-test + "no deferrals" rule. 24 units rejected because they protect against scenarios we have no evidence of; the 5 kept address either observed problems (C1 cost, C4-lean hallucination, C16 disk-full, C21 stagnant cycles) or mathematical correctness (C5 tier weights).
- **2026-05-11 #5 (THIS VERSION):** 5 units, ~620 LOC. After JR's "sequential is fine" decision. All units retargeted from v1 (`autoresearch/evolve.py`, `evaluate_variant.py`) to v2 architecture (`autoresearch_v2/tools/`). Stream C now sequential-after-Stream-B. C1 becomes agent-callable `tools/check_novelty.py`; C21 becomes agent-callable `tools/check_cycle.py` + prose advice in `lanes/<lane>.md`; C16 heartbeat moves to `tools/run_experiment.py`; C4-lean targets `tools/score_holdout.py`'s rubric_hash attach point (added by Stream B U3 revision); C5 unchanged (rubrics.py is outside v2 substrate work).

**Rationale for cut from 29 → 5:** Stream A shipping evidence revealed that per-axis collapse was an aggregator bug (not judge bug), holdout actually ran (just not lineage-captured), and 6/7 fragile fixtures had min=0 from variant output failures (not judge noise). The bulk of audit additions were defending against judge-noise failure modes that aren't actually happening in production.

## 15. Glossary

- **Stream A / B / C:** the three parallel workstreams (bug fixes / v2 simplification / external absorptions)
- **Vendor:** copy file into `vendor/` subdir with LICENSE preservation + attribution; not a `pip install` dependency
- **Pattern-only:** re-implement the design without copying code
- **Frontier judge:** Claude Opus 4.7 (current single judge; panel rejected)
- **Inner-loop generator:** DeepSeek (current default per JR's 2026-05-11 note)
- **RUBRIC_VERSION:** existing SHA-256 hash at `src/evaluation/rubrics.py:1437` that C4-lean propagates and enforces
- **MAX_DECISION_PIVOTS=2:** hard cap from AutoResearchClaw's `stages.py` ported by C21 to prevent infinite REFINE loops
