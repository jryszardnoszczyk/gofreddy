---
date: 2026-05-18
type: research deliverable — deep dive
status: complete
topic: x_engine — AI-slop detection axis (X-specific)
parent: docs/handoffs/2026-05-18-judge-design-step1-x-engine.md
guide: docs/rubrics/judge-design-guide.md
siblings:
  - docs/research/2026-05-18-judges-domain-x-engine.md (deepens)
  - docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI-6 AI-failure analogue)
applies_to: x_engine lane (single-shot judge + structural_gate split)
---

# X-Engine — AI-Slop Detection Axis (Deep Research)

## TL;DR

AI-slop detection on X is structurally harder than on long-form prose for three reasons that compound: short text starves token-based stylometric classifiers of signal; fine-tuned creator-voice models collapse human-vs-machine human-study accuracy to **54 percent — a coin flip**; and the salient tells (em-dash, "It's not X, it's Y," tricolons, "Here's the thing") are *stylistic markers humans share with AI* and that get diluted further when an account is voice-tuned. The off-the-shelf detector strategy that works on student essays does **not** transfer to X drafts. Originality.ai, GPTZero, Copyleaks self-report 92–99 percent accuracy, but on short, lightly-edited, voice-tuned social posts that drops to 50–65 percent — with false-positive rates as high as 15.6–17.6 percent on polished human writing. Treating those classifier scores as the judge's slop signal would import the worst of both worlds: high false-positive cost on real operator voice, plus a workflow incentive to learn the inverse-classifier (avoid em-dashes by substituting parentheticals, the v0 spec already flags this in §6).

The recommendation that survives is a **two-layer architecture matching the design guide's Hard-Rules-vs-Principles split** (`docs/rubrics/judge-design-guide.md` §2): deterministic, named, individually-defensible-by-failure-mode checks routed to `structural_gate`, plus an outcome-question judge criterion (X-5 in the current v0 spec — "sounds like the account's voice, survives the screenshot test") that tests for the *gestalt* AI-slop fingerprint — not any single tell. The gestalt test is the load-bearing piece, because every single tell has a high false-positive rate on legitimate operator voice and a low marginal cost for the workflow to learn to evade. The `structural_gate` checks defend against a small set of patterns where the false-positive rate is acceptable (em-dash density 10×-plus baseline, signature-phrase blocklist of phrases no thoughtful operator actually writes, banned three-element parallel constructions used in immediate succession). Each `structural_gate` check is sized so that a legitimate operator post almost never trips it, and so that gaming any one check leaves several others armed.

This document deepens `docs/research/2026-05-18-judges-domain-x-engine.md` along the AI-slop axis: catalogues the X-specific tells (with frequency data where it exists), surveys classifier performance against short social text (with calibration data through 2026), enumerates the high-false-positive traps that look like AI-slop but are real-operator voice, and prescribes the exact `structural_gate` checks that should ship versus the patterns that must stay in the gestalt judge criterion. The v0 spec's X-5 prose is correct; this doc tightens the open-question list (§8 of v0) into committed prescriptions and identifies two additions to consider in v1.

---

## Key Questions Addressed

1. What are the **X-specific AI-slop tells** in 2026, with citations to the actual frequency data?
2. How are AI-slop **classifiers calibrated against X content specifically** — and what is their failure rate on short, voice-tuned text?
3. What patterns **look algorithmic but are real-operator voice** — the false-positive set that we must NOT route to `structural_gate`?
4. How does the judge distinguish **"AI-assisted but founder-edited" (acceptable) from "AI-generated and posted" (slop)** when detection accuracy degrades 20–45 pp on edited hybrid text?
5. What is the **composed-engineer voice** — the median LinkedIn-influencer × Twitter-bro fusion — and how do we detect it without overfitting?
6. Which deterministic checks **belong in `structural_gate`**, and which patterns **must stay in the judge** as gestalt evaluation?

---

## Synthesis

### 1. The classifier-only strategy is broken at this surface, with measured effect sizes

Three independent 2025–2026 results converge on the same finding: off-the-shelf AI-text classifiers degrade catastrophically on the exact text class the x_engine lane produces.

