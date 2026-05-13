---
name: site-quality-rubric
version: v1
created: 2026-05-13
owner: gofreddy
purpose: |
  Shared prose anchors for site-improvement evaluation. Consumed by:
  (1) the `site_engine` autoresearch lane (judges score variants against SE-1..SE-8),
  (2) the `compound-engineering:site-improvement` Claude Code skill (human + Claude iteration).
  Both surfaces read this file unchanged. Edit once, propagate both places.
status: source-of-truth
applies_to:
  - site_engine lane (per LaneSpec.rubric_ids = SE-1..SE-8)
  - site-improvement skill
license_note: |
  Calibration data sourced from the 2026-05-13 gofreddy.ai landing-page session
  (Jan Noszczyk, founder + builder). Treat as opinionated baseline; tune anchors
  per client when fixtures diverge from the calibration domain.
---

# Site Quality Rubric — v1

Eight axes (SE-1..SE-8). Each axis carries: operational definition, falsifiability
criterion, Score-3 failure modes (most diagnostic anchor — what "average" looks like
when graded honestly), and anti-gaming clauses (what scoring 5 does NOT permit).

Scoring scale: 1 (broken) · 3 (works but unremarkable) · 5 (genuinely strong).
Half-scores allowed for judge confidence; structural gates hard-fail before scoring.

Rubric anchors below are calibrated to **a section-level artifact** (hero, value_prop,
social_proof, faq, cta, pricing) — not full pages. Full-page composition is v1.5.

---

## SE-1 — Visual hierarchy + CTA prominence

**What it measures.** Whether eye flow lands at the primary CTA without conscious
effort. Includes: heading-size cascade, whitespace as separator, contrast direction
(primary CTA more saturated than supporting elements), reading-order matching
intent.

**Falsifiability.** Show the rendered screenshot to three readers in <3s each.
"Where does your eye go first / second / third?" Answers must converge on
{H1 / supporting copy / CTA} in that order for score ≥ 4. Disagreement = ≤ 3.

**Score-3 failure modes.**
- CTA visible but visually equal-weight to a supporting button.
- Three equal-size headlines competing for attention.
- A decorative element (illustration, screenshot) draws the eye before the headline.
- Whitespace is uniform — no visual grouping signals what belongs together.

**Score-5 anchors.**
- One clear primary CTA, visually distinct from any secondary action.
- Heading cascade descends in size + weight (H1 > H2 > body > caption).
- A visible "rest" of whitespace immediately above or after the CTA.
- Scan order matches intended reading order on first glance, verified at 3-reader test.

**Anti-gaming.** Cannot be earned by simply making the CTA huge or neon. Hierarchy
is RELATIVE — a strong CTA in a weak hierarchy still scores ≤ 3.

---

## SE-2 — Copy clarity + plain-English

**What it measures.** Whether a reader outside the client's domain can understand
what's being offered and what to do next, on first read, without a glossary.

**Falsifiability.** Read the copy to a friend in an unrelated profession. Ask:
"What does this company do? What would you have to do to use it?" Both answers
correct + given without re-reading = ≥ 4. Re-reading required, or wrong answer,
or "I'd have to look up these words" = ≤ 3.

**Score-3 failure modes.**
- Jargon that requires domain knowledge to parse (e.g., "fixtures", "rubric",
  "harness", "held-out", "autoresearch", "L1/L2/L3") presented without translation.
