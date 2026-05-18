---
date: 2026-05-18 v1
type: judge-design Step 1 — x_engine optimal-output spec
status: DRAFT v1 — Path-A iteration; ready for redundancy check + fixture validation + propagation
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
companions:
  - docs/research/2026-05-18-judges-domain-x-engine.md (generalist x_engine domain research)
  - docs/research/2026-05-18-x-engine-algorithm-jan-2026.md (algorithm-signals axis)
  - docs/research/2026-05-18-x-engine-hook-discipline.md (hook discipline axis)
  - docs/research/2026-05-18-x-engine-voice-screenshot-test.md (voice / screenshot axis)
  - docs/research/2026-05-18-x-engine-ai-slop-detection.md (AI-slop detection axis)
revision_history:
  - 2026-05-18 v0 — initial 5-criterion skeleton with numeric algorithm weights in wrapper, em-dash/moreover/tricolon enumeration in X-5 score-0
  - 2026-05-18 v1 — Path-A iteration grounded in 4 deep-research deliverables. Stripped numerical weights from §5 wrapper → direction-of-effect language. Strengthened X-1 with 3-axis CoT (forward-vector / first-fixation-survivable / hook-body alignment). Reworked X-5 with gestalt-stack language, "looks like slop but isn't" defense, X-vs-LinkedIn register check, explicit cold-start sub-anchor. Routed em-dash / banned-phrase / tricolon / "Stop X. Start Y." / listicle-parallelism / link-suppression / hashtag enumeration OUT of judge into 6 structural_gate checks (~120 LOC). Added 3 sample-and-flag telemetry signals. 5-criterion ceiling held (potential X-6 hook-body alignment deferred to §8 — promote only if empirical variance forces).
---

# X Engine — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md`. Frameworks (Welsh content matrix, Cole/Bush *Ship 30* 1 Chip Rule + 1-3-1 Rhythm + Rate of Revelation, Naval specific-knowledge, Bloom paradox/razor, Mack counter-stereotype, Veerasamy units-of-consideration, Hormozi jab-jab-jab-right-hook, Isenberg post-as-MVP, Schneider distribution-first, Koe PPP) inform the reader/success/failure spec and the judge's private reasoning toolkit. They do NOT appear by name in criterion prose.

This v1 supersedes v0 after a Path-A iteration grounded in 4 deep-research deliverables: algorithm-signals (Jan-2026 open-source release), hook discipline (forward-vector / first-fixation / hook-body alignment), voice / screenshot-test (stylometry + Wang et al. EMNLP 2025), and AI-slop detection (Dawkins et al. 2025 at 54% detection accuracy on fine-tuned voice models). The v0 miscalibrations corrected: (a) named numerical algorithm weights in the wrapper (operator-community reconstructions, not official; soft Goodhart vector); (b) em-dash / "moreover" / tricolon enumeration in X-5 score-0 (~30% FPR on real authors per Goedecke 2025 + The Ringer 2025); (c) X-1 testing only forward-vector presence, missing the clickbait failure mode. The v0 simplification ("judge tests outcomes, not surface features") stays load-bearing — what v1 adds is research-grounded specificity on encoding each outcome question to survive 50 generations of selection pressure.

---

## 1. Reader (LOCKED 2026-05-18)

**Primary reader.** A power-user on X with Premium subscription, scrolling the For-You feed on a phone with ~0.5 seconds of attention per post: a topical-niche scroller (B2B founder, indie hacker, growth marketer, writer, researcher, or domain specialist) arriving via interest-graph fanout — ~50% of any For-You feed is out-of-network content surfaced by SimClusters + Grok-based candidate retrieval (per xai-org/x-algorithm Jan 2026). Commitment to expand / reply / repost / bookmark / profile-click happens inside the first 400–700ms based on first-fixation lexical features; full-post read happens only if the opening earned that commitment. They are slop-aware — by mid-2026 most active power-users pattern-match AI-generated content and hit "not interested" (negative-signal cluster) on recognizable slop before the third line.

**Secondary reader: the algorithm.** Phoenix (Grok-1-derived transformer, candidate-isolated scoring) reads the post as semantic content — no separate hashtag-lookup table, no keyword-multiplier pipeline. It outputs ten action probabilities (favorite, reply, repost, quote, click, profile_click, video_view, photo_expand, share, dwell) combined via positive-and-negative-weighted summation. Reply, repost, bookmark, and long-dwell are heavily-positive; mute, block, "not interested," and report are heavily-negative. Phoenix also reportedly factors tone-of-voice (constructive distribution > combative). Primary and secondary readers align: the algorithm rewards what the scroller actually does, so a post that earns substantive scroller engagement earns algorithmic out-of-network fanout.

**Substitute readers the same post should also serve:** a peer practitioner in the niche who would substantively reply, quote-tweet with a real add, or want to disagree publicly; a 100k+-follower creator who would repost or copy-link to DM; an interest-graph adjacent scroller surfaced via SimClusters fanout; an AI-aware reader who would recognize "generic founder voice" within one fixation and bail.

**NOT the reader.** Bot accounts (negative signal source, not target); engagement-farming peers (artificial signal, not target); the author's first-degree network alone (golden-hour kick, not the goal — fanout requires winning second-and-third-degree out-of-network); a long-form reader from a blog (different commitment regime — they've already committed; the X scroller has not).

