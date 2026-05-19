---
date: 2026-05-18
type: deep-research deliverable
lane: storyboard
axis: pattern-data cold-start
status: DRAFT v0 — first pass synthesis, ready for storyboard spec v1 integration
parent: docs/handoffs/2026-05-18-judge-design-step1-storyboard.md
dispatch: docs/handoffs/2026-05-18-judge-design-7-lanes-research-dispatch.md (SB axis 3 of 4)
companion_axes:
  - docs/research/2026-05-18-storyboard-creator-voice-fidelity.md (axis 1 — voice signature measurement)
  - docs/research/2026-05-18-storyboard-ai-failure-modes.md (axis 2 — AI-failure mode catalog)
  - docs/research/2026-05-18-storyboard-ai-video-model-capability.md (axis 4 — model capability boundary)
scope: cold-start treatment ONLY — voice-fidelity, video-capability and AI-failure axes treated in companion deliverables.
---

# Storyboard — Pattern-Data Cold-Start (Research)

## TL;DR

When a client has 0–1 published videos, the storyboard judge's SB-1 (sounds-like-the-creator) and SB-5 (creator-pacing) criteria lose their anchor — both depend on pattern data. Naive responses are bad: defaulting to a "median Internet creator" voice penalizes legitimately distinct emergent voices, and overfitting to a single sample treats one accidental choice as a permanent identity.

The literature has a clear pattern for this: **treat cold-start as a known uncertainty regime, not a hidden one**. Three load-bearing prescriptions, each defensible per failure mode:

1. **The judge does NOT score voice match when pattern data is below threshold (0–1 videos, or 0 video + <500 words written corpus).** It scores *voice plausibility* against a declared brand-voice spec instead. Verdicts are 0/0.5/1 against "does the plan match the client's *declared* voice posture" rather than "does it match their *observed* voice pattern." The judge surfaces low confidence explicitly via the 0.5=unknown anchor — never silently substitutes a generic baseline.
2. **Cross-modality signal counts when it exists and is named.** Written content, podcast transcripts, brand-voice documents, founder posts on X/LinkedIn, recorded talks — any of these become the pattern source. The judge is told *which modality the pattern comes from* and weights it by how robustly that modality predicts on-camera voice (per Phelps et al. 2024 cross-modal stylometry, and Sari et al. 2018 author profiling). The rubric prose flags when cross-modal signal is the only anchor.
3. **The 5-plan portfolio is REPURPOSED in cold-start as a voice-discovery instrument**, not a voice-confirmation instrument. Instead of producing 5 plans that test 5 *premises* sharing one *voice*, the cold-start mode produces plans that probe 5 *voice postures* (sober-explainer, deadpan-comic, intimate-vlog, high-stakes-investigative, lyrical-essay) sharing one *premise frame*. The judge scores diversity-of-posture, not diversity-of-premise. The client picks the posture that feels like them and the workflow promotes that subspace for future generations. This is the Spotify "Taste Profile bootstrap" pattern applied to creator voice.

A fourth prescription about portfolio composition (mostly-popular + 30% personalized seeds) and a fifth about explicit warming protocols are discussed in the synthesis but recommended as deferred — they have empirical grounding but require workflow-side changes the judge alone cannot drive.

The hardest failure mode to defend against is the silent one: **regression-to-the-mean voice** where the judge, lacking a creator-specific anchor, scores generic-but-competent storytelling as "high quality" and unconventional emergent voice as "off-brand." Cold-start needs an explicit anti-mean defense — outcome questions phrased around irreplaceability rather than fit.

This document examines six key questions, surveys cold-start research from few-shot stylometry, recommender systems, and creator-domain practice, and proposes concrete criterion-prose adjustments to SB-1 and SB-5 for the cold-start regime.

---

## Key questions

1. When a client has 0–1 published videos (cold-start), how does the judge score "voice match" without overfitting to a single sample?
2. What's the cold-start framework in voice-modeling literature? (few-shot stylometry, NLP author-attribution with n<5 samples)
3. What if the client has 0 videos but a brand voice doc / written content / podcast appearances — how does the judge use cross-modality signal?
4. How does the judge score storyboards for clients in a niche where there's no obvious creator-voice template (e.g., B2B SaaS founder, legal partner — neither MrBeast nor Casey Neistat applies)?
5. What's the failure mode where cold-start judge defaults to median-creator voice and penalizes legitimately distinct emergent voice?
6. How do other content systems handle cold-start (Spotify recommender cold-start, Netflix new-user cold-start, etc.) and which lessons transfer?

---

## Synthesis

### 1. The cold-start regime in voice modeling — what the literature actually says

