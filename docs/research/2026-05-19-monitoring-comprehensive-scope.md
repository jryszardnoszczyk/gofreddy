---
date: 2026-05-19
type: research deliverable — comprehensive MON workflow surface map
status: complete
topic: Monitoring (MON) workflow — full surface beyond a weekly digest
parent: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md
companions:
  - docs/research/2026-05-18-monitoring-vertical-conventions.md
  - docs/research/2026-05-18-monitoring-artifact-taxonomy.md
  - docs/research/2026-05-18-monitoring-ai-failure-modes.md
  - docs/research/2026-05-18-monitoring-compound-narrative-absence.md
  - docs/rubrics/judge-design-guide.md
sibling-precedent: docs/research/2026-05-17-judge-design-step1-competitive.md (CI v3.3 expansion pattern)
framing: gofreddy is a generic AI-native agency. Klinika + DWF are first-cohort. Primary client mix:
  SaaS / AI / agency / professional services / finance / e-commerce, US-primary,
  with Poland regulated verticals (legal_pl, medical_pl) as first-cohort anchors.
mandate: DO NOT scope-reduce. Map the FULL comprehensive surface of monitoring
  for a 2026 modern AI-native agency. v1's "weekly digest only" is the LOCKED
  artifact shape for the current MON lane — this document maps everything the
  workflow could legitimately produce for clients across the spectrum.
---

# Monitoring (MON) — Comprehensive Workflow Surface

## TL;DR

Current MON v1 ships a single LOCKED artifact: a 600–1,400 word weekly executive digest for a Series-B-or-later comms director. That is the right scope **for v1 against the current first cohort** (Anthropic / Perplexity AI-labs, DWF legal, Klinika healthcare). It is not the full surface of what a modern AI-native agency client genuinely needs from a monitoring function in 2026.

The full MON surface spans **at least 22 distinct signal axes** crossed with **at least 7 deliverable form factors** crossed with **3 cadence shapes** (standard / event-driven / incident-driven). Most current monitoring vendors (Cision, Meltwater, Brandwatch, Talkwalker, Onclusive) cover roughly 6–10 of those axes well, neglect the rest, and treat the deliverable as a single shape — a weekly clip-dump with sentiment chart. The 2026-modern lever — that an AI-native agency can credibly own — is **interpretation across the full surface, decomposed by trust dimension, with absence-as-signal and compound-narrative detection as first-class outputs, AI-engine citation tracking baked in from day one, and decision-shape-aware cadence per client**.

The single highest-leverage modernization for gofreddy specifically: **add AI engine citation monitoring (how the brand surfaces in ChatGPT, Perplexity, Claude, Google AI Overviews, Gemini, Copilot answers) as a recurring axis** — most 2024-era monitoring vendors do not cover this; Profound, Daydream, Athena, Goodie, Otterly, AthenaHQ, Peec, Scrunch, Bluefish AI are the dedicated 2026 entrants. This axis is invisible to brands today and will be the dominant inbound-discovery surface within 18 months.

The architectural takeaway: **v1's lane-locked single artifact is correct for the evolution-loop's selection pressure**, but the lane should grow over the next 12 months into a **multi-cadence sibling-lane family**: pager-tier, daily brief (event-driven verticals only), weekly digest (current v1), monthly scorecard, quarterly memo, board-prep input, incident postmortem, plus the AI engine citation report as its own deliverable. Each sibling lane carries its own optimal-output spec, structural_gate, and 4–6 judge criteria. Don't fork them until at least 2 verticals demand them; do fork them before stretching the weekly digest to cover incompatible decision shapes.

---

## §1. Full MON Surface — 22 Signal Axes

The signal substrate a 2026 modern monitoring function actually has to ingest, interpret, and surface. Each axis carries (a) what it is, (b) why current first-cohort clients care, (c) the modern vendors / data sources, (d) what the AI-native agency does that incumbent monitoring vendors do not.

### A1. Brand mention monitoring (multi-surface)

The classical core — every public mention of the brand name across news, social, podcasts, Reddit, Hacker News, Wikipedia, AI engines, newsletters. Vendor canon: Cision, Meltwater, Brandwatch, Mention, Brand24, Talkwalker, Onclusive. Modern: Notified (Cision spinout), Determ, Awario, Prowly, Critical Mention (broadcast).

What changes for gofreddy: the modern lever is **interpretation density per mention**, not mention count. v1 explicitly rejects "230 mentions this week" framing in favor of baseline-relative deltas. The agency-side opportunity is per-mention triage with named source-tier credibility (WSJ vs Stratechery vs Reddit vs LinkedIn post-by-a-customer) and orthogonal-axis severity (Hazard + Outrage; Competence + Ethics).

### A2. Sentiment tracking with trust-dimension decomposition

NOT single-axis sentiment ("62% positive"). Edelman Trust Barometer's 2026 finding holds: **competence and ethics decompose distinctly, with roughly 76/24 of trust capital sitting in ethics for B2B / professional services and finance**. A single-axis "positive sentiment" reading systematically misses ~3× of reputational damage on ethics-exposed events (regulatory, executive-misconduct, data-breach).

Modern decomposition axes the workflow should ingest:
- **Edelman competence vs ethics** (the canonical pair for B2B + finance + healthcare).
- **Cision React Score: Hazard + Emotionality** dual-axis (the canonical pair for crisis / brand events).
- **Sandman Risk = Hazard + Outrage** (the canonical pair for regulator-watching verticals).
- **Aaker Brand Personality 5-factor** (sincerity, excitement, competence, sophistication, ruggedness) for DTC/e-commerce/agency-client work.
- **Net warmth + competence (Fiske SCM)** for consumer-facing personality classification.

The 2024-era monitoring stack reports one number. The 2026-modern agency reports the **decomposition vector with named-axis reasoning**. v1's MON-2 captures this for criterion-grading; the full surface includes the underlying telemetry.

### A3. Share of voice (SoV) with negation filter + ESOV math

SoV is the conventional vanity metric. Britopian's 2024 critique and Sprout Social's 2025 SoV reframing both flag: **SoV without negation-filter** counts mentions that are explicitly negative as "share," inflating presence; **SoV without ESOV** (Excess Share of Voice, Binet & Field 2013) treats market-share-vs-mention-share ratios as the actual lead indicator.

The full surface includes:
- Raw mention SoV.
- Negation-filtered SoV (drop mentions whose sentiment is < -0.4 from share calculation).
- ESOV per competitor (`mention_share − market_share`) — the long-run growth predictor.
- AI engine citation SoV (how often each competitor surfaces in answer-engine results vs the brand).
- Tier-weighted SoV (a WSJ mention counts 50× a Reddit comment).
- Conversational SoV (depth of thread engagement, not just first-mention count).

### A4. Competitor activity monitoring (CI handoff)

Distinct from the CI lane's strategic-brief output. MON owns **daily competitor activity volume** — product launches, pricing-page changes, hiring postings, executive LinkedIn moves, status-page incidents, blog post velocity. CI owns **strategic interpretation of that activity**.

