---
date: 2026-05-19
type: 7-lane code propagation smoke verdict
branch: design/judge-redesign-7-lanes
status: smoke complete — 16 fixtures across 7 lanes; CI + MON correctly wired binary; GEO/SB/MA/X/LI prose propagated but routing through legacy gradient template
---

# 7-Lane Smoke Verdict — Code Propagation Status

## Coverage

| Lane | Fixtures | Mean agg | Score span | Wiring status |
|------|----------|---------|-----------|---------------|
| CI (earlier smoke) | 5 | 6.86 | 0-1 binary | ✅ Binary routed |
| GEO | 3 | 5.59 | 1-9 gradient | ⚠️ Gradient (not in `_BINARY_DOMAINS`) |
| MON | 3 | 8.33 | 0/0.5/1 binary | ✅ Binary routed (added in commit e0ff046) |
| SB | 3 | 5.22 | 0-9 gradient | ⚠️ Gradient (not in `_BINARY_DOMAINS`) |
| MA | 3 | 4.52 | 0-9 gradient | ✅ By design (MA uses its own 0-10 prompt format) |
| X | 3 | 4.63 | 0-10 gradient | ⚠️ Routed through `scorer_templated.md` (gradient by design or by lack of binary-templated path?) |
| LI | 1 | 8.35 | 5-10 gradient | ⚠️ Same as X |

**Total**: 16 fixtures, all 7 lanes that have v3+ prose in code.

## Per-fixture scores (full matrix)

```
fixture                              | fam   | per-criterion scores            | agg
------------------------------------------------------------------------------------
CI (5 fixtures already smoked earlier — see docs/handoffs/2026-05-19-competitive-v2-spot-check.md)

geo-ahrefs                           | prima | 7 2 6 5 6 5 7 5                | 5.10
geo-ahrefs                           | secon | 8 2 7 5 5 4 6 3                | 5.00
geo-mayoclinic                       | prima | 8 9 8 9 9 7 9 7                | 8.00
geo-mayoclinic                       | secon | 8 7 8 7 8 6 5 7                | 6.95
geo-semrush                          | prima | 7 3 7 5 4 6 5 2                | 4.90
geo-semrush                          | secon | 8 1 6 4 3 5 1 1                | 3.60

monitoring-lululemon                 | prima | 0.5 1 1 1 0.5 0.5              | 7.50
monitoring-lululemon                 | secon | 0.5 1 1 0.5 0.5 0.5            | 6.67
monitoring-notion                    | prima | 1 1 1 1 0.5 0.5                | 8.33
monitoring-notion                    | secon | 1 1 1 1 0.5 0.5                | 8.33
monitoring-shopify                   | prima | 1 1 1 1 1 1                    | 10.00
monitoring-shopify                   | secon | 1 1 1 0.5 1 1                  | 9.17

storyboard-gossip_goblin             | prima | 8 8 7 7 8 5 8 5                | 7.00
storyboard-gossip_goblin             | secon | 8 9 8 8 9 6 8 7                | 7.90
storyboard-mrbeast                   | prima | 2 1 0 0 0 0 2 0                | 0.50
storyboard-mrbeast                   | secon | 2 1 0 0 0 0 2 1                | 0.70
storyboard-techreview                | prima | 8 7 7 7 7 7 6 5                | 6.80
storyboard-techreview                | secon | 9 9 8.5 9 9 8 7.5 7            | 8.40

marketing_audit-anthropic            | prima | 6 6 6 6 1 1 4 0                | 4.00
marketing_audit-anthropic            | secon | 5 7 5 5 6 4 8 3                | 4.80
marketing_audit-dwf                  | prima | 4 7 6 3 3 4 8 3                | 4.80
marketing_audit-dwf                  | secon | 6 7 5 3 5 7 8 2                | 5.40
marketing_audit-perplexity           | prima | 4 8 9 5 8 2 7 6                | 5.00
marketing_audit-perplexity           | secon | 3 1 1 4 4 6 7 1                | 3.10

x_engine-jr-a121                     | prima | 4 5 5 5 4 3 10                 | 5.10
x_engine-jr-a121                     | secon | 8 5 8 3 3 2 3                  | 4.60
x_engine-jr-a122                     | prima | 4 5 7 6 4 2 1                  | 4.00
x_engine-jr-a122                     | secon | 9 5 9 7 0 2 0                  | 4.10
x_engine-jr-a123                     | prima | 6 5 7 8 5 5 10                 | 6.00
x_engine-jr-a123                     | secon | 7 5 9 3 2 2 0                  | 4.00

linkedin_engine-jr-a121              | prima | 10 8 9 9 10 6                  | 8.70
linkedin_engine-jr-a121              | secon | 10 10 10 10 5 5                | 8.00
```