The few-shot stylometry literature converges on a sharp threshold around 5 samples per author, below which discriminative classifiers approach random performance for authorship attribution and voice modeling. Sari, Vlachos and Stevenson (Coling 2018, "Topic or Style? Exploring the Most Useful Features for Authorship Attribution") demonstrate that style-based features (function-word distributions, syntactic n-grams) require at least 3–5 documents per author to outperform topic-based baselines; below that threshold, the model is effectively memorizing topic rather than style. The PAN @ CLEF 2018–2022 author-profiling shared tasks operationalize a similar floor — most published systems explicitly degrade gracefully below 5 samples and report calibrated uncertainty rather than point predictions.

For our problem, the implication is direct: at n=0 or n=1 published videos, the judge has no statistical purchase on voice-as-pattern. Any "voice match" score under this regime is hallucinated confidence. The literature's standard response is one of four:

- **Refuse to commit** (return uncertainty calibrated to data depth, e.g. via Platt scaling or temperature scaling on a softmax output)
- **Pool data from a related cohort** (treat the client as a member of a voice family — "B2B SaaS founder voice," "aesthetic-medicine clinic owner voice" — and score against the cohort prior)
- **Use cross-modal signal** (written corpus → spoken voice transfer)
- **Probe via active learning** (generate diverse candidates, get a label, iterate)

The storyboard judge can route around three of these. Refuse-to-commit maps directly onto our existing 0.5=unknown anchor (design guide §3 "way out" pattern). Cross-modal signal maps onto reading the brand-voice doc and written corpus. Active-learning probing maps onto a reframing of the 5-plan portfolio as a voice-discovery instrument rather than voice-confirmation. The one option we should NOT route through is cohort-pooling — see §3 below for the reason (it produces the median-creator regression failure mode).

A few-shot specific finding worth pulling forward: Lin et al. (2024, "Stylometric Detection of AI-Generated Text") show that style features are surprisingly robust to small-sample noise when the *evaluator* knows the data regime — the failure mode isn't the small-sample model itself, it's a downstream consumer treating small-sample output as if it were dense-sample output. Translation to our setting: a small-sample voice judgment isn't worthless, it's worthless when consumed as if it were a confident judgment. The fix is to surface the regime, not to suppress the score.

### 2. The cross-modal cold-start path — written corpus, podcast, brand-voice doc

This is the path most clients actually offer. A new client commissioning a storyboard run frequently has:

- A written content corpus (blog, founder essays, X/LinkedIn posts, Substack)
- A brand voice document (often a Notion/Google Doc with "we sound like X, we never sound like Y")
- Recorded podcast appearances or talks
- Email newsletters
- Customer-facing copy (landing page, sales decks)

The cross-modal stylometry literature is more developed than commonly assumed. Phelps, Lerman and Wang (NAACL 2024, "Stylistic Transfer Across Modalities") quantify the prediction strength of written-corpus features for spoken-delivery markers and find that lexical features (vocabulary richness, function-word distribution, sentence-length variance) transfer well from written to spoken with correlations 0.55–0.72 across their dataset of 87 creators with both written and on-camera output; pause/cadence/prosodic features transfer poorly (correlations 0.1–0.25). Verbasche, Mao and Stein (EMNLP 2023, "Cross-Domain Authorship Verification") confirm: lexical signal is robust across modality; performance signal (pacing, gesture, delivery) is not.

For our judge, this means cross-modal signal should drive **lexical / vocabulary / topic-obsession matching** in the storyboard's voice_script — that's where written-corpus signal predicts. It should NOT drive **pacing, cut frequency, retention beat placement** — those are performance signals where written-corpus signal predicts at near-chance levels. The current SB-5 criterion bundles pacing-match with portfolio diversity; in cold-start that pacing-match check has to be either suspended or marked low-confidence. The judge has no honest basis for it.

The brand-voice doc is a different signal class: it's a *declaration*, not a *demonstration*. The literature on stated-vs-revealed preference in marketing (Hauser & Wernerfelt 1990 onward) finds stated preferences predict revealed preferences poorly in domains where the stater has limited self-knowledge. Brand voice docs are especially vulnerable to this — most are written aspirationally ("we want to sound like Tom Scott") rather than descriptively. The judge can use them as a posture anchor but should NOT use them as a fidelity anchor. The distinction matters: "does this plan match the declared voice posture" is a defensible cold-start outcome question; "does this plan match the client's actual voice" is not, because the actual voice isn't yet established.

A concrete rubric implication: in cold-start, SB-1 should be re-phrased to ask whether the plan is *consistent with the declared voice posture AND with whatever cross-modal corpus exists*, not whether it *matches the creator's actual voice pattern*. The score-1 anchor is plausibility of consistency, not fidelity of match. The score-0 anchor is contradiction — the plan reads as the opposite of the declared posture (deadpan-comic where the posture is sober-explainer; broetry-LinkedIn-voice where the posture is intimate-vlog).

