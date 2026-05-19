---
date: 2026-05-19
type: research deliverable — comprehensive scope mapping
lane: storyboard (and adjacent video workflow)
status: DRAFT v0 — surface map, NOT a plan, NOT criterion prose
parent: docs/handoffs/2026-05-18-judge-design-step1-storyboard.md
companions:
  - docs/research/2026-05-18-storyboard-creator-voice-fidelity.md
  - docs/research/2026-05-18-storyboard-ai-failure-modes.md
  - docs/research/2026-05-18-storyboard-pattern-data-cold-start.md
  - docs/research/2026-05-18-storyboard-ai-video-model-capability.md
  - docs/rubrics/judge-design-guide.md
scope_posture: Aggressive expansion. Current v1 storyboard lane scopes to "5 video story plans, 90s–8min each." Per JR direction, that is too narrow. This deliverable maps the full comprehensive surface a modern AI-native agency should encompass for a gofreddy client's video presence in 2026. Out of scope: criterion prose, implementation, v1 rescoping.
clients_assumed: SaaS / AI lab / agency / service firm / finance operator / e-commerce. US-primary. Poland first-cohort (Klinika + DWF) acknowledged but not architectural target.
---

# Storyboard — Comprehensive Scope Map (2026)

A modern AI-native marketing agency in 2026 cannot ship a "5 video story plans" deliverable and call it a video workflow. Video is the dominant on-ramp to attention for every gofreddy client archetype (founder visibility for SaaS/AI; thought-leadership for service firms; product education for e-commerce; founder-led trust for finance and aesthetics). The current v1 storyboard lane is structurally a single shelf inside a 20-shelf store.

This document maps the full surface. It does not propose criterion prose, does not reduce v1, does not pick which surfaces ship first. It exists so the storyboard-lane planning conversation can see what it's currently not covering before any v2 / v3 scope decisions get made.

---

## TL;DR

**The current v1 storyboard lane ships ~10% of what a 2026 client needs from their video workflow.** It produces 5 plans (90s–8min) and stops at the page — a script-shop deliverable. 2026 demands a coordinated portfolio across roughly 20 axes spanning strategy, production, distribution, community, and measurement, all of which compound or undermine each other if treated in isolation.

Six framing claims:

1. **Distribution is the production constraint, not the production output.** Plans authored without platform-native distribution cuts pre-specified yield the "horizontal 16:9 hero plus 8 weak shorts" pattern that defines AI-slop content marketing in 2026. Cuts must be primary artifacts, not post-hoc extractions.
2. **Founder-led on-camera beats AI-generated talking-head in 2026, full stop.** YouTube's January 2026 Mohan letter and the Kapwing 278-AI-slop-channels report ($117M ad revenue at bottom-tier CPM) confirmed the algorithmic posture: AI-only downranked; founder-led-with-AI-augmentation is the only path with social proof.
3. **Thumbnail and title strategy drive ~30–60% of CTR variance** (Veritasium / MrBeast / Boucher analytics blogs converge across 2024–2026 retrospectives). A great script with a generic thumbnail loses to a competent script with a category-killer thumbnail. The lane currently produces zero thumbnail artifacts.
4. **Series arc, not single video, is the unit of audience growth.** MrBeast handbook explicit; Cleo Abram, Modern Wisdom, Lex Fridman, Logan Ury all series-shaped. Single videos isolated from a series have worse retention, lower CTR, zero downstream pull. The lane must plan in arc-units of 4–12 videos, not 5 standalone plans.
5. **Comment management is a real workflow.** First-60-min engagement velocity correlates with reach more strongly in 2026 than in any prior year per TikTok and YouTube Shorts published creator guides. Pinned comments, first-30-min replies, comment-magnet engineering at script stage are first-class deliverables.
6. **AI-video-model selection is a per-scene routing decision, not a per-plan declaration.** The May 2026 fleet (Veo 4, Runway Gen-4.5, Kling 3.0, Luma Ray 3, Pika 2.5) has overlapping but non-identical envelopes — a 3-min piece typically routes 3–5 different models across scenes.

The expansion is not "do more plans." It's: turn the lane into a video-program workflow owning ~20 axes coordinated around series arcs, distributing across platforms natively, augmenting founder-led on-camera with AI-video where capability allows, and instrumenting against modern engagement realities.

---

## §1 — Full Surface Mapping (20+ Axes)

These are independent value-bearing axes a modern video workflow needs to make decisions on. Each one a real client either has handled (well or badly) or is leaving on the table.

### 1.1 — Video content strategy (the macro layer)

**Cadence.** How often. 2026 norms: YouTube 1–2/wk for sub-100k channels growing, 3–5/wk for established; Shorts/Reels 1–2/day for active growth; LinkedIn video 2–4/wk for B2B founder visibility; TikTok 1–3/day for serious channel growth. Cadence determines staffing, AI-augmentation ratio, burnout risk. v1: silent.

**Format mix.** Talking-head / cinematic / AI-generated / documentary / interview / reaction / educational explainer / montage / vlog. Modern creator portfolios are deliberate mixes where the mix itself is part of the brand (Cleo Abram = explainer + documentary; Lex Fridman = interview + monologue intros; MrBeast = cinematic + reaction + stunt). v1 doesn't plan one.

**Distribution mix.** YouTube long-form / YouTube Shorts / TikTok / Reels / LinkedIn video / X video / podcast-as-video (Spotify, Apple, YT) / newsletter-embed / website-embed. Each platform has different optimal duration, aspect ratio, hook style, retention curve, comment culture.

**Series arc.** A 4–12 video commitment around one premise that compounds week over week (Cleo's "Huge If True"; Modern Wisdom's weekly interview cadence; Johnny Harris's per-topic deep-dives; MrBeast's $1 → $100k → $1M escalating-stakes sequences). Without it, individual videos don't compound.

**Audience plan.** Who the content is *for* (avatar specificity). Hank Green's "I write for my brother John" is the canonical formulation. For SaaS founders: peer-positioning vs lead-positioning vs recruiting-positioning — different content. v1: silent.

### 1.2 — Video story plans / scripts / storyboards (current v1 focus)

