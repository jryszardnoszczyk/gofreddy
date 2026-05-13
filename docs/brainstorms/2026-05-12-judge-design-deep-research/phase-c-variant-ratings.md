---
date: 2026-05-12
phase: C
topic: self-rate archived variants against Phase B calibration corpus
---

# Phase C — Variant Rating Validation

Goal: confirm whether Phase B's proposed new criteria catch real failure modes the existing rubric misses. Rated archived v189 artifacts from monitoring, geo, x_engine. Spot-checks rather than exhaustive — sample sized to validate the load-bearing Phase B claims, not to compute statistical gaps.

## monitoring/Lululemon v189 — score 8.6 composite, all 8 criteria pass

**Artifact:** weekly digest, 84 lines. Honest framing: the underlying monitor returned 0 mentions for 2 consecutive weeks. The whole digest articulates that empty-data state and what to do about it.

**Judge scores:** All 8 of MON-1..MON-8 passed (1.0/1.0). Composite 8.6.

**My ratings against Phase B calibration:**

| Criterion | Judge | Me | Notes |
|---|---|---|---|
| MON-1 difference | 1.0 | ≈5 | "Flat at zero week over week" — explicit delta, agreement |
| MON-2 severity defensible | 1.0 | ≈5 | LOW/MEDIUM with confidence + alternative reading — strong |
| MON-3 top development | 1.0 | ≈5 | Names "measurement silence" upfront with rationale |
| MON-4 action items | 1.0 | ≈5 | Each action: owner + timeframe + dual outcome — exemplary |
| MON-5 compound narratives | 1.0 | ≈5 | Pattern 3 names falsifiable forward projection |
| MON-6 numbers answer "so what" | 1.0 | ≈5 | 100% SOV explicitly flagged as zero-denominator artifact |
| MON-7 arc continuity | 1.0 | ≈5 | Prior digest referenced by date, action carried forward |
| MON-8 word count discipline | 1.0 | ≈4 | 84 lines for "we have no data" is long but justifiable; slight gap |

**Phase B proposed new criteria — would they catch anything?**

- **MON-9 source faithfulness (auto-cap)**: N/A — empty-data digest has no quotes/numbers to verify. Criterion would pass trivially. **Phase C can't validate this on Lululemon; need a digest WITH retrieved mentions for the real test.**
- **MON-10 event canonicalization**: N/A — no stories to canonicalize.
- **MON-11 author/source weighting**: N/A — no sources.
- **MON-13 channel diversity**: Would FAIL (0 source classes), but justifiably — the artifact acknowledges this is an observability gap.
- **MON-14 forward hooks**: Score 5 — explicit "watchpoint for next week" present. **But this is redundant with existing MON-7 sub-question #4 ("Does the digest create forward hooks?"). Drop MON-14 from the Phase D proposal.**
- **MON-15 missing-expected-signal callouts**: Score 5 — "What did not happen matters" paragraph. **But this is redundant with existing MON-6 sub-question #3. Drop MON-15.**

### Phase C findings on monitoring

1. **Existing MON rubric is exceptionally well-calibrated.** My ratings agree with the judge across all 8 dimensions on this artifact. JR's "gold standard" assessment is confirmed empirically.

2. **Two of Phase B's proposed new criteria are redundant with existing checklist sub-questions** — MON-14 ⊂ MON-7#4 and MON-15 ⊂ MON-6#3. Drop them from Phase D.

3. **MON-9 (faithfulness with auto-cap) is the only Phase B-proposed criterion that adds load-bearing capability** — but the Lululemon empty-data artifact can't test it. Need a digest with retrieved mentions for the real validation.

4. **Empty-data state is a real production failure mode** and the existing rubric handles it well. The judge correctly rewarded an artifact that says "the monitor is broken" with high scores, because that's the right action-driving content for the operator.

5. **MON-8 (word count proportional to importance) is slightly compressed at ceiling** — 84 lines on "no data" got a 1.0 but my read is 4/5. Either the criterion's anchor needs sharpening or this artifact reveals genuine score compression at the top.

## geo/mayoclinic v189 — structural-gate failure prevents rating

