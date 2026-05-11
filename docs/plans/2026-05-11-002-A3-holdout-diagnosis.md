# A3 — Diagnosis of `holdout_metrics: {"ran": false}` across every lineage entry

## Verdict: Failure Mode 3c (holdout runs, result is lost during lineage write)

## Evidence

### Env + config are healthy
- `~/.config/gofreddy/judges.env` sets `EVOLUTION_HOLDOUT_MANIFEST`.
- Manifest files exist: `~/.config/gofreddy/holdouts/holdout-v1.json`, `holdout-v1-deepseek.json`.
- `evolve.py:976-994` validates `EVOLUTION_HOLDOUT_MANIFEST` before sweep, so unset would fail loudly. So holdout IS configured.

### Holdout DOES run
Private finalize cache at `${TMPDIR}/autoresearch-holdouts/<variant>/<lane>--finalize_result.json` contains real, complete holdout results. Example (v009 geo):

```json
{
  "variant_id": "v009",
  "suite_id": "holdout-v1-deepseek",
  "lane": "geo",
  "scores": {"geo": 4.7706, "composite": 4.7706, ...},
  "eligible_for_promotion": true,
  "reason": "holdout_passed",
  "evaluated_at": "2026-05-09T14:56:03.681634+00:00"
}
```

Plus full per-fixture `geo--holdout_result.json` (~6 KB) with aggregated suite metrics. So `_run_holdout_suite` runs, scores get computed, eligibility is decided.

### Where the data is lost

Only ONE place writes `holdout_metrics` in the entire codebase: `evaluate_variant.py:1616`, inside `_lineage_entry`. The single caller of `_lineage_entry` is `evaluate_search` (search-time), passing `holdout_ran=False`.

`evaluate_holdout` (line 2954) and `_write_finalize_result` (line 1996) NEVER call back into `_lineage_entry` or `append_lineage_entries`. The finalize path:

1. Computes `holdout_scores` via `_run_holdout_suite`
2. Decides `eligible` via `_holdout_eligibility`
3. Calls `_write_finalize_result(...)` which calls `_write_private_result(variant_id, "finalize", payload)` — payload lives in `/tmp/autoresearch-holdouts/<variant>/<lane>--finalize_result.json`
4. Returns. Never updates lineage.

`evolve.py:_do_finalize_step` (line 1774) → `_run_holdout(config, variant_dir)` → subprocess `python evaluate_variant.py --mode holdout ...` → `evaluate_holdout()` → same path. Lineage stays `{ran: false}` even when the variant was actually promoted (e.g., v009 above became the head for geo).

### Knock-on effects

- The v2 simplification plan's U10 gate (`holdout-v1 ≥ 4.5`) is **structurally unreachable** today: the lineage field it gates on is hard-coded to "didn't run."
- `evolve_ops._holdout_composite(entry)` at line 306 reads `entry.get("holdout_composite")` from lineage — always returns `None` for every entry, even when private cache has real numbers.
- The promotion code path at `_do_finalize_step` calls `promote_atomic` correctly (it consults the private finalize cache, not lineage's `holdout_metrics`), so promotion IS happening on real data — just lineage never reflects it.

## Three plausible failure modes from the plan, mapped

| Plan label | Status |
|---|---|
| 3a — `EVOLUTION_HOLDOUT_MANIFEST` unset, holdout silently skipped | NO. Manifest is set, validated, and `_smoke_test_judge_auth` runs. |
| 3b — Holdout runs but every fixture short-circuits with composite=0 | NO. /tmp cache shows v009 geo=4.7706, v010 competitive non-zero, etc. |
| 3c — Holdout result is computed but lost during lineage write | **YES.** Single-author write at line 1616 with `holdout_ran=False`; no second writer. |

## Fix design (Stream A A4)

Add a lineage-update step at the end of `evaluate_holdout` so the `holdout_metrics` block reflects what actually happened:

```python
holdout_metrics = {
    "ran": True,
    "suite_id": holdout_manifest["suite_id"],
    "lane": lane,
    "holdout_composite": _composite_from(holdout_scores),
    "secondary_holdout_composite": _composite_from(secondary_holdout_scores),
    "baseline_holdout_composite": baseline_composite,
    "eligible_for_promotion": eligible,
    "reason": reason,
    "evaluated_at": ...,
}
# Then update the existing lineage entry for this variant_id in-place,
# rewriting lineage.jsonl atomically.
```

Plus an invariant test: `tests/test_holdout_lineage_invariant.py` asserts that after `evaluate_holdout` completes successfully on a variant, the lineage entry for that variant has `holdout_metrics.ran == True` and `holdout_composite > 0`.

Gated by `AUTORESEARCH_EVAL_FIX_HOLDOUT=on` per plan §6.A4.
