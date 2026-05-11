# Lane: monitoring — weekly brand/topic monitoring digests

**What this lane does:** evolves the prose at `lanes/monitoring.md` so each session produces a `digest.md` summarising the past week's mentions across press, social, podcasts, video, and reviews — clustered into stories, synthesised into recommendations.

**Baselines you're trying to beat:**
- v006 search-v1 composite: **8.12** for monitoring.
- v011 introduced a regression (composite 3.41 from a too-aggressive MON-1+5 calibration) — explicitly avoid that mutation pattern. Decision recorded: roll back was accepted; v006 baseline stands.

---

## Deliverable contract

The session writes `digest.md` + `findings.md` under `sessions/monitoring/<client>/`. Each session MUST satisfy ALL of:

1. `session.md` exists.
2. `results.jsonl` is non-empty and parseable line-by-line.
3. At least one `results.jsonl` entry has `type: select_mentions`.
4. Clustering evidence — either `stories/*.json` files OR a `digest.md` (low-volume weeks may skip clustering).
5. Synthesis evidence — `digest.md` is the canonical synthesised deliverable.
6. Recommendation evidence — `recommendations/` files OR a `results.jsonl` entry with `type: recommend` OR `digest.md`.
7. `digest.md` exists.
8. `findings.md` exists.
9. Session status is terminal — `## Status: COMPLETE` in `session.md` OR `digest.md` present.
10. If any `recommendations/` files exist, both `executive_summary.md` AND `action_items.md` are present.
11. **Source coverage** — the latest `select_mentions` entry reports ≥2 sources, OR `digest.md` is present (low-volume fallback).

Any failure → `checks_failed`.

---

## The 8 MON judges (your fitness function)

Composite = geometric mean across MON-1 .. MON-8.

Historical lessons (v011 regression):
- **MON-1+5 over-calibration is dangerous.** v011 tightened both axes simultaneously and the lane composite collapsed 8.12 → 3.41. Calibrate one axis at a time.
- **Source coverage matters** — fewer than 2 sources in `select_mentions` is the single biggest signal of a thin digest.
- **Cluster fidelity** — `stories/*.json` should each have ≥3 supporting mentions; one-source stories score low on MON-2.

---

## Custom persistence

This lane uses `_persist_monitoring_dqs_score` (referenced in `lane_registry.LANES['monitoring']`) to fold a DQS (data quality score) into the lane's metrics row. v2 preserves this via the v006 workflow subprocess — no v2 tool changes needed.

---

## What you CANNOT edit

- `autoresearch/archive/v006/workflows/monitoring.py`
- `autoresearch/archive/v006/workflows/session_eval_monitoring.py`

Plus all the universal don't-edit rules (other lanes, tools/, harness/, judges/, autoresearch.md).

---

## Mutation surfaces that worked

- Adding "if `<2 sources` is hit twice in a row, escalate to JR" pattern.
- Forcing `stories/<id>.json` to include `evidence_ids` referencing specific mention IDs.

## Mutation surfaces that regressed

- v011's joint MON-1+5 calibration (composite 8.12 → 3.41). Single-axis tightening only.
- Removing the `findings.md` requirement — the synthesis gate cascades from missing findings.

---

## Fixture coverage

- Search-v1: `monitoring-*` fixture_ids in `eval_suites/search-v1.json`.
- Holdout-v1: per-lane fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`.

---

## Recent history pointers

- `git log --oneline lanes/monitoring.md`
- Last ~10 rows of `lanes/monitoring/results.tsv`
- `alerts.jsonl` filtered by `lane=monitoring` (the v011 collapse was a real alert here)