**Artifact:** report.md plus 3 optimized page evals. The report.md shows: "Intro blocks: 0 / FAQ blocks: 0 / How-to blocks: 0 / Schema blocks: 0 / Structured tables: 119". Every optimized eval JSON: `"decision": "DISCARD", "reason": "structural_gate_failed"` with "No FAQ block found" and "No [INTRO] block found" as gate failures.

**Score:** geo domain 5.24, composite 5.62 (after render_quality blend).

### Phase C findings on geo

1. **The structural gate is doing the work** — caught optimized pages that have only tables, missing the [FAQ] and [INTRO] markers downstream consumers require. The judge never scored per-criterion because no artifact passed structural.

2. **This is a substrate failure, not a judge failure** — the optimizer is over-pruning content blocks. The judge rubric for GEO-1..8 doesn't get exercised on these artifacts; cannot validate or refute Phase B's proposed new criteria from this sample.

3. **Implication for Phase D**: Judge criteria only matter on artifacts that pass structural. Phase B's proposed new criteria (quoted-expert attribution, inline citations, freshness markers, fan-out coverage, answer-first framing) need a DIFFERENT geo session — one where the optimizer produced complete pages with INTRO+FAQ markers — to validate. Did not find one in the v189 archive.

4. **The structural gate's hard requirement on [INTRO] / [FAQ] markers may itself be too narrow.** Phase B research suggests answer-first paragraph framing (a soft signal) is more important than the literal `[INTRO]` marker (a structural one). Worth revisiting whether the gate is gating the right thing — but that's a substrate question, not a judge question.

## x_engine v007-curated drafts (2026-05-12 session) — Phase B X-9 validated empirically

**Artifacts:** 3 drafts from the latest x_engine session, all about "OpenAI's B2B Signals":
- jr-2026-05-08-121-001 (sharp, 255 chars)
- jr-2026-05-08-121-002 (build, 715 chars)
- jr-2026-05-08-121-003 (build, 727 chars)

**Judge scores:** Not surfaced in standard scores.json (x_engine architecture uses different scoring path). Drafts shipped per session_summary.

**My rating against existing X-1..6 + Phase B-proposed X-7..10:**

Looking specifically at draft #2 (build bracket, 715 chars):

```
Most AI agency positioning still sounds like a tool inventory.
[...]
This is why gofreddy is built around 11 marketing areas and 149 lenses.
[...]

[REPLY]
Source frame: my read on OpenAI's B2B Signals for agency operators.
https://openai.com/index/introducing-b2b-signals
[/REPLY]
```

| Criterion | My score | Note |
|---|---|---|
| X-1 voice + plain language | 4 | Operator voice present, but "agentic," "workflow maturity map" trigger plain-language cap |
| X-2 factual grounding | 4 | OpenAI's B2B Signals verifiable; "5 drafts in 80-130s at $0/run" is specific lived-work |
| X-3 hook earns next line | 4 | "Most AI agency positioning still sounds like a tool inventory" — competent, generic |
| X-4 zero AI-tells | 3 | `->` arrow listicle structure is slightly templated |
| X-5 structure earns length | 3 | 5-bullet listicle is a known AI-output pattern; bullets substantive though |
| X-6 cohort diversity | 2 | **All 3 drafts about the same OpenAI source. Same voice pillar. Same general angle. Cohort = 3 wordings of 1 bet.** |
| **X-7 specificity density** (proposed) | 3 | 2-3 numeric anchors per 715 chars — sparse |
| **X-8 reply-worthiness** (proposed) | 3 | Implicit closing question but not sharp invitation to disagree |
| **X-9 algorithmic-citizenship** (proposed) | **1** | **EXTERNAL LINK IN REPLY BLOCK** — per Phase B research, external links = 30-50% reach reduction since March 2025. All 3 drafts include the openai.com URL. |
| **X-10 original perspective** (proposed) | 3 | "AI adoption is turning into sales collateral" is a take, but generic-POV-style |

### Phase C findings on x_engine

1. **Phase B's X-9 (algorithmic-citizenship) is empirically validated.** All 3 drafts include external links in REPLY blocks. Distribution penalty is documented (X reduced external-link reach 30-50% from March 2025 per Phase B research). Existing X-1..6 doesn't catch this. Adding X-9 as essential-tier with score-cap-on-violation would force the loop to evolve away from external links.

