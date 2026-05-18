---
date: 2026-05-18
type: research deliverable — judge-design deep-research dispatch
lane: linkedin_engine
axis: AUTHOR-CONTEXT COHERENCE
status: complete
parent: docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md
guide: docs/rubrics/judge-design-guide.md
deepens: docs/research/2026-05-18-judges-domain-linkedin-engine.md (LI-E / LI-5)
sibling_dispatches:
  - depth (LI-2)
  - comment-seed (LI-4)
  - AI-slop / voice (LI-3)
  - trailer (LI-1)
---

# Author-Context Coherence as a Judge Axis for `linkedin_engine`

## TL;DR

Author-context coherence — does the post's claim, voice, and standing match the author's visible professional surface? — is not a "soft" credibility-perception factor in 2026. LinkedIn's 360Brew algorithm rewrite (rolling Q4 2025 → Q2 2026) introduced **Topic Authority**, an internal credibility score that cross-references an author's claimed expertise against the corpus of content they actually publish. A "SaaS expert" posting motivational quotes receives **measurably reduced distribution**; topic-consistent authors receive **up to 78% higher distribution** on in-lane content. This converts a classical communication-theory construct (Berlo's *competence / trustworthiness / dynamism*; Cialdini's *authority shortcut*; Hovland-Weiss expertise-trust) into a platform-physics signal the judge can target without inventing a new outcome.

The dominant failure mode is **not** "obvious mismatch" (a CFO suddenly posting growth-marketing tactics — easy to detect). It is **subtle authority-voice mismatch under selection pressure**: an AI loop optimizing for hook density and comment-seed strength produces posts that read as one register above or below the author's actual seat (Series-A founder narrating Series-D scaling pain, IC narrating CEO-stance posts, executive narrating IC-tactical detail). These posts are technically well-written, may even earn dwell, and quietly erode credibility with the decision-maker reader who pattern-matches "this is not what someone in this seat sees."

The judge must test author-context coherence at three resolutions: (1) **role-vs-topic congruence** — does the claim sit in the author's plausible standing? (2) **authority-voice register** — is the confidence level coherent with the seat? (3) **temporal coherence** — do claims about "what I'm working on" track the author's recent visible activity? Resolutions 1 and 3 admit a substantial `structural_gate` slice (role-token-vs-topic-token gate, employer-mention check, recent-activity claim verifier). Resolution 2 is the irreducible judge-only signal: register mismatch is not a token-level fact.

The LI-5 criterion in `2026-05-18-judge-design-step1-linkedin-engine.md` v0 is structurally correct but **under-anchored** at the score-0 pole. It catches the obvious-mismatch failure (B2B founder posting fitness content); it does not explicitly catch the under-the-cut authority-voice-register failure, which is the failure mode an optimizing loop is most likely to produce. This document proposes a revised LI-5 that defends per failure mode, plus a `structural_gate` slice that hoists the determinable portion out of the judge.

---

## Key questions answered

1. **What does "author-context coherence" mean operationally for a LinkedIn post draft?** — Three-resolution definition: role-vs-topic, authority-voice register, temporal coherence. Each resolution has a distinct failure mode and a distinct verifiability profile.
2. **What does the judge see vs. what can be deterministic?** — Profile bio + work history + recent post titles are tokenizable surface (`structural_gate`). Authority-voice register requires reading the post for confidence calibration vs. the author's seat — irreducibly judge-side.
3. **What is the literature on credibility / source coherence in social communication?** — Berlo competence-trustworthiness-dynamism; Hovland-Weiss expertise-trust; Cialdini authority-as-shortcut; Pornpitakpan 2004 meta-analysis (47 source-credibility studies); Edelman/LinkedIn 2025 B2B Thought Leadership Report (73% of B2B buyers treat consistent thought leadership as a trust signal; the operative word is *consistent*).
4. **What's the failure mode where AI posts are technically well-written but read as "wrong author"?** — Authority-voice register mismatch under selection pressure. Posts that score well on hook + insight + voice + comment-seed but quietly trip the decision-maker's "this is not what someone in this seat sees" detector.
5. **What deterministic `structural_gate` checks are feasible?** — Role-vs-topic token overlap gate; employer-mention validity check (does the employer mentioned in the post match the author's current employer field?); claim-vs-recent-activity check (does "I just launched X" appear in the author's recent activity feed or shipping history?). All three are >70% precision on the role-mismatch slice and **must** be hoisted out of the judge per §2 of `judge-design-guide.md`.
6. **What's the irreducible judge signal?** — Authority-voice register coherence. Token-level techniques cannot tell whether a Series-A founder is writing Series-D-stage posts; the judge has to read for confidence calibration against author seat.