**First-cohort overfitting watch.** The reader spec is research-grounded against English-language Anglosphere founder/operator voice (Naval, Bloom, Mack, Welsh, Schneider, Veerasamy, Graham, Andreessen as exemplars). gofreddy's first-cohort includes Polish-language operators (DWF lawyers, Klinika dermatology) where the architectural shape applies (peer-not-broadcast, punchy-not-narrative, schema-violation-as-hook) but specific lexical anti-patterns (em-dash conventions, discourse markers) need separate calibration. The criteria below test mechanisms that are language-universal at the cognitive-load level; the lexical surface enforcement in `structural_gate` is English-calibrated and needs a Polish-language fixture pass before locking. See §8 open-question 7.

---

## 1.5. Artifact shape (LOCKED 2026-05-18)

The lane produces ONE of two artifact shapes, per practitioner literature converging on Veerasamy unit-of-consideration + Cole/Bush 1-3-1 rhythm + Naval thread-as-essay:

1. **Single X post** — one tweet, ≤280 chars, exactly one coherent claim that resolves within the post.
2. **Thread of 3–12 tweets** — opening tweet promises a trajectory; each subsequent unit instantiates one beat and reveals something the prior unit did not (Rate of Revelation per unit). Veerasamy's 3–7 typical, up to ~12 max.

**Locked because shape-drift Goodhart is a documented failure mode.** Under 50-generation selection pressure, the workflow would learn that dense-single-post outputs score well on X-2 while expansive-thread outputs score well on X-4, producing Frankenstein artifacts (wall-of-text "threads" of 2 dense tweets; padded single-posts that should have been threads). The lock prevents this.

**Out-of-scope shapes (lane will NOT produce these):**
- Long-form essay or article cross-posted to X (X-native register differs; lives in `site_engine` / `linkedin_engine`)
- Multi-thread series ("part 1 of 5") — forces multi-post commitment, collapses single-post and thread signal
- Screenshot-of-text post (photo_expand-dominant ranking regime; separate calibration)
- Image carousel
- Native video draft under 60s — video_view + 50%-completion signal lives in `structural_gate` if/when video drafts enter scope; out of judge scope for v1

**Shape enforcement lives in `structural_gate`, NOT in judge criteria.** Judge tests outcomes (X-1..X-5); `structural_gate` tests artifact-shape conformance (character count, thread unit-count band, thread reply-chain continuity). Per design guide §11.1, this preserves outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift.

**Empirical validation scope.** Two-shape spec is research-grounded against English-language Anglosphere founder/operator content. When fixtures from differently-shaped registers appear (Polish-language conversational, multi-language thread, post-with-quote-tweet-add), re-validate the form factor.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18)

After ~0.5 seconds the scroller stops; after ~3 seconds they take an action: tap to expand, reply substantively, repost with conviction, bookmark, profile-click, or pause long enough for dwell-time to fire (long-dwell ≥2 minutes per the open-source release). The post earns a substantive reply (not "Great post!") from at least one relevant peer in the first 90 minutes; that early substantive engagement drives algorithmic out-of-network fanout, which is where viral reach lives in 2026.

The post survives the screenshot test in the gestalt sense documented in the voice axis research: if a regular reader of this account encountered it in their feed without seeing the avatar, they would attribute it to this account specifically — not to "some founder." Generic founder voice (earnest, slightly conspiratorial, prescriptive, "what nobody tells you" framing) fails this test even when it earns first-day likes, because the second-fixation pattern-match by an AI-aware scroller recognizes the centroid voice and hits "not interested." Wang et al. EMNLP 2025 (arxiv 2509.14543) measures the mechanism: frontier LLMs default to an average generic tone under voice-imitation tasks, and few-shot demonstrations beyond ~10 give diminishing returns.

A peer in the niche would either repost without comment, quote-tweet with a substantive add, or want to disagree publicly. Posts that earn engagement-bait clicks ("Like if you agree," "Drop a 🔥") trigger Grok's `engagement_arbitrage` detector and the negative-signal cascade — these are NOT success even if they earn high impressions in the first 30 seconds.

**Sleep test.** If the scroller bookmarked and re-encountered the post 24 hours later, they would still find it worth their attention — the post's claim survives reflection, not just momentum. Posts that work on adrenaline but disappoint on re-read produce the bounce-after-hook gap that Phoenix's `engagement_arbitrage` penalizes.

**World-class real-world exemplars** — quality anchors, NOT templates to copy:

- **Naval's *How to Get Rich (without getting lucky)*** (230k+ likes, canonical thread-as-essay) — each tweet a coherent atomic claim that stands alone if quoted; specific knowledge from lived obsession; voice signature recognizable across years.
- **Bloom's paradox / razor / framework one-liners** — condenses a 5000-word essay into one screenshot-survivable claim. Uses tricolons + em-dashes substantively, not as AI tells, because rhetoric earns them.
- **Mack's *High Agency* counter-stereotype posts** — surfaces a person or situation whose attributes don't match the reader's stereotype; schema-violation forces additional processing → dwell-time.
- **Veerasamy threads** — 3–7 unit discipline; each unit a distinct move (define, exemplify, counter, anchor, generalize, test, close); Rate of Revelation enforced per-unit.
- **Welsh's content-matrix execution** — each post occupies a defensible 2×2 cell (topic × format); genre-clear outperforms genre-mixed.

