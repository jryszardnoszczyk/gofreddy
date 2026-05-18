---
date: 2026-05-18
type: next-session brief (judge-design — propagation to 7 remaining lanes)
status: open for next dedicated session
supersedes: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
parent_session: completed CI v3.3 design end-to-end via Path-A iteration + 4 deep-research passes + honest reflection cycle
---

# Judge Design — Next Session Brief (Propagation to 7 Lanes)

## TL;DR

CI lane is DESIGN-COMPLETE at v3.3. Implementation + validation pending. The next session should:
1. Read the canonical docs (see Resume Prompt below)
2. **Validate CI v3.3 empirically OR begin propagation to 7 other lanes** — JR's call, both paths sketched below
3. If propagating: dispatch lane-customized deep research (NOT mechanical 4-question template repeat) per lane, then Path-A iterate each

## State at end of this session

### CI lane — DESIGN COMPLETE (v3.3)

Spec: `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (v3.3, ~4500 words)
- Reader / §1.5 Artifact-shape (LOCKED) / Success / Failure (3 mediocre modes + Phase 4 + AI-specific surfaces) / 6 criteria with up-to-3 vertical examples each + structured 3-step CoT + 0.5-unknown anchor / Goodhart-resistance verification / structural_gate expansion list (9 added checks)
- 5 vertical examples across criteria: legal / AI-lab / healthcare / fintech / B2B-SaaS — first-cohort overfitting reduced in v3.3
- CI-6 evidence-chain documented as ≤5-ceiling exception; expected to absorb into CI-2 via redundancy check

### Research deliverables (7 docs, all complete)

Methodology (3 passes):
- `docs/research/2026-05-15-judges-methodology.md` — single-shot fundamentals (MT-Bench, G-Eval, TrustJudge, PoLL, ICRH, Evolution-without-Oracle)
- `docs/research/2026-05-16-agentic-judges-methodology.md` — collapses to "stay single-shot, route verifiables to structural_gate"
- `docs/research/2026-05-17-qualitative-judge-design-methodology.md` — prescriptive design SOTA; load-bearing answer: outcome-questions-not-feature-checks is supported (RaR +31%, OpenRubrics +8.4%, Rubrics-as-Attack-Surface 27.9pp drift on feature-shaped)
- `docs/research/2026-05-18-judge-design-gaps-research.md` — gap-closure pass; 7 of 10 May-17 uncertainties graduated to prescriptions

Domain research (8 lanes):
- `docs/research/2026-05-15-judges-domain-competitive.md` (generalist CI)
- `docs/research/2026-05-15-judges-domain-geo.md` (Aggarwal KDD 2024 + Volpini + Shepard)
- `docs/research/2026-05-15-judges-domain-monitoring.md` (Cision React Score + Coombs + Sandman + AMEC + FAA AD)
- `docs/research/2026-05-15-judges-domain-storyboard.md` (MrBeast handbook + Pixar 22 + Casey Neistat + Johnny Harris)
- `docs/research/2026-05-18-judges-domain-marketing-audit.md` (Sean Ellis + Balfour + Lenny Rachitsky + McClure + Tunguz + Dunford + Campbell + Simmonds)
- `docs/research/2026-05-18-judges-domain-x-engine.md` (algorithm Jan-2026 open-source + Welsh + Cole/Bush + Naval + Bloom + Mack + Veerasamy + Hormozi)
- `docs/research/2026-05-18-judges-domain-linkedin-engine.md` (Van Der Blom Algorithm InSights + Welsh + Acosta + Alić + Denning + Meer + Edelman)
- `docs/research/2026-05-18-judges-domain-site-engine.md` (CXL + Dunford + Balfour + Marketing Examples + Aggarwal extended)

CI-specific deep research (4 passes):
- `docs/research/2026-05-18-ci-vertical-conventions.md`
- `docs/research/2026-05-18-ci-artifact-taxonomy.md`
- `docs/research/2026-05-18-ci-ai-failure-modes.md`
- `docs/research/2026-05-18-ci-decision-format-mapping.md`

### Design guide

`docs/rubrics/judge-design-guide.md` — v2.1 (with documented-exception clause in §5 for justified breach of ≤5 ceiling). Canonical reference for all judge design across all 8 lanes.

### Other 7 lane specs (v0 drafts only — UNVALIDATED, MAY HAVE OVERFITTING)

- `docs/handoffs/2026-05-18-judge-design-step1-geo.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-x-engine.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` (v0)

**These are skeleton drafts written before the CI v3.3 deep-research pattern was developed.** They follow the design-guide format but have NOT been through Path-A iteration with JR, deep-research passes, or first-cohort-overfitting reduction. Treat them as starting points, not validated specs.

## Three load-bearing lessons from this session (apply to all 7 propagations)

### Lesson 1: Outcome-questions-not-feature-checks IS literature-backed

Supported by RaR (arxiv 2507.17746, +31% HealthBench), OpenRubrics (arxiv 2510.07743, +8.4% RewardBench), Rubrics-as-Attack-Surface (arxiv 2602.13576, 27.9pp drift on feature-shaped under selection pressure). With one caveat: vague outcome prose collapses to central-tendency bias (arxiv 2506.22316) — must be paired with concrete behavioral binary anchors. Do NOT propagate without this discipline.

### Lesson 2: "Looks elaborate" ≠ "over-engineered"

This session burned a cycle where v3 was simplified to v3.1 on JR's good-faith over-engineering check, then restored to v3.2 after honest reflection that the cuts removed research-backed defenses. The honest verdict: each deterministic check in structural_gate is a thin defense against a documented failure mode (URL HEAD vs dead links, quote-grep vs Perplexity-37% fab rate, entity-existence-lookup vs GPT-4o 19.9% citation-fab). Cutting them shifts brittleness to a layer that can't do the work (the judge can't do deterministic verification).

**The over-engineering check is still valid.** Apply it per elaboration: does this correspond to a documented failure mode with a measured effect size? If yes, keep. If no, cut. Don't trim by aggregate spec length.

### Lesson 3: First-cohort overfitting is a real risk

The CI deep research targeted legal (DWF) / AI-lab (Anthropic, Perplexity) / healthcare (Klinika) because those are first-cohort fixtures. v3.3 broadened beyond that to defend against client-mix expansion. **Apply the same discipline when designing the other 7 lanes:** choose vertical anchors that are STRUCTURALLY DIVERGENT in each lane's evidence substrate, not just the verticals where current fixtures live. Per JR's memory: gofreddy is a generic AI-native agency targeting tech-savvy founder/early-co clients; first-cohort is concrete anchor, not architectural target.

## Two paths forward — JR's call

### Path 1: Validate CI v3.3 empirically before propagating

Pro: confirms the format works before 7× investment in propagation
Con: ~2 week serial bottleneck before other lanes start

Steps:
1. **Redundancy check** (~$35, ~30 min) — 5 fixtures × 6 criteria × 3 panel models = ~90 calls. CI-2 ↔ CI-6 most-likely-to-merge pair. Will tell empirically if CI-6 absorbs.
2. **Fixture validation** — run 5 existing CI fixtures (DWF / Anthropic / Perplexity + ≥1 Klinika-class if available) through locked criteria; eyeball judge rationales for human-reasoning match. Surface findings before propagating.
3. **structural_gate code implementation** — 9 added checks: URL HEAD + quote-grep + entity-existence lookup + "as of" date + ≥1 cited source <90 days + word-count band + Klue 5-section presence + CB Insights triple presence + comparison-structure. Entity-existence is highest operational cost; can be implemented last but don't skip.
4. **Implement v3.3 prose** into `autoresearch/archive/v006/workflows/session_eval_competitive.py` CRITERIA dict + judge-prompt wrapper.
5. **Build 2–3 Klinika-class healthcare fixtures** (current coverage is thin).
6. Observe live behavior over 3–5 generations.
7. THEN propagate Path-A + customized deep research to other 7 lanes.

### Path 2: Propagate deep research to all 7 lanes in parallel NOW

Pro: all 8 lanes designed within ~1 week wall time
Con: ~$300–420 research cost; if CI v3.3 has unidentified issues, propagates them

**CRITICAL: do NOT mechanically apply CI's 4 deep-research questions to all 7 lanes.** Each lane has its own load-bearing questions. Suggested customization (revise per JR direction):

| Lane | Vertical conventions | Artifact taxonomy | AI failure modes | Decision-to-format | Lane-unique questions |
|---|---|---|---|---|---|
| GEO | Yes (industry-specific AEO) | Some (page-type) | **Critical** (AI engines ARE the reader) | Less | Dual-audience tension; Aggarwal-method-by-domain |
| MON | Yes | Settled (weekly digest) | Yes | Less | Compound-narrative detection; absence-as-signal |
| SB | Less (creator not industry) | Settled (story plan) | Yes + AI-video-model | N/A | Creator-voice fidelity; pattern-data cold-start; AI-video-model capability awareness |
| MA | Yes (industry-specific) | Yes (audit-shape by stage) | Yes | **Yes (audit-by-stage)** | Fractional-CMO 30/60/90; upstream-vs-marketing diagnostic |
| X | Less (platform-specific) | Settled | **Critical** (AI-slop) | N/A | Algorithm Jan-2026 signals; Cole/Dickie hook discipline; account-voice screenshot test |
| LI | Less | Settled | **Critical** (LinkedIn AI-slop + broetry) | N/A | Van Der Blom Depth Score; comment-seed quality; author-context coherence |
| Site | Yes | Already in May-18 research | Yes | Less | Dual-audience tension; CXL hero audit; existing site-quality.md retirement plan |

Per-lane research dispatch:
- 3–4 agents per lane × 7 lanes = 21–28 agents total
- Cost: $15 × ~25 = ~$375
- Time: ~30 min wall per agent (all parallel)

After research returns per lane:
- Path-A iterate with JR on Reader / Success / Failure / Criteria (each lane's 4-section iteration)
- Apply first-cohort-overfitting reduction
- Document justified-exception breaches if any lane has its own AI-failure surface needing CI-6-equivalent criterion

**Recommended: Path 1 (validate CI first), then Path 2.** But JR's call.

## Resume Prompt for Next Session

```
Resume judge-design propagation work from `docs/handoffs/2026-05-18-judge-design-next-session-brief.md`.

