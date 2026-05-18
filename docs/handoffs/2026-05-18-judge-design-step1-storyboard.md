---
date: 2026-05-18 v1
type: judge-design Step 1 — storyboard (SB) optimal-output spec
status: DRAFT v1 — research-backed expansion from v0 skeleton; ready for redundancy check + fixture validation + workflow-side schema work
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
gold_standard: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.3 — documented ≤5-ceiling exception precedent)
companions:
  - docs/research/2026-05-15-judges-domain-storyboard.md (creator-strategist validation pass; SB-1..SB-8 ≈85% coverage, 2 recommended adds, 1 sharpen)
  - docs/research/2026-05-18-storyboard-creator-voice-fidelity.md (axis 1 — measurable stylometric substrate, 70–80% PAN-CLEF verification ceiling)
  - docs/research/2026-05-18-storyboard-ai-failure-modes.md (axis 2 — script confabulation 40–80% open-ended, 19.9% Chelli citation-fab, 75% Stanford legal-case; SB-6 documented-exception rationale)
  - docs/research/2026-05-18-storyboard-pattern-data-cold-start.md (axis 3 — cold/lukewarm/warm regime; brand-voice doc as POSTURE not FIDELITY anchor; r=0.55-0.72 lexical, r=0.1-0.25 prosody)
  - docs/research/2026-05-18-storyboard-ai-video-model-capability.md (axis 4 — fleet rotated Jan–May 2026; model-name anchor routed to configs/storyboard/supported_models.yaml)
revision_history:
  - 2026-05-18 v0 — initial skeleton compressing SB-1..SB-8 + recommended SB-9 stakes + SB-10 named specificity into 5 outcome questions
  - 2026-05-18 v1 — Four-axis research synthesis applied. SB-1..SB-5 KEPT (with sharpening); SB-6 added as documented ≤5-ceiling exception per design guide §5 (mirrors CI-6 precedent — defends against script confabulation 40–80%, citation 19.9%, false personal experience per arxiv 2505.01800, legal-case 75%). Model-name anchor routed OUT of judge prose into configs/storyboard/supported_models.yaml. SB-5 cold-start REFRAMED to portfolio-of-postures (5 voice probes sharing one premise frame) per cold-start research §7. 7 structural_gate checks for SB-1 voice-fidelity (function-word divergence, sentence-length KS, AI-slop blocklist, em-dash density, n-gram anti-laundering, specificity rate, anchor sufficiency). 4 structural_gate checks for SB-6 (stat-grep, quote-grep, "as of" date, rights-flag). 8 structural_gate checks for SB-4 capability (model-in-supported-list, duration vs native clip, stitch_strategy, consistency-anchor fields, banned-construct lint, primary camera move, beat-timing tolerance, AI-slop). pattern_data_density (cold/lukewarm/warm) computed in structural_gate and passed to judge for SB-1/SB-5 routing.
---

# Storyboard — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md` with one documented exception (§7). Frameworks (MrBeast handbook, Pixar 22 Rules, Save the Cat, Casey Neistat structure, Johnny Harris visual-first method, Hank/John Green imagine-others-complexly, Hormozi Hook-Retain-Reward, Story Spine, Dan Harmon Story Circle) inform the spec's reader/success/failure framing and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

