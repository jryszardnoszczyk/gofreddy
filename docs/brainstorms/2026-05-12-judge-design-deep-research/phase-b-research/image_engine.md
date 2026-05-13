# image_engine — Phase B research

Lane: composed static visuals (PNG/JPG/SVG) for IG carousel, LinkedIn document carousel, hero banner, ad static. Clients Klinika Melitus (medical, compliance-bound) and DWF Poland (legal-explainer, compliance-bound). fal.ai for generation + Pillow/Cairo/skia for composition. Judged by vision-judge (Gemini 2.5 Flash pattern from `autoresearch/archive/v006/scripts/render_judge.py`), deterministic format checks, and a text-judge for alt-text and arc semantics.

Raw tweet input was thin (only Chris Do's timeline returned, text-aphorisms not carousels), so this leans on web research.

## 1. Top 9-tier signals (excellent static visual content in 2026)

### IG carousel

1. **First-slide pattern-break composition.** Oversized single word/numeral, off-grid asymmetric crop, or one high-contrast object on negative space. Source: Mentionlytics + Socialinsider via SocialBee / Buffer 2026. Mechanism: feed scroll runs 3–4 posts/sec; one dominant element resolves under 2s, a busy slide doesn't. Judge: vision — "Score 5 if exactly one element occupies the optical centre and exceeds 40% of slide area with no competing element above 25%; Score 1 if three or more elements compete at similar visual weight."
2. **4:5 portrait (1080×1350) frame utilisation.** Designed-for-portrait, not square-cropped-from-landscape. Critical content stays inside the centre 80% safe zone (nothing in the bottom 110px IG overlay strip). Source: TrueFuture / TryMyPost 2026 IG sizing. Mechanism: portrait occupies more vertical feed real estate; bottom-strip overlap clips the hook. Judge: deterministic ratio + bottom-strip pixel budget.
3. **Hook readable at thumbnail (≤320px).** Headline survives the explore-tab render. Source: Imagine.art + Bannerbear 2026 (mobile renders 120–320px). Mechanism: if a hook only reads at 1080px, the slide loses the secondary distribution channel. Judge: vision on a 256×320 downscale — "Score 5 if the primary headline is legible without enlargement; Score 1 if unreadable."
4. **Last slide is an explicit non-'follow-me' CTA.** Names a concrete next action that compounds (save, share-to-role, comment keyword that triggers a DM, swipe back). Source: Buffer 2026 + Mosseri confirmed signals (sends, saves > likes). Mechanism: "follow for more" no longer generates engagement velocity; saves and DM-sends are the highest-weighted 2026 ranking signals. Judge: text on slide-N copy — "Score 5 if CTA names a concrete action with named output; Score 1 if 'follow for more' or absent."

### LinkedIn document carousel

5. **7–10 slides, portrait (1080×1350) PDF.** Save-rate peak per Oktopost / postunreel.com 2026 benchmarks (6.60% engagement at 7, +22% reach at 10 vs 3). Mechanism: <7 doesn't justify a save, >12 drops completion. Judge: deterministic slide-count + aspect-ratio + PDF mime check.
6. **Slide 1 is a falsifiable claim, not a topic label.** "KSeF will not be ready for 1 Feb 2027 — three reasons" vs "KSeF — overview". Source: Postiv AI / SocialPilot 2026 examples. Mechanism: a stance triggers the dispute reflex that converts impressions into swipes; a label doesn't. Judge: text on slide-1 — "Score 5 if a complete sentence with a verb and a falsifiable claim; Score 1 if a noun phrase or topic label."
7. **Save-bait density: one frameable insight per slide.** One quotable line in oversized type + one supporting diagram. Source: TryMyPost + Nealschaffer 2026. Mechanism: saves require per-slide modularity ("I want to come back to *this* slide"); paragraph walls get liked not saved. Judge: vision — "Score 5 if each interior slide has one bolded line >36pt in the upper 40% with supporting text ≤16pt below; Score 1 if every slide is uniform body copy."

### Hero banner

8. **Single subject, eye-line aligned to CTA.** Gaze or long-axis points toward the headline, not away. Source: Imagine.art 2026 layout. Mechanism: viewers follow gaze direction within ~200ms, increasing CTA fixation. Judge: vision — "Score 5 if the subject's directional axis points within 30° of the CTA; Score 1 if away."
9. **Brand stamp consistent without dominating.** Fixed position across banners, <8% of canvas, on-palette. Source: Tenet / Venngage / Shopify 2026 brand-system guides. Mechanism: consistency builds recognition; dominance reads as ad. Judge: deterministic logo bbox-ratio + colour Delta E <5 vs brand palette.

### Ad static

10. **Reads in 1.5s at platform thumbnail size.** Single product, single claim, single visual cue, single CTA — survives 1.5s IG / 2s LinkedIn render. Source: Mentionlytics + TryMyPost 2026. Mechanism: in-feed ad rendering is shorter than organic; complexity loses. Judge: vision with explicit 1.5s framing.
11. **Differentiated from generic AI aesthetic.** No DALL-E faces, no cyberpunk-neon-alley default, no porcelain skin, no impossible hands. Source: CyberGuy + Kellogg + Insight 2026 detection research. Mechanism: 2026 viewers reliably identify AI imagery and discount trust on identification. Judge: vision — "Score 1 if any of: (a) ≠5 fingers on a visible hand, (b) symmetrical pupil reflections with no environmental detail, (c) porcelain skin with no pores, (d) malformed text on a sign/shirt/object, (e) shadow direction inconsistent with single light source."

### Across formats

12. **Alt-text is one descriptive sentence per slide.** Names the depicted subject + key visual elements; not a keyword list, not the headline duplicated. Source: ixdf.org 2026 + platform accessibility docs. Mechanism: alt-text feeds screen readers, search indexes, and IG content classification. Judge: text — "Score 5 if one declarative sentence naming subject + key elements; Score 1 if empty, keyword-stuffed, or duplicates the on-image headline."
13. **Brand palette discipline: ≤3 swatches per slide.** No ad-hoc spot colours. Source: Tenet 2026. Mechanism: consistency reads as professional. Judge: deterministic k-means to 5 colours, count those within Delta E <10 of a palette swatch.
14. **Typography hierarchy: ≤2 faces, ≤3 sizes per slide.** One headline face, one body face, three discrete size steps. Source: Shopify 2026. Mechanism: more sizes destroy the size→importance heuristic. Judge: vision — "Score 5 if ≤2 typefaces and ≤3 sizes; Score 1 if 4+ of either."
15. **Carousel arc: slide N+1 depends on slide N.** Each headline references / continues / contradicts the prior; permuting middle slides breaks the read. Source: Postiv AI + Krumzi 2026 examples. Mechanism: dependency drives swipe-completion (the 2026 LinkedIn / IG ranking signal). Judge: text permutation test — "Score 5 if shuffling slides 2..N-1 breaks coherence; Score 1 if any interior slide is interchangeable."

## 2. Top 5-tier signals (mediocrity)

5-tier ships and gets some engagement; doesn't move the metric.

- Slide 1 is a **topic label** ("Top 5 KSeF mistakes") not a stance — competent, doesn't trigger swipe.
- Body slides **uniform** layout / sizes — designed, doesn't compel saves.
- Hook reads at full-size IG render but **fails at thumbnail** (16pt "hook" body copy).
- **One AI tell** survives (one porcelain-skin photo, one mangled sign). Trust dips subliminally.
- CTA is **"follow for more"** — algorithmically dead in 2026.
- **3–4 brand colours + accent colours** — over the "3 swatches" line, not chaotic.
- **6 slides** — under the 7-slide LinkedIn save-peak.
- **Alt-text duplicates the headline** — accessibility tick, no incremental discoverability.
- Hero subject **gazes off-canvas** with no compositional reason — eye exits frame.
- **Logo size varies** across the set (10% slide 1, 3% slide 5) — undermines stamping.

## 3. Slop patterns (1-tier)

- **Generic AI faces.** Porcelain skin, symmetric-no-detail pupil reflections, mismatched earrings, six-finger hands, glossy-no-stray-strand hair (Kellogg / CyberGuy / Insight 2026).
- **Cyberpunk-neon-alley default.** Midjourney / DALL-E un-directed style. Every 2026 viewer has seen it.
- **Stock photo + black translucent band + sans-serif overlay.** Pre-2020 LinkedIn default; ages the brand 5+ years.
- **Slide N+1 doesn't connect to slide N.** No arc, no compounding swipes, no save reason.
- **Brand inconsistency across slides.** Fonts / logo position / palette drift.
- **Text-on-image with no hierarchy.** All-caps body copy as "headline".
- **Klinika compliance violations.** Before/after patient image, superlatives, numeric result promises, needles/cannulas/procedure depiction. Legal exposure under Art. 14 + Ustawa o wyrobach medycznych (eff. 1 Jan 2023).
- **DWF compliance violations.** Solicitation, fee mentions, case-specific legal advice, contingent-fee framing.
- **Malformed text inside the image** (signage, t-shirts with non-letter glyphs). Reliable AI tell.
- **Inconsistent shadow direction.** Physics violation, common when overlaying generated subject on generated background.
- **Logo dominates** (>15% canvas) — reads as ad.
- **CTA absent** or replaced by "thanks for reading".

## 4. What separates 9-tier from 5-tier (per format)

**The binding constraint across formats is the first-slide-stop-scroll test.** "Would a scrolling viewer stop here?" must answer yes. Everything else is downstream.

- **IG carousel.** 9-tier breaks feed rhythm on slide 1 (asymmetric crop, oversized single element, unexpected colour). 5-tier uses a competent-but-conventional title card. Both ship; only 9-tier compounds, because the 2026 IG ranking signal is active dwell time + swipe-through velocity (TrueFuture / Buffer / Sprout 2026) and the swipe is triggered by the first-slide arrest.
- **LinkedIn document carousel.** 9-tier = falsifiable stance + per-slide modularity → high saves. 5-tier = topic label + uniform body slides → likes, no saves. The benchmark is 6.60% engagement at the 7-slide peak (postunreel.com 2026); 9 vs 5 ≈ the save-rate gap.
- **Hero banner.** 9-tier = single subject, directional axis pointing to CTA, brand stamp <8%, clean negative space. 5-tier = competent stock comp with no directional axis and a slightly oversized logo.
- **Ad static.** 9-tier reads in 1.5s, no AI tells. 5-tier reads in 3s with one tell, costing measurable trust.

**Vision-judge anchor design.** Anchors must be physically observable on a screenshot. "Feels premium" collapses to noise; "exactly one element exceeds 40% slide area and no competing element exceeds 25%" survives. The MDPI 2026 IQA study shows Claude-vision underperforms GPT-4o on no-reference quality; render_judge.py (Gemini 2.5 Flash) sits between them — write anchors for the weakest plausible judge (geometric / colour / count-based, not aesthetic). Decompose any aesthetic claim into ≥2 observable sub-properties.

## 5. Klinika + DWF specifics

### Klinika "5 myths about Botox" IG carousel

Allowed: stylised vector illustrations of skin layers / anatomy (educational, no patient image); clinic-interior editorial photo with NO procedure in frame; doctor portrait with named credentials in informational tone ("dr n. med. X, specjalista dermatologii"); text-only myth slides with one-sentence factual correction + cited peer-reviewed source; final CTA "Zapisz na konsultację" linking to a contact form.

Forbidden: before/after patient images ("metamorfoza") — direct violation of medical-device advertising ban (Marek Wasiluk / Sago Media / prawo.pl 2025–2026); superlatives ("najlepszy", "spektakularne"); numeric result promises ("redukcja zmarszczek o 90%"); needle/cannula/procedure depiction (the wyrób medyczny itself); patient testimonials.

Excellent shape: 9-slide carousel, slide 1 = oversized "MIT 1" + anatomical illustration; slides 2–8 = one myth + correction + citation each; slide 9 = "Konsultacja — link w bio". Brand stamp bottom-right, <8% area, identical every slide. Zero patient imagery.

### DWF KSeF timeline LinkedIn document carousel

Allowed: horizontal timeline of statutory dates (1 Feb 2027 obligatory KSeF, 1 Apr 2026 voluntary phase) — informational, sourced; process-flow diagram (invoice → KSeF → recipient → archiving); pre/post-KSeF comparison table; DWF brand stamp + author byline + "informacja prawna, nie stanowi porady" disclaimer; closing slide pointing to a free explainer.

Forbidden: solicitation ("zatrudnij DWF", "skontaktuj się, aby kupić"); fee or pricing mention; case-specific legal advice ("w sytuacji X powinieneś zrobić Y") — must read as general information; disparaging named-competitor comparisons.

Excellent shape: 9-slide PDF 1080×1350. Slide 1 = "KSeF: 1 lutego 2027 — 6 rzeczy, które musisz wiedzieć dzisiaj" (dated, falsifiable). Slides 2–8 = one fact per slide + statutory citation + diagram. Slide 9 = "Pełen przewodnik [link] — informacja prawna, nie stanowi porady". DWF navy/charcoal palette, one typeface family, identical layout each slide.

### Klinika hero banner

Allowed: editorial doctor portrait in clinical environment (NO procedure in frame), or stylised abstract visual (skin-layer illustration); brand stamp bottom-right; factual headline ("Konsultacja dermatologiczna — Klinika Melitus"); one informational subhead. No before/after, no needles, no superlatives, no patient image.

## 6. 2026 emerging signals

- **IG: sends + saves > likes.** Mosseri-confirmed 2026 ranking. Carousels get 55% more reach + 70% more saves than single images (Socialinsider via Buffer 2026). Implication: heavy judge weight on save-bait (signal 7) and explicit-CTA (signal 4).
- **LinkedIn document-post boost.** 6.60% engagement vs 1.6% baseline — ~4× lift (postunreel.com 2026). Portrait PDF 7–10 slides. Implication: hard preference justified.
- **AI-slop fatigue is measurable.** Public detection accuracy moved from coin-flip (2023) to >75% (2026) per Kellogg + CyberGuy + Insight research. Brands using obviously-AI imagery pay a trust penalty. AI tells (five-finger / pupil / porcelain / shadow / malformed text) are now a 1-tier risk, not a stylistic preference.
- **Composition over generation.** Visuals that don't register as AI-generated combine: real photography for humans/products; generated assets only for abstract/illustrative/texture roles; heavy manual composition over generated raster; shadow/light-direction consistency check; one style across slides (not "everything Midjourney can do"). This is the path for image_engine to NOT read as AI-slop while using fal.ai upstream.
- **Vision-judge state 2026.** GPT-4o leads no-reference IQA (MDPI 2026); Claude-vision underperforms; Gemini 2.5 Flash is the cost-effective middle. render_judge.py pattern is fine for evolution-loop cost; for promotion-gate evaluation an ensemble (Gemini 2.5 Flash + GPT-4o, or + Claude Opus when GPT cost is prohibitive) reduces single-judge bias.
- **Thumbnail-first.** IG explore + LinkedIn feed render carousels at ≤320px before interaction. Designs that pass at 1080px and fail at 320px lose the secondary distribution channel. The 256×320 downscale test (signal 3) is now table-stakes.

## 7. Implications for the judge — 8 candidate criteria

Each criterion: judge type, tier separated, anchors.

### IMG-1: First-slide stop-scroll (vision; 9-vs-5)
Slide-1 PNG in isolation.
- **5:** Exactly one element occupies the optical centre and exceeds 40% slide area; no competing element exceeds 25%; dominant element identifiable in <2s; headline legible at 256×320.
- **3:** One dominant element present but a competing element exceeds 25%, OR headline legible at 1080px but fails 256×320.
- **1:** Three+ elements compete at similar visual weight, OR no clear focal point, OR headline unreadable at 256×320.

### IMG-2: Carousel arc & dependency (text on extracted copy; 9-vs-5)
- **5:** Each interior headline references/continues/contradicts the prior; permuting slides 2..N-1 breaks coherence; slide 1 is a stance; slide N is a concrete non-"follow-me" CTA.
- **3:** Slides share a topic but order is interchangeable; CTA is generic.
- **1:** Slides unrelated; no CTA or "thanks for reading" close.

### IMG-3: Format compliance (deterministic; hard gate)
- **5:** Format matches declared target — IG ≤10 slides at 1080×1350 or 1080×1080; LinkedIn doc 7–10 at 1080×1350 PDF; hero per brand-guide ratio; ad per platform spec. All slides match each other in aspect ratio. No critical content in IG bottom-110px overlay.
- **1:** Slide count outside platform window (4-slide LinkedIn doc; 12-slide IG); mixed aspect ratios; wrong file format; critical content under the bottom-strip overlay.

### IMG-4: Brand consistency (deterministic + vision; 5-vs-1)
- **5:** Logo position+size constant (<8% area, same corner); ≤3 brand swatches per slide all within Delta E <10 of palette; ≤2 typefaces + ≤3 sizes per slide, all brand-guide families.
- **3:** One slide deviates but the set reads as the brand.
- **1:** Logo varies in size/position/colour; >3 colours per slide or off-brand swatches; ≥4 typefaces/sizes break hierarchy.

### IMG-5: AI-slop avoidance (vision; hard gate for trust-sensitive clients)
- **5:** No AI tells. Humans: 5 fingers per visible hand, asymmetric environmental pupil reflections, visible pores/stray hair, clean subject-background edges. Any in-image text correctly formed. Shadows consistent with single declared light source.
- **3:** Plausibly real but one minor tell (one over-smooth skin pass, one slightly-off shadow).
- **1:** Two+ tells from: (a) ≠5 visible fingers on a hand, (b) symmetric pupil reflections with no environmental detail, (c) porcelain skin no pores, (d) malformed in-image text, (e) conflicting shadow directions under one light, (f) "halo" blur at subject edge, (g) glossy-default-Midjourney aesthetic.

### IMG-6: Thumbnail legibility (vision on 256×320 downscale; 9-vs-5)
- **5:** At 256×320, primary headline legible without enlargement; dominant element identifiable as a single subject.
- **3:** Headline legible only with effort; element identifiable.
- **1:** Headline unreadable at 256×320 (too small, low contrast, or font weight too thin).

### IMG-7: Alt-text quality (text; 5-vs-1)
- **5:** One declarative sentence per slide naming subject + key visual elements; not a duplicate of the on-image headline.
- **3:** Present but partially duplicates the headline or omits the visual element.
- **1:** Empty, keyword-stuffed, or verbatim the headline.

### IMG-8: Compliance precondition (deterministic + text; hard gate, per client)
Klinika (medical_pl):
- **5:** No before/after patient imagery; no needle/cannula/procedure/wyrób medyczny depiction; no superlatives ("najlepszy", "najnowocześniejszy", "spektakularne"); no numeric result promises; informational tone.
- **1:** Any of the above present, or testimonial framing.

DWF (legal_pl):
- **5:** No solicitation ("zatrudnij nas", "skontaktuj się, aby kupić"); no fee/pricing mention; framed as edukacyjny/informacyjny; "informacja prawna, nie stanowi porady" disclaimer on close.
- **1:** Solicitation; fee/pricing reference; case-specific legal advice; disparaging named-competitor comparison.

### Judge composition notes

- **IMG-3 and IMG-8 are hard gates** — score 1 clamps the lane composite (format failure / legal exposure can't be offset by visual quality).
- **IMG-1, IMG-2, IMG-5, IMG-6** are the primary 9-vs-5 discriminators.
- **IMG-4, IMG-7** are 5-vs-1 hygiene checks.
- **Vision passes:** slide-1 in isolation for IMG-1 / IMG-5 / IMG-6; full carousel grid for IMG-4.
- **Cost:** Gemini 2.5 Flash is ~linear in slide count; budget ~7–10× a single-image call per carousel. Extend render_judge.py's `RENDER_JUDGE_LANES_ALLOWED` pattern to image_engine so customer content isn't uploaded to consumer endpoints without opt-in.
- **Anchor stress-test:** before promotion, run each anchor against 3 obviously-9 and 3 obviously-1 fixtures per format. The MDPI 2026 IQA study found Claude-vision weak on no-reference quality; geometric/count-based anchors score more stably than aesthetic ones in any ensemble that includes Claude.

Sources: Oktopost / Expandi / SocialPilot / Nealschaffer / SocialBee / postunreel.com / TryMyPost / Postiv / Dataslayer (LinkedIn carousel + algorithm 2026); TrueFuture / Mentionlytics / Resont / InstaCarousel / MarketingAgent / SocialHabit / Viraly / Krumzi (IG carousel 2026); Buffer / Later / Sprout / Hootsuite / Clixie (IG algorithm 2026); ThumbMagic / Bannerbear / Imagine.art / IxDF (thumbnail + readability 2026); Tenet / Shopify / Venngage / VersaCreative (brand-system 2026); Creativa.legal / adwokat-seidel.pl / Marek Wasiluk / prawo.pl / Sago Media / ktzr.pl / imagemed.pl / NIL (Polish medical-advertising ban 2023–2026); Kellogg / CyberGuy / Insight / GIJN (AI-image detection 2026); MDPI / DataCamp / LM Council / Vellum (vision-LLM benchmarks 2026); plus `autoresearch/archive/v006/scripts/render_judge.py` + v006 `programs/render-rubric.md` RND-1..5 anchors.