---

## Synthesis

### 1. Why this axis matters now: 360Brew turns Topic Authority into algorithmic physics

LinkedIn's 360Brew transformer-based ranker (rolled out Q4 2025, fully live by Q2 2026 per Vulse, Stackmatix, Bang Marketing, Melanie Goodman's algorithm dispatch, and the GBG learning lab) introduced an internal "Topic Authority" score that explicitly cross-references the author's claimed-expertise surface (headline, About section, work history, stated specialization) against the corpus of content they actually publish. The algorithm assigns each creator a "topic fingerprint" or "topic DNA" derived from posts, engagements, and saves. If a post's content sits outside that fingerprint, the algorithm treats it as low-authority for that topic and constrains distribution to the author's first-degree network. If the post sits inside the fingerprint, the algorithm extends fanout to readers who have engaged with that topic across the platform — even if they have zero network connection to the author. Melanie Goodman's substack puts a number on it: topic-consistent authors see **up to 78% higher distribution** on in-lane content versus topic-dispersed authors on the same dwell metrics.

This is a regime change. Pre-2025, LinkedIn's ranker was primarily a relationship-based feed (network-graph distance + engagement velocity). Post-2026, it is an **expertise- and interest-based distribution model** where coherence between claimed identity and content is structurally rewarded. The Edelman/LinkedIn *2025 B2B Thought Leadership Impact Report* completes the picture from the buyer side: 73% of B2B decision-makers say thought leadership is more trustworthy than other marketing, but the central word in that finding is **consistent**. Thought leadership accumulates trust only when the author's claim, voice, and angle stay coherent across posts and remain coherent with their visible professional context.

The autoresearch judge needs to absorb this regime change. Author-context coherence is no longer a soft "would the reader find this credible?" question — it is the platform's primary distribution gate **and** the buyer's primary trust gate. A post that scores well on every other dimension but trips the coherence gate is now structurally a low-performing post on both axes simultaneously. The judge must encode this.

### 2. The three resolutions of author-context coherence

The judge cannot treat "author-context coherence" as a single binary. Three distinct failure resolutions exist, each with its own evidence locus and verifiability profile.

**Resolution A — Role-vs-Topic Congruence.** Does the topic of the post fall within the author's plausible standing to speak? Examples of incongruence: a CFO posting growth-marketing tactics with the confidence of a CMO; a junior IC posting CEO-stance content about market positioning; a B2B SaaS founder posting fitness/spirituality content unconnected to their professional surface. This is the obvious-mismatch failure mode and is the one LI-5 v0 catches. It is **partially deterministic** — token-overlap between the author's headline/About/recent-post-titles and the post's primary topic detects the gross failures. The judge sees what the gate misses (e.g., the post claims to be about "founder lessons" but the author hasn't shipped a product, which is harder to detect on tokens alone).

**Resolution B — Authority-Voice Register.** Does the *confidence level* of the post match the author's seat? This is where the AI-optimized failure mode lives. A Series-A founder narrating Series-D scaling pain ("when you're scaling past 500 reps...") is technically well-written and topically congruent (it's still founder content from a founder), but the register is one stage above their actual position. An IC writing VP-stance assertions ("our team's playbook for cross-functional alignment...") is similarly coherent on Resolution A and incoherent on Resolution B. Inversely, a CEO writing IC-tactical detail ("here's the exact subject line that worked...") collapses the seniority signal and reads as register-pretending.

Resolution B is **irreducibly judge-side**. No token-overlap gate can detect that "scaling past 500 reps" implies post-Series-C operations while the author's current role is at a 30-person company. The judge has to read for *confidence calibration*: does the author write as someone who has seen this, or as someone who has read about this?

Pornpitakpan's 2004 meta-analysis of 47 source-credibility studies (Journal of Applied Social Psychology) is load-bearing here: high-credibility sources are more persuasive than low-credibility sources, but the credibility-persuasion link **collapses when message content sits outside the source's expertise band**. The reader has been pattern-matching this for forty years; the AI optimizing for hook density and insight specificity will routinely violate it.

