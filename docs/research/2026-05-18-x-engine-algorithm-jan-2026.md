---
date: 2026-05-18
type: research deliverable — algorithm-signals axis
status: complete
topic: x_engine lane — January 2026 open-source algorithm signals
parent: docs/rubrics/judge-design-guide.md
sibling: docs/research/2026-05-18-judges-domain-x-engine.md
companion: docs/handoffs/2026-05-18-judge-design-step1-x-engine.md
axis: algorithm Jan-2026 signals (PROMOTED / DEMOTED, observable post-features predicting each signal, 2025–2026 deltas)
---

# X Engine — Algorithm Signals (January 2026 Open-Source Release)

**Purpose.** Deepen the algorithm axis of the x_engine domain research with citations from the real January 2026 open-source release (xai-org/x-algorithm) and verified operator data. The companion file (`2026-05-18-judges-domain-x-engine.md`) already covers playbooks (Welsh, Cole/Bush, Naval, Bloom, Mack, Veerasamy, Hormozi); this file does NOT restate them. Here the axis is: what does the algorithm reward and penalize in 2026, what observable post-features predict each signal, what changed between 2024 operator lore and the 2026 code release, and how should the judge encode this without collapsing into algorithm-rules-checking (feature-checking pathology per `judge-design-guide.md` §11.1).

---

## TL;DR

1. **The January 2026 open-source code (xai-org/x-algorithm) confirms ten predicted action-probabilities — P(favorite), P(reply), P(repost), P(quote), P(click), P(profile_click), P(video_view), P(photo_expand), P(share), P(dwell) — and confirms the scoring formula `Final Score = Σ (weight_i × P(action_i))`, but does NOT publish the numerical weights.** The 13.5× / 27× / 150× / −74× / +12 / +10 figures in circulation are operator-tested community reconstructions, not authoritative coefficients. Treat them as direction-of-effect markers, not load-bearing constants.
2. **The high-conviction promoted signals are: reply (especially reply-with-author-response, ≈150× a like by multiple reconstructions); repost (≈20×); bookmark (≈10×); profile click (≈12×); long-dwell (≈+10× as a positive feature). Demoted signals: blocks, mutes, reports, "not interested" clicks at ≈−74× (community consensus), and external links at 30–94% reach reduction depending on cohort.**
3. **The biggest 2024→2026 shift is the Grok-based Phoenix transformer replacing hand-engineered features. It reads semantic content directly (no hashtag lookup tables, no keyword multipliers), uses candidate isolation so post scores don't depend on what else is in the batch, and is reported to factor "tone of voice" into ranking — constructive/positive distribution > combative/negative.**
4. **2025–2026 deltas operator content from 2024 misses: external-link suppression intensified to near-zero for non-Premium accounts in Q1 2026 (workaround: post link as first reply); Grok-based tone analysis is new; Premium-account boost (≈+4× in-network, +2× out-of-network) is now structural not promotional; community-noted posts get a "moderate distribution penalty while the note is active"; the 21% YoY increase in replies AND 35% increase in reposts shifts the optimal post-shape toward "earns substantive reply" rather than "earns like."**
5. **The judge cannot, must not, become an algorithm-rules-checker.** The right shape is to score for the *observable reader behaviors* the algorithm proxies (substantive reply, repost, bookmark, dwell, profile click) — never for the algorithm's surface features (reply-bait CTAs, "Bookmark this," "follow me" tells). The reader-effect framing is what makes this Goodhart-resistant: the algorithm rewards what the scroller actually does; the judge tests whether the post earns that doing.

---

## Key Questions Investigated

1. What signals are PROMOTED in the January 2026 open-source release? Verified weights, ranges, or directional certainty?
2. What signals are DEMOTED? What zeroes reach (external links, viral-kit detection)?
3. For each signal: what observable post-feature predicts it? (e.g., first-line question → reply rate; concrete number with named entity → bookmark rate; link in body → reach kill.)
4. What changed in 2025–2026 that operator content from 2024 misses? (Grok integration, Premium dynamics, community-note effect, link suppression intensification, tone-based ranking.)
5. How does the judge score "post engineered for current algorithm" without becoming an algorithm-rules-checker (feature-checking pathology, per `judge-design-guide.md` §11.1)?

---

## Synthesis

### 1. What the open-source code actually publishes (and what it doesn't)

The xai-org/x-algorithm repo (Jan 2026, refresh May 2026) ships:

- **Architecture** — four Rust/Python components: Home Mixer (orchestration), Thunder (in-memory post storage), Phoenix (Grok-based transformer ranking), Candidate Pipeline (reusable retrieval framework). Phoenix is described as a "Grok-1-derived transformer" by the README and external code-readers; the May 15 update added a downloadable mini-transformer for local inference.
- **Predicted action set** — Phoenix outputs ten probabilities per (user, candidate post) pair: `P(favorite), P(reply), P(repost), P(quote), P(click), P(profile_click), P(video_view), P(photo_expand), P(share), P(dwell)`. Plus three share sub-types tracked separately: generic share, DM share, copy-link share.
- **Scoring template** — `Final Score = Σ (weight_i × P(action_i))`, with the README explicitly noting "positive actions (like, repost, share) have positive weights. Negative actions (block, mute, report) have negative weights."
- **Candidate isolation** — posts are scored independently in a batch; a post's score does NOT depend on what else is in the candidate set. Operator implication: there is no in-batch "stuff a viral post into a cluster of weak ones to relatively rank higher" exploit anymore. The signal must be intrinsic to the post.

The repo does NOT publish:

- **Numerical weight coefficients** (the multipliers — see (2) below for what's known and how).
- **The trained Phoenix model weights** (the May 2026 release ships a small pre-trained inference model but not the production model).
- **Hashtag / link / spam detector thresholds** (these now live inside the transformer's learned representation; there is no separate feature pipeline to inspect).

**Implication for the judge.** We have a stable architectural picture (ten action probabilities; positive-vs-negative direction) but no stable numerical anchors. The judge prose must encode the *direction of effect* on a small set of reader behaviors, never specific weight numbers. The numbers move; the direction (reply > like, dwell > scroll-past, mute kills) is stable.

### 2. The reconstructed engagement weights and how to treat them

Independent operator analyses (OpenTweet, Typefully, Wallaroo, Glitchwire, Slim Boulahouech on Medium, AutoTweet, indieradar) converge on a recognizable engagement-weight stack but disagree on exact numbers:

| Signal | OpenTweet Jan-26 | Typefully Jan-26 | Glitchwire May-26 | Bias direction |
|---|---|---|---|---|
| Like | 1 (baseline 0.5) | 1 | 0.5 | + |
| Bookmark | 10× | 10× | ≈10× | + |
| Profile click | 12× | 12× | "+12 weight" | + |
| Link click | 11× | 11× | — | + |
| Repost | 20× | 20× | ≈20× | + |
| Quote tweet | 25× | 25× | — | + |
| Reply | 13.5× (formula) / 27× (with author response) | 27× | 13.5× | + |
| Reply with author-response | 150× | 150× | 150× | + |
| Dwell (per second / 2-min+) | "+10 weight" bonus | not quantified | not quantified | + |
| Block | −3 (vs +0.5 like = 6× negative) | — | −3 | − |
| Mute / not-interested / report | ≈−74× | "punch above their weight" | ≈−74× | − |

The 13.5× vs 27× discrepancy for "reply" appears to be: 13.5× is the bare-formula coefficient (the reply weight alone, independent of the chain that follows), and 27× is the practical multiplier observed when the reply triggers downstream signal (author engages with it, conversation thread builds). 150× ("conversation") is the full chain. All three numbers describe the same underlying mechanic at different chain lengths.

**Operator-data triangulation.** The 13.5× / 20× / 27× / 150× / −74× cluster appears with citation in at least four independent 2026 analyses (OpenTweet, Typefully, Glitchwire, IndieRadar) and is the closest thing to verified operator data. The Slim Boulahouech Medium analysis (Jan 2026) ran A/B tests on his ~50k-follower account and reported reply-shaped posts hit 4–8× the impression of like-shaped posts holding topic constant — a result consistent with reply being heavily over-weighted vs like.

**Verdict for the judge.** The 27× reply-weight claim is empirically supported as a direction-of-effect but should not be cited as a number in rubric prose. The judge tests whether the post earns the reply, not whether the post "looks like a reply-eligible post."

### 3. What's PROMOTED in 2026 (and the observable post-features that predict it)

**Reply (≈13.5× alone, ≈27× with author-response, ≈150× full conversation).** Substantive replies — the kind that produce a back-and-forth — are the single most-rewarded action.

- Predictive post-features (correlational, not load-bearing): post asserts a falsifiable claim a peer could dispute (Mack, Bloom); post opens a genuine question the author doesn't already know the answer to (Isenberg's post-as-MVP); post takes a position that contradicts conventional wisdom in the niche.
- *Anti-feature* the judge must NOT reward: "What do you think?" CTAs ending the post, "Like if you agree" reply-bait, planted controversy. These are the engagement-farming tells now algorithmically suppressed since 2024 and Grok-flagged in current policy.
- Judge framing: outcome — would a relevant peer write back with substance, not "Great post!"?

**Repost (≈20×).** The repost is "I want my network to see this." Conviction-level endorsement.

- Predictive: claims that are screenshot-survivable (Bloom); counter-stereotype framings that surprise the reader (Mack); compressed essays (Naval-style 6-word reframings); specific knowledge the reader hasn't seen elsewhere.
- *Anti-feature*: "Repost if you agree" CTAs (engagement-farming, suppressed); generic platitudes that earn likes-not-reposts.
- Judge framing: outcome — would a 100k-follower creator in this niche repost this?

**Bookmark (≈10×).** Save for later — reader signals "I'll come back to this."

- Predictive: practical, actionable claims with specific named entities, numbers, dates (Koe PPP "Practical" leg); long-form posts with structured takeaways; threads with reference-grade information density.
- *Anti-feature*: "Bookmark this" prompts (now flagged as manipulation); pad-with-emojis "save this thread for later" tells.
- Judge framing: outcome — is there something here a reader would need to consult again within a week?

**Profile click (≈12×).** "Who wrote this? I want to see more."

- Predictive: distinctive voice signature recognizable across posts (Welsh content-matrix consistency); a single post that implies the author has a deeper body of work (Naval-style); first-person specifics that hint at lived experience (Naval "specific knowledge" test).
- Judge framing: outcome — would the reader want to know what else this person has written?

**Long-dwell (2+ minutes; +10 weight bonus).** The reader actually reads the whole thing.

- Predictive: density-matched form (single post ≤280 chars with one claim; thread of 3–7 units each revealing something new — Cole/Bush "Rate of Revelation"); not padded; not buried.
- *Anti-feature*: padded threads where dwell is "stuck scrolling past restated points," wall-of-text single posts no scroller will parse.
- Judge framing: outcome — would the reader still be reading at the bottom?

**Share sub-types (generic / DM / copy-link, tracked separately as of May 2026).** The DM-share and copy-link tells suggest the post lives outside-platform too.

- Predictive: posts that work as standalone artifacts (Bloom paradoxes); posts that survive being quoted with attribution stripped (the screenshot-survivability test).
- Judge framing: would a reader send this to a friend in DM with no context?

**Video completion (50%+ of <60s native video).** Newer signal, less load-bearing for our text-focused x_engine lane.

- Predictive (not in scope for text drafts): tight cuts, first-3-seconds payoff, native-uploaded not link-embedded.
- For the x_engine lane this lives in `structural_gate` if/when video drafts enter scope.

### 4. What's DEMOTED — what zeroes reach

**External links in the main post body (30–94% reach reduction, near-zero distribution for non-Premium accounts since Q1 2026).** The single biggest demoter operator content from 2024 underestimates. The mechanism is NOT a hard heuristic — it's that Phoenix learned (during 2024–2025) that link-containing posts predict session-end (reader leaves X), which propagates to lower P(action) across every downstream signal. Posts with links in body get suppressed even before negative signals fire.

- Workaround documented in the operator literature: post the link as the *first reply* to your own top-level post. The top-level post then ranks normally and the link is one tap away. This is now standard creator hygiene.
- Implication for the judge: a post drafted with an external URL in body should score against this. But this is a `structural_gate` check (URL-in-body → drop), not a judge criterion. The judge sees the post after `slop_gate`/`structural_gate` filters this out.

**Negative signals — block, mute, report, "not interested" — at ≈−74×.** One negative action erases ~150 likes. The asymmetry is the load-bearing mechanic.

- Predictive of negative signals: hot-take-without-evidence (likes-yes, replies-no, mutes-yes = net negative); fake-vulnerability bait; performative parasocial signaling; commodity AI-slop content (the reader hits "not interested" because they've seen the pattern in their feed eight times this week).
- The judge tests for these via X-3 (falsifiability — hot takes without evidence don't pass) and X-5 (voice / screenshot test — AI-slop signatures don't pass).

**Excessive hashtags (3+ → ≈40% reach reduction; 5+ → spam flag).** Hashtag count is deterministic; lives in `structural_gate`. The judge does NOT score it.

**Engagement-farming patterns (suppressed since 2024, intensified in 2026 under Grok).** "Like if you agree," "RT if X," binary-choice provocation polls, "Drop a 🔥 if you got value," planted-controversy reply farming. These are Grok-flagged in current policy docs.

- The judge tests for these via X-3 (substantive vs manufactured controversy) and X-1 (genuine tension vs templated bait-shape).

**Quote-tweet-of-own-post-for-amplification.** Grok-flagged manipulation. Lives outside the judge scope (operator behavior, not post content).

**Posts that don't end with an "open door."** A flourish-ending earns likes; an opening-question earns replies. The post that terminates with a stinger and nothing else is implicitly demoted because it never triggers reply / repost. This is correlation not causation; the judge encodes it through X-3 (does the claim invite substantive disagreement?).

**"Subscribers-only" Premium-gated content.** Demoted from out-of-network recommendation (Typefully Jan-26). Operator constraint, not judge concern.

**Community-noted posts.** Moderate distribution penalty while the note is active. Operator concern (don't post misinformation); not a judge criterion at the draft level — the note arrives post-publication.

### 5. The 2024 → 2026 shifts operator content misses

Operator content written before January 2026 (i.e., before the open-source release) frequently relies on outdated assumptions:

- **Phoenix replaces hand-engineered features.** Pre-2026 operator advice assumed feature tables: "the algorithm checks for hashtag count, then link count, then keyword match." That's gone. Phoenix is a learned transformer reading semantic content. Implication: surface-marker hacks (specific punctuation, specific opener template, specific emoji) don't survive — the model reads semantics, not syntax. The judge benefits because it can avoid syntactic anchors and lean on semantic outcome questions.
- **Grok-tone analysis is new.** Multiple 2026 sources (Glitchwire, OpenTweet, Pramod Singh, Wallaroo) report that Phoenix factors "tone of voice" — constructive / curious / positive tones get wider distribution; combative / negative / aggressive tones get reduced visibility. This is not the same as keyword filtering; it's learned representation. Implication for the judge: a falsifiable, disagreeable, substantive claim is rewarded (X-3 passes); a *combative-and-empty* hot take is penalized (fails X-3 because the claim is unfalsifiable + likely triggers mutes). The judge's existing X-3 spec handles this without special-casing.
- **Premium boost is structural, not promotional.** Pre-2026 lore treated Premium as a marketing tier ("verified accounts get extra reach as a perk"). 2026 confirms it's baked into ranking: ≈+4× in-network, ≈+2× out-of-network. This means non-Premium accounts now hit ≈100 median impressions vs ≈600 for Premium. Not a judge concern (the judge doesn't know the account's tier), but worth flagging in the open-questions: the *same draft* will perform very differently across Premium vs non-Premium.
- **External link suppression intensified through 2025.** The 30–50% penalty cited in older sources is now 94% in Q1 2026 cohort tests (PPC.land, multiple operator A/B tests). The "link in first reply" workaround is now standard. Implication for `structural_gate`: link-in-body drafts should be downscored or auto-rewritten to link-in-reply form *before* the judge sees them.
- **Reply volume up 21% YoY; repost volume up 35%.** The platform's center of gravity is shifting from like-shaped to reply-and-repost-shaped engagement (Sprout Social, Digital Applied 2026 stats). Operator advice from 2023–2024 over-indexed on likes; 2026 advice (and the judge) should over-index on substantive replies and convicted reposts.
- **Engagement velocity matters more than total.** "50 likes in the first 30 minutes outperforms 100 likes over 24 hours" (multiple operator A/B reports). Time-decay is ~50%/6 hours. Practical implication: the post's first-90-minute substantive reply is the load-bearing signal — not because the algorithm has a magic 90-minute window, but because that's when the post enters the out-of-network fanout. The judge already targets this via X-1 (earns the next tap from a scroller) and X-3 (earns a substantive reply).
- **Community Notes ranking is now its own published algorithm** (communitynotes.x.com/guide/en/under-the-hood/ranking-notes) with matrix-factorization-based "bridging" — a note is "helpful" if users who normally disagree both rate it helpful. Out-of-scope for the x_engine judge (Community Notes are downstream of publication), but useful context: misinformation-flavored drafts will trigger the bridging algorithm post-publication and lose distribution. The X-3 falsifiability criterion partially protects against this by requiring substantive claims that survive scrutiny.

### 6. How the judge scores "engineered for current algorithm" without becoming a rules-checker

This is the load-bearing question for the algorithm-axis research. The temptation is to walk down the published weights and create one criterion per signal: "does the post earn a reply (X-Reply)?", "does the post avoid external links (X-NoLink)?", "does the post earn a bookmark (X-Bookmark)?". This is precisely the feature-checking pathology that produced the Phase 4 rollback at `c76f051` (per `judge-design-guide.md` §11.1 and incident catalog).

**The right framing — outcome-questions about reader behavior, structural surface routed to `structural_gate`.**

The current draft x_engine spec (`2026-05-18-judge-design-step1-x-engine.md`) already implements this correctly via 5 criteria:

- **X-1 (earns the next tap)** — observable behavior: scroller stops, dwell-time registers. Algorithm proxy: dwell, profile_click. No mention of dwell weight or scroller in prose; the prose asks "would a relevant power-user stop and either tap or pause?"
- **X-2 (specific knowledge / lived-experience)** — observable behavior: peer recognizes lived experience, bookmarks, profile-clicks for more. Algorithm proxy: bookmark (10×), profile_click (12×). The prose asks about the reader's recognition, not about features that "look bookmarkable."
- **X-3 (falsifiable claim)** — observable behavior: peer disagrees substantively, replies. Algorithm proxy: reply (27×), reply-with-author-response (150×). The prose asks "could a peer substantively disagree?" — NOT "does the post end with a question?"
- **X-4 (form matches function)** — observable behavior: each unit earns its place; reader doesn't drop out mid-thread. Algorithm proxy: dwell. Prose tests Rate-of-Revelation, NOT a fixed thread-length.
- **X-5 (voice / screenshot survivability)** — observable behavior: screenshot survives without context, reader recognizes voice, peers share. Algorithm proxy: share, repost. Prose tests AI-slop signature stack + voice consistency, NOT specific punctuation.

**The Goodhart-resistance argument.** Each criterion targets reader behavior the algorithm proxies. The workflow cannot game the criterion by adding a surface marker (a specific opener template, a specific punctuation pattern, a specific length) because the criterion checks the *effect on the reader's likely behavior*, not the marker. As the algorithm changes (and it will — May 2026 already shipped an architectural refresh), the reader behaviors stay roughly stable: "would a power-user stop and read this" is invariant; "does this start with a specific number" is not.

**What's deliberately NOT a criterion (verified against the algorithm axis).**

- **No "earns a reply" criterion** — even though reply is the highest-weighted positive signal. Reason: "earns a reply" collapses to feature-checking ("ends with a question") within 5–10 generations under selection pressure. X-3 (falsifiability) is the reader-behavior shape that proxies this without inviting CTA-stuffing.
- **No "avoids external link" criterion** — links are deterministic and live in `structural_gate`. Confirmed routing in §3 of the spec.
- **No "uses Premium-tier voice" criterion** — Premium boost is account-level, not draft-level; the draft has the same quality regardless of tier.
- **No "matches Grok tone" criterion** — tone is captured by X-3 (substantive falsifiability) + X-5 (account voice); a separate tone criterion would over-correlate.
- **No weight numbers in prose** — the judge prose mentions zero numerical weights. The wrapper paragraph in the current spec (§5) mentions `reply (13.5×), repost (20×), bookmark (10×), long-dwell (+10×), negative (−74×)` as context for the scoring task. **Recommendation:** this context paragraph should be re-examined; named numbers in the wrapper prose are still feature-anchors and risk Goodhart at the wrapper level. Better wrapper: "the post should earn substantive replies, reposts, bookmarks, and long-dwell from relevant readers; it should avoid the kind of content that triggers mutes, blocks, or 'not interested' clicks." Direction of effect, no numbers.

### 7. Recommendations — what's outcome-question vs structural_gate vs sample-and-flag

**Outcome-questions (in the judge prose, behavioral anchors, no algorithm-feature names):**

1. Earns the next tap from a relevant scroller — proxies dwell + profile_click. → **X-1 (current spec, KEEP).**
2. Carries specific knowledge a generative model alone couldn't produce — proxies bookmark + profile_click. → **X-2 (current spec, KEEP).**
3. Asserts something falsifiable a peer could substantively disagree with — proxies reply + author-response + repost. → **X-3 (current spec, KEEP).**
4. Form matches density of claim, each unit earns its place — proxies long-dwell. → **X-4 (current spec, KEEP).**
5. Survives the screenshot test and matches account voice — proxies share + repost + DM-share. → **X-5 (current spec, KEEP).**

The current 5-criterion spec is correct on the algorithm axis. No new criteria needed; no existing criteria need rewriting on this axis.

**Structural_gate (deterministic, routed away from the judge per §2 of the design guide):**

1. **External link in post body** — auto-suppress / auto-rewrite to first-reply form. Link presence in body should fail `structural_gate` (or be rewritten before scoring).
2. **Hashtag count >2** — fail or strip.
3. **Character count over 280 for non-thread single posts** — already handled.
4. **Thread continuity** (no broken reply chains, no orphan replies) — handled by `slop_gate`.
5. **Engagement-farming CTAs literal-string match** — "Like if you agree," "RT if X," "Bookmark this," "Drop a 🔥," "Follow me for more" — these are deterministic catches. The current `slop_gate` should cover these; confirm coverage. NOT a judge criterion (would be feature-checking).
6. **Quote-tweet of own post for amplification** — operator behavior, not artifact content; outside judge scope.
7. **Subscribers-only / Premium-gated draft** — flag if present, but not load-bearing.
8. **>10 posts per day from same account** — account-level, not draft-level; outside scope.

**Sample-and-flag (lightweight LLM check, NOT scored, used to track drift):**

1. **Grok-tone proxy** — sample 10% of drafts and run a lightweight tone classifier (constructive / neutral / combative-empty). If a generation shows ≥30% combative-empty drafts, flag the workflow for inspection. Goal: catch when the workflow learns to mimic edgy-takes-without-substance even when X-3 is passing on a surface read.
2. **Reply-bait CTA detector** — sample drafts for end-of-post bait patterns ("what do you think?", "agree or disagree?", "drop your thoughts below"). Track per-generation rate. If rising, the workflow is templating toward reply-bait — flag.
3. **AI-slop signature density** — count em-dashes, tricolons, "moreover/furthermore/delve" tokens across the generation. If density rises monotonically across 3 generations, flag — even if X-5 is still passing per-fixture, the workflow may be drifting toward slop on average.
4. **Community Notes risk proxy** — sample drafts for unsourced specific-numeric claims (e.g., "97% of founders fail"). High volume of unsourced specifics correlates with post-publication note risk. Flag for human review.

These four "sample-and-flag" probes are NOT judge criteria — they're variance-instrumentation in the §11.5 sense of the design guide. They run alongside the judge, generate telemetry, and trigger redesign rather than score.

### 8. Goodhart-resistance verification on the algorithm axis

Per `judge-design-guide.md` §11, each criterion gets walked through the "what does the workflow do to game this?" test:

- **X-1 (next tap):** Goodhart attempt — every post opens with a number or counter-intuitive declaration. Test: does the second unit actually resolve the tension, or is it a non-sequitur? CoT step 2 catches non-sequitur openings. Passes.
- **X-2 (specific knowledge):** Goodhart attempt — fabricate specific-looking details. Test: does the specific claim hold up against the niche reader's knowledge? Judge can't verify ground-truth, but can flag obvious confabulation patterns (e.g., "according to a 2023 study by Stanford" with no journal name). Partial pass; needs sample-and-flag (4) above to catch sustained confabulation drift.
- **X-3 (falsifiability):** Goodhart attempt — manufacture controversy. Test: is the disagreement substantive or stylistic? CoT step 2 enforces substantive test. Passes.
- **X-4 (form matches function):** Goodhart attempt — always-5-tweet threads regardless of content density. Test: per-unit rate-of-revelation. CoT step 2. Passes.
- **X-5 (voice):** Goodhart attempt — avoid em-dashes by replacing with parentheticals (different surface tell, same model-collapse). Test: AI-slop is a pattern stack, judge tests gestalt. Passes — and the sample-and-flag (3) above catches sustained drift across patterns.

**The wrapper-prose risk.** As noted in §6, the current wrapper prose names numerical weights. This is a soft Goodhart vector — the workflow may infer "the judge cares about replies, reposts, bookmarks, dwell" from the wrapper itself and start template-fitting. Recommendation: replace the numerical-weight enumeration in the wrapper with direction-of-effect prose. Lower risk, same orientation.

---

## Open Questions

1. **Wrapper-prose numeric weights — keep or strip?** The current spec wrapper names `reply (13.5×), repost (20×), bookmark (10×), long-dwell (+10×), negative (−74×)`. These are direction-anchors but also potential surface-feature anchors. Decision pending: replace with direction-only prose vs keep for judge calibration. Recommend strip.
2. **Cold-start handling for X-2 and X-5.** When the account has no prior voice data, X-2 (lived-experience test) and X-5 (voice consistency test) both lose their reference. The linkedin_engine v040 cold-start mutation memo flags an analogous gap. Recommend: when source_data has <5 prior posts for the account, route to 0.5-unknown for X-5 specifically; X-2 should still score because lived-experience is about the claim, not voice.
3. **Premium vs non-Premium account context.** Premium ≈+4× in-network, ≈+2× out-of-network is account-level. Should the wrapper acknowledge tier? Recommend no — the draft's *quality* is invariant to tier; the *distribution* is not. The judge scores quality.
4. **Phoenix model retraining cadence — judge stability implication.** The May 2026 release shows Phoenix is iterated regularly. If the algorithm shifts, the direction-of-effect anchors in this research could drift. Recommend: re-run this axis quarterly; track whether `reply > like > repost > bookmark > profile_click` ordering still holds.
5. **Tone-based ranking and falsifiable disagreement.** Phoenix's tone analysis reportedly demotes "combative" tones. But X-3 explicitly rewards substantive falsifiable disagreement. There's a tension: does substantive disagreement read as combative to Grok? Operator data suggests no — Phoenix distinguishes constructive disagreement from rage-bait. But this is unverified at the post level; worth a 1-month sample-and-flag probe of X-3 high-scoring posts to see if they actually earn reach.
6. **Video drafts.** Out of scope for current x_engine spec but in scope for future versions. The 50%+ completion threshold for <60s native video is a structural_gate item when video drafts enter scope.
7. **The 13.5× vs 27× reply-weight ambiguity.** This is unresolved in the operator literature — different sources cite different numbers depending on whether they're describing the bare coefficient or the chain-multiplier. Not load-bearing for the judge (we don't cite numbers), but the lane operators may want clarity for telemetry interpretation.
8. **Three-share-types signal (generic / DM / copy-link) — does the judge benefit from this distinction?** Current X-5 (voice / screenshot) captures the gestalt but doesn't separately test copy-link vs DM-share. Probably not worth a sixth criterion; would correlate >0.7 with X-5 per the §5 redundancy check. Confirm in calibration.

---

## Citations

**Primary (open-source release):**
- [xai-org/x-algorithm GitHub repo (Jan 2026 + May 2026 update)](https://github.com/xai-org/x-algorithm) — repo README confirms ten predicted actions, scoring formula, candidate isolation, Grok-1-derived Phoenix transformer architecture. Numerical weights NOT published.
- [x-algorithm Phoenix README](https://github.com/xai-org/x-algorithm/blob/main/phoenix/README.md) — architecture detail.

**Operator-tested weight reconstructions (Jan 2026 cohort):**
- [The X Algorithm in 2026 — OpenTweet Blog](https://opentweet.io/blog/how-twitter-x-algorithm-works-2026) — 13.5× / 20× / 10× / +10 dwell / 6-hour decay.
- [10 X Algorithm Secrets — OpenTweet Blog](https://opentweet.io/blog/x-algorithm-secrets-2026) — +12 profile click weight, 3–5 posts/day cadence finding, 30–60-min initial scoring window.
- [Everything you need to know about X Algorithm — Typefully](https://typefully.com/blog/x-algorithm-open-source) — 27× reply weight, 25× quote, conversation 150×.
- [X Open-Sources Its Algorithm Again — Glitchwire](https://glitchwire.com/news/x-open-sources-its-algorithm-again-10-things-you-need-to-know-about-how-your-fee/) — full ten-point weight reconstruction including −3 block, −74× mute/report, +4× Premium in-network, +2× Premium out-of-network.
- [How the X Algorithm Works in 2026 (Source Code) — PostEverywhere](https://posteverywhere.ai/blog/how-the-x-twitter-algorithm-works) — formula breakdown.
- [X Algorithm Open Source: May 15 Update — Pasquale Pillitteri](https://pasqualepillitteri.it/en/news/2594/x-algorithm-open-source-may-2026) — May 2026 refresh details.
- [They Just Open-Sourced The X Algorithm — Slim Boulahouech, Medium](https://medium.com/@slim.boulahouech/they-just-open-sourced-the-x-algorithm-here-are-the-new-rules-for-viral-growth-aefbcfc84e76) — operator A/B data, ~50k-follower cohort.
- [X Algorithm Explained — AutoTweet](https://www.autotweet.io/blog/x-algorithm-explained-2026) — additional weight confirmations.
- [X Algorithm 2026: Inside the Open-Source Code — IndieRadar](https://indieradar.app/blog/x-algorithm-2026-open-source-code-guide) — share sub-types (generic / DM / copy-link).
- [X Algorithm Explained — Ajit Singh](https://singhajit.com/system-design/x-twitter-for-you-algorithm/) — system-design walkthrough.

**External-link suppression:**
- [Simon Hayes operator-data thread on X](https://x.com/Hayess5178/status/2010846576252535245) — 30–50% link penalty cite, January 2026.
- [How X's algorithm silently kills your links — PPC.land](https://ppc.land/how-xs-algorithm-silently-kills-your-links-without-explicitly-penalizing-them/) — Q1 2026 94% visibility reduction A/B finding.
- [X softens stance on external links — Tomorrow's Publisher](https://tomorrowspublisher.today/content-creation/x-softens-stance-on-external-links/) — counterpoint / nuance.

**2025–2026 platform shifts:**
- [Twitter/X Statistics 2026 — Digital Applied](https://www.digitalapplied.com/blog/twitter-x-statistics-2026-marketing-data-points) — replies +21% YoY, reposts +35% YoY, engagement +19%.
- [Sprout Social: Twitter Algorithm 2026](https://sproutsocial.com/insights/twitter-algorithm/) — platform-level practitioner summary.
- [SocialBee: X Algorithm 2026](https://socialbee.com/blog/twitter-algorithm/) — negative weights, Premium boost.
- [Pramod Singh on Grok-AI shift](https://x.com/SinghPramod2784/status/2034908220905652580) — Grok-powered model transition context.

**Community Notes:**
- [Community Notes Ranking Algorithm — communitynotes.x.com](https://communitynotes.x.com/guide/en/under-the-hood/ranking-notes) — matrix-factorization bridging algorithm.

**Engagement-farming policy:**
- [Engagement Bait Tactics — SuccessOnX](https://successonx.com/guides/what-to-avoid/twitter-engagement-bait-traps) — named bait patterns suppressed since 2024.
- [How to Go Viral on X — PostEverywhere](https://posteverywhere.ai/blog/how-to-go-viral-on-x) — engagement-farming detection signals.

**Press / context:**
- [X open sources its algorithm — TechCrunch](https://techcrunch.com/2026/01/20/x-open-sources-its-algorithm-while-facing-a-transparency-fine-and-grok-controversies/) — release context.
- [Wallaroo Media: X Algorithm Explained Jan 2026](https://wallaroomedia.com/x-algorithm-explained/) — practitioner-facing summary.
- [VentureBeat: X open sources algorithm](https://venturebeat.com/data/x-open-sources-its-algorithm-5-ways-businesses-can-benefit) — business-analyst frame.

---

## Notes for Rubric Authors

1. **The five criteria in the current spec correctly target the algorithm-axis without becoming algorithm-rules-checkers.** No new criteria needed on this axis. The current shape — outcome questions about reader behaviors that the algorithm proxies — is the load-bearing design move.
2. **Strip numerical weights from the wrapper prose.** Replace with direction-of-effect language. This is the single concrete recommendation from this axis.
3. **External-link handling stays in `structural_gate`** (or `slop_gate`). Do not import the link-penalty into the judge as a criterion. Confirm current `slop_gate` covers `https?://` URL detection in post body; if not, add it.
4. **Engagement-farming literal-string detection in `structural_gate`.** "Like if you agree," "RT if X," "Bookmark this," "Drop a 🔥 if," "Follow me for more" — deterministic, route to gate.
5. **Add four sample-and-flag probes** for variance instrumentation per `judge-design-guide.md` §11.5: Grok-tone proxy, reply-bait CTA detector, AI-slop signature density across generations, unsourced-specific-numeric-claim detector. None of these are judge criteria; all are telemetry.
6. **Re-run this axis quarterly.** Phoenix is iterated regularly (May 2026 refresh confirms). The 5-criterion outcome-question shape is durable; the underlying weights and operator data are not. Direction-of-effect anchors should hold; specific numeric reconstructions will drift.
7. **The judge's wrapper paragraph should NOT name the algorithm.** Mentioning "the Phoenix transformer" or "Grok-based ranking" in judge prose risks the judge attending to algorithm-implementation features rather than reader behaviors. Keep it reader-shaped.
