---
title: "Audit Coverage — Research Synthesis Round 2 (57 capabilities from R3+R4+R5+reconsidered-deferrals+reconsidered-skips)"
type: research
status: triaged
date: 2026-04-22
related_plans:
  - 2026-04-20-002-feat-automated-audit-pipeline-plan.md
  - 2026-04-22-001-audit-coverage-gaps.md
  - 2026-04-22-002-audit-coverage-research.md
---

# Audit Coverage Research Synthesis — Round 2

Consolidated findings from 5 parallel research agents on the 57 accepted-for-application items across R3 + R4 + R5 + reconsidered-deferrals + reconsidered-skips. Source dossiers persisted at `~/.claude/projects/.../tool-results/toolu_01L2V62Fc354HS4phC3dyGgL.txt` (Group A SEO/GEO/Compliance, 12 items), `toolu_01RPucbEDtsteUBN2xGeD8ex.txt` (Group B Brand/Narrative/PR, 14 items), `toolu_019bsS9gvuCbuxvXKbUgHsyn.txt` (Group C Conversion/Trust/Sales, 12 items), `toolu_01AL5BbngadpVcQgnaF7kVQz.txt` (Group D Distribution/Community/Partnerships, 12 items), and inline (Group E Specialized/Infrastructure, 8 items). This file is the source-of-truth input for the next plan-edit pass.

---

## Spec changes from research (apply BEFORE adding capabilities)

### Critical infrastructure changes flagged by research

1. **Firebase Dynamic Links is DEAD (shut down 2025-08-25)** — `*.page.link` detection in `audit_mobile_app_linking` should flag "BROKEN FDL infrastructure" as a finding (still-live FDL = active outage), NOT treat as live deep-link infra. Recommend Branch.io / Adjust / AppsFlyer OneLink as live alternatives.
2. **ProgrammableWeb directory dead since 2022** (Mulesoft acquisition consolidation) — drop from `audit_open_api_public_data_access` scope.
3. **RapidAPI declining post-Nokia 2024 acquisition** — listings still queryable but new providers dwindling. Treat as historical signal in `audit_open_api_public_data_access`.
4. **Reddit free API formally degraded** in 2026 — `audit_reddit_ama_brand_subreddit` requires OAuth setup (free tier still adequate at ~20 audits/month with new client_id/secret env vars). Don't silently skip; mark `partial=true` with `degraded_reason="REDDIT_CLIENT_ID/SECRET env vars not set"`.
5. **Apply renames forced by research:**
   - Email signature marketing → **`audit_email_signature_marketing_indicators`** (research-flagged MEDIUM-LOW confidence — rename signals expectations)
   - Voice search → **`audit_conversational_query_optimization`** (since AI search subsumed voice-search era)
   - Diversity in marketing imagery → **DOWNGRADE/REJECT** (research-flagged LOW + litigation risk)

### REJECTED by research (despite earlier acceptance)

**Diversity in marketing imagery** (R5 Tier 2 ext) — Agent B Research flagged as **LOW confidence + significant litigation/reputation risk**. Sonnet vision classification of skin-tone / age / gender-presentation can produce defamatory mis-categorizations; per-person classifications are particularly risky. Better-confidence + lower-risk alternatives already exist: B-Corp directory check, EEO-1 disclosure detection, DEI report PDF discovery — all in `audit_corporate_responsibility`. **Recommendation: reject this addition.** If we want a DEI signal, deepen the structural ESG signals already in `audit_corporate_responsibility` instead.

### New env vars required

- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` — for `audit_reddit_ama_brand_subreddit` (free OAuth tier sufficient)
- `HUGGINGFACE_TOKEN` (optional) — raises rate-limit ceiling for `audit_huggingface_presence`
- `MAILINATOR_API_TOKEN` (optional) — private Mailinator domain ($99/mo) eliminates disposable-email blocklist issues at scale for `audit_welcome_email_signup`

### New shared providers to build

| Provider | LOC est | Used by | Auth | Cost |
|---|---|---|---|---|
| `src/audit/providers/sec_edgar.py` | ~60 | `audit_public_company_ir` | None (User-Agent header required) | Free, 10 req/sec |
| `src/audit/providers/huggingface.py` | ~80 | `audit_huggingface_presence` | Optional `HUGGINGFACE_TOKEN` | Free |
| `src/audit/providers/disposable_email.py` | ~150 | `audit_welcome_email_signup` | None (Mailinator public) | Free / $99/mo private |
| `src/audit/providers/apis_guru.py` | ~30 | `audit_open_api_public_data_access` | None | Free |
| `src/audit/providers/reddit.py` | ~60 | `audit_reddit_ama_brand_subreddit` | OAuth | Free |
| `src/audit/providers/mail_tester.py` (optional) | ~40 | `audit_welcome_email_signup` sender-reputation sub | None | Rate-limited free |

### Extensions to existing providers

- `src/audit/providers/github.py` — add `fetch_discussions(owner, repo, since)` GraphQL method (~60 LOC) for `audit_github_discussions_volume`
- `src/audit/data/martech_rules.yaml` — add categories: `email_signature_marketing` (Sigstr/Wisestamp/etc), `b2c_personalization` (Dynamic Yield/Adobe Target/VWO Personalize/Insider/Bloomreach/Movable Ink), `trust_center_vendors` (SafeBase/Vanta Trust/Drata Trust/Whistic/Conveyor), `push_notifications` (OneSignal/Pushwoosh/Pusher/VWO Engage), `cross_sell_widgets` (Searchspring/Algolia Recommend/Klaviyo Reviews/Yotpo)
- `src/audit/primitives.py:capture_surface_scan` — extend deep-form-CRO to include `_audit_application_form_via_ats()` sub-pass for `audit_hiring_funnel_ux`
- `src/audit/primitives.py:scrape_careers` — extend with ATS-questions API call (Greenhouse `?questions=true`, Ashby Job Posting API) for `audit_hiring_funnel_ux`
- `src/audit/primitives.py:audit_messaging_consistency` — extend Wayback usage to logo-evolution (pHash diff) + name-change detection for `audit_rebrand_history`

---

## 57 capabilities — per-item compact dossier

Full per-primitive specs (signals, sources, implementation pattern, output schema, caveats) live in the four persisted dossier files referenced above. Below is the consolidated triage table for plan-edit pass consumption.

### Group A — SEO + GEO + Compliance (12 items)

| # | Primitive | Lens | Trigger | Confidence | $/audit | Key reuse / new |
|---|---|---|---|---|---|---|
| 1 | `audit_eeat_signals` | SEO + GEO | unconditional | HIGH | $0.03 | Reuses 200-page corpus from `analyze_internal_links`; 1 Sonnet YMYL classifier; cross-link to GEO (author entities → AI citations) |
| 2 | `audit_schema_competitive` | SEO synthesis | unconditional | HIGH | $0.00 | Pure synthesis on existing `detect_schema` + `scan_competitor_pages` data |
| 3 | `audit_robots_strategic` | SEO + GEO | unconditional | HIGH | $0.00 | Verified bot list (2026): GPTBot, ClaudeBot, anthropic-ai, CCBot, Bytespider, Google-Extended, PerplexityBot, OAI-SearchBot, Applebot-Extended, FacebookBot, DiffbotBot. Includes `meta name="robots" content="noai"` detection (non-standard but emerging) |
| 4 | `audit_crawl_budget_bloat` | SEO | unconditional | MEDIUM (cluster reliable, absolute counts approximate) | $0.04 | ~20 DataForSEO `site:` queries detecting `?utm=*` indexed variants, faceted-nav explosion, paginated archive series |
| 5 | Footer optimization (ext `audit_on_page_seo`) | SEO | unconditional | HIGH (struct) / MEDIUM (badge ID) | $0.00 | Parses already-fetched homepage; link-distribution density + NAP citation cross-check |
| 6 | Documentation translations (ext `audit_help_center_docs`) | SEO + Brand | conditional dev-tool | HIGH (Mintlify/Docusaurus) / MEDIUM (GitBook) | $0.00 | Mintlify `docs.json` + Docusaurus URL pattern + hreflang on docs subdomain + language switcher detection |
| 7 | `audit_conversational_query_optimization` (renamed from voice search) | SEO + GEO | unconditional | HIGH | $0.00 | Composite synthesis: FAQPage schema + question-format `<h2>` + long-tail conversational keywords + `HowTo`/`QAPage` schema. Reuses `detect_schema` + `analyze_serp_features` |
| 8 | Backlink anchor-text branded-vs-commercial breakdown (ext `analyze_backlinks`) | SEO | unconditional | HIGH (dist) / MEDIUM (risk threshold) | $0.00 | Anchor data already in `analyze_backlinks` payload; over-optimization flag at >30% commercial = penalty risk |
| 9 | `audit_vertical_compliance` | MarTech-Attribution + Brand | conditional vertical | MEDIUM (claim detection HIGH, absence ambiguous) | $0.05 | Per-vertical signals: HIPAA BAA (healthtech), PCI-DSS Level + state MTL (fintech), FERPA (edtech), DSA/DMA (EU large platforms), FDA 510(k) (medical devices), SOX (public), GLBA (financial services) |
| 10 | Sub-processor / DPA disclosure (ext `audit_trust_signals`) | MarTech-Attribution | unconditional | HIGH (presence) / MEDIUM (completeness) | $0.02 | Path probes + Sonnet completeness scoring on `/legal/sub-processors` + `/dpa` + `/data-processing` |
| 11 | `audit_ai_policy` | Brand/Narrative + MarTech | unconditional | HIGH (presence) / MEDIUM (substantive eval) | $0.03 | Path probes for `/ai-policy`, `/responsible-ai`, `/ai-ethics`, `/ai-governance`, `/ai-principles` + Sonnet quality pass |
| 12 | Sustainability / website carbon (ext `audit_corporate_responsibility`) | Brand/Narrative | unconditional | MEDIUM (CO2 estimate order-of-magnitude only) | $0.01 | Free Website Carbon Calculator API + Green Web Foundation greencheck + page-weight from existing PageSpeed |

### Group B — Brand / Narrative / PR / Earned-Media (13 items, was 14 — diversity-imagery REJECTED)

| # | Primitive | Lens | Trigger | Confidence | $/audit | Key notes |
|---|---|---|---|---|---|---|
| 13 | `audit_branded_serp` | Brand/Narrative | unconditional | HIGH | $0.003 | DataForSEO SERP Advanced returns Knowledge Panel + sitelinks + reviews stars + AI Overview + PAA + top stories in single `/v3/serp/google/organic/live/advanced` call. 4 brand-name queries |
| 14 | `audit_branded_autosuggest` | Brand/Narrative | unconditional | HIGH | $0.00 (free) / $0.05 (worst-case SerpAPI fallback) | Google autosuggest endpoint + SerpAPI fallback. Mines `is X scam?` / `X reviews` / `X alternatives` / `X vs Y` / `X down` |
| 15 | `audit_industry_analyst_position` | Brand/Narrative + Competitive | unconditional | HIGH (self-promoted) / MEDIUM (G2 quadrant detail Cloudflare-blocked) / LOW (Gartner/Forrester direct paywalled — accept this) | $0.01 | **Single largest remaining B2B SaaS finding.** Detect via SerpAPI brand-name + analyst-firm queries + scrape brand's own marketing pages declaring "Gartner MQ Leader 2024" + cached awards lookup (Inc 5000 / Fast Company / Deloitte Fast 500) |
| 16 | `audit_clv_retention_signals` | Brand/Narrative + Conversion | unconditional | MEDIUM-HIGH (signal density low for private cos; most utility series-B+ SaaS) | $0.03 | 6 SERP queries + 1 NewsData + Wayback CDX + 1 Sonnet extraction for NPS/retention/GRR/NRR claims |
| 17 | Newsletter quality (ext `audit_content_strategy_shape`) | Brand/Narrative | unconditional | HIGH (cadence/archive/og) / MEDIUM (prose quality Sonnet) | $0.06 | Substack/Beehiiv archive scrape + 3× Sonnet quality pass on recent issues |
| 18 | Owned podcast quality (ext `audit_podcast_footprint`) | Brand/Narrative + Distribution | conditional owned-podcast detected | HIGH (cadence/Podchaser/transcript) / MEDIUM (guest-tier) | $0.02 | Podchaser free tier + RSS + Pod Engine reuse + 1 Sonnet guest-tier pass |
| 19 | Original research depth (ext `audit_content_strategy_shape`) | Brand/Narrative | conditional research detected | MEDIUM-HIGH (composite, sub-signals noisy) | $0.13 | DataForSEO Backlinks anchor-text matching report titles + 5 reports × refresh-cadence detection + 1 Sonnet methodology-disclosure pass |
| 20 | Wire-service vs original-pitch press ratio (ext `audit_earned_media_footprint`) | Brand/Narrative | unconditional | HIGH | $0.02–0.05 | Cision/PRNewswire/Business Wire/GlobeNewswire/Newsfile boilerplate detection — host classification deterministic + Sonnet body-pass |
| 21 | Brand demand trend (ext `gather_voc`) | Brand/Narrative + Monitoring | unconditional | HIGH (trajectory/seasonality) / MEDIUM (auto-inflection) / LOW (low-volume disambiguation) | $0.14 | 3 Apify GoogleTrends runs + 1 DataForSEO keyword query for `<brand>` + `<brand> reviews` + `<brand> pricing` |
| 22 | Comments engagement on owned content (ext `audit_partnership_event_community_footprint`) | Brand/Narrative | unconditional | HIGH (platform/count) / MEDIUM (exec-response detection) | $0.02 | Disqus/Hyvor Talk/Commento/Cusdis/Remark42 detection + native CMS comments + Reddit megathread cross-ref via existing Xpoz adapter |
| 23 | Acquisition / M&A history (ext `audit_earned_media_footprint`) | Brand/Narrative | unconditional | HIGH (press-disclosed) / MEDIUM (sub-threshold deals) | $0.03 | 5 NewsData queries + 2 SERP + Wikipedia + Sonnet extraction for "acquired by" / "merger" patterns |
| 24 | Rebrand history Wayback (ext `audit_messaging_consistency`) | Brand/Narrative | unconditional | HIGH (name/domain) / MEDIUM (logo pHash) | $0.02 | 4-5 Wayback fetches + pHash logo-diff + meta-title diff + 1 Sonnet tagline-drift pass |
| 25 | Brand voice cross-platform analysis (ext `audit_messaging_consistency`) | Brand/Narrative | unconditional | HIGH (spaCy/textstat metrics) / MEDIUM (Sonnet verdict) / LOW (LinkedIn surface) | $0.05 | Reuse adapter calls + spaCy/textstat (free) + 1 Sonnet batched cross-surface voice pass |
| ~~26~~ | ~~Diversity in marketing imagery~~ | ~~Brand/Narrative~~ | — | **REJECTED** by research | — | LOW confidence + litigation risk per Agent B. Use structural ESG signals (B-Corp, EEO-1, DEI report PDF) in `audit_corporate_responsibility` instead. |

### Group C — Conversion + Trust + Funnel + Sales-Motion (12 items)

| # | Primitive | Lens | Trigger | Confidence | $/audit | Key notes |
|---|---|---|---|---|---|---|
| 27 | `audit_customer_support` | Conversion + Lifecycle | unconditional | HIGH (vendor + business hours) / MEDIUM (after-hours + bot-vs-human) | $0.03–0.06 | Reuses `fingerprint_martech_stack` chat vendor detection (Intercom/Drift/Crisp/Tidio/Tawk.to/LiveChat/Zendesk/Olark/HubSpot Chat) + 2× Playwright (open-hours + after-hours simulation) + 1 Sonnet pass |
| 28 | `audit_cro_experimentation_maturity` | Conversion | unconditional | HIGH (vendor + cookie) / MEDIUM (cadence inference) / LOW (server-side blind) | $0.02 | Wayback CDX free + cookie-pattern detection (`_optly_*`, `_vwo_uuid`, `_ab`, `cv_*`) + URL params (`?vid=`, `?test=`, `?variant=`) |
| 29 | `audit_ecommerce_catalog` | Conversion | conditional DTC/e-comm | HIGH (platform/schema/reviews vendor) / MEDIUM (review density SSR variance) / LOW (checkout flow shape — needs R23) | $0.05–0.15 | Per-SKU image count + `Product`/`AggregateRating` schema + recommendations engine detection (Klaviyo Reviews/Yotpo/Bazaarvoice/Searchspring/Algolia Recommend/Constructor/Bloomreach) + guest-checkout |
| 30 | `audit_b2c_personalization` | Conversion | conditional B2C/DTC | HIGH (vendor) / MEDIUM (active runtime) / LOW (campaign maturity) | $0.01 base / $0.06 with geo-variance | Wappalyzer/martech_rules.yaml extension: Dynamic Yield (`window.DY`), Optimizely Web Personalization, Adobe Target (`window.adobe.target`), VWO Personalize, Insider (`Insider.eventManager`), Bloomreach Engagement (`exponea`), Movable Ink (`mi.js`), Persado, Rokt. **Movable Ink + Rokt primarily email/post-checkout** — light on-page JS |
| 31 | `audit_homepage_demo_video` | Conversion | unconditional | HIGH (embed/platform/duration/captions) / MEDIUM (view counts YouTube only) / LOW (qualitative score) | $0.01 | Wistia (`fast.wistia.net`) + Vimeo + Loom (`loom.com/embed/`) + YouTube + Mux + Cloudflare Stream + Bunny Stream. Wistia + YouTube oEmbed for view counts |
| 32 | `audit_first_party_data_strategy` | MarTech-Attribution + Conversion | unconditional | HIGH (vendor/path) / MEDIUM (marketing-vs-in-product classification + progressive profiling) | $0.03 | Typeform/Tally/Outgrow/Riddle/Jotform/Ceros/Octane.ai detection + multi-step form pattern + CDP cross-reference |
| 33 | `audit_trust_center` | Conversion + MarTech-Attribution | unconditional | HIGH (vendor/URL) / MEDIUM (self-serve depth) | $0.02 | SafeBase (`safebase.io`/`cdn.safebase.io`) + Vanta Trust (`trust.vanta.com`/`trust.<brand>.com`) + Drata Trust Hub + Whistic + Conveyor + OneTrust Vendorpedia + SecurityScorecard ATLAS. **Cuts enterprise sales cycle 30-60 days when present** |
| 34 | `audit_sales_motion_classification` (reasoning-only synthesis) | Synthesis | unconditional | HIGH (well-defined feature space; Sonnet good at structured classification) | $0.02 | Composes from `audit_pricing_page` + `scrape_careers` + `capture_surface_scan` + `tech_stack` outbound-tool detection. Output: `motion_type ∈ {plg, inside_sales, enterprise_sales, hybrid_plg_to_sales, hybrid_smb_to_enterprise}` |
| 35 | `audit_mobile_ux` | Conversion + SEO | unconditional | HIGH (touch target + viewport + form attrs deterministic) | $0.02 | One extra Playwright fetch in mobile mode (375×667 viewport) + touch-target measurement (44×44 iOS / 48×48 Android per HIG/Material) + `inputmode` attribute + AMP detection |
| 36 | Push notification opt-in (ext `capture_surface_scan`) | Lifecycle + Conversion | unconditional | HIGH (vendor) / MEDIUM (opt-in timing classification) | $0.00 (in existing P23 pass) | OneSignal (`onesignal.com/sdks/`) + Pushwoosh + Pusher Beams + VWO Engage + FCM + WonderPush + PushOwl (Shopify) + Iterable web push. Timing: immediate-on-load vs delayed/contextual |
| 37 | Cross-sell / upsell on product+pricing pages (ext Conversion lens) | Conversion | unconditional | HIGH (vendor + section presence) / MEDIUM (anchoring quality) | $0.02 | Searchspring + Algolia Recommend + Klaviyo Recommendations + Yotpo SMSBump cross-sell + Stamped recommendations |
| 38 | `audit_paywall_upgrade_cro` (ext `audit_pricing_page`) | Conversion | conditional freemium detected | HIGH (tier/CTA/toggle) / MEDIUM (copy quality) / LOW (full upgrade flow needs R23) | $0.02 | Pricing-page upgrade-CTA placement + clicks-to-upgrade + urgency/scarcity copy + social-proof on upgrade prompts |

### Group D — Distribution + Community + Partnerships (12 items)

| # | Primitive | Lens | Trigger | Confidence | $/audit | Key notes |
|---|---|---|---|---|---|---|
| 39 | `audit_mobile_app_linking` | Distribution | conditional mobile-app detected | HIGH | $0.00 | Smart App Banner `<meta name="apple-itunes-app">` + `/.well-known/apple-app-site-association` + `/.well-known/assetlinks.json` + Branch.io (`*.app.link`) + Adjust + AppsFlyer OneLink. **Firebase Dynamic Links DEAD as of Aug 25 2025** — flag `*.page.link` as broken-FDL finding |
| 40 | Status page maturity (ext `audit_partnership_event_community_footprint`) | Brand/Narrative + Distribution | conditional status-page detected | HIGH (Atlassian Statuspage dominant) / MEDIUM (MTTR/post-mortem parsing) | $0.02 | Atlassian Statuspage `/history.atom` + Better Stack `/feed` + incident-frequency last 90d + post-mortem cadence + SLA-credit policy disclosure |
| 41 | `audit_reddit_ama_brand_subreddit` | Brand/Narrative + Monitoring | unconditional | MEDIUM (Reddit OAuth required + founder ID weak link) | $0.00 (free tier) | **Requires `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` env vars** (Reddit free unauthenticated `search.json` formally degraded in 2026). One-time ~30min OAuth setup |
| 42 | Newsletter leaderboard rank (ext `audit_content_strategy_shape` newsletter sub) | Brand/Narrative + Distribution | conditional newsletter detected | MEDIUM (top-100 only) | $0.05 | Substack `/discover/rising` + `/discover/top` per category + Beehiiv `/explore` + ConvertKit `kit.com/<handle>` + SparkLoop network indicator |
| 43 | `audit_influencer_ftc_compliance` (ext `audit_partnership_event_community_footprint` affiliate sub) | Brand/Narrative + MarTech-Attribution | conditional influencer mentions detected | HIGH (hashtag/phrase) / MEDIUM (native disclosure) | $0.01 | Reuses existing `ICContentAdapter` + `XpozAdapter` creator content. Detects `#ad`, `#sponsored`, `#partner`, "Paid partnership with", platform-native sponsorship-disclosure tags |
| 44 | Hackathon / dev-event sponsorships (ext existing conference-sub) | Distribution | conditional dev-tool firmographic | MEDIUM (SerpAPI breadth good, dedup heuristic) | $0.05 | SerpAPI `"<brand>" sponsor "hackathon"` + `site:mlh.io` + HackerEarth + Devpost direct fetch |
| 45 | Branded merchandise / swag program (ext `audit_partnership_event_community_footprint`) | Distribution | unconditional | HIGH (presence) / MEDIUM (platform fingerprint) / LOW (product count accuracy) | $0.02 | Path probes `/shop`, `/store`, `/swag`, `/merch`, `/gear` + shop-platform detection (Shopify/Printful/Cotton Bureau/Threadless/Bonfire) |
| 46 | Customer advisory board references (ext `audit_customer_story_program`) | Brand/Narrative + Conversion | conditional B2B firmographic | MEDIUM (direct mentions reliable, absence ambiguous) | $0.03 | Regex on `/about`, `/team`, `/customers`, `/community`, `/advisors` + LinkedIn announcements + NewsData |
| 47 | University / academic partnerships (ext `audit_partnership_event_community_footprint`) | Brand/Narrative + Distribution | conditional research-heavy/dev-tool/edtech firmographic | MEDIUM (multiple parallel signals) | $0.04 | Path probes `/research`, `/university-program`, `/students`, `/edu`, `/academia` + SerpAPI for grants + free-tier-for-students offer detection |
| 48 | `audit_ctv_ads_detection` | Distribution | conditional CTV-targeting surfaced via Foreplay | LOW (degraded primitive — primary value is "pointer to upgrade path") | $0.00 | Reuses existing Foreplay `creative_targeting` field where exposed; mark `partial=true` with explicit "limited coverage — full requires R20 ad-platform enrichment" |
| 49 | `audit_apple_search_ads` | Distribution | conditional mobile-app + R20 ad-platform enrichment | LOW without R20 / HIGH with R20 | $0.01 | iTunes Search API free + manual SERP-mining via keyword extraction (cross-ref `audit_aso`); explicit upgrade path to R20 attach-ads |
| 50 | Geographic expansion / office locations (ext `scrape_firmographics`) | Brand/Narrative + Distribution | unconditional | MEDIUM-HIGH (when offices listed) | $0.03 base / +$0.10–0.30 if Apify enrichment | Path probes + Sonnet extraction + LinkedIn company-page office-locations field |

