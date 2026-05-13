---
date: 2026-05-13
phase: D-review
topic: adversarial review of phase-d-master-spec.md + 10 per-lane rubric specs
reviewer: adversarial-reviewer
status: critique — read before approval
---

# Adversarial review — Phase D judge-design spec

This is a hostile read. The spec author asked for failure modes, not flattery. I am not evaluating prose quality, structure, or coherence — coherence-reviewer / feasibility-reviewer own that. I am attacking the *epistemic foundation*: are the premises true, are the assumptions warranted, are the decisions load-bearing on evidence that was actually gathered.

---

## 1. Strongest single critique

**The spec confuses "research consensus across the 2026 web" with "evidence that this evolution loop will produce better artifacts."**

Phase A surveyed lane purposes. Phase B did external research (X API + WebSearch). Phase C self-rated three archived artifacts: one (Lululemon MON v189) where the rubric *passed everything*; one (mayoclinic GEO v189) where the *structural gate ran before the judge could rate anything*; one (3 x_engine drafts from one session sharing one OpenAI source). That is the entire empirical footprint behind a proposal to grow judge surface area by **+106 %** (52 → 107 criteria) across 10 lanes — three of which (article, image, ad) have zero archived artifacts.

`phase-c-variant-ratings.md:41` literally states the conclusion as: *"Existing MON rubric is exceptionally well-calibrated. My ratings agree with the judge across all 8 dimensions."* When the evidence shows the current rubric is calibrated, the inference that **+55 criteria** is the correct response is unsupported. The honest conclusion from Phase C is: "the current rubric is good and the proposed additions are inferred from external research, not from observed failures of the current rubric on real artifacts." The spec does not write that sentence.

This is the load-bearing problem. Almost every other critique below is a downstream consequence.

---

## 2. Top-5 ranked critiques

### #1 — Phase C did not validate the spec's central thesis

(See above.) Phase C examined N=1 monitoring artifact, N=0 successfully-rated geo artifacts, and N=3 x_engine drafts from one session. The spec claims this validates a 10-lane redesign. The most generous reading is that Phase C validated **X-9** (algorithmic-citizenship), confirmed monitoring is fine as-is, and could not validate anything else. Yet `phase-d-master-spec.md:32` summarises this as "+55 criteria" across all 10 lanes — including criteria that were never tested. The phrase "Phase D writes the final per-lane rubric specs, incorporating Tier-1 confirmed + Tier-3 research-grounded + dropped Tier-2 redundancies" (`phase-c-variant-ratings.md:156`) admits this: the majority of new criteria are "research-grounded," meaning "we read 2026 blog posts about LinkedIn algorithms and turned them into rubric prose." That is not validation.

### #2 — Adding criteria probably degrades the fitness signal, not improves it

The spec's implicit theory is monotonic: more criteria = more granular fitness signal = better evolution. This is the opposite of how composite scoring tends to behave with LLM judges. Three problems compound:

1. **Score compression.** With 8 criteria each on 1-3-5, the composite already lives in a narrow [3.0, 4.5] band most of the time (every shipped lane shows this — v007 geo 7.82, monitoring 8.12, marketing_audit 4.88). Adding 5 more criteria of similar shape *flattens* the distribution further. Selection pressure goes down, not up.
2. **Halo bleed.** "ONE quality framing" (Pattern 1) does not actually prevent halo in LLM judges. The same artifact gets re-scored 13 times by 13 prompts that share most of the input context. Empirical literature on LLM-judge ensembling (rating-roulette / preference-leakage) shows criterion-criterion correlation typically ≥ 0.6; the marginal signal from criterion 9 vs criterion 13 is much smaller than the rubric author thinks.
3. **AUTO-CAP collisions.** The spec adds 11 AUTO-CAP criteria (master-spec line 87). If two fire, what wins? Composite cap at 4 + composite cap at 4 + HARD FLOOR at ART-4=2 + auto-cap at IMG-3=1 — the spec does not specify cap precedence. With four caps live in image_engine alone (IMG-3, IMG-5, IMG-8 plus the cross-lane compliance precondition), the *cap regime* becomes the rubric — quality-tier criteria become decoration. Evolution will optimise around the caps, not toward quality.

