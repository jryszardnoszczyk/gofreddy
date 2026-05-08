# Judge stability calibration — linkedin_engine

- Runs per draft: 3
- Drafts: 3
- Cross-item dimension: LI-6

**Verdict: FAIL** — dimensions ≥ 2.0 max variance: LI-1, LI-2, LI-3. Rewrite the rubric anchors before evolution.

## Per-dimension variance (primary judge)

Cross-item dim (the lane's last criterion) is reported separately below — its semantic axis is cohort-spread, not per-draft swing.

| dim | avg variance | max variance | drafts ≥ 2.0 |
|---|---:|---:|---:|
| LI-1 | 1.00 | 2.00 | 1 |
| LI-2 | 1.33 | 2.00 | 1 |
| LI-3 | 1.00 | 2.00 | 1 |
| LI-4 | 0.33 | 1.00 | 0 |
| LI-5 | 0.33 | 1.00 | 0 |
| LI-6 | — | — | (cross-item; see below) |

## Cohort-fit spread (LI-6)

Spread = max(score) − min(score) across drafts within one run. Tracks whether the anchor differentiates the cohort. Near-zero spread on a varied cohort suggests the anchor isn't seeing differentiation; high spread suggests it is.

- spread per run: [1.0, 0.0, 0.0]
- avg spread: 0.33
- runs with cohort signal: 3

## Judge-family agreement

| draft | primary avg | secondary avg | abs(Δ) |
|---|---:|---:|---:|
| case_study | 7.51 | 6.33 | 1.18 |
| short_take | 7.27 | 6.87 | 0.40 |
| thought_leader | 6.90 | 6.37 | 0.53 |
