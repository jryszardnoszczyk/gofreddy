---
date: 2026-05-19
type: research deliverable — comprehensive scope mapping
status: draft v1 — supersedes the implicit "3-cluster A/B/C routing" framing in the 2026-05-18 MA Step-1 spec
topic: Marketing Audit (MA) workflow — full comprehensive 149-lens surface, CUT/REDUCE/ADD framing, deliverable architecture
parent_handoff: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md
supersedes_framing_in:
  - docs/research/2026-05-18-marketing-audit-decision-format-mapping.md (3-cluster A/B/C routing — REJECTED by JR 2026-05-19)
  - docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md §1, §1.5, §2 (cluster-routed reader/artifact/success framing — REJECTED)
preserves_from_prior_research:
  - docs/research/2026-05-18-marketing-audit-vertical-conventions.md (vertical × stage axis — KEPT as v-axis)
  - docs/research/2026-05-18-marketing-audit-ai-failure-modes.md (5 LLM failure surfaces — KEPT)
  - docs/research/2026-05-18-marketing-audit-upstream-diagnostic.md (6 upstream classes + sequencing — KEPT)
  - docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md (149-lens catalog — LOAD-BEARING)
  - autoresearch/archive/v006/workflows/session_eval_marketing_audit.py (live MA-1..MA-8 + capability_registry substrate — LOAD-BEARING)
guide: docs/rubrics/judge-design-guide.md
audience: gofreddy operators + judge-design Step 2/3 sessions + evolution-loop iteration on the MA lane
---

# Marketing Audit — Comprehensive Scope Mapping

> Companion deliverable that maps the **full surface** of the Marketing Audit
> workflow — what it audits, what it CUTS, what it REDUCES, what it ADDS,
> what it delivers, and how the evolution loop iterates on it.

---

## TL;DR

The Marketing Audit (MA) workflow is the most important commercial artifact gofreddy ships. It is not a "Day-30 fractional-CMO deliverable," not a "channel-cut memo," not a "fire-CMO verdict." It is a **comprehensive 2026-current diagnosis of the client's marketing reality across ~149 auditable lenses organized into 12 macro-axes, ending with a strategic prescription — explicit CUTS, REDUCES, and ADDS — that names the most valuable marketing strategy going forward for that specific company at its specific stage in its specific vertical.**

The 3-cluster A/B/C routing pattern recommended in the 2026-05-18 decision-format-mapping research is **rejected**. It was a sibling-to-CI design move that imported the wrong framing into MA. CI's clusters survive because CI artifacts serve genuinely different decision shapes at non-overlapping irreversibility-horizons (war-game posture vs evaluate vs monitor). MA artifacts do not split that way at the artifact level — every credible MA client wants the same thing: a comprehensive audit of where they are now and a prescription for where to go. The decision-shape variance (personnel / operational / strategic) shows up inside the prescription's emphasis, NOT as separate artifact types.

The comprehensive MA produces:

1. **State-of-the-business opener** anchored on 9 Phase-0 meta-frames already wired in v006 (traffic mix, channel-model fit, traffic trajectory, growth-loops inventory, maturity tier, share-of-voice, geo mix, north-star vs vanity tells, engagement-tier proxies).
2. **12-macro-axis diagnostic** covering ~149 always-on lenses + vertical / geo / segment bundles (per `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`), with SubSignal → ParentFinding rollup so the deliverable surfaces ~25-32 strategic findings, not 149 line items.
3. **Strategic narrative** — one organizing argument that ties the diagnosis together.
4. **CUT prescription** — what to stop doing, with reasoning per cut (typically banner-display retargeting, broetry-style LinkedIn, classic-SEO keyword-stuffing, generic content-calendar cadence, broad outbound, paid-only-acquisition thinking, vanity-metric reporting, generic case studies, logo-wall-only social proof, "leverage social media" platitudes, generic email-drip).
5. **REDUCE prescription** — what to dial back (typically over-allocated paid budgets, over-broad ICP, generic email volume, low-leverage channel sprawl, agency-of-record sprawl, MQL-volume-as-headline).
6. **ADD prescription** — what to start doing with budget and named owners (typically founder-led content, LinkedIn + X audience-building, AEO-native presence, distribution-first content engineering, comparison-page warfare, named-customer case studies, demo-direct CTAs, modern algorithmic signals, brand-mention engineering, comment-magnet engineering).
7. **The most valuable marketing strategy going forward** — a single organizing thesis. Not a buffet of options.
8. **30/60/90 execution plan** with owners, budgets, success metrics, kill-triggers, and Day-45 founder-impatience off-ramps.
9. **Capability-registry mapping** — every recommendation tier-mapped to `fix_it` / `build_it` / `run_it` so the audit IS a credible $15K–$150K agency engagement pitch, not a $1K one-off PDF.

Size envelope: **8,000-18,000 words** in a multi-part deliverable (4-7 files), not a 2,000-4,500 word memo. The earlier MA Step-1 spec's word-count band was scoped down to fit a "founder Tuesday-afternoon skim" frame; that frame undersells the artifact. Tech-savvy founders WILL spend 90 minutes on a 15,000-word document if it lands strategic conviction. The Bell Curve audit, the ProfitWell pricing teardown, and Kalungi's 95-point B2B SaaS audit all sit in this range or above. We match that ceiling.

This deliverable is structured: TL;DR / §1 the full 149-lens surface mapped to 12 macro-axes / §2 CUTS / §3 REDUCES / §4 ADDS / §5 vertical adjustments / §6 deliverable architecture / §7 evolution-loop considerations / §8 SOTA exemplars / §9 open questions.

---

## 1. The full comprehensive surface — 12 macro-axes, ~149 lenses

The 2026-04-23 locked lens catalog (`docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`) defines 149 always-on lenses plus vertical / geo / segment bundles. This research re-maps those 149 onto **12 macro-axes** that an actual senior marketer would recognize as the comprehensive surface of a 2026 audit. The 11-marketing-area view in the catalog is engineering-shaped (lens-bucket counts); the 12-axis view below is reader-shaped (how a CRO / founder / fractional CMO thinks about the marketing program). They cover the same 149 lenses with one re-bucketing — see Axis 12 notes.

The 12 axes correspond to the questions a senior operator asks in order. The audit walks them in order. Each axis can fire as a strong / weak / neutral finding; only the strong findings become ParentFindings.

### Axis 1 — Strategic Foundations (Positioning, ICP, Category)

The upstream-of-marketing layer. If this is broken, every downstream channel investment is leverage on a misalignment. **~12 lenses** sit here, drawn from the catalog's Area 9 Brand & Authority plus Phase-0 meta-frames.

- **Positioning (Dunford-grade)** — does the buyer understand the category, the alternatives, the unique value? Surfaces from win-loss interviews, comparison-page conversion, sales-call transcripts, "how would you describe what we do" customer responses, founder-narrative-vs-public-positioning drift.
- **ICP sharpness** — is one cohort getting >2× the value of another? Bimodal sales conversion, expansion-revenue concentration, customer-success effort variance >3×, churn cohorts by ARR band.
- **Category placement** — are we riding an existing category, sharpening a sub-category, or trying to create one? Implication: messaging investment differs by 10× between these.
- **Customer-language alignment (JTBD framing)** — do customers describe the product in the buyer's language or the company's language? Wynter-style messaging-resonance signal.
- **Founder narrative coherence** — does the founder's public voice + latest fundraising deck + last keynote say the same thing as the homepage and pricing page? Repositioning costs cascade through this surface.
- **Customer switching narratives** — does the audit-target have `/switch-from-X`, `/migrate-from-Y` pages? Counter-positioning surface.
- **Marketing-Jiu-Jitsu / counter-positioning** — does the audit-target lean INTO its competitor's strengths (the "we're the simpler alternative to bloated Salesforce" play)?
- **Brand differentiation (BAV vitality / stature)** — measurable brand-equity proxy.
- **Brand personality consistency / voice drift** — does the audit-target sound like one company or three?
- **AI-generated copy density ("AI tells") in OWN copy** — does the brand sound human, or has the marketing team papered the site with GPT slop?
- **Brand salience proxy** — Google Trends branded-search trajectory; the slowest of all lagging indicators but the most truthful.
- **Strategic-narrative coherence** — does the company's public-facing story compose? (Andy Raskin / Drift territory.)

**Why this axis is named first.** The Step-1 MA-5 criterion encodes "when upstream-of-marketing is the constraint, name it and sequence behind it." The reason MA-5 is load-bearing is that ~40% of MA audits should conclude "the binding constraint is upstream — pause marketing investment until the strategic foundation is fixed." Putting this axis first in the walk-order disciplines that judgment.

### Axis 2 — Demand Diagnostics & Stage Map (Where the company actually sits)

Phase 0 meta-frames + early-axis diagnostics that locate the company on a stage map BEFORE any tactic recommendation. **~10 lenses.**

