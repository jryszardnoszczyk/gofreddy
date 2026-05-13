# Phase B research — `x_engine` lane

Calibration corpus for the `x_engine` judge. Anchors what 9-tier looks like for a single ship-ready X post in JR's voice across three length brackets — sharp (250–300 chars), build (500–900), case_study (1000–1500) — against the 2026 X/Grok algorithm and the post-AI-slop attention floor. Goal: the judge predicts "would the operator publish this unedited" with veto patterns hard-capping the score.

Existing rubric: X-1 JR voice + plain language (auto-≤4 on jargon), X-2 factual grounding (hard floor ≤3 on unverifiable lived-work), X-3 hook earns next line, X-4 zero AI-tells, X-5 structure earns length, X-6 cohort diversity.

Lane-success target: ship-eligible rate ≥30%, near-ship ≥50%. The judge is the gate; everything below is what the gate has to recognise.

## 1. Top 9-tier signals

Each entry: what excellence looks like, source with engagement weight, mechanism (why this works in the post-March-2025 native-content regime), judge-able test. Graded on the artifact, not on 7-day impression outcomes.

### 1.1 (sharp) Observation that earns a screenshot — concrete object + non-obvious second beat
- **Description:** A 200–300-char post anchored on a concrete physical or numeric object, with a second beat that lands a non-obvious implication. Bar: `It's wild that you can drill a hole in the ground and drinking water comes out.` (Vassallo, `https://x.com/dvassallo/status/2052473028332941520`, 210 likes / 25 replies / 20.4K views, organic non-RT)
- **Source:** Vassallo's two highest organic-non-RT posts in the corpus are both single-sentence physical observations. The "drill a hole" tweet runs 80 chars; "DIY go kart" runs 67 chars (`https://x.com/dvassallo/status/2053145949200171266`, 291 likes / 27 replies). Both earn replies because they invite "yeah and also…" extensions.
- **Mechanism:** Sharp-bracket success in 2026 is "screenshot economy" — posts have to function as standalone artifacts that survive being cropped out of feed. Concrete nouns + unexpected angle = the format. Abstract claims at the same length die at 0 replies (the Welsh `Marry well, stay in shape, build something you own, and protect your time.` cluster, `https://x.com/thejustinwelsh/status/2053807858714587630`, gets likes but is platitude-tier — see §2).
- **Judge test:** (a) ≤300 chars, (b) ≥1 concrete proper noun OR sensory/physical object (not a category abstraction), (c) the closing clause is not the same beat as the opener — it adds an implication, contradiction, or twist that wasn't telegraphed in the first 10 words. All three for 9.

### 1.2 (sharp) Pithy declarative that compresses a real frame shift
- **Description:** 4–10 word axiom that names a real phenomenon people had no shorthand for. Bar: `AIs replace UIs and APIs.` (Naval, `https://x.com/naval/status/2050560057675522500`, 8,512 likes / 948 replies / 2.06M views). Or: `"What did you build this week?" is the new "what did you get done this week?"` (Naval, `https://x.com/naval/status/2050072434943144398`, 7,996 likes / 479 replies).
- **Source:** Naval's two highest organic-non-RT shorts both compress a 2026 shift into ≤80 chars. Reply-counts are huge (948, 479) because the format is intrinsically quote-tweet-bait — the structure invites "yes, and here's where I saw it." PG's `People are still getting cancelled, just for different things.` (`https://x.com/paulg/status/2053044738530382312`, 1,714 likes / 56 replies) is the same shape.
- **Mechanism:** Algorithm 2026 weights reply×13.5 and quote×20 vs like×1 (`https://opentweet.io/blog/how-twitter-x-algorithm-works-2026`). Axioms that compress a contemporary observation maximise quote-rate per impression because they hand the reader a frame they can apply. Same length but generic (`The most successful people I know are annoyingly unaware…`, Welsh) gets 215 replies on 5,391 likes — high absolute but a 4% reply rate vs Naval's 11%.
- **Judge test:** (a) ≤120 chars, (b) names a phenomenon, condition, or shift that is dated (post-2024 specifically), (c) is not a self-help platitude (no "be more X" or "successful people Y" framing). All three required.

### 1.3 (build) Named-person + numbers + lived-work scene
- **Description:** 500–900 char post that names ≥1 real person (collaborator, customer, source), carries ≥2 specific numbers, and grounds the claim in a scene the operator witnessed first-hand. Bar: PG's `A friend's startup is growing at 93% a month. I pointed out that her net worth is also growing at 93% a month, and that she can thus feel, in her own life, the falsity of politicians' claim that you have to do bad things to get rich. They're just focusing on making users happy.` (`https://x.com/paulg/status/2054195256615215467`, 3,695 likes / 200 replies / 223K views).
- **Source:** Vassallo's `Yapping about this game for 2 weeks not only brought 35,000 players and $8,500 in sponsorship revenue, but also my biggest X payout yet.` (`https://x.com/dvassallo/status/2052812834959175952`, 83 likes / 21 replies) — three numbers (2 weeks, 35K players, $8,500), one event (vibejam game), first-person verb. Dwarkesh's body-fat post (`https://x.com/dwarkesh_sp/status/2053490464968597771`, 578 likes / 28 replies, 597 chars) demonstrates the same shape at build length without self-reference: named domain (hunter-gatherers, agricultural societies), specific mechanism (food instability vs disease/famine), evolutionary direction reversed.
- **Mechanism:** Specificity density is what separates the rubric's X-2 hard floor from a pass. The 2026 grounding regime — both Grok's transformer ranker and reader trust post-AI-slop — collapses if the post lacks proper nouns or quantitative anchors. Adlibrary 2026 X algorithm guide names specificity as the single highest delta between viral and dead replies-per-impression (`https://adlibrary.com/guides/x-twitter-algorithm-explained`).
- **Judge test:** ≥1 named person/company/place (not "a friend"/"a guy") OR ≥2 distinct numbers AND ≥1 first-person verb of doing/witnessing (`I built`, `she shipped`, `we measured`). Build-bracket posts missing both quantitative anchor and named referent cap at 5.

