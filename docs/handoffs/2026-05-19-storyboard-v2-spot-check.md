---
date: 2026-05-19
type: adversarial spot-check — storyboard SB v2 spec
target: docs/handoffs/2026-05-18-judge-design-step1-storyboard.md (v2)
companions:
  - docs/research/2026-05-19-storyboard-comprehensive-scope.md
  - docs/rubrics/judge-design-guide.md
  - docs/handoffs/2026-05-18-judge-design-v1-cross-check.md
posture: adversarial — falsifying premises, surfacing assumptions, stress-testing decisions
depth: deep (>3000 words, high-stakes domain, multiple load-bearing decisions, abstraction-heavy)
scope_excluded: coherence / feasibility / scope-goal alignment / UX / security / product-framing — owned by sibling reviewers
---

# Adversarial Spot-Check — Storyboard v2

## Summary

v2 is more disciplined than the comprehensive-scope research that birthed it — the judge layer stays atomic at Part 2 (5-plan portfolio, 6 criteria), and the program expansion rides `structural_gate`. That architectural restraint is the right call and the strongest move in the spec.

The exposed surfaces, in order of confidence:

- **(HIGH 0.85)** The "business clients NOT YouTube creators primarily" framing in §1 is **contradicted by the example anchors throughout §2 and §3**. v2 claims the dominant case is founder-led business; the exemplar list still bends to creator-led (MrBeast, Casey Neistat, Tom Scott, Cleo Abram, Modern Wisdom). SB-2's score-1 example ("I Spent 50 Hours In Ketchup") is a creator-economy hook — exactly the kind a SaaS founder would reject as off-brand. The judge will reward business plans that look like creator content.
- **(HIGH 0.82)** **SB-5's WARM-regime portfolio-diversity test breaks the "founder-led business" framing.** A founder-led B2B program that runs a coherent series arc (per Part 3 structural_gate) on one premise is the *winning* shape — and SB-5 WARM penalizes it as "5 variations on the same premise."
- **(HIGH 0.80)** **The 4-part decomposition (Strategy / Production / Distribution & Community / Coaching & Growth) is overstructured for what `structural_gate` can actually deterministically verify.** Parts 1 and 4 in particular contain components that are inherently judge-shaped questions being routed to a deterministic gate — and the gate's spec admits as much ("cadence × team math," "client-specific references in coaching brief," "callback structure"). These will collapse into either (a) judgmental presence-checks that pass everything or (b) brittle regex/length heuristics that produce false negatives. The clean split the spec claims is fuzzy at the boundary.
- **(MODERATE 0.72)** **The 5-plan portfolio at the judge core is the wrong shape for founder-led business clients.** A SaaS founder's actual production unit in 2026 is one long-form anchor + N native cuts (the 1→8 rule §3c #5 explicitly endorses) and a weekly cadence, not a 5-plan deliberative menu. The 5-plan shape is a creator-economy artifact (a writers'-room pitch). Locking it because "shape-drift Goodhart is documented" defends the wrong shape.
- **(MODERATE 0.68)** **The SB-6 lived-experience exception is genuinely earned**, but the effect sizes are cited loosely. The 40–80% script confab band is for open-ended generation broadly, not script-specific; the 19.9% Chelli citation-fab is on literature reviews not storyboards; the 75% Stanford figure is for legal-case fabrication in QA, not storyboard production. The asymmetric-broadcast-risk argument (vs CI-6) is the load-bearing case — and that argument doesn't need the effect-size numbers to hold.
- **(MODERATE 0.70)** **`configs/storyboard/supported_models.yaml` will rot** in production at quarterly cadence under current ownership ambiguity. The "ops team owner; cadence locked" line (§8.1 #4) is a presupposition without an accountable owner named.
- **(MODERATE 0.65)** **Cold/warm regime fork via `pattern_data_density` flag is creator-architecture-shaped** and doesn't translate cleanly to business clients. For a SaaS founder, the relevant signal isn't "anchor density of prior video output" — it's "founder's written/podcast corpus + brand-voice doc." v2 acknowledges this in §1's archetype split but the regime fork itself stays creator-shaped.
- **(MODERATE 0.62)** **First-cohort overfitting risk is acknowledged but not structurally defended.** §8.1 #5 names re-validation as a *trigger*, but the criterion prose (especially SB-1's archetype examples) was authored against Klinika + DWF + B2B SaaS as concrete fixtures. The spec will calcify against these unless re-validation runs *before* a 4th-archetype client onboards, not after.

---

## §1 — Premise challenging

### Finding 1 (HIGH 0.85): "Business clients NOT YouTube creators" framing collides with the exemplar/anchor stack

**Evidence from the spec.** §1 lines: "**gofreddy serves business clients, not YouTube creators primarily.** When the spec uses MrBeast / Casey Neistat / Cleo Abram / Hank Green / Tom Scott as anchors, they are concrete reference points for the judge's reasoning toolkit, not the population gofreddy is selling to."

This disclaimer is doing too much work. Look at what the judge actually scores against:

- **SB-2 score-1 example:** "I Spent 50 Hours In Ketchup" beats "I Spent 50 Hours In My Front Yard." This is a MrBeast-shape stunt hook. A SaaS founder, an AI-lab researcher, or a law-firm partner — *the dominant gofreddy case* — cannot ship this hook without being laughed off LinkedIn. The judge will reward business plans that *adopt* the creator-economy hook shape because that's where the rewarded example points.
- **§2 "Cross-form rigor (the ceiling)" lists MrBeast handbook stair-step + Johnny Harris visual-first** — both creator-economy shapes. The "achievable floor" list is more honest (Lenny Rachitsky, Patrick Boyle) but the ceiling is creator-shaped and that's what the judge will reach for.
- **§3a "Well-paced and pointless" is MrBeast handbook language.** It's a useful diagnostic but it imports the creator-economy success metric (premise stakes for a stunt video) into a B2B context where "stakes" might be "the founder's reputation if this thesis is wrong" — different surface entirely.

**Why this matters under selection pressure.** Per the design guide §11.1, the judge IS the selection signal. If the judge's score-1 anchors are creator-shaped and the disclaimer is a single paragraph in §1, the workflow will learn to produce creator-shaped plans for business clients and the disclaimer won't restrain it. The Phase 4 rollback at `c76f051` proves this — surface markers in anchors drive workflow optimization regardless of disclaimer text.

**What survival would look like.** Either (a) anchor examples come from the "achievable floor" cohort (Lenny / Patrick Boyle / Logan Bartlett / a named SaaS founder's actual content) and the creator-ceiling references move to the "reasoning toolkit" footnote, OR (b) SB-2's substitution test acquires a vertical-aware sub-anchor: for B2B founder-led, irreplaceability tests against the *founder's actual capacity to perform on-camera and the audience's professional context*, not against creator-stunt irreplaceability.

### Finding 2 (HIGH 0.82): SB-5 WARM portfolio diversity penalizes the winning founder-led shape

**Evidence from the spec.** SB-5 WARM score-0: "The 5 plans are variations on the same premise dressed differently."

**Counter-argument.** The winning founder-led B2B shape in 2026 is a *coherent series arc on one premise* — Cleo Abram "Huge If True" probes one frame across 8 episodes; Patrick Boyle does weekly market commentary on one thesis frame; Lenny Rachitsky's podcast is one premise (operator interviews) executed 200+ times. The Part-3 series-arc structural_gate explicitly rewards this: "4–12 video commitment around a shared premise that compounds week over week" / "shared premise frame in N≥3 episodes."

Part 3 says "shared premise frame across episodes is the winning shape"; SB-5 WARM says "5 plans on the same premise dressed differently is mediocre mode 3." Two parts of the same lane reward opposite shapes.

**The defense in the spec.** SB-5's "different premises, different emotional registers, different structural choices, different hook-formula fingerprints" leaves room for "same premise frame, different bets within the frame." But the score-0 anchor doesn't enforce that distinction — "variations on the same premise dressed differently" is exactly what 5 episodes of "Huge If True" look like at the synopsis level. The judge cannot reliably distinguish "5 variations on safe premise" from "5 distinct bets sharing a series-arc premise frame" without explicit guidance, and the score-1 prose doesn't carry it.

**What survival would look like.** SB-5 WARM score-1 should explicitly distinguish *premise-frame coherence* (rewarded) from *premise repetition with garnish* (penalized). The COLD regime already does this ("same premise frame, different postures probed"); the WARM regime doesn't.

### Finding 3 (MODERATE 0.72): The 5-plan portfolio is the wrong unit for founder-led business clients

**Evidence from the spec.** §1.5.2 locks the 5-plan portfolio as the judge's atomic unit. The justification: "shape-drift Goodhart is a documented failure mode in evolution loops: under selection pressure, the workflow learns that single-plan outputs score higher on SB-2 / SB-3 (hook, emotional arc) while portfolio outputs score higher on SB-5 (diversity), producing inconsistent artifact shapes."

**Counter-argument.** Shape-drift Goodhart defense is a *substrate engineering* argument for keeping the artifact stable across evolution generations. It is not an argument that the 5-plan shape is the right deliverable for the dominant client case.

For a founder-led B2B client, the production unit that matches §3c #5 ("Cross-platform native cuts as primary artifacts designed at plan stage, not extracted post-hoc") and §3c #13 ("Distribution map per long-form anchor — 1 long → 6–12 native derivatives") is: *one long-form anchor + its native-cut roster + the series-arc episode-N position*. That's one plan with explicit multi-platform shape, not five competing pitches.

The 5-plan menu is a writers'-room pitch shape — it presupposes a decision-maker selecting one premise from five. A SaaS founder doing weekly thought-leadership doesn't operate that way; they operate on a cadence with a series-arc, picking the next episode in the arc. Modern Wisdom doesn't get 5 candidate interview premises per week; Chris Williamson picks the guest and the conversation generates the premise.

**What survival would look like.** Either (a) accept the 5-plan shape is creator-economy-derived and acknowledge it explicitly as "5-pitch selection ritual fits creator-led + brand-author archetypes; founder-led may use it as voice-discovery instrument early-program but production unit is one-plan-per-week-with-series-arc-position once cadence locks," OR (b) document the 5-plan shape as a *deliberate process artifact* (used to force diversity-of-thinking even when only one ships) and separate it from "what gets produced." The current spec conflates these.

### Finding 4 (MODERATE 0.68): SB-6 effect sizes loosely cited, but the criterion still earns its keep

**Evidence from the spec.** §3d cites: "40–80% on open-ended generation; 19.9% citation-fab rate on GPT-4o literature reviews (Chelli et al. 2025); 75% case-fabrication on legal QA (Stanford 2024 RegLab)." §7 footnote: "script confabulation at 40–80% open-ended rate; citation confabulation at 19.9% rate; legal-case fabrication at 75% rate."

**Where the effect-size citations are loose:**

- **40–80% open-ended script confab.** The original measurement is "open-ended generation" broadly — not specifically script generation in video storyboard contexts. Storyboard scripts are *not* open-ended in the same sense (they're constrained by client brief, pattern data, format). The 40–80% range likely doesn't transfer cleanly. The criterion is still warranted because some fabrication rate exists; the specific number is overprecise.
- **19.9% Chelli citation-fab.** This is the GPT-4o-on-medical-literature-review measurement. Storyboard fact citation is a different surface (creator brief → script → factual claim → citation). The rate might be higher (less editorial scaffolding) or lower (fewer citations per artifact). The number was measured under different conditions.
- **75% Stanford legal-case fabrication.** This is legal QA hallucination — specifically case-citation in legal research output. Not storyboard production. The relevance is the *broadcast-risk asymmetry* argument (§7: "storyboard outputs *broadcast* the confabulation to thousands"), and that argument is the real load-bearing claim, not the rate transfer.

**Where SB-6 is still warranted.** The asymmetric-broadcast-risk argument (one CI brief misleads one decision-maker; one storyboard video misleads thousands) is the strongest case for SB-6 as a documented ≤5-ceiling exception. That argument doesn't need rate-precision — it needs only "some nontrivial fabrication rate exists." The spec wins the breach on the broadcast-risk argument and the rates serve as supporting indicators, not the load-bearing case.

**What survival would look like.** Reframe the effect-size citations as "documented LLM fabrication rates in *adjacent* tasks (open-ended generation, literature review, legal QA) cluster in the 20–80% range; the storyboard-specific rate is not yet measured but the asymmetric broadcast-risk shape justifies treating it as load-bearing." Don't claim "40–80% script confab" without the qualifier.

---

## §2 — Assumption surfacing

### Finding 5 (MODERATE 0.70): `supported_models.yaml` quarterly refresh will rot

**Evidence from the spec.** §8.1 #4: "Quarterly model-fleet refresh of `configs/storyboard/supported_models.yaml`. Fleet rotated 4 major releases Jan–May 2026; quarterly updates are the floor. Operations-team owner; cadence locked."

**Unstated assumption.** "Operations team" is named without an accountable role. gofreddy is a small team; "ops team" is a forward-looking organizational fiction at v1 deployment. In practice the file will be refreshed when (a) someone notices it's stale, or (b) a fixture fails because the declared model is no longer supported. Neither is "quarterly cadence locked."

**Failure mode.** SB-4 score-1 requires the declared rendering model to match the supported list. If the YAML is 6 months stale, fixtures will declare Veo 4 (current) and the YAML still lists Veo 3.5 (last refresh) — SB-4 fails on shape, not substance. The judge then routes to 0.5 unknown, evolution loop discards good variants for the wrong reason.

**Quarterly cadence is also under-specified for the actual rate.** Per the spec itself: "Fleet rotated 4 major releases Jan–May 2026" — that's roughly monthly major releases. Quarterly cadence locks in 2–3-month staleness as the steady state. For SB-4 to do its job, the refresh cadence has to be at least monthly, and the model envelope description has to update with new minor releases.

**What survival would look like.** Either (a) name the human accountable for the file with a specific role (not "ops team") and require a refresh-PR cadence visible in git history, OR (b) defang SB-4's model-list dependence by routing "is this model real and current?" to a deterministic API check (Veo / Runway / Kling / Luma / Pika all have public model listings), and let SB-4 score against capability-envelope text the judge can reason about. The YAML is the rot vector; the API is the truth.

### Finding 6 (MODERATE 0.65): Cold/warm regime fork is creator-architecture-shaped

**Evidence from the spec.** SB-1 and SB-5 fork on `pattern_data_density="cold"` / `"lukewarm"` / `"warm"`. SB-5 COLD regime presumes "≤3 anchor samples"; WARM presumes the creator's "actual videos" provide pacing patterns.

**Unstated assumption.** Pattern-data density is measured against *prior video output*. The cold/warm taxonomy presupposes a creator-archetype client where video pattern data is the relevant substrate.

**Where it breaks for business clients.** A SaaS founder commissioning their first video program has:
- 0 prior videos (cold by the video-archive metric)
- BUT 200 LinkedIn posts in a distinctive voice (warm by the written-corpus metric)
- AND 8 podcast appearances with transcripts (warm by the spoken-corpus metric)
- AND a brand-voice doc the company wrote in 2024 (warm by the brand-author metric)

Per §1, "Pattern data is the founder's published written corpus + any podcast appearances + any prior video. On-camera voice is partly emergent because they haven't shot much yet." So the spec *acknowledges* this — but the regime fork itself still tilts toward the video-archive metric. SB-1's COLD regime says "fewer than 3 anchor samples — cannot reliably score voice match" but doesn't specify what counts as an anchor sample. Is a LinkedIn post one sample? Three samples? A podcast transcript? A brand-voice doc?

**Failure mode.** A founder-led fixture with a 200-post LinkedIn corpus and zero videos will route to COLD regime if the workflow measures pattern-data against video archive; the judge will then apply COLD-regime scoring ("probe at least 3 different voice postures") which is appropriate for first-time-on-camera but mis-applies the written-corpus richness. Or it routes to WARM by counting LinkedIn posts as anchors and the score-1 anchor "pacing matches creator's native cadence" misfires because LinkedIn-post pacing isn't video pacing.

**What survival would look like.** Decompose `pattern_data_density` into modality-specific signals: video-archive density / written-corpus density / spoken-corpus density / brand-voice-doc presence. The COLD/WARM fork applies per modality. SB-1's voice-anchor density is measured against whichever modality is richest, with explicit "what counts as an anchor" rules per modality.

### Finding 7 (MODERATE 0.62): First-cohort overfitting acknowledged but structurally undefended

**Evidence from the spec.** §8.1 #5: "First-cohort overfit — SB lane fixtures are BUSINESS clients NOT YouTube creators. Re-validation trigger: any fixture from an established-creator archetype."

**Where this is good.** The trigger is named and the substitute-readers list in §1 is explicitly broadened.

**Where this is undefended.** Re-validation as a *trigger* means it happens *after* a 4th-archetype client onboards. By then the SB-1 archetype examples (Marco the espresso-machine guy / Dr. Maria Noszczyk / Stripe-style B2B SaaS voice) have been read by ~50 evolution generations against ~3 fixtures and the workflow has converged on whatever voice the criterion prose rewards on those fixtures. The 4th archetype hits a workflow already shaped against the first three.

The Phase 4 rollback pattern is exactly this — surface markers in anchors drove workflow optimization. SB-1's "Marco the Tuesday regular" example will become a slot to be filled with a similarly-shaped recurring-character reference for any client, because that's what scores well.

**What survival would look like.** Pre-rotate the SB-1 examples through 4+ archetypes *before* shipping v2 to evolution (current spec has 3 archetype examples — creator-led / founder-led / brand-author). The substitute-readers list in §1 names 6 archetypes (SaaS / AI-lab / agency / service / finance / e-commerce). The SB-1 prose should carry examples from at least 5 of these so the workflow can't slot-fill against a single shape.

---

## §3 — Decision stress-testing

### Finding 8 (HIGH 0.80): 4-part decomposition is overstructured for what structural_gate can verify

**Evidence from the spec.** §1.5 decomposes the deliverable into Part 1 Strategy / Part 2 Production / Part 3 Distribution & Community / Part 4 Coaching & Growth. The judge scores Part 2; `structural_gate` validates Parts 1, 3, 4.

§6.2 enumerates the structural_gate program-level checks:
- "cadence × team-size sanity check" (Part 1)
- "each native cut has at least one platform-specific design element (hook position, subtitle style, opening shot)" (Part 3)
- "explicit callback structure (Ep N references Ep M; shared premise frame)" (Part 3)
- "client-specific references in coaching brief (named footage references, specific observed habits to address)" (Part 4)
- "roadmap math against cadence + platform-mix + staffing declarations" (Part 4)
- "comment-magnets for specificity (named-claim invitation, controversial-but-defensible take, specific story call)" (Part 3)

**Counter-argument.** Several of these are inherently judge-shaped:

- **"Cadence × team-size sanity check."** A 1-person founder team can ship 5/wk Shorts if they're a video native (Daniel Vassallo) or cannot (most founders). This is not deterministic; it depends on the founder's video skill, AI-augmentation ratio, sponsor budget for editor support, day-job constraints. A regex/heuristic gate either passes everything (false negative) or hardcodes one team-size→cadence mapping that overfits to the first cohort.
- **"Each native cut has at least one platform-specific design element."** "Specificity" is the load-bearing word. A YouTube Shorts cut declared "9:16, hook-front, ≤60s" technically has 3 platform-specific elements per the spec's enumeration in §1.5.3. So does the same script copied across 6 platforms with the aspect ratio swapped. The gate cannot detect re-aspect-ratio extraction without semantic comparison.
- **"Explicit callback structure (Ep N references Ep M; shared premise frame)."** A regex search for "as I discussed in Episode 3" passes the gate. A series that thematically references prior episodes without verbal callback fails. The semantic test is judge-shaped.
- **"Client-specific references in coaching brief."** "Named footage references" requires the brief to cite specific prior video — which a first-engagement client *doesn't have*. A regex grep for "in your video on X" either passes everything for established clients (workflow learns to slot-fill a fake citation) or fails everything for new clients.
- **"Comment-magnets for specificity."** "Specific" is the test; a regex catches the cliché "what do you think? comment below" but doesn't catch slightly-rephrased clichés ("let me know in the comments"). And the spec's own example ("comment if you've ever shipped a 3am hotfix") is structurally identical to "comment if you've ever felt overwhelmed by a release" — the difference is *cultural specificity* which is semantic.

**Pattern.** The spec lists 6 program-level structural_gate checks; 4-5 of them are semantically-shaped tests that will not survive as deterministic gates without becoming brittle or empty.

**Falsifiability.** What evidence would prove this decision wrong? Run a sample of 20 candidate program deliverables through the proposed structural_gate v2 checks. If the gate catches the documented Goodhart modes (cadence theater, native-cuts as re-aspect-ratio, series-arc-as-label, coaching-as-stock-advice, roadmap-as-aspiration, comment-magnet-as-cliche) with ≥80% precision and ≥80% recall on hand-labeled fixtures, the decision survives. If precision OR recall falls below 60% on any check, that check is judge-shaped and routing it through structural_gate is mis-architecture.

**What survival would look like.** Either (a) accept that some program-level Goodhart modes are judge-shaped and add a *thin* program-level judge call (1-2 outcome questions, separate criterion set, separate model panel) that scores Parts 1/3/4 holistically, OR (b) rewrite the program-level checks as truly deterministic presence-checks ("does the deliverable contain a coaching brief?" / "does Part 3 list ≥4 platforms?") and explicitly acknowledge that the semantic quality of these components is *not* graded.

The current spec wants both — deterministic gate semantics with judgmental rigor — and that combination doesn't survive a Goodhart-pressured loop.

### Finding 9 (MODERATE 0.65): The split between judge core and structural_gate has fuzzy boundaries on at least 3 components

**Evidence from the spec.** §1.5.2 places "thumbnail strategy + samples" and "title strategy" inside Part 2 (Production) but explicitly marks them as "structural_gate-validated, not judge-scored." Part 2 is the judge's atomic unit.

**Counter-argument.** The spec's own §1.5.2 lists thumbnail and title as Part 2 components and the judge's prompt wrapper §5 says "you score ONLY Part 2 (the 5-plan portfolio)." If thumbnail and title are Part 2 but not judge-scored, the gate is doing semantic work inside the judge's territory.

Specifically, **title craft** (§1.5.2: "front-loaded specificity, curiosity-gap-without-clickbait, contrastive framing, numeric anchoring, named-entity inclusion, throat-clearing removed") is six semantic criteria collapsed into a structural_gate. None of these are deterministically verifiable. A regex for "throat-clearing" catches "really" / "actually" / "basically" but misses "in this video I'll explain" (which IS throat-clearing). "Curiosity-gap-without-clickbait" is the kind of judgment call that a 0.5-anchored judge criterion handles exactly.

**Pattern.** The 6-criterion ceiling exception (SB-6) was justified on broadcast-risk asymmetry. Thumbnail/title craft has similar asymmetry (a single thumbnail drives 30-60% of CTR per the spec's own §1.4 of the research; one bad thumbnail damages reach across an entire arc). Routing it to a gate that can't actually verify the craft is asymmetric in the wrong direction.

**What survival would look like.** Either (a) add a 7th judge criterion for thumbnail/title craft (which means revisiting the ≤5 ceiling argument — two documented exceptions already wears thin against the design guide's discipline), OR (b) move thumbnail/title to Part 3 (Distribution) and explicitly mark them as not-graded at v2 — accepting that the lane ships them as planning artifacts and the human ships the actual thumbnail.

---

## §4 — Alternative blindness

### Finding 10 (MODERATE 0.65): The "5-plan" shape is path-dependent from v1, not deliberate from first principles

**Evidence from the spec.** §1.5.2: "**THE 5-PLAN PORTFOLIO IS THE JUDGE'S ATOMIC UNIT.** Five short-form video story plans, each 90 seconds to 8 minutes. This shape is locked because shape-drift Goodhart is a documented failure mode in evolution loops."

**What's missing.** The spec does not address why 5 (vs 3 or 7 or N), why 90s-8min (vs other duration bands), why a portfolio-of-pitches (vs episode-N-in-arc) is the right shape for the judge to score.

The shape comes from v1, which inherited it from the original storyboard lane spec, which was authored before the comprehensive-scope research established that founder-led business is the dominant case. The 5-plan menu is a creator-economy artifact. v2 widened the lane to cover the full program but did not revisit whether the judge's atomic unit should still be 5-plan-menu-shaped given the wider lane.

**Alternative not considered.** The judge's atomic unit could be:
- **1 plan + its native-cut roster + episode-N-in-arc position** — matches the founder-led production unit; the diversity test moves to series-arc structure (which Part 3 already validates).
- **3-plan probe set** — keeps voice-discovery instrument shape but reduces selection-ritual presupposition.
- **1 long-form anchor with 3 hook ladder variants** — focuses the judge on hook irreplaceability (SB-2) and emotional arc (SB-3) which are the highest-leverage axes per the comprehensive-scope research's CTR/retention findings.

**Why this matters.** Locking the wrong shape because "shape-drift Goodhart is documented" defends shape-stability across evolution generations, not shape-correctness for the dominant client case. The shape decision is upstream of evolution and deserves first-principles scrutiny, not stability-by-default.

### Finding 11 (LOW-MODERATE 0.55): Build-vs-use for thumbnail generation tooling unexamined

**Evidence from the spec.** §1.5.2: "Optional generated mockups via Nano Banana Pro / Gemini Imagegen / GPT-4o image / Flux for client review."

**Missing.** No consideration of (a) whether the lane should pre-select a tool or (b) whether thumbnail generation should be in-scope at all vs human-shipped (the §8 open-question Q13 names this but as a deferred question, not a v2 decision). The "optional" framing means the lane can ship without thumbnails, which means the gate's "2-4 thumbnail directions per plan" check (§8.1 #3) is either enforced (then it's required) or optional (then it's not a gate).

**What survival would look like.** Make the v2 stance explicit: thumbnail directions are text-description-only at v2; the tool selection question is deferred; the gate enforces text-description presence and 2-4 count, not mockup generation. The current spec leaves this fuzzy.

---

## §5 — Modern-lever bias check

The spec earnestly tries to bake in modern-lever bias via §3b (14 CUTS) and §3c (20 ADDS). Stress-testing whether this actually penalizes the slop shapes and rewards the modern shapes:

**Does the spec penalize talking-head-only?** §3b #1 names it as a CUT validated by program-level structural_gate. But the *judge layer* doesn't penalize a single 5-plan portfolio where all 5 plans are talking-head founder reading to camera. The gate catches it only at program level (Part 3 native-cuts roster). At the judge layer, SB-1..SB-6 can all score 1 for a talking-head-only plan if voice / hook / arc / capability / pacing / source-tracing all check out. **Verdict:** judge layer doesn't penalize; gate does, but per Finding 8 the gate's semantic precision is suspect.

**Does the spec penalize AI-slop explainer?** §3d names the "Here's the thing" / "Stop X. Start Y" Kapwing pattern as the storyboard-specific failure surface. SB-1 score-0 catches this ("generic creator-archetype voice"). SB-6 catches the citation-fab side. **Verdict:** yes, primarily through SB-1 and the structural_gate banned-construct lint.

**Does the spec penalize motivational montage?** Indirectly through SB-1 (generic voice) and SB-3 (no real stakes). Not explicitly named as a failure mode in §3a/d. **Verdict:** weak coverage at the judge layer; could be a §3a mediocre mode addition.

**Does the spec penalize hook-formula slot-fill?** §3b #4 + SB-5's "different hook-formula fingerprints" requirement at the portfolio level. SB-2 catches single-plan clichéd opener-formulas. **Verdict:** strong coverage.

**Does the spec penalize 5-plans-same-premise portfolios?** Yes via SB-5 WARM — but per Finding 2, this collides with the series-arc reward.

**Does the spec reward founder-led on-camera?** §3c #1 names it as the default lever. But the judge layer doesn't *test* for founder-led framing in a 5-plan portfolio. A plan that's "AI-generated cinematic with VO" can pass SB-1..SB-6 if voice fidelity and source-tracing check out. Founder-led-on-camera is rewarded at program-level (Part 4 coaching brief) but not judge-scored. **Verdict:** modern lever stated as default but not load-bearing in the scoring signal.

**Does the spec reward irreplaceable hooks per platform?** SB-2 handles this but doesn't differentiate per-platform. A hook irreplaceable for YouTube long-form might not work for LinkedIn (where sound-off audience reads captions and the first 3 lines drive expansion). The 1→8 cuts roster in Part 3 implies per-platform hook discipline but the judge doesn't score it. **Verdict:** partial.

**Does the spec reward cross-platform native cuts?** Program-level gate per §1.5.3 + §6.2. Not judge-scored. **Verdict:** gate-only, per Finding 8 the gate semantic precision is suspect.

**Does the spec reward series-arc as growth unit?** Program-level gate. SB-5 WARM penalizes "same premise dressed differently" which collides with series-arc shape — see Finding 2.

**Pattern.** The judge layer (6 criteria, the actual selection signal) covers voice / hook / arc / capability / pacing / source-tracing. The modern levers (founder-led / native cuts / series arc / thumbnail craft / hook-per-platform / comment management) all ride structural_gate. If the gate's semantic precision is weak (Finding 8), the modern-lever bias is performative — declared in prose, not enforced in the loop.

---

## §6 — Net assessment

v2 is meaningfully better than v1 — the comprehensive-scope research is real, the 4-part program decomposition correctly identifies that "5 video story plans" undersells what a 2026 agency must ship, and the architectural restraint (judge stays atomic at Part 2; program rides structural_gate) is the right move under the design guide.

The exposed risks:

1. **Creator-economy bias in anchors** despite the explicit "business clients NOT creators" disclaimer. The judge will reward business plans that adopt creator-economy shape because that's what the anchors reach for.
2. **SB-5 WARM collides with Part-3 series-arc reward** — the two parts reward opposite shapes for the same plan.
3. **The 5-plan shape is path-dependent**, not first-principles-derived for the founder-led case.
4. **Program-level structural_gate carries semantic load it can't deterministically verify** — at least 4 of the 6 gate checks are judge-shaped.
5. **Modern-lever bias is performative** — declared in §3b/c but ride a gate whose precision is weak; the judge's 6 criteria don't directly enforce the levers.
6. **Cold/warm regime fork is creator-archetype-shaped** and doesn't decompose cleanly for business clients with mixed-modality pattern data.
7. **First-cohort overfitting is acknowledged but undefended** — re-validation triggers fire after the fact.
8. **SB-6 effect sizes are loosely sourced** but the criterion still earns its keep on broadcast-risk asymmetry.
9. **Model-YAML rot risk** under "ops team owns it" ambiguity at quarterly cadence when fleet rotates monthly.

The highest-leverage interventions:
- Re-author SB-1 archetype examples across 5+ verticals, not 3, before evolution exposure.
- Resolve SB-5 WARM vs Part-3 series-arc collision in score-1 anchor prose.
- Either add a 7th outcome-question criterion for thumbnail/title/program-shape, OR explicitly route Parts 1/3/4 to a thin program-level judge call rather than presupposing structural_gate can do semantic work.
- Decompose `pattern_data_density` into per-modality signals.
- Name the human accountable for `supported_models.yaml` and tighten cadence to monthly OR route model truth to API.
- Reframe SB-6 effect-size citations as adjacent-task indicators, not direct measurements.

The lane scope expansion to a four-part program is the right direction. The judge-layer atomicity is correctly defended. The structural_gate carrying weight it cannot deterministically bear is the load-bearing risk — and it's the part most likely to fail silently under selection pressure.
