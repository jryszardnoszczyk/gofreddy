# Marketing Audit Lens Ranking

**Date:** 2026-04-22 (updated 2026-04-23)
**Companion to:** `2026-04-22-005-marketing-audit-lens-catalog.md`
**Purpose:** Forced ranking of all ~325 core lenses by genuine value/usefulness — buyer-decision-shaping power, regulatory weight, diagnostic depth, signal quality, and engagement-conversion potential.

**Methodology:** ranked at the lens's value **when it applies**, not weighted by frequency of applicability. Conditional/vertical lenses noted as such. Effort, code complexity, cost, and report-density tradeoffs are NOT factored — those are downstream cutoff decisions.

## LOCKED FINAL RECOMMENDATION

- **167 always-on lenses** (cutoff at rank 167)
- **25 vertical bundles** (~200 conditional lenses; 1-3 fire per audit)
- **10 geo-conditional bundles** (~36 conditional lenses; 0-2 fire per audit)
- **5 segment-conditional bundles** (~30 conditional lenses; 1-2 fire per audit)
- **9 meta-frames at Phase 0** (sit at ranks 1-5 + 31/38/44/52)
- **Total catalog capacity:** ~591 lens slots
- **Typical audit firing:** ~185-195 lenses per audit
- **Catalog organized into 11 marketing areas** (deliverable view) + 23 super-sections A-W (engineering view) — see catalog doc for both

**Tier breakpoints (post-final reshuffle):**
- Ranks 1-25: Audit floor — must-have for "comprehensive" claim
- Ranks 26-65: Foundational (Tier 2) — drops here would feel like obvious gaps
- Ranks 66-135: High value, slightly situational (Tier 3)
- Ranks 136-167: Genuinely useful, narrower (Tier 4 above cutoff) — **CUTOFF LINE locked at rank 167**
- Ranks 168-200: Tier 4 below cutoff (most extracted to segment bundles)
- Ranks 201-280: Real but lower priority (Tier 5)
- Ranks 281-325: Long-tail / specialized / overlap-heavy (Tier 6)

## Boundary rerank addendum (2026-04-22)

After locking option-2 reshuffle, a focused rerank pass on items 100-180 (the cutoff boundary zone) identified 8 under-ranked items and 6+ items that should fire conditionally on geographic detection rather than appearing in the linear ranking at all. Changes applied below; original ranking preserved with strikethrough + promotion notes for traceability.

**Promotions within the boundary zone:**

| Lens | Old rank | New rank | Why promote |
|---|---|---|---|
| Email deliverability posture (SPF/DKIM/DMARC/BIMI/MTA-STS) | #115 (Tier 3) | **#70** | For any prospect doing email, deliverability failure = pipeline failure. Mandatory baseline. |
| Customer advocacy / champion / advisory board programs | #121 (Tier 4) | **#80** | For SaaS retention, advocacy is the moat. Champion programs predict expansion + reference revenue. |
| Brand salience proxy (Google Trends branded-search trajectory) | #112 (Tier 3) | **#75** | Single highest-leverage diagnostic for mid/late-stage prospects (Keller CBBE base). |
| Trust-mark stack (SOC 2 / ISO 27001 / HIPAA badges + DPF) | #124 (Tier 4) | **#85** (B2B-conditional) | For B2B enterprise prospects, pass/fail procurement gate. |
| Schema stacking for AI citation (3-4 complementary @types per page) | #134 (Tier 4) | **#95** | Directly drives AI citation lift (research shows 2x cite rate); cheap implementation. |
| PDF gating posture for Perplexity citation | #138 (Tier 4) | **#98** | Quick win — form-walled PDFs lose Perplexity citation entirely. |
| Effort asymmetry (clicks-to-cancel vs clicks-to-buy — Forrester CXi) | #162 (Tier 4) | **#100** | Forrester CX Index core diagnostic; brutally diagnostic + scriptable in one probe. |
| Vendor sprawl per category (2+ analytics / 2+ CDPs / 2+ chats co-loaded) | #175 (Tier 4) | **#110** | MarTech-debt indicator; predicts attribution chaos + maintenance drag. |

**New cutoff: rank 160 (was 135).** The boundary zone clearly contains higher-value items than my prior pass acknowledged. Lifting cutoff to 160 captures: AI-search depth (Bing/IndexNow/Brave/Agent-card/Product-feed cluster), 2-3 additional CX/T&S lenses (effort asymmetry already promoted), additional persuasion-density lenses, and several FTC compliance items.

**Items extracted to Geo-Conditional Bundles (see new section below):**

These were sitting in the linear ranking but should fire **conditionally on geo detection**, not be in always-on count:

- ~~#146 Quebec Law 25~~ → **EU-FR/Canada-Quebec geo bundle**
- ~~#148 UK ICO registration number~~ → **UK geo bundle**
- ~~#149 LGPD (Brazil) Encarregado~~ → **Brazil geo bundle**
- ~~#150 POPIA (South Africa) Information Officer + PAIA~~ → **South Africa geo bundle**
- ~~#151 China PIPL ICP license~~ → **China geo bundle**
- ~~#152 Switzerland nFADP + Swiss representative~~ → **Switzerland geo bundle**

Plus from Tier 5 (201-280):

- Japan APPI, South Korea PIPA, Singapore PDPA, Thailand PDPA, Vietnam PDPD, Philippines DPA → **APAC geo bundles**
- Argentina Ley 25.326, Colombia Ley 1581 → **LATAM geo bundles**
- UAE PDPL, Saudi PDPL, Israel PPL → **MEA geo bundles**
- Australian Privacy Act + 2026 reforms → **Australia geo bundle**

This removes ~14 lenses from always-on count and bundles them into **10 geo-conditional bundles** that fire only when prospect has presence in that geography (hreflang signal + ccTLD + currency + local CDN + privacy-policy enumeration).



---

## Tier 1: Audit floor — ranks 1-25 (must-have)

**Reshuffle applied:** Top 5 promoted to meta-frames (W-section). Tactical lenses shift down by 5 slots. Meta-frames sit above tactical lenses because they shape interpretation of every tactical finding (e.g., "low review-site count" means something different at a brand in growth-trajectory vs decline-trajectory).