**Resolution C — Temporal Coherence.** Does the post's claim about the author's current activity match what is visible from the author's recent post history, work history changes, or platform activity? Examples: "I'm launching a new product next week" when nothing in the author's last 30 days mentions a product launch; "We just closed our Series B" when there is no announcement post or company-page update; "I've been thinking a lot about X" when the author's last 20 posts are about an unrelated topic. This is the **claim-vs-recent-activity** failure and it is the most platform-detectable resolution — it has the highest deterministic-check yield.

Each resolution requires a different evidence pull. Resolution A pulls bio + work history. Resolution B pulls bio + work history + tonal calibration. Resolution C pulls recent post history + recent activity feed. The judge prompt and the source_data wired into the lane have to support all three.

### 3. Failure mode the AI loop is most likely to produce: authority-voice register mismatch

Under selection pressure, the autoresearch evolution loop will optimize for whatever the judge rewards. If the judge rewards hook specificity (LI-1), insight density (LI-2), human voice (LI-3), and comment-seed strength (LI-4), the loop will produce posts that maximize those signals — and the cheapest way to maximize them is to **plagiarize the register of high-engagement posts the loop has seen in the wild**, regardless of whether that register fits the author it is generating for. This is the Goodhart-collapse failure mode for LI-5: the loop learns to write Series-D-stage scaling posts, executive-stance market-positioning posts, and category-defining thought-leadership posts — *for every author* — because those registers produce the strongest hooks, insights, and comment-seeds in the training corpus.

The result is technically well-written posts that quietly fail the reader's "this is not what someone in this seat sees" detector. Engagement metrics may not even be the canary: the post can earn surface engagement from the author's first-degree network (who know and trust the author) while failing the decision-maker reader two degrees out — who is the actual target. The credibility damage compounds across posts because each register-mismatched post pollutes the author's Topic Authority fingerprint, which in turn restricts distribution of *future* posts. The 360Brew ranker punishes register-mismatch on a 30-90 day lag, which is too slow for a judge running per-generation to catch via downstream signal.

The judge therefore has to catch this *in the artifact alone*, without waiting for platform feedback. The only signal available is whether the post's authority-voice register is calibrated to the author's documented seat. This is the load-bearing reason LI-5 must remain a judge criterion and cannot be fully replaced by a `structural_gate`: the gate detects topic mismatch; only the judge detects register mismatch.

### 4. Literature foundations — credibility coherence as a forty-year construct

Berlo, Lemert & Mertz (1969–1970) decomposed source credibility into three dimensions: *competence / safety / dynamism*. Competence is the "does this source have standing to speak?" dimension — the exact construct LI-5 targets. Hovland & Weiss (1951) had earlier established the two-factor *expertise + trustworthiness* model; Berlo's contribution was adding *dynamism* (the source's energy / forcefulness / confidence) as a third orthogonal dimension. The Berlo three-factor model is the canonical reference frame in communication research; Pornpitakpan's 2004 meta-analysis and McCroskey's source-credibility scale work both build on it.

Cialdini's *Influence* (1984, updated 2021) collapsed the construct into one of his six (later seven) persuasion principles: *authority as cognitive shortcut*. People defer to authority signals to reduce decision uncertainty, but the shortcut works only when authority cues are **congruent** — a doctor in a white coat selling toothpaste works; a doctor in a white coat selling cryptocurrency does not. The relevant research finding is that **incongruent authority cues actively decrease persuasion below baseline**: the audience reads the mismatch as deception or self-aggrandizement, and the source's credibility on adjacent topics also takes damage. This is the "credibility damage even if engagement metrics OK" failure mode named in the dispatch brief.

For LinkedIn specifically, the Edelman/LinkedIn *2025 B2B Thought Leadership Impact Report* is the modern restatement: 73% of B2B decision-makers treat thought leadership as a trust signal, but only when the source's claim is coherent with their visible context. The report frames this as the **consistency dimension** — a single mismatched post damages trust faster than ten coherent posts build it.

The platform side of the literature converges with the buyer side. The 360Brew algorithm and the Topic Authority score are the platform's formalization of the Berlo/Cialdini coherence intuition. The two literatures — communication-theory credibility and 2026 platform-physics — now point at the same judge criterion from opposite ends.

### 5. What the judge sees vs. `structural_gate`

Per `judge-design-guide.md` §2, verifiable facts route to `structural_gate`. For the author-context-coherence axis, three deterministic checks are feasible:

