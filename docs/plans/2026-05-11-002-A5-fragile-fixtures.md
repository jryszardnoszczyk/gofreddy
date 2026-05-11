# A5 — Fragile-fixture audit

Per Stream A plan (`docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`) §6.A5.

## Method

Scanned every `autoresearch/archive/v*/scores.json` for per-fixture composite
scores under `domains.<lane>.fixtures_detail.<fixture_id>.score`. Computed
population standard deviation per (lane, fixture_id) pair across observations.
Threshold: sd > 2.0 = "very fragile" (single fixture can flip a lane
composite by several points across variants).

## Findings

Seven fixtures exceed sd > 2.0. The first six all show `min = 0.00`, meaning
some variants completely failed to produce output for those fixtures — the
"fragility" is largely output-failure cold-start, not judge stochasticity.

| Lane           | Fixture                                  | n  | sd    | min  | max  |
|----------------|------------------------------------------|----|-------|------|------|
| competitive    | competitive-epic-ehr                     | 6  | 3.49  | 0.00 | 8.15 |
| geo            | geo-nubank-br-conta                      | 11 | 3.41  | 0.00 | 7.45 |
| geo            | geo-mayoclinic-atrial-fibrillation       | 12 | 3.36  | 0.00 | 7.95 |
| competitive    | competitive-figma                        | 6  | 3.36  | 0.00 | 7.85 |
| competitive    | competitive-patreon                      | 5  | 3.04  | 0.00 | 7.95 |
| geo            | geo-semrush-pricing                      | 12 | 2.75  | 0.00 | 7.90 |
| monitoring     | monitoring-ramp-arc-t1                   | 7  | 2.47  | 1.50 | 8.43 |

Healthy sibling fixtures for reference:

| Lane           | Fixture                                  | n  | sd    | min  | max  |
|----------------|------------------------------------------|----|-------|------|------|
| monitoring     | monitoring-lululemon-2026w12             | 7  | 0.70  | 6.62 | 8.85 |
| monitoring     | monitoring-rippling-firstweek            | 7  | 0.55  | 7.30 | 8.90 |
| monitoring     | monitoring-shopify-2026w12               | 7  | 0.44  | 7.38 | 8.62 |
| monitoring     | monitoring-ramp-arc-t0                   | 7  | 0.34  | 7.60 | 8.55 |

x_engine and linkedin_engine "angle" fixtures all show sd = 0.0 (every
observation is 0.0). They do not represent fragility — they represent a
different scoring shape (binary success aggregated upstream) and are not
included in the fragile set.

## Decision

The 7 fragile fixtures land in
[`autoresearch/lane_registry.FRAGILE_FIXTURES`](../../autoresearch/lane_registry.py).
With `AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on`,
`_aggregate_suite_results` excludes those fixtures from the lane composite
while keeping their scores in `fixtures_detail` for observability.
Default behaviour (flag unset) preserves the historical composite for
baseline comparability.

The plan considered "oversample to reduce leverage" as an alternative.
That doesn't help here because the failure mode is `min = 0` from variants
that produced no output — running the same fragile fixture 5× would just
yield 5× zero. Excluding is the conservative choice; reintroducing
specific fixtures after a root-cause fix is the follow-up.

## Reversibility

- `unset AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES` returns to the historical
  composite for the next run.
- `git revert <A5-commit>` removes the registry + the filter call site.
- The fragile set itself is a single frozenset in `lane_registry.py`;
  reintroducing one fixture is a one-line edit.

## Open follow-up

After Stream A's per-axis-collapse + holdout fixes land, refresh the audit
with the next sweep. The seven fragile fixtures may stabilise once the
underlying eval pipeline produces meaningful per-axis scores — at which
point the FRAGILE_FIXTURES set should shrink rather than grow.