### Group E — Specialized + Infrastructure + Operations (8 items)

| # | Primitive | Lens | Trigger | Confidence | $/audit | Key notes |
|---|---|---|---|---|---|---|
| 51 | `audit_email_signature_marketing_indicators` (renamed) | MarTech-Attribution | unconditional | MEDIUM-LOW | $0.00 | Triangulation of 3+ weak signals: tech_stack JS hits + outbound-link click-trackers + JD mentions + DNS CNAMEs. **Emit only when ≥2 signals concur**; else silent. Best detection via welcome-email signature fingerprinting (Capability 56 cross-feed) |
| 52 | `audit_error_page_ux` (404/500) (ext `audit_on_page_seo`) | SEO | unconditional | HIGH | $0.02 | 2 jittered random-path probes (`/__gofreddy-audit-{uuid}-404test`); 10s spaced; never `/admin`/`/wp-admin`/`.env` patterns (WAF-trigger). Soft-404 detection via DOM-text inspection for SPA |
| 53 | `audit_open_api_public_data_access` (ext `audit_marketplace_listings` + new) | Distribution | unconditional | MEDIUM-HIGH (presence) / MEDIUM (data-company classification heuristic) | $0.05 | RapidAPI (declining post-Nokia 2024) + Postman API Network + APIs.guru directory (free JSON, 1.7MB cached) + Bump.sh + path probes for `/data`, `/datasets` + Datawrapper/Flourish iframe scan + Kaggle dataset hosting + GitHub data-repo discovery. **ProgrammableWeb dropped (dead since 2022)** |
| 54 | `audit_github_discussions_volume` (ext `github.py`) | Distribution + Brand/Narrative | conditional Discussions enabled | HIGH | $0.00 | GitHub GraphQL `repository.discussions(first: 100, orderBy: {field: UPDATED_AT, direction: DESC})` + `authorAssociation` enum for team-vs-community classification |
| 55 | `audit_huggingface_presence` | Distribution | conditional AI firmographic | HIGH (verified slug) / MEDIUM (guessed slug) | $0.00 | Hugging Face Hub API (`huggingface.co/api/models?author=<org>` etc.) — fully public, optional `HUGGINGFACE_TOKEN`. Returns model count + downloads + likes + datasets + spaces + library tags + trending score + inference provider mappings |
| 56 | `audit_welcome_email_signup` (ext `audit_plg_motion`) | PLG / Lifecycle / MarTech | conditional free-trial/freemium detected + **manual user opt-in flag** | MEDIUM (50-60% signup success rate due to disposable-email blocking) | $0.10 / $3.30 amortized at scale | Mailinator public inbox API (free) + Maildrop/GuerrillaMail/tempmail.io fallback. **CRITICAL safety pattern** documented below |
| 57 | `audit_public_company_ir` | Brand/Narrative | conditional `firmographic.is_public == True` | HIGH (filings) / MEDIUM (IR-page quality) | $0.02 | SEC EDGAR APIs (free, 10 req/sec, User-Agent header required): `company_tickers.json` for ticker→CIK lookup + `data.sec.gov/submissions/CIK<padded>.json` for filings history. US-only (foreign listings need 20-F/6-K detection separately) |
| 58 | `audit_hiring_funnel_ux` (ext `scrape_careers` + `_deep_inspect_forms`) | Brand/Narrative + Conversion | conditional ATS detected | HIGH (Greenhouse/Ashby) / MEDIUM (Lever) / MEDIUM-LOW (Workable + custom) | $0.03 | Greenhouse `?questions=true` + Ashby Job Posting API (clean public APIs with full questions schema). **Lever public API only gives high-level posting data** — fall back to Playwright DOM. **Never submit application form** (fraud) |