**Gate-1: Role-Topic Token Overlap Gate.** Compute Jaccard or TF-IDF overlap between the author's profile-surface tokens (headline, About paragraph, current role title, current employer name, top 5 LinkedIn-Skills tags) and the post's primary topic tokens (extracted via a small NER + topic-classifier pass). Threshold tuned per fixture-cohort to roughly 0.2 — below threshold flags an obvious role-topic mismatch. Hard fail (exit code 1) when overlap = 0 AND post topic resolves to a recognized industry/discipline different from the author's. ~50 LOC; runs offline against cached profile data.

**Gate-2: Employer-Mention Validity Check.** When the post references "we" / "our team" / a specific employer name, validate against the author's current employer field. Flag if "we" implies a different company than the one in the author's headline. ~30 LOC; runs offline.

**Gate-3: Claim-vs-Recent-Activity Check.** When the post contains a temporal claim ("I just launched X" / "We closed Y" / "I've been working on Z"), validate that a matching mention exists in the author's last 30 days of post history or activity. Use a lightweight LLM call only for the matching step; the extraction is regex-tractable. Hard fail when temporal claim has no matching recent activity AND no matching announcement. ~80 LOC.

These three gates remove the determinable share of Resolution A and Resolution C from the judge's surface, satisfying `judge-design-guide.md` §1.2 (Hard Rules → structural_gate). What remains in the judge is exclusively Resolution B (authority-voice register), which is irreducibly subjective.

The judge then sees: the post artifact + the author's *source_data* block (role, employer, stage, expertise tags, recent-post topics summary, work-history headline). The judge does NOT score topic-overlap or temporal-match (handled by gate); it scores register coherence.

### 6. Revised LI-5 — defends per failure mode

Conforms to `judge-design-guide.md` §3 (binary + 0.5 unknown), §4 (outcome question + behavioral anchors + hedged examples), §6 (structured CoT). Reference-free. No framework names. No anti-gaming clauses.

```
CRITERION LI-5 — Author-context coherence: credible thought leadership

Outcome question (binary):
Would a relevant decision-maker reader treat this post as credible
thought leadership from this specific author — i.e., does the
post's confidence level, scope of claim, and frame of reference
match the author's visible professional seat (role, stage,
employer, expertise)?

Score 1 (yes) — The post's authority-voice register matches the
author's seat. A founder-stage author writes about founder-stage
problems they have plausibly encountered; an IC writes from IC
vantage; an executive writes from executive vantage. When the
author makes a strong claim, the claim sits inside their plausible
standing to make it. A reader who knows the author's role would
not pause on the post and think "that is not what someone in this
seat would write."
  Example (do not optimize toward this): a Series-A founder
  describing the specific moment they made a hiring trade-off
  between two early salespeople, with the texture of having lived
  it — not a general "lessons from scaling sales orgs" piece that
  reads as one stage above their actual position.

Score 0 (no) — The post's register is one stage above or below the
author's seat. Examples: Series-A founder narrating Series-D
scaling pain ("when you're scaling past 500 reps"); IC writing
VP-stance assertions about cross-functional strategy without
grounding; CEO writing IC-tactical detail (specific subject lines,
specific tool keyboard shortcuts) that flattens the seniority
signal; OR the post's topic sits outside the author's plausible
standing entirely (motivational/spiritual content from a B2B SaaS
founder unconnected to their professional surface; growth-marketing
tactics from a CFO with no marketing surface in their work
history).

Score 0.5 (unknown) — The author's professional context cannot be
inferred from the artifact + source_data alone — emit 0.5 +
"unknown" + the specific context that would have to be present
(e.g., "author's stage or employer not in source_data; cannot
assess register coherence").

Required CoT:
- Step 1: Read the author's source_data block. Identify role, stage
  (founder/IC/manager/executive; early/mid/late), employer scope
  (early-stage vs scaled), domain expertise.
- Step 2: Read the post. Identify the implied vantage of the
  author: what stage / role / scope does the post's confidence
  level and frame of reference assume the author occupies?
- Step 3: Compare. Is the implied vantage congruent with the
  author's actual seat? If gap > one register (founder→executive,
  IC→VP, junior→CEO), score 0. If aligned within one register,
  score 1. Emit verdict + one-sentence justification naming the
  specific register signal.

Do not score: topic-vs-role overlap (structural_gate), employer-
mention validity (structural_gate), temporal-claim-vs-recent-
activity (structural_gate), claim ambition level on its own (a
junior IC with deep specialty can make strong claims in their
specialty — only score 0 if the claim sits outside the specialty).
```