This is what v1 currently produces. 5 plans, 90s–8min, voice-script + scene list + declared rendering model + citation list + pattern-data anchor references. Scoped well per the existing four-axis research (voice fidelity, AI failure modes, cold-start, model capability). The criticism: this is ~10% of the surface, not 100%.

### 1.3 — Hook ladder testing + first-3-sec arc design

OpusClip / TikTok / YouTube Shorts published creator guides 2026 converge: the first 3 seconds determine 60–80% of completion-rate variance for short-form. The first 8 seconds determine the same for long-form (MrBeast handbook is explicit; Veritasium has discussed in interviews). A modern workflow does not produce one hook per video — it produces a hook ladder (3–5 alternative hooks per video, tested in soft-publishes on Shorts/Reels, with the winner promoted to the long-form lead-in).

**The hook ladder as a first-class artifact.** For each video plan, the lane should produce 3–5 hook variants spanning different mechanisms (declarative-imperative, question-as-thesis, sensory-scene, stat-led, tension-first, raw-vulnerability, absurd-juxtaposition). Test cheaply on platforms with high distribution and forgiving cycle times (TikTok, Shorts). Winning hook drives the long-form publish.

**First-8-second beat-by-beat.** The lane should produce a frame-level (or near-frame-level) beat sheet for the opening 8 seconds. What's on screen at 0:00, 0:01, 0:02, 0:03, 0:05, 0:08. What's the cut count. What's the audio. What's the b-roll. What's the on-screen text. This is the highest-leverage 8 seconds in any video and currently it's underspecified at the plan stage.

### 1.4 — Title + thumbnail strategy (drives 30–60% CTR variance)

**Title as a separate craft.** Veritasium's 3-title A/B is well documented; MrBeast handbook describes title-craft as its own workflow with its own team. Title skills: front-loading specificity, curiosity-gap-without-clickbait, contrastive framing, numeric anchoring, named-entity inclusion, removing throat-clearing words.

**Thumbnail (highest-leverage single artifact in the workflow).** MrBeast handbook: "thumbnails are more important than titles which are more important than the video." Still empirically true at the CTR layer in 2026. Craft: high-contrast face expression, single subject clarity, < 3 elements on screen, color-saturation tuning, text legibility at mobile-thumb-size, A/B across 2–4 variants. Channels that invest in thumbnail iteration (Veritasium, Logan Ury, MKBHD, MrBeast, ColinAndSamir) consistently outperform same-size peers.

**Biggest single lane gap.** A v2 lane should produce 2–4 thumbnail concept directions per video (composition + facial expression + props + text + color palette), one title variant per thumbnail (paired), and optionally generated mockups via Nano Banana Pro / Gemini Imagegen / GPT-4o image / Flux for client review.

### 1.5 — Description + tag optimization

YouTube descriptions still drive SEO in 2026 (per the YouTube Creator Insider channel and the 2025–2026 creator strategist consensus). First 150 characters before the "more" fold are highest-leverage. Tag relevance for the algorithm matters less than it did in 2018 but the algorithm still uses description text for topic disambiguation. Pinned comment is a description extension (most under-used surface in 2026 — Veritasium and Logan Ury both use this aggressively).

For non-YouTube platforms: TikTok caption / Reels caption is the entire description. LinkedIn description is a separate craft (LinkedIn rewards 3-line hooks followed by a "see more" expand). X description is the entire post. Each platform has its own description craft.

**Lane gap:** description and pinned-comment are not in v1.

### 1.6 — Voiceover artist selection + AI voice

For founder-led content the founder IS the voice. For non-founder-led pieces (SaaS documentary series, fintech explainer, agency case study) the voice is either a hired VO (Voices.com, Backstage, Voquent) or AI voice (ElevenLabs v3 Conversational, Hume EVI 3, Resemble, PlayHT). 2026 state: ElevenLabs v3 / Hume EVI 3 indistinguishable from human in blind tests for 30–90s segments; 3+ min monologue still drifts prosodically. AI voice is faster and cheaper but does not build the personal brand the way founder-led-on-camera does. **Lane gap:** voice modality is not a declared field in v1.

### 1.7 — Music + sound design + mix budget

Audio is the most under-credited retention variable. Modern Wisdom's audio mix is part of the brand; Cleo Abram has discussed her audio team as load-bearing; Casey Neistat's hip-hop-cut-plus-ambient-pad scoring has been studied. 2026 tools: Suno v4 / Udio v3 / Eleven Music produce broadcast-grade music in 2–8 minute pieces; royalty-free libraries (Artlist, Epidemic, Musicbed) still dominate brand-safe workflows; sound effects via Soundstripe / Pro Sound Effects / ElevenLabs Sound Effects. **Lane gap:** music direction (mood / BPM / instrumentation / structural relationship to scene-beats) not in v1.

### 1.8 — Distribution plan (the multi-platform native cuts problem)

**1-long-form → 8-short-form rule.** Modern workflow produces one long-form anchor (8–25 min YT or podcast) and 6–12 platform-native short-form derivatives — not re-aspect-ratio re-exports.

Platform-native means:
- **YT main** (16:9, 8–25 min): title + thumbnail driven; description + chapters + pinned comment.
- **YT Shorts** (9:16, ≤60s): hook in first 1s; auto-loop bait; high-density subtitle.
- **TikTok** (9:16, 9–90s): native audio matters; rewards "build-up to payoff" more than Shorts' "payoff first."
- **IG Reels** (9:16, 15–60s): cover frame + music selection drive discovery.
- **LinkedIn video** (square or 9:16, ≤2:30 for B2B founder): native captions (sound-off audience); hook in first 3s; document-style stills sometimes outperform.
- **X video** (16:9 or 9:16, ≤2:20): quote-tweet bait; thread-friendly cuts each standing alone.
- **Podcast video** (16:9, full ep + cuts): Spotify Video / YT podcast / Apple Podcasts video — long-form, less editing.

v1 treats distribution as downstream. That's the architectural mistake; distribution must be designed at plan stage.

### 1.9 — Cross-platform repurposing rules

For each long-form anchor the workflow specifies: which 90-sec segments become Shorts/Reels/TikTok; which 30-sec become quote-cards / X clips; which still frames become LinkedIn carousel slides; which transcript paragraphs become a newsletter section; which key claim becomes a tweet-thread; which audio segments become a podcast clip. The repurposing map is a lane deliverable.

