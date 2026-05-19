---
date: 2026-05-19
type: research deliverable — comprehensive scope mapping
status: complete v1
topic: x_engine lane v2 — full surface of valuable X workflow activities
parent: docs/handoffs/2026-05-18-judge-design-step1-x-engine.md
companions:
  - docs/research/2026-05-18-judges-domain-x-engine.md
  - docs/research/2026-05-18-x-engine-algorithm-jan-2026.md
  - docs/research/2026-05-18-x-engine-hook-discipline.md
  - docs/research/2026-05-18-x-engine-voice-screenshot-test.md
  - docs/research/2026-05-18-x-engine-ai-slop-detection.md
guide: docs/rubrics/judge-design-guide.md
audience: lane redesigners, plan authors, judge designers, evolution operators
constraint: do NOT scope-reduce; do NOT propose criterion prose; the existing 5-criterion judge
            covers the *artifact* layer — this doc maps the *workflow* layer the lane is currently missing.
---

# X Engine — Comprehensive Scope (2026)

## TL;DR

The current x_engine v1 spec (`2026-05-18-judge-design-step1-x-engine.md` §1.5) locks the artifact shape to ONE of: a single ≤280-char post, or a thread of 3–12 tweets. That decision is correct *for the judge* (shape-drift Goodhart is real and the lock prevents Frankenstein artifacts) but it is incorrect *for the lane*. An X workflow that ships only single posts and threads in 2026 is operating on a 2021 mental model of X. The platform that the Phoenix transformer ranks (xai-org/x-algorithm Jan/May 2026), that 21% YoY more replies and 35% more reposts flow through, that has absorbed Articles + Communities + Spaces + Premium-gated long-form + Grok-tone analysis, has at least **24 distinct activity surfaces** a serious account operates across. A workflow that produces only the artifact (post / thread) and not the rest leaves 80% of the value on the table.

This document maps the full surface. The judge layer (5 criteria, locked) stays as-is for per-draft artifact scoring. What this doc adds is the *workflow scope* the lane should produce when it ships for a client: profile audit + content strategy + cadence plan + reply-discovery list + DM templates + Spaces strategy + Communities participation + series-arc plan + measurement plan + 30/60/90 execution roadmap — alongside the individual posts and threads. The deliverable shape becomes a multi-artifact bundle, not a single artifact, and the evolution loop scores across the bundle's *coherence* + the bundle's *per-component quality*, not just on whether one tweet survives the screenshot test.

The five most-load-bearing additions to scope: (1) **reply-discovery strategy** — replies to bigger accounts in the niche is the single highest-ROI growth lever in 2026 (one operator went 500 → 12,000 followers in 6 months on a 70/30 reply-to-original ratio; reply-with-author-response is ~150× a like in algorithmic weight); (2) **profile-as-conversion-surface** — bio + pinned + banner + custom URL + handle convert profile-clicks (12× weight) into follows; a well-optimized profile doubles follow-rate from the same content; (3) **bookmark engineering** — bookmarks are 10× a like, and "would a reader save this for later" is now a first-class content design axis (reference frameworks, dated playbooks, screenshot-survivable checklists); (4) **Spaces + Communities + Articles** — three under-used surfaces a Premium account can monetize as authority anchors; X has declared 2026 "the year of the creator" with a $1M Articles writing contest and structurally-baked-in Premium boost (+4× in-network / +2× out-of-network); (5) **series-arc cadence over weeks** — single-post-or-thread per generation is a one-shot artifact; a series arc ("here's what I'm learning building X over the next 8 weeks") is a compounding-attention engine. Indie hackers documented as growing audiences on build-in-public arcs include Pieter Levels (600k followers over 10 years, $40-60M net worth), Daniel Vassallo (small-bets portfolio in public), Justin Welsh (solopreneur framework). The arc is the lane's missing 7th content shape.

The five biggest cuts vs old-school playbooks: (1) engagement-bait CTAs ("Like if you agree," "RT if X," "Drop a 🔥") — Grok-flagged as `engagement_arbitrage`, ≈−74× negative-signal cascade; (2) external-link-in-body — 94% reach reduction for non-Premium in Q1 2026, near-zero median engagement since March 2026; (3) fake-vulnerability bait ("I lost everything. Three lessons.") — composed-engineer voice tell, AI-slop fingerprint; (4) "Stop X. Start Y." imperative-pair rhythm — endemic to AI-generated founder content, Tier-2 structural slop signature; (5) generic motivational-quote single-posts — fail X-2 (specific knowledge) and X-3 (falsifiable disagreement) simultaneously; algorithmically suppressed via tone-based ranking.

The deliverable architecture for v2: instead of one artifact per evolution iteration, the lane ships a **12-component bundle** the first time it engages a client (profile audit, strategy doc, sample posts, sample threads, reply-target list, DM templates, Spaces brief, Communities map, series-arc storyboard, measurement plan, 30/60/90 roadmap, cross-platform syndication rules) — and then per-cycle increments (post / thread / reply suggestion / quote-tweet add / Spaces recap / Article draft / DM template / pinned tweet rotation). The evolution loop is scoped across this bundle's coherence (one workflow shouldn't ship a "data-rich SaaS founder" voice doc plus posts in "vulnerability-bait coach" voice) plus per-component quality (each artifact passes its own judge). The 5-criterion artifact judge stays; a bundle-coherence judge gets added (§5 below).

Vertical adjustments matter at the strategy layer, not the artifact layer. A SaaS founder operating on X has a different reply-target graph (other founders, VCs, technical buyers) than an AI lab researcher (other researchers, journalists, technical influencers) than an agency principal (agency-prospects, fellow-agency-operators, marketing decision-makers) than a finance operator than an indie e-commerce operator. The bundle's reply-target list, Communities map, and Spaces brief change per vertical; the judge criteria do not.

This doc is comprehensive scope mapping, not implementation. It surfaces what the lane *could* do; the operator and plan author decide which surfaces ship in v1.5 vs v2 vs v3. The hard constraint flagged at the top of every section: each surface either passes through the existing 5-criterion judge (artifact-shaped) or is scored at the bundle layer (workflow-shaped) — no surface is left unscored, no surface is scored with a 6th feature-shaped criterion that re-creates Phase-4 pathology.

---

## §1. Full Surface — 24 Axes the Lane Should Map

These are the activity surfaces an X account should operate across in 2026. Each is named, briefly defined, evidence-grounded (algorithm signal or practitioner playbook), and bucketed as "artifact" (lane already produces, judge already scores) or "workflow" (lane should additionally produce, needs bundle-layer scoring) or "operator" (account-holder action, lane provides strategy/template only).

### 1.1. Profile audit + optimization (WORKFLOW)

The profile is the conversion surface for every other surface. A scroller who taps "profile_click" (12× algorithmic weight) lands on a page; the page either converts to follow or doesn't. Tweet Archivist 2026 measurement: well-optimized profile doubles follow-rate from the same content; XPatla 2026 measurement: optimized profile increases follow conversion by 20-30%. The conversion window is ~3 seconds. The five sub-surfaces, each with measurable conversion impact:

- **Bio.** ≤160 chars. "I help X achieve Y" + credibility marker pattern outperforms generic "founder | writer | builder" stacking by ~2× follow rate (Unfollr 2026 A/B). Should include: one concrete niche claim; one credibility marker (specific number, named project, dated achievement); one clear forward expectation ("weekly thread on what's actually working in X"). Examples that work: "I help bootstrapped SaaS founders reach 10K MRR / weekly thread on what's actually working"; "Building DSPy.rb — open-source Ruby framework for LLM apps / 4k+ ⭐"; "Senior partner @DWF / Real estate finance / 23yrs Polish CRE / Pre-IPO + post-deal."
- **Pinned tweet.** First content surface after bio. Three goals: introduce / provide immediate value / drive a conversion. Should rotate every 2-4 weeks per content velocity. Anti-pattern: a 6-month-old pinned post that hasn't been refreshed.
- **Banner.** 1500×500px, 3:1 aspect ratio. Boosts profile visits up to 30% when well-designed (Tweet Archivist 2026). Should reinforce niche + credibility, not be a generic stock photo.
- **Profile photo.** Recognizable face for personal accounts; clean logo for brand accounts. Founder accounts on X get 5-10× more engagement than brand accounts (Conbersa 2026) — strong argument for personal-account-first strategy.
- **Custom URL / handle.** Memorability; consistency across X / LinkedIn / website.

Lane output: a **profile audit document** that reviews current state, prescribes specific edits, and provides 3 candidate pinned tweets the operator can rotate through. Workflow-layer scoring, not artifact-layer.

### 1.2. Content strategy (WORKFLOW)

The strategy doc that sits behind all artifacts. Components:

- **Topic pillars.** 3-5 themes the account credibly owns. Welsh content-matrix methodology: pillars × formats grid; each cell is a defensible 2×2 position. For SaaS founder: e.g., (product-building × technical-deep-dive), (pricing-experiments × case-study), (hiring × failure-postmortem), (distribution × playbook), (build-in-public × weekly-update). Each pillar should be inhabitable for 6-12 months of content before exhaustion.
- **Voice plan.** The lane already extracts voice substrate to `programs/references/voice.md`; the strategy doc additionally articulates voice posture (declarative-not-hedging, peer-not-mentor, lived-experience-not-summary, contrarian-not-conclusive). This is what the X-5 voice criterion measures against; it should be explicitly authored, not implicit.
- **Cadence + posting times.** 3-6 posts/day (SocialRails 2026; Sprout Social 2026 consensus). B2B: 9 AM–1 PM Mon/Thu (US-Eastern, ICP-dependent). SaaS: 9 AM–12 PM and 3–5 PM Tue/Thu. Threads at 12-1 PM (lunch) or 5-6 PM (commute). Morning hours bad for threads (Statweestics 2026). The lane should produce a per-client cadence calendar.
- **Format mix.** The 5 X-native shapes: single post, thread (3-12 units), quote-tweet-add, reply (substantive), long-form Article (Premium). Per-week mix should be ~5-10 single posts, 1-2 threads, 5-15 substantive replies, 1-3 quote-tweets-with-add, 0-1 Article per fortnight for Premium accounts.

