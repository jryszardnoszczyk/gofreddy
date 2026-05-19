---
date: 2026-05-19
type: judge code propagation aggregation status
branch: design/judge-redesign-7-lanes (pushed to origin at HEAD 7daa693)
status: aggregation complete; smoke in flight; wiring gap surfaced
---

# Judge Code Propagation — Aggregation Status (2026-05-19 late)

## Commits aggregated on `design/judge-redesign-7-lanes` (20 ahead of main)

```
7daa693 design(judges): LI v3 prose propagation to rubrics.py
15a922a design(judges): X v3.1 prose propagation to rubrics.py
c6f23b4 design(judges): MA v3.1 prose propagation to judge prompts
e0ff046 design(judges): MON v3 prose propagation to rubrics.py
f7c69ea design(judges): GEO v3 prose propagation to rubrics.py
292c3b2 design(judges): CI v3.5→v3.7 prose propagation to rubrics.py
97ff22f docs(judges): next-session brief for post-compact handoff
0608d9a design(judges): v3 verification + post-verification surgical fixes (CI v3.7, MA v3.1, X v3.1)
9e56e53 design(judges): Option D surgical v3 edits across 8 lanes + 8 spot-check audits
33fbb4a design(judges): v2 — comprehensive-scope restructure across 8 lanes (School B)
8582aab feat(judges): CI v3.3 Task 1 — redundancy check across v3.4 6-criteria rubric
2e1c8b2 feat(judges): wire variant_scorer.py → deterministic structural_gate for binary lanes
c4a1244 feat(judges): CI v3.4 — propagate cross-check restorations into rubric + structural_gate
7ecd752 feat(eval-suite): CI v3.3 Task 4 — add 3 healthcare CI fixtures (non-Klinika)
c4dc5ce feat(structural): CI v3.3 — expand competitive structural_gate to 9 deterministic checks
fcca429 design(judges): GEO + MA surgical restoration — hybrid fold preserving both architectures
ae34597 design(judges): cross-check audit + surgical restoration of live-code prose (5 lanes)
9b599c4 feat(judges): CI v3.3 — outcome-question + binary-anchor rubric for competitive lane
4780a4e design(judges): 7-lane redesign — v1 specs + 40 research deliverables + design guide v2.1
```

## Lane-by-lane state

| Lane | Spec | Prose in code | Routing wired | Smoke result |
|------|------|---------------|---------------|--------------|
| CI | v3.7 | ✅ rubrics.py | ✅ `_BINARY_DOMAINS` | ✅ 5/5 fixtures green (earlier smoke) |
| GEO | v3 | ✅ rubrics.py (commit f7c69ea) | ❌ NOT in `_BINARY_DOMAINS` | ⚠️ Wiring gap surfaced |
| MON | v3 | ✅ rubrics.py (commit e0ff046) | ✅ Added in same commit | Pending |
| SB | v3 | ✅ via MON commit (parallel-agent overlap) | ❌ NOT in `_BINARY_DOMAINS` | Pending — expect wiring gap |
| MA | v3.1 | ✅ programs/marketing_audit/prompts/judges/ (commit c6f23b4) | n/a (kept 0-10 format) | Pending |
| X | v3.1 | ✅ rubrics.py (commit 15a922a) | ❌ NOT in `_BINARY_DOMAINS`, IS in `_TEMPLATED_DOMAINS` | Skipped (no v006 sessions) |
| LI | v3 | ✅ rubrics.py (commit 7daa693) | ❌ NOT in `_BINARY_DOMAINS`, IS in `_TEMPLATED_DOMAINS` | Skipped (no v006 sessions) |
| SITE | v3 | ❌ Lane not registered in `lane_registry.py` | n/a | Cannot smoke |

## The wiring gap

Each parallel agent (GEO, SB, X, LI) migrated rubric prose to binary 0/0.5/1 anchors per the v3 specs. None of them added their lane to `_BINARY_DOMAINS` in `judges/evolution/agents/variant_scorer.py`, so the judge service routes them through the legacy `scorer.md` template (gradient 1/3/5 + 0-10 envelope) — but the prose has binary anchors.

Result for GEO (smoke first fixture, geo-semrush-pricing):
- Primary scored: 7, 3, 7, 5, 4, 6, 5, 2 (gradient out of 10)
- Secondary scored: 8, 1, 6, 4, 3, 5, 1, 1 (gradient)

