---
date: 2026-05-12
phase: D
lane: ad_engine
status: spec — implementer-ready; C7 (Foreplay-alignment) gated on Phase A reliability test; compliance trigger-phrase content gated on Resolve-Before-Planning #2 (legal review)
inputs:
  - phase-a-lane-purposes.md §10 (ad_engine)
  - phase-b-research/ad_engine.md (six-criterion proposal, ~3,000 words)
  - phase-c-variant-ratings.md (no existing variants — NEW lane; proceed on Phase B strength)
optimization_target: per-variant ship-eligibility × cohort variant diversity (distinct bets, not distinct wordings) × LP coherence
---

# Phase D — ad_engine rubric spec (NEW lane, 6 criteria + optional C7)

ad_engine produces 3-5 paid-ad variants per format per campaign brief. v1: Klinika (Meta Reels + Meta image/carousel) and DWF (LinkedIn Sponsored Content). Each variant ships creative + image/video brief + matched LP hero copy. Phase A pins the optimization target to per-variant ship-eligibility × cross-variant diversity × LP coherence — three grading shapes no single criterion can carry. Phase C had no fixtures; spec proceeds on Phase B strength.

This spec locks **6 criteria** under **platform-conditional anchors** (Meta vs LinkedIn) and **artifact-shape conditional firing** (per-variant vs cohort). Compliance precondition (`medical_pl` Klinika, `legal_pl` DWF) fires BEFORE the quality judge — quality criteria assume compliance passed. C7 is **optional, default-OFF**; lights up only if Phase A's reliability test passes.

Operator-gated: (a) LP hero paired with ad at score time (§4); (b) compliance rule files (`configs/compliance/{medical_pl,legal_pl}/rules.yaml`) need legal-review sign-off per Resolve-Before-Planning #2.

---

## Section 1 — Summary table

Tier vocabulary: **essential** (load-bearing; failure caps), **important** (drags score when failed), **pitfall** (HARD FLOOR / AUTO-CAP), **optional** (positive when present, neutral when absent), **precondition** (fires before this rubric; pass-or-block, not graded).

| ID    | Tier              | ONE-quality summary                                                       | Scope             | Platform                    |
|-------|-------------------|---------------------------------------------------------------------------|-------------------|-----------------------------|
| ADE-1 | essential         | Hook stop-power — tension AND resolution inside truncation window.        | per-variant       | both (anchors diverge)      |
| ADE-2 | essential         | Specificity / falsifiability — brand-replace test fails the slop.         | per-variant       | both                        |
| ADE-3 | essential, pitfall | Platform compliance & format fit — AUTO-CAP triggers per platform.       | per-variant       | both (rules differ)         |
| ADE-4 | essential         | LP coherence — ad's named outcome reused verbatim/close-synonym in LP.    | per-variant XART  | both                        |
| ADE-5 | essential (top)   | Variant diversity — distinct (angle, lever, stage) tuples.                | cohort            | both                        |
| ADE-6 | important         | POV / non-genericity — falsifiable contrarian stance.                     | per-variant       | both (LinkedIn-weighted)    |
| C7    | optional (OFF)    | Foreplay-alignment — penalize high-deviation outliers only.               | per-variant       | both                        |
| —     | precondition      | Compliance regime (`medical_pl` / `legal_pl`) — fires BEFORE this rubric. | per-variant XART  | Klinika=medical_pl; DWF=legal_pl |

**Final count:** 6 criteria active (5 essential incl. highest-weight ADE-5, 1 important) + pitfall on ADE-3 + optional C7 + cross-cutting compliance precondition.

ADE-5 carries the highest weight. Phase B: "5 wordings of 1 bet" is the most common high-effort failure mode and hardest to catch — in the editor they look like 5 distinct bets. Meta's Creative Entity ID (Andromeda, 2026) clusters wordings as one concept, starving the redundant variants. The cohort judge predicts this before launch.

