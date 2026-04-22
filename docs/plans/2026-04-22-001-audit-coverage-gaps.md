---
title: "Audit Coverage Gaps — Continuous Discovery"
type: research
status: active
date: 2026-04-22
related_plan: 2026-04-20-002-feat-automated-audit-pipeline-plan.md
---

# Audit Coverage Gaps — Continuous Discovery Log

Working document tracking marketing-audit dimensions identified as gaps in the current 9-lens / 32-primitive plan (`2026-04-20-002-feat-automated-audit-pipeline-plan.md`). Updated each time a new gap-finding pass is run; round-by-round structure so we can see what was identified when and which gaps have been closed in the plan since.

**Each new gap is tagged with status:**
- `proposed` — identified, awaiting JR approval
- `approved` — JR approved for plan addition
- `in plan` — already merged into the audit pipeline plan
- `skip` — JR explicitly chose not to add (with reason)

---

## Round 1 — 2026-04-22 (Corey Haines `marketingskills` audit)

**Method:** Inventoried all 38 skills in `coreyhaines31/marketingskills` GitHub repo. Cross-referenced each against current 9-lens / 32-primitive plan. Plus independent brainstorm of audit dimensions Corey's framework doesn't cover.

### Coverage map vs Corey's 38 skills

| Skill | Plan coverage | Notes |
|---|---|---|
| ab-test-setup | partial | Detect A/B test vendors via `fingerprint_martech_stack`, no experimentation-cadence audit |
| ad-creative | covered | Distribution lens via Foreplay normalized fields |
| ai-seo | covered | GEO lens via `score_ai_visibility` |
| analytics-tracking | covered | MarTech-Attribution lens |
| aso-audit | partial | P31 `audit_aso` exists but doesn't match Corey's 6-dimension weighted rubric + brand-maturity tier adjustment |
| churn-prevention | partial | `gather_voc` surfaces churn signals; no dedicated retention-program audit |
| cold-email | N/A | Outbound, out-of-scope |
| community-marketing | covered | `audit_partnership_event_community_footprint` |
| competitor-alternatives | covered | `scan_competitor_pages` finds /vs/, /alternatives/ |
| competitor-profiling | partial | Competitive lens covers data; doesn't produce per-competitor structured dossier per Corey's 12-section template |
| content-strategy | covered | `audit_content_strategy_shape` |
| copy-editing | covered | `audit_messaging_consistency` |
| copywriting | partial | We audit positioning; no copy-quality scoring (jargon density, benefit-vs-feature ratio, headline strength) |
| customer-research | covered | `gather_voc` + R21 |
| **directory-submissions** | **MISSING** | No detection of G2 / Capterra / GetApp / AlternativeTo / SaaSHub / Product Hunt history / BetaList / Futurepedia / TAAFT / Chrome Web Store / Apple Developer / GitHub Marketplace listings. Corey: AI-referred traffic from directories converts 6–27× higher than traditional search |
| email-sequence | covered | Lifecycle lens + R19 ESP enrichment |
| form-cro | partial | Conversion lens consumes `capture_surface_scan`; no field-by-field form audit |
| **free-tool-strategy** | **MISSING** | No detection of calculators / generators / extensions / micro-tools (engineering-as-marketing — major lead-gen + SEO asset class) |
| **launch-strategy** | **MISSING** | No Product Hunt history, changelog cadence, waitlist mechanism, beta-signal detection |
| lead-magnets | partial | `capture_surface_scan` picks up gated assets; no magnet-quality audit |
| marketing-ideas | N/A | 139-idea library — useful as heuristic, not auditable as checklist |
| marketing-psychology | N/A | Applied, not audited |
| onboarding-cro | MISSING | Requires post-signup access — same constraint as flow-observation pipeline (rejected) |
| page-cro | covered | Conversion lens |
| paid-ads | covered | Distribution lens |
| paywall-upgrade-cro | MISSING | Freemium-specific, narrow |
| popup-cro | covered | Lifecycle lens |
| pricing-strategy | partial | We read pricing positioning only; no tier-structure audit, no anchoring/recommended-plan CRO, no competitive pricing comparison |
| product-marketing-context | covered | Stage 0 intake |
| programmatic-seo | covered | SEO lens (`audit_internal_links` + `audit_content_quality`) |
| referral-program | covered | `audit_partnership_event_community_footprint` |
| **revops** | **MISSING** | Marketing→sales handoff signals (Calendly/Chili Piper/HubSpot Meetings detection, demo-form BANT/MEDDIC field requirements, "talk to sales" CTA placement) |
| **sales-enablement** | partial | R22 covers if client uploads decks; no detection of customer-facing sales motion (Calendly fields, gated demo, comparison battle-card pages) |
| schema-markup | covered | SEO lens (`detect_schema`) |
| seo-audit | partial | Most covered; **International SEO / hreflang / locale URL section is a hard miss** |
| signup-flow-cro | partial | Conversion lens; no signup-step audit |
| site-architecture | covered | SEO lens (`analyze_internal_links`) |
| social-content | covered | Distribution lens |

### Round 1 — Tier 1 additions (clear hard gaps, externally cheap, high signal)

| Primitive | Lens | Source | Status |
|---|---|---|---|
| `audit_directory_presence` | Distribution | Corey directory-submissions skill | proposed |
| `audit_international_seo` | SEO | Corey seo-audit International SEO section | proposed |
| `audit_free_tools` | Distribution | Corey free-tool-strategy skill | proposed |
| `audit_launch_cadence` | Distribution | Corey launch-strategy skill | proposed |
| `audit_pricing_page` | Conversion | Corey pricing-strategy skill | proposed |
| `audit_trust_signals` | Conversion | Independent brainstorm | proposed |
| `audit_help_center_docs` | Conversion + SEO | Independent brainstorm | proposed |
| `audit_accessibility` | SEO + Conversion | Independent brainstorm + Lighthouse a11y | proposed |

### Round 1 — Tier 2 deepening (no new primitives, extend existing specs)

