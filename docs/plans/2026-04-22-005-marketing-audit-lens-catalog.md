# Marketing Audit Lens Catalog

**Date:** 2026-04-22
**Purpose:** Comprehensive reference of every auditable marketing-audit lens identified through 8 parallel research passes (4 against the marketing-skills repo, 4 against established frameworks + emerging dimensions + verticals + adjacent disciplines + global compliance + channel sophistication + niche industries).

**Scope rule:** every lens here must be auditable from **public signals only** — no CRM access, no ESP access, no product-internal access. Where a lens partially needs internal access, it is flagged.

**Status:** consolidated inventory; not yet ranked or scoped to the audit pipeline. See companion ranking document for cut-line decisions.

---

## Methodology

Lenses surfaced from:
1. The marketing-skills repo (38 SKILL.md files + ~30 reference taxonomies + tools/integrations directory)
2. Established marketing audit frameworks (HubSpot Grader, SEMrush, Ahrefs, Moz, Conversion Factory, Demand Curve, NoGood, Wpromote, Tinuiti, Single Grain, Kotler, McKinsey, Bain, AARRR, Reforge, Forrester, Gartner, Aaker, Keller CBBE, BAV)
3. Emerging 2025-2026 marketing dimensions (LLMO/GEO/AEO, agent-readiness, MCP, AI-commerce, signal-based selling, dark social, retail media networks, clean rooms, MMM revival)
4. Adjacent disciplines (CX, brand audit, content audit, design system, DAM, MarOps, ABM, demand gen, PMM, influencer, PR, internal comms, CSAT, T&S, localization, conversion psychology, voice/tone, mobile UX, conversation intelligence, journey orchestration)
5. Global + industry compliance (US state, EU, UK, APAC, LATAM, MEA, plus HIPAA/FDA/FINRA/SEC/COPPA/FERPA/TCPA/CAN-SPAM/CASL/AI Act/EAA/DSA/DMA/DORA/MiCA/NIS2/state privacy laws/ad-disclosure laws)
6. Channel sophistication tiers (TikTok, Amazon, ASA, RMNs, CTV, audio, OOH, LinkedIn paid, PMax, Reddit, Pinterest, Snap, X, Bluesky)
7. Vertical-specific dimensions (28 verticals: e-commerce, healthcare, fintech, edtech, manufacturing, marketplaces, local services, real estate, restaurants, legal, nonprofits, creator economy, gaming/esports, dating, travel-deep, automotive, beauty/fashion/CPG DTC, subscription boxes, telecom, insurance, crypto/web3, AI/ML companies, OSS, hosting/infra, media/publishing, government/B2G, defense, pharma, industrial, agriculture, cannabis, adult/regulated, religious, wedding/events, pets, MLM, service businesses, membership orgs)
8. Niche emerging surfaces (ChatGPT GPT Store, ChatGPT Apps, Claude Skills, Copilot extensions, Perplexity Spaces, IDE extension marketplaces, Figma plugins, Zapier templates, browser extensions, AWS/Azure/GCP marketplace, B2B SaaS app marketplaces)

**Deduplication:** lenses are listed once even when surfaced by multiple agents. Sub-lenses split from a parent lens are nested under the parent.

---

## Top-level structure

The catalog is organized into 23 super-sections plus vertical bundles plus meta-diagnostic frames:

| Code | Super-section | Lens count |
|---|---|---|
| A | Discoverability & Organic Traffic | 28 |
| B | Paid Media & Ad Creative | 22 |
| C | Earned Media & PR | 11 |
| D | Directories, Marketplaces & Listings | 14 |
| E | Social, Community & Owned Audience | 22 |
| F | Free Tools & Lead Magnets | 8 |
| G | Conversion Architecture | 16 |
| H | Activation & Product-Led | 10 |
| I | Lifecycle & Retention | 14 |
| J | Sales/GTM/Enablement | 17 |
| K | Brand & Authority | 18 |
| L | MarTech, Measurement & Analytics | 23 |
| M | Competitive | 8 |
| N | Developer & DevRel | 12 |
| O | AI Surface & Agent-Readiness | 12 |
| P | Persuasion & Conversion Psychology | 7 |
| Q | Customer Experience (CX) | 9 |
| R | Trust & Safety / Transparency | 6 |
| S | Design System & Brand Governance | 9 |
| T | Customer Support Quality | 7 |
| U | Compliance & Regulatory (Global + Industry) | 35 |
| V | Mobile & App Experience | 8 |
| W | Meta-Diagnostic Frames | 9 |
| **TOTAL CORE** | | **~325 lenses** |
| Vertical bundles | 25 bundles × avg ~8 lenses each | ~200 conditional |
| Geo-conditional bundles (added 2026-04-22) | 10 bundles × avg 3-4 lenses each | ~36 conditional |
| **GRAND TOTAL** | | **~561 lenses** |