What ties these together: forward-vector hook in the first 7 words; specific knowledge from lived experience; falsifiable claim inviting substantive disagreement; form matched to claim density; voice that survives screenshot with attribution stripped.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — four failure modes the judge must discriminate against

**Generic founder advice.** Reads as competent X content — has a hook, a specific number, ends with a question — but every claim is the centroid of "founder advice" prose. No named entities the author was present for; no dated specifics; no first-person details that survive Naval's specific-knowledge test. Reader recognizes template within 0.5 seconds and scrolls.

**Hot take without evidence.** Strong claim ("Most founders are wrong about X") earns instant likes (low weight) but no substantive replies (high weight), and triggers high mute rate among readers who recognize provocation without substance. Net algorithmic value: negative. Mack falsifiability test catches this — the hot take is unfalsifiable because the underlying claim is too vague to be wrong on substance.

**Catalog / clip dump.** List of niche facts ("Acme raised $40M; Beta hired a CRO"). No claim, no implication, no forward-vector — competitor-monitoring log re-shaped as content. Nothing earns the next tap.

**Vulnerability theater.** "I failed at X. Here's what I learned." / "Last year I almost went bankrupt. Three lessons." Carefully calibrated admission of failure that feels authentic but isn't threatening; followed by exactly-3 numbered lessons where the failure is non-specific (no named entity, dollar amount, or date) and the lessons are platitudes. Reader's parasocial filter catches it within two fixations. "Performative pathless path" failure per Millerd / Stoddart.

### 3b. Goodhart-collapse — four named AI-slop families (per AI-slop deep-research)

**Structural broetry.** "Stop X. Start Y." imperative-pair constructions stacked across a thread; every other tweet opens with negation-then-replacement antithesis. Endemic to AI-generated founder-advice content. Hormozi teaches the single-instance version; the slop variant is the *rhythm* — three of these in a 5-tweet thread is past any thoughtful operator's natural rate.

**Surface signature stack.** Em-dash density above account baseline + signature transitions ("moreover," "furthermore," "delve into," "in conclusion," "let me explain," "here's the thing") + three-element parallel constructions used reflexively + tricolons in every other paragraph. Any single tell is high-FPR against real operators (Naval uses em-dashes substantively; Bloom uses tricolons as foundational rhetoric); the slop fingerprint is the *stack* — 3+ co-occurring in a single post.

**Affective flatness.** Smooth, gradeless prose with no rough edges, no specific names, no dated claims, no commitments-with-cost. Cadence collapse — sentence-length variance compresses toward the 18–24-word AI-cadence plateau (Wang et al. EMNLP 2025 + 2026 burstiness stylometry consensus). Simulates authority but has not used a product or survived a failed launch.

**Algorithmic-affinity templating.** Phase 4 pathology rolled back at `c76f051`. Workflow learns to slot-fill surface markers: every post opens with a number or counter-intuitive declaration regardless of substance; every post namechecks a person with a fabricated quote; every thread is exactly 5 units; every post ends with a planted question to extract reply count; em-dashes get replaced with parentheticals (different surface, same model-collapse). Surface markers compliant, content underneath empty.

**Historical context.** This lane shares root pathology with the lanes that triggered three prior rollbacks: `2ce99bb` (σ-widening), `ca4a256` (v2 contract-prose), `698e658` (Phase 4 feature-checking → `c76f051`). Criteria below are designed to resist re-creating any of them AND to defend against the four AI-slop families above.

**Deterministic AI-slop checks live in `structural_gate`** — em-dash density >5/100w, signature-phrase blocklist, tricolon density, "Stop X. Start Y." regex, listicle-syntactic-uniformity above 0.85, external-link-in-body suppression flag (94% reach reduction per Q1 2026 PPC.land A/B data), >2 hashtag count. Per OpenRubrics (Hard Rules → `structural_gate`, Principles → judge): deterministic verification belongs in `structural_gate` because (a) the judge cannot enumerate features without inviting feature-checking, (b) deterministic checks fail closed with low FPR against real operator voice, (c) workflow has to evade all 6 checks simultaneously to game the gate, (d) gestalt judge catches the residual stack. AI-detector classifier output (GPTZero, Originality.ai, BERTweet) is NOT integrated — Dawkins et al. 2025 (arxiv 2506.09975) measures 54% detection on fine-tuned voice models; 15.6–17.6% FPR disproportionately penalizes non-native English writers (core to first-cohort).

---

## 4. Criteria — outcome questions (5)

### X-1 — Earns the next tap from a relevant scroller (hook discipline, 3-axis CoT)

**Outcome question (binary):**
Would a relevant X power-user — scrolling For-You at 0.5s/post, first-fixation commitment in 400–700ms — stop on this post and tap to expand, reply, repost, bookmark, or pause for dwell? And does the body deliver the specific gap the opening promised, rather than over-promising and producing the bounce-after-hook cliff?

**Score 1 (yes)** — The opening (first 1–2 sentences for a single post; opening tweet for a thread) opens a specific, bounded, finitely-closeable information gap the reader's brain commits to closing. It anchors first-fixation via ≥1 named entity, specific number, concrete noun, or schema-violating juxtaposition — and does NOT instantiate the topic-statement anti-pattern ("Today I want to talk about X") or the throat-clearing anti-pattern ("I've been thinking lately about Y"). The body delivers the gap: for single post, gap closes within the post; for thread, opening promises a trajectory and each subsequent unit instantiates one beat.

