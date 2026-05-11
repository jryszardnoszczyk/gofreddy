# Eval Pipeline Bug Fixes Plan (Stream A)

**Date:** 2026-05-11
**Author:** Jan + Claude (after 3-agent research thread)
**Status:** Awaiting JR green-light for A0 verification
**Companion plans:**
- `2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md` (Stream B — v2 simplification)
- `2026-05-11-003-external-absorptions-plan.md` (Stream C — external paper/OSS absorptions)

## 1. Goal

Resolve three structural bugs in the existing judge / eval pipeline before any judge composition or panel work begins. **These bugs make all downstream calibration measurements uninterpretable.** Fix them, verify the fix with regression tests, then run a synthetic Krippendorff α experiment to ground all Stream C scope decisions in real data.

## 2. Non-goals (explicit out of scope)

- Frontier-judge panel composition → Stream C unit C0
- Rubric hash-locking, extractive evidence, weighted checklists → Stream C C4/C5
- v2 substrate simplification → Stream B (existing plan)
- Replacing single-judge architecture with panel-of-3 → Stream C C6 (gated on Stream A's α measurement)

## 3. Decisions (locked)

| ID | Decision | Rationale |
|---|---|---|
| D1 | Fix axis collapse before any composition work | Panel calibration on broken per-axis output is uninterpretable; RRD whitening requires non-degenerate axes |
| D2 | Verify Agent C's claims independently before fixing | 100% uniformity (158/158 files) is so extreme it warrants a sanity check — possible measurement artifact |
| D3 | Restore holdout before promoting any further variants | `lineage.jsonl.holdout=0.0` across all variants means anti-gaming is non-functional; v2 plan gates depend on real holdout numbers (search-v1≥7.0 AND holdout-v1≥4.5) |
| D4 | Synthetic rerun experiment is mandatory before deciding panel-of-3 | Rating Roulette α 0.33-0.79 is a literature average; gofreddy's actual α might be higher (competitive CV=0.8%, MA CV=4.8% suggests reasonable stability on stable lanes) |
| D5 | Stream C v1 scope is decided by A6's α data | If α ≥ 0.7 essential-axis: single frontier judge suffices, defer panel; if 0.4-0.7: panel justified; if <0.4: rubric itself needs rewriting before panel |
| D6 | Fragile-fixture audit is part of Stream A, not Stream B | `monitoring-ramp-arc-t1` sd=2.671 (vs siblings <0.75) flips the lane composite by ~7 points; deleting it from composite is independent of substrate simplification |

## 4. Evidence base

All findings from Agent C audit on 2026-05-11 against `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/archive/`:

### Bug 1 — per-axis score collapse
- **158 eval files scanned**; **158/158** had identical scores within an eval
- Geo example: `GEO-1..GEO-8` all 1.00 in the same eval; pairwise Pearson r=1.00 across all axis pairs over 25 (variant, fixture, eval) cells
- Marketing audit `eval_feedback.json` for Stripe: MA-1..MA-8 all = 0.5 with same `feedback` string copy-pasted
- Monitoring: MON-1, MON-2, MON-4, MON-6 collapsed within each eval
- **Implication:** RRD whitening, panel-of-3, Krippendorff α — all presuppose per-axis variation that doesn't exist. Bug 1 is the first thing to fix.

### Bug 2 — holdout = 0.0 across every variant
- `lineage.jsonl` has `holdout_composite=0.0` (or absent) for every recorded variant
- The anti-gaming mechanism is off; either holdout suite isn't running or runs and discards
- v2 plan U10 hard gate (`holdout-v1≥4.5`) is uncheckable in current state

### Bug 3 — fragile fixture `monitoring-ramp-arc-t1`
- Score range **1.500 – 8.550** across 7 variants (sd=2.671)
- Sibling monitoring fixtures (rippling, shopify, ramp-arc-t0, lululemon) all have sd < 0.75
- The MEMORY note "monitoring REGRESSED 8.12→3.41 from MON-1+5 calibration" is technically misleading — within-eval axes can't disagree (Bug 1), so the regression came from one knife-edge fixture flipping its gate
- **Implication:** panel-of-3 cannot fix `monitoring-ramp-arc-t1`; this is fixture-level fragility, not judge noise

### Bug 4 — geo signal/noise ratio
- Signal (across-mutant variance on the same fixture) / Noise (across-fixture variance within the same mutant) = **0.38**
- Healthy systems have ratio ≥ 5
- Geo evolution selection signal is currently sub-noise; v2 U10 gate may be selecting on noise

### Cost picture
- 182 eval files across 147 variants ≈ 1.2 judge calls per variant
- Judges almost certainly < 20% of total compute spend
- Cost case for panel-of-3 is weak on its own; quality/α has to carry the argument

## 5. Units

| Unit | Title | LOC | Reversible | Depends on |
|---|---|---|---|---|
| A0 | Sanity-verify Agent C's claims | ~30 (test script) | yes (just delete) | — |
| A1 | Root-cause-trace per-axis collapse | logging-only | yes | A0 passes |
| A2 | Fix per-axis collapse + regression test | ~80 | yes via env flag | A1 root cause confirmed |
| A3 | Diagnose holdout=0.0 origin | logging + grep | yes | A0 passes |
| A4 | Restore holdout suite + invariant test | ~50 | yes | A3 |
| A5 | Audit fragile fixtures (drop/oversample) | ~40 | yes via config | A2 (need working per-axis first) |
| A6 | Synthetic rerun experiment (Krippendorff α) | ~100 (one-shot script) | yes (script-only) | A2, A4 |
| A7 | Stream C scope decision gate | doc-only | n/a | A6 |

**Total LOC: ~300** (mostly diagnostic + tests; the actual bug fixes are smaller than the verification harness)

## 6. Unit detail

### A0 — Sanity-verify Agent C's claims (1 hour)

**Goal:** Independently confirm Bug 1, Bug 2, Bug 3 before committing engineering time to fixes.

**Steps:**
1. Bug 1 verification — run on host:
   ```bash
   cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
   for f in autoresearch/archive/v006/sessions/geo/*/evals/*.json; do
     jq -r '.rubric_results[] | .score' "$f" | sort -u | wc -l
   done | sort | uniq -c
   ```
   - Expected if Bug 1 real: most lines show "1" (one unique score per eval)
   - Expected if false positive: lines show varied counts (2, 3, 4...)
2. Bug 2 verification — run on host:
   ```bash
   jq -r '.[] | .holdout_composite // 0' autoresearch/archive/lineage.jsonl | sort -u
   ```
   - Expected if Bug 2 real: output is just `0` or `null`
3. Bug 3 verification — pull fixture variance:
   ```bash
   for v in autoresearch/archive/v*/scores.json; do
     jq -r --arg fid "monitoring-ramp-arc-t1" '.fixtures_detail[$fid].composite // empty' "$v"
   done | python3 -c "import sys, statistics; xs=[float(x) for x in sys.stdin if x.strip()]; print(f'n={len(xs)} min={min(xs):.2f} max={max(xs):.2f} sd={statistics.pstdev(xs):.2f}')"
   ```

**Acceptance criterion:** all three bugs reproduce on JR's machine. If any one does NOT reproduce, halt this plan and re-audit before proceeding.

**Reversibility:** zero artifacts.

### A1 — Root-cause-trace per-axis collapse (3-4 hours)

**Goal:** Pin down which of the three hypotheses is correct.

**Three hypotheses to discriminate:**
1. **Prompt-quality bug:** Judge LLM is being lazy and emitting identical per-axis scores despite the prompt asking for distinct values
2. **Parser bug:** `evaluate_variant.py:1362-1409` aggregator collapses `per_criterion` to a single value before persisting
3. **Storage/aggregator bug:** Composite is computed correctly but back-filled across axes at write time

**Steps:**
1. Add logging at `judges/evolution/agents/variant_scorer.py:128` to capture **raw LLM response** before any parsing — write to `/tmp/raw_judge_response.jsonl`
2. Run one geo fixture eval (`semrush`) with the logging enabled
3. Inspect `/tmp/raw_judge_response.jsonl`:
   - If raw response has identical scores → Hypothesis 1 (prompt bug)
   - If raw response has varied scores but `scores.json` has uniform → Hypothesis 2 or 3
4. If Hypothesis 2/3 suspected, add logging at `evaluate_variant.py:1362` capturing the `per_criterion` payload before aggregation
5. Document root cause in `/tmp/A1-root-cause.md` (committed alongside A2's fix)

**Acceptance criterion:** one of the three hypotheses is identified with raw-response evidence.

**Reversibility:** logging removed in A2.

### A2 — Fix per-axis collapse + regression test (1 day)

**Goal:** Ship the fix gated by `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on` env flag.

**Files touched (depends on A1 outcome):**
| Hypothesis | Likely fix site | LOC |
|---|---|---|
| 1 — prompt | `judges/evolution/prompts/scorer.md` + `scorer_templated.md` | ~30 |
| 2 — parser | `autoresearch/evaluate_variant.py:1362-1409` | ~40 |
| 3 — aggregator | `judges/evolution/agents/variant_scorer.py:128-180` | ~50 |

**Implementation notes:**
- Add `tests/test_axis_distinctness.py`:
  ```python
  def test_axis_scores_have_meaningful_variance():
      """Regression test for per-axis collapse bug (Stream A).

      For any single eval, per_criterion scores must show variance > 0
      across ≥50% of fresh runs. Identical scores within a 158/158 sample
      indicates the axis-collapse bug has returned.
      """
      eval_files = glob("autoresearch/archive/v*/sessions/*/evals/*.json")
      varied_count = sum(
          1 for f in eval_files
          if len(set(r["score"] for r in load(f)["rubric_results"])) > 1
      )
      assert varied_count / len(eval_files) >= 0.50, (
          f"Only {varied_count}/{len(eval_files)} files show axis variance — "
          "axis-collapse bug may be back"
      )
  ```
- Add this test to CI; failing the test blocks all autoresearch sweeps
- For Hypothesis 1, the prompt fix likely needs explicit phrasing: *"Each criterion must be scored independently with potentially different values; do not back-fill identical scores"*

**Acceptance criterion:**
- One fresh `freddy autoresearch evolve --lane geo --max-iters 1` run produces an eval file where `len(set(scores)) > 1`
- New regression test passes against fresh archive content
- 519/519 existing tests stay green

**Reversibility:** `unset AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE` reverts to pre-fix behavior (in case the fix has unintended consequences); follow with `git revert`.

### A3 — Diagnose holdout=0.0 origin (2 hours)

**Goal:** Find whether holdout suite isn't running at all, runs but discards, or runs but writes 0.

**Steps:**
1. Grep for holdout invocation:
   ```bash
   rg -n "_run_holdout_suite|EVOLUTION_HOLDOUT" autoresearch/ judges/ src/ --type py
   ```
2. Check env at runtime:
   ```bash
   env | grep -i HOLDOUT
   cat judges.env | grep -i HOLDOUT
   ```
3. Read the holdout gate in `evaluate_variant.py` — find where `holdout_composite` is computed and written to lineage
4. Run one variant with `AUTORESEARCH_LOG_LEVEL=DEBUG` and trace the holdout decision branch
5. Document the failure mode in `/tmp/A3-holdout-diagnosis.md`

**Three plausible failure modes:**
- **3a:** `EVOLUTION_HOLDOUT_MANIFEST` env var is unset → holdout silently skipped
- **3b:** Holdout suite runs but every fixture short-circuits with `composite=0`
- **3c:** Holdout result is computed but lost during the lineage write

**Acceptance criterion:** root cause identified with evidence (env dump, log trace, or code location).

**Reversibility:** zero artifacts.

### A4 — Restore holdout suite + invariant test (1 day)

**Goal:** Make `lineage.jsonl.holdout_composite > 0` for at least one fixture; add invariant test.

**Files touched (depends on A3 outcome):**
- If 3a: ship `judges.env` template with required holdout vars + `run.py` validation that refuses to start without them
- If 3b: trace the short-circuit in `evaluate_variant.py:_run_holdout_suite`; likely a fixture path glob or cache key mismatch
- If 3c: fix the lineage writer at the promotion path (`autoresearch/evolve.py:promote_atomic`)

**Invariant test:**
```python
def test_no_variant_promoted_with_zero_holdout():
    """After Stream A fixes, no new variant should land in lineage.jsonl
    with holdout_composite==0 unless explicitly marked as 'holdout_skipped'."""
    lineage = read_jsonl("autoresearch/archive/lineage.jsonl")
    for entry in lineage:
        if entry.get("status") == "promoted":
            assert entry.get("holdout_composite", 0) > 0 or entry.get("holdout_skipped"), (
                f"Variant {entry['id']} promoted with zero holdout — Bug 2 may have returned"
            )
```

**Acceptance criterion:**
- One fresh geo variant produces `holdout_composite > 0` in `lineage.jsonl`
- Invariant test passes on a fresh sweep
- v2 plan's U10 gate (search-v1≥7.0 AND holdout-v1≥4.5) becomes checkable

**Reversibility:** gated by `AUTORESEARCH_EVAL_FIX_HOLDOUT=on`; revert via `git revert`.

### A5 — Audit fragile fixtures (4 hours)

**Goal:** Either drop `monitoring-ramp-arc-t1` from composite or oversample to reduce its leverage.

**Steps:**
1. Run the same variance analysis as A0-Bug3 across ALL fixtures in ALL lanes:
   ```bash
   # Per fixture: sd across all variants
   for lane in geo monitoring competitive marketing_audit storyboard x_engine linkedin_engine; do
     # ... compute sd per fixture in $lane
   done
   ```
2. Build `fragile-fixtures.md` listing every fixture with sd > 1.5
3. **Decision matrix** per fragile fixture:
   - sd > 2.0 and only fixture of its kind → drop from composite; add to "ablation set"
   - sd > 1.5 and has siblings → require composite computation only when n_fixtures ≥ 3 successfully scored
4. Implement composite-floor logic in `autoresearch/lane_registry.py`:
   ```python
   def compute_lane_composite(fixture_scores):
       if len(fixture_scores) < 3:
           return None  # don't promote on n<3
       return geometric_mean(fixture_scores)
   ```

**Acceptance criterion:** `monitoring-ramp-arc-t1` is either dropped from composite or no longer single-handedly determines the lane verdict.

**Reversibility:** revert config change in `lane_registry.py`.

### A6 — Synthetic rerun experiment (1 day, ~$30 budget)

**Goal:** Measure real Krippendorff α per lane on the now-fixed pipeline. This is the gating measurement for Stream C scope.

**Protocol:**
- **10 fixtures across 4 lanes** (geo×2, monitoring×3, marketing_audit×3, competitive×2 — pick stable, high-quality fixtures)
- **5 reruns each** at temperature=0.3 (per Rating Roulette's finding that T=0 degrades agreement)
- **Same prompt, same model** (current default judge — likely Sonnet)
- Compute Krippendorff α per axis per lane via the `krippendorff` Python package, interval scale
- Compute coefficient of variation (CV) per fixture
- Compute signal/noise ratio (across-mutant / within-fixture variance) — should be > 5 in a healthy system

**Output:** `/tmp/A6-alpha-measurement.md` with:
- Per-axis α per lane (≥30 samples per axis floor)
- Distribution plot (axes with α < 0.5 flagged red)
- CV per fixture
- Recommendation for Stream C scope

**Cost estimate:** 10 fixtures × 5 reruns × 8 axes × ~1500 tokens × $5/M = **~$30** at current Sonnet pricing. Total wall time ~3 hours with current concurrency.

**Acceptance criterion:** α data exists for ≥3 lanes; signal/noise ratio computed; Stream C scope decision is data-driven.

**Reversibility:** experiment is script-only; metrics file is sidecar.

### A7 — Stream C scope decision gate (1 hour, doc-only)

**Goal:** Use A6's data to make a binding decision on Stream C v1 scope.

**Decision matrix:**

| A6 finding | Stream C v1 scope |
|---|---|
| α ≥ 0.7 on essential axes across all lanes | **Skip panel-of-3 in v1.** Single frontier judge (current Sonnet) is fine. Ship C1 (novelty), C4 (rubric hash), C5 (RaR weights), C13 (policy invariance), C14 (J/ΔJ diagnostic) only. Defer C0/C6 panel work. |
| 0.5 ≤ α < 0.7 | **Panel justified.** Ship full Stream C Phase 1+2 including C0 (frontier panel composition) and C6 (multi_scorer). |
| α < 0.5 on any essential axis | **Rubric prose itself is ambiguous.** Pause Stream C; rewrite the failing axis rubric with explicit anchoring (0/1/2/3/4/5 prose anchors) before any panel work. |

**Acceptance criterion:** decision documented in `/tmp/A7-stream-c-scope.md`; communicated to Stream C plan owner (JR).

## 7. Phases

| Phase | Units | Wall time | Gates |
|---|---|---|---|
| P1 — Verify | A0 | 1 hour | All three bugs reproduce |
| P2 — Diagnose | A1, A3 | 5-6 hours | Root causes pinned |
| P3 — Fix | A2, A4 | 2 days | Regression tests green |
| P4 — Audit | A5 | 4 hours | Fragile-fixtures decision |
| P5 — Measure | A6 | 1 day (mostly waiting) | α data exists per lane |
| P6 — Decide | A7 | 1 hour | Stream C scope set |

**Total: ~4-5 working days.**

## 8. Hard gates

- **Gate G1 (between P1 and P2):** If any bug fails to reproduce in A0, **halt and re-audit**. Don't fix what you can't reproduce.
- **Gate G2 (between P3 and P5):** A2's regression test must be green AND A4's invariant test must pass before A6's α experiment runs. Otherwise α is measured on a still-broken pipeline.
- **Gate G3 (P6 outputs to Stream C):** A7's decision is binding; Stream C plan owner does not greenlight C0/C6 work without it.

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Agent C's 100% finding is a measurement artifact | Medium | A0 verifies independently before any engineering work |
| Bug 1 fix breaks existing scoring assumptions (e.g., callers assume uniform per-axis scores) | Medium | A2 ships behind env flag; revert by `unset` |
| Holdout fix reveals additional broken fixtures | Medium | A5 audit happens regardless |
| α experiment shows lanes are actually fine (no panel needed) | Low | This is a **good outcome** — saves Stream C effort |
| Fragile-fixture drop changes the lane composite enough to invalidate prior v006 baselines | Medium | v2 plan's U10 gate already requires fresh baseline measurement; A5 result feeds into that |
| Holdout root cause is in `EVOLUTION_PRIVATE_ARCHIVE_DIR` setup outside the repo (operator config) | Medium | A3 explicitly checks env first; if it's operator config, fix is documentation + run.py validation |
| Stream A drags > 1 week | Low | Each unit is independent; can ship A2 + A4 separately |

## 10. Reversibility per unit

| Unit | Revert path |
|---|---|
| A0 | No artifacts — nothing to revert |
| A1 | Logging removed in A2 |
| A2 | `unset AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE` + `git revert <commit>` |
| A3 | No artifacts |
| A4 | `unset AUTORESEARCH_EVAL_FIX_HOLDOUT` + `git revert <commit>` |
| A5 | Revert `lane_registry.py` config change |
| A6 | Script + metrics file in `/tmp/` — delete |
| A7 | Doc-only |

All units are individually reversible with `git revert`. No data-destructive operations.

## 11. Open questions

| Q | Resolution path |
|---|---|
| Q1 — Does Bug 1 affect the 7 newest variants (v167+) or did it pre-exist v006? | A1 checks raw-response logs across multiple variants |
| Q2 — Is holdout = 0 because the suite never ran, or because it ran on empty fixtures? | A3 logs the holdout branch |
| Q3 — If A2's fix changes baseline scores, does v2 plan's U10 gate need to be recalibrated? | Re-measure v006 baseline after A2; update v2 plan if so |
| Q4 — Should the synthetic rerun in A6 use the current single-judge default or test panel-of-3 directly? | A6 default is single-judge baseline; if α is borderline, can re-run with panel as a side experiment |
| Q5 — Are there other lanes besides monitoring with fragile single-fixture composites? | A5 surfaces this |

## 12. Success criteria

Stream A is complete when:
1. ✅ A0 reproduces all three bugs on JR's machine
2. ✅ A2's axis-distinctness regression test is in CI and green
3. ✅ A4's holdout invariant test is in CI and green
4. ✅ One fresh geo variant has both `len(set(per_criterion_scores)) > 1` AND `holdout_composite > 0`
5. ✅ A5's fragile-fixture audit is committed
6. ✅ A6 produces per-axis α per lane in `/tmp/A6-alpha-measurement.md`
7. ✅ A7's Stream C scope decision is documented

After (7), the user (JR) greenlights the corresponding Stream C scope and we move to the external absorptions plan.

## 13. Communication

- **Daily standups:** unit completion posted to memory as one-liners
- **Failure escalation:** if any unit blocks > 4 hours past its budget, halt and re-evaluate with JR
- **A7 output:** lands in `memory/project-stream-a-complete-YYYY-MM-DD.md` with the Stream C scope decision quoted verbatim

## 14. Cross-references

- v2 simplification plan: `docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md` — Stream B does not start its U0 audit until Stream A's A4 (holdout restore) lands, because the v2 plan's U10 gate requires real holdout numbers
- External absorptions plan: `docs/plans/2026-05-11-003-external-absorptions-plan.md` — its Phase 1 cannot start until Stream A's A7 decision lands
- Judge decisions memo: `memory/project-judge-decisions-2026-05-11.md` — frontier-only judges locked
- Three-agent research thread: see `memory/project-external-additions-research-complete-2026-05-11.md`