This v1 supersedes the v0 skeleton with four-axis research synthesis (voice fidelity, AI failure modes, pattern-data cold-start, AI-video-model capability). Each elaboration is anchored in a measured failure rate: voice-fidelity research (70–80% PAN-CLEF verification ceiling bounding SB-1's honest range); AI-failure modes research (40–80% open-ended confabulation, 19.9% Chelli citation-fab, 75% Stanford legal-case, false-personal-experience per arxiv 2505.01800 — motivating SB-6 as the documented ≤5-ceiling exception); cold-start research (regression-to-mean voice as the silent failure mode in cohort-pooling); capability research (fleet rotation rate of 4 major releases Jan–May 2026 forcing the model-name anchor out of judge prose).

The v0 skeleton compressed 10 candidate criteria into 5. v1 KEEPS the 5-criterion spine and adds a 6th as a documented exception — not because more is better, but because the AI-failure surface SB-1..SB-5 cannot catch is measurable and broadcast-risk asymmetric (a storyboard fabrication ships to thousands; a CI brief fabrication misleads one decision-maker). Per design guide §5 v2.1 amendment, this is the same pattern CI-6 established.

---

## 1. Reader (LOCKED 2026-05-18)

A solo creator with a production team of 1–3 people (shooter, editor, voiceover), 5–15 minutes of planning time before locking the shot list, holding a 90-second to 8-minute video plan in hand. They will commit to producing one of 5 submitted plans if and only if it (a) sounds like THEM rather than a generic AI imitation, (b) has a hook they could honestly text a friend ("you have to see this"), (c) earns its claimed emotional arc through specific producing beats not just metadata declarations, (d) lands within the declared rendering model's envelope for the bits they'll generate AND within their own production-source constraints (location, rights, guest access), (e) reads as 5 distinct bets rather than 5 variations on the safest premise, (f) survives source-tracing — every stat / quote / experiential claim either cites a source, matches pattern-data, or is explicitly flagged scripted-fiction.

**Decision-making shape varies by client archetype** (per cold-start research §3):

- **Creator-led** — solo content creator with established voice signature (a YouTube creator, a TikTok personality, a podcast host). Pattern data is rich; the reader IS the voice authority; the brand-voice doc, if it exists, is descriptive of an observed practice.
- **Brand-author** — a creator strategist commissioning storyboards for a brand client, or an in-house content lead at a media-native brand. Pattern data is the brand's editorial voice; the brief specifies what the brand wants to sound like; the reader is responsible to the brand's voice authority, not their own.
- **Founder-led business** — a founder-CEO or partner whose video content represents the company (a SaaS founder doing thought-leadership; a law-firm partner explaining a regulatory shift; a clinic owner running patient-education shorts). Pattern data is the founder's published written corpus + any podcast appearances; on-camera voice is partly emergent because they haven't shot much yet. **This is the first-cohort case for gofreddy** (Klinika clinic owner, DWF partner, B2B SaaS founder).

The plan still has to drive concrete production-commitment regardless of which archetype the reader operates in — but the voice-fidelity anchor (SB-1) differs across archetypes (observed voice for creator-led; brand editorial voice for brand-author; founder's published anchor for founder-led).

**Reading time is not load-bearing.** They read until they have what they need, then stop. Length guidelines route to `structural_gate`, not the judge.

Substitute readers the same plan should also serve: script-doctor reviewing another creator's plans; in-house brand content director reviewing freelancer-produced storyboards; agency creative director evaluating a campaign deck before client presentation.

**First-cohort overfit watch.** The current SB lane fixtures are BUSINESS clients (Klinika clinic owner, DWF partner, B2B SaaS founder) — NOT established YouTube creators with rich pattern data. SB-1 prose must cover "the client's published anchor" (which may be written essays, LinkedIn posts, podcast transcripts) NOT only "the creator's voice family" (which presumes a YouTube/TikTok-shaped catalog). The creator-strategist reference set (MrBeast, Casey Neistat, Johnny Harris, Hank Green, Tom Scott, Cleo Abram) exists in this spec because the practitioner literature is concrete there. They are **not** the architectural target — they are concrete anchors for the judge's reasoning toolkit. When client #5+ onboards from an established-creator archetype, re-validate SB-1 prose (see §8).

NOT the reader: a VFX supervisor finalizing shot specs; a screenwriter writing for traditional film; a marketing team using a story plan as a sales deck; a post-production editor doing color and grade.

---

## 1.5. Artifact shape (LOCKED 2026-05-18)

**The lane produces a SET OF 5 SHORT-FORM VIDEO STORY PLANS, each 90 seconds to 8 minutes.** Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that single-plan outputs score higher on SB-2/SB-3 (hook, emotional arc) while portfolio outputs score higher on SB-5 (diversity), producing inconsistent artifact shapes that fail SB-5's cross-plan portfolio check. The 5-plan set is the artifact unit, not the individual plan.

**Form factor per plan:**
- One **voice-script** (the spoken VO or on-camera dialogue) sized to the target plan duration
- One **scene list** with named beats, durations, camera-move primaries, consistency anchors
- One **declared rendering model** field (per capability research §5 — routes to `configs/storyboard/supported_models.yaml`)
- Plan-level metadata: hook sentence, claimed emotional arc, declared stakes, citation list (for any factual claim), pattern-data anchor references (for first-person claims)

**Out of scope shapes (the lane will NOT produce these):**
- A single video plan (the lane unit is the 5-plan set; individual plan handed off to render is downstream)
- A traditional screenplay or shooting script (different audience, different format)
- A marketing deck or campaign storyboard (sells the idea to client; doesn't drive production commitment)
- Longer-form episodic content (>8 minutes; serial structure presumes different commitment-shape)

**Why one shape:** the Reader spec (creator/brand-author/founder-led with 5–15 minutes to commit) and Success spec (commit to producing one plan or reject all 5) point unambiguously to portfolio form. SB-5 portfolio diversity presumes 5 plans; SB-1 voice fidelity is scored per-plan but read across the portfolio for cohort-default detection.

**Empirical validation scope.** Form factor is research-grounded against creator-strategist literature (MrBeast / Pixar / Neistat / Harris) + first-cohort business-client fixtures (Klinika, DWF, B2B SaaS founder). When fixtures from new archetypes appear — established YouTube creator with deep pattern data, podcaster commissioning video adaptation, music artist commissioning a video plan — re-validate the form factor. Established creators may justify lane variants (e.g., per-plan substrate may be a single deep plan, not a portfolio); founder-led may justify shorter portfolios (3 plans probing 3 postures while the founder discovers their voice).

**Shape enforcement lives in `structural_gate`, NOT in the judge criteria.** The judge tests outcomes (SB-1..SB-6 below); the workflow's `structural_gate` tests shape conformance (5 plans present, voice-script and scene-list per plan, declared rendering model, citation list, consistency-anchor section). Per design guide §11.1, this preserves the outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18)

After reading the 5-plan set, the reader commits to producing one specific plan — or rejects all 5 and asks for a new set. The commitment is specific enough that they could pitch the plan in 30 seconds to their editor and the editor would immediately know what to cut for. The hook is something they'd say aloud in a coffee meeting and the listener would ask "send me the link when it's done." The claimed emotional response — wonder, dread, awe, recognition, vulnerability — is something they could point at on the page: "this beat produces it, here."

The reader knows what they're giving up by picking this plan over the other four. They could explain to their producer in one sentence why this premise beats the next-best alternative they're declining. **Sleep test:** if they slept on it overnight, they'd commit to producing the same plan tomorrow — the plan's promise survives 24 hours of reflection, not just momentum.

The plan is **traceable**: every factual claim (stat, study, named-source quote) has a citation; every first-person experiential claim either matches the creator's published anchor, is explicitly flagged as scripted-fiction, or is generically lived-in ("when you first walk into a Polish dermatology consult" — true of any patient experience). When the creator shoots it, the resulting video looks like the creator made it (or like the brand's editorial voice on camera), not like an AI imitated the creator.

World-class real-world exemplars — used as quality anchors, NOT as templates to copy:

**Cross-form rigor (the ceiling):**
- **MrBeast handbook stair-step** — $1 firework → $100K firework → world-record firework. Progressive escalation as the within-video version of portfolio diversity. The handbook is explicit that wow-factor + retention curve do NOT save a plan with no stakes.
- **Johnny Harris visual-first script** — visual evidence carries the script; the voice-script supports what the eye is processing rather than vice versa. Most rigorous of the reference set on script-vs-visual subordination.

**Practitioner-grade (the achievable floor):**
- **Casey Neistat three-act-in-ten-minutes** — three-act compression where the bookend reframes the opening. Workmanlike, closer to what real fixture plans look like, earns its place when executed well.
- **Hank Green vlogbrothers** — written for one specific person (his brother). Voice-as-discipline grounded in a known audience rather than "the internet."
- **Tom Scott single-take** — pause-and-reveal beats calibrated; the camera does the work that cuts would do for a different creator. Voice as cadence.
- **Cleo Abram portfolio** — shorts that share a creative universe but bet on 5 different premises. Portfolio-diversity exemplar.

What ties these together: a point of view at the top, structural reasoning about why this story exists, beats that earn their emotional position, and a premise the creator could defend over a coffee meeting.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — four failure modes the judge must discriminate against

**Well-paced and pointless.** Plan moves competently, every beat lands on the page, the emotional metadata claims a coherent arc — and the story has nothing at stake. Reads as "a person walks into a coffee shop and has a realization." The MrBeast handbook's named "well-shot, well-paced, pointless" failure. Most common AI-generated short-form failure mode per the domain research.

**Generic creator voice — the median-creator trap.** The voice-script reads as a competent generic creator essay. No signature obsessions, no distinctive cadence, no named props the creator has actually used. Per stylometric research, frontier LLMs without explicit anchor converge on a "high-entropy YouTube essay neutral" register matching nobody. The plan reads competently and the resulting video would look like ChatGPT's idea of a creator brief.

**5 plans that are 5 variations on the safest premise.** Portfolio dressed to look diverse — different premises in surface description, different emotional registers in metadata — collapsing under inspection to the same structural shape. The AI found one safe premise and 5-times-served the same dish with different garnishes.

**Capability-blind ambition.** Plan specifies shots that current AI video models cannot render at usable quality (legible long text on signs, sustained multi-character lip-sync to externally-authored dialogue, multi-room continuous-motion takes, sub-second-precise timing of named beats, complex multi-constraint camera moves) — AND does NOT flag fallback strategy. The creator commits, regenerate-loops eat 20-50 credits, the artifact-laden gen ships into the final cut, or the team falls back mid-production to a salvage live-action shoot. Capability-blind plans waste real production money — industry-reported 15-25% credit-waste rate.

### 3b. Goodhart-collapse — Phase 4 pathology + storyboard-specific AI-failure surfaces

**Phase 4 pathology (the historical Goodhart trap).** 50-generation evolution against a feature-checking judge produced exactly the pathology rolled back at `c76f051`. The workflow learns to slot-fill surface markers:

- **Every plan opens with a high-specificity sensory hook** regardless of whether the rest of the plan supports it. Surface marker present, premise empty.
- **Every plan declares a target emotion in metadata** ("the viewer now feels dread at 0:35") that isn't earned by any specific producing beat.
- **Every plan inserts a "stakes" sentence** ("if this doesn't work, X loses Y") whether the story has actual stakes or not. The sentence is the marker; the stakes are absent.
- **Every plan namechecks the creator's known obsessions** whether they're load-bearing for this story or just lip-service. Pattern-data fragments stuck on without grounding.
- **Every set of 5 plans is templated to look diverse** — different premises labeled, different emotional registers labeled — while all 5 collapse to the same structural shape.

**Storyboard-specific AI-failure surfaces (new in v1, per the four research deliverables):**

- **Script confabulation — fake stats, fake studies, fake quotes.** The plan hooks or pays off on a factual claim: "73% of creators…", "A Harvard 2024 study showed…", "As Einstein once said…". No cited source. Confabulation rates: 40–80% on open-ended generation (sqmagazine 2026 compilation of TruthfulQA / HaluEval); 19.9% citation-fab rate on GPT-4o literature reviews (Chelli et al. 2025); 75% case-fabrication on legal QA (Stanford 2024 RegLab). Catastrophic for storyboards specifically because the rendered video *broadcasts* the falsehood to thousands of viewers.

- **False personal experience — first-person "I" for events that didn't happen.** Plan generates first-person voice-script describing events the creator didn't experience: "I tried X for 30 days" when they didn't, "When I was in Tokyo last summer" when they weren't, "my mom always told me" — fabricated relational anecdote plausibly matching the voice extracted from pattern data but never happened. Per arxiv 2505.01800 (Distinguishing AI-Generated and Human-Written Text via Psycholinguistic Analysis): AI models lack experiential grounding; emotional expressions in AI texts appear flat, stereotyped, or overly uniform. StoryScope (arxiv 2604.03136) confirms across 10,272 prompts × 5 LLMs.

- **Narrative-arc gaming.** Plan hits all the formal beats — hook, tension, payoff, CTA — but each is generic filler that doesn't earn its position. Hook promises X; body delivers Y. Tension isn't tensed. Payoff doesn't pay off. Structure compliant, substance empty. Storyboard analogue of CI's "plausible strategy memo with no actionable specifics."

- **Hook-formula slot-fill across the portfolio.** All 5 plans open with "what if I told you…", or all 5 with "the [X] you didn't know existed", or all 5 with "I tried [X] for 30 days." Patterns work individually (measured 3-second-hold retention lift); templated reuse across the portfolio produces 5 plans that read as one. TikTok 2026 explicit downranking: "identical trend templates without adding substantial originality."

- **Video-specific confabulation — shots that can't be sourced or produced.** Plan calls for shots, b-roll, or visual evidence the creator cannot acquire within their actual production constraints. Travel/location confab ("Tokyo skyline drone" when creator shoots a Brooklyn kitchen), rights-violating b-roll ("2007 iPhone reveal" / "that scene from Inception"), unavailable guest ("interview with [named expert]" never contacted), impossible-prop b-roll, stat-as-visual confab (chart of a mode-1 fabricated number).

Every surface marker present, structurally compliant, semantically empty — and now publicly broadcast as well. The judge that rewards these gets the workflow that learns to produce them.

**Historical context.** The sibling CI lane triggered three prior rollbacks for the same Phase-4 pathology: `2ce99bb` (σ-widening prose), `ca4a256` (v2 contract-prose), `698e658` (Phase 4 feature-checking → `c76f051`). The criteria below are designed to resist re-creating any of them AND to surface the storyboard-specific AI-failure surfaces those rollbacks didn't address.

**Deterministic AI-failure checks live in `structural_gate`** — stat-grep against citation list, quote-grep against citation list, "as of" date requirement on time-sensitive claims, rights-flag grep on commercial titles / copyrighted footage / named commercial music. Per the OpenRubrics design principle (Hard Rules → structural_gate, Principles → judge), deterministic verification belongs in `structural_gate` because the judge cannot deterministically verify citation existence, quote provenance, freshness signaling, or rights status — those are factual checks, not semantic judgments. **Semantic source-tracing and lived-experience integrity lives in SB-6** below.

---

## 4. Criteria — outcome questions (6)

### SB-1 — Sounds like the creator (or brand, or founder) made it

**Outcome question (binary):**
Does the plan's voice — sentence cadence, vocabulary register, named details, recurring obsessions — match the client's actual published anchor in `source_data`, rather than reading like a generic AI imitation of a creator in this register? If the client read it, would they say "yeah, this is me" or "this is what me sounds like to someone who studied my videos for an afternoon"?

**Score 1 (yes)** — Voice-script demonstrates (a) at least one specific named detail, prop, place, or obsession that matches or extends the client's published anchor; (b) sentence-length and vocabulary register in-distribution against the anchor; (c) opening-sentence shape matching the client's habitual opening pattern; (d) the specific way this client surprises an audience is present — the worldview turn, juxtaposition, or signature reframe that distinguishes them from a competent imitator, not just generic markers of competence; (e) the script is performable speech with designed silence — a voice actor (or the client) could perform it cold, and what is deliberately absent, processed, or contrasted in the audio direction carries as much story as the visuals. Reads as a draft the client could perform without translation. In `pattern_data_density="cold"` regime: plan is consistent with the declared brand-voice posture AND shows at least one distinctive marker that isn't cohort-default (named obsession, specific worldview marker, recurring formal choice).

Example A — creator-led (do not optimize toward this): for a creator whose published anchor consistently references their Tuesday-morning regular Marco and the original 1987 espresso machine in the back room, plan names Marco and the espresso machine in a beat that fits the story.

Example B — founder-led business (do not optimize toward this): for Dr. Maria Noszczyk at Klinika Melitus whose written anchor uses clinical precision ("a 0.5 mm needle gauge," "Restylane Vital Light not Vital Skinbooster") and warm patient-address ("when you come in for the consult"), plan names the specific product line and uses the second-person consult-room register rather than glossy aesthetic-influencer voice.

Example C — brand-author (do not optimize toward this): for a B2B SaaS brand whose editorial voice carries dry-technical-but-warm register (Stripe-style "the boring thing well-explained"), plan voice-script avoids enthusiasm markers ("amazing," "incredible") and stays in the brand's actual published cadence.

**Score 0 (no)** — Voice-script reads as generic creator-archetype voice. Named details (if present) don't match the anchor — generic placeholders ("a coffee shop") where named details should be. Sentence cadence drifts toward AI-essayistic register regardless of client's actual cadence. Opening sentence shape is generic ("Have you ever wondered...", "In today's video..."). Reads as ChatGPT-trying-to-sound-like-a-creator. In cold-start: plan reads as cohort-default median voice (would be a fine first plan for any client in this category, not specifically this client).

**Score 0.5 (unknown)** — Voice match is borderline OR `source_data` contains fewer than 3 anchor samples to score against. Emit 0.5 + "unknown" + one sentence: either (i) which dimension is borderline, or (ii) "fewer than 3 anchor samples — cannot reliably score voice match." In cold-start: plan is consistent with declared posture but reads as cohort-default — competent but not yet distinctive.

**Required CoT:**
- Step 1: Read the anchor samples in `source_data` and the `pattern_data_density` flag. List the client's voice markers: typical sentence-length range, vocabulary register, recurring named details / obsessions / phrases, opening-sentence shape. If cold-start, list the declared brand-voice posture instead.
- Step 2: For the plan's voice-script, verify (a) at least one named detail matches or extends the anchor's specific references, (b) sentence cadence in-distribution against anchor, (c) opening shape matches habit. In cold-start: verify consistency with declared posture AND presence of at least one distinctive non-cohort-default marker.
- Step 3: Emit verdict + one-sentence justification. If pattern data has <3 anchors AND cold-start has no brand-voice doc, emit 0.5 + "unknown" + missing-anchor note.

Do not score: total length, scene count, voice-script header presence (structural_gate); function-word divergence against anchor (structural_gate); em-dash density (structural_gate); n-gram overlap with anchor — anti-laundering (structural_gate); performance dimensions (comic timing, on-camera energy, rhythm-in-performance — not the judge's job; the script cannot encode them).

**Honest bound.** PAN-CLEF authorship-verification benchmarks ceiling at 70–80% AUC for frontier-grade methods on short texts. SB-1's score-1 verdict should be reserved for unambiguous matches; borderline cases route to 0.5 generously rather than forced to 0 or 1.

### SB-2 — Irreplaceable hook

**Outcome question (binary):**
Is the hook a concrete, specific image or sentence that could not come from any other story? Could the creator describe it to a friend in one breath and have the friend reply "send the link when it's done"? Specificity and irreplaceability — not which mechanism achieves them.

**Score 1 (yes)** — The hook is a sentence or image so specific it could not be substituted with a generic alternative. The mechanism may be impossible-concept, raw emotional vulnerability, absurd juxtaposition, visual impossibility, declarative-imperative, question-as-thesis — what matters is irreplaceability, not which mechanism.

Example (do not optimize toward this): "I Spent 50 Hours In Ketchup" beats "I Spent 50 Hours In My Front Yard" not because ketchup is funnier in the abstract but because the substitution test fails — you cannot replace "ketchup" with another noun and get the same hook.

**Score 0 (no)** — Hook is content, not promise. Hook could be swapped for another similar concept without losing anything. Hook is engagement-bait without a specific premise behind it. Hook is a clichéd opener-formula slot ("what if I told you…", "the X you didn't know existed") with no specific premise behind it.

**Score 0.5 (unknown)** — Hook is specific but the substitution test is borderline (could swap one or two elements and still work). Emit 0.5 + "unknown" + one sentence on which element is generic.

**Required CoT:**
- Step 1: Identify the hook (first scene or first 1–2 sentences of voice-script).
- Step 2: Run substitution test — could you swap the key noun/image/claim for a similar one and lose nothing essential?
- Step 3: Emit verdict + one-sentence justification.

Do not score: hook length, hook position (script vs scene 1), use of question-form hooks (mechanism agnostic), whether hook matches a named retention-formula (irrelevant — irreplaceability is the test).

### SB-3 — Earned emotional arc with real stakes (sharpened)

**Outcome question (binary):**
Is the claimed emotional response (wonder, dread, awe, recognition, vulnerability) actually produced by a specific beat in the story — and does the hook's promise match what the body delivers? Would a viewer finish the rendered video and feel the thing the metadata claims, rather than feeling "that was well-shot and pointless"?

**Score 1 (yes)** — Every claimed emotional transition maps to a specific producing beat (a revelation, an action, a juxtaposition) — emotion in metadata is paired with the beat that creates it, not just declared. The story has stakes: something is at risk, the protagonist wants something, the resolution changes someone or something. The hook's promise matches what the body delivers (hook promises X; body delivers X — not X promised, Y delivered). The opening means something different by the end (turn / reframe / bookend).

Example (do not optimize toward this): plan claims "viewer feels dread at 0:35"; at 0:35 there is a specific beat — the camera pans to the open back door that should have been locked — that produces dread. Hook promises "I locked the door behind me"; body delivers the moment it wasn't.

**Score 0 (no)** — Emotion declared in metadata, not produced by any specific beat. No stakes — nothing at risk, no question being answered, no change. Story is a vignette, not an arc. Hook promises one thing; body delivers another (hook-body mismatch). Single underlying signal extended into multiple beats by restatement (one idea expanded into 4 paragraphs).

**Score 0.5 (unknown)** — Stakes present but emotional beats are vague, or beats are specific but stakes are unclear, or hook-body alignment is borderline. Emit 0.5 + "unknown" + one sentence on which is weak.

**Required CoT:**
- Step 1: Identify the claimed emotional arc (from `emotional_map` or metadata) and the hook's promise (first 1–2 sentences).
- Step 2: For each claimed emotional transition, find the specific producing beat. Identify the stakes (what's at risk, what changes). Verify the body delivers on the hook's promise (no hook-body mismatch).
- Step 3: Emit verdict + one-sentence justification.

Do not score: number of emotions claimed, density of emotion-tags, whether the arc follows a named structure (Story Spine, Story Circle, Save the Cat) — all framework-name embedding violations.

### SB-4 — Within rendering envelope (model + production-source)

**Outcome question (binary):**
Given the declared rendering model and the creator's stated production constraints, can every scene actually be produced at usable quality? Are out-of-envelope scenes flagged with a usable fallback — OR are they capability-blind ambitions that will eat credits, ship with artifacts, or force mid-production salvage?

**Score 1 (yes)** — Every scene either (a) stays within the declared rendering model's envelope for duration, multi-character, text, camera moves, beat timing, AND within the creator's production-source constraints (location, rights, guest access); OR (b) is explicitly flagged with a usable fallback (route to a different renderer named in the supported list, route to live-action shoot, redesign to fit envelope). Consistency anchors are functional engineering decisions naming what must stay identical between clips (specific named appearance markers, specific lighting key with directional anchor, specific prop continuity rules) — not decorative restatement. Plan acknowledges regen-risk for in-envelope but ambitious shots ("expect 2-5 regenerates on this multi-character scene"). The model declared in the plan's metadata matches the shot grammar the plan calls for.

**Score 0 (no)** — One or more scenes contain elements current models cannot render reliably (legible long text on signs, sustained multi-character lip-sync to externally-authored dialogue, smooth continuous motion through multiple environments, sub-second-precise timing of named beats, multi-constraint camera moves) WITHOUT a fallback strategy. OR scenes are too vague to interpret ("a person in a room"). OR consistency anchors are decorative ("the character looks consistent") not engineering. OR production-source constraints are ignored — plan calls for shots the creator cannot acquire (location they don't have access to, rights they don't have, guest never contacted).

**Score 0.5 (unknown)** — Most scenes are within envelope; 1–2 ambitious scenes are load-bearing and may fail without explicit fallback. Emit 0.5 + "unknown" + one sentence on which scene is at risk.

**Required CoT:**
- Step 1: Identify the declared rendering model (from plan metadata; structural_gate already verified it's in the supported list).
- Step 2: For each scene specification, map against the declared model's envelope (durations, multi-character continuity, text legibility, camera-move count, beat-timing tolerance) AND against the creator's stated production-source constraints (location, rights, guest access).
- Step 3: For out-of-envelope scenes, verify the fallback strategy actually resolves the gap (not pro-forma flagging). Evaluate consistency anchors as functional engineering vs decorative restatement. Verify model declared matches shot grammar called for.
- Step 4: Emit verdict + one-sentence justification.

Do not score: scene count, scene-prompt length, presence of camera-direction fields (structural_gate); model preference in the abstract (any in-list model is acceptable); whether the model is "the best" for this kind of work (relative ranking ties the judge to fleet specifics that rotate); model names by enumeration (routed to `configs/storyboard/supported_models.yaml`).

**Fleet context (May 2026, for reasoning toolkit only — NOT enumerated in prose).** Persistent capability boundaries: (1) legible long text on signs, (2) sustained character-consistent multi-character interaction in one shot, (3) precise lip-sync to externally-authored dialogue across cuts, (4) multi-constraint camera moves, (5) sub-second-precise timing of named beats. These boundaries persist across the full fleet and are unlikely to clear within 6 months. The supported model list is maintained quarterly by the operations team.

### SB-5 — Creator pacing + portfolio diversity (cold-start reframed)

**Outcome question (binary, WARM regime — `pattern_data_density="lukewarm"` or `"warm"`):**
Does the pacing (duration, scene count, cut frequency) match how the creator's actual videos move — not how a screenplay reads? AND across the 5 plans submitted, are they genuinely different bets (different premises, different emotional registers, different structural choices, different hook-formula fingerprints) sharing a creative universe — not 5 variations on the safest premise the AI found easiest to generate?

**Outcome question (binary, COLD regime — `pattern_data_density="cold"`):**
Across the 5 plans, do they probe at least 3 genuinely different voice postures (different formal stance, different relationship to the viewer, different rhythm of attention) sharing one premise frame the client commissioned? Could the client read all 5 and have a defensible opinion about which posture feels closest to their voice?

**Score 1 (yes), WARM** — Pacing matches the creator's native cadence (from pattern data). For plans over ~45 seconds, at least one explicit retention-reset beat is named ("at 1:30, cut to the impossible reveal"). Across the 5 plans, 3+ are genuinely different bets — different premises, different emotional registers, different hook-formula fingerprints (e.g., declarative-imperative + sensory-scene + stat-led + tension-first + question-first as 5 different formulas; 5 "what if I told you" openers count as one) — sharing the creator's voice.

**Score 1 (yes), COLD** — 3+ genuinely different voice postures probed (different formal stance, different relationship to viewer, different rhythm of attention), each tested against the same premise frame, each plan internally consistent in its chosen posture. The client could read all 5 and have a defensible opinion about which feels closest.

**Score 0 (no), WARM** — Pacing forces the creator off their native cadence — the plan moves the way a screenplay reads, not the way the creator's real videos move. No retention-reset for longer plans. The 5 plans are variations on the same premise dressed differently, OR all 5 use the same hook-formula fingerprint.

**Score 0 (no), COLD** — 5 plans all in the same voice posture, OR 5 plans across different postures but each plan internally incoherent (mixing postures within one plan), OR premise frame drifts across the 5 plans (5 different premises in cold regime when the brief specified one premise frame).

**Score 0.5 (unknown)** — WARM: Pacing matches but portfolio diversity is borderline (3 strong bets, 2 dressed-up variations). COLD: 3 distinct postures plus 2 variations of the same posture, OR 5 distinct postures but premise frame drifts. Emit 0.5 + "unknown" + one sentence on which plan is weak.

**Required CoT:**
- Step 1: Read `pattern_data_density` flag. If WARM/LUKEWARM: identify creator's native pacing pattern from pattern data. If COLD: identify the declared premise frame from the brief.
- Step 2 (WARM): For each plan, verify pacing match + retention-reset for plans >45s. Across the 5, identify how many are genuinely distinct bets — different premises AND different hook-formula fingerprints. Step 2 (COLD): For each plan, identify the voice posture taken (formal stance + viewer relationship + rhythm-of-attention). Across the 5, count distinct postures and verify each plan is internally consistent in its chosen posture.
- Step 3: Emit verdict + one-sentence justification.

Do not score: total duration, scene count as a numeric target (varies by creator), presence of explicit "Plan 1/2/3/4/5" labels, cohort-default voice match (toxic for cold-start — produces regression-to-mean voice and silently penalizes legitimately distinct emergent voice).

**Cold-start anti-regression-to-mean defense.** Cohort priors ("aesthetic-medicine clinic owner voice family," "B2B SaaS founder voice family") are explicitly NOT to be used as default reference for SB-5 cold-start scoring. The 5-plan portfolio is REPURPOSED in cold-start as a voice-discovery instrument — diversity-of-posture rewarded; same-posture-as-cohort penalized as regression-to-mean. This is the load-bearing cold-start prescription. Per cold-start research §4, the failure is silent — workflow won't surface that it's optimizing toward median voice; variance instrumentation per design guide §11.5 catches this only if cold-start SB-5 variance is tracked separately from warm-start SB-5 variance.

### SB-6 — Plan survives lived-experience and source-tracing (NEW in v1)

**Outcome question (binary):**
For each factual claim and each first-person experiential claim in the voice-script, can the reader trace the claim — to a cited source for factual claims, OR to a pattern-data anchor (or explicit scripted-fiction flag) for first-person claims? Or does the plan include claims the creator would have to fabricate on camera, quietly drop before production, or publicly broadcast as truth?

**Score 1 (yes)** — Every factual claim (stat, study, named-source quote, attributed quote) has a citation in the plan's `citations` list AND every first-person experiential claim either (a) matches a `pattern_data` anchor (creator-history field; the creator has documented this experience), (b) is explicitly flagged `scripted_fiction: true` (the plan acknowledges this is fiction the creator will perform as fiction), or (c) is generically lived-in (universal experience true of any reasonable member of the audience — "when you first walk into a Polish dermatology consult" rather than "when I walked in for my first consult last Tuesday"). Confidence is calibrated to evidence depth — strong claims have multi-source backing; tentative claims are flagged tentative.

Example (do not optimize toward this): "73% of patients self-treat with off-label retinoids before their first consult" — cited to Polish Aesthetic Dermatology Survey 2025, URL resolves, "as of" date present. "When my mom asked me about Botox last Christmas" — flagged `scripted_fiction: true` because the creator's pattern_data shows no published reference to her mother + Christmas + Botox; alternatively, the plan rewrites to "when a friend's mom asks about Botox over Christmas dinner" as generically lived-in.

**Score 0 (no)** — At least one stat / study / quote asserted with no citation. OR a specific first-person experiential claim ("I tried X for 30 days," "When I was in Tokyo last summer") cannot be matched to pattern-data and is not flagged scripted-fiction. OR plan contains script-confabulation tells (a "Harvard study" with no link, a quote attributed to a famous person who never said it, a fabricated percentage). OR plan contains false-personal-experience tells (first-person specific claim that contradicts or has no support in pattern_data — creator did 3-day, plan says 30; creator has no published reference to "my mom," plan invents a maternal anecdote). OR plan contains video-production confabulation (shots that can't be sourced — Tokyo skyline drone when creator shoots Brooklyn; rights-violating b-roll without licensed flag).

**Score 0.5 (unknown)** — Citations or anchors partially present; at least one major claim is borderline (citation exists but URL not resolvable from plan alone; first-person claim could plausibly be lived-in but pattern_data is thin). Emit 0.5 + "unknown" + one sentence on which claim is unanchored.

**Required CoT:**
- Step 1: List every factual claim in the voice-script (stats, studies, named-source quotes, attributed quotes).
- Step 2: List every first-person experiential claim ("I…", "my…", "when I was…", "last [time-marker] I…").
- Step 3: For factual claims, verify citation is present and that the cited entity is named (URL resolution lives in structural_gate). For experiential claims, verify pattern-data anchor OR scripted-fiction flag OR generically-lived-in framing.
- Step 4: Flag any script confabulation (fake stat / fake study / fake quote), false personal experience (specific first-person claim not in pattern_data and not flagged scripted), or production confabulation (shots that can't be sourced).
- Step 5: Emit verdict + one-sentence justification.

Do not score: citation count or footnote density (structural_gate); completeness of pattern-data (operator-side concern, not judge); presence of citation-list section header.

**Note on the ≤5 ceiling.** SB-6 is a justified breach of design guide §5's ≤5 criterion ceiling. Rationale documented in §7 below. The redundancy check (§8) will tell us empirically if SB-6 correlates with another criterion >0.7 across re-runs; most-likely-to-merge pair is SB-1 ↔ SB-6 (both test grounded-vs-ungrounded at different layers — voice anchor vs source/experience anchor). Don't fight the absorption if it happens.

---

## 5. Shared judge-prompt wrapper

```
You are scoring a set of 5 short-form video story plans (each 90s
to 8min) for a specific client. The client may be (a) a creator
with established voice signature, (b) a creator strategist or
content lead commissioning for a brand, or (c) a founder-led
business commissioning thought-leadership / patient-education /
explainer video. The reader is the client themselves (or the
commissioning party), about to commit to producing one of the 5
plans.

The plan set is the lane's locked artifact shape: 5 plans, each
with voice-script + scene list + declared rendering model +
citation list + pattern-data anchor references. Read all 5 before
scoring SB-5 (portfolio diversity); SB-1..SB-4 and SB-6 may be
scored per-plan but the digest aggregates across the 5.

Read `pattern_data_density` flag from session metadata (cold /
lukewarm / warm). For SB-1 and SB-5, apply the regime-appropriate
prose. In COLD regime: cross-modal signal (brand voice doc,
written corpus, podcast transcripts) is treated as POSTURE anchor
only, not FIDELITY anchor. Cohort priors ("aesthetic-medicine
clinic owner voice family," "B2B SaaS founder voice family") are
explicitly NOT to be used as default reference — score against
the client's declared posture and distinctive markers, not
against generic-cohort competence.

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale that follows the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the plan alone, emit
0.5 + "unknown" + one sentence on what would have to be present
to commit to 1.

The reader has seen enough AI-generated story plans that are
well-paced and pointless to recognize the pattern. They want a
plan they could shoot tomorrow, not a plan that looks like
ChatGPT's idea of a creator brief. Score for whether the plan
would actually get produced AND result in a video that looks
like the client made it AND survives source-tracing — not for
whether the plan contains specific metadata fields, named
frameworks, or template sections.

Emit per-criterion JSON:
{"criterion_id": "SB-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **SB-1**: Named-detail stuffing without pattern-data grounding doesn't pass — details must match the client's actual published anchor (CoT Step 2 forces the comparison). Function-word mimicry without obsession-grounding doesn't pass — outcome question asks whether plan names the client's *actual* obsessions. Anchor-paraphrase laundering doesn't pass — n-gram anti-laundering lives in structural_gate. Cold-start regression-to-mean voice doesn't pass — distinctive-marker requirement is explicit. **Median-creator-trap defense**: in cold-start, generic-competent voice without a distinctive marker scores 0.5, not 1.

- **SB-2**: Specific-sounding hooks that fail the substitution test (could swap a noun and still work) don't pass. Clichéd opener-formulas without specific premise behind them don't pass. **Name-drop-slot-fill defense**: hook must be irreplaceable, not just specific-sounding.

- **SB-3**: "Viewer now feels X at 0:35" metadata without a producing beat at 0:35 doesn't pass. Hook promising X with body delivering Y doesn't pass. Single signal restated three ways doesn't pass. **Narrative-arc-gaming defense**: emotional metadata must map to a specific producing beat; hook-body coherence is required.

- **SB-4**: Decorative consistency anchors ("looks consistent") don't pass — engineering-grade anchors with specific named appearance markers + lighting key + prop rules required. Banned-construct phrases without fallback flags don't pass — structural_gate enforces. Pro-forma stitch_strategy without resolving the gap doesn't pass. Model declared mismatching shot grammar doesn't pass.

- **SB-5**: Templated "5 different bets" labels on 5 variations of the same premise don't pass — hook-formula fingerprint variety required across the 5. Cohort-default voice match in cold-start doesn't pass — distinctive-posture probing required. **Hook-formula-slot-fill defense**: SB-2 enforces per-plan irreplaceability; SB-5 enforces across-portfolio fingerprint variety; neither alone sufficient.

- **SB-6**: Confident factual claim without a citation doesn't pass — structural_gate stat-grep / quote-grep enforces; semantic source-tracing is the judge's residual. First-person specific claim without pattern-data anchor or scripted-fiction flag doesn't pass. Shots that can't be sourced (location / rights / guest) without fallback don't pass. **Anchor-paraphrase-laundering defense**: paraphrasing anchor content into a fabricated "lived experience" doesn't satisfy SB-6; pattern-data must contain the underlying anchor.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0.

---

## 7. Verification — does v1 conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (3 archetype examples per criterion where applicable: creator-led / founder-led / brand-author) ✓
- §5 criterion count: **6 (documented exception to ≤5 ceiling)** — see note below
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3–5 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §11 Goodhart-resistance verification ✓
- §13 specimen criterion template followed ✓

**Note on the ceiling exception.** SB-6 (Plan survives lived-experience and source-tracing) is a 6th criterion justified by the AI-specific failure surface documented across two research deliverables — script confabulation at 40–80% open-ended rate (sqmagazine 2026 compilation of TruthfulQA / HaluEval); citation confabulation at 19.9% rate on GPT-4o literature reviews (Chelli et al. 2025); legal-case fabrication at 75% rate (Stanford 2024 RegLab); false personal experience per arxiv 2505.01800 (Psycholinguistic Analysis — AI models lack experiential grounding); production confabulation per Moonlight 2026 (Survey on Hallucination in Video LLMs). This mirrors the CI-6 precedent at `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §7. Asymmetric risk vs CI: storyboard outputs *broadcast* the confabulation to thousands of viewers; reputational cost dominates production cost; unlike CI briefs (one decision-maker who verifies before acting), storyboard fabrication goes public.

**"Looks elaborate" ≠ "over-engineered."** Each elaboration here is a thin defense against a measured failure rate. SB-6 alone defends against 4 documented LLM-specific failure modes (script confab, false personal experience, narrative-arc gaming partial, production confab) that SB-1..SB-5 cannot catch. The 7 SB-1 structural_gate checks each defend a specific stylometric-attribution failure shape. The 8 SB-4 structural_gate checks each defend a specific capability-blind production-cost shape. The 4 SB-6 structural_gate checks each defend a specific confabulation shape. Cutting any of these shifts brittleness from a testable layer (`structural_gate`) to a layer that can't do the work (the semantic judge).

The redundancy check applies. Subject to the same rule as the rest: **the live count may absorb to 5 after the check runs** — most-likely-to-merge pairs are SB-1 ↔ SB-6 (grounded-vs-ungrounded at different layers — voice vs source/experience) and SB-3 ↔ SB-5 (story-structure overlap — earned arc vs creator pacing). Don't fight absorption when it happens; the cost of one judge call is small, the cost of redundant signal in the digest is larger.

Length per criterion ≈ 250 words (longer than the design guide's 150-word target due to 3 archetype examples on SB-1 and the cold-start/warm-start fork on SB-5; absorbable per CI v3.3 precedent). Total spec body ≈ 4800 words including §1.5, §3b, and SB-6 expansions.

---

## 8. Open questions

Reader / Artifact-shape / Success / Failure / 6 Criteria are LOCKED at v1. Remaining:

1. **Pairwise redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 6 criteria × 3 panel models = ~90 calls (~$35). Drop any criterion correlating >0.7 with another. Expected live floor 4–5. Most-likely-to-merge pairs: **SB-1 ↔ SB-6** (voice grounding vs source/experience grounding both test "is this real" at different layers); **SB-3 ↔ SB-5** (earned emotional arc vs creator pacing both test story-structure integrity); **SB-4 ↔ SB-6** (capability awareness vs source-tracing both test "can this be produced"). If SB-6 absorbs into SB-1 or SB-4, the absorbing criterion's prose extends to cover SB-6's failure surface — don't simply delete the protection.

2. **Cold-start workflow flag implementation.** `pattern_data_density` (cold / lukewarm / warm) must be computed in `structural_gate` from session metadata and passed to the judge prompt. Cold = 0 published videos OR ≤1 video with <500 words written corpus and no podcast/talk corpus. Lukewarm = 2–4 published videos OR 1 video plus substantial cross-modal corpus. Warm = 5+ published videos OR cross-modal equivalence. Parallel to `linkedin_engine v040 cold-start mutation` pattern per memory — implementation likely shares structural_gate helpers across SB / X / LinkedIn lanes. Coordinate.

3. **`structural_gate` expansion (before spec ships to v006/workflows).** Add the following anti-hallucination + shape-conformance + voice-fidelity + capability checks. Existing v006 checks (3+ scenes, voice-script present, banned-phrases) stay.

   **SB-1 voice-fidelity checks (7, per voice-fidelity research §Synthesis):**
   - Function-word divergence < 0.4 (cosine of function-word frequency vectors against anchor)
   - Sentence-length distribution within 1.5 stdev of anchor mean (Kolmogorov-Smirnov or bin-comparison)
   - AI-slop phrase blocklist ("moreover," "furthermore," "in conclusion," "let me explain," "the truth is," "interestingly," "what's even more remarkable")
   - Em-dash density < 1.5x anchor mean (per Yang et al. arxiv 2509.13245)
   - Anti-laundering n-gram check: no 5-gram in voice-script appears verbatim in any anchor sample
   - Specificity rate: ≥2 named entities per 100 words (NER-based)
   - Anchor sufficiency: `source_data` contains ≥3 anchor pieces; if not, structural_gate passes but judge sees `anchor_insufficient` flag and emits 0.5 on SB-1

   **SB-6 source-tracing checks (4, per AI-failure-modes research §7):**
   - Stat-grep — every numeric in voice-script (`\d+%`, `\$\d+`, `\d+x`, ranked-list patterns) must appear in `citations` with source URL
   - Quote-grep — every direct quote (string in `""` + attribution verb) must match a verified citation
   - "As of" date required on time-sensitive factual claims
   - Rights-flag grep — commercial film titles, copyrighted footage, named commercial music in scene-description must be paired with `rights_status: licensed`

   **SB-4 capability checks (8, per capability research §Recommendations):**
   - Plan declares `rendering_model` field with value in `configs/storyboard/supported_models.yaml`
   - Every scene declares `duration_sec`; sum ≤ declared total runtime
   - For scenes where `duration_sec` > model native clip length, `stitch_strategy` field present (`scene_extension` / `pikaframes` / `manual_cut` / `multi_shot_native`)
   - `consistency_anchor` block present with required fields (`subject_name`, `appearance_markers` ≥3, `lighting_key`, `prop_list`, `environment_markers`)
   - Banned-construct lint per scene (legible text, lip-sync to external, 3+ characters speaking, smooth motion through 2+ rooms) without `fallback_strategy` field
   - Per-scene `primary_camera_move` single-value enum (static / dolly / pan / tilt / orbit / crane / handheld / tracking)
   - Per-scene `beat_timing_tolerance_sec` ≥ 0.3s if any named beat references a specific timestamp
   - AI-slop banned-phrase list extension (em-dash density, "let me explain why," "moreover," "the perfect [shot|scene|moment]")

4. **Quarterly model-fleet refresh of `configs/storyboard/supported_models.yaml`.** Fleet rotated 4 major releases Jan–May 2026 (Veo 3.1, Runway Gen-4.5, Kling 3.0, Veo 4) + Sora 2 consumer sunset April 26 2026 + Luma Ray 3 / Dream Machine 2.0 March 2026 + Pika 2.5 early 2026. If this rate holds, quarterly updates are the floor. Operations-team owner needed; cadence locked in. **Per-model native-clip-length table travels with the judge prompt as a compact envelope reference, not in rubric prose** — avoids framework-name-embedding violation while letting the judge reason about fallback usability.

5. **First-cohort overfit — SB lane fixtures are BUSINESS clients NOT YouTube creators.** Current and near-term fixtures: Klinika clinic owner (Polish aesthetic dermatology), DWF partner (Polish legal services), B2B SaaS founder. The creator-strategist reference set (MrBeast, Casey Neistat, Johnny Harris, Hank Green, Tom Scott, Cleo Abram) informs the judge's reasoning toolkit but is NOT the architectural target. SB-1 must cover "the client's published anchor" — written essays, LinkedIn posts, podcast transcripts, founder appearances — not "the creator's voice family" from a YouTube/TikTok-shaped catalog. **Re-validation trigger:** any fixture from an established-creator archetype (YouTube creator, TikTok personality, podcast host with dense pattern-data) should prompt a quick re-validation pass on SB-1's archetype examples + SB-5's cold-start framing (likely shifts to warm-start regime for that fixture).

6. **Per-story vs cross-item criteria — SB-5 mixes both; verify per-criterion isolation holds.** SB-1 / SB-2 / SB-3 / SB-4 / SB-6 are per-plan (scored on each of 5 plans, aggregated for digest). SB-5 is cross-plan (scored once on the 5-plan portfolio). The judge prompt wrapper must instruct the judge to score SB-1..SB-4 and SB-6 per-plan THEN read all 5 before scoring SB-5. Verify per-criterion isolation holds — SB-5's cross-plan reading should not leak into SB-1..SB-4 / SB-6 individual scores. If it does, redesign the prompt or split SB-5 into a separate judge call.

7. **Variance instrumentation deferred until Path 1 CI validation.** Per design guide §11.5, track judge variance per criterion per generation. Any criterion whose variance grows monotonically over 3 generations, or whose mean compresses toward the middle, is flagged for redesign — NOT calibration. **For SB specifically, instrument cold-start SB-1 variance separately from warm-start SB-1 variance** (per cold-start research §4 — the failure mode is silent; without separate channels, cold-start regression-to-mean drift gets masked by warm-start stability and we lose the signal). Defer until CI v3.3 validates via fixture validation pass — confirm the instrumentation pattern works on one lane before propagating to seven.

8. **Live-code restoration applied (2026-05-18, post-cross-check).** Three items from `autoresearch/archive/v006/workflows/session_eval_storyboard.py` (live code at `fc99d64`) were lost during v0→v1 synthesis and have been surgically restored without adding a 7th criterion:
   - **Live SB-5 (audio design / performable cold / designed silence)** folded into SB-1 score-1 as anchor (e) — "performable speech with designed silence" + "voice actor could perform it cold" + "what is deliberately absent, processed, or contrasted carries as much story as the visuals." Voice/creator-identity is the closest semantic match because audio direction is voice-craft; adding a 7th criterion would violate the documented ≤5-ceiling exception (SB-6 already claims that allowance). SB-6's pattern (CI-6 precedent) is reserved for AI-failure-surface, not for additional craft criteria.
   - **"Not how a screenplay reads" anti-pattern** restored as part of SB-5 WARM score-0 — pacing that moves the way a screenplay reads rather than how the creator's real videos move now explicitly scores 0. This was the live SB-7 anti-pattern phrasing; it had distinct affective load that v1's "Pacing forces the creator off their native cadence" alone didn't carry.
   - **"Specific way they surprise an audience"** restored into SB-1 score-1 as anchor (d). The cross-check flagged this as having affective load the v1 mechanical voice-marker checklist (named details / cadence / vocabulary / opening shape) didn't reproduce. Restored verbatim from live SB-1 prose.
   - **Intentionally NOT restored:** Live SB-4 ("turn recontextualizes the beginning") stays absorbed into v1 SB-3 as confirmed in the cross-check PRESERVED list — v1 SB-3 score-1 already says "the opening means something different by the end (turn / reframe / bookend)." No regression there.

9. **Brand-voice doc as POSTURE not FIDELITY anchor.** Cross-modal stylometry research finds lexical features (vocabulary richness, function-word distribution, sentence-length variance) transfer well from written to spoken with r=0.55–0.72 across 87 creators; pause/cadence/prosodic features transfer poorly at r=0.1–0.25. SB-1's CoT instructs the judge to score what transfers (lexical / vocabulary / named-detail / opening-shape) and explicitly NOT to score what doesn't (pacing, prosody, performance-in-delivery — those are post-production properties the script cannot encode). The 70–80% PAN-CLEF authorship-verification ceiling on short texts honestly bounds SB-1's reliable-verdict range — score-1 reserved for unambiguous matches; borderline routes to 0.5 generously rather than forced to 0 or 1.

10. **Fixture validation.** Run 5 existing SB fixtures (Klinika + DWF + B2B SaaS + 1–2 creator-archetype fixtures if available) through the locked criteria; eyeball judge rationales. If the rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating.

11. **Propagation to other 6 lanes (after CI + SB validate).** Sequence per project memory: GEO → MON → MA → SB → X → LI → site_engine. Each lane gets its own Path-A iteration + (optionally) lane-customized deep-research pattern — NOT a mechanical repeat. The 4 SB deep-research axes (voice fidelity / AI failure modes / cold-start / capability) were calibrated to the storyboard problem shape; X-engine and LinkedIn-engine likely share voice-fidelity + cold-start axes but have different AI-failure surfaces and no video-capability axis. Per-lane axis scoping needed.