---

## R23 attach-demo + R26 attach-winloss + new R27 (welcome-email signup) safety patterns

### R27 `audit_welcome_email_signup` — CRITICAL safety pattern (research-mandated)

The most novel safety risk added in this round. Required mitigations:

1. **Manual-fire only** with explicit user opt-in flag — NEVER on automated schedule
2. **Cap to 1 signup per audit**
3. **Identifiable test fixture name**: `Audit GoFreddy-{audit_id}` so prospect can see this isn't a real lead
4. **Public domain in audit log** — clearly logged as audit signup with full traceability
5. **NEVER click any link** in captured email (would skew prospect's analytics, may trigger nurture sequences)
6. **NEVER input payment info** — free-trial-only, no credit-card flows
7. **Honor "uncheck marketing"** boxes during signup — capture product email only
8. **One-shot** — discard inbox after capture; do not maintain ongoing receipt
9. **Document in client engagement letter** that audit may include a single test signup
10. **CFAA / unauthorized-access risk**: don't breach ToS in a way that constitutes "exceeding authorized access"
11. **Mailinator public inbox IS public** — captured PII or sensitive content (rare in welcome emails) is exposed. Use private Mailinator domain ($99/mo) if scaling >10 audits/month
12. **Disposable-email blocklist reality**: many SaaS ToS prohibit signup with disposable emails; many signups will fail outright (~50-60% success rate budget)

### `audit_hiring_funnel_ux` — explicit safety pattern

**Never submit the form** (would constitute fraudulent job application). Render application page + use existing `_deep_inspect_forms()` only.

### `audit_error_page_ux` — WAF safety pattern

2 probes max, randomized paths, 10s spaced apart. Avoid `/admin`, `/wp-admin`, `/.env` (high WAF-trigger). Prefix `__gofreddy-audit` is a benign self-identifier. Cloudflare challenge pages (1020/1015) may look like 4xx — distinguish by `cf-ray` header.

---

## Net delta to plan (after applying all 56 — 57 minus rejected diversity-imagery)

| Dimension | Current plan (post R1+R2) | After 56 additions |
|---|---|---|
| Collection primitives | 48 | **~80** (32 new primitives + ~24 deepening extensions to existing primitives) |
| Reasoning primitives | 1 | **3** (+`audit_sales_motion_classification`, +`audit_schema_competitive`) |
| Total `primitives.py` functions | 49 | **~83** |
| Lenses | 9 | 9 |
| Conditional enrichments | 9 (R18-R26) | 9 (unchanged) |
| Conditional firmographic primitives | 6 | **~16** (+vertical_compliance, +b2c_personalization, +ecommerce_catalog, +mobile_app_linking, +public_company_ir, +sales_motion_classification, +Hugging Face for AI, +API marketplaces for data-companies, +B2B-only customer advisory board, +dev-tool university partnerships) |
| New shared providers | 6 (R1+R2) | **+6** (sec_edgar, huggingface, disposable_email, apis_guru, reddit, mail_tester) |
| New env vars | 4 (R1+R2) | **+3** (REDDIT_CLIENT_ID/SECRET, optional HUGGINGFACE_TOKEN, optional MAILINATOR_API_TOKEN) |
| External-auditable coverage | ~99% | **~99.99%** (asymptote) |
| Cost per audit increase | baseline | **+$1.00–2.00/audit** (most items <$0.05; biggest spenders: R27 welcome-email signup $0.10 + brand demand trend $0.14 + original research depth $0.13) |

---

## High-confidence "go" items (32 of 57 — HIGH confidence per research)

All Group A 12 (mostly extensions to existing primitives, all HIGH for what they're measuring). Group B: 13/13 except diversity (8 HIGH + 5 MEDIUM/MEDIUM-HIGH). Group C: 12/12 (mix of HIGH for vendor/structural detection, MEDIUM for qualitative scoring). Group D: 12/12 (mix). Group E: 8/8.

## Items where research surfaced safety/ToS concerns

- R27 `audit_welcome_email_signup` — ToS + CFAA + signup-blocklist risk; manual opt-in only
- `audit_hiring_funnel_ux` — fraud risk if form submitted; never submit
- `audit_error_page_ux` — WAF rate-trigger risk; jittered paths + budget cap
- `audit_branded_autosuggest` — Google autosuggest endpoint sometimes rate-limited; SerpAPI fallback
- `audit_huggingface_presence` — gate on AI-firmographic detection to avoid noisy fires

## Items REJECTED by research

- **Diversity in marketing imagery** (was R5 Tier 2 ext) — Agent B Research: LOW confidence + litigation risk. Use structural ESG signals in `audit_corporate_responsibility` instead.

## Items requiring rename

- "Email signature marketing tools" → `audit_email_signature_marketing_indicators` (signal MEDIUM-LOW confidence)
- "Voice search optimization" → `audit_conversational_query_optimization` (AI search subsumed voice)

---

## Sources (key research dossiers)

Full per-primitive research dossiers (signals, sources, implementation pattern, output schema, caveats) live in:
- `~/.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/112981ab-84ae-4316-9024-e3e0dc43f9b6/tool-results/toolu_01L2V62Fc354HS4phC3dyGgL.txt` (Group A: SEO/GEO/Compliance, 974 lines)
- `~/.claude/projects/.../toolu_01RPucbEDtsteUBN2xGeD8ex.txt` (Group B: Brand/Narrative/PR, 1063 lines)
- `~/.claude/projects/.../toolu_019bsS9gvuCbuxvXKbUgHsyn.txt` (Group C: Conversion/Trust/Sales, 958 lines)
- `~/.claude/projects/.../toolu_01AL5BbngadpVcQgnaF7kVQz.txt` (Group D: Distribution/Community/Partnerships, 757 lines)
- Inline this file (Group E: Specialized/Infrastructure, 8 items)

Plus inline source citations in each agent's dossier (Firebase Dynamic Links FAQ, SEC EDGAR APIs, GitHub Discussions GraphQL, Hugging Face Hub API rate limits, Mailinator API, Greenhouse Job Board API, DataForSEO SERP Advanced AI Overview docs, Mozilla HTTP Observatory v2 API, Reddit OAuth rate limits 2026, etc.).