The spec never asks "what happens to score variance after going from 8 criteria to 13." That is the first question the operator should ask.

### #3 — "Shape-only mode" is a credibility laundromat

Master spec §"Pre-population behavior — shape-only mode" (`phase-d-master-spec.md:151-158`) introduces a mode where compliance criteria *exist in the rubric, declare they are not scoring, and abstain*. The same pattern recurs in ART-4 (voice corpus consent), IMG-4 (brand-style guide), IMG-8 (compliance), SB-12/15, LI-11, ADE compliance precondition.

This is a substrate trick that pretends the criteria exist while doing none of the work. Concretely:

- The composite score is computed *without* these criteria (they abstain).
- The operator sees "13 criteria in monitoring rubric" but only 12 fire.
- The judge-prompt overhead is still paid (criterion text is loaded into context).
- The cap mechanism advertises protections that don't exist.

The two production risks are:

1. **Silent ship.** A Klinika carousel with a compliance violation will not be auto-capped because IMG-8 abstained. The "two-gate" defence (`phase-d-master-spec.md:146-148`) says the human pre-publish gate catches it. Fine — but then *what is IMG-8 doing*? If the in-loop gate adds no value during the demo window, why is it in the rubric? The honest answer is: it is there so the spec can claim 8 criteria in image_engine. That is theatre, not safety.
2. **Evolution mis-direction.** The loop *thinks* the criterion is scoring. Selection pressure under shape-only is undefined. If criteria fire silently as 5/5 (default-pass abstention), the loop drifts toward "looks clean enough that the absent rule wouldn't fire," which is exactly the failure mode the criterion was meant to prevent. If they fire as 1/5 (default-fail), no artifact is ship-eligible and the lane is dark.

**The spec does not pick.** That ambiguity alone is a blocker.

### #4 — The voice-fidelity rolling-window mechanism is design theatre

ART-4 (`article_engine.md:93-107` + §4 mechanism on lines 210-228) proposes a 200-word sliding-window mechanism with 100-word stride, weighted sum of four components (bigram cosine, sentence-length KL, signature-phrase frequency, clause-type ratio), HARD FLOOR at 2σ.

Five things are wrong with this:

- **Threshold has no calibration source.** "2σ" is presented as a number with no derivation. 2σ of what distribution? The corpus's own self-distribution? At 2σ ≈ 98th percentile, *every long article will have some 2σ window* simply by chance unless the corpus is enormous. A 2,500-word blog has ~25 windows; P(at least one >2σ) ≈ 1 - 0.98²⁵ ≈ 0.4. **Every other article auto-caps from random sampling.**
- **Corpus size requirement (≥5,000 words) is too small.** Five thousand words is one or two blog posts. The window-distance distribution at that corpus size is high-variance. The "corpus 90th percentile" anchor (`article_engine.md:222`) for Score 5's worst-window-distance is sampling noise.
- **The four components are not independent.** Sentence-length KL and clause-type ratio are heavily correlated; bigram cosine and signature-phrase frequency are partial-duplicate signals. Weighted-sum-of-4 reads as four components; the rank of the feature matrix is closer to 2.
- **Mid-paragraph drift is not actually the failure mode.** The spec says (`article_engine.md:97-98`) that mid-article drift is "the biggest 9-vs-5 gap." This is asserted, not shown. The Phase B research cited does not specifically support rolling-window detection over global voice scoring; the spec invented the mechanism.
- **No falsification test.** V1 (`article_engine.md:290`) describes a synthetic-drift test where the validator constructs an artifact known to drift. That tests whether the mechanism fires on a positive control. It does not test whether the mechanism stays silent on negative controls (genuine in-voice variation). Without false-positive testing, the mechanism is one-tailed.

ART-4 is the highest-effort net-new mechanism in the spec. It is also the most speculative. It needs either to be cut to v1.5 or to have its calibration explicitly written out (corpus size, distribution shape, threshold derivation) before any code lands.