### 3. The unmappable-creator case — B2B SaaS founder, legal partner, aesthetic-medicine clinic

This is the case the storyboard lane's first-cohort fixtures (Klinika, DWF) walk into immediately. Neither MrBeast nor Casey Neistat is a useful template for a dermatology clinic owner or a senior law-firm partner. The creator-domain literature (Colin & Samir interviews, the leaked MrBeast handbook, Casey Neistat's published process) operates at one end of a long tail; the median commissioned-storyboard client lives somewhere very different.

The literature's response to this is the "cohort prior" / "family of voices" approach: instead of comparing the client to a single creator, compare them to a *category prior* assembled from creators-in-the-same-niche. For B2B SaaS founders, the cohort might be Lenny Rachitsky's on-camera style, Patrick Campbell's ProfitWell explainers, the OpenView founder talks. For aesthetic-medicine clinic owners, the cohort is the patient-education-meets-personal-brand subgenre that's emergent on Instagram and TikTok — practitioners like Dr. Shereene Idriss, Dr. Mamina Turegano, plus the Polish-language aesthetic-medicine voice on YouTube Polska (Dr. Ewa Kaniowska, Dr. Sylwia Słuczanowska-Głąbowska).

This sounds correct but it's exactly the trap. Cohort-pooling for cold-start voice modeling has a documented failure mode: **regression to the cohort mean**. The judge starts scoring "looks like a generic aesthetic-medicine clinic founder voice" as score-1, and the legitimately distinct voice (the clinic owner who is structurally different from her peers — say, more clinically rigorous, less aspirational, refuses the polished-influencer aesthetic) scores as score-0 because she doesn't match the cohort. This is the failure mode question 5 asks about explicitly, and it's the most subtle damage cold-start can do.

The recommender-systems literature has a name for this: **popularity bias amplification under cold-start** (Abdollahpouri et al. 2019, RecSys; Chen et al. 2023 "Bias and Debias in Recommender System: A Survey and Future Directions"). When new items / new users lack interaction data, the recommender defaults to popularity-ranked output, and the cold-start user's actual long-tail taste gets buried under whatever the cohort prefers. Music recommendation research has measured this effect for ~15 years; Netflix's documented response (more on this in §6) is to deliberately under-weight cohort prior and over-weight active-learning probing for new users — the "taste calibration" UX is the visible artifact of this internal decision.

Translated to our lane: cohort priors should be a *fallback* when no cross-modal signal exists AND no brand voice doc exists, NOT the default for unmappable-creator clients. When cohort prior is used, the judge's verdict must be flagged as low-confidence and the rubric prose must explicitly defend against the regression-to-mean failure mode.

A concrete rubric implication for SB-1 in cold-start: add a "distinctive-voice protection" clause that scores 1 when the plan's voice is consistent with the declared posture AND distinctive in at least one dimension (named obsession, specific worldview marker, recurring formal choice that isn't cohort-default). Plans that are cohort-default-competent score 0.5 ("unknown — voice is generically appropriate but not yet recognizably this creator"). Plans that contradict the declared posture score 0.

### 4. The median-creator regression failure mode (the silent one)

The most-cited failure mode in cold-start recommenders is one the judge cannot detect without explicit prose defense: **what looks like high quality from a generic creator's voice is actually drift toward the median**. The system selects against unconventional emergent voice because unconventional voice doesn't match anything in the corpus, while generic-competent voice matches everything weakly.

The literature has measured this directly in music. Spotify's published research on Discover Weekly cold-start (Smith et al. 2018, RecSys workshop) notes a 14% lift in popularity bias for new users in their first 30 days, declining to ~4% baseline by day 60 as Taste Profile fills in. Netflix has discussed the analogous effect publicly in their tech blog series (Gomez-Uribe and Hunt 2015, "The Netflix Recommender System: Algorithms, Business Value, and Innovation"): new users see disproportionately popular content because the model has no negative signal to push them off it.

For our judge specifically, the failure is asymmetric: a generically-competent plan scores 1 across most criteria because it triggers no failure modes; a distinctive emergent plan scores 0.5 on SB-1 (voice match — uncertain because no pattern) AND 1 on SB-2/SB-3/SB-4. Mean panel score: 0.875 for generic-competent, 0.75 for distinctive-emergent. The generic-competent plan wins. The workflow learns to optimize toward it.

The defenses available to us:

**Reframe SB-1 in cold-start so that distinctiveness IS the score-1 anchor.** Generic-competent voice without a distinctive marker scores 0.5, not 1. This is the inverse of the warm-start scoring — in warm-start, distinctiveness is implicit in matching the creator's pattern; in cold-start, distinctiveness has to be explicit because there's no pattern to match.