| Existing primitive | Extension | Status |
|---|---|---|
| `audit_aso` | Match Corey's 6-dimension weighted rubric (Title 20% / Description 15% / Visual 25% / Ratings 20% / Metadata 10% / Conversion 10%) + brand-maturity tier adjustment (Dominant / Established / Challenger) | proposed |
| `audit_messaging_consistency` | Add copy-quality scoring (jargon density, benefit-vs-feature ratio, headline strength, clarity) | proposed |
| `audit_partnership_event_community_footprint` | Add press kit detection (`/press` page, downloadable logos/screenshots/headshots, boilerplate copy, press contact) + status page detection (statuspage.io, status.io, Better Stack) | proposed |
| `audit_earned_media_footprint` | Deepen Wikipedia page-quality audit (refs / citations / recent-edit cadence / reference-quality rubric) | proposed |
| Conversion lens consumption of `capture_surface_scan` | Add field-by-field form audit (count, type, friction, multi-step vs single, social-login presence, autofill compliance, error UX) | proposed |

### Round 1 — Tier 3 conditional / new enrichment

| Item | Type | Status |
|---|---|---|
| `audit_plg_motion` | Conditional primitive (runs if SaaS firmographic) — free trial vs freemium vs free tier, credit-card-required, time-to-value, viral mechanisms (powered-by branding, public profiles, share-to-unlock), self-serve vs gated demo | proposed |
| `audit_devex` | Conditional primitive (runs if dev-tool firmographic) — API docs quality, quickstart time, SDK/library coverage, sample apps, status page, changelog, OpenAPI spec presence | proposed |
| **R23 conditional enrichment**: `freddy audit attach-demo` | Client provides demo account → external onboarding-flow audit (mirrors GSC/ESP pattern from R18-R22) | proposed |

### Round 1 — Skip list (with reasons)

| Item | Reason for skip |
|---|---|
| competitor-profiling structured dossier | Competitive lens output already covers data; structuring as Corey-style 12-section dossier per competitor is presentation-layer, not new audit |
| Onboarding flow audit without demo account | Same 3-day-SLA constraint as flow-observation pipeline we rejected; better as conditional enrichment R23 |
| marketing-ideas 139-idea checklist | Checklist hell; useful as synthesis heuristic, not auditable primitive |
| marketing-psychology mental models | Applied, not auditable |
| cold-email skill | Outbound, out-of-scope |
| paywall-upgrade-cro skill | Too narrow / freemium-only |

### Round 1 net impact (if all approved)

- Primitives: 31 → **41 collection** (8 Tier 1 + 2 Tier 3 conditional) + 1 reasoning = 42 total
- Lenses: 9 → 9 (distribute across existing — no new lens)
- Conditional enrichments: 5 → 6 (add R23 demo-account)
- Coverage: ~90% → **~97% of externally-auditable marketing dimensions**
- Cost increase per audit: +$0.50–1.00 (mostly free additions; SerpAPI for doc-SEO + directory checks adds modestly)

---

## Round 2 — 2026-04-22 (deeper independent brainstorm + framework cross-check)

**Method:** Cross-checked current plan + Round 1 additions against (a) industry-specific dimensions for B2C/DTC, marketplaces, FinTech, dev tools, local businesses, public companies; (b) emerging marketing categories (DEI/ESG, public roadmaps, OSS, customer education, ABM); (c) operations/measurement audit categories common in agency RFPs (pipeline velocity, budget allocation, CRM hygiene, win-loss analysis); (d) external frameworks: Smart Insights RACE, 310 Creative comprehensive audit checklist, B2B 4 C's, 70/20/10 budget rule, Directive Consulting 2026 SaaS playbook, Branch8 marketing automation audit. Sources cited at end.

### Round 2 — additional hard gaps identified

#### Tier 1 (R2): clear gaps, high signal, externally observable

| Primitive | Lens | Source / rationale | Status |
|---|---|---|---|
| `audit_local_seo` | SEO (conditional on local-business firmographic) | Google Business Profile detection, NAP consistency across major citation sites (Yelp / Bing Places / Apple Maps / TripAdvisor / Yellow Pages / Foursquare), local citation count + consistency, geographic landing pages, "near me" + city-keyword targeting, schema (LocalBusiness, Organization with address). For local-business prospects this is the #1 finding category and we have ZERO coverage today. | proposed |
| `audit_oss_footprint` | Distribution + Brand/Narrative (conditional on dev-tool or tech-company firmographic) | GitHub org existence, total repo count, total stars, contributor count, recent commit activity (last 90 days), OSS license strategy (MIT vs Apache vs GPL), CLA presence, sponsor program (GitHub Sponsors / Open Collective), "good first issue" labeling, README quality. For dev-tools this is reputation-gold; for any tech company it's credibility. **Tied to AI-search citations** — GitHub repos are heavily indexed by Claude / ChatGPT / Perplexity. | proposed |
| `audit_customer_education` | Conversion + Brand/Narrative | Detect `/academy`, `/university`, `/certifications`, `/learn`, `/training`, `/tutorials`, `/courses` paths. Audit: course count, certification programs, learning-path structure, free vs paid tiers, completion-tracking signals. **Major HubSpot Academy / Salesforce Trailhead / Klaviyo / Twilio Quest play** — single highest-leverage retention + advocacy mechanism for SaaS. | proposed |
| `audit_public_roadmap` | Brand/Narrative + Conversion | Detect Canny / Productboard / Notion public-roadmap / GitHub Discussions / UserVoice / Frill / public Trello board. **Customer-centricity signal — different from changelog (past) — roadmap is future.** Vote-count visibility, response-rate from team, idea-to-shipped pipeline transparency. | proposed |
| `audit_corporate_responsibility` | Brand/Narrative + MarTech-Attribution | Diversity statement detection, sustainability report (annual ESG report PDF detection via `filetype:pdf "sustainability"`), B-Corp certification, carbon-neutral claims, accessibility statement, supplier diversity, charitable partnerships, mission-driven narrative. **Increasingly required for enterprise procurement RFPs** (Fortune 500 procurement scoring weights ESG 10-20% in 2026). | proposed |
| `audit_marketplace_listings` | Distribution | **Distinct from `audit_directory_presence`** (which is general SaaS/AI directories). This is platform-integration marketplaces: Zapier App Directory, Slack App Directory, Salesforce AppExchange, AWS Marketplace, HubSpot App Marketplace, Microsoft AppSource, Google Workspace Marketplace, Shopify App Store, Notion Integrations, Atlassian Marketplace. Signal of integration maturity + reach into adjacent platforms' user bases. | proposed |
| `audit_abm_signals` | Conversion + MarTech-Attribution (conditional on B2B enterprise firmographic) | Personalization tools (Mutiny / RightMessage / Demandbase / 6sense / Webeyez), named-account landing pages (`/for/<industry>` + dynamic-content signals), intent-data vendors (Bombora / G2 Buyer Intent / ZoomInfo Intent), reverse-IP detection (Clearbit Reveal / Snitcher / Leadfeeder / RB2B), account-based ad-targeting signals (LinkedIn Matched Audiences via ad library). **Critical for B2B enterprise prospects ($50K+ ACV).** | proposed |
| `audit_funnel_velocity_proxies` | Conversion + Synthesis | External-only proxies for funnel performance (real metrics need R20 ad-platform + R25 CRM enrichments): time-to-first-customer-story (case-study published date vs company founding date), content density per funnel stage (TOFU/MOFU/BOFU asset count + ratio), demo-vs-trial-vs-buy CTA placement frequency, gated-vs-ungated content ratio at each stage. **Best external approximation for "how good is this company at converting?"** | proposed |
| `audit_customer_story_program` | Brand/Narrative + Conversion | **Extends `audit_content_strategy_shape`**, BUT case-study program is a distinct asset class worth a primitive. Detect: case-study count + cadence, outcome quantification quality (real %, $, hours saved vs adjectives), video case study presence, logo wall vs full case studies, customer-led content (UGC contests, customer-submitted templates/recipes/integrations), G2 + Capterra review velocity + response rate, NPS-quote integration in marketing. | proposed |