Lane-boundary discipline (per `docs/research/2026-05-18-monitoring-vertical-conventions.md` open question #7): MON surfaces "Acme launched 4 features this week vs 1 last week," CI interprets "Acme's product-velocity acceleration is being funded by their April Series C — they are the credible threat in the developer-AI segment over the next 6 months." Without this discipline, both lanes optimize for the same signal and neither produces differentiating insight.

Modern surfaces:
- **Product page change tracking**: Wachete, Visualping, Distill.io, Hexowatch, Versionista.
- **Pricing page diffing**: same vendors + custom regex.
- **Status page monitoring**: StatusGator (aggregates 3,800+ status pages), IsDown, Pingdom, Better Stack.
- **LinkedIn personnel tracking**: TheirStack, Predictleads, LeadIQ, Apollo, Champify, Cognism.
- **Hiring posting tracking**: TheirStack (hiring intent), Greenhouse / Ashby public boards, LinkedIn Jobs.
- **Patent filing**: USPTO PAIR, Google Patents alerts, PatSnap, IFI Claims.
- **Trademark / domain registration**: USPTO TESS, DomainTools, WhoisXML, RiskIQ Digital Footprint.

### A5. Industry trend monitoring (category-level signal)

Above the brand. Category-level forces — new regulation, new entrants, new financing patterns, new failure modes — that change the brand's positioning context.

Modern sources:
- **CB Insights / PitchBook / Crunchbase** for funding + M&A trend.
- **Gartner Magic Quadrant / Forrester Wave / IDC MarketScape** placement movements.
- **a16z State of (X), Bessemer / Battery / Sequoia / IVP / Insight market reports.**
- **OpenAI / Anthropic / Google research-paper publication patterns** (for AI-adjacent clients — predicts capability frontier).
- **Stratechery, Latent Space, Interconnects, Lenny's, Every, Not Boring, The Generalist, Stratechery, Software Engineering Daily.**
- **Reddit subreddit trend volume** (r/devops, r/dataengineering, r/sysadmin, r/selfhosted, r/SaaS — the leading-indicator surface for technical SaaS).

The trend axis is the integral over time of A4; it is what makes A4 interpretable.

### A6. Customer pulse monitoring

The signal substrate that most "brand monitoring" vendors don't touch but that determines actual retention. Integrated with the GTM / customer-success function but flagged in the digest when anomalous.

Modern surfaces:
- **NPS / CSAT delta** (Delighted, Qualtrics, Wootric, Pendo NPS, internal tooling).
- **Review velocity + sentiment**: G2, Capterra, Trustpilot, App Store, Play Store, ProductHunt, TrustRadius.
- **Support ticket volume + topic clustering** (Zendesk, Intercom, Front, HubSpot Service — surfaced via internal API if client granted access).
- **Account-health-score deltas** (Gainsight, ChurnZero, Catalyst — gated to retainer-clients).
- **Churn / contraction signal** from LinkedIn departure tracking at flagship accounts.

Lane-boundary: MON surfaces anomalous deltas. The agency's CS / GTM teams own day-to-day account-health workflows.

### A7. Regulatory / compliance signal

Per vertical-conventions §2.4 + §3.4 + §4.5, this is legally mandatory for several first-cohort verticals.

Surfaces by vertical:
- **Financial services**: SEC EDGAR filings (10-K Risk Factors, 10-Q MD&A, 8-K material events), FRB enforcement actions, OCC notices, FINRA Disciplinary Notices + Form U4/U5 amendments, FCA Final Notices, FINRA Rule 4530 reportable events, EU DORA + MiCA + GDPR Art. 33–34 breach notifications, NAIC ORSA inputs.
- **Healthcare**: FDA Warning Letters, FDA 483 observations, FAERS + MAUDE signals, HHS Wall of Shame breach reports, OIG inspection findings, CMS Star Ratings publications, Joint Commission sentinel events (when they become public via state-board), state medical-board disciplinary actions.
- **Legal**: SRA disciplinary, state-bar disciplinary, Chambers + Legal 500 tier-shifts.
- **Regulated industries**: FAA Airworthiness Directives, NRC 10 CFR 50.72 event reports, NERC CIP cybersecurity disclosures, FCC NORS network-outage filings, CMMC/DFARS cyber-incident reports.
- **General**: USPTO IP filings, FTC enforcement actions, DOJ press releases, state AG actions, OFAC sanctions designations.

Modern aggregators: **GovTrack, RegTrace, Compliance.ai, Thomson Reuters Regulatory Intelligence, RegBot, FiscalNote** for federal/state regulatory monitoring; **EDGAR Online, Sentieo (now AlphaSense), MyEDGAR** for SEC filings.

### A8. PR + crisis detection

The classical core of executive monitoring. Coombs SCCT (victim / accidental / intentional crisis cluster classification), Benoit Image Restoration, Sandman Outrage Management, Cision React Score, Dezenhall *Glass Jaw*.

Modern detection:
- **Brandwatch Vizia / Iris** real-time spike alerts on volume + sentiment cliff + tier-1-source amplification.
- **Talkwalker** five-warning-indicator model.
- **Cision Komo, Onclusive Crisis Push, Meltwater Mira AI** crisis-room dashboards.
- **PagerDuty / Slack-integrated** reputation-event escalation routing.

The 2026-modern lever: classify each detected event into the SCCT cluster + Sandman Hazard+Outrage quadrant + Coombs response-strategy recommendation (denial / diminish / rebuild / bolstering) within the digest itself — not as an attached framework reference, but as the analytic reasoning behind the severity tier.

### A9. Crisis-trigger off-cadence response

Distinct deliverable from cyclic monitoring. When a Sandman-quadrant-1 event (high hazard + high outrage) fires off-cycle, the monitoring function needs to surface a **pager-tier alert + same-day situation report**, not wait for Monday's digest.

Per artifact-taxonomy §2.1 + §2.3 + open question #3: this is a **separate workflow** from the weekly digest lane. The architectural decision for gofreddy: lane MON-pager-tier as a sibling lane, with its own optimal-output spec (< 100 words, single-source-anchored, named escalation owner, sub-1hr decision velocity) and its own structural_gate (alert-fatigue tier-distribution check, false-positive rate ≤ 30% over rolling 4 weeks).

### A10. Compound narrative detection

Per `docs/research/2026-05-18-monitoring-compound-narrative-absence.md`. Multi-week threads that exist across time but read as routine inside any single week. The Pearl Harbor signals-to-noise problem imported into corporate monitoring.

The 2026-modern AI-native agency lever: **compound detection IS the AI-on-AI moat**. Human analysts at Cision / Meltwater don't carry multi-week memory across 200+ clients. An LLM-driven monitoring function with a persistent fixture corpus and a per-client compound-graph can surface threads that 4 distinct human analysts (each owning one week) would systematically miss.

Defenses against compound-fabrication (apophenia, the load-bearing AI failure surface here): distinct time-points required, source-grounded connective tissue required, at least one disconfirming reading engaged at weight comparable to favored. v1 MON-6 captures this for criterion-grading.

### A11. Absence-as-signal

Per the same compound-narrative research. The dog that didn't bark. Conrad Doyle's "Silver Blaze" mnemonic adopted across CIA tradecraft, FM 34-2 PIR doctrine, and Tetlock's superforecaster calibration findings.

Specific absence classes the digest surfaces:
- Competitor silent on a major industry event (expected response missing).
- Founder absent from earnings call (baseline: present every prior call).
- Expected product launch missed (announced window passed without launch).
- Regulator response window passed without action.
- Expected analyst coverage didn't materialize (compared to vertical-cadence baseline).
- Required filing window approaching without filing.
- Customer reference call cancelled / postponed (signal from CS).

The structural defense (apophenia): every flagged absence carries a **named baseline expectation with corpus source** — prior-period digest, public calendar, industry cadence, named precedent. Fabricated absences fail because they can't supply the baseline.

v1 MON-5 captures this for criterion-grading.

### A12. Forward projection on monitored narratives

Falsifiable conditional forecasting on the narratives the digest surfaces. NOT vibe-projections ("expect continued volatility"). Tetlock-grade calibrated forecasting: "if Pinsent confirms the 6th lateral by Friday, expect 2–3 additional firms to announce reciprocal-defenses within 2 weeks; if no confirmation by Friday, the narrative resolves into the noise."

Per the design-guide §1.1 outcome-question discipline + Tetlock's *Superforecasting*: projections must be (a) falsifiable within a stated window, (b) calibrated to evidence depth (not narrative coherence), (c) decomposed into named conditionals.

The 2026-modern lever: integrate with a **prediction-market or Brier-scored calibration tracker** — Manifold Markets, Polymarket, Kalshi, Metaculus, or an internal Brier-tracked judgment register. Each quarter, score the prior-quarter projections; surface the calibration record in the quarterly deep-dive. Most agencies don't do this; the few that do (FullIntel, AlphaSense's enterprise tier) charge a premium for it.

### A13. Talent flow signal

Personnel movement — the highest-fidelity leading indicator of competitor instability per the vertical-conventions B2B-SaaS section.

Surfaces:
- **LinkedIn departure tracking** — TheirStack, Predictleads, Champify, LeadIQ, Cognism for systematic; manual LinkedIn alerts for high-fidelity.
- **Leopard Solutions Firmscape** for legal-services lateral tracking.
- **Above the Law lateral-link blog** for legal trade-press.
- **Glassdoor "Reviews" trend velocity** — directional but noisy.
- **Levels.fyi / Blind salary movements** for tech-vertical signal.
- **AngelList / Wellfound profile changes** for early-stage signal.
- **GitHub commit-activity per author at competitor public repos** (clever leading indicator for OSS-dependent startups).

The 2026-modern agency lever: per-competitor talent-flow scorecard refreshed weekly, with named-departure context (where they went, what they were leading, what the public LinkedIn message says).

### A14. M&A + funding signal

Funding rounds, acquisitions, divestitures, IPOs, secondary-market activity.

Sources: Crunchbase, PitchBook, CB Insights, Mergermarket, Dealogic, S&P Capital IQ, FactSet, SEC EDGAR (8-K, S-1, Schedule 13D/G), state secretary-of-state corporate filings, public-equity short-interest data.

Modern lever: per-client funding-signal scorecard — when a competitor raises, the customer-success / sales / pricing functions need to be alerted within 24h, not in Monday's digest. This is a same-day-pager-tier signal class, not weekly-digest material.

### A15. Earnings call + public-statement parsing

For public competitors and for clients facing earnings calls: parse the earnings-call transcript + investor-day presentation + 10-Q/10-K narrative for positioning shifts, hedged guidance, executive-tone changes.