### 1.10 — Comment management + community strategy

**First-60-min engagement velocity drives reach.** TikTok and YouTube Shorts both published creator guides in 2025–2026 confirming first-hour engagement signal is heavily weighted. Implication: founder/team replies to first 10–20 comments in first 30 minutes; pinned comment selected pre-publish; reply strategy pre-written for likely comment categories.

**Comment-magnet engineering at script stage.** The script engineers a comment-magnet (unanswered question at the end, controversial-but-defensible take, specific call for story from viewers). MrBeast handbook discusses this; Logan Ury consistently ends with a specific question; Casey Neistat plants the controversial seed in the body, not just the outro.

**Heart / pin / reply / engage as a workflow.** Per-video checklist: which comments get hearted / pinned / founder-replied / boosted. Currently silent in the lane.

### 1.11 — Series-arc planning (multi-video story across weeks)

A 4–12 video series sharing one premise, one audience, one visual signature, with each video building on or recontextualizing prior ones. Cleo Abram's "Huge If True," Modern Wisdom's question-of-the-week, MrBeast's "I Survived X," Johnny Harris's per-region deep-dives all series-shaped.

A series arc has: premise frame across N videos, title-naming convention (Episode N: [hook]), thumbnail visual signature (same font/color/character treatment), inter-video callback structure (Ep 3 callbacks Ep 1), audience commitment ramp (Ep 1 introduces; Ep 5 deepens; Ep 12 pays off), measurement frame across the arc. **v1: silent.** The 5 plans are independent bets, not a series.

### 1.12 — Cross-creator collaboration plan

Collabs are the highest-leverage growth lever in 2026 (Logan Ury / Modern Wisdom / Cleo Abram have all publicly attributed growth to collab strategies). The workflow should produce collab targets per series-arc:
- 3–5 named creators to approach for guest appearances, interview slots, cross-promos
- Outreach scripts for each
- Reciprocal-value offer (what you give them in exchange)
- Specific episode/slot positioning

Founder-led clients benefit specifically from podcast-tour strategies — a founder appearing on 8–12 mid-tier podcasts over 3 months generates more durable inbound than 8–12 paid ad placements.

**Current v1: silent.**

### 1.13 — Sponsorship integration

Two cases: (a) the founder is the sponsor (i.e., the SaaS company sponsoring its own creator content as inbound marketing), (b) the founder is sponsored (revenue strand for creator-led clients).

For (a), the sponsorship integration is the entire workflow. The product placement / demo / mention has to feel native, has to land in the right beat, has to convert at meaningful rates.

For (b) — relevant if any gofreddy client takes external sponsorship — the integration calculus is more complex (sponsorship-fit screening, brand-safe handling, ad-read placement at 30–50% mark per modern attention research, native-style "this video sponsored by" disclosure).

**Lane gap:** sponsorship slot specification per video — not currently in v1.

### 1.14 — AI-video model selection per scene

Covered exhaustively in `docs/research/2026-05-18-storyboard-ai-video-model-capability.md`. Implication for scope: per-scene routing (not per-plan declaration) is production reality — a 3-min piece routes Kling 3.0 for multi-shot continuity, Luma Ray 3 for cinematic crane shots, Pika 2.5 for closing reaction beats, Runway Gen-4.5 for emotion-on-face holds. Lane should produce a scene-level routing table; v1 doesn't.

### 1.15 — Talking-head / cinematic / AI-generated mix

Per video, declare fractions across: founder talking-head (highest-trust), cinematic b-roll (production-value frame; live-shot or AI-generated), AI-generated narrative scenes (cost-efficient explainer), stock footage (workmanlike, avoided in 2026 for slop-flagging risk), on-screen text / graphics / motion design (explainer-overlay), documentary footage (high-trust real-world). Mix is strategic — a 60s Reel might be 80% talking-head + 20% on-screen text; an 8-min explainer might be 30% talking-head + 40% cinematic b-roll + 20% motion graphics + 10% AI-generated. Lane needs a per-video mix declaration.

### 1.16 — On-camera coaching for founder

This is the surface gofreddy has the most strategic interest in *for B2B founder-led clients* (SaaS, AI, agency, finance). Founders almost universally start on-camera bad. The coaching ramp:
- Posture / framing / lighting setup (typical first-month deliverables)
- Voice projection / pace / breath (typical month-2)
- Authenticity vs polish calibration (ongoing)
- Energy management for multi-take days (ongoing)
- Specific scripts for repeat-shoot scenarios (founder Q&A, customer testimonial intro, etc.)

A modern workflow includes a coaching brief per founder, refreshed quarterly, integrated with the plan deliverable. Some agencies (Modern Wisdom's production process, ColinAndSamir's consulting practice) treat coaching as their primary deliverable for founder-led clients.

### 1.17 — Founder-led visibility plan via video

For SaaS / AI / agency / service / finance: the founder *is* the brand in 2026. Logan Ury, Lenny Rachitsky, Patrick Campbell, Lex Fridman, Chris Williamson — every B2B-adjacent breakout in 2024–2026 is founder-led with video as primary surface.

The visibility plan integrates: long-form interviews (Lex/Lenny model) 1–2/month; short-form thought-leadership clips (LinkedIn / X / Reels) 3–5/wk; series-arc deep-dives quarterly; podcast tour (8–12 guest appearances per 3 months) quarterly; live appearances (conference talks, panel moments, AMA livestreams) monthly+. Dominant client need for listed verticals. v1: silent.

### 1.18 — Live video (YT Live, IG Live, TikTok Live, X Spaces)

Live differs from recorded: higher engagement multiplier (1–4× recorded), comment-driven, mistakes-are-features, lower production cost, higher founder-time cost. A 2026 founder-led plan should include live cadence (monthly AMA, weekly office-hours, quarterly virtual conference). Lane should produce live-stream prep briefs (talking points, expected questions, comment-management plan), not full scripts. v1: silent.

### 1.19 — Vertical-first short-form (Shorts/Reels/TikTok) vs horizontal long-form

A 2026 strategic decision: which direction is primary? Some clients are vertical-first (a B2C aesthetic clinic, an early-stage e-commerce, a personal-brand founder). Some are horizontal-first (a documentary-style explainer brand, a long-form podcast). Most are both.