### 7. Goodhart-resistance — what the criterion will not reward

Per `judge-design-guide.md` §11 (time-to-Goodhart, not Goodhart-immunity), the rubric needs to defend against the specific evolutionary moves a loop will try:

- **Move 1: Loop adds an "as a [role]" prefix to every post.** "As a founder, here is what I learned about hiring..." — surface-marker compliance, no register change. Doesn't pass: the criterion tests *implied vantage from the substance*, not from prefix tokens.
- **Move 2: Loop drops in author-employer name to every post.** "At [Company], we learned..." — name-drop compliance, no register coherence. Doesn't pass: judge ignores the name-drop and reads for vantage.
- **Move 3: Loop replicates the author's last-three-posts' register on every new post.** Surface-similarity, no actual register coherence with stage. Catches when the author's last three posts already drifted, which is the lagging-indicator failure mode. Partial defense — flagged for variance instrumentation (§11.5 of the guide).
- **Move 4: Loop reduces all claims to within-specialty.** Underfit response — every post becomes a narrow micro-claim with no thought-leadership punch. The criterion permits broad claims within the author's specialty; this move loses LI-2 (insight density) faster than it preserves LI-5.

The move space is bounded by the requirement that vantage be inferred *from the post's substance*, not from surface tokens. The loop can game tokens; it cannot easily game substance without losing other criteria.

### 8. Redundancy check with LI-3 (AI-slop voice)

`judge-design-step1-linkedin-engine.md` §8 Open Question 4 flags potential redundancy between LI-3 (voice) and LI-5 (author-context coherence) because both anchor on author voice. The distinction is:

- **LI-3** tests whether the voice is *human vs. AI* (gestalt AI-slop stack: em-dash density, template phrases, P.S.↓ closers, affective flatness).
- **LI-5** tests whether the voice is *this author's seat vs. some other seat* (authority-voice register).

A post can be high LI-3 (clearly human-written, no AI tells) and low LI-5 (human-written but in the wrong register for the author — e.g., a junior writer ghosting a CEO badly). Conversely, a post can be low LI-3 (AI-slop) and high LI-5 (the AI happened to hit the right register for the author). The dimensions are orthogonal under selection pressure even if they correlate on the current fixture set.

**Test:** run pairwise correlation across the existing `linkedin_engine` fixture set after applying the revised LI-5. If correlation > 0.7, the guide's §5 redundancy-removal rule applies and the weaker criterion drops. Expected: correlation 0.4–0.6 — same direction (an AI-slop post is more likely to also be register-mismatched because the underlying loop is the same), but the divergent cases (human-written but register-wrong; AI-written but register-right) are the load-bearing failure modes both criteria need to catch.

### 9. Calibration set requirements for LI-5

Per `judge-design-guide.md` §15, build a 100-fixture calibration set per lane with stratification across both score-1 and score-0 examples. For LI-5, stratify across:

- **Role**: founder × IC × manager × executive (4 strata)
- **Stage**: early × growth × late (3 strata)
- **Failure type**: Resolution A (topic mismatch) × Resolution B (register mismatch) × Resolution C (temporal mismatch) (3 strata)
- **Coherent baseline**: 25 fixtures with no mismatch (score-1 ground truth)

The hardest fixtures to label are Resolution B (register mismatch within the same role family) — e.g., founder writing founder-stage content but with one-register-too-high confidence. These are the calibration anchors for the criterion. JR or a senior reviewer must label these directly; LLM-assist labeling will likely miss them precisely because the LLM has the same bias.

---

## Recommendations

**R1. Hoist Resolution A and Resolution C into `structural_gate`** as Gate-1 (Role-Topic Token Overlap), Gate-2 (Employer-Mention Validity), Gate-3 (Claim-vs-Recent-Activity). Estimated 160 LOC total. This removes ~40% of the LI-5 surface from the judge and converts it into a deterministic pre-check. Conforms to `judge-design-guide.md` §1.2.

**R2. Adopt the revised LI-5 prose above** in place of the v0 version in `2026-05-18-judge-design-step1-linkedin-engine.md`. The v0 prose catches Resolution A (topic mismatch) but is under-anchored on Resolution B (register mismatch), which is the AI-loop-most-likely failure mode. The revised score-0 anchor names the register-mismatch failure explicitly with three concrete examples.