## Findings

### 1. Wiring gap confirmed across 5 lanes

GEO, SB, X, LI rubric prose has binary 0/0.5/1 anchors per their v3 specs. But the judge produces gradient scores (1-10) because:

- GEO + SB are not in `_BINARY_DOMAINS` in `judges/evolution/agents/variant_scorer.py` → routes through `scorer.md` (gradient)
- X + LI are in `_TEMPLATED_DOMAINS` → routes through `scorer_templated.md` (gradient with criteria injection)

The substrate doesn't break — it still consumes a 0-10 `aggregate_score` envelope, and judges still discriminate strongly. But binary-anchor discipline is NOT enforced at the criterion level.

### 2. MON correctly wired (only lane that did it)

The MON agent added `"monitoring"` to `_BINARY_DOMAINS` in commit `e0ff046`. Smoke confirms binary 0/0.5/1 scoring across all 3 fixtures.

### 3. MA uses its own 0-10 format by design

MA judge prompts are loaded from `programs/marketing_audit/prompts/judges/MA-{1..8}-judge.md` and have their own 0-10 envelope. Not the same wiring gap — this is by spec.

### 4. Judges discriminate well even under wiring gap

Despite gradient scoring, judges produce **strong empirical discrimination**:

- **SB mrbeast scored 0.6** (correctly identifying a weak storyboard — primary scores 2/1/0/0/0/0/2/0; secondary 2/1/0/0/0/0/2/1)
- **SB techreview scored 7.6** (correctly identifying a strong storyboard)
- **5-point spread** across SB fixtures = real discrimination
- **GEO mayoclinic 7.48 vs semrush 4.25** = 3.23-point spread
- **MA perplexity 4.05 vs dwf 5.10** = healthy distribution

### 5. MON shopify scored 9.585 — judges correctly rewarded a digest that demonstrated absence-as-signal pattern

This is the v3 MON-5 documented-exception criterion working as designed: when the monitor has zero captured data, naming that gap honestly IS the most important signal. Both primary and secondary scored MON-5 = 1.

### 6. CI + MON empirically validated production-ready

These two lanes have correct binary wiring + binary prose + healthy discrimination. The other 5 (GEO/SB/X/LI in code + MA by design) have correct prose but produce gradient outputs that the substrate consumes correctly.

## Recommendation

**Branch is ready to merge as-is.** The wiring gap is:
- Documented (this report + `docs/handoffs/2026-05-19-judge-aggregation-status.md` + `.tmp/wiring-fix-plan.md`)
- Non-breaking (substrate still works; judges still discriminate)
- A 1-2 hour follow-up (next-session task #84)

OR — keep branch open and apply the wiring fix in this branch before merging. Same final state; cleaner history.

JR decision: **merge tonight with documented wiring debt** vs **keep branch open + fix wiring next session + merge clean**.

## Files inventory

- Specs: `docs/handoffs/2026-05-1{7,8}-judge-design-step1-{lane}.md` (8 specs)
- Verification reports: `docs/handoffs/2026-05-19-{lane}-v3-verification.md` (8 reports)
- This smoke verdict: `docs/handoffs/2026-05-19-judge-7lane-smoke-verdict.md`
- Aggregation status: `docs/handoffs/2026-05-19-judge-aggregation-status.md`
- Wiring fix plan: `.tmp/wiring-fix-plan.md`
- Smoke artifacts: `.tmp/smoke-4lane-*.json` (16 files), `.tmp/smoke-rationales-*.json` (5 CI files from earlier)
- Code: `src/evaluation/rubrics.py` (CI/GEO/MON/SB/X/LI prose), `programs/marketing_audit/prompts/judges/*.md` (MA prose), `autoresearch/lane_registry.py` (MON 8→6), `judges/evolution/agents/variant_scorer.py` (MON added to binary), `tests/autoresearch/test_lane_registry.py` (MON assertion)

## Branch state

`design/judge-redesign-7-lanes` on origin at `bca11a0` + this commit (TBD on commit). 21 commits ahead of main.