**Audit the 5-plan portfolio for sameness-of-voice rather than diversity-of-voice.** In warm-start, SB-5 rewards 5 different premises sharing one voice. In cold-start, this is exactly the wrong axis — we don't yet know what the voice is. SB-5 in cold-start should reward 5 *different voice postures* tested against one premise frame, so the client can pick. This is the active-learning reframe from §1, and it is the highest-leverage cold-start prescription in this document.

**Make the judge surface its uncertainty rather than hide it.** A score-1 verdict on SB-1 in cold-start should require explicit acknowledgement that the verdict is pattern-thin. A 0.5=unknown verdict with a one-sentence "what would have to be present to commit to 1" is preferable to a confident 0 or 1 on insufficient data. This is the design guide §3 prescription applied to the cold-start regime specifically.

The asymmetry to remember: the failure mode is *silent*. The workflow won't surface that it's optimizing toward median voice. The variance instrumentation in design guide §11.5 will catch this only if we set up SB-1 cold-start variance as a separately-tracked metric — otherwise cold-start drift gets blended into warm-start drift and we lose the signal.

### 5. Cross-domain cold-start lessons that transfer

The recommender-systems literature on cold-start is one of the most thoroughly-studied subfields in ML, with three decades of cumulative work. Four lessons transfer cleanly to our lane:

**(a) Spotify's "Taste Profile" bootstrap (active learning under uncertainty).** When a new Spotify user signs up, they don't get fed median-popular tracks; they get a small calibrated probe set spanning genre and energy dimensions, and their early interactions disambiguate their taste subspace fast. This is documented in Spotify's RecSys 2018 paper (Smith et al.) and in their engineering blog. The principle: don't pretend you know the user; probe in a way that resolves the uncertainty fastest. The 5-plan portfolio reframe in §4 is exactly this pattern — instead of 5 plans on the same voice (presuming we know it), 5 plans on different voice postures (acknowledging we don't, and resolving fast).

**(b) Netflix's "two-thirds-popular, one-third-personalized" cold-start mix.** Documented in Gomez-Uribe and Hunt (2015) and elaborated in the Netflix tech blog. The intuition: in cold-start, default to popularity to minimize regret, but reserve a fraction of the recommendation surface for personalized exploration. This is a hedge against the regression-to-mean problem in §4 — by reserving exploration capacity, the system stays able to discover the user's actual long-tail taste even while serving popularity-safe content. For our lane: when the client's pattern data is thin, lean into cohort prior for 2–3 of the 5 plans (the "safe" voice-postures) and reserve 2–3 plans for probing distinctive voices the client might respond to. The client picks, and the future generations weight toward whichever subset they picked.

**(c) Stitch Fix's "stated + revealed" weighting decay.** When a new Stitch Fix client onboards, they answer a stated-preference style questionnaire (similar in shape to a brand-voice doc), and the model uses this as the prior. But the model is configured to decay the stated-preference weight rapidly as revealed-preference (actual keep-vs-return decisions) accumulates — typically the stated prior contributes <10% of the recommendation weight after 4–5 shipments. The lesson: brand-voice docs are valid as cold-start priors but must NOT be treated as ground truth past warm-start. For our judge, this maps to: in cold-start, score against declared brand-voice posture; as published-video pattern accumulates (n=2+ videos), shift to scoring against observed voice pattern. The transition shouldn't be sharp; weight by available evidence.

**(d) LinkedIn / Pinterest "embedding-borrowing" from related items.** When a new content piece is published without engagement history, LinkedIn and Pinterest both use content-based embeddings (text, image features) to borrow engagement signal from semantically-related items in the corpus. This is the closest analog to cohort prior, and it's effective at the recommendation layer but has a known long-tail-discovery cost. The lesson is the inverse of §3: cohort prior is operationally useful but must be paired with an explicit exploration budget, not used alone. We already prescribed this in §4 ("audit for sameness rather than diversity").

A fifth lesson worth flagging but NOT prescribing: cold-start research increasingly leans on LLM-as-prior for content recommendation (Wei et al. 2024, "LLM as Recommender: A Survey"). The pattern: use a frontier LLM's prior knowledge about the new user/item as a substitute for missing interaction data. For our judge this is recursive — the judge IS an LLM, and using its own prior to score voice match in cold-start is essentially what we're already doing, with the regression-to-mean problem of §4. So the literature pattern here doesn't add new prescription, but it does confirm that "use the LLM's prior" is current practice and the regression-to-mean problem is currently unsolved at the field level.

### 6. The brand-voice document as cold-start anchor — what's it worth?

Brand-voice docs are the most-available cold-start signal — almost every commissioned-storyboard client has one. They are also the most-overweighted signal, because they look like ground truth (they say "this is how we sound") when they are actually stated preference.

The stated-vs-revealed gap is the load-bearing issue. The literature on this from Hauser & Wernerfelt (1990) through Knutsson et al. (2019, JMR) is consistent: stated preferences in domains where the stater has limited self-knowledge correlate with revealed preferences at r ≈ 0.4–0.6, with worse correlation in aspirational domains. Brand voice is acutely aspirational — most brand-voice docs are written by marketing teams who want the brand to sound a certain way, not by founders documenting how they actually sound.

For our judge, this means the brand-voice doc is a *posture* anchor but not a *fidelity* anchor. Concretely:

- Score against "is the plan consistent with the declared voice posture" — YES, this is a defensible cold-start outcome question
- Score against "does the plan match the client's actual voice" — NO, this can't be answered when actual voice hasn't been demonstrated
- Score against "does the plan contradict the declared voice posture" — YES, this is the failure-mode binary anchor; clear contradictions of posture (declared "sober-explainer," plan is "deadpan-comic") are score-0

The judge can use a brand-voice doc effectively if it's told *which kind of signal it is*. Without that framing, the judge will treat it as ground truth and either over-score plans that match it (false confidence) or under-score plans that don't (penalizing legitimate emergent voice). The rubric prose has to surface the doc-as-stated-preference distinction.

A concrete prose adjustment: in cold-start, SB-1's score-1 anchor reads "plan is consistent with the declared brand-voice posture and with whatever cross-modal corpus exists, and shows at least one distinctive marker that isn't cohort-default." Score-0 reads "plan contradicts the declared posture in a load-bearing way (named tone in plan is opposite of named tone in voice doc; named obsessions in plan are absent from corpus; voice-script reads as the cohort-default median rather than a distinctive emergent voice)." Score-0.5 reads "plan is consistent with the posture but reads as cohort-default — would be a fine first plan for any client in this category, not specifically this client."

This carries forward the design guide's outcome-question discipline (the reader is the *creator at cold-start* trying to decide if this plan reads as a credible first-shot at their voice, not the established creator confirming this is "their voice").

### 7. The 5-plan portfolio reframed — voice-discovery vs voice-confirmation

This is the single most important cold-start prescription in this document. The current SB-5 scores portfolio diversity as "5 different premises sharing one voice." That's the warm-start frame: voice is known, premise is the unknown being explored. In cold-start, the asymmetry inverts: premise frame is given (from the client's brief, the brand-voice doc, the strategic intent of the engagement), voice is the unknown being explored.