The lane should specify which mode each piece is in and design accordingly — vertical-first design has different hook style, different camera framing, different audio strategy.

### 1.20 — Closed captions + accessibility

Required (not optional) on: LinkedIn (sound-off-by-default), TikTok / Reels / Shorts (subtitle-trend mandatory). Caption style itself is a brand signature in 2026 (MrBeast red-yellow-white burned-in, Cleo Abram clean sans-serif, Modern Wisdom branded font). Accessibility extends to: audio-description tracks, transcript-as-text-asset for SEO + screen readers, contrast ratios in on-screen graphics. **Lane gap:** caption style spec is not currently a deliverable.

### 1.21 — Multilingual / dubbing strategy

Polish first-cohort (Klinika, DWF) targets Polish-language. Polish founder + English customer base (common B2B SaaS shape) → bilingual native PL + dubbed EN. 2026 tools: HeyGen (avatar dubbing), Eleven Labs (voice-clone dubbing), Submagic (subtitle-translate), Captions.ai. Eleven Labs voice-clone PL→EN is broadcast-grade in 2026; lip-sync is the weak point. US-primary clients: ES for LATAM, PT-BR for Brazil, sometimes JP for tech-adjacent.

### 1.22 — Analytics + measurement

Per-video metrics tracked: CTR; AVD + AVD-ratio; 30-sec hold; comment-velocity (per 1k views in first 24h); like-velocity; share-velocity (highest correlation with reach in 2026 per multiple platform-published creator guides); subscriber-add per video; revenue attribution; cross-platform repurpose performance. Measurement loops back into the next plan. Lane should produce a measurement frame per series-arc with retrospective-update cadence (e.g., week-4 retro on first 4 eps drives ep 5 plan).

### 1.23 — Audience-building → email list integration

Video drives subscribers; the long-term moat is an owned channel (email + RSS + push). Every founder-led client in 2026 should be converting video viewers to email subscribers at a measurable rate. Conversions happen via:
- End-card CTAs ("subscribe to the newsletter")
- Pinned comment with newsletter link
- Lead-magnet specific to the video topic
- Course / community offering

The plan should specify the CTA target per video and the lead-magnet variant.

### 1.24 — Monetization integration (YT Partner, sponsorships, lead gen)

Long-term: most founder-led B2B content monetizes via lead-gen (inbound demos for SaaS, consultations for service firms, qualified inquiries for finance). YouTube Partner Program ad revenue is small relative to lead-gen for B2B; large relative to lead-gen for B2C / creator-led.

The lane should specify the monetization mode per video / per series, and design CTAs accordingly.

### 1.25 — 2026 platform-specific tactics

Tactics rotate. Current state (Q2 2026):
- **YouTube**: Shorts + long-form converging; Shorts feed into long-form watch-time. Pinned comment + chapter markers under-used. "Pay-per-view" rolling out for select creators.
- **TikTok**: STEM-content monetization launch Q1 2026 rewards educational creators. CapCut Templates auto-discovery favors trending audio. Live shopping (Shopify integration) expanding.
- **Instagram Reels**: Edits app (Adobe-acquired) integrated as native editing surface. Music library expanded for commercial accounts.
- **LinkedIn**: Native video reach up ~3x YoY per LinkedIn's own creator-economy report. Document-style PDF carousel still outperforms most video for B2B SaaS.
- **X**: Premium subscriber video reach inflated vs free; long-form (>20min) ad-rev-share favors creators.
- **Podcasts**: Spotify Video integration drove ~40% lift in video-podcast subs for top shows. Apple Podcasts video lagging.

The lane should know these tactics and bias designs quarter-over-quarter.

---

## §2 — CUTS: Old-School / Slop Patterns to Reject

These are the patterns a 2026 AI-native agency must **not** ship. Many are still default-mode for AI-generated video workflows. All of them are reasons clients eventually fire their content agency.

1. **Talking-head-only.** Founder reading a script directly to camera, no b-roll, no motion, no graphics. Worked in 2018; 2026 algorithm + audience both downrank. Talking-head is a *frame* (highest-trust), not a *format*.
2. **Generic AI-explainer with "Here's the thing" / "Stop X. Start Y." voiceover.** The Kapwing 278-AI-slop-channels analysis catalogued exactly this pattern (ElevenLabs default voice + Pexels stock + ChatGPT copy + "moreover/furthermore/in conclusion"). Bottom-tier CPM; reputation-destroying for B2B.
3. **Motivational montage with stock music.** Inspirational VO + Pexels stock + Epidemic uplift. Inflates production-value-illusion for a week; degrades brand for a year. Still defaulted to by lazy shops.
4. **Hook-formula slot-fill across the portfolio.** All 5 plans open with "What if I told you..." OR "Stop doing X." OR "I tried X for 30 days." AI-failure-modes research mode #4. Cut at script stage.
5. **5 plans, same premise, different garnish.** v1 spec's Mediocre mode 3.
6. **Plan with no thumbnail / title / distribution craft.** Stopping at script + scene list is a 2015 deliverable. No thumbnail = no CTR strategy.
7. **One-video-fits-all-platforms.** Horizontal long-form chopped post-hoc into Shorts/Reels/TikTok yields the slop pattern. Each platform needs native design from plan stage.
8. **Cinematic AI-generated brand film with no founder presence.** Nike-style 60s entirely in Veo 4 + Runway. Looks impressive; converts near-zero for B2B. Founder absence kills trust in founder-led-business case.
9. **"Subscribe and ring the bell" CTAs.** Generic CTAs generate near-zero conversion. Specific CTAs ("comment if you've ever shipped a 3am hotfix" / "join 8k SaaS founders on the newsletter") work.
10. **Episode-as-standalone.** Video N without explicit relationship to N-1 and N+1 leaves audience-building on the table.
11. **No measurement loop.** Open-loop content gets worse over time.
12. **Generic-creator-voice in the founder's mouth.** Per voice-fidelity research, the "high-entropy YouTube essay neutral" register with the founder's name attached. Founder shoots it, feels like they're cosplaying themselves; audience can tell.
13. **"5 video story plans" as a finished product.** The current v1 lane unit, treated as the final deliverable, is itself a cut. A script-shop deliverable from 2018. 2026 demands the full video-program deliverable.
14. **Anti-platform tactics.** Horizontal content on TikTok without subtitles; LinkedIn >2:30 without strong hook; X video with no captions; YouTube without chapter markers. "We'll fix it in post" thinking — and it never gets fixed.

