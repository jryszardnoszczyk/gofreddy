# AE-1..AE-8 Rubric Anchors (article_engine, U13)

Mirror of `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` for the
article_engine lane. Per TD-40: the 8 AE rubrics are operationalized
with explicit Score-1 / Score-3 / Score-5 anchors, falsifiability
hooks, named Score-3 failure modes, and anti-gaming clauses where
applicable.

The rubric prose itself lives in `src/evaluation/rubrics.py` (`_AE_1`
through `_AE_8`). This doc is the design reference + the operator's
quick-look cheat sheet during reviewer-assist + judge-prose lock-step
review.

## Anchor design principles (per TD-40)

1. **Operational definitions.** "Hook" is not "engaging opener" — it's
   "first 60 words / 210 chars deliver a falsifiable claim, named
   subject, or concrete result, testable against body's main thesis."
2. **Falsifiability.** Each anchor names what would falsify it. AE-2's
   "thesis specificity" specifies "≥3 concrete numeric/named-entity
   claims per 1,000 words" — measurable, not vibes.
3. **Named Score-3 failure modes.** Each rubric calls out the specific
   anti-pattern that would land a draft at Score-3 (the "middle, but
   formulaic" tier). This prevents Goodharting toward an arbitrary
   middle score — the agent has to actually clear the named patterns.
4. **Anti-gaming clauses.** Pattern-based caps (e.g., AE-3 "untraceable
   citation = structural fail", AE-4 "anti-pattern words cap at 4")
   give the judge deterministic floor mechanics so the rubric isn't
   gamed by clever prose that triggers the qualitative anchors but
   fails the structural lower bound.

## Tier assignments

| Rubric | Tier      | Rationale                                                     |
|------- |-----------|---------------------------------------------------------------|
| AE-1   | important | Hook is structurally important but not the article's core.    |
| AE-2   | essential | Thesis falsifiability IS the article's reason to exist.       |
| AE-3   | essential | Citation verifiability is the anti-AI-slop hard floor.        |
| AE-4   | essential | Voice fidelity — long-form slop fatal in a way 280-char isn't.|
| AE-5   | important | Argument coherence — important; "wall of disconnected paragraphs" caps at 3 regardless of other dimensions. |
| AE-6   | optional  | Skimmability — cosmetic but real.                             |
| AE-7   | important | Platform-adapter compliance — structural fail handled by gate.|
| AE-8   | important | Cross-cohort diversity — cross-item; mirrors X-6 / LI-6.      |

## Per-rubric anchor reference

### AE-1 Hook strength

- **What it measures:** falsifiable claim, named subject, or concrete
  result in the first 60 words (blog) / 210 chars (LinkedIn fold).
- **Anti-gaming:** rhetorical-question opener auto-≤3; "in today's
  fast-paced world" opener variant auto-≤4 (via anti_patterns.yml hit).
- **Score-3 failure mode:** concrete-number opener without a specific
  entity, OR story-led sentence that doesn't earn the show-more
  cutoff.
- **Verification:** judge sees the first 60-210 chars; can a
  disagreeing operator quote the hook in a tweet?

### AE-2 Thesis specificity & falsifiability

- **What it measures:** the body advances at least one claim that
  could be proven wrong.
- **Hard floor:** ≥3 concrete numeric/named-entity claims per 1,000
  words. Below the floor scores ≤3.
- **Score-3 failure mode:** thesis names ONE entity or carries ONE
  number, surrounding prose generalizes.
- **Anti-gaming:** the rubric checks claim-density, not surface
  specificity — sprinkling "47" and "Linear" into vague prose
  doesn't pass.

### AE-3 Citation density & verifiability

- **What it measures:** every numeric/attributive claim carries an
  inline `[N]` reference traceable to brief.source_id, voice.md
  entity, or verifier-checked URL.
- **Hard structural floor:** untraceable citation = structural fail
  (the gate blocks before the rubric fires). Degraded URL → cap at
  4. No `[N]` at all → cap at 3.
- **Score-3 failure mode:** "studies show" / "experts say" /
  "research indicates" without inline citation.
- **Verifier integration:** AE-3 score depends on citation_verifier
  (TD-44) output. Verification rate ≥0.9 for Score-5.

### AE-4 Voice fidelity

- **What it measures:** first-person operator voice, lived-work
  claims grounded in voice.md, no slop register.
- **Anti-pattern deny-list:** seamlessly, robust, holistic, leverage,
  optimize, streamline, cutting-edge, game-changing, revolutionary,
  transform/ative — any hit caps at 4.
- **Hard floor (mirrors X-2 / LI-2):** lived-work claims REQUIRE
  named entity in voice.md → unnamed scores ≤3.
- **Score-3 failure mode:** mostly first-person but 2-3 anti-pattern
  words OR hedge stack in an otherwise-specific section.

### AE-5 Argument coherence & structure

- **What it measures:** visible problem → mechanism → evidence →
  implication arc.
- **Anti-gaming:** listicle-disguise check — if paragraphs are
  freely reorderable, the rubric caps at 3.
- **Score-3 failure mode:** arc exists but muddled; evidence is thin
  or implication paragraph repeats introduction.
- **Verification:** reader should outline the article in 4-5 bullets
  after one read; if not, the arc isn't visible.

### AE-6 Skimmability & rhythm

- **What it measures:** subhead density (every 200-300 words blog /
  150-250 words LinkedIn), paragraph length (≤4 sentences blog / ≤3
  LinkedIn), one TL;DR or summary callout.
- **Score-1 failure mode:** wall-of-text >400 words without break,
  OR every paragraph is one sentence (no density).
- **Score-3 failure mode:** subhead density acceptable but
  inconsistent.

### AE-7 Platform-adapter compliance

- **Blog requirements (structural gate enforces):** H1, meta
  description 140-160 chars, schema.org Article JSON with
  headline/author/datePublished/image, ≥1 hero image brief, ≥1
  inline image brief.
- **LinkedIn Article requirements:** 210-char fold-safe hook, no
  markdown headers (LI strips them), bold + line breaks, 3-5
  hashtags.
- **Score-1 failure mode:** markdown headers in LinkedIn Article;
  blog missing schema.org; hook truncates mid-claim at 210 chars.
- **Anti-gaming:** structural gate catches most violations
  pre-judge; rubric scores qualitative fit within compliance.

### AE-8 Cross-cohort diversity & novelty

- **Cross-item:** scores the BATCH, not individual drafts.
- **What it measures:** no two drafts share opening pattern, thesis
  shape, or named-entity invocation.
- **Score-1 failure mode:** ≥2 drafts share opening verbatim.
- **Verification:** geometric mean across cohort high.

## Operational notes

- **AE-3 verifier wiring (TD-44):** the rubric depends on
  `src.verification.citation_verifier.verify_citation` post-generation.
  The lane invokes it once per `[N]` reference; cached results from
  `src.verification.citation_cache.CitationCache` short-circuit
  repeat calls.
- **Anti-patterns YAML:** `templates/article_engine/anti_patterns.yml`
  drives the deterministic pre-check that runs BEFORE judge dispatch.
  12 patterns enforced in v1 (TD-40 list).
- **Length brackets:** standard blog 1,500-2,500 words (industry
  benchmark per Bluehost / Orbit Media 2025 data — 39% of marketers
  publishing 2,000+ report strong vs 21% baseline). Deep-dive
  2,200-3,500 (technical case studies — Anthropic / Stripe / OpenAI
  engineering-blog shape). LinkedIn short 1,200-1,500 (algorithm-
  preferred); long 1,500-2,200 ("7x posts" multiplier dies past
  2,000 unless thought-leader status).

## Stability + drift detection

The rubric prose hash (`src/evaluation/rubrics.RUBRIC_VERSION`)
incorporates AE-1..AE-8 + the 3 article_engine compliance rubric
IDs. Any prose edit bumps the hash, which invalidates parent-score
caches (Stream C C4-lean part 3). This is intentional — rubric
drift must invalidate cached evaluations.

When a future judge-prose lock-step review touches AE-* prose,
update both `src/evaluation/rubrics.py` AND the matching anchor in
this doc to keep them in sync.
