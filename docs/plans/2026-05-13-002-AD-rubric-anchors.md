# AD-1..AD-8 Rubric Anchors (ad_engine, U15)

Mirror of the AE / IE rubric-anchors docs for the ad_engine lane.
Per TD-42: 8 AD rubrics operationalized with explicit Score-1/3/5
anchors, falsifiability hooks, and anti-gaming caps from
`src/ads/compliance/anti_patterns.py`.

The rubric prose itself lives in `src/evaluation/rubrics.py` (`_AD_1`
through `_AD_8`).

## Backend wiring

Per the U15 §judge wiring section:
- Inner-loop **statically pinned to claude/sonnet** from day 1 — NOT
  codex. Healthcare-vertical (Klinika) + regulated-legal (DWF) ad
  vocabulary trips codex's cyber filter; no automatic fallback
  substrate exists. Reversible by LaneSpec edit + redeploy or per-
  invocation `--inner-backend codex` CLI override.
- Outer judge: claude/opus.
- Compliance-judge: per D25 (`COMPLIANCE_JUDGE` from U5).

## Tier assignments

| Rubric | Tier      | Rationale                                                     |
|------- |-----------|---------------------------------------------------------------|
| AD-1   | essential | Hook strength — fail an ad if it doesn't stop scroll.         |
| AD-2   | important | CTA clarity — important but not always fatal.                 |
| AD-3   | important | Offer specificity — important; sometimes vague is intentional. |
| AD-4   | essential | Platform-format compliance — banned terms = auto-reject.     |
| AD-5   | important | Variant diversity (cross-item) — A/B testing depends on it.   |
| AD-6   | pitfall   | Voice fidelity — anti-pattern hits cap the score.             |
| AD-7   | important | Market-signal alignment — informational when signal degraded. |
| AD-8   | essential | Conversion-readiness — ad-to-LP message-match drives lift.    |

## Per-rubric anchor reference

### AD-1 Hook strength

- **Falsifiable floor:** hook MUST contain ≥1 of {concrete number,
  named competitor/category, contrarian claim, specific workflow noun}.
- **Anti-pattern caps:** per-hit cap from `cap_score_from_hits(...)`
  — AD-1 caps at `max(2, 4 - 0.5 × (hits - 1))`.
- **Score-3 failure mode:** generic "Are you tired of" / "Meet" /
  "Introducing" opener.

### AD-2 CTA clarity

- **Falsifiable floor:** CTA verb is a platform-native action enum
  (Meta: Shop Now / Get Quote / Book Now; LinkedIn: Apply / Download
  / Sign Up) OR a specific outcome verb + object.
- **Score-3 failure mode:** "Learn More" or "Discover the Power of".
- **Anti-gaming:** 0% of top-2%-CTR LinkedIn ads use "Learn More".

### AD-3 Offer specificity

- **Falsifiable floor:** offer includes ≥1 of {price, duration,
  quantity, named deliverable}. Competitor-stealable = specific.
- **Score-3 failure mode:** "Better analytics" / "Smarter workflows"
  — competitor could ship the same ad.

### AD-4 Platform-format compliance

- **Hard structural gate (session_eval enforces):**
  - Meta: ≤125 char primary, ≤27 char headline, ≤30 char description,
    text-in-image <20% area.
  - LinkedIn Sponsored: ≤150 char intro, 1-2 line headline.
  - LinkedIn Document Ad: 3-10 slides, cover works standalone, ≤30 words/slide.
  - Reels: 9-15s, vertical 9:16, hook in first 0.8-1.2s.
- **Banned-terms hard-gate** (Meta health-vertical, LinkedIn aggressive,
  Guaranteed N% regex).

### AD-5 Variant diversity (cross-item)

- **Falsifiable floor:**
  - Pairwise Jaccard on hook+opening-8-token ≤0.3
  - Archetype enum values all distinct (no shared hook_archetype)
  - No two variants share the same proof noun
- **Per-format diversity dim:**
  - Meta Reels: hook archetype (5 archetypes)
  - Meta Image: promise type (outcome / status / efficiency / risk-reduction)
  - LinkedIn Sponsored: insight angle (observation / framework / contrarian / list)
  - LinkedIn Document: content shape (case-study / framework / mistake-list / data-viz)
- **Diversity gate behavior:** reject + regen failing slot with
  budget=2 retries; on retry, prompt names offending overlapping
  n-grams explicitly.

### AD-6 Voice fidelity

- **Anti-pattern caps:** ANY hit caps at 3 (voice slipped into AI
  house-style). 14 patterns from `src/ads/compliance/anti_patterns.py`.
- **Banned-term floor:** zero presence of banned-word list (Meta
  health-vertical for health clients; LinkedIn aggressive).

### AD-7 Market-signal alignment

- **R19 NO-OP:** when `signal_aggregator.all_meta_sources_degraded ==
  True`, this rubric scores N/A (defaults to 5). The rubric depends
  on signal availability; missing signal is operational, not the
  variant's fault.
- **Falsifiable floor:** agent must cite `brief.recurring_hook_archetypes`
  EITHER as counter (variant's hook explicitly differs from saturated
  archetype) OR as amplify (variant rides the archetype with new angle).

### AD-8 Conversion-readiness

- **Hard structural gate (session_eval enforces):**
  - `jaccard(tokenize(ad.hook), tokenize(lp.headline)) ≥ 0.4` after
    stopword removal
  - `ad.cta.verb == lp.primary_cta.verb` (exact match)
  - `ad.body.proof_noun ∈ lp.proof_point`
- **Research basis:** 2.3% conversion lift per 1% headline alignment;
  top advertisers see 25% lift from message-match optimization.

## Operational notes

### Signal aggregator (5 DI providers — JR's 2026-05-19 U15 decision)

`src/ads/signal_aggregator/` carries the 5-provider orchestrator:
- ForeplayProvider (crowdsourced ad library, US-DTC-skewed)
- AdyntelProvider (transparency-pull, broad geo, 24-72h lag)
- MetaAdLibraryProvider (EU-DSA-favored, free, authoritative)
- SerpApiProvider (SERP signal for offer keywords)
- GscProvider (first-party SEO via Search Console)

Each ships as a dependency-injected `fetch_*` callable. Production
wiring (API keys + httpx clients) lands at U18 alongside Klinika +
DWF onboarding.

### Anti-patterns YAML (operator-mutable)

`src/ads/compliance/anti_patterns.py` carries 14 deterministic
patterns; `src/ads/compliance/banned_terms.yaml` carries the hard-
gate word lists. Both are mutable by meta-agent during evolution
(tightening Meta moderation policies, expanding LinkedIn term list).

### Stability + drift detection

RUBRIC_VERSION hash bumps when any AD-* prose changes (incl.
compliance rubric prose_refs). This invalidates parent-score caches
per Stream C C4-lean part 3.
