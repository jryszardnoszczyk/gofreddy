---
date: 2026-05-13
phase: HANDOFF (post-audit reframe)
status: v2 spec invalidated by 5-agent audit; v3 reframe required
session_arc: 2026-05-12 morning → 2026-05-13 (~30hr work + 5-agent audit)
---

# Judge Design Deep Research — Pre-Compaction Handoff (v2 + audit findings)

This is the single canonical document for picking up where this session left off. Everything in the brainstorm dir is referenced here; this doc is the index + state-of-play.

## TL;DR — read this first

The v2 master spec was audited by 5 parallel agents on 2026-05-13. **The audit invalidated v2's premise.** Findings are in `audit-findings-2026-05-13.md` — read that BEFORE acting on v2.

Headline: existing judges produce 3-level scores (0/0.5/1) not 1-10 gradient; 66% of sessions emit identical feedback across all 8 criteria (judge broadcasts one verdict 8×); monitoring/competitive/storyboard rubrics are ceiling-bound. **Adding +14 criteria onto a substrate that doesn't use the existing 52 per-criterion is the wrong problem.** A Phase 0 substrate fix is now load-bearing.

Recommended kernel scope from the audit: **+5 evidence-backed criteria, not +14.** v3 reframe required before any `/ce:plan`.

## What we set out to do

JR's framing (verbatim): *"we should really figure out what's needed for each workflow and design optimal judges... the judges should be demanding."*

Driver: 2 flagship clients coming in 1-2 months (Klinika Melitus aesthetic dermatology Warsaw + DWF Poland law firm) need ship-eligible content output from gofreddy's evolution loop. Judges define what the loop optimizes toward; bad judges → bad output → demos fail.

Scope: redesign judge criteria across all 10 lanes (7 existing + 3 new from v1 content-engine-lanes brainstorm) + Polish statutory compliance regime.

## What got produced

**~85,000 words across 27 files** at `docs/brainstorms/2026-05-12-judge-design-deep-research/`. Two-version structure:

### v1 (over-built, preserved for history + v1.5 trigger conditions)
- `phase-a-lane-purposes.md` (lane purposes — still load-bearing)
- `phase-b-research/raw/<lane>.json` × 10 (580 X tweets pulled via twitterapi.io)
- `phase-b-research/<lane>.md` × 10 (calibration corpora, 25-32k words total)
- `phase-c-variant-ratings.md` (empirical findings — N=1-3 only)
- `phase-d-rubrics/<lane>.md` × 10 (per-lane full rubric specs, ~40k words)
- `phase-d-master-spec.md` (v1 synthesis, proposed +55 criteria)

### v1.5 review (the corrective)
- `adversarial-review.md` (hostile critique — sustained the central charge that research consensus ≠ empirical validation)

### v2 (the kernel — what should actually ship)
- `phase-d-master-spec-v2.md` (revised: +14 criteria, not +55)
- `HANDOFF.md` (this file)

## The headline finding

The adversarial review's central critique landed: I confused "research consensus across the 2026 web" with "evidence this evolution loop will produce better artifacts." 80% of v1's +55 criteria are inferred from external research, not validated on the existing loop's 180+ archived variants.

**v2 ships the validated 20% kernel: +14 criteria total, not +55.**

## v2 kernel — what ships

| Lane | Validated addition | Evidence |
|---|---|---|
| **monitoring** | MON-9 source faithfulness AUTO-CAP | Phase C identified as biggest current gap |
| **x_engine** | X-9 algorithmic-citizenship AUTO-CAP | Phase C: 3/3 archived drafts violate |
| **geo** | GEO-9 named-expert quoted attribution | Phase B: KDD 2024 +41% citation lift |
| **competitive** | CI-9 triangulation depth | Phase B practitioner consensus + 2026 research |
| **marketing_audit** | MA-9 decision-changing insight density | Distinct from existing MA-1; addresses boilerplate-audit failure mode |
| **storyboard** | SB-12 + SB-15 compliance preconditions | Gated on compliance rule content |
| **linkedin_engine** | LI-11 compliance precondition | Gated on compliance rule content |
| **article_engine** (new) | ART-1 hook + ART-2 argument coherence + ART-3 citation density + ART-8 compliance | Minimum-viable rubric |
| **image_engine** (new) | IMG-1 vision-judge hook + IMG-3 format compliance + IMG-5 AI-slop avoidance + IMG-8 compliance | Minimum-viable, vision-judge architecture |
| **ad_engine** (new) | ADE-1 hook + ADE-3 format compliance + ADE-4 LP coherence + cross-cutting compliance | LP coherence cross-artifact check is the innovation |