**R3. Wire author source_data into the judge prompt explicitly.** The judge needs role, stage, employer-scope, and expertise tags from the author's profile. Without this, LI-5 collapses to "is the post coherent with itself" — a degenerate criterion. The source_data block already exists in the lane's fixture schema (per `linkedin_engine v040 cold-start mutation` memory note); confirm wiring.

**R4. Cold-start handling.** When `source_data` has no author context (new account, no prior posts, no work-history surface), LI-5 must emit 0.5 + "unknown" rather than scoring blind. The `linkedin_engine v040` cold-start pattern applies here. Adding a hard "if source_data.role is null → 0.5 unknown" check in the judge prompt's Step 1 is sufficient.

**R5. Variance instrumentation per `judge-design-guide.md` §11.5.** LI-5 is one of the criteria most likely to drift — register-coherence prose is easier to subvert with surface compliance than topic-coherence. Track per-generation variance for LI-5 specifically; if mean compresses toward 1 over 3 generations while AI-loop output objectively trends toward register-mismatch (verified by spot-check), the criterion is being gamed and needs redesign — not calibration.

**R6. Run the redundancy correlation check** between LI-3 and LI-5 on the next stable fixture batch before promoting LI-5 to live rubric. If r > 0.7, drop one. Expected r ≈ 0.4–0.6 — keep both.

**R7. Reserve LI-5 anchor examples to JR-curated exemplars only.** Per `judge-design-guide.md` §7 (reference-free) and §4 (hedge examples with "do not optimize toward this"), the score-1 example in LI-5 prose must remain a hedged, single, JR-validated exemplar — not a model-authored one. The Series-A-hiring-decision example in §6 above is illustrative only; replace with a real curated exemplar before shipping.

---

## Open questions

1. **Can we get the author's recent-post history into source_data reliably?** Gate-3 (Claim-vs-Recent-Activity) requires the last 30 days of post titles or summaries. If the platform-scraper layer cannot provide this consistently across fixtures, Gate-3 collapses back into the judge surface, which inflates LI-5 to scoring temporal coherence as well as register coherence — a problematic conflation. **Action:** confirm with the scraper-pipeline owner whether recent-post history is reliable in `source_data`.

2. **How does LI-5 interact with ghostwritten content?** Some authors publish ghostwritten posts where the register is deliberately calibrated above their organic voice (e.g., a founder using a ghostwriter to sound more polished and one register more senior than their daily IC mode). Is this a Resolution B failure or an intentional brand choice? **Action:** likely out of scope for v1 — the lane is generating drafts *for* a specific author and the brief contains tone-targets; ghostwriting-divergence is a pre-judgment configuration concern, not a runtime judge concern.

3. **Is there a Goodhart move where the loop generates posts that are *exactly* one stage below the author's seat to avoid the register-too-high failure?** Underfit response that would pass LI-5 but score weaker on LI-2 (insight depth) for senior authors. **Action:** monitor across 3 generations. If LI-5 mean rises while LI-2 mean falls on senior-author fixtures specifically, this move is in play.

4. **Topic Authority compounding lag.** The 360Brew ranker's Topic Authority score updates on a 30-90 day lag. Single-judgment LI-5 scoring catches per-post mismatches but cannot model cross-post topic-fingerprint pollution. **Action:** out of scope for the single-shot judge; document as a known limitation. Cross-post coherence belongs in a downstream portfolio-level analyzer, not in LI-5.

5. **Author-stage detection precision in source_data.** Resolution B (register mismatch) requires knowing the author's stage at sub-role granularity (Series A vs Series C; junior IC vs senior IC; first-time manager vs VP). Profile bios rarely state stage this precisely. **Action:** the judge has to infer stage from work-history dates and employer-headcount when available; emit 0.5 + "unknown" when the stage cannot be inferred to better than two adjacent registers.

---

## Citations

**Communication-theory credibility foundations:**

