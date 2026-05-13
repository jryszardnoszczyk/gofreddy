---
date: 2026-05-12
phase: D
lane: image_engine
status: spec — NEW lane; implementer-ready pending (a) brand-style-guide schema lock, (b) compliance rule-file content per Resolve-Before-Planning #2, (c) RENDER_JUDGE_LANES_ALLOWED opt-in for Klinika/DWF visual content
inputs:
  - phase-a-lane-purposes.md §9 (image_engine — NEW)
  - phase-b-research/image_engine.md (3009 words, 8 candidate criteria IMG-1..IMG-8)
  - phase-c: not applicable (NEW lane, no existing variants)
  - autoresearch/archive/v006/scripts/render_judge.py (Gemini 2.5 Flash + RENDER_JUDGE_LANES_ALLOWED precedent)
optimization_target: first-slide stop-scroll prediction + carousel arc + brand consistency, conditioned on hard format and compliance gates
formats: ig_carousel | li_doc_carousel | hero_banner | ad_static
---

# Phase D — image_engine rubric spec (8 criteria)

The image_engine lane produces composed PNG/JPG/SVG: IG carousels, LinkedIn document carousels, hero banners, ad statics. Phase A pins the optimization target to first-slide stop-scroll prediction + carousel arc + brand consistency, on top of hard format and compliance gates. Phase B reviewed the 2026 platform landscape — IG ranking collapses onto saves and sends (not likes); LinkedIn document carousels hit 6.60% engagement at the 7-slide peak vs 1.6% baseline; public AI-slop detection accuracy is above 75% — and proposed an 8-criterion superset (IMG-1..IMG-8) under a vision-judge-led grading model. Phase C is N/A: net-new lane, no existing variants. Spec proceeds on Phase B strength.

This spec locks **8 criteria** under **format-conditional firing**. IMG-3 (format), IMG-5 (AI-slop), IMG-8 (client compliance) are **hard gates with auto-cap**: a confirmed failure caps the overall fixture score regardless of other criteria. IMG-1, IMG-2, IMG-4 are the primary 9-vs-5 discriminators. IMG-6 and IMG-7 are 5-vs-1 hygiene checks. The grading model is a vision judge (Gemini 2.5 Flash, mirroring `render_judge.py`), supplemented by deterministic checks for format and palette and a text judge for alt-text and arc semantics.