---

## Section 2 — Final criterion prose

### ADE-1 (essential) — Hook stop-power

**Evaluate this ad variant for ONE quality:** Does the hook — first 3s for Meta Reels / slide-1 headline + first body line for Meta image-or-carousel / first 150 chars for LinkedIn — contain BOTH a tension element AND an early-resolution element (number, named name, specific verb, contrast flip) inside the truncation/scroll window?

Highest-leverage variant feature on both platforms. Meta Reels completion is a primary ranking signal — hook + payoff <3s lifts hook rate ~22% (Motion App Q1 2026). LinkedIn truncates at ~150 chars; chars 0-149 are the entire ad for non-clickers. A hook that promises tension without resolving it inside the window loses the read.

- **Score 1:** Category statement or vague question; no resolution in window. *Meta:* "Looking for a Warsaw aesthetic clinic?" *LinkedIn:* "Better forecasting for finance teams."
- **Score 3:** Tension OR resolution but not both inside window. Resolves past the 3s cliff or 150-char truncation.
- **Score 5:** Tension AND resolution both inside window. *Meta:* "Two follow-ups in your first month. Your doctor on WhatsApp. No portal." *LinkedIn:* "GC of a Polish manufacturer with cross-border IP: three deadlines you should already have answers to — 1 Feb, 15 Apr, 30 Jun. Memo attached."

**Ground-truth verification.** Count chars (LinkedIn) or scene seconds (Meta Reels) deterministically. For LinkedIn, grade only `body_copy[0:150]`. For Reels, read scene-1 duration; if >3s, grade what fits in first 3s of voice-over.

**Closing.** Provide your reasoning, cite the specific substring, then give your score.

### ADE-2 (essential) — Specificity / falsifiability

**Evaluate this ad variant for ONE quality:** Could a generic competitor substitute their logo and run this copy truthfully? If yes, fail.

Phase B M5 + M7 (Harry Dry): "Good copy is falsifiable. 'We care about your skin' — every clinic could say it." Generic claims trigger the "no, scrolling" reflex.

- **Score 1:** Generic competitor swap undetectable. "We care about your skin." "Trusted by Polish business leaders."
- **Score 3:** One specific element (named role OR number OR named outcome); two of three slots generic.
- **Score 5:** Named role + named outcome + at least one specific number or named name. Swap would require rewriting. *Meta:* "Two follow-ups in your first month. Your doctor's WhatsApp. No portal." *LinkedIn:* "Three things every COO of a 200-500-FTE Polish manufacturer gets wrong in cross-border IP — 4-page memo."

**Ground-truth verification.** Apply the brand-replace test mechanically: substitute client name with "ACME" everywhere. If the result still reads true and reasonable for ACME, the variant fails. Judge quotes post-swap copy in evidence.

**Closing.** Provide your reasoning, run the brand-replace test in evidence, then give your score.

### ADE-3 (essential, pitfall, AUTO-CAP) — Platform compliance & format fit

**Evaluate this ad variant for ONE quality:** Is the variant format-correct, soft-compliance-clean against platform policy (statutory compliance is precondition), and native-style in production brief?

**HARD FLOOR / AUTO-CAP.** Confirmed violation triggers **auto-cap at 2** for ADE-3 and **caps variant composite at 3** (below ship-eligibility):
- Meta image/carousel with `image_brief.text_overlay_pct > 20`.
- Meta Reels brief specifying "cinematic," "high production value," "studio polish," or muted-audio default (Phase B M2/M3, S11).
- LinkedIn `body_copy` > 3000 chars OR document-ad page 1 is the cover, not the hook (L5, S12).
- CTA is "Learn more" with no specific offer in body (S1).

**Platform-conditional anchors.** *Meta:* native-style brief (handheld, ambient audio, VO for Reels), audio-on, 9:16 for Reels; image/carousel text overlay ≤20%, slide 1 carries hook; CTA carries specific promise. *LinkedIn:* body <3000 chars; chars 0-149 contain audience + outcome + implicit CTA; document ad page 1 is hook frame; CTA matches offer ("Get the memo," not "Learn more").