Lane output: a **content-strategy document** per client, ~3-5 pages, that pre-commits the operator to pillars + voice + cadence + format mix.

### 1.3. Single posts (ARTIFACT, current lane focus)

Already scored by the 5-criterion judge. No expansion needed at the artifact layer. The strategy doc above provides the substrate (which pillar, which format, which voice).

### 1.4. Threads, 3-12 units (ARTIFACT, current lane focus)

Already scored. Per the v1 lock (§1.5 of the spec), the lane produces threads of 3-12 units, each unit instantiating one beat (Rate of Revelation). Threads receive 63% more impressions than single tweets (PostEverywhere 2026); generate 3× more engagement when posted in dwell-windows (12-1 PM, 5-6 PM).

### 1.5. Quote-tweets with substantive add (ARTIFACT — NEW)

The single largest scope gap in the v1 spec. Quote-tweets score ≈25× a like (Typefully Jan 2026 reconstruction; combines a share with a reply). One indie operator reports "4 of our top 10 performing tweets in 2026" came from quote-tweets-of-self with new context — a +1.2M-impression post on a sub-5K-follower account (OpenTweet 2026 data).

The quote-tweet artifact has its own shape constraints:
- The parent post sets context the QT must add to (not restate).
- The QT body must close a new gap the parent didn't.
- The QT can be: of someone else's post (add a counter-take / extension / specific-knowledge reframe) or of your own post (continuation arc, "update X weeks later," specific result).

**Recommend:** lane v2 produces quote-tweets as a distinct artifact shape, scored by the same 5 criteria (X-1 forward-vector, X-2 specific knowledge, X-3 falsifiability, X-4 form-matches-function — extended to "QT-of-self continuation" sub-shape, X-5 voice). Structural_gate adds: QT-parent context check (does the QT make sense without the parent? if yes, route to single post; if no, the parent context dependency is intentional and the artifact is correctly shaped).

### 1.6. Reply strategy (ARTIFACT + WORKFLOW — NEW, highest-ROI)

The reply is the single highest-leverage discovery mechanism on X in 2026. The 70/30 reply-to-original ratio is now the documented growth strategy (Teract 2026): 70% of post-volume is replies to larger accounts in the niche, 30% is original posts. Operator data: 500 → 12,000 followers in 6 months on this ratio; another account 4,500 followers in 69 days from replies-to-viral. Replies are 13.5× a like; reply-with-author-response is 150× (operator-tested community reconstructions, not official). Reply-early advantage: first 15-60 minutes of a post's life is when the reply gets surfaced to the parent's audience.

The lane should produce TWO reply artifacts:

- **Reply-target list** (WORKFLOW). A curated list of 10-30 accounts in the client's niche that (a) post frequently (>1 post/day), (b) have follower-count ≥10× the client (asymmetric audience-exposure), (c) are topically aligned (replies are on-niche, not generic), (d) are receptive to replies (the account-holder engages back). Niche-specific:
  - SaaS founder: e.g., @rauchg, @jvns, @swyx, @levelsio, @marc_louvion, @dvassallo, @JustinJackson, @SaaStr, @hnshah, @david_perell
  - AI lab researcher: @karpathy, @sama, @AnthropicAI's @mealchemist, @ID_AA_Carmack, @woj_zaremba, @sleepinyourhat, @goodside, @hardmaru
  - Agency principal: @amandanat, @jasonresnick, @joshbachynski, @rdotinga
  - Service firm partner: niche-specific (Polish law firms might track @lawtechnologyto, @bigblawyer, @LawSites)
  - Finance operator: @sahilbloom, @morganhousel, @TheStalwart, @litcapital
  - E-commerce operator: @joshelizetxe, @samparr, @nikitabier, @shaanvp, @TheStoicEmperor

  The list is per-client and per-vertical, refreshed quarterly. Lane output is the list + per-account context (what they post about, what tone is welcomed, what reply-shape works).

- **Reply drafts** (ARTIFACT). On-demand: given a target post (URL or text), produce 1-3 candidate substantive replies. Each scored on a reply-specific variant of X-1/X-2/X-3 (does it add specific knowledge? does it earn an author-response? does it contradict substantively-not-stylistically?). The 5-criterion judge applies with one extension: X-1 becomes "earns the next tap *plus* the author's response" because the reply lives or dies on whether the parent-author engages.

The reply-bait CTA detector (already in the v1 sample-and-flag list) defends against the lane producing reply-shaped slop. Substantive reply ≠ "Great point @author!"; substantive reply = adds specific knowledge or counter-argument or extension the parent didn't have.

### 1.7. Community participation (WORKFLOW — NEW)