Three pre-implementation gates remain operator-owned: (a) brand-style-guide schema + per-client palette/typography/logo files must exist — IMG-4 cross-references the path but invents nothing; (b) compliance rule files at `configs/compliance/{medical_pl,legal_pl}/rules.yaml` need legal sign-off (Resolve-Before-Planning #2 — same gate storyboard's SB-12/SB-15 wait on); (c) the static-image composition module (Pillow/Cairo/skia per v1 brainstorm R12) is net-new infrastructure that must land before fixtures render.

---

## Section 1 — Summary table

Tier vocabulary: **essential** (load-bearing for ship-eligibility), **important** (drags the score when failed), **pitfall** (specific failure mode that caps), **deterministic** (rule-based).

| ID    | Tier               | ONE-quality summary                                                            | Format applicability                | Judge type                |
|-------|--------------------|--------------------------------------------------------------------------------|-------------------------------------|---------------------------|
| IMG-1 | essential          | First-slide stop-scroll: one dominant focal element; readable at scroll speed. | all (slide 1)                       | vision (Gemini 2.5 Flash) |
| IMG-2 | essential          | Carousel arc: each slide depends on the prior; middle permutation breaks read. | ig_carousel, li_doc_carousel only   | vision + text composite   |
| IMG-3 | essential, pitfall | Format compliance: slide count, aspect, safe-zone, Meta 20% text-overlay.      | all (per-platform)                  | deterministic (hard gate) |
| IMG-4 | essential          | Brand consistency: logo, palette, typography against client style-guide.       | all (cross-slide on carousels)      | deterministic + vision    |
| IMG-5 | essential, pitfall | AI-slop avoidance: geometric/count-based tells on photorealistic surfaces.     | all (each photoreal surface)        | vision (hard gate)        |
| IMG-6 | important          | Thumbnail legibility: headline readable at 256×320 downscale.                  | all (slide 1 minimum)               | vision (downscale)        |
| IMG-7 | important          | Alt-text quality: descriptive declarative sentence per slide, not headline dup.| all (one per surface)               | text                      |
| IMG-8 | essential, pitfall | Client compliance: medical_pl / legal_pl — auto-cap on match.                  | all (when regime is set)            | deterministic + vision    |

**Per-format firing.** ig_carousel and li_doc_carousel fire all 8. hero_banner and ad_static fire IMG-1, IMG-3, IMG-4, IMG-5, IMG-6, IMG-7, IMG-8 (IMG-2 skips — no multi-slide arc). For ad_static, IMG-3 additionally enforces the Meta 20% text-overlay rule.

**Counts.** Six essential (IMG-1/-2/-3/-4/-5/-8); two important (IMG-6/-7); three pitfalls with auto-cap (IMG-3/-5/-8). No optional tier — Phase B's view: visual content fails sharply below threshold; "nice to have" criteria don't apply.

---

## Section 2 — Final criterion prose

Prose is written as input to a Gemini 2.5 Flash vision judge ingesting a PNG (single slide) or composed grid PNG (whole carousel). Anchors are deliberately **geometric, count-based, physically observable**: "exactly one element exceeds 40% of slide area" survives the weakest plausible vision-judge ensemble; "feels premium" collapses to noise (Phase B MDPI 2026 finding). Each criterion follows: ONE-quality question → why-before-what → 1/3/5 anchors → cross-reference where load-bearing → closing instruction to cite specific visual evidence by slide and region before scoring.

### IMG-1 (essential, vision) — First-slide stop-scroll

**Evaluate this composed image for ONE quality:** Would a viewer scrolling at platform speed (IG ~1.5s/post; LinkedIn ~2s) stop on this first slide before deciding to swipe?

First-slide arrest is the binding constraint across all four formats. IG ranks on active dwell + swipe-through velocity (Mosseri-confirmed); LinkedIn document carousels rank on save rate; both ladders start at "did the viewer arrest on slide 1." Everything downstream (arc, brand, compliance) is wasted if slide 1 does not break feed rhythm. Grade what is physically observable, not what feels novel.

- **Score 1:** Three or more elements compete at similar visual weight (each 15-30% of slide area, none clearly dominant); OR no identifiable focal point; OR primary headline unreadable at full size; OR generic talking-head with no graphic intervention. The viewer's eye has nowhere to land in under 2 seconds.
- **Score 3:** One dominant element present but a competing element exceeds 25% area; OR headline reads at 1080px but text-vs-background contrast is below 4.5:1 (WCAG AA) so the hook strains at scroll speed; OR focal element centred but composition is symmetric / on-grid (no pattern break against the feed's typical content).
- **Score 5:** Exactly one element occupies the optical centre and exceeds 40% of slide area; no other element exceeds 25%; the dominant element is identifiable in under 2 seconds (judge confirms it can name the focal subject in one phrase); headline (if present) is in the upper or middle third with contrast above 4.5:1; composition breaks feed rhythm through at least one of: oversized single word/numeral, off-grid asymmetric crop, high-contrast single object on negative space, unexpected colour.

**Cross-reference (format-conditional).** For ig_carousel and hero_banner the judge additionally confirms critical content sits outside the bottom 110px IG overlay strip (deterministic pre-check feeds this).

**Closing.** Identify the focal element by region. Estimate its area as % of canvas. Name any competing element above 25%. Confirm headline contrast. Then score.

### IMG-2 (essential, vision + text) — Carousel arc and dependency

**Evaluate this carousel for ONE quality:** Does each interior slide depend on the prior — references, continues, contradicts — such that permuting slides 2 through N-1 would break the read?

Phase B grades carousel completion as the multiplier on first-slide arrest. If slide 1 stops the scroll but slides 2-N are interchangeable wallpaper, the viewer swipes once and leaves. 2026 IG and LinkedIn ranking (saves, sends, swipe-through) requires dependency: slide N+1 must extend slide N's hook for the swipe to compound. This is the gap between 6.60% LinkedIn engagement and the 1.6% baseline.

The judge sees the carousel as **a composed grid PNG** (one row per 3 slides; whole carousel in one frame) + extracted on-image text + caption/alt-text as parallel text input. Vision + text composite: a calendar prop appearing in slides 2/3/4 forming a timeline arc is a visual dependency that text alone cannot see.

- **Score 1:** Slides unrelated — five myths about one topic with no compounding, or 10 disconnected images sharing only a brand stamp. No CTA on the last slide, or close is "thanks for reading" or "follow for more" (algorithmically dead in 2026 per Mosseri). Judge confirms it could shuffle slides 2 through N-1 and the read would not noticeably change.
- **Score 3:** Slides share topic and visual identity but order is partially interchangeable — three slides could swap without breaking coherence; OR slides build but the last-slide CTA is generic ("learn more") not naming a concrete action (save, share-to-role, comment keyword that triggers a DM, swipe back).
- **Score 5:** Each interior headline references / continues / contradicts the prior — permuting slides 2 through N-1 demonstrably breaks the read (judge tests this by simulating one shuffle). Slide 1 is a falsifiable claim or stance (complete sentence with a verb), not a topic label. Slide N is a concrete non-"follow-me" CTA naming a specific action with explicit output. Visual continuation (recurring prop, colour anchor, layout grid) reinforces the arc.

**Format conditional.** Fires on ig_carousel and li_doc_carousel only. Skips for hero_banner and ad_static.

**Closing.** Read slide headlines in order. State the arc in one sentence. Identify two slides whose order matters and explain why a swap would break the read. Then score.

### IMG-3 (essential, pitfall, deterministic — auto-cap) — Format compliance

**Evaluate this composed image set for ONE quality:** Does the output match the declared platform-format spec exactly — slide count window, aspect, safe-zone, and (for ad_static on Meta) the 20% text-overlay budget?

Format failure is the cheapest auto-reject in the pipeline. A 4-slide LinkedIn doc sits below the 7-slide save peak; a 12-slide IG exceeds the platform cap; a 16:9 hero cropped to 4:5 puts critical content under the IG overlay; a Meta ad with 40% text is rejected at upload. **Deterministic; runs before the vision judge.** Format violations cannot be offset by visual quality.

Parameterised by `format` on the fixture frontmatter (ig_carousel, li_doc_carousel, hero_banner, ad_static); reads platform constraints from `configs/image_engine/format_specs.yaml`:

```
ig_carousel:        slides 2-10, aspect 1080x1080 or 1080x1350, bottom safe-zone 110px
li_doc_carousel:    slides 7-10 (save peak), aspect 1080x1350, file format PDF
hero_banner:        single surface, aspect per brand-style-guide
ad_static:          single surface, aspect per platform, Meta text-overlay <=20% canvas
```

- **Score 1 (auto-cap fires; overall fixture capped at 4):** Slide count outside the platform window; mixed aspect ratios across slides; wrong file format (PNG where PDF required); critical content under the IG bottom-110px overlay; for ad_static on Meta, text region area >20% of canvas (Pillow bounding-box union / canvas area).
- **Score 3:** Single-slide deviation in a multi-slide set (eg. one slide of 9 runs <5% off the 1080x1350 grid); bulk ships, no cap.
- **Score 5:** All format constraints met. Slide count in band. Aspect uniform. File format matches. Critical content inside the centre 80% safe zone. For ad_static, text overlay below 20%.

**When the cap fires.** Confirmed format violation → **auto-cap at score 1** for IMG-3 + **overall fixture capped at 4**. Deterministic (Pillow/skia measures canvas, slide count, mime, text-region area). Vision judge does not adjudicate format.

**Closing.** Report measured slide count, aspect, file format, and (for ad_static) text-overlay %. Compare against declared spec. If any out of spec, fire the cap.

### IMG-4 (essential, deterministic + vision) — Brand consistency

**Evaluate this composed image set for ONE quality:** Do logo placement, colour palette, and typography match the client brand-style-guide consistently across all slides?

Brand consistency turns a single-shot visual into a stamp the audience recognises. Phase B B9 anchors: fixed-position brand mark below 8% canvas, palette discipline below 3 swatches per slide, typography hierarchy below 2 faces + 3 sizes per slide. 2026 brand-system literature (Tenet, Venngage, Shopify): consistency is the line between professional and ad-hoc; senior B2B buyers (DWF audience) drop trust on visual inconsistency within the first carousel they see.

**Cross-references** `configs/brand/<client>/style_guide.yaml`. Schema:

```
palette:        list of hex swatches with Delta-E tolerance (default <10)
typography:     {headline_face, body_face, allowed_sizes}
logo:           {asset_path, max_canvas_fraction, allowed_corners}
```

Without a populated style_guide.yaml the judge **abstains** (declares "not yet scoring") rather than scoring against an empty rule list — failure-loud, per storyboard's SB-12/SB-15 pattern. Brand-style-guide is normative; this rubric invents no palette/typography rules.

Two-pass: (a) deterministic — k-means cluster slide to 5 colours, count those within Delta E < 10 of declared swatches; measure logo bbox-ratio; OCR type samples and match against declared faces. (b) vision — judge confirms qualitative cross-slide consistency on the composed grid.

- **Score 1:** Logo varies in size, position, or colour across slides (10% top-left on slide 1; 3% bottom-right on slide 5; missing on slide 7). More than 3 colours per slide OR off-palette swatches failing Delta E. 4+ typefaces or sizes break hierarchy. Set does not read as one brand.
- **Score 3:** One slide deviates but the rest reads as the brand — logo moves on one slide; OR one slide introduces a 4th palette colour but others stay disciplined. Drift visible, recognition intact.
- **Score 5:** Logo constant across slides (within 5% positional tolerance; <8% canvas area; same corner). Per-slide palette ≤3 swatches, all within Delta E < 10 of declared palette. Typography ≤2 faces + ≤3 sizes per slide, all matching declared brand families. Set reads unambiguously as the client.

**Closing.** For each slide, report: logo position + canvas fraction; palette swatch count + Delta E match; typeface + size count. Compare against style_guide.yaml. Note drift slide-to-slide.

### IMG-5 (essential, pitfall, vision — auto-cap on 2+ confirmed tells) — AI-slop avoidance

**Evaluate this composed image set for ONE quality:** Are there confirmed geometric/count-based AI-generation tells that the 2026 audience reliably detects and that trigger a measurable trust penalty?

Phase B: AI-slop fatigue is measurable in 2026 — public detection accuracy moved from coin-flip (2023) to >75% (Kellogg/CyberGuy/Insight). Brands using obviously-AI imagery pay a trust penalty that compounds: audience identifies the artifact as AI-generated, discounts brand signal, screens out subsequent posts. Load-bearing for Klinika (medical content, trust is the product) and DWF (B2B, senior buyers screen on professionalism). Written in terms of physically observable tells, not "this looks AI" — judge must cite the tell by region.

**Tell catalogue (2+ from this list → cap):**

a. **Hand anomaly:** Visible hand with not exactly 5 fingers (4, 6, 7), OR fused fingers, OR thumb in structurally impossible position.
b. **Pupil anomaly:** Symmetric pupil reflections with no environmental detail (both pupils show same generic round highlight) — real photography reflects environment asymmetrically.
c. **Skin anomaly:** Porcelain-smooth skin with no pores, stray hair, or micro-imperfection — especially in close-up portraits.
d. **In-image text malformation:** Signage / t-shirts / in-frame text containing non-letter glyphs, malformed letterforms, or non-words in the declared language.
e. **Shadow inconsistency:** Two+ subjects in same scene with shadows pointing different directions, OR a subject with no shadow when lighting clearly establishes a single light source.
f. **Edge artifact:** "Halo" blur at subject-background boundary (1-3px soft ring where generative compositing leaks), OR hard mask edge not respecting hair / fabric strands.
g. **Default-Midjourney aesthetic:** Cyberpunk-neon-alley palette without compositional reason, glossy-no-stray-strand hair, perfect-symmetric face, "epic dramatic lighting" applied universally.

- **Score 1 (auto-cap; overall capped at 4):** Two or more confirmed tells from the catalogue. Judge cites each by slide and region.
- **Score 3:** One minor tell — one slightly-off shadow, one over-smooth skin pass, one suspect edge — rest reads as plausibly real or as deliberately stylised. Risk present but bounded.
- **Score 5:** Zero tells. Humans (if any): 5 fingers per visible hand, asymmetric environmental pupil reflections, visible pores or stray hair, clean subject-background edges. In-image text correctly formed. Shadows consistent with single declared light source. No default-AI aesthetic.

**Stylised-illustration carve-out.** If the slide is deliberately stylised (vector, line drawing, infographic — no photorealistic claim), the catalogue does not apply (no expectation of pore detail on a vector face). Judge confirms photoreal-vs-stylised first. Cap fires only on photorealistic surfaces with confirmed tells.

**When the cap fires.** 2+ confirmed tells on a photorealistic surface → **auto-cap at score 1** + **overall capped at 4**. One tell = score 3 (warning, no cap). Zero tells is the only path to 5.

**Closing.** For each photorealistic slide, walk tells (a)-(g) one by one. Cite each confirmed tell by slide and region with one quoted visual phrase. Count tells. Apply the cap rule. If stylised, declare it and skip.

### IMG-6 (important, vision on downscale) — Thumbnail legibility

**Evaluate this composed image for ONE quality:** At a 256×320 downscale, is the primary headline legible without enlargement and is the dominant element identifiable as a single subject?

Phase B B3: IG explore and LinkedIn feed render carousels at ≤320px before interaction; the 2026 distribution lever flows through that surface as much as through the primary render. A composition that works at 1080px but fails at 256×320 loses the explore-tab and the LinkedIn-feed pre-tap impression. Judge runs on a downscaled rendering (Pillow lanczos resample to 256×320) and applies legibility anchors to that surface.

- **Score 1:** At 256×320, primary headline unreadable (type too small, contrast <3:1, font weight too thin). Dominant element unidentifiable (mixed colour blob, three competing shapes). Scrolling the explore tab gets no signal.
- **Score 3:** At 256×320, headline reads only with effort — squint required or reads after element resolves. Element identifiable but takes longer than 1.5s scroll budget.
- **Score 5:** At 256×320, primary headline legible without enlargement (judge can read and quote the string from the downscale). Dominant element identifiable as a single subject in under 1 second. Composition survives the secondary distribution channel.

**Cross-reference.** IMG-1 grades scroll-speed legibility on the primary feed surface; IMG-6 grades it on the thumbnail. Not redundant: a slide can pass IMG-1 and fail IMG-6 if the headline is 16pt at full-size.

**Closing.** Quote the headline as read from 256×320. Name the dominant element. Confirm both legible at thumbnail. Then score.

### IMG-7 (important, text) — Alt-text quality

**Evaluate the alt-text strings for this composed image set for ONE quality:** Is each slide's alt-text one declarative sentence naming the subject and key visual elements, distinct from the on-image headline?

Phase B B12: alt-text serves screen readers (accessibility), search indexing (discoverability), IG content classification (2026 algorithm reads alt-text for distribution signals). Duplicating the on-image headline gives the algorithm one signal where it could give two; keyword-stuffing gives a low-quality signal.

- **Score 1:** Alt-text empty, OR keyword-stuffed ("Botox myths Klinika Warszawa best dermatologist 2026"), OR verbatim duplicate of the on-image headline.
- **Score 3:** Present and partially descriptive but omits a key visual element (eg. describes the headline but not the anatomical diagram below it), OR partially duplicates the headline with one new word.
- **Score 5:** One declarative sentence per slide naming subject + key visual elements — distinct from the on-image headline and from other slides' alt-text. Example: "Anatomical diagram of skin layers showing dermis and epidermis with hyaluronic acid filler placement marked in blue." Vision judge confirms match to rendered image.

**Cross-reference.** Alt-text strings live in fixture metadata alongside rendered images. If the alt-text field is absent or null, Score 1 (missing alt-text is the failure mode, not a missing-data exception).

**Closing.** For each slide, quote the alt-text. Compare against the rendered image. Confirm one declarative sentence, named subject, named visual element. Note duplication with the headline.

### IMG-8 (essential, pitfall, deterministic + vision — auto-cap on match) — Client compliance

**Fires when** `compliance_regime` is set on the fixture frontmatter (`medical_pl` or `legal_pl`).

**Evaluate this composed image set for ONE quality:** Does the rendered content stay inside the declared compliance regime — no statutory violations on visible imagery, on-image text, or alt-text?

Phase A flags `medical_pl` and `legal_pl` as cross-cutting compliance regimes applied to every content-for-publish lane. Image content has a sharper compliance edge than text because **imagery itself** is regulated under Polish medical-device advertising law (eff. 1 Jan 2023): before/after patient images, needle/cannula/procedure depictions, and superlatives are statutorily disallowed for Klinika. DWF visual surface is narrower (no solicitation overlays, no fee mentions, no contingent-fee framing) but legal exposure is the same. Judge catches violations in the loop so the human pre-publish gate doesn't have to.

**Cross-references** `configs/compliance/{medical_pl,legal_pl}/rules.yaml`. Shape:

```
medical_pl:
  visual_blocklist:
    - before_after_patient    # ban on metamorfoza imagery
    - needle_cannula_procedure  # ban on wyrob medyczny depiction
    - patient_testimonial_image
  text_blocklist:
    - superlative_patterns    # "najlepszy", "najnowoczesniejszy", "spektakularne"
    - numeric_result_promise  # "redukcja zmarszczek o 90%"
    - pom_names               # POM blocklist: Botox, Dysport, Vistabel, Azzalure

legal_pl:
  visual_blocklist:
    - solicitation_overlay    # contact buttons, phone numbers, email
    - fee_display
  text_blocklist:
    - solicitation_verbs      # "zatrudnij DWF", "skontaktuj sie, aby kupic"
    - fee_mentions
    - case_specific_advice
    - disparaging_competitor
```

Rule-file content is operator-loaded after legal review (Resolve-Before-Planning #2). Until populated, IMG-8 fires in **shape-only mode**: judge confirms the cross-reference path exists, declares "not yet scoring," abstains.

Two-pass: (a) deterministic regex against on-image text (OCR-extracted) + alt-text strings; (b) vision pass against rendered imagery for visual_blocklist items.

- **Score 1 (auto-cap; overall capped at 4):** Confirmed violation quoted from imagery, on-image text, or alt-text. Judge cites violating evidence (visual region or quoted string) and names the rule category matched. Match triggers cap regardless of qualitative read.
- **Score 3:** No explicit violation but content so cautious it loses informational value (Klinika carousel saying "we can't talk about specific brands" three times; DWF closing so vague it doesn't ask the buyer-side question). Compliance-clean, useless.
- **Score 5:** Useful, specific, compliance-clean. Names what *can* be named (filler chemistry, hyaluronic acid, post-procedure timelines, statute references, dated regulatory events). Avoids what cannot (POMs, results, comparisons, solicitation, fees). The avoidance doesn't show — content stays peer-useful at Dr. Maria's or the partner's register.

**Cap requires concrete evidence.** Vague evidence ("the carousel mentions Botox" without quoted string) does not trigger the cap — the cap requires evidence the human reviewer could verify in 5 seconds (quoted string or named visual region).

**Closing.** Scan on-image text and alt-text against each text_blocklist category. Scan rendered imagery against each visual_blocklist category. If any match, quote the violation or cite the visual region. Only then assess the qualitative dimension.

---

## Section 3 — Vision-judge architecture spec

**Pattern reuse.** Image_engine extends `autoresearch/archive/v006/scripts/render_judge.py`: Gemini 2.5 Flash multimodal (image bytes + prompt), JSON-array output `{criterion, score, rationale}`, graceful no-op when `GEMINI_API_KEY` is unset or `google-genai` is unavailable, env-var lane allowlist. Image_engine module mirrors that shape.

**Per-slide vs whole-carousel firing:**

| Criterion | Surface                                         | Why                                                  |
|-----------|-------------------------------------------------|------------------------------------------------------|
| IMG-1     | slide 1 PNG (in isolation)                      | First-slide arrest graded against the first frame alone — viewer has not seen slide 2 yet. |
| IMG-2     | composed grid PNG (whole carousel)              | Arc requires the judge to see all slides simultaneously for dependency + permutation. |
| IMG-3     | metadata + per-slide PNGs (no vision call)      | Deterministic — Pillow/skia measures canvas, count, format. |
| IMG-4     | composed grid PNG + per-slide deterministic     | Cross-slide consistency requires the grid view; deterministic palette/logo feeds qualitative read. |
| IMG-5     | per-slide PNG (each photorealistic surface)     | Tells are slide-local; a clean slide 3 does not excuse a six-finger slide 7. |
| IMG-6     | slide 1 PNG downscaled to 256×320               | Thumbnail legibility is a property of the first-impression surface. |
| IMG-7     | alt-text + per-slide PNG                        | Text judge with vision-confirm. |
| IMG-8     | rendered imagery + OCR text + alt-text          | Deterministic regex on text; vision confirm on imagery. |

For a 9-slide carousel: 1 grid call (IMG-2 + IMG-4), 9 per-slide calls (IMG-5), 1 first-slide call (IMG-1 + IMG-6 batched on the same slide-1 PNG), plus text-only for IMG-7. Total Gemini calls per carousel ≈ 11 (1 grid + 9 per-slide + 1 first-slide). Hero banner and ad_static: 2-3 calls total.

**Allowlist mechanism.** `render_judge.py` already implements `RENDER_JUDGE_LANES_ALLOWED` — comma-separated env var gating which lanes can upload to Gemini's consumer endpoint. Image_engine extends this: customer carousel content for Klinika and DWF embeds clinic interiors, named-doctor portraits, partner imagery operators may not want uploaded without explicit decision. Default allowlist stays `geo,competitive,monitoring,storyboard`; image_engine is **opt-in only** — operators add `image_engine` when ready. Until opt-in, vision judge declines gracefully and the lane falls back to deterministic checks only. Preserves the v006 precedent: customer visual data does not move through consumer Gemini without an operator decision.

**Cost.** Gemini 2.5 Flash multimodal ≈ USD 0.10 per million input tokens; a 1080×1350 image encodes ≈ 1300 tokens. Per-carousel: ~11 calls × (1300 image + 500 prompt + 200 output) ≈ 22000 tokens ≈ USD 0.002. Across 50-fixture calibration corpus: ~USD 0.10. **Cost is not the bottleneck; latency is** — 4-8s per Flash call, 11 calls serial = 60-90s per carousel. Judge runs fan out per-slide calls in parallel with a semaphore of 4-6 concurrent Gemini requests.

---

## Section 4 — Implementation notes

**New LaneSpec entry.** `lane_registry.LANES` gains `image_engine`: format dispatch field (`ig_carousel | li_doc_carousel | hero_banner | ad_static`), compliance_regime field (`null | medical_pl | legal_pl`), brand reference field (`configs/brand/<client>/style_guide.yaml`), rubric ID list `[IMG-1..IMG-8]`, hard-gate set `{IMG-3, IMG-5, IMG-8}`. Lane signature follows the existing 4 workflow lanes pattern (geo, competitive, monitoring, storyboard) — no master-plan precedent needed (simplest-precedent pattern from Phase A: "5th and 6th lane added without master plans").

**New rubric IDs.** `src/evaluation/rubrics.py` gains `IMG-1` through `IMG-8` with prose as constants imported by the judge module. RUBRIC_VERSION hashes over rubric prose + brand-style-guide content + compliance rule-file content (per storyboard SB-12/SB-15 precedent): without that, the score cache returns stale verdicts when a rule or palette changes.

**Brand-style-guide schema (net-new structural input).** `configs/brand/<client>/style_guide.yaml` is authored per client:

```
palette:
  - hex: "#0B1F3A"
    name: "DWF navy"
  - hex: "#7E8B9A"
    name: "DWF graphite"
typography:
  headline_face: "Source Serif Pro"
  body_face: "Inter"
  allowed_sizes: [12, 18, 36, 64]
logo:
  asset_path: "configs/brand/dwf/logo.svg"
  max_canvas_fraction: 0.08
  allowed_corners: ["bottom-right"]
delta_e_tolerance: 10
```

Operator-authored, version-controlled. IMG-4 reads it; without it the judge abstains.

**Compliance regime integration.** IMG-8 cross-references the same compliance rule files storyboard's SB-12/SB-15 use — `configs/compliance/{medical_pl,legal_pl}/rules.yaml`. Resolve-Before-Planning #2 covers rule-file *content*; this spec covers *shape*. The **visual blocklist** (before/after, needle, fee display, solicitation overlay) is new — text-only lanes don't need it — so the rule-file schema is extended for image lanes specifically.

**Static-image composition module.** v1 brainstorm R12 specifies Pillow/Cairo/skia as net-new infrastructure. Judge is downstream of composition — without a composition module there is no PNG to judge. Most expensive net-new dependency in the lane; spec assumes composition lands first.

**RUBRIC_VERSION hash invalidates on:** (1) IMG-1..IMG-8 prose changes; (2) per-format firing table changes; (3) `configs/brand/<client>/style_guide.yaml` content hash changes; (4) `configs/compliance/{medical_pl,legal_pl}/rules.yaml` content hash changes. Without (3)+(4), score cache returns stale verdicts after rule/palette updates and ships non-conforming visuals.

**Deterministic pre-checks.** Format compliance (IMG-3), palette/logo measurement (IMG-4 det pass), OCR text extraction (IMG-7/-8 text pass), downscale rendering (IMG-6) all run in the structural gate **before** the vision judge. Format violation rejects fixture without spending Gemini calls. Judge prose carries ceiling; deterministic checks carry floor.

---

## Section 5 — Klinika + DWF demo specifics

**Klinika "5 myths about Botox" educational IG carousel** (`format: ig_carousel`, `compliance_regime: medical_pl`). 9-slide @ 1080×1350. Slide 1: oversized "MIT 1" numeral + anatomical illustration (vector — IMG-5 catalogue skips, stylised). Slides 2-8: one myth + one-sentence correction + one cited source. Slide 9: "Konsultacja — link w bio" CTA. Brand stamp bottom-right 6% canvas across all 9. Zero patient imagery. Load-bearing failure: **IMG-8 (medical_pl)** — fixture must NOT name "Botox" anywhere (POM blocklist), must not depict needles / cannulas / procedures (visual blocklist), must not include before/after patient imagery. Brief uses "toksyna botulinowa" or "neurotoxin" instead. If "BOTOX" appears, IMG-8 caps at 1 → overall caps at 4.

**DWF KSeF timeline LinkedIn document carousel** (`format: li_doc_carousel`, `compliance_regime: legal_pl`). 9-slide PDF @ 1080×1350. Slide 1: "KSeF: 1 lutego 2027 — 6 rzeczy, które musisz wiedzieć dzisiaj" (dated, falsifiable, complete sentence). Slides 2-8: one statutory fact + named citation (komunikat MF nr 7/2026, ustawa z dnia X) + horizontal timeline diagram. Slide 9: "Pełen przewodnik [link] — informacja prawna, nie stanowi porady." DWF navy/graphite palette; one serif headline + one sans body face; logo at 6% bottom-right across all slides. IMG-2 arc: timeline depends on chronological slide order, permutation breaks read. Load-bearing failure: **IMG-8 (legal_pl)** — fixture must NOT include "skontaktuj się z nami", phone numbers, email addresses, or fee references on any slide. Closing slide phrases next step as a question or links to a free explainer (informational), not solicitation. If any slide has a "Contact DWF" overlay or solicitation verb, IMG-8 caps.

**Klinika hero banner** (`format: hero_banner`, `compliance_regime: medical_pl`). Single surface @ brand-style-guide aspect. Editorial doctor portrait in clinical environment with NO procedure in frame, OR stylised abstract skin-layer illustration. Focal element >40% canvas (doctor's face or central illustration). Brand stamp at 6% canvas. Factual headline "Konsultacja dermatologiczna — Klinika Melitus" + one informational subhead. IMG-2 skips. IMG-1 / IMG-3 / IMG-4 / IMG-5 (photoreal portrait → full catalogue check) / IMG-6 / IMG-7 / IMG-8 all fire.

**Klinika ad_static** (`format: ad_static`, `compliance_regime: medical_pl`). Meta single-image ad. IMG-3 enforces the Meta 20% text-overlay rule (deterministic OCR text-region union / canvas area < 0.20). IMG-1 first-slide stop-scroll. IMG-5 if photoreal. IMG-8 (medical_pl) — no POM names, no result promises, no superlatives in on-image text or alt-text.

---

## Section 6 — Validation plan

Image_engine has no existing variant corpus to calibrate against. Validation runs on the **first 5 composed visuals per client** (Klinika + DWF) once composition module ships and brand-style-guide + compliance rule files are populated. Five-fixture anchor matches storyboard's Phase D and the simplest-precedent pattern from existing lanes.

**V1. IMG-1 stop-scroll calibration.** 5 Klinika + 5 DWF fixtures. Operator independently rates each first slide on binary "would I stop scrolling here?" Run IMG-1 against the same slides. Expected: ≥4 of 5 per client correlate (Score 5 → operator yes; Score 1 → operator no). Drift >2 of 5 → geometric anchors miss what the operator perceives; re-anchor against the operator's named stop-trigger feature.

**V2. IMG-5 AI-slop detection on synthetic slop.** Compose 3 deliberate slop fixtures: (a) hero banner with photoreal portrait, one hand has 6 fingers; (b) IG carousel slide 4 with porcelain skin + symmetric pupil reflections; (c) ad_static with a t-shirt that says "DRMATOLGY KLNIKA" (malformed text). Expected: all 3 → Score 1 + cap; judge cites each tell by region. Drift → catalogue too narrow or vision misses geometric anomalies; tighten tell descriptions.

**V3. IMG-8 auto-cap on synthetic Klinika before/after.** 5-slide carousel where slide 3 shows a before/after patient face composition. Expected: IMG-8 = 1 + cap + overall capped at 4; judge cites "before/after patient image, slide 3" as visual_blocklist match. Drift → rule-file content does not align with what vision can recognise; refine the visual_blocklist entry (eg. "two adjacent photographs of the same face under contrasting lighting or state").

**V4. IMG-3 format auto-cap on out-of-spec submission.** 12-slide IG carousel (exceeds 10-slide cap). Expected: Score 1 + cap + overall capped at 4. Pillow-side check; drift = bug in deterministic check, not calibration.

**V5. IMG-2 arc dependency on shuffled middles.** Take Klinika fixture 1 ("5 myths"). Permute slides 4/5/6 in the JSON manifest, regenerate grid, run IMG-2. Expected: judge identifies the shuffle as coherence break ("MIT 4" content now under "MIT 6" header) → Score 3 or 1. If judge scores 5, arc anchor isn't grading — judge is treating slides as independent. Re-anchor by requiring the judge to read headlines in order + state the arc in one sentence as part of the prompt.

**V6. Brand-consistency drift across slides.** Take DWF fixture 1 (KSeF timeline). Move logo from bottom-right to top-left on slide 5 only. Expected: Score 3 + evidence citing slide 5 logo position. If judge scores 5, cross-slide consistency isn't firing — confirm IMG-4 vision pass receives the composed grid PNG, not per-slide PNGs (per-slide hides positional drift).

**Promotion gate.** All 6 V-tests pass before image_engine moves from experimental to ship-eligibility. Fixture scoring 5 across the board on first run is a calibration smell — spot-check evidence strings against fixture content. Cap criteria (IMG-3/-5/-8) must demonstrate deterministic auto-cap on synthetic violations; discriminator criteria (IMG-1/-2/-4) must demonstrate operator-correlation on ≥4 of 5 per client.

---

**End of spec.** Implementer prerequisites: (a) author `configs/brand/<client>/style_guide.yaml` per client before IMG-4 fires non-abstain; (b) wait for compliance rule files at `configs/compliance/{medical_pl,legal_pl}/rules.yaml` per Resolve-Before-Planning #2 before IMG-8 fires non-abstain; (c) ship the static-image composition module (Pillow/Cairo/skia per v1 brainstorm R12) before any fixture renders; (d) extend `RENDER_JUDGE_LANES_ALLOWED` to include `image_engine` only after operator opt-in to Gemini upload of customer visual content.