---

## §3 — ADDS: Modern Levers To Bake In

Default-on levers for a 2026 AI-native agency:

1. **Founder-led on-camera as the primary frame** for SaaS / AI / agency / service / finance. Coaching brief + lighting kit + 60s-Reel cadence + monthly long-form interview is the MVP founder visibility plan.
2. **Irreplaceable hooks** (SB-2 substitution test) as script-stage default — extended across all hook ladder variants.
3. **Modern creator pacing per platform.** TikTok 0.5–2.0s cuts (density-high); YouTube long-form 2.5–4.5s (medium); LinkedIn 3.0–5.0s (low — sound-off audience reads captions).
4. **AI-video augmented, not AI-video led.** Founder talking-head + AI-generated b-roll cutaways is the modern default; pure AI-generated video downranks.
5. **Cross-platform native cuts as primary artifacts** designed at plan stage, not extracted post-hoc.
6. **Series-arc storytelling as the unit** — 4–12 video arcs with premise + callbacks + audience commitment ramp.
7. **Comment-magnet engineering at script stage** — script plants the comment seed; workflow handles first-hour reply velocity.
8. **Thumbnail + title workflow** — 2–4 variants per video with explicit A/B.
9. **First-8-seconds frame-by-frame** specification.
10. **Hook ladder** — 3–5 hooks per video, tested cheaply on Shorts/Reels first.
11. **On-camera coaching brief** refreshed quarterly per founder.
12. **Live cadence** (monthly AMA, weekly office-hours, quarterly virtual conference).
13. **Distribution map per long-form anchor** (1 long → 6–12 native derivatives).
14. **Per-scene AI-video model routing** across current fleet.
15. **Measurement loop with explicit retrospective cadence** (week-4 retro drives episode 5 plan).
16. **Caption-style as brand signature** — burned-in style is part of brand identity, not post-production afterthought.
17. **Multilingual dub strategy** where audience warrants.
18. **Sponsorship slot pre-planned** (client-as-sponsor or client-takes-sponsor).
19. **Email-list integration** via end-cards + pinned-comment + lead-magnets.
20. **Quarterly tactics refresh** — platform tactics rotate; workflow tracks them.

---

## §4 — Vertical Adjustments

The verticals gofreddy serves have meaningfully different video-workflow shapes. The lane should know these.

### 4.1 — SaaS founder
**Frame:** founder-led thought-leadership + product education hybrid. **Mix:** 60-sec LinkedIn/X clips (3–5/wk) + monthly long-form podcast/video interview + quarterly series-arc deep-dives ("How we built X" 6-episode). **Distribution:** LinkedIn primary, YouTube secondary, X tertiary; podcast very high-leverage for B2B. **Length:** short 30–90s; long 30–60 min. **Voice:** founder, brand-author-mode. **Measurement:** demos-booked / MQL per 1k views. Lead-gen dominant. **References:** Lenny Rachitsky, Patrick Campbell, Aakash Gupta, Ben Lang, Logan Bartlett, Harry Stebbings, Pat Walls.

### 4.2 — AI lab researcher / startup
**Frame:** technical authority + research demonstration. **Mix:** demo videos (Anthropic / OpenAI / DeepMind use these as primary trust-builders), founder interviews, technical explainers. **Distribution:** X primary (AI-twitter), YouTube secondary, LinkedIn for talent, podcast guesting heavy. **Length:** demos 2–8 min, interviews 60–120 min, explainers 5–15 min. **Voice:** technical-precise, low-hype. **Measurement:** GitHub stars, X follows, recruiting inbound. **References:** Andrej Karpathy, Yannic Kilcher, Lex Fridman (interview), Sebastian Raschka, AI Explained.

### 4.3 — Agency principal
**Frame:** craft-demonstration + thought-leadership + founder-positioning. **Mix:** case-study videos (low-cadence, high-stakes), founder vlog (medium), industry-commentary (high). **Distribution:** LinkedIn primary, YouTube secondary; TikTok for creative-led agencies; podcast guesting for awareness. **Length:** case studies 3–8 min; vlogs 5–12 min; commentary 60–90s. **Voice:** confident, opinionated, craft-aware. **Measurement:** inbound RFPs, hire-quality, peer-recognition. **References:** ColinAndSamir, Casey Neistat, Chris Williamson (Modern Wisdom).

### 4.4 — Service firm partner (legal / consulting / finance services)
**Frame:** authority + trust. Less personal-brand than SaaS; more institutional. **Mix:** explainers (regulatory updates, client education), partner commentary, case-summary reaction videos. **Distribution:** LinkedIn primary, firm-website-hosted secondary, YouTube tertiary. **Length:** explainers 3–8 min; commentary 60–180s. **Voice:** authoritative, precise, conservative. **Measurement:** RFP quality, brand-recall, lateral-recruiting interest. **References:** few clean exemplars in 2026 — most service firms still in basic talking-head era. DWF case is representative here.

### 4.5 — Finance operator (wealth management, fund manager, fintech founder)
**Frame:** thesis-led commentary + market-moment analysis. **Mix:** weekly market commentary (Patrick Boyle model), thesis essays in video form, founder Q&A. **Distribution:** YouTube primary, podcast strong, X primary for real-time. **Length:** market commentary 8–15 min; thesis essays 15–45 min. **Voice:** measured, authoritative, contrarian-defensible. **Measurement:** subscriber LTV, fund inflows, app installs. **References:** Patrick Boyle, Aswath Damodaran, Lyn Alden, Plain Bagel, Joseph Carlson, Howard Marks.

### 4.6 — E-commerce operator
**Frame:** product-demonstration + founder-story + customer-testimonial. **Mix:** product demo (high-cadence, short-form), founder vlog (medium), UGC-style content (curated and reshared). **Distribution:** TikTok + Reels primary, YouTube Shorts strong, YouTube long-form tertiary; live shopping (TikTok Shop, IG Shop) increasingly central. **Length:** demos 15–60s; vlogs 2–5 min; live 30+ min. **Voice:** energetic, specific, conversion-aware. **Measurement:** ROAS, conv-rate-per-video, AOV-per-source. **References:** Steven Bartlett, Daniel Vassallo, Three Ships Beauty founders, Ali Abdaal-style.