- Acronyms not expanded on first use (especially industry-internal ones).
- Sentences that pile three adjectives + a noun-phrase ("AI-native distribution-engineered
  marketing pipelines") and require the reader to disassemble.
- "Solutions", "platforms", "synergies", and other corporate-SaaS filler.

**Score-5 anchors.**
- A non-domain reader can paraphrase what's offered in their own words after one read.
- Sentences are short (avg < 18 words) and each conveys one fact.
- Technical terms appear only when they ARE the offering, and are immediately defined.
- The CTA verb is concrete ("book an audit", "see the demo") not abstract ("get started").

**Anti-gaming.** Cannot be earned by stripping all specificity. Concrete claims
("149 lenses across 9 dimensions") count as plain-English when paired with the
plain meaning ("we check 149 specific things"). Vague abstraction ("comprehensive
analysis") is NOT plain-English even if every word is short.

---

## SE-3 — Claim honesty + anti-overselling

**What it measures.** Whether every claim is something the client could survive
being asked to demonstrate. Distinct from copy clarity (SE-2): a claim can be
plain English AND dishonest.

**Falsifiability.** For each numeric, comparative, or capability claim on the
section: can the client produce the artifact backing it up within 24 hours?
("3-6× cheaper than the average agency" → produce the average-agency cost
calculation. "Hours per change" → produce a sample change log.)

**Score-3 failure modes.**
- Hedge language masking overstated claims ("up to N×", "as much as", "designed to").
- Unsubstantiated comparatives ("faster than", "better than", "leading", "best-in-class").
- Anthropomorphized agent capability ("autonomous", "intelligent", "thinking",
  "understands") when the actual mechanism is mechanical (LLM call + judge).
- "We" or "our" claims that conflate aspiration with what's actually shipped.

**Score-5 anchors.**
- Every number is concrete and sourced (e.g., "149 lenses · 9 dimensions" — backed
  by the rubric file in the audit pipeline).
- Capability claims describe MECHANISM ("AI agents draft, engineer + human review every output")
  not magic ("autonomous AI does the work").
- Anti-claims appear where appropriate ("not autonomous robots", "no auto-publish").
- Pricing / timeline / scope numbers match the contract / runbook / live ops state.

**Anti-gaming.** Cannot be earned by being maximally vague. A score-5 section is
honestly specific, not honestly silent.

---

## SE-4 — Voice persona fit

**What it measures.** Whether the section reads as if written by the client's
established voice persona, not a generic template. Distinct from SE-2 (clarity)
and SE-3 (honesty): a section can be clear and honest AND off-voice.

**Falsifiability.** Place the section's body copy next to 3 prior pieces of
voice corpus from the same client (`client_config.voice_persona.corpus_path`).
Run text-similarity (sentence-length distribution, contraction rate,
hedge-word frequency, sentence-opener variety). Distance to corpus centroid ≤
established threshold for the client = ≥ 4. Distance > threshold = ≤ 3.

**Score-3 failure modes.**
- Copy that reads as if written by a different brand. (Most common failure:
  generic-AI voice imposed over client persona.)
- Style anchors ignored when persona explicitly defines them
  (e.g., client persona says "never use exclamation marks" — section has 3).
- Hedge language alien to the client's voice (overly polished when the client
  is gruff; overly punchy when the client is contemplative).

**Score-5 anchors.**
- Section copy passes a blind-attribution test: a regular reader of the client's
  prior content identifies the section as the client's voice.
- Style anchors from `voice_persona.style_anchors` all respected.
- Sentence cadence (long / short alternation) matches corpus distribution.

**Anti-gaming.** Voice fit ≠ literal quote-stuffing. A section that copies prior
client sentences verbatim is plagiarism, not voice fit.

---

## SE-5 — Brand-token + aesthetic-fit

**What it measures.** Whether the visual treatment (colors, type, spacing,
motion) matches the client's `brand_tokens`. Distinct from SE-1 (hierarchy):
hierarchy can be strong on the wrong palette.

**Falsifiability.** Compare rendered section against `client_config.brand_tokens`:
all colors used appear in the token list (or are derived via documented
opacity/tint rules from the token list). All font-families appear in the
token list. Spacing uses the token grid. = ≥ 4 if all three pass. Any drift =
≤ 3.

**Score-3 failure modes.**
- A color introduced that's not in tokens (most common: a generic "AI blue"
  or "tech purple" that didn't exist in the client's prior identity).
- A typeface drift (Google Font default sneaking in alongside the brand's
  licensed family).
- Spacing values off the documented grid (e.g., 13px gap instead of token 16px).
- Motion / animation curves that don't match the brand's established kinetic
  language (over-bouncy when the brand is restrained; static when brand is
  motion-forward).

**Score-5 anchors.**
- Every color in the section maps to a `brand_tokens` entry.
- Every typeface in the section is from the client's token list (typically
  ≤ 3 families — sans, mono, optional one serif moment).
- Spacing uses ONLY token-grid values.
- Motion respects the client's established kinetic profile.

**Anti-gaming.** Cannot be earned by hiding off-brand color in opacity/blend modes.
Renderer extracts and checks all colors at full opacity.

---

## SE-6 — Accessibility + semantic structure

**What it measures.** Whether the section is usable by all readers, including
those using assistive tech, and whether the underlying HTML expresses what
the visual design implies.

**Falsifiability.** Run axe-core on the rendered section. Zero violations of
severity "serious" or "critical" = ≥ 4. ≥ 1 such violation = ≤ 3.
Plus semantic-structure check: every visual heading uses heading tags;
every interactive element is focusable; every image with non-decorative
content has alt text; color contrast ≥ WCAG AA on body copy.

**Score-3 failure modes.**
- Decorative `<div>`s used where `<button>` / `<a>` / `<nav>` would be semantic.
- Heading levels skipped (H1 → H3 with no H2).
- Interactive elements not keyboard-focusable.
- Text on background fails WCAG AA contrast (4.5:1 for body, 3:1 for large).
- Images carrying meaning have empty or missing alt text.

**Score-5 anchors.**
- Zero axe-core violations of severity ≥ "moderate".
- Semantic HTML matches visual structure 1:1.
- Keyboard-only navigation reaches every interactive element in reading order.
- Color contrast WCAG AA across body, AAA on critical CTAs.
- Animation respects `prefers-reduced-motion`.

**Anti-gaming.** Cannot be earned by adding `role="..."` overrides that disagree
with the underlying element. Audit checks both axe AND element-tag semantics.

---

## SE-7 — Performance

**What it measures.** Whether the section's weight + render cost is proportional
to what it delivers.

**Falsifiability.** Render section in isolation with `prefers-reduced-data` off.
Lighthouse-equivalent metrics: First Contentful Paint < 1.5s, Cumulative Layout
Shift < 0.05, Total Blocking Time < 200ms. All three met = ≥ 4. Any fail = ≤ 3.
Plus payload check: section's JS + CSS + images ≤ documented budget per
section type.

