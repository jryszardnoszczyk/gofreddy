# Judge stability calibration — x_engine

- Runs per draft: 3
- Drafts: 3
- Cross-item dimension: X-6

**Verdict: FAIL** — dimensions ≥ 2.0 max variance: X-1, X-2, X-3, X-4, X-5. Rewrite the rubric anchors before evolution.

## Per-dimension variance (primary judge)

Cross-item dim (the lane's last criterion) is reported separately below — its semantic axis is cohort-spread, not per-draft swing.

| dim | avg variance | max variance | drafts ≥ 2.0 |
|---|---:|---:|---:|
| X-1 | 1.00 | 2.00 | 1 |
| X-2 | 2.00 | 4.00 | 2 |
| X-3 | 3.33 | 4.00 | 3 |
| X-4 | 2.67 | 5.00 | 2 |
| X-5 | 2.33 | 4.00 | 2 |
| X-6 | — | — | (cross-item; see below) |

## Cohort-fit spread (X-6)

Spread = max(score) − min(score) across drafts within one run. Tracks whether the anchor differentiates the cohort. Near-zero spread on a varied cohort suggests the anchor isn't seeing differentiation; high spread suggests it is.

- spread per run: [0.0, 0.0, 2.0]
- avg spread: 0.67
- runs with cohort signal: 3

## Judge-family agreement

| draft | primary avg | secondary avg | abs(Δ) |
|---|---:|---:|---:|
| build | 5.90 | 6.03 | 0.13 |
| case-study | 4.53 | 5.20 | 0.67 |
| sharp | 5.30 | 6.60 | 1.30 |
