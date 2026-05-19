---
date: 2026-05-19
type: scope-expansion research deliverable
status: complete (Step 0 — comprehensive surface mapping; expands BEYOND v1)
lane: linkedin_engine
parent_spec: docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md
companions:
  - docs/research/2026-05-18-linkedin-engine-van-der-blom-depth.md
  - docs/research/2026-05-18-linkedin-engine-ai-slop-li-specific.md
  - docs/research/2026-05-18-linkedin-engine-author-context-coherence.md
  - docs/research/2026-05-18-linkedin-engine-comment-seed-quality.md
  - docs/rubrics/judge-design-guide.md
intent: map the FULL surface of valuable LinkedIn activities for a 2026 AI-native agency; v1 spec scopes a single text post — this document scopes the BEYOND
audience_primary: tech-savvy founders / operators across small-to-medium SaaS, AI, agency, service, finance, e-commerce verticals (US-primary, Poland first-cohort)
hard_constraints:
  - DO NOT scope-reduce
  - DO NOT propose criterion prose (separate downstream task)
  - DO NOT restate v1 spec
  - Modern-lever bias (founder-led, audience-building, Topic Authority, modern algorithm)
---

# LinkedIn Engine — Comprehensive Scope (2026 AI-Native Agency Surface)

## TL;DR

The current `linkedin_engine` v1 spec scopes ONE artifact: a 600–2,000-character text post, single-post or short-thread. That is correct for v1 judge design (the lock prevents shape-drift Goodhart), and that is also the right MVP for evolution-loop iteration. But it is a tiny fraction of what a 2026 AI-native agency should *actually do* for a small-to-medium client's LinkedIn presence. A LinkedIn text-post draft is the smallest atomic unit of value — comparable to a single tweet in the X surface area. A real LinkedIn program in 2026 spans roughly 25 distinct activities across five layers: **profile foundation** (audit + headline + about + featured + banner + custom URL + skills + company-page sync), **content production** (single text posts + document carousels + native video + LinkedIn newsletters + articles + polls + LinkedIn Live + collab posts), **distribution & engagement** (Topic Authority deliberate building + comment strategy on others' posts + DM strategy + connection strategy + employee/founder advocacy + golden-hour timing), **funnel mechanics** (content → DM → call funnel design + Sales Navigator + paid LinkedIn Ads + newsletter subscriber list-building + SSI optimization), and **measurement** (analytics + 30/60/90 execution roadmap + 12-month Topic Authority compounding plan).

Three load-bearing 2026 shifts make this scope expansion non-optional: (1) the **360Brew ranker rewrite** (Q4 2025 → Q2 2026) introduced Topic Authority as a structural distribution gate — single-post optimization in isolation is now dominated by *topic-consistent corpus over time* across content surfaces; (2) **document carousels** earn 6.60% engagement and 39% more reach than text posts (Socialinsider 2026), making "ignore carousels" an actively bad trade for B2B SaaS / consulting / AI / agency clients; (3) the **comment strategy on others' posts** is now the dominant audience-building lever for new accounts — building a 10–50K following from a cold start by posting alone is structurally harder in 2026 than building it via deliberate high-leverage commenting in the first 90 minutes of in-lane authors' posts. The Welsh, Acosta, Goodman, and Edelman 2025 literature all converge here independently.

The comprehensive deliverable architecture this document proposes is a **multi-part LinkedIn Program** (analog to the marketing audit's multi-part output), not a single artifact: (a) a LinkedIn audit (~1,500 words covering profile + current content + current engagement + current Topic Authority fingerprint); (b) a Cut/Reduce/Add prescription (~1,200 words); (c) a profile audit with replacement copy (headline + about + featured + banner spec; ~800 words); (d) a content strategy (pillars + cadence + voice guidelines + format mix; ~1,500 words); (e) 5–10 sample posts across formats (text + carousel storyboard + thread + newsletter excerpt; ~2,000 words); (f) a comment strategy + 10 target accounts to engage (~800 words); (g) DM templates (cold + warm + qualification arcs; ~600 words); (h) connection strategy + ICP targeting plan (~600 words); (i) 30/60/90 execution roadmap (~1,000 words); (j) Topic Authority compounding plan (12-month arc; ~800 words); (k) cross-platform syndication rules (X→LI, blog→LI, podcast→LI; ~400 words). Total target: ~11,000 words, comparable in size envelope to the marketing audit deliverable. The single-text-post lane becomes ONE downstream production unit inside Layer 2 of this program, not the program itself.

For the evolution loop, this raises a non-trivial architecture question: the loop's per-fixture iteration cost grows with deliverable size, and an 11,000-word multi-part deliverable would 5–10× the per-iteration cost vs the current text-post lane. The recommended structure is **stratified production** — each layer has its own sub-lane with its own judge criteria, and the top-level "LinkedIn Program" deliverable is the composition (analogous to how `competitive` produces audit-shaped output while `linkedin_engine` produces post-shaped output). This means scoping LinkedIn at the program level requires *multiple* lanes, not one super-lane: `linkedin_profile`, `linkedin_engine` (text-post, current v1), `linkedin_carousel`, `linkedin_newsletter`, `linkedin_comment_strategy`, `linkedin_program` (the meta-composition lane that produces the full multi-part deliverable). The v1 text-post lock holds; the architecture extends sideways via sibling lanes rather than vertically via lane bloat.

The rest of this document maps the 20+ activity axes in detail, identifies what gets CUT from the 2018–2023 LinkedIn playbook, identifies the modern levers that get ADDED, flexes the scope across the six verticals gofreddy targets, proposes the multi-part deliverable architecture with size envelopes, identifies evolution-loop architecture considerations, inventories SOTA exemplars across the full surface, and flags open questions.

---

## §1 Full surface mapping — the 20+ axes

A 2026 LinkedIn program for a small-to-medium tech-savvy founder client should encompass roughly 25 distinct activities. They cluster into five layers. Within each layer, activities are ordered by leverage (highest first); cross-layer dependencies are noted.

### Layer 1 — Profile foundation (the substrate for everything else)

**1.1 Profile audit.** Baseline review against the 2026 profile-quality bar. Inputs: current headline, About paragraph, Featured section, banner image, custom URL, skills section, recommendations count and recency, work history coherence, company-page connection. Outputs: a per-element score plus prioritized issues. The audit is the entry point for every other Layer 1 activity. Leverage: foundational — every post downstream inherits the profile's credibility surface. Per Edelman/LinkedIn 2025, 73% of B2B decision-makers cite consistent thought leadership as a trust signal, and the profile is what they check after the post earns dwell.

**1.2 Headline rewrite.** The headline is the most-viewed 220 characters in LinkedIn — it appears in feed bylines, search results, DM previews, and comment-thread author lines. The 2026 pattern that compounds: *(target audience) + (specific outcome) + (mechanism / proof point)* — not job title alone. Sample structure: "Helping B2B SaaS founders ($1M–$10M ARR) turn LinkedIn into pipeline | 50+ posts shipped | 3 client case studies live." Old playbook ("VP of Marketing at Acme | Storyteller | Coffee Enthusiast") is dead — it provides zero signal to a feed-reader.

**1.3 About rewrite.** Maximum 2,600 characters; the first 250 characters appear above the "...see more" cut. The 2026 pattern: open with a specific reader-side problem statement, deliver one specific proof point, name the work the author actually does, close with a concrete next step (DM trigger, newsletter signup, calendar link). Old playbook (third-person bio, generic career narrative, no CTA) is also dead.

**1.4 Featured section.** Three pinned items maximum (more dilutes). The slots: (a) the author's strongest piece of content from the last 90 days (a high-performing post, a carousel, a newsletter issue); (b) the author's primary off-platform asset (newsletter signup page, lead magnet, podcast); (c) a credibility anchor (case study, press mention, talk recording). The Featured section is the conversion surface inside the profile — when a reader clicks the byline after a post, this is what holds them.

**1.5 Banner image.** The 2026 banner pattern: clear visual reinforcement of the headline's positioning + one explicit CTA visible above the fold on mobile (the banner is the second most-viewed visual on the profile after the avatar). Old playbook (generic landscape, abstract office shot, no copy) is now low-status.

**1.6 Custom URL.** `/in/firstname-lastname` is the 2026 baseline; deviations are tracked as "this person doesn't know LinkedIn." Free to set.

**1.7 Skills section.** Top 5 pinned skills appear under the headline and feed into LinkedIn's recommendation graph. Choose to reinforce the headline's positioning, not to enumerate every skill the author has. Endorsements from in-network peers compound.

**1.8 Company-page sync.** When the client has a company page, the founder's personal profile and the company page need coherent positioning (same target audience, complementary content, employee-advocacy linkage). Founders who run a personal profile in one direction while their company page runs in another direction confuse the algorithm's Topic Authority fingerprint.

**1.9 Recommendations strategy.** Recommendations decay in algorithmic weight after ~12 months. The 2026 pattern: 5–10 recent (within last 18 months) recommendations from named peers in the client's ICP. Old playbook (collect as many as possible, decade-old recommendations from former colleagues) provides diminishing return.

### Layer 2 — Content production (the renewable surface)

**2.1 Single text posts (current v1 scope).** 600–2,000 characters, text-only or with one image. The atomic unit of LinkedIn content. Cadence recommendation: 3–5 per week for active growth, 2–3 per week for maintenance, daily for hard-launch periods (under 90 days). Engagement benchmark: 4.2% per Socialinsider 2026.

**2.2 Document carousels.** PDF uploads displayed as swipe-able cards (4–12 slides typical, hard ceiling at ~20). The 2026 dominant format: 6.60% engagement, 39% more reach than text per Socialinsider; LinkedIn's product team has actively promoted this format since 2024 because the dwell mechanic (swipe-completion) is harder for AI to game than text dwell. Use cases: structured frameworks, before/after comparisons, multi-step processes, swipe-able case studies, list-based posts where each item earns its own slide. **The v1 spec scope OUT decision is correct for the judge — carousels have different dwell mechanics — but scope OUT of the program would be a major miss for B2B SaaS / AI / consulting / agency clients.** Cadence: 1 per week is the upper bound (production cost is higher than text); some clients should run carousels every 2 weeks alternating with text.

**2.3 Native video posts.** 30–180 second videos uploaded natively (NOT third-party-hosted; LinkedIn cuts third-party-app video reach 50–70% per Van Der Blom 2025/26). 2026 engagement: ~3.2% but with 2× conversion vs text for personality-driven authors. Use cases: founder-led short-form (talking-head insights), product demos, behind-the-scenes, conference-talk excerpts. Cadence: 1 per 2 weeks typical; weekly for personality-led brands (Welsh, Bloom, Murray).

**2.4 LinkedIn newsletters.** Subscribe-based content surface — separated distribution from feed, separate Depth Score, ~10× higher avg open rate vs feed reach when sub list >500. Format: 500–2,500 words, weekly or bi-weekly. The 2026 newsletter use case: long-form thought leadership that earns ongoing trust + a subscriber list-building mechanism (subscribers become the activation seed for every other content surface). Sahil Bloom's "Curiosity Chronicle" and Sarah Tavel's "Threshold of Insight" are the canonical exemplars. This is the highest-leverage long-form surface LinkedIn offers — and the most under-utilized by small-to-medium clients.

**2.5 LinkedIn articles.** The original long-form surface (predates newsletters). 2026 use case is narrower: occasional deep-dive pieces (1,500–4,000 words) that the author wants the SEO surface for and that may be syndicated to a personal blog. Articles share the newsletter's distribution physics but lack subscriber stickiness. Most small-to-medium clients should use newsletters not articles.

**2.6 LinkedIn polls.** 2026 engagement: ~4.0% when options are non-trivial; rebounded after a 2024 dip per Socialinsider. Use case: data-gathering, audience-pulse-taking, conversation-starting where the poll options frame a specific debate. Old playbook (4-option commodity surveys) is dead; modern polls have 2 deliberately-contrasting options or 3-option triages of a real decision. Cadence: 1 per 2–4 weeks; over-use signals laziness.

**2.7 LinkedIn Live.** Real-time video broadcasting. 2026 use case: launches, AMAs, expert panels, conference-companion sessions. Production cost is high; most small-to-medium clients should run 1 Live event per quarter (a hard launch, a year-end retro, a category-defining talk). Companion content (clips + post-event carousel + post-event newsletter) compounds the production cost.

**2.8 LinkedIn collab posts.** Native co-authored posts (the 2024–2025 feature). Two or more named authors share authorship on a single post; both networks see the post. Use case: partnerships, co-marketing, joint launches. Cadence: 1 per quarter typical; quality > frequency.

**2.9 Image-with-text posts.** Single image + caption (500–1,500 char body). Use case: announcement posts, product shots, founder photos, event photos. Engagement is moderate (~3.8%); the image works as a scroll-stopper but the caption carries the substance.

**2.10 Cross-platform syndication content (LI-native repurposing).** X threads → LinkedIn carousel; blog post → LinkedIn article excerpt; podcast episode → LinkedIn audiogram + transcript-derived text post; conference talk → LinkedIn carousel + Live recording clip. The 2026 syndication rule: never paste a post directly across platforms — each surface needs its native register. X-shaped contrarian punch lands as bait on LinkedIn (a documented LI-3 failure mode in v1 spec); LinkedIn-shaped longform reads as preachy on X.

### Layer 3 — Distribution & engagement (the growth lever)

**3.1 Topic Authority deliberate building.** The single highest-leverage 2026 activity. 360Brew's Topic Authority cross-references claimed expertise against published content corpus; topic-consistent authors see up to 78% higher distribution on in-lane content. The deliberate build: pick 1–2 primary topic pillars + 1–2 secondary pillars + ~10% off-topic posts (Welsh's published 80/20 split); ship in-lane content consistently for 90+ days before expecting Topic Authority lift; track which topics earn distribution and double down on those. Most small-to-medium clients have no deliberate topic strategy and are penalized by the algorithm for topic dispersion.