X Communities (topic-based feeds, X's answer to Facebook Groups). Posts inside a Community surface to topically-engaged audiences regardless of follower count — a discovery surface for accounts pre-fanout. Successful Communities require value-first contribution (NealSchaffer 2026: <20% promotional). Community admin position gives direct access to engaged niche audience.

Lane output (per client): a **Communities map** identifying 5-10 Communities the client should join, plus posting cadence into them (typically 1-2 posts/week per active Community), plus whether the client should create their own Community (if no existing Community covers their exact niche).

Examples per vertical:
- SaaS founder → Build in Public, Indie Hackers, SaaS Founders, Bootstrappers
- AI lab researcher → ML Twitter, AI Safety, Generative AI Builders
- Agency principal → Marketing Twitter, Growth Marketing, Agency Owners
- Service firm partner → LegalTech, BigLaw, Polish Legal (vertical Community)
- Finance operator → FinTwit, Macro, Quantitative Finance
- E-commerce operator → DTC, Shopify, eComm

### 1.8. Spaces participation + hosting (WORKFLOW + ARTIFACT — NEW)

X Spaces (live audio rooms). X's own research: 10% increase in Space-conversation correlates with 3% sales-volume rise (X internal data, cited in NealSchaffer 2026, KickoffLabs 2026). Weekly Space hosting is the cited "single most underused growth tool on X." Hosting positions account as thought-leader; participants follow host afterward.

Lane output for client:
- **Spaces strategy brief** (WORKFLOW). Decides: should the client host? if yes, what cadence (weekly recommended; same-time-each-week trains audience), what format (founder Q&A, day-in-the-life, technical deep-dive, panel with 2-3 guests), what guest list (rotating co-hosts from the reply-target list above).
- **Spaces title + description per session** (ARTIFACT). The Space title is itself a hook — same first-7-words / forward-vector discipline as a post hook. Title and description should pass the X-1 / X-2 / X-3 filter. Lane produces these per scheduled Space.
- **Spaces recap thread** (ARTIFACT). After hosting, a thread of 5-7 key takeaways. Distinct artifact shape; scored on same 5 criteria with X-2 (specific knowledge from the conversation) carrying extra weight because the lived-experience source is the Space itself.

### 1.9. X Premium / Verified strategy (OPERATOR + WORKFLOW)

Premium ($8/month) and Premium+ ($40/month) tiers. Premium accounts receive +4× in-network and +2× out-of-network ranking boost (Glitchwire May 2026 reconstruction). Non-Premium median impressions ~100; Premium ~600 — 6× distribution differential. Premium+ unlocks Articles + Radar Search + higher Grok limits + largest reply prioritization.

For gofreddy clients in 2026, **Premium is no longer optional for serious accounts** — the structural distribution multiplier makes it ROI-positive for any account targeting >100 impressions/post. Premium+ is the call for accounts that will use Articles (see §1.10) or need TweetDeck (now Premium+-gated per Engadget 2026).

Lane output: **Premium-tier recommendation document** per client (which tier, why, expected ROI window). This is an operator-action document, not an artifact. The lane should NOT condition the artifact's quality on tier; the same draft has the same quality whether the account is Premium or not. Distribution differs; quality doesn't.

### 1.10. Long-form Articles (ARTIFACT — NEW, Premium+ accounts only)

X Articles (Premium+ feature). Up to 25,000 chars. X's $1M Writing Contest signals strategic investment in long-form (ProofWrite 2026). Articles get SEO/Google discoverability (X is now functioning as a search surface for technical / opinion content per Econsultancy 2026). Premium expanded Articles access from Premium+ to all Premium subscribers as of mid-2026.

Article shape (distinct from thread):
- Long-form prose, not unit-of-consideration thread structure.
- Acts as the X-native equivalent of a Substack post or a blog article.
- Can include images, hyperlinks (without the body-link suppression that hits posts).
- Searchable via X Radar Search and indexed by Google.

Lane output: **Article drafts**, scored as a distinct artifact shape. The 5-criterion judge applies but with shape-adjusted thresholds:
- X-1 (hook) — opening still load-bearing but operates on the article-headline + first-paragraph level, not first-7-words.
- X-2 (specific knowledge) — most important for Articles because the longer surface lets the author go deeper.
- X-3 (falsifiability) — strong claim becomes thesis.
- X-4 (form matches function) — now means "Article-shape matches claim density"; some claims are post-sized, some are thread-sized, some are Article-sized.
- X-5 (voice) — same screenshot test but at Article scope.

Cadence recommendation: 0-2 Articles per fortnight for Premium+ accounts. More Articles ≠ better; one strong Article > five weak.

### 1.11. X Newsletter integration (WORKFLOW — Premium)

X integrates with Substack-like newsletter functionality for Premium creators (Revue replacement). Workflow: convert top-performing Articles into newsletter issues; cross-promote between newsletter and posts. Lane output: cross-platform syndication ruleset (see §1.21).

### 1.12. Bookmark engineering (ARTIFACT — NEW emphasis)

Bookmarks are 10× a like. "Bookmark-worthy" is now a first-class content design axis. Reference frameworks, dated playbooks, screenshot-survivable checklists, data tables, decision trees — all save-for-later shapes.

The current X-2 (specific knowledge) criterion partially captures bookmark-worthiness but doesn't anchor on the save-for-later mechanic specifically. Recommendation: do NOT add a 6th criterion (preserves the 5-criterion ceiling); instead, the *strategy doc* (§1.2) should pre-commit ~30% of the content mix to bookmark-shaped artifacts (reference / playbook / checklist) and the *evolution loop* should track bookmark rate per content shape across generations.

Anti-pattern the lane already filters: "Bookmark this thread" CTAs — flagged as manipulation, ≈−74× negative cascade.

### 1.13. List building (WORKFLOW — NEW, low-effort high-leverage)

X Lists (public + private). Three uses:

- **Curated content sources** (private lists): the client's daily reading; not for the lane to author.
- **Reply-target list as a public list** (relationship-building): each account added gets a notification; some follow back / engage out of curiosity. A public list named "Best [Industry] Voices" is a low-effort relationship-building tactic (TweetArchivist 2026, TweetBe 2026).
- **Competitive intel / monitoring** (private lists): the client's competitors / niche-adjacent accounts.

Lane output: **List building plan** — 2-3 public lists + 2-3 private lists per client, populated with 10-20 accounts each.

### 1.14. Build-in-public cadence + transparency (WORKFLOW + ARTIFACT)

The dominant founder-on-X mode for indie / SaaS / AI / e-commerce in 2026. Pieter Levels (600k followers over 10 years; net worth $40-60M; multi-product portfolio including Nomad List $3M ARR, Photo AI $132K MRR by month 18) is the canonical exemplar. Daniel Vassallo (small-bets portfolio in public). Marc Lou (multi-product micro-SaaS in public). The pattern: post the mundane reality (hiring decisions, tool choices, pricing experiments, customer conversations, failure post-mortems) on a weekly-or-more cadence; failure posts often outperform success posts because they feel more useful (SoftwareSeni 2026).

Lane output: **Build-in-public cadence plan** per client (which metrics they'll share publicly — MRR / users / churn / launches; what frequency — weekly update? per-experiment? milestone-only; what tone — celebratory or honest-about-grind). The cadence plan feeds into the strategy doc (§1.2); the actual weekly artifacts pass through the artifact judge.

Vertical applicability: HIGH for SaaS / AI / indie / e-commerce; MEDIUM for agency (selectively, around marketing experiments); LOW for service firm (regulated industries) and most finance operators (regulatory constraints).

### 1.15. Cross-creator collaboration / engagement reciprocity (WORKFLOW)

The reciprocal-engagement effect: creators who reply to comments get more engagement than those who don't, on every platform measured (Buffer 2026 across 6 platforms). Posts where the author engages in comments outperform posts where they don't.

The lane should produce a **reciprocity calendar** per client: a list of 5-10 peer creators (similar follower count, adjacent niche, complementary not directly-competitive) the client commits to engaging with weekly. This is the "tribe" layer above the reply-target list (§1.6) — the reply-target list is for asymmetric exposure (bigger accounts); the reciprocity layer is for peer exchange.

### 1.16. DM strategy (WORKFLOW + ARTIFACT)

Two DM modes:

- **Outbound DMs.** Cold outreach for B2B. Founder-led outperforms SDR-led by 30-50% (Cleverly 2026 reply-rate benchmarks). The DM should follow a warm-conversation-first sequence: substantive replies to the target's posts for 2-3 weeks, then a DM that references the prior exchange and offers something specific. Cold DMs without warm-up are spam.
- **Inbound DMs.** Founders should respond to inbound DMs within 24 hours during the audience-building phase (responsive accounts get more inbound). Templates needed for: thanks-for-following, response-to-question, response-to-collab-request, response-to-sales-pitch.

Lane output:
- **DM strategy brief** (WORKFLOW) — when to use DMs, what fraction of outreach is DM vs reply vs email, response SLA.
- **DM templates per use case** (ARTIFACT) — 5-7 templates for the common scenarios. Each scored by a DM-specific reading of X-2 (specific knowledge — references something specific to the recipient) + X-3 (falsifiability is less relevant; substituted by "specific value being offered" — does the DM offer something concrete?) + X-5 (voice — matches account voice, not generic outreach-bot voice).

### 1.17. Pinned tweet rotation strategy (WORKFLOW + ARTIFACT)

The pinned tweet is the highest-conversion content on the profile. Rotation cadence: every 2-4 weeks (XPatla 2026). Rotation should follow: best-performer-of-the-fortnight OR specific-positioning-update (new launch, new milestone) OR seasonal-relevance.

Lane output: **Pinned tweet rotation calendar** with 3-5 candidate pinned tweets always in the pipeline.

### 1.18. Reply-guy strategy (DH3-DH5 substantive replies in high-traffic threads) (ARTIFACT — extends §1.6)

Variation on §1.6 reply strategy with a higher rigor anchor. "DH" refers to Paul Graham's "How to Disagree" hierarchy (DH0 name-calling → DH6 refuting central point). DH3-DH5 are the substantive-reply zone: DH3 (contradiction with reasoning), DH4 (counterargument with evidence), DH5 (refutation). DH3-DH5 replies to high-traffic threads earn substantive engagement and signal the author's expertise.

Lane output: when producing reply drafts (§1.6), explicitly target DH3-DH5; DH0-DH2 (name-calling, ad hominem, responding-to-tone) should never ship. This is encoded at the artifact-judge level: X-3 (falsifiability) catches DH0-DH2 (they're stylistic disagreement, not substantive).

### 1.19. Algorithm timing for ICP timezone (WORKFLOW)

Already covered in §1.2 (cadence). The lane should pull the client's ICP timezone (US-East / US-West / EU / APAC) and adjust posting times accordingly. The 9-11 AM Tue/Wed/Thu finding holds in the ICP's local time, not the operator's. A Polish founder targeting US-East should post at 3-5 PM Warsaw time (= 9-11 AM EST).

### 1.20. Cross-platform syndication (LI → X, blog → X threads) (WORKFLOW)

LinkedIn removed direct cross-posting to X mid-2025 (Buffer 2026); third-party tools handle this. Critical rule: **repurpose the idea, not the text** (PostBridge 2026, GetLate 2026, Influencers-Time 2026). Each platform version should feel platform-native. LI rewards personal narrative + slower-tempo authority-positioned voice; X wants punchy, peer-not-broadcast, opinionated brevity. Cross-posting verbatim produces voice register mismatch (catches X-5 voice criterion).

Lane output: **Cross-platform syndication rules document** per client that specifies which post originates where + how it adapts to the other platform. E.g., "LinkedIn long-form essay → X thread (extract 5-7 key beats, restructure as units-of-consideration, rewrite voice to peer-register, drop LinkedIn 'lesson-extracting' conclusive tone)"; "X thread → LinkedIn carousel (extract claim + 5 supporting bullets + 1 close, restructure as visual carousel slides)."

### 1.21. Topic Authority on X (WORKFLOW)

Analogous to LinkedIn Topic Authority. Sustained signal that an account credibly owns a niche; emerges from the joint distribution of pillar consistency + lived-experience claims + peer engagement on those topics + repeated bookmarks-by-niche-readers. The lane builds Topic Authority by sustained execution on §1.2 (pillars) + §1.14 (build-in-public on those pillars) + §1.6 (replies on those pillars).

Topic Authority is the meta-objective; individual artifacts are the means. The strategy doc (§1.2) should explicitly name the 3-5 topics the client is going to compound on. Topic Authority is measurable at the 6-month horizon (search-mentions; profile-clicks from search; inbound DMs that reference the topic).

### 1.22. Grok-tone integration (WORKFLOW — operator awareness)

Phoenix factors tone-of-voice — constructive / curious / positive distribution > combative / negative / aggressive (Glitchwire 2026, Wallaroo 2026). Operator awareness: the artifact judge (X-3 falsifiability) already filters combative-empty hot takes. The strategy doc should pre-commit to a tone band ("contrarian-not-combative" is the sweet spot — substantive disagreement, civil register).

Sample-and-flag telemetry (already in the v1 spec §6 sample-and-flag signals) catches workflow drift toward combative-empty.

### 1.23. Reply-bait CTA detection + avoidance (DETERMINISTIC — already in structural_gate)

Already covered in the v1 spec §3b + §8 open-question 9. Engagement-bait CTAs ("Like if you agree," "RT if X," "Drop a 🔥 if," "Bookmark this," "Follow me for more") are deterministic and live in structural_gate. The lane never produces them.

### 1.24. External-link 94% suppression — routing around (DETERMINISTIC — already in structural_gate)

Already covered. Links in body get auto-rewritten to first-reply form. Standard creator hygiene (Tomorrow's Publisher 2026, PPC.land Q1 2026). The lane handles this at gate level.

### 1.25. Custom thread-pinning strategy (WORKFLOW — extends §1.17)

Pinned threads (not just pinned single posts) are now valid. A pinned thread can compound: each new visitor reads the full thread, not a single moment-in-time post. Lane output: when a thread outperforms a candidate pinned post by ≥3× (impressions + dwell), pin the thread instead.

### 1.26. Series-arc threading (multi-post arcs over weeks) (ARTIFACT BUNDLE — NEW shape)

The missing 7th content shape. A series arc is a multi-post commitment over 4-12 weeks where each post is a unit but the arc compounds — "I'm spending the next 8 weeks figuring out how to grow from $5K to $20K MRR; here's week 1." Each post is a single-post or thread artifact, but the arc itself is meta-content with its own quality criteria:

- Arc *premise* must be compelling at week 0 (single-post-judge applies).
- Arc *cadence* must hit (missed-week disrupts compounding).
- Arc *resolution* must deliver (failure to land is over-promise / under-deliver at series scale).

The v1 spec §1.5 lists "Multi-thread series ('part 1 of 5')" as out-of-scope. Recommendation: **revisit this lock for v2**. A series-arc artifact bundle is one of the highest-leverage shapes in 2026 (Copyblogger 2026, BitsKingdom 2026); cutting it leaves growth value on the table. The recommended path: the *individual posts/threads* within the arc are judged by the existing 5 criteria; the *arc itself* is judged by a bundle-coherence judge (§5 below).

Vertical applicability: HIGH for SaaS (build-in-public-style arcs), AI lab (research-thread-arcs), e-commerce (launch-arcs); MEDIUM for agency (case-study-arcs); LOW for service firm (regulatory) + finance operator (regulatory).

### 1.27. Profile-click optimization (CROSS-CUTTING — covered by §1.1 + §1.5)

Profile click is 12× weighted. The artifact (post or QT) creates the curiosity; the profile (§1.1) converts it to follow. Both must be strong; one without the other leaks value. The lane's bundle output ensures both ship together.

### 1.28. Long-dwell post engineering (+10× weight) (CROSS-CUTTING — covered by §1.4 + §1.10)

Long-dwell (2+ minutes) is +10× weight (operator-tested reconstructions). Long-dwell-eligible artifacts: threads of 5+ units, Articles. The artifact judge X-4 (form-matches-function) catches padded threads that produce dwell-completion drops; bookmark engineering (§1.12) catches the save-for-later proxy.

### 1.29. Analytics + measurement (WORKFLOW)

X Analytics dashboard (Premium-gated for desktop access; post-level metrics free in mobile app per DashSocial 2026). Core metrics: impressions, engagement rate, profile visits, follower growth, replies/reposts, link/media clicks, video retention.

Lane output: **Measurement plan** per client. Pre-commits to: 5-7 KPIs the client will track weekly (e.g., profile clicks, substantive replies, bookmarks per thread, follower growth net of unfollows, DM inbound count); a monthly report cadence; threshold for variant-rotation (e.g., if pillar X's posts hit 50% lower engagement than pillar Y over a fortnight, rotate pillar mix).

This is the feedback loop that closes the lane: artifacts ship → metrics measure → strategy doc updates → next artifacts ship. The lane should produce the measurement plan; the operator runs the measurement.

### 1.30. 2026-specific tactics post-Phoenix-rewrite + Grok integration (CROSS-CUTTING)

Already integrated into the above. The big 2026 deltas:
- Phoenix candidate-isolated scoring (no batch-relative ranking exploits remain)
- Grok-tone analysis (combative-empty penalized)
- External-link suppression at 94% for non-Premium (Q1 2026)
- Premium structural boost (+4× / +2×)
- Reply volume +21% YoY, repost +35% YoY
- Engagement velocity center of gravity is the first 30 minutes (Phoenix shrunk the window)
- Communities + Spaces + Articles surfaces actively prioritized

The 5-criterion judge already handles these at the artifact layer. The §1.1-§1.29 workflow surfaces above are how the lane operationalizes them at the strategy layer.

---

## §2. CUTS — Old-School Plays That Now Backfire

These are explicitly suppressed by the 2026 algorithm + AI-slop pattern recognition. Each is referenced as a "DO NOT PRODUCE" rule the lane carries (most live in `structural_gate`; a few are gestalt judgments the artifact judge catches).

**C1. Engagement-bait CTAs.** "Like if you agree," "RT if X," "Drop a 🔥 if you got value," "Comment YES if," "Follow me for more." Grok-flagged as `engagement_arbitrage`. ≈−74× negative-signal cascade per single negative reaction. Endemic to 2018-2022 growth-hacking guides; suppressed since 2024 Twitter policy update; intensified under Phoenix. (Lane: deterministic literal-string match in structural_gate.)

**C2. Fake-vulnerability bait.** "I lost everything last year. Here's what I learned." "I almost went bankrupt. 3 lessons." Carefully calibrated admission of failure with abstract failure + platitude lessons. AI-slop tell (DigiPalms 2025, Pathless Path / Stoddart critique). Tier-2 structural slop signature. (Lane: artifact judge X-2 catches if no specific entity / dollar / date; structural_gate catches if confessional-opener + exactly-3 numbered bullets + abstract-failure shape.)

**C3. "Stop X. Start Y." imperative-pair rhythm.** Endemic AI-generated founder-advice rhythm. Single instance is Hormozi rhetoric; 2+ in a 5-tweet thread is the slop signature. (Lane: deterministic regex in structural_gate, >1 instance per post fails.)

**C4. Em-dash density above account baseline.** GPT-4-family 3.28× human baseline (Goedecke 2025). Single em-dash is rhetoric; >5 em-dashes per 100 words is the slop signature. (Lane: deterministic density check in structural_gate.)

**C5. "Moreover / furthermore / delve into / in conclusion / let me explain / here's the thing / let's be clear / it's worth noting" + the slop-transition stack.** Tier-1 surface signatures. Single instance high-FPR against real operators; the stack is the signal. (Lane: deterministic literal-string match in structural_gate; >2 phrases triggers.)

**C6. Three-element parallel constructions (tricolons) used reflexively.** Naval and Bloom use tricolons as foundational rhetoric. The slop is reflexive density: tricolons every other paragraph. (Lane: syntactic-uniformity density check, >2 tricolons per thread, in structural_gate.)

**C7. Hot takes without evidence.** "Most founders are wrong about X" with no falsifiable substance underneath. Earns likes (low weight); no substantive replies; triggers mutes. Mack falsifiability test catches. (Lane: artifact judge X-3.)

**C8. Generic motivational quotes.** "Consistency beats intensity." "Done is better than perfect." Centroid-voice platitudes. Fail X-2 (no specific knowledge) + X-3 (unfalsifiable) + X-5 (no voice). (Lane: artifact judge.)

**C9. Hollow tricolons / parallel-listicle inflation.** "Build. Ship. Iterate." stacked across a thread without substance. Goodhart variant of (C6); listicle syntactic uniformity >0.85. (Lane: structural_gate listicle-uniformity check.)

**C10. Throat-clearing openers.** "I've been thinking a lot lately about..." "There's something I want to share..." "It occurs to me that..." Topic-statement openers similarly: "Today I want to talk about consistency." First-7-words wasted on meta. (Lane: artifact judge X-1, Axis B + anti-pattern flag.)

**C11. Link-in-body posts.** 94% reach reduction for non-Premium since Q1 2026 (PPC.land); near-zero median engagement since March 2026 (Joe Youngblood 2026; SocialBee 2026). Workaround: link in first reply. (Lane: structural_gate auto-rewrite.)

**C12. Multiple hashtags.** 3+ hashtags = ~40% reach reduction; 5+ = spam flag. Old-school growth-hack from 2010s no longer works in 2026. (Lane: structural_gate hashtag-count cap.)

**C13. Brand-account posts treated as personal-account posts.** Personal accounts get 5-10× more engagement than brand accounts on X (Conbersa 2026). Brand-account voice ("at Acme, we believe in...") fails X-5 voice check. Recommendation: gofreddy strategy doc defaults to personal-account-first for founder clients; brand account is secondary or absent.

**C14. Quote-tweet-of-own-post-for-amplification (as the only QT pattern).** Grok-flagged as manipulation. (Lane: operator behavior, not artifact-level; the legitimate QT-of-self with new substantive context is allowed and encouraged per §1.5.)

**C15. Posting cadence over 10/day from a single personal account.** Triggers spam-detection signals. (Lane: cadence calendar caps at 6 posts/day for normal accounts; bursts allowed during launch / news events.)

**C16. Long-form essays cross-posted verbatim from blog / LinkedIn.** Voice register mismatch. LinkedIn broadcast voice on X reads as imported and fails X-5. (Lane: cross-platform syndication ruleset, §1.20, requires platform-adaptive rewriting.)

**C17. Numbered-list inflation.** "Here are 7 things..." with items 4-7 being restatements. Promise-inflation; bounce-after-hook gap fires. (Lane: artifact judge X-1 Axis C catches numbered-list inflation; structural_gate listicle-uniformity catches.)

**C18. Quote-tweet without substantive add.** A QT that just retweets-with-attribution. Adds no value; fails X-2 + X-3. (Lane: artifact judge.)

**C19. Cliffhanger that doesn't pay.** "The result will surprise you." Followed by ordinary content. (Lane: artifact judge X-1 Axis C.)

**C20. Bookmark-this CTAs.** "Bookmark this thread." Flagged manipulation. (Lane: structural_gate literal-string match.)

---

## §3. ADDS — Modern Levers Worth Pulling

Each lever is grounded in 2026 algorithm signals OR 2025-2026 named-practitioner evidence. The lane should bake these into the strategy doc / artifact production / bundle composition.

**A1. First-7-words discipline.** Forward-vector hook with first-fixation-survivable tokens (named entity / specific number / concrete noun / schema-violation). Already encoded in X-1. Strategy doc should pre-commit to this discipline; client-facing brief explains why.

**A2. Specific-knowledge claims from lived experience.** Naval / Mack / Bloom / Schneider exemplars. X-2 anchors. The voice substrate (programs/references/voice.md) loads operator-specific lived-experience anchors; this is the load-bearing differentiator vs centroid-founder-voice.

**A3. Falsifiable claims peers can substantively disagree with.** X-3 anchor. Strategy doc: 30-40% of original posts should make a falsifiable claim (the rest can be observation / commentary / reply-thread / build-in-public update). Hot takes without evidence don't qualify; manufactured controversy doesn't qualify.

**A4. Reply-discovery as primary growth mechanism.** §1.6 + §1.18. 70/30 reply-to-original ratio (Teract 2026). Substantive DH3-DH5 replies on the curated 10-30 account reply-target list. This is the highest-ROI lever in 2026 — operationally more impactful than any single post optimization.

**A5. Quote-tweets with new substantive context.** §1.5. 4-of-top-10 highest-performing posts per OpenTweet 2026 case data come from QT-of-self with new context. Distinct artifact shape.

**A6. Bookmark-shaped content (reference / playbook / checklist).** §1.12. 10× a like. Strategy doc commits 20-30% of content mix to bookmark-shaped artifacts. The lane should learn which formats earn the most bookmarks per client (telemetry across generations).

**A7. Build-in-public weekly cadence (where vertical applicable).** §1.14. Pieter Levels / Daniel Vassallo / Marc Lou exemplars. Vertical-conditional (HIGH for SaaS/AI/indie/e-commerce; MEDIUM for agency; LOW for service firm / finance).

**A8. Series-arc threading over 4-12 weeks.** §1.26. The compounding-attention engine. Series premise must be compelling, cadence must hit, resolution must deliver. Bundle-judged separately from per-post judging.

**A9. Spaces hosting on weekly cadence (where vertical applicable).** §1.8. NealSchaffer 2026 / KickoffLabs 2026 / X's own data. Single most-underused growth tool. Co-hosting with larger guests pulls their audience.

**A10. Communities participation (5-10 active Communities per client).** §1.7. Topic-graph fanout regardless of follower count. The pre-fanout discovery surface.

**A11. Premium subscription for any client targeting >100 impressions/post.** §1.9. +4× / +2× structural multiplier. ROI-positive at $8/month.

**A12. Premium+ + Articles for any client where long-form is on-strategy.** §1.10. $1M X Writing Contest signals platform strategic priority. Articles get Google discoverability.

**A13. Public-list relationship-building.** §1.13. "Best [Industry] Voices" list named publicly; each add notifies the account; some follow back. Low-effort high-leverage.

**A14. Pinned tweet / thread rotation every 2-4 weeks.** §1.17 + §1.25. Best-performer-of-fortnight pins.

**A15. DM warm-up sequence before outbound.** §1.16. 2-3 weeks of substantive replies → DM. 30-50% reply-rate uplift founder-led vs SDR-led.

**A16. Cross-platform adaptive rewriting (not verbatim).** §1.20. LinkedIn → X requires voice register conversion: authority-positioned → peer; narrative → punchy; "lesson-extracting" → contrarian-not-conclusive.

**A17. ICP-timezone-aware posting calendar.** §1.19. 9-11 AM Tue/Wed/Thu in client's ICP timezone, not operator's.

**A18. Reciprocity calendar with 5-10 peer-creator accounts.** §1.15. Engagement reciprocity effect documented across all 6 major platforms (Buffer 2026).

**A19. Topic Authority 6-month roadmap.** §1.21. Pillar consistency + lived-experience + peer-engagement + bookmark-by-niche-readers. Measurable at 6 months.

**A20. Constructive-tone band ("contrarian-not-combative").** §1.22. Grok-tone analysis rewards constructive distribution; substantive falsifiability is fine; combative-empty hot takes are suppressed.

**A21. Engagement-velocity-first design.** Phoenix shrunk the post-evaluation window to 30 minutes. Posts that don't earn conversation in the first 30 minutes don't recover. Strategy doc commits operator to post → engage with first 5-10 replies within 30 minutes (founder-led; not delegable).

**A22. Long-form Articles with Google-search discoverability.** §1.10. Long-form is the 2026 inflection point. X is becoming a search-and-discovery surface (Econsultancy 2026, Brand24 2026).

**A23. Founder-account-first over brand-account.** Personal accounts 5-10× engagement (Conbersa 2026). Brand account as secondary aggregator, not primary.

**A24. Measurement-driven pillar rotation.** §1.29. Each pillar's posts get tracked; bottom-performing pillars rotated out at 6-week marks.

---

## §4. Vertical Adjustments

The bundle architecture (§5) stays constant across verticals; what changes is the contents of the bundle's variable components. The judge criteria do not change across verticals (mechanism-universal); the strategy / reply-target list / Communities map / Spaces brief / DM templates / series-arc choices do change.

**V1. SaaS founder (small-to-medium, $0-$10M ARR).**
- Pillars: product-building, pricing-experiments, hiring, distribution, build-in-public weekly metrics.
- Voice: peer-to-peer, lived-experiment, dollar-amounts named, contrarian-not-combative.
- Reply targets: @levelsio, @marc_louvion, @dvassallo, @JustinJackson, @SaaStr, @hnshah, @david_perell, @rauchg, @swyx — vertical-niche-adjusted.
- Communities: Build in Public, Indie Hackers, SaaS Founders, Bootstrappers.
- Spaces: weekly founder Q&A or build-in-public-update format.
- Series-arc: HIGH applicability — "$5K to $20K MRR in 8 weeks" is the canonical shape.
- DM strategy: outbound to enterprise prospects; inbound from candidates / customers / fellow founders.
- Articles: pricing-experiment write-ups, hiring playbooks, distribution post-mortems.

**V2. AI lab researcher (academic / industry / open-source).**
- Pillars: research findings, technique deep-dive, paper review / commentary, lab updates, open-source release announcements.
- Voice: technical-rigor, citation-respecting, peer-not-broadcast, lower-status (researcher-to-researcher).
- Reply targets: @karpathy, @sama, @ID_AA_Carmack, @woj_zaremba, @sleepinyourhat, @goodside, @hardmaru, @AnthropicAI's research-active staff.
- Communities: ML Twitter, AI Safety, Generative AI Builders.
- Spaces: panel format with research-active peers; technical-deep-dive monthly.
- Series-arc: MEDIUM applicability — research-thread-arc per paper / project; not weekly-life-update shape.
- DM strategy: inbound from journalists / VCs / fellow researchers; outbound minimal.
- Articles: paper-explainers, technique tutorials, lab-experiment write-ups.

**V3. Agency principal (small-to-medium agency, US/EU).**
- Pillars: client case studies, marketing experiments, agency-operations behind-the-scenes, industry commentary, hiring-and-team-building.
- Voice: practitioner-credibility, results-anchored, contrarian on agency-industry conventions.
- Reply targets: @amandanat, @jasonresnick, @joshbachynski, @rdotinga, agency-prospect accounts.
- Communities: Marketing Twitter, Growth Marketing, Agency Owners.
- Spaces: monthly client-case-study walk-through.
- Series-arc: MEDIUM applicability — case-study-arc shape; "how we grew X client from Y to Z."
- DM strategy: outbound to agency prospects; warm-conversation-first sequence critical.
- Articles: case-study deep-dives, agency-operations playbooks.

**V4. Service firm partner (legal / accounting / consulting; Polish-language for first-cohort DWF / Klinika).**
- Pillars: industry commentary, deal-or-case write-ups (compliance-aware), professional-development takes, regulatory updates.
- Voice: authority-positioned (regulated industry constrains contrarian-edge), peer-to-peer to fellow practitioners, formal-register.
- Reply targets: vertical-specific. For Polish legal: senior practitioners in CRE finance / restructuring / IP; international legal-tech accounts (@bigblawyer, @LawSites). For Polish dermatology: medical professional bodies, fellow dermatologists, professional journals.
- Communities: LegalTech, BigLaw, Polish Legal (vertical-language Community).
- Spaces: monthly industry-update format; co-host with peer practitioners.
- Series-arc: LOW applicability — regulatory constraints + client confidentiality kill weekly-update arcs.
- DM strategy: inbound only; outbound is non-standard in regulated professions.
- Articles: thought-leadership on regulatory developments, deal-structure explainers (post-deal, with attribution).
- Voice register risk: HIGH for Polish-language voice-substrate calibration; the structural_gate English-only lexical anti-patterns need Polish-language separate pass (per v1 spec §8 open-question 7).

**V5. Finance operator (PE / VC / hedge fund / capital-markets analyst).**
- Pillars: macro commentary, sector takes, deal/IPO commentary, investment-process behind-the-scenes (compliance-aware), book/research reviews.
- Voice: analytically-rigorous, citation-respecting, contrarian-on-consensus.
- Reply targets: @sahilbloom, @morganhousel, @TheStalwart, @litcapital, @business, @neuxfox, vertical-specific.
- Communities: FinTwit, Macro, Quantitative Finance.
- Spaces: weekly market-recap or sector-deep-dive format.
- Series-arc: MEDIUM applicability — thesis-arc shape ("my X conviction over the next quarter; here's how it's playing out").
- DM strategy: inbound from journalists / fellow analysts; outbound minimal (regulatory).
- Articles: thesis pieces, deal-post-mortems, sector deep-dives.

**V6. E-commerce operator (DTC / Shopify / Amazon / direct-response).**
- Pillars: product-launches, marketing-channel experiments, supply-chain / ops behind-the-scenes, customer-acquisition cost / retention metrics, build-in-public monthly revenue.
- Voice: results-anchored, dollar-amounts named, peer-to-peer to fellow operators.
- Reply targets: @joshelizetxe, @samparr, @nikitabier, @shaanvp, @TheStoicEmperor, @Shaan_lol.
- Communities: DTC, Shopify, eComm, Amazon FBA.
- Spaces: monthly channel-experiment walkthrough.
- Series-arc: HIGH applicability — launch-arc shape ("launching X over the next 6 weeks; week 1 numbers").
- DM strategy: outbound to potential partners / suppliers; inbound from customers / fellow operators.
- Articles: channel-experiment write-ups, launch post-mortems, retention-deep-dives.

**V7. Indie hacker / solo operator (cross-vertical, often AI-adjacent in 2026).**
- Pillars: product-building (often multi-product portfolio), MRR / users / revenue updates, technique experiments (AI-adjacent), failure post-mortems, "small bets" philosophy.
- Voice: lived-experiment, dollar-amounts named, contrarian-not-combative, lower-status-peer.
- Reply targets: @levelsio, @dvassallo, @marc_louvion, @JustinJackson, @rauchg, @swyx.
- Communities: Build in Public, Indie Hackers, AI Builders, Bootstrappers.
- Spaces: monthly "what I shipped this month" format.
- Series-arc: VERY HIGH applicability — this is the canonical build-in-public shape.
- DM strategy: outbound minimal; inbound from fellow builders / customers / VCs.
- Articles: build-in-public weekly deep-dives, product launch post-mortems.

---

## §5. Deliverable Architecture — the 12-Component Bundle + Per-Cycle Increments

The lane's v2 deliverable is NOT a single artifact. It is a **bundle of 12 components** the first time a client is engaged, plus per-cycle artifact increments thereafter.

### 5.1. First-engagement bundle (12 components)

Each component has its own quality criteria; many pass through the existing 5-criterion artifact judge; others pass through a new bundle-coherence judge.

| # | Component | Type | Judge route |
|---|-----------|------|------------|
| B1 | Profile audit document | WORKFLOW doc | Bundle-coherence judge |
| B2 | Content strategy document (pillars + voice + cadence + format mix) | WORKFLOW doc | Bundle-coherence judge |
| B3 | 5-10 sample single posts | ARTIFACT × 5-10 | 5-criterion judge per artifact |
| B4 | 2-3 sample threads | ARTIFACT × 2-3 | 5-criterion judge per artifact |
| B5 | Reply-target list (10-30 accounts + per-account context) | WORKFLOW doc | Bundle-coherence judge |
| B6 | DM templates (5-7 use-case templates) | ARTIFACT × 5-7 | DM-adapted 5-criterion judge per template |
| B7 | Spaces strategy brief + first month's 4 Space topics | WORKFLOW doc | Bundle-coherence judge |
| B8 | Communities map (5-10 Communities to join + per-Community posting plan) | WORKFLOW doc | Bundle-coherence judge |
| B9 | Series-arc storyboard (first month's arc) | WORKFLOW + ARTIFACT bundle | Bundle-coherence judge + per-post 5-criterion |
| B10 | Measurement plan (5-7 KPIs + report cadence + rotation thresholds) | WORKFLOW doc | Bundle-coherence judge |
| B11 | 30/60/90 execution roadmap | WORKFLOW doc | Bundle-coherence judge |
| B12 | Cross-platform syndication ruleset (LI ↔ X ↔ blog) | WORKFLOW doc | Bundle-coherence judge |

### 5.2. Per-cycle increments (after first-engagement bundle ships)

| # | Component | Cadence | Type | Judge route |
|---|-----------|---------|------|------------|
| I1 | Single post drafts | 5-10/week | ARTIFACT | 5-criterion judge |
| I2 | Thread drafts | 1-2/week | ARTIFACT | 5-criterion judge |
| I3 | Reply suggestions (on target accounts' recent posts) | 10-20/week | ARTIFACT | 5-criterion + reply-adapted |
| I4 | Quote-tweet drafts | 1-3/week | ARTIFACT | 5-criterion + QT-adapted |
| I5 | Spaces recap thread (after each hosted Space) | weekly if hosting | ARTIFACT | 5-criterion judge |
| I6 | Article draft (Premium+ accounts only) | 0-2/fortnight | ARTIFACT | 5-criterion + Article-adapted |
| I7 | DM template instances (use-case specific) | on-demand | ARTIFACT | DM-adapted judge |
| I8 | Pinned tweet rotation candidates | every 2-4 weeks | ARTIFACT × 3-5 | 5-criterion judge |
| I9 | Series-arc per-post update (within active arc) | weekly | ARTIFACT | 5-criterion + arc-coherence |
| I10 | Measurement report (telemetry rollup) | monthly | WORKFLOW doc | Bundle-coherence judge |

### 5.3. Bundle-coherence judge — a NEW workflow-layer judge (5 criteria, named outcome questions)

To avoid Phase-4 pathology, the bundle-coherence judge is also outcome-question-shaped, not feature-shaped. The bundle is judged on five outcome questions:

- **BC-1.** *Does the bundle's voice carry coherently across all components?* Would a reader of the strategy doc, then the sample posts, then the DM templates, find them attributable to the same person? Or do they read like three different ghostwriters?
- **BC-2.** *Do the strategy doc's pillars actually appear in the sample posts + sample threads + series-arc + reply-target choices?* Or is the strategy doc decoupled from the artifacts?
- **BC-3.** *Is the reply-target list and Communities map vertical-appropriate?* Would a peer in the client's vertical recognize these as the accounts and Communities they themselves would target — not generic founder-Twitter accounts?
- **BC-4.** *Does the measurement plan have a closed feedback loop to strategy updates?* Or is it a list of metrics that never feeds back into pillar / format / cadence rotation?
- **BC-5.** *Does the bundle work as a starting point for a client running the workflow themselves — or does it require gofreddy operating it indefinitely?* The bundle should be hand-off-able. (This is the differentiation lever — generic AI-output bundles are not.)

These BC-1 through BC-5 are not yet locked criterion prose; they are outcome questions to be authored as a separate spec (parallel structure to the artifact-layer spec at `2026-05-18-judge-design-step1-x-engine.md`).

### 5.4. Size envelope

- Bundle B1-B12 first ship: target 25-40 pages of substrate + 15-30 sample artifacts. Total lane-substrate ~30-40K words on first engagement.
- Per-cycle increments: target 5-15 artifacts/week + 1 monthly report.

This is comparable to a 1-2-week senior agency engagement output. The size justifies serious lane investment.

### 5.5. Multi-part structure for evolution loop

The evolution loop operates at two layers:
- **Artifact-layer evolution** (existing): 5-criterion judge scores per-artifact across N variants; promoted variants update lane prompts / templates / voice substrate.
- **Bundle-layer evolution** (NEW): BC-1 through BC-5 score per-bundle; promoted bundles update meta-strategy templates, vertical-adjusted reply-target lists, Communities maps, measurement-plan formats.

Bundle-layer evolution operates on a slower cadence (per-client engagement, not per-iteration) because bundles are heavier to produce. Artifact-layer evolution stays per-iteration.

---

## §6. Evolution-Loop Considerations

The current evolution loop scores one artifact per iteration. The v2 deliverable architecture introduces 12 components on first engagement + 10 per-cycle increments. The evolution loop needs to scale.

**E1. Don't try to evolve all 12 components in one iteration.** Stagger: iterate per-component over multiple generations. E.g., generation N optimizes B3 (sample single posts) + I1 (single-post drafts); generation N+1 optimizes B4 + I2 (threads); generation N+2 optimizes B6 + I7 (DM templates); etc.

**E2. The bundle-coherence judge runs on every Nth generation, not every generation.** BC-1 (voice coherence across components) only fires when the workflow has shipped enough components for incoherence to be measurable. Run bundle-coherence every 5-10 artifact-layer generations.

**E3. Goodhart-resistance is shared.** The existing artifact judge's Goodhart-resistance verification (§6 of v1 spec) applies. The new bundle-coherence judge needs its own Goodhart-resistance verification — the most likely Goodhart on BC-1 is "match a single voice template across all components and call it coherent," which actually IS what BC-1 asks for, so the failure mode is voice-template overfit rather than feature-stuffing.

**E4. Cross-cohort holdout for bundles.** The v1 spec's cross-cohort criterion (workflow-level `cross_item_criteria`) applies at bundle scale: no two clients' bundles should be carbon copies of each other (which would defeat the personalization promise of gofreddy). Diversity test: across N=10 client bundles, the strategy docs should not be templated with only client name substituted; the reply-target lists should differ vertical-appropriately; the Communities maps should differ.

**E5. Fragile-fixture testing extends to bundles.** The v1 spec's fragile-fixture aware sampling applies. Bundle fixtures should include adversarial cases: cold-start client with <30 prior posts; multi-language client (Polish-language for DWF / Klinika); regulated-industry client (legal / dermatology); cross-platform-conflicted client (strong LinkedIn presence + nascent X presence requiring divergent voice).

**E6. Bundle evolution cadence.** First-engagement bundle production is high-cost ($X per client). Bundle-layer evolution operates on a per-client basis, not per-iteration. Recommendation: archive every produced bundle's per-component scores; bundle-layer redesign triggered when ≥3 clients flag the same coherence failure across cohorts.

**E7. The 5-criterion artifact judge is reused unchanged.** This is load-bearing. The judge spec is locked at v1; the v2 lane scope expansion does NOT require new criteria. The criteria are mechanism-universal (forward-vector, specific-knowledge, falsifiability, form-matches-function, voice / screenshot-test); they apply to single posts, threads, QTs, replies, DM templates, Article drafts, Spaces recaps, series-arc per-post updates. What changes per artifact shape is the structural_gate (different shape-conformance checks per artifact type), not the judge.

**E8. Telemetry expansion.** The v1 spec's 3 sample-and-flag signals (Grok-tone proxy, reply-bait CTA detector, AI-slop signature density) apply to every artifact shape. Bundle-layer adds: bundle-coherence variance per client over time, vertical-mix coverage (are all 6+ verticals represented in the calibration set), Premium-tier confound tracking.

---

## §7. SOTA Exemplars

Named practitioners whose 2024-2026 X content is the empirical anchor for "what good looks like." Each is referenced as a quality anchor, NOT a template to copy.

**SOTA-1. Naval Ravikant.** *How to Get Rich (without getting lucky)* canonical thread-as-essay (230k+ likes). Specific-knowledge claims compressed to 6-word declarative reframings ("Seek wealth, not money or status"). Voice signature recognizable across 200+ posts. Posture: declarative, peer-not-mentor, lower-status. Reference for X-2 + X-5.

**SOTA-2. Sahil Bloom.** Paradox / razor / framework one-liner pattern. 400k+ followers in 36 months; 700k+ by 2026 via Creator Science podcast cite. Framework Handbook substack. Uses tricolons + em-dashes substantively as foundational rhetoric. Headlines and hooks are the primary copywriting surface (Tim Denning analysis 2026). Reference for X-1 (hook discipline) + X-3 (paradox-as-falsifiable-claim).

**SOTA-3. George Mack.** *High Agency* counter-stereotype framing ("the boxer who writes poetry"). Schema-violation as primary hook shape. Antithesis + counter-stereotype as foundational moves. Reference for X-1 (Axis B schema-violation) + X-3 (counter-consensus claims).

**SOTA-4. Visakan Veerasamy (@visakanv).** Prolific threader. Unit-of-consideration thread theory: typical 3-7 units, up to ~12 max; each unit a distinct move (define, exemplify, counter, anchor, generalize, test, close). Reference for X-4 (thread form-matches-function; Rate-of-Revelation per unit).

**SOTA-5. Justin Welsh.** Content Matrix framework (pillars × formats grid). 1M+ followers across X / LinkedIn. Solopreneur framework documented in 2026 (Jano le Roux Medium analysis). Reference for §1.2 strategy doc + content-pillar discipline.

**SOTA-6. Dickie Bush + Nicolas Cole.** *Ship 30 for 30* curriculum. 1 Chip Rule + 1-3-1 Rhythm + Rate of Revelation. The most concretely documented hook framework in the creator economy. Reference for the judge's private reasoning toolkit (hook discipline, not in rubric prose).

**SOTA-7. Alex Hormozi.** Curiosity gap mechanism in *$100M Offers* + *$100M Leads*. Hook-promise-deliver structure. Single-instance "Stop X. Start Y." rhetoric (the slop is reflexive density, not the construction). Reference for hook discipline + clickbait-avoidance.

**SOTA-8. Cody Schneider.** Documented 5,000 follows in 30-60 days via reply-strategy experiments on his own account. Specific-knowledge claim per X-2: "expect ~20% follow-back from substantive replies on bigger-account threads." Reference for §1.6 reply-discovery strategy.

**SOTA-9. Pieter Levels (@levelsio).** 600k followers over 10 years. $40-60M net worth. Multi-product portfolio: Nomad List ($3M ARR), Remote OK, Photo AI ($132K MRR by month 18), Interior AI. Canonical build-in-public exemplar. Reference for §1.14 build-in-public cadence.

**SOTA-10. Daniel Vassallo (@dvassallo).** Small Bets portfolio in public. Build-in-public on Twitter is his canonical distribution strategy. Reference for §1.14 + indie hacker / solo operator vertical.

**SOTA-11. Marc Lou.** TrustMRR + multi-product micro-SaaS in public. Newer-cohort (2024-2026) build-in-public exemplar. Reference for SaaS / indie cohort.

**SOTA-12. Paul Graham (@paulg).** Essay-shape on X (long-form Articles, where X is now competing with Substack). Sentence-length distribution: 15-25-word essayistic with periodic 5-word punctuation. Reference for X-5 voice (specific-founder-idiolect signature) + §1.10 Articles.

**SOTA-13. Hamel Husain.** Domain-expert credibility on technical content. Specific-knowledge claims from lived ML/AI engineering. Reference for X-2 (specific-knowledge anchor) and AI lab researcher vertical.

**SOTA-14. Andrej Karpathy (@karpathy).** Technical-deep-dive thread shape; research-explainer Articles. Reference for AI lab researcher vertical.

**SOTA-15. xai-org/x-algorithm repository (Jan + May 2026).** Primary source for Phoenix transformer architecture, ten-action probability set, scoring formula, `engagement_arbitrage` detector. Reference for every algorithm-axis claim in this doc; the operator-data triangulations cited elsewhere reconstruct numerical weights from this source.

---

## §8. Open Questions

The questions left unresolved for the lane operator + plan author to triage before v2 ships.

**Q1. Bundle-coherence judge prose — author next.** The 5 outcome questions BC-1 through BC-5 in §5.3 are sketched but not authored as criterion prose. Recommendation: parallel-author a `2026-05-19-judge-design-step1-x-engine-bundle-layer.md` spec following the same shape as the artifact-layer spec.

**Q2. Series-arc shape unlocking.** The v1 spec §1.5 explicitly excludes "Multi-thread series ('part 1 of 5')." Recommendation in §1.26: REVISIT this lock for v2. Decision needed before v2 ships: does the series-arc artifact bundle ship in v2, or is it deferred to v3? If shipped in v2, the bundle-coherence judge gets arc-specific BC criteria.

**Q3. Premium tier confound in measurement.** The +4× / +2× Premium structural boost means the lane can't easily separate "this artifact is high-quality" from "this account has Premium distribution." Telemetry should track Premium-status per fixture so the substrate doesn't misread distribution as quality.

**Q4. Polish-language voice substrate.** The v1 spec §8 open-question 7 flags this for the structural_gate. The v2 bundle architecture adds Polish-language strategy doc + reply-target list + Communities map + DM templates. Each needs Polish-language calibration before DWF + Klinika launch. Vertical adjustment is harder when language register also shifts.

**Q5. Vertical breadth vs depth.** Section §4 lists 7 verticals (SaaS founder / AI lab researcher / agency principal / service firm partner / finance operator / e-commerce operator / indie hacker). Recommendation for v2: ship calibration for 3 verticals (probably SaaS founder + AI lab researcher + agency principal) deeply; the other 4 follow in v3. The bundle-coherence judge BC-3 (vertical-appropriateness) only meaningfully tests against verticals the lane has calibrated for.

**Q6. Reply-target list freshness.** Reply-target lists go stale as the X graph evolves (accounts move, new accounts emerge, niche topology shifts). Recommendation: quarterly refresh per vertical; bundle-coherence judge BC-3 flags stale targets.

**Q7. Spaces transcription + recap-thread loop.** If Spaces hosting is in scope (HIGH ROI per §1.8), the recap-thread artifact (I5) requires audio-to-text transcription substrate. Is that in scope for the lane, or does the operator provide the transcript? Recommendation: lane v2 expects operator-provided Space transcript; lane v3 adds native transcription.

**Q8. Article shape vs thread shape.** §1.10 introduces Articles as a distinct artifact shape. The 5-criterion judge applies with shape-adjusted thresholds. Should Article shape be a separate sub-lane (own structural_gate, own thresholds) or a shape-tag on the existing lane? Recommendation: shape-tag, not sub-lane. Articles are X-native; same criteria; different `structural_gate` settings (character count, paragraph structure, headline anatomy).

**Q9. Build-in-public confidentiality boundary.** Some clients can't share MRR / users / churn publicly (B2B enterprise SaaS with NDA constraints; regulated finance; legal / medical). The strategy doc should explicitly negotiate the confidentiality boundary per client. Bundle-coherence judge BC-3 (vertical-appropriateness) should flag if the strategy doc proposes build-in-public-shape for a vertical where it's regulatorily blocked.

**Q10. Quote-tweet-of-self vs quote-tweet-of-other.** §1.5 covers both. The QT-of-self is amplification-shape (continuation, "X weeks later," update); the QT-of-other is conversation-shape (counter-take, extension, specific-knowledge reframe). These are different artifact shapes with different X-1 / X-2 / X-3 anchors. Recommendation: structural_gate distinguishes; same 5-criterion judge applies; sub-anchors in CoT.

**Q11. Reply substance threshold.** §1.6 + §1.18 commit to DH3-DH5 substantive replies; DH0-DH2 (name-calling, ad hominem) never ship. But the boundary between DH2 (responding-to-tone) and DH3 (contradiction-with-reasoning) is judgment-laden. Recommendation: artifact judge X-3 already catches DH0-DH2 (they're stylistic disagreement, not substantive); explicit DH3-DH5 anchor lives in private reasoning toolkit, not in criterion prose.

**Q12. Engagement-velocity-first design vs founder-time constraint.** §A21 recommends the founder engages with first 5-10 replies within 30 minutes of posting. This is a founder-action requirement, not a lane-produceable artifact. The lane can produce *suggested response drafts* for the first replies, but the founder still has to be online. Recommendation: bundle's 30/60/90 roadmap explicitly negotiates founder time-commitment.

**Q13. Cross-platform syndication conflict with X-native authoring.** §1.20 prescribes LinkedIn → X adaptation. But if the lane ALSO operates a `linkedin_engine`, the syndication rules become bidirectional and the two lanes need coordination. Recommendation: cross-platform syndication ruleset is a shared substrate between `x_engine` and `linkedin_engine`, not duplicated.

**Q14. Bundle versioning + client-facing handoff.** Each bundle ships with a version number; subsequent updates produce v1.1, v1.2, etc. Handoff should explicitly version + diff so the client knows what changed. Operational concern, not lane-design concern; flag for ops.

**Q15. AI-slop signature drift.** §1.22 + §3b list 2025-2026 AI-slop signatures. These will drift as LLMs train on the named tells. Recommendation: refresh AI-slop signature list quarterly; bundle-coherence judge gets a "post-2026 slop signature" sub-check on artifacts produced after the signature-list freshness threshold.

---

## Citations

Primary sources cited in this doc (in addition to the companion 4 deep-research files which carry the algorithm + hook + voice + slop axis citations):

**Algorithm + platform (2026):**
- [xai-org/x-algorithm GitHub repo (Jan + May 2026)](https://github.com/xai-org/x-algorithm)
- [The X Algorithm in 2026 — OpenTweet](https://opentweet.io/blog/how-twitter-x-algorithm-works-2026)
- [10 X Algorithm Secrets — OpenTweet 2026](https://opentweet.io/blog/x-algorithm-secrets-2026)
- [Everything you need to know about X Algorithm — Typefully Jan 2026](https://typefully.com/blog/x-algorithm-open-source)
- [X Algorithm Open Source — Glitchwire May 2026](https://glitchwire.com/news/x-open-sources-its-algorithm-again-10-things-you-need-to-know-about-how-your-fee/)
- [How X's algorithm silently kills your links — PPC.land Q1 2026](https://ppc.land/how-xs-algorithm-silently-kills-your-links-without-explicitly-penalizing-them/)
- [X softens stance on external links — Tomorrow's Publisher](https://tomorrowspublisher.today/content-creation/x-softens-stance-on-external-links/)
- [Twitter/X Statistics 2026 — Digital Applied](https://www.digitalapplied.com/blog/twitter-x-statistics-2026-marketing-data-points)
- [SocialBee: X Algorithm 2026](https://socialbee.com/blog/twitter-algorithm/)
- [Sprout Social: Twitter Algorithm 2026](https://sproutsocial.com/insights/twitter-algorithm/)

**Premium / Articles:**
- [Is X Premium Worth It? 2026 Creator Guide — Ordinal](https://www.tryordinal.com/blog/is-x-premium-worth-it-a-complete-guide-for-creators-and-brands)
- [X Premium+ — Grokipedia](https://grokipedia.com/page/X_Premium)
- [X's $1M Writing Contest — ProofWrite](https://proofwrite.io/blog/x-s-1m-writing-contest-signals-rise-of-long-form-content-means-content-creators)
- [TweetDeck Premium+ gating — Engadget 2026](https://www.engadget.com/social-media/x-moves-the-ashes-of-tweetdeck-behind-its-40-premium-subscription-210601250.html)

**Reply strategy / 70/30:**
- [How to Grow on Twitter/X in 2026: The 70/30 Reply Strategy — Teract](https://www.teract.ai/resources/grow-twitter-following-2026)
- [Logan Holdsworth — Growth via Reply Strategy 2026](https://medium.com/@loganholdsworth/a-full-guide-to-early-x-account-growth-8f3aebabe419)
- [X Reply Guy Strategy — Startup Spells](https://startupspells.com/p/x-reply-guy-strategy)
- [Reply Guy strategy — Grokipedia](https://grokipedia.com/page/Reply_Guy_strategy)

**Spaces:**
- [How to Host Successful Twitter Spaces in 2026 — Tweet Archivist](https://www.tweetarchivist.com/twitter-spaces-hosting-guide-2025)
- [Complete Guide to Twitter Spaces — Neal Schaffer](https://nealschaffer.com/twitter-spaces/)
- [Outfy: How to Use X Spaces for Marketing in 2026](https://www.outfy.com/blog/how-to-use-twitter-spaces/)

**Communities:**
- [How to Use X / Twitter Communities to Grow Your Brand in 2026 — Neal Schaffer](https://nealschaffer.com/twitter-communities/)

**Profile optimization:**
- [Twitter Profile Optimization Guide 2026 — XPatla](https://xpatla.com/blog/twitter-profile-optimization-guide)
- [Twitter Bio Optimization 2026 — Tweet Archivist](https://www.tweetarchivist.com/twitter-bio-optimization-guide-2025)
- [Twitter Banner Design 2026 — Tweet Archivist](https://www.tweetarchivist.com/twitter-banner-design-guide-2025)
- [Optimize Your X Profile to Gain Followers — Unfollr](https://www.unfollr.com/blog/optimize-twitter-profile)

**Posting times / cadence:**
- [Best Times to Post on Twitter (X) in 2026 — Sprout Social](https://sproutsocial.com/insights/best-times-to-post-on-twitter/)
- [Best Time to Post on X in 2026: Data-Backed by Day and Industry — Statweestics](https://statweestics.com/blog/best-time-to-post-on-x-twitter-in-2026-data-backed-guide-by-day-and-industry/)
- [Your Twitter Posting Schedule: 2026 Data-Driven Guide — SuperX](https://superx.so/blog/twitter-posting-schedule)
- [Best Time to Post on Twitter — OpenTweet 50k+ Tweets Study](https://opentweet.io/blog/best-time-to-post-on-twitter-data-study)

**Build in public:**
- [Building in Public: The 10-Year Distribution Strategy — SoftwareSeni](https://www.softwareseni.com/building-in-public-the-10-year-distribution-strategy-behind-solo-founder-revenue/)
- [Twitter Strategy for Indie Hackers 2026 — Teract](https://www.teract.ai/resources/twitter-strategy-indie-hackers-2026)
- [Twitter for Startup Founders: Building in Public Guide — Conbersa](https://www.conbersa.ai/learn/twitter-for-startup-founders)
- [Build in Public for Non-Technical Founders 2026 — Monolit](https://monolit.sh/blog/build-in-public-non-technical-founders-how-to-start-2026)
- [How Pieter Levels grew Nomad List to $3M ARR — Software Growth](https://www.softwaregrowth.io/blog/how-pieter-levels-grew-nomad-list)
- [Pieter Levels Net Worth 2026 — UN Networth](https://unnetworth.com/pieter-levels-net-worth/)
- [Daniel Vassallo Small Bets — Bootstrapped Founder](https://thebootstrappedfounder.com/a-conversation-with-daniel-vassallo/)

**Cross-platform / repurposing:**
- [How to Crosspost on Social Media: 2026 Guide — Buffer](https://buffer.com/resources/how-to-crosspost/)
- [Cross-Platform Content Repurposing — PostPreview](https://postpreview.github.io/cross-platform-content-repurposing)
- [GetLate: Smart Social Media Cross Posting](https://getlate.dev/blog/social-media-cross-posting)

**Analytics:**
- [How To Check and Utilize Your Twitter (X) Analytics in 2026 — Dash Social](https://www.dashsocial.com/blog/x-analytics)
- [X/Twitter analytics guide 2026 — Sociality](https://sociality.io/blog/twitter-analytics/)
- [Twitter Analytics Guide for Creators — BrandGhost](https://blog.brandghost.ai/posts/twitter-x-analytics-guide-creators/)
- [Twitter analytics 2026: ultimate guide — Hootsuite](https://blog.hootsuite.com/twitter-analytics-guide/)

**Lists:**
- [Twitter Lists Complete Guide 2026 — Tweet Archivist](https://www.tweetarchivist.com/twitter-lists-complete-guide)
- [X (Twitter) Lists Guide 2026 — Tweetbe](https://tweetbe.at/blog/x-twitter-lists-guide-2026/)
- [What Are X Lists 2026 — Inspire To Thrive](https://inspiretothrive.com/twitter-lists-explained/)

**DM strategy:**
- [Cold Email Strategy for B2B SaaS 2026 — Cleverly](https://www.cleverly.co/blog/cold-email-strategy-for-b2b-saas)
- [9 SaaS Outreach Tactics — Azarian Growth Agency](https://azariangrowthagency.com/saas-outreach/)

**Engagement reciprocity / creator economy:**
- [State of Social Media Engagement 2026: 52M+ Posts Analyzed — Buffer](https://buffer.com/resources/state-of-social-media-engagement-2026/)
- [2026 Creator Economy Report — Influencer Marketing Factory](https://theinfluencermarketingfactory.com/wp-content/uploads/2026/02/Creator-Economy-Report-2026.pdf)

**SOTA exemplars:**
- [Naval Ravikant — How to Get Rich](https://nav.al/rich)
- [George Mack — High Agency](https://www.highagency.com/)
- [Sahil Bloom — The Framework Handbook](https://sahilbloom.substack.com/p/the-framework-handbook)
- [Sahil Bloom 400k+ Growth in Reverse profile](https://growthinreverse.com/sahil-bloom/)
- [Sahil Bloom Writing Style — Tim Denning](https://timdenning.com/sahil-bloom/)
- [Visakan Veerasamy — The Art of Threading](https://threader.app/the-art-of-threading/a-conversation-with-visakan-veerasamy)
- [Justin Welsh — My Content Matrix](https://www.justinwelsh.me/article/content-matrix)
- [Justin Welsh — LinkedIn Guide 2026](https://www.justinwelsh.me/article/linkedin-guide-2026)
- [How to Become a Solopreneur 2026 — Jano le Roux on Justin Welsh framework](https://janoleroux.medium.com/how-to-become-a-solopreneur-in-2026-the-framework-justin-welsh-proved-and-the-ai-layer-he-didnt-28025e5e97d1)
- [Ship 30 for 30 — Dickie Bush + Nicolas Cole](https://www.ship30for30.com/)
- [Pieter Levels — Cheeky Pint transcript on building in public](https://cheekypint.transistor.fm/4/transcript/)

**Companion deep-research files (same lane):**
- `docs/research/2026-05-18-judges-domain-x-engine.md` — domain research on playbooks (Welsh / Cole-Bush / Naval / Bloom / Mack / Veerasamy / Hormozi)
- `docs/research/2026-05-18-x-engine-algorithm-jan-2026.md` — algorithm-signals axis (PROMOTED / DEMOTED, observable post-features, 2025-2026 deltas)
- `docs/research/2026-05-18-x-engine-hook-discipline.md` — hook discipline (forward-vector, first-fixation, hook-body alignment)
- `docs/research/2026-05-18-x-engine-voice-screenshot-test.md` — voice / screenshot-test axis (Wang et al. EMNLP 2025, X-vs-LinkedIn differential, regime-aware criteria)
- `docs/research/2026-05-18-x-engine-ai-slop-detection.md` — AI-slop detection axis (Dawkins et al. 2025, structural_gate vs gestalt judge split, 6 deterministic checks)

**Project context:**
- `docs/handoffs/2026-05-18-judge-design-step1-x-engine.md` — current artifact-layer 5-criterion spec; locked at v1
- `docs/rubrics/judge-design-guide.md` — judge design philosophy + Goodhart-resistance discipline + Phase-4 incident catalog