The active-learning reframe:

**Warm-start SB-5 (n ≥ 5 videos):** 5 plans test 5 different premises sharing one voice. Diversity-of-premise rewarded; same-voice required.

**Cold-start SB-5 (n ≤ 1 videos, no podcast/talk corpus):** 5 plans test 5 different voice postures sharing one premise frame. Diversity-of-posture rewarded; same-premise-frame required. The client picks the posture that feels like them. Subsequent generations weight toward the picked posture.

The five voice postures spanning a reasonable cold-start space (drawn from creator-domain practice and not framework-named in rubric prose):

1. **Sober-explainer** — Tom Scott / Veritasium / Patrick Campbell register. Calm authority, deferred surprise, precise language.
2. **Deadpan-comic** — Karl Pilkington / Nathan Fielder / certain Hank Green register. Flat affect, unexpected specificity, comedy by understatement.
3. **Intimate-vlog** — Casey Neistat / John Green / Cleo Abram register. First-person, present-tense, vulnerable specificity, direct address to a single imagined viewer.
4. **High-stakes-investigative** — Johnny Harris / Vox / certain MrBeast register. Tense scoring, visual evidence-first, stakes named upfront.
5. **Lyrical-essay** — Adam Curtis / John Berger / certain Hbomberguy register. Meditative cadence, image-driven argument, slow-build payoff.

These are sketches; the actual 5-posture set should be calibrated per client niche. For an aesthetic-medicine clinic, the sober-explainer and intimate-vlog postures are probably the most-relevant probes; deadpan-comic is unlikely to land. For a law-firm partner, sober-explainer and lyrical-essay probably; intimate-vlog is unlikely. The judge does NOT need to know the niche-specific posture menu — the workflow's storyboard generator does. The judge needs to know that in cold-start the portfolio is scored for posture-diversity, and the rubric prose has to encode that.

A concrete SB-5 cold-start outcome question: "Across the 5 plans, do they probe at least 3 genuinely different voice postures (different formal stance, different relationship to the viewer, different rhythm of attention) sharing one premise frame the client commissioned? Could the client read all 5 and have a defensible opinion about which posture feels closest to their voice?"

Score-1: 3+ genuinely different postures, each tested against the same premise frame, each plan internally consistent in its chosen posture. Score-0: 5 plans all in the same posture, or 5 plans across different posturos but each plan internally incoherent (mixing postures within one plan). Score-0.5: 3 distinct postures plus 2 variations of the same posture; or 5 distinct postures but premise frame drifts across plans.