- **Score 1:** AUTO-CAP fires.
- **Score 3:** Format-correct, no cap, but visual brief defaults to studio-glossy OR CTA generic-but-allowed OR copy slightly over-long.
- **Score 5:** Native-style brief, CTA tied to specific offer, audio-on with VO/music script for Reels, page-1-as-hook document, image overlay ≤20%, LinkedIn first 149 chars complete the hook.

**Ground-truth verification.** Judge reads `image_brief.text_overlay_pct`, `visual_brief.production_style`, `cta.button_text`, `body_copy` length. If any AUTO-CAP condition matches, judge quotes the field; cap fires deterministically.

**Closing.** Provide your reasoning, check each AUTO-CAP condition in evidence, then give your score.

### ADE-4 (essential, CROSS-ARTIFACT) — LP coherence

**Evaluate this ad variant for ONE quality:** Does the matched LP hero copy deliver on the ad headline's named outcome — verbatim or close-synonym — and promise the same artifact (consult / memo / framework / booking)?

Cross-artifact check that prevents the most common silent failure: bait-and-switch. Meta's 2026 cross-asset compliance evaluation treats ad + LP + image as one unit; misaligned LP gets distribution-throttled. Reader CVR collapses independently of enforcement.

**Input format (LOCKED — §4).** Judge receives ad creative AND matched LP hero as paired artifact. If `lp_hero` missing, ADE-4 = 1 (HARD FLOOR).

- **Score 1:** LP hero is generic welcome ("Welcome to DWF") OR names a different outcome (bait-and-switch). HARD FLOOR also fires when `lp_hero` missing.
- **Score 3:** LP references same domain but rewords the outcome.
- **Score 5:** LP hero uses ad's named outcome verbatim or close synonym, names the same artifact, CTAs match. Reader experiences LP as the ad continuing.

**Ground-truth verification.** Judge quotes BOTH ad headline and LP hero side-by-side. Operator-declared `named_outcome_synonyms` (§4) defines close-synonym match; without it, judge defaults to literal-string match. If named outcome appears nowhere in LP hero, score 1 is mandatory.

**Closing.** Provide your reasoning, quote both side-by-side in evidence, then give your score.

### ADE-5 (essential, highest weight, COHORT) — Variant diversity

**Evaluate this ad cohort for ONE quality:** Across the 3-5 variants, how many distinct underlying *bets* are represented — not distinct wordings, but distinct (angle, hook-lever, persona-stage) tuples?

Most important criterion in the rubric. Phase B: "A copywriter can produce 5 truly different bets or 5 wordings of one bet, and to a human they often look similar." Meta's Andromeda + Creative Entity ID clusters wordings as one concept; four redundant variants get starved. The judge predicts this collapse before the campaign runs. Mechanic is deterministic; full spec in §3.

- **Score 1:** 1 distinct bet across all variants. Five "save time" wordings or five testimonials about one procedure (Phase B S4 — hardest-to-catch slop).
- **Score 3:** 2-3 distinct bets across 5 variants (50-60% distinct). Some diversity; pairs collapse.
- **Score 5:** Each variant occupies a distinct (angle, lever, stage) tuple. cohort_size = distinct_tuples.

**Ground-truth verification.** Judge MUST emit the explicit (angle, hook-lever, persona-stage) tuple per variant in its rationale. Operator can read tuples and override. Distinct-tuple count computed deterministically; score = `round((distinct_tuples / cohort_size) * 4 + 1)`, capped at 5.

**Closing.** For each variant, emit the tuple. Then count distinct tuples. Then compute the score.

### ADE-6 (important) — POV / non-genericity