**3.2 Comment strategy on others' posts.** Now the dominant audience-building lever for accounts under 10K followers. Mechanism: high-leverage comments on in-lane authors' posts inside the first 90-minute golden hour earn impressions and profile clicks from that author's network — and the algorithm reads the commenter's name as a Topic Authority signal in the same lane. The 2026 playbook: identify 10–25 in-lane creators with 5K–50K followers; comment substantively (30–80 words; same comment-substance threshold as the post's own comment seeds in LI-4) within their first hour for 3–4 of their posts per week. This produces 5–15K incremental impressions per week from cold, in-lane readers. The Daniel Murray and Lara Acosta growth trajectories were both substantially comment-built.

**3.3 DM strategy — inbound.** Inbound DMs from posts are the highest-credibility signal LinkedIn produces — a reader who DMs after reading thought it was worth a private follow-up. 2026 playbook: have a templated-but-personalized first-response that opens a conversation arc rather than slamming into a sales pitch; the conversation arc should qualify in 2–3 messages (do they fit the ICP? do they have intent?) and offer either a deeper async resource or a 30-minute call. The Sahil Bloom and Justin Welsh DM funnels are the canonical exemplars (both publish their templates).

**3.4 DM strategy — outbound.** Outbound DMs to ICP-fit connections are the second-highest-leverage growth tactic, conditional on doing them well. 2026 reality: most outbound DMs are spam, the LinkedIn algorithm rate-limits high-volume senders, and recipients are deeply jaded. The narrow window that works: warm outbound to people who have engaged with the sender's content (commented, liked, viewed profile) within 7 days. Cold outbound to ICP-fit strangers with no prior engagement signal converts at 1–3%; warm outbound converts at 15–30%. Lavender's outbound research and the 2025 Hubspot State of Outbound report are the data sources.

**3.5 Connection strategy.** Two distinct patterns: (a) the *open networker* pattern (accept all connections, build a 30K+ network, treat connections as broadcast surface); (b) the *curated network* pattern (only ICP-fit + in-lane peers; quality > quantity; 5K–10K). The 2026 algorithm rewards engagement-density-per-connection, which means the curated network often outperforms the open network on Depth Score. Welsh's 50K+ network is curated; Acosta's is similar. Recommendation for most small-to-medium clients: curated network; specifically, an ICP-fit growth target of 50–100 net new connections per month from people who have engaged with the author's content.

**3.6 Founder-led visibility plan.** For founder clients, the founder's personal profile should be the primary content surface (not the company page). Algorithm reality: personal profiles earn ~5–10× the organic reach of company pages on equivalent content. The pattern: founder posts personally; company page reshares the founder's content; employees engage with both. This requires the founder's *time*, which is the binding constraint for most founder clients — most of the agency's work is making this lift sustainable (drafting, ghostwriting, scheduling, editing) while preserving voice.

**3.7 Employee/team advocacy program.** When the client has a team (10+ employees), an advocacy program multiplies content reach 3–8× per post (each employee who reshares hits a partially-overlapping network). 2026 pattern: opt-in advocacy with a Slack/Notion content-share board, weekly digest of company posts + suggested commentary, periodic content-creation workshops for advocates. Tools: EveryoneSocial, GaggleAMP, or a homegrown Slack workflow. Most small-to-medium clients under-utilize this.

**3.8 Engagement pod strategy (or deliberate avoidance).** Engagement pods were widely used 2019–2023 to game the algorithm via coordinated likes/comments inside the golden hour. The 2026 reality: LinkedIn detects pod patterns (suspiciously similar engagement timing, suspiciously similar account clusters) and downranks. AI-generated pod comments are filtered as of mid-2025. Recommendation: deliberate avoidance. The replacement is organic golden-hour engagement from a curated network (Activity 3.5) plus comment strategy on others' posts (Activity 3.2) — both unbottable.

**3.9 Golden-hour timing optimization.** The first 90 minutes after publishing determine ~70% of total reach per Van Der Blom 2025/26 — the algorithm uses early engagement velocity to predict downstream performance. 2026 playbook: time posts to the ICP's natural reading window (US B2B: 7:30–9:00 AM and 12:00–13:00 client local time; international: matched). The author should be available to respond to comments in the first 60 minutes (the reciprocity signal Van Der Blom names as a Depth Score input). LinkedIn's native scheduler is now reliable; third-party schedulers (Buffer, Hootsuite) work but third-party-API content sometimes sees marginal reach cuts.

**3.10 Cross-platform syndication strategy.** The agency-level decision: what content lives where, and what gets syndicated. Default 2026 pattern for tech-savvy founders: X for short-form / quick takes / community / hot-take fluency; LinkedIn for long-form thought leadership / case studies / company news / B2B reach; personal blog or newsletter for evergreen long-form; podcast for relationship-building. The agency's job is to keep these in a coherent operating cadence rather than letting one platform starve the others.

### Layer 4 — Funnel mechanics (the monetization surface)

**4.1 LinkedIn-native funnel design — content → DM → call.** The canonical 2026 small-to-medium B2B funnel: (a) high-value content earns dwell + comment + profile-click; (b) interested reader DMs the author; (c) async DM conversation qualifies the lead in 2–4 messages; (d) qualified lead books a 30-minute call via a Calendly link; (e) call → proposal → close. The agency's job is engineering each stage's conversion — the post needs to invite the DM, the DM template needs to qualify without selling, the call link needs to be 1 click. The Welsh "Saturday Solopreneur" newsletter funnel and the Sahil Bloom "Curiosity Chronicle" funnel are the canonical exemplars (both publish the mechanics).

**4.2 LinkedIn newsletter as subscriber list builder.** Newsletters are the only LinkedIn surface where the author *owns the audience* — the subscriber list is portable (LinkedIn allows CSV export) and the subscriber gets a notification on every issue. The 2026 strategy: every post → 1–2% CTR to the newsletter signup → the newsletter does the recurring trust-building. For most small-to-medium clients, building a 1K+ newsletter subscriber list inside LinkedIn over 12 months is the single highest-leverage compounding outcome.

**4.3 Sales Navigator integration.** LinkedIn's paid prospecting tool. 2026 use case for small-to-medium clients: identifying the ICP-fit warm-outbound targets (Activity 3.4) by saved-search; tracking which targets are engaging with the author's content; identifying buying-signal accounts. Cost: ~$80/mo per seat. ROI is positive for any client doing B2B outbound; ROI is marginal for pure content-distribution clients.

**4.4 LinkedIn Ads (paid scope).** 2026 ad formats: sponsored content (boost a high-performing organic post), sponsored InMail (direct DMs to non-connections; high CPL but high conversion when targeted), conversation ads (interactive multi-CTA DMs), lead-gen forms (forms inside the LinkedIn surface so the user doesn't leave). Cost: LinkedIn Ads are 3–10× the CPM of Meta and 2–4× X — small-to-medium clients should run paid sparingly and only when organic compounds aren't producing the volume needed. The canonical first paid spend: boost the author's top organic post each month against the ICP audience (~$500–2,000/mo) — earns 5–10× the post's organic reach without writing new content.

**4.5 SSI (Social Selling Index) optimization.** LinkedIn's proprietary score: 4 dimensions × 25 points each (establish professional brand / find right people / engage with insights / build relationships). Public score at `linkedin.com/sales/ssi`. 2026 use case is diagnostic, not target — SSI is a moderate-quality proxy for whether the author is following LinkedIn's best practices. SSI >75 is "good"; >85 is "exceptional"; the score corresponds to roughly 2× the engagement at >75 vs <50. Track quarterly.

### Layer 5 — Measurement & strategy

**5.1 Analytics + measurement plan.** Native LinkedIn analytics cover post-level (impressions, reactions, comments, shares, click-throughs) and audience demographics. Third-party tools (Authoredup, Shield Analytics, Inlytics) add cohort analysis, time-of-day heatmaps, content-pillar attribution, and historical archives. The 2026 measurement minimum: track per-post per-pillar engagement rate + per-post profile-click rate + per-post DM rate; track newsletter subscriber growth weekly; track SSI quarterly. The lagging-indicator: pipeline contribution from LinkedIn-attributed leads — track via UTM-tagged CTA links + DM-to-call conversion logs.

**5.2 30/60/90 execution roadmap.** Standard agency deliverable for client onboarding. The 2026 pattern: 30 days = profile foundation + content production startup (Layers 1 + 2.1–2.2) + first 5–8 posts shipped; 60 days = full content cadence live + comment strategy + DM strategy + 100 net new connections; 90 days = first Topic Authority signal visible + newsletter launched + first measurable pipeline contribution. Beyond 90 days requires recalibration based on what the analytics show.

**5.3 12-month Topic Authority compounding plan.** The longer-arc strategy. Most small-to-medium clients see meaningful Topic Authority lift around month 4–6 (after ~50–80 in-lane posts); compounding becomes obvious around month 9–12. The plan defines: which 1–2 primary pillars + which 1–2 secondary pillars; quarterly pillar reviews + cadence adjustments; quarterly newsletter format experiments; semi-annual content-mix rebalances. Without a 12-month arc, most clients churn out of LinkedIn content programs around month 3–4 because they haven't seen ROI yet — the Topic Authority compounding inflection point is past their attention window.

**5.4 Content calendar + production system.** The operational surface — what content is being produced when, by whom, against what fixture set. For agency clients, the production system spans: a topic ideation backlog (50–200 candidate post ideas tied to the 1–2 primary pillars); a weekly editorial review; a daily ghostwriting → founder-review → publish cycle; a comment-strategy daily list; a monthly carousel + quarterly newsletter cycle. The system is what makes the program *sustainable* over the 12-month arc; without it, content production peters out around month 3.

**5.5 Brand voice + style guide.** A documented voice substrate — what the founder sounds like in writing, what phrases they avoid, what topics are off-limits, what topics are core, what level of self-disclosure is comfortable. This is the analog of the v1 spec's `programs/references/voice.md` substrate but at the program level. Without it, the agency's ghostwriters drift toward generic LinkedIn voice (which scores poorly on LI-3 and LI-5).

---

## §2 What gets CUT from the old LinkedIn playbook

The 2018–2023 LinkedIn playbook contains a substantial layer of tactics that no longer work in 2026 — either because the algorithm has actively suppressed them, because the audience has pattern-matched them as low-status, or because the AI-generation toolchain has flooded them past their useful lifespan. The agency's role is to recognize and cut these surgically.

**CUT-1: Broetry as default format.** Single-sentence-per-line dramatic-pause posts engineered to game the read-more click. Originated December 2017 (Mac, BuzzFeed News); originator banned; LinkedIn deprecated 2018. The format has survived because the AI-generation toolchain rediscovered it as default — broetry maximizes apparent emotional weight per token. In 2026, broetry-line density ≥40% triggers the LI-3 AI-slop gestalt stack (v1 spec §3a) AND triggers visible audience eye-rolling. CUT means: not banning single-line paragraphs entirely (Welsh's posts use them; the technique is legitimate when substance compounds across lines) but cutting the structural overuse where every line is one sentence regardless of content.

**CUT-2: The hero's journey post.** "$7 in my bank account → 7-figure business" closing on a course pitch. Engineered to extract emotion before a sale. Cringe-tagged as one of the most reliably AI-generated formats. The audience's tolerance for this format has cratered; even authentic versions (real founders who genuinely went from $7 to 7 figures) now read as performative. The 2026 replacement: specific tactical insight from the same journey, told as one moment not a complete arc.

**CUT-3: The janitor-wisdom / airport-story format.** "A janitor at LAX taught me everything I know about leadership." Almost always fabricated or composite. The 2026 audience flags this within 3 seconds. CUT entirely.

**CUT-4: The humblebrag.** "I'm so humbled to announce...". Sezer/Norton/Gino 2018 (MIT): humblebraggers are perceived as less likeable, less competent, less influential than direct braggarts. The format inverts its own goal. The 2026 replacement: direct announcement ("We just shipped X.") without the false-modesty wrapper.

**CUT-5: Generic motivational quotes.** "Success is going from failure to failure without losing enthusiasm." — Churchill (probably misattributed). Add an obligatory inspiring image. 2018–2022 these were a content backbone for low-effort accounts; in 2026 they fail the Denning name-stripped test (could be written by any author) and score 0 on LI-2. CUT entirely.

**CUT-6: "I X for Y years. Here's what I learned" generic openers.** The opener shape is legitimate (Denning has built his audience on close variants) — but only with substantive author-specific content underneath. The CUT is the *generic-listicle-under-the-opener* version: 7 lessons that swap across authors. The opener stays; the contentless listicle goes.

**CUT-7: AI-slop with em-dash density >1.0 per 100 words.** Plagiarism Today June 2025 dataset: GPT-4o median 0.6 per 100 words vs human median 0.05 per 100 words. The AI-baseline-overuse range (>1.0/100 words) is now an audience-detectable signal. CUT means: ghostwriters editing AI drafts down to the human-stylist range (0.2–0.4 per 100 words), not eliminating em-dashes (legitimate operators like Acosta and Alić use them deliberately).

**CUT-8: "Stop X. Start Y." parallel-list compression.** A 2024–2026 AI-generation tell when used repetitively across an entire listicle. The format is legitimate as a single rhetorical move (Welsh uses it occasionally) but kills the post when stretched into the structural backbone. CUT the structural-backbone version; preserve the single-move version.

**CUT-9: Engagement-bait CTAs.** "Comment YES if you agree," "Type 1 if you agree," "Tag a friend who needs this," "Like for Part 2," "Repost if you've felt this." LinkedIn's 2026 NLP classifier triggers ~60% distribution suppression once any of these fires regardless of account history (per LinkBoost, meet-lea 2026). CUT entirely — these are now self-defeating.

**CUT-10: P.S.↓ closers.** Per Plagiarism Today: ~12% of GPT-4o LinkedIn outputs vs <1% of human posts. CUT entirely — currently an unambiguous AI-slop tell.

**CUT-11: "Here are 7 lessons" listicle-bloat openers.** Numbers in {5, 7, 10, 12} dominate because they hit the algorithm's familiar reading patterns; the AI generation toolchain has converged on these so heavily that the opener alone now reads as templated. CUT the openers; preserve the underlying numbered-list format when each item is author-specific and substantive (LI-2 anchor).

**CUT-12: Symmetrical bullet rhythm.** Every bullet identical length, identical syntactic shape. Quantifiable via variance of bullet lengths (CV <0.15 = AI-shaped). CUT the symmetrical version; preserve varied-length bullets that match human writing rhythm.

**CUT-13: Template-phrase openers.** "Let me explain why," "Here's the kicker," "Here's the thing," "It's not just X — it's Y." Each is a generation-model bridge token. CUT entirely — they're a deterministic AI-slop tell.

**CUT-14: Engagement pod participation.** LinkedIn detects pod patterns (suspiciously similar engagement timing, suspiciously similar account clusters) and downranks. AI-generated pod comments are filtered as of mid-2025. CUT entirely — they're now distribution-negative.

**CUT-15: Third-party-app video uploads.** LinkedIn cuts third-party-API video reach 50–70% per Van Der Blom 2025/26. CUT — upload native or skip video entirely for that post.

**CUT-16: Generic "Open to work" badges as long-term profile state.** Useful when actually job-hunting; a low-status signal when permanent (suggests the author has been job-hunting for 6+ months). CUT — replace with a "Helping (target) achieve (outcome)" headline that signals current value-creation, not job-seeking.

**CUT-17: Profile bios in third-person.** "John is a passionate marketing leader with 15 years of experience..." Reads as ghostwritten by a 2015 employer comms team. CUT — replace with first-person, problem-statement-led, conversion-driven copy.

**CUT-18: Posting daily without a topic pillar strategy.** Pre-2026, posting volume was a primary growth lever. Post-360Brew (Topic Authority), posting volume *without* topic-consistency now penalizes the author's distribution — the algorithm reads dispersion as expertise dilution. CUT the volume-without-strategy approach; replace with the cadence + pillar plan from §1 Activity 3.1.

**CUT-19: Posting from the company page as primary surface for founder content.** Personal profiles earn 5–10× the organic reach of company pages. CUT — founder content goes on the founder's personal profile; the company page reshares.

**CUT-20: "Repost if you agree" requests as engagement strategy.** Reposts without commentary are now near-zero algorithmic value per Van Der Blom (naked reshares contribute a fraction of substantive comments). CUT — replace with collab posts (Activity 2.8) and earned reshares-with-commentary.

---

## §3 What gets ADDED as modern levers

The 2026 LinkedIn playbook adds roughly 15 explicit modern levers that the 2018–2023 playbook did not include. Most of these correspond to algorithmic changes (360Brew, Topic Authority, comment NLP classifier) or audience shifts (AI-slop fatigue, founder-led-content rise). They are higher-leverage on average than the cuts in §2 — the cuts are defensive, the adds are offensive.

**ADD-1: Topic Authority deliberate building.** Single highest-leverage 2026 activity (§1 Activity 3.1). The 78% distribution lift for topic-consistent authors is the largest single algorithmic lever LinkedIn has introduced since 2018. ADD means: every client gets a documented 1–2 primary + 1–2 secondary topic pillar strategy with a 90-day commit minimum.

**ADD-2: Comment strategy on others' posts as audience-building lever.** For accounts under 10K followers, comments on others' posts now produce more incremental impressions per week than the author's own posts. ADD means: every client gets a documented 10–25-account target list + a daily 15-minute commenting block.

**ADD-3: Document carousels as 1× per week minimum format.** 6.60% engagement, 39% more reach than text. ADD means: every B2B SaaS / consulting / AI / agency client produces a carousel weekly (or every 2 weeks). Even non-B2B clients in service businesses / finance / e-commerce benefit when their topic admits visual framing.

**ADD-4: LinkedIn newsletters as subscriber-list-building primary lever.** The only LinkedIn surface where the author owns the audience. ADD means: every client launches a newsletter within the first 60 days of the program; the newsletter is the conversion target for every other content surface.

**ADD-5: Founder-led visibility plan for founder clients.** Founder personal profiles earn 5–10× company-page reach. ADD means: for founder clients, the agency's content production is founder-first (ghostwriting + editing + scheduling for the founder's personal profile) rather than company-page-first.

**ADD-6: Modern algorithm timing — 90-minute golden hour as production constraint.** Per Van Der Blom: first 90 minutes determine ~70% of total reach. ADD means: the production schedule pegs publishing to the ICP's natural reading window (US B2B: 7:30–9:00 AM and 12:00–13:00); the author is available for golden-hour response.

**ADD-7: 30–80-word substantive comment seed as the unit of engagement.** Per Van Der Blom + LinkBoost: comments under 10 words contribute ~0 to Depth Score; ideal comment band 30–80 words; comments weighted ~15× a like. ADD means: every post is designed to invite 30–80-word substantive comments (the four mechanism families in v1 spec §4 LI-4), and the author engages 30–80 words back in the golden hour.

**ADD-8: Cross-platform syndication rules.** Each platform has its native register; pasting across platforms produces register failures. ADD means: X→LI translation rules (de-compress the contrarian punch into thoughtful authority), blog→LI rules (excerpt the strongest 800-word section, not the full piece), podcast→LI rules (audiogram + transcript-derived text-post + carousel slides). Documented in the program's strategy doc.

**ADD-9: Cut/Reduce/Add prescription as standard deliverable.** Per the marketing-audit lane pattern: every client engagement opens with a documented Cut/Reduce/Add prescription based on their current state, not a generic best-practices doc. ADD means: the program's first 1,200-word deliverable is the prescription.

**ADD-10: Comment-magnet engineering vs comment-bait elimination.** The four mechanism families (debatable defensible claim / genuine question requiring reader experience / enumerated frame with empty-slot affordance / honest-disagreement signal) replace the older "ask a question at the end" pattern. ADD means: post drafting walks through which of the four mechanisms is being invoked, organically.

**ADD-11: AI-slop fatigue defense — gestalt-stack monitoring.** The audience's tolerance for AI-slop has collapsed; the agency's role is producing content that *uses* AI in production but doesn't *read as* AI. ADD means: every draft passes a deterministic gestalt-stack check (em-dash density, broetry-line density, bullet-rhythm CV, banned-phrase scan) before publishing.

**ADD-12: Author-context coherence as content-design constraint.** Per Edelman/LinkedIn 2025 + 360Brew Topic Authority: register mismatch is now a structural distribution gate AND a structural trust gate. ADD means: every post is checked for register coherence (founder-stage writing about founder-stage problems, not Series-D scaling) before publishing.

**ADD-13: LinkedIn Live + collab posts as relationship-building levers.** Both formats compound network value beyond their direct engagement. ADD means: every client schedules 1 Live event per quarter + 1 collab post per quarter as deliberate network-building moves.

**ADD-14: Employee/team advocacy programs for 10+ employee clients.** 3–8× content reach multiplier. ADD means: clients with 10+ employees get an opt-in advocacy program with a Slack/Notion content-share board.

**ADD-15: Quarterly content-pillar review + semi-annual content-mix rebalance.** Topic Authority compounds over 9–12 months; the program needs deliberate review points to recalibrate based on what the analytics show. ADD means: the program's strategy doc bakes in quarterly review points and the agency runs them with the client.

---

## §4 Vertical adjustments

The comprehensive scope above is anchored on tech-savvy founder / operator clients. Across the six verticals gofreddy targets — SaaS, AI lab researcher, agency principal, service firm partner, finance operator, e-commerce operator, mid-career B2B IC — the surface flexes but does not fragment. The flex points are: which formats fire hardest, which topic pillars compound, what register matches the audience, and what funnel stages are dominant. The 25 activities themselves remain stable across verticals.

**B2B SaaS founder ($1M–$50M ARR).** Default mix: 60% single text posts (founder-narrated tactical insight, hiring decisions, product strategy) + 25% carousels (frameworks, case studies, before/after) + 10% video (product demos, founder takes) + 5% polls/articles. Topic pillars typically: (a) the company's core product domain (e.g., "B2B onboarding"); (b) a meta-topic the founder has standing on (e.g., "early-stage SaaS GTM"). Funnel stage dominant: content → DM → call (Activity 4.1) — qualifying inbound founder-stage interest. Newsletter is high-value (subscriber list = warm leads). Sales Navigator is positive ROI. The Welsh model is the canonical exemplar for solo founders; the Lenny Rachitsky model for thought-leader founders with a horizontal audience.

**AI lab researcher / scientific organization.** Default mix: 40% single text posts (specific findings, model-card releases, methodological takes) + 30% carousels (paper summaries, diagram-heavy explanations, before/after metric comparisons) + 15% newsletter (long-form research writeups) + 10% articles (deep technical pieces) + 5% video (lab tours, talk excerpts). Topic pillars: (a) the lab's core research area; (b) cross-cutting AI safety / alignment / interpretability topic. Audience is narrower (researcher peers + applied-AI engineers + AI-aware operators); LinkedIn is a secondary platform vs Twitter/X for this audience (which is X-native). Funnel stage dominant: content → newsletter sub → hiring/collab DM. Volume can be lower (1–2 posts/week) because audience expects depth not frequency. The Anthropic + Google DeepMind + OpenAI org-level approach is the exemplar; for individual researchers, the Sebastian Raschka or Andrej Karpathy model.

**Agency principal (small-to-mid services firm).** Default mix: 50% single text posts (client work, agency philosophy, hiring decisions, business-of-agency takes) + 30% carousels (case studies, frameworks, anonymized client wins) + 10% video (founder-led behind-the-scenes, talk recordings) + 5% poll + 5% newsletter. Topic pillars: (a) the agency's core service category (e.g., "modern brand design"); (b) the meta-topic of running an agency or doing the work well. Funnel stage dominant: content → DM → call → proposal (Activity 4.1 is the agency's entire growth engine when paid is not running). Comment strategy on others' posts is critical because agency principals win clients via their visible expertise + relationships. Daniel Murray's model + Lara Acosta's model are the canonical exemplars.

**Service firm partner (law / accounting / consulting).** Default mix: 60% single text posts (case-based insights, regulatory takes, professional anecdotes within ethics bounds) + 25% carousels (visual frameworks for clients, before/after of a complex topic) + 10% articles (long-form for SEO + LinkedIn surface) + 5% video. Topic pillars: (a) the partner's practice specialty (e.g., "regulated finance M&A"); (b) the meta-topic of doing the work (e.g., "what M&A buyers look for"). Constraints: regulatory / privilege / confidentiality bounds are tighter than other verticals (no client names without consent, no in-process matters, no specific dollar amounts). Funnel stage dominant: content → relationship-building inbound. Newsletter is high-value because the audience often re-reads. SSI optimization is high-value because peer-network strength is the conversion mechanism (referrals). The DWF Poland + Pinsent Masons + EY senior-partner approaches are the exemplars; individually, Tim Stobierski's model for thought-leader services.

**Finance operator (founder / CFO / fund-LP / investor).** Default mix: 50% single text posts (deal takes, market commentary, portfolio thesis, hiring takes) + 30% newsletter (long-form thesis writeups, quarterly recaps) + 15% carousels (frameworks, market data visualization) + 5% poll. Topic pillars: (a) the operator's specific finance sub-domain (e.g., "B2B SaaS valuations" or "European M&A"); (b) a meta-topic the operator has standing on (e.g., "running a finance org at growth-stage"). Audience is dense (other operators + LPs + portfolio companies); LinkedIn is competitive with X for this audience but LinkedIn dominates for the operator who isn't X-native. Funnel stage dominant: content → newsletter → DM → call (longer arc; trust-building is slower). Sahil Bloom's Curiosity Chronicle is the canonical exemplar; Marc Rubinstein's Net Interest is the canonical newsletter-only model.

**E-commerce operator (DTC founder / marketplace operator / retail owner-op).** Default mix: 40% single text posts (operator narrative, brand decisions, supply-chain takes) + 35% carousels (product showcases, before/after creative tests, marketing-campaign breakdowns) + 15% video (product launches, behind-the-scenes, customer stories) + 10% other. Topic pillars: (a) the operator's specific e-commerce sub-domain (e.g., "DTC food brands" or "Shopify scaling"); (b) a meta-topic (e.g., "running an e-comm brand sustainably"). Audience cluster: other e-comm operators + agency/freelance service providers + investors. Visual content is structurally higher-leverage than other verticals because e-com is product-driven. Funnel stage dominant: content → DM → call OR content → newsletter → DM. The Sahil Lavingia (Gumroad) + Sara Blakely (Spanx) + Patrick Coddou (Supply) operator personalities are the exemplars at different scales.

**Mid-career B2B IC (engineer, marketer, product, sales).** Default mix: 50% single text posts (tactical insight, learning-in-public, project breakdowns) + 25% carousels (frameworks, before/after work examples, debugging walkthroughs) + 10% newsletter (deep-dive learning) + 10% poll + 5% video. Topic pillars: (a) the IC's specific specialty (e.g., "B2B SaaS pricing", "API design", "demand-gen ops"); (b) often a meta-topic about the discipline (e.g., "what makes a great PM"). Audience cluster: peer ICs + hiring managers + adjacent-discipline ICs. Funnel stage dominant: content → relationship-building → job opportunities OR content → side-project credibility. Lower commercial-intent than founder/agency verticals; newsletter value is in personal-brand-compounding more than direct lead-gen. Sebastian Raschka (ML/AI), Stripe Press's authors, and Lenny Rachitsky's "Lenny's Newsletter" model are the exemplars; closer to home, individual ICs at Stripe / Linear / Vercel.

**Cross-vertical invariants.** Regardless of vertical, five aspects of the program are constant: (a) the profile foundation activities (Layer 1) are identical in structure (headline + about + featured + banner + URL + skills + company-page sync); (b) the Topic Authority deliberate building (Activity 3.1) is the highest-leverage activity; (c) the four comment-magnet mechanisms (debatable claim / genuine question / enumerated frame / honest disagreement) work across all audiences; (d) the AI-slop gestalt stack to avoid is identical; (e) the 30/60/90 execution roadmap structure is identical.

**First-cohort overfitting watch.** The Welsh / Acosta / Alić / Denning / Meer / Murray / Bloom creator-archetype reference set used throughout the v1 spec and this document is tech-saas-skewed (and US-skewed). As gofreddy clients onboard from regulated-finance, hospitality, retail, healthcare-services, legal-services verticals, the agency must re-validate which anchor patterns generalize — most do (the platform physics are vertical-independent), but the specific exemplar names will rotate.

---

## §5 Proposed comprehensive deliverable architecture

The current `linkedin_engine` v1 lane produces ONE text-post draft per fixture, ~600–2,000 chars. The comprehensive scope this document maps requires a multi-part deliverable comparable in size envelope to the marketing audit lane. Architecture proposal:

**LinkedIn Program — multi-part deliverable.** Single deliverable, multiple sections, ~11,000 words total. Composed from sibling lane outputs.

**Section A — Audit (~1,500 words).** Current state assessment. Sub-sections: (a1) Profile audit (per-element score: headline, about, featured, banner, URL, skills, recommendations, company-page sync; specific issues identified); (a2) Content audit (last 30 days post inventory by format, engagement-rate distribution, topic-pillar coherence assessment, voice-substrate signal extraction); (a3) Engagement audit (network composition vs ICP, comment-strategy current state, DM-funnel current state, SSI score); (a4) Topic Authority fingerprint (which topics the algorithm currently associates with the author, dispersion analysis).

**Section B — Cut/Reduce/Add prescription (~1,200 words).** Concrete prescription tied to §2 cuts + §3 adds, customized to the client's audit. Includes the 20 cuts the client is currently doing (or 0–20 depending on baseline) and the 15 adds the agency is committing to introduce. Each cut/add is one paragraph with the rationale + specific first-action.

**Section C — Profile rewrite (~800 words).** Concrete replacement copy for headline, About paragraph, Featured section spec, banner image spec, custom URL recommendation, top 5 skills, recommendation-acquisition plan. Output is paste-ready copy + a punch-list of operator actions.

**Section D — Content strategy (~1,500 words).** Topic pillars (1–2 primary + 1–2 secondary with rationale), cadence by format (text / carousel / video / newsletter / poll / Live / collab; weekly counts), voice guidelines (tone register + phrase library + topics to avoid), format-fit-by-topic matrix (which topics fire as text vs carousel vs newsletter vs video), cross-platform syndication rules (X→LI, blog→LI, podcast→LI), 90-day content backlog (~50 topic ideas tied to pillars).

**Section E — Sample posts (~2,000 words).** 5–10 finished or near-finished post drafts across formats. Suggested: 4 text posts (one per topic pillar × 2 angles each) + 1 carousel storyboard (10 slides outlined) + 1 thread (3–4 connected posts) + 1 newsletter issue (excerpted; full draft would be ~1,500 words on its own) + 1 video script (90-sec founder-led). Each draft includes the editorial rationale: which pillar, which mechanism family from LI-4, target audience segment, expected reader-effect.

**Section F — Comment strategy + target accounts (~800 words).** 10 named target accounts (in-lane creators with 5K–50K followers); for each, why they're a target + when they typically post + what kind of comment to leave (mechanism family). Plus a daily 15-minute commenting checklist.

**Section G — DM templates (~600 words).** Cold-outbound template (3 variants matched to the ICP's top 3 personas), warm-outbound template (4 variants based on engagement signal: commenter / liker / profile-viewer / re-poster), inbound-response template (qualification arc: 2-message → 3-message → 4-message), call-booking link spec.

**Section H — Connection strategy + ICP targeting (~600 words).** ICP definition (titles + company-size + industry + geography), Sales-Navigator saved-search recommendations, weekly connection-request targets (50–100/week), connection-request message templates (3 variants), connection-acceptance follow-up arc.

**Section I — 30/60/90 execution roadmap (~1,000 words).** Day-by-day for first 30 days + week-by-week for days 31–90. Operator actions, agency actions, milestones, decision points. Includes risk-flags for the patterns that historically derail clients (volume burnout in week 4, no-results-yet anxiety in month 2, scope-expansion temptation in month 3).

**Section J — Topic Authority compounding plan (~800 words).** 12-month arc: quarterly milestones, expected compounding inflection points (month 4–6 for first signal, month 9–12 for visible compounding), pillar-review checkpoints, content-mix rebalance recommendations.

**Section K — Cross-platform syndication rules (~400 words).** Documented rules for X→LI, blog→LI, podcast→LI translations. Includes the specific register-translation moves (X compression → LI thoughtful authority; blog full-piece → LI 800-word excerpt; podcast episode → audiogram + carousel + text post + newsletter mention).

**Total: ~11,200 words** comparable in envelope to the marketing audit deliverable (~10–14K words typical). Stratified production: each section is produced by a sibling lane.

**Size envelope rationale.** 11K words is large enough to be a real strategic deliverable (clients pay for this; it's a 2-hour read + 4-hour absorb), small enough to fit inside a single Notion/Proof document and be iterable, and within the size envelope the existing marketing audit lane handles. The output is a one-time engagement-opener deliverable (delivered once per client at program kickoff); subsequent renewals produce just Sections A + B + D rebalance + I refresh quarterly (~3,500 words per quarter).

---

## §6 Evolution-loop architecture considerations

Implementing the comprehensive scope as a single super-lane would 5–10× the per-iteration cost of the current `linkedin_engine` lane, which is a non-starter for the autoresearch evolution loop. Three architectural moves keep the loop tractable.

**Move 1: Sibling-lane composition, not lane bloat.** Instead of a single super-lane producing the full 11K-word program, the surface is decomposed into 5–7 sibling lanes:

- `linkedin_engine` (current v1) — single text post, ~600–2,000 chars (Section E.4 text posts in the program deliverable). Already designed.
- `linkedin_carousel` — single document-carousel storyboard, 10 slides + caption. New lane. Different dwell mechanics → different judge criteria (swipe-completion, slide-text-density, framework-coherence, visual-hierarchy).
- `linkedin_newsletter` — single newsletter issue, ~1,500 words. New lane. Different reader (subscriber, not feed-scroller); different success conditions (read-through-rate, click-through-to-CTA, save-for-later); different judge criteria.
- `linkedin_profile` — full profile rewrite: headline + about + featured + banner + skills. New lane. Different artifact shape (multiple short pieces); deterministic length-band gates per section; judge tests positioning coherence + conversion-driven structure.
- `linkedin_comment_strategy` — produces the target-account list + commenting playbook for Section F. New lane. Outputs a structured list of accounts + rationale + comment-template-per-account.
- `linkedin_program` — the meta-composition lane. Pulls outputs from the sibling lanes + produces the high-level Sections A, B, D, I, J that integrate across them. Highest cost per iteration but lowest iteration count (program-level changes are quarterly, not per-post).

This pattern matches how `competitive` produces multi-part audit-shaped output while `linkedin_engine` produces single-post-shaped output; the agency already has architectural precedent for stratified lanes. Total surface area expands from 1 lane to 6 lanes — substantial scope expansion but tractable.

**Move 2: Per-lane fixture sets, shared exemplar substrate.** Each sibling lane needs its own fixture set (carousel fixtures ≠ text-post fixtures ≠ newsletter fixtures) but shares the exemplar substrate (the same `programs/references/voice.md` author voice file, the same Topic Authority topic pillars, the same ICP definition). The substrate becomes a shared pre-step that runs before any sibling lane evaluates a draft.

**Move 3: Iteration cadence varies by lane.** The text-post lane iterates fastest (cost per post is lowest; per-iteration value is highest because text posts are produced most frequently in production). The newsletter lane iterates monthly. The profile lane iterates once per quarter (profiles don't change weekly). The program lane iterates per-client-onboarding (single-shot at kickoff, then quarterly refreshes). This staggered cadence keeps the total iteration budget bounded while preserving evolution-loop coverage of every artifact type.

**Implication for v1 spec.** The v1 spec's locked text-post scope is correct AND should hold. The expansion happens by spinning up sibling lanes, not by expanding the v1 lane's artifact shape. The §1.5 LOCKED text-post form factor in v1 is load-bearing for the v1 lane's Goodhart resistance and should not be unlocked even after sibling lanes are stood up.

**Judge-design implications.** Each sibling lane needs its own optimal-output spec (Step 1) and its own 5-criterion judge. The criteria differ by lane:

- `linkedin_engine` (text post): LI-1..LI-5 already designed in v1 spec.
- `linkedin_carousel`: criteria likely include trailer-slide-earns-swipe, framework-coherence-across-slides, last-slide-CTA-fit, visual-hierarchy, author-context-coherence.
- `linkedin_newsletter`: criteria likely include opening-earns-the-full-read, single-insight-clarity, voice-residual, subscribe-incentive-coherence, author-context-coherence.
- `linkedin_profile`: criteria likely include headline-conversion-density, about-trailer-earns-read-more, featured-conversion-stack, banner-message-fit, recommendation-recency.
- `linkedin_comment_strategy`: criteria likely include target-account-ICP-fit, comment-template-mechanism-coherence, golden-hour-feasibility, voice-consistency-across-comments, anti-pod-pattern.
- `linkedin_program`: criteria likely include section-coherence, audit-prescription-fit, 30-60-90-actionability, topic-authority-pillar-defensibility, cross-platform-consistency.

Each sibling lane's specs would follow the same v1 structure: reader spec, artifact-shape lock, success spec, failure spec, 5 criteria (no 6th), shared wrapper. Building all 6 specs is 5–6× the v1 effort but the work amortizes across the next 12+ months of agency engagements.

**Recommendation: prioritize sibling-lane build in this order.** Phase 1: `linkedin_carousel` (highest-impact missing surface). Phase 2: `linkedin_newsletter` (highest-impact funnel mechanism). Phase 3: `linkedin_program` (highest-impact at agency-engagement-opening). Phase 4: `linkedin_profile` (lower volume but high-leverage one-time work). Phase 5: `linkedin_comment_strategy` (operator-runs-day-to-day; can be templated rather than per-client). Phases 1–5 spread across 6–12 months of judge-design work parallel to the other 7 lanes in the redesign program.

---

## §7 SOTA exemplar inventory — across the full surface

Anchoring the scope on real practitioners with documented playbooks. Note: each exemplar is anchored at a specific layer; few exemplars do all 25 activities well. The agency's job is borrowing the right move from the right exemplar.

**Profile foundation exemplars (Layer 1).**

- **Justin Welsh** (justinwelsh.me; @thejustinwelsh). Published profile-rewrite playbook. Headline: "Building 2 one-person businesses to $10M. Sharing everything I learn." Conversion-driven, outcome-explicit, no buzzwords. About paragraph opens with reader-problem, closes with newsletter signup. Featured section: 3 slots (newsletter, course, podcast). Banner image: clear visual reinforcement + CTA. The 2026 profile-rewrite anchor.
- **Lara Acosta** (lara-acosta.com). Founder of LA Digital, agency principal. Headline: "Helping creators scale to 100K+ followers." Same conversion-driven pattern. Her profile-rewrite framework is published in her SLAY methodology.
- **Sahil Bloom** (sahilbloom.com). Newsletter founder. About paragraph is masterclass in personal-brand storytelling without humblebragging.

**Single text post exemplars (Layer 2.1).**

- **Justin Welsh** — trailer-meat-CTA discipline; specific named-entity hooks; honest-disagreement-style framings.
- **Lara Acosta** — hook-rehook structure; bait-and-switch defended by substantive body.
- **Jasmin Alić** — 27 LinkedIn Writing Tips; specificity test (swap-the-named-entity); algorithm-aware structural moves.
- **Tim Denning** — 9-sentence narrative; conversational cadence; "write like you talk."
- **Ben Meer** (Growth in Reverse) — 4 story-types frame (personal pivot / business insight / client win / leadership belief).
- **Daniel Murray** (The Marketing Millennials) — agency-principal positioning; tactical insight density; debatable defensible claims.
- **Sahil Bloom** — quotable single-sentence-per-post inserts; emergent thought-leadership voice.

**Document carousel exemplars (Layer 2.2).**

- **Lara Acosta** — runs ~weekly carousels with consistent visual identity; clear framework-per-carousel structure.
- **Justin Welsh** — solo-build carousel storyboards on his "one-person business" pillar.
- **Lenny Rachitsky** — product-management carousels; data-visualization-heavy; SaaS-operator audience.
- **Adam Grant** — academic-research-summary carousels; non-business broader audience but pattern-translates.
- **Jeff Su** — productivity-framework carousels; engineering audience.

**Native video exemplars (Layer 2.3).**

- **Daniel Murray** — founder-led short-form on agency / marketing topics.
- **Gary Vee** — high-volume / multi-clip strategy (less applicable to small-to-medium clients but exemplifies the volume end).
- **Cody Wittick** — DTC operator video; short-form product-led.

**LinkedIn newsletter exemplars (Layer 2.4).**

- **Sahil Bloom — Curiosity Chronicle.** 800K+ subs; weekly long-form; canonical 2026 LinkedIn-newsletter exemplar.
- **Justin Welsh — Saturday Solopreneur.** 280K+ subs; weekly; solo-business operator focus.
- **Lenny Rachitsky — Lenny's Newsletter.** Now substack-primary but LinkedIn-native version is the canonical PM newsletter.
- **Marc Rubinstein — Net Interest.** Finance-operator long-form; smaller list, higher per-reader engagement.
- **Sebastian Raschka — Ahead of AI.** ML/AI deep-dives; researcher-IC pattern.

**LinkedIn Live exemplars (Layer 2.7).**

- **Adam Grant** — periodic Live with high-profile guests; brand-building > lead-gen.
- **Salesforce / HubSpot org-level** — Live for product announcements + customer events.

**Topic Authority exemplars (Layer 3.1).**

- **Justin Welsh** — single-topic dominance ("one-person business"); 78%+ distribution lift visible in his post performance.
- **Lara Acosta** — content-creator vertical authority.
- **Lenny Rachitsky** — product-management vertical authority.
- **Sahil Bloom** — slightly broader (curiosity / mental models / personal finance) but disciplined pillars.
- **Daniel Murray** — marketing-millennials niche authority.
- **Melanie Goodman** — published Topic Authority methodology; her own Topic-Authority-on-Topic-Authority is meta-but-real.

**Comment strategy exemplars (Layer 3.2).**

- **Lara Acosta** — built her early audience substantially through commenting on Welsh + Alić + Bloom.
- **Daniel Murray** — comments on marketing-vertical creators with substantive 50–80-word case-comparisons.
- **The "comment-first" growth pattern** is documented in Welsh's own playbook + the Buldrr.com Acosta breakdown.

**DM strategy exemplars (Layer 3.3, 3.4).**

- **Justin Welsh** — publishes his DM funnel + qualification arc.
- **Sahil Bloom** — publishes inbound DM volume + conversion arcs.
- **Lavender** (sales tooling vendor) — outbound research; 2025 State of Outbound report.

**Founder-led visibility exemplars (Layer 3.6).**

- **Brian Halligan** (HubSpot) — founder-personal-profile > company-page approach.
- **Dharmesh Shah** (HubSpot CTO) — same pattern.
- **Sahil Lavingia** (Gumroad) — DTC operator founder-led.
- **Tobi Lütke** (Shopify) — Twitter/X-primary but LinkedIn cross-syndication.

**Employee advocacy exemplars (Layer 3.7).**

- **HubSpot** — formal advocacy program; employees regularly post; brand-coherent across employees.
- **Salesforce** — same pattern at larger scale.
- **Stripe** (informal) — employees post substantively, often becoming individual thought leaders themselves.

**Funnel mechanics exemplars (Layer 4).**

- **Justin Welsh — content → newsletter → course funnel.** ~$5M ARR solo business built on this funnel.
- **Sahil Bloom — content → newsletter → investment/advisory funnel.**
- **Lara Acosta — content → DM → agency-engagement funnel.**

**Newsletter-as-list-builder exemplars (Layer 4.2).**

- **Justin Welsh — 280K LinkedIn subscribers** — substantial portion of revenue attributable to newsletter list compounding.
- **Sahil Bloom — 800K LinkedIn subscribers** — same dynamic at larger scale.

**Sales Navigator + Ads exemplars (Layer 4.3, 4.4).**

- **Lavender, Apollo, Clay** — sales-tooling vendor accounts; canonical Sales-Nav-driven outbound exemplars.
- **B2B SaaS vendor accounts** generally; Sales Navigator integration is table-stakes for B2B sales orgs.

**Analytics exemplars (Layer 5.1).**

- **Authoredup, Shield Analytics, Inlytics** — third-party analytics tools the SOTA practitioners use.
- **LinkedIn's native analytics** — adequate for most clients; third-party for cohort analysis + historical archives.

**2026 winners (full-stack exemplars across layers).**

- **Justin Welsh** — single most-cited full-stack exemplar; Layer 1 + Layer 2.1 + Layer 2.4 + Layer 3 + Layer 4 all at SOTA level.
- **Sahil Bloom** — same; slightly different audience (curiosity / mental-models vs solo-business).
- **Lara Acosta** — best agency-principal full-stack exemplar; published her playbook openly.
- **Lenny Rachitsky** — best PM-vertical full-stack exemplar.
- **Daniel Murray** — best marketing-vertical full-stack exemplar.

**Edelman/LinkedIn 2025 B2B Thought Leadership Impact Report** — the data-foundation behind every "consistent thought leadership builds trust" claim in the agency's positioning. Read in full; cite to clients.

**Melanie Goodman's Topic Authority methodology** — published in her substack + LinkedIn newsletter. Single best-documented Topic Authority playbook in 2026.

**Van Der Blom's Algorithm InSights 2025/26** — single best-documented algorithm research; used as the empirical foundation for the v1 spec's Depth Score axis.

---

## §8 Open questions

The comprehensive scope above is the agency-program target. Eight open questions remain before this expands into implementation.

**8.1 Sibling-lane prioritization order.** The §6 recommendation (carousel → newsletter → program → profile → comment-strategy) is one ordering; alternative orderings (program-first to anchor the full deliverable shape; profile-first because profile audit is the smallest scope and easiest to ship) are defensible. JR-side decision based on which lane unblocks the most agency client value.

**8.2 Per-sibling-lane judge-criteria design effort.** Each sibling lane needs its own optimal-output spec (Step 1) — comparable in effort to the v1 LinkedIn spec (~4–6 hours including research synthesis). Total: 5 specs × ~5 hours = ~25 hours of judge-design work. Plus calibration sets per lane (100 fixtures each × 5 lanes = 500 new fixtures). Substantial but bounded; need explicit prioritization vs the other 7-lane redesigns in the queue.

**8.3 Multi-lane composition coherence.** When the `linkedin_program` lane composes outputs from 5 sibling lanes into a single 11K-word deliverable, how does coherence get enforced? Naive composition concatenates 5 outputs that may have drifted internally. Options: (a) the program lane re-judges the composition for coherence; (b) the sibling lanes share a common substrate (voice.md, ICP, pillars) and coherence emerges; (c) a human-in-the-loop editorial pass at composition time. Likely (b) + (c) with (a) as a backup; needs design.

**8.4 First-cohort overfitting risk.** The §7 exemplar inventory is heavily US-skewed and tech-SaaS-skewed. Polish first-cohort clients (Klinika, DWF) operate in different vertical (Polish aesthetic dermatology + Polish legal services) with different content conventions. The 25-activity scope flexes — but the specific tactics within (timing windows, target-account lists, ICP definitions, register conventions) may not transfer. Re-validate when Polish client #3+ onboards.

**8.5 Comment-strategy lane operational tractability.** The comment-strategy lane produces a daily 15-minute commenting playbook with named target accounts. But the playbook needs to update weekly (target accounts post new content; the comment opportunities are time-sensitive). Is this a lane the evolution loop iterates on, or is it a one-time-per-client static playbook with operator daily execution? The v1-equivalent question is: does this lane have iterable per-fixture artifacts, or does it produce a single static playbook that gets refreshed quarterly?

**8.6 LinkedIn Live + collab posts in scope or out?** Both are low-volume (1 per quarter) high-effort activities. They probably don't warrant their own evolution-loop sibling lanes (per-fixture iteration value is low; production effort is high). Recommendation: scope them into the `linkedin_program` lane as operator playbook items, not as iterable artifacts. Verify.

**8.7 Sales Navigator + Ads scope.** Paid LinkedIn surface (Sales Nav for prospecting; Ads for amplification). Currently not in any judge-design scope; the agency runs these manually with client-specific config. Should they be evolution-loop lanes? Probably not — paid budget allocation is too client-specific to benefit from per-fixture iteration; static playbooks + per-engagement tuning is the right model. Document as out-of-evolution-loop scope.

**8.8 Cross-platform syndication lane.** The X→LI / blog→LI / podcast→LI translation rules in Section K of the program deliverable could be a sibling lane (`linkedin_syndication`) or could live inside the `linkedin_program` lane. Given the small per-fixture surface area (translation rules are mostly static), it probably doesn't warrant its own lane — keep in `linkedin_program`. Verify.

**8.9 Multi-language scope (Polish-specific content for Polish first-cohort).** gofreddy's first-cohort includes Polish clients (Klinika, DWF). LinkedIn content for Polish-language audiences has different register conventions, different exemplar accounts, different ICP demographics. Should the lanes be multi-language from day 1, or English-only with Polish as a v2 expansion? Likely English-first with Polish substrate (voice.md + ICP + pillars) per Polish client and operator-managed translation; Polish-native lane is a v2 scope expansion. Verify with JR.

**8.10 Time-to-value vs time-to-comprehensive-scope tradeoff.** The single-text-post v1 lane is shippable now; the full comprehensive program above takes 6–12 months of judge-design work to fully stand up. Most agency clients will pay for the program deliverable at engagement-opening (high WTP at start; degrades) — meaning shipping the program lane fast is the highest commercial-leverage move. The tradeoff: ship single-text-post lane fast and let the program emerge organically over 6–12 months, OR ship a thinner program lane sooner (Sections C + D + E + I only, ~5K words) and expand. Likely the latter; the program lane is the highest commercial-leverage missing surface.

---

## Citations

**Algorithm research (primary):**

- Van der Blom, Richard. *Algorithm InSights Report 2025/2026.* Just Connecting B.V. PDF mirror via The Loner Recruiter, October 2025: https://thelonerecruiter.com/wp-content/uploads/2025/10/Mastering-the-LinkedIn-Algorithm-in-202526-.pdf
- Meet-Lea. "LinkedIn Algorithm Explained 2026: Dwell Time, Comments." https://meet-lea.com/en/blog/linkedin-algorithm-explained
- Dataslayer. "LinkedIn Algorithm 2026: What Works Now." https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now
- Postiv AI. "Your Definitive Guide to the LinkedIn Algorithm 2026." https://postiv.ai/blog/linkedin-algorithm-2026
- LinkBoost. "LinkedIn Algorithm Changes 2026: Beat the Depth Score." https://blog.linkboost.co/linkedin-algorithm-changes-2026/
- Authoredup. "How the LinkedIn Algorithm Works in 2025 [Data-Backed Facts]." https://authoredup.com/blog/linkedin-algorithm
- Botdog. "Everything You Need To Know About LinkedIn's Algorithm In 2025." https://www.botdog.co/blog-posts/linkedin-algorithm-report
- Vulse, Stackmatix, Bang Marketing 360Brew coverage; Melanie Goodman algorithm dispatch (Substack); GBG learning lab.

**Format-performance benchmarks (2026):**

- Socialinsider. "LinkedIn Organic Benchmarks 2026." https://www.socialinsider.io/social-media-benchmarks/linkedin — 6.60% carousel engagement; 4.2% text engagement; 4.0% poll engagement.
- Metricool. "LinkedIn Trends: 6 Strategy Insights from Our 2026 Study." https://metricool.com/linkedin-trends/
- Grow with Ghost. "LinkedIn Post Formats Ranked 2026." https://www.growwithghost.io/blog/linkedin-post-formats-ranked-text-vs-carousel-vs-video-vs-polls-2026/

**B2B trust + thought-leadership data:**

- Edelman & LinkedIn. *2025 B2B Thought Leadership Impact Report.* https://www.edelman.com/expertise/Business-Marketing/2025-b2b-thought-leadership-report — 73% B2B decision-makers cite consistent thought leadership as trust signal.

**Topic Authority methodology:**

- Goodman, Melanie. Topic Authority dispatch (Substack + LinkedIn newsletter) — single best-documented Topic Authority playbook in 2026.

**Outbound + sales research:**

- Lavender. State of Outbound 2025. https://lavender.ai/state-of-outbound — outbound conversion benchmarks; warm-vs-cold differential.
- Hubspot. State of Outbound 2025.

**Practitioner playbooks (full-stack 2026 SOTA):**

- Welsh, Justin. *How to Grow on LinkedIn in 2026.* https://www.justinwelsh.me/article/linkedin-guide-2026 (profile + content + funnel + newsletter full-stack).
- Acosta, Lara. SLAY framework + LA Digital methodology. https://buldrr.com/the-acosta-linkedin-model/ (agency-principal full-stack).
- Alić, Jasmin. *27 Proven LinkedIn Writing Tips* (single text-post deep dive).
- Denning, Tim. https://timdenning.com/linkedin-language/ (text-post voice + cadence).
- Meer, Ben. Growth-in-Reverse Creator Method. https://growthinreverse.com/ben-meer/ (4-story-types frame).
- Murray, Daniel. *The Marketing Millennials.* https://growthinreverse.com/daniel-murray/ (agency-principal text-post + newsletter).
- Bloom, Sahil. *Curiosity Chronicle.* https://www.sahilbloom.com/newsletter (newsletter full-stack; 800K+ subs).
- Rachitsky, Lenny. *Lenny's Newsletter.* (PM-vertical newsletter exemplar).
- Rubinstein, Marc. *Net Interest.* (finance-operator newsletter exemplar).
- Raschka, Sebastian. *Ahead of AI.* (researcher-IC newsletter exemplar).

**AI-slop / failure-mode literature:**

- Plagiarism Today. "Em Dashes, Hyphens and Spotting AI Writing." June 2025. https://www.plagiarismtoday.com/2025/06/26/em-dashes-hyphens-and-spotting-ai-writing/
- Cybernews. "The em dash dilemma." June 2025. https://cybernews.com/editorial/linkedin-em-dash-ai/
- TechRadar. "Blade Runners of LinkedIn." https://www.techradar.com/computing/artificial-intelligence/blade-runners-of-linkedin-are-hunting-for-replicants-one-em-dash-at-a-time
- Sezer, Norton, Gino. "Humblebragging: A Distinct — and Ineffective — Self-Presentation Strategy." *Journal of Personality and Social Psychology* 2018. MIT Sloan summary.
- Mac, Ryan. "Pure Broetry." BuzzFeed News, December 2017 (broetry origin coining).
- Workweek. "Why is LinkedIn so cringe?" https://workweek.com/2022/01/15/why-is-linkedin-so-cringe/

**Comment-seed + constructive-disagreement literature:**

- WikiDisputes (arxiv 2101.10917; arxiv 2212.08353; arxiv 2411.03295) — Graham's-hierarchy reply-ladder research.
- Tan & Lee (arxiv 1805.10389) — Reddit AMA question-effectiveness research.

**Internal references (gofreddy):**

- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` — v1 optimal-output spec being expanded BEYOND.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-linkedin-engine-van-der-blom-depth.md` — Depth Score axis deep-dive.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-linkedin-engine-ai-slop-li-specific.md` — AI-slop axis deep-dive.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-linkedin-engine-author-context-coherence.md` — author-context-coherence axis deep-dive.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-linkedin-engine-comment-seed-quality.md` — comment-seed quality axis deep-dive.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/rubrics/judge-design-guide.md` v2.1 — design guide.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/x_engine/pipeline/slop_gate.py` — current LinkedIn deterministic slop floor (LINKEDIN_BANNED_PHRASES + whitespace inflation + platform-aware em-dash skip).
- Memory `Content Engine Lanes v1 PLAN` — agency lanes program; LinkedIn lane is part of the 4-new-lanes scope.
- Memory `linkedin_engine v040 cold-start mutation 2026-05-08` — cold-start handling pattern.
- Memory `Klinika + DWF first 2 onboarded clients 2026-05-12` — Polish first-cohort context.
- Memory `Don't overfit on a single client when designing the platform 2026-05-15` — generalization discipline.