**Total: 14 new criteria** (10 with empirical or external-cliff evidence + 4 compliance preconditions content-gated on legal review).

## What got cut from v1 (deferred to v1.5)

41 criteria deferred. Each has a documented trigger condition for revival (see `phase-d-master-spec-v2.md` "Deferred to v1.5" table). Examples:

- All of monitoring MON-10/11/12/13 (Phase C confirmed rubric is at ceiling)
- All of geo's split-criteria + GEO-10/11/12 (geo regression is substrate, not rubric)
- Storyboard mode-conditional SB-9..15 (revisit after first Klinika + DWF fixtures)
- Article_engine ART-4 voice-fidelity rolling-window (design theater — 2σ threshold has no calibration; revisit at corpus ≥50K words)
- Image_engine IMG-2 (carousel arc), IMG-4 (brand consistency — no brand-style-guide yet), IMG-6/7 (hygiene)
- Ad_engine ADE-5 variant-diversity tuple-tag (judge-inflatable), ADE-2/6 (judge-fuzzy)
- voice_persona shared abstraction (gated on 2+ lanes needing it)
- brand-style-guide schema (gated on first Klinika brand-stamped artifact)

## Architectural decisions — final state

### Kept from v1
- **Shared compliance rule files** at `configs/compliance/{medical_pl,legal_pl}/rules.yaml` (correct in steady state)
- **Vision-judge architecture** for image_engine (extends `render_judge.py`, Gemini 2.5 Flash)
- **MA's JSON-envelope architecture** (deliberate divergence preserved)
- **"ONE quality" framing + WHY-before-WHAT + ground-truth cross-references** as observed best practices (NOT elevated to normative "design language" — that was v1's overreach)

### Revised in v2
- **AUTO-CAP only on deterministic checks**, not judge calls (v1 had 11 AUTO-CAPs; v2 has 5, all regex/Pillow-measured)
- **"Shape-only mode" REPLACED** with "substrate gates first" — when content isn't loaded, substrate refuses the fixture rather than judge abstaining the criterion. Fails loud.
- **Storyboard mode-conditional firing DEFERRED** (single 8-criterion rubric + SB-12/SB-15 compliance ones fire on fixture metadata)
- **Voice fidelity rolling-window DEFERRED** (no calibration; design theater per adversarial review)

### New in v2 (7 principles from adversarial review §6)
1. **Negative controls in every V-test** (cap false-positive rate ≤5% before promotion)
2. **Shadow-rubric mode for 4 weeks** (score both v007 + v008 rubrics in parallel)
3. **Cross-family agreement check per criterion** (extend `judge_calibration.py`)
4. **Cap precedence rules explicit** (AUTO-CAP at 1 > HARD FLOOR > composite cap)
5. **Score-distribution invariant** (σ(v008) ≥ 0.85 × σ(v007) on matched fixtures, or abort)
6. **Substrate gates first, judge criteria second** (replaces shape-only mode)
7. **Cost projection up-front** (~27% increase, not 100% as v1 implied)

## Realistic timeline (revised)

- **Phase 1 foundation (1 week)**: compliance rule schema, findings_brief contract, RUBRIC_VERSION hash extension, cap precedence in `evaluate_variant.py`
- **Phase 2 existing-lane kernel (1.5 weeks)**: MON-9 → X-9 → GEO-9 → CI-9 → MA-9
- **Phase 3 new-lane minimum-viable (1-2 weeks)**: article_engine + image_engine + ad_engine 4-criterion rubrics each
- **Phase 4 validation framework (1 week, concurrent)**: shadow-rubric, cross-family check, negative controls, score-distribution invariant

**Total: 4-6 weeks to demo-ready** (vs v1's claimed 6 weeks which baked in deferred work). Fits operator's 1-2 month window with buffer.

## What blocks implementation

1. **Operator approval of v2 kernel** — required before `/ce:plan`. Specifically: does cutting 41 criteria + deferring rolling-window + adopting 7 new principles look right?

2. **Compliance rule content** (Resolve-Before-Planning #2 from v1 brainstorm) — gated on legal-review owner + budget. Lanes don't evolve on Klinika/DWF until this lands. **Highest-priority operator task.**

3. **Dr. Maria + DWF partner consent for corpus ingestion** (Resolve-Before-Planning #1) — gates voice_persona (deferred to v1.5). NOT blocking v2 kernel.

4. **Foreplay reliability test** (Resolve-Before-Planning #4) — gates ad_engine optional C7 (deferred from v2). Low priority.

## File inventory — what to read next

### If you're picking this up cold, read in this order:

1. **`HANDOFF.md`** (this file) — orientation
2. **`audit-findings-2026-05-13.md`** — 5-agent audit invalidating v2 premise (~3,500 words, MOST IMPORTANT)
3. **`phase-d-master-spec-v2.md`** — superseded canonical spec (~5,000 words; read after audit)
4. **`adversarial-review.md`** — earlier critique that drove v1→v2 (~3,000 words)

### If you want to dig deeper:

4. **`phase-a-lane-purposes.md`** — what each lane is FOR (still load-bearing)
5. **`phase-c-variant-ratings.md`** — empirical findings (small N but real)
6. **`phase-d-rubrics/<lane>.md`** — per-lane v1 specs (kernel criteria lift cleanly; cut criteria stay archived)

### If you want the research substrate:

7. **`phase-b-research/<lane>.md`** × 10 — calibration corpora (research-grounded; preserved for v1.5 trigger conditions)
8. **`phase-b-research/raw/<lane>.json`** × 10 — 580 raw X tweets

### Cross-references outside the brainstorm dir:

- `docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md` — v1 client expansion brainstorm
- `docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md` — MA's master plan (deliberately divergent architecture preserved)
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` — 2,235 lines of MA lens research
- `autoresearch/judge_calibration.py` — shipped 2026-04-23 drift detection (v2 wires into this)
- `src/evaluation/rubrics.py` — current 52-criterion rubric (the kernel additions land here)
- `programs/marketing_audit/prompts/judges/MA-N-judge.md` × 8 — MA's external rubric files

## Memory entries (already saved)

- `~/.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/memory/project-judge-design-deep-research-2026-05-12.md`
- MEMORY.md index entry line 2 (v1 framing; needs v2 update post-compaction)

## Key learnings for future judge work

1. **Phase C empirical validation must come BEFORE Phase D criterion design**, not after. v1 had Phase C at N=1-3 because most archived variants either passed everything or hit structural-gate. Future work should compute composite-score distributions across the full archive *first*, then identify low-variance criteria (compressed → candidates to cut) and cross-family-disagreement criteria (judge-dependent → candidates to demote).

2. **Research consensus is not validation.** Phase B's 2026 web research was high-quality but produced inferred-from-research criteria, not validated-against-loop additions. The X-9 / MON-9 / GEO-9 pattern (specific known violations or external-cliff evidence) is the right shape; the "13-pattern research synthesis per lane" was overreach.

3. **AUTO-CAP only on deterministic checks.** Judge-call AUTO-CAPs (v1's ART-4 hard floor, IMG-5 aesthetic tells, LI-11 fuzzy compliance) fire on judge wording, not ground truth. Cap regime then becomes the rubric; quality criteria become decoration.

4. **"Shape-only mode" is credibility laundromat.** Don't ship criteria that abstain. If content isn't ready, substrate refuses fixture. Fails loud.

5. **The simplest-precedent test should bound spec scope.** gofreddy's own lanes 4-7 (geo/competitive/monitoring/storyboard) were added without 40,000-word master plans. v2 honors that precedent; v1 violated it 10×.

## Post-compaction continuation prompt

Use this verbatim to resume in a fresh session:

> Resume judge-design work per `docs/brainstorms/2026-05-12-judge-design-deep-research/HANDOFF.md`. Critical: read `audit-findings-2026-05-13.md` FIRST. The 5-agent audit on 2026-05-13 invalidated v2's premise (substrate emits 3-level scores + broadcasts one verdict across 8 criteria; rubrics ceiling-bound outside GEO). v2 spec at `phase-d-master-spec-v2.md` is preserved but superseded. Awaiting JR decision on v3 reframe: Phase 0 substrate fix (per-criterion scoring, 1-10 gradient, persist `dimension_scores` + `rubric_version` to scores.json) + +5 kernel (MON-9, MA-9, GEO-9, CI-9, X-9) + compliance hardcode-first + KILL Phase 3 (new lanes). If JR says "go," start Phase 0 by investigating `src/evaluation/judges/sonnet_agent.py` and `claude.py` for why per-criterion scoring collapses.

## Audit findings — what changed

5-agent audit on 2026-05-13. All findings in `audit-findings-2026-05-13.md`. Key shifts:

### v2 was wrong about
- **Adding +14 criteria.** Substrate doesn't use existing 52 per-criterion; adding more is decorative. **Cut to +5 evidence-backed kernel.**
- **Shape-only mode renamed to "substrate refuses fixture."** Still credibility laundromat under demo-deadline pressure. **Replace with hardcoded inline trigger lists per lane that needs them.**
- **4-week shadow-rubric mode.** 2× judge cost multiplier for hypothetical v007↔v008 frontier comparison that can't even be computed for new lanes. **Replace with one-shot archive replay.**
- **σ ≥ 0.85 invariant.** Wrong-directional: successful AUTO-CAPs *raise* σ, would misfire on the rollout it's meant to validate. **Defer.**
- **3 new lanes (article/image/ad).** Zero archived artifacts; 4 criteria × 4 variants × 30 generations can't calibrate. **KILL from demo window; revive when first 5 client deliverables produce ground truth.**
- **J/ΔJ paper citation.** Misapplied; paper supports calibration-drift detection, not cross-family κ. **Rewrite citation; use Rating Roulette + Preference Leakage for cross-family principle.**

### v2 was right about
- The +5 kernel (MON-9, X-9, GEO-9, CI-9, MA-9) survives. All have evidence (X-9 strongest at 3/3 Phase C; GEO-9 catches corpus-wide gap; CI-9 σ=2.2 on N=4).
- AUTO-CAP on deterministic checks only.
- Vision-judge architecture for image_engine (when image_engine actually runs).
- Phase A lane-purpose docs — load-bearing across both versions.
- Cap precedence rules (Principle 4) — pure documentation, ~20 LOC.

### What v2 missed
- The substrate is broken in ways nobody knew about. Three pathologies:
  1. 3-level scoring despite "gradient" declaration
  2. Identical-feedback broadcast across 8 criteria in 66% of sessions
  3. `rubric_version` never persisted to score rows
- Until these fix, every rubric-criterion change is invisible at the per-criterion level.

## v3 shape (recommended; awaiting JR)

- **Phase 0 NEW — substrate fixes** (~3-5 days; blocks everything): per-criterion scoring, 1-10 gradient output, persist `dimension_scores` + `rubric_version` to scores.json
- **Phase 1 REVISED — +5 kernel** (~5-7 days): MON-9, MA-9 (with explicit anchors), GEO-9 (with substrate hint), CI-9, X-9 (with corrected reach-penalty framing); citations rewritten per paper verification
- **Phase 2 REVISED — one-shot archive replay** (~1-2 days): not 4-week shadow mode
- **Phase 3 KILLED** from demo window: article/image/ad deferred to v1.5
- **Compliance REVISED**: hardcode inline `MEDICAL_PL_TRIGGERS` list (~30 LOC) when needed; no YAML schema until 2+ lanes need it
- **Principles**: KEEP 1/3/4/6/7; DEFER 2 (shadow) and 5 (σ invariant)

**Revised timeline: 2-3 weeks**, not 4-6. Saves 2-3 weeks against v2 estimate; leaves slack in 1-2 month demo window for legal-review + client deliverables.

## Current task state at audit

- Phase A: ✅ complete
- Phase B: ✅ complete (research corpora preserved; 4/5 cited claims verified)
- Phase C: ✅ complete (small N flagged in v1; re-rated at N=4-8 in audit)
- Phase D v1: ✅ complete (preserved)
- Adversarial review (v1→v2): ✅ complete
- Phase D v2: ✅ complete (SUPERSEDED by audit)
- 5-agent audit (2026-05-13): ✅ complete
- HANDOFF.md: ✅ this file (updated post-audit)
- **Awaiting**: JR review of audit findings + v3 reframe decision
- **Plan written**: `docs/plans/2026-05-13-001-judge-substrate-fix-and-kernel-plan.md` — 11 units across 3 phases, ~10-15 working days
- **Next action**: execute Phase 0 (U0.1 substrate investigation)

No code has been touched. Everything in this work stream lives in `docs/brainstorms/` and is reversible.
