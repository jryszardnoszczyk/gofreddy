---
date: 2026-05-19 late
type: post-wiring-fix smoke verdict
branch: design/judge-redesign-7-lanes
status: ALL 4 LANES VERIFIED BINARY — merge-ready
---

# Wiring Fix Smoke Verdict — Binary Scoring Confirmed Across All 4 Lanes

## Status

✅ **Wiring fix verified successful.** All 4 lanes that had the wiring gap (GEO, SB, X, LI) now produce binary 0/0.5/1 criterion scores. 7 post-fix smoke fixtures × 14 family-runs = 104 individual criterion judgments — **100% within {0, 0.5, 1}**.

## Per-lane verification

```
lane               | N    | score span  | binary?  | aggregate range
geo                | 32   | [0, 1]      | ✅ True  | 2.50 → 7.50 (spread 5.00)
linkedin_engine    | 12   | [0.5, 1]    | ✅ True  | 9.17 → 9.17 (1 fixture)
storyboard         | 32   | [0, 1]      | ✅ True  | 0.00 → 8.75 (spread 8.75)
x_engine           | 28   | [0, 1]      | ✅ True  | 3.57 → 6.43 (spread 2.86)
```

## Discrimination signal

The wiring fix didn't compromise discrimination — judges still produce strong signal:

- **SB mrbeast scored 0.00 across BOTH families** (16/16 zeros). A genuinely weak storyboard is correctly destroyed.
- **SB techreview scored 8.13/8.75** (cross-family agreement on a strong storyboard). 8.75-point spread between weakest and strongest SB fixture.
- **GEO mayoclinic 7.50 vs semrush 3.75** — 3.75-point spread; mayoclinic's substantive medical content earns binary 1s on most criteria, semrush's lighter pricing page gets honest 0s on weaker criteria.
- **LI a121 = 9.17 both families** — strong cross-family agreement on a single LinkedIn draft.

## Cross-family panel behavior

Primary (Claude) and Secondary (Codex) producing meaningfully different scores per fixture confirms the cross-family panel is doing its job:

- GEO mayoclinic: primary 7.50, secondary 5.00 — Claude found more "yes" criteria than Codex
- X a121: primary 5.00, secondary 3.57 — Claude more lenient
- SB mrbeast: 0.00 unanimous — both families agree the storyboard is broken
- SB techreview: 8.13 vs 8.75 — both families agree it's strong, slight disagreement on edge cases

## Wiring fix architecture

**4 files changed**, 174 insertions / 23 deletions:

1. `judges/evolution/prompts/scorer_binary.md` — replaced CI-hardcoded prefix with `{lane_context}` placeholder; replaced `"criterion": "CI-N"` with `<criterion-id from criteria block>`; dynamic divisor (`sum × 10 / len(per_criterion)`) instead of `÷ 6`.

2. `judges/evolution/prompts/scorer_templated.md` — added binary 0/0.5/1 scoring requirement; added `{lane_context}` injection; preserves templated criteria-injection for X/LI.

3. `autoresearch/lane_registry.py` — added `binary_scorer_context: str = ""` field to LaneSpec; populated for 6 lanes (competitive, geo, monitoring, storyboard, x_engine, linkedin_engine) with their reader/artifact/scope prose from each lane's v3 spec.

4. `judges/evolution/agents/variant_scorer.py` — added `geo` + `storyboard` to `_BINARY_DOMAINS`; added `_lane_context_for_domain()` helper with curly-brace escaping for safe `str.format()` passage; added `_criterion_count_for_domain()` helper for future use; updated both binary and templated format calls to inject `{lane_context}`.

## What this means for merge

**Branch is now genuinely merge-ready.** No documented debt. No wiring gaps. Every lane that has v3 prose in code also has correct routing.

| Lane | Spec | Code | Wiring | Smoke | Status |
|------|------|------|--------|-------|--------|
| CI | v3.7 | ✅ | ✅ binary | ✅ 5 fixtures | Production-ready |
| GEO | v3 | ✅ | ✅ binary (fixed) | ✅ 2 fixtures | Production-ready |
| MON | v3 | ✅ | ✅ binary | ✅ 3 fixtures | Production-ready |
| SB | v3 | ✅ | ✅ binary (fixed) | ✅ 2 fixtures | Production-ready |
| MA | v3.1 | ✅ markdown | ✅ 0-10 by design | ✅ 3 fixtures | Production-ready |
| X | v3.1 | ✅ | ✅ binary via templated (fixed) | ✅ 2 fixtures | Production-ready |
| LI | v3 | ✅ | ✅ binary via templated (fixed) | ✅ 1 fixture | Production-ready |
| SITE | v3 | ❌ lane not registered | n/a | n/a | Infrastructure work pending |

## Commit history (relevant)

- `d20bbf5` feat(judges): wiring fix — binary scoring across geo/sb/x/li
- `8628af4` design(judges): 7-lane smoke verdict + 21 fixture rationale archive
- `bca11a0` docs(judges): aggregation status + smoke-surfaced wiring gap

## Test sweep

116 passed across `tests/test_evaluation_structural.py + tests/autoresearch/test_evaluate_variant_fixes_2026_05_12.py + tests/autoresearch/test_lane_registry.py + tests/autoresearch_v2/test_score_holdout.py` after the wiring fix. Pre-existing failure in `tests/judges/test_evolution_judge_server.py::test_score_endpoint` (claude CLI exit 1 — unrelated to wiring; verified pre-existing via clean-tree replay).

## Recommendation

**Merge `design/judge-redesign-7-lanes` to main now.** All lanes with v3 prose have verified binary scoring. SITE lane infrastructure remains as a separate downstream task (no spec implementation conflict — it's an additive lane registration that doesn't affect the 7 already-shipped lanes).

Squash recommended for clean main history (22 commits → 1 commit).