Modern surfaces:
- **AlphaSense, Sentieo (now AlphaSense), Bamsec, FactSet StreetAccount, Bloomberg Transcripts** for raw transcript access + LLM-extractable annotations.
- **Hedge-fund-grade sentiment models** on call transcripts (Linguistic Atlas, Quiver Quantitative, EarningsCall.app).
- **Voice-stress analysis on CEO/CFO Q&A sections** (controversial but used by some quant funds; flagged here for awareness, not recommendation).

Lane integration: earnings-call insights feed both MON (reputation positioning signal) and CI (strategic moves signal). The MON-side ownership is "what did Acme's CEO say about our category" — the CI-side ownership is "what does Acme's GTM resourcing imply about their 12-month strategy."

### A16. Social listening — multi-platform

Across **LinkedIn, X (Twitter), Reddit, TikTok, Threads, Bluesky, Mastodon, Instagram, YouTube, Discord, Slack public communities**. Each platform carries distinct signal density per vertical.

Per-platform vendor canon:
- **X/Twitter**: TwitterAPI.io, Sprinklr, Sprout Social, Hootsuite, Buffer, Brandwatch, Talkwalker.
- **LinkedIn**: Phantombuster, ScrapingBee, LinkedIn Sales Navigator (manual), Apollo, Cognism. Note: LinkedIn API access is restricted; most monitoring relies on scraping or curated lists.
- **Reddit**: PRAW API, Pushshift (limited), F5Bot, Mention, Brandwatch (via Reddit firehose), GummySearch.
- **TikTok**: TikTok Research API (limited), Tagger Media (now Sprout Social), Tubular Labs, Talkwalker.
- **Threads**: Meta Threads API, Sprinklr, Brandwatch (limited).
- **Bluesky**: AT Protocol direct, Skyfeed, Graysky.
- **Discord**: Discord API (gated to bot in server), Statbot, MEE6 analytics.
- **YouTube**: YouTube Data API, Tubular Labs, Tubebuddy, vidIQ, Brandwatch.
- **Podcast surfaces**: Listen Notes, Podchaser, Podscan, Speechmatics for transcript extraction, Snipd for clip discovery.

The 2026-modern lever: **cross-platform narrative threading** — when the same narrative crosses 3+ platforms within 48h, flag as compound-narrative-class signal regardless of per-platform volume. Most monitoring vendors silo per-platform; the agency-side opportunity is platform-agnostic narrative tracking.

### A17. AI engine citation monitoring

The 2026-defining new axis. How does the brand show up in answer-engine results — ChatGPT, Perplexity, Claude, Google AI Overviews, Gemini, Microsoft Copilot, Brave Leo, DuckDuckGo DuckAssist, Kagi Assistant, You.com, Phind?

This is invisible to all 2024-era brand monitoring vendors. Dedicated 2026 entrants:
- **Profound** (raised Series A in 2026; AI-engine citation tracking + visibility scoring).
- **AthenaHQ / Athena** (visibility across ChatGPT, Perplexity, Claude, Google AI Overviews).
- **Daydream** (LLM SEO + answer-engine optimization).
- **Otterly.ai** (AI search visibility tracking).
- **Peec AI** (LLM brand mention monitoring).
- **Scrunch AI** (AI search ranking + content optimization).
- **Bluefish AI** (LLM brand tracking).
- **Goodie** (AI citation + content recommendations).
- **HubSpot AI Search Grader** (free tier).
- **SE Ranking AIO tracker**.
- **Semrush AI Toolkit (2026 launch)**.
- **Ahrefs Brand Radar** (AI visibility module).

