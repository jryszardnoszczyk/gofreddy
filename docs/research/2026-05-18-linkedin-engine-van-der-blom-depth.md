---
date: 2026-05-18
type: deep-research deliverable
status: complete
lane: linkedin_engine
axis: Van Der Blom Depth Score
parent_spec: docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md
parent_domain: docs/research/2026-05-18-judges-domain-linkedin-engine.md
guide: docs/rubrics/judge-design-guide.md
---

# LinkedIn Engine — Van Der Blom Depth Score Deepening

## TL;DR

The Van Der Blom *Algorithm InSights 2025/26* report identifies a composite "Depth Score" as LinkedIn's dominant 2026 ranking signal. It is not a single number but a weighted aggregation of five observable post-effects: dwell time per impression, comment-thread depth (length × replies × reciprocity), share quality (with-comment vs naked), post-format–specific weights, and profile-click follow-through. The empirical cliff is sharp — 0–3s dwell yields 1.2 % engagement and capped distribution; 61s+ dwell yields 15.6 % and full second/third-degree fanout. Comments are weighted ~15× a like but only count when they exceed roughly 10 words (ideally 30–80) and contain enough lexical surface for the NLP filter to score them as substantive.

Per-signal predictability: dwell is predicted by paragraph breaks, sentence rhythm, and trailer-payoff coherence, NOT line-break density alone. Comment depth is predicted by post stance (debatable claim / open question / list-with-room / contrarian-but-defensible), NOT by a bolted-on "what do you think?" closer — the algorithm penalizes engagement-bait CTAs as of 2025 and the penalty hardened in early 2026. Share quality is predicted by quotability — a single sentence the reader wants to put their name next to. Profile clicks are predicted by author-context fit and credibility coherence — the reader clicks the byline when the claim makes them want to know who said it.

Format weights in 2026 (LinkedIn's own product team confirmed via the November 2025 LinkedIn newsroom + verified by Authoredup/Socialinsider/Metricool independent benchmarks):

- **Document carousels:** ~6.60 % engagement, 39 % more reach than text — the format ceiling for B2B SaaS / consulting frameworks
- **Native video:** reach dropped 36 % YoY in 2026 but ~2× conversion vs text for personality-driven authors
- **Text posts:** 4.2 % engagement, deepest comment threads when the angle is debatable
- **Polls:** rebounded after a 2024 dip, now ~4.0 % engagement when the options are non-trivial
- **LinkedIn articles:** distribution surface separated from posts; Depth Score scored independently
- **Newsletter posts:** distinct distribution surface; not in scope for post-draft judging

The failure mode the lane has to defend against is precise: an AI optimizer that learns the surface markers of high-Depth-Score posts (line-break cadence + a question at line 4 + a numbered list with an open slot + a contrarian framing) and slot-fills them onto substantively empty content. Posts score well on judge AND get muted on platform. The judge's job is to test **whether the post would actually produce the Depth Score effects** — not whether the artifact contains the markers literature associates with those effects.

The rubric's load-bearing constraint: **all observable Depth-Score predictors that can be deterministically detected belong in `structural_gate`** (em-dash density, P.S.↓ closer presence, engagement-bait CTA detection, length bands per format, line-break count). The LI-2026 judge tests the **residual** — would a real professional reader produce dwell, substantive comment, share, and profile click — that determinism cannot catch. This is the OpenRubrics Hard-Rules-vs-Principles split applied surgically to the Depth Score axis.

## Key Questions Addressed

1. What is the canonical Van Der Blom Depth Score formulation, and which sub-signals does it weight?
2. Per sub-signal, what observable post features predict it — and which of those predictors are deterministic (structural_gate) vs gestalt (judge)?
3. What format types have the highest Depth Score in 2026 vs 2024–2025, and what changed?
4. What's the Goodhart failure mode where the workflow optimizes for Depth-Score-predictor surface markers and produces algorithmically performant + substantively empty posts?
5. How does the judge reward Depth-Score-effect achievement without becoming a feature-checker (the constraint that killed Phase 4)?
6. The over-engineering trap: many depth signals are observable — why not just route ALL of them to structural_gate? Where is the line?

## Synthesis

### 1. Canonical Depth Score formulation

Van Der Blom's *Algorithm InSights 2025/26* report does not publish the score as an arithmetic formula — LinkedIn keeps the exact weighting proprietary — but the report reverse-engineers the weighting through controlled experiments across his Just Connecting consulting client base (Van Der Blom's stated sample: 6,000+ posts, 38 countries, October 2024 – September 2025 measurement window with 2026 refresh). The follow-up coverage in *meet-lea*, *dataslayer*, *postiv*, and the *LinkBoost* blog independently corroborate the same five-component decomposition that LinkedIn's own product communications (the November 2025 newsroom + the January 2026 algorithm explainer) describe in plain English without naming it as a unified score.