- **Traffic-mix ratio** — direct vs organic vs paid vs social vs referral vs email (Phase 0).
- **Channel-model fit (Balfour Four Fits)** — does the channel mix match the business model? Self-serve + outbound is structural mismatch; PLG + ABM is structural mismatch.
- **Traffic trajectory 12-month delta** — Phase 0 leading indicator.
- **Growth-loops vs funnel inventory** — Reforge framing; does the company have any loops, or is it funnel-only?
- **Marketing-maturity tier** — Kotler / Forrester 6-axis (positioning / segmentation / customer-research / brand / digital / measurement).
- **Geo / country mix vs ICP** — ICP-channel mismatch detector.
- **North-star metric / vanity-metric tell** — does the audit-target lead with MQLs or with payback?
- **Engagement-tier proxies** — bounce / session-duration / pages-per-session.
- **Share-of-voice vs named competitors** — branded-search + SOV in target keywords.
- **Stage anchor** — ARR band (SaaS), location count (services), monthly revenue (DTC), pipeline composition (regulated B2B). MA-4's load-bearing anchor.

### Axis 3 — Discoverability (Organic Search + AEO + AI-citation)

The "can the prospect find us" layer in a 2026 world where 30-60% of B2B research now starts in ChatGPT / Claude / Perplexity rather than Google. **~24 lenses.**

