---
date: 2026-05-18
type: research deliverable
status: complete
topic: domain research — x_engine lane
parent: docs/rubrics/judge-design-guide.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# Domain Research: What Makes an Excellent X (Twitter) Post Draft

**Date:** 2026-05-18
**Purpose:** Ground the `x_engine` lane judge in published practitioner playbooks, named creator exemplars, and the post-2026 X algorithm — not statistical surface markers, not embedded framework names in rubric prose.
**Scope:** Synthesis of (a) X's open-sourced ranking system as of Jan-2026, (b) named-creator playbooks (Welsh, Cole/Bush, Koe, Naval, Sahil Bloom, George Mack, Visakan Veerasamy, Hormozi, Greg Isenberg, Cody Schneider), (c) practitioner failure-mode catalogues (engagement-farming, AI-slop, model-collapse), (d) the four hook/structure frameworks the creator economy actually uses (Welsh content matrix, Cole/Bush "Ship 30" hook taxonomy + 1-3-1 rhythm, Hormozi jab-jab-jab-right-hook, Isenberg ACP).

---

## 1. What Makes an X Post Irreplaceable

The strongest convergence across the open-sourced January-2026 algorithm, named-creator playbooks, and Hamel-Husain-style practitioner critique is a single distinction: **a post earns its place in someone's feed by triggering a specific, named action from a specific, named scroller — a reply, a repost, a save, or a profile visit. A post that earns "scroll-past with a half-second eye-touch" has failed by every signal that matters in 2026.** The algorithmic and the human reader reward the same thing for different reasons: the human stops because the post earned attention against the next post; the ranker amplifies because dwell, reply, and repost weights now dwarf likes.

### The reader and the algorithm in 2026