Example A (do not optimize toward this): "Seek wealth, not money or status." Six words; three named referents; forward-vector is the bounded question "what's the difference?" Body delivers by re-defining wealth as "assets that earn while you sleep" — gap closes specifically.

Example B (do not optimize toward this): "Pinsent Masons pulled 6 partners from CMS in May." Named entity + specific number + dated event; forward-vector is "what does this mean for our practice?" Thread delivers the lateral-flight analysis its first tweet promised.

**Score 0 (no)** — Opening instantiates topic-statement, throat-clearing, vague-promise ("Here's something that changed my life"), or cliché closed-loop ("Most people don't realize how important consistency is"). OR opening anchors first-fixation correctly but body fails to deliver the promised gap: hollow superlative (ordinary advice underneath); fake-revelation tease (contrarian framing was a vehicle for conventional content); numbered-list inflation (items 4–7 are restatements); cliffhanger-that-doesn't-pay; vulnerability bait. Bounce-after-hook gap fires.

**Score 0.5 (unknown)** — Opening framing depends on context not in the artifact (reply to unseen post, quote-tweet of unseen context). Emit 0.5 + "unknown" + one sentence on what context would resolve it.

**Required CoT (3 axes):**
- Step 1 (Axis B — first-fixation-survivable opening): Identify the opening (first ~7 words ±2 for single post; opening tweet for thread). Tag tokens as first-fixation-survivable (named entity, specific number, concrete noun, mid-narrative action verb, schema-violating juxtaposition) or abstract (motivational noun, hedge, topic-statement framing, throat-clearing). Flag topic-statement and throat-clearing anti-patterns.
- Step 2 (Axis A — forward-vector presence): Determine whether sentence two / tweet two is (a) predictable from the opening (cliché — fail), (b) unconstrained (vague promise — fail), or (c) bounded-but-unresolved (working hook — pass). Gap must be specific, bounded, finitely closeable (~3–15 words of resolution).
- Step 3 (Axis C — hook-body alignment): Identify what specific gap the opening promised. For single post, does the body close that specific gap? For thread, do subsequent units instantiate the promised trajectory (Rate of Revelation per unit)? Flag clickbait: hollow superlative, fake revelation, numbered-list inflation, cliffhanger that doesn't pay, vulnerability bait.
- Step 4: Emit verdict + one-sentence justification. Score 1 only if all three axes pass.

Do not score: hashtag count, emoji, formatting, exact character count (those live in `structural_gate`). Do not score literal first-7-words as a threshold — it's a working approximation the CoT applies as private reasoning.

### X-2 — Carries specific knowledge only this author could write

**Outcome question (binary):**
Would a relevant practitioner reading this post recognize it as written by someone with lived experience — not summarized from secondary sources, not regenerable from public-internet summarization?

**Score 1 (yes)** — Contains ≥1 specific detail (named person, dated event, specific number with provenance, unique anecdote, named project, specific failure with named context, dollar amount with attribution) demonstrating the author was present for the underlying experience. Claim cannot be regenerated by an LLM reading the public internet — required first-hand exposure.

Example A (do not optimize toward this): "Cody Schneider's '5,000 follows in 30–60 days, expect ~20% follow-back' is specific because he ran the experiment on his own account and published the result with numbers."

Example B (do not optimize toward this): "When I rolled out our SOC2 prep flow last quarter, 7 of the 12 customers said 'finally — the BambooHR compliance bundle requires us to do this manually'." Named entity + specific number + first-person observation.

**Score 0 (no)** — Every claim could appear in any productivity-niche post. No named entities the author was present for; no dated specifics; no first-person details. Generic platitude framed as wisdom. OR specific-looking details that are confabulated: fabricated quotes, made-up "Stanford 2023 study," conflated entities, dated events that don't exist (documented LLM failure mode).

**Score 0.5 (unknown)** — Single-line aphorism where lived-experience claim is ambiguous (could be quote-tweet, could be generic platitude, could be earned reframing). Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: List every specific entity, number, date, named project, or first-person anecdote.
- Step 2: For each, test whether the claim is non-regenerable from public-internet summarization. Flag specific-looking details reading as confabulated (no attribution, no resolvable provenance, conflated entities, non-existent dated events).
- Step 3: Emit verdict + one-sentence justification.

