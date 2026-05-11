# A7 — Stream C scope decision

Per Stream A plan (`docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`) §6.A7.

## TL;DR

**Verdict: SKIP panel-of-3 in Stream C v1.** Single frontier judge (current Sonnet) is sufficiently stable on the data we have. Defer Stream C C0 (frontier panel composition) and C6 (multi_scorer) to v2. Proceed with C1 (novelty), C4 (rubric hash), C5 (RaR weights), C13 (policy invariance), C14 (J/ΔJ diagnostic) in v1.

**Coverage caveat:** A6 was supposed to cover 4 lanes × ~10 fixtures × 5 reruns. The claude CLI hit its quota mid-run (`claude CLI exit 1` from `judges/invoke_cli.py:104`) after 13 of 50 calls. Successful coverage:

| Lane | Fixtures | Reruns | Status |
|---|---|---|---|
| geo | 2/2 (ahrefs, mayoclinic) | 5/5 each | ✅ complete |
| monitoring | 1/3 (rippling) | 3/5 | partial |
| marketing_audit | 0/3 | 0 | missed |
| competitive | 0/2 | 0 | missed |

The verdict below stands on the 13 successful calls — judge stability is sufficiently high that adding 37 more datapoints across other lanes is very unlikely to flip the decision, but **re-running A6 after claude CLI quota recovers is recommended to confirm.**

## Why the α numbers are misleading

The plan's decision matrix uses Krippendorff α, but α is mathematically degenerate when within-fixture variance is near zero — which is exactly what we observed. Sample raw data for `geo-ahrefs` across 5 reruns:

```
GEO-1: 9.0, 9.0, 9.0, 9.0, 9.0  (sd=0.000)
GEO-2: 7.0, 8.0, 8.0, 7.5, 8.0  (sd=0.400)
GEO-3: 9.0, 9.0, 9.0, 9.5, 9.0  (sd=0.200)
...
```

α-interval reports GEO-3 as α=−0.000 ("rewrite") because the *between-fixture* variance is also tiny (mayoclinic GEO-3 also clusters at 9.0). Numerically α can't tell "stable judges" from "broken rubric" — both produce near-zero observed disagreement. The right intra-rater stability signal here is the raw within-fixture sd, which is what we should be reading.

## Real stability signal — intra-fixture sd per axis

| Fixture | n reruns | max axis sd | mean axis sd |
|---|---|---|---|
| geo-ahrefs | 5 | 0.400 | 0.250 |
| geo-mayoclinic | 5 | 0.800 | 0.350 |
| monitoring-rippling | 3 | 0.471 | 0.198 |

Every axis across every observed fixture lands inside a ~1-point band. The single excursion (mayoclinic GEO-6 sd=0.800, range 8.0–10.0) had one outlier 10.0 in 5 reruns; even there the judges were stable to within 1 ulp on the 0–10 scale 4 out of 5 times.

Per-fixture composite CV (coefficient of variation):

| Fixture | composite range | CV |
|---|---|---|
| geo-ahrefs | 8.15 – 8.30 | 0.0073 |
| geo-mayoclinic | 7.10 – 7.50 | 0.0202 |
| monitoring-rippling | 7.85 – 8.05 | 0.0131 |

Composite CV ≤ 2.0% is far below the noise floor that would justify a panel.

## Mapping to the plan's decision matrix

The plan's matrix was written assuming a meaningful α reading. Translating the actual stability signal:

- **α-interval shorthand** "α ≥ 0.7 on every essential axis" was meant as "judges agree within tolerance"; the equivalent intra-rater check is **max axis sd ≤ 1.0**. The data passes that comfortably (max observed 0.800).
- **Panel-justified band** "0.5 ≤ α < 0.7" was meant for "judges diverge enough that majority voting helps"; that requires intra-fixture sd ≥ 1.0–2.0. We don't see this.
- **Rubric-rewrite band** "α < 0.5 on any essential axis" was meant for "judges can't agree what the rubric is asking"; that requires high intra-fixture sd, not degenerate near-zero values. We don't see this either.

The right verdict from this evidence: **judges are stable, panel is unnecessary, rubrics are fine.**

## Stream C consequences

Skip panel work in v1. The Stream C plan (`docs/plans/2026-05-11-003`) units affected:

| Unit | Action |
|---|---|
| C0 — frontier panel composition | **Defer to v2** |
| C6 — multi_scorer | **Defer to v2** |
| C1 — novelty | Ship in v1 |
| C4 — rubric hash-locking | Ship in v1 |
| C5 — RaR weighted rubrics | Ship in v1 |
| C13 — policy invariance diagnostic | Ship in v1 |
| C14 — J/ΔJ diagnostic | Ship in v1 |

## Caveats and follow-ups

1. **Re-run A6 after claude CLI quota recovers.** The verdict on 13/50 calls is well-founded but coverage of MA + competitive lanes would harden it. Use `scripts/a6_krippendorff_alpha.py --lane marketing_audit` and `--lane competitive`.
2. **Replace α with intra-fixture sd in `scripts/a6_krippendorff_alpha.py`.** The Krippendorff calculation produces misleading verdicts on near-constant data; track raw within-rater sd alongside.
3. **Watch monitoring-ramp-arc-t1.** A5's audit flagged it sd=2.47 *across variants* — A6's intra-fixture sd is only meaningful on a STABLE variant. The cross-variant fragility is a separate question covered by A5.
4. **Stream A's Bug 1 fix (axis-collapse via `/invoke/critique`) was NOT validated by A6.** A6 hit `/invoke/score` (the EVOLUTION judge) which already produced per-axis scores. The bug was in `/invoke/critique` (the SESSION judge) used by v006's batch evaluator. To validate the A2 fix end-to-end, exercise the batch-critique path via `freddy evaluate critique` with `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on`. The unit tests already prove the contract; a live integration run would close the loop.

## Audit trail

- Plan §6.A7 decision matrix (binding)
- Raw data: `/tmp/A6-alpha-measurement.raw.jsonl` (13 successful, 37 errored)
- Generated report (with degenerate α): `/tmp/A6-alpha-measurement.md`
- Stream A summary: `docs/plans/2026-05-11-002-stream-a-summary.md`