**Evaluate this ad variant for ONE quality:** Does the copy take a position a competing firm/clinic would dispute — or could every competing operator co-sign the text?

Phase B M4 (Trott triangle) + L4 (POV not summary): "We help GCs reduce litigation risk" is category-correct and forgettable; "Three things every GC of a Polish manufacturer gets wrong in cross-border IP" stakes a claim some operators won't co-sign. LinkedIn weights this heavily (GrowthSpree 2026); Meta weights less — visual hook can carry, but generic copy still fails M7.

- **Score 1:** Every competitor could co-sign. Pure category language.
- **Score 3:** Implicit POV but no surfaced disagreement. "Most clinics get filler consults wrong" — hints without naming what speaker does differently.
- **Score 5:** Explicit contrarian stance + falsifiable evidence. "Most M&A advisors will tell you to redomesticate before holding consolidation. We've done five where the opposite saved 30%+ in stamp duty."

**Platform weighting.** LinkedIn carries heavier portion of cohort composite for DWF; Meta important.

**Ground-truth verification.** Apply the co-sign test against a named competitor from the campaign brief. If yes, score ≤3.

**Closing.** Provide your reasoning, run the co-sign test against a named competitor, then give your score.

### C7 (optional, default OFF) — Foreplay-alignment

**Status:** Held back pending Phase A reliability test. If reliability passes, C7 lights up as `optional`. If fails, DROPPED entirely (removed from RUBRIC_VERSION hash).

**Evaluate this ad variant for ONE quality (if enabled):** Does the variant resemble (in concept-tagging) ads currently in-market from Foreplay's library for the same vertical? Penalize ONLY high-deviation outliers. Foreplay shows IN-MARKET, not WORKING, so criterion is asymmetric: penalizes radical deviation, not non-conformity. A variant beating archetypes via defensible contrarian POV (ADE-6 = 5) is not penalized. Cross-reference: `inputs/foreplay/{vertical}/winners.json`.

---

## Section 3 — ADE-5 variant-diversity mechanic spec

Fully deterministic on the judge's emitted tuples; only judgment call is the tagging.

**Tag schema (emitted per variant):**

```yaml
diversity_tags:
  angle: "process"                          # 1 of 7 (below)
  hook_lever: "specificity-as-credibility"  # 1 of 7 (below)
  persona_stage: "solution-aware"           # 1 of 5 (below)
```

**Angle taxonomy (7).** `process` (how work gets done); `outcome` (what buyer gets — cautious under medical_pl); `cost` (money/time/effort — avoid Klinika/DWF); `risk` (what buyer avoids); `peer-reputation` (what peers in segment do); `regulatory-deadline` (dated event forcing decision); `identity` (buyer-as-protagonist).

**Hook-lever taxonomy (7).** `loss-aversion`; `curiosity`; `authority`; `social-proof`; `specificity-as-credibility` (anchors on number/date/named detail); `contrarian-POV` (names what others get wrong); `scarcity` (cautious under medical_pl).

**Persona-stage taxonomy (5).** `unaware` → `problem-aware` → `solution-aware` → `vendor-comparison` → `decision`.

**Cohort score:** `round((distinct_tuples / cohort_size) * 4 + 1)`, capped at 5. 1.00 → 5; 0.80 (4/5) → 4; 0.60-0.66 → 3; 0.40 → 2; 0.20 → 1. Score-5 anchor: cohort_size distinct tuples. Score-1 anchor: all variants share a tuple.

---

## Section 4 — ADE-4 LP-coherence input spec

ADE-4 requires ad creative AND matched LP hero copy paired as one artifact at score time:

