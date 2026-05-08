# Judge stability calibration — linkedin_engine

- Runs per draft: 3
- Drafts: 3
- Cross-item dimension: LI-6

**Verdict: PASS** — avg variance ≤ 3.0 on every scoreable dim, cross-judge abs Δ ≤ 1.5 on every draft. (info: dims with single-run max ≥ 2.0 — LI-1, LI-4 — within the empirical noise floor; rationales worth a glance for promotion-gate sensitivity tuning)

## Per-dimension variance (primary judge)

Cross-item dim (the lane's last criterion) is reported separately below — its semantic axis is cohort-spread, not per-draft swing.

| dim | avg variance | max variance | drafts ≥ 2.0 |
|---|---:|---:|---:|
| LI-1 | 1.67 | 3.00 | 1 |
| LI-2 | 0.67 | 1.00 | 0 |
| LI-3 | 0.67 | 1.00 | 0 |
| LI-4 | 0.67 | 2.00 | 1 |
| LI-5 | 0.00 | 0.00 | 0 |
| LI-6 | — | — | (cross-item; see below) |

## Cohort-fit spread (LI-6)

Spread = max(score) − min(score) across drafts within one run. Tracks whether the anchor differentiates the cohort. Near-zero spread on a varied cohort suggests the anchor isn't seeing differentiation; high spread suggests it is.

- spread per run: [0.0, 1.0, 0.0]
- avg spread: 0.33
- runs with cohort signal: 3

## Judge-family agreement

| draft | primary avg | secondary avg | abs(Δ) |
|---|---:|---:|---:|
| case_study | 7.57 | 6.90 | 0.67 |
| short_take | 7.20 | 6.47 | 0.73 |
| thought_leader | 7.07 | 6.40 | 0.67 |
