# Stream A — Summary

Plan: `docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`
Branch: `feat/stream-a-eval-fixes`

## Status by unit

| Unit | Status | Commit(s) | Evidence |
|---|---|---|---|
| A0 — verify bugs reproduce | ✅ | (in-session) | All 3 bugs confirmed against `autoresearch/archive/` |
| A1 — root-cause axis collapse | ✅ | `e30a3f8` | `docs/plans/2026-05-11-002-A1-root-cause.md` (Hypothesis 3) |
| A2 — fix axis collapse + tests | ✅ | `e30a3f8` | 4 new tests in `tests/test_cli_evaluate.py` + `tests/test_axis_distinctness.py` |
| A3 — diagnose holdout=0.0 | ✅ | `44634aa` | `docs/plans/2026-05-11-002-A3-holdout-diagnosis.md` (Failure Mode 3c) |
| A4 — restore holdout lineage + tests | ✅ | `44634aa` | 16 tests in `tests/autoresearch/test_holdout_lineage_invariant.py` |
| A5 — fragile-fixture audit + filter | ✅ | `3b44167` | `docs/plans/2026-05-11-002-A5-fragile-fixtures.md` + 15 tests |
| A6 — α experiment | (running) | `985a103` | `/tmp/A6-alpha-measurement.md` (post-run) |
| A7 — Stream C scope decision | (pending A6) | — | `/tmp/A7-stream-c-scope.md` (post-A6) |

## What was actually broken

### Bug 1 — per-axis score collapse (84% of evals showed flat scores)
**Root cause** (`cli/freddy/commands/evaluate.py:_handle_legacy_batch_critique`):
The session-judge's `/invoke/critique` endpoint returns a single
`overall: pass|rework|fail`. When v006's batch-critique caller asked for
N criteria, the bridge code concatenated every rubric into one
`session_goal`, posted ONE request, then broadcast the resulting score
across every criterion (lines 215-225 pre-fix). An in-line comment
called the loss out but it was never reverted.

**Fix** (gated by `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE`):
- The critique prompt now requests `per_criterion[]` when the session
  goal carries multiple numbered rubrics.
- The bridge unpacks `per_criterion` to distinct per-criterion scores
  when present and complete; falls back to broadcast otherwise.

### Bug 2 — `lineage.jsonl.holdout_metrics: {ran: false}` for all 348 entries
**Root cause** (`autoresearch/evaluate_variant.py`):
Only one writer ever touched `holdout_metrics` (line 1617, search-time
with `holdout_ran=False`). `evaluate_holdout` wrote private finalize
results to `${TMPDIR}/autoresearch-holdouts/` but never refreshed the
public lineage. The v2 plan's U10 gate (`holdout-v1 ≥ 4.5`) was
structurally uncheckable.

**Fix** (gated by `AUTORESEARCH_EVAL_FIX_HOLDOUT`):
- New `_update_lineage_holdout_metrics` helper appends a refreshed
  lineage entry whose `holdout_metrics` mirrors the private finalize
  payload (composite, baseline, eligibility, reason, per-domain).
- Top-level `holdout_composite` mirrored so `evolve_ops._holdout_composite`
  reads correctly.

### Bug 3 — `monitoring-ramp-arc-t1` plus six other fragile fixtures
**Audit:** Seven fixtures swing > 2σ across the archive. Six show
`min=0.00` (variants completely failing the fixture) — not judge noise,
output failure.

**Fix** (gated by `AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES`):
- New `autoresearch.lane_registry.FRAGILE_FIXTURES` frozenset.
- `_aggregate_suite_results` excludes those fixtures from the lane
  composite while keeping their scores in `fixtures_detail`.

## How to verify

```bash
# Unit-level (always-on)
.venv/bin/python -m pytest \
  tests/test_cli_evaluate.py \
  tests/test_axis_distinctness.py \
  tests/autoresearch/test_holdout_lineage_invariant.py \
  tests/autoresearch/test_fragile_fixtures.py \
  -v
# Expect: 47+ passed (2 skipped for sweep-time gates)

# After a fresh sweep, enable the sweep-time invariants:
AUTORESEARCH_ARCHIVE_AXIS_CHECK=1 \
AUTORESEARCH_ARCHIVE_HOLDOUT_CHECK=1 \
.venv/bin/python -m pytest \
  tests/test_axis_distinctness.py::test_archived_evals_show_axis_variance \
  tests/autoresearch/test_holdout_lineage_invariant.py::test_no_variant_promoted_with_zero_holdout
```

## How to roll out

Three env flags, each independently reversible:

```bash
export AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on    # Bug 1 fix
export AUTORESEARCH_EVAL_FIX_HOLDOUT=on          # Bug 2 fix
export AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on # Bug 3 fix
```

Unset any flag to revert that fix only. `git revert` per-unit
commits to remove a fix entirely.

## Cross-references

- v2 simplification plan (Stream B): `docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md` — U10 gate now checkable
- External absorptions plan (Stream C): `docs/plans/2026-05-11-003-external-absorptions-plan.md` — scope decided by A6+A7
- Judge architecture decisions: `memory/project-judge-decisions-2026-05-11.md` (frontier-only judges locked)