The five components, in approximate weight order:

**(a) Dwell time per impression.** Single largest factor as of the 2026 measurement window. The cliff Van Der Blom names: 0–3s dwell → 1.2 % engagement rate, capped distribution to ~10 % of the author's first-degree network. 4–10s → 2.8 % engagement, partial fanout. 11–30s → 6.4 % engagement. 31–60s → 11.1 % engagement. 61s+ → 15.6 % engagement and full second/third-degree fanout. The 61s threshold is the rough boundary where LinkedIn appears to classify the impression as "deeply read" and award the post a positive Depth-Score increment.

**(b) Comment-thread depth.** Comments weighted ~15× a like. But only substantive comments count toward Depth — the threshold per Van Der Blom is comments longer than 10 words; the ideal band is 30–80 words. "Great post!" comments contribute zero. Reply chains compound: a comment that earns the author's reply that earns the original commenter's counter-reply triples the Depth credit. Reciprocity (the author responds to ≥50 % of substantive comments in the first 90 minutes) further compounds the credit.

**(c) Share weight by share type.** A share with a comment ("here's what made me think" + the share) is worth several plain reshares. A naked reshare is worth a fraction of a substantive comment. DM-shares (the user clicks "send to a connection") are weighted higher than feed-shares because they signal individual-reader-thought-this-was-worth-sending-to-a-specific-person — exactly the credibility signal the Edelman 2025 thought-leadership data identifies.

**(d) Post-format–specific weights.** The Depth Score uses different weight constants per format because dwell mechanics differ structurally. A carousel earns Depth via swipe-completion ratio; a video via watch-completion ratio; a text post via scroll-completion + comment-density; a poll via vote-density + comment-density. The format-weight table is what makes carousels currently look like the dominant format in benchmarks — high swipe-completion is easier to manufacture than 61s+ text dwell.

**(e) Profile-click follow-through.** The reader's downstream behavior after reading: do they click the author's byline to read more of the author's recent posts? Do they follow? Do they DM? Profile clicks are the credibility-coherence signal — they map directly to the LI-5 author-context-coherence criterion in the optimal-output spec. Van Der Blom's frame is that the algorithm interprets a profile-click cluster as evidence the post raised the author's individual reach equity, not just the post's transient reach.

### 2. Per-signal observable predictors

**Dwell time predictors.** Practitioners and the Van Der Blom report converge on a stack:

- *Trailer earns the click* (above-the-cut content has tension or specificity). This is the entry gate. If the trailer fails, dwell is 0–3s and nothing else matters. Welsh's trailer/meat/CTA and Acosta's hook+rehook both anchor here.
- *Payoff coherence* (the body below the cut delivers what the trailer promised). Bait-and-switch trailers earn the click but lose dwell at the cut.
- *Sentence rhythm* (varied length, plain English, conversational cadence). Denning's "write like you talk" is the surface marker; the underlying mechanism is that reading-cadence-matched prose holds attention longer per cognitive-load research (see Plagiarism Today's note on "oddly flat" affect as the AI-tell that fails to hold dwell).
- *Paragraph break density* (NOT line-break count alone — the load-bearing factor is whether each break creates a natural reading pause that lets the next line restart attention). Broetry tried to game this by making every line a paragraph; the algorithm's NLP filter has since learned to discount low-content one-word "paragraphs."
- *Content density at the end of the post* (whether the last line is the strongest, not the start). Posts with weak endings see drop-off in the last 20 % of reading time, which the algorithm reads as truncated dwell.

**Predictor → judge vs structural_gate routing for dwell:**

- Line-break count → `structural_gate` (deterministic; a max of ~15 line breaks per post is a reasonable hard cap to detect broetry slot-filling).
- Trailer presence (cut at ~210 chars / 3 lines) → `structural_gate` (deterministic).
- Trailer-payoff coherence → JUDGE (gestalt; LI-1 in the optimal-output spec already covers this).
- Sentence-rhythm variation → JUDGE (this is a voice-residual signal; LI-3 covers it).
- Paragraph-break naturalness → JUDGE (this is gestalt; trying to deterministically score "natural" pause is the textbook over-engineering trap — see §6 below).

