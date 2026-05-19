# IE-1..IE-8 Rubric Anchors (image_engine, U14)

Mirror of `docs/plans/2026-05-13-002-AE-rubric-anchors.md` for the
image_engine lane. Per TD-41: the 8 IE rubrics are operationalized
with explicit Score-1 / Score-3 / Score-5 anchors, falsifiability
hooks, named Score-3 failure modes, and anti-gaming clauses.

The rubric prose itself lives in `src/evaluation/rubrics.py` (`_IE_1`
through `_IE_8`). This doc is the design reference + the operator's
quick-look cheat sheet during reviewer-assist + judge-prose lock-step
review.

## Backend routing

Per the U14 §judge wiring section + JR's 2026-05-19 model update:

| Rubric | Backend                          | Notes                                  |
|--------|----------------------------------|----------------------------------------|
| IE-1   | Gemini 3 Flash Preview (vision)  | hook visual; scored on focal_clarity + stop_scroll_strength + thumbnail_legibility |
| IE-2   | Gemini 3 Flash Preview (vision)  | brand consistency; palette + typography + logo + iconography |
| IE-3   | Gemini 3 Flash Preview (vision)  | info density + legibility; thumbnail-test + whitespace + hierarchy |
| IE-4   | claude/opus (text)               | format compliance; structural gate catches most pre-judge |
| IE-5   | Gemini 3 Flash Preview (vision)  | visual specificity; anti_patterns.yml hits cap at 4 |
| IE-6   | Gemini 3 Flash Preview (vision)  | carousel arc (cross-item); rolls up per-slide via min-gate |
| IE-7   | claude/opus (text)               | alt-text + caption voice; matches voice persona |
| IE-8   | claude/opus (text)               | repurposability; optional rubric |

The visual rubrics dispatch through `src/evaluation/vision_judge.py`
which wraps the Gemini 3 Flash Preview backend. v1 ships with
dependency-injected `call_gemini` callable — production wiring
(Gemini SDK + API key) lands in U18.

D24 originally specified **Gemini 2.5**. JR updated the backend to
**Gemini 3 Flash Preview** during U14 design (2026-05-19). The DI
pattern is unchanged; only the documented production backend shifts.

## Tier assignments

| Rubric | Tier      | Rationale                                                     |
|------- |-----------|---------------------------------------------------------------|
| IE-1   | essential | Hook visual — fail an image fully if it doesn't stop scroll.  |
| IE-2   | essential | Brand consistency — fail an image fully if off-brand.         |
| IE-3   | important | Info density legibility — important but not always fatal.     |
| IE-4   | essential | Format compliance — wrong dims = structural fail.             |
| IE-5   | essential | Visual specificity — anti-AI-slop hard floor.                 |
| IE-6   | important | Carousel arc (cross-item) — only fires for carousels.         |
| IE-7   | important | Alt-text + caption voice — accessibility + voice fidelity.    |
| IE-8   | optional  | Repurposability — nice-to-have, scored informationally.       |

## Per-rubric anchor reference

### IE-1 Hook visual

- **Sub-dimensions:** stop_scroll_strength, focal_clarity, thumbnail_legibility.
- **Hard caps:** text-overlay >7 words → cap at 4; no clear focal
  subject at thumbnail scale → cap at 3.
- **Score-3 failure mode:** focal subject exists but generic
  ("businessperson at laptop"); text-overlay unmotivated rhetorical.

### IE-2 Brand consistency

- **Sub-dimensions:** palette_fidelity (ΔE ≤15), typography_consistency,
  logo_treatment, iconography_register.
- **Hard cap:** any fal-rendered brand wordmark → cap at 2.
- **Score-3 failure mode:** palette mostly matches but one accent drifts;
  typeface in right family but wrong weight; logo present but oversized.

### IE-3 Info density + legibility

- **Sub-dimensions:** legibility_at_thumbnail, whitespace_balance, hierarchy_clarity.
- **Hard cap:** li_doc_carousel slide >60 words → cap at 3.
- **Score-3 failure mode:** hierarchy clear at full view but body fails
  at thumbnail; OR whitespace imbalance.

### IE-4 Format compliance

- **Structural gate enforces:** dimensions, slide counts, safe-zones,
  text-overlay caps. Rubric scores qualitative fit within compliance.
- **Score-1 failure mode:** wrong dimensions; slide count out of bounds;
  text in IG story safe-zone; hero text contrast <4.5:1.

### IE-5 Visual specificity

- **Sub-dimensions:** concept_concreteness, absence_of_generic_filler,
  metaphor_strength.
- **Hard cap:** any `anti_patterns.yml` hit observed by vision_judge →
  cap at 4. Substrate-banned patterns (extra fingers, garbled text,
  hallucinated logos) → cap at 2.
- **Score-3 failure mode:** concrete subject but weak metaphor;
  surrounding scene generic.

### IE-6 Carousel arc (cross-item)

- **Sub-dimensions:** cover_hook, slide_pacing, payoff_strength, cta_clarity.
- **Rollup:** `mean(dimension_scores) + min(score) gate` — one weak
  slide drags the carousel score.
- **Score-1 failure mode:** cover identical to interior slides; no PSR
  arc; middle slides reorderable.

### IE-7 Alt-text + caption voice

- **NOT a vision rubric.** Scores TEXT (alt-text + caption) via
  claude/opus outer judge.
- **Sub-dimensions:** alt_text_information_density, caption_voice_fidelity.
- **Hard cap:** alt-text missing OR alt-text generic ("image") → cap at 1.
- **Score-3 failure mode:** alt-text describes image but generically;
  caption mostly voice-consistent but slips.

### IE-8 Repurposability (optional)

- Scores informational, not gating.
- **Score-5:** composition respects ≥2 aspect-ratio cuts; operator
  could repurpose with a 5-minute Pillow script.
- **Score-1:** single-platform shot; reuse requires re-generation.

## Operational notes

- **vision_judge integration:** `src/evaluation/vision_judge.py`
  dispatches IE-1/2/3/5/6 to Gemini 3 Flash Preview with a multimodal
  prompt + per-rubric dimension list + brand_tokens hex codes +
  anti_patterns.yml as context.
- **Carousel rollup:** `src.evaluation.vision_judge.roll_up_carousel()`
  takes per-slide scores and returns a synthetic VisionScore with
  min-gate + dimension means + failure-mode union.
- **fal_image semaphore:** `autoresearch.concurrency.fal_image_semaphore()`
  defaults to 2 (matches fal free-tier shape); operators bump via
  `FAL_IMAGE_MAX_CONCURRENCY` on paid plans.

## Anti-patterns YAML (TD-41 — 15 patterns)

Lives at `autoresearch/archive/v007-curated/templates/image_engine/anti_patterns.yml`.
Vision_judge consumes as natural-language hints + scores the image
against them; observed hits land in `failure_modes_observed` and cap
IE-5 at 4. Substrate-banned hits (fal-rendered brand wordmarks, hand
anatomy artifacts, garbled in-image text) cap at 2.

## Stability + drift detection

RUBRIC_VERSION hash bumps when any IE-* prose changes (incl. compliance
rubric prose_refs). This invalidates parent-score caches.

When future judge-prose lock-step review touches IE-* prose, update
both `src/evaluation/rubrics.py` AND the matching anchor in this doc.
