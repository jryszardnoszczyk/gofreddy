---
date: 2026-05-19
type: judge-redesign next-session brief (post-compact handoff)
parent_branch: design/judge-redesign-7-lanes
status: 8 v3+ specs design-complete + verified; awaiting JR decisions on code propagation + push + MA substrate-build
---

# Judge Redesign — Next Session Brief (Post-Compact 2026-05-19)

## Where we are

Branch `design/judge-redesign-7-lanes` (12 commits, NOT pushed to origin per safety protocol):

```
0608d9a v3 verification + 3 surgical fixes (CI v3.7, MA v3.1, X v3.1)
9e56e53 v3 surgical edits + 8 spot-check audits (Option D)
33fbb4a v2 comprehensive-scope restructure (School B)
8582aab Path 1: redundancy check v3.4
2e1c8b2 Path 1: variant_scorer wiring binary lanes
c4a1244 CI v3.4 code propagation (rubrics.py + structural.py)
7ecd752 Path 1: 3 healthcare fixtures
c4dc5ce Path 1: structural_gate 9-check expansion
fcca429 GEO + MA surgical restoration (cross-check folds)
ae34597 cross-check audit + 5-lane restoration
9b599c4 Path 1: CI v3.3 code implementation
4780a4e initial 7 v1 specs + design guide v2.1 + 40 research deliverables
```

## 8 lane specs — final state

| Lane | Spec version | Words | Verification verdict |
|---|---|---|---|
| CI | v3.7 | 13,618 | All 4 new issues resolved post-verification |
| GEO | v3 | 18,373 | APPROVE w/ 1 v4 candidate (healthcare reader) |
| MON | v3 | 12,635 | MOSTLY-CLOSED w/ Component D moat residual |
| SB | v3 | 12,509 | MATERIALLY RESOLVED (series-arc fix) |
| MA | v3.1 | 13,386 | §5 wrapper lag closed; dual-schema = v4 candidate |
| X | v3.1 | 14,512 | All numerical-weight leaks closed spec-wide |
| LI | v3 | 14,821 | CLOSURE 9/9 |
| SITE | v3 | 12,458 | VERIFIED ALL 7+5 (cleanest) |

Total: ~112k words of spec across 8 files. Plus 48 research deliverables under `docs/research/` (May-15 through May-19). Plus 8 v2 spot-check audits + 8 v3 verification reports under `docs/handoffs/`.

## Code state