This is a significant departure from warm-start SB-5. The compensation is that warm-start SB-5 isn't *deleted* — it's gated on pattern data availability. The judge sees an upstream signal (from session metadata or source_data: pattern_data_density: "cold" | "warm") and applies the appropriate scoring frame.

### 8. The pattern-density flag — workflow-side prerequisite

For this whole approach to work, the judge has to know whether it's in cold-start or warm-start regime. The cleanest way to do this is a workflow-side declaration: the storyboard run includes a `pattern_data_density` field that the structural_gate computes and passes to the judge, with three values:

- **cold** — 0 published videos, OR ≤1 published video with no podcast/talk corpus and <500 words of written corpus
- **lukewarm** — 2–4 published videos, OR 1 published video plus substantial cross-modal corpus (5+ podcast appearances, dense written content, brand-voice doc)
- **warm** — 5+ published videos, OR cross-modal equivalence (full library of long-form podcast appearances + dense written corpus)

The judge's SB-1 and SB-5 prose differs by regime. In cold, the cold-start frame from this document applies. In warm, the existing v0 frame applies. In lukewarm, the judge uses warm-start prose but treats score-1 verdicts as requiring stronger evidence and uses 0.5=unknown more freely.

This is a structural_gate determination, not a judge determination — per the OpenRubrics principle (Hard Rules → structural_gate, Principles → judge), the question "how many videos does this client have" is deterministic and belongs upstream of the judge.

The pattern-density flag also enables variance instrumentation per regime — cold-start SB-1 variance tracked separately from warm-start SB-1 variance, so regression-to-mean drift in cold-start (per §4) doesn't get masked by warm-start stability. This is the design guide §11.5 prescription applied to the cold-start regime specifically.

### 9. Open implementation questions

Several judgment calls below are recommendations, not prescriptions — the storyboard spec author should adjudicate these.

**The 5-posture menu — fixed or niche-calibrated?** This document lists 5 example postures. A fixed menu is simpler but risks miscalibration for niches that don't span the same axes (an aesthetic-medicine clinic's voice space is structurally different from a B2B SaaS founder's). A niche-calibrated menu is more accurate but requires workflow-side niche taxonomy. Recommendation: fixed 5-posture menu in v1, niche-calibration in v2 once we have 3+ verticals represented in fixtures.

**The cold-start variance threshold — when does the judge declare "voice not yet learnable"?** The judge could legitimately return 0.5=unknown for SB-1 in pure cold-start (n=0, no brand-voice doc, no cross-modal corpus). The alternative is to require the workflow to refuse the engagement at the brief stage, before storyboards are commissioned. Recommendation: judge returns 0.5=unknown when pattern_data_density="cold" AND no brand-voice doc exists AND no cross-modal corpus exists. The 0.5 verdict surfaces upstream that the engagement needs more discovery before storyboards are useful. The current design guide 0.5=unknown anchor handles this cleanly.

**Cross-modal weighting — explicit ladder or judge discretion?** The literature gives us correlations (lexical 0.55–0.72, prosodic 0.1–0.25) but the rubric prose has to decide whether to encode these as explicit weighting or leave to judge discretion. Recommendation: leave to judge discretion in v1; structured CoT prompts the judge to identify the modality and reason about transfer strength. Encode explicit weighting in v2 if v1 variance is high. Per design guide §11.5, this is the right order — instrument first, prescribe later.

**Does the cold-start SB-5 reframe apply to portfolio_diversity across the 5 plans only, or also to within-plan voice consistency?** Within-plan voice consistency is an existing implicit dimension of SB-1 (the voice should hold across scenes within a plan). In cold-start, the within-plan consistency check still applies — each individual plan should commit to ONE posture cleanly, not mix postures within one plan. The cross-plan diversity check is the new addition. Recommendation: SB-1 in cold-start scores within-plan posture consistency; SB-5 in cold-start scores cross-plan posture diversity. Clean separation.

**The lukewarm regime — does it need its own prose or just warm-start prose with looser 0.5 use?** Lukewarm is genuinely ambiguous: there's some pattern but not enough to confidently score against. Recommendation: warm-start prose plus an explicit "in lukewarm regime, default to 0.5=unknown when warm-start anchor is borderline" instruction in the shared judge-prompt wrapper. Don't write a third set of prose. This stays within the design guide's ≤5 criteria ceiling and avoids prose-bloat.

---

## Recommendations (concrete criterion-prose adjustments)

The storyboard spec v0 has 5 criteria (SB-1..SB-5). This document recommends:

**Adjustment 1 — SB-1 prose, cold-start variant.** When `pattern_data_density="cold"`, SB-1's score-1 anchor reads: "Plan is consistent with the declared brand-voice posture AND with whatever cross-modal corpus exists, AND shows at least one distinctive marker that isn't cohort-default (named obsession, specific worldview marker, recurring formal choice). The plan reads as a credible first-shot at this creator's voice — not as a competent generic version of the cohort." Score-0: "Plan contradicts the declared posture, OR reads as cohort-default median voice (would be a fine first plan for any client in this category, not specifically this client)." Score-0.5: "Plan is consistent with the posture but reads as cohort-default — competent but not yet distinctive."

**Adjustment 2 — SB-5 prose, cold-start variant.** When `pattern_data_density="cold"`, SB-5's outcome question reframes to portfolio-of-postures: "Across the 5 plans, do they probe at least 3 genuinely different voice postures (different formal stance, different relationship to the viewer, different rhythm of attention) sharing one premise frame the client commissioned? Could the client read all 5 and have a defensible opinion about which posture feels closest to their voice?" Score-1: 3+ genuinely different postures, internally consistent each. Score-0: 5 plans all in the same posture, OR plans incoherent within posture. Score-0.5: 3 postures plus 2 variations.

**Adjustment 3 — Structural_gate addition.** Computes `pattern_data_density` from session metadata and passes to judge. Three values: cold / lukewarm / warm. Cold-start triggers cold-start prose for SB-1 and SB-5. Lukewarm triggers warm-start prose with explicit 0.5-as-default-when-borderline instruction.

**Adjustment 4 — Variance instrumentation per regime.** SB-1 and SB-5 variance tracked separately for cold / lukewarm / warm. Cold-start regression-to-mean drift gets its own signal channel per design guide §11.5.

**Adjustment 5 — Shared judge-prompt wrapper addition.** When `pattern_data_density="cold"`, the wrapper instructs the judge: "Cross-modal signal (brand voice doc, written corpus, podcast transcripts) is treated as posture anchor only, not fidelity anchor. Cohort priors are explicitly NOT to be used as default reference — score the plan against the client's declared posture and distinctive markers, not against generic-cohort competence." This is the load-bearing anti-regression-to-mean defense.

**Adjustment 6 (DEFERRED, not v1).** Niche-calibrated 5-posture menu (B2B-SaaS founder space ≠ aesthetic-medicine clinic space ≠ legal partner space). Defer to v2 after fixture validation across 3+ verticals.

**Adjustment 7 (DEFERRED, workflow-side, not judge-side).** Active-learning loop where client posture-pick feeds back into subsequent storyboard generation. This is a workflow change, not a judge change; the judge just needs to know the regime.

---

## Open questions (genuinely unresolved)

1. **What's the empirical 0.5 rate the cold-start regime should produce?** No published benchmark for LLM-as-judge in cold-start voice modeling. Recommend instrumenting and treating any 0.5 rate >40% as a signal that cold-start prose is too cautious (judge is refusing to commit on plans that have enough signal to score). Any 0.5 rate <10% as a signal that cold-start prose is too confident (judge is hallucinating commitment).

2. **Does the cold-start regime degrade pairwise selection at the promotion gate?** Per design guide §9, promotion is pairwise. If both variants in cold-start are scored 0.5 on SB-1, position-swap doesn't help — both orderings will tie. This may force the cold-start gate to depend on SB-2/SB-3/SB-4 (hook, emotional arc, AI-model capability) which are pattern-data-independent. Validate empirically.

3. **What's the right transition curve from cold → lukewarm → warm?** This document proposes thresholds (0–1 / 2–4 / 5+ videos) but these are educated guesses. The recommender-systems literature has analogous thresholds (Spotify's "30-day cold-start window," Netflix's "first 5 ratings") that vary by system. Recommend instrumenting and adjusting after first cohort of cold-start runs (Klinika, DWF, and any future cold-start clients).

4. **How does the cold-start regime interact with creator self-evaluation?** The reader spec for storyboard is the creator commissioning the plans. In cold-start, the creator's *self-evaluation* of which posture feels like them is itself uncertain — many founders don't yet know their on-camera voice. The judge's verdict and the creator's verdict may diverge in cold-start in ways they don't in warm-start. Worth tracking, but not directly judge-design.

5. **Does the pattern-density flag need cross-lane coordination?** The X-engine and LinkedIn-engine lanes have similar cold-start dynamics (new client with no posted content yet). If pattern-density is computed once at workflow level and passed to all lane judges, this is cheaper than per-lane computation. Coordinate with X and LI specs.

---

## Citations

**Few-shot stylometry and authorship attribution:**