Do not score: total word count, presence of "I" pronouns, claim accuracy (judge can't verify; confabulation flagging is pattern recognition, not fact-checking).

### X-3 — Asserts something falsifiable a peer could substantively disagree with

**Outcome question (binary):**
Could a thoughtful peer in this niche say "I disagree, and here's why" — substantively, not stylistically? Is the claim wrong in at least one knowable way a peer could articulate?

**Score 1 (yes)** — Position contradicts at least one widely-held belief in its niche, OR claims a specific causal relationship the reader could test against their own experience, OR makes a falsifiable forward prediction. Claim is wrong in at least one knowable way — peer could write a substantive counter-thread, not just a stylistic complaint. Disagreement would be about substance (causal model, empirical claim, strategic prescription), not surface (tone, formatting, example choice).

Example A (do not optimize toward this): "Low-agency people are passengers in their own lives" — testable against any reader's autobiography; peer could substantively disagree by arguing low agency is structural rather than dispositional.

Example B (do not optimize toward this): "Most B2B newsletters that hit 1,000 subscribers got there by reposting LinkedIn content to email, not by building from email-first." Specific causal claim; peer could disagree by citing email-first newsletters that grew without LinkedIn repurposing.

**Score 0 (no)** — Unfalsifiable: tautology, generic platitude, claim so hedged no one could substantively disagree, manufactured controversy where the "disagreement" invited is stylistic. Earns likes, earns no substantive replies. Triggers high mute rate among readers who recognize provocation without substance.

**Score 0.5 (unknown)** — Falsifiability cannot be evaluated without knowing the account's prior positions (claim might be radical for this author and conventional for others); OR post is reply/quote-tweet where the parent context carries the load. Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: Identify the central claim.
- Step 2: Test whether a thoughtful peer could substantively disagree on substance — not stylistically, not on tone, not by criticizing example choice, but by arguing the underlying causal model or empirical claim is wrong.
- Step 3: Emit verdict + one-sentence justification.

Do not score: claim controversy level, "controversial opinion" markers, presence of "what do you think?" CTA (engagement-bait CTAs routed to `structural_gate`), whether the claim is actually true.

### X-4 — Form matches function — single post or 3–12-unit thread, no padding

**Outcome question (binary):**
Does the post's structure (single post vs thread) match the density of its claim? Does each unit earn its place — would removing any unit degrade the post?

**Score 1 (yes)** — Either (a) a single post under ~280 chars containing exactly one coherent claim that resolves within the post, OR (b) a thread of 3–12 tweets where each tweet reveals something the prior tweet did not (Rate of Revelation per unit). Removing any unit would degrade the post or break the promised trajectory.

Example A (do not optimize toward this): A 6-word Naval-style declarative reframing that condenses a 5000-word essay; single-post form earned because expansion would dilute.

Example B (do not optimize toward this): A 7-unit Veerasamy thread on courage where each unit is a distinct move (define, exemplify, counter, anchor, generalize, test, close); removing unit 4 breaks the trajectory.

**Score 0 (no)** — Either (a) single dense post burying a multi-claim argument no scroller will parse — wall-of-text without 1-3-1 rhythm; OR (b) thread padding one insight across 8+ tweets with restated points and connective tweets that reveal nothing (promise-inflation). Padded threads produce the dwell-completion drop documented in Phoenix's `engagement_arbitrage` detector.

**Score 0.5 (unknown)** — Intended distribution (single post vs thread, X-native vs cross-post) ambiguous from artifact. Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: Identify the post's form (single post / thread of N units).
- Step 2: For single posts, test whether claim density fits 280 chars (no buried multi-claim argument). For threads, walk each unit and test whether it reveals something the prior unit did not — Rate of Revelation applied per-unit, not as a sum.
- Step 3: Emit verdict + one-sentence justification.

Do not score: specific unit-count as target (always-5, always-7 templating fails this), exact character count, thread-length conventions.

### X-5 — Survives the screenshot test in the account's voice (gestalt, regime-aware)

**Outcome question (binary):**
If the avatar and handle were stripped, would a regular reader of this account — encountering the post in their feed — recognize it as the author's voice and attribute it to this account specifically (not "some founder")? Or does it read as machine-finished prose anchored in the generic-niche-attractor cadence — the centroid of "founder X voice" belonging to no specific person?

**Score 1 (yes)** — In **data-rich regime (≥30 prior posts in `source_data`)**: voice consistent with the account's established empirical register (cadence, vocabulary mode, posture, joke-to-seriousness ratio, signature rhetorical moves) AND no AI-slop signature stack triggers (no 3+ co-occurring Tier-1/2 tells — em-dash density past account baseline + signature transitions + reflexive tricolons + "Stop X. Start Y." + listicle parallelism + false-vulnerability shape). Draft reads as in-the-X-conversation (peer-to-peer, in-the-moment, punchy) rather than imported from a different register (LinkedIn broadcast, blog narrative, "lesson-extracting" conclusive tone). Post would be screenshottable with author's name re-attributed and still read as theirs.

In **cold-start regime (<30 prior posts)**: prose is not recognizable as machine-finished to an AI-aware reader (no centroid-voice cadence collapse, no slop-stack triggers) AND draft is consistent with the account's stated positioning in `source_data` (bio, declared niche, stated topic focus). Slop-absence + positioning-consistency replaces empirical voice-match. Addresses Wang et al. EMNLP 2025 plateau finding (few-shot beyond ~10 gives diminishing returns) and the `linkedin_engine v040 cold-start mutation` precedent.

**"Looks like slop but isn't" defense.** Real operators legitimately use the surface markers that AI-slop detection enumerates. Naval uses em-dashes substantively (his "Seek wealth, not money or status" is a tricolon). Bloom uses paradox-and-tricolon as foundational rhetoric. Mack uses counter-stereotype + antithesis as core moves. The slop signal is the *stack* — 3+ Tier-1/2 tells co-occurring — NOT any single tell in isolation. A post with one em-dash, one antithesis, and one substantive claim is not slop; a post with em-dash-every-line + "Stop X. Start Y." + reflexive tricolons + "moreover" + parallel-listicle is slop. Judge tests gestalt, not feature presence.

Example A (do not optimize toward this): Naval's 6-word openings where rhythm + lexical mode + posture (declarative-reframing, lower-status, peer-not-mentor) all match across 200+ posts. New draft in that pattern with substantive content scores 1.

Example B (do not optimize toward this): Bloom's paradox-as-headline with tricolon — uses three slop-adjacent features substantively. Score 1 because the stack is rhetoric not template.

**Score 0 (no)** — Voice mismatches account's prior register (sober technical account posting Hormozi-style heat); reads as LinkedIn-shape imported to X (authority-positioned, narrative, "the lesson is X" conclusive framing rather than peer-not-broadcast, punchy-not-narrative); OR reads as machine-finished (generic-niche-attractor cadence, 18–24-word sentence-length plateau, no specific person's idiolect surface); OR triggers 3+ AI-slop signature stack tells co-occurring (the gate filters most upstream — if the judge sees a draft with this stack, the gate missed a residual and the judge catches it); OR opens with template phrases anchoring a known LLM register ("Here's the thing nobody tells you about," "Most people get this wrong," "Stop X. Start Y." rhythm).