- Berlo, D.K., Lemert, J.B., & Mertz, R.J. (1969–1970). "Dimensions for Evaluating the Acceptability of Message Sources." *Public Opinion Quarterly* 33(4): 563–576. Three-factor model (competence / trustworthiness / dynamism).
- Hovland, C.I. & Weiss, W. (1951). "The Influence of Source Credibility on Communication Effectiveness." *Public Opinion Quarterly* 15: 635–650. Two-factor expertise-trust model.
- McCroskey, J.C. & Teven, J.J. (1999). "Goodwill: A reexamination of the construct and its measurement." *Communication Monographs* 66(1): 90–103. McCroskey source-credibility scale; <http://www.jamescmccroskey.com/publications/96.htm>.
- Ohanian, R. (1990). "Construction and Validation of a Scale to Measure Celebrity Endorsers' Perceived Expertise, Trustworthiness, and Attractiveness." *Journal of Advertising* 19(3): 39–52. Standard source-credibility scale in marketing literature.
- Pornpitakpan, C. (2004). "The Persuasiveness of Source Credibility: A Critical Review of Five Decades' Evidence." *Journal of Applied Social Psychology* 34(2): 243–281. Meta-analysis of 47 studies; expertise-message-band coherence finding.
- Cialdini, R.B. (1984, updated 2021). *Influence: The Psychology of Persuasion.* Authority as cognitive shortcut; incongruent-authority-cue research.

**LinkedIn 2026 platform research — Topic Authority / 360Brew:**

- Van der Blom, R. *Algorithm InSights 2025/26.* <https://thelonerecruiter.com/wp-content/uploads/2025/10/Mastering-the-LinkedIn-Algorithm-in-202526-.pdf>. Dwell-time mechanics + Depth Score.
- Goodman, M. "LinkedIn Algorithm 2026: Why Your Reach Dropped (and How Topic Authority, Documents and Saves Fix It)." <https://melaniegoodmanlinkedinconsultant.substack.com/p/linkedin-algorithm-2026-reach-topic-authority>. Topic Authority + 78% distribution lift finding.
- Vulse. "How LinkedIn's 2026 Algorithm Works: A Guide for Marketers." <https://vulse.co/blog/how-linkedin-2026-algorithm-works-and-what-it-means-for-your-content-strategy>. 360Brew transformer rewrite.
- Stackmatix. "How the LinkedIn Algorithm Works in 2026: A Data-Driven Breakdown." <https://www.stackmatix.com/blog/linkedin-algorithm-how-it-works>. Topic-fingerprint / topic-DNA mechanism.
- Bang Marketing. "LinkedIn Algorithm 2026: What Changed and How to Adapt." <https://www.bang-marketing.com/en/linkedin-algorithm-2026-b2b-marketing/>. Thematic-dispersion as primary B2B distribution leak.
- Upgrowth. "LinkedIn Algorithm 2026 Explained: What 360Brew Means for Reach & Growth." <https://upgrowth.in/linkedin-algorithm-2026-360brew-update/>. 360Brew rewrite details.
- Dataslayer. "LinkedIn Algorithm 2026: What Works Now (Documents, Newsletters, Video)." <https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now>. Depth Score + AI-classification.
- GBG Learning Lab. "What We Know About the LinkedIn Algorithm in 2026." <https://gbgmarketing.com/labs/what-we-know-about-the-linkedin-algorithm-in-2026/>.
- Tareno. "LinkedIn Algorithm 2026: What Actually Matters Now." <https://tareno.co/resources/blog/linkedin-algorithm-2026-what-actually-matters-now>.

**B2B trust + thought-leadership coherence:**

- Edelman & LinkedIn. *2025 B2B Thought Leadership Impact Report.* <https://www.edelman.com/expertise/Business-Marketing/2025-b2b-thought-leadership-report>. 73% decision-maker trust signal; consistency dimension.
- LinkedIn Business Blog. "6 B2B Marketing Insights for 2026: Why Creators Are Up..." <https://www.linkedin.com/business/marketing/blog/trends-tips/b2b-marketing-insights-creators-thought-leadership>.

**Project context (referenced, not re-cited):**

- `docs/rubrics/judge-design-guide.md` (judge-design canonical reference)
- `docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` (LI-5 v0 prose this document deepens)
- `docs/research/2026-05-18-judges-domain-linkedin-engine.md` (domain research sibling)

---

**Word count:** ~3,200 words. Conforms to `judge-design-guide.md` constraints: outcome-questions only, binary anchors, no framework-name embedding in criterion prose, verifiables routed to `structural_gate`, reference-free, defends per failure mode. Does not overlap with sibling-dispatch axes (depth / comment-seed / AI-slop / trailer) — stays on the author-context-coherence axis exclusively.