### 4.7 — Cross-cutting: archetype overlays

Beyond vertical, the lane should know the client archetype:
- **Creator-led** — content IS the business (sponsorships, ads, course sales).
- **Brand-author** — content is operated by a commissioning entity (in-house lead, agency).
- **Founder-led business** — content represents the business; founder is the face. **This is the dominant gofreddy case.**

The first-cohort framing (Klinika, DWF, B2B SaaS founder) maps to founder-led business archetype. Most US-primary gofreddy clients will also be founder-led business. Creator-led is a stretch case; brand-author is occasional.

---

## §5 — Deliverable Architecture (size envelope + multi-part structure)

What a comprehensive 2026 storyboard / video-workflow deliverable for a gofreddy client looks like. This is the full v∞ shape; v2/v3 implementations would phase in subsets.

### 5.1 — Component deliverables

1. **Video content audit (refresh quarterly).** Channel state across all platforms (subs, engagement, retention, top/bottom performers); voice + positioning current state; audience composition; format-mix analysis; gap analysis vs reference creators in same vertical.

2. **Cut / Reduce / Add prescription.** Specific to client's current state — aligned to §2 / §3.

3. **Channel positioning + voice plan.** Single-source-of-truth voice document derived from founder's published anchor. Reader avatar spec. Brand signature (caption style, thumbnail aesthetic, music palette, color).

4. **Content strategy (pillars + cadence + platform mix).** 3–5 content pillars; cadence and format mix per pillar per platform.

5. **N video story plans across platforms.** The existing v1 lane unit — but embedded inside the larger deliverable, not the deliverable itself. Scope to 8–15 per quarter rather than 5 one-time.

6. **Thumbnail + title strategy + samples.** 2–4 thumbnail concept directions per video; generated mockups; A/B testing framework.

7. **Distribution rules across platforms.** Per-plan: where it goes, what cuts get made, aspect ratios, caption styles, CTAs.

8. **Series-arc plan for first month / first quarter.** 4–12 video arc with premise, callbacks, ramp, measurement frame.

9. **Sponsorship integration plan.** Sponsored slots (client-as-sponsor or client-takes-sponsor), disclosures, conversion measurement.

10. **AI-video-model selection guide per scene.** Per-scene routing across the current fleet (Veo 4, Runway Gen-4.5, Kling 3.0, Luma Ray 3, Pika 2.5). Fallbacks. Budget envelope per scene.

11. **On-camera coaching brief for founder.** Posture / framing / lighting kit; voice / pace / breath drills; authenticity-vs-polish calibration. Refresh quarterly.

12. **Comment management playbook.** Pinned comment patterns; first-hour reply velocity targets; comment-magnet engineering at script stage; heart/pin/reply/engage workflow.

13. **Hook ladder per video.** 3–5 hook variants across mechanism types; soft-publish protocol on Shorts/Reels.

14. **First-8-seconds beat-by-beat.** Frame-level specification for the highest-leverage opening of each video.

15. **Music + sound direction per video.** Mood / BPM / instrumentation / structural relationship to scene-beats.

16. **Voiceover modality declaration.** Founder-led / hired-VO / AI-voice (with model + prompt).

17. **Multilingual / dubbing strategy.** Per-video dub target (if any).

18. **Live cadence plan.** Monthly AMA / weekly office-hours / quarterly virtual conference framework.

19. **Cross-creator collaboration plan.** 3–5 named targets per quarter; outreach scripts; reciprocal-value offers.

20. **30/60/90 execution roadmap.** Days 1–30, 31–60, 61–90 with staffing and tooling implications.

21. **Measurement frame + retrospective cadence.** Per-video metrics; series-arc retro at week 4; quarterly content audit refresh.

22. **Audience-building integration.** Email-list CTAs; topic-specific lead-magnets; newsletter cadence.

23. **Monetization integration.** Per-platform monetization mode; CTA design per video.

24. **Quarterly platform-tactics refresh.** What's new; what to bias toward.

### 5.2 — Size envelope

A comprehensive deliverable for a single founder-led business client in 2026 is roughly 60–150 pages (depending on size of video story portfolio inside it) at the planning level — plus N video story plans (currently scoped 5 in v1, should be 8–15) — plus a continuously updated execution layer (cadence calendar, retrospective journal, performance dashboard).

This is not a one-document deliverable. It's a structured workspace.

### 5.3 — Multi-part structure

A reasonable decomposition (not the only one):

- **Part A — Strategy** (one-time, refresh quarterly): channel positioning, voice plan, content strategy, series-arc plan, distribution rules.
- **Part B — Production** (per video): story plan + hook ladder + first-8-sec beat sheet + thumbnail direction + title variants + scene-list with model routing + distribution-cut map + music direction + caption style.
- **Part C — Distribution & community** (per video): pinned comment + reply playbook + cross-promo schedule + email-CTA + measurement frame.
- **Part D — Coaching & growth** (continuous): on-camera coaching brief refreshed quarterly + collab pipeline + live cadence + audit retrospective + tactics refresh.

The v1 lane fits inside Part B's first item (story plan) but doesn't touch Parts A, C, D.

---

## §6 — Evolution-Loop Considerations

As lane scope expands, the evolution loop has to evolve too. Practical considerations:

**6.1 — Per-axis vs whole-deliverable scoring.** With 20+ axes, holistic scoring is a non-starter (design guide §5 on per-criterion isolation + ≤5 ceiling). Likely structure: one judge call per axis (or per axis-cluster), each a narrow 3–5-criterion rubric. Storyboard becomes ~5–8 sub-lanes, not one lane.

**6.2 — Cross-axis consistency as meta-criterion.** A series-arc plan strong individually may be inconsistent across episodes; a thumbnail strong individually may not match the voice-script tone. Meta-consistency criteria across sub-lanes would be a new pattern.

**6.3 — First-cohort fixtures need expansion.** Klinika + DWF + B2B SaaS founder too narrow for 20+-axis lane. Need creator-led, e-commerce, finance, AI-lab additions. Per cold-start research §5, cohort-pooling failure mode gets worse as lane gets wider — distinctive emergent voices penalized harder.

