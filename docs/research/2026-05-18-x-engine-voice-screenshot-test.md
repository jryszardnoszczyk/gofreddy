---
date: 2026-05-18
type: deep-research deliverable — voice / screenshot-test axis
lane: x_engine
axis: voice / screenshot-test
parent: docs/handoffs/2026-05-18-judge-design-step1-x-engine.md
companions:
  - docs/research/2026-05-18-judges-domain-x-engine.md
  - docs/rubrics/judge-design-guide.md
status: complete v1
---

# X-Engine Voice & Screenshot-Test — Deep Research

## TL;DR

The screenshot test ("strip the avatar, would a reader familiar with the account still recognize this?") is the load-bearing voice criterion for x_engine — but only if it is operationalized as a reader-effect outcome question, not as a stylometric feature check. The 2021–2025 short-text authorship-verification literature (Zhu & Jurgens 2021 idiolect-in-online-registers; Theóphilo et al. 2020 microblog n-grams; Boenninghoff et al. 2019 similarity learning) demonstrates that idiolects ARE measurable in sub-280-char text via lexico-syntactic and discourse features — but the same features used as scoring targets in a generative loop collapse into surface mimicry: em-dash counts gameable, function-word distributions matchable, "specific names" plantable. The most recent direct evidence — Wang et al. EMNLP 2025 *Catch Me If You Can? Not Yet* (arxiv 2509.14543) — measured 40,000+ generations per model across 400+ authors and found that frontier LLMs partially imitate news/email style but fail on blog/forum (closer to X's register), AND that increasing few-shot demonstrations gives diminishing stylistic returns. This is good news for the failure-mode defense (model-collapsed "generic founder X voice" is genuinely detectable) and bad news for cold-start (with ≤5 prior posts, the lane cannot rely on imitation; it must rely on negative absence-of-AI-slop checks plus consistency-with-stated-register checks).

The X-vs-LinkedIn voice differential is real and load-bearing: X voice for the same founder is shorter, more contrarian, more in-the-moment, lower-status, more punchy; LinkedIn voice is authority-positioned, narrative, "lesson-extracting," higher-status. A judge that scores them with the same anchors will systematically reward LinkedIn-shape voice on X drafts. The fix: a separate X-voice criterion that anchors on X-specific behavioral markers (contrarian-not-conclusive; punchy-not-narrative; in-conversation-not-broadcast) rather than generic "voice match."

Data-rich (100+ prior posts) and cold-start (≤5 prior posts) require structurally different judge behavior. Data-rich: voice-match against an empirically-derived register description (NOT against raw exemplars — preference leakage). Cold-start: AI-slop-absence + register-consistency-with-account-stated-positioning + 0.5-unknown when neither is determinable. The current X-5 criterion in the draft spec conflates these two regimes and needs a regime-aware structure.

Three recommendations: (1) split the current X-5 into a register-consistency outcome question (data-rich anchor) plus a screenshot-survivability outcome question (cold-start-safe anchor); (2) replace any "absence of em-dashes / 'moreover' / tricolons" tells with a single gestalt outcome anchor ("would a reader recognize this as machine-finished prose?") because feature-level slop signatures will be evaded by Generation N+5 and the gestalt anchor is the only Goodhart-resistant version of the same idea; (3) instrument voice variance across generations as the §11.5 early-warning signal, with specific attention to convergence toward 18–24-word sentence-length cadence (the 2026 burstiness collapse signature).

---

## Key questions addressed

1. **The screenshot test:** what does the judge actually measure when it asks "would a reader believe this is from the founder?" without overfitting to a single voice sample?
2. **Voice signatures for founder accounts:** which dimensions matter at sub-280-character scale?
3. **X voice vs LinkedIn voice** for the same founder: where do they diverge, and how does the judge encode the difference without leaking LinkedIn anchors into X scoring?
4. **The "generic founder X voice" failure mode:** how does an outcome-shaped judge defend against AI generating prose that screenshots as belonging to no specific person?
5. **Data-rich (100+ prior posts) vs cold-start (≤5):** different regimes, different judge behavior.
6. **Stylometry literature for short-form social content:** what's separable in 280 chars, what isn't, and what's safe to encode in rubric prose vs what isn't.

---

## Synthesis

### 1. What the screenshot test actually measures (and why the obvious version Goodharts)

The screenshot test in its naive form — "if you removed the avatar, could a reader still recognize this as the author?" — is the right intuition wrapped around the wrong implementation. The intuition tracks Hamel Husain's domain-expert test: a creator in the niche should be able to attribute the post correctly. The wrong implementation is the one that asks the judge to do attribution itself.

Attribution-style scoring fails three ways under selection pressure:

**Failure mode 1: stylistic-feature plant.** If the judge rewards "matches the account's voice," and the workflow has access to prior posts (which it does, via `source_data`), the workflow learns to plant high-discriminating-power n-grams, signature phrases, and punctuation patterns from the prior corpus. This produces posts that are *stylometrically* identical to the account but *semantically* unmoored — the founder voice over an empty content well. This is the exact Goodhart pattern documented in arxiv 2602.13576 (Rubrics-as-Attack-Surface, 27.9pp drift on feature-shaped criteria) translated to the voice axis.

**Failure mode 2: model-family preference leakage.** If the judge panel includes a Claude-family model and the workflow's inner-loop is also Claude-family, the judge will systematically rate Claude-family-shaped voice higher (Li et al. arxiv 2502.01534, 6–22% preference leakage per related-pair). On the voice axis specifically, this is dangerous: Claude's prose pattern includes high-frequency em-dashes, balanced tricolons, and "moreover/furthermore" connectives that themselves are the AI-slop signature stack the rubric is supposed to penalize. A Claude judge will systematically under-penalize Claude-shaped voice. The §8 mitigation (three frontier families, no same-family panels) is necessary but not sufficient on this axis — even Gemini and GPT have their own slop signatures that their judges under-penalize. The structural fix is to never ask the judge to match patterns; only to ask the judge whether the artifact achieves a reader-effect outcome.

**Failure mode 3: cold-start void.** If the account has 5 prior posts and the judge is asked to verify "matches the account's voice," there is no empirically-derived voice to match. The judge fabricates a voice signature from the limited corpus, scores the draft against the fabrication, and the workflow optimizes against the fabrication. Within 3–5 generations, the account has a strongly-defined "voice" that nobody — including the founder — recognizes. This is the same pathology that produced the `linkedin_engine v040 cold-start mutation` (memory: 2026-05-08).

The structural fix across all three failure modes: **the judge does NOT do attribution.** The judge does outcome-style reasoning: "would a reader, knowing what this account claims to be about, find this post consistent with that positioning?" and "would the prose itself be recognizable as machine-finished?" Both questions are reader-effect outcomes that can't be planted via feature mimicry.

### 2. Voice signatures for founder accounts at 280-char scale

The short-text stylometry literature is unambiguous on this point: idiolect IS measurable in sub-280-char windows, but the signal is distributed across multiple linguistic levels rather than concentrated in any single feature.

Zhu & Jurgens (EMNLP 2021, arxiv 2109.03158, *Idiosyncratic but not Arbitrary*) — the canonical reference — demonstrates that "idiolectal variations permeate all linguistic levels, present in both surface lexico-syntactic features and high-level discourse organization." Their neural model achieves strong authorship-identification performance on short texts via a representation that captures:

- Lexical: vocabulary register, function-word frequencies, character n-grams
- Syntactic: sentence-length distribution, punctuation patterns
- Discourse: how the author transitions between claims within a constrained window
- Idiosyncratic: distinctive phrasings that recur

The Boenninghoff et al. 2019 work on similarity learning for authorship verification (arxiv 1908.07844) and Theóphilo et al. 2020 forensic microblog analysis (arxiv 2003.11545) replicate the finding with classical features: even with 100-280 chars of source text, n-grams + stylometric features support binary authorship verification with reasonable accuracy.

**What this means for the judge: the voice signature is real and distinctive at our scale.** It does NOT mean the judge should be feature-coded to detect it. The Zhu-Jurgens model that does the verification is a learned neural representation, not an enumerable feature list. The literature explicitly warns against "feature engineering" approaches for short text precisely because the signal is in the joint distribution, not in any single marker.

Practical implication: the judge's reasoning toolkit (private, not in rubric prose) should be that idiolect is real and distributed. The judge's rubric criteria should NOT enumerate "uses em-dashes" or "short opening sentences" or "first-person pronouns" as features. The judge should answer the gestalt question: "given what I've seen of this author's prior posts, does this draft sound like one of theirs, or does it sound like a generic post in the niche?"

Founder-account voice signatures observed across the named exemplars (Naval, Sahil Bloom, George Mack, Paul Graham, Marc Andreessen, Visa Veerasamy, Justin Welsh) cluster on four reader-perceptible dimensions:

- **Vocabulary register** — the lexicon a founder uses repeatedly. Naval: "leverage," "specific knowledge," "judgment," "wealth not money or status." Paul Graham: "essay," "founder," "ideas," "schlep." Mack: "agency," "leverage," "high-leverage." This is the most visible signature but the most plantable; rubric prose must not anchor on lexicon.
- **Sentence-length distribution and burstiness** — Naval's mode is 6-word declarative; Graham's mode is 15–25-word essayistic with periodic 5-word punctuation; Bloom's mode is symmetric one-liner; Mack's mode is short opening + medium expansion. Critically: the 2026 AI-detection literature has converged on cadence-uniformity as the *single biggest* AI tell — frontier-LLM-generated prose settles into 18–24-word sentences across the entire post, paragraph after paragraph. Burstiness measurement (sentence-length variance) is the most robust short-text AI signal. Humans show high variance; LLMs show low variance.
- **Signature phrases and recurring rhetorical moves** — "Seek wealth, not X" (Naval, declarative reframing); "Here's the thing nobody tells you about X" (Hormozi, audience-positioning); "Most people think X. Actually Y." (Mack, counter-stereotype); "X-but-not-Y" definitional moves (Graham). These are partially plantable but increasingly so as the corpus grows.
- **Joke-to-seriousness ratio and opinion strength** — distinct per founder. Bloom is almost-never-joking; Mack alternates serious frames with one-line zingers; Graham deadpans; Andreessen weaponizes irony. Posture is the hardest dimension to fake because it requires the model to commit to a stance, not just match a pattern.

The judge's job is to imagine the reader of the account encountering the post and asking "does this sound like them?" — without checking off the dimensions one by one. Rubric criteria targeting "is the lexicon consistent" or "are sentence lengths varied" are feature checks and will Goodhart. Rubric criteria targeting "would a regular reader of this account recognize this?" are outcome questions and survive.

### 3. X voice vs LinkedIn voice for the same founder — the differential is real and load-bearing

The same founder writes systematically differently on X than on LinkedIn. The platform-difference literature for 2026 is unambiguous on this, and the difference must be encoded in the x_engine judge separately from any voice-match logic shared with linkedin_engine.

**X voice for a founder is characterized by:**

- **Shorter units.** Even when the founder ports the same idea to LinkedIn, the X version is denser and contains less connective tissue. A 200-char X post becomes a 1200-char LinkedIn post with explanatory scaffolding.
- **More contrarian, less conclusive.** X posts assert positions and invite disagreement; LinkedIn posts conclude with a takeaway or lesson. Mack's high-agency posts on X invite testing; the LinkedIn versions wrap with "the lesson is X." Graham's X posts are throwaway speculations; his essays are conclusions.
- **In-the-moment, lower-status.** X posts read as in-conversation with the wider X discourse, often with implicit replies to ambient claims. LinkedIn posts read as broadcast, status-positioning, "here's what I learned and you should too." The X register is peer-to-peer; LinkedIn is mentor-to-mentee.
- **More punchy, less narrative.** X posts pop one claim; LinkedIn posts build through a narrative arc. The 1-3-1 rhythm Cole/Bush prescribe operates per-tweet on X but per-paragraph on LinkedIn.
- **More personality-forward, less authority-positioned.** Andreessen on X is sarcastic and prolific; Andreessen on LinkedIn is authoritative and curated. Same person, different register.

The implication for the judge: **a voice-match criterion that doesn't differentiate the register will systematically reward LinkedIn-shape voice on X drafts.** This is because the LinkedIn shape is what model-defaulted "professional writing" looks like — the smooth, narrative, conclusion-bearing prose Claude/GPT/Gemini all converge to. Without explicit anti-anchoring, the X judge will treat LinkedIn-shape as "voice consistent with founder authority positioning" and miss the X-native pathology.

The fix in the rubric: the voice criterion's score-1 anchor must include a behavioral check on X-native register markers (contrarian-not-conclusive, peer-not-broadcast, punchy-not-narrative) rather than a generic "matches account voice" check. The judge's structured CoT step 2 should explicitly map the draft against "would this read as in-the-X-conversation, or as imported from a different platform's register?"

This is a regime-specific outcome question, not a feature check. It survives Goodhart because the workflow can't easily plant "peer-not-broadcast" — that's a posture that has to be committed to at the claim level, not the surface level.

### 4. Defending against "generic founder X voice"

The dominant failure mode at this point in the LLM cycle is what one might call generic-founder-voice collapse: prose that hits all the surface markers of founder-on-X (short sentences, contrarian framing, named entity, specific number, ends with a question) but reads as belonging to no specific person. It screenshots as "founder content" — which is the failure.

Wang et al.'s EMNLP 2025 finding (arxiv 2509.14543) gives us the structural reason this is happening: LLMs default to an "average, generic tone" when imitating, AND increasing few-shot demonstrations beyond ~10 gives little additional alignment. In other words, the model has a strong attractor toward generic professional-voice prose, and showing it more exemplars doesn't break the attractor. The model collapses toward the centroid of "founder X voice" rather than toward the specific founder.

The judge's defense against this is the gestalt screenshot test framed as a reader-effect outcome: **"if a regular reader of this account read this post in their feed without seeing the handle, would they recognize it as one of the account's posts — or would it read as a generic post in the niche?"** This is the question that, when reasoned through honestly, catches the centroid-collapse pathology. The reader-of-the-account is the key qualifier: not the abstract X user, not the niche-aware practitioner, but specifically someone who knows the account.

The judge implements this question via three CoT steps:

- Step 1: Read the prior posts in `source_data` and form a one-sentence private description of the account's recognizable register (cadence, lexical mode, posture).
- Step 2: Read the draft and test whether a regular reader, encountering it in feed, would attribute it to this account vs. attribute it to "some founder."
- Step 3: Commit to verdict + one-sentence justification.

Critically, step 1 is private reasoning, not anchor enumeration. The judge forms an internal register description and tests against it; it does NOT generate a feature list and check the draft against the list. The latter is the Goodhart trap. (This distinction maps onto the Wang-et-al. result: feature-list imitation is what the LLMs fail at; gestalt is what they're actually doing when they fail.)

Anti-pattern: encoding the slop signatures (em-dashes, "moreover," tricolons) as exclusion features in the rubric. The 2026 em-dash discourse has converged on this being misleading — em-dashes are a weak signal that gets gamed away within one or two generations of selection pressure, and they produce significant false-positive collateral against humans who genuinely use em-dashes (Emily Dickinson the canonical case). The robust signal is cadence collapse — the 18–24-word sentence-length plateau. But even cadence collapse cannot be safely encoded as a rubric feature because the workflow will inject artificial cadence breaks; the only safe encoding is the gestalt outcome question.

The current X-5 criterion's score-0 anchor explicitly enumerates slop signatures ("excessive em-dashes, 'moreover/in conclusion,' smooth-but-gradeless prose, symmetrical bullet rhythm"). This is the pattern the guide warns against in §12 anti-patterns #1 and #2. Recommend rewriting the score-0 anchor to focus on the gestalt outcome — "reads as machine-finished, recognizable to readers familiar with the account as not-from-them or recognizable to AI-aware readers as not-from-a-specific-person" — and routing the surface-marker check to `slop_gate` (which already has slop-pattern detection for cross-platform use).

### 5. Data-rich vs cold-start regimes

A 100-prior-posts account and a 5-prior-posts account are different regimes for the voice judge. Pretending they're not — as the current X-5 spec does, with a single score-0.5 way-out for cold-start — produces systematic miscalibration.

**Data-rich regime (≥30 prior posts):** the judge has enough corpus to form a reliable register description. The screenshot-test outcome question is fully evaluable. Score 1 / 0 / 0.5-unknown all in play.

**Mid-data regime (10–30 prior posts):** register is partially formable. The judge can detect strong inconsistencies (sober technical account posting Hormozi heat) but cannot reliably detect subtle drift. The cleaner protocol here is to score the gross-inconsistency check at full confidence and the subtle-fit check at 0.5-unknown.

**Cold-start regime (≤10 prior posts):** the judge cannot empirically derive register. The screenshot test in its standard form is unevaluable. Two structurally different things become the available signals:

- **Negative absence-of-AI-slop check.** Independent of the account, is this prose recognizable as machine-finished to an AI-aware reader? Cadence collapse, generic motivational frame, smooth-but-gradeless prose — these are detectable in absolute terms, without an account-voice reference. This survives in the cold-start regime.
- **Register-consistency with stated positioning.** The account profile (`source_data` typically includes bio, niche, stated topic focus) declares what the account is supposed to be about. The judge can score whether the draft is consistent with the stated positioning — sober technical positioning → does the draft read sober and technical? Contrarian-startup-founder positioning → does the draft commit to a contrarian stance? This is a weaker check than full screenshot-test but is the strongest available signal at cold-start.

The linkedin_engine v040 cold-start mutation (memory note, 2026-05-08) implies the team has hit this regime-difference issue before. The structural fix for x_engine is to make the cold-start regime explicit in the criterion:

- Score 1 in cold-start: prose is not recognizable as machine-finished AND draft is consistent with the account's stated positioning.
- Score 0 in cold-start: prose is recognizable as machine-finished OR draft contradicts the account's stated positioning.
- Score 0.5 in cold-start: only when stated positioning is itself absent from source_data and prose is borderline.

This is operationalizable without expanding the criterion count past the §5 ceiling — it's a single criterion with an explicit cold-start sub-clause.

### 6. Voice variance instrumentation — the early warning

Per §11.5 of the judge-design-guide, voice criterion variance per generation is the load-bearing Goodhart-time-constant signal. Three specific patterns to watch on the voice axis:

- **Sentence-length-distribution convergence.** If across generations the voice-criterion score rises while the underlying drafts show declining sentence-length variance (i.e., converging toward the 18–24-word AI-cadence plateau), the rubric is being optimized for surface compliance with a Goodharted voice signal. Flag for redesign — NOT calibration.
- **Lexical-bigram-recurrence growth.** If the corpus of drafts across generations exhibits increasing recurrence of specific bigrams from the prior-posts corpus (the workflow planting plates), the voice criterion is rewarding stylistic mimicry rather than reader-effect outcome. Flag.
- **Asymmetric panel drift.** Per the §16 known-uncertainty on reference-free durability: if the Claude judge's mean voice score rises faster than the Gemini judge's mean while the inner-loop is Claude-family, that's the preference-leakage signal on the voice axis specifically. Track the asymmetry; if it grows monotonically over 3 generations, the panel is leaking and the rubric prose needs to push harder on outcome-shape away from family-pattern-shape.

The current design has none of this instrumentation called out at the per-axis level. Recommend adding the three signals above to the variance dashboard as voice-specific early warnings.

---

## Recommendations for the X-5 criterion

### R1. Split the current X-5 into two criteria — register-consistency and slop-absence

X-5 as currently drafted conflates two distinct outcome questions:

1. "Does this match the account's voice?" (data-rich and mid-data regimes)
2. "Would the prose read as machine-finished to an AI-aware reader?" (cold-start-safe; also data-rich)

These are different questions with different failure modes. Question 1 is regime-dependent and Goodhart-prone via lexical mimicry. Question 2 is regime-independent and harder to Goodhart because it's testing for the absence of a known LLM attractor rather than the presence of a learned signature.

**Proposed:** keep one voice criterion (X-5 in the current numbering), and rewrite its score-1 and score-0 anchors to test the gestalt outcome at both regime levels. Score 0.5 routes cold-start unknown cases to a defined sub-anchor rather than collapsing them into a generic way-out.

If keeping a single criterion proves to compress the two signals too much during empirical validation (i.e., the criterion's variance grows because the judge struggles to weight them consistently), promote the §5 documented-exception path and add a sixth criterion targeting the slop-absence outcome specifically. The literature justification is in place: Wang et al. EMNLP 2025 documents the LLM-specific "generic centroid voice" failure surface at measured effect sizes, which is the §5 v2.1 justified-breach precondition.

### R2. Remove all surface-marker enumeration from the X-5 anchors

The current X-5 score-0 anchor enumerates "excessive em-dashes, 'moreover/in conclusion,' smooth-but-gradeless prose, symmetrical bullet rhythm." Remove these. They are:

- Goodhart-prone: workflow learns to replace em-dashes with parentheticals (same model-collapse pattern, different surface)
- False-positive-prone against legitimate humans (Emily Dickinson, Naval — em-dash users)
- Fragile to LLM evolution: the surface signatures of GPT-5.5 and Claude 4.7 in mid-2026 will not be the same as those of GPT-6 and Claude 5 in late 2026

Replace with a single gestalt outcome anchor: "the prose reads as machine-finished to an AI-aware reader — generic-niche-attractor cadence and rhythm, no specific person's idiolect surface." The structured CoT step 2 forces the judge to reason about the gestalt rather than tally features.

Surface-marker checks belong in `slop_gate` (deterministic, versionable, audit-trail-friendly), not in the judge.

### R3. Add an explicit cold-start sub-anchor to X-5

Make the regime structure explicit. The score-1 anchor reads at two levels:

- Data-rich (≥30 prior posts in source_data): draft is consistent with the account's empirical register AND prose is not recognizable as machine-finished.
- Cold-start (<30 prior posts): prose is not recognizable as machine-finished AND draft is consistent with the account's stated positioning in source_data (bio, declared niche, stated topic focus).

The score-0 anchor mirrors. The score-0.5 anchor reserves only for cases where neither register nor positioning is determinable from source_data AND prose is borderline.

This is the single largest robustness gain available on this axis. It directly addresses the Wang et al. finding that few-shot mimicry plateaus quickly — the cold-start branch of the criterion stops asking the judge to do something the literature says it can't do reliably.

### R4. Add X-vs-LinkedIn register check to the CoT structure

The structured CoT for X-5 currently reads:

- Step 1: Identify the account's voice from prior posts (cadence, vocabulary, register).
- Step 2: Test the post for voice consistency + absence of AI-slop signature stack.
- Step 3: Emit verdict + one-sentence justification.

Add a step 2.5 (or fold into step 2): "Test whether the draft reads as in-the-X-conversation (peer-to-peer, in-the-moment, punchy) versus as imported from a different register (broadcast, conclusive, narrative)." This explicitly forces the judge to discriminate X-native from LinkedIn-shape, which is the most-common cross-platform voice failure observed in repurposed founder content.

### R5. Instrument three voice-specific variance signals per §11.5

Add to the per-generation variance dashboard:

- Sentence-length-variance (burstiness) across the lane's drafts. Monotone decline → cadence collapse → redesign trigger.
- Lexical-bigram-recurrence between drafts and prior-posts corpus. Monotone growth → plate planting → redesign trigger.
- Claude-vs-Gemini mean-voice-score divergence. Monotone growth with Claude-family inner-loop → preference leakage on voice axis → push outcome-shape harder in rubric prose.

Each signal is cheap to compute (existing per-generation telemetry plus three new aggregations). Each gives a different early warning. Together they cover the three documented Goodhart pathways on the voice axis.

---

## Open questions

1. **What's the right `source_data` snapshot freshness?** A founder's voice on X evolves — the version of Naval who posted in 2015 sounds different from the version posting in 2026. If `source_data` captures all-time posts, the judge will compare against an averaged register that may not match the current voice. Recommend capturing a sliding 90-day window for the register-consistency check and the full corpus only as a secondary anchor.

2. **Quote-tweets and replies — different voice regime?** A founder's quote-tweets and replies often diverge from their primary-post voice (more casual, more reactive, less curated). Should the judge treat draft posts and draft replies as the same voice criterion, or separate? Lean toward same — the gestalt outcome question handles both — but worth confirming on empirical validation.

3. **The 30-prior-posts threshold for cold-start vs data-rich is a hypothesis, not a measurement.** The Zhu-Jurgens model achieves "strong" authorship identification with corpus sizes in the hundreds; 30 is the operating heuristic from analogous practice but is not directly derived. Recommend tuning the threshold empirically after first 5–10 generations of x_engine telemetry.

4. **Voice consistency across the panel's three frontier families.** The three model families have their own voice attractors. Claude's smooth-em-dash-rich prose; GPT's bulleted-list-shape; Gemini's structured-conclusory-shape. Each judge's gestalt outcome check will under-penalize its own family's attractor. The cross-family panel mitigates but doesn't eliminate. The asymmetric-panel-drift signal (R5) is the available diagnostic. Whether it's sufficient depends on how aggressively the inner-loop family is constrained to differ from the panel composition — currently the project's policy is to fix the panel at Anthropic + OpenAI + Google and allow the inner-loop to mutate freely, which means any inner-loop family will partly overlap one panel member. Worth tracking explicitly.

5. **Founder-account-with-ghost-writer regime.** If the founder uses a human ghost-writer (per Fortune May-2026, this is common at the executive-tech level), the prior-posts corpus reflects the ghost-writer's voice, not the founder's. The judge's voice criterion treats the ghost-writer as the truth; this is correct for screenshot-survivability (a reader will recognize the consistent voice regardless of provenance) but creates risk if the workflow's job is specifically to "sound like the founder personally." Out-of-scope for the v1 judge but flagging.

6. **Calibration set size for voice specifically.** The judge-design-guide §15 prescribes 100 fixtures per lane. Voice is one of 5 criteria for x_engine, so ~20 fixtures will exercise it per calibration run. Recommend ensuring those 20 are stratified across cold-start, mid-data, and data-rich accounts (not just topical niches) so the regime branches of the criterion are independently calibratable.

---

## Citations

**Stylometry and authorship in short / microblog text:**

- Zhu, J. and Jurgens, D. (2021). *Idiosyncratic but not Arbitrary: Learning Idiolects in Online Registers Reveals Distinctive yet Consistent Individual Styles.* EMNLP 2021. arxiv 2109.03158. https://arxiv.org/abs/2109.03158
- Theóphilo, A., Pereira, L. A. M. and Rocha, A. (2020). *Forensic Authorship Analysis of Microblogging Texts Using N-Grams and Stylometric Features.* arxiv 2003.11545. https://arxiv.org/pdf/2003.11545
- Boenninghoff, B. T. et al. (2019). *Similarity Learning for Authorship Verification in Social Media.* arxiv 1908.07844. https://arxiv.org/pdf/1908.07844
- Theóphilo, A. et al. (2020). *Writer Identification Using Microblogging Texts for Social Media Forensics.* arxiv 2008.01533. https://arxiv.org/pdf/2008.01533
- Kumar, T. et al. (2023). *Stylometric Detection of AI-Generated Text in Twitter Timelines.* arxiv 2303.03697. https://arxiv.org/abs/2303.03697

**LLM style mimicry — direct evidence:**

- Wang, J. et al. (2025). *Catch Me If You Can? Not Yet: LLMs Still Struggle to Imitate the Implicit Writing Styles of Everyday Authors.* EMNLP 2025 Findings. arxiv 2509.14543. https://arxiv.org/abs/2509.14543
- Hung, T. et al. (2026). *Decoding AI Authorship: Can LLMs Truly Mimic Human Style Across Literature and Politics?* arxiv 2603.23219. https://arxiv.org/pdf/2603.23219
- Przystalski, K. et al. (2025). *Stylometry recognizes human and LLM-generated texts in short samples.* arxiv 2507.00838. https://arxiv.org/pdf/2507.00838

**Judge design / rubric methodology (canonical references — kept short, not duplicating the design guide bibliography):**

- Li, Y. et al. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-Judge.* ICLR 2026. arxiv 2502.01534
- Anonymous (2026). *Rubrics as an Attack Surface for LLM Judges.* arxiv 2602.13576
- Anonymous (2026). *AutoRubric: Unifying Rubric-based LLM Evaluation.* arxiv 2603.00077

**X-platform-specific (2026 algorithm and creator-economy literature):**

- xai-org. (2026). *x-algorithm.* GitHub open-source release, Jan 2026. https://github.com/xai-org/x-algorithm
- *X (Twitter) Algorithm 2026: How It Works.* Teract.ai. https://www.teract.ai/resources/twitter-algorithm-2026
- *How to Grow on Twitter/X in 2026: The 70/30 Reply Strategy.* Teract. https://www.teract.ai/resources/grow-twitter-following-2026
- *LinkedIn vs Twitter (X) for Founders in 2026.* Monolit. https://monolit.sh/blog/linkedin-vs-twitter-x-for-founders-2026-pros-cons-which-platform-grows-your-business
- *Should You Use LinkedIn Or Twitter (X) for B2B in 2026?* DemandBird. https://demandbird.com/resources/linkedin-vs-twitter/

**AI-slop / detection / em-dash discourse:**

- *AI slop.* Wikipedia (2025 Word of the Year). https://en.wikipedia.org/wiki/AI_slop
- *The Em-Dash Myth: What Actually Gives Away AI Writing.* Duey.ai. https://www.duey.ai/post/em-dash-ai-writing
- *AI and the Em Dash.* MDPI Blog, Oct 2025. https://blog.mdpi.com/2025/10/09/ai-and-the-em-dash/
- *Are AI Detectors Accurate? 2026 Data on 7 Major Detectors.* TheHumanizeAI Pro. https://thehumanizeai.pro/articles/are-ai-detectors-accurate-2026
- *LLM Default Voice: Why AI Writing Sounds the Same in 2026.* Junia.ai. https://www.junia.ai/blog/llm-default-voice-ai-writing
- *After AI stole his clients, one Big Tech ghostwriter is using AI to get them back.* Fortune, May 2026. https://fortune.com/2026/05/18/ai-ghostwriting-clients-llms-claude/

**Project documents:**

- `docs/rubrics/judge-design-guide.md` (canonical design reference)
- `docs/handoffs/2026-05-18-judge-design-step1-x-engine.md` (current X-engine optimal-output spec)
- `docs/research/2026-05-18-judges-domain-x-engine.md` (companion domain research — Welsh / Cole-Bush / Naval / Mack / Bloom playbooks)
- Project memory: `linkedin_engine v040 cold-start mutation 2026-05-08` (prior precedent for regime-specific judge behavior)