- **CI v3.4 IS in live code** at `src/evaluation/rubrics.py` + `src/evaluation/structural.py`. RUBRIC_VERSION = `21476ca9d7e9`. 46 structural/rubric tests pass.
- **CI v3.5 → v3.6 → v3.7 deltas NOT yet in code**. Need to propagate the 3 v3.5-v3.7 changes (CI-4 imagine-prior fix + CI-6 internal-inconsistency-only + CI-3 4th example + §6a Goodhart-mode update + §8c 3-phase pipeline + first-cohort posture + substrate-readiness gate).
- **Other 7 lanes' code is on `fc99d64` / pre-Phase-4 baselines**. Specs are v3+ but `session_eval_*.py` workflows haven't been updated.
- Path 1 (separate Claude Code agent, launched from JR's clipboard prompt) shipped 4 commits independently to this same branch.

## What's iteration-complete

- ✅ 8 lane specs at design-complete + verification-clean
- ✅ All v1 + v3.4 surgical restorations preserved
- ✅ Comprehensive multi-component bundles (NOT scope-reduced)
- ✅ Substrate-readiness gating universal across all 8 lanes
- ✅ First-cohort overfitting posture universal across all 8 lanes
- ✅ Modern-lever bias (CUTS + ADDS) in §3 across all 8 lanes
- ✅ Design-guide §5 ≤5-ceiling preserved + documented exceptions (CI-6, GEO-6, SB-6, MON-5+MON-6)
- ✅ Cross-check audit + 5-lane surgical restoration committed
- ✅ 8 v3 verification reports committed
- ✅ 3 surgical post-verification fixes committed (CI v3.7, MA v3.1, X v3.1)

## What's NOT done (decisions for JR)

1. **Push branch to origin** — per safety protocol; needs explicit ask
2. **Code propagation for all 8 lanes** — recommended order:
   - CI v3.4 → v3.7 deltas (~30 min, ~$5)
   - Then 7 lanes in parallel (LI, SITE, SB, X, MON, GEO, MA) — each ~30-60 min, propagates rubric prose to `rubrics.py` + structural_gate basics. ~$200-300 total, ~1-2 hours parallel wall
3. **MA substrate-build** — separate workflow-engineering task. ~2-4 sprint-weeks. Builds `proposal.md` + `roadmap.md` + `cuts_reduces_adds.md` emission. Spec already handles this gracefully via v3.1 substrate-readiness gate (judge scopes findings.md only; doesn't downscore on missing files)
4. **Smoke test CI v3.7** — take one DWF/Anthropic/Perplexity fixture, run through CI v3.7 with `CI_STRUCTURAL_V33=1`, eyeball judge rationales. ~10 min, ~$5. This is the only thing paper review hasn't done.
5. **Empirical redundancy checks** per design guide §5 — deferred until first production cohort:
   - GEO-6 ↔ GEO-2 (predicted absorption)
   - MON-5 ↔ MON-1 (predicted absorption)
   - LI-3 ↔ LI-5 (predict r=0.4-0.6, keep both)
   - MA-1 ↔ MA-4 + MA-2 ↔ MA-3 (parallel watches)
   - CI-6 ↔ CI-2 (predicted absorption)
   - SB-3 ↔ SB-5, SB-1 ↔ SB-6, SB-4 ↔ SB-6
6. **Merge strategy** — branch has 12 commits + 60+ files. Squash to main? Long-lived branch? PR with review? Direct merge?
7. **v4 candidates** — documented residual risks per lane, not blockers:
   - MA 9-section vs 12-axis dual-schema (HIGH risk per verification)
   - GEO §1 healthcare substitute reader out-of-family (v4 candidate)
   - LI Components A-H multi-component preservation vs spot-check "ship A only" recommendation (intentional architectural call)
   - SB `supported_models.yaml` ops-ownership rot (unaddressed; v3.2 candidate)
   - X X-1 3-axis CoT attack-surface (intentional; observe in production)
   - CI client-validation gap for Components B-F (Phase 3 production observation will surface)

## Recommended resume-prompt for next session

```
Resume judge-redesign work from `docs/handoffs/2026-05-19-judge-redesign-next-session-brief.md`.

State: 8 v3+ specs design-complete + verified on branch design/judge-redesign-7-lanes (12 commits, NOT pushed). CI v3.4 in code; v3.5 → v3.7 deltas + 7 other lanes' code propagation pending.

READ FIRST:
1. This brief (judge-redesign-next-session-brief 2026-05-19)
2. CI v3.7 spec (docs/handoffs/2026-05-17-judge-design-step1-competitive.md)
3. Skim 7 other v3 specs + 8 v3 verification reports for context

PENDING DECISIONS:
- Push branch to origin?
- Full 8-lane code propagation (~$200-300, ~1-2 hours parallel)?
- 1-fixture CI v3.7 smoke test (~$5, 10 min)?
- MA substrate-build sequencing decision?
- Merge strategy (squash vs PR vs direct)?
- v4 candidates triage (defer or address now)?

DO NOT redo:
- 8 spot-check audits (committed under docs/handoffs/2026-05-19-{lane}-v2-spot-check.md)
- 8 v3 verifications (committed under docs/handoffs/2026-05-19-{lane}-v3-verification.md)
- Cross-check audit (committed under docs/handoffs/2026-05-18-judge-design-v1-cross-check.md)
- 48 research deliverables (committed under docs/research/2026-05-{15,16,17,18,19}-*.md)
- Substrate-readiness gating decision (locked across all 8 lanes)
- Cluster A/B/C routing rejection in MA (locked)
- School B multi-component bundle architecture (locked across all 8 lanes; substrate-gated)

Ask JR what to start with from the pending-decisions list.
```

## Hard constraints (preserved across all 8 v3+ specs)

- No σ-widening, no anti-gaming clauses, no framework-name embedding in criterion prose
- No feature-checking inside LLM judge — route verifiables to structural_gate
- Outcome questions with behavioral binary anchors required
- Per-criterion structured 3-step CoT (LI was collapsed 6→3 in v3)
- 0/0.5/1 scoring (no 1/3/5)
- Cross-family three-model panel (Opus 4.7 + GPT-5.5 + Gemini 3 Flash)
- Pointwise digest + pairwise promotion gate with position swap
- Reference-free (no model-authored exemplars)
- First-cohort overfitting watch — universal across all 8 lanes via §1 posture clause
- Comprehensive multi-component bundles preserved (Substrate-Readiness Gate via §1.5, NOT scope reduction)
- All v1 surgical restorations from `ae34597` + `fcca429` preserved
- All v3.4 surgical restorations from `c4a1244` preserved

## Three load-bearing lessons from this session arc

1. **Mechanical verification ≠ taste verification.** Structural checks (sections present, criteria count correct, hard constraints clean) said v1 was complete. Cross-check audit found 32 lost items from live code. Same pattern at v2→v3: structural-OK, taste-NEEDS-EDIT. Lesson: always run an adversarial spot-check on substantive design work; mechanical verification is necessary but never sufficient.

2. **"Looks elaborate" ≠ "over-engineered".** v1 was simplified to v3.1 on a good-faith over-engineering check; v3.2 restored the cuts after honest reflection that they were research-backed defenses. Each elaboration must defend against a documented failure mode with measured effect size — that's the discipline. Aggregate spec length is not the right metric.

3. **Comprehensive scope and substrate-readiness are different concerns.** Spec specifies the comprehensive target; substrate readiness gates client-side shipping. Conflating them produces either scope reduction (if substrate constrains spec) or empty production-default bundles (if spec leads substrate). Universal §1.5 Substrate-Readiness Gate resolves this.

## File inventory

Specs (8):
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (CI v3.7)
- `docs/handoffs/2026-05-18-judge-design-step1-geo.md` (GEO v3)
- `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` (MON v3)
- `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` (SB v3)
- `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` (MA v3.1)
- `docs/handoffs/2026-05-18-judge-design-step1-x-engine.md` (X v3.1)
- `docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` (LI v3)
- `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` (SITE v3)

Design guide:
- `docs/rubrics/judge-design-guide.md` (v2.1)

v2 spot-check audits (8):
- `docs/handoffs/2026-05-19-{competitive,geo,monitoring,storyboard,marketing-audit,x-engine,linkedin-engine,site-engine}-v2-spot-check.md`

v3 verification reports (8):
- `docs/handoffs/2026-05-19-{competitive,geo,monitoring,storyboard,marketing-audit,x-engine,linkedin-engine,site-engine}-v3-verification.md`

Cross-check audit (v1):
- `docs/handoffs/2026-05-18-judge-design-v1-cross-check.md`

SITE roadmap (extracted from v3):
- `docs/handoffs/2026-05-19-site-engine-roadmap.md`

Comprehensive-scope research (8):
- `docs/research/2026-05-19-{competitive,geo,monitoring,storyboard,marketing-audit,x-engine,linkedin-engine,site-engine}-comprehensive-scope.md`

Lane-axis research (29):
- `docs/research/2026-05-18-{lane}-{axis}.md`

Domain research (7):
- `docs/research/2026-05-15-judges-domain-{competitive,geo,monitoring,storyboard}.md`
- `docs/research/2026-05-18-judges-domain-{marketing-audit,x-engine,linkedin-engine,site-engine}.md`

Methodology research (4):
- `docs/research/2026-05-15-judges-methodology.md`
- `docs/research/2026-05-16-agentic-judges-methodology.md`
- `docs/research/2026-05-17-qualitative-judge-design-methodology.md`
- `docs/research/2026-05-18-judge-design-gaps-research.md`

Code (CI only):
- `src/evaluation/rubrics.py` (CI v3.4 — needs v3.5-v3.7 propagation)
- `src/evaluation/structural.py` (CI v3.3 9-check + v3.4 CI_BANNED_PHRASES + SOV-negation-filter)
- `autoresearch/lane_registry.py` (count parameter wired for binary lanes)
- `judges/evolution/agents/variant_scorer.py` (_BINARY_DOMAINS routing)
- `judges/evolution/prompts/scorer_binary.md` (v3.3 binary scoring template)

## TL;DR for the next session

8 v3+ specs are design-complete + verification-clean. Branch has 12 commits not pushed. CI is the only lane with code; 7 others need code propagation. MA has a separate ~2-4 sprint-week substrate-build dependency that's gracefully handled by the v3.1 substrate-readiness gate (judge scopes findings.md only until substrate catches up). The judge-design phase is functionally complete; the next phase is production/code work.