(Of which ~236 fire only when prospect's vertical or geography is detected. Typical audit fires ~170-180 lenses based on detection signals.)

---

## A. Discoverability & Organic Traffic (28)

### A1. Technical SEO health (split into sub-lenses)
- A1a. Crawlability (robots.txt syntax, crawl budget bloat)
- A1b. Indexation status + index bloat
- A1c. **Core Web Vitals percentile** (LCP, INP, CLS — CrUX data)
- A1d. **HTTPS/SSL + mixed content + security headers (CSP, HSTS, Permissions-Policy)**
- A1e. Mobile-friendliness
- A1f. URL structure + URL hygiene
- A1g. **4xx/5xx errors + redirect chains + orphan pages** (Ahrefs top errors)
- A1h. **Canonicalization + duplicate content + pagination correctness**
- A1i. **XML sitemap health vs robots.txt conflicts** (4xx in sitemap, freshness)
- A1j. Favicon + 404-page UX + cookie banner UX

### A2. On-page SEO
- A2a. Title tags, meta descriptions, H1 structure
- A2b. Content depth + word count vs SERP median
- A2c. Image optimization + alt-text coverage
- A2d. Keyword targeting + intent match

### A3. Internal linking + hub-and-spoke architecture
- A3a. Hub-and-spoke topic-cluster model
- A3b. Anchor-text distribution
- A3c. **Orphan-page ratio** (pages with zero internal inbound)

### A4. International SEO
- A4a. Hreflang implementation
- A4b. **Self-referencing hreflang integrity** (67% of sites broken)
- A4c. Canonical-hreflang-cluster validity (canonical outside cluster invalidates all hreflang)
- A4d. International sitemaps
- A4e. Locale URL structure
- A4f. **Local-case-study parity** (case studies per non-English locale vs English)
- A4g. **RTL rendering quality** (Lighthouse on ar-SA)

### A5. EEAT signals
- A5a. Author entity composition + bio depth
- A5b. About-page depth
- A5c. Editorial standards page
- A5d. Citation density in content

### A6. Programmatic SEO posture
- A6a. Templated-content pattern detection at scale
- A6b. Unique-value-per-page check
- A6c. Index/no-index discipline on programmatic pages

### A7. Site architecture / Information Architecture
- A7a. Navigation depth (3-click rule conformance)
- A7b. URL taxonomy + breadcrumb-URL alignment
- A7c. Hub-and-spoke vs flat
- A7d. Sitelinks search box (WebSite SearchAction schema)

### A8. Content pillars / topic clusters
- A8a. Pillar identification + cluster coverage
- A8b. Content-pillar internal-link density
- A8c. **Format diversity index** per pillar (long-form / interactive / video / template)

### A9. Searchable vs shareable content balance

### A10. Buyer-stage keyword coverage (Awareness / Consideration / Decision / Implementation)

### A11. Content refresh discipline
- A11a. Median age of top-50 organic landing pages
- A11b. **Content half-life** (sitemap lastmod + Wayback decay curve)
- A11c. "Last updated" prominence

### A12. Parasite SEO / external-platform publishing (Medium, LinkedIn, Substack)

### A13. AI search citation patterns
- A13a. Actual AIO presence (ChatGPT/Claude/Perplexity/Google AIO citation rate for prospect's key queries)
- A13b. **Schema stacking for AI citation** (3-4 complementary @types per page)
- A13c. **PDF gating posture for Perplexity** (form-walled PDFs lose citation)
- A13d. **Bing Webmaster + IndexNow posture** (Copilot citation prerequisite)
- A13e. **Brave Search visibility** (Claude citation prerequisite)
- A13f. **AI citation tracking tooling presence** (Profound, Peec, Otterly, AthenaHQ)

### A14. AI bot access (split)
- A14a. Training-crawler access (GPTBot, ClaudeBot, CCBot, Google-Extended)
- A14b. Answer-engine-crawler access (OAI-SearchBot, ChatGPT-User, PerplexityBot, Claude-SearchBot, AppleBot-Extended)
- A14c. Differentiated policy correctness (blanket blocks usually wrong)

### A15. llms.txt / machine-readable files
- A15a. llms.txt presence (low-weight; correlation with citations is weak)
- A15b. llms-full.txt presence
- A15c. Markdown twins (.md endpoints, ?format=md, /raw/)

### A16. Content extractability for LLMs
- A16a. Semantic HTML structure (article, section, headings hierarchy)
- A16b. Lists + tables + definition-block usage
- A16c. Lead-answer format (under-30-word lede before context)

### A17. Glossary / /learn-X-101 long-tail SEO

### A18. **Voice-search / natural-question formatting** (conversational headings)

### A19. Schema.org structured data
- A19a. Schema type coverage (Organization, WebSite, Article, FAQPage, HowTo, Product, BreadcrumbList)
- A19b. **Schema @graph composability** (linked types via shared @id)
- A19c. JSON-LD validation correctness
- A19d. Structured-data depth across page types

### A20. Spam score / toxic backlinks / link profile risk (Moz spam score, Ahrefs DR distribution)

### A21. Backlink profile quality (referring-domains growth + topical relevance, NOT raw DA)

### A22. **AI-generated copy density in own content ("AI tells")** — em-dash frequency, lexical patterns ("delve", "leverage", "robust", "seamless", "in today's landscape")

### A23. Branded-search query coverage / branded-keyword defense

### A24. Domain portfolio & defensive-domain strategy (typo-squat coverage, defensive ccTLDs)

### A25. Wikipedia entry presence + monitoring
- A25a. Wikipedia entry quality (citations, recency)
- A25b. **Monitored-vs-unmonitored** (citation-watch retainer signal)

### A26. Featured snippet / People Also Ask coverage

### A27. SERP feature ownership (image pack, video, knowledge panel)

### A28. **End-of-year "Wrapped"-style personalized recap campaigns** (Spotify Wrapped model)

---

## B. Paid Media & Ad Creative (22)

### B1. Paid creative corpus & strategy (Foreplay / Adyntel)
- B1a. Hook taxonomy
- B1b. Persona / emotional-driver coverage
- B1c. UGC vs produced ratio
- B1d. Landing-page congruence with ad promise
- B1e. Channel-native fit
- B1f. Spend intensity (volume × duration)

### B2. Paid platform breadth (Google, Meta, LinkedIn, TikTok, Reddit, Quora, Pinterest, Snap, X)

### B3. **Ad creative format diversity** (RSA, Meta, LinkedIn, TikTok, Twitter — per-platform native lengths)

### B4. **Copy-platform-length discipline** (distinct copy per platform vs truncated cascades)

### B5. Retargeting pixel coverage across site

### B6. **Pre-targeting / warmup ad strategy** (awareness before direct-response)

### B7. **TikTok paid sophistication**
- B7a. Spark Ads ratio (% spend through creator handles)
- B7b. Symphony / TikTok One marketplace usage
- B7c. GMV Max / Smart+ adoption
- B7d. Video Shopping Ads with catalog feed
- B7e. Live Shopping cadence

### B8. **Amazon DSP / Sponsored ecosystem**
- B8a. AMC (Amazon Marketing Cloud) clean-room usage
- B8b. Sponsored TV (Fire TV / Freevee) presence
- B8c. Brand Store 2.0 layers (traffic widget / Posts / Live)
- B8d. Rufus-readiness (FAQ schema in A+ content)
- B8e. Sponsored Display split (contextual + audience)

### B9. **Apple Search Ads sophistication**
- B9a. Custom Product Pages variants count (1 = beginner; 8-15 = mature)
- B9b. Today Tab presence (invite-managed)
- B9c. 5-campaign canonical structure (Search Match / Discovery / Brand / Competitor / Keyword)

### B10. **Retail Media Networks breadth** (Walmart Connect, Roundel, Kroger Precision, Instacart, Chase Media, Uber Ads, DoorDash, Costco, Lyft Media, Marriott Media, Best Buy, United MileagePlus)
- B10a. RMN count (1 → 6+)
- B10b. On-site SOV per RMN
- B10c. Off-site extensions (Walmart TradeDesk, Roundel display)
- B10d. Closed-loop measurement adoption

### B11. **Connected TV / OTT sophistication**
- B11a. Direct-sold IO vs programmatic guaranteed vs DSP-bought mix
- B11b. Shoppable CTV (Roku Action Ads, Fire TV shoppable, NBCU Must ShopTV)
- B11c. CTV creative count (1 → 6+ sequenced)
- B11d. Co-viewing measurement (iSpot / VideoAmp / ComScore)
- B11e. Premium inventory (Pause Ads, Binge Ads, Marquee)

### B12. **Audio / podcast advertising sophistication**
- B12a. SPAN / AdsWizz / Acast / SiriusXM Media DSP coverage
- B12b. Spotify Video Podcast ads
- B12c. Chapter sponsorships + transcript-targeted DAI
- B12d. Pixel-based incrementality (Podscribe, Magellan, Claritas)
- B12e. Host-read approval cycle latency + script personalization depth

### B13. **OOH / programmatic OOH**
- B13a. pOOH share vs traditional IO (Vistar, Hivestack, Place Exchange, AdQuick)
- B13b. Trigger-based creative (weather, sports, stock price, flight delay)
- B13c. Geo-fenced OOH retargeting

### B14. **LinkedIn paid sophistication**
- B14a. Conversation Ads click-tree depth (3+ branches)
- B14b. Document Ads + Thought Leader Ads (TLA) — boosting employee posts
- B14c. LinkedIn CTV / Wire Program
- B14d. Predictive Audiences + Account IQ usage
- B14e. Revenue Attribution Report (RAR) CRM integration

### B15. **Google Performance Max maturity**
- B15a. Asset group count (1 = beginner; 5+ themed = advanced)
- B15b. Customer-provided audience signals attached
- B15c. Brand exclusion lists + account-level negatives
- B15d. PMax + Search coexistence with negative architecture
- B15e. Final URL expansion + page feed sophistication
- B15f. Demand Gen split-out
- B15g. Search Themes usage

### B16. **Reddit Ads sophistication**
- B16a. Conversation Placements (in-feed-of-comments)
- B16b. Subreddit Targeting precision count
- B16c. AMA Ads usage

### B17. **Pinterest sophistication** (Premiere Spotlight, Idea Ads, Trends-API-driven creative)

### B18. **Snap / X / Bluesky** (AR Lens with try-on, First Story, Vertical Video; Bluesky monetization is sponsored starter packs / labelers only)

### B19. **Newsletter sponsorship economy** (Beehiiv Ads, Sponsy, Paved, Swapstack)

### B20. **Influencer & creator-economy paid**
- B20a. Influencer whitelisting (running ads through creator accounts)
- B20b. Creator-network platform presence (Aspire, Grin, CreatorIQ)
- B20c. **FTC #ad / #sponsored disclosure ratio** on tagged-creator posts
- B20d. B2B influencer / LinkedIn-creator activation (branded-content disclosures)

### B21. **Click-to-Messenger / DM-objective ads** (Meta + Instagram + WhatsApp Business)

### B22. **Cross-platform retargeting + audience-sharing pixel partnerships**

---

## C. Earned Media & PR (11)

### C1. Press coverage
- C1a. Tier distribution (Tier-1 flagship vs Tier-3 syndicated-aggregator)
- C1b. **Newsroom freshness gradient** (median days between last 10 releases)
- C1c. **Journalist quote density** (named outlets in last 12 months)
- C1d. Source-priority + ai_tags from NewsData

### C2. Analyst relations posture (Gartner, Forrester, IDC)
- C2a. Magic Quadrant / Wave / MarketScape positioning
- C2b. Analyst-report citations on site
- C2c. Analyst badge presence

### C3. Awards & "as seen in" badges (G2 badges, Capterra, Gartner, industry awards)

### C4. **Media acquisitions as marketing** (acquired newsletters / podcasts owned)

### C5. **HARO 2.0 / expert-quote programs** (Connectively, Featured.com, Qwoted, SourceBottle, Help A B2B Writer — reply velocity proxy)

### C6. **"Best-of" editorial listicle inclusion** (DR40-70 "best X tools 2026" coverage)

### C7. Documentary / long-form video coverage

### C8. Fundraising PR (leverage of raises as press moments)

### C9. **PR tooling fingerprints** (Cision / Muck Rack / Prowly outbound link patterns)

### C10. **Internal-comms-as-external-signal** (Glassdoor / Comparably review velocity + response rate)

### C11. **Leadership content cadence** (CEO LinkedIn post frequency + comment-reply rate)

---

## D. Directories, Marketplaces & Listings (14)

### D1. Review sites (G2, Capterra, TrustRadius, TrustPilot, GetApp, Software Advice)
- D1a. Listing presence per platform
- D1b. Rating + review count + recency
- D1c. **Review-response hygiene** (developer/brand replies to negative reviews)
- D1d. Grid / Wave / category-leader badge

### D2. Launch directories — comprehensive 17-platform Tier-1 + Tier-2/3 coverage
- D2a. **Coverage breadth** (% of 17 launch platforms actually landed)
- D2b. Launch-week vs later submission timing
- D2c. Tier-1 platforms: Product Hunt, HN Show HN, BetaList, Launching Next, Fazier, Uneed, Microlaunch, OpenHunts, DevHunt, PeerPush, LaunchVault, What Launched Today, Firsto, GetByte, Best of Web, Tiny Launch, PitchWall
- D2d. Tier-2 SaaS: AlternativeTo, SaaSHub, SourceForge, Slashdot, Startup Stash, SideProjectors, F6S, Stackshare, Resource.fyi, Shipybara, Crozdesk
- D2e. Tier-3 AI: TAAFT, Futurepedia, Toolify, Future Tools, AI Tools Neilpatel, Good AI Tools, NewTools.site

### D3. Integration marketplaces — comprehensive coverage
- D3a. Horizontal app stores: Zapier, Make, n8n, Pipedream, Workato
- D3b. SaaS app stores: Salesforce AppExchange, HubSpot Marketplace, Slack App Directory, Microsoft Teams App Store, Atlassian Marketplace, Intercom App Store, Zendesk Marketplace, ServiceNow Store, Shopify App Store, WordPress Plugin Directory, Webflow Marketplace, Wix App Market, Google Workspace Marketplace, Microsoft AppSource
- D3c. **Cloud hyperscaler marketplaces: AWS Marketplace, Azure Marketplace, Google Cloud Marketplace, Oracle Cloud Marketplace** (major B2B distribution moat)
- D3d. IDE marketplaces: VS Code, Open VSX, JetBrains Marketplace, Raycast Store
- D3e. Design marketplaces: Figma Plugins + Widgets + Community files
- D3f. Productivity marketplaces: Notion templates, Coda gallery, Airtable Universe, Obsidian community plugins
- D3g. API networks: Postman API Network, RapidAPI, APILayer
- D3h. Browser extension stores: Chrome Web Store, Firefox Add-ons, Edge Add-ons, Safari, Arc, Brave, Opera

### D4. ASO — App Store + Google Play
- D4a. Title + subtitle + description optimization
- D4b. Screenshot strategy + ordering
- D4c. **Promotional-text slot utilization (Apple 170-char + What's New cadence)**
- D4d. **In-App Events (Apple) + Promotional Content tiles (Play)**
- D4e. **Data-safety / privacy-nutrition-label completeness**
- D4f. Rating count + rating distribution + recency
- D4g. Review-response hygiene
- D4h. Keyword ranking (Sensor Tower / data.ai / AppFigures)
- D4i. Brand-maturity-adjusted scoring (Dominant / Established / Challenger tier)

### D5. Niche directories beyond launch tier (industry-specific catalogs, association directories, government listings)

### D6. **MCP server / AI-agent registry listings** (Glama.ai, LF MCP Registry, APITracker)

### D7. **Stackshare / tech-stack directory presence** (reveals customer fit)

### D8. **AppSumo / lifetime-deal site presence**

### D9. **Crunchbase / Pitchbook / Tracxn profile completeness**

### D10. **Company directories** (Owler, AmbitionBox, Comparably)

### D11. **Open-source registries** (npm, PyPI, RubyGems, Crates.io, Packagist, Maven Central, Homebrew, Docker Hub, Helm Hub) — package-as-marketing for OSS-tier distribution

### D12. **AI-assistant directories** (ChatGPT GPT Store, OpenAI Apps, Microsoft Copilot agents, Perplexity Spaces, Cursor Directory)

### D13. **Industry-specific marketplaces** (depending on vertical: Etsy, Reverb, ThredUp, StockX, Grailed, Poshmark — when applicable)

### D14. **Government procurement listings** (SAM.gov, GSA Schedules, SEWP, state procurement registries)

---

## E. Social, Community & Owned Audience (22)

### E1. Organic social footprint
- E1a. Platform coverage (LinkedIn / X / Instagram / TikTok / YouTube / Facebook / Pinterest / Reddit)
- E1b. Cadence × engagement-rate vs category benchmark
- E1c. Present-or-absent × dormancy

### E2. **Short-form video strategy** (TikTok / Reels / Shorts cadence + posture)

### E3. Founder / exec content posture
- E3a. LinkedIn cadence + post-format diversity
- E3b. X/Twitter activity
- E3c. Substack / personal blog presence
- E3d. Podcast guesting frequency

### E4. **Owned podcast** (separate from advertising)
- E4a. Show launch + cadence
- E4b. Audience tier
- E4c. Network membership

### E5. Podcast guesting at scale
- E5a. CEO podcast-guesting volume (≥6 guest appearances in trailing 12mo via Listen Notes / Podscan / Podchaser)
- E5b. **Guest-graph centrality** (network-position metric)

### E6. Owned community
- E6a. Platform (Slack / Discord / Circle / Skool / Geneva / Heartbeat / Discourse / own forum)
- E6b. Member count + activity tier
- E6c. **Discord sophistication** (Onboarding quest, Forum channels, AutoMod, Stage cadence, Server Subscriptions)
- E6d. **Slack sophistication** (Slack Connect channel count, Workflow Builder automations, Canvas usage)
- E6e. **Circle/Skool/Geneva sophistication** (course completion, gamification, paid-tier conversion)
- E6f. **Stack Overflow / Reddit moderator status** (owns subreddit/tag = moat)

### E7. Creator / ambassador program (/creators, /ambassadors, /partner-program for influencers)

### E8. Live audio (Twitter Spaces, LinkedIn Audio)

### E9. **YouTube channel quality** (depth)
- E9a. Upload cadence
- E9b. Shorts vs long-form ratio
- E9c. Thumbnail CTR proxy
- E9d. Playlist IA
- E9e. Community-tab usage
- E9f. End-screen + cards usage
- E9g. Subscriber trajectory

### E10. **LinkedIn Newsletter sophistication**
- E10a. Subscriber-to-follower ratio
- E10b. Send cadence variance
- E10c. Swipe-carousel-PDF density
- E10d. Repost-by-employees count

### E11. **Substack network posture**
- E11a. Notes posting cadence
- E11b. Recommendations given/received count
- E11c. Chat usage
- E11d. Paid-tier price ladder

### E12. **Beehiiv network growth** (Boosts marketplace participation, referral-program tier rewards, Recommendations network count)

### E13. **Reddit-as-primary-channel posture**
- E13a. Brand-owned subreddit existence
- E13b. AMA history (volume + Q&A depth)
- E13c. Reddit Ads pixel detection

### E14. **Webinar / event-hosting infrastructure**
- E14a. /webinars, /events URL discovery
- E14b. BrightTALK, Demio, Restream, Zoom Webinar fingerprints
- E14c. On-demand library + replay discoverability
- E14d. Gating strategy

### E15. **HN / Indie Hackers / dev.to / Hashnode publishing posture**
- E15a. HN submission domain history (algolia.hn site: search)
- E15b. Indie Hackers milestone-post cadence + Product of the Week wins
- E15c. dev.to / Hashnode / Medium publication ownership vs guest posting

### E16. **Mastodon / Bluesky / Threads / Lemmy** (emerging social)
- E16a. Bluesky custom-feed ownership (running a feed generator)
- E16b. Mastodon instance ownership (running .yourbrand.social)
- E16c. Threads tagged-topic seeding

### E17. **Engagement pods / coordinated-amplification** (mostly invisible; flag as not-auditable for honesty)

### E18. **Comment marketing** (low signal, hard to audit)

### E19. **Quora marketing** (declining 2026; presence-only check)

### E20. **Owned events / flagship event** (Dreamforce, INBOUND, Twilio Signal — subdomain detection)

### E21. **Conference speaking** (NewsData + speaker-bureau pages)

### E22. **Sponsorship visibility** (logo on sponsor pages of industry conferences, podcast network sponsors)

---

## F. Free Tools & Lead Magnets (8)

### F1. Free tool inventory **by type**
- F1a. Calculators (ROI, savings, cost, salary, tax, break-even)
- F1b. Generators (policy, template, name, subject-line, resume, color palette, logo)
- F1c. Analyzers / Auditors (website grader, SEO analyzer, headline analyzer, security checker)
- F1d. Testers / Validators
- F1e. Libraries / Resources
- F1f. Interactive Educational
- F1g. **Side projects as marketing** (separate sub-product)
- F1h. **Chrome extensions** (Web Store search by company)

### F2. Lead magnet inventory **by format**
- F2a. Ebooks & guides
- F2b. Checklists
- F2c. Cheat sheets
- F2d. Templates & spreadsheets
- F2e. Swipe files (curated example libraries)
- F2f. Mini-courses
- F2g. Quizzes & assessments
- F2h. Webinars & workshops

### F3. **Template library / template gallery** (templates.X, Figma/Canva/Notion model)
- F3a. Template count + category coverage
- F3b. Free vs paid template tier
- F3c. Pinterest-pin viability of templates

### F4. Research reports / "State of X" data-driven authority
- F4a. /state-of-, /research, annual benchmark releases
- F4b. Methodology disclosure
- F4c. Citation-worthiness for press

### F5. Proprietary data journalism (/insights, /benchmarks — product-data-driven content distinct from research reports)

### F6. Courses + books (authority depth)
- F6a. /academy, /university, /learn URL discovery
- F6b. Teachable / Thinkific / Maven / Kajabi fingerprints
- F6c. Books by author search (Google Books / Amazon)

### F7. **Importer / migration tool as marketing asset** ("Import from [Competitor]" tooling)

### F8. **Curation / resource library** (/resources, /library — curated content listings, third-party curation)

---

## G. Conversion Architecture (16)

### G1. Page CRO by page type
- G1a. Homepage CRO
- G1b. Landing page CRO
- G1c. Pricing page CRO
- G1d. Feature page CRO
- G1e. About page CRO
- G1f. Blog post CRO

### G2. Value proposition clarity
- G2a. Above-fold value-prop test
- G2b. Hero copy clarity (Dunford "We help X do Y unlike Z" structure NLP test)
- G2c. CTA hierarchy + placement
- G2d. Subheadline supports headline

### G3. Logo wall + homepage social-proof density
- G3a. Logo count
- G3b. **Customer-logo verification / dead-logo ratio** (logos without matching case study)
- G3c. "Trusted by X companies" stats
- G3d. Named-investor signaling

### G4. Trust signals density
- G4a. Security badges (SOC 2, ISO, HIPAA, PCI)
- G4b. Testimonials with photo + name + company
- G4c. Customer count / volume claims
- G4d. Star ratings / review aggregates

### G5. **Case studies / customer stories**
- G5a. /customers, /case-studies, /stories enumeration
- G5b. Case study depth + recency
- G5c. Industry / size / use-case coverage
- G5d. Quotable quote presence
- G5e. Quantified outcome density

### G6. **Comparison-page strategy (own)**
- G6a. /vs-X individual comparison pages
- G6b. /alternatives-to-Y individual pages
- G6c. **/vs and /alternatives hub-page architecture** + footer-column linking

### G7. Pricing page architecture & transparency
- G7a. Transparent vs gated ("contact sales" ratio)
- G7b. Tier structure clarity
- G7c. Annual/monthly toggle
- G7d. ROI calculator embedded
- G7e. Per-seat / per-usage clarity
- G7f. Free tier / free trial CTA prominence

### G8. **Form CRO** (demo / contact / lead — non-signup)
- G8a. Field count + required vs optional
- G8b. Multi-step vs single-step pattern
- G8c. **Progressive commitment / progressive profiling fingerprint**
- G8d. Social-auth options
- G8e. Inline validation + error handling
- G8f. Submit button copy + placement

### G9. **Signup flow CRO**
- G9a. Required field minimization
- G9b. SSO / social-auth presence
- G9c. Email verification flow + friction
- G9d. Mobile signup optimization
- G9e. **One-click registration / OAuth options**
- G9f. Time-to-value gate count

### G10. Popup CRO
- G10a. Trigger strategy (time / scroll / exit / click / page-count / behavior)
- G10b. Copy + design
- G10c. Frequency capping + audience targeting
- G10d. Compliance + accessibility

### G11. Demo / trial flow architecture
- G11a. Self-serve vs gated demo vs sales-only vs interactive product tour
- G11b. Trial duration + credit card required
- G11c. Demo routing by qualification

### G12. **Booking friction** (Calendly, SavvyCal, Chili Piper, HubSpot Meetings)

### G13. **Speed-to-lead / response-time** (test via demo-form submission)

### G14. **Refund / guarantee / returns policy visibility** (/refund, /guarantee, /returns reachability + specificity)

### G15. **Offer construction** (anchor pricing, bonus stack, urgency, scarcity, risk-reversal language on pricing page)

### G16. **Cart / abandoned-cart UX** (e-commerce cart-CRO; cart icon visibility, mini-cart, save-for-later)

---

## H. Activation & Product-Led (10)

### H1. **Onboarding CRO**
- H1a. Aha moment definition
- H1b. Onboarding checklist pattern
- H1c. Empty states quality
- H1d. Tooltips / guided tours (Userpilot / Appcues / Chameleon / Pendo fingerprints)
- H1e. Time-to-value
- H1f. Email + in-app coordination
- H1g. Stalled-user re-engagement

### H2. Freemium / free-tier / migration tools
- H2a. Pricing page free-tier presence
- H2b. /migrate-from-X, /switch-from-X, /import-from-X URL discovery
- H2c. Migration tool depth (data, settings, integrations)
- H2d. **Contract buyout offers**

### H3. **Paywall by trigger type**
- H3a. Feature gates
- H3b. Usage limits
- H3c. Trial expiration
- H3d. Time-based prompts
- H3e. Anti-pattern detection (dark patterns)

### H4. Changelog / public release cadence
- H4a. /changelog, /releases, /whats-new presence
- H4b. RSS / email subscribable
- H4c. Author attribution
- H4d. Release frequency

### H5. AI-feature marketing
- H5a. "ChatGPT plugin" / GPT / Claude Skill presence
- H5b. MCP server publication
- H5c. AI-native positioning on homepage

### H6. Viral loops / PLG distribution signals

### H7. "Powered by X" badge detection

### H8. **In-product upsell / cross-sell motion visibility** (signup observation)

### H9. **Concierge setup / white-glove onboarding** (/enterprise-setup, /concierge CTA)

### H10. **Trial reactivation flow** (expired-trial recovery)

---

## I. Lifecycle & Retention (14)

### I1. Capture surface scan
- I1a. Popup capture
- I1b. Form capture
- I1c. SMS capture (TCPA-compliant 2-step)
- I1d. Lead-magnet capture
- I1e. Content-upgrade capture
- I1f. Preference-center-at-signup

### I2. Welcome / onboarding email sequence
- I2a. Email 1: welcome + single next step
- I2b. Email 2-7: progressive activation
- I2c. Founder welcome email pattern

### I3. Product usage digest emails (daily / weekly / monthly summaries)

### I4. Milestone / achievement emails

### I5. Billing email suite
- I5a. Upcoming renewal reminder
- I5b. Failed-payment / dunning recovery
- I5c. Cancellation survey email
- I5d. Annual-switch incentive
- I5e. Pricing-update communication

### I6. NPS survey program (Delighted / Wootric / SurveyMonkey fingerprints)

### I7. **Review-request automation** (feeds D1 review-site posture)

### I8. **Cancel flow / churn prevention UX**
- I8a. Cancel button accessibility
- I8b. Exit survey
- I8c. Save-offer disclosure (discount / pause / annual / downgrade)
- I8d. **MRR-tier routing** (B2C automated vs B2B personal-touch)
- I8e. **Click-to-Cancel / FTC compliance** (online-cancel for online-signup)
- I8f. Retention-tool fingerprint (Churnkey, ProsperStack, Raaft)

### I9. Win-back / trial reactivation sequence

### I10. Lifecycle stack maturity (ESP / SMS / loyalty / reviews / referral / subscription)

### I11. **Email deliverability posture (publicly auditable)**
- I11a. SPF record correctness
- I11b. DKIM presence + alignment
- I11c. DMARC policy (p=reject vs quarantine vs none)
- I11d. BIMI + VMC presence
- I11e. MTA-STS / TLS-RPT
- I11f. ESP fingerprint via headers + return-path

### I12. **Mistake / "oops" email marketing pattern** (qualitative, low priority)

### I13. **Trial-expiry sequence quality** (fake-signup observation)

### I14. **Referral / share mechanics**
- I14a. Referral code / link in user menu / footer
- I14b. Share-with-team CTA
- I14c. Newsletter referral mechanic (Beehiiv / SparkLoop)
- I14d. Two-sided referrals (reward both)

---

## J. Sales / GTM / Enablement (17)

### J1. Verticalization / persona-site architecture
- J1a. /industries/ pages
- J1b. /solutions/ pages
- J1c. /for-developers, /for-marketers persona pages
- J1d. **Account-tier landing pages** (/enterprise/<industry> depth)

### J2. Sales enablement public assets
- J2a. /security overview
- J2b. /soc2, /compliance pages
- J2c. ROI calculators + value-prop tools
- J2d. Battle cards (publicly accessible)
- J2e. Sub-processor list (DPA self-serve download — GDPR Article 28)
- J2f. **Trust center page** (trust.brand.com / vanta-style centralized)

### J3. Press / media kit
- J3a. /press, /brand-kit, /media URLs
- J3b. Logo download (3+ formats)
- J3c. Color tokens, typography, spokesperson bios, fact sheet
- J3d. Press contact email visibility

### J4. **Sales deck / pitch deck public availability** (rare; /investors, /pitch URLs)

### J5. Objection handling content
- J5a. FAQ depth
- J5b. "Why us" page
- J5c. "Why not X competitor" content (defensive)

### J6. Booking friction (Calendly, SavvyCal, Chili Piper, HubSpot Meetings)

### J7. Speed-to-lead (test via form submit)

### J8. Lead scoring & MQL-SQL lifecycle
- J8a. Form-field patterns suggesting scoring
- J8b. **MQL-handoff transparency** (jobs page / careers MOps role descriptions)

### J9. Enrichment / identity resolution
- J9a. RB2B / Clearbit Reveal / Leadfeeder
- J9b. **Geo-gating check** (RB2B is US-only — global use = GDPR finding)
- J9c. **HubSpot Breeze Intelligence** (current Clearbit successor)
- J9d. Modern waterfall (Apollo + Clay + ZoomInfo)

### J10. ABM tooling (6sense, Demandbase, Terminus)
- J10a. Intent-data vendor footprint (6sense / Demandbase / Bombora pixel detection)
- J10b. **Reverse-IP personalization evidence** (differing hero copy by ASN — probe from cloud IPs)

### J11. **Clean-room posture** (LiveRamp, AWS Clean Rooms, Snowflake, Habu, InfoSum) — vendor case-study + careers signals

### J12. **AI SDR agent in own outbound** (Artisan "Ava" / 11x "Alice" / Regie / Relevance fingerprints in demo-response)

### J13. **Sales engagement / outbound infrastructure** (Outreach, Salesloft, Apollo, Instantly, Lemlist, Snov fingerprints; SDR/BDR team-size signaling via LinkedIn/jobs)

### J14. **Conversation intelligence presence** (Gong / Chorus / Wingman / Fathom — fingerprint on customer-facing webinar/demo pages)

### J15. **Customer journey orchestration** (Adobe Journey Optimizer / Braze Canvas / Iterable Workflow Studio fingerprints)

### J16. **Channel partner program** (/resellers, /partners/reseller, white-label tier)

### J17. **Customer-Cloud / partner-overlap signaling** (Crossbeam / Reveal / Nearbound — "X of your tools use [Product]" widgets)

---

## K. Brand & Authority (18)

### K1. Positioning + narrative clarity
- K1a. Hero positioning statement explicitness
- K1b. Category claim consistency
- K1c. Differentiation vs "like everyone"

### K2. Customer language alignment (Jobs-to-Done framing; reviewer-language match)

### K3. Thought leadership program (sustained public output)

### K4. Certifications program (HubSpot Academy / Trailhead / AWS Certs model)
- K4a. /certification, /academy, /credentials URL
- K4b. Credly / Accredible / certified.dev fingerprints
- K4c. Tier structure (free / paid / enterprise)

### K5. Owned events / flagship event (Dreamforce / INBOUND model — subdomain detection)

### K6. Status page + uptime transparency
- K6a. status.brand.com / Statuspage.io / Better Stack / Atlassian Statuspage
- K6b. Component count + granularity
- K6c. Historical uptime % visible
- K6d. Incident-history depth
- K6e. RSS / webhook subscribable

### K7. ESG / sustainability / DEI positioning
- K7a. /sustainability, /impact, /dei pages
- K7b. B Corp Certified tier
- K7c. 1% for the Planet member
- K7d. Climate Neutral Certified / Climate Label
- K7e. Fair Trade USA / Fair Trade International
- K7f. Cradle to Cradle, LEED, Rainforest Alliance
- K7g. **SBTi commitment tier** (Near-term / Net-Zero)
- K7h. **CDP score letter grade**
- K7i. **EcoVadis medal tier**
- K7j. **ISO 14001, ISCC PLUS, GreenGuard**

### K8. Board / advisor / investor credibility signaling (/about, /team, LinkedIn cross-reference)

### K9. **Brand salience proxy** (Google Trends branded-search volume trajectory)

### K10. **Brand esteem / sentiment delta**
- K10a. Review-platform sentiment (polarity + aspect-based)
- K10b. Reddit / HN thread tone
- K10c. Social mention sentiment

### K11. **Brand differentiation (BAV vitality/stature)** — counter-positioning vs claimed-category proof

### K12. **Brand personality consistency / voice drift** across landing / blog / social / sales decks

### K13. **AI-generated copy density audit** (in own copy — "AI tells")

### K14. **Share-of-search vs named competitors** (Google Trends comparison)

### K15. **Unlinked brand mentions volume** (Brand24 / Mention / BuzzSumo)

### K16. **Marketing org / leadership signals**
- K16a. CMO / head-of-marketing public on LinkedIn
- K16b. Marketing-team headcount via LinkedIn employees count
- K16c. Open marketing roles on careers page + velocity
- K16d. Agency-of-record signals (case studies on agency sites)
- K16e. CMO LinkedIn tenure

### K17. **Employer brand / careers-page-as-marketing**
- K17a. Glassdoor rating + response rate
- K17b. Comparably ratings
- K17c. Careers-page tech-problem storytelling (Stripe / Notion model)
- K17d. Open-roles count
- K17e. **DEI / supplier-diversity signals**

### K18. **Investor relations page**
- K18a. /investors page existence
- K18b. SEC filings link
- K18c. ESG report
- K18d. Analyst-coverage surface

---

## L. MarTech, Measurement & Analytics (23)

### L1. MarTech stack inventory (BuiltWith / Wappalyzer — 20+ categories)

### L2. Attribution maturity
- L2a. Client-side only vs server-side vs first-party-ID vs full closed-loop
- L2b. Cookieless tracking readiness
- L2c. **Server-side GTM presence** (first-party subdomain metrics./sst./t./data. resolving to GCP Cloud Run)
- L2d. **Meta CAPI deployment** (server-side hashing, _fbp/_fbc handling)
- L2e. **Google Enhanced Conversions deployment**
- L2f. **CAPI/server-side event deduplication** (event_id pattern)
- L2g. **Aggregated Event Measurement (iOS 14+) configuration** (Meta priority ordering — partial)

### L3. Event-naming discipline + funnel instrumentation
- L3a. Object-action naming convention
- L3b. Event taxonomy completeness vs business questions
- L3c. Custom event examples
- L3d. Funnel-step instrumentation depth

### L4. Consent / CMP / privacy signal handling
- L4a. CMP detection (OneTrust, Cookiebot, TrustArc, Osano)
- L4b. **Consent Mode v2 quality** (4 parameters pre/post consent: analytics_storage, ad_storage, ad_user_data, ad_personalization)
- L4c. DNT / GPC honoring
- L4d. Universal-Opt-Out-Signal (UOOS) honoring
- L4e. Pre-consent script firing audit
- L4f. **TCF v2.2 / GPP (Global Privacy Platform) compliance**
- L4g. **DAA AdChoices icon presence**

### L5. UTM taxonomy discipline
- L5a. Standard parameter usage
- L5b. Naming convention consistency
- L5c. **Dub.co-style centralized shortlink attribution hygiene** (consistent shortlink domain across social/newsletter)

### L6. CRO tooling (Optimizely, VWO, Mutiny, Intellimize, Adobe Target)

### L7. Session replay / heatmap (Hotjar, FullStory, Mouseflow, LogRocket)

### L8. Product analytics (Amplitude, Mixpanel, PostHog, Heap)

### L9. RevOps stack (CRM + MAP + sales engagement)
- L9a. CRM detection (HubSpot, Salesforce, Close, Pipedrive)
- L9b. MAP detection (HubSpot Marketing, Marketo, Pardot)
- L9c. Sales engagement (Outreach, Salesloft, Apollo)
- L9d. **Lead-scoring fingerprint** (form patterns)

### L10. Customer research tooling (SparkToro, Dovetail, User Interviews, Maze, dscout)

### L11. **AI citation tracking tooling** (Profound, Peec, Otterly, AthenaHQ — script + careers signals)

### L12. **MMM (Marketing Mix Modeling) infrastructure** — Meridian / Robyn / Recast / Incrementality (jobs page + vendor case-study pages)

### L13. **Self-reported attribution field** in demo/trial forms ("How did you hear about us?")

### L14. **Conversion tracking** (GA4, Adobe Analytics, Plausible, Fathom — alternative analytics)

### L15. **Tag-manager hygiene** (GTM container size, fired-vs-defined tags, deprecated pixels — FB legacy / GA UA)

### L16. **Vendor sprawl per category** (2+ analytics libs / 2+ CDPs / 2+ chat widgets co-loaded — MarTech debt indicator)

### L17. **CDP / reverse-ETL fingerprint** (Segment analytics.js, RudderStack, Hightouch, Census)

### L18. **Chat widget detection + routing behavior** (Intercom vs Drift vs Tidio vs Crisp vs none)

### L19. **A/B test tooling fingerprint** (visible to client SDK)

### L20. **Personalization tooling fingerprint** (Mutiny, Intellimize, Hyperise)

### L21. **Form tooling** (Typeform, Tally, Paperform, HubSpot Forms, Gravity Forms)

### L22. **Booking tooling** (Calendly, SavvyCal, Chili Piper, HubSpot Meetings, Cal.com)

### L23. **Email/SMS deliverability tooling** (Postmark headers, SendGrid X-Mailer, Klaviyo signature, Iterable, Customer.io)

---

## M. Competitive (8)

### M1. Competitive ad research (SpyFu, Facebook Ad Library, Google Ads Transparency Center, LinkedIn Ad Library)

### M2. Marketing Jiu-Jitsu / counter-positioning (turning competitor strengths into your weakness positioning)

### M3. Own comparison-page strategy (overlaps G6)

### M4. Contract buyout / migration tools (overlaps H2)

### M5. **Customer switching narratives** ("/switch-from-X" content; "switched from X" testimonials)

### M6. **Pixel sharing / audience-sharing partnerships** (legacy)

### M7. **Competitive intelligence tooling** (Klue, Crayon, Kompyte fingerprints)

### M8. **Win-loss analysis surfacing** (Klue / public win-loss reports / customer-quote analysis)

---

## N. Developer / DevRel (12, when applicable)

### N1. Public API / developer portal
- N1a. /developers, /api, /docs URL pattern
- N1b. API reference quality
- N1c. SDK availability per language
- N1d. Authentication flow documentation

### N2. SDK language coverage (JS, Python, Go, Ruby, Java, .NET, PHP, Swift, Kotlin)

### N3. API docs tooling (ReadMe, Mintlify, Stoplight, Redoc, Scalar, Bump.sh)

### N4. Developer hackathon presence + sponsor-of-record

### N5. Open-source community depth
- N5a. Stars velocity
- N5b. Issue response time
- N5c. PR diversity (contributor count, bus factor)
- N5d. Last-commit recency
- N5e. Discussions activity
- N5f. **License clarity** (AGPL/SSPL/BSL with conversion date + commercial-tier delta)
- N5g. **GitHub Sponsors + OpenCollective** transparency

### N6. Hacker News submission history (algolia.hn search by site:)

### N7. **Show HN submission history** (specific subset)

### N8. **DevRel team signaling** (jobs page DevRel roles, CodingHorrors-style technical blog presence)

### N9. **Public roadmap** (Productboard / Canny / GitHub Projects publicly visible)

### N10. **Technical community metrics** (Stack Overflow tag activity, GitHub Discussions, Discord developer channel size)

### N11. **AI-coding-tool integrations** (Cursor / Cline / Windsurf rules in awesome-cursor / Cursor Directory; .mdc files in repo)

### N12. **Postman API Network / RapidAPI listing** (followers, fork count, public collections)

---

## O. AI Surface & Agent-Readiness (12)

### O1. AI bot access (split — see A14 for details)

### O2. llms.txt / machine-readable files (low-weight per research; see A15)

### O3. Content extractability for LLMs (see A16)

### O4. AI citation patterns (see A13)

### O5. **Agent-card / MCP discoverability**
- O5a. /.well-known/agent-card.json (A2A protocol)
- O5b. /.well-known/mcp-server (announced June 2026)
- O5c. agents.json
- O5d. Public remote MCP server publication

### O6. **Product feed for AI commerce**
- O6a. /.well-known/ucp/manifest.json (Google UCP)
- O6b. sitemap-products.xml
- O6c. Product JSON-LD with gtin, return_policy, popularity_score
- O6d. ChatGPT Shopping integration
- O6e. Perplexity Shopping integration

### O7. **AI-feature marketing posture**
- O7a. ChatGPT GPT Store listing + ranking
- O7b. ChatGPT Apps (App SDK, Q4 2025+)
- O7c. Microsoft Copilot extensions / Copilot agents in AppSource
- O7d. Perplexity Spaces presence + follower count
- O7e. Cursor / Cline / Windsurf presence
- O7f. Anthropic-partner / Claude Skills (when public marketplace)

### O8. **AI-content disclosure policy** (page existence; AI-generated content labeling per state law)

### O9. **EU AI Act Article 50 readiness** (chatbot disclosure in first turn, AI-content labeling, synthetic-media watermarking commitments)

### O10. **AI policy / model cards** (for AI/ML companies — model card per shipped model, evals page with benchmark scores)

### O11. **AI-content provenance (C2PA / content credentials)** in marketing imagery — image-metadata audit

### O12. **AI SDR agent in own outbound** (see J12)

---

## P. Persuasion & Conversion Psychology (7)

### P1. **Cialdini-6 density audit**
- P1a. Reciprocity (free value given before ask)
- P1b. Commitment & consistency
- P1c. Social proof density (logo bars, review counts, testimonials per landing page)
- P1d. Authority signals (certifications, awards, named experts)
- P1e. Liking
- P1f. Scarcity (and **scarcity authenticity** — multi-session probe to detect fake "only 3 left")

### P2. Anchoring (pricing-page anchor placement)

### P3. Loss aversion framing

### P4. Default bias / choice architecture (preselected options)

### P5. Framing effects in copy

### P6. **Reading-grade variance across surfaces** (Flesch-Kincaid: homepage vs legal vs error microcopy)

### P7. **Pronoun ratio** ("we" vs "you" — customer-centricity proxy)

---

## Q. Customer Experience (CX) (9)

### Q1. **Effort asymmetry** (clicks-to-cancel vs clicks-to-buy — Forrester CXi core)

### Q2. **Resolution channel parity** (self-serve / chat / phone / email all reach same KB version)

### Q3. **Emotion words in microcopy** (confirmation / error / empty-state pages)

### Q4. **Time-to-value across the funnel** (signup → aha)

### Q5. **Feedback-loop presence** (in-app feedback widget, NPS prompt, support-ticket follow-up)

### Q6. **Service-recovery posture** (response to negative reviews, public complaints)

### Q7. **Customer journey transparency** (process page, "what happens next" content)

### Q8. **Onboarding-to-CSM handoff visibility** (B2B SaaS — customer-success contact assigned at signup or post-trial)

### Q9. **Voice & tone consistency** (across surfaces — separate from copy quality; bordering S)

---

## R. Trust & Safety / Transparency (6)

### R1. **Transparency report cadence** (annual / quarterly / none)

### R2. **Abuse-reporting flow depth** (clicks-to-report from any UGC; for any UGC-bearing platform)

### R3. **Content moderation policy** (for platforms with UGC)

### R4. **Security disclosure policy / security.txt** (/.well-known/security.txt presence)

### R5. **Bug bounty program** (Immunefi / HackerOne / Bugcrowd listing + max payout disclosure)

### R6. **Vulnerability disclosure timeline** (publicly committed window)

---

## S. Design System & Brand Governance (9)

### S1. **Public Storybook presence** (storybook.brand.com / design.brand.com / ui.brand.com — Storybook 8/9 expose index.json manifest)

### S2. **Component count + last-publish** (from Storybook index.json or Chromatic public library)

### S3. **Figma Community presence** (figma.com/@org library file count)

### S4. **Brand portal accessibility** (brand.brand.com / press. / Frontify / Brandfolder / Bynder vanity URLs)

### S5. **Press-kit completeness score** (logos in 3+ formats / color tokens / typography / spokesperson bios / fact sheet)

### S6. **Logo-version sprawl** (count distinct logo SVG hashes across press kit / footer / favicon / og-image / app icon)

### S7. **Color drift** (hex-distance between stated brand color and actual CSS custom properties)

### S8. **Typeface license posture** (self-hosted vs Adobe Fonts / Typekit / Google Fonts — implies governance maturity)

### S9. **Brand-consistency monitoring tooling** (Frontify / Brandfolder / Bynder DAM presence)

---

## T. Customer Support Quality (7)

### T1. **Help center / docs maturity**
- T1a. /docs, /help, /support presence
- T1b. Article count
- T1c. Last-edited dates
- T1d. "Helpful?" widget presence
- T1e. Documentation tooling (ReadMe, GitBook, Mintlify, Document360)

### T2. **AI-chat handoff transparency** (scripted chat probe — time-to-human, escalation visibility)

### T3. **Knowledge base depth + recency**

### T4. **Community-support ratio** (forum / Discord / Discourse vs ticket-only)

### T5. **Support response-time SLA disclosure** (publicly committed)

### T6. **Multi-channel support availability** (chat / email / phone / in-app — coverage map)

### T7. **Self-service success-rate proxy** (search bar prominence in docs, related-articles depth)

---

## U. Compliance & Regulatory (35)

### U1. **GDPR / EU privacy**
- U1a. Privacy policy GDPR-compliant content
- U1b. DPO contact disclosed
- U1c. Cookie consent compliance
- U1d. Data Subject Access Request (DSAR) flow
- U1e. Right-to-erasure UX

### U2. **UK GDPR / DPA 2018**
- U2a. ICO registration number (ZA-prefix) in footer/policy
- U2b. UK representative named for non-UK controllers (Art. 27)

### U3. **Switzerland nFADP** (Swiss representative named, "revFADP" / "nFADP" reference)

### U4. **Quebec Law 25**
- U4a. French-language privacy notice
- U4b. **Personne responsable** disclosure
- U4c. Automated-decision opt-out
- U4d. Privacy-by-default signals

### U5. **APAC privacy laws**
- U5a. **Japan APPI** (個人情報保護方針 header, designated representative if no JP entity)
- U5b. **South Korea PIPA** (separate consent checkboxes 필수/선택, CPO mandatory disclosure)
- U5c. **China PIPL** (cross-border transfer mechanism named, ICP 备案 license number for .cn presence)
- U5d. **Singapore PDPA** (DPO contact, DNC compliance)
- U5e. **Thailand PDPA** (DPO for sensitive-data, Thai-language banner for .th)
- U5f. **Vietnam PDPD** (Decree 13/2023 — DPIA reference, MPS notification)
- U5g. **Philippines DPA** (NPC registration, DPO disclosed)

### U6. **LATAM privacy laws**
- U6a. **LGPD (Brazil)** — Encarregado name + email mandatory, ANPD complaint pointer, Portuguese version for .com.br
- U6b. **Argentina Ley 25.326** — AAIP database registration mention
- U6c. **Colombia Ley 1581** — SIC registration claim

### U7. **MEA + Other privacy laws**
- U7a. **UAE PDPL** (Federal Decree 45/2021)
- U7b. **Saudi PDPL** (SDAIA registration, KSA-resident DPO)
- U7c. **Israel PPL + 2024 Amendment 13**
- U7d. **South Africa POPIA** (Information Officer registered, PAIA manual link)
- U7e. **Australian Privacy Act + 2026 reforms** (right to deletion, statutory tort)

### U8. **US state privacy laws** (18+ active by 2026)
- U8a. State enumeration in privacy policy (CA, VA, CO, CT, UT, TX, OR, MT, IA, TN, DE, NH, NJ, MN, MD, IN, KY, RI...)
- U8b. **Do-Not-Sell links** ("Do Not Sell My Personal Information")
- U8c. **Sensitive-data opt-in signals**
- U8d. **Profiling opt-out**
- U8e. **Universal-Opt-Out-Signal (UOOS) honoring**
- U8f. **CTDPA loyalty-program disclosure** (Connecticut)
- U8g. **Maryland MOPDA** (most restrictive — minor data prohibitions)
- U8h. **Texas TDPSA** (sensitive-data consent)
- U8i. **Washington My Health My Data Act** (WMHMDA — separate consumer-health-data notice; broadest)
- U8j. **Nevada SB 370 + Connecticut health amendments**

### U9. **HIPAA + healthcare-specific**
- U9a. HIPAA-safe analytics posture (no Meta Pixel / GA4 on condition pages)
- U9b. BAA-tooled stack (Freshpaint / Piwik Pro / server-side tagging)
- U9c. **42 CFR Part 2** (substance-use treatment)
- U9d. **HITECH Act marketing restrictions**
- U9e. **FDA REMS marketing**
- U9f. **DEA telemedicine** controlled-substance disclosures

### U10. **Children's privacy (COPPA / KOSA)**
- U10a. Verifiable parental consent
- U10b. Age gate quality
- U10c. Data-collection limits for under-13

### U11. **FERPA** (directory-info opt-out, school-official designation)

### U12. **GLBA** (financial privacy notice, opt-out before sharing with affiliates)

### U13. **SOX** (investor-comms disclosure, material event)

### U14. **FDA marketing regulation**
- U14a. Drug/device/supplement claims substantiation
- U14b. **Fair-balance ISI placement** (Important Safety Information above fold + every page)
- U14c. **MedDRA-coded AE reporting form + 1-800-FDA-1088**
- U14d. **DTC ad disclosure compliance** (FDA Final Rule)

### U15. **FTC marketing regulation**
- U15a. Endorsement disclosure (revised 2023 Endorsement Guides)
- U15b. **Substantiation of claims**
- U15c. **Dark-pattern guidance compliance**
- U15d. **Click-to-Cancel rule** (effective 2025/2026)
- U15e. **Junk-fee rule disclosure**
- U15f. **Income claims** (MLM/biz-opp specific)

### U16. **TCPA** (SMS/calling consent, prior express written consent, time-of-day restrictions)

### U17. **CAN-SPAM** (unsubscribe link, physical address, From: line accuracy)

### U18. **CASL (Canada)** (express consent, identification info, prescribed unsubscribe)

### U19. **ADA Title III + Section 508**
- U19a. **WCAG 2.2 AA conformance** (axe-core / Lighthouse a11y)
- U19b. **Accessibility statement** + VPAT linked
- U19c. **EAA (European Accessibility Act)** — enforceable June 2025; €100k penalties
- U19d. **Overlay-vs-real-fix detection** (AccessiBe / UserWay = ADA-lawsuit magnet)

### U20. **EU Digital regulation**
- U20a. **DSA (Digital Services Act)** — VLOP notification, transparency reports, content moderation
- U20b. **DMA (Digital Markets Act)** — gatekeeper obligations
- U20c. **MiCA** — crypto marketing restrictions, whitepaper publication
- U20d. **DORA** (Digital Operational Resilience Act) for finance
- U20e. **NIS2 cybersecurity disclosures**
- U20f. **EU AI Act Article 50** (chatbot disclosure, AI-content labeling — binding Aug 2026)

### U21. **Marketing-specific regulatory**
- U21a. **AI-generated content disclosure** (US states starting 2024 — CA, IL, MA, MN, NY, PA, WA)
- U21b. **AI political advertising disclosure** (multiple state laws)
- U21c. **Influencer FTC #ad disclosure**
- U21d. **Native advertising labeling** (FTC guidance)
- U21e. **Comparative advertising claims substantiation** (Lanham Act §43(a))
- U21f. **Fake reviews crackdown** (FTC 2024 rule)

### U22. **Industry trust/security badges**
- U22a. **SOC 2 Type II vs SOC 3 distinction** (SOC 3 publicly displayable; SOC 2 behind NDA)
- U22b. **ISO 27001 / 27017 / 27018 / 27701**
- U22c. **FedRAMP Moderate / High / Li-SaaS** + StateRAMP + TX-RAMP / AZ-RAMP
- U22d. **CMMC 2.0** (defense-tier)
- U22e. **HITRUST r2 / i1 / e1 tier specificity** (generic "HITRUST" claim is low-signal)
- U22f. **PCI DSS v4.0** (post-March 2025; v3.2.1 = stale)
- U22g. **CSA STAR Level 1/2/3 registry** presence
- U22h. **TISAX** (automotive supply chain)
- U22i. **IRAP** (Australian gov cloud)
- U22j. **C5** (Germany BSI cloud)

### U23. **Privacy seal certifications**
- U23a. **TrustArc Verified, ePrivacyseal, EuroPriSe** (EU privacy seals)
- U23b. **JIPDEC PrivacyMark** (Japan)
- U23c. **EU-US Data Privacy Framework (DPF)** active certification (replaces Privacy Shield — verifiable on dataprivacyframework.gov)
- U23d. **APEC CBPR / Global CBPR participant**

### U24. **AI-specific certifications**
- U24a. **ISO 42001** (AI management system) — emerging 2024+
- U24b. **NIST AI RMF alignment claim**

### U25. **Trademark / IP / patent signaling** (USPTO search; defensible moat signaling)

### U26. **Sub-processor page transparency** (DPA self-serve download)

### U27. **Vertical-specific regulatory** (FINRA / SEC 206(4)-1 / TILA / NMLS / state UPL — see verticals)

### U28. **Stale-trust-page red flag** (Norton Secured / McAfee SECURE = decommissioned 2019/2020; presence today is negative signal)

### U29. **MAP (Minimum Advertised Price) policy disclosure**

### U30. **Prop 65 warnings** (CA — placement on product pages)

### U31. **State AI-ad disclosure** (multi-state political and consumer)

### U32. **Crypto/web3 OFAC compliance** (jurisdictional ToS, sanctioned-country exclusions)

### U33. **Cookie banner first-firing audit** (scripts firing pre-consent — major GDPR finding)

### U34. **Data-retention policy disclosure**

### U35. **Data-breach notification policy + history** (transparency reports)

---

## V. Mobile & App Experience (8)

### V1. **Thumb-zone CTA placement** (primary CTA y-coordinate on 375×667 viewport)

### V2. **App-vs-web feature parity** (App Store description vs web pricing page)

### V3. **Deep-link well-knowns**
- V3a. apple-app-site-association presence + correctness
- V3b. assetlinks.json (Android App Links)
- V3c. Branch.io / Firebase Dynamic Links / smart app banner

### V4. **Mobile-only friction** (forms, navigation, tap targets)

### V5. **Mobile site speed** (separate from desktop — distinct CrUX)

### V6. **Progressive Web App posture** (manifest.json, service worker, install prompts)

### V7. **In-app browser handling** (Instagram / TikTok in-app browser detection + accommodations)

### V8. **App Store Optimization** (see D4 — separate audit dimension)

---

## W. Meta-Diagnostic Frames (9)

These sit *above* the tactical lenses — they shape how findings are interpreted.

### W1. **Channel-model fit** (Balfour's Four Fits — does pricing/ACV support the channels they're running?)

### W2. **Growth loops vs funnel inventory** (Reforge framework — can any compound? Catalog public viral / content / paid / sales loops)

### W3. **North-star metric / vanity-metric tell** (what do they publicly brag on? MRR vs follower count)

### W4. **Marketing-maturity tier** (Kotler / Forrester 6-axis — strategy / org / systems / productivity / function)

### W5. **Traffic-mix ratio** (direct / organic / paid / social / referral / email — SimilarWeb top-layer diagnostic)

### W6. **Share-of-voice vs named competitors** (search + social + display)

### W7. **Traffic trajectory 12-month delta** (growth / plateau / decline)

### W8. **Geo / country mix** (ICP-channel mismatch detector)

### W9. **Engagement tier proxies** (bounce rate / session duration / pages-per-session — SimilarWeb)

---

## Vertical Bundles

These bundles fire **only when the prospect's vertical is detected** via signals (Shopify presence → e-com; .gov / .mil → government; HIPAA disclaimer → healthcare; etc.). Each bundle sits on top of the core 23 super-sections.

### Vertical 1: E-commerce (DTC + retail + marketplace)
- Shopify app fingerprint (Recharge / Skio / Klaviyo / Gorgias / Yotpo / Okendo / Social Snowball)
- PDP completeness score (Product schema, reviews visible, shipping/returns on PDP, BOPIS, subscription toggle, size-chart, ETA)
- Checkout friction probe (guest checkout, Shop Pay / Apple Pay / Link, shipping threshold, returns-policy in footer + cart)
- Amazon presence parity (Brand Registry, A+ Content, Storefront URL, Attribution pixel)
- Post-purchase surface (order-status branding, Loop / Returnly, Aftership)
- Subscription cadence flexibility (skip / swap / pause depth)
- Cart abandonment recovery (cart-recovery emails — partial via fake checkout)

### Vertical 2: Healthcare / health tech
- HIPAA-safe analytics posture (Meta Pixel / GA4 absence on condition pages)
- BAA-tooled vs consumer analytics
- Condition-page consent granularity
- NPI visibility
- Accepted-insurance page
- Provider-directory SEO
- HHS OCR online-tracking-guidance compliance
- 42 CFR Part 2 (substance-use)
- Washington My Health My Data separate notice

### Vertical 3: Fintech / banking / mortgage / insurance
- Disclosure footer density (FINRA / SEC 206(4)-1, TILA disclaimers)
- NMLS-ID on every LO profile (state-by-state)
- State-licensing footprint map (NMLS Consumer Access embed)
- Third-party-rating compensation disclosure (Dec 2025 SEC Risk Alert)
- Reg E (EFT error-resolution)
- CFPB §1033 open-banking claim
- NYDFS 23 NYCRR 500 (CISO disclosure for NY)
- FINCEN BSA AML program disclosure
- Quote-flow architecture (insurance: zip-first vs personal-info-first)

### Vertical 4: Edtech
- FERPA / COPPA posture page
- Student-data-privacy pledge (Future of Privacy Forum)
- State-level DPA library (CA SB-1177, NY Ed Law 2-d Parents' Bill of Rights)
- Accreditation / ESSA-tier badges
- District case studies vs B2C/self-serve split
- California SOPIPA student-data restrictions

### Vertical 5: Manufacturing / industrial / construction
- Spec compliance badges (UL / CE / NSF / FM / CSA / IECEx)
- BIM library presence (Revit / SketchUp / AutoCAD downloads)
- Engineer specifier portal (CAD / CSI MasterFormat 3-part spec downloads)
- Distributor locator + "where to buy" depth
- RFQ form (not "contact us")
- Trade-pub presence (ThomasNet, GlobalSpec, IndustryNet)
- Tradeshow calendar page
- Catalog/PIM externality (spec-sheet PDFs crawled)

### Vertical 6: Marketplaces (two-sided)
- Supply-side recruiting funnel (dedicated "become a seller/partner" landing)
- Supply liquidity proxies (listings per category, time-to-first-match, take-rate disclosure)
- Dual-NPS / dual-trust signals
- Buyer + seller success-story balance

### Vertical 7: Local services / multi-location
- GBP-per-location audit (NAP consistency across GBP / Bing Places / Apple Maps / Yelp / Facebook)
- Per-location review velocity + response rate
- Service-area pages with unique content (not templated)
- Geo-grid rank scan
- Citation governance source-of-truth
- Industry-specific directories (Angi / Thumbtack / HomeAdvisor)
- Financing partner badge (Synchrony / GreenSky / Wisetack)
- 24/7 emergency CTA prominence

### Vertical 8: Real estate
- IDX vs MLS syndication
- MLS-feed freshness
- Neighborhood / school-district geo-pages
- Agent-bio pages with reviews
- Zillow Premier Agent status
- Listing schema markup

### Vertical 9: Restaurants / hospitality
- Reserve-with-Google integration
- OpenTable / Resy / Tock connection
- Menu schema (prices, dietary)
- Third-party delivery parity (DoorDash / UberEats / Grubhub menu match)
- Yelp / TripAdvisor presence by tourism index
- Travelers' Choice / ranking-in-locality

### Vertical 10: Travel-deep (hotels / OTAs / airlines / vacation rentals / cruise / tour)
- OTA distribution width (Booking / Expedia / Agoda / Hotels.com / Trip.com / Hopper)
- Direct-vs-OTA price parity
- GDS code presence (Sabre / Amadeus / Travelport)
- Loyalty program tier visibility, points-on-base-rate, partner reciprocity
- TripAdvisor "Travelers' Choice"
- IATA accreditation (tour operators)

### Vertical 11: Legal services
- State-bar disclaimers ("past results don't guarantee future outcomes")
- Attorney-name-on-every-page rule
- Avvo / Martindale / Super Lawyers badges
- Jurisdictional-admissions disclosure
- AI-generated-ad disclosure (emerging 2026 state requirement)
- "Attorney Advertising" required by NY/NJ/FL/MO/TX rules
- State unauthorized-practice-of-law (UPL) compliance

### Vertical 12: Nonprofits
- Candid Seal of Transparency tier
- Charity Navigator score
- 990 linked publicly
- Donation-funnel (Donorbox / Givebutter)
- Recurring-giving option
- Impact-report page
- GuideStar presence

### Vertical 13: Creator economy / personal brand
- Course platform (Teachable / Kajabi / Skool)
- Paid newsletter (Substack / Beehiiv) tier
- Media-kit / sponsorship deck link
- Past-brand-deal logos
- Community (Discord / Circle / Geneva) surface
- Patreon / Buy Me a Coffee / Ko-fi presence

### Vertical 14: Government / B2G / Defense
- SAM.gov registration + UEI visible
- GSA Schedule + contract number
- FedRAMP status (Moderate / High / Li-SaaS)
- CMMC 2.0 level (defense)
- NAICS coverage list
- StateRAMP / TX-RAMP / AZ-RAMP for state work
- ITAR registration (defense)
- DFARS 7012 compliance
- Five Eyes / NATO citizenship requirements
- DoD-specific case studies
- SBIR award history

### Vertical 15: Pharma / biotech / medical device
- FDA approval letter linked
- Indication-specific HCP-vs-patient site split
- Fair-balance ISI placement
- MedDRA-coded AE reporting + 1-800-FDA-1088
- Patient assistance program eligibility tool
- DTC ad compliance per FDA Final Rule
- ISI on every page
- Risk Evaluation and Mitigation Strategy (REMS) marketing

### Vertical 16: Crypto / Web3
- ToS jurisdictional restrictions (US states + OFAC)
- Audit reports linked (CertiK / Quantstamp / Trail of Bits) with date
- Tokenomics page (vesting schedule + allocation chart)
- Governance forum (Discourse / Commonwealth) post velocity + unique authors
- Bug bounty (Immunefi listing + max payout)
- MiCA compliance (EU) + whitepaper publication

### Vertical 17: AI / ML companies (selling AI tools)
- Model card per shipped model
- Evals page with benchmark scores + methodology
- EU AI Act Article 13/14 transparency disclosure (high-risk classification)
- RSP / RAIL license / acceptable-use policy
- Training-data transparency tier (data-card or refusal)
- Safety / alignment commitments

### Vertical 18: Gaming / Esports / Adult / Cannabis / MLM / Religious
**Gaming/esports:**
- Steam page conversion stack (trailer-above-fold, badge, achievement count, Steam Deck Verified)
- Discord server tier (Partner/Verified badge + member count + boost)
- Twitch category presence (hours-watched rank)
- Esports sponsor stack
- Beta-key gating mechanism

**Adult/regulated:**
- State-specific age-verification (UT/TX/LA/AR/MS/MT/VA/NC/IN — distinct compliance UX)
- High-risk processor disclosure (CCBill / Segpay / Epoch — no Visa/MC, ACH only)
- 18 USC 2257 record-keeping statement

**Cannabis:**
- State-by-state product availability matrix
- Age-gate UX + METRC compliance language
- High-risk payment processor disclosure

**MLM / direct sales:**
- Income disclosure statement linked from "earnings" claims (FTC requirement)
- Distributor-recruiting funnel separation from product funnel
- Comp-plan PDF accessibility

**Religious / faith-based:**
- Tithe.ly / Pushpay / Subsplash integration
- Livestream sophistication (multi-cam, captions, ASL track)
- Multi-campus selector UX
- Sermon archive + transcript availability

(Bundles 19-23 — Beauty, Fashion, CPG/F&B, Subscription Boxes, Pets, Wedding, Service-businesses, Membership orgs, Telecom/ISP, Hosting/infra, OSS-SaaS, Media/publishing — listed as **overlays** that fold into core verticals rather than standalone bundles.)

---

## Geo-Conditional Bundles (added 2026-04-22)

These bundles fire **only when prospect has presence in that geography**, detected via signals: hreflang tag, ccTLD (.co.uk, .de, .fr, .com.br, .cn, .ch, .co.jp, .kr, .sg, .ae), currency selector (GBP, EUR, BRL, CNY, CHF, JPY, KRW, SGD, AED), local CDN/DNS hints, or privacy policy enumeration of the jurisdiction.

Each bundle contains the mandatory regulatory lenses for operating in that geography. Missing items are high-severity findings (regulatory-risk category).

### Geo Bundle 1: EU / UK regulatory (largest — fires for ~50% of B2B SaaS prospects)
Triggers on: hreflang=de/fr/es/it/nl, .eu/.uk/.de/.fr/.es/.it/.nl TLD, GBP/EUR currency, EU CDN, GDPR cookie banner

- GDPR full compliance (DPO contact + DSAR flow + right-to-erasure UX)
- UK GDPR / DPA 2018 (ICO registration number ZA-prefix in footer; UK representative for non-UK controllers Art. 27)
- Consent Mode v2 quality (already #32 always-on — bundle adds the EU-specific UOOS check)
- EU-US Data Privacy Framework (DPF) active certification (already #64 always-on)
- EAA / WCAG 2.2 AA conformance + accessibility statement + VPAT (already #42 always-on — bundle adds the €100k EU-penalty disclosure)
- EU AI Act Article 50 readiness (already #37 always-on — bundle adds Article 13/14 high-risk classification check)
- Sub-processor page transparency / DPA self-serve (already #59 always-on — bundle adds GDPR Art. 28 DPA depth)

### Geo Bundle 2: Canada-Quebec Law 25
Triggers on: .ca TLD, fr-CA hreflang, CAD currency, PIPEDA mention

- French-language privacy notice (mandatory for QC traffic)
- "Personne responsable" disclosure (mandatory)
- Automated-decision opt-out
- Privacy-by-default signals

### Geo Bundle 3: Brazil LGPD
Triggers on: .com.br TLD, pt-BR hreflang, BRL currency, Portuguese content

- Encarregado (DPO equivalent) name + email mandatory
- ANPD complaint-channel pointer
- Portuguese-language version for .com.br traffic

### Geo Bundle 4: South Africa POPIA
Triggers on: .za TLD, ZAR currency, SA business address

- Information Officer registered with Information Regulator + name disclosed
- PAIA manual link in footer (legally required)

### Geo Bundle 5: China PIPL
Triggers on: .cn TLD, zh-CN hreflang, CNY currency, ICP 备案 license

- ICP license number in footer (mandatory for any .cn presence)
- Cross-border transfer mechanism named (CAC standard contract / certification / security assessment)
- Separate consent for sensitive data categories
- Local representative for foreign processors

### Geo Bundle 6: Switzerland nFADP
Triggers on: .ch TLD, CHF currency, German/French/Italian hreflang

- Swiss representative named for non-CH controllers
- Explicit "revFADP" / "nFADP" reference

### Geo Bundle 7: Japan APPI
Triggers on: .jp/.co.jp TLD, ja hreflang, JPY currency, Japanese content

- 個人情報保護方針 header
- Designated representative if no JP entity
- Cross-border transfer opt-out
- CPO (Chief Privacy Officer) disclosure

### Geo Bundle 8: South Korea PIPA
Triggers on: .kr TLD, ko hreflang, KRW currency, Korean content

- Required separate consent checkboxes (필수 required vs 선택 optional)
- CPO mandatory disclosure (name + email)
- Separate consent for sensitive personal info

### Geo Bundle 9: SEA Privacy (Singapore + Thailand + Vietnam + Philippines)
Triggers on: .sg/.th/.vn/.ph TLD, SGD/THB/VND/PHP currency, local language

- Singapore PDPA (DPO contact + DNC compliance + withdrawal-of-consent mechanism)
- Thailand PDPA (DPO for sensitive-data + consent banner in Thai for .th)
- Vietnam PDPD Decree 13/2023 (DPIA reference + MPS notification)
- Philippines DPA (NPC registration + DPO disclosed)

### Geo Bundle 10: MEA Privacy (UAE + Saudi + Israel)
Triggers on: .ae/.sa/.il TLD, AED/SAR/ILS currency

- UAE PDPL (Federal Decree 45/2021) — Data Office notification claim, controller identification
- Saudi PDPL — SDAIA registration, KSA-resident DPO for sensitive processors
- Israel Privacy Protection Law + 2024 Amendment 13 — Database registration number, expanded sensitive categories enumeration

### Excluded from geo bundles (intentional)

- **Australia Privacy Act 2026 reforms** — covered by statutory-tort signals in core lens U7
- **Argentina Ley 25.326 / Colombia Ley 1581** — auditable but typically lower signal; fold into "LATAM posture flag" as a single lens, not a bundle

### Interaction with vertical bundles

A prospect in healthcare operating in the UK fires the **healthcare vertical bundle** AND the **EU/UK regulatory geo bundle** — both on top of the 160 always-on lenses. Bundle activation is independent and additive.

### Operational impact

- **EU/UK geo bundle**: largest at 7 lenses, fires for ~50% of B2B SaaS prospects
- **Brazil / Quebec / China / Switzerland / Japan / Korea / SEA / MEA bundles**: 2-4 lenses each, fire for 5-20% of prospects each
- **Total geo-bundle lens count**: ~36 conditional lenses
- **Typical audit firing**: 0-2 geo bundles → 0-10 additional lenses

---

## Lenses to Deprecate or Down-weight

These items appear in legacy audit frameworks but research suggests low signal value or have been superseded:

- **llms.txt presence as a scored lens** — zero correlation with AI citations; 10% adoption, none in top-1k. Keep as hygiene flag, don't weight.
- **Meta-description character count / H1 count / title-tag length tables** — near-zero 2026 ranking correlation. Keep as health flag, don't weight.
- **SSL cert presence (binary)** — universal yes. Only flag absence.
- **Mobile-friendly binary** — universal yes in 2026. Only flag absence.
- **Social follower counts without engagement-rate context** — vanity metric.
- **Domain Authority / Moz DA as a scored number** — proprietary black box, noisy. Prefer referring-domains growth + topical relevance.
- **Generic SWOT per social network** (Sprout template) — performative, low-action.
- **"Do you have a blog?" / "Do you have a newsletter?"** presence-only checks — trivially yes for any prospect worth auditing.
- **Norton Secured / McAfee SECURE / TRUSTe-original badges** — all decommissioned 2019-2020; present-today = negative stale-trust-page signal.
- **ChatGPT plugins** — deprecated; GPTs replaced them; MCP is the real layer now.
- **Web3 / token-gated community / NFT loyalty** — vaporware for 99% of B2B SaaS unless prospect is crypto-native.
- **Engagement pods, comment marketing, coordinated amplification** — invisible to public signals; honest-flag rather than score.

---

## Lenses NOT publicly auditable (do NOT include)

Flagged here so reviewers don't suggest adding them:

- HIPAA BAA-tooled stack quality (vendor BAAs are private contracts; only inferable from vendor identity)
- DPIA / TIA completion (internal docs; only the *claim* is public)
- CCPA/CPRA training records
- GLBA "opt-out before sharing" actual sharing behavior
- TCPA "prior express written consent" records (only checkbox UX visible)
- FERPA school-official designation (contractual, not public)
- NIS2 incident reporting quality (regulator-only)
- MQL/SQL scoring thresholds and recalibration cadence
- Meta AEM 8-event priority ordering
- Enhanced-Conversions hashed-data upload configuration
- Engagement-score decay rules
- MRR-based cancel-flow routing thresholds (only the visible UX, not the routing logic)
- Smart-retry / card-updater enrollment (dunning internals)
- ESP flow content beyond what fake-signup reveals
- Real win rates / conversion rates / funnel metrics
- Internal viral mechanics / in-app A/B test inventory
- Actual ad spend dollars (only spend-intensity proxies)
- NPS scores (rarely public)
- Sales playbook contents
- Email flow content beyond observable from disposable inbox

---

## Sources

### Marketing-skills repo (38 SKILL.md files)
ab-test-setup · ad-creative · ai-seo · analytics-tracking · aso-audit · churn-prevention · cold-email · community-marketing · competitor-alternatives · competitor-profiling · content-strategy · copy-editing · copywriting · customer-research · directory-submissions · email-sequence · form-cro · free-tool-strategy · launch-strategy · lead-magnets · marketing-ideas · marketing-psychology · onboarding-cro · page-cro · paid-ads · paywall-upgrade-cro · popup-cro · pricing-strategy · product-marketing-context · programmatic-seo · referral-program · revops · sales-enablement · schema-markup · seo-audit · signup-flow-cro · site-architecture · social-content

### Established frameworks
- HubSpot Website Grader · SEMrush Site Audit (140+ checks) · Ahrefs Site Audit (170+ issues) · Moz DA/PA/Spam · Conversion Factory · Demand Curve · NoGood · Wpromote · Tinuiti · Single Grain · KlientBoost · PipelineRoad · Kotler 6-axis · McKinsey marketing-effectiveness · Bain marketing audit · AARRR (Pirate Metrics) · Reforge growth audit / Growth Loops · Forrester B2B Marketing Maturity (5 competencies) · Gartner Website Maturity Model (5 dimensions) · Aaker brand · Keller CBBE pyramid · BAV (Y&R Brand Asset Valuator) · SimilarWeb marketing channels · Sprout Social audit · Wappalyzer · BuiltWith · Siteimprove

### Emerging 2025-2026 dimensions
- LLMs.txt adoption research (Rankability, SERanking) · Cloudflare AI-crawler analysis · Anthropic Claude bots policy · State of Agent Discovery Q1 2026 · A2A Agent Discovery spec · MCP Adoption 2026 (Knak) · Profound vs Peec vs Otterly · Server-Side Tracking 2026 · Google Consent Mode v2 in 2026 · Google Analytics ad-data authority change June 2026 · EU AI Act Article 50 · EU Code of Practice on AI-generated content · European Accessibility Act 2026 · US State Privacy Law Tracker 2026 · ChatGPT Shopping product-feed · Agentic Commerce Protocols (ACP/UCP) · Schema markup for AI citations · Apple MPP impact 2026 · Reddit as B2B channel 2026 · LinkedIn newsletter strategy 2026 · Best intent-data providers 2026 · Retail Media Networks 2026 · Best AI SDR tools 2026 · Dark Social & Attribution 2026 · Self-Reported Attribution 2026 · Google Meridian MMM

### Compliance + regulatory sources
- HHS OCR online tracking guidance · HIPAA Journal · SEC Dec 2025 Marketing Rule Risk Alert · 17 CFR 275.206(4)-1 · FINRA social media · NMLS / SAFE Act advertising guide · Florida Bar 2025 lawyer advertising handbook · ABA law firm marketing 2025 · ADA lawsuit 2025 mid-year report · FTC AccessiBe $1M settlement context · GuideStar transparency contribution lift · EdTech FERPA/COPPA compliance checklist · Multi-state privacy law tracker · Quebec Law 25 · Switzerland nFADP · APAC privacy law trackers

### Vertical / industry sources
- Amazon Brand Registry & A+ Content · Marketplace liquidity (Reforge / Point Nine) · GBP multi-location audit (ALM) · IDX vs MLS real estate SEO · Reserve with Google · InfluenceFlow creator earnings 2026 · Stripe payment localization · Climate trust marks · Shopify DTC PDP/CRO audit · The Culture Edit employer brand audit

### Channel sophistication sources
- TikTok Creative Center / Symphony / Spark Ads docs · Amazon AMC partner directory · Apple Search Ads Reporting API · Walmart TradeDesk / Roundel display extensions · Spotify Megaphone / SPAN · LinkedIn Ad Library / Wire Program · Google Performance Max best practices 2026 · Reddit Conversation Placement docs · Pinterest Premiere Spotlight · Discord Onboarding / Stage docs · Substack Notes / Recommendations · Shield Analytics (LinkedIn Newsletter) · Listen Notes / Podchaser / Podscan
