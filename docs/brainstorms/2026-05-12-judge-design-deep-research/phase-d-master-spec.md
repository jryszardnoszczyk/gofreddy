---
date: 2026-05-12
phase: D-master
topic: judge design master spec — all 10 lanes + compliance regime shape
status: ready for review
---

# Phase D Master Spec — Optimal Judge Design Across All 10 Lanes

This is the deliverable spec. Per-lane criteria with full anchored prose live in `phase-d-rubrics/<lane>.md` (10 files, ~40,000 words). This master doc captures:

- The cross-cutting design language extracted from the 7 existing lanes + sharpened through Phase A-C
- The compliance regime shape (medical_pl + legal_pl) — structure designed, content gated on legal-review per v1 brainstorm Resolve-Before-Planning #2
- The aggregate rubric inventory across all 10 lanes
- Implementation sequencing
- Validation framework

## TL;DR

| Lane | Pre | Post | Net change | Critical addition |
|---|---|---|---|---|
| `geo` | 8 | 13 | +5 (4 new, 1 split into 2) | GEO-9 named-expert quoted attribution (KDD 2024 +41% citation lift) |
| `competitive` | 8 | 11 | +3 new | CI-9 triangulation depth (≥2 source classes per claim) |
| `monitoring` | 8 | 13 | +5 (5 new) | MON-9 source faithfulness with AUTO-CAP (catches fabricated quotes) |
| `storyboard` | 8 | 15 | +7 mode-conditional | SB-12 medical_pl + SB-15 legal_pl AUTO-CAP compliance preconditions |
| `marketing_audit` | 8 | 11 | +3 new | MA-9 decision-changing insight density |
| `x_engine` | 6 | 10 | +4 new | X-9 algorithmic-citizenship (no external links — empirically validated Phase C: 3/3 current drafts violate) |
| `linkedin_engine` | 6 | 12 | +6 (5 new, 1 split into 2) | LI-11 compliance precondition + dual-adaptor dispatch (operator vs named-byline) |
| `article_engine` | 0 | 8 | +8 NEW lane | ART-4 voice fidelity via rolling 200-word-window vs corpus |
| `image_engine` | 0 | 8 | +8 NEW lane | IMG-1 vision-judge stop-scroll with geometric/count-based anchors |
| `ad_engine` | 0 | 6+1 | +7 NEW lane | ADE-5 variant diversity via (angle, hook-lever, persona-stage) triple-tag |
| **Total** | **52** | **107** | **+55 criteria** | |

Storyboard 8→15 is mode-conditional — no single fixture fires all 15. Marketing_audit preserves its JSON-envelope architecture (deliberate divergence from gradient-prose pattern in other lanes).

## Design language — the 12 patterns

Phase A-C surfaced 12 patterns that distinguish strong rubrics from weak ones. The 7 existing lanes use the first 9 to varying degrees. The 3 new lanes + the strengthened existing lanes adopt all 12.

### Pattern 1: "ONE quality" framing per criterion
Each rubric scopes its question to a single concrete behavior. Anti-halo by prompt design. Cited inside the prompt as "Evaluate this <artifact> for ONE quality: <question>." Used across all 7 existing well-iterated rubrics; preserved in all 10 final specs.

### Pattern 2: Mixed scoring shapes — gradient + checklist
Some criteria are 1/3/5 anchored prose (holistic judgments); others are 4-question YES/NO checklists (decomposable). Match shape to the criterion's natural grain. Preserved across all 10 lanes.

### Pattern 3: WHY-before-WHAT
Anchor prose includes the rationale before the rule. Example from GEO-3: *"AI search engines give higher citation weight to sources that demonstrate balanced assessment."* This is chain-of-thought prefacing baked into the rubric. Added throughout the new specs where load-bearing.

### Pattern 4: Ground-truth cross-references
Judge verifies output against source artifacts — anti-fabrication structural. Existing examples: GEO-4 vs page content, CI-4 vs `_client_baseline.json`, MA-5 deterministic severity rollup. New: ART-4 voice fidelity vs `voice_persona.corpus_path`; IMG-4 brand consistency vs brand-style-guide; ADE-4 LP coherence vs landing-page hero copy.