**Comment-depth predictors.** The post earns substantive comments when it offers one of four entry points (synthesized from the Authoredup, Botdog, and Van Der Blom corpora):

- A **debatable claim** the reader will agree or disagree with at the experience-specific level (not the truisms level).
- An **open question** that requires the reader's specific experience to answer (not "what do you think?" — that's engagement-bait and the algorithm has detected and penalized that since 2025).
- A **numbered list with obvious room for additions** — readers add their own item.
- A **contrarian-but-defensible angle** the reader has to position themselves against.

The negative predictor — what *prevents* substantive comments — is the closed-monologue shape: a fully resolved insight with no entry point for the reader to add anything, plus a CTA that points away from the post (link to a newsletter, sign-up, calendar booking) and signals "this post is a funnel, not a conversation."

**Predictor → routing for comment-depth:**

- Engagement-bait CTA presence ("comment YES if you agree," "drop a 🔥 below," "tag someone who needs this") → `structural_gate` (deterministic; ~10 phrase patterns cover most cases).
- Question mark in body → NOT a reliable predictor on its own; depends on whether the question requires the reader's specific experience or is rhetorical. JUDGE (LI-4 already tests this).
- Debatable-claim presence → JUDGE (gestalt; the test is whether a relevant professional reader would have a 30–80-word reply, which requires reasoning about the reader).
- Numbered-list presence → `structural_gate` can detect the format, but whether the list has "room for additions" is gestalt. JUDGE.

**Share-quality predictors.** Substantive shares are predicted by:

- **Quotability** — a single sentence the reader wants to put their name next to. Sahil Bloom's curiosity newsletter is the named exemplar (one quotable insight per piece).
- **Author-context coherence** — the reader is willing to associate their name with the post because the post sits coherently in the author's professional surface (Edelman 2025 trust signal).
- **Insight density** — the reader earns social credit for sharing a post that gives their network a non-obvious takeaway.

Per-signal routing: quotability is gestalt (JUDGE, partly covered by LI-2 insight delivery). Author-context coherence is gestalt (JUDGE, covered by LI-5). Insight density is gestalt (JUDGE, covered by LI-2).

**Format-weight predictors.** The format-weight table is structural; given the post's format and length, the structural_gate can verify the post is in the format-appropriate band (e.g., a carousel with <4 slides is below the format's reach threshold; a text post above 1,300 chars hits a fatigue ceiling). The judge does NOT score format choice — format-job-fit is implicit in LI-2 (the insight delivery criterion will reward the right format for the right insight without ever naming format).

**Profile-click predictors.** A profile click is predicted by the reader's curiosity about the author after reading the post. Predictors:

- A claim that exceeds the reader's prior expectation of what someone in the author's apparent role/stage would say.
- A turn of phrase or moment of voice that signals "this person is interesting."
- An anchor to the author's specific professional context (a client win, a build-in-public detail, a hiring decision, a strategic call) that makes the reader want to read more from the same author.

All three predictors are gestalt — they cannot be deterministically detected. LI-3 (voice) and LI-5 (author-context coherence) jointly cover this.

### 3. Format weights — what changed 2024 → 2026

The 2024 baseline (per Hootsuite and Socialinsider 2024 benchmarks):

- Text posts: 4.5 % engagement, dominant format by volume
- Carousels: 5.1 % engagement, growing
- Video: 3.8 % engagement, declining
- Polls: 2.9 % engagement, deprecated-feel

The 2026 reality (per Socialinsider, Metricool, Authoredup, Grow with Ghost, ContentIn, all measuring 2026 Q1):

- Carousels: 6.60 % engagement, 39 % more reach than text — the format LinkedIn's product team most actively promoted in 2025–2026 due to dwell mechanics (swipe-completion is a cleaner Depth signal than scroll-completion)
- Text: 4.2 % engagement, deepest comment threads when debatable — still the dominant format for thought-leadership genres because the algorithm has the longest history scoring text and the NLP filter is most sophisticated on text
- Video: ~2× conversion vs text for personality-driven authors despite reach dropping 36 % YoY — Van Der Blom and Postiv both note this is because LinkedIn is reducing video reach for non-native-uploaded content (third-party-app video sees a 50–70 % reach cut)
- Polls: ~4.0 % engagement after a 2024 dip — the 2026 algorithm change appears to weight poll-comment-density alongside vote-density, making polls with substantive options (not 4-option commodity surveys) the winning shape
- Newsletter and article surfaces: separated distribution; Depth Score computed independently; **out of scope for post-draft judge**