**Score-3 failure modes.**
- Unused JS dependencies imported (most common: a full animation library when
  CSS keyframes would suffice).
- Images served at desktop resolution to mobile.
- Layout shift from late-loading fonts or unsized images.
- Render-blocking external resources (third-party fonts without `font-display: swap`).

**Score-5 anchors.**
- Section payload ≤ 50KB compressed (typical section budget).
- All metrics within the documented budget for the section type.
- No third-party render-blocking resources.
- Animation uses CSS where possible, JS only when CSS can't express the motion.

**Anti-gaming.** Cannot be earned by deferring loads past the visible viewport in
a way that breaks the section's intent on slow networks. Budget applies to what
the user sees in the first 5 seconds, not what's lazy-loaded out of view.

---

## SE-8 — Anti-slop (does it look generated)

**What it measures.** Whether the section reads + renders as if a human cared.
The catch-all for "generic AI output" signals: stock gradients, three-icon
trios, generic "AI Solutions" / "Powered by AI" framing, formulaic
section-card-grids, palette that screams template.

**Falsifiability.** Place the rendered section in a 10-section "generic AI
landing page" mosaic. Have 3 reviewers point at the one that "looks
handmade." If the section is NOT the one picked = ≤ 3. If the section IS
the one picked = ≥ 4.

**Score-3 failure modes.**
- Three-icon trios with generic gradient strokes (the dead giveaway of 2024-25
  Tailwind boilerplate).
- Stock "abstract tech" hero illustrations (gradient meshes, dot-grid backgrounds
  with floating boxes, "AI orb" art).
- "We help you..." pattern leading paragraph copy.
- Six identical bordered cards, each with icon + title + 2-line description.
- Lime + purple + dark gradient (the AI-tool default palette of 2025).
- Stock testimonial-card grid with circular avatar placeholders.

**Score-5 anchors.**
- At least one element in the section that wouldn't fit any other client's site.
- A specific concrete claim or number that's clearly THIS client's truth.
- Hand-touch signals: an animated SVG with hover state, a hand-tuned curve, a
  quote that reads as something a specific person said.
- Palette + treatment that feels claimed (one strong accent + one supporting +
  neutral base) rather than templated (three equal accents + gradient mesh).
- ZERO of the Score-3 failure modes present.

**Anti-gaming.** Cannot be earned by adding random eccentricity. Score-5 requires
the section to feel SPECIFIC to this client, not generically weird.

---

## Cross-axis interactions

Some failure modes touch multiple axes. Examples:

- **"Autonomous AI" framing** — fails SE-3 (honesty: not actually autonomous)
  AND SE-8 (anti-slop: generic AI signal).
- **Generic gradient hero illustration** — fails SE-5 (off-brand) AND SE-8
  (anti-slop signal).
- **Heading-level skip with skipped semantic structure** — fails SE-1 (visual
  hierarchy) AND SE-6 (a11y).
- **Stock-photo testimonial cards with placeholder names** — fails SE-3 (honesty:
  implies real testimonials) AND SE-8 (anti-slop).

When two axes both fail on the same root cause, score each axis on that axis's
own criterion. Do not double-count or compensate.

## Scoring artifact format

Per variant, the judge emits:

```json
{
  "se_scores": {
    "SE-1": {"score": 4.0, "rationale": "...", "structural_pass": true},
    "SE-2": {"score": 3.5, "rationale": "...", "structural_pass": true},
    "SE-3": {"score": 4.5, "rationale": "...", "structural_pass": true},
    "SE-4": {"score": 3.0, "rationale": "...", "structural_pass": true},
    "SE-5": {"score": 4.0, "rationale": "...", "structural_pass": true},
    "SE-6": {"score": 5.0, "rationale": "...", "structural_pass": true,
              "axe_violations": [], "lighthouse": {"a11y": 100}},
    "SE-7": {"score": 4.0, "rationale": "...", "structural_pass": true,
              "fcp_ms": 980, "cls": 0.02, "tbt_ms": 110, "payload_kb": 42},
    "SE-8": {"score": 4.5, "rationale": "...", "structural_pass": true}
  },
  "composite": 4.06,
  "rubric_version": "site-quality-v1"
}
```

`rubric_version` matches the frontmatter `version` field so scored variants stay
attributable across anchor revisions.

## Revision policy

Material changes to anchors (new failure modes, raised thresholds, new
falsifiability tests) bump the `version` field. Pre-existing scored variants
remain valid against their original anchors — do NOT re-score historical fixtures
unless explicitly running a re-calibration cycle.

Editorial changes (typo fix, prose clarity, example replacement) do not bump
version.

## See also

- `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` — the lane
  implementation plan that wires this rubric via `LaneSpec.rubric_ids`.
- `compound-engineering:site-improvement` skill — the human + Claude iteration
  surface that consumes the same anchors.
- `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` — sibling rubric file
  (X-1..X-6 anchors) for the X engine, same anchor-design convention.