```yaml
variant_id: klinika-reels-v2
campaign_id: klinika-q2-2026-consults
platform: meta_reels             # meta_reels | meta_image | meta_carousel | linkedin_single_image | linkedin_document | linkedin_video
compliance_regime: medical_pl    # medical_pl | legal_pl | null

ad:
  headline: "Two follow-ups in your first month"
  body: "Your doctor's WhatsApp. No portal."
  cta:
    button_text: "Book a 20-min consult"
    target_url: "https://klinika.example/consult"
  visual_brief: "Handheld POV, natural daylight, clinic anteroom."
  voice_script: "..."                       # required for meta_reels
  image_brief:                              # required for meta_image / meta_carousel
    text_overlay_pct: 14                    # ADE-3 AUTO-CAP if > 20
    aspect_ratio: "1:1"
  diversity_tags: { angle: process, hook_lever: specificity-as-credibility, persona_stage: solution-aware }

lp_hero:
  url: "https://klinika.example/consult"    # MUST match ad.cta.target_url
  headline: "Two follow-ups, your doctor's WhatsApp, no portal."
  subhead: "Aesthetic-medicine consultations in Warsaw. 20 minutes, by appointment."
  cta: { button_text: "Book your 20-min consult" }
  named_outcome_synonyms:                   # operator-declared close-synonym list
    - "two follow-ups in your first month"
    - "WhatsApp access to your doctor"
    - "no patient portal"
```

**Required for scoring:** `ad.headline`, `ad.cta.target_url`, `lp_hero.url` (must equal `ad.cta.target_url`), `lp_hero.headline`. Missing any → ADE-4 = 1.

**Score-5 anchor:** `lp_hero.headline` contains named outcome verbatim OR a member of `named_outcome_synonyms`. CTAs match. **Score-1 anchor:** Different outcome (bait-and-switch), or generic welcome with no shared named outcome, or `lp_hero` missing.

Operator owns `named_outcome_synonyms` — deliberate calibration knob, not judge invention. Without it, judge defaults to literal-string match.

LP hero is **authored by the lane**, not scraped from live LP — ad_engine produces both ad creative and proposed LP hero as paired deliverable. Client updates live LP to match before launch (Phase A §10).

---

## Section 5 — Implementation notes

**NEW lane — LaneSpec entry needed.** `autoresearch/lane_registry.py` requires a new `ad_engine` entry under `LANES`. Closest precedent: `linkedin_engine` / `x_engine` (content-for-publish with cohort criteria). Session prompts under `autoresearch/lanes/ad_engine/`.

**Rubric IDs.** `ADE-1..ADE-6`. C7 retains label until reliability resolves; if enabled, becomes `ADE-7`. Prose at `src/evaluation/rubrics.py` under new `AD_ENGINE_RUBRIC` block.

**Provider plumbing.** Foreplay / Adyntel / SerpAPI wired via `autoresearch/lanes/audit_provider_check.py` (on disk). Foreplay feed populates `inputs/foreplay/{vertical}/winners.json` for optional C7.

**LP hero location.** Per-variant artifact at `sessions/{session_id}/variants/{variant_id}/variant.yaml` with the `ad` + `lp_hero` structure from §4.

**Compliance regime integration (cross-cutting).** `medical_pl` Klinika, `legal_pl` DWF — fires BEFORE ADE-1..ADE-6. Hard-block means variant never reaches quality judge. Soft-warn flags but doesn't gate.

Precondition is often MORE constraining than ADE-3 (statute vs platform policy). Example: ADE-3 might pass a Reels ad with 18% text overlay and "Book a consult" CTA — but if voice-over names "Botox" (POM blocklist under `medical_pl`), compliance hard-blocks before ADE-3 fires. Rule files at `configs/compliance/{medical_pl,legal_pl}/rules.yaml` — gated on Resolve-Before-Planning #2. Until populated, precondition fires in shape-only mode: confirms cross-reference path, declares "not yet scoring," abstains. Failure-loud rather than scoring against empty rule list (matches storyboard SB-12/SB-15 pattern).

**Ship-eligibility threshold.** Cohort ship-eligible when ALL hold: (1) cohort composite ≥ 3.5; (2) ADE-5 ≥ 3; (3) no variant has ADE-1 < 2; (4) no variant has ADE-4 < 2; (5) ADE-3 has not auto-capped on any variant; (6) compliance precondition passed for all variants.