### Pattern 5: Cold-start handling
First-week digests / first-time clients / cold-data edge cases get explicit redirection in anchor prose. Example: MON-1 and MON-7 redefine themselves for first-week digests with no prior data. Preserved.

### Pattern 6: Hostile failure-mode detection
Anchor language specifically names known anti-patterns observed in archived rejected variants. Example: CI-8 #3 *"Does a competitor with 'detect-only' data_tier get compared on equal footing with one that has 'full' data? It should not."* Strengthened across all new specs with specific slop archetypes per lane (LinkedIn-on-X, broetry-cascade, AI-image-tells, etc.).

### Pattern 7: Non-uniform tier mix per lane
The lane's shape determines its tier distribution. Final mix per lane:
- geo: 6 essential / 4 important / 1 optional / 2 pitfall (13 total)
- competitive: 4 essential / 5 important / 0 optional / 2 pitfall (11 total)
- monitoring: 5 essential / 6 important / 1 optional / 2 pitfall (13 total — incl 1 essential auto-cap)
- storyboard: 3-5 essential (mode-dependent) / 4-6 important / 0-1 optional / 1-3 pitfall (8-15 active)
- marketing_audit: 4 essential / 5 important / 1 optional / 1 pitfall (11 total)
- x_engine: 3 essential / 5 important / 0 optional / 2 pitfall (10 total)
- linkedin_engine: 3-4 essential (adaptor-dependent) / 6 important / 0 optional / 1-2 pitfall (11-12 active)
- article_engine: 5 essential / 2 important / 0 optional / 1 pitfall (8 total)
- image_engine: 6 essential / 2 important / 0 optional / 3 pitfall (8 total — 3 auto-caps)
- ad_engine: 5 essential / 1 important / 0 optional / 1 pitfall (6+optional C7 — Foreplay-conditional)

### Pattern 8: Cross-item criteria for cohort value
Lanes where value is in the *batch* (X/LI/SB/AD/IMG carousel) get one cross-item criterion. Strengthened anchors demand distinct source-frames / angles / pillars, not distinct wordings — addresses Phase C finding that 3/3 current X drafts shared one source frame.

### Pattern 9: CoT-before-score closing format
Standard rubric closing: *"Provide your reasoning, cite specific evidence from <X>, then give your score."* Preserved for all gradient/checklist criteria. NOT preserved for MA's JSON-envelope criteria (deliberate divergence — MA uses structured output with derived counts).

### Pattern 10: Deterministic checks woven into rubrics (from MA)
MA's innovation: per-rubric deterministic computations (severity rollup, capability_id ∈ registry, banned-vocab count). Selectively propagated:
- MA's existing checks preserved
- MON-10 event canonicalization computable (cluster count vs source citation count)
- ADE-5 cohort diversity score computed deterministically from per-variant triple-tags
- ADE-3 format compliance computable (Meta 20% text overlay rule, etc.)
- IMG-3 format compliance deterministic (slide count, aspect ratio, file format)

### Pattern 11: "Hard rule" / AUTOMATIC cap mechanism (from MA + X/LI)
Structured score caps where boundary violations are catastrophic. Final inventory:
- **AUTO-CAP at score 1 (severity)** — for fabrication, compliance violation, external-link distribution-killers: MON-9, X-9, IMG-3, IMG-5, IMG-8, ADE-3, ADE compliance precondition, SB-12, SB-15, ART-8, LI-11
- **HARD FLOOR at 3-4** — for unverifiable lived-work claims: X-2, LI-2, ART-4
- **Overall composite cap at 4-5** — when hard rule fires: MA-7 (gap honesty), MA-8 (off-registry), MA-6 (banned vocab ≥10), all auto-cap criteria above

### Pattern 12: Compliance regime as precondition, not criterion (NEW)
For all content-for-publish lanes touching Klinika/DWF clients, compliance judge fires *before* the quality judge. Hard-block from medical_pl/legal_pl means artifact never reaches quality scoring. Soft-warn flags but doesn't gate. Quality criteria assume compliance has passed. Detail in next section.

## Compliance regime shape (medical_pl + legal_pl)