**6.4 — Capability-aware evolution.** AI-video fleet rotates quarterly. Structural_gate config for supported models needs evolution-loop refresh — possibly a separate fleet-tracker sub-lane running monthly.

**6.5 — Outer judge cost ceiling.** 5–8 sub-lane judges × per-fixture × per-generation multiplies cost. At 50 gen × 5 fixtures × 8 sub-lanes × ~$0.30/call = ~$600/run. Manageable; cost-aware sub-lane selection (full panel only on promotion candidates, cheap-screen on most variants) is a likely architecture.

**6.6 — Holdout discipline holds.** Per memory `project-stream-a-shipping-2026-05-11`, holdout-vs-train discipline must be preserved across the expanded surface — easy to leak when 20+ axes are in play. Each sub-lane's holdout split must be independent.

**6.7 — Goodhart surface multiplies.** Each axis has its own Goodhart-collapse mode. Phase 4 pathology at HEAD `c76f051` is one example; 20+ axes means 20+ pathology surfaces. The discipline that worked for 5 criteria (outcome questions, structural_gate routing, binary anchors) extends but surface area is much larger.

**6.8 — Evolution target shifts from "script quality" to "program quality."** A workflow evolved to produce excellent scripts is not the same workflow as one evolved to produce coherent series arcs. Selection pressure has to be set at program level for the program to compound.

---

## §7 — SOTA Exemplars (real channels, real data, 2026 winners)

These are the channels and creators a 2026 video workflow should benchmark against. Each has a measurable, observable pattern that has worked in 2024–2026.

### 7.1 — MrBeast — cross-form rigor ceiling
~290M YT subs; $1 → $100K → $1M stair-step structure (2024 leaked handbook); dedicated thumbnail team (15+ variants per video, A/B tested); thumbnail + title account for ~50–60% of CTR variance per published analyses. Lesson: production rigor at every layer; thumbnail is a separate department.

### 7.2 — Casey Neistat — founder-led-vlog standard
Vlog-era peak 2015–2016, persistent influence as agency principal. Three-act compression in 10 minutes — still-relevant 2026 structure. Lesson: voice-driven single-creator format works when voice is genuinely distinctive.

### 7.3 — Johnny Harris — visual-evidence-first script
Geographic / geopolitical explainer; ~6M YT subs. Visual-evidence subordinates the voice-script; map-cuts every 8–12s as visual-evidence beat. Lesson: in explainer content, visual-first design beats script-first design.

### 7.4 — Hank Green (Complexly portfolio) — voice-as-discipline
Vlogbrothers / SciShow / Crash Course; 30M+ cross-channel. Written-for-one-person voice discipline (the "brother John" formulation). Lesson: voice-as-discipline beats voice-as-style; series-arc beats episode-as-unit.

### 7.5 — Tom Scott — single-take, pause-and-reveal
~6M YT subs; retired 2023, archive still studied. Single-take format with calibrated pauses; voice-as-cadence. Lesson: deliberate pacing-and-camera-work-as-style can itself be a signature.

### 7.6 — Cleo Abram — explainer + portfolio diversity
"Huge If True" series; ~1M YT subs. Shorts that share a creative universe but bet on different premises. Lesson: series-arc with portfolio-diversity-within-arc.

### 7.7 — Marques Brownlee (MKBHD) — production-value-led tech review
~20M YT subs. Best-in-class production quality (lighting, audio, color) as brand signature. Lesson: in product-review verticals, production value compounds as moat.

### 7.8 — Modern Wisdom (Chris Williamson) — interview + clip-extraction engine
2.5M+ YT subs. Weekly interview + clip-extraction workflow. Lesson: long-form-interview-plus-cut-extraction is among the highest-leverage cadences in 2026 for thought-leadership.

### 7.9 — Lex Fridman — long-form interview as format
~5M YT subs. 2–5 hour interviews defy short-form orthodoxy and work because guest quality + audience commitment are dialed. Lesson: counter-orthodox format works when audience-content fit is strong.

### 7.10 — ColinAndSamir — creator-economy commentary + advisory
Podcast + YouTube + advisory. Lesson: founder-led-agency model where content IS the advisory funnel.

### 7.11 — Logan Ury — applied behavioral science
YouTube + book + Match Group direction-of-research. Strong specific-CTA-per-video pattern. Lesson: applied-expertise verticals benefit from specific-CTA discipline.

### 7.12 — AI-video pioneers (2026)
Pure-AI channels (MyShell-style "Frostbite," AI Showrunner experiments) sit mid-tier in engagement. Founder + AI-augmented consistently beats pure-AI in 2026 across verticals. Lesson: AI-augmentation works; AI-replacement doesn't.

### 7.13 — Patrick Boyle — finance commentary
Ex-banker; weekly market-moment commentary; dry-precise voice. Lesson: market-moment cadence works for finance vertical.

### 7.14 — Lenny Rachitsky — B2B SaaS founder-content
Podcast + newsletter + course portfolio. Light video, high signal. Lesson: B2B founder content doesn't need video volume — high-quality long-form interviews + LinkedIn clips suffice.

### 7.15 — Polish-market exemplars (first-cohort context)
Dr Ewa Kaniowska (dermatology educator), Dr Anna Ostrowska / Klinika Estetyki Łódź (aesthetic-medicine), Patryk Kuchar (founder/creator hybrid). DWF: very few Polish-legal video exemplars in 2026 — service-firm vertical is still emergent in this market.

---

## §8 — Open Questions

Genuinely unresolved questions that the planning conversation needs to adjudicate before any v2 / v3 scope decisions.

**Q1 — Lane shape: one lane with 20+ axes or 5–8 sub-lanes?** Expanding to 20+ axes essentially requires multiple sub-lanes (per §6.1). Do we keep one lane (likely violating ≤5 criterion ceiling) or split into sub-lanes (channel-positioning, story-plans, thumbnail-strategy, distribution, etc.)?

**Q2 — Storyboard vs video-program: rename or extend?** Once the lane covers distribution + thumbnails + comment + coaching, "storyboard" is the wrong name. Rename to "video program" / "creator engine"? Defer? Maintain "storyboard" and treat new surface as adjacent lanes?