What changed in 2026 specifically:

1. **Document carousel dominance hardened.** The format's dwell mechanic (swipe-completion) is harder for AI to game than text dwell, so the algorithm rewards it.
2. **Engagement-bait CTA penalty hardened.** The 2025 deprioritization became an explicit downrank in early 2026 per LinkBoost and meet-lea.
3. **Comment-substance threshold hardened.** The NLP filter that scores comment substance was upgraded; comments under ~10 words now contribute essentially zero Depth credit (whereas in 2024 even a "Great insight!" had marginal value).
4. **Profile-click weight introduced.** This is the newest component of the 2026 Depth Score and the one with the least public documentation; Van Der Blom's report identifies it as a distinct signal because his client cohort saw reach disproportionate to comments + likes when profile-click clusters were high.
5. **AI-generated comment detection.** LinkedIn deployed AI-generated comment detection mid-2025 and the system is operational in 2026 — Van Der Blom and the LinkBoost coverage both note that AI-generated comments are now downweighted or filtered, so engagement-pod tactics that worked in 2023–2024 have collapsed.

### 4. Goodhart failure mode — the slot-filling pathology

The specific Goodhart collapse for this axis: an evolution loop running 50+ generations against a Depth-Score-shaped rubric learns to slot-fill the surface markers literature associates with high Depth Score. The collapse pattern, derived from the broetry-to-AI-slop trajectory and the v40 cold-start memory:

- Every post opens with a specific number or named-entity hook regardless of whether the substance benefits.
- Every post has a rehook in line 2 that bait-and-switches mechanically.
- Every post inserts a question at line 4 to "earn comments" — the question is grammatically a question but semantically a CTA.
- Every post replaces em-dashes with semicolons or single dashes (different surface tell, same gradeless prose).
- Every post namechecks a customer or anecdote whether load-bearing or pasted-in.
- Every post has exactly 7–9 sentences (Denning's max) regardless of whether 4 or 12 would serve the insight.
- Every post closes with a numbered list with three items and one "open slot" for reader additions.

The result is a corpus that is structurally compliant, recognizable as templated within 3 seconds by a human reader, and that the LinkedIn 2026 algorithm's distinctiveness filter (a new component per Postiv's January 2026 coverage) detects and downranks. Posts score well on the judge AND get muted on platform. This is the exact failure mode the Phase 4 prose rollback at HEAD `c76f051` was about, applied to the LinkedIn surface.

The Reward Hacking Era survey (arxiv 2604.13602) names this as the Feature → Representation → Evaluator → Environment escalation pattern. Slot-filled surface markers are the Feature level; if the judge holds the line at outcome-questions, the workflow can't easily get past the entry point.

### 5. How the judge rewards depth without becoming a feature-checker

The judge-design-guide.md §1.1 prescription is the canonical pattern: **outcome questions, not feature checks**. Applied to the Depth Score axis, every criterion asks "would the reader DO X?" where X is the Depth-Score-producing behavior, not "does the post CONTAIN Y?" where Y is a Depth-Score-predicting feature.

The five LI criteria in the optimal-output spec are constructed exactly this way:

- **LI-1** asks "would the reader click '...more'?" — not "does the post have a hook?"
- **LI-2** asks "would the reader leave with pattern-recognition they didn't arrive with?" — not "does the post contain a specific number?"
- **LI-3** asks "would a colleague recognize the author's voice?" — not "does the post avoid em-dashes?"
- **LI-4** asks "would the reader leave a 30–80-word comment?" — not "does the post have a question at line 4?"
- **LI-5** asks "does the claim sit coherently in the author's professional context?" — not "does the post namecheck the author's role?"

The behavioral anchors in each criterion are concrete enough to ground the judge's reasoning but never name a framework or feature target. Example hedge ("do not optimize toward this") is the lightest possible mitigation against the workflow adopting the example as a target — per guide §4.