**Score 0.5 (unknown)** — Data-rich: voice consistency borderline and slop-absence ambiguous from artifact alone. Cold-start: stated positioning itself absent from `source_data` AND prose is borderline. Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: Identify the account's register from prior posts in `source_data` (cadence, vocabulary mode, posture, signature rhetorical moves). If <30 prior posts, switch to cold-start: identify stated positioning from `source_data` bio/niche/topic-focus. Form a one-sentence private description; do NOT enumerate features as a checklist.
- Step 2: Test whether the draft reads as in-the-X-conversation (peer-to-peer, in-the-moment, punchy, contrarian-not-conclusive) versus imported from a different register (LinkedIn broadcast, blog narrative, "lesson-extracting" mentor tone). X-vs-LinkedIn discriminator defends against the most-common cross-platform voice failure in repurposed founder content.
- Step 3: Test the draft for AI-slop signature *stack* — ≥3 of the named tells (em-dash density past account baseline, signature transition phrases, reflexive three-element parallel rhythm, "Stop X. Start Y." imperative-pair, false-vulnerability shape, listicle syntactic parallelism, cadence collapse toward 18–24-word plateau) co-occurring. NOT presence-of-any-single-tell. Apply "looks like slop but isn't" defense — sparse use of em-dashes / antithesis / tricolons is rhetoric.
- Step 4: Emit verdict + one-sentence justification.

Do not score: emoji in isolation, formal vs casual register on its own, any specific punctuation in isolation, AI-detector classifier output (not integrated — see §3b rationale).

---

## 5. Shared judge-prompt wrapper (direction-of-effect, NO numerical weights)