State: CI lane v3.3 is DESIGN-COMPLETE. Implementation + validation pending.
Other 7 lanes have v0 skeleton drafts that pre-date the CI deep-research pattern.

READ FIRST (in order):
1. This brief (next-session brief 2026-05-18)
2. The design guide: docs/rubrics/judge-design-guide.md (v2.1)
3. The CI v3.3 spec: docs/handoffs/2026-05-17-judge-design-step1-competitive.md
4. Skim the 7 other lane v0 specs to know what's there
5. Memory entry: project-judge-design-ci-v3.3-complete-2026-05-18.md

THREE LOAD-BEARING LESSONS to apply across all propagations:
- Outcome-questions-not-feature-checks IS literature-backed (RaR +31%, OpenRubrics +8.4%, Rubrics-as-Attack-Surface 27.9pp)
- "Looks elaborate" ≠ "over-engineered" — judge each elaboration against a documented failure mode
- First-cohort overfitting is a real risk — don't anchor specs on DWF/Klinika/Anthropic only

DECISION POINT on session start:
- Path 1: validate CI v3.3 empirically (redundancy check + fixture validation + code implementation) before propagating
- Path 2: propagate deep research to all 7 lanes in parallel NOW (cost ~$375, ~1 week wall)

JR's preference TBD — ask if not stated in opening message.