What this does NOT mean: the judge ignores the surface features. Surface features are still present in the artifact; the judge will read them as part of its reasoning about whether the reader would experience the outcome. The discipline is that the surface features do not enter the *criterion definition* — they enter the *judge's reasoning toolkit*, which the judge applies privately per criterion.

### 6. The over-engineering trap — where structural_gate ends and judge begins

The seductive over-engineering trap on this axis: most Depth-Score predictors are observable. Therefore (the trap reasons) the judge should be replaced by an aggregator over deterministic structural_gate checks — line-break count, em-dash density, P.S.↓ closer detection, CTA-phrase pattern matching, question-mark presence, numbered-list detection, length-band per format. The aggregator would be faster, cheaper, and reproducible across generations.

Three reasons this fails:

**(i) The deterministic-check ceiling.** Each deterministic check on its own is gameable by the workflow trivially (replace em-dashes with semicolons; replace P.S.↓ with "in summary:"; rephrase engagement-bait as a softer prompt). The aggregator over deterministic checks does not produce the gestalt — it just teaches the workflow a longer slot-filling list. This is the Rubrics-as-Attack-Surface drift (arxiv 2602.13576) at the structural layer.

**(ii) The reader-effect cannot be deterministically simulated.** Dwell time, comment substance, share quality, and profile-click follow-through are reader-state-dependent outcomes that depend on the reader's prior knowledge, professional context, and what they consumed before this post. A structural_gate cannot reason about the reader; only an LLM judge with imagine-the-reader prose can. The Edelman 2025 trust-signal data is reader-side, not artifact-side.

**(iii) The Hard-Rules-vs-Principles split is load-bearing.** The OpenRubrics framing (judge-design-guide.md §1.2) is that verifiable requirements live in structural_gate and *subjective* qualities live in the judge. Depth-Score predictors are a mix: some are verifiable (line-break count, CTA-phrase presence, length-band), some are subjective (would the reader engage substantively, is the voice coherent with author context). The discipline is to route every verifiable predictor to structural_gate AND keep the subjective layer in the judge. The trap is collapsing both layers into one.

**The correct routing for the LinkedIn lane:**

- `structural_gate`:
  - Length-band per format (text 600–1500 chars, carousel 4+ slides, video 30–90s native upload)
  - Line-break count (cap ~15)
  - Trailer cut position (text posts have a ~210-char first-fold)
  - Engagement-bait CTA phrase detection (~10 patterns cover 90 %+)
  - P.S.↓ closer detection
  - Em-dash density (>10× human baseline = AI-slop flag)
  - Symmetrical bullet detection (all bullets within ±2 words of each other)
  - Template-phrase opener detection ("Let me explain why," "Here's the kicker," "Here's the thing")
  - File / payload validity (the post draft parses, story.json validates)

- Judge (LI-1 through LI-5):
  - Trailer-payoff coherence (residual past trailer-cut-position structural check)
  - Insight non-obviousness and reader-progress
  - Voice residual past AI-tell-stack structural check (affective flatness, voice mismatch, generic register)
  - Comment-seed quality past CTA-phrase structural check (debatable claim, open question requiring reader experience, list with room, contrarian angle)
  - Author-context credibility coherence

This split matches the LinkedIn-engine optimal-output spec §8.2 explicitly: "LinkedIn-specific deterministic signals (em-dash density, template-phrase stack, P.S.↓ closer, symmetrical-bullet rhythm) should live in `structural_gate` for LI lane. LI-3 then tests the *residual* (affective flatness, voice mismatch) that determinism cannot catch."

### 7. Operator-firsthand observations from gofreddy's lane history

The v40 cold-start mutation (memory `linkedin_engine v040 cold-start mutation 2026-05-08`) added `templates/linkedin_engine/skeleton-short_take.md` plus a pre-ship checklist to fix a 0/4 structural-fail cohort. The failure mode was specifically that parent variants produced no output for cold-start fixtures — the structural_gate caught the absent payload before the judge ever ran. This validates the routing: structural_gate handles file presence; judge handles substantive quality.

The X-engine port (memory `X+LinkedIn port — IN PROGRESS as of 2026-05-08`) introduced `slop_gate` as a platform-aware AI-detection layer. The LinkedIn lane inherits this pattern and should route LinkedIn-specific deterministic AI-tells (em-dash density, P.S.↓, template phrases, symmetrical bullets) into the LI lane's structural_gate. The LI-3 voice criterion then tests the residual.