### Structure designed; content gated on Resolve-Before-Planning #2

The v1 brainstorm's R22 specifies per-lane duplication of `medical_pl_*` and `legal_pl_*` rubric IDs across 6 content-for-publish lanes (article, image, ad, storyboard, x_engine, linkedin_engine). Phase D refines this:

**Shape decision: shared rule files referenced by per-lane compliance criteria.**

Instead of duplicating 24-36 rubric entries across 6 lanes, each lane carries ONE compliance criterion that references shared rule files:
- `configs/compliance/medical_pl/rules.yaml` — Polish medical advertising (Art. 14 *Ustawa o działalności leczniczej*, Polish Medical Chamber Code of Ethics art. 63-65, 2023 medical-device advertising ban)
- `configs/compliance/legal_pl/rules.yaml` — Polish bar/radca advertising (solicitation, fee mentions, comparative, ESP language)

Each lane's compliance criterion:
- **storyboard**: SB-12 (medical_pl, fires in educational mode for Klinika) + SB-15 (legal_pl, fires in brand_authority mode for DWF)
- **article_engine**: ART-8 (medical_pl if `byline=Klinika` / legal_pl if `byline=DWF`)
- **image_engine**: IMG-8 (medical_pl / legal_pl based on `client` field)
- **ad_engine**: cross-cutting compliance precondition (fires before ADE-1..6)
- **x_engine**: not applicable v1 (JR's operator profile, not client byline)
- **linkedin_engine**: LI-11 (medical_pl if Klinika named-byline / legal_pl if DWF named-byline; not fired on operator profile)

### Rule file schema

```yaml
# configs/compliance/medical_pl/rules.yaml
regime: medical_pl
version: <semver>
last_legal_review: <date or null>
reviewer: <name or null>
rules:
  - id: med-pl-001
    name: superlative_terms
    severity: hard-block
    description: "Comparative superlatives forbidden under Art. 14 medical advertising restrictions"
    trigger_patterns:
      - "the best"
      - "najlepszy"
      - "najtańszy"
      # ...
    text_blocklist: [...]
    visual_blocklist: [...]  # image_engine extension
  - id: med-pl-002
    name: result_promises
    severity: hard-block
    # ...
  - id: med-pl-003
    name: pom_treatment_names
    severity: hard-block
    description: "Botox is a POM under Polish law; cannot be named in marketing"
    # ...
```

### Two-gate behavior (preserved from v1 brainstorm)

1. **In-loop fitness judge** — compliance criterion fires per fixture. Hard-block triggers `score = 1` + overall composite cap at 4. Soft-warn flags in metadata without capping.
2. **Pre-publish human gate** — load-bearing risk control regardless of judge sophistication. Polish medical and bar advertising liability is **client's**, not gofreddy's. Human gate is mandatory.

### Pre-population behavior — shape-only mode

Until `last_legal_review` populates and rule files have content, each compliance criterion runs in **shape-only mode**:
- Judge confirms cross-reference path exists
- Declares "not yet scoring against populated rule list"
- Abstains rather than scoring against empty rule list
- Surfaces in artifact metadata for human review

This fails loud rather than silently scoring against an empty rule list.

### Cost of duplication-vs-shared decision

The v1 brainstorm's "duplicate per-lane" option preserves backward compat (no new cross-lane primitive). The shared-rule-file option introduces one new structural input (`configs/compliance/...`) but avoids 24-36 manual rubric entries. Phase D recommends shared-rule-file because:
- Single source of truth for legal review
- Rule edits propagate atomically across lanes
- RUBRIC_VERSION hash invalidates on rule file content (so cache stays correct)
- Lane-specific criteria (SB-12, ART-8, etc.) still own per-lane anchors (visual vs text vs video)

## Cross-cutting structural changes

Beyond per-lane rubric prose, Phase D requires four structural changes to the codebase:

### Change 1: `voice_persona` shared abstraction

Per v1 brainstorm R20. Schema:
```
configs/voice_persona/<name>/
  corpus.md            # ingested books / prior writing — flat text
  voice_rules.yaml     # what to do / what to avoid
  style_anchors.yaml   # named voice anchors
  credentials.yaml     # for compliance + authority cross-references
```

Consumed by: storyboard SB-1/SB-5/SB-13, article_engine ART-4, linkedin_engine LI-1/LI-2, x_engine X-1, image_engine IMG-4 (brand voice in copy overlays).

### Change 2: `findings_brief` contract

Per v1 brainstorm R21. JSON schema with locked minimum field set: `brief_id`, `source_lane`, `priority`, `topic`, `target_lanes`, `target_formats`, `voice_persona_ref`, `source_pointers`, `success_notes`.

Consumed by article_engine (v1) + extends to other content-for-publish lanes in v1.5.

### Change 3: `configs/compliance/{medical_pl,legal_pl}/rules.yaml`

New cross-lane structural input. Referenced by compliance criteria in 6 content-for-publish lanes. Content gated on Resolve-Before-Planning #2 (named legal-review owner + budget).

### Change 4: `configs/brand/<client>/style_guide.yaml`

For image_engine IMG-4 brand consistency. Per-client brand-style-guide spec (typography + palette + logo placement rules). Net-new structural input. Populated by client onboarding.

## Aggregate rubric inventory

### Final criterion count: 107 across 10 lanes

| Tier | Count | % |
|---|---|---|
| Essential | 44 | 41% |
| Important | 41 | 38% |
| Optional | 3 | 3% |
| Pitfall (with auto-cap) | 19 | 18% |

Pitfall count is elevated because the new lanes (article/image/ad) and the strengthened lanes (monitoring +MON-9, x_engine +X-9, storyboard +SB-12/15, linkedin_engine +LI-11) all add auto-cap criteria for known catastrophic failure modes.

### Criteria by ground-truth verification type

- **Text-judge gradient/checklist (no external cross-reference)**: GEO-1, GEO-2, GEO-3, CI-1, CI-3, CI-6, CI-7, MON-2, MON-3a, MON-3b, MON-5, MON-6, SB-2, SB-3, SB-4, SB-7, MA-1, MA-3, MA-6, X-1, X-3, X-4, X-5, X-10, LI-1, LI-3a, LI-3b, LI-4, LI-9, LI-10, ART-1, ART-2, ART-5, ART-6, ADE-1, ADE-2, ADE-6. ~37 criteria.

- **Text-judge with cross-reference to source artifacts**: GEO-4 (page content), GEO-7a, GEO-7b, GEO-8a, GEO-8b, GEO-9, GEO-10, GEO-11, CI-4 (_client_baseline), CI-5, CI-8 (data_tier), CI-9, CI-10, CI-11, MON-1, MON-4, MON-7, MON-11 (author profile), MON-12 (raw mentions), MON-13, MA-2, MA-4, MA-5, MA-7, MA-8, MA-9, MA-10, MA-11, SB-1 (creator pattern data), SB-5, SB-6, SB-8, SB-13, X-2, X-6, X-7, X-8, X-9, LI-2, LI-5, LI-6, LI-7, LI-8, ART-3, ART-4 (voice corpus), ART-5, ART-7, ADE-4 (LP hero), ADE-5. ~48 criteria.

- **Vision-judge (Gemini multimodal)**: IMG-1, IMG-2, IMG-4, IMG-5, IMG-6, IMG-7. ~6 criteria. Extends existing `render_judge.py` pattern.

- **Deterministic check (no judge, mechanical)**: MA-5 severity rollup, MA-6 banned-vocab count, MA-8 capability_id ∈ registry, MON-10 event canonicalization (cluster count vs source count), MON-9 fabrication trigger (substring matching against `mentions/<week>.json`), IMG-3 format compliance (slide count + aspect + file format), ADE-3 format compliance (text-overlay %, char count), ADE-5 cohort diversity score (deterministic from tags). Plus compliance regex matching for all SB-12/SB-15/ART-8/IMG-8/LI-11/ADE compliance criteria. ~16 mechanical anchors.

## Implementation sequencing

### Phase 1 — Foundation (1 week, blocks lane rubric work)

1.1. `configs/voice_persona/<name>/` schema spec'd in `docs/architecture/voice-persona.md` + Python loader added.

1.2. `configs/compliance/<regime>/rules.yaml` schema spec'd in `docs/architecture/compliance-regime.md`. Schema-only (no rule content yet). Loader added.

1.3. `configs/brand/<client>/style_guide.yaml` schema spec'd. (Populated by Klinika + DWF onboarding when v1 starts.)

1.4. RUBRIC_VERSION hash extension — invalidates on rubric text OR voice_persona file content OR compliance rule file content OR brand-style-guide content.

### Phase 2 — Existing 7 lanes' new criteria (1.5 weeks)

Per-lane PR per spec. Lane order by priority of demo dependency:

2.1. **monitoring** — MON-9 source faithfulness AUTO-CAP is the highest-value addition (catches fabricated quotes; load-bearing for the DWF demo)
2.2. **geo** — 5 new criteria; load-bearing for Klinika SEO/AI-search
2.3. **competitive** — 3 new criteria; well-iterated baseline
2.4. **storyboard** — 7 mode-conditional; load-bearing for both demos; depends on Phase 1 (voice_persona + compliance regime)
2.5. **marketing_audit** — 3 new criteria; preserves JSON-envelope architecture
2.6. **x_engine** — 4 new criteria; X-9 auto-cap fixes current archived-draft failure
2.7. **linkedin_engine** — 6 new (5 + LI-3 split); LI-11 depends on Phase 1 compliance regime

### Phase 3 — New lane scaffolding (2-3 weeks; can overlap with Phase 2 once Phase 1 lands)

3.1. **article_engine** — depends on Phase 1 voice_persona + compliance regime + findings_brief contract
3.2. **image_engine** — depends on Phase 1 brand-style-guide + compliance regime + new vision-judge architecture + new static-image composition module (Pillow/Cairo/skia)
3.3. **ad_engine** — depends on Phase 1 compliance regime + LP coherence input format

### Phase 4 — Real-world validation (post-demo, ongoing)

4.1. First 5 real Klinika audits — validate medical_pl rule file content
4.2. First 5 real DWF deliverables — validate legal_pl rule file content
4.3. Brand-replace test for marketing_audit MA-10
4.4. Voice-fidelity rolling-window validation for article_engine ART-4
4.5. Vision-judge calibration for image_engine IMG-1..IMG-8

### Sequencing notes

- **Phase 1 blocks Phase 2 partially (storyboard + linkedin_engine compliance need rule schema; rest can proceed without)**
- **Phase 1 blocks Phase 3 fully (new lanes need all 4 foundation pieces)**
- **Compliance rule file CONTENT (the actual trigger phrases) is operator-track work** — gated on Resolve-Before-Planning #2 (named legal-review owner + budget). Shape-only mode keeps the loop functional until content lands.
- **v1 brainstorm's 1-2 month demo timeline:** Phase 1 + Phase 2 fits in ~3 weeks. Phase 3 needs ~3 weeks. Total ~6 weeks — fits inside 1-2 month window.

## Validation framework (cross-lane)

Each per-lane spec has a Section 5/6/7 with validation tests. Aggregate validation across lanes:

### V1: Fabrication catches
- monitoring MON-9 on synthetic digest with hallucinated quote → AUTO-CAP fires
- x_engine X-2 on draft with unverifiable lived-work claim → HARD FLOOR ≤3
- article_engine ART-3 on article with unsourced load-bearing claim → score ≤3
- ad_engine ADE-2 falsifiability check

### V2: Compliance preconditions
- storyboard SB-12 on Klinika storyboard with "Botox" named (POM violation under Polish 2023 ban) → AUTO-CAP at 1
- storyboard SB-15 on DWF brand_authority video with "Skontaktuj się z nami" (solicitation) → AUTO-CAP at 1
- article_engine ART-8 on Klinika article with "guaranteed results" → AUTO-CAP at 1
- image_engine IMG-8 on Klinika carousel with before/after slide → AUTO-CAP at 1
- ad_engine cross-cutting compliance on Meta Reels with "the best clinic in Warsaw" → AUTO-CAP at 1

### V3: Algorithmic-citizenship + structural failures
- x_engine X-9 on draft with `https://...` in [REPLY] block → AUTO-CAP at 1 (3/3 current archived drafts fail this; first regenerated cohort should pass)
- ad_engine ADE-3 on Meta image ad with text overlay >20% area → AUTO-CAP at 1
- image_engine IMG-3 on ig_carousel with 11 slides → AUTO-CAP at 1

### V4: Voice fidelity (rolling window)
- article_engine ART-4 on synthetic article with mid-paragraph voice drift → window > 2σ → HARD FLOOR
- linkedin_engine LI-1 on Klinika named-byline draft with operator (JR) voice patterns → AUTOMATIC ≤4

### V5: Cohort diversity
- x_engine X-6 strengthened on 3 drafts sharing one source frame → score 2 (currently scoring higher)
- ad_engine ADE-5 on 5 ads with same (angle, hook-lever, persona-stage) tuple → score 1
- storyboard SB-8 on 5 storyboards sharing structural pattern → score 2

### V6: Cross-artifact coherence
- ad_engine ADE-4 LP-coherence on synthetic ad with bait-and-switch LP → score 1
- image_engine IMG-2 carousel arc on 10 disconnected slides → score 1-2
- marketing_audit MA-10 brand-replace test → confirm boilerplate findings score ≤3

### V7: Vision-judge calibration
- image_engine IMG-1 on synthetic stop-scroll-fail (focal element <20% area, competing elements >40%) → score 1
- image_engine IMG-5 AI-slop on synthetic image with malformed hands → AUTO-CAP

## Open questions

1. **Foreplay reliability** (Phase A's Resolve-Before-Planning #4) — determines whether ad_engine's optional C7 ships. Phase D recommends ad_engine ships without C7 by default; flip ON only after Foreplay reliability test passes.

2. **Compliance rule content** (Resolve-Before-Planning #2) — gates Phase 2.4, Phase 2.7, Phase 3 timelines. Shape-only mode unblocks the substrate; content unblocks real evolution against compliance.

3. **Voice corpus consent** (Resolve-Before-Planning #1) — gates ART-4 and SB-13 voice fidelity criteria. Without Dr. Maria's books + DWF partner prior writing ingested, these criteria abstain in shape-only mode.

4. **Vision-judge cost cap** — image_engine fires Gemini Vision per slide (7-10× single-image call per carousel). At Gemini 2.5 Flash pricing ~$0.002/call, this is ~$0.02 per 10-slide carousel. Acceptable for v1; revisit if image_engine generation rate grows.

5. **Marketing_audit JSON-envelope vs gradient-prose** — MA preserved its existing architecture (deliberate). Could be retrofitted to match other lanes' shape post-v1; not load-bearing for current functioning.

## What this spec doesn't do

- **Doesn't write the actual `configs/compliance/{medical_pl,legal_pl}/rules.yaml` content** — gated on legal-review input per Resolve-Before-Planning #2
- **Doesn't write the actual `configs/brand/<client>/style_guide.yaml` content** — populated by Klinika + DWF onboarding
- **Doesn't write the actual `configs/voice_persona/<name>/corpus.md` content** — gated on Dr. Maria + DWF partner consent per Resolve-Before-Planning #1
- **Doesn't change the existing 8-in-1-call judge architecture** (preserved per JR's framing — focus on criteria, not architecture)
- **Doesn't ship the implementation** — this is the SPEC; implementation is the next phase

## Next steps

1. **Operator review** of this master spec + the 10 per-lane specs in `phase-d-rubrics/`. Approve, redirect, or request changes.

2. **On approval:** copy this master spec + per-lane specs to `docs/superpowers/specs/2026-05-12-judge-design-spec.md` (single file or directory; user preference).

3. **Implementation planning:** `/ce:plan` or equivalent to generate per-lane PR plans for Phase 1 + Phase 2 + Phase 3. Sequenced per the implementation order above.

4. **Resolve-Before-Planning work continues in parallel** — legal-review owner, voice corpus consent, brand-style-guide population. These gate content of the compliance / voice / brand structural inputs but not the structural inputs themselves.

5. **First 5 client deliverables become the validation corpus** — empirical refinement of rubric anchors based on real Klinika + DWF artifact + operator feedback.