Post-January-2026, X open-sourced its Grok-powered ranking stack ([xai-org/x-algorithm](https://github.com/xai-org/x-algorithm)) and the engagement formula is no longer in doubt. The publicly documented weights:

- **Reply ≈ 13.5× a like; reply with author response ≈ 27× a like; full conversation thread ≈ 150× a like.**
- **Repost ≈ 20× a like; bookmark ≈ 10×; profile click ≈ 12×; link click ≈ 11×; long-dwell (2+ min) ≈ +10×.**
- **Negative signals (mute, block, "not interested", report) ≈ −74×.** A single negative action erases dozens of positive ones.
- **Premium subscribers receive a +4 to +16 ranking bonus on out-of-network distribution.**
- **~50% of a typical feed is out-of-network** content surfaced by SimClusters and Grok's interest-graph retrieval; this is where viral reach lives.
- **Text-only posts still beat video by ~30% on engagement-per-impression** — X is the only major platform where text outperforms native video, though sub-60s native video gets a separate distribution bonus.
- **Hashtag penalty:** 3+ hashtags trigger a ~40% reach reduction.

The reader who matters in 2026 is a specific persona: a power-user with X Premium (Premium replies rank higher in conversations, so they dominate visible discourse); a topical-niche scroller arriving via the "For You" tab not the Following tab; someone whose half-second of attention is the gating event before any other signal fires. **The judge's reader spec should target this scroller, not the abstract "Twitter user."**

### Empirical patterns from named creators

**Pattern 1 — The first sentence is the artifact.** Dickie Bush and Nicolas Cole's *Ship 30 for 30* curriculum is built around the "1 Chip Rule": the opening line must function like the first chip from a Pringles can — once tasted, the next one is inevitable. Cole's *Art and Business of Online Writing* formalizes this as the **Curiosity Gap**: a hook tells the reader what the piece is about, who it's for, and what it promises, *without revealing the answer*. The judge's test is whether sentence one earns sentence two — not whether it contains a "hook."

**Pattern 2 — Specific knowledge over generic wisdom.** Naval Ravikant's *How to Get Rich (without getting lucky)* tweetstorm (230k+ likes, the canonical reference exemplar for thread-as-essay) rides on **"specific knowledge"** — knowledge that cannot be trained for or outsourced, that emerged from one person's lived obsession. The post that survives is the one only one person could have written. AI-slop posts fail this test by definition.

**Pattern 3 — A claim, not a topic.** Sahil Bloom's one-liner pattern (paradoxes, razors, frameworks) and George Mack's *High Agency* tweets share the same structural property: the post asserts a specific, falsifiable thing that disagrees with conventional wisdom. Mack's frame is "clear thinking + bias to action + strategic disagreeableness"; the diagnostic is whether the post says something that could be *wrong*, not something that could only be agreed-with.

**Pattern 4 — Unit-of-consideration discipline.** Visakan Veerasamy's published heuristic — "a tweet is a unit of consideration; a good thread is 3–7 units, max ~12" — is the most-cited length-discipline rule among practitioners. Threads beyond ~12 units are usually one post that should have been an essay. A single-shot post that should have been a thread is the symmetric failure.

**Pattern 5 — Voice-density that survives screenshot.** Dan Koe's PPP framework (Pull-in / Perspective / Practical) and Justin Welsh's content-matrix execution both rest on a voice signature that a reader could identify without the avatar. The Hamel-Husain-style test: if you remove the handle and the post still reads as that specific creator, voice is high; if it could have been written by any productivity-tweet account, voice is generic.

**Pattern 6 — Reply-bait that earns replies because the question is real.** Greg Isenberg's "Treat every post as an MVP" practice means posts are framed as testable hypotheses inviting disagreement. A post that ends with a hollow "what do you think?" is engagement-farming; a post that surfaces a genuine open question — one the author actually doesn't know the answer to — earns the 27× reply weight.

### Dimensions practitioners cite

Synthesising across the named-creator literature, the dimensions creators genuinely care about are:

1. **Earns sentence two from sentence one** (Cole/Bush 1 Chip Rule, Curiosity Gap)
2. **Carries specific knowledge** the author alone could have written (Naval)
3. **Asserts something falsifiable** (Mack, Bloom, Hormozi)
4. **Matches form to unit-count** — single post or 3–7 thread units (Veerasamy)
5. **Sounds like the account voice** under screenshot test
6. **Earns a real reply, repost, or save** (not a like, not a vanity reaction)
7. **Survives the negative-signal test** — would not trigger mute/block/"not interested" from the target reader

---

## 2. What Separates Great X Posts from Mediocre — Named Failure Modes

Named practitioners and the broader creator commentariat catalogue specific, recurring failure modes — not abstract criticisms.

**AI-slop tells** (the 2025 Word of the Year per both Merriam-Webster and the American Dialect Society). The named signatures, repeated across multiple critique sources:

1. **Em-dash overuse and "moreover," "in conclusion," "furthermore," "delve into"** — model-collapse residue. These markers don't make the post bad; they make it identifiably *generated*, which trips the reader's slop filter before the content registers.
2. **Tricolon abuse** — "It's not X, it's Y, it's Z" three-element parallel structures, used reflexively.
3. **Smooth, gradeless prose** — no rough edges, no specific names, no dated claims. "AI can simulate authority, but it cannot actually use a product, run a campaign, or survive a failed launch" (model-collapse literature, 2025).
4. **Generic motivational frame** — "The best investment you can make is in yourself." Could have been any account. Fails Naval's specific-knowledge test and Mack's falsifiability test in one move.

**Elon-suspended engagement-farming tactics** (X has actively suspended these since 2024; they now carry direct algorithmic risk, not just aesthetic risk):

5. **"Like if you agree" / "RT if X"** — explicitly named as bait in X's anti-spam policy; distribution-suppressed.
6. **Binary-choice provocation polls** — oversimplified two-option polls designed to harvest engagement.
7. **Reply-farming via planted controversy** — Grok-flagged in policy docs as "provocative, misleading, or rage-baiting content posted to artificially boost likes, replies, retweets, and views." Reply-farmer posts attract bot replies that further pollute the engagement signal.
8. **Fake-vulnerability bait** — "I lost everything last year. Here's what I learned." When the vulnerability is performative and the lesson is generic, the reader's parasocial filter catches it. Tim Stoddart and Paul Millerd have both written about this as the "performative pathless path" failure mode that infected the writing-online niche after 2023.

**Structure-form mismatches** named by Cole/Bush, Koe, and Veerasamy:

9. **Thread that should have been one post** — a single insight padded with 8 "And here's why that matters" expansion tweets. Cole's *Rate of Revelation* fix: every tweet must reveal something new; if a tweet only restates the prior one, cut it.
10. **One post that should have been a thread** — a dense, multi-claim post that gives the scroller no on-ramp. The 1-3-1 Writing Rhythm (Ship 30) prescribes alternation: one short line, three medium, one short. Wall-of-text posts violate this and lose dwell time.
11. **Account-voice mismatch** — a sober technical account posting a Hormozi-style "97% of you won't act on this" post. The voice/persona collision is a stronger negative signal than a weak post in the account's native voice.

**Mechanism-of-engagement failures** caught by the 2026 ranking weights:

12. **Hot take without evidence** — earns instant likes (low weight), zero replies (high weight), high mute rate (−74× weight). Net algorithmic value: negative.
13. **Quote-tweet of own post for amplification** — explicitly Grok-flagged as manipulation.
14. **Posts that don't end** — no implicit invitation to reply, save, or share. The post terminates with a flourish instead of opening a door.

**Hamel-Husain "what would a domain expert reject"** — for the x_engine lane the equivalent test is: *would a 100k-follower creator who writes in this niche themselves repost or quote-tweet this? Or would they scroll past?* The judge should reason as this creator.

---

## 3. Industry Frameworks — The Judge's Reasoning Toolkit

These are the frameworks the creator community actually uses for X content. Each carries a specific quality test a post should pass. **Per `docs/rubrics/judge-design-guide.md` §11.1, framework names do NOT appear in rubric prose** — they live here as the judge's private reasoning toolkit.

### Justin Welsh — Content Matrix
A 2×2 system: the Y-axis lists content topics (subtopics within the creator's niche); the X-axis lists content formats (story, list, observation, contrarian take, framework, case study, etc.). Each cell is one post. The diagnostic for a draft: **does the post occupy a defensible cell, or is it a hybrid format with no clear shape?** Welsh's published frame is that genre-clear posts outperform genre-mixed posts because the reader knows within one second what they're being offered.

### Dickie Bush + Nicolas Cole — Ship 30 for 30 Hook Taxonomy
The most concretely documented hook framework in the creator economy. Three sub-systems matter for the judge:

- **The 1 Chip Rule** — sentence one must make sentence two inevitable.
- **5 Proven Ways to Write a Compelling First Sentence** — (a) contrarian declaration, (b) specific stat or number, (c) named-person mini-story, (d) provocative question with implied answer, (e) "How I [unexpected outcome] in [specific timeframe]."
- **The 1-3-1 Writing Rhythm** — one short line, three medium, one short, for visual scannability. Threads use 1-3-1 per tweet; long posts use 1-3-1 per paragraph.
- **Rate of Revelation** — each unit reveals something the prior unit did not. The diagnostic: a post that could lose any sentence without changing meaning is over-padded.

### Cole — *Art and Business of Online Writing* Headline Anatomy
Headline framework: **The 1** (opening hook words) + **Question** (what the piece is about, framed as a question/way/reason/solution) + **Gets** (connective tissue) + **Specific Reader** (who it's for) + **Promise** (what they'll get, language with emotional valence). The Curiosity Gap is the unifying mechanism: tell what it's about, who it's for, and what it promises — without revealing the answer.

### Naval Ravikant — Specific Knowledge + Tweetstorm-as-Essay
Naval's *How to Get Rich* is the canonical thread-as-essay exemplar. Three judge-relevant tests: (a) **Specific knowledge** — knowledge that cannot be trained for, that emerged from the author's specific obsession; (b) **Wealth-not-money** style claims — first-principles reframings that the reader hasn't heard in that exact form; (c) **Atomic unit testable in isolation** — each tweet in the thread stands as a coherent claim if quoted alone.

### Dan Koe — PPP and Hook > Value > Conclusion
PPP = **Pull-in / Perspective / Practical**. Pull-in catches with a number, percentage, or contrarian frame. Perspective is the author's unique angle (lived-experience filter). Practical converts the insight into something the reader can act on within 24 hours. The diagnostic for a draft: does it execute all three moves, or does it stop at "interesting"?

### Sahil Bloom — Paradox / Razor / Framework
Bloom's one-liner pattern: condense a 5000-word essay into a paradox, razor (decision heuristic), or framework. The named criterion: a post should be **screenshottable** — survive as a screenshot quoted by someone else, with the author's name added back as attribution. The judge's test: would this be screenshotted?

### George Mack — High Agency + Counter-Stereotype
Mack's frame: high-engagement posts feature people whose beliefs don't line up with their stereotypes ("the boxer who writes poetry," "the beauty queen who reads Nietzsche"). The post that earns reposts is the one that surfaces a counter-stereotype, a "you wouldn't expect this from this source" angle. The test: does the post earn surprise?

### Alex Hormozi — Jab-Jab-Jab-Right-Hook (Gary-Vee-via-Hormozi)
98% value, 2% ask. The judge-relevant principle: a post that asks before it earns is discounted by the algorithm and the reader. The ask is permitted, but only inside an account-level ratio. **For draft-level judgment, the relevant test is whether the draft is value-shaped or ask-shaped.** Ask-shaped drafts in a value-shaped account are off-voice.

### Visakan Veerasamy — Units of Consideration
Threads: 3–7 units typical, up to ~12 max. Each unit a coherent thought. The diagnostic: does each tweet earn its place, or is the unit-count padded?

### Greg Isenberg — ACP (Audience / Community / Product) + Post-as-MVP
Every post is a hypothesis to be tested. The judge-relevant move: posts that take a falsifiable position invite the replies and reposts that prove or disprove the hypothesis. The diagnostic: is the post testable — could it be wrong?

### Cody Schneider — Distribution-First
Schneider's frame: "hacky content + good distribution > polished content + no distribution." The post must match where the audience actually lives. For x_engine, the format constraint is the medium's constraint — sub-280-char single posts and 3–7-unit threads dominate; longer text-image hybrids and embedded long-form posts have a place but require a different judging frame.

---

## 4. Proposed Judge Criteria (5 Outcome Questions, Draft)

Each criterion below is an **outcome question** about reader effect, not a feature check. Each names what a low/high score looks like behaviorally. Framework names are absent from criterion prose per `docs/rubrics/judge-design-guide.md` §4. Per §11.1, the design target is *time-to-Goodhart*, not feature presence.

### X-A — Earns the next tap from a specific scroller
**Outcome question (binary):** Would a relevant X power-user — scrolling the For-You feed, half-second of attention per post — stop on this post and either tap to read more, expand the thread, or pause long enough for dwell-time to register?
**Score 1 (yes) — Behavioral description:** Sentence one introduces a tension, a counter-intuitive claim, a specific named entity with a dated finding, or a question whose answer the reader cannot predict. The opening earns the *next* unit, whether that's sentence two or tweet two.
**Score 1 example (do not optimize toward this):** "Naval's *How to Get Rich* opens 'Seek wealth, not money or status.' Six words, three reframings, no fluff."
**Score 0 (no) — Behavioral description:** Opens with a generic frame, abstract motivational claim, or topic-statement that could appear on any account. The reader can predict the second sentence from the first.
**Score 0.5 (unknown):** Use only when the post's first-line framing depends on context not in the artifact (e.g., reply to an unseen post).

### X-B — Carries specific knowledge that this author alone could write
**Outcome question (binary):** Would a relevant practitioner reading this post recognize it as written by someone with lived experience in the domain — not summarized from secondary sources?
**Score 1 (yes) — Behavioral description:** Contains at least one specific detail (named person, dated event, specific number, unique anecdote, or named project) that demonstrates the author was present for the underlying experience. The claim cannot be regenerated by a model reading the public internet.
**Score 1 example (do not optimize toward this):** "Cody Schneider's '5,000 follows in 30-60 days, expect ~20% follow-back' is specific because he ran the experiment."
**Score 0 (no) — Behavioral description:** Every claim could appear in any productivity-niche post. No named entities, no dated specifics, no first-person details that survive Naval's specific-knowledge test.
**Score 0.5 (unknown):** Use only when the post is a single-line aphorism where lived-experience claim is ambiguous from the artifact.

### X-C — Asserts something falsifiable a peer could disagree with
**Outcome question (binary):** Could a thoughtful peer reading this post say "I disagree, and here's why" — and would that disagreement be substantive, not stylistic?
**Score 1 (yes) — Behavioral description:** The post takes a position that contradicts at least one widely-held belief in its niche, or claims a specific causal relationship the reader could test against their own experience. The claim is wrong in at least one knowable way.
**Score 1 example (do not optimize toward this):** "George Mack on agency: 'low-agency people are passengers in their own lives.' Falsifiable — testable against any reader's autobiography."
**Score 0 (no) — Behavioral description:** The post is unfalsifiable — a tautology, a generic platitude, or a claim so hedged that no one could disagree. Earns likes; earns no replies.
**Score 0.5 (unknown):** Use only when the falsifiability test cannot be evaluated without knowing the account's prior positions.

### X-D — Form matches function — single post or 3–7-unit thread, no padding
**Outcome question (binary):** Does the draft's structure (single post vs. thread) match the density of the claim it's making, with each unit earning its place?
**Score 1 (yes) — Behavioral description:** Either (a) a single post under ~280 chars that contains exactly one coherent claim, or (b) a thread of 3–12 tweets where each tweet reveals something the prior tweet did not. Removing any unit would degrade the post.
**Score 1 example (do not optimize toward this):** "Sahil Bloom condenses what would be a 5000-word essay into one paradox. Visakan's thread on courage runs 7 units, each a distinct move."
**Score 0 (no) — Behavioral description:** Either (a) a single dense post that buries a multi-claim argument no scroller will parse, or (b) a thread that pads one insight across 8+ tweets, with restated points and connective tweets that reveal nothing.
**Score 0.5 (unknown):** Use only when intended distribution (single post vs. thread, X-native vs. cross-post) is ambiguous from the artifact.

### X-E — Sounds like this account's voice and would survive the screenshot test
**Outcome question (binary):** If the avatar and handle were stripped, would a reader familiar with the account still recognize this as the author's voice — and would the post survive being screenshotted and quoted without falling into AI-slop tells?
**Score 1 (yes) — Behavioral description:** Voice is consistent with the account's established register (formal/conversational/contrarian/etc.). No em-dash-heavy "moreover/furthermore/delve" tells. No generic tricolons that any account could have posted. The post would be screenshottable with the author's name re-attributed and still read as theirs.
**Score 1 example (do not optimize toward this):** "Naval's 6-word openings; Mack's counter-stereotype framing; Bloom's paradox-as-headline — voice is distinctive enough that even screenshots are recognized."
**Score 0 (no) — Behavioral description:** Reads like any productivity / writing-online / startup-niche account. AI-slop signatures present (excessive em-dashes, "moreover/in conclusion," smooth-but-gradeless prose). Or: voice mismatches the account's prior register (sober technical account posting Hormozi-style provocations).
**Score 0.5 (unknown):** Use only when the account's prior voice is not represented in the artifact.

**Notes on what this rubric deliberately does NOT score:** Whether the post "has a hook" (feature check); whether it uses a specific framework (framework-name embedding); whether it's a specific length (structural — route to `structural_gate`); whether it includes hashtags, emoji, or specific punctuation (surface markers, easily gamed). The judge tests the post's effect on a specific reader; verifiable surface features live in `structural_gate`.

---

## 5. Sources Cited

**Algorithm (primary, post-Jan-2026 open-source release):**
- [xai-org/x-algorithm GitHub repo](https://github.com/xai-org/x-algorithm) — January 2026 open-source release of the Grok-powered For-You ranking system; Rust-based architecture (Home Mixer, Thunder, Phoenix, Candidate Pipeline)
- [The X Algorithm in 2026: What Actually Makes Posts Go Viral — OpenTweet](https://opentweet.io/blog/how-twitter-x-algorithm-works-2026) — engagement weights, dwell-time mechanics
- [How the Twitter/X Algorithm Works in 2026 (Source Code) — PostEverywhere](https://posteverywhere.ai/blog/how-the-x-twitter-algorithm-works) — weight formula breakdown
- [X open sources its algorithm — TechCrunch](https://techcrunch.com/2026/01/20/x-open-sources-its-algorithm-while-facing-a-transparency-fine-and-grok-controversies/) — context for the release
- [Twitter Algorithm Explained — Sprout Social](https://sproutsocial.com/insights/twitter-algorithm/) — practitioner summary
- [How Does the X Algorithm Work in 2026 — SocialBee](https://socialbee.com/blog/twitter-algorithm/) — negative-signal weights, premium boost

**Named-creator playbooks:**
- [Ship 30 for 30 (Dickie Bush + Nicolas Cole)](https://www.ship30for30.com/) — 1 Chip Rule, 1-3-1 Rhythm, Rate of Revelation, Atomic Essay
- [The Art and Business of Online Writing (Cole) — book summary](https://storylab.ai/the-art-and-business-of-online-writing-nicolas-cole/) — headline anatomy, Curiosity Gap
- [Justin Welsh — My Content Matrix](https://www.justinwelsh.me/article/content-matrix) — 2×2 topic-format system
- [Justin Welsh — How to Grow on LinkedIn in 2026](https://www.justinwelsh.me/article/linkedin-guide-2026) — repurposing strategy
- [Naval — How to Get Rich (without getting lucky)](https://nav.al/rich) — specific knowledge, leverage, tweetstorm-as-essay
- [Dan Koe — PAS/PASTOR + PPP frameworks (X post)](https://x.com/thedankoe/status/1775178639681651109) — short-form vs long-form structure
- [Dan Koe — How to Write Authentic Content](https://thedankoe.com/letters/dont-get-replaced-by-ai-how-to-write-authentic-content/) — voice-density anti-AI-slop
- [Sahil Bloom — Growth In Reverse profile](https://growthinreverse.com/sahil-bloom/) — paradox/razor/framework one-liner pattern
- [George Mack — Growth In Reverse profile](https://growthinreverse.com/george-mack/) — High Agency, counter-stereotype framing
- [High Agency in 30 Minutes — George Mack](https://www.highagency.com/) — primary text
- [Visakan Veerasamy — substack note on thread units](https://substack.com/@visakanv/note/c-98988639) — 3–7 units, max ~12, "unit of consideration"
- [Visakan Veerasamy threads archive](https://visakanv.github.io/threads/) — exemplar corpus
- [Greg Isenberg — audience building framework](https://www.contentgrip.com/greg-isenberg-audience-building-framework/) — ACP, post-as-MVP
- [Alex Hormozi — Give More, Ask Less (Ep 892)](https://www.shortform.com/podcast/episode/the-game-w-alex-hormozi-2025-05-23-episode-summary-give-more-ask-less-ep-892) — 98/2 ratio, jab-jab-jab-right-hook
- [Cody Schneider — Distribution Mastery podcast](https://www.distribute.so/podcasts/master-content-distribution-efficiently-cody-schneiders-top-tips-e005) — distribution-first frame
- [Paul Millerd — Pathless Path](https://pathlesspath.com/) — voice/lived-experience writing
- [Visa Slade / Visakan Veerasamy art-of-threading interview](https://threader.app/the-art-of-threading/a-conversation-with-visakan-veerasamy) — published thread theory

**Failure-mode catalogues:**
- [AI Slop — Wikipedia](https://en.wikipedia.org/wiki/AI_slop) — 2025 Word of the Year context
- [Why AI Slop Content Is Diluting Your Brand — Flux8Labs](https://medium.com/@flux8labs/why-ai-slop-content-is-diluting-your-brand-and-how-to-fight-it-fa8d7d27fb5b) — em-dash / "moreover" / tricolon signatures
- [Engagement Bait Tactics That Hurt Your X Growth — Success On X](https://successonx.com/guides/what-to-avoid/twitter-engagement-bait-traps) — named bait patterns
- [There is a reason your X feed has turned more toxic — Scroll.in](https://scroll.in/article/1072706/there-is-a-reason-your-x-feed-has-turned-more-toxic-have-you-heard-of-engagement-farming) — engagement-farming pathology
- [Elon Musk's engagement-farming suspension policy](https://x.com/elonmusk/status/1781183251731677264) — platform-level signal

---

## Notes for Rubric Authors

1. **The five proposed criteria (X-A through X-E) map to the judge-design-guide §13 specimen template** and follow §4 outcome-question shape: question → score-1 behavioral anchor → score-0 behavioral anchor → 0.5 as "unknown" way-out only. Each anchor cites a hedged example with "do not optimize toward this" per §7.
2. **Framework names live in §3 of this research, NOT in rubric prose.** Per `docs/rubrics/judge-design-guide.md` §11.1 and §12 anti-pattern #2 (framework-name embedding), the rubric prose stays framework-name-free. The judge reasons with Welsh / Cole-Bush / Naval / Mack / Bloom as private toolkit.
3. **Structural items routed to `structural_gate`:** character-count bands (single post ≤280, thread tweet count 3–12), URL resolution, hashtag count (≤2), image-attach validity, thread continuity (no broken reply chains). Do not score these in the judge.
4. **The "would a 100k-follower creator in this niche repost this?" test** is the synthesized version of the Hamel-Husain expert-rejection diagnostic for the x_engine lane. Useful as a frame in the optimal-output spec; not as a criterion in the rubric.
5. **What to deliberately NOT encode** (per design hygiene): no claims about specific topics or niches (would bias the judge across fixtures); no algorithmic weight numbers (algorithm changes faster than the rubric); no anti-bait clauses ("do not score engagement-bait higher" — theatrical, redistributes bias per §10); no length-thresholds in judge prose (route to structural_gate).
6. **Goodhart-resistance check (per §11):** the five criteria target reader effect (would-scroller-stop, would-peer-disagree, would-screenshot, etc.) rather than artifact features (has-hook, has-named-person, has-falsifiable-claim-marker). The design target is time-to-Goodhart on outcome-shaped criteria, watched via §11.5 variance instrumentation per generation.