### 1.4 (build) Hook that pays a debt within 2 lines
- **Description:** Opening sentence makes a falsifiable claim or asks a question whose answer ships in the next sentence — no thread tease, no "read on." Bar: `David Reich is back. He and collaborator Ali Akbari just published a paper that overturns a long-standing consensus about human evolution — that natural selection has been dormant in our species since the agricultural revolution.` (Dwarkesh, `https://x.com/dwarkesh_sp/status/2052798237828960334`, 1,962 likes / 67 replies, 2,156 chars).
- **Source:** Dwarkesh's hook formula is consistent across his top posts: name the source, state the overturned belief, state the new finding — all in the first 60 words. The `What was the most important transition in human history…` post (`https://x.com/dwarkesh_sp/status/2053128080802394601`, 1,254 likes / 51 replies, 859 chars) opens with a clean question, then commits to a structured answer in the same post. Compare to thread-tease hooks (§3.2) which dump the payoff into a reply.
- **Mechanism:** Long-post dwell-time weighting (`+10` weight per Tweet Archivist's 2026 breakdown, `https://www.tweetarchivist.com/how-twitter-algorithm-works-2025`) requires the reader to stay past the fold. A hook that doesn't deliver inside the visible window before the "Show more" cut surrenders the dwell signal. Native long-form posts have explicit dwell weighting now; threads do not get the same multiplier.
- **Judge test:** First 280 chars of a build/case_study post must contain (a) the claim or question, (b) the first substantive payoff beat, (c) no "thread below" / "more in replies" / "🧵". If the post forces the reader to leave the post to find the value, cap at 4.

### 1.5 (build) Plain-language reframe of an idea the reader half-knew
- **Description:** Takes an idea the audience has already encountered and re-states it without jargon, exposing the assumption behind it. Bar: PG's `It's an unimpressive-sounding word, but one of the most powerful motivations is the motivation of the hobbyist. That's what keeps successful founders working on their companies long past the point when they've made enough to quit. It's their beloved project.` (`https://x.com/paulg/status/2053432032621965741`, 3,488 likes / 203 replies, 290 chars).
- **Source:** Same structure across the PG corpus: `It's a rough combination when people are simultaneously overreaching and uninformed. They want the best of everything, but they don't know what the best is, so their demands are simultaneously strident and random, like a set of vectors with large magnitudes and random directions.` (`https://x.com/paulg/status/2053103261113000125`, 1,789 likes / 143 replies). Zero jargon, one technical simile (`vectors with large magnitudes and random directions`) deployed for clarity not status.
- **Mechanism:** Plain-language posts beat jargon-equivalent posts at all brackets in 2026 because the AI-slop floor has been raised — readers have been trained to skip business-jargon registers ("synergy," "leverage," "ecosystem"). The Wikipedia Signs-of-AI-writing index lists these among detected AI tells (`https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing`). Operator voice cuts through specifically by refusing the register.
- **Judge test:** Zero instances of: leverage (as verb), unlock, ecosystem, journey, synergy, ROI, value-add, scalable, holistic, optimize (without object). ≤1 instance of "important," "powerful," "interesting" as standalone adjectives. Failing this caps at X-1's automatic ≤4.

### 1.6 (case_study) Sustained argument with three locked beats
- **Description:** 1000–1500 char post that holds one thesis across three distinct evidentiary beats. Bar: Dwarkesh's `What was the most important transition in human history…` post (`https://x.com/dwarkesh_sp/status/2053128080802394601`, 1,254 likes / 51 replies, 859 chars) — opens with the question, enumerates two candidate answers, then introduces the adjudication mechanism (natural selection accelerates when environment changes), then names the empirical finding. Each beat could stand alone but compounds.
- **Source:** Dwarkesh's `David Reich doesn't think population size has been a big constraint on human evolution. Why?` (`https://x.com/dwarkesh_sp/status/2053853502905204960`, 260 likes / 558 chars) — (1) genome already has enough diversity, (2) weak selection swamped by drift only in small pops, (3) therefore pop size doesn't matter either way. Three numbered beats, no padding. Dwarkesh's intelligence-Bronze-Age post (`https://x.com/dwarkesh_sp/status/2053188381455298820`, 330 likes / 563 chars) follows the same shape: common idea → opposite empirical finding → mechanism.
- **Mechanism:** Long-form X (1,000+ chars) only earns the dwell multiplier if the reader gets to the bottom (`https://posteverywhere.ai/blog/how-the-x-twitter-algorithm-works`). Cases that meander past the first beat hemorrhage scrollers; the dwell signal goes negative and the post is downranked. Three locked beats give the reader a structural prediction — they know there's a payoff coming.
- **Judge test:** A case_study draft must contain ≥3 distinguishable substantive beats (not three rephrasings of the same point), each contributing new information to the thesis. A reader skim of the first sentence of each paragraph should produce a recognisable argument. Posts that pad to length with restatement cap at 5.

### 1.7 (case_study) Proprietary scene only the operator could witness
- **Description:** Long post grounded in a specific scene — a conversation, a build session, a meeting, a measurement — that no one else could have written because no one else was there. Bar: Vassallo's $8,500 vibejam post anchored in "2 weeks of yapping about this game." For JR's voice, the analogue would be: a specific autoresearch run that produced a counter-intuitive result with named lane + score numbers + the specific patch that fixed it.
- **Source:** Cyrus Shepard 2026-04-22 on "Non-Commodity Content" — proprietary scenes and named-source quotes are the 17 content-types Google's zero-click future rewards (`https://x.com/CyrusShepard/status/2046629661233553483`, 127 likes / 160 bookmarks). The same logic applies on X: when 1,000 generic founder-lesson posts compete for the same impression slot, the one with verifiable lived detail wins.
- **Mechanism:** Lived-work scenes pass the X-2 hard floor by definition (the operator was there, the claim is verifiable against their public history). They also score the algorithm's "credible-account engagement" weight (Bisonary 2026, `https://www.bisonary.com/blog/best-twitter-growth-tools`) because the format invites credible-account replies — peers in the same domain respond to specifics, not platitudes.
- **Judge test:** Case_study posts (1000+ chars) must contain ≥1 datable scene (week or month resolution) AND ≥1 piece of evidence the operator could reasonably possess but a generic writer could not (an internal number, a private conversation excerpt with attribution, a specific build artifact). Posts that read as "I have observed in my career that…" without anchoring cap at 5.

### 1.8 (all brackets) Reply-worthy structure — leaves a hook for response
- **Description:** Post ends in a way that hands the reader a clean response surface — an open question they can answer with specifics, a claim they can corroborate or correct with their own example, a hot-take they can quote-tweet with disagreement. Bar: Naval's `"What did you build this week?" is the new "what did you get done this week?"` — every founder reading it has a specific build to name in reply. 479 replies on 7,996 likes = 6% reply-rate.
- **Source:** PG's `93% a month` post — 200 replies on 3,695 likes (5.4%). Dwarkesh's `David Reich is back` — 67 replies on 1,962 likes but 2,156 chars, so 3.4% reply rate per char-adjusted (long posts have lower nominal reply rates because reading-to-replying funnel is steeper). Compare to Welsh's `Marry well, stay in shape…` at 2.6% (138/5,391) — the closed-list register doesn't invite specifics in reply.
- **Mechanism:** Reply×13.5 and reply-from-author×150 (Conbersa 2026, `https://www.conbersa.ai/learn/what-is-twitter-algorithm`) make reply-rate the dominant lever above ~1K impressions. A post-shape that invites reply doubles the algorithmic distribution per like. The 70/30 reply strategy (Teract 2026, `https://www.teract.ai/resources/grow-twitter-following-2026`) describes the same dynamic from the consumption side.
- **Judge test:** End of the post must do one of: (a) ask a question whose answer is a specific example, (b) state a claim that a reader with relevant experience would feel compelled to corroborate or correct, (c) reference an unsettled question. Posts that end in a button-up ("That's the lesson," "Stay curious," "Build something") cap at 5.

### 1.9 (all brackets) Native-only — zero external links in body
- **Description:** Post contains no `t.co` link to an external destination. Quote-tweets, native media, and replies to threads are fine; external blog/YouTube/Substack links are not. Bar: Naval, Dwarkesh, PG organic non-RT bodies — no external links. Naval's USVC post (`https://x.com/naval/status/2046991137022648800`, 12K likes, 5.3M views) is the exception that proves the rule: he embeds the full pitch in 2,000+ native chars and only adds the link at the bottom.
- **Source:** Buffer 2026 on the X link penalty (`https://buffer.com/resources/links-on-x/`): since March 2025, link posts from non-Premium accounts have median engagement at zero; the open-sourced algorithm code carries a 30–50% reach penalty for external links. October 2025 X softened the stance for in-app browser handling (`https://www.socialmediatoday.com/news/x-formerly-twitter-testing-links-in-app-link-post-penalties/803176/`) but native-only still outperforms in throughput.
- **Mechanism:** The algorithm wants users to stay on platform. Posts that pull users off-platform tank dwell-time AND reply-velocity in the critical first 30-minute window. Native-only is not stylistic — it's a distribution requirement.
- **Judge test:** Zero `http://`, `https://`, `t.co/`, `bit.ly/`, or naked-domain (`example.com`) tokens in body text. Embedded media (image, video, native quote-tweet of another X post) is fine. Failing this caps at 5 regardless of content quality.

### 1.10 (all brackets) Voice purity — pronoun + register match operator's recent posts
- **Description:** First-person register matches operator's last 30 days. JR's voice is: lowercase casual when sharp, full sentences when build, no exclamation, no emoji except occasional one-token (📈), dashes used for asides not for effect, references to specific projects (autoresearch, Freddy, GoFreddy stack) by name not by hand-wave.
- **Source:** Vassallo's $8,410 update (`https://x.com/dvassallo/status/2049932774564635010`, 56 likes / 10 replies) uses `$8,410 now! 📈` — one number, one emoji, one verbal beat. Across his 20 posts there are zero hashtags, zero exclamation outside numeric updates, consistent first-person. PG never uses `🧵`, `1/`, or thread markers. Welsh occasionally drifts toward listicle template (`How to increase your luck:`) — that's the boundary where his voice tips into LinkedIn-on-X (§3.1).
- **Mechanism:** Voice authenticity is the primary anti-slop signal in 2026. The AI-slop detector industry (ZeroSlop, ThatSlop — `https://chromewebstore.google.com/detail/thatslop-%E2%80%94-ai-slop-detect/ghohaianocgoennpjlllbdglmnljijcl`) flags inconsistent register within a single account as well as cross-account uniformity. A post that doesn't match the operator's recent voice gets flagged by readers even before the slop heuristics fire.
- **Judge test:** Score against ≥10 most recent operator-authored posts: lowercase ratio, sentence-length distribution, emoji usage, hashtag presence, exclamation frequency. Drafts outside ±1σ on more than two of these dimensions cap at 5. X-1's auto-≤4 on jargon already encodes part of this — voice-purity strengthens it.

## 2. Top 5-tier signals

Competent but doesn't earn the scroll-stop or build audience. These are the posts the operator could ship but wouldn't screenshot.

### 2.1 Generic self-help axiom (closed register, no specifics)
- **Bar:** Welsh's `Marry well, stay in shape, build something you own, and protect your time.` (`https://x.com/thejustinwelsh/status/2053807858714587630`, 2,757 likes / 138 replies). The four-clause list is well-balanced, the advice is defensible, the register is clean — but there's no specific moment, no named referent, no falsifiable claim. The 5% reply rate (138 / 2,757) is half of Naval's comparable shorts.
- **Why 5 not 9:** Engagement is real but ceiling-bound. The post can never trigger a quote-tweet that names a specific example because the source post offers no specific to attach to.
- **Judge test fail:** No proper noun, no number, no datable scene, no contrarian beat.

### 2.2 Standalone declarative without dating or anchor
- **Bar:** Welsh's `The most successful people I know are annoyingly unaware of what everyone else is doing.` (5,391 likes / 215 replies, 4% reply rate). Mid-tier because the claim is plausible but not falsifiable — "the successful people I know" is unverifiable, and "annoyingly" softens the claim into a brag-disguised-as-observation.
- **Why 5 not 9:** Compared to Naval's `AIs replace UIs and APIs.` — same length category, same declarative shape — Naval's compresses a dateable shift (post-2024 agent stack); Welsh's compresses a vibe.
- **Judge test fail:** No 2025/2026 dateable phenomenon, no measurable claim, anchor relies on "people I know."

### 2.3 Productivity list with no surprising entry
- **Bar:** Welsh's `How to increase your luck: - Read more - Write more - Build more - Meet more people - Introduce more people` (`https://x.com/thejustinwelsh/status/2051287490372194477`, 1,016 likes / 186 replies). Reply count is OK because list format invites "what about X" responses, but every entry is the consensus answer.
- **Why 5 not 9:** A 9 here would either contradict the consensus (one item that surprises) or anchor each item with a specific number/example. The bare list is template content the audience can predict before reading.
- **Judge test fail:** Every list item is the modal answer for the topic; no entry surprises or contradicts.

### 2.4 Single emoji-anchored update without context
- **Bar:** Vassallo's `$8,410 now! 📈` (56 likes / 10 replies, 9.3K views). The format is in-voice for Vassallo specifically (he runs ongoing public revenue updates), so it earns its existence — but as a standalone first-time post from a new operator it would be 5-tier: no context, no narrative beat, no reply hook beyond "congrats."
- **Why 5 not 9:** Requires audience to already know what's being tracked. For a building-audience operator, this is a low-leverage format.
- **Judge test fail:** Post requires audience prior to parse; no in-post context, no narrative beat.

### 2.5 Quoted-find with no operator commentary
- **Bar:** RT-only posts (Vassallo's RT of `@dropalltables` heated-pool datacenter joke, 11,581 likes — the joke is great but the operator added nothing).
- **Why 5 not 9:** Reach signal is misleading — the engagement belongs to the original post. From the operator's distribution perspective, this is at best a relevance signal for the algorithm, not voice-building.
- **Judge test fail:** Post is `RT @user: …` or naked quote-tweet with no added thought.

## 3. Slop patterns (1-tier — automatic veto)

Each pattern caps the draft at 1 regardless of other dimensions.

### 3.1 LinkedIn-on-X (inspirational arc + business jargon)
- **Signature:** Three-line structure — setback, lesson, inspirational close. Words: leverage, unlock, journey, mindset, ecosystem, growth, scalable. Sample slop: `I almost quit last week. Then I remembered: every setback is a setup. Now we're unlocking 10x growth. Stay relentless.`
- **Detection:** ≥2 of {leverage, unlock, journey, mindset, ecosystem, relentless, hustle}; emotional-arc structure; closing imperative without an action object.
- **Veto:** Auto-1, cannot be rescued by other dimensions.

### 3.2 Thread-baiter (`🧵 1/`)
- **Signature:** Opening line is a list-promise; post contains `🧵`, `1/`, `(thread)`, `🪡`, or `↓`. Real value sits in replies the reader has to chase.
- **Detection:** Token match on the markers above; also `Here are the 7 X you need to Y` opener with no payoff in the same post.
- **Veto:** Auto-1. Dwell-time weighting in 2026 punishes the format directly — value siloed in replies forfeits the long-post dwell multiplier. Note: a thread-style multi-post sequence where the first post is itself complete and the replies extend rather than gate-keep is fine; the veto is for posts whose value is in the reply chain, not the post body.

### 3.3 Generic-bro confident declarative
- **Signature:** Confident assertion + zero specificity + reciprocity ask. Sample: `99% of founders fail because they don't focus. Drop a 🚀 if you agree.`
- **Detection:** Reciprocity-CTA tokens (`drop a`, `like if`, `follow for more`, `RT to spread`, `comment 'X' below`); plus declarative percentage with no source.
- **Veto:** Auto-1.

### 3.4 Hashtag-stuffer
- **Signature:** ≥2 hashtags, especially `#AI #buildinpublic #startup #growthmindset` clusters.
- **Detection:** Hashtag count ≥2 in body, or any `#growthhacking` / `#mindset` / `#hustle` / `#entrepreneurlife` token.
- **Veto:** Auto-1. Hashtag use on X 2026 is a slop tell (`https://aifreeforever.com/blog/9-proven-tips-for-writing-twitter-x-posts`) — the algorithm doesn't use them for distribution and readers treat them as bot signature.

### 3.5 Growth-hack-template (`I did X for Y days. Here's what happened:`)
- **Signature:** `I did [activity] for [N] days. Here's what happened:` opener. Or `I read [N] books on [topic]. Here are the [M] lessons:` variant. Or `[N] [things] every [role] should [verb]:` listicle opener.
- **Detection:** Regex on the opener templates; also `Bookmark this thread for later.`
- **Veto:** Auto-1. These templates are the most-trained AI-slop pattern of 2025–2026 and are flagged by all major slop detectors.

### 3.6 Rage-bait
- **Signature:** Universalising negative claim about a group, no specifics, designed for quote-tweet anger. Sample: `Most founders are frauds. They sell hope and ship nothing.`
- **Detection:** Universalising quantifier (`most`, `every`, `all`, `99%`) + negative emotional adjective + identity group + no anchoring example.
- **Veto:** Auto-1. The 2026 "unregretted user-seconds" reform (`https://reclaimthenet.org/elon-musk-x-algorithm-overhaul-unregretted-user-seconds`) explicitly de-prioritizes rage-bait that "technically grows user time, but not unregretted user time." Mute/block-rate from credible accounts is now a downrank signal.

### 3.7 AI-laundered insight (plausible but generic)
- **Signature:** Reads coherent, no obvious slop markers, but the claim is consensus-summary the reader could have written. Em-dashes used as syntactic glue (`The thing is — and this matters — most people…`). Sentence rhythm uniform. No proper nouns, no numbers, no dates.
- **Detection:** ≥3 em-dashes used as structural connectors (not for asides); zero proper nouns; sentence-length variance below 1σ of operator baseline; "delve," "navigate," "leverage" as verbs; `It's important to note`, `It's worth mentioning`. Per `https://www.ignorance.ai/p/the-field-guide-to-ai-slop`: openers like "Absolutely!", filler `it's important to note`, bullet-points for simple answers.
- **Veto:** Auto-1. This is the most insidious slop because it passes surface QC. Detection has to combine structural signature (em-dash density, sentence-length uniformity) with content signature (zero specificity).

## 4. What separates 9-tier from 5-tier

Specific dimensions where the gap is measurable in the draft text, not in post-hoc engagement.

### 4.1 Hook stop-power (≤100 chars)
- **9-tier:** First 100 chars contain a concrete noun + a non-obvious claim or question. Examples: `David Reich is back.` (16 chars, full payoff in the next 60); `It's wild that you can drill a hole in the ground and drinking water comes out.` (full thought in 80 chars); `A friend's startup is growing at 93% a month.` (44 chars, anchored on the number).
- **5-tier:** First 100 chars are setup — `The most successful people I know…` (35 chars before the predicate lands), `Life hack 101:` (label without content).
- **Test:** First 100 chars must contain ≥1 concrete noun AND deliver enough payload that the reader could screenshot the first sentence as a thought. Labels and category nouns (`successful people`, `life hack`) without an anchor cap at 5.

### 4.2 Specificity density (proper nouns + numbers per 100 words)
- **9-tier:** ≥3 proper nouns OR ≥2 specific numbers per 100 words. Dwarkesh's posts run dense — David Reich, Ali Akbari, Indian, Bronze Age, 10,000 BC, 1800 AD, 5,000 years, 90% — in 200 words. Vassallo runs $8,500 / 2 weeks / 35,000 players in 30 words.
- **5-tier:** ≤1 proper noun, ≤1 number per 100 words. Welsh's `Marry well, stay in shape, build something you own, and protect your time.` — zero proper nouns, zero numbers.
- **Test:** Count proper-noun tokens (NER) + numeric tokens; divide by word count × 100. Bar for 9: ≥3 combined per 100 words. **This is the load-bearing signal X-2 currently underweights.** A post can pass X-2 (no unverifiable lived-work) by saying nothing specific; the new specificity-density metric forces something specific to be said.

### 4.3 Authority anchoring
- **9-tier:** Lived experience (operator was there) OR named source (`David Reich's lab found`, `Y Combinator's data`). Verifiable.
- **5-tier:** "I've noticed," "I've found," "people often say" — first-person observational without specific anchor.
- **Test:** Every load-bearing claim must trace to (a) operator's own work with datable referent, (b) named third party that can be looked up, or (c) public dataset/study with reference. Unanchored generalisations cap at 5.

### 4.4 Voice authenticity (cross-post variance + register match)
- **9-tier:** Matches operator's recent posts on lowercase ratio, sentence length, emoji frequency. Doesn't drift into list-template or LinkedIn register.
- **5-tier:** Generically competent but stylistically inert; reads like the operator could have written it but also like 1,000 other people could.
- **Test:** Compute style fingerprint against operator's last 30-day window. ±1σ on ≥3 dimensions = drift, cap at 5.

### 4.5 Original perspective (vs consensus summary)
- **9-tier:** Either takes a position the modal post on the topic doesn't take, or reveals an angle the topic-discourse has missed. Dwarkesh's Bronze-Age-favoured-intelligence post inverts the "society lets us outsource thinking, so intelligence-selection weakened" consensus.
- **5-tier:** Restates what the audience already knows; the post adds no information beyond the reader's prior.
- **Test:** Adversarial check — could the operator's competitor have published the same post? If yes, cap at 5. If the post would only have come from this operator's specific corpus of work, score for 9.

### 4.6 Reply-worthiness
- **9-tier:** Ending hands the reader a clean response surface — open question, falsifiable claim, named-but-incomplete observation.
- **5-tier:** Closes the thought cleanly with a moralism or summary; nothing for the reader to add.
- **Test:** Read the last sentence in isolation. Does it invite a reply that adds specifics? If yes, score for 9. If it's a button-up, cap at 5.

### 4.7 Algorithmic-citizenship (no external links + native-format)
- **9-tier:** Zero external links in body. Native media if used. Text optimised for in-feed reading.
- **5-tier:** External link in body. Or post body is a tease pointing elsewhere.
- **Test:** Token-match external-link patterns. Failing this is an automatic distribution cap; the post can be substantively excellent but is delivery-broken.

## 5. 2026 emerging signals

### 5.1 Grok-powered ranking (January 2026 cutover)
Per `https://posteverywhere.ai/blog/how-the-x-twitter-algorithm-works`: xAI replaced the legacy ranker with a transformer model (Phoenix) in the Home Mixer / Thunder / Phoenix / Candidate Pipeline architecture. The model reads every post and watches every video. Implication: content-level features (specificity, voice consistency, claim verifiability) now matter at the ranking layer, not just engagement-feedback features. This is what makes specificity-density a distribution lever and not just a reader-quality lever.

### 5.2 Long-post dwell-time multiplier (+10 weight)
Per `https://www.tweetarchivist.com/how-twitter-algorithm-works-2025`: dwell time on long-form content (2+ minutes) carries +10 weight in the score. Native long-form posts above 1,000 chars get the multiplier; threads do not get it the same way. Implication: case_study bracket (1,000–1,500 chars) now has a structural distribution advantage over multi-post threads — but only if the post earns the dwell (no thread-tease, no padding, three locked beats per §1.6).

### 5.3 External-link reach reduction (March 2025 → October 2025 partial softening)
Per `https://buffer.com/resources/links-on-x/`: link posts from non-Premium accounts had median engagement at zero from March 2025 onward; open-sourced code carries a 30–50% reach penalty for external links. October 2025 X announced removal of algorithmic penalties on link posts (`https://www.socialmediatoday.com/news/x-formerly-twitter-testing-links-in-app-link-post-penalties/803176/`) but native content still consistently outperforms. Implication: native-only is still the dominant pattern; treat the October 2025 softening as risk-reduction, not policy-shift. Algorithmic-citizenship stays in the rubric.

### 5.4 Reply×13.5 / quote×20 / author-reply×150 weights
Per `https://opentweet.io/blog/how-twitter-x-algorithm-works-2026`: simplified scoring `Likes × 1 + Retweets × 20 + Replies × 13.5 + Profile Clicks × 12 + Link Clicks × 11 + Bookmarks × 10`, with a reply-from-author worth 150× a like. Implication: reply-worthiness is the second-largest distribution lever after specificity density. Engagement-velocity in the first 30 minutes drives the broadcast (`https://www.bisonary.com/blog/best-twitter-growth-tools`), and replies drive velocity.

### 5.5 Unregretted-user-seconds reform
Per `https://reclaimthenet.org/elon-musk-x-algorithm-overhaul-unregretted-user-seconds`: the algorithm now penalises content that grows user time but generates regret — operationalised via mute/block-rate from credible verified accounts. Implication: rage-bait and inspirational-arc slop are not just style-bad — they're algorithmically downranked once the credible-account-mute signal fires. The slop vetos in §3 align with the algorithm's own filter.

### 5.6 AI-slop detection industry maturing
Per `https://www.ignorance.ai/p/the-field-guide-to-ai-slop` + ZeroSlop / ThatSlop browser extensions: readers can install client-side AI-slop detectors that mark posts in real time. The detection heuristics target: em-dash density used as structural connector, opener vocabulary (`Absolutely!`, `Picture this`), filler phrases (`it's important to note`), bullet-points for simple answers, uniform sentence-length distribution. The Wikipedia AI-writing signs page is becoming canonical (`https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing`). Implication: AI-tells in 2026 are not just GPT-3-era hallucination — they're stylistic fingerprints. The X-4 criterion needs to encode the 2026 signature set, not the 2023 set. GPT-5.1 specifically suppresses em-dashes now (per `https://medium.com/@brentcsutoras/the-em-dash-dilemma-how-a-punctuation-mark-became-ais-stubborn-signature-684fbcc9f559`), so em-dash absence is no longer exonerating; the new tells are sentence-rhythm uniformity and specificity-density vacuum.

### 5.7 Premium / verification reach multiplier (~10×)
Per `https://www.bisonary.com/blog/best-twitter-growth-tools`: Premium accounts get ~10× reach per post. This is structural and not addressable from the judge side (it's a configuration not a content feature) but it bounds expected distribution outcomes — the judge should not penalise a draft for failing to break out if the operator is not Premium. Document this as a confounder when calibrating ship-eligible rate against post-hoc impressions.

## 6. Implications for the judge — keep / strengthen / split + new criteria

### Existing rubric updates

**X-1 (JR voice + plain language, auto-≤4 on jargon):** KEEP. Strengthen by expanding the jargon list to include the 2026 AI-slop opener vocabulary (`Absolutely`, `Picture this`, `It's important to note`, `delve`, `navigate`) on top of the current business-jargon list. The auto-≤4 floor is the right shape; the list needs the 2026 update.

**X-2 (factual grounding, hard floor ≤3 on unverifiable lived-work):** KEEP the hard floor. STRENGTHEN by pairing with X-7 (new — see below) on specificity density. Currently X-2 catches false-lived-work; it doesn't catch posts that are vacuously generic but technically verifiable ("startups grow when founders focus"). Specificity density is the load-bearing companion metric that forces something specific to be said even when nothing is being claimed about the operator's own work.

**X-3 (hook earns next line, bracket-aware):** KEEP. STRENGTHEN with the §4.1 test: first 100 chars must contain ≥1 concrete noun AND deliver enough payload that the reader could screenshot the first sentence. Currently "earns next line" is interpreted broadly; the concrete-noun-by-char-100 test makes it operationalisable. Bracket-aware adjustment: sharp posts hit the bar by 100 chars; build/case_study hit it by 280.

**X-4 (zero AI-tells):** KEEP, but UPDATE the detection set to 2026. Drop em-dash density as primary signal (GPT-5.1 suppresses it). Add: sentence-length variance below operator baseline, uniform paragraph-length pattern (3+ paragraphs of similar length), absence of proper-noun anchors paired with confident-declarative register, opener vocabulary (`Absolutely`, `Picture this`, `Here's the thing`).

**X-5 (structure earns length, bracket-aware):** KEEP. STRENGTHEN for case_study with the §1.6 three-locked-beats test: case_study posts must contain ≥3 distinguishable substantive beats, each contributing new information. Padding-by-restatement is the failure mode this targets.

**X-6 (cohort diversity):** KEEP. No update — this is set-level not draft-level, and the current implementation is sound.

### New criteria

**X-7 (NEW): Specificity density — important tier**
- **Mechanism:** Operationalises the load-bearing gap that X-2 leaves. Forces proper nouns and numbers regardless of whether the post is about the operator's own work.
- **Score-1:** Zero proper nouns AND zero numbers in the post. Pure abstraction.
- **Score-3:** 1 proper noun OR 1 number total; insufficient density for the bracket.
- **Score-5:** Meets minimum density (≥1 proper noun + ≥1 number per 100 words) but neither is load-bearing — could be removed without changing the claim.
- **Score-7:** Meets density and ≥1 anchor is load-bearing (claim depends on it).
- **Score-9:** ≥3 proper nouns OR ≥2 specific numbers per 100 words AND ≥1 anchor is the post's central claim.
- **Ground-truth verification:** Spacy NER on the draft text, plus regex on numeric tokens. Compute density per 100 words. Quick automatable check; doesn't need an LLM call.

**X-8 (NEW): Reply-worthiness — important tier**
- **Mechanism:** Reply-rate is the second-largest distribution lever in the 2026 algorithm. The judge needs to predict it from text features.
- **Score-1:** Post ends with a button-up moralism or summary statement; no surface for reply.
- **Score-3:** Generic open-ended close (`thoughts?`, `agree?`) without an anchored hook.
- **Score-5:** Closes with a claim that could be replied to, but the response would be generic ("good point," "agreed").
- **Score-7:** Ending invites a specific reply — open question, falsifiable claim, named-but-incomplete observation.
- **Score-9:** Ending is a clean response surface that the operator's specific audience would feel compelled to answer with their own example, correction, or anchored disagreement.
- **Ground-truth verification:** LLM-judged on the last sentence in isolation; "would a reader with relevant experience feel compelled to reply with specifics, and what would they say?" If the answer is generic affirmation, cap at 5.

**X-9 (NEW): Algorithmic-citizenship — essential tier (cap at 5 on failure)**
- **Mechanism:** Native-format compliance. External links and thread-tease formats forfeit distribution before content quality is evaluated.
- **Score-1:** Body contains external link AND thread-tease marker. Distribution-broken twice over.
- **Score-3:** Body contains external link OR thread-tease marker. Distribution-broken on one axis.
- **Score-5:** Native format compliant but post would have been better as a multi-post sequence (long-form padding when the content didn't earn it).
- **Score-7:** Clean native-format. Appropriate length for content. No distribution-broken patterns.
- **Score-9:** Native-format + content optimised for in-feed reading (clean line breaks, first sentence is the hook, no formatting that reads weird in the timeline).
- **Ground-truth verification:** Token-match for `http`, `https`, `t.co`, `bit.ly`, `🧵`, `1/`, `(thread)`, `↓`. Auto-cap at 5 on failure.

**X-10 (NEW): Original perspective — pitfall tier**
- **Mechanism:** Distinguishes 9-tier from competent-consensus. The adversarial "could the operator's competitor have published the same post?" test.
- **Score-1:** Post is a verbatim restatement of consensus on the topic; reader's prior is unchanged after reading.
- **Score-3:** Post is consensus + first-person framing; reader's prior is unchanged but the operator is now associated with the consensus.
- **Score-5:** Post adds an angle but it's a well-known one in the discourse; doesn't change anyone's prior.
- **Score-7:** Post takes a position the modal post on the topic doesn't take, or reveals a specific angle the discourse has missed.
- **Score-9:** Post inverts a consensus or reveals an observation that could only have come from the operator's specific corpus of work; the post is non-substitutable.
- **Ground-truth verification:** LLM-judged with the prompt "Could a competent generalist writer in the same domain have written this post without access to the operator's specific work, conversations, or measurements? If yes, score ≤5. If no, score for 9."

### Composition rule

Final draft score is the minimum of (X-1, X-2, X-9) — the three essential criteria with caps — and the weighted mean of (X-3, X-4, X-5, X-7, X-8, X-10) for the substantive quality, with X-6 evaluated set-level for diversity. The auto-≤4 (X-1 jargon), hard-≤3 (X-2 unverifiable lived-work), and auto-≤5 (X-9 algorithmic-citizenship) floors compound. Three slop-veto patterns (§3) drop the draft to 1 regardless.

Target calibration: on the operator's last 30 days of organic non-RT posts, the judge should rate ≥30% as ship-eligible (≥7) and ≥50% as near-ship (≥6). If actual operator-shipped posts cluster below that threshold, the judge is over-strict; if ≥50% rate ≥7 and operator-shipped posts include LinkedIn-on-X drift, the judge is under-strict on the slop vetos.

Sources:
- [How the Twitter/X Algorithm Works in 2026 (Source Code)](https://posteverywhere.ai/blog/how-the-x-twitter-algorithm-works)
- [The X Algorithm in 2026: What Actually Makes Posts Go Viral | OpenTweet](https://opentweet.io/blog/how-twitter-x-algorithm-works-2026)
- [How the Twitter Algorithm Works in 2026: Complete Technical Breakdown | Tweet Archivist](https://www.tweetarchivist.com/how-twitter-algorithm-works-2025)
- [Do Posts with Links Affect Content Performance on X? | Buffer](https://buffer.com/resources/links-on-x/)
- [X Is Testing a New Way To Handle Links in Posts | Social Media Today](https://www.socialmediatoday.com/news/x-formerly-twitter-testing-links-in-app-link-post-penalties/803176/)
- [How Does the X (Twitter) Algorithm Work in 2026? | Conbersa](https://www.conbersa.ai/learn/what-is-twitter-algorithm)
- [Best Twitter Growth Tools in 2026 | Bisonary](https://www.bisonary.com/blog/best-twitter-growth-tools)
- [How to Grow on Twitter/X in 2026: The 70/30 Reply Strategy | Teract](https://www.teract.ai/resources/grow-twitter-following-2026)
- [X Algorithm Explained 2026 | AdLibrary](https://adlibrary.com/guides/x-twitter-algorithm-explained)
- [Elon Musk Announces Algorithm Overhaul for X — "Unregretted User-Seconds" | ReclaimTheNet](https://reclaimthenet.org/elon-musk-x-algorithm-overhaul-unregretted-user-seconds)
- [The Field Guide to AI Slop | Charlie Guo](https://www.ignorance.ai/p/the-field-guide-to-ai-slop)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [The Em Dash Dilemma | Brent Csutoras / Medium](https://medium.com/@brentcsutoras/the-em-dash-dilemma-how-a-punctuation-mark-became-ais-stubborn-signature-684fbcc9f559)
- [ThatSlop AI Slop Detector | Chrome Web Store](https://chromewebstore.google.com/detail/thatslop-%E2%80%94-ai-slop-detect/ghohaianocgoennpjlllbdglmnljijcl)
- [9 Proven Tips for Writing Twitter/X Posts in 2026 | AI Free Forever](https://aifreeforever.com/blog/9-proven-tips-for-writing-twitter-x-posts)