### #5 — The 12 "design patterns" are descriptive, not normative — and presenting them as normative locks the spec into the current architecture

`phase-d-master-spec.md:36-92` elevates 12 patterns to "design language." But patterns 1-9 are described as *"used across all 7 existing well-iterated rubrics; preserved in all 10 final specs."* This is post-hoc rationalisation: the patterns are extracted from the current rubrics and then made the basis for evaluating the new rubrics, which then by construction conform to the patterns. There is no comparison cohort.

Concrete consequence: the spec never asks "is the WHY-before-WHAT pattern (Pattern 3) actually load-bearing?" or "does the CoT-before-score closing format (Pattern 9) measurably affect scores?" Without ablation, the patterns are the rubric author's aesthetic preferences crystallised as constraints. The cost is that the 10 new specs all look like the 7 old specs, which means the spec has no chance of discovering a *better* rubric architecture than the current one. The spec is a faithful reproduction of the current style at 2× scale.

A specific test: marketing_audit is preserved as deliberately divergent (JSON envelope + structured output + deterministic counts — `phase-d-master-spec.md:33-34`, Pattern 9 on line 75 admits the divergence). The spec calls this "deliberate divergence." But it never asks whether MA's design is *better* than the gradient-prose design. If so, why are 9 lanes copying the worse pattern? If not, why does MA get to keep its divergence? The spec dodges this and inherits the answer from JR's prior tooling decisions.

---

## 3. Per-section critique

### Premises