The judges produced gradient scores even though the rubric prose has binary anchors. The template wins.

**Root cause:** `scorer_binary.md` is hardcoded CI-specific:
- "competitive-intelligence brief"
- "800–2,000 words, Klue 5-section spine"
- "CB Insights triple scaffolding"
- `"criterion": "CI-N"`

Routing GEO/SB through it would mis-frame the lane. The proper fix is either:
1. Generalize `scorer_binary.md` (parameterize lane-specific language)
2. Create per-lane binary scorer prompts (`scorer_binary_geo.md`, etc.)
3. Use `scorer_templated.md` and make it binary-aware

## What was done tonight

1. CI v3.7 prose propagation (commit 292c3b2, 882 tests pass)
2. 5-fixture rescore-only smoke for CI v3.7 — clean (all 4 failure-mode tests resolved)
3. 6 parallel agents dispatched for the other 6 lanes (GEO/MON/SB/MA/X/LI)
4. All 6 agents committed prose changes on isolated worktree branches
5. Aggregated 6 commits onto `design/judge-redesign-7-lanes` via cherry-pick (1 cleanly skipped due to parallel-agent overlap)
6. Test sweep: 160 passed / 1 pre-existing failure
7. Pushed branch to origin
8. Smoke in flight: 4 lanes × 3 fixtures = 12 fixtures (GEO, MON, SB, MA)

## What's NOT done

1. **Wiring gap fix** for GEO + SB + X + LI: add to `_BINARY_DOMAINS`, generalize `scorer_binary.md` OR create per-lane binary scorer prompts
2. **X + LI smoke**: no v006 sessions on disk for these lanes (different artifact structure); would need fresh session generation
3. **SITE lane**: not registered in `lane_registry.py`; spec is design-complete but lane infrastructure doesn't exist
4. **SB independent commit**: SB's prose changes were absorbed into MON's commit due to parallel-agent worktree contamination (not blocking — content is correct, just attribution)
5. **Merge to main**: pending JR's call on merge strategy (squash recommended)

## Recommended next-session work

### Critical-path

1. Add `geo`, `storyboard` to `_BINARY_DOMAINS` (one-line change in `variant_scorer.py`)
2. Generalize `scorer_binary.md` to be lane-agnostic (replace "competitive-intelligence brief" with "{domain} {artifact}" + "Klue 5-section spine" with reference to lane-specific structural_gate)
3. Smoke GEO + SB again with corrected routing
4. Decide X + LI routing path (binary-templated vs binary-domain)

### Lower-priority

5. SITE lane infrastructure (lane_registry registration + workflow scaffolding) — separate ~1-2 day task
6. X + LI smoke (requires fresh session generation; ~$50 + 1-2 hr)
7. Generalized `scorer_templated.md` to support binary-aware scoring

## Key files touched tonight

- `src/evaluation/rubrics.py` — prose for CI, GEO, MON, SB, X, LI (all updated)
- `programs/marketing_audit/prompts/judges/MA-{1..5}-judge.md` — MA v3.1 prose
- `autoresearch/lane_registry.py` — MON entry reduced 8→6 rubrics
- `judges/evolution/agents/variant_scorer.py` — `_BINARY_DOMAINS` += `monitoring`
- `tests/autoresearch/test_lane_registry.py` — MON count assertion updated to 6
- `docs/handoffs/` — this status file + v3 verification reports from earlier work
- `.tmp/` — smoke artifacts (rationale files, manifests, scripts)

## Branch state (origin synced)

```
Branch: design/judge-redesign-7-lanes
HEAD: 7daa693
Ahead of main: 20 commits
Status: pushed to origin
```

## Three lessons from this aggregation arc

1. **Parallel agents in worktrees contaminate each other under high concurrency.** MON's commit absorbed SB's changes despite isolation flags. Use sequential agents or single-file edits with clear non-overlap when overlap risk is high.

2. **Prose-only propagation is incomplete without routing wiring.** Migrating rubric anchors from gradient to binary requires updating the scorer-prompt routing AND the binary scorer template's lane-agnosticism. The agents didn't catch this because the task framing said "Only rubrics.py."

3. **Pre-merge smoke catches what tests can't.** All tests passed after aggregation, but the smoke revealed the judge produces gradient scores when prose is binary but template is gradient. This is a behavioral check that unit tests don't replicate.