**Composite formula.** Per-variant = weighted mean of ADE-1, ADE-2, ADE-3, ADE-4, ADE-6 (weights 0.25 / 0.20 / 0.20 / 0.20 / 0.15; C7 if enabled takes 0.05 from ADE-6). Cohort = `mean(per_variant) * (ADE-5 / 5)` — diversity multiplier prevents high-diversity-mediocre from beating low-diversity-excellent.

**Audit-ability.** Judge MUST emit per variant: (a) ADE-5 tuple; (b) ADE-4 ad/LP pair side-by-side; (c) ADE-2 brand-replace post-swap copy; (d) any ADE-3 AUTO-CAP trigger string.

**RUBRIC_VERSION hash invalidates on:** (1) criterion text changes; (2) tier mapping changes; (3) compliance rules.yaml content hash changes; (4) ADE-5 tag taxonomies change; (5) ship-eligibility threshold changes; (6) C7 enabled/disabled transition.

---

## Section 6 — Klinika + DWF demo specifics

### Klinika Meta Reels — Art-14-compliance-bounded creative

EU's hardest paid-media environment: 2023 Art. 14 device-advertising ban + Meta health-vertical policy + cross-asset enforcement. Inside these walls:

- **Educational POV from the clinic (NOT the doctor).** First-person plural, no doctor image, no procedure photo. "Most Warsaw clinics get filler consults wrong. Here's what we ask new patients before going near a syringe." Tuple: (process, contrarian-POV, problem-aware).
- **Founder / operations POV.** Owner on WHY the clinic exists — brand narrative. Tuple: (identity, authority, unaware→problem-aware).
- **Anonymous patient story, no procedure named.** "I came in confused. Three appointments later I had a plan I trusted." Procedure-name vacuum drives consult inquiry, not price-shopping. Tuple: (identity, social-proof, problem-aware).
- **Process and trust signals, not outcomes.** "Two follow-ups in the first month. Your doctor's WhatsApp. No portal." Falsifiable, not an outcome claim — passes Art. 14. Tuple: (process, specificity-as-credibility, solution-aware).
- **CTA = "Book a consultation," never "Book this treatment."** Consultation is information-exchange (compliant); specific-treatment breaches Art. 14.

### Klinika Meta image / carousel — same constraints + three additions

NO before/after (Meta health-policy hard-blocks; cross-asset eval reads LP). Image text overlay ≤ 20% (ADE-3 AUTO-CAP). Slide 1 carries hook, not logo card.

### DWF LinkedIn Sponsored Content — partner-track inquiry

Polish bar rules: solicitation prohibited, fee disclosure restricted. Substitutes for "Hire us":

- **Expertise-sharing, not retainer-sale.** Document ad with gated memo. "A short memo on Article 102 GCJ enforcement risk for Polish exporters." Tuple: (regulatory-deadline, authority, problem-aware).
- **Named role + outcome + decision-stage.** "Help your CFO close Q3 without three reforecasts." Self-targets by role + stage.
- **Contrarian POV + falsifiable numbers.** "Most M&A advisors will tell you to redomesticate before holding consolidation. We've done five where the opposite saved 30%+ in stamp duty." Tuple: (risk, contrarian-POV, vendor-comparison).
- **Page-1-as-hook on document ads.** Title-card = AUTO-CAP. Spiciest stat or diagram = score 5.
- **No fee mentions, no "engage us."** Solicitation flag owned by `legal_pl` precondition.

Five DWF angle-buckets that don't violate solicitation rules (Phase B §5): regulatory-deadline memo, cross-border tax/IP framework, anonymized restructuring case, opinion-piece on recent court decision, partner-authored research drop. Natural 5-tuple basis for ADE-5.

---

## Section 7 — Validation plan