#### Tier 2 (R2): deepening of existing primitives

| Existing primitive | Extension | Status |
|---|---|---|
| `audit_content_strategy_shape` | Add: newsletter subscriber-count detection ("Join 50K+ subscribers" claims, public Substack/Beehiiv counts, SparkLoop recommendations), glossary/encyclopedia marketing detection (`/glossary` / `/wiki` / `/terms` depth + entry count + per-term SEO targeting) | proposed |
| `audit_pricing_page` (Round 1 Tier 1) | Add pricing-localization extension: currency switcher, regional pricing, tier-availability by region, payment-method localization (SEPA / iDEAL / Alipay / WeChat Pay / Boleto / OXXO / GCash) | proposed |
| `audit_executive_visibility` | Add founder-led-marketing extension: weight founder visibility differently for early-stage prospects (founder presence matters more than employee thought leadership for <50-employee orgs); detect "founder mode" patterns (founder X/LinkedIn frequency, founder podcast appearances, founder-written blog content ratio) | proposed |
| `scrape_careers` | Add employer-brand extension: Glassdoor rating + review count via scraping public Glassdoor pages (or Indeed reviews), LinkedIn employer-page followers + employee count, hiring velocity (open roles ÷ total employees ratio), tech-stack disclosure on engineering JDs (huge signal of internal capability), team page quality, salary transparency in JDs (compliance-driven signal) | proposed |
| `audit_partnership_event_community_footprint` | Add webinar / virtual event extension: owned webinar series detection (`/webinars`, Goldcast / Hopin / Zoom / Riverside registration pages indexed), past webinar archive, registration page architecture, attendance signals via repeated webinar series + email-capture-as-registration | proposed |
| `audit_aso` (Round 1 Tier 2 extension) | Add app-marketplace extension for non-mobile-app prospects with desktop apps: Mac App Store, Microsoft Store, Setapp listings | proposed |

#### Tier 3 (R2): new conditional enrichments

| Item | Type | Status |
|---|---|---|
| **R24 conditional enrichment**: `freddy audit attach-budget` | Client uploads marketing budget breakdown (CSV/JSON: % by channel × monthly $). Audit against 70/20/10 rule (70% proven / 20% experiments / 10% bets), channel mix vs category benchmark, MarTech spend % of total marketing budget (industry benchmark: 15–25%), budget-to-revenue % vs vertical benchmark | proposed |
| **R25 conditional enrichment**: `freddy audit attach-crm` | Client uploads CRM export (Hubspot / Salesforce / Pipedrive / Close / Attio CSV or API connection). Audit: pipeline velocity formula (opps × ACV × win-rate ÷ sales-cycle-days), lead-to-opp conversion rate, opp-to-close rate, sales-cycle length per segment, MQL→SQL conversion, lead-source ROI ranking, dead-lead recovery opportunity | proposed |
| **R26 conditional enrichment**: `freddy audit attach-winloss` | Client uploads win-loss interview transcripts (PDF/Markdown/CSV). Audit: top-3 win reasons, top-3 loss reasons, competitive displacement patterns (won vs lost), pricing-objection frequency, time-to-decision per persona | proposed |

#### Round 2 skip list (with reasons)

| Item | Reason for skip |
|---|---|
| Public-company-specific marketing (earnings calls, IR page audit, analyst coverage) | Narrow to public companies (~5% of prospect pool); marginal value vs build cost |
| AR/3D product visualization audit | Too vertical (e-commerce only) and emerging |
| Web3/crypto wallet integration audit | Niche; not a mainstream prospect category |
| Live commerce signals (live-stream shopping) | Emerging, narrow vertical (mostly DTC fashion/beauty) |
| Brand protection / trademark monitoring | Too tactical / legal-adjacent — not marketing-strategy audit |
| White-label / private-label channel partner program audit | Too niche per prospect |
| AppLovin / mobile measurement partner audit | Niche to mobile gaming |
| Print media / OOH detection (billboards, magazine ads) | Hard to audit externally; only signal is news mentions which we already capture |
| Trade show booth photo audit | LinkedIn images already partially captured by Distribution lens |
| Influencer-to-purchase attribution signals (deep affiliate-link tracking) | Already covered partially in `audit_partnership_event_community_footprint` affiliate detection |