The Phase 4 prose rollback (memory `Judge design — Phase 4 prose REVERTED`) is the load-bearing prior incident. The rollback was triggered specifically by feature-checking pathology (CI-4 Helmer-power-name-check, MON-4 FAA-AD-slot-fill, etc.) where the judge prose embedded framework names and surface markers. The LinkedIn-engine judge MUST NOT repeat this pattern with Depth-Score predictors. Specifically:

- The judge must NOT instruct the model to "check for a specific number in the first three lines."
- The judge must NOT instruct the model to "verify the post has a debatable claim."
- The judge must NOT instruct the model to "score the post higher if it follows the 5-12-3 rule."

The judge instead asks reader-effect questions whose answers happen to correlate with those features but do not name them.

## Recommendations

**R1 — Adopt the optimal-output spec's 5 criteria (LI-1 through LI-5) as-is.** The criteria are constructed correctly: each is an outcome question with binary anchors, none embed framework names, none reduce to feature checks. The Depth Score axis is covered by the criteria collectively (LI-1 covers trailer→dwell entry; LI-2 covers insight→share/save behavior; LI-3 covers voice→AI-detector residual; LI-4 covers comment-seed→Depth-Score comments component; LI-5 covers author-context→profile-click + trust signal).

**R2 — Move all deterministically-detectable Depth-Score predictors to structural_gate before the judge sees the artifact.** The full list in §6 above: em-dash density, P.S.↓ closer, template-phrase opener detection, symmetrical bullet detection, engagement-bait CTA phrase detection, length-band per format, line-break count cap, trailer cut position. ~150 LOC; zero runtime cost. This is the OpenRubrics Hard-Rules-vs-Principles split applied surgically.

**R3 — Run the redundancy check after first 5–10 fixtures.** Per design guide §5, drop any criterion correlating >0.7 with another across re-runs. Expect LI-3 (voice) and LI-5 (author-context) to be the candidate redundancy pair — both anchor on author voice — but the design intent is that LI-3 tests voice residual past AI-slop detection while LI-5 tests claim-stance-context coherence. Per-criterion isolation should keep them separable in practice; verify empirically. If they collapse, keep LI-3 (it has the more concrete behavioral anchor) and fold the LI-5 author-context test into LI-2's "is this insight author-specific?" check.