First 5 ad cohorts validate discrimination on the four highest-risk failure modes.

**V1. ADE-5 discriminates 5-distinct-bets from 5-wordings-of-one-bet.**

Cohort A: 5 Klinika Reels variants, all "save time on your aesthetic consult" with different verbs (cut / slash / recover / reclaim / free up). Same (outcome, loss-aversion, solution-aware) tuple. Expected: ADE-5 = 1; cohort capped below ship-eligibility regardless of per-variant scores.

Cohort B: 5 variants spanning 5 distinct tuples — process / identity-founder / peer-reputation / risk / regulatory-deadline. Expected: ADE-5 = 5.

Test passes if A scores below threshold and B above, regardless of per-variant ADE-1..ADE-4. If both pass or both fail, anchors need tightening.

**V2. ADE-4 catches bait-and-switch on synthetic test.**

Strong Klinika variant: ad headline "Two follow-ups, doctor's WhatsApp, no portal" / LP hero verbatim echo → ADE-4 = 5. Three corruptions: (i) LP hero → "Welcome to [Clinic] — 20 years of experience" → ADE-4 = 1; (ii) LP hero → "Personalized aesthetic-medicine consultations" → ADE-4 = 3; (iii) `lp_hero` removed → ADE-4 = 1 (HARD FLOOR).

Bait-and-switch scoring above 1 means criterion isn't catching the most common silent failure.

**V3. ADE-3 fires on Meta 20%-text-overlay synthetic violation.**

Klinika carousel at `text_overlay_pct: 14` → ADE-3 = 4-5. Corrupt to `28` → AUTO-CAP at 2; composite capped at 3; judge quotes 28% in evidence.

Repeat: Reels brief "handheld POV" → "cinematic studio, dramatic lighting" → AUTO-CAP, judge quotes "cinematic"/"dramatic." LinkedIn document ad page 1 "key stat callout" → "title card with firm logo" → AUTO-CAP, judge quotes page-1-as-cover violation.

Any synthetic violation scoring above cap means AUTO-CAP logic isn't wired correctly.

**V4. Compliance precondition (medical_pl) catches synthetic Klinika "guaranteed results" ad.**

Compliant variant → precondition passes; ADE-1..ADE-6 run normally.

Corrupt voice-over: append "Guaranteed results in 14 days. The best clinic in Warsaw." Expected: precondition hard-blocks on rule (b) result-promise + (c) comparative-claim; variant never reaches ADE-1..ADE-6; `compliance_flags` cites both with quoted strings.

Repeat with variant naming "Botox" → precondition hard-blocks on rule (a) POM-name; judge quotes "Botox."

Compliance-violating variant reaching the quality judge means precondition isn't wired correctly. Load-bearing for evolution direction (Phase A): false-negatives on real statutory violations cap lane value.

**V5. Cohort composite assembly.**

Score one 5-variant Klinika cohort end-to-end. Confirm: each variant emits a tuple; ADE-4 quotes ad headline + LP hero side-by-side; ADE-3 AUTO-CAP triggers quoted; per-variant composite = weighted mean of ADE-1, ADE-2, ADE-3, ADE-4, ADE-6; cohort composite = `mean(per_variant) * (ADE-5 / 5)`; ship-eligibility matches the six-clause threshold.

A cohort scoring high overall but failing one clause must NOT be marked ship-eligible. Wired-threshold bug otherwise.

---

**Ground-truth cross-reference index.** LP hero paired with ad: `sessions/{session_id}/variants/{variant_id}/variant.yaml` (§4). Foreplay winners (C7): `inputs/foreplay/{vertical}/winners.json`. Compliance rules: `configs/compliance/{medical_pl,legal_pl}/rules.yaml` (gated). Diversity taxonomies: §3 (operator-overridable). Brand visual pack: `configs/brand/{client}/visual_pack.yaml` (shared with image_engine, storyboard).