```
You are scoring an X (Twitter) post draft for a power-user
scrolling the For-You feed in 2026. The reader has roughly 0.5
seconds of attention per post; they commit to expanding,
replying, reposting, bookmarking, or profile-clicking inside
the first 400–700ms based on first-fixation lexical features,
then read the full post only if the opening earned that
commitment. They are slop-aware — they recognize generic
founder voice within two fixations and hit "not interested."

The post must work for the scroller (would they tap, reply,
repost, bookmark, dwell, profile-click?) AND for the algorithm,
which rewards substantive replies, conviction-level reposts,
save-for-later bookmarks, and long-dwell — and heavily
penalizes mutes, blocks, "not interested," and reports. These
align by design: the algorithm rewards what the scroller
actually does, so a post that earns substantive scroller
engagement earns algorithmic out-of-network fanout.

The draft is the lane's locked artifact shape: a single X post
(≤280 chars, one coherent claim that resolves within the post)
or a thread of 3–12 tweets where each tweet reveals something
the prior tweet did not.

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale following the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the draft alone, emit
0.5 + "unknown" + one sentence on what context would have to
be present to commit to 1.

A relevant practitioner in the account's niche should
recognize this as written by someone with lived experience.
The post should earn a substantive reply (not "Great post!")
from a peer; it should survive the screenshot test with the
avatar stripped and handle re-attributed. Score for OUTCOMES
on the scroller and the algorithm — not for the presence of
named frameworks, specific punctuation, template opener
shapes, or named surface markers.

Emit per-criterion JSON:
{"criterion_id": "X-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

**Note on stripping numerical weights.** The v0 wrapper named "reply (13.5×), repost (20×), bookmark (10×), long-dwell (+10×), negative signals (−74×)." v1 strips these for two reasons grounded in the algorithm-axis research: (a) the numbers are operator-community reconstructions, not official — the open-source repo confirms the ten-action probability set + positive-and-negative-weighted summation formula, but the numerical coefficients are NOT published; treating reconstructions as load-bearing is unsafe; (b) named numbers are a soft Goodhart vector — the workflow can infer "the judge cares about replies, reposts, bookmarks, dwell" from the wrapper itself and start template-fitting toward "reply-eligible-looking posts" rather than substantively-reply-earning posts. Direction-of-effect language gives the judge the same orientation without anchoring on gameable numbers.

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **X-1**: "Templated specific-number + counter-intuitive declaration opener" doesn't pass — Axis B catches the opening as anchored, Axis A catches the body if the gap is closed-loop or unbounded, Axis C catches the body if it over-promises or under-delivers (clickbait failure). All three axes must pass.
- **X-2**: Fabricated specifics don't pass — lived-experience claim must be non-regenerable; CoT tests for confabulation patterns (no attribution, no resolvable provenance, conflated entities, non-existent dated events).
- **X-3**: Manufactured controversy doesn't pass — falsifiability requires the claim could actually be wrong on substance. Hot-takes-without-evidence fail because the disagreement invited is stylistic, not substantive.
- **X-4**: Always-5-units, always-7-units thread templating doesn't pass — Rate of Revelation is per-unit, not summed. Unit-count is incidental.
- **X-5**: Avoiding em-dashes by replacing with parentheticals doesn't pass — AI-slop is a *stack*, not a single tell; judge tests gestalt at 3+ co-occurring. LinkedIn-shape voice imported to X doesn't pass — X-vs-LinkedIn discriminator in CoT step 2 catches the broadcast-not-peer register mismatch. Cold-start void doesn't collapse to feature-checking — regime-aware sub-anchor switches to slop-absence + positioning-consistency.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0 — and the 6 structural_gate checks gate the surface markers upstream, so the workflow has to evade all of them simultaneously AND produce content the gestalt judge can't dismiss.

**3 sample-and-flag telemetry signals** (variance instrumentation per design guide §11.5, NOT criteria — these run alongside the judge, generate telemetry, trigger redesign rather than score):

- **Grok-tone proxy.** Sample 10% of drafts; run a lightweight tone classifier (constructive / neutral / combative-empty). If a generation shows ≥30% combative-empty, flag. Catches workflow learning to mimic edgy-takes-without-substance even when X-3 passes on surface read.
- **Reply-bait CTA detector.** Sample drafts for end-of-post bait patterns ("what do you think?", "agree or disagree?", "drop your thoughts below"). Track per-generation rate. Rising rate = workflow templating toward reply-bait; flag for redesign.
- **AI-slop signature density across generations.** Count em-dashes, tricolons, "moreover/furthermore/delve" tokens, "Stop X. Start Y." imperative-pairs across the generation's corpus. If density rises monotonically across 3 generations, flag — even if X-5 passes per-fixture, the workflow may be drifting toward slop on average.

---

## 7. Verification — conforms to design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples ✓
- §5 criterion count: **5** (no documented exception; X-1 absorbs hook-discipline + clickbait failure via 3-axis CoT rather than promoting Axis C to a 6th criterion — see §8 open-question 1) ✓
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3–4 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §11 Goodhart-resistance verification with 3 sample-and-flag telemetry signals ✓
- §13 specimen criterion template followed ✓

**Note on the 5-criterion ceiling.** Unlike the CI lane's CI-6 evidence-chain criterion (a documented justified-breach per design guide §5 v2.1, justified by 19.9% GPT-4o citation-fab and 37% Perplexity confabulation effect sizes), x_engine v1 does NOT promote a 6th criterion. The hook-discipline deep research identified a potential X-6 "hook-body alignment" that would catch the clickbait failure mode — v1 folds hook-body alignment into X-1's Axis C CoT step rather than promoting. Rationale: X-1 (with 3-axis CoT) + X-2 (specific knowledge — most clickbait fails X-2 because the body is generic) together should catch ≥90% of seeded clickbait fixtures. If the redundancy check shows <90%, the §5 documented-exception path opens and X-6 hook-body alignment becomes a 6th criterion. Until then: 5.

Length per criterion ≈ 250–350 words (longer than the design guide's 150-word target due to 3-axis CoT on X-1 and regime-aware sub-anchors on X-5; absorbable). Total spec body ≈ 4500 words.

---

## 8. Open questions

Reader / Artifact-shape / Success / Failure / 5 Criteria / wrapper-strip / structural_gate routing are LOCKED at v1. Remaining:

1. **X-6 hook-body alignment promotion — promote only if empirical variance forces.** The hook-discipline deep research identified a potential 6th criterion targeting the clickbait failure (high impression / low dwell-completion / high negative-signal cascade). v1 folds hook-body alignment into X-1's Axis C CoT. After redundancy check (§5): if X-1 (3-axis CoT) + X-2 catch ≥90% of seeded clickbait fixtures, fold holds and 5 criteria is correct. If <90%, promote X-6 per the §5 v2.1 documented-exception path — LLM-specific failure surface is documented (xai-org/x-algorithm `engagement_arbitrage` detector + Phoenix bounce-after-hook penalty).

2. **Redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Drop any criterion correlating >0.7 with another. Most-likely-to-merge pairs: X-2 (specific knowledge) ↔ X-3 (falsifiability) — specific lived-experience claims are often falsifiable; X-2 ↔ X-5 (voice) — composed-engineer voice tends to make claims simultaneously unfalsifiable AND off-voice, forcing co-variance on slop-positive cases.

3. **Phoenix retraining cadence — quarterly algorithm-axis re-run.** Phoenix is iterated regularly (May 2026 release shipped an architectural refresh). The 5-criterion outcome-question shape is durable; underlying weight reconstructions and operator-data triangulations are not. Re-run algorithm-axis research quarterly; track whether `reply > like > repost > bookmark > profile_click` ordering still holds, whether `engagement_arbitrage` still fires on the same bounce-after-hook patterns, whether external-link suppression cohort thresholds shift.

4. **Cold-start handling for X-2 and X-5 — fixture-stratify the calibration set.** When the account has <30 prior posts (working data-rich threshold), X-2 and X-5 both lose their account-history reference. X-5 has an explicit cold-start sub-anchor (slop-absence + stated-positioning-consistency); X-2 still scores because lived-experience is about claim specificity not voice. The `linkedin_engine v040 cold-start mutation` (memory 2026-05-08) flags analogous prior precedent. Recommend: 100-fixture calibration set stratify across cold-start (≤10), mid-data (10–30), data-rich (≥30) regimes, ~33 fixtures each, so X-5 regime branches are independently calibratable.

5. **Premium vs non-Premium accounts — no spec effect; monitor for distribution-vs-quality confound.** Premium accounts receive +4× in-network and +2× out-of-network ranking bonus on Phoenix output. Draft quality is invariant to tier; distribution is not. Judge scores quality, so spec does not condition on Premium. Open question: if Phase-3 telemetry shows Premium drafts hitting median 600 impressions vs non-Premium 100, the substrate may misread that as quality signal during evolution. Track for the first 3 generations post-deployment.

6. **Wrapper numerical-weight strip — decision documented (this lane done).** v0 named "reply (13.5×), repost (20×), bookmark (10×), long-dwell (+10×), negative signals (−74×)." v1 strips for the two reasons in §5 above (reconstructions not official; soft Goodhart vector). Decision: stripped, direction-of-effect language replaces. Revisit if the open-source release publishes official numerical weights (currently the repo publishes the formula template + ten-action probability set but NOT coefficients).

7. **First-cohort overfitting watch — Polish-language fixture risk.** v1 is research-grounded against English-language Anglosphere founder/operator voice. The 6 structural_gate checks (em-dash density, signature-phrase blocklist, tricolon density, "Stop X. Start Y." regex, listicle uniformity, hashtag count) are English-calibrated. Polish-language clients (DWF lawyers, Klinika dermatology) may show different Tier-1 tell frequencies — Polish em-dash conventions, Polish discourse markers, Polish parallel-construction baselines. Judge criteria (X-1..X-5) test mechanisms that are language-universal at the cognitive-load level (forward-vector, gestalt voice, falsifiability, specific knowledge) so the criterion prose should generalize. Structural_gate thresholds need a Polish-language fixture pass before locking. Memory references `linkedin_engine v040 cold-start mutation` as analogous prior precedent. Re-validation trigger: any fixture in a non-English-Anglosphere register should prompt a quick re-validation pass on `structural_gate` thresholds (judge criteria expected to hold).

8. **Fixture validation.** Run 5 existing X-engine fixtures (current archive `v007-curated` + any Polish-language fixtures available) through the locked criteria; eyeball judge rationales. If rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating.

9. **`structural_gate` expansion (before spec ships to v006/workflows)** — add 6 deterministic checks (~120 LOC total) per AI-slop deep research §4. Each defends a specific named failure surface with real-operator FPR below 5%:

   - **Em-dash density gate** — reject drafts with >5 em-dashes per 100 words. Defends against GPT-family 3.28×-baseline overuse (Goedecke 2025 + Piece of K 2025). Real-operator FPR very low (most operators run 0.5–1.5). ~20 LOC.
   - **Signature-phrase blocklist** — hard-reject on appearance of conversational tells that don't belong in 280-char tweets: "moreover," "furthermore," "delve into," "in conclusion," "let me explain," "here's the thing:", "let's be clear:", "it's worth noting," "navigate the complexities," "tapestry of," "transformative," "unleash," "harness the power of," "leverage" (as verb). ~15 LOC + curated list.
   - **Three-element parallel-construction density** — detect tricolons via syntactic-uniformity scoring; reject if >2 per thread. Defends against tricolon abuse documented across VERMILLION / Flux8Labs. ~30–40 LOC.
   - **"Stop X. Start Y." structural detector** — regex or parse-tree match for two immediately-adjacent imperative sentences (first contains stop/don't/quit; second contains start/begin/try). >1 instance per post fails. ~15 LOC.
   - **Listicle syntactic-uniformity gate** — when draft contains 3+ numbered or bulleted items, compute cosine similarity of bullet POS-tag sequences. Reject if >0.85. ~40 LOC.
   - **External-link-in-body suppression flag** — Phoenix learned link-containing posts predict session-end; Q1 2026 cohort tests measured 94% reach reduction for non-Premium (PPC.land). Flag `https?://` URLs in body; auto-rewrite to first-reply form per standard creator hygiene. ~20 LOC.
   - **Hashtag count gate** — reject if >2 hashtags (3+ triggers ~40% reach reduction per the open-source release). Already in `slop_gate`; confirm coverage. ~0 LOC.

   AI-detector classifier output (GPTZero, Originality.ai, fine-tuned BERTweet) is NOT added — see §3b rationale (54% detection on fine-tuned voice models per Dawkins et al. 2025; 15.6–17.6% FPR disproportionately penalizes non-native English writers).

10. **Propagation to other 7 lanes.** Once x_engine v1 validates on real fixtures, propagate per-lane — NOT mechanical 4-question repeat. The 4 x_engine deep-research questions (algorithm, hook discipline, voice screenshot test, AI-slop detection) were lane-specific; LinkedIn engine needs a partially-overlapping but distinct deep-research set (algorithm differs; voice register differs — broadcast vs peer; AI-slop ghostwriter regime differs).