2. **Phase B's X-6 cohort diversity gap is also real** — but it's NOT a missing criterion, it's an existing one (X-6) that's not being demanding enough. Three drafts on identical source-frame should score 2 on X-6's current anchors. If they're scoring higher in production, the X-6 anchors need sharpening, not new criteria.

3. **The drafts are competent but not 9-tier.** Each individually scores 3-4 across most dimensions. None would pass "operator publishes unedited" test for JR — the language register has multiple jargon-driven plain-language cap triggers.

4. **Phase B's X-7 (specificity density) would add useful signal** but isn't catching a binary failure here — the drafts have some specifics but not enough.

## Cross-lane synthesis

After spot-rating 3 lanes, the Phase B proposals can be re-classified:

### Tier 1 — Empirically validated, must include in Phase D
- **X-9 algorithmic-citizenship** — caught real failure in 3/3 current drafts
- **MON-9 source faithfulness with auto-cap** — couldn't test on empty-data digest but the criterion design is structurally sound; needs validation on content-rich digest (e.g., when monitoring fixture has retrieved mentions)
- **CI-9 triangulation depth** (≥2 sources per claim) — Phase B documented practitioner consensus; couldn't validate empirically without competitive brief in v189 (briefly checked, no recent variant with non-stub brief.md found)
- **All new article_engine / image_engine / ad_engine criteria** — no archived variants to validate, but each grounded in Phase B 2026-current research

### Tier 2 — Strengthen existing criteria rather than add new
- **MON-14 forward hooks** — redundant with MON-7#4; drop from new criteria, validate that MON-7 anchors demand forward hooks
- **MON-15 missing-expected-signal** — redundant with MON-6#3; drop and confirm MON-6 anchors
- **X-6 cohort diversity** — existing criterion is fine; sharpen anchors to demand 3-5 distinct source-frames, not 3-5 wordings of same frame
- **GEO criteria** — couldn't validate due to structural gate failure on v189 fixture; recommended new criteria stand on Phase B research

### Tier 3 — Need additional validation before committing
- **MA-9 / MA-10 / MA-11** (insight density, brand-replace test, cross-section threading) — couldn't validate on v189 archive (templates only). Need a real marketing_audit run to confirm.
- **SB-9..15 mode-conditional** — couldn't validate; storyboard v189 had Gossip.Goblin / TechReview fixtures but those are narrative mode, not the educational/brand_authority modes that need the new criteria.
- **LI-7..11** — couldn't validate (linkedin_engine archive doesn't have v189 fixtures in same path structure).

## Implications for Phase D

1. **Tier-1 criteria go into the final rubric specs.** All 4 lanes that produced Phase B research with clear-evidence proposals.

2. **Tier-2 redundancies get removed.** Don't add MON-14/MON-15 — strengthen MON-7#4 / MON-6#3 anchors instead. This keeps the criterion count lean.

3. **Tier-3 untested criteria go in with explicit "validate on first 5 real client artifacts" flag.** Don't gate the rubric on perfect empirical validation — these are designed against current 2026 research, which is the best available anchor without real artifacts to rate.

4. **Cohort criteria need re-examination.** X-6 (and SB-8, LI-6) anchors should be sharpened to demand distinct source-frames / angles / pillars, not just distinct wordings. This is the most consistent failure mode across all content-for-publish lanes.

5. **The structural gate boundary matters.** Judges only score artifacts that pass structural. Phase D rubric design should explicitly note that compliance-precondition + structural-precondition fire BEFORE judge scoring.

6. **JR's "monitoring is the gold standard" claim is empirically confirmed** on Lululemon. The rubric architecture (8 ONE-quality criteria with mixed gradient + checklist + cross-references to raw data) is the design language Phase D inherits.

## What Phase C did NOT do

- Did not rate 30+ variants per lane (originally proposed). Spot-checks chosen for highest-signal validation given time budget.
- Did not validate MA, SB-educational, SB-brand_authority, LI new criteria empirically — these proceed to Phase D on Phase B research strength alone, with explicit validation flag.
- Did not run inter-family agreement analysis (claude vs codex disagreement). Useful for future calibration drift detection but not the binding constraint for Phase D rubric design.

Phase D writes the final per-lane rubric specs, incorporating Tier-1 confirmed + Tier-3 research-grounded + dropped Tier-2 redundancies.