- **"More criteria → better fitness signal."** Unstated, almost certainly wrong (see #2). The current 8-criterion rubrics produce composites in [3, 4.5]; adding criteria does not move the mean, it tightens the variance, which hurts evolution.

- **"Anchored prose constrains LLM judges."** Master spec assumes it does (Patterns 3, 6). Empirically LLM judges anchor on the *latest exemplar in context*, not on prose discipline. The geometric/count-based anchors in image_engine (IMG-1: "exactly one element occupies the optical centre and exceeds 40% of slide area") are the right direction for vision. The narrative anchors in article_engine ART-2 ("Reader can defend the thesis citing any section") are not anchors — they are aesthetic descriptions.

- **"Current 7 lanes are the right starting point."** Phase C validated *one* artifact rated 5/5. Geo and storyboard rubrics were not exercised because the substrate gate caught the artifact first. Marketing_audit, linkedin_engine, and competitive were not rated at all. The starting-point claim is asserted with N=1 evidence on one lane.

- **"The 12 patterns are normative."** They are descriptive (see #5).

### Architecture

- **Shared compliance rules vs duplicated per-lane** (`phase-d-master-spec.md:160-167`). Spec picks "shared." The justification is single-source-of-truth and atomic propagation. Both are valid. But the spec never measures the *cost* of the alternative — how often would the operator actually need to edit 6 lane-local files vs one shared file? For Klinika + DWF over a 1-2 month demo window, the answer might be "twice." Twice is not 24-36 maintenance edits; it's 2-6. The shared-rules decision is correct in steady-state but might be premature given that the rules don't even have content yet. **A simpler v1: hard-code 5 trigger phrases per lane locally, write the shared abstraction in v1.5 after the operator has felt the actual pain.**

- **AUTO-CAP applied to ~12 criteria with fuzzy boundaries.** Master spec line 87 lists 11 AUTO-CAP criteria. Some are sharp (IMG-3 format compliance: Pillow measures the canvas, deterministic, fine). Some are fuzzy (LI-11 compliance precondition without rule content yet — what fires the cap?). Some are categorical errors (ART-8 fires on "guaranteed permanent results" regex match — but what about "patients report seeing results within weeks"? Same statutory category, different surface). **Auto-caps work for deterministic checks. They are dangerous for LLM-judge calls because the cap fires on judge wording, not on ground truth.** A judge that hallucinates a Botox mention caps a clean artifact at 4. A judge that misses an actual Dysport mention does not cap. This is correctly named in the validation plan (V2/V3) but the spec proceeds anyway.

- **Mode-conditional firing in storyboard.** 3 modes × different criterion sets → 8-15 active criteria depending on mode. Substrate complexity. The simpler alternative (one storyboard rubric of 10 criteria, anchors named to handle three modes inline) was not considered. The mode-conditional architecture is justified by "no fixture fires all 15" — which is exactly what would be true under the simpler architecture too. The argument for mode-conditional is dispatch correctness; the cost is RUBRIC_VERSION hash explosion (3 mode-states × N criteria = 3× cache fragmentation).

- **Adaptor dispatch in linkedin_engine** (operator vs named-byline). LI-11 firing depends on byline; LI-1 / LI-2 anchors branch on byline. The spec does not say whether the dispatch logic lives in substrate (one place, hard to test) or in the judge prompt (every prompt has byline-conditional text, brittle). Both options have known failure modes (substrate dispatch silently sends wrong anchors; prompt-conditional silently confuses the judge). The spec ships the dispatch without picking the implementation pattern.

### Compliance regime

The most concerning section. Master spec §"Compliance regime shape" + per-lane ART-8 / SB-12 / SB-15 / LI-11 / IMG-8 / ADE compliance precondition.

- **The rules don't exist yet.** `phase-d-master-spec.md:319-323` flatly admits the spec does not write rule content. Resolve-Before-Planning #2 is the gate. **The spec ships the substrate for a regime that has no content, attaches AUTO-CAP semantics to the regime, and proposes shape-only mode as the workaround.** The risk profile of this combination is bad: it advertises legal protection that does not exist. The Klinika demo (Polish medical clinic, statutory liability on the *client*) is too sensitive for this. If the legal-review gate slips past the demo window, the lane ships marketing-clean but compliance-inert. The two-gate design (`master-spec:146-148`) leans on the human reviewer to catch everything the in-loop judge missed — which is fine, but then *the in-loop criterion is doing zero work during the demo window*. Why is it in the rubric?

- **The "useful and specific while staying inside the rule set" Score 5 anchor (ART-8, IMG-8) is uncalibrated without rule content.** Score 5 says things like "filler chemistry named where compliant (hyaluronic acid), post-procedure timelines specific, contraindications section present, PWZ on byline." The judge cannot grade these without a list of what *is* compliant. The Score 5 anchors implicitly assume the judge knows Polish medical advertising law. It does not. Without rule files, the judge will hallucinate compliance.

- **Two-gate as risk mitigation does not justify in-loop compliance criteria during demo.** If the human gate is the actual safety mechanism (correct framing), the in-loop criteria should be *dropped to shape-only with a tracker for later*, not promoted to AUTO-CAP-with-shape-only-pretence. The current design conflates "we want this eventually" with "this is in the rubric now."

### Vision-judge architecture (image_engine)

- **Cost math is wrong.** Master spec §"Open questions" #4 says "Acceptable for v1." Image_engine spec §3 says ~11 calls × 2000 tokens ≈ USD 0.002 per carousel; calibration corpus 50 fixtures ≈ USD 0.10. **This is per-fixture cost; the spec ignores that fixtures fan out across variants × generations.** Evolutionary loop: 30 generations × 4 variants × 10 fixtures = 1,200 carousel evaluations = USD 2.40. That is still cheap. But the spec's "≈11 calls per carousel" assumes a 9-slide carousel; the IG carousel range is 2-10 slides; the LinkedIn document carousel range is 7-10. With per-slide IMG-5 calls being the dominant term, peak-case 10-slide carousels are ~25% more expensive than the estimate. And the latency math (4-8s × 11 calls / semaphore of 4-6 → 60-90s per carousel) is the real bottleneck. Per generation per variant: 90s. Per variant: 30 × 90 = 2,700s = 45 min. Per fixture × 4 variants: 3 hours. Per 10-fixture corpus: 30 hours. **A 30-hour image_engine evolution run is not "acceptable for v1."** The cost claim hides a wall-time problem.

- **Tell catalogue (IMG-5 a-g) is brittle.** Spec lists 7 AI-generation tells. Items a-d (hand count, pupil reflection, skin smoothness, in-image text) are observable. Items e-g (shadow inconsistency, edge artifact, default-Midjourney aesthetic) are qualitative. The "two-tells-from-this-list → cap" rule mixes the categories. A vision judge that flags one observable tell (e) + one aesthetic tell (g) caps the artifact; whether that's correct depends on whether the operator agrees about the aesthetic tell. **The cap is fired on a 50%-aesthetic judgement.** The stylised-illustration carve-out (`image_engine.md:147`) is correct but underspecified: how does the judge decide photoreal vs stylised on a hybrid (vector illustration with one photo inset)?

- **Brand-style-guide abstain mode** (`image_engine.md:117`). Same problem as compliance regime: ship the criterion, the rule content does not exist, abstain. This is the second criterion in image_engine alone that ships pre-validation. Image_engine is 6/8 essential criteria; IMG-4 and IMG-8 are both pre-validation. The lane is half-implemented at spec time.

### New lanes (article, image, ad) — zero historical data

- **The validation framework is a "first 5 fixtures" anchor for each new lane** (master spec §"Phase 4," `article_engine.md:299-301`, `image_engine.md:305-317`, `ad_engine.md:271-307`). 5 fixtures × 4 variants = 20 artifacts. The 8 criteria × 5 fixtures = 40 score data points per criterion. For a 5-point scale with cap mechanics, 40 data points is not enough to detect calibration drift in the first criterion, let alone validate all 8. **The validation plans are first-deliverable smoke tests, not rubric calibration.**

- **The new lanes assume infrastructure that is not in scope.** Image_engine assumes Pillow/Cairo/skia composition module (`image_engine.md:281`) — net-new. Article_engine assumes findings_brief contract (`master-spec:186-190`) — net-new. Ad_engine assumes Foreplay/Adyntel/SerpAPI providers wired (`ad_engine.md:221`) — partially wired. The spec's "6 weeks total" timeline (`master-spec:265`) bakes in the structural-input work but does not bake in the composition module (image rendering library, brand-style-guide population, voice corpus consent). **Realistic timeline is 10-14 weeks, not 6.**

### Validation framework

- **V1-V7 are positive controls.** Every V-test in master spec §"Validation framework" is "synthetic violation → cap fires." None of them test "clean artifact → no cap." Without negative controls the rate of false positives is unknown. A cap regime with 80% true-positive rate and 30% false-positive rate is worse than no cap regime — it just adds noise. The spec does not measure false-positive rate.

- **Inter-family agreement is missing.** `judge_calibration.py` exists (100 LOC, last touched 2026-04-23) and runs a Claude-vs-Codex drift check. The spec adds 55 new criteria; cross-family agreement on those criteria is unknown. If Claude and Codex disagree systematically on (say) IMG-5 "default-Midjourney aesthetic," the evolution loop's fitness signal is judge-family-dependent. **The spec does not mention `judge_calibration.py` at all.** That is the existing in-house mechanism for the exact failure mode the spec is most exposed to.

- **Rollback plan is missing.** If the new rubric produces *worse* evolution outcomes than the v007 baseline, how does the system revert? The RUBRIC_VERSION hash invalidates the score cache, so a rollback re-runs all variants. The spec does not specify a "shadow rubric" mode (score both old and new rubric in parallel for N generations, compare frontier composition) which is the standard de-risk pattern for evolutionary-loop rubric changes.

---

## 4. Counter-evidence the spec ignored or misread

The existing evolution loop has 180+ archived variants and a clear history. The spec under-reads its own substrate.

### What v006/v007 history actually says

1. **The current 8-criterion rubrics already produce stable composites** (geo 7.82, monitoring 8.12, marketing_audit 4.89 — recent commit messages). The system *is converging*. The spec's premise that the rubric needs +55 criteria implies the system is *not converging*. Those are different problems with different fixes. If composites are stable in [3, 8] and the operator wants higher peaks, the answer is probably better *substrate* (mutation operators, exemplar selection, parent-pair construction), not better fitness signal.

2. **Monitoring is "gold standard" per JR's assessment + Phase C confirmation** (`phase-c-variant-ratings.md:41`). The spec adds 5 new monitoring criteria (`master-spec:24`). One (MON-9 source faithfulness) is genuinely load-bearing. Four others (MON-10/11/12/13 plus the MON-14/15 already dropped) are improvements over a rubric Phase C just called exceptionally well-calibrated. **You don't fix what isn't broken.** The honest move: MON-9 only.

3. **X-9 algorithmic-citizenship is the only Phase B addition with N=3 empirical support.** Phase C confirmed this on three drafts. The spec ships X-9 as essential AUTO-CAP at score 1 (`master-spec:87`). This is the one case where the spec's reasoning is solid. Notice it is also the case where the spec proposed *removing one behaviour* (external links), not *adding a new behaviour*. The pattern that worked is "catch a known violation," not "elaborate criteria for new dimensions."

4. **The "5th and 6th lane added without master plans" precedent** (cited in image_engine.md:254). The 4 existing workflow lanes did not have rubric master specs. They have a small registry entry and a handful of criteria authored in-line. The spec is now writing 40,000 words of rubric across 10 lanes including 3 new ones. This violates the lane's own established norm. The simplest-precedent test (the operator's own rule: "anchor plans to simplest existing precedent" — see MEMORY.md) would shrink Phase D by 80%.

### What the existing rubric scores say

The `autoresearch/archive/v006/scores.json` and v007 history show composites clustering. If criterion 9 of monitoring were missing real signal, MON v007 would not be at 8.12. The composite is at ceiling for the lane. **Adding criteria below ceiling does not raise the ceiling.** It re-distributes the score weight across more dimensions. The spec never addresses this.

### What the substrate's history says

The 2026-05-08 geo regression root-cause memo notes that v007→v008 cliff was caused by OpenAI gpt-5.5's cybersecurity filter rejecting the geo prompt's bot-user-agent enumeration — *not* a rubric problem. The geo lane has dropped from 7.82 (v007) to ~0 (v008+) because of substrate-side prompt rejection. **The geo lane's score volatility is from the substrate, not the rubric.** Adding 5 new geo criteria (GEO-7a/7b/8a/8b/9, master-spec line 23) does not address the actual failure mode.

---

## 5. What I'd cut

In order of confidence:

1. **Drop MON-10/11/12/13.** Keep MON-9 only. Phase C confirmed the existing rubric is at ceiling; the only validated gap is fabrication detection. (-4 criteria)

2. **Drop GEO-7a/7b/8a/8b split + GEO-10/GEO-11.** The geo lane's recent issues are substrate, not rubric. Keep GEO-9 (named-expert quoted attribution — the only one with citation-lift evidence). (-5 criteria)

3. **Drop the rolling-window ART-4 mechanism for v1.** Replace with a single corpus-distance score on the whole article. The 200-word-window mechanism is design theatre without calibration. Revisit when the corpus is ≥50K words. (-1 mechanism, ART-4 stays as criterion)

4. **Drop IMG-6 (thumbnail legibility), IMG-7 (alt-text quality).** Both are hygiene checks. IMG-6 can be a deterministic Pillow downscale-and-OCR test, not a vision-judge criterion. IMG-7 is text-only and small. They consume vision-judge calls disproportionate to their signal. (-2 criteria)

5. **Drop "shape-only mode" entirely.** Replace with: compliance criteria do not ship until rule files are populated. The lane ships without them and the human pre-publish gate is the documented control. This kills the credibility-laundromat pattern. (-4 criteria temporarily; revisit when legal review completes)

6. **Drop ADE-5's specific (angle, hook-lever, persona-stage) taxonomy lock-in.** The 7×7×5 = 245-tuple space with the judge picking one per variant is invitation to inflate distinct-tuple counts. The judge will emit a different tuple per variant to maximise ADE-5. Replace with "judge writes one-sentence bet per variant; operator post-hoc dedupes." Operator-loop, not in-loop. (-1 criterion; replaced with metadata field)

7. **Drop Pattern 12 ("Compliance regime as precondition") as a precondition; demote to one criterion per lane.** The precondition framing implies hard-gating which the substrate does not actually do during shape-only mode. Make it explicit: one criterion, may cap, that's all.

Total cuts: 12 criteria + 1 mechanism + 1 architectural pattern. Spec goes from 107 → ~95, with the dropped criteria being precisely the ones with the weakest evidence.

---

## 6. What I'd add

1. **Negative controls in V1-V7.** Each V-test gets a paired "clean artifact → no cap" run with the same fixture. Cap false-positive rate must be ≤ 5% before promotion.

2. **Shadow-rubric mode.** Score both the v007 rubric and the v008 rubric on the same fixture for the first 4 weeks. Frontier composition comparison; only switch primary if v008 produces a measurably different frontier with non-degenerate scores.

3. **Cross-family agreement check per new criterion.** Wire `judge_calibration.py` to score every new criterion under Claude + Codex. Criteria with cross-family disagreement above threshold get demoted to "informational" (no composite weight).

4. **Cap precedence rules.** Explicit document: if AUTO-CAP at 1 (IMG-3) and AUTO-CAP at 4 (compliance) fire on the same artifact, what is the final score? Spec is silent.

5. **Score-distribution invariant.** Before promoting any new rubric, compute the distribution of composite scores on the calibration corpus. If variance shrinks (criterion bloat → composite compression), abort.

6. **Pre-population fail-loud, not abstain.** If `voice_persona.corpus_path` is missing for an article fixture, the substrate refuses the fixture, not the judge abstains the criterion. Move the gate up.

7. **Cost projection.** Real numbers: 107 criteria × N fixtures × 4 variants × 30 generations × dollar/call. The master spec mentions "doubles judge cost per fixture" only in the review prompt; the spec itself doesn't have a cost section. The operator deserves the number.

---

## 7. Verdict

**Revise. Do not ship as-is. Do not scrap.**

The spec contains 3-5 genuinely good additions (X-9, MON-9, MA-9, possibly IMG-3) and a substantial amount of speculative bolt-on that was inferred from external research rather than from observed gaps in the current rubric.

Concrete revision path:

- **Phase E (1 week):** Replace Phase C with actual rubric calibration analysis on the v006/v007 archive. Compute composite distribution per lane. Identify criteria with low variance (= compressed, candidate for cut). Identify criteria with cross-family disagreement (= judge-dependent, candidate for cut). This is the empirical work Phase C did not do.

- **Phase F (1 week):** Re-write master-spec as a *cut* exercise. Default: existing 7 lanes get +0 criteria except where Phase E or Phase C produced clear-evidence cases (X-9, MON-9, MA-9). New lanes get *minimum-viable* rubrics (3-4 criteria each — anchored to the simplest existing lane precedent). Compliance regime ships content-first, criteria-second. Voice fidelity ships single-shot, rolling-window in v1.5.

- **Phase G (the rest of the demo window):** Build the Klinika + DWF deliverables against the minimum-viable rubric. Watch the operator's actual feedback. Add criteria only on observed failures.

The spec author asked for a hostile read. The hostile read is: 80% of this spec is well-meaning research-grounded ornamentation around a 20% kernel of real validated additions. The operator's 1-2 month demo window cannot afford the 80%, and the 80% is also where most of the spec's epistemic risk lives (shape-only mode, rolling-window theatre, vision-judge tells, AUTO-CAP collisions, design-pattern lock-in).

The 20% kernel is good and should ship.

---

## Files referenced

- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/brainstorms/2026-05-12-judge-design-deep-research/phase-c-variant-ratings.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-rubrics/article_engine.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-rubrics/image_engine.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-rubrics/ad_engine.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/judge_calibration.py` (existing 2026-04-23 drift-detection mechanism the spec doesn't acknowledge)