- **Technical SEO health** — CWV, security headers, redirects, sitemap, canonicalization, mobile-friendliness, URL structure, orphan pages, 4xx/5xx coverage.
- **On-page SEO** — title tags, meta, H1, depth, alt-text, intent match.
- **Internal linking + hub-and-spoke** — anchor-text distribution, orphan-page ratio.
- **International SEO** — hreflang, self-referencing integrity, RTL rendering, local case studies, locale URL structure.
- **EEAT signals** — author entity, about-page depth, editorial-standards, citation density.
- **Programmatic SEO posture** — templated-content detection, unique-value-per-page, index discipline.
- **Site architecture / IA** — navigation depth, taxonomy, breadcrumb-URL alignment.
- **Content pillars / topic clusters** — pillar identification, cluster coverage, format-diversity index.
- **Buyer-stage keyword coverage** — awareness / consideration / decision / implementation balance.
- **Content refresh discipline** — content half-life via sitemap lastmod + Wayback decay.
- **Parasite SEO / external publishing** — Medium, LinkedIn, Substack distribution.
- **AI search citation patterns** — actual AIO presence (ChatGPT / Claude / Perplexity / Google AIO citation rate for the target's key queries). Use Profound / Peec / Otterly / AthenaHQ if instrumented; otherwise SERP-probe sample.
- **Schema stacking for AI citation** — 3-4 complementary @types per page.
- **PDF gating posture for Perplexity** — form-walled PDFs lose citation; the gating model has changed in 2026.
- **Bing Webmaster + IndexNow posture** — Copilot citation prerequisite.
- **Brave Search visibility** — Claude citation prerequisite.
- **AI bot access (differentiated training-vs-answer-engine policy)** — GPTBot, ClaudeBot, CCBot, Google-Extended for training; OAI-SearchBot, ChatGPT-User, PerplexityBot, Claude-SearchBot, AppleBot-Extended for answer engines. Blanket blocks usually wrong.
- **llms.txt / machine-readable files / markdown twins** — low-weight in 2026 but signaling.
- **Content extractability for LLMs** — semantic HTML + lead-answer format.
- **Wikipedia entry quality + monitored status** — load-bearing for AEO; AIs preferentially cite Wikipedia.
- **Glossary / `/learn-X` long-tail** — AEO-grade.
- **Searchable vs shareable content balance** — Rachitsky framing.
- **Agent-card / MCP discoverability** — 2026 emerging.
- **Product feed for AI commerce (UCP + Product JSON-LD)** — 2026 emerging for DTC.

### Axis 4 — Content Engine + Authority

The "do we have content that actually compounds" layer. **~10 lenses.**

- **Lead-capture asset inventory** — free tools, lead magnets, templates, calculators, engineering-as-marketing.
- **Research reports / "State of X" authority plays** — Lattice's State-of-People-Strategy, Vanta's State-of-Trust, OpenView's SaaS Benchmarks pattern.
- **Proprietary data journalism** (`/insights`, `/benchmarks`) — owned-data plays.
- **Courses + books** — authority depth.
- **Thought-leadership program** — sustained public output cadence.
- **Owned podcast** — distribution + brand-equity hybrid.
- **Customer-research-driven content** — JTBD interviews → content.
- **Distribution ratio** — Ross Simmonds: "create once, distribute forever" — does each piece of content get 8+ distribution surfaces, or zero?
- **Content half-life and refresh** — does old content keep ranking, or decay to zero in 18 months?
- **Searchable + shareable balance** — Lenny / Hockenmaier framing; companies that lean 100% searchable miss compounding social.

### Axis 5 — Paid Acquisition + Performance

The "how efficiently are we converting cash to demand" layer. **~12 lenses.**

- **CAC by channel** — paid Google, paid LinkedIn, paid Meta, paid TikTok, paid Reddit, paid Quora, paid X, paid Pinterest, paid Snap, retargeting, programmatic — every channel separately.
- **CAC payback by channel** — Bessemer / OpenView benchmarks per channel: <12mo SMB, <18mo mid-market, 24+mo enterprise.
- **Paid creative corpus** — Foreplay / Adyntel hook taxonomy; spend intensity per creative angle.
- **Ad creative format diversity** — RSA / Meta / LinkedIn / TikTok native; not just "ran Google Ads."
- **Pre-targeting / warmup ad strategy** — does the company sequence cold→warm→hot, or just cold-bomb?
- **Retargeting pixel coverage** — Meta + LinkedIn + Google + TikTok + Reddit pixels; site-wide vs page-type.
- **Paid platform breadth** — Google / Meta / LinkedIn / TikTok / Reddit / Quora.
- **Competitive ad research** — what creative is the competition running? Foreplay, AdSpy, MagicBrief.
- **Incrementality testing posture** — for DTC: geo-holdout, Haus, Northbeam, Recast. Post-iOS-14.5 Meta and Google systematically over-credit themselves; without incrementality, paid budget allocation is fiction.
- **MMM infrastructure** — Meridian / Robyn / Recast presence.
- **Attribution maturity** — first-touch / last-touch / multi-touch / MMM; server-side GTM, Conversions API, Enhanced Conversions.
- **Channel saturation signal** — Andrew Chen's Law of Shitty Clickthroughs: is marginal CAC rising 15% QoQ?

### Axis 6 — Earned + Distribution-First

The Ross Simmonds layer — the "are we getting found by humans because we're useful, not because we paid" layer. **~14 lenses.**

- **Press coverage + tier distribution** — Tier 1 (NYT / WSJ / FT / WP / TechCrunch), Tier 2 (industry trade), Tier 3 (vertical blogs).
- **Analyst relations posture** — Gartner / Forrester / IDC engagement + included-in-coverage.
- **Founder / exec content posture** — LinkedIn (daily? weekly? monthly?), Substack, podcast guesting, conference speaking, on-camera presence.
- **Podcast guesting at scale** — CEO ≥6 in 12 months + guest-graph centrality.
- **Awards + "as seen in" badges** — third-party validation density.
- **Press / media kit + newsroom freshness + journalist-quote density** — does a journalist want to write about you?
- **"Best-of" editorial listicle inclusion** — am I in "Top 10 X tools" pieces?
- **Distribution mechanics per piece** — Simmonds 8-channel repurposing rate: does each piece hit Twitter / LinkedIn / Reddit / Hacker News / podcast / video / newsletter / community?
- **Comment-magnet engineering** — does the LinkedIn / X content invite replies? (Algorithm-2026 favors comment-density.)
- **Brand-mention engineering** — am I being mentioned in places I don't own (Reddit, Hacker News, Twitter threads)?
- **Hacker News submission history** — Show HN cadence, comment-thread quality.
- **Developer hackathon presence + sponsor-of-record** — for dev-tool verticals.
- **Creator / ambassador program** — `/creators`, `/ambassadors` infrastructure.
- **Organic social footprint** — Twitter / LinkedIn / Instagram / TikTok / YouTube cadence + quality.

### Axis 7 — Owned Audience + Founder-Led

The 2026-current layer that didn't exist in 2018 audits. The dominant high-leverage acquisition surface for tech-savvy founders today is the founder's own public voice + the audience they build. **~10 lenses.**

- **Founder LinkedIn presence** — daily / weekly cadence, original POVs, comment-magnet quality, follower trajectory.
- **Founder X / Twitter presence** — daily / weekly cadence, original POVs, reply-engagement quality.
- **Founder podcast guesting** — covered in Axis 6, scored here for owned-audience leverage.
- **Founder owned podcast / Substack** — long-form owned-distribution.
- **Founder on-camera presence** — YouTube channel, conference talks, sales-cycle video assets.
- **Owned community** — Slack / Discord / Circle / Skool — depth, retention, founder participation.
- **OSS community depth** — for dev-tools.
- **Email list growth + lead-magnet engineering** — does the audit-target capture and nurture email subscribers? List growth trajectory.
- **Topic Authority compounding** — does the founder own one topic in their niche (Patrick Campbell = pricing; Brian Balfour = retention; April Dunford = positioning; Ross Simmonds = distribution)? Or is the voice scattershot?
- **Audience-quality signal** — is the LinkedIn audience the actual buyer, or VCs / employees / consultants?

This axis is one of the two axes most often misaudited in 2026 — Cluster B "channel-cut audits" from 2018 don't have it; ADD-grade prescriptions live here.

### Axis 8 — Conversion Architecture + Pricing

The "do we close once they show up" layer. **~14 lenses.**

- **Value-prop clarity + above-fold + CTA hierarchy** — 5-second test.
- **Case studies depth + recency + breadth** — by vertical, by use-case, by company size; quoted-customer presence.
- **Pricing page architecture + transparency** — visible price vs "Contact us," value-metric clarity (per-seat vs per-event vs per-volume), tier-comparison ergonomics.
- **Comparison-page strategy** — `/vs-X`, `/alternatives`, `/comparison-hub`, structured-data, comparison-page conversion rate.
- **Integration-page warfare** — for SaaS/AI: `/integrations/[partner]`, partner-logo wall, integration-tier specificity.
- **Form CRO** — demo / contact / lead.
- **Signup flow CRO** — for PLG.
- **Demo / trial flow architecture** — booking friction, time-to-demo, demo conversion rate.
- **Logo wall + dead-logo-ratio + social-proof density** — does the homepage show 20 logos including 4 that are dead customers?
- **Trust signals density** — refund / guarantee / returns visibility, SOC 2, security badges, customer count, ratings count.
- **Page CRO by page type** — homepage vs landing vs pricing vs feature.
- **Popup CRO** — triggers, copy, frequency, compliance.
- **Booking friction** — Calendly / SavvyCal / Chili Piper / HubSpot Meetings; time-to-meeting after demo request.
- **Offer construction** — anchor pricing, bonuses, urgency authenticity, risk reversal.
- **Marketing-psychology cross-cut** — Cialdini-6 density (authority / scarcity / reciprocity / social-proof / commitment / liking), scarcity authenticity.

**Pricing as marketing — Patrick Campbell territory.** Pricing-page warfare is the single highest-leverage conversion lever and the most under-audited. The audit must engage it explicitly, not defer it to "pricing is out-of-scope."

### Axis 9 — Activation + Product-Led + Retention

The "do they stay" layer. **~13 lenses.**

- **Onboarding CRO** — aha moment, checklist, empty states, tours.
- **Activation metrics** — D7, D30, time-to-first-value, activation-rate by cohort.
- **Freemium / free-tier / migration tools** — competitive switching cost reduction.
- **Public API / developer portal** — for dev-tools.
- **Help center / docs maturity** — knowledge base depth, recency, helpful widget, search quality.
- **AI-feature marketing** — ChatGPT GPT Store + Copilot + Perplexity Spaces + MCP server presence.
- **Viral loops / PLG distribution signals** — invite-flow, share-with-team, watermark loops.
- **Public roadmap** — Productboard / Canny / GitHub Projects.
- **"Powered by X" badge detection** — distribution loop.
- **Changelog / public release cadence** — author attribution, frequency.
- **Welcome / onboarding email sequence** — quality, length, personalization.
- **Cancel flow / churn prevention UX** — MRR-tier routing, save offers.
- **Effort asymmetry** — clicks-to-cancel vs clicks-to-buy (Forrester CXi).
- **NPS survey program** — Delighted / Wootric / SurveyMonkey, response rate, NPS by cohort.

### Axis 10 — Lifecycle + Retention + Expansion

The "do they buy more over time" layer (separate from activation; this is the post-activation revenue engine). **~10 lenses.**

- **Email deliverability posture** — SPF / DKIM / DMARC / BIMI / MTA-STS.
- **Lifecycle stack maturity** — Customer.io / Iterable / Klaviyo / HubSpot / Salesforce Marketing Cloud feature use.
- **Product usage digest emails** — daily / weekly / monthly cadence + quality.
- **Win-back / trial-reactivation sequences** — does the company recover dormants?
- **Milestone / achievement emails** — engagement amplifier.
- **Billing email suite** — renewal / failed-payment / cancel-survey / annual-switch.
- **Customer advocacy programs** — champion-of-the-quarter, customer-advisory-board, reference engineering.
- **NRR by cohort + expansion-revenue concentration** — is expansion a separate growth engine or is it 0?
- **Referral / share mechanics** — codes, share-with-team, two-sided rewards.
- **Self-reported attribution field** ("How did you hear about us?") — closes the loop on attribution.

### Axis 11 — Sales / GTM Alignment

The "marketing-to-sales handoff works" layer. **~10 lenses.**

- **Sales enablement public assets** — `/security`, `/soc2`, ROI calcs, trust center.
- **Verticalization / persona-site architecture** — `/industries`, `/for-X`, account-tier landing.
- **Sub-processor page + DPA self-serve** — enterprise-sales-cycle compression.
- **Enrichment / identity resolution** — RB2B / Clearbit Reveal / 6sense (with geo-gating for GDPR).
- **Objection handling content** — FAQ depth, "why us" pages.
- **Speed-to-lead** — measured via demo-form submission test.
- **Lead scoring + MQL-SQL lifecycle** — definition rigor, conversion rate.
- **ABM tooling maturity** — 6sense / Demandbase / Terminus, reverse-IP personalization.
- **Channel partner program** — `/resellers`, `/partners/reseller`, white-label.
- **Customer-Cloud / partner-overlap signaling** — Crossbeam / Reveal.

### Axis 12 — MarTech, Measurement, Compliance, MarOps

The "do we know what's happening" layer. **~27 lenses** — the heaviest axis count because compliance has grown 4× since 2018 and 2× since 2024.

**MarTech & measurement** (~14):

- Attribution maturity + server-side GTM + CAPI + Enhanced Conversions.
- MarTech stack inventory (BuiltWith / Wappalyzer 20+ categories).
- CRO tooling (Optimizely / VWO / Mutiny / Intellimize).
- Product analytics (Amplitude / Mixpanel / PostHog / Heap).
- Event-naming discipline + funnel-instrumentation depth.
- Session replay / heatmap (Hotjar / FullStory / Mouseflow).
- RevOps stack (CRM + MAP + sales-engagement + lead-scoring fingerprint).
- Customer research tooling (SparkToro / Dovetail / User Interviews).
- UTM taxonomy discipline + Dub-style shortlinks.
- Vendor sprawl per category (2+ analytics / 2+ CDPs / 2+ chats).
- Tag-manager hygiene (pre-consent script firing, container bloat).
- MMM infrastructure (Meridian / Robyn / Recast).
- AI citation tracking tooling (Profound / Peec / Otterly / AthenaHQ).
- Self-reported attribution field.

**Compliance & regulatory** (~13 — load-bearing in 2026 because enforcement multiplied):

- Consent Mode v2 quality (4 params pre/post consent).
- EU AI Act Article 50 readiness (chatbot disclosure + AI-content labeling).
- EAA / WCAG 2.2 + accessibility statement + VPAT.
- Multi-state US privacy enumeration (18+ states by 2026).
- Click-to-Cancel FTC compliance (online-cancel for online-signup).
- EU-US Data Privacy Framework (DPF) active certification.
- Trust-mark stack (BBB / SOC 2 / ISO 27001 / DPF).
- TCPA / SMS-consent compliance.
- CAN-SPAM / CASL compliance.
- FTC Endorsement Guides + #ad disclosure ratio.
- FTC junk-fee rule disclosure.
- FTC fake-reviews crackdown compliance.
- Comparative-advertising claim substantiation (Lanham Act §43(a)).

**Lens-count verification.** Summing the 12 axes: 12 + 10 + 24 + 10 + 12 + 14 + 10 + 14 + 13 + 10 + 10 + 27 = **166**. The catalog's locked count is 149. The 17-lens delta comes from this re-bucketing: a handful of lenses appear in two macro-axes (e.g., `traffic-mix ratio` is both Axis 1 strategic and Axis 2 diagnostic; `MMM infrastructure` is both Axis 5 paid and Axis 12 measurement; `attribution maturity` ditto). These are not counted twice in the catalog; they are counted once and referenced from both axes. The 12-axis mapping is **reader-facing organization**, not lens-bucket arithmetic. The 149-lens catalog stays the canonical lens registry.

**Vertical + geo + segment bundles add ~18-28 conditional lens-hits per audit** (vertical detection → 1-3 vertical bundles × ~8 lenses each; geography detection → 0-2 geo bundles × ~3.6 lenses each; segment detection → 1-2 segment bundles × ~6 lenses each). Per the catalog: typical audit fires ~167-177 lenses total.

---

## 2. CUTS — what to stop doing

The audit's CUTS section names tactics that should be eliminated because they no longer pay back in 2026, because the modern algorithm signal has shifted against them, or because they actively destroy the brand. Each cut is reasoned, not asserted. The CUT prescription is one of the audit's three highest-leverage outputs because most marketing budgets are 30-50% misallocated to legacy tactics the team is afraid to kill.

**~12 canonical 2026 cuts. The audit picks the 3-7 that actually apply to the target.**

### Banner / display retargeting

The 2010s assumption was that bombarding visitors with display ads keeps the brand top-of-mind. The 2026 reality: post-iOS-14.5 attribution overstates display lift; incrementality studies (Haus, Northbeam, geo-holdouts) routinely show display retargeting at negative ROAS once organic-buyer baseline is netted out. Cut unless there is incrementality evidence specific to the target.

### Broetry-style LinkedIn

Single-sentence-paragraph LinkedIn posts engineered for the 2020-2022 algorithm. The 2026 LinkedIn algorithm rewards original POVs, comment-density, and dwell time; broetry now signals "this person is gaming an old algorithm" to both algorithm and reader. Cut and replace with original-thinking posts.

### Classic keyword-stuffing SEO

Writing "10 best CRM tools" listicles to capture commercial-intent keywords. The 2026 SERP for those terms is dominated by Reddit threads, comparison-engine AI answers, and Wikipedia. Listicle traffic has collapsed 40-70% YoY for non-domain-authority sites. Cut and reallocate to: (a) original-research content that ranks on its merit, (b) comparison pages that win the `/vs-X` SERP slot, (c) founder-driven thought-leadership distributed via owned channels.

### Generic content-calendar cadence

"Post 2x/week on the blog, 3x/week on social, send 1 newsletter/week" pattern from agency playbooks. The 2026 problem: published cadence without distribution mechanics produces no compounding signal. Cut the calendar-as-strategy thinking; replace with Simmonds-style distribution-first ("publish one thing per quarter, distribute it 30 times").

### Paid-only acquisition thinking

The treatment of marketing as a paid-channel optimization problem. Founders who treat marketing as "how do we spend $X on Google + Meta to get $Y leads" have already lost — they are competing in the most-saturated channel-set against companies with 10× their budget. Cut the paid-only framing; the audit must surface owned and earned as primary, paid as amplifier.

### Broad outbound

Cold-email sequences to 10,000 prospects/month with 1.2% reply rate. The 2026 spam-filter and recipient-bar have shifted: legitimate prospects mark cold-email-of-this-shape as spam, deliverability collapses across the sending domain, and the LTV of the 1.2% who reply doesn't pay back the brand cost. Cut volume-outbound; replace with signal-based selling (intent data, warm intros, founder-led outreach to 50 prospects/month).

### "Best practices" decks

The agency / consultant artifact that lists 20-30 channel-agnostic best practices ("write better headlines," "test your CTAs," "improve your email subject lines"). Cut as a deliverable shape; the audit's job is to make specific recommendations against THIS company's specific evidence, not to publish a generic checklist.

### Generic case studies

"Customer logo + 2-paragraph description + quote-from-VP-Marketing" template. The 2026 buyer wants named-customer + named-stakeholder + specific quantified outcome + reproducible mechanism. Cut the generic template; ADD named-stakeholder-quoted case studies.

### Logo-wall-only social proof

A homepage logo wall with 20 customer logos, no context, no quotes, no quantification. The 2026 buyer assumes logo walls are decorative. Cut as the primary social-proof surface; replace with quoted-customer testimonials by use-case + dynamic-by-vertical surfacing.

### "Leverage social media" platitudes

Strategy decks that recommend "leverage social media" as a top-line action item. Cut as recommendation language; the audit must specify WHICH platform, WHICH content type, WHICH cadence, WHICH owner.

### Lead-gen-only thinking

Treating marketing's job as "produce MQLs." The 2026 unit-economic reality: MQL-as-currency creates a bullwhip where marketing celebrates volume, sales rejects 80% as unqualified, and pipeline coverage looks healthy but closed-won doesn't move. Cut the MQL-as-headline framing; the audit must report pipeline-sourced and closed-won-sourced as the headline metrics.

### MQL-volume reporting as headline

Direct cousin of the prior cut. Cut MQL volume from the dashboard headline; relegate to a sub-metric on the channel-attribution detail page.

---

## 3. REDUCES — what to dial back

The audit's REDUCES section names tactics that should NOT be eliminated but should be reduced in volume, scope, or budget allocation because the marginal return has crossed the marginal cost. The REDUCES prescription is harder than the CUTS prescription because it requires evidence on where the inflection point sits.

**~10 canonical 2026 reductions. The audit picks the 3-6 that apply.**

### Over-allocated paid budgets

When the audit-target's CAC payback by channel shows >18mo and the channel has been running for 4+ quarters without improvement, the marginal dollar is destroying value. Reduce to a maintenance level pending creative refresh + incrementality test, not zero (because pause-then-restart has restart cost).

### Over-broad ICP

When the audit shows expansion-revenue concentrated in one cohort and high-effort customer-success in a different cohort, the broad ICP is taxing the team. Reduce the ICP scope to the proven-best-fit, sequence the deferred ICP behind product/positioning maturity.

### Generic email volume

Marketing-automation lists sending 4-6 newsletters/month to broad lists at 1.8% click-through and 0.4% reply rate. Reduce send volume by 60%, segment the remaining sends by behavior, raise the bar on what triggers a send.

### Low-leverage channel sprawl

Companies with active presence on Twitter + LinkedIn + Instagram + TikTok + Reddit + Threads + YouTube + Pinterest where 5 of the 8 channels show no engagement. Reduce to the 2-3 channels where the buyer actually is.

### Agency-of-record sprawl

Companies with 4-7 simultaneous agency engagements (paid agency + SEO agency + content agency + PR agency + lifecycle agency + analyst-relations agency). Reduce to 1-2, with the rest internalized or paused. The coordination tax compounds non-linearly.

### MQL-volume targets

Even when MQL framing isn't cut entirely (some companies have stage-appropriate reasons to track it), the QUOTA for MQLs is almost always too high relative to sales capacity. Reduce MQL quota by 40-60%, raise the qualification bar.

### Late-stage best-practices at early-stage

When the target is sub-$5M ARR but has ABM tooling, full marketing-ops stack, demand-gen programmes, and multi-channel attribution infrastructure — the infrastructure is taxing the team without producing payback. Reduce the infrastructure to single-channel + simple-attribution until the company can fund expansion.

### Content-volume targets without distribution

Companies publishing 8-12 blog posts/month with zero distribution mechanics. Reduce volume to 2-3 pieces/month, reallocate freed time to distribution.

### Generic vertical content

Companies producing 1 piece/quarter for each of 6 verticals (1 healthcare piece, 1 finance piece, 1 retail piece). Reduce to 2-3 high-depth pieces in the top vertical, sequence others behind win-rate-by-vertical data.

### Founder time on non-founder-leveraged work

When the founder is spending 8 hours/week reviewing ad creative or editing the editorial calendar — work that doesn't compound the founder's unique leverage. Reduce founder time on tactical execution by 70%, reallocate to founder-led-content (Axis 7) + analyst relations + customer interviews.

---

## 4. ADDS — what to start doing (the modern lever bias)

The audit's ADDS section is where the audit lands strategic conviction. It names the 3-6 highest-leverage things the audit-target should start doing in the next 90 days. Every ADD is grounded in evidence-from-the-diagnostic and tied to a revenue mechanism through MA-3's chain.

The 2026 modern-lever bias is heavy. ~14 canonical ADDS the audit can prescribe from; it picks 3-6.

### Founder-led content engineering

If the founder is not publishing 2-4 high-signal posts/week on LinkedIn and X (or wherever the audience is), this is the single highest-leverage ADD for most pre-Series-C tech-savvy-founder companies in 2026. Specific recommendation includes: cadence, platform, original-POV theme, comment-engagement playbook, downstream conversion mechanic (newsletter? demo? podcast?), owner (the founder, not a ghostwriter), measurement (audience-growth rate + downstream conversion).

### LinkedIn + X audience-building program

Separate from founder-content; this is the platform-strategy layer. LinkedIn for B2B; X for technical-builder DTC and AI; combined for both. Specific recommendation includes: content-pillars per platform, posting cadence, engagement-allocation (commenting on others' posts is 30-40% of the lift), follower-growth target, downstream conversion path.

### AEO-native presence

The 2026 reality: 30-60% of B2B research starts in AI answer engines. Specific recommendation includes: (a) llms.txt + markdown twins + extractable HTML; (b) Wikipedia entry quality + monitored status; (c) schema stacking (Article + Organization + Person + Product per page); (d) PDF de-gating to allow Perplexity citation; (e) Bing Webmaster + IndexNow + Brave Search posture; (f) AI citation tracking tool (Profound / Peec / Otterly / AthenaHQ); (g) prompted-query test set with monthly tracking.

### Distribution-first content engineering

The Ross Simmonds "create once, distribute forever" pattern. Specific recommendation includes: 8-channel-per-piece distribution checklist, repurposing-templates, content-half-life refresh discipline. The shift is from "publish more" to "distribute more from what we already published."

### Comparison-page warfare

`/vs-[competitor]` pages structured for SEO + AEO + decision-stage buyer. Specific recommendation includes: page structure (head-to-head feature table + use-case-by-use-case + pricing + named customer migration stories), schema markup, internal linking from category content. For SaaS / AI, this is often the highest-converting page on the site once shipped.

### Integration-page warfare (for SaaS / AI)

`/integrations/[partner]` pages structured for partnership-driven distribution. Specific recommendation includes: page-per-integration, partner-logo-mutual-promotion, integration-tier classification, partner-marketing-coordination.

### Named-customer + named-stakeholder case studies

Quoted-CEO / quoted-CMO / quoted-CRO testimonials with specific quantified outcomes. Specific recommendation includes: case-study-production pipeline, customer-reference engineering, quote-and-quantify-with-permission workflow, deployment across PDP + sales-deck + email + nurture.

### Demo-direct CTAs

Replace "Contact us" with "Book a demo" or "Try free" or "Get a sample audit." Specific recommendation includes: primary CTA across homepage / pricing / case-study / blog footer; secondary CTA hierarchy; conversion-rate baseline + target.

### Modern algorithmic-signal optimization

The 2026 SEO + AEO + social-algorithm reality: original POVs, comment density, dwell time, link-from-authoritative-domain. Specific recommendation includes: original-research investment, comment-magnet engineering, link-velocity from Wikipedia / Substack / authority domains.

### Brand-mention engineering

Engineering the systematic appearance of the brand in places the brand doesn't own — Reddit threads, Hacker News comments, podcast guests, community discussions. Specific recommendation includes: target-community list, named-contributor relationships, content-seeding mechanics, measurement (mention velocity + sentiment).

### Customer-expansion / NRR engineering

For SaaS / AI: a separate growth engine. Specific recommendation includes: in-product upsell hooks, customer-success-driven expansion playbook, advisory-board engineering, reference-engineering, expansion-revenue-by-cohort measurement.

### Customer-interview cadence (Wynter-style)

The audit-target should be running monthly customer-language interviews to keep messaging fresh. Specific recommendation includes: 6-8 interviews/month, JTBD framing, Wynter messaging-resonance-panel option, output-to-messaging pipeline.

### Reference-customer engineering

Engineering a stable of 8-12 customers who will take a reference call. Specific recommendation includes: criteria, incentives, cadence, deployment in late-stage sales-cycle.

### Email-list growth + lead-magnet engineering

The most-underrated owned channel. Specific recommendation includes: 2-3 high-leverage lead magnets, content-upgrade integration into existing blog posts, list-growth target, nurture-sequence quality.

---

## 5. Vertical adjustments — what flexes by SaaS / AI / agency / service-firm / finance / e-commerce

The 12 axes are invariant across verticals; what changes is (a) which axes are load-bearing, (b) which lenses inside the axis matter most, (c) which CUTS / REDUCES / ADDS apply, (d) the evidence substrate.

### B2B SaaS (the first-cohort default — Anthropic, Perplexity)

Load-bearing axes: 1 (positioning), 5 (paid + CAC payback), 7 (founder-led), 8 (conversion + pricing), 9 (activation + retention), 11 (sales / GTM). De-emphasized: 6 (earned-PR — secondary) for sub-$10M ARR.

Distinctive metrics: CAC payback (<12mo SMB, <18mo mid-market, 24+mo enterprise per Bessemer), NRR (>110% healthy), trial-to-paid (~6% SaaS median), MQL→SQL→opportunity→closed-won, pipeline-sourced ratio.

Distinctive ADDS: comparison-page warfare (especially load-bearing for mature categories with named competitors), integration-page warfare, founder LinkedIn (B2B-skewed), AEO presence (developer-facing categories see 50%+ AI-answer traffic share).

Distinctive CUTS: ABM tooling for sub-$5M ARR (premature), full marketing-ops stack for sub-$3M ARR.

### AI lab / dev-tools (Anthropic / Perplexity / OSS-grade)

Load-bearing axes: 1 (category placement is moving target), 3 (AEO load-bearing — AI labs are the consumers of AEO), 6 (earned + analyst), 7 (founder-led — heavy), 9 (developer activation), 12 (compliance — fast-moving in AI).

Distinctive metrics: developer NPS, time-to-first-API-call, docs engagement, stars-to-activation ratio, OSS contribution velocity (if applicable), AI-citation share (Profound / Peec).

Distinctive ADDS: docs-as-marketing (the documentation IS the marketing surface), GPT Store / Claude Skills / Perplexity Spaces / MCP-server presence, technical-conference-speaking, OSS community engineering.

Distinctive CUTS: paid social for developer-facing categories (developers ad-block + dislike), broad outbound (developers detect-and-mark-spam).

### Agency (gofreddy itself, plus client agencies)

Load-bearing axes: 1 (positioning + category — agencies are commodity unless positioned tightly), 4 (content + authority — load-bearing for trust), 6 (earned — case studies are the conversion mechanism), 7 (founder-led — agencies are bought on the founder's voice).

Distinctive metrics: pipeline-sourced from content, founder-LinkedIn-driven inbound, case-study-driven closed-won, repeat-client rate, referral-source mix.

Distinctive ADDS: thought-leadership program with founder as primary publisher, named-customer case study velocity (2-3/quarter minimum), conference-speaking, founder-podcast-guesting.

Distinctive CUTS: cold outbound (agencies who cold-outbound signal weak brand), generic case studies.

### Service firm (legal, accounting, consulting — DWF)

Load-bearing axes: 1 (positioning — practice-area + jurisdiction specificity matters), 6 (earned — Chambers rankings, league-tables, awards), 7 (founder/partner-led — buyers buy the named partner), 11 (sales / GTM — referral-source mix dominates).

Distinctive metrics: pipeline + win-rate + sales cycle, referral-source mix, repeat-client rate, partner-utilization, practice-area mix, geographic mix.

Distinctive ADDS: partner-led thought leadership, named-partner-led webinars, referral-network engineering, conference-keynote-speaking. The "founder-LinkedIn" axis becomes "named-partner LinkedIn."

Distinctive CUTS: paid acquisition (legal services have channel-mix regulatory constraints in some jurisdictions), generic-firm-positioning content.

### Finance (regulated, fintech, advisory)

Load-bearing axes: 1 (positioning — trust-bound), 6 (earned — analyst relations, press), 11 (sales / GTM — referral + reference-customer driven), 12 (compliance — heaviest of any vertical).

Distinctive metrics: pipeline + win-rate + sales cycle, AUM growth (advisory), customer-acquisition by referral-vs-paid, sales-cycle by deal size.

Distinctive ADDS: trust-mark stack engineering (SOC 2, ISO 27001, BBB, DPF), regulatory-clearance positioning, analyst-relations engagement.

Distinctive CUTS: any cold-outbound (financial-promotions regulation), aggressive paid-social on consumer-fintech (compliance-bound).

### E-commerce / DTC

Load-bearing axes: 2 (demand-mix — the stage map differs: $500k/mo early, $5M/mo mid, $20M+/mo late), 5 (paid + CAC + incrementality), 6 (earned — influencer + UGC), 9 (lifecycle — retention is the unit-economic make-or-break), 8 (conversion — Shopify / Amazon UX details).

Distinctive metrics: contribution margin per cohort, CAC:LTV by cohort, repeat-purchase at 30/60/90/180/365 days, first-purchase-AOV vs LTV-AOV, returns rate, channel-incrementality (post-iOS-14.5 critical).

Distinctive ADDS: SMS retention flows (Klaviyo), TikTok creative engineering (DTC-favorable algorithm), UGC engineering (creator partnerships), product-page CRO (PDP is the highest-leverage page), email-segmentation by repeat-purchase-cohort.

Distinctive CUTS: TikTok Shop expansion before unit economics close, influencer pilots without contribution-margin model, "expand to retail" before digital unit economics close.

### Local-services / healthcare (Klinika)

Load-bearing axes: 2 (stage-map: capacity-utilization + review-velocity are stage anchors, NOT ARR), 6 (earned — reviews + referrals dominate), 9 (lifecycle — patient retention + NPS), 11 (sales — referral engineering + intake).

Distinctive metrics: CAC by channel (referral $50-150 vs RealSelf $200-400 vs Google paid $400-800 vs cold paid $600+), capacity utilization, review velocity + rating (Google, RealSelf, Healthgrades), patient LTV by treatment mix, referral-source mix.

Distinctive ADDS: GBP review-response system, RealSelf profile completion, referral-source engineering, Instagram + TikTok aesthetic content.

Distinctive CUTS: paid Meta for Botox-acquisition before GBP rating crosses 4.5, national PR for single-location practice.

---

## 6. Deliverable architecture — what the comprehensive MA actually ships

The deliverable is multi-part. The single-artifact-mid-length-founder-audit framing from the 2026-05-18 Step-1 spec was the wrong frame; it scoped the artifact to fit a fictional reader's 30-minute Tuesday window. Real tech-savvy founders WILL spend 90 minutes on a 15,000-word document if it lands strategic conviction. The audit is a sales artifact pitching a $15K-$150K agency engagement, not a one-off PDF.

**Total envelope: 8,000-18,000 words across 4-7 files.** Detail follows.

### File 1 — `findings.md` — the strategic spine

The main reader-facing artifact. **5,000-9,000 words.** Structure:

1. **State-of-the-business opener** (~400-800 words). Pulls measurements from `phase0_meta.json` (9 meta-frames). Names where the company sits today on traffic mix, channel-model fit, traffic trajectory, growth-loops, maturity tier, share-of-voice, geo mix, north-star vs vanity, engagement-tier. Gap-honest: Phase-0 measurements that returned null surface as findings, not papered over.
2. **Stage diagnostic + named binding constraint** (~400-600 words). Locates the company on stage map (vertical-appropriate stage signals). Names ONE binding constraint with ≥2 evidence sources. Walks the 6-class upstream triage (PMF → ICP → positioning → pricing → product → sales-motion) and either sequences marketing behind upstream OR defends marketing-as-the-constraint on the merits.
3. **12-axis comprehensive diagnostic** (~3,000-5,000 words). For each axis: 2-4 ParentFindings (rolled up from SubSignals per the catalog architecture), each with headline, severity, confidence, evidence-summary, recommendation (tier-mapped). NOT every axis fires equally — strong axes (where evidence is rich) get 4 findings; weak axes (where evidence is thin or the dimension genuinely isn't broken) get 1 finding or just a "no finding" note. Total ParentFindings target: 25-32 across the 12 axes, per the locked catalog architecture.
4. **The most valuable marketing strategy going forward** (~500-1,000 words). The audit's organizing argument. One thesis. "Given everything above, the binding constraint is X; the leverage move is Y; the single most valuable thing you can do over the next 90 days is Z." This section is the gravitational center; it's what gets quoted in board meetings.
5. **CUTS prescription** (~400-800 words). 3-7 named cuts, each with reasoning + named savings + named replacement.
6. **REDUCES prescription** (~400-800 words). 3-6 named reductions, each with reasoning + named target volume / budget.
7. **ADDS prescription** (~600-1,200 words). 3-6 named adds, each with reasoning + named owner + budget envelope + revenue mechanism + measurement.

### File 2 — `roadmap.md` — the 30/60/90 execution plan

**1,500-3,000 words.** Structure:

1. **Day 0-30** — 2-4 foundational commitments with action + owner + budget + timeline + success metric tied to current baseline + kill-trigger. These are usually the highest-leverage CUTS + 1-2 ADDS. Includes "Day-1 quick wins" — 1-2 things shipped in week 1 to establish credibility.
2. **Day 31-60** — 1-2 build-phase commitments that depend on Day-30 foundation. Usually 1-2 ADDS at scale.
3. **Day 61-90** — 1-2 scale-phase commitments + read-out of Day 31-60 bets.
4. **Day 45 founder-impatience off-ramps** — explicit guidance: "If, at Day 45, the founder is reading Day-30 results and wants to pull the plug because X hasn't moved yet, here's the diagnostic: [...]." This off-ramp set was specifically called out by the upstream-diagnostic research as a known fractional-CMO failure mode.
5. **Day 90 read-out + decision gate** — what gets decided at Day 90 (kill-and-replace vs scale; team-build vs maintain; reposition vs hold).
6. **Capability-registry tier mapping per commitment** — every commitment in the 30/60/90 maps to `fix_it` / `build_it` / `run_it` per the v006 capability_registry. The audit-target sees not just "do X" but "we (gofreddy) would fix-it / build-it / run-it for $X scope."

### File 3 — `proposal.md` — the agency engagement pitch

**1,000-2,000 words.** Structure:

1. **Engagement summary** — scope, duration, dollar envelope ($15K-$150K range).
2. **`fix_it` deliverables** — short-term audit-to-action items the audit-target needs done in the next 30 days. Tracking cleanup, GBP review-response system setup, comparison-page authoring, AEO-meta-setup.
3. **`build_it` deliverables** — Day 31-60 build engagements. Founder-content engineering, comparison-page-warfare program, integration-page-portfolio, AEO presence stack, named-customer case-study production.
4. **`run_it` deliverables** — ongoing run-rate engagements at Day 61-90+. Founder-content production cadence, AEO monitoring + iteration, content-distribution-engine, comparison-page maintenance, NRR-expansion-engineering.
5. **Pricing** — tier-by-tier breakdown.
6. **Why us / proof** — gofreddy's named case studies + named senior operators.

### File 4 — `cuts_reduces_adds.md` — the supporting evidence appendix

**1,500-2,500 words.** A reference appendix that:

1. For each CUT: detailed reasoning, evidence from the company's actual data, 2-3 reference cases (named external companies that made this cut and the named outcome).
2. For each REDUCE: detailed reasoning, current vs target volume / budget / scope.
3. For each ADD: detailed mechanism, target metric, comparable success cases.

This file is where the audit-target's competent technical reader (head-of-growth, fractional-CMO) goes to defend the audit's recommendations against pushback.

### File 5 — `gap_report.md` — the honesty layer

**500-1,500 words.** Per MA-7 in v006: surfaces Phase-0 nulls, provider-blocked lenses, evidence we couldn't gather, and what additional data would change the audit's recommendations. Critical for the strategic-conviction posture; "we don't know X" is more credible than "we made up a number."

### File 6 (optional) — `vertical_overlay.md` — vertical-specific deep dive

**0-2,000 words depending on vertical complexity.** When the vertical triggers a heavy bundle (e.g., regulated finance, multi-jurisdiction legal, multi-state e-commerce), the vertical-specific findings consolidate here. For most B2B SaaS audits this file is empty or absorbed into `findings.md`.

### File 7 (optional) — `geo_overlay.md` — geographic / multi-region deep dive

**0-1,500 words.** When the target operates in 3+ jurisdictions with different regulatory + cultural marketing constraints (Klinika in Poland with EU GDPR + Polish-medical-promotion rules; DWF UK with FCA financial-promotions + Solicitors Regulation Authority; an e-commerce brand with US + EU + UK customers), this file consolidates per-geo findings.

### Why multi-part instead of single-artifact

(a) Reader-routing without cluster-routing — the founder reads `findings.md` for the strategic narrative; the head-of-growth reads `cuts_reduces_adds.md` for the defensible recommendations; the operations lead reads `roadmap.md` for the execution plan; the procurement person reads `proposal.md` for the engagement scope. Different readers, same source-of-truth diagnostic.

(b) Evolution-loop iteration is easier on smaller files. The evolution agent can mutate `roadmap.md`'s sequencing without re-writing `findings.md`'s diagnostic.

(c) The substrate already supports multi-file output (v006 has `findings.md`, `proposal.md`, `gap_report.md` wired). Adding `roadmap.md`, `cuts_reduces_adds.md`, `vertical_overlay.md`, `geo_overlay.md` is incremental.

(d) Total word count of 8,000-18,000 in a single file is in the un-readable range; split across 4-7 files, each is in the readable range.

---

## 7. Evolution-loop considerations

The MA workflow runs in autoresearch's evolution loop. Comprehensive scope has implications:

### Token-cost envelope

A 15,000-word multi-part deliverable consumes 20-40× more tokens than the 2026-05-18 Step-1 spec's 2,000-4,500 word target. Per-audit cost lifts. Per the catalog: $50 → $100 per audit with $150 hard breaker. The comprehensive scope pushes this further: expect $100-300 per audit at quality-production-grade, with the corresponding bill on the evolution loop (multiply by 50-iteration evolution + 4-8 fixtures + 5-10 lineage variants per iteration).

**Mitigation:** the v006 architecture already does Stage-1a deterministic pre-pass for ~25 cheap lenses (DNS, well-known files, schema parsing, badge regex), saving ~$10/audit. Push more lenses to deterministic pre-pass where possible. Stage-2 agent fan-out (findability / narrative / acquisition / experience) parallelizes the heavy LLM lensing; this should be preserved.

### Slot-fill Goodhart resistance

Comprehensive scope creates more surface area for slot-fill drift under 50-generation evolution pressure. Specifically:

- **Lens-count gaming** — the workflow learns to mention all 149 lenses ("we checked AI bot access; no issues found"). Caught by SubSignal → ParentFinding rollup discipline; the deliverable surfaces ParentFindings, not lens-by-lens checks. The judge tests strategic-narrative-coherence, not lens-coverage-percentage.
- **CUT/REDUCE/ADD volume gaming** — the workflow learns more CUTS = more value. Caught by structural_gate ceiling: 3-7 CUTS, 3-6 REDUCES, 3-6 ADDS, with hard penalty above 8 of any.
- **Vertical-bundle slot-fill** — when the target is dev-tools, the workflow learns to mention "developer-NPS, time-to-first-API-call, GPT Store presence" as a checklist. Caught by the judge testing whether the vertical findings actually tie to the target's evidence vs being recited.
- **30/60/90 boilerplate** — the workflow learns "Day-1 quick wins" + "Day 90 read-out" become slot-fill headers. Caught by MA-2 outcome question testing whether the founder could actually walk into the leadership meeting and assign each commitment.
- **AEO checklist** — the workflow learns to recommend llms.txt + schema-stacking + Wikipedia + PDF-de-gating for every audit. Caught by MA-4's stage-anchor + refusal-on-stage-grounds — AEO recommendations are stage-appropriate for some companies, premature for others.

### Variance instrumentation

Per the judge-design-guide §11.5: track per-criterion variance across generations. If variance grows monotonically OR mean compresses to middle, redesign — don't calibrate. For the comprehensive MA, the criteria most at risk:

- **MA-1 binding constraint** — at risk if the workflow learns to slot-fill "the binding constraint is positioning" by default. Variance should remain high across fixtures because real binding constraints differ; if variance compresses, the workflow has learned a default.
- **MA-3 revenue mechanism** — at risk if the workflow learns to fabricate revenue chains. Variance should remain high because real revenue mechanisms differ; if compressed, the workflow has learned a templated chain.
- **MA-5 upstream-vs-marketing** — at risk if the workflow learns to always say "the bottleneck is upstream" (over-correction from the original "always recommend more marketing" bias). Variance should be moderate-to-high because real audits should split roughly 40% upstream / 60% marketing.

### Fixture diversity

The first-cohort fixtures (Anthropic, Perplexity, DWF, Klinika) are SaaS-skewed. Per the vertical-conventions research, fixtures need to span verticals BEFORE the comprehensive scope locks. Specifically: add 2-3 DTC fixtures, 1-2 marketplace fixtures, 1-2 service-firm fixtures (beyond DWF), 1-2 finance fixtures, 1-2 dev-tools fixtures. The 12-axis structure was designed to generalize; fixture validation is what proves it.

### Multi-file deliverable + structural_gate

`structural_gate` needs extension to verify multi-file presence (`findings.md` + `roadmap.md` + `proposal.md` + `cuts_reduces_adds.md` + `gap_report.md` minimum; vertical/geo overlay conditional), per-file word-count bands, per-file structural requirements (e.g., `cuts_reduces_adds.md` must have ≥3 CUTS + ≥3 REDUCES + ≥3 ADDS). The v006 STRUCTURAL_DOC_FACTS tuple already encodes a similar pattern for the 9-section findings.md; extend to multi-file.

### Judge criteria — minimal-change posture

The 8 MA criteria (MA-1..MA-8) in v006 are mostly correct for the comprehensive scope. Specific adjustments:

- **MA-1 Strategic Narrative Coherence** — KEEP. The comprehensive scope amplifies the need for one organizing argument; otherwise 149 lenses becomes 149 disconnected findings.
- **MA-2 Evidence Traceability** — KEEP. Every claim cites a lens_id + evidence_url. The 5 AI-failure surfaces (financial-metric / channel-claim / competitor-data confab + misdiagnosis + recommendation-hallucination) live in MA-2 + structural_gate.
- **MA-3 Phase-0 Framing Applied** — KEEP. State-of-business opener pulls from phase0_meta.json.
- **MA-4 Actionable + Capability-Mapped** — KEEP. Each recommendation maps to a `fix_it` / `build_it` / `run_it` tier.
- **MA-5 Severity Calibration** — KEEP. Anchored to lens-specific severity_anchors; no sea of 3's.
- **MA-6 Polish + Voice Consistency** — KEEP. Customer-facing $15K+ agency-artifact voice.
- **MA-7 Gap Honesty** — KEEP. Phase-0 nulls are findings, not papered-over.
- **MA-8 Engagement-Fit** — KEEP. The deliverable IS pitching a credible $15K+ engagement.

**Specifically reject** adding cluster-routing criteria. The decision-format-mapping research's recommendation to route MA-2 anchor across "binary verdict for Personnel / 30-day experiment for Operational / 90-day plan for Strategic" is rejected. Instead, MA-2 stays unified: every audit produces ALL THREE (cuts + reduces + adds + 30/60/90 + proposal). The decision-shape variance shows up in the emphasis inside each, not as separate artifact types.

### Calibration set weighting

Per the upstream-diagnostic research §7: at least 30% of the 100-fixture calibration set should have upstream-evidence shape (low retention + clear PMF/positioning/pricing/product/sales-motion signal). Without this, MA-1 ↔ MA-5 correlation exceeds 0.7 and the redundancy check drops MA-5 — losing the only criterion specifically targeting marketing-misdiagnosis bias.

Add: at least 20% of fixtures with strong CUT-prescription shape (target has clear over-allocated paid budget, obvious legacy-channel-decay, or sprawling agency-of-record cost). At least 20% with strong ADD-prescription shape (target has zero founder-content presence and an obviously founder-driven sales motion). These weighting choices keep the CUT and ADD axes of the audit empirically grounded.

---

## 8. SOTA exemplars — the practitioners the comprehensive MA learns from

The comprehensive MA inherits structure and discipline from a set of named practitioners + frameworks. The judge does NOT mention them by name in criterion prose (per design-guide §1.1 — no framework-name embedding). They sit in the judge's reasoning toolkit and the audit's quality ceiling.

### Strategic foundations

- **April Dunford** — *Obviously Awesome*, *Sales Pitch*. Positioning starting from competitive alternatives; the dominant 2026 framework for positioning audits.
- **Roger Martin** — *Playing to Win*; strategic-choice attribution (separate operator effort from strategic context).
- **Christopher Lochhead** — *Play Bigger*; category-design discipline.
- **Andy Raskin** — strategic-narrative essays; the "one big story" frame.
- **Eric Ries** — *The Lean Startup*; vanity-vs-actionable, applied recursively.
- **Sean Ellis** — *Hacking Growth*; PMF survey (40%-very-disappointed), ICE, North Star Metric.
- **Brian Balfour** — Four Fits Framework; Reforge canon on premature scaling; ecosystem-fit thinking.
- **Lenny Rachitsky + Dan Hockenmaier** — customer-acquisition-lanes essay (First Round Review); growth-lanes operational framework.

### Marketing-audit methodology

- **Kalungi** — 95-point B2B SaaS audit; one-page readiness audit; SaaS-growth-stages framework. The practitioner reference for mid-length B2B SaaS audits.
- **Bell Curve / Demand Curve** — paid-acquisition audit methodology (foundation-then-scale); Growth Guide.
- **TripleDart / ByDefaultCMO / Growth Syndicate** — operator-grade audit templates.
- **Patrick Campbell (ProfitWell)** — pricing audit at Patrick-Campbell-grade rigour; value-metric + packaging + Van Westendorp methodology.
- **Wynter (Peep Laja)** — B2B messaging audit grounded in ICP panel research.
- **CXL (Peep Laja)** — ResearchXL six-step Conversion Research model.
- **Animalz / Foundation Inc (Ross Simmonds)** — content audit at editorial-first depth; Foundation Inc's "create once, distribute forever" distribution philosophy.
- **MKT1 (Emily Kramer / Kathleen Estreich)** — strategy memos; B2B SaaS marketing operating system.
- **Tomasz Tunguz** — SaaS-startup-benchmarks; CAC payback discipline.

### Modern + 2026-current

- **Ross Simmonds (Foundation Inc)** — distribution-first content engineering.
- **Sahil Bloom** — audience-building playbook; founder-led-content modern grammar.
- **Justin Wells (Pavlov's Inbox)** — sales-engineering + founder-distribution.
- **Frank Sondors** — sales-led modern outreach (replacing broad-outbound).
- **Andrew Chen** — Growth essays; Law of Shitty Clickthroughs.

### Agency-vertical exemplars

- **HubSpot Agency Partner playbooks** — agency-economics audits.
- **Win Without Pitching (Blair Enns)** — agency-positioning + agency-pricing methodology.
- **David C. Baker** — agency-economics audits; agency-valuation methodology.

### DTC

- **Common Thread Collective (Taylor Holiday)** — DTC unit-economics audit shape.
- **Northbeam / Haus** — post-iOS-14.5 incrementality measurement.
- **Drew Sanocki** — DTC repeat-purchase economics.
- **Andrew Faris (AJF Growth)** — DTC operator playbook.
- **Tinuiti** — DTC paid-media audit shape.

### Healthcare / local services

- **AmSpa Medical Spa State of the Industry** — vertical benchmark source.
- **ASDS Consumer Survey** — vertical benchmark source.
- **Growth99 / Cardinal / Intrepy** — vertical-specific benchmark methodology.
- **RealSelf Insights Center** — vertical-specific data substrate.

### Regulated B2B / fintech

- **Gartner / Forrester / IDC** — analyst-positioning methodology.
- **Pavilion / RevGenius** — pipeline-benchmark references.

### Marketplaces

- **Bill Gurley** — two-sided-marketplace canon.
- **Sarah Tavel** — Reforge / Benchmark marketplace canon.
- **Andrew Chen / Jin Mei (a16z)** — marketplace canon.

### Dev-tools

- **Heavybit / DevTools Insiders** — dev-tool-specific GTM playbook.
- **Bessemer Roadmap to a Better Developer Platform** — dev-tool benchmark methodology.
- **Joseph Jacks / Adam Gross / Adam Frankl** — OSS-GTM literature.

### Frameworks the judge reasons with (NOT in criterion prose)

- **AARRR (Dave McClure)** — Pirate Metrics.
- **Four Fits (Brian Balfour)** — ecosystem-fit framework.
- **AAA (Acquisition / Activation / Retention / Revenue / Referral)** — McClure variant.
- **ResearchXL (Peep Laja)** — six-step CRO methodology.
- **Kotler / Forrester 6-axis maturity** — marketing-maturity tier framework.

---

## 9. Open questions + first-cohort overfit watch

### Open question 1 — Multi-file structural_gate enforcement

The 12-axis comprehensive scope produces a 4-7 file deliverable. `structural_gate` needs extension to:

- Verify each required file exists.
- Verify each file's word-count band (`findings.md` 5,000-9,000 words; `roadmap.md` 1,500-3,000; etc).
- Verify per-file structural facts (`cuts_reduces_adds.md` has ≥3 CUTS + ≥3 REDUCES + ≥3 ADDS; `roadmap.md` has Day-30 + Day-60 + Day-90 sections + off-ramps).
- Verify cross-file consistency (every Day-30 commitment in `roadmap.md` references a recommendation from `findings.md`; every `proposal.md` deliverable maps to a finding-recommendation pair).

Implementation cost: ~150-250 LOC extension of `session_eval_marketing_audit.structural_gate`. Acceptable per existing pattern.

### Open question 2 — Token-cost envelope ceiling

A 15,000-word multi-part deliverable at production quality may cost $300-500/audit (Phase-0 + 5 Stage-2 agents in parallel + Stage-3 cross-cutting synthesis + Stage-4 proposal + 8 judge criteria). The locked catalog raised the cap from $50 → $100 with a $150 hard breaker. Reality may need $200-400 with a $500 hard breaker. JR triage point.

### Open question 3 — Fixture coverage for non-SaaS verticals

First cohort is SaaS-skewed (Anthropic / Perplexity AI labs; DWF legal; Klinika healthcare). For the comprehensive scope to validate, need fixtures from:

- DTC e-commerce (1-2 fixtures).
- Marketplace (1-2 fixtures).
- Mid-stage B2B SaaS at $5M-$20M ARR (current cohort skews pre-Series-A and post-Series-C).
- Dev-tools (Perplexity is partial-coverage; needs a pure dev-tools fixture).
- Regulated finance (no current fixture).
- Service-firm (DWF is partial-coverage; needs a mid-size agency or accounting fixture).

Recommend: build 6-8 additional fixtures before locking the comprehensive scope via redundancy check.

### Open question 4 — Founder-content axis (Axis 7) — overfit risk

The bullishness on founder-led content + LinkedIn/X audience-building is empirically grounded for 2026 tech-savvy-founder clients, but the entire axis could over-fire for clients where the founder is NOT the right voice (e.g., a 200-person agency where the named partners are the voice; a regulated-finance fintech where the founder is not the audience-builder by design; a healthcare practice where the founder-physician's voice is regulated). Mitigation: the audit must engage the founder-voice question explicitly, not default to "you should post on LinkedIn." MA-5's upstream-vs-marketing check absorbs this — if the founder is structurally not the audience-builder, MA-5 should catch it.

### Open question 5 — Verbatim 2026 lens-cutoff drift

The locked 149-lens catalog is from 2026-04-22 / 2026-04-23. By the time the comprehensive scope ships, 2-3 lenses may have shifted in 2026 importance: AEO instrumentation tools matured (Profound, Peec); Wikipedia citation share shifted; X (Twitter) algorithm dynamics shifted under post-2025-acquisition changes; specific compliance regulations have moved (EU AI Act Article 50 phased-in throughout 2026). The catalog should be re-validated quarterly per a documented schedule.

### Open question 6 — CUT/REDUCE/ADD evidence threshold

For each named CUT / REDUCE / ADD, what evidence threshold from the target's data is required? Without a threshold, the audit can fabricate CUTS for which there is no client-specific evidence (e.g., "cut paid LinkedIn" applied to a target that doesn't run paid LinkedIn). MA-3's revenue-chain criterion partially catches this, but a stricter rule may be warranted: every CUT must cite specific evidence from the target's actual data (a screenshot, a stat, a named campaign-report). Add as a structural_gate check: each CUT entry has ≥1 inline citation to source data.

### Open question 7 — Strategic-narrative-coherence at 15,000 words

MA-1 in v006 is "Strategic Narrative Coherence — findings.md is organized around ONE strategic argument." At 5,000-9,000 words across 4-7 files, the narrative-coherence test gets harder. The judge needs to test cross-file coherence — does `roadmap.md` execute against `findings.md`'s strategic argument? Does `cuts_reduces_adds.md` reinforce the same thesis or undercut it? Resolution: keep MA-1 as the single-thesis test on `findings.md`'s "most valuable strategy going forward" section; rely on `structural_gate` to verify cross-file consistency mechanically.

### First-cohort overfit watch

Per the CI v3.3 first-cohort overfitting reduction pattern: the SaaS-skewed first-cohort fixtures will tempt the workflow to optimize for SaaS-shaped audits and grade non-SaaS audits down for failing to fit. Mitigation:

1. Use vertical-aware fixture set (per Open Q3 above) before lock.
2. Verify per-criterion variance across vertical fixture cohorts; if MA-1 / MA-3 / MA-5 fire systematically lower on DTC or service-firm fixtures, the criteria have overfit.
3. The 12-axis structure is intentionally vertical-agnostic; the verticality lives in WHICH axes get prioritized and WHICH lenses fire inside them, not in different criteria per vertical.
4. The CUT / REDUCE / ADD framing is intentionally vertical-agnostic at the structural level; the SPECIFIC cuts/reduces/adds per vertical are documented in §5 but not in criterion prose.

### Hard constraints — all preserved

Per the design-guide §1.1 / §12 / §6:

- **No σ-widening.** The 5-criterion (or 8-criterion in v006) ceiling holds; no Goodhart-resistance via expanding rubric prose.
- **No anti-gaming clauses.** No "don't be biased toward marketing recommendations" prose in criteria.
- **No framework-name embedding in rubric prose.** Dunford / Ellis / Balfour / Campbell / Simmonds / Lochhead are reasoning toolkit, not criterion text.
- **No feature-checking.** Criteria test outcomes (does the founder commit to the named action), not surface features (is there a "CUTS" header).
- **Outcome questions throughout.** Every criterion tests reader-effect.
- **Reference-free examples in spec prose.** Score-1 examples carry "do not optimize toward this" hedges.
- **First-cohort overfit watch explicit.** Per CI v3.3 precedent.

---

## End notes

This deliverable supersedes the 3-cluster A/B/C routing recommendation in `docs/research/2026-05-18-marketing-audit-decision-format-mapping.md` and the cluster-routed reader / artifact / success framing in `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` §1 / §1.5 / §2 / §4. It preserves the upstream-diagnostic, AI-failure-mode, and vertical-conventions deliverables as load-bearing. It preserves the v006 live code structure (8 criteria, capability_registry, Phase-0 meta-frames, SubSignal → ParentFinding rollup, 9-section findings, gap_report). It expands the deliverable architecture from single-artifact to multi-file. It commits the audit to the modern-lever bias: founder-led + AEO-native + distribution-first + comparison-page-warfare + named-customer case studies + demo-direct.

The audit's gravitational center is the phrase: **"the most valuable marketing strategy going forward."** Every other section serves that conviction.