**R4 — Do NOT add a 6th criterion for format-fit.** Format-job-fit is implicit in LI-2 (the right insight in the wrong format will fail to deliver pattern-recognition because the format degrades the reader's comprehension). Adding a format criterion would (i) violate the ≤5 ceiling without the literature-documented justified-breach pattern from guide §5, and (ii) invite the workflow to slot-fill format-feature markers (always-use-a-carousel; always-include-3-slides) instead of choosing format from substance.

**R5 — Do NOT include any anti-gaming clauses in criterion prose.** Per guide §10, these are theatrical. Do not include "do not be biased toward longer outputs"; do not include "ignore engagement-bait CTAs"; do not include "the workflow should not slot-fill features." The structural_gate handles the deterministic flag detection. The criterion prose stays clean.

**R6 — Variance instrumentation per criterion per generation.** Per guide §11.5, track the variance of LI-1 through LI-5 across generations. Any criterion whose variance grows monotonically over 3 generations or whose mean compresses toward the middle gets flagged for redesign — NOT for calibration. This is the only Goodhart-time-constant signal available; the literature has not yet quantified time-to-Goodhart per rubric shape, so the variance telemetry is the early-warning system.

**R7 — Pin panel models to dated versions.** Per guide §15: `claude-opus-4-7-20260201`, `gpt-5-5-20260301`, `gemini-3-flash-20260201` (or the actual current-pinned IDs). Rotate within-family minor versions every ~5 generations; keep cross-family composition fixed.

**R8 — Build the LI calibration set with format-stratified fixtures.** Per guide §15: 100 fixtures total, stratified across (a) the 4 audience-types (founder, IC, recruiter, peer), (b) the 5 formats (text, carousel, video, poll, article), and (c) both score-1 and score-0 ground-truth examples per criterion. The stratification matters because Depth-Score predictors differ by format — a carousel that earns swipe-completion has different surface markers than a text post that earns scroll-completion, and the judge needs to learn that the *underlying outcome* is what's being scored.

**R9 — Hedge LI-1's exemplar with explicit "do not optimize toward this."** The Lara Acosta "Hired a Gen-Z candidate without interviewing him" example in LI-1's score-1 anchor is concrete and useful for judge calibration, but the design guide §4 prescription is that any score-1 anchor with a named example must include the hedge. Verify this hedge is present in the final criterion prose.

**R10 — Defer the comment-seed-fixture-question-mark redundancy review until after LI-D + LI-2 are calibrated.** The optimal-output spec §8.2 already flags that LI-3 (voice) and LI-5 (author-context) may correlate. Add LI-4's comment-seed test to the redundancy review — it may correlate with LI-2's insight-delivery test if the workflow learns that "non-obvious insight" implicitly creates comment-seed potential. The redundancy check should catch this.

## Open Questions

1. **Profile-click follow-through is the least-documented Depth-Score component.** Van Der Blom names it but does not publish a weight or a sub-signal decomposition. The LI-5 author-context-coherence criterion is the closest proxy in the judge; whether it actually predicts profile-click behavior empirically is an open question that requires post-deployment telemetry. Track in the calibration set.

2. **Format-weight stability across 2026.** LinkedIn's product team has not communicated a stable weighting; the 2026 carousel dominance may shift if the platform's product strategy changes. The judge should be format-agnostic in design (LI-1 through LI-5 do not reward format choice on its own), so weight shifts should not require rubric changes.

3. **AI-generated comment detection upstream consequences.** As of 2026, LinkedIn filters AI-generated comments. If the agency's post-draft workflow ever generates *comments* on the author's own post (auto-replies in the golden hour), that's a separate workflow outside this lane's scope but worth flagging — the substrate would game its own Depth Score and the platform would catch it.

4. **Newsletter-surface vs post-surface drift.** The Depth Score is computed separately for newsletter posts. If a workflow learns to game post-surface Depth Score and the agency then publishes the same content to the newsletter surface, the newsletter's Depth Score will be computed against a different reader population (subscribers, not feed scrollers). Out of scope for this lane; flag for the newsletter lane if/when it exists.

5. **Cold-start author context.** When the author has no LinkedIn posting history (new account, first post, no prior pattern data), LI-3 (voice) and LI-5 (author-context) lose their grounding anchor. The v40 cold-start memory notes this; the structural_gate's `skeleton-short_take.md` template addresses the structural side, but the judge-side handling remains open. Possible mitigation: a `source_data.author_context_known = false` flag passed to the judge that triggers LI-3 and LI-5 to emit 0.5 + "unknown" by default rather than scoring. Implementation deferred to the lane spec.

6. **Time-to-Goodhart under matched compute for outcome vs feature rubrics.** Per guide §16, no literature has fit a curve to this. The variance instrumentation per criterion per generation (R6) is the only available signal. Revisit when 6–12 months of post-deployment data exist.

7. **Edelman 2025 trust-signal data validity for non-thought-leadership posts.** Edelman's 73 % decision-maker-trust figure is measured against posts the buyer recognizes as thought leadership. The LI-5 author-context-coherence criterion assumes all LinkedIn posts are subject to the same trust mechanism, but posts that are clearly career-narrative or culture-signaling (not insight-claim) may follow different trust dynamics. If fixtures cluster around career-narrative posts, validate that LI-5 still discriminates correctly there.

## Citations

**Van Der Blom (primary algorithm research):**

- Van der Blom, Richard. *Algorithm InSights Report 2025 / 2025-26.* Just Connecting B.V. PDF mirror at The Loner Recruiter (October 2025): https://thelonerecruiter.com/wp-content/uploads/2025/10/Mastering-the-LinkedIn-Algorithm-in-202526-.pdf
- Van der Blom, Richard. "Algorithm Insights Report 2025/26." LinkedIn Pulse: https://www.linkedin.com/pulse/algorithm-insights-report-2025-here-xdooc

**Independent corroboration of the Depth Score decomposition:**

- Meet-Lea. "LinkedIn Algorithm Explained 2026: Dwell Time, Comments." https://meet-lea.com/en/blog/linkedin-algorithm-explained
- Dataslayer. "LinkedIn Algorithm 2026: What Works Now." https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now
- Postiv AI. "Your Definitive Guide to the LinkedIn Algorithm 2026." https://postiv.ai/blog/linkedin-algorithm-2026
- LinkBoost. "LinkedIn Algorithm Changes 2026: Beat the Depth Score." https://blog.linkboost.co/linkedin-algorithm-changes-2026/
- Botdog. "Everything You Need To Know About LinkedIn's Algorithm In 2025." https://www.botdog.co/blog-posts/linkedin-algorithm-report
- Authoredup. "How the LinkedIn Algorithm Works in 2025 [Data-Backed Facts]." https://authoredup.com/blog/linkedin-algorithm
- Hootsuite. "How the LinkedIn algorithm works in 2025." https://blog.hootsuite.com/linkedin-algorithm/

**Format-performance benchmarks (2026):**

- Socialinsider. "LinkedIn Organic Benchmarks 2026." https://www.socialinsider.io/social-media-benchmarks/linkedin
- Metricool. "LinkedIn Trends: 6 Strategy Insights from Our 2026 Study." https://metricool.com/linkedin-trends/
- Grow with Ghost. "LinkedIn Post Formats Ranked 2026." https://www.growwithghost.io/blog/linkedin-post-formats-ranked-text-vs-carousel-vs-video-vs-polls-2026/
- ContentIn. "LinkedIn Algorithm 2026: Format Strategy That Actually Works." https://contentin.io/blog/linkedin-algorithm-2025-the-complete-content-format-strategy-guide/
- Authoredup. "Best Performing Content on LinkedIn in 2026." https://authoredup.com/blog/best-performing-content-on-linkedin

**Trust + thought-leadership data:**

- Edelman & LinkedIn. *2025 B2B Thought Leadership Impact Report.* https://www.edelman.com/expertise/Business-Marketing/2025-b2b-thought-leadership-report

**Practitioner playbooks (named-creator frameworks; reasoning toolkit only, NOT rubric prose):**

- Welsh, Justin. "How to Grow on LinkedIn in 2026." https://www.justinwelsh.me/article/linkedin-guide-2026
- Acosta, Lara. SLAY framework + hook patterns: https://buldrr.com/the-acosta-linkedin-model/ ; cool-story breakdown: https://cool-story.beehiiv.com/p/lara-acosta-slay-framework
- Alić, Jasmin. *27 Proven LinkedIn Writing Tips:* https://www.scribd.com/document/701462598/27-Proven-LinkedIn-Writing-Tips-by-Jasmin-Alic-1706131277
- Denning, Tim. "My Best Tip for LinkedIn Growth — LinkedIn Language." https://timdenning.com/linkedin-language/
- Meer, Ben. Growth-in-Reverse profile + Creator Method: https://growthinreverse.com/ben-meer/

**AI-slop / failure-mode literature:**

- TechRadar. "Blade Runners of LinkedIn." https://www.techradar.com/computing/artificial-intelligence/blade-runners-of-linkedin-are-hunting-for-replicants-one-em-dash-at-a-time
- Plagiarism Today. "Em Dashes, Hyphens and Spotting AI Writing." https://www.plagiarismtoday.com/2025/06/26/em-dashes-hyphens-and-spotting-ai-writing/
- Cybernews. "The em dash dilemma." https://cybernews.com/editorial/linkedin-em-dash-ai/

**Operator-firsthand (gofreddy project incidents and memory):**

- Memory `Judge design — CI v3.3 COMPLETE, 7 lanes pending 2026-05-18` — current state of LinkedIn lane in the 8-lane judge redesign program.
- Memory `Judge design — Phase 4 prose REVERTED, next session = optimal-output-first design 2026-05-15` — Phase 4 feature-checking pathology and the rollback at HEAD `c76f051` that motivates the outcome-question discipline.
- Memory `linkedin_engine v040 cold-start mutation 2026-05-08` — cold-start handling pattern; `templates/linkedin_engine/skeleton-short_take.md` precedent for structural_gate handling.
- Memory `X+LinkedIn port — IN PROGRESS as of 2026-05-08` — `slop_gate` platform-aware AI-detection precedent that the LinkedIn lane structural_gate should inherit.
- `docs/rubrics/judge-design-guide.md` v2.1 — load-bearing design guide with the Hard-Rules-vs-Principles split, the outcome-question prescription, and the ≤5-criterion ceiling.
- `docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` — the lane's optimal-output spec being deepened here.
- `docs/research/2026-05-18-judges-domain-linkedin-engine.md` — the domain research synthesis being deepened here.