| # | Lens | Catalog ref |
|---|---|---|
| 1 | **Traffic-mix ratio** (direct/organic/paid/social/referral/email — single most diagnostic chart) | W5 |
| 2 | **Channel-model fit** (Balfour Four Fits — does pricing/ACV support the channels they're running?) | W1 |
| 3 | **Traffic trajectory 12-month delta** (growth / plateau / decline — shapes every other finding) | W7 |
| 4 | **Growth loops vs funnel inventory** (Reforge — can any compound? catalog public loops) | W2 |
| 5 | **Marketing-maturity tier** (Kotler / Forrester 6-axis — strategy / org / systems / function) | W4 |
| 6 | Review-site posture (G2/Capterra/TrustRadius/TrustPilot/GetApp/Software Advice) | D1 |
| 7 | Case studies depth + recency + breadth | G5 |
| 8 | Pricing page architecture + transparency | G7 |
| 9 | Tech SEO health (CWV, security headers, redirects, sitemap, canonicalization) | A1 |
| 10 | Value proposition clarity + above-fold + CTA hierarchy | G2 |
| 11 | Positioning + narrative clarity | K1 |
| 12 | Free tools / lead magnets / engineering-as-marketing inventory | F1, F2 |
| 13 | Programmatic SEO posture | A6 |
| 14 | Comparison-page strategy (own /vs-X + /alternatives + hub architecture) | G6, M3 |
| 15 | Research reports / "State of X" authority plays | F4 |
| 16 | On-page SEO | A2 |
| 17 | Sales enablement public assets (/security, /soc2, ROI calcs, trust center) | J2 |
| 18 | Verticalization / persona-site architecture | J1 |
| 19 | Integration marketplaces (Zapier, Salesforce, Shopify, Slack, MS, Chrome, AWS/Azure/GCP) | D3 |
| 20 | Attribution maturity + server-side GTM + CAPI + Enhanced Conversions | L2 |
| 21 | AI search citation patterns (actual AIO presence + schema stacking + tracking tooling) | A13, O4 |
| 22 | Form CRO (demo / contact / lead) | G8 |
| 23 | Onboarding CRO (aha moment + checklist + empty states + tours) | H1 |
| 24 | Content pillars / topic clusters | A8 |
| 25 | Template library (Figma/Canva/Notion model) | F3 |

## Tier 2: Foundational — ranks 26-65

**Reshuffle applied:** 4 remaining meta-frames promoted in (W6, W8, W3, W9). 6 high-stakes regulatory lenses promoted up from Tier 4 (Consent Mode v2 quality, EU AI Act Article 50, EAA/WCAG 2.2, Multi-state US privacy, Click-to-Cancel FTC, Sub-processor page, EU-US DPF certification) — these are 2026-enforcement gates that B2B SaaS prospects will increasingly fail. Tier 2 widened from 35 to 40 slots to absorb promotions; original Tier 2 items shift down accordingly. Items previously at these slots are noted as moved to Tier 3.

| # | Lens | Catalog ref |
|---|---|---|
| 26 | Launch + niche directories (full 17-platform Tier-1 + Tier-2/3) | D2 |
| 27 | Press coverage + tier distribution | C1 |
| 28 | Thought leadership program (sustained public output) | K3 |
| 29 | Signup flow CRO | G9 |
| 30 | Demo / trial flow architecture | G11 |
| 31 | **Share-of-voice vs named competitors** (search + social + display) | W6 |
| 32 | **Consent Mode v2 quality** (4 params pre/post consent — June 2026 single-control transition) [↑ from #67] | L4, U1 |
| 33 | MarTech stack inventory (BuiltWith / Wappalyzer 20+ categories) | L1 |
| 34 | Logo wall + dead-logo-ratio + homepage social-proof density | G3 |
| 35 | Customer language alignment (JTBD framing) | K2 |
| 36 | Paid creative corpus (Foreplay/Adyntel hook taxonomy + spend intensity) | B1 |
| 37 | **EU AI Act Article 50 readiness** (chatbot disclosure + AI-content labeling — binding Aug 2026) [↑ from #143] | O9, U20 |
| 38 | **Geo / country mix** (ICP-channel mismatch detector) | W8 |
| 39 | AI bot access — differentiated training-vs-answer-engine policy | A14, O1 |
| 40 | llms.txt / machine-readable files / markdown twins (low weight) | A15, O2 |
| 41 | Content extractability for LLMs (semantic HTML + lead-answer format) | A16, O3 |
| 42 | **EAA / WCAG 2.2 conformance + accessibility statement + VPAT** (€100k EU penalties since June 2025) [↑ from #144] | U19 |
| 43 | Lead magnet inventory by format (ebook/checklist/template/swipe-file/quiz/webinar) | F2 |
| 44 | **North-star metric / vanity-metric tell** (what do they publicly brag on? MRR vs follower count) | W3 |
| 45 | Trust signals density (security badges, testimonials with names, customer counts) | G4 |
| 46 | ASO — App Store + Google Play (when mobile applies) | D4 |
| 47 | Customer switching narratives ("/switch-from-X" content + testimonials) | M5 |
| 48 | Page CRO by page type (homepage / landing / pricing / feature) | G1 |
| 49 | **Multi-state US privacy enumeration** (18+ active state laws by 2026 — CA/VA/CO/CT/UT/TX/OR/MT/IA/TN/DE/NH/NJ/MN/MD/IN/KY/RI...) [↑ from #145] | U8 |
| 50 | Freemium / free-tier / migration tools | H2 |
| 51 | Certifications program (HubSpot Academy / Trailhead / AWS Certs model) | K4 |
| 52 | **Engagement tier proxies** (bounce / session duration / pages-per-session — SimilarWeb) | W9 |
| 53 | Cancel flow / churn prevention UX (MRR-tier routing + save offers) | I8 |
| 54 | **Click-to-Cancel FTC compliance** (online-cancel for online-signup — effective 2025/2026) [↑ from #157] | I8, U15 |
| 55 | Analyst relations posture (Gartner / Forrester / IDC) | C2 |
| 56 | Public API / developer portal (when dev-tool applies) | N1 |
| 57 | Founder / exec content posture (LinkedIn cadence + Substack + podcast guesting) | E3 |
| 58 | Owned events / flagship event (Dreamforce / INBOUND / Signal) | K5 |
| 59 | **Sub-processor page + DPA self-serve download** (GDPR Art. 28; B2B procurement gate) [↑ from #153] | J2, U26 |
| 60 | Proprietary data journalism (/insights, /benchmarks) | F5 |
| 61 | Enrichment / identity resolution (RB2B / Clearbit Reveal / Leadfeeder + geo-gating) | J9 |
| 62 | CRO tooling (Optimizely / VWO / Mutiny / Intellimize) | L6 |
| 63 | Product analytics (Amplitude / Mixpanel / PostHog / Heap) | L8 |
| 64 | **EU-US Data Privacy Framework (DPF) active certification** (replaces Privacy Shield; verifiable on dataprivacyframework.gov) [↑ from #147] | U23 |
| 65 | Owned community (Slack / Discord / Circle / Skool — depth, not just presence) | E6 |

## Tier 3: High value, slightly situational — ranks 66-135 (REBUILT v2)

**Renumbered after option-C final reshuffle (extend-surgically + segment bundles).** 12 boundary promotions inline (marked **↑**). 8 overlap items folded into existing lenses (marked italicized in catalog ref). 70 items.

| # | Lens | Catalog ref |
|---|---|---|
| 66 | Objection handling content (FAQ depth + "why us") | J5 |
| 67 | Popup CRO (triggers + copy + frequency + compliance) | G10 |
| 68 | Internal linking + hub-and-spoke architecture | A3 |
| 69 | Site architecture / IA (navigation, URL taxonomy, breadcrumb alignment) | A7 |
| 70 | **Email deliverability posture (SPF/DKIM/DMARC/BIMI/MTA-STS)** [↑ from #115] | I11 |
| 71 | Status page + uptime transparency (sophistication tier) | K6 |
| 72 | Wikipedia entry quality + monitored-vs-unmonitored | A25 |
| 73 | Welcome / onboarding email sequence | I2 |
| 74 | Open source community depth (stars / issues / PRs / contributors) | N5 |
| 75 | **Brand salience proxy (Google Trends branded-search trajectory)** [↑ from #112] | K9 |
| 76 | Event-naming discipline + funnel instrumentation depth | L3 |
| 77 | Session replay / heatmap (Hotjar / FullStory / Mouseflow) | L7 |
| 78 | Paywall UX by trigger type (feature gates / usage limits / trial expiration) | H3 |
| 79 | Content refresh discipline (post dates + half-life + "last updated" cadence) | A11 |
| 80 | **Customer advocacy / champion / advisory board programs** [↑ from #121] | (in K) |
| 81 | Podcast guesting at scale (CEO ≥6 in 12mo + guest-graph centrality) | E5 |
| 82 | Buyer-stage keyword coverage (awareness/consideration/decision/implementation) | A10 |
| 83 | ESG / sustainability / DEI positioning (B Corp / 1% / Climate Neutral / SBTi / EcoVadis) | K7 |
| 84 | RevOps stack (CRM + MAP + sales engagement + lead-scoring fingerprint) | L9 |
| 85 | **Trust-mark stack (BBB / Norton / SOC 2 badge / ISO 27001 / DPF)** [↑ from #124, B2B-conditional] | (in U22) |
| 86 | Glossary / /learn-X long-tail SEO | A17 |
| 87 | Customer research tooling (SparkToro / Dovetail / User Interviews) | L10 |
| 88 | International SEO (hreflang/canonical/locale URL + RTL + local case studies + self-ref hreflang) *folds: #189-192* | A4 |
| 89 | Ad creative format diversity (RSA/Meta/LinkedIn/TikTok native) | B3 |
| 90 | Speed-to-lead (test via demo-form submission) | G13, J7 |
| 91 | Lead scoring + MQL-SQL lifecycle | J8 |
| 92 | Booking friction (Calendly / SavvyCal / Chili Piper / HubSpot Meetings) | G12, J6 |
| 93 | ABM tooling (6sense / Demandbase / Terminus + reverse-IP personalization) | J10 |
| 94 | Board / advisor / investor credibility signaling | K8 |
| 95 | **Schema stacking for AI citation (3-4 complementary @types per page)** [↑ from #134] | A19, O4 |
| 96 | Owned podcast (sustained brand-affinity engine) | E4 |
| 97 | UTM taxonomy discipline + Dub-style centralized shortlinks | L5 |
| 98 | **PDF gating posture for Perplexity citation** [↑ from #138] | A13 |
| 99 | Courses + books (authority depth) | F6 |
| 100 | **Effort asymmetry (clicks-to-cancel vs clicks-to-buy — Forrester CXi)** [↑ from #162] | Q1 |
| 101 | Awards + "as seen in" badges (G2/Capterra/Gartner badges) | C3 |
| 102 | Billing email suite (renewal / failed-payment / cancel-survey / annual-switch) | I5 |
| 103 | Short-form video strategy (TikTok / Reels / Shorts cadence + posture) | E2 |
| 104 | Pre-targeting / warmup ad strategy | B6 |
| 105 | **Help center / docs maturity** (article count + last-edited + "helpful?" widget + KB depth + recency) *folds: #164* [↑ from #163] | T1, T3 |
| 106 | API docs tooling (ReadMe / Mintlify / Stoplight / Redoc / Scalar) | N3 |
| 107 | Hacker News submission / Show HN history | N6, N7 |
| 108 | Retargeting pixel coverage across site | B5 |
| 109 | Review-request automation (feeds D1 review sites) | I7 |
| 110 | **Vendor sprawl per category (2+ analytics / 2+ CDPs / 2+ chats — MarTech debt)** [↑ from #175] | L16 |
| 111 | Paid platform breadth (Google/Meta/LinkedIn/TikTok/Reddit/Quora) | B2 |
| 112 | SDK language coverage (when API product) | N2 |
| 113 | NPS survey program (Delighted / Wootric / SurveyMonkey) | I6 |
| 114 | AI-feature marketing (ChatGPT GPT Store + Copilot agents + Perplexity Spaces + MCP) | H5, O7 |
| 115 | **AI-chat handoff transparency** (scripted chat → human latency + widget routing detection) *folds: #175* [↑ from #162] | T2, L18 |
| 116 | Product usage digest emails (daily / weekly / monthly) | I3 |
| 117 | Marketing Jiu-Jitsu / counter-positioning | M2 |
| 118 | Parasite SEO / external-platform publishing (Medium / LinkedIn / Substack) | A12 |
| 119 | Win-back / trial reactivation sequence | I9 |
| 120 | Press / media kit availability + completeness score (newsroom freshness + journalist quote density + leadership cadence overlap) *folds: #193-194, #197* | J3, C1, C11 |
| 121 | Developer hackathon presence + sponsor-of-record | N4 |
| 122 | Searchable vs shareable content balance | A9 |
| 123 | Competitive ad research (overlap with B1 from competitor angle) | M1 |
| 124 | Viral loops / PLG distribution signals | H6 |
| 125 | **Public roadmap (Productboard / Canny / GitHub Projects publicly visible)** [↑ from #184] | N9 |
| 126 | "Powered by X" badge detection | H7 |
| 127 | Creator / ambassador program (/creators, /ambassadors) | E7 |
| 128 | **Tag-manager hygiene (pre-consent script firing + GTM container size + deprecated pixels)** [↑ from #173, GDPR-critical] | L15 |
| 129 | Milestone / achievement emails | I4 |
| 130 | Changelog / public release cadence + author attribution | H4 |
| 131 | EEAT signals (overlaps K3 thought leadership) | A5 |
| 132 | Capture surface scan (popup / form / SMS / lead-magnet / content-upgrade) | I1 |
| 133 | Lifecycle stack maturity (ESP/SMS/loyalty/reviews/referral/subscription) | I10 |
| 134 | Marketing psychology cross-cut (Cialdini-6 density + scarcity authenticity) | P1 |
| 135 | Microsite / subdomain-sprawl audit | (Long-tail) |

## Tier 4: Genuinely useful, narrower — ranks 136-167 (REBUILT v2)

**Items 136-167 are above the recommended cutoff line.** 3 new boundary promotions inline (marked **↑**). Account-tier landing (was #186) folded into Verticalization at Tier 1 #18. Numbering is absolute.

| # | Lens | Catalog ref |
|---|---|---|
| 136 | Contract buyout / migration offers (overlap H2) | M4 |
| 137 | Organic social footprint | E1 |
| 138 | Customer-Cloud / partner-overlap signaling (Crossbeam / Reveal) | J17 |
| 139 | Brand esteem / sentiment delta (review-platform sentiment polarity) | K10 |
| 140 | Refund / guarantee / returns policy visibility + specificity | G14 |
| 141 | Offer construction (anchor pricing + bonuses + urgency + risk-reversal) | G15 |
| 142 | **Form progressive-profiling fingerprint (return visit returns fewer fields)** [↑ from #187] | G8 |
| 143 | Employer brand / careers-page-as-marketing (Glassdoor + Stripe-Press style + DEI) | K17 |
| 144 | Investor relations page (SEC filings + ESG report + analyst coverage) | K18 |
| 145 | Referral / share mechanics (codes + share-with-team + two-sided) | I14 |
| 146 | Brand differentiation (BAV vitality/stature) | K11 |
| 147 | Brand personality consistency / voice drift across surfaces | K12 |
| 148 | AI-generated copy density in own copy ("AI tells" — em-dash + lexical scan) | A22, K13 |
| 149 | Self-reported attribution field in demo/trial forms ("How did you hear about us?") | L13 |
| 150 | **Channel partner program (/resellers / /partners/reseller / white-label tier)** [↑ from #180] | J16 |
| 151 | MMM infrastructure (Meridian / Robyn / Recast — jobs + vendor case studies) | L12 |
| 152 | AI citation tracking tooling presence (Profound / Peec / Otterly / AthenaHQ) | L11 |
| 153 | Schema @graph composability (linked types via shared @id) | A19 |
| 154 | WebSite SearchAction (sitelinks search box) schema | A19 |
| 155 | Voice-search / natural-question formatting | A18 |
| 156 | Bing Webmaster + IndexNow posture (Copilot citation prerequisite) | A13 |
| 157 | Brave Search visibility (Claude citation prerequisite) | A13 |
| 158 | Agent-card / MCP discoverability (/.well-known/agent-card.json + MCP server) | O5 |
| 159 | Product feed for AI commerce (UCP manifest + Product JSON-LD with gtin) | O6 |
| 160 | TCPA / SMS-consent compliance | U16 |
| 161 | CAN-SPAM / CASL compliance | U17, U18 |
| 162 | FTC Endorsement Guides + #ad disclosure ratio (influencer audit) | U21, B20 |
| 163 | FTC junk-fee rule disclosure | U15 |
| 164 | FTC fake-reviews crackdown compliance (no incentivized hidden reviews) | U21 |
| 165 | Comparative-advertising claim substantiation (Lanham Act §43(a)) | U21 |
| 166 | **"Best-of" editorial listicle inclusion ("best X tools 2026" coverage)** [↑ from #195] | C6 |
| 167 | Stale-trust-page red flag (Norton/McAfee/TRUSTe-original = decommissioned) | U28 |

---

### ✂️ CUTOFF LINE — LOCKED at rank 167 (recommended always-on scope)

Everything above this line is **always-on**. Items below are cut from default scope, moved to segment-conditional bundles, or folded into higher-ranked lenses as sub-signals. Re-add individually only if a specific use-case requires it.

---

| # | Lens | Catalog ref |
|---|---|---|
| 161 | Resolution channel parity (chat/phone/email/self-serve KB) | Q2, T2 |
| 162 | AI-chat handoff transparency (scripted chat → human latency) | T2 |
| 163 | Help center / docs maturity (article count + last-edited + helpful widget) | T1 |
| 164 | Knowledge base depth + recency | T3 |
| 165 | Community-support ratio (forum / Discord / Discourse vs ticket-only) | T4 |
| 166 | Public Storybook presence (storybook./design./ui. probe + index.json) | S1 |
| 167 | Component count + last-publish (from Storybook manifest) | S2 |
| 168 | Brand portal accessibility (Frontify / Brandfolder / Bynder / brand. presence) | S4 |
| 169 | Press-kit completeness score (logos 3+ formats / tokens / typography / bios / fact sheet) | J3, S5 |
| 170 | Logo-version sprawl (distinct SVG hashes across surfaces) | S6 |
| 171 | Color drift (hex distance: stated brand color vs actual CSS) | S7 |
| 172 | Typeface license posture (self-hosted vs Adobe / Typekit / Google) | S8 |
| 173 | Tag-manager hygiene (GTM container size + deprecated pixels) | L15 |
| 174 | CDP / reverse-ETL fingerprint (Segment / RudderStack / Hightouch / Census) | L17 |
| 175 | Chat widget detection + routing (Intercom vs Drift vs Tidio) | L18 |
| 176 | Conversation intelligence presence (Gong / Chorus / Wingman / Fathom on demo pages) | J14 |
| 177 | Customer journey orchestration (Adobe AJO / Braze Canvas / Iterable) | J15 |
| 178 | AI SDR agent in own outbound (Artisan/11x/Regie demo-response fingerprints) | J12, O12 |
| 179 | Sales engagement / outbound infrastructure (Outreach / Salesloft / Apollo / Instantly) | J13 |
| 180 | Channel partner program (/resellers / /partners/reseller / white-label) | J16 |
| 181 | Clean-room posture (LiveRamp / Snowflake / Habu — case-study + careers signals) | J11 |
| 182 | Postman API Network / RapidAPI listing (followers + fork count) | N12 |
| 183 | DevRel team signaling (jobs page DevRel roles + technical blog) | N8 |
| 184 | Public roadmap (Productboard / Canny / GitHub Projects publicly visible) | N9 |
| 185 | AI-coding-tool integrations (Cursor / Cline / Windsurf rules; .mdc files) | N11 |
| 186 | Account-tier landing pages (/enterprise/<industry> depth) | J1 |
| 187 | Form progressive-profiling fingerprint (return visit returns fewer fields) | G8 |
| 188 | MQL-handoff transparency (jobs / careers MOps role descriptions) | J8 |
| 189 | Hreflang/locale matrix coverage vs claimed-market footprint | A4 |
| 190 | Local-case-study parity (case studies per non-English locale vs English) | A4 |
| 191 | RTL rendering quality (Lighthouse on ar-SA) | A4 |
| 192 | Self-referencing hreflang integrity + canonical-hreflang-cluster validity | A4 |
| 193 | Newsroom freshness gradient (median days between last 10 releases) | C1 |
| 194 | Journalist quote density (named outlets in last 12 months) | C1 |
| 195 | "Best-of" editorial listicle inclusion ("best X tools 2026" coverage) | C6 |
| 196 | Internal-comms-as-external-signal (Glassdoor / Comparably velocity + response) | C10 |
| 197 | Leadership content cadence (CEO LinkedIn post frequency + reply rate) | C11 |

## Tier 5: Real but lower priority — ranks 198-277 (REBUILT, shifted by -3 due to Tier 4 promotions)

**Renumbering note:** Items below shift down by ~3 ranks vs original numbering. Numbers preserved as relative ordering for catalog cross-reference.



| # | Lens | Catalog ref |
|---|---|---|
| 201 | Onboarding email sequence observation (fake-signup + 7-14d) | I13 |
| 202 | Footer trust-cluster density (privacy/terms/security/accessibility/sitemap) | (cross-cut) |
| 203 | Cookie banner first-firing audit (scripts firing pre-consent) | U33 |
| 204 | Data-retention policy disclosure | U34 |
| 205 | Data-breach notification policy + history | U35 |
| 206 | DSA / DMA / DORA / NIS2 / MiCA EU compliance | U20 |
| 207 | ISO 42001 (AI management system) — emerging | U24 |
| 208 | NIST AI RMF alignment claim | U24 |
| 209 | SOC 2 Type II vs SOC 3 distinction | U22 |
| 210 | PCI DSS v4.0 specificity (post-March 2025 v3.2.1 = stale) | U22 |
| 211 | HITRUST tier specificity (r2/i1/e1) | U22 |
| 212 | FedRAMP / StateRAMP / TX-RAMP / AZ-RAMP / TISAX / IRAP / C5 | U22 |
| 213 | CSA STAR Level 1/2/3 registry presence | U22 |
| 214 | TrustArc / ePrivacyseal / EuroPriSe (EU privacy seals) | U23 |
| 215 | JIPDEC PrivacyMark (Japan) | U23 |
| 216 | APEC CBPR / Global CBPR participant | U23 |
| 217 | TCF v2.2 / GPP (Global Privacy Platform) compliance | U10 |
| 218 | DAA AdChoices icon presence | U10 |
| 219 | AI-content provenance (C2PA / content credentials) in marketing imagery | O11 |
| 220 | Trademark / IP / patent signaling (USPTO search) | U25 |
| 221 | MAP (Minimum Advertised Price) policy disclosure | U29 |
| 222 | Prop 65 warnings (CA — placement on product pages) | U30 |
| 223 | State AI-ad disclosure (multi-state political and consumer) | U31 |
| 224 | Crypto/web3 OFAC compliance (jurisdictional ToS) | U32 |
| 225 | Newsletter sponsorship economy (Beehiiv / Sponsy / Paved / Swapstack) | B19 |
| 226 | B2B influencer / LinkedIn-creator activation | B20 |
| 227 | Influencer whitelisting (running ads through creator accounts) | B20 |
| 228 | Substack network posture (Notes cadence + recommendations + Chat + paid-tier) | E11 |
| 229 | Beehiiv network growth (Boosts + referral tier + Recommendations) | E12 |
| 230 | Discord sophistication (Onboarding quest + Forum channels + AutoMod + Stage) | E6 |
| 231 | Slack sophistication (Slack Connect + Workflow Builder + Canvas) | E6 |
| 232 | Stack Overflow / Reddit moderator status (owns subreddit/tag = moat) | E6 |
| 233 | Mastodon / Bluesky / Threads custom-feed-ownership / instance-ownership | E16 |
| 234 | Live audio (Twitter Spaces / LinkedIn Audio) | E8 |
| 235 | Conference speaking + sponsor visibility | E21, E22 |
| 236 | TikTok Spark Ads ratio + Symphony usage + GMV Max + Live Shopping cadence | B7 |
| 237 | Amazon AMC + Sponsored TV + Brand Store 2.0 + Rufus-readiness | B8 |
| 238 | Apple Search Ads CPP variants + 5-campaign canonical structure | B9 |
| 239 | Retail Media Networks breadth (Walmart / Roundel / Kroger / Chase / Uber / DoorDash / Costco) | B10 |
| 240 | CTV sophistication (DSP mix + shoppable + creative count + co-viewing measurement) | B11 |
| 241 | Audio sophistication (SPAN/AdsWizz/SiriusXM + chapter sponsorships + pixel incrementality) | B12 |
| 242 | OOH / pOOH (Vistar/Hivestack/AdQuick + trigger-based + geo-fenced retargeting) | B13 |
| 243 | LinkedIn paid sophistication (Conversation Ads + TLA + LinkedIn CTV + Predictive Audiences) | B14 |
| 244 | Google Performance Max maturity (asset groups + signals + brand exclusions + Search Themes) | B15 |
| 245 | Reddit Ads sophistication (Conversation Placements + Subreddit precision + AMA Ads) | B16 |
| 246 | Pinterest sophistication (Premiere Spotlight + Idea Ads + Trends-API creative) | B17 |
| 247 | Snap / X / Bluesky / X-Ad inventory | B18 |
| 248 | Click-to-Messenger / DM-objective ads (Meta / Insta / WhatsApp Business) | B21 |
| 249 | Pixel sharing / audience-sharing partnerships (legacy) | B22, M6 |
| 250 | Time-to-value across the funnel (signup → aha) | Q4 |
| 251 | Feedback-loop presence (in-app feedback widget + NPS prompt + ticket follow-up) | Q5 |
| 252 | Service-recovery posture (response to negative reviews / public complaints) | Q6 |
| 253 | Customer journey transparency ("what happens next" content) | Q7 |
| 254 | Onboarding-to-CSM handoff visibility | Q8 |
| 255 | Voice & tone consistency across surfaces | Q9 |
| 256 | Emotion words in microcopy (confirmation / error / empty-state pages) | Q3 |
| 257 | Reading-grade variance across surfaces (Flesch-Kincaid) | P6 |
| 258 | Pronoun ratio ("we" vs "you") | P7 |
| 259 | Anchoring (pricing-page anchor placement) | P2 |
| 260 | Loss aversion framing | P3 |
| 261 | Default bias / choice architecture (preselected options) | P4 |
| 262 | Framing effects in copy | P5 |
| 263 | Transparency-report cadence (annual / quarterly / none) | R1 |
| 264 | Abuse-reporting flow depth (clicks-to-report from any UGC) | R2 |
| 265 | Content moderation policy (for UGC platforms) | R3 |
| 266 | Security disclosure policy / security.txt (/.well-known/security.txt) | R4 |
| 267 | Bug bounty program (Immunefi / HackerOne / Bugcrowd + max payout) | R5 |
| 268 | Vulnerability disclosure timeline | R6 |
| 269 | Thumb-zone CTA placement (375×667 viewport y-coordinate) | V1 |
| 270 | App-vs-web feature parity (App Store description vs web pricing) | V2 |
| 271 | Deep-link well-knowns (apple-app-site-association + assetlinks.json + Branch.io) | V3 |
| 272 | Mobile-only friction (forms / nav / tap targets) | V4 |
| 273 | Mobile site speed (separate from desktop CrUX) | V5 |
| 274 | Progressive Web App posture (manifest + service worker + install prompts) | V6 |
| 275 | In-app browser handling (Insta / TikTok in-app) | V7 |
| 276 | AI-content disclosure policy (page existence) | O8 |
| 277 | AI policy / model cards (for AI/ML companies) | O10 |
| 278 | AI-feature marketing posture (ChatGPT GPT Store + Copilot + Perplexity Spaces detail) | O7 |
| 279 | Branded-search query coverage / branded-keyword defense | A23 |
| 280 | Domain portfolio & defensive-domain strategy | A24 |

## Tier 6: Long-tail / specialized / overlap-heavy — ranks 278-313 (REBUILT)

**Renumbering note:** All 9 W-section meta-frames (W1-W9) promoted UP into Tier 1/2 (ranks 1-5 + 31, 38, 44, 52). Tier 6 slots reduced by 9. Items below shift down by ~3 ranks vs original numbering. Numbers preserved as relative ordering.

| # | Lens | Catalog ref |
|---|---|---|
| 281 | Brand-maturity-adjusted scoring (Dominant / Established / Challenger tier) — meta-frame | (meta) |
| 291 | Reverse-IP personalization evidence (probe from cloud IPs) | J10 |
| 292 | Featured snippet / People Also Ask coverage | A26 |
| 293 | SERP feature ownership (image pack / video / knowledge panel) | A27 |
| 294 | End-of-year "Wrapped"-style personalized recap campaigns | A28 |
| 295 | Cart / abandoned-cart UX (e-commerce) | G16 |
| 296 | Concierge setup / white-glove onboarding (/enterprise-setup CTA) | H9 |
| 297 | In-product upsell visibility (signup observation) | H8 |
| 298 | "Mistake" / "oops" email marketing pattern | I12 |
| 299 | Trial-expiry sequence quality (fake-signup observation) | I13 |
| 300 | Index/hub page architecture for comparison content (overlap G6 / M3) | G6 |
| 301 | Importer / migration tool as marketing asset (overlap H2) | F7 |
| 302 | Curation / resource library | F8 |
| 303 | AI policy / model cards (overlap with O10) | O10 |
| 304 | Side projects as marketing (separate sub-product) | F1 |
| 305 | Chrome extensions (Web Store search by company) | F1 |
| 306 | Scarcity authenticity (multi-session probe to detect fake "only 3 left") | P1 |
| 307 | Authority signals density (certifications + awards + named experts) | P1 |
| 308 | Form tooling fingerprint (Typeform / Tally / HubSpot Forms) | L21 |
| 309 | Booking tooling fingerprint (Calendly / SavvyCal / Cal.com) | L22 |
| 310 | Email/SMS deliverability tooling (Postmark / SendGrid / Klaviyo signatures) | L23 |
| 311 | Personalization tooling fingerprint (Mutiny / Intellimize / Hyperise) | L20 |
| 312 | A/B test tooling fingerprint (visible client SDK) | L19 |
| 313 | Conversion tracking (GA4 / Adobe / Plausible / Fathom — alternative analytics) | L14 |
| 314 | Win-loss analysis surfacing (Klue / public win-loss reports) | M8 |
| 315 | Competitive intelligence tooling (Klue / Crayon / Kompyte fingerprints) | M7 |
| 316 | Multi-channel support availability (chat / email / phone / in-app coverage map) | T6 |
| 317 | Self-service success-rate proxy (search bar prominence in docs) | T7 |
| 318 | Support response-time SLA disclosure | T5 |
| 319 | Brand-consistency monitoring tooling (Frontify / Brandfolder / Bynder DAM) | S9 |
| 320 | Figma Community presence (figma.com/@org library file count) | S3 |
| 321 | Sponsorship visibility (logo on conference sponsor pages, podcast network sponsors) | E22 |
| 322 | Engagement pods / coordinated-amplification (mostly invisible) | E17 |
| 323 | Comment marketing (low signal) | E18 |
| 324 | Quora marketing (declining 2026) | E19 |
| 325 | "Best-of" listicle inclusion if not yet covered above | C6 |

---

## Vertical Bundles — ranked when their vertical fires

Each bundle's rank is its value **conditional on the prospect being in that vertical**. Bundle activation is binary (vertical detected → all bundle lenses fire).

| Rank-when-fires | Bundle | Trigger signal |
|---|---|---|
| 1 | Healthcare | HIPAA disclaimer / .hospital / EHR fingerprint / NPI presence |
| 2 | Pharma / biotech / medical device | FDA approval letter / ISI / HCP-vs-patient site split |
| 3 | Government / B2G / Defense | .gov / .mil / GSA Schedule / SAM.gov registration |
| 4 | Fintech / banking / mortgage / insurance | NMLS-ID / FINRA / SEC / state-license footprint |
| 5 | Legal services | Attorney advertising disclaimer / state-bar admission |
| 6 | E-commerce (DTC + retail + marketplace) | Shopify fingerprint / Add-to-Cart / Product schema |
| 7 | Crypto / Web3 | Wallet connect / token contract / OFAC ToS |
| 8 | AI / ML companies (selling AI tools) | Model cards / evals / AI-positioning homepage |
| 9 | Marketplaces (two-sided) | Supply + demand pages / take rate visible |
| 10 | Local services / multi-location | Multiple GBP / NAP across locations / service-area pages |
| 11 | Edtech | FERPA / COPPA / accreditation badges |
| 12 | Manufacturing / industrial / construction | Spec compliance badges / BIM library / RFQ form |
| 13 | Travel-deep (hotels / OTAs / airlines) | OTA listings / GDS code / loyalty program |
| 14 | Adult / regulated content | Age-verification UX / 18 USC 2257 / high-risk processor |
| 15 | Cannabis | State-by-state availability / age-gate / METRC |
| 16 | Real estate | IDX / MLS / agent profiles / neighborhood pages |
| 17 | Restaurants / hospitality | Menu schema / OpenTable / DoorDash listing |
| 18 | Nonprofits | Candid Seal / 990 / donation funnel |
| 19 | Creator economy / personal brand | Course platform / paid newsletter / sponsorship deck |
| 20 | Gaming / esports | Steam page / Discord Partner / Twitch presence |
| 21 | MLM / direct sales | Distributor recruiting page / income disclosure |
| 22 | Religious / faith-based | Tithe.ly / Pushpay / livestream / multi-campus |
| 23 | Subscription boxes / DTC overlay | Subscription cadence / Cratejoy listing |
| 24 | Service businesses (HVAC/plumbing/cleaning) | Angi/Thumbtack listing / 24/7 emergency CTA |
| 25 | Membership orgs / associations | Chapter map / certification programs / dues page |

---

## Geo-Conditional Bundles (new — extracted 2026-04-22)

These bundles fire **only when the prospect has presence in that geography**, detected via signals: hreflang tag, ccTLD (.co.uk, .de, .fr, .com.br, .cn, .ch, .co.jp, .kr, .sg, .ae), currency selector (GBP, EUR, BRL, CNY, CHF, JPY, KRW, SGD, AED), local CDN/DNS hints, or privacy policy enumeration of the jurisdiction.

Each bundle contains the mandatory regulatory lenses for operating in that geography. Missing items are high-severity findings (regulatory-risk category).

| Rank when fires | Geo bundle | Trigger signal | Lens count |
|---|---|---|---|
| 1 | **EU / UK regulatory** (GDPR + UK GDPR + Consent Mode v2 quality + DPF + ICO registration + EAA/WCAG + AI Act Article 50) | hreflang=de/fr/es/it/nl, .eu/.uk/.de/.fr/.es TLD, GBP/EUR currency, EU CDN, GDPR cookie banner | 7 |
| 2 | **Canada-Quebec Law 25** (French notice + Personne responsable + automated-decision opt-out + privacy-by-default) | .ca TLD, French hreflang (fr-CA), CAD currency, PIPEDA mention | 4 |
| 3 | **Brazil LGPD** (Encarregado name + ANPD complaint pointer + Portuguese privacy notice + .com.br audit) | .com.br TLD, pt-BR hreflang, BRL currency, Portuguese content | 3 |
| 4 | **South Africa POPIA** (Information Officer registered + PAIA manual link in footer) | .za TLD, ZAR currency, SA business address | 2 |
| 5 | **China PIPL** (Cross-border transfer mechanism named + separate consent for sensitive data + ICP license in footer + local representative) | .cn TLD, zh-CN hreflang, CNY currency, ICP 备案 license | 4 |
| 6 | **Switzerland nFADP** (Swiss representative named + "revFADP" / "nFADP" reference) | .ch TLD, CHF currency, German/French/Italian hreflang | 2 |
| 7 | **Japan APPI** (个人情报保护方针 header + designated representative + cross-border opt-out + CPO disclosure) | .jp/.co.jp TLD, ja hreflang, JPY currency, Japanese content | 4 |
| 8 | **South Korea PIPA** (separate consent 필수/선택 + CPO mandatory disclosure + sensitive-data consent) | .kr TLD, ko hreflang, KRW currency, Korean content | 3 |
| 9 | **SEA privacy** (Singapore PDPA + Thailand PDPA + Vietnam PDPD + Philippines DPA — DPO disclosure + DNC compliance + consent standards) | .sg/.th/.vn/.ph TLD, SGD/THB/VND/PHP currency, local language | 4 |
| 10 | **MEA privacy** (UAE PDPL + Saudi PDPL + Israel PPL) | .ae/.sa/.il TLD, AED/SAR/ILS currency | 3 |

**Additional considered but excluded from geo bundles** (not mandatory regulatory; already covered by core lenses):

- Australia Privacy Act 2026 reforms — covered by statutory-tort signals in core lens U7
- Argentina / Colombia privacy — auditable but typically lower signal; fold into "LATAM posture flag"

**Operational note:** The EU/UK bundle is intentionally the largest because it's the most common non-US geo and has the deepest compliance surface. Fires for ~50% of B2B SaaS prospects. Other bundles fire for 5-20% each.

**Interaction with vertical bundles:** A prospect in healthcare operating in the UK fires the **healthcare vertical bundle** AND the **EU/UK regulatory geo bundle** — both on top of the 160 always-on lenses.

---

## Segment-Conditional Bundles (added 2026-04-22)

These bundles fire **only when prospect's customer-segment is detected** via signals: pricing-page structure (transparent vs gated), homepage CTA language ("Sign up free" vs "Talk to sales"), signup-flow inspection, jobs-page role mix (SDRs vs PLG-PM), enterprise-pricing language (MSA/DPA/SOC 2 mentions).

Same architectural pattern as vertical/geo bundles: detection-gated activation, additive on top of always-on.

### Segment Bundle 1: PLG / self-serve
**Triggers on:** Free tier visible + in-app upgrade prompts in signup flow + no "contact sales" gate on pricing + product-tour video on homepage

- Resolution channel parity (chat/phone/email/self-serve KB)
- Community-support ratio (forum / Discord / Discourse vs ticket-only)
- Onboarding CRO depth (beyond #23 always-on — empty states, progress motivation, multi-channel coordination)
- Paywall sophistication depth (beyond #78 always-on — feature gates vs usage limits vs trial expiration vs time-based detail)
- PLG distribution signals depth ("powered by" + viral loops at sub-lens detail)

### Segment Bundle 2: Sales-led B2B
**Triggers on:** Form-gated demo + SDR/BDR signaling on LinkedIn + "Talk to sales" homepage CTA + enterprise-tier-only pricing

- Sales engagement infrastructure (Outreach / Salesloft / Apollo / Instantly / Lemlist / Snov fingerprints)
- Conversation intelligence presence (Gong / Chorus / Wingman / Fathom on customer-facing pages)
- AI SDR agent in own outbound (Artisan / 11x / Regie / Relevance fingerprints in demo-response)
- MQL-handoff transparency (jobs / careers MOps role descriptions, marketing-to-sales handoff visible)
- Reverse-IP personalization evidence (probe from cloud IPs in different ASNs for differential hero copy)
- BDR/SDR team-size signaling (LinkedIn employee filter)

### Segment Bundle 3: Enterprise B2B
**Triggers on:** SOC 2 / ISO 27001 badge + "contact sales" pricing + MSA/DPA mentions + Fortune-500-style logo wall + investor-relations page

- Clean-room posture (LiveRamp / AWS Clean Rooms / Snowflake / Habu / InfoSum — case-study + careers signals)
- CDP / reverse-ETL fingerprint (Segment / RudderStack / Hightouch / Census)
- Customer journey orchestration (Adobe AJO / Braze Canvas / Iterable Workflow Studio fingerprints)
- Trust-center depth (sub-processor list depth beyond always-on, security whitepaper, SOC 2 Type II vs SOC 3 distinction)
- Internal-comms-as-external-signal (Glassdoor / Comparably review velocity + response rate)
- Account-tier landing pages (depth beyond Verticalization #18 — /enterprise/<industry> sub-pages)

### Segment Bundle 4: Developer tools
**Triggers on:** API docs / SDK / developer portal / GitHub org with public repos / "for developers" homepage CTA

- DevRel team signaling (jobs page DevRel roles + technical blog cadence)
- Postman API Network / RapidAPI listing (followers + fork count)
- AI-coding-tool integrations (Cursor / Cline / Windsurf rules; .mdc files; awesome-cursor / Cursor Directory presence)
- HN submission depth (beyond Show HN — repeat-domain front-page signal)
- OSS community depth beyond basics (Discussions activity, contributor diversity, bus factor)
- IDE marketplace presence (VS Code, Open VSX, JetBrains, Raycast)

### Segment Bundle 5: Mature-brand / late-stage
**Triggers on:** Investor relations page + press kit + large team size (LinkedIn 500+ employees) + category-leader brand search volume + analyst-coverage citations

- Public Storybook presence (storybook./design./ui. probe + index.json manifest)
- Component count + last-publish (from Storybook manifest or Chromatic public library)
- Brand portal accessibility (Frontify / Brandfolder / Bynder / brand. presence)
- Logo-version sprawl (distinct SVG hashes across surfaces)
- Color drift (hex distance: stated brand color vs actual CSS custom properties)
- Typeface license posture (self-hosted vs Adobe Fonts / Typekit / Google Fonts)
- Brand-consistency monitoring tooling (DAM with publishing automation)

### Operational impact

- **PLG bundle**: ~5 lenses, fires for ~30% of B2B SaaS (PLG products)
- **Sales-led B2B bundle**: ~6 lenses, fires for ~50% of B2B SaaS (sales-led)
- **Enterprise B2B bundle**: ~6 lenses, fires for ~25% of B2B SaaS (enterprise prospects)
- **Developer-tools bundle**: ~6 lenses, fires for ~15% of B2B SaaS (dev tools)
- **Mature-brand bundle**: ~7 lenses, fires for ~10% of B2B SaaS (Tier-1 enterprise / public co)
- **Total segment-bundle lens count**: ~30 conditional lenses
- **Typical audit firing**: 1-2 segment bundles → 5-12 additional lenses

### Interaction with vertical + geo bundles

A healthcare prospect operating in the UK with PLG motion fires:
- 167 always-on lenses
- Healthcare vertical bundle (~9 lenses)
- EU/UK regulatory geo bundle (~7 lenses)
- PLG segment bundle (~5 lenses)
= ~188 lenses fired for that audit

All bundle activations are independent and additive.

---

## Cutoff guidance (post-reshuffle + boundary rerank + segment bundles)

For setting an audit-scope cutoff, the natural breakpoints after option-C reshuffle (extend-surgically + segment bundles):

- **Cutoff at rank 25 (Tier 1)**: Floor for "comprehensive" claim — top 5 meta-frames + 20 must-have tactical lenses
- **Cutoff at rank 65 (Tier 1 + 2)**: Strong "comprehensive" — adds remaining meta-frames + 6 high-stakes 2026-enforcement regulatory lenses
- **Cutoff at rank 135 (Tier 1 + 2 + 3)**: Best-in-class but missing some genuinely-universal items at 136-167
- **Cutoff at rank 167 (LOCKED RECOMMENDATION)**: Captures all items I judge genuinely universal after item-by-item boundary review. Surgical promotions: 7 items (help center maturity, AI-chat handoff, tag-manager hygiene, public roadmap, form progressive-profiling, channel partner program, "best-of" listicle) lifted from below cutoff because applicability is broad (not segment-specific)
- **Cutoff above 167**: Items below 167 are correctly segment-specific (PLG / sales-led / enterprise / dev-tools / mature-brand). Adding them as always-on would inflate every audit including for prospects who don't fit the segment. Better routed via segment bundles.

## LOCKED FINAL RECOMMENDATION (option C)

| Tier | Lens count | Fires when |
|---|---|---|
| **Always-on** | **167 lenses** | Every audit |
| **Vertical bundles** (25 bundles) | ~200 conditional | 1-3 bundles fire per audit based on vertical detection |
| **Geo-conditional bundles** (10 bundles) | ~36 conditional | 0-2 bundles fire per audit based on geography detection |
| **Segment-conditional bundles** (5 bundles) | ~30 conditional | 1-2 bundles fire per audit based on segment detection |
| **Meta-frames at Phase 0** | (already in always-on at ranks 1-5 + 31/38/44/52) | Every audit (foundational) |
| **TOTAL CAPACITY** | **~433 lens slots** | |
| **Typical audit firing** | **~185-195 lenses** | 167 always-on + ~18-28 bundle hits |

**Why 167 not 135 or 200:**
- Item-by-item review of 161-200 zone identified 7 items that are genuinely universal (not segment-specific) that I'd mis-categorized
- 25 items at 168-200 are correctly cut as below-cutoff or moved to segment bundles
- Going to 200+ would bloat always-on with segment-specific items that don't apply to all prospects (enterprise design-system lenses firing for SMB = noise)
- The cleanest architecture: extend always-on **only** for items with broad applicability; route segment-specific to segment bundles

**Why segment bundles are the right architecture for the rest:**
- Same activation pattern as vertical + geo bundles (all conditional based on detection signals)
- Detection is straightforward: pricing structure + CTA language + signup flow reveals PLG / sales-led / enterprise immediately
- Segment-specific depth gets proper treatment without bloating non-applicable prospect audits
- Bundle activation is independent and additive

**Change log (2026-04-22, option C final):**
- Meta-frames (W1-W9) promoted to Tier 1/2 (ranks 1-5 + 31/38/44/52)
- 6 regulatory lenses promoted from Tier 4 → Tier 2 (Consent Mode v2, EU AI Act 50, EAA/WCAG 2.2, Multi-state US privacy, Click-to-Cancel FTC, Sub-processor page, EU-US DPF)
- 8 boundary-zone items promoted within Tier 3 (deliverability, advocacy, brand salience, trust-mark stack, schema stacking, PDF gating, effort asymmetry, vendor sprawl)
- 7 boundary-zone items promoted to always-on (help center maturity, AI-chat handoff, tag-manager hygiene, public roadmap, form progressive-profiling, channel partner program, "best-of" listicle)
- 8 overlap items folded into existing higher-rank lenses (KB depth, chat widget, account-tier landing, hreflang matrix, local case studies, RTL, PR depth, leadership cadence)
- 14+ geo-regulatory items extracted to 10 Geo-Conditional Bundles
- ~30 segment-specific items extracted to 5 Segment-Conditional Bundles
- **Cutoff at #167 always-on + 25 vertical + 10 geo + 5 segment bundles**
