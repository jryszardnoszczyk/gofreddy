# Judge stability calibration — x_engine

- Runs per draft: 3
- Drafts: 3
- Cross-item dimension: X-6

**Verdict: FAIL** — avg variance ≥ 3.0 on dims: X-4 (systematic drift). Rewrite the relevant rubric anchors before evolution.

## Per-dimension variance (primary judge)

Cross-item dim (the lane's last criterion) is reported separately below — its semantic axis is cohort-spread, not per-draft swing.

| dim | avg variance | max variance | drafts ≥ 2.0 |
|---|---:|---:|---:|
| X-1 | 1.33 | 2.00 | 1 |
| X-2 | 2.67 | 4.00 | 2 |
| X-3 | 2.00 | 3.00 | 2 |
| X-4 | 3.33 | 4.00 | 3 |
| X-5 | 2.00 | 3.00 | 2 |
| X-6 | — | — | (cross-item; see below) |

## Cohort-fit spread (X-6)

Spread = max(score) − min(score) across drafts within one run. Tracks whether the anchor differentiates the cohort. Near-zero spread on a varied cohort suggests the anchor isn't seeing differentiation; high spread suggests it is.

- spread per run: [2.0, 2.0, 0.0]
- avg spread: 1.33
- runs with cohort signal: 3

## Judge-family agreement

| draft | primary avg | secondary avg | abs(Δ) |
|---|---:|---:|---:|
| build | 5.68 | 5.77 | 0.09 |
| case-study | 4.33 | 5.17 | 0.83 |
| sharp | 5.17 | 6.47 | 1.30 |