Modern coverage axes:
- **Citation frequency**: how often the brand is mentioned in answer-engine results across N controlled prompts per week.
- **Citation tier**: cited as primary source vs cited as one-of-many.
- **Citation sentiment**: how the answer engine describes the brand (favorable / neutral / critical).
- **Citation vs competitor share**: brand citation count / (brand + top-5 competitors) citation count.
- **Citation drift**: week-over-week change in citation prompts where the brand appears.
- **Hallucination flagging**: when an answer engine attributes false claims to the brand.
- **Source attribution**: which underlying sources (the brand's own site, Wikipedia, Reddit, G2, Stack Overflow, GitHub, partner content) are feeding the citations.

This axis genuinely is invisible to brands today. gofreddy has a window to own it before AI-engine traffic dwarfs conventional-search traffic (Gartner projects 50% search-volume migration to AI engines by 2028).

### A18. Knowledge graph monitoring

Wikidata, Google Knowledge Panel, Bing entity panel, Apple Knowledge entity, ChatGPT-source-grounding context, Perplexity-source-grounding context.

The brand's knowledge-graph footprint determines whether AI engines pick the right entity when a prompt mentions the brand name (vs picking a homonym or a wrong-vertical company). Most agencies don't actively manage this; Wikidata is the leverage point because it feeds Google + Bing + most LLM training corpora.

Modern surfaces:
- **Wikidata Query Service** for direct property monitoring.
- **Kalicube** for branded SERP / knowledge panel tracking.
- **Wikipedia Watchlist** for editorial-grade change tracking on the brand's own + competitors' Wikipedia pages.
- **Schema.org markup validation** via Google Rich Results Test + Schema.org Validator.

### A19. Review monitoring

G2, Capterra, Trustpilot, Yelp, Google Maps, App Store, Play Store, ProductHunt, TrustRadius, Glassdoor employee reviews, Healthgrades (healthcare), Avvo + Martindale (legal), Vault (consulting / legal).

Surfaces:
- Velocity delta (review count delta week-over-week).
- Sentiment-mix delta.
- Specific-claim clustering (3+ reviews citing the same defect signal a real product issue, not noise).
- Competitor review-velocity comparison.
- Response-rate tracking (how fast the brand responds to negative reviews).

Modern aggregator vendors: ReviewTrackers, Birdeye, Podium, Reputation.com, Yotpo, Trustpilot Business, Reviews.io.

The 2026-modern lever: **review-claim extraction and clustering** — surfacing the specific product / service claim that 3+ reviews converge on, not the aggregate sentiment number. LLMs are the natural tool for this; conventional review-monitoring vendors lag.

### A20. Podcast + interview tracking

Executive interview tracking — when did the founder / CEO / spokesperson last appear on a podcast, in what context, with what positioning. Also: when do competitors' executives appear, on what podcasts, saying what.

Modern surfaces:
- **Listen Notes API** for podcast catalog search.
- **Podchaser** for podcast metadata + episode-level data.
- **Podscan, Podchaser Pro, Snipd** for transcript-grounded mention monitoring.
- **Speechmatics, AssemblyAI, Whisper.cpp** for transcript extraction from podcasts not yet transcribed.

For founder-led startups (per vertical conventions §4.2), podcast appearances are the **highest-distribution-per-effort channel** in 2026 — Latent Space, Lenny's, How I Built This, Acquired, Decoder with Nilay Patel, This Week in Startups, The Generalist Show, Stratechery interview series. Monitoring them is monitoring the brand's category-positioning broadcast layer.

### A21. Event + conference monitoring

Industry conferences (AWS re:Invent, Google I/O, Anthropic Builder Day, OpenAI DevDay, Snowflake Summit, Salesforce Dreamforce, RSA, HIMSS, JPM Healthcare, Davos), named talks at those conferences, panel participants, named-speaker announcements.

Monitoring axes:
- Did the brand's founder / CEO get on a named-conference panel?
- Did competitors' executives get on panels the brand wanted?
- Did a named talk at conference X mention the brand by name (transcript-grounded)?
- Did the brand's customer give a named-case-study talk?

Sources: Conference public agendas, YouTube post-conference uploads (where applicable), SlidesShare archival, conference press kits, conference-specific Twitter/X listening, paid analyst seat (Gartner Symposium / Forrester / IDC client briefings).

### A22. Influencer + creator mentions, newsletter mentions, Reddit + Hacker News + Product Hunt signal, Glassdoor + employee signal, litigation + lawsuit signal, public-filing parsing

A bundle of remaining surfaces, each individually load-bearing for specific verticals:

- **Influencer + creator mentions**: TikTok / Instagram / YouTube creator-tier mentions. CreatorIQ, Modash, Aspire, Tagger Media, Tagger now Sprout Social. Per-creator sentiment + reach-weighted impact.
- **Newsletter mentions**: Substack, Beehiiv, Ghost, ConvertKit, Mailchimp public-archive scanning. Stratechery, Lenny's, Every, The Generalist, Not Boring, First Round Review, Software is Awesome, Latent Space, Interconnects, Pragmatic Engineer, Lethain — for tech / startup verticals these often dominate week-to-week mindshare more than trade press.
- **Reddit + Hacker News + Product Hunt signal**: technical-buyer leading indicators. HN front page mentions, r/programming top posts, Product Hunt launches in adjacent categories.
- **Glassdoor + employee signal**: review velocity, employee NPS proxy, "would recommend to a friend" delta. Particularly load-bearing for hiring-competitive verticals (AI, consulting, finance) where employee sentiment IS competitive signal.
- **Litigation + lawsuit signal**: Court Listener API, PACER, state-court online portals, RECAP archive, securities-class-action databases (Stanford Securities Class Action Clearinghouse, Stanford Law SCAS). Plaintiff-firm IR-watching (the moment a 10b-5 firm files an investigation announcement) is a leading indicator of securities litigation per the financial-services vertical conventions.
- **Public-filing parsing**: SEC EDGAR (8-K, 10-Q, 10-K, S-1, 13D/G), state-corporate filings, UK Companies House, EU equivalent registries, IP filings.

---

## §2. CUTS — what current monitoring vendors do that the 2026-modern agency should NOT replicate

Anti-patterns the lane explicitly rejects, drawn from the v1 spec's mediocre + Goodhart catalog and the artifact-taxonomy + AI-failure-modes research:

**C1. Clip dump with no interpretation.** "Acme was mentioned 230 times this week. Top sources: TechCrunch, Reddit, Twitter, LinkedIn. Sentiment: 62% positive, 23% neutral, 15% negative." This is the FullIntel "data dump, not intelligence" failure; the Barcelona Principles V4.0 explicit violation; the dominant Cision / Meltwater / Brandwatch default-report shape. The 2024-era monitoring product is structurally a clip dump.

**C2. Sentiment-score-only reporting.** Single-axis "positive / neutral / negative" percentages without trust-dimension decomposition. Misses ~3× of reputational damage on ethics-exposed events per Edelman Trust Barometer 2026.

**C3. "We tracked 230 mentions this week" volume reporting.** Volume without baseline comparator is noise. v1 MON-1 explicitly rejects this.

**C4. Surface SoV without decomposition.** SoV without negation filter, without ESOV math, without tier weighting. Britopian's 2024 critique applies.

**C5. Generic "continue to monitor" recommendations.** Observations dressed as recommendations. No deadline, owner, or consequence. v1 MON-4 explicitly rejects this.

**C6. Alert fatigue from over-promotion.** Every uptick framed "URGENT" or "crisis." 73% SOC false-positive rate (SANS 2025) transfers to brand monitoring. Trains the reader to ignore urgency signals.

**C7. False-urgency framing.** Sycophantic LLM tier inflation — routine items tagged "watch" because "noise" feels like a non-answer. Per AI-failure-modes Q3.

**C8. Single-archetype reader assumption.** Monday-8:55am framing as universal. Per vertical-conventions: 3 of 7 verticals operate on event-driven or regulator-clock cadences. v1 fixes this via decision_shape-aware reader.

**C9. AVE (Advertising Value Equivalent) reporting.** Barcelona Principles V4.0 canonical violation: "AVE is not the value of public relations." Yet most legacy vendor default reports still include it.

**C10. Backward-looking-only digest.** Heavy on last week, thin on next week. Per artifact-taxonomy §2.4 (monthly scorecard failure mode #6).

**C11. Forced "Cross-Story Patterns" section with weak connections.** Co-occurring but causally unrelated stories stitched together to satisfy a compound criterion cosmetically. v1 MON-6 explicitly defends against this with distinct-time-points + source-grounded-connective-tissue requirements.

**C12. Single-event spun three ways to satisfy compound requirements.** Same week's signal restated three times in three paragraphs. v1 MON-6 structural defense.

**C13. Fabricated absence with no baseline anchor.** "Competitor did not announce a Mars program." Apophenia failure mode. v1 MON-5 structural defense.

**C14. Required-silence misread as anomalous-silence.** Recommending response during FDA pre-approval / SEC quiet period / NRC classified investigation phase. Per vertical-conventions §4.5: this is a regulator-rule-violation prescription. v1 MON-5 CoT step 3 catches this.

**C15. Event / source / quote confabulation in the digest body.** Apple News withdrawal pattern. 19.9% citation-fab base rate for GPT-4o. Per AI-failure-modes Q1. v1 routes this to structural_gate (URL HEAD + quote-grep + entity allowlist).

**C16. Recency / training-cutoff distortion presented as "this week."** 23–35% relative-temporal-framing accuracy drop on LLMs (NAACL 2025). Per AI-failure-modes Q2. v1 routes this to structural_gate (as-of date + evidence_dates).

**C17. Compound-claim fabrication via invented connective tissue.** Real-Y + real-Z + invented "led to." 59% forecast-error inflation on AI-assisted equity reports (FactSet 2025). Per AI-failure-modes Q4. v1 MON-6 structural defense.

**C18. Mechanical tier tagging.** "TIER: HIGH/MEDIUM/LOW" populated as template-field-stuffing without orthogonal-axis reasoning. v1 MON-2 explicitly rejects.

**C19. Chart-junk monthly scorecards.** Visualizations that obscure rather than reveal. Per artifact-taxonomy §2.4 failure mode #3.

**C20. Performative scorecards.** Every quarter green-tick regardless of underlying state. Per artifact-taxonomy §2.4 failure mode #5.

**C21. Digest bloat.** 1,800-word weekly digest that nobody reads Monday morning. Hard length cap in structural_gate at 1,500 words is v1's defense.

**C22. Form-factor drift.** Frankenstein digest blending pager-alert lede + deep-dive-memo body + monthly-scorecard tables. Per artifact-taxonomy §5. v1 structural_gate enforces shape.

---

## §3. ADDS — what the modern 2026 AI-native agency should add beyond current vendor norms

The forward-looking expansion. Each is the inverse of a CUT or a genuinely new axis enabled by 2025–2026 capability.

**N1. Multi-axis severity classification with named orthogonal-pair reasoning.** Edelman competence-vs-ethics (B2B / finance / healthcare), Cision Hazard+Emotionality (crisis events), Sandman Hazard+Outrage (regulator-watching), Aaker 5-factor (DTC consumer), Fiske SCM warmth+competence (consumer-facing) — per-vertical pair selection with reasoning visible. v1 MON-2 captures this for criterion-grading; the full surface includes the underlying telemetry per-event.

**N2. Trust-dimension decomposition.** Not just "competence vs ethics" labels but a competence-score-delta and ethics-score-delta tracked per-event and per-period. Edelman Trust Barometer 2026 methodology serves as the source-of-truth for the decomposition mechanic; gofreddy's instantiation is per-client lightweight.

**N3. Compound-narrative detection across multi-week windows.** First-class output, not buried in the digest. Per the compound-narrative-absence research — the AI-on-AI moat where LLMs naturally beat fragmented human-analyst staffing.

**N4. Absence-as-signal with corpus-anchored baseline.** First-class output. Tetlock superforecaster discipline — flag absence-of-pattern when stakeholders want a story but evidence doesn't support one. Defended against apophenia via named-baseline-expectation requirement.

**N5. Falsifiable forward projection with calibration tracking.** Brier-scored conditional projections, refreshed quarterly via a calibration scorecard. Most agencies don't do this; the few that do can charge a premium.

**N6. Action items in FAA-AD format.** Named owner + specific deadline + operationalized consequence-of-inaction. v1 MON-4 captures this for criterion-grading; the full surface treats this as the production format for the entire client-facing recommendation surface.

**N7. AI engine citation monitoring.** New axis. Profound / AthenaHQ / Daydream / Otterly / Peec category. The 2026-defining modernization that 2024-era vendors don't cover. **The single highest-leverage axis to lead with for new clients.**

**N8. Distribution moat tracking.** Where each piece of brand mention surfaced via — newsletter, podcast, X thread, LinkedIn post, Reddit, AI engine, SEO. The competitive question "where is our distribution actually working" rather than the volume question "how many times did we get mentioned." Particularly load-bearing for founder-led startups whose distribution is fragmented across many channels.

**N9. Founder-visibility monitoring.** For founder-led-startup clients: track founder appearance volume + tier (which podcasts / newsletters / panels / X threads + sentiment + topic clustering) as its own axis. Per vertical-conventions §4.2 — the founder IS the monitoring consumer AND the brand's primary distribution channel; founder-visibility IS brand monitoring.

**N10. Decision_shape-aware cadence.** Standard / event-driven / incident-driven per client. v1 reader spec captures this. The full surface: structural_gate per-client `cadence_class` field that gates the form factor + delivery latency + per-criterion expectations.

**N11. Watchlist construction + maintenance.** First-class deliverable: per-client watchlist of named competitors + named regulators + named industry analysts + named journalists + named investors + named conferences + named keywords + named subreddits. The watchlist IS the monitoring substrate; gofreddy's job includes maintaining the watchlist as the client's competitive context evolves.

**N12. Cross-lane handoff to CI for strategic implications.** Per lane-boundary discipline: MON surfaces the signal, CI interprets the strategic move. The handoff IS the deliverable for events crossing the activity-vs-strategy boundary.

**N13. Cross-lane handoff to GEO for narrative drift.** When monitoring surfaces a narrative shift that affects how AI engines describe the brand, hand off to the GEO lane for prompt-side response. This is the bidirectional integration with A17 (AI engine citation monitoring).

**N14. Cross-lane handoff to marketing_audit for category positioning shifts.** When monitoring surfaces a category-level shift (new entrant, new regulation, new buying-criteria), hand off to MA for positioning refresh.

**N15. Quarterly calibration scorecard.** Per N5: every quarter, score the prior-quarter projections (compound predictions, absence predictions, severity classifications). Surface Brier scores in the quarterly memo. Transparency is the trust-building lever.

**N16. Multi-cadence sibling-lane family.** Per §5 below: pager-tier (sub-1hr), daily brief (event-driven verticals), weekly digest (current v1), monthly scorecard, quarterly memo, board-prep slide input, incident postmortem, AI engine citation report. Each sibling lane has its own optimal-output spec.

**N17. Per-client dashboard with live signal feed.** Continuous-monitoring layer underneath the cadenced deliverables. Mirrors the gofreddy client-portal telemetry pattern (per project-telemetry-audits-client-portal-2026-05-13 memory) — clients see the raw signal flow + their digests + the agency's interpretive overlay in one surface.

**N18. Compound-claim evidence-chain visualization.** When a digest cites a multi-week compound, the portal renders the evidence chain as a navigable graph (signal nodes + connective-tissue edges + dated provenance). Reader can trace any compound claim back to the source nodes. Defends compound-fabrication on the user-side too.

**N19. Required-silence calendar.** Per vertical-conventions §4.5: for regulated-vertical clients, maintain a per-client required-silence calendar — FDA pre-approval windows, SEC quiet periods, NRC classified-investigation windows. The MON workflow honors required-silence as a structural constraint, never recommends response during required-silence phases.

**N20. Per-event Coombs SCCT cluster classification + Benoit response-strategy recommendation.** For crisis-class events, the digest names the SCCT cluster (victim / accidental / intentional) and the implied response posture (denial / diminish / rebuild / bolstering) as the analytic reasoning behind the severity tier — not as a framework reference, but as the substrate of the recommendation.

**N21. Plaintiff-firm-attention-index for financial-services + healthcare + tort-exposed verticals.** Per vertical-conventions §2.6: plaintiff-firm IR-watching (the moment a 10b-5 firm files an investigation announcement) is a leading indicator of securities litigation. Track this as a per-client axis when vertical is exposed.

**N22. Short-seller-asymmetry weighting for financial-services + public-competitor verticals.** Per vertical-conventions §2.6: a single Hindenburg-grade short report moves a stock 20%; routine analyst notes don't. Weight by author-impact, not by mention count.

---

## §4. Vertical Adjustments

Per `docs/research/2026-05-18-monitoring-vertical-conventions.md`, the v1 spec already accommodates three decision shapes. The full vertical-adjustment surface:

### 4.1 SaaS (Series-B+ tech)
**Cadence**: standard weekly (Monday morning) + daily-pager for security incidents (SOC2 / ISO27001 / customer-data exposure).
**Primary axes**: A1 (brand mention), A4 (competitor activity), A6 (customer pulse), A13 (talent flow), A17 (AI engine citation), A19 (review monitoring).
**Severity orthogonal pair**: revenue-impact + customer-success-signal-velocity.
**Forward-projection window**: 6–8 weeks (renewal cycle + sales pipeline).
**Specific failure modes**: vanity-metric over-weighting (Twitter mentions without ESOV), HN-bias (over-weighting HN coverage in markets where HN ≠ buyer), missing LinkedIn-departure signal.

### 4.2 AI / AI-lab
**Cadence**: standard weekly + event-driven for capability-frontier announcements (OpenAI / Anthropic / Google DeepMind releases).
**Primary axes**: A1, A4, A5 (industry trend — capability frontier), A13 (researcher movement IS leading indicator), A17, A20 (podcast monitoring — Latent Space / Interconnects / Lenny's dominate category mindshare).
**Severity orthogonal pair**: capability-shift + market-positioning-shift.
**Forward-projection window**: 4–12 weeks (capability releases cluster).
**Specific failure modes**: paper-publication-volume over-weighting (signal-to-noise crisis), researcher-Twitter over-weighting without verifying production claims.

### 4.3 Agency / professional services
**Cadence**: standard weekly + monthly retainer-review brief + same-day for audit-quality findings / lateral-partner moves.
**Primary axes**: A1, A4, A8 (PR + crisis — partnership reputation IS balance sheet), A13 (lateral tracking, Chambers / Legal 500 tier-shifts), A19 (Glassdoor + Vault).
**Severity orthogonal pair**: partnership-reputation-impact + client-loss-cascade-risk.
**Forward-projection window**: 4–8 weeks (lateral arcs run quarters).
**Specific failure modes**: client-name-leak (regulatory violation), directory-publication-day burying, lateral-rumor-vs-confirmed confusion, partnership-culture-vs-public-mention-mismatch.

### 4.4 Service businesses (smaller in-market: aesthetic / dental / hospitality / retail / fitness)
**Cadence**: weekly + same-day for viral patient-safety / customer-incident events.
**Primary axes**: A1, A19 (Google Maps + Yelp + RealSelf + Healthgrades + Avvo dominant), A21 (local event monitoring), A22 (Glassdoor for small-team hiring health).
**Severity orthogonal pair**: local-reputation-impact + customer-acquisition-funnel-impact.
**Forward-projection window**: 1–4 weeks (local-market arcs short).
**Specific failure modes**: HIPAA-violating recommendations (healthcare practice), AMA/ACGME advertising-rule violations (healthcare), Klinika first-cohort overfit (clinical-visuals + before-after-imagery on content denylist per the Klinika rule set).

### 4.5 Finance (banks, asset management, insurance, fintech)
**Cadence**: event-driven + daily pre-market brief + weekly board-input + 8-K-trigger pager. Routine-weekly insufficient.
**Primary axes**: A1, A2 (Edelman competence-vs-ethics decomposition load-bearing), A7 (regulatory mandatory), A15 (earnings call parsing), A21 (plaintiff-firm IR-watching per N21), A22 (short-seller asymmetry per N22).
**Severity orthogonal pair**: materiality (SEC SAB 99) + velocity (regulator-clock proximity).
**Forward-projection window**: quarter-aligned (10-Q / 10-K cycle).
**Specific failure modes**: materiality miscalibration (Reg-FD exposure), selective-disclosure / Reg-FD bypass, sentiment-as-trust-proxy (SVB pattern — Twitter sentiment was lagging by 48h when wire-transfer outflows were the leading indicator), plaintiff-firm-attention-index ignorance, short-seller-asymmetry blindness.

### 4.6 E-commerce / DTC
**Cadence**: weekly + same-day for product-safety / supply-chain / payment-processor events.
**Primary axes**: A1, A6 (customer pulse — review velocity dominant), A19 (App Store / Play Store / Trustpilot / Amazon review monitoring), A16 (TikTok + Instagram creator-tier mentions dominant).
**Severity orthogonal pair**: conversion-funnel-impact + brand-trust-impact.
**Forward-projection window**: 1–4 weeks (seasonal-cycle-aligned).
**Specific failure modes**: creator-mention-volume over-weighting without engagement-quality decomposition, Amazon-listing-suppression incidents missed, supply-chain-disruption blindness.

### 4.7 Regulated industries (utilities, energy, telecom, defense, pharma, transportation)
**Cadence**: incident-driven, regulator-clock-anchored. NRC 10 CFR 50.72 (1–8 hour notification), FCC NORS (120-min), CMMC/DFARS (72-hour), FAA AD cycle.
**Primary axes**: A7 (regulatory mandatory + sector-specific), A8 (crisis detection in FAA-AD bulletin format), A9 (incident response).
**Severity orthogonal pair**: regulator-clock-proximity + operational-impact.
**Forward-projection window**: regulator-cycle-aligned.
**Specific failure modes**: required-silence misread (FDA pre-approval, NRC classified, DoD classified — per C14, N19), bulletin-format-drift, regulator-publication-day cycle synchronization.

---

## §5. Deliverable Architecture — Multi-Cadence Sibling-Lane Family

v1 ships ONE locked artifact (weekly digest). The 12-month roadmap forks the MON workflow into a sibling-lane family. Each sibling has its own optimal-output spec, structural_gate, and 4–6 judge criteria. Sibling-lane treatment is the more honest expansion than per-cadence flag on the same lane (per artifact-taxonomy open question #1).

### S1. MON-pager-tier (real-time pager alert)
**Form factor**: < 100 words. Subject line + 2–3 sentences. Mobile-first.
**Cadence**: event-triggered, 24/7. Volume target: 0–3 per week healthy state.
**Reader**: comms director on oncall rotation, agency duty officer, in-house counsel for reputational-legal events.
**Decision velocity**: sub-1hr.
**Structural gate**: alert-fatigue tier-distribution check (rolling false-positive rate ≤ 30% over 4 weeks), single-source-anchor required, named-escalation-owner required.
**Cross-pollination risk**: weekly-digest workflow learns to add pager-flavored "URGENT" stanzas — structural defense via lane-boundary structural_gate rejecting pager-shape on weekly lane.

### S2. MON-daily-brief (event-driven verticals)
**Form factor**: 300–800 words, 3–7 items.
**Cadence**: weekday mornings, 6–8am local. Event-driven verticals only (financial services pre-market brief, healthcare incident response). NOT a default lane.
**Reader**: C-level or chief-of-staff. Time budget: 5–10 minutes.
**Decision velocity**: same-day.
**Structural gate**: per-item ceiling 150 words, total ceiling 800 words, PDB-style multi-article structure enforced.
**Cross-pollination risk**: weekly-lane drift toward daily-brief shape (5–7 short items, no synthesis stanza) shortcutting MON-5/MON-6. Per artifact-taxonomy §5.

### S3. MON-weekly-digest (current v1, LOCKED)
**Form factor**: 600–1,400 words, 3–6 items, 80–250 words each. FullIntel triple per item. FAA-AD action items in closing stanza.
**Cadence**: weekly, Monday-morning modal delivery.
**Reader**: senior comms director / PR lead at Series-B-or-later.
**Decision velocity**: weekly action.
**Structural gate**: word band, item count, per-item ceiling, FullIntel triple presence, FAA-AD action-item structure, tier-distribution floor, banned-phrase list, URL HEAD checks, quote-grep, entity allowlist, evidence_dates.

### S4. MON-monthly-scorecard
**Form factor**: 2–4 pages, 800–1,800 words + 4–8 charts. AMEC Integrated Evaluation Framework + Barcelona V4.0 outcome-orientation.
**Cadence**: monthly, 5th–10th of following month.
**Reader**: VP of Communications, CMO, agency account director.
**Decision velocity**: resource-allocation review.
**Primary axes ingested**: A1, A2, A3 (ESOV math first-class), A5, A6, A8, A17 (AI engine citation trend), A19. KPI scorecard with month-over-month deltas.
**Structural gate**: chart-data-source verification, KPI-methodology-consistency check (undocumented methodology change forbidden), AVE-rejection (Barcelona V4.0 hard rule).

### S5. MON-quarterly-memo
**Form factor**: 5–15 pages, 3,000–8,000 words. Edelman Trust Barometer-grade decomposition. Narrative + trend.
**Cadence**: quarterly, 4–8 weeks after quarter-end.
**Reader**: C-level executive committee, board, retainer-client senior team.
**Decision velocity**: strategic rebalancing.
**Primary axes**: full surface (all 22), with trend-line synthesis across the quarter.
**Includes**: prior-quarter projection calibration scorecard (per N15).
**Structural gate**: citation density floor, primary-vs-secondary source ratio, evidence-chain integrity verification (compound-claim-fabrication defense).

### S6. MON-board-input
**Form factor**: 8–15 slides + speaker notes per slide.
**Cadence**: quarterly, aligned to board meeting cycle.
**Reader**: board of directors, audit / governance committee.
**Decision velocity**: governance oversight.
**Primary axes**: A2 (trust decomposition), A7 (regulatory + compliance), A8 (PR + crisis), A14 (M&A + funding), A21 (litigation). Narrative Contradictions framework (Harvard Law 2025) embedded as the analytic discipline.
**Cross-vertical override**: financial-services + regulated-industries clients require this lane; B2B SaaS does not until Series-D-plus.

### S7. MON-incident-postmortem
**Form factor**: 3–5 pages, 1,500–3,500 words. NTSB / CISA / SRE blameless-postmortem tradition translated to comms.
**Cadence**: event-triggered, 2–8 weeks post-incident. NOT a routine cadence.
**Reader**: crisis team, executive committee, sometimes board (escalated cases).
**Decision velocity**: process / playbook / training update.
**Primary axes**: per-incident, full retrospective surface.
**Structural gate**: timeline anchoring required, root-cause attribution required, named-corrective-action with named-owner-and-deadline required, blameless-language enforcement.

### S8. MON-ai-engine-citation-report (NEW, per N7)
**Form factor**: 2–4 pages, 800–1,800 words + per-engine visibility tables.
**Cadence**: monthly (initially), forking to weekly for AI-engine-priority clients.
**Reader**: CMO, Head of Growth, Head of Content, Head of SEO.
**Decision velocity**: content + GEO + AEO (Answer Engine Optimization) prioritization.
**Primary axes**: A17 (AI engine citation), A18 (knowledge graph), with cross-feed from A4 (competitor AI-engine SoV).
**Structural gate**: per-engine citation-frequency tracking, citation-tier classification (primary / one-of-many), citation-sentiment classification, hallucination flagging.
**Sources**: Profound + AthenaHQ + Daydream + Otterly + Peec + custom-prompt-controlled corpus runs against ChatGPT / Perplexity / Claude / Google AI Overviews / Gemini / Copilot.

### Multi-part vs multi-cadence single artifact?

**Recommendation**: **multi-cadence sibling-lane family, not single multi-part artifact**. Per artifact-taxonomy §5: a single hybrid artifact attempting all cadences produces a Frankenstein digest serving no coherent reader. Each sibling lane has a coherent reader, decision shape, and structural_gate. The cross-lane integration is **client-portal-level** (per N17), not artifact-level.

### Size envelope

Per current v1: weekly digest = 600–1,400 words.
Roadmap full surface:
- Pager: < 100 words per alert; cap 3 per week.
- Daily brief: 300–800 words per brief; weekday cadence.
- Weekly: 600–1,400 words (current).
- Monthly: 800–1,800 words + 4–8 charts.
- Quarterly: 3,000–8,000 words.
- Board input: ~400–800 deck words + 1–2 pages speaker notes per slide.
- Incident postmortem: 1,500–3,500 words.
- AI engine citation report: 800–1,800 words + tables.

---

## §6. Evolution-Loop Considerations

The selection pressure landscape changes when the lane forks. Per the v007/v008 / Phase 4 history catalogued in CLAUDE memory:

### 6.1 Lane-boundary structural defense

Each sibling lane's `structural_gate` MUST reject the other lanes' shapes explicitly. Per the artifact-taxonomy open question #5: cross-pollination risk between sibling lanes is real — the weekly lane might learn pager-flavored urgent stanzas; the monthly lane might learn weekly-flavored compression. Defense: each lane's structural_gate tests for its own out-of-scope shapes.

### 6.2 Fixture-corpus growth for the full surface

Current fixture corpus is heavily SaaS + AI-lab + legal + healthcare (Anthropic, Perplexity, DWF, Klinika). To validate the full surface without first-cohort overfit:
- Add financial-services fixtures (pre-market brief shape).
- Add regulated-industries fixtures (FAA-AD bulletin shape).
- Add e-commerce / DTC fixtures (review-velocity-dominant shape).
- Add founder-led-startup fixtures (Slack-thread-shape).
- Add small-practice fixtures (Klinika archetype extended — dental, aesthetic, hospitality, retail).
- Add public-company fixtures with real SEC filings (financial-services lane).

Trigger per vertical-conventions open question #5: any fixture from a non-current-cohort vertical prompts re-validation of the affected criteria.

### 6.3 Multi-week corpus prerequisite for compound detection

Per the judge-design step1 open question #1: MON-6 (compound-claim) requires multi-week context at judgment time. Current `evaluate_variant.py` pipeline may not pass multi-week context into the judge call. The full surface explicitly depends on this — every additional sibling lane (monthly, quarterly, board, postmortem) requires increasingly long-horizon corpus context.

**Architectural prerequisite for the full surface**: persistent per-client monitoring corpus with date-indexed retrieval, queryable by lane at evaluation time. This is a substrate-level change to the evolution loop; not a judge-prose change.

### 6.4 Calibration tracking surface

Per N5 + N15: Brier-scored projection calibration is a fixture-level instrumentation requirement. Every projection in a digest carries (a) a falsifiable conditional, (b) a window, (c) a confidence level. Quarterly, the calibration pipeline scores prior-quarter projections and feeds the Brier-tracked judgment register. This is an evolution-loop side-product, not a judge criterion per se.

### 6.5 Goodhart-collapse risks at the full surface

Beyond v1's catalog, the full surface introduces additional Goodhart pathways:

- **A17 (AI engine citation) gaming**: workflow learns that running 1000 prompts against ChatGPT scores well on "citation frequency" — the metric becomes prompt-corpus-dependent. Defense: standardized prompt corpus + tier-weighted citation analysis.
- **A12 (forward projection) sycophancy**: workflow learns that hedging every projection scores well on "calibrated confidence" — under-projects to avoid Brier penalty. Defense: require minimum projection-confidence-spread per digest.
- **A10 (compound narrative) apophenia compounding**: across multiple sibling lanes (weekly + monthly + quarterly), the same compound gets re-surfaced in three artifacts. Defense: cross-lane compound deduplication at structural_gate.
- **A11 (absence-as-signal) confabulation across lanes**: monthly scorecard fabricates "absences" not flagged in weekly digests. Defense: cross-lane absence-baseline verification — monthly absences must trace to weekly-digest absence-baseline anchors or be flagged as novel.
- **N15 calibration scorecard gaming**: workflow learns to under-project across the board to maintain a flatteringly-good Brier score. Defense: require minimum projection-count per quarter and minimum confidence-spread.

### 6.6 Cross-lane handoff loss

Per N12, N13, N14: monitoring hands off to CI / GEO / MA. The handoff is itself a deliverable that needs structural enforcement — if MON surfaces a strategic-implication-class signal and CI never picks it up, the handoff is broken. Defense: cross-lane handoff manifest tracked at the portal layer (per N17), with reciprocal acknowledgment from the receiving lane.

---

## §7. SOTA Exemplars — Quality Anchors, Not Templates

Per design-guide §4 + §11: exemplars serve as quality anchors. Naming them in the judge prose would invite framework-name-embedding pathology (per the Phase 4 rollback). Naming them HERE in the research deliverable is correct.

### 7.1 Classical / intelligence-tradecraft exemplars

- **President's Daily Brief (PDB)**. 6–7 single-paragraph articles + 2 deep-dives. Highest-stakes first. Multi-week thread continuity standard. Absence-of-expected-reporting treated as analytic comment. The format gold standard.
- **CIA Tradecraft Primer / Sherman Kent School** — *Analysis of Competing Hypotheses* (ACH) as discipline; "absence of evidence" as first-class analytic surface; "indicator-not-observed" as reportable signal.
- **Wohlstetter, *Pearl Harbor: Warning and Decision* (1962)** — canonical signals-to-noise post-mortem. Foundation for strategic-early-warning literature.
- **FM 34-2 *Intelligence Production* (US Army)** — PIR → Indicator → SIR crosswalk. Indicator-not-observed treated as collection product.
- **DOD JP 2-0 *Joint Intelligence*** — absence-of-expected-activity as reportable indicator state.
- **Heuer, *Psychology of Intelligence Analysis* (1999)** — ACH discipline; absence-of-evidence reasoning.
- **NTSB accident reports** — incident-postmortem canonical format; sections: factual narrative, analysis, probable cause, recommendations.

### 7.2 Corporate-crisis / PR exemplars

- **J&J Tylenol-era (1982) internal monitoring** — caught the cyanide cluster fast; routed actions to specific owners with named deadlines.
- **Wells Fargo whistleblower-pattern (2016 fake-accounts scandal)** — anomalous-silence-not-flagged failure; lessons in absence-as-signal absence.
- **BP Deepwater Horizon (2010)** — non-escalation pattern; engineering postmortem missed cultural root cause.
- **Boeing 737 MAX (2018–2019)** — Narrative Contradictions board-level governance failure; reputation signal contradicted publicly-stated narrative.
- **SVB collapse (2023)** — sentiment metrics lagging 48 hours when wire-transfer outflows were the leading indicator; Twitter-sentiment-as-trust-proxy failure.
- **Secret Service 2024 (Trump assassination attempt aftermath)** — buried-lede pattern in agency post-mortem.
- **Apple News withdrawal (early 2025)** — AI-summary feature withdrawn after compound-claim fabrication (real event + invented arc).

### 7.3 Severity / decomposition frameworks

- **Cision React Score** — Hazard + Emotionality dual-axis crisis severity.
- **Coombs SCCT (2007)** — victim / accidental / intentional crisis-type cluster + response-strategy mapping.
- **Benoit Image Restoration Theory (1995, 1997)** — denial / evasion / reduce-offensiveness / corrective-action / mortification taxonomy.
- **Peter Sandman Outrage Management** — Risk = Hazard + Outrage; outrage-factor categorization.
- **Edelman Trust Barometer 2026** — competence vs ethics decomposition; ~76/24 trust-capital split on B2B.
- **Aaker Brand Personality 5-factor** (1997) — sincerity / excitement / competence / sophistication / ruggedness.
- **Fiske Stereotype Content Model (SCM)** — warmth + competence as the two primary dimensions of social perception.
- **Dezenhall, *Glass Jaw*** — counterintuitive crisis-comms; "knee-jerk apology can draw attention to non-issue."

### 7.4 Measurement frameworks

- **AMEC Integrated Evaluation Framework** — outputs → out-takes → outcomes → organizational impact.
- **Barcelona Principles V4.0 (June 2025)** — "AVE is not the value of public relations"; outcomes-not-outputs.
- **PRSA Measurement Standards** — industry-association KPI set.
- **PRovoke Media annual Crisis Review** — public post-mortem teaching corpus.

### 7.5 Tradecraft / calibration

- **Tetlock Good Judgment Project / *Superforecasting* (2015)** — top-2% calibration habits; hedgehog-vs-fox classification; "flag absence-of-pattern when stakeholders want a story."
- **Brier scoring** — quadratic-loss probabilistic-forecast accuracy metric.
- **Mellers et al. (2014)** — superforecaster characterization study.
- **Ansoff (1975) "Managing Strategic Surprise"** — weak-signal SEWS framework.
- **Day & Schoemaker, *Peripheral Vision*** — strategic-blind-spot taxonomy.
- **Weick sensemaking** — organizational signal-interpretation literature.

### 7.6 Vendor-side modern exemplars

**Conventional monitoring vendors (2024-era baseline):**
- **Cision** — Komo crisis push + React Score dual-axis severity.
- **Meltwater** — Mira AI weekly synthesis + Explore conversational analytics.
- **Brandwatch** — Vizia + Iris real-time + Consumer Research panels.
- **Talkwalker** — Quick Search alerts + crisis-room dashboards (Deutsche Telekom case study).
- **Onclusive** — formerly AirPR + Critical Mention + Kantar Media; analyst-curated daily briefs.
- **Mention** — mid-tier real-time alerts.
- **Brand24** — small-business mid-tier.
- **Determ, Awario, Prowly, Notified, Sprout Social, Sprinklr, Hootsuite, Buffer** — adjacent tier.

**Strategic-monitoring / market-intelligence (2024-era):**
- **AlphaSense (incorporates Sentieo)** — earnings-call transcripts + filings + expert calls.
- **Bloomberg Intelligence** — sector briefs; quantitative anchor + named comparable.
- **Gartner / Forrester / IDC** — analyst briefings + Magic Quadrant / Wave methodology.
- **CB Insights** — funding + M&A trend + State of (X) reports.
- **PitchBook, Crunchbase, Mergermarket** — funding / M&A databases.

**AI-engine citation monitoring (2026-defining new tier):**
- **Profound** — Series A 2026; dedicated AI-engine visibility scoring.
- **AthenaHQ / Athena** — visibility across ChatGPT, Perplexity, Claude, Google AI Overviews.
- **Daydream** — LLM SEO + answer-engine optimization.
- **Otterly.ai** — AI search visibility tracking.
- **Peec AI** — LLM brand mention monitoring.
- **Scrunch AI** — AI search ranking + content optimization.
- **Bluefish AI** — LLM brand tracking.
- **Goodie** — AI citation + content recommendations.
- **HubSpot AI Search Grader** (free tier).
- **SE Ranking AIO tracker, Semrush AI Toolkit, Ahrefs Brand Radar** (incumbent SEO vendors adding AI-citation modules).

**Crisis-team / SOC-flavored tooling:**
- **PagerDuty** for reputation-event routing (increasingly common 2024–2026 pattern).
- **Slack-integrated** Brandwatch / Talkwalker / Mention alerting.
- **Crisis-room dashboards** — Talkwalker, Brandwatch, Onclusive.

**Knowledge graph / Wikidata:**
- **Kalicube** — branded SERP / knowledge panel tracking.
- **Wikidata Query Service** for direct property monitoring.
- **Wikipedia Watchlist** for editorial-grade change tracking.

**Podcast monitoring:**
- **Listen Notes, Podchaser, Podscan, Snipd** for transcript-grounded mention monitoring.
- **Speechmatics, AssemblyAI, Whisper.cpp** for transcript extraction.

**Personnel / talent flow:**
- **TheirStack, Predictleads, Champify, LeadIQ, Cognism** for systematic LinkedIn-move tracking.
- **Leopard Solutions Firmscape** — legal-services lateral-tracking canonical.
- **Above the Law** — legal trade-press lateral coverage.

**Litigation:**
- **Court Listener, PACER, RECAP, Stanford Securities Class Action Clearinghouse.**

**Practitioner-side modern executive-briefing exemplars:**
- **FullIntel executive briefings to Fortune 500** — "what happened / why it matters / recommended action" triple; "long briefings signal poor judgment."
- **Axios PM, Punchbowl AM** — smart-brevity format with named-source anchors.
- **PRWeek Weekender, Bulldog Reporter Friday** — agency-cadence weekly digests.
- **ArchIntel Daily Intelligence Brief** — 6am newsletter format.

**Practitioner-side modern researcher / writer exemplars:**
- **Stratechery (Ben Thompson)** — long-form market analysis; per-event interpretation.
- **Latent Space (Shawn Wang / Alessio Fanelli)** — AI category news + interviews.
- **Interconnects (Nathan Lambert)** — AI research-frontier weekly.
- **Lenny's Newsletter (Lenny Rachitsky)** — product-management weekly.
- **The Generalist (Mario Gabriele)** — strategy + investing.
- **Not Boring (Packy McCormick)** — culture + technology + finance.
- **Every (Every Inc.)** — software + ideas weekly.
- **First Round Review** — startup operator content.
- **Software Engineering Daily (Jeff Meyerson legacy + new)** — technical-deep-dive daily.

**Crisis-comms practitioner books:**
- **Dezenhall, *Glass Jaw*** — counterintuitive crisis-comms.
- **Coombs, *Ongoing Crisis Communication*** — SCCT canonical.
- **Benoit, *Accounts, Excuses, and Apologies*** — image-restoration canonical.
- **Brandwatch *Crisis Management Playbook***.

---

## §8. Open Questions

These are genuinely unresolved for the full-surface scope — beyond v1's open questions in `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` §8.

**Q1. Sibling-lane fork sequence.** When do the 7 additional sibling lanes (S1, S2, S4, S5, S6, S7, S8) get forked from the v1 weekly digest lane? Recommendation: fork sequence by client-demand pull, not by capability push. Trigger: any first-cohort client requesting (or any prospect rejecting because of the lack of) a specific sibling-shape. Predicted sequence: S8 (AI engine citation) → S1 (pager-tier crisis) → S5 (quarterly memo) → S4 (monthly scorecard) → S6 (board input) → S2 (daily brief, event-driven verticals only) → S7 (incident postmortem, event-triggered only).

**Q2. Cross-lane handoff manifest format.** Per N12, N13, N14: handoffs to CI / GEO / MA need a structured format. Recommendation: per-event handoff record at portal layer with (a) source-lane, (b) target-lane, (c) signal-class, (d) recommended-next-step, (e) target-lane acknowledgment. Defer schema until first cross-lane integration ships.

**Q3. Persistent per-client monitoring corpus architecture.** Per §6.3: multi-week + multi-month + multi-quarter corpus retrieval is an architectural prerequisite. Where does this live? Recommendation: client-portal substrate (per project-telemetry-audits-client-portal memory) with date-indexed retrieval; lane-side `evaluate_variant.py` passes corpus context per cadence.

**Q4. Calibration scorecard surface.** Per N15: prior-quarter projection scoring. Should this be (a) per-client (private to that client), (b) per-agency (aggregate gofreddy reputation surface), or (c) per-lane (calibration as part of evolution-loop selection)? Recommendation: all three; per-client lives in client portal, per-agency lives in marketing surface (a credibility moat), per-lane feeds evolution-loop fitness.

**Q5. AI engine citation methodology drift.** Per A17: AI engines change their grounding behavior frequently. A consistent prompt-corpus today may produce different citation patterns in 6 months as the engines re-train. Recommendation: refresh prompt-corpus quarterly + version-tag the methodology + surface methodology drift in the quarterly memo.

**Q6. Required-silence calendar maintenance.** Per N19: per-client required-silence calendar requires regulatory-affairs awareness. Who maintains it? Recommendation: agency-side maintenance with client review; flagged in the client portal; structural_gate honors it per-period.

**Q7. Plaintiff-firm IR-watching scope.** Per N21: 10b-5 plaintiff-firm tracking is load-bearing for financial-services and tort-exposed verticals but not for SaaS / agency / DTC. Should this be a per-vertical opt-in axis (default-off for non-exposed verticals) or always-on? Recommendation: per-client vertical flag drives inclusion; structural_gate enforces.

**Q8. Founder-visibility axis weight calibration.** Per N9: founder-visibility IS brand monitoring for founder-led-startups but is a minor axis for Series-D-plus. The axis weight is vertical+stage-dependent. How does the lane learn the right weight? Recommendation: client onboarding intake collects "founder-visibility-priority" flag; weight calibrated by client confirmation, not auto-learned (evolution-loop selection pressure would overfit to first-cohort default).

**Q9. Compound-narrative deduplication across sibling lanes.** Per §6.5: same compound surfacing in weekly + monthly + quarterly. Cross-lane deduplication mechanism? Recommendation: portal-level compound-graph with timestamped surfacing per lane; lane structural_gate checks against the graph to avoid re-surfacing without new signal.

**Q10. First-cohort overfitting risk on the full surface.** v1's spec is already at risk per first-cohort overfit feedback. The full surface (22 axes) compounds the risk — more axes = more dimensions of overfit. Recommendation: explicit per-axis vertical-coverage matrix tracked in the lane spec; trigger re-validation when a new vertical's fixtures don't match the current axis-weight pattern.

**Q11. AI-on-AI moat sustainability.** Per the framing: compound-narrative + AI-engine-citation are the AI-native-agency moats vs incumbent monitoring vendors. How sustainable are they? Predicted: Cision / Meltwater / Brandwatch will add AI-engine-citation modules within 12 months (some have started — Cision Insights, Meltwater Mira AI). The moat narrows. Recommendation: the durable moat is the integration — agent-native-architecture (per CLAUDE skill `agent-native-architecture`) where the monitoring agent has bidirectional access to the client's GEO / MA / CI lanes. Vendor monitoring can't integrate horizontally; AI-native agency can.

**Q12. Multi-client agency-tier digest variant.** Per v1 open question #4: substitute reader #2 ("agency lead on behalf of multiple clients"). Recommendation per artifact-taxonomy open question #4: one-client-per-digest as modal case; multi-client roll-up explicitly out-of-scope until a multi-client-managing-firm cohort emerges as primary persona (which is not the current gofreddy direction — gofreddy is the agency, not a tool for other agencies).

**Q13. The "AI-engine citation" vs "GEO" lane boundary.** A17 (AI engine citation monitoring) overlaps the GEO lane's mandate. Is this a MON axis or a GEO axis? Recommendation: MON owns the **measurement** (how often the brand surfaces in answer engines, in what tier, with what sentiment); GEO owns the **optimization** (what prompts to test, what content to publish to influence citations). Bidirectional handoff per N13.

**Q14. The "founder visibility" vs "site engine" lane boundary.** N9 (founder-visibility monitoring) overlaps site_engine's mandate around founder-as-distribution. Recommendation: MON owns the **measurement** (where the founder appeared, with what reach, sentiment, topic clustering); site_engine + X + LI lanes own the **production** (what the founder writes / says / records). Bidirectional handoff.

**Q15. Modernization risk — over-indexing on AI-engine citation.** Per N7 + Q11: AI-engine citation is the 2026-defining new axis, but indexing too heavily on it risks (a) the methodology becoming stale within 18 months as AI engines change grounding, (b) the metric becoming a vanity number like SoV was in 2014. Recommendation: lead with it for client acquisition (it's the "we cover something nobody else does" lever), but balance with the classical surface (A1 + A2 + A4) so the lane's value is durable across methodology shifts.

---

## Closing Note

The current v1 weekly-digest lane is the **right scope for the current evolution-loop selection pressure on the current first-cohort fixture corpus**. Don't fork it before the substrate supports multi-week corpus retrieval (§6.3). Don't broaden the criterion surface (currently 6 with two documented exceptions) — the §5 ≤5 ceiling discipline holds.

The full surface (22 axes × 8 sibling-lane form factors × 3 cadence shapes × 7 vertical adjustments) IS the 12-month roadmap, not the v1 spec. The roadmap fork sequence is client-pull-driven (per Q1), not capability-push. The single-highest-leverage modernization to lead with for new clients is **AI engine citation monitoring** (A17 / S8 / N7) — the 2026-defining axis no 2024-era vendor covers credibly yet.

The architectural moat is integration — agent-native-architecture where the monitoring agent has bidirectional access to CI / GEO / MA / X / LI / site_engine lanes. Vendor monitoring (Cision, Meltwater, Brandwatch) can't integrate horizontally with the client's full marketing surface; an AI-native agency can. That's the durable answer to Q11.

The single largest open architectural question is Q3 (persistent per-client monitoring corpus). Without it, compound-narrative detection (the strongest LLM-native lever) is bottlenecked by the substrate. With it, the lane can ship into the full sibling-lane family at production grade. Surface for substrate-roadmap prioritization.
