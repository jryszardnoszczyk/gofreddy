# Judge Calibration Drift Detection (Plan B Phase 4 Step 3b — deferred)

**Status:** stub created 2026-04-23 for MVP carve-out deferral. Do NOT start until drift has been observed OR calibration data has accumulated.

## What this plan ships

Bi-directional cross-family judge drift detection:

- `autoresearch/judge_calibration.py` — CLI entry point reading the monthly score snapshots from `events.jsonl`, invoking the drift-detection agent via `call_quality_judge(role="calibration_drift", ...)`.
- PR-gated baseline re-record workflow (`.github/workflows/deploy-evolution-judge.yml` extension): when a new baseline is recorded, it MUST land via PR review, not runtime API.
- Monthly cron entry running `calibration-snapshot.sh` (already shipped) + the drift check.
- Bi-directional aggregation: Codex judging Claude's scores AND Claude judging Codex's scores; correlated drift across both families is the "mixed" verdict.

## Why deferred (per 2026-04-23 review)

- Builds drift-detection system for drift that has not been observed.
- Monthly cadence means up to 30 days of production decisions against a silently-shifted judge before the check fires.
- The acknowledged failure mode (both providers update models the same week) is NOT detected by bi-directional alone; the plan said "just rebaseline when a major version ships" but doesn't wire that up.

## What's already shipped toward this

- `autoresearch/scripts/calibration-snapshot.sh` — log-only stand-in (MVP). Records `kind="calibration_score"` per (variant, fixture) pair. Data accumulates.
- `autoresearch/judges/quality_judge.py::call_quality_judge` accepts `role="calibration_drift"`. The role already exists; only the autoresearch-side CLI + aggregation is missing.

## Trigger conditions — when to start

1. **≥3 months of `kind="calibration_score"` data in `events.jsonl`**. Follow-up plan reasons about trend magnitude / variance / reasoning drift; short data series produces false-positives.
2. **OR: one observed post-promotion regression that correlates with a model version change** (judge model bumped, scores shifted, scoring bias masked actual degradation). This is the real signal that drift matters.

## What to copy from the deferred Plan B material

`docs/plans/2026-04-21-003-feat-fixture-program-execution-plan.md` Phase 4 Step 3b has the full 80-line `judge_calibration.py` skeleton + CI workflow extension. Copy after resolving:

- Embed `prompt_version` + `judge_cli_version` in every score event so the drift check can distinguish "judge drifted" from "judge was replaced."
- Add an escape hatch: operator-triggered `judge_calibration.py --force-rebaseline` for known model-version changes (the acknowledged hole the plan flagged).

## Acceptance

- Monthly run completes under 30 min.
- When a baseline is manually mutated in the judge-service (simulating drift), the next check's verdict is `magnitude_drift` or `variance_drift` with defensible reasoning.
- False-positive rate on stable-model baselines: the check returns `stable` for ≥6 consecutive months of known-no-drift data.