If Path 2: dispatch lane-customized deep research per the table in §"Path 2" of this brief. NOT mechanical 4-question repeat. Per-lane unique questions matter.

HARD CONSTRAINTS (unchanged from May-15 brief):
- No σ-widening, calibration-driven prose, anti-gaming clauses
- No feature-checking in rubric prose (route verifiables to structural_gate)
- No framework-name embedding in rubric prose
- No "smoke testing the prose" (variance-adjacent measure-and-tune)
- Outcome questions with behavioral binary anchors are required, not optional
```

## Files inventoried

Spec docs (8 lanes):
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (v3.3 COMPLETE)
- `docs/handoffs/2026-05-18-judge-design-step1-geo.md` (v0 — needs Path-A + deep research)
- `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-x-engine.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` (v0)
- `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` (v0)

Design guide: `docs/rubrics/judge-design-guide.md` (v2.1)

Live rubric (UNCHANGED — v3.3 NOT YET IMPLEMENTED):
- `autoresearch/archive/v006/workflows/session_eval_competitive.py` — still on commit `ce386b8` (14 judge rewrites from `fc99d64`)
- Other 7 lane `session_eval_*.py` files — still on their `fc99d64` / pre-Phase-4 baselines

## What NOT to do next session

- Do NOT mechanically apply CI's 4-question deep-research template to all 7 lanes — each lane needs lane-customized questions
- Do NOT default to legal/AI-lab/healthcare vertical anchors for non-CI lanes — pick verticals divergent in each lane's evidence substrate
- Do NOT cut research-backed defenses on "over-engineering" reflexes — judge each elaboration against documented failure modes
- Do NOT ship spec to v006/workflows code without redundancy check + fixture validation first
- Do NOT skip the first-cohort-overfitting watch in §8 of CI v3.3 or its equivalents in other lanes