**Q3 — Fixture expansion: which verticals first?** Current fixtures (Klinika, DWF, B2B SaaS founder) too narrow. Add creator-led (YouTube creator with rich pattern data) first? E-commerce? Finance? AI-lab? In what order, with what budget?

**Q4 — Operator boundaries.** If the lane produces thumbnail directions, the human ships the thumbnail. Hook ladders → human runs the soft-publish tests. Coaching briefs → human runs the session. At what surface does the lane hand off, and how do we document handoffs?

**Q5 — Cost ceiling per program.** Sub-lane multiplication multiplies cost (per §6.5). What's the budget envelope per client per quarter? Without this, the lane will balloon.

**Q6 — AI-video model fleet refresh cadence and ownership.** Fleet rotates ~quarterly. Who owns `configs/storyboard/supported_models.yaml`? Ops team? Lane-maintainer? A fleet-tracker sub-lane?

**Q7 — Coaching brief: lane-generated or human-authored?** Diagnostic part requires footage of the founder; prescriptive part can be lane-generated. How much can the lane do without footage input?

**Q8 — Live video + AMA prep: in-scope or adjacent workflow?** Live is unscripted by definition. Lane could generate talking-point briefs + expected-question lists. In-lane or in adjacent "founder visibility" workflow?

**Q9 — Measurement integration: portal vs lane-output vs both.** Per memory `project-telemetry-audits-client-portal-2026-05-13`, the client portal handles telemetry. Does the video-program measurement frame live in the portal (consuming lane events) or as lane-output (recommendations re-fed to next plan)?

**Q10 — Comprehensive-lane minimum-viable input.** For SB-1 voice-fidelity, cold-start threshold is 3–5 anchor samples. For 20+ axes, the cold-start floor is much higher (brand-voice doc, channel-state audit, founder-content history, customer voice samples, competitor video map). What's the minimum-viable input?

**Q11 — Series-arc: prescriptive vs emergent.** 12-ep arc planned at ep 1 risks brittleness if ep 3 surprises with viral moment. Purely emergent never compounds. How do we encode "loose-arc-with-strong-premise"?

**Q12 — Polish-market vs US-primary tension.** First-cohort PL (Klinika, DWF); architectural target US-primary. PL audio expectations, host culture, platform mix (TikTok-dominant in PL vs YT-equal in US), tooling availability all differ. US-first and re-validate against PL, PL-first and re-validate against US, or simultaneous and pay dual-cohort cost?

**Q13 — Thumbnail generation tooling.** Nano Banana Pro / Gemini Imagegen / GPT-4o image / Flux / Midjourney v7 all produce thumbnail-grade images. Does the lane pre-select a tool, or produce text-description-only and let the operator choose?

**Q14 — Sponsorship integration: in-scope or deferred.** Complex (disclosure law, brand-safe handling, conversion measurement, partnership negotiation). In-scope for comprehensive lane or deferred to separate monetization workflow?

**Q15 — Evolution-loop signal granularity.** With 20+ axes the evolution signal becomes noisier. Which sub-axes drive highest signal-to-noise? Should evolution run on all axes equally or weighted?

**Q16 — Goodhart at program level vs video level.** A program optimized for "5 great videos that match the rubric" may fail as a series. Series-arc-optimized may produce coherent-but-mediocre individual videos. How do we balance per-video vs per-arc Goodhart resistance?

**Q17 — Modern-creator vs first-cohort overfitting.** Cleo Abram / Modern Wisdom / Lex Fridman: modern-creator anchor exemplars with dense pattern data. Klinika / DWF: first-cohort fixtures with thin pattern data. Structurally different. Which set drives architectural decisions, and how do we avoid overfitting to either?

**Q18 — Timing relative to OSS extraction.** Per memory `project-autoresearch-oss-extraction-deferred-2026-05-13`, OSS extraction gated to Q4-2026 / Q1-2027 on Content Engine Lanes v1 shipped + 2–3 clients + portal + Phase 3 stable. How much comprehensive-storyboard surface needs to ship before OSS extraction makes sense?

**Q19 — Quality parity with hand-crafted programs.** Best-in-class hand-crafted (Cleo Abram, Modern Wisdom, MrBeast) is the ceiling. Lane-generated likely falls short. Explicit target — 70% of hand-crafted at 10% of cost? 90% at 30%? Without calibration, the lane optimizes against an undefined target.

**Q20 — Comprehensive lane vs minimum-viable lane: tier strategy.** Full 20+-axis for tier-1 high-spend clients; MVP (5–8 axes: plans + hooks + thumbnails + distribution + measurement) for tier-2/3. One lane with optional add-ons, or multiple lanes (storyboard-lite, storyboard-comprehensive, storyboard-program)?

---

## Coda

The current v1 storyboard lane is a single shelf in a 20-shelf store. The four-axis research deliverables (voice fidelity, AI failure modes, cold-start, model capability) make that one shelf sturdy — they do not build the other 19.

A 2026 AI-native agency that ships only 5 video story plans per engagement and calls it a video workflow is undersized for the market. Modern clients (SaaS founders, AI-lab researchers, agency principals, service firm partners, finance operators, e-commerce operators) need the comprehensive surface this document maps — series arcs, thumbnails, distribution, comments, coaching, multi-platform native cuts, measurement loops.

The path is phased: v2 adds the 4–6 highest-leverage axes (hook ladder, thumbnail strategy, distribution map, series-arc planning, comment-magnet engineering); v3 adds the next 6–8 (on-camera coaching, music direction, measurement frame, multilingual, monetization integration); v∞ has the full surface.

The open questions in §8 are real adjudication points. The planning conversation that follows this document should pick which questions to answer first, not which axes to ship first — answering the question determines the axes.

This document does not advocate scope at the expense of quality. It advocates for *seeing the full surface before scope-reducing back to v1.* The first-cohort posture (Klinika, DWF, B2B SaaS founder) does not justify a permanent 5-plan ceiling — it justifies a starting point the platform is intentionally moving past as the next cohort onboards.

---

*Companion files:*
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-18-judge-design-step1-storyboard.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-storyboard-creator-voice-fidelity.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-storyboard-ai-failure-modes.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-storyboard-pattern-data-cold-start.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-storyboard-ai-video-model-capability.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/rubrics/judge-design-guide.md`