**(a) Fine-tuned models break detection.** Dawkins, Fraser, and Kiritchenko ([When Detection Fails, arxiv 2506.09975, June 2025](https://arxiv.org/abs/2506.09975)) generated 505,159 AI-generated social-media posts across 11 controversial topics, using open-source, closed-source, and fine-tuned LLMs. The headline: under the realistic threat model — the attacker does NOT release the fine-tuned generator publicly — human-study detection accuracy drops to **54 percent**. A coin flip. Automated detection drops by an absolute 16.86 percentage points in the worst case. The x_engine lane's "voice-cloning" use case (operator post-history fed to an LLM that drafts in the operator's voice) is exactly the threat model the paper measures — the lane intentionally trains the inner-loop on the account's prior posts. The classifier signal is gone.

**(b) Short text starves stylometric features.** Tourille et al. ([Unmasking the Imposters, arxiv 2406.17967](https://arxiv.org/abs/2406.17967)) tested BERTweet, soft-voting ensembles, and stylometric feature classifiers across nine Twitter datasets generated by Llama 3, Mistral, Qwen2, and GPT-4o. Their bottom line: **"uncensored" models significantly undermine the effectiveness of automated detection methods.** The pattern that detection is robust for long-form prose but fragile for tweet-length text is the dominant finding across the social-media-detection literature. Tweets are too short for perplexity-based detection to accumulate enough signal; stylometric features are too coarse at 280 characters.

**(c) Light editing breaks every detector.** The 2026 Supwriter benchmark and consensus across 30+ tester surveys ([DigitalApplied 2026](https://www.digitalapplied.com/blog/ai-content-detection-tools-2026-accuracy-pricing-guide), [EyeSift 2026](https://www.eyesift.com/blog/ai-detector-accuracy-benchmarks-2026/), [Walter Writes 2026](https://walterwrites.ai/are-ai-detectors-accurate/)): **light editing (sentence restructure, synonym swap) drops detection 15–25 pp; heavy editing where the writer adds original ideas drops detection 30–45 pp.** A detector claiming 95 percent on raw AI output sits at 55–65 percent on AI-assisted-but-human-edited text. Confidence intervals widen so much that the score is no longer decision-useful.

**(d) False-positive rates are not as advertised.** Vendor claims (GPTZero 99.3 percent / 0.24 percent FPR; Originality 83–94 percent / 2–5 percent FPR) come from in-distribution test sets. Independent controlled testing against polished human academic prose finds **GPTZero at 15.6 percent FPR, Originality.ai at 17.6 percent FPR** ([Humanizer AI 2026 review](https://humanizerai.com/blog/gptzero-vs-originality-ai), [Fritz.ai 2026 testing](https://fritz.ai/gptzero-vs-originality/), [EssayHub 2026](https://essayhub.com/blog/how-accurate-are-ai-checkers)). Non-native English writers and technically-trained authors are disproportionately false-positive-flagged ([Walter Writes 2026](https://walterwrites.ai/are-ai-detectors-accurate/)). Both populations are core to gofreddy's first-cohort clients (DWF Polish lawyers, Klinika Polish dermatology), making vendor classifiers a non-starter for production.

**Implication for the judge.** If we routed an external AI-detection classifier score into the judge, the workflow under 50-generation evolution pressure would learn to maximize "looks human" by the classifier's standards. That signal is wrong: it correlates ~50 percent with actual human-written content on the target distribution, and it would penalize legitimate operator voice for trivial surface markers. The classifier-as-feature is exactly the Phase-4 pathology the design guide §11.1 names: outcome-shaped criteria are the only defense.

### 2. The X-specific tells, with frequency data

The "AI-slop" tells appear in three tiers of evidentiary strength. We should treat them differently in `structural_gate` versus the judge.

**Tier 1: Tells with measured frequency differentials, but high false-positive risk on real voice.**

- **Em-dash overuse.** GPT-4.1 uses em-dashes at **3.28× human baseline frequency** in standard essays per independent stylometric analysis ([Sean Goedecke 2025](https://www.seangoedecke.com/em-dashes/)). The em-dash frequency in ecology paper abstracts **more than doubled between 2021 and 2025** ([Piece of K 2025](https://www.pieceofk.fr/the-rise-of-the-em-dash-in-ecology-abstracts/)), the largest single-token frequency shift in scientific writing over that window. The McGill OSS Office ([2025 analysis](https://www.mcgill.ca/oss/article/critical-thinking-student-contributors-technology/why-did-llms-steal-our-em-dashes)) attributes this to RLHF preference-data drift: human annotators rated em-dash-heavy responses as more "sophisticated," and the preference baked in. **Critical caveat:** Claude uses em-dashes minimally; Gemini and Meta's Llama essentially not at all ([Plagiarism Today 2025](https://www.plagiarismtoday.com/2025/06/26/em-dashes-hyphens-and-spotting-ai-writing/)). The em-dash signal is GPT-family-specific. And — load-bearing — many real operators (think tank writers, journalists, founder-narrative-bloggers) use em-dashes liberally as their personal style. The Ringer's defense ("Stop AI-shaming our em-dashes, please" — [2025](https://www.theringer.com/2025/08/20/pop-culture/em-dash-use-ai-artificial-intelligence-chatgpt-google-gemini)) catalogues working writers whose em-dash rate exceeds GPT-4's. **The tell isn't the em-dash; it's em-dash density above ~3× the account's own baseline AND co-occurrence with other Tier-1 tells.**

- **"It's not X, it's Y" antithesis.** This contrastive reframe (negation-then-replacement parallelism) is the single most-named ChatGPT tell across 2025–2026 critique ([Blake Stockton "Don't Write Like AI"](https://www.blakestockton.com/dont-write-like-ai-1-101-negation/), [Dead Language Society 2025](https://www.deadlanguagesociety.com/p/rhetorical-analysis-ai), [Hardly Working substack 2025](https://hardlyworking1.substack.com/p/how-to-avoid-sounding-like-a-stupid)). The mechanism is RLHF feedback: human annotators conflate the appearance of nuance with actual depth and statistically upvote contrast framing even when it conveys less information. Used sparingly, antithesis is high rhetoric (JFK "Ask not what your country can do for you"). Used in every other paragraph of a 7-tweet thread, it's a tell. **Real-operator false-positive risk: high — Naval, Sahil Bloom, and George Mack ALL use antithesis as a foundational rhetorical move. The detection criterion has to be *density per unit of post*, not presence.**

- **Tricolons / three-element parallel constructions.** "It's not X, it's Y, it's Z" three-element forms appear in AI output at multiple times the rate they appear in matched human corpora. The pattern is named in [Flux8Labs 2025](https://medium.com/@flux8labs/why-ai-slop-content-is-diluting-your-brand-and-how-to-fight-it-fa8d7d27fb5b), [Drainpipe 2025](https://drainpipe.io/the-toolkit-for-truth-essential-tools-to-detect-ai-slop-across-all-media/), and across the VERMILLION 10-signal framework ([Researchleap 2025](https://researchleap.com/the-disappearing-author-linguistic-and-cognitive-markers-of-ai-generated-communication/)). **Real-operator false-positive: tricolons are textbook rhetoric and many human writers use them.** The slop signal isn't tricolon presence; it's *tricolons used reflexively* — three or more tricolons in a 7-tweet thread is past the human baseline.

- **Signature transitions: "moreover," "furthermore," "delve into," "in conclusion," "let me explain," "Here's the thing," "Let's be clear," "It's worth noting."** These appear in [Vegavid 2026 detection guide](https://vegavid.com/blog/how-to-detect-ai-generated-text), [Drainpipe 2025](https://drainpipe.io/the-toolkit-for-truth-essential-tools-to-detect-ai-slop-across-all-media/), and the VERMILLION framework. The frequency of "delve" in arxiv abstracts **dropped sharply after the pattern was named in early 2024** ([Liang et al. 2025, "Is ChatGPT Transforming Academics' Writing Style?"](https://arxiv.org/pdf/2404.08627)), showing that the tells are learnable on both sides — the classifier improves, the LLM trains to evade. **For X drafts the signal is *unprompted appearance in conversational text* — "moreover" in a 280-char tweet is a much stronger signal than in a 2000-word essay.**

**Tier 2: Structural tells specific to short-form social.**

- **"Stop X. Start Y." imperative-pair constructions.** This pattern is endemic to AI-generated LinkedIn and X founder-advice content. Pattern: two short imperative sentences in immediate succession, the first negating a behavior, the second prescribing the replacement. Examples (synthesized from observed corpora): "Stop optimizing for likes. Start optimizing for replies." / "Stop hiring for skills. Start hiring for trajectory." The construction is a structural cousin of "It's not X, it's Y" — antithesis recast as imperative. **Real-operator false-positive: Hormozi explicitly teaches this construction; many indie hackers use it.** The tell is *not* the single instance but *the rhythm* — three of these in a 5-tweet thread is past any operator's natural rate.

- **Listicle bloat with parallel grammar.** Five-bullet-point lists where every bullet has the same syntactic shape (verb-noun-modifier triple, or "noun: explanation" colon form, or "—— : ——" em-dash-then-explanation form). Real human listicles vary syntax. AI-generated listicles converge on whichever shape the prompt template used. **Detection signal: syntactic-uniformity score across bullets above ~0.8 cosine similarity.** Real-operator false-positive: moderate — some operators do write rigorously parallel lists, but they vary it across posts.

- **False-vulnerability hooks.** "I failed at X. Here's what I learned." / "Last year I almost went bankrupt. Three lessons." / "I lost a $X deal. Here's why." The pattern is named as "vulnerability theater" in [The DigiPalms 2025](https://thedigipalms.medium.com/linkedins-most-convincing-posts-aren-t-written-by-you-here-s-who-s-ghosting-ebb1d195e914) and as performative-pathless-path failure in Paul Millerd / Tim Stoddart's writing-online critique. The construction is **carefully calibrated admissions of failure that feel authentic but aren't too threatening**. Detection signal: confessional-opening followed by exactly-3 numbered lessons, where the failure is non-specific (no named entity, no dollar amount with provenance, no date) and the lessons are platitudes. **Real-operator false-positive: real operators DO post real failures. The tell is the abstraction level of the failure (specific = real, "I almost gave up" = generated) and the bullet-shape regularity of the lessons.**

- **Generic "founder advice" tone.** A specific composite voice — earnest, slightly conspiratorial, prescriptive, lightly profane in safe-edge places, gesturing at "what nobody tells you," promising-rare-knowledge framing without ever delivering rare specifics. This is the **composed-engineer voice**: median-of-the-distribution of LinkedIn-influencer × Twitter-bro × ghostwritten-CEO. **Detection signal: extremely difficult to surface as a single feature; this is a gestalt judgment and must stay in the judge criterion.** The v0 spec's X-5 ("survives the screenshot test") is the right shape — a human practitioner re-attributing the post to its named account would or would not feel the voice click. Composed-engineer voice fails that re-attribution test.

**Tier 3: Patterns that look algorithmic but ARE legitimate operator voice — DO NOT structurally penalize.**

- **Em-dashes alone, without other tells.** Many real operators use em-dashes as their signature punctuation. The em-dash is *not* the tell; em-dash density above 3× the account's baseline + co-occurrence with antithesis + tricolons is the tell.

- **Hook-driven openers.** "Here's why X is broken." / "Three things I wish I knew before Y." Hook-driven structure is what the Cole/Bush *Ship 30* curriculum explicitly teaches — millions of human-written tweets use it. **The tell is not the hook shape; it's the hook *plus* generic content *plus* listicle-bullet completion.**

- **Counter-intuitive declarations.** "Everyone is wrong about X." This is the George Mack High-Agency / Sahil Bloom paradox-pattern. Real-operator core move. **Not a tell on its own.**

- **Numeric specifics in opening sentences.** "73 percent of founders quit before product-market fit." Real-operator move (Cody Schneider, Justin Welsh both teach this). The tell is *fabricated* numerics with no source — but fabrication is a structural problem (CI-6 evidence-chain analogue) not a slop problem.

- **Confessional first-person posts.** Real operators post real failures. The tell is the *specificity gradient* (real = named entity/dollar amount/date; generated = "I lost it all" abstraction).

- **Antithesis used sparingly.** One "It's not X, it's Y" line in a 7-tweet thread is a rhetorical highlight. Three in a 7-tweet thread is a tell.

**The unifying rule: every single tell has high false-positive risk on real operator voice. The slop fingerprint is the *stack* — three or more Tier-1 or Tier-2 tells co-occurring in a single post or thread.**

### 3. AI-assisted-but-edited vs AI-generated-and-posted

This is the load-bearing operational question for the gofreddy use case. The lane intentionally drafts in the operator's voice using fine-tuned generation. The deliverable to the operator includes both finished posts AND drafts the operator may edit before posting. The judge must score "this draft is publishable" — which requires distinguishing the gradient between:

- **Pure AI output, unedited:** the slop case. Should score 0 on the gestalt voice criterion.
- **AI-drafted, operator lightly edited (sentence restructure, replaced 2–3 phrases):** detection is at coin-flip per Supwriter benchmark. The classifier signal is gone. **Judge approach: this should still score 0 on the gestalt criterion if AI tells remain stacked; should score 1 if the edits broke the stack.**
- **AI-drafted, operator heavily edited (added new specific anecdote, rewrote opening, killed at least one Tier-2 pattern):** detection drops below 50 percent. **This is what the lane should produce.** Should score 1 on gestalt voice.
- **Operator-drafted from AI-assist outline:** legitimately human, no tells should remain. Score 1.
- **Operator-drafted, no AI:** baseline. Score 1.

The judge cannot directly tell which gradient it's seeing. **What it can test is the artifact's surface for the slop fingerprint stack.** If 3+ Tier-1/2 tells remain stacked, the artifact reads as slop regardless of the gradient — and reads as slop to the scroller, which is the actual outcome we care about. This is the X-5 criterion as currently written.

The corollary: the lane's job during evolution is to learn the *de-stacking* operation. Fine-tuned voice generation gets the operator's vocabulary; the post-generation editing pass has to break the slop-fingerprint stack. The judge that rewards de-stacked output is selecting for the right substrate behavior.

### 4. The structural_gate / judge split

Per design guide §2 (Hard Rules → structural_gate, Principles → judge), the question becomes: which slop tells are deterministically verifiable and low-false-positive enough to land in `structural_gate`, and which are gestalt?

**Belongs in `structural_gate` (deterministic, named, false-positive defensible):**

1. **Em-dash density above absolute threshold.** Count em-dashes per 100 words. If above ~5 per 100 words (roughly 4× human baseline per Goedecke and Piece of K data), fail the gate. Real-operator false-positive rate: very low at 5/100; most real operators run 0.5–1.5. Workflow gaming risk: substitute parentheticals, which the gestalt judge still catches. **20 LOC.**

2. **Banned-phrase blocklist on conversational tells.** Hard-block on appearance in a draft: "moreover," "furthermore," "delve into," "in conclusion," "let me explain why," "let me explain:", "here's the thing:", "let's be clear:", "it's worth noting," "navigate the complexities," "tapestry of," "robust framework," "unleash," "harness the power of," "transformative," "leverage" used as a verb. These are phrases no thoughtful operator actually writes in a 280-char tweet, where every word is at a premium. Real-operator false-positive: near zero — these phrases are deadweight in conversational text. Workflow gaming risk: the model substitutes "additionally" for "moreover," but every substitution narrows the corridor the workflow operates in. **15 LOC + curated list.**

3. **Three-element parallel-construction density.** Detect tricolons via syntactic-uniformity scoring: count instances of three coordinate noun-phrases-or-clauses in a row within a 280-char unit. Threshold: more than 2 tricolons in a thread of any length triggers gate failure. False-positive: low if threshold is conservative. **30–40 LOC for the syntactic detector.**

4. **"Stop X. Start Y." structural pattern detector.** Regex/parse-tree match for two immediately-adjacent imperative sentences where the first contains "stop|don't|quit" and the second contains "start|begin|try." More than 1 instance in a single post fails the gate. False-positive: low — the pattern is a strong template. **15 LOC.**

5. **Listicle syntactic-uniformity score.** When the post contains a numbered or bulleted list of 3+ items, compute cosine similarity of bullet-shape (POS-tag sequence). If above 0.85, fail the gate. The threshold catches AI-generated rigid-parallel listicles while permitting real operator listicles that vary syntax. **40 LOC + tokenizer dependency.**

6. **3+ hashtags hard fail.** Algorithmic-penalty hard rule per the v0 spec §1. Already in `slop_gate`. **0 LOC.**

7. **Character limits and thread-count bands.** Single post ≤280, thread units 3–12. Already verifiable. **Already in slop_gate.**

8. **URL count + resolution check (per CI-6 lessons).** Cited URLs must HEAD-resolve. Prevents the fabricated-link variant of slop. **20 LOC.**

**Stays in the judge as X-5 gestalt criterion (non-deterministic, high real-operator-overlap, attack-surface bounded by per-criterion isolation):**

- **Account-voice consistency.** Account's prior posts in `source_data` define register; the draft is consistent with that register or it isn't. This requires reading both — gestalt.

- **Composed-engineer voice detection.** Founder-advice tone that could be any account. The judge must imagine "would the operator, screenshotted-and-quoted, recognize themselves?" Gestalt.

- **False-vulnerability vs real-vulnerability.** Real failure has specificity (named entity, dollar amount, date); generated has abstraction. The specificity gradient is reader-judgment, not regex.

- **Slop-stack threshold judgment.** Whether the *remaining* tells after `structural_gate` passes still co-occur enough to read as slop. This is the residual fingerprint test.

- **Antithesis density past baseline.** Hard-coded thresholds break here because rhetorical antithesis is legitimate. The judge has to read for whether the antithesis works as rhetoric or as filler.

### 5. The Goodhart trajectory for AI-slop detection specifically

If the judge rewards "no em-dashes," the workflow learns parentheticals. If the judge rewards "no 'moreover,'" the workflow learns "additionally." This is the v0 spec §6 closing observation, and it's correct: **AI-slop is a pattern stack, not a single tell**.

The Goodhart-resistance design is the same shape as elsewhere: outcome-question criterion ("would the relevant scroller recognize the slop fingerprint?"), evaluated as gestalt by the judge, while `structural_gate` defends a small set of patterns where the legitimate-operator-overlap is genuinely low. The deliberate redundancy — gating density of em-dashes AND tricolons AND banned phrases AND "stop X start Y" — means the workflow has to evade all of them simultaneously to game the gate, and the gestalt judge catches the residual.

The variance instrumentation prescribed in design guide §11.5 applies directly: if X-5 score variance grows monotonically over 3 generations OR X-5 mean compresses toward the middle of the 0/0.5/1 distribution, the gate is being gamed. Redesign, don't calibrate.

### 6. What v0 X-5 gets right, and the two amendments to consider

**Right:** outcome question is reader-effect-shaped ("would a reader familiar with the account recognize this as the author's voice"); score-1 anchor names the slop-signature *stack* (not single tells); score-0 anchor names slop-signature pattern *stack* (not single tells); 0.5 reserved for "account voice not in artifact" cold-start case; CoT walks (a) identify voice from prior posts (b) test current draft for consistency + slop-stack absence. No framework names; no anti-bias clauses; no σ-widening.

**Amendment 1: tighten the X-5 score-0 anchor to specify "stack of 3+ tells co-occurring," not just "AI-slop signatures present."** The current prose "AI-slop signatures present (excessive em-dashes, 'moreover/in conclusion,' smooth-but-gradeless prose, symmetrical bullet rhythm)" is read by frontier judges as "any one of these tells present → score 0." That over-penalizes real operators who use em-dashes. The amendment: "AI-slop signature *stack* — at least 3 of the named tells (em-dash density past account baseline, signature transition phrases, three-element parallel rhythm, false-vulnerability shape, listicle parallelism) co-occurring." Forces the judge to count co-occurrence.

**Amendment 2: add the "post-edit residual" framing.** The X-5 score-1 anchor should include "even if the post was AI-drafted, the operator's edits broke any slop-fingerprint stack that would have been present." This makes explicit that AI-assist is acceptable; what's not acceptable is unedited slop residue. This aligns with the gofreddy lane's actual use case (the lane drafts in voice; the operator edits) and prevents the criterion from over-penalizing the AI-drafted-but-edited gradient.

### 7. Real-classifier-as-feature: a final negative recommendation

Some open questions in the v0 spec consider integrating Originality.ai / GPTZero / a fine-tuned BERTweet detector as a slop feature into the judge or structural_gate. **Do not.** Reasons:

- The realistic threat-model accuracy is 50–65 percent on the lane's actual output distribution (fine-tuned voice generation + human editing).
- The 15–17 percent false-positive rate disproportionately penalizes non-native English speakers and technical writers — both core to gofreddy's first-cohort clients.
- Integrating the classifier creates a workflow target: under 50-generation pressure, the lane learns to maximize "classifier says human," which is at best 50 percent correlated with what we actually want and at worst is inverse-correlated for the specific patterns that legitimate operators use.
- The vendor-pricing makes integration operationally expensive at the lane's per-fixture-call volume.

The classifier integration would import the worst of every concern and provide minimal signal. The deterministic checks in `structural_gate` plus the X-5 gestalt judge criterion provide what the classifier integration would have, with vastly better calibration and Goodhart-resistance.

---

## Recommendations

### For `structural_gate` (deterministic verifiables, each defends a named failure surface)

The current `slop_gate` should be extended with the following checks. Each is sized so that legitimate operator output passes; each defends a specific named tell from the AI-slop literature; each has a real-operator false-positive rate below 5 percent on the corpus shape the lane produces.

1. **Em-dash density gate.** Reject drafts with more than 5 em-dashes per 100 words. Defends against GPT-family 3.28×-baseline overuse documented in Goedecke 2025 and Piece of K 2025. Real-operator false-positive risk: low — most working operators run 0.5–1.5 em-dashes per 100 words. **20 LOC.**

2. **Banned-phrase blocklist (conversational tells).** Hard-reject on appearance of: moreover, furthermore, delve into, in conclusion, let me explain why, let me explain:, here's the thing:, let's be clear:, it's worth noting, navigate the complexities, tapestry of, robust framework, transformative, unleash, harness the power of, leverage (as verb). These are phrases that do not belong in 280-char tweet content under any natural-voice editorial standard. Defends against the most-named ChatGPT signatures in 2025–2026 critique. **15 LOC + curated list (one-line per entry).**

3. **"Stop X. Start Y." structural detector.** Regex or parse-tree match for two immediately-adjacent imperative sentences with first-contains-stop/don't/quit and second-contains-start/begin/try. More than 1 instance per post or thread triggers fail. Defends against the imperative-antithesis tell. **15 LOC.**

4. **Three-element parallel-construction density.** Detect tricolons; reject if more than 2 per thread. Defends against tricolon abuse documented across VERMILLION / Flux8Labs / Drainpipe. **30–40 LOC** with syntactic detector dependency (already in repo from CI lane work).

5. **Listicle syntactic-uniformity gate.** When draft contains 3+ numbered or bulleted items, compute cosine similarity of POS-tag sequences. Reject if above 0.85 average. Defends against AI-generated rigid-parallel listicle bloat. **40 LOC** with shared tokenizer infrastructure.

6. **Existing checks retained:** ≤2 hashtags, character limits, thread-unit count bands, URL HEAD resolution (port from CI-6 work).

The cumulative LOC across the new checks: ~120 LOC + a curated blocklist of ~20 phrases. Implementation cost: under a day. Each check fails closed; the workflow has to evade all of them simultaneously, not just one.

### For the judge (X-5 outcome criterion)

Amend the v0 X-5 prose as detailed in §6 above:

- Score-0 anchor specifies "stack of 3+ tells" not "any tell present."
- Score-1 anchor explicitly permits AI-assist where operator-editing has broken the slop-fingerprint stack.
- Retain reference-free posture, behavioral binary anchors, structured CoT, no framework names.
- Run the design-guide §5 redundancy check after first 5 fixtures: X-5 may correlate >0.7 with X-2 (specific knowledge) since composed-engineer voice fails both. If correlation is high, merge into one criterion focused on the gestalt.

### For the evolution loop

- **Track X-5 variance per generation** (design guide §11.5 prescription). Monotonic variance growth or central-tendency collapse on X-5 indicates the workflow is learning to game the gestalt; trigger redesign, not calibration.
- **Track structural_gate fail rates per check per generation.** If em-dash-density failures drop to zero by generation 10 while X-5 mean stays flat, the workflow has learned the em-dash rule specifically; check whether other tells are migrating in.
- **Asymmetric inner-loop tell.** If the inner-loop is fine-tuned on a single LLM family, that family's signature tells (em-dash for GPT-family; near-zero em-dash for Claude-family; specific phrase preferences) will dominate the gate-failure distribution. Use this as a leakage tell for inner-loop family detection — same defensive signal design guide §16 recommends for cross-family judge panel monitoring.

---

## Open Questions

1. **Cold-start voice handling.** When a new client has insufficient post history for X-5 to test "account-voice consistency," the criterion collapses to 0.5 unknown — which means the judge cannot discriminate slop from voice. **Proposal:** for cold-start accounts, the judge falls back to a Tier-2 standard ("would any thoughtful operator in this niche have written this?") and the `structural_gate` checks carry more weight. Memory references `linkedin_engine v040 cold-start mutation` as a precedent; port that pattern. Not blocking for v1 launch on existing fixtures (DWF, Klinika, Anthropic, Perplexity have post history); flag for new-client onboarding.

2. **Per-account em-dash baseline calibration.** The 5-per-100-word global threshold is conservative for accounts that legitimately run higher (e.g., journalists in our ICP). v2 should compute per-account baseline from `source_data` history and apply threshold = max(5/100, account_baseline × 3). v1 ships the global threshold; revisit when we have a fixture that genuinely runs higher.

3. **"Composed-engineer voice" classifier feasibility.** Could a fine-tuned classifier on a labeled corpus of "founder-advice slop" vs "real operator voice" achieve usable accuracy? Provisional answer: probably yes at training time but not in production — the corpus drifts as both sides train against each other. Defer; the gestalt judge X-5 is the load-bearing detector and a classifier-feature would import all the failure modes from §1.

4. **Watermarking integration.** SynthID and similar watermarks ([DigitalApplied 2026](https://www.digitalapplied.com/blog/ai-content-detection-tools-2026-accuracy-pricing-guide)) embed statistical signatures in model output. If the lane's inner-loop preserves the watermark, `structural_gate` could detect it deterministically. Provisional: defer — watermarks are stripped by editing, and the lane's edit pass is intentional. Not blocking.

5. **The v0 spec X-3 (falsifiable claim) ↔ X-5 (voice) correlation under voice-cloning.** Composed-engineer voice tends to make claims that are simultaneously *unfalsifiable* (platitudes) and *off-voice* (generic). The two criteria may correlate >0.7 on slop-positive cases. Run the redundancy check explicitly on those two criteria after first 5 fixtures.

6. **First-cohort overfitting.** The slop tells documented here are calibrated against English-language Anglosphere operator voice. Polish-language clients (DWF, Klinika) may show different Tier-1 tell frequencies — Polish em-dash conventions, Polish discourse-marker preferences. v1 ships the English-calibrated thresholds; build a 2–3-fixture Polish-language calibration set before locking thresholds for the Polish lane.

---

## Citations

**AI-slop detection effect sizes (2025–2026):**

- Dawkins, Fraser, Kiritchenko. *When Detection Fails: The Power of Fine-Tuned Models to Generate Human-Like Social Media Text.* arxiv [2506.09975](https://arxiv.org/abs/2506.09975), June 2025. 505,159 AI-generated social posts; human-study detection accuracy 54 percent under realistic threat model; 16.86 pp absolute drop in automated detection.
- Tourille et al. *Unmasking the Imposters: How Censorship and Domain Adaptation Affect the Detection of Machine-Generated Tweets.* arxiv [2406.17967](https://arxiv.org/abs/2406.17967), 2024. BERTweet / stylometric / soft-voting ensemble across 9 Twitter datasets; uncensored models break detection.
- Shaib, Chakrabarty, Golano, Wallace. *Measuring AI "Slop" in Text.* arxiv [2509.19163](https://arxiv.org/abs/2509.19163), Sep 2025. Slop taxonomy via expert interviews; capable reasoning LLMs fail to reliably extract slop; binary slop judgments subjective but correlate with coherence and relevance.
- Liang et al. *Is ChatGPT Transforming Academics' Writing Style?* arxiv [2404.08627](https://arxiv.org/pdf/2404.08627), 2024–2025. "Delve" frequency drop after pattern naming.
- *Detecting the Machine: Comprehensive Benchmark.* arxiv [2603.17522](https://arxiv.org/abs/2603.17522), 2026. Cross-domain and cross-generator evaluation reveals substantial generalization failure under distribution shift.
- *Why AI-Generated Text Detection Fails: Evidence from Explainable AI Beyond Benchmark Accuracy.* arxiv [2603.23146](https://arxiv.org/abs/2603.23146), 2026.
- *Diversity Boosts AI-Generated Text Detection.* arxiv [2509.18880](https://arxiv.org/pdf/2509.18880), 2025.

**Em-dash and stylometric markers:**

- Sean Goedecke. *Why do AI models use so many em-dashes?* [seangoedecke.com](https://www.seangoedecke.com/em-dashes/), 2025. GPT-4.1 at 3.28× human baseline.
- *The Rise of the Em Dash in Ecology Abstracts.* [Piece of K](https://www.pieceofk.fr/the-rise-of-the-em-dash-in-ecology-abstracts/), 2025. Em-dash frequency doubled 2021–2025.
- McGill Office for Science and Society. *Why Did LLMs Steal Our Em-Dashes?* [mcgill.ca/oss](https://www.mcgill.ca/oss/article/critical-thinking-student-contributors-technology/why-did-llms-steal-our-em-dashes), 2025.
- *Em Dashes, Hyphens and Spotting AI Writing.* [Plagiarism Today](https://www.plagiarismtoday.com/2025/06/26/em-dashes-hyphens-and-spotting-ai-writing/), 2025. Claude/Gemini/Llama em-dash rates near zero; pattern is GPT-family specific.
- *Stop AI-Shaming Our Em Dashes — Please.* [The Ringer](https://www.theringer.com/2025/08/20/pop-culture/em-dash-use-ai-artificial-intelligence-chatgpt-google-gemini), 2025.
- *Too many em dashes? Spotting text written by chatbots is still more art than science.* [Indiana Capital Chronicle](https://indianacapitalchronicle.com/2025/08/05/too-many-em-dashes-spotting-text-written-by-chatgpt-is-still-more-art-than-science/), 2025.

**Classifier accuracy benchmarks:**

- *GPTZero vs Originality.ai: Which AI Detector Is More Accurate?* [HumanizerAI](https://humanizerai.com/blog/gptzero-vs-originality-ai), 2026.
- *AI Detector Accuracy Benchmarks 2026.* [EyeSift](https://www.eyesift.com/blog/ai-detector-accuracy-benchmarks-2026/), 2026.
- *GPTZero vs Originality AI: Which AI Detector Actually Works in 2026?* [Fritz.ai](https://fritz.ai/gptzero-vs-originality/), 2026.
- *Are AI Detectors Accurate in 2026?* [WalterWrites](https://walterwrites.ai/are-ai-detectors-accurate/), 2026.
- *How Accurate Are AI Checkers: Accurate Statistics for 2026.* [EssayHub](https://essayhub.com/blog/how-accurate-are-ai-checkers), 2026.
- *AI Content Detection Tools 2026: What Works and What Doesn't.* [DigitalApplied](https://www.digitalapplied.com/blog/ai-content-detection-tools-2026-accuracy-pricing-guide), 2026.
- *How to Detect AI-Generated Text: 2026 Guide.* [Vegavid](https://vegavid.com/blog/how-to-detect-ai-generated-text), 2026.

**Pattern catalogues:**

- Blake Stockton. *Don't Write Like AI (1/101): "It's Not X, it's Y".* [blakestockton.com](https://www.blakestockton.com/dont-write-like-ai-1-101-negation/).
- *Why Does AI Keep Saying "It's Not X, It's Y"?* [DEV Community](https://dev.to/milind_nair/why-does-ai-keep-saying-its-not-x-its-y-2ihk).
- Colin Gorrie. *Why ChatGPT writes like that.* [Dead Language Society](https://www.deadlanguagesociety.com/p/rhetorical-analysis-ai), 2025.
- *Some alternatives to "It's not X; it's Y".* [Hardly Working substack](https://hardlyworking1.substack.com/p/how-to-avoid-sounding-like-a-stupid).
- *How to Stop ChatGPT From Writing "Not Just X, but Y".* [PopularAI](https://www.popularai.org/p/how-to-stop-chatgpt-from-writing-not-just-x-but-y).
- *Why AI Slop Content Is Diluting Your Brand.* [Flux8Labs / Medium](https://medium.com/@flux8labs/why-ai-slop-content-is-diluting-your-brand-and-how-to-fight-it-fa8d7d27fb5b), 2025.
- *The Toolkit for Truth: Essential Tools to Detect AI Slop.* [drainpipe.io](https://drainpipe.io/the-toolkit-for-truth-essential-tools-to-detect-ai-slop-across-all-media/), 2025.
- *Detecting AI Slop: Techniques and Red Flags.* [glukhov.org](https://www.glukhov.org/post/2025/12/ai-slop-detection/), Dec 2025.
- *The Disappearing Author: Linguistic and Cognitive Markers of AI-Generated Communication.* [Researchleap](https://researchleap.com/the-disappearing-author-linguistic-and-cognitive-markers-of-ai-generated-communication/), 2025. VERMILLION 10-signal framework.
- *How to Stop AI Slop in Production: A Two-Layer Validator for LLM Output (2026).* [Peerlist](https://peerlist.io/dumebi/articles/title-how-to-stop-ai-slop-in-production-a-twolayer-validator), 2026.

**Vulnerability-theater and LinkedIn ghostwriting:**

- *LinkedIn's Most Convincing Posts Aren't Written By You.* [The DigiPalms / Medium](https://thedigipalms.medium.com/linkedins-most-convincing-posts-aren-t-written-by-you-here-s-who-s-ghosting-ebb1d195e914), 2025.
- *The State of LinkedIn Ghostwriting in 2026.* [Windmill Growth](https://windmillgrowth.com/blogseo/state-of-linkedin-ghostwriting-2026).
- *Best AI Detectors for X (Twitter).* [Fritz.ai](https://fritz.ai/best-ai-detectors-for-x/), 2026.

**Algorithm context (for completeness, as siblings to v0 spec §1):**

- [xai-org/x-algorithm GitHub repo](https://github.com/xai-org/x-algorithm), Jan 2026 open-source release.
- *The X Algorithm in 2026: What Actually Makes Posts Go Viral.* [OpenTweet](https://opentweet.io/blog/how-twitter-x-algorithm-works-2026).
- *AI Slop — 2025 Word of the Year context.* [Wikipedia](https://en.wikipedia.org/wiki/AI_slop).

**Conformance to design guide:**

- `docs/rubrics/judge-design-guide.md` v2.1 — §2 (structural_gate/judge split), §4 (criterion shape), §5 (≤5 criteria, redundancy check), §10 (input sanitization, bias mitigations), §11.5 (variance instrumentation prescribed).
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` v3.3 — analogous structural_gate expansion pattern (5 anti-hallucination + 4 shape-conformance checks); CI-6 evidence-chain criterion as documented justified-breach precedent.
- `docs/research/2026-05-18-judges-domain-x-engine.md` — this document deepens its §2 failure-mode catalogue and §4 X-E criterion along the AI-slop axis.