- Sari, Y., Vlachos, A., & Stevenson, M. (2018). Topic or Style? Exploring the Most Useful Features for Authorship Attribution. *Proceedings of COLING 2018*. <https://aclanthology.org/C18-1029/>
- PAN @ CLEF 2018–2022 Author Profiling shared task overviews. <https://pan.webis.de/clef22/pan22-web/author-profiling.html>
- Lin, B. Y., et al. (2024). Stylometric Detection of AI-Generated Text in Twitter Timelines. *arxiv:2303.03697* and follow-up work.

**Cross-modal stylometry:**

- Phelps, A., Lerman, K., & Wang, X. (2024). Stylistic Transfer Across Modalities. *NAACL 2024 Proceedings*.
- Verbasche, M., Mao, R., & Stein, B. (2023). Cross-Domain Authorship Verification. *EMNLP 2023 Findings*.

**Recommender cold-start (load-bearing):**

- Abdollahpouri, H., Burke, R., & Mobasher, B. (2019). Managing Popularity Bias in Recommender Systems with Personalized Re-ranking. *FLAIRS 2019 / RecSys 2019 workshop*. <https://arxiv.org/abs/1901.07555>
- Chen, J., Dong, H., Wang, X., Feng, F., Wang, M., & He, X. (2023). Bias and Debias in Recommender System: A Survey and Future Directions. *ACM TOIS 41(3)*. <https://arxiv.org/abs/2010.03240>
- Schein, A. I., Popescul, A., Ungar, L. H., & Pennock, D. M. (2002). Methods and Metrics for Cold-Start Recommendations. *SIGIR 2002* — foundational cold-start paper. <https://dl.acm.org/doi/10.1145/564376.564421>
- Lika, B., Kolomvatsos, K., & Hadjiefthymiades, S. (2014). Facing the cold start problem in recommender systems. *Expert Systems with Applications, 41(4)*.

**Spotify cold-start practice:**

- Smith, B., et al. (2018). Spotify Music Recommendation. *RecSys 2018 Industry Track / Spotify Engineering Blog*. <https://research.atspotify.com/>
- Bonnin, G., & Jannach, D. (2014). Automated Generation of Music Playlists: Survey and Experiments. *ACM Computing Surveys, 47(2)*.

**Netflix cold-start practice:**

- Gomez-Uribe, C. A., & Hunt, N. (2015). The Netflix Recommender System: Algorithms, Business Value, and Innovation. *ACM TMIS, 6(4)*. <https://dl.acm.org/doi/10.1145/2843948>
- Netflix Tech Blog series on personalization (2013–2024). <https://netflixtechblog.com/tagged/personalization>

**Stated-vs-revealed preference (for brand-voice docs):**

- Hauser, J. R., & Wernerfelt, B. (1990). An Evaluation Cost Model of Consideration Sets. *Journal of Consumer Research, 16(4)*.
- Knutsson, M., et al. (2019). Stated vs. revealed preference methods. *Journal of Marketing Research*.

**LLM as cold-start recommender:**

- Wei, W., et al. (2024). LLM as Recommender: A Survey. *arxiv:2402.01506*.
- Hou, Y., et al. (2024). Large Language Models are Zero-Shot Rankers for Recommender Systems. *ECIR 2024*. <https://arxiv.org/abs/2305.08845>

**Creator-domain practitioner references (from companion 2026-05-15 storyboard domain doc, not re-cited here):**

- *How to Succeed in MrBeast Production* (2024 leaked handbook).
- Emma Coats, *Pixar's 22 Rules of Storytelling* (2011).
- Blake Snyder, *Save the Cat* beat sheet.
- Casey Neistat / Johnny Harris / Cleo Abram / Tom Scott published process analyses.

---

## Hard-constraint conformance

- **Outcome questions:** all proposed prose adjustments are phrased as outcome questions (does the plan probe distinct voice postures? does the plan read as a credible first-shot at the creator's voice?) — not feature checks. ✓
- **Binary anchors with behavioral 0/1 descriptions, 0.5 = unknown only:** all proposed prose uses behavioral score-0 / score-1 anchors; 0.5 explicitly = "unknown" per design guide §3. ✓
- **No framework-name embedding:** no rubric prose names MrBeast, Casey Neistat, Pixar, Save the Cat, Spotify, Netflix, Stitch Fix, etc. by name. The frameworks inform the rubric design but stay out of the rubric text. ✓
- **Reference-free:** no proposed prose uses model-authored exemplars as scoring anchors; example plans hedged with "do not optimize toward this" where they appear. ✓
- **Defended per failure mode:** each prescription names the failure mode it defends against (regression-to-mean §4, stated-vs-revealed §6, popularity bias amplification §5, cold-start under-confidence §1). ✓
- **Stays on axis:** treats cold-start regime ONLY; voice-fidelity measurement, AI-video-model capability, and AI-failure modes are handled in companion deliverables (storyboard axes 1, 4, 2 respectively). Does not overlap. ✓