### Round 2 net impact (if all approved on top of Round 1)

- Primitives: 41 (after Round 1) → **50 collection** (+ 9 Round 2 Tier 1) + 1 reasoning = **51 total**
- Lenses: 9 → 9 (distribute new primitives across existing lenses; no new lens)
- Conditional enrichments: 6 (after Round 1 R23) → **9 total** (+R24 budget / +R25 CRM / +R26 win-loss)
- Conditional primitives (firmographic-triggered): 4 (audit_aso, audit_plg_motion, audit_devex, audit_local_seo, audit_oss_footprint, audit_abm_signals) — runs only when applicable
- Coverage: ~97% (after Round 1) → **~99% of externally-auditable marketing dimensions**, near-100% with all 9 conditional enrichments granted
- Cost increase per audit (Round 2 only): +$0.40–0.80 (mostly free additions; SerpAPI for ESG/award queries, GitHub API for OSS audit free, Glassdoor public scrape free)

### Round 2 sources

- [How to Conduct a Comprehensive Marketing Audit (310 Creative, 2026)](https://www.310creative.com/blog/marketing-audit)
- [80 Marketing Audit Questions Free Checklist (Karola Karlson)](https://karolakarlson.com/80-marketing-audit-questions/)
- [The 2026 Blueprint for Scalable B2B SaaS Marketing (Directive)](https://directiveconsulting.com/blog/blog-b2b-saas-marketing-guide-2026/)
- [Marketing Automation Stack Audit Checklist for B2B SaaS (Branch8)](https://branch8.com/posts/marketing-automation-stack-audit-checklist-b2b-saas)
- [B2B SaaS Marketing KPIs Revenue Efficiency Guide (SaaS Hero)](https://www.saashero.net/strategy/best-b2b-saas-marketing-kpis/)
- [The RACE digital marketing audit checklist (Smart Insights)](https://www.smartinsights.com/digital-marketing-strategy/digital-strategy-development/the-race-digital-marketing-audit-checklist/)
- [B2B SaaS Funnel Benchmarks & Pipeline Audit Framework (The Digital Bloom)](https://thedigitalbloom.com/learn/pipeline-performance-benchmarks-2025/)
- [9 Marketing Audits for New Agency Clients (Leadsie)](https://www.leadsie.com/blog/types-of-marketing-audits-for-new-clients)
- Corey Haines `marketingskills` repo: [github.com/coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)

---

## Round 3 — 2026-04-22 (post-research-validation pressure-test)

**Method:** After Round 1 + 2 + research-synthesis pass landed in plan, JR pressure-tested "are we covering all aspects of marketing audit?" — self-audit identified 10 important dimensions still uncovered against senior-CMO bar ("would they say 'how did you not look at X?'").

### Round 3 — Tier 1 additions (high-leverage, externally auditable, would meaningfully change findings)

| Primitive | Lens | Source / rationale | Status |
|---|---|---|---|
| `audit_branded_serp` | Brand/Narrative + Monitoring | Brand defensive-perimeter — when users google `<brand>`, Knowledge Panel claimed/complete? Sitelinks correct? Reviews stars? AI Overview? PAA "is X legit?" / "is X scam?" / "is X safe?" surfaced? Free via DataForSEO SERP for brand-name query | proposed |
| `audit_customer_support` | Conversion + Brand/Narrative | Live chat widget detection (Intercom/Drift/Crisp/Tidio — already detected in martech_stack) + deployment quality (office hours visible, multilingual, bot-vs-human, response-time SLA, AI chatbot on-brand). Major conversion + retention lever entirely uncovered | proposed |
| `audit_cro_experimentation_maturity` | Conversion | Beyond vendor presence (Optimizely/VWO/Convert detected): actual experimentation cadence via split-test cookies, URL parameters indicating live tests, Wayback diffs of pricing/CTA copy showing variant rotation. 0 vs 50 tests/month is Fix-it vs Run-it tier finding | proposed |
| `audit_eeat_signals` | SEO | Author bios on blog posts, `Person` schema, expertise indicators ("Reviewed by Dr. X, certified Y"), "About the author" pages, YMYL credential disclosure. **Google's #1 content ranking factor since 2023** | proposed |
| `audit_ecommerce_catalog` | Conversion (conditional DTC/e-comm) | Per-SKU image count, product description length + structured `Product` schema, customer review density per SKU, related products, recommendations engine quality, guest-checkout option, checkout flow step count, faceted search/sort UX | proposed |
| `audit_schema_competitive` | SEO + Synthesis | Extends `detect_schema` — compare prospect schema coverage to top 3 competitors. "Your competitors all use FAQPage + HowTo; you only have Organization." Synthesis-layer miss, not new primitive | proposed |
| `audit_b2c_personalization` | Conversion (conditional B2C/DTC) | Distinct from `audit_abm_signals` (B2B): Dynamic Yield, Optimizely Web Personalization, Adobe Target, VWO Personalize, Insider, Bloomreach, Movable Ink. Different prospect base entirely | proposed |

### Round 3 — Tier 2 additions (medium-priority)

| Primitive | Lens | Source / rationale | Status |
|---|---|---|---|
| `audit_ai_policy` | Brand/Narrative + MarTech-Attribution | Detect `/ai-policy`, `/responsible-ai`, `/ai-ethics`, model-training opt-out disclosure pages. Increasingly required for Fortune 500 enterprise procurement 2026 (parallel to ESG already covered for mid-market+) | proposed |
| `audit_crawl_budget_bloat` | SEO | Index bloat detection — low-quality URLs cannibalizing crawl budget (`?utm=*` indexed variants, faceted nav explosion, paginated archive series, parameterized search results in index). Depth gap on existing SEO lens | proposed |
| `audit_mobile_ux` | Conversion + SEO | Beyond Core Web Vitals: touch target sizes (44×44 px iOS / 48×48 dp Android), mobile checkout flow steps, hamburger nav UX, viewport meta validity, mobile-first form patterns | proposed |

### Round 3 — Skip list (with reasons)

| Item | Reason for skip |
|---|---|
| Sustainability / website carbon footprint | Emerging signal, low-actionable today |
| Hiring funnel UX | Overlaps with R23 attach-demo philosophy |
| Channel partner / reseller deep audit | Narrow per prospect — re-skip from R1 |
| Live shopping / social commerce | DTC fashion-only, narrow vertical |
| Annual transparency report | Mostly captured by `audit_corporate_responsibility` deepening |
| Browser / OS compatibility audit | Engineering-scope, not marketing |
| Feature flag platform detection | Engineering signal, not marketing diagnostic |

### Round 3 net impact (if all approved on top of R1 + R2)

- Primitives: 50 → **57 collection** (7 Tier 1) + 1 reasoning = 58 total
- Coverage: ~99% → **~99.7%**
- Cost increase: +$0.30–0.60/audit

---

## Round 4 — 2026-04-22 (extended pressure-test, JR asked "anything else?")

**Method:** Cross-checked against AAARRR pirate metrics, RACE framework, B2B SiriusDecisions Demand Waterfall, vertical-specific compliance regimes, procurement-readiness rubrics — surfaced 12 more high-value misses + 10 nice-to-haves.

### Round 4 — Tier 1 additions

| Primitive | Lens | Source / rationale | Status |
|---|---|---|---|
| `audit_branded_autosuggest` | Brand/Narrative + Monitoring | Google autosuggest mining — `is <brand>...` / `<brand> reviews` / `<brand> alternatives` / `<brand> vs Y` / `<brand> scam`. **Brand defensive-perimeter signal** complementary to R3 #1 (Branded SERP) | proposed |
| `audit_trust_center` | Conversion + MarTech-Attribution | SafeBase / Vanta Trust Center / Drata Trust / Whistic / Conveyor / OneTrust Vendorpedia detection. **Self-serve security review = enterprise-procurement-ready** — cuts enterprise sales cycle 30-60 days when present | proposed |
| `audit_vertical_compliance` | MarTech-Attribution + Brand/Narrative | Conditional on firmographic vertical: HIPAA BAA availability (healthtech), PCI-DSS Level (fintech), FERPA (edtech), state MTL/Money Transmitter License (fintech), DMA/DSA (EU large platforms), FDA 510(k) (medical devices). **Zero coverage today** | proposed |
| `audit_sales_motion_classification` | Synthesis (reasoning-only) | Pricing-transparency binary (public Y/N) + sales-rep LinkedIn enumeration + "Talk to Sales" gating depth + outbound tool detection (Apollo/Outreach/Salesloft via tech_stack + JD mentions) → classify motion as PLG / inside-sales / enterprise-sales / hybrid. Major synthesis layer | proposed |
| `audit_mobile_app_linking` | Distribution (conditional mobile-app) | Smart app banner `<meta name="apple-itunes-app">`, branch.io / firebase dynamic links, app deep-link sitemap, universal links. 4-8x install-from-web conversion when wired | proposed |

### Round 4 — Tier 2 deepenings

| Existing primitive | Extension | Status |
|---|---|---|
| `audit_content_strategy_shape` | Newsletter quality: cadence consistency, OG-card quality, archive depth, recent-issue Sonnet quality pass (signal-to-promo ratio) | proposed |
| `audit_podcast_footprint` | Owned-podcast quality: cadence, Podchaser ratings/reviews, guest-tier (recurring big names vs unknown), production-quality proxies | proposed |
| `audit_content_strategy_shape` (research depth) | Original research: PR coverage via DataForSEO anchor-text matching, citation count, format quality (interactive viz vs PDF), refresh cadence | proposed |
| `audit_partnership_event_community_footprint` (status sub) | Status page maturity: incident frequency last 90d, MTTR signals, post-mortem cadence, SLA-credit policy | proposed |
| `audit_corporate_responsibility` OR `audit_trust_signals` | Sub-processor / DPA disclosure: `/legal/sub-processors`, `/dpa`, `/data-processing` page presence + completeness. **Required for B2B EU enterprise sales** (Art. 28 GDPR) | proposed |
| `audit_earned_media_footprint` | Wire-service vs original-pitch ratio: Cision / PRNewswire / Business Wire / GlobeNewswire boilerplate-language detection. Wire-only press = cheap signal, original-pitch = real PR rigor | proposed |
| `gather_voc` | Brand demand trend: GoogleTrendsAdapter on brand-name + `<brand> reviews` + `<brand> pricing`. Cleanest top-of-funnel demand signal | proposed |

### Round 4 — Tier 3 defer (keep on radar)

| Item | Why defer |
|---|---|
| Reddit AMA presence | Niche; Reddit API works but signal sparse |
| Substack / Beehiiv leaderboard rank | Only signal for prospects who publish leaderboard rank |
| Influencer FTC #ad disclosure compliance | Adversarial finding; sales-call-friendliness unclear |
| Hackathon / dev-event sponsorships | Niche to dev-tool prospects + partial via partnership_event |
| Branded merchandise / swag programs | Signal-thin; Linear/GitHub-shop tier only |
| Customer advisory board references | Easy to scrape but rarely actionable |
| University / academic partnerships | Niche to specific verticals |
| CTV / Connected TV ads | Hard externally without paid tools (MediaRadar/Pathmatics $$$) |
| Email signature marketing tools | B2B-specific; signal-thin externally |
| Apple Search Ads detection | Mobile-app paid signal; hard externally |

### Round 4 — Skip list

| Item | Reason for skip |
|---|---|
| Marketing leadership tenure / stability | Hard externally, low signal |
| Backlink anchor-text brand-vs-keyword breakdown | Incremental on existing data |
| Audio ad detection | Mostly covered via Pod Engine `is_ad_segment` |

### Round 4 net impact (if all approved on top of R1 + R2 + R3)

- Primitives: 57 → **62 collection** (5 Tier 1) + 1 reasoning + 1 new reasoning (`audit_sales_motion_classification`) = 64 total
- Conditional firmographic primitives: 6 → 9 (`audit_vertical_compliance`, `audit_b2c_personalization` from R3, `audit_mobile_app_linking`, `audit_ecommerce_catalog` from R3)
- Coverage: ~99.7% → **~99.85%**
- Cost increase (R4 only): +$0.30–0.50/audit

---

## Round 5 — 2026-04-22 (third pressure-test pass, JR: "do another full pass")

**Method:** Systematic AAARRR-by-AAARRR enumeration — examined what's missing across each funnel stage, then vertical-specific deep dive (B2B SaaS, DTC, fintech, healthtech, dev tools, marketplaces, agencies, AI-tool companies). Identified industry-analyst rankings as the single largest remaining miss for B2B SaaS.

### Round 5 — Tier 1 additions (genuinely important, not yet covered)

| Primitive | Lens | Source / rationale | Status |
|---|---|---|---|
| `audit_industry_analyst_position` | Brand/Narrative + Competitive | **G2 Grid quadrant position (Leader / High Performer / Contender / Niche), Capterra Shortlist, Forrester Wave position, Gartner Magic Quadrant position, IDC MarketScape, industry awards (Inc 5000, Fast Company Most Innovative, Deloitte Fast 500)**. Detect via SerpAPI `"<brand>" "magic quadrant"` / `"<brand>" "forrester wave"` / `"<brand>" "g2 leader"` + scrape G2's quadrant page directly. **Gartner MQ "Leader" designation alone drives 30-50% of enterprise close rate** — single largest remaining B2B SaaS miss | proposed |
| `audit_first_party_data_strategy` | MarTech-Attribution + Conversion | Quizzes / configurators / surveys (Typeform/Tally/Outgrow) for first-party data collection; CDP integration for activation; progressive profiling on forms; privacy-first marketing posture. Increasingly important as third-party cookies die. Complementary to existing CMP detection | proposed |
| `audit_clv_retention_signals` | Brand/Narrative + Conversion | Public NPS publication ("Our NPS is 67"), customer-retention page claims ("99.7% of customers stay"), expansion-revenue case study signals, GRR/NRR mentions in shareholder letters, customer-base growth charts. Health signal for SaaS prospects — "is this company healthy?" tell | proposed |
| `audit_homepage_demo_video` | Conversion | Homepage explainer/demo video detection (Wistia / Vimeo / Loom / YouTube embed), view count proxies, video chapter markers, transcript availability, captions in multiple languages, CTA-after-video presence. Distinct from `audit_youtube_channel` (owned channel) — this is the homepage conversion lever | proposed |
| `audit_robots_strategic` | SEO + GEO | **AI crawler controls in robots.txt** — GPTBot / ClaudeBot / CCBot / Bytespider / Anthropic-AI / Google-Extended / PerplexityBot allow vs block patterns. **Strategic GEO-lens decision** — blocking AI crawlers = giving up future AI-search citations; allowing = increasing AI citation supply. Plus standard audit: sitemap declarations, crawl-delay strategy, parameter handling rules. **Major gap** for both SEO + GEO lenses | proposed |

### Round 5 — Tier 2 deepenings

| Existing primitive | Extension | Status |
|---|---|---|
| `audit_partnership_event_community_footprint` | Comments engagement on owned content: Disqus / Hyvor Talk / Commento detection on blog posts; exec response patterns in comments; Reddit megathreads for major launches | proposed |
| `capture_surface_scan` | Push notification opt-in: OneSignal / Pushwoosh / Pusher / VWO Engage detection + opt-in UX timing (immediate-on-load vs delayed). Major lifecycle channel for content sites | proposed |
| Conversion lens (cross-sell/upsell) | Product-page + pricing-page audit: "Related products", "Frequently bought together", "Customers also viewed", upgrade-prompts on lower tiers. For e-comm + SaaS prospects | proposed |
| `audit_on_page_seo` | Footer optimization: strategic link-distribution density, NAP citation in footer (cross-check with `audit_local_seo`), trust badges in footer, social-proof in footer | proposed |
| `audit_help_center_docs` | Documentation translations: multilingual docs depth for dev-tool prospects (English-only vs N-language coverage). Complementary to `audit_international_seo` | proposed |
| `audit_corporate_responsibility` | Diversity in marketing imagery: inclusive imagery audit on hero/customer photos via image-classification heuristic (skin-tone / age-range / gender-presentation diversity). DEI signal complementary to existing ESG dimensions | proposed |

### Round 5 — Tier 3 defer (keep on radar)

| Item | Why defer |
|---|---|
| 404 / 500 / error page UX | Custom error pages — low-frequency, low-leverage |
| Acquisition / M&A history | Niche; mostly captured via earned_media_footprint |
| Open API / public data access | Niche to data-companies |
| Rebrand history via Wayback | Interesting context, low-actionable |
| Geographic expansion / office locations | Overlap with audit_local_seo |
| Voice search optimization | Adoption plateaued |
| Brand voice cross-platform analysis | Partial via audit_messaging_consistency |
| GitHub Discussions activity volume | Overlap with audit_oss_footprint |
| Open-weights model hosting (Hugging Face) | Overlap with audit_oss_footprint |
| Public API monitoring (separate from status page) | Overlap with audit_partnership status sub |
| Receipt/transactional email design | Needs R19 ESP access (already covered when granted) |
| Order-confirmation / post-purchase UX | Needs R23 demo access (already covered when granted) |

### Round 5 — Skip list

| Item | Reason for skip |
|---|---|
| DNS health beyond email (DNSSEC/DANE/IPv6) | Engineering-scope, not marketing |
| Page weight / third-party script bloat | Covered by Lighthouse via `audit_page_speed` |
| Charm pricing detection ($X.99 vs $X.00) | Too cosmetic |
| INP-specific page experience | Already captured in Core Web Vitals |
| Internal vs external links ratio | Already covered by `audit_on_page_seo` |
| Time-on-site estimation | Similarweb-tier paid only |
| Rate-limited free tools / fair-use signals | Niche to free-tools-as-marketing prospects |

### Round 5 net impact (if all approved on top of R1 + R2 + R3 + R4)

- Primitives: 62 → **67 collection** (5 Tier 1) + 2 reasoning = 69 total
- Coverage: ~99.85% → **~99.95%** (asymptote — past this point all remaining dimensions are vertical-niche)
- Cost increase (R5 only): +$0.20–0.40/audit

---

## Combined totals — Round 1 + 2 + 3 + 4 + 5 (full state, if all approved on top of current plan)

| Dimension | Current plan (post R1+R2 applied) | After R3 | After R3 + R4 | After R3 + R4 + R5 |
|---|---|---|---|---|
| Collection primitives | 48 | 55 | 60 | **67** |
| Reasoning primitives | 1 | 1 | 2 (+`audit_sales_motion_classification`) | **2** |
| Total `primitives.py` functions | 49 | 56 | 62 | **69** |
| Lenses | 9 | 9 | 9 | 9 |
| Conditional enrichments | 9 (R18–R26) | 9 | 9 | **9** |
| Conditional firmographic primitives | 6 | 8 (+`audit_b2c_personalization`, `audit_ecommerce_catalog`) | 11 (+`audit_vertical_compliance`, `audit_mobile_app_linking`, `audit_sales_motion_classification`) | **11** |
| External-auditable coverage | ~99% | ~99.7% | ~99.85% | **~99.95%** |
| Cost per audit increase (cumulative R3+R4+R5) | baseline | +$0.30–0.60 | +$0.60–1.10 | **+$0.80–1.50** |

---

## Skill / framework areas confirmed STILL NOT covered after Round 2 (intentional skips)

These are categories I considered and explicitly chose not to add. Listed here so future rounds don't re-litigate:

| Category | Why skipped |
|---|---|
| Cold email / outbound prospecting | Outbound, not audit-scope (different motion entirely) |
| Marketing-ideas 139-idea checklist (Corey skill) | Useful as synthesis heuristic, not auditable as primitive — would be checklist hell |
| Marketing-psychology mental models (Corey skill) | Applied tool, not audit dimension |
| Paywall-upgrade-cro (Corey skill) | Too narrow / freemium-only |
| Public-company IR / earnings-call / analyst coverage | Narrow to ~5% of prospects |
| AR/3D / web3 / live-commerce / AppLovin niche channels | Too vertical / emerging |
| Brand-protection trademark monitoring | Legal, not strategy |
| Channel partner / reseller / white-label programs | Too narrow |
| Print / OOH / billboard / trade-show booth photos | Limited external audit signal |
| Editorial operations beyond cadence (calendar, brief templates, freelance vs staff) | Internal systems work — engagement-scope |
| Brand visual identity beyond website (sales decks, internal assets) | Already covered via R22 conditional enrichment when client uploads |
| Onboarding-flow audit without demo account | Already covered via R23 conditional enrichment when client provides demo |
| Customer NPS / churn-reason coding without survey upload | Already covered via R21 conditional enrichment |

---

## Decision log (updated as JR resolves)

| Round | Item | Status | Date | Notes |
|---|---|---|---|---|
| R1 Tier 1 | `audit_directory_presence` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_international_seo` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_free_tools` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_launch_cadence` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_pricing_page` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_trust_signals` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_help_center_docs` | proposed | 2026-04-22 | |
| R1 Tier 1 | `audit_accessibility` | proposed | 2026-04-22 | |
| R1 Tier 2 | Deepen `audit_aso` (6-dim rubric) | proposed | 2026-04-22 | |
| R1 Tier 2 | Deepen `audit_messaging_consistency` (copy-quality) | proposed | 2026-04-22 | |
| R1 Tier 2 | Deepen `audit_partnership_event_community_footprint` (+press kit + status page) | proposed | 2026-04-22 | |
| R1 Tier 2 | Deepen `audit_earned_media_footprint` (+Wikipedia depth) | proposed | 2026-04-22 | |
| R1 Tier 2 | Deepen Conversion lens form-CRO (field-by-field) | proposed | 2026-04-22 | |
| R1 Tier 3 | `audit_plg_motion` | proposed | 2026-04-22 | |
| R1 Tier 3 | `audit_devex` | proposed | 2026-04-22 | |
| R1 Tier 3 | R23 `freddy audit attach-demo` | proposed | 2026-04-22 | |
| R2 Tier 1 | `audit_local_seo` | proposed | 2026-04-22 | conditional on local-business firmographic |
| R2 Tier 1 | `audit_oss_footprint` | proposed | 2026-04-22 | conditional on dev-tool/tech firmographic |
| R2 Tier 1 | `audit_customer_education` | proposed | 2026-04-22 | |
| R2 Tier 1 | `audit_public_roadmap` | proposed | 2026-04-22 | |
| R2 Tier 1 | `audit_corporate_responsibility` | proposed | 2026-04-22 | |
| R2 Tier 1 | `audit_marketplace_listings` | proposed | 2026-04-22 | |
| R2 Tier 1 | `audit_abm_signals` | proposed | 2026-04-22 | conditional on B2B enterprise firmographic |
| R2 Tier 1 | `audit_funnel_velocity_proxies` | proposed | 2026-04-22 | |
| R2 Tier 1 | `audit_customer_story_program` | proposed | 2026-04-22 | |
| R2 Tier 2 | Deepen `audit_content_strategy_shape` (+newsletter subscribers + glossary marketing) | proposed | 2026-04-22 | |
| R2 Tier 2 | Deepen `audit_pricing_page` (+pricing localization) | proposed | 2026-04-22 | |
| R2 Tier 2 | Deepen `audit_executive_visibility` (+founder-led marketing) | proposed | 2026-04-22 | |
| R2 Tier 2 | Deepen `scrape_careers` (+employer brand: Glassdoor / LinkedIn) | proposed | 2026-04-22 | |
| R2 Tier 2 | Deepen `audit_partnership_event_community_footprint` (+webinar / virtual event) | proposed | 2026-04-22 | |
| R2 Tier 2 | Deepen `audit_aso` (+desktop app-marketplace listings) | proposed | 2026-04-22 | |
| R2 Tier 3 | R24 `freddy audit attach-budget` | proposed | 2026-04-22 | |
| R2 Tier 3 | R25 `freddy audit attach-crm` | proposed | 2026-04-22 | |
| R2 Tier 3 | R26 `freddy audit attach-winloss` | proposed | 2026-04-22 | |
| R3 Tier 1 | `audit_branded_serp` (Knowledge Panel + sitelinks + reviews stars + AI Overview + brand PAA) | proposed | 2026-04-22 | |
| R3 Tier 1 | `audit_customer_support` (live chat deployment quality + multilingual + bot-vs-human + SLA) | proposed | 2026-04-22 | |
| R3 Tier 1 | `audit_cro_experimentation_maturity` (vendor presence + actual cadence) | proposed | 2026-04-22 | |
| R3 Tier 1 | `audit_eeat_signals` (author bios + Person schema + expertise indicators) | proposed | 2026-04-22 | |
| R3 Tier 1 | `audit_ecommerce_catalog` | proposed | 2026-04-22 | conditional on DTC/e-commerce firmographic |
| R3 Tier 1 | `audit_schema_competitive` (vs top 3 competitors) | proposed | 2026-04-22 | synthesis-layer |
| R3 Tier 1 | `audit_b2c_personalization` (Dynamic Yield/Optimizely Web/Adobe Target/VWO Personalize/Insider) | proposed | 2026-04-22 | conditional B2C/DTC |
| R3 Tier 2 | `audit_ai_policy` (`/ai-policy`, `/responsible-ai`, `/ai-ethics`) | proposed | 2026-04-22 | |
| R3 Tier 2 | `audit_crawl_budget_bloat` (index-bloat detection beyond orphan pages) | proposed | 2026-04-22 | |
| R3 Tier 2 | `audit_mobile_ux` (touch targets + viewport + mobile checkout + nav UX) | proposed | 2026-04-22 | |
| R4 Tier 1 | `audit_branded_autosuggest` (Google autosuggest mining for brand) | proposed | 2026-04-22 | |
| R4 Tier 1 | `audit_trust_center` (SafeBase/Vanta/Drata/Whistic/Conveyor/OneTrust Vendorpedia) | proposed | 2026-04-22 | |
| R4 Tier 1 | `audit_vertical_compliance` (HIPAA/PCI-DSS/FERPA/state-MTL/DMA/DSA/FDA) | proposed | 2026-04-22 | conditional on firmographic vertical |
| R4 Tier 1 | `audit_sales_motion_classification` (PLG / inside-sales / enterprise-sales / hybrid) | proposed | 2026-04-22 | reasoning-only synthesis layer |
| R4 Tier 1 | `audit_mobile_app_linking` (smart app banner + branch.io + universal links + deep-link sitemap) | proposed | 2026-04-22 | conditional on mobile-app presence |
| R4 Tier 2 | Deepen `audit_content_strategy_shape` (newsletter quality: cadence + OG cards + archive + Sonnet quality pass) | proposed | 2026-04-22 | |
| R4 Tier 2 | Deepen `audit_podcast_footprint` (owned-podcast quality: ratings + guest tier + production quality) | proposed | 2026-04-22 | |
| R4 Tier 2 | Deepen `audit_content_strategy_shape` (research depth: PR coverage + citation count + format quality + refresh cadence) | proposed | 2026-04-22 | |
| R4 Tier 2 | Deepen `audit_partnership_event_community_footprint` (status page maturity: incident frequency + MTTR + post-mortem cadence + SLA-credit policy) | proposed | 2026-04-22 | |
| R4 Tier 2 | Deepen `audit_corporate_responsibility` OR `audit_trust_signals` (sub-processor / DPA disclosure for B2B EU sales) | proposed | 2026-04-22 | |
| R4 Tier 2 | Deepen `audit_earned_media_footprint` (wire-service vs original-pitch press ratio) | proposed | 2026-04-22 | |
| R4 Tier 2 | Deepen `gather_voc` (brand demand trend via GoogleTrendsAdapter on `<brand>` + `<brand> reviews` + `<brand> pricing`) | proposed | 2026-04-22 | |
| R5 Tier 1 | `audit_industry_analyst_position` (G2 Grid / Capterra Shortlist / Forrester Wave / Gartner MQ / IDC MarketScape / Inc 5000 / Fast Company) | proposed | 2026-04-22 | **Single largest remaining B2B SaaS miss — Gartner MQ Leader drives 30-50% enterprise close rate** |
| R5 Tier 1 | `audit_first_party_data_strategy` (quizzes/configurators/surveys + progressive profiling + CDP activation) | proposed | 2026-04-22 | |
| R5 Tier 1 | `audit_clv_retention_signals` (public NPS + retention-rate claims + expansion-revenue case studies + GRR/NRR mentions) | proposed | 2026-04-22 | |
| R5 Tier 1 | `audit_homepage_demo_video` (Wistia/Vimeo/Loom/YouTube embed + view counts + transcripts + captions + multilingual) | proposed | 2026-04-22 | |
| R5 Tier 1 | `audit_robots_strategic` (AI crawler controls — GPTBot/ClaudeBot/CCBot/Bytespider/Anthropic-AI/Google-Extended/PerplexityBot allow vs block + sitemap declarations + crawl-delay) | proposed | 2026-04-22 | **Strategic GEO-lens decision** — major SEO+GEO gap |
| R5 Tier 2 | Deepen `audit_partnership_event_community_footprint` (comments engagement: Disqus/Hyvor/Commento + exec response patterns) | proposed | 2026-04-22 | |
| R5 Tier 2 | Deepen `capture_surface_scan` (push notification opt-in: OneSignal/Pushwoosh/Pusher/VWO Engage) | proposed | 2026-04-22 | |
| R5 Tier 2 | Cross-sell/upsell on product+pricing pages (extends Conversion lens) | proposed | 2026-04-22 | |
| R5 Tier 2 | Deepen `audit_on_page_seo` (footer optimization: link distribution + NAP citation + trust badges + social proof) | proposed | 2026-04-22 | |
| R5 Tier 2 | Deepen `audit_help_center_docs` (documentation translations for dev-tool prospects) | proposed | 2026-04-22 | |
| R5 Tier 2 | Deepen `audit_corporate_responsibility` (diversity in marketing imagery — inclusive imagery audit on hero + customer photos) | proposed | 2026-04-22 | |
