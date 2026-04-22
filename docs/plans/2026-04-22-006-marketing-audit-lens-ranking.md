# Marketing Audit Lens Ranking

**Date:** 2026-04-22
**Companion to:** `2026-04-22-005-marketing-audit-lens-catalog.md`
**Purpose:** Forced ranking of all ~325 core lenses by genuine value/usefulness — buyer-decision-shaping power, regulatory weight, diagnostic depth, signal quality, and engagement-conversion potential.

**Methodology:** ranked at the lens's value **when it applies**, not weighted by frequency of applicability. Conditional/vertical lenses noted as such. Effort, code complexity, cost, and report-density tradeoffs are NOT factored — those are downstream cutoff decisions.

**Tier breakpoints (post-boundary rerank):**
- Ranks 1-25: Audit floor — must-have for "comprehensive" claim
- Ranks 26-65: Foundational (Tier 2) — drops here would feel like obvious gaps
- Ranks 66-135: High value, slightly situational (Tier 3)
- Ranks 136-200: Genuinely useful, narrower (Tier 4) — **cutoff line at rank 160 (recommended)**
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

## Tier 3: High value, slightly situational — ranks 66-135 (REBUILT)

**Renumbered with absolute ordering after option-2 reshuffle + boundary rerank.** Old Tier 2 items 50-60 absorbed at top. 8 boundary promotions inline (marked **↑**). 70 items.

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
| 88 | International SEO (hreflang/canonical/locale URL + RTL + local case studies) | A4 |
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
| 105 | API docs tooling (ReadMe / Mintlify / Stoplight / Redoc / Scalar) | N3 |
| 106 | Hacker News submission / Show HN history | N6, N7 |
| 107 | Retargeting pixel coverage across site | B5 |
| 108 | Review-request automation (feeds D1 review sites) | I7 |
| 109 | Paid platform breadth (Google/Meta/LinkedIn/TikTok/Reddit/Quora) | B2 |
| 110 | **Vendor sprawl per category (2+ analytics / 2+ CDPs / 2+ chats — MarTech debt)** [↑ from #175] | L16 |
| 111 | SDK language coverage (when API product) | N2 |
| 112 | NPS survey program (Delighted / Wootric / SurveyMonkey) | I6 |
| 113 | AI-feature marketing (ChatGPT GPT Store + Copilot agents + Perplexity Spaces + MCP) | H5, O7 |
| 114 | Product usage digest emails (daily / weekly / monthly) | I3 |
| 115 | Marketing Jiu-Jitsu / counter-positioning | M2 |
| 116 | Parasite SEO / external-platform publishing (Medium / LinkedIn / Substack) | A12 |
| 117 | Win-back / trial reactivation sequence | I9 |
| 118 | Press / media kit availability + completeness score | J3 |
| 119 | Developer hackathon presence + sponsor-of-record | N4 |
| 120 | Searchable vs shareable content balance | A9 |
| 121 | Competitive ad research (overlap with B1 from competitor angle) | M1 |
| 122 | Viral loops / PLG distribution signals | H6 |
| 123 | "Powered by X" badge detection | H7 |
| 124 | Creator / ambassador program (/creators, /ambassadors) | E7 |
| 125 | Milestone / achievement emails | I4 |
| 126 | Changelog / public release cadence + author attribution | H4 |
| 127 | EEAT signals (overlaps K3 thought leadership) | A5 |
| 128 | Capture surface scan (popup / form / SMS / lead-magnet / content-upgrade) | I1 |
| 129 | Lifecycle stack maturity (ESP/SMS/loyalty/reviews/referral/subscription) | I10 |
| 130 | Marketing psychology cross-cut (Cialdini-6 density + scarcity authenticity) | P1 |
| 131 | Microsite / subdomain-sprawl audit | (Long-tail) |
| 132 | Contract buyout / migration offers (overlap H2) | M4 |
| 133 | Organic social footprint | E1 |
| 134 | Customer-Cloud / partner-overlap signaling (Crossbeam / Reveal) | J17 |
| 135 | Brand esteem / sentiment delta (review-platform sentiment polarity) | K10 |

## Tier 4: Genuinely useful, narrower — ranks 136-200 (REBUILT)

**Items 136-160 are above the recommended cutoff line.** 14+ geo-regulatory items extracted to Geo-Conditional Bundles (see new section below). 6 items already promoted to Tier 2 are removed from this tier. 8 items promoted up to Tier 3 are removed. Numbering is now absolute.

| # | Lens | Catalog ref |
|---|---|---|
| 136 | Refund / guarantee / returns policy visibility + specificity | G14 |
| 137 | Offer construction (anchor pricing + bonuses + urgency + risk-reversal) | G15 |
| 138 | Employer brand / careers-page-as-marketing (Glassdoor + Stripe-Press style + DEI) | K17 |
| 139 | Investor relations page (SEC filings + ESG report + analyst coverage) | K18 |
| 140 | Referral / share mechanics (codes + share-with-team + two-sided) | I14 |
| 141 | Brand differentiation (BAV vitality/stature) | K11 |
| 142 | Brand personality consistency / voice drift across surfaces | K12 |
| 143 | AI-generated copy density in own copy ("AI tells" — em-dash + lexical scan) | A22, K13 |
| 144 | Self-reported attribution field in demo/trial forms ("How did you hear about us?") | L13 |
| 145 | MMM infrastructure (Meridian / Robyn / Recast — jobs + vendor case studies) | L12 |
| 146 | AI citation tracking tooling presence (Profound / Peec / Otterly / AthenaHQ) | L11 |
| 147 | Schema @graph composability (linked types via shared @id) | A19 |
| 148 | WebSite SearchAction (sitelinks search box) schema | A19 |
| 149 | Voice-search / natural-question formatting | A18 |
| 150 | Bing Webmaster + IndexNow posture (Copilot citation prerequisite) | A13 |
| 151 | Brave Search visibility (Claude citation prerequisite) | A13 |
| 152 | Agent-card / MCP discoverability (/.well-known/agent-card.json + MCP server) | O5 |
| 153 | Product feed for AI commerce (UCP manifest + Product JSON-LD with gtin) | O6 |
| 154 | TCPA / SMS-consent compliance | U16 |
| 155 | CAN-SPAM / CASL compliance | U17, U18 |
| 156 | FTC Endorsement Guides + #ad disclosure ratio (influencer audit) | U21, B20 |
| 157 | FTC junk-fee rule disclosure | U15 |
| 158 | FTC fake-reviews crackdown compliance (no incentivized hidden reviews) | U21 |
| 159 | Comparative-advertising claim substantiation (Lanham Act §43(a)) | U21 |
| 160 | Stale-trust-page red flag (Norton/McAfee/TRUSTe-original = decommissioned) | U28 |

---

### ✂️ CUTOFF LINE — locked at rank 160 (recommended scope)

Everything above this line is **always-on**. Items below are cut from default scope; they're real but yield diminishing signal-to-noise. Re-add individually if a specific use-case requires it.

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

## Cutoff guidance (post-reshuffle + boundary rerank)

For setting an audit-scope cutoff, the natural breakpoints with the option-2 reshuffle + boundary rerank applied:

- **Cutoff at rank 25 (Tier 1)**: Floor for "comprehensive" claim — top 5 meta-frames + 20 must-have tactical lenses. Estimated implementation: ~55 rubrics, 9 sections.
- **Cutoff at rank 65 (Tier 1 + 2)**: Strong "comprehensive" — adds remaining meta-frames + 6 high-stakes 2026-enforcement regulatory lenses + foundational tactical depth. Estimated implementation: ~140 rubrics, 12-14 sections.
- **Cutoff at rank 135 (Tier 1 + 2 + 3)**: Best-in-class — covers decision-shaping content. Estimated implementation: ~225 rubrics, 14-16 sections.
- **Cutoff at rank 160 (RECOMMENDED)**: Best-in-class + boundary-rerank-safe — catches the high-value items at 136-160 (AI-search depth cluster, remaining CX signals, FTC compliance detail, Storybook/design-system, vendor sprawl). Hedges against misrank at the boundary. Estimated implementation: ~265 rubrics, 14-16 sections.
- **Cutoff at rank 200 (Tier 1-4 full)**: Adds regional-compliance depth (now handled via geo-conditional bundles instead) + ad-platform sophistication + design-system breadth + adjacent-discipline depth. Mostly diminishing returns since geo-conditional bundles already pick up the regulatory delta. Estimated implementation: ~310 rubrics, 18-20 sections.
- **Cutoff at all 325 + vertical bundles + geo bundles**: Theoretical maximum. Over-engineered for $1K positioning.

**Locked recommendation:**

- **160 always-on lenses** (cutoff at rank 160)
- **25 vertical bundles** conditionally activated (8-12 lenses each per bundle; 1-3 fire per audit based on vertical detection)
- **10 geo-conditional bundles** (2-7 lenses each; 0-2 fire per audit based on geography detection)
- Top 5 meta-frames at Phase 0 by virtue of being ranked 1-5 — no separate Phase-0 sidecar needed
- Total scoped: 160 always-on + ~200 conditional vertical lenses + ~36 conditional geo lenses = ~396 lens capacity, of which a typical audit fires ~170-180

**Why 160 not 135:**
- Boundary rerank identified 8 genuinely under-ranked items that sat just below #135 — their exclusion would have been a real gap
- Asymmetric risk: a senior B2B buyer who notices "they didn't audit our SOC 2 badge" or "they missed our advocacy program" cracks the report's credibility. Cost of one wrong cut >> cost of ~25 extra rubrics.
- Geo bundles pulled ~14 regulatory lenses out of the linear count, freeing capacity for higher-value items to slot into Tier 3-4.

**Why not 200:**
- Items 161-200 are mostly narrow regulatory depth (APAC privacy, specialized trust certs) that geo bundles now cover, or specialized ad-platform sophistication tiers that fire for <30% of prospects.
- Adding them to always-on count inflates runtime and rubric count without proportional signal lift for typical B2B SaaS prospects.
- Better as "depth pack" add-on tiers or vertical-conditional activations.

**Change log (2026-04-22):**
- Meta-frames (W1-W9) promoted to Tier 1/2 (ranks 1-5 + 31, 38, 44, 52)
- 6 regulatory lenses promoted from Tier 4 → Tier 2 (Consent Mode v2, EU AI Act 50, EAA/WCAG 2.2, Multi-state US privacy, Click-to-Cancel FTC, Sub-processor page, EU-US DPF)
- 8 boundary-zone items promoted within Tier 3 (deliverability, advocacy, brand salience, trust-mark stack, schema stacking, PDF gating, effort asymmetry, vendor sprawl)
- 14+ geo-regulatory items extracted from linear ranking into 10 Geo-Conditional Bundles
- Cutoff lifted from #135 to **#160**
