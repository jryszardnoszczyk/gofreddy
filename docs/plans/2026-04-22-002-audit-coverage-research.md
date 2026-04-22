---
title: "Audit Coverage — Research Synthesis (34 capabilities)"
type: research
status: triaged
date: 2026-04-22
related_plan: 2026-04-20-002-feat-automated-audit-pipeline-plan.md
related_gap_doc: 2026-04-22-001-audit-coverage-gaps.md
---

# Audit Coverage Research Synthesis

Consolidated findings from 5 parallel research agents on the 34 proposed capabilities in `2026-04-22-001-audit-coverage-gaps.md`. Source dossiers live in agent transcripts; this file is the source-of-truth input for the plan-edit pass.

---

## Spec changes from research (apply these BEFORE adding capabilities)

1. **`audit_funnel_velocity_proxies` → rename to `audit_funnel_content_shape`** (per Agent 4). Cap severity at `low`, reframe as descriptive content/CTA shape — NOT a velocity/conversion claim. External proxies cannot honestly support velocity inference.
2. **`audit_form_cro_deep` is NOT a new primitive** — extend existing P23 `capture_surface_scan` with `_deep_inspect_forms()` sub-pass. Enriches existing `embedded_forms[]` schema. Net primitive delta unchanged.
3. **`SecurityHeaders.com` sunsetting April 2026 (Snyk acquisition)** — DO NOT integrate. Use Mozilla HTTP Observatory v2 (`https://observatory-api.mdn.mozilla.net/api/v2/scan`, free, no auth, 1 scan/host/min). Update Data Provider Inventory.
4. **`python-Wappalyzer` is unmaintained (chorsley fork)** — swap to `wappalyzer-next` (s0md3v fork, last update Jan 2026) in `pyproject.toml`.
5. **`textstat` is PyPI "Inactive"-flagged** — pin to `0.7.4`, document fallback to `py-readability-metrics`.
6. **Wikipedia ORES deprecated (Jan 2025)** — use Lift Wing API (`https://api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict`).
7. **Glassdoor API dead** (consolidated into Indeed July 2025). Glassdoor data only via Bright Data Cloudflare-bypass scraping (~$0.10–0.50/audit, 70–80% success). Indeed Company Pages become primary public source.

---

## New shared providers to build (consolidate, don't duplicate)

| Provider | LOC est | Used by | Auth | Cost |
|---|---|---|---|---|
| `src/audit/providers/github.py` | ~150 | audit_oss_footprint, audit_devex, audit_launch_cadence, audit_free_tools | `GITHUB_TOKEN` (5K req/hr authed) | Free |
| `src/audit/providers/producthunt.py` | ~80 | audit_directory_presence, audit_launch_cadence | `PRODUCT_HUNT_TOKEN` OAuth client-creds | Free (gray for commercial — email PH to confirm) |
| `src/audit/providers/crtsh.py` | ~30 | audit_free_tools (subdomain enum) | None | Free |
| `src/audit/providers/amo.py` | ~40 | audit_free_tools (Firefox AMO) | None | Free |
| `src/audit/providers/atlassian_marketplace.py` | ~40 | audit_marketplace_listings | None | Free |
| `src/audit/providers/wikipedia.py` | ~80 | audit_earned_media_footprint, audit_executive_visibility | Optional `WIKIMEDIA_API_KEY` for Lift Wing | Free |

Plus **extensions** (no new files):
- `src/seo/providers/dataforseo.py`: add `audit_hreflang()`, `business_data_gbp()`, `local_pack_serp()`, `serp_site_query()`
- `src/seo/providers/pagespeed.py`: add `category=accessibility` param (5 LOC)
- `fingerprint_martech_stack` (P25): extend `martech_rules.yaml` with categories `personalization`, `reverse_ip`, `intent_data`, `chat_intent`, `lms`, `consent_quality`, accessibility overlays, regional payment methods, docs platforms

**New env vars**: `GITHUB_TOKEN`, `PRODUCT_HUNT_TOKEN`, optional `WIKIMEDIA_API_KEY`. Bright Data and Apify already in env.

---

## Capability dossiers (34 items, grouped by lens)

### Group 1 — SEO + Site Quality (5 items)

| # | Primitive | Trigger | Confidence | $/audit | Key signal source |
|---|---|---|---|---|---|
| 1 | `audit_international_seo` | conditional (multi-locale) | HIGH | $0.07 | DataForSEO On-Page hreflang fields (already in API as of 2026 update) |
| 2 | `audit_local_seo` | conditional (local biz) | MEDIUM | $0.20 | DataForSEO Business Data GBP (no GBP API approval needed) + JSON-LD `sameAs[]` scrape; **BrightLocal NOT required for v1** — covers 80% of value free |
| 3 | `audit_accessibility` | unconditional | HIGH | $0.05 | PageSpeed `category=accessibility` (free, 25K/day) + axe-playwright-python; **flag accessibility overlays (UserWay/AccessiBe) as NEGATIVE signal** (ADA litigation risk) |
| 4 | `audit_help_center_docs` | conditional (SaaS, thin path for others) | HIGH | $0.10 | Path probes + DocSearch detection (Algolia DocSearch CDN script = strong investment signal) |
| 5 | `audit_pricing_page` + localization | unconditional | MEDIUM | $0.07 | Custom Playwright + 1 Cloro AI-pricing triangulation query; tier extraction needs Sonnet fallback (~70-80% regex extraction rate across diverse SaaS) |

**Group total**: ~$0.49/audit; zero new paid vendors required.

### Group 2 — Distribution + Listings (5 items)

| # | Primitive | Trigger | Confidence | $/audit | Key signal source |
|---|---|---|---|---|---|
| 6 | `audit_directory_presence` | unconditional + AI-firmographic subset | HIGH presence / MEDIUM quality | $0.15 | DataForSEO `site:` queries for G2/Capterra (presence-only — bot-blocked for detail), Product Hunt API, Apify for AlternativeTo/TAAFT/Futurepedia/CWS |
| 7 | `audit_marketplace_listings` | unconditional | HIGH presence / MEDIUM detail | $0.20 | Atlassian REST API (only platform with clean public API), DataForSEO `site:` for the rest (Zapier/Slack/AppExchange/AWS/HubSpot/Shopify/Notion/Stripe etc.) |
| 8 | `audit_launch_cadence` | unconditional | HIGH (PH+GitHub) / MEDIUM (changelog) | $0.05 | Product Hunt API + GitHub releases.atom + path probes for /changelog + RSS autodiscovery |
| 9 | `audit_free_tools` | unconditional | HIGH (subdomain+path) / MEDIUM (extension attribution) | $0.10 | crt.sh CT logs (free) for subdomain enum + path probes + Firefox AMO API + Apify for Chrome Web Store |
| 10 | `audit_oss_footprint` | conditional (dev-tool/tech firmographic) | HIGH (when org found) | ~$0 | GitHub REST + GraphQL (5K/hr authed). **Cross-link to GEO lens** — high-star repos heavily indexed by Claude/ChatGPT/Perplexity |

**Group total**: ~$0.50/audit; new env vars `GITHUB_TOKEN` + `PRODUCT_HUNT_TOKEN`.

### Group 3 — Brand / Narrative / Customer (9 items)

| # | Primitive | Trigger | Confidence | $/audit | Key signal source |
|---|---|---|---|---|---|
| 11 | `audit_customer_education` | unconditional | HIGH (vendor LMS) / MEDIUM (self-hosted) | $0.00–0.02 | Path probes + LMS Wappalyzer fingerprints (Thinkific, Teachable, Skilljar, Northpass, Disco, Docebo, LearnUpon, Mighty Networks) + DNS CNAME |
| 12 | `audit_public_roadmap` | unconditional | HIGH (vendor) / MEDIUM (transparency score) | $0.00–0.01 | DNS CNAME for Canny/Productboard/Frill/Featurebase/UserVoice + JS widget signatures |
| 13 | `audit_corporate_responsibility` | conditional (mid-market+; SMB false-negative trap) | MEDIUM | $0.05–0.10 | SerpAPI PDF discovery (`site: filetype:pdf "ESG report"`) + B-Corp directory lookup + accessibility overlay detection |
| 14 | `audit_customer_story_program` | unconditional | HIGH (count/format) / MEDIUM (outcome quality) | $0.10–0.30 | RenderedFetcher + Sonnet outcome-classifier + extend reviews adapters with G2/Capterra Apify scrapers |
| 15 | `audit_messaging_consistency` deepening (copy-quality) | unconditional | HIGH (readability/jargon) / MEDIUM (headlines) | $0.02 | textstat (pin 0.7.4) + spaCy + jargon corpus YAML + piggyback Sonnet on existing call. **CoSchedule API does NOT exist publicly** — build composite scoring locally |
| 16 | `audit_partnership_event_community_footprint` deepening | unconditional | HIGH (status/webinars) / MEDIUM (press kit) | $0.00–0.05 | Path probes for /press; status subdomain CNAME (statuspage.io/Better Stack/Instatus/sorryapp/Hund); webinar platform fingerprints (Goldcast/Hopin/Zoom/Riverside/Demio/On24/Livestorm/BigMarker) |
| 17 | `audit_earned_media_footprint` Wikipedia depth | unconditional | HIGH | $0.00 | MediaWiki Action API (free) + Wikimedia REST + Lift Wing for article-quality scoring (free with API key); reuse existing `pub_tier_dict.yaml` |
| 18 | `audit_executive_visibility` founder-led extension | conditional weighting (employee_count<50) | HIGH (owned providers) / LOW (LinkedIn) | $0.20–0.50 | Reuse Xpoz (founder X), PodEngine (transcript search) + Podchaser (structured guests), NewsData, IC, SerpAPI; **LinkedIn degrade gracefully — flag `linkedin_data_quality: limited`** |
| 19 | `audit_content_strategy_shape` extensions (newsletter + glossary) | unconditional | HIGH (glossary) / MEDIUM (newsletter — claims unverified) | $0.05–0.30 | Substack/Beehiiv direct HTML scrape (no public API); DataForSEO keyword lookup on top-25 glossary terms |

**Group total**: ~$0.45–1.30/audit; **textstat + spaCy + jargon corpus YAML** are net-new.

### Group 4 — Conversion / Trust / Funnel / ABM (4 items)

| # | Primitive | Trigger | Confidence | $/audit | Key signal source |
|---|---|---|---|---|---|
| 20 | `audit_trust_signals` | unconditional | HIGH | ~$0 | RenderedFetcher + Mozilla HTTP Observatory v2 (free, no auth) + reuse `fingerprint_martech_stack` consent category |
| 21 | `audit_form_cro_deep` (extends P23 capture_surface_scan) | unconditional | HIGH | ~$0 | Playwright form enumeration; HTML5 autocomplete compliance; CAPTCHA fingerprints (reCAPTCHA v2/v3, hCaptcha, Turnstile); honeypot heuristics |
| 22 | `audit_funnel_content_shape` (renamed from velocity proxies) | unconditional, severity ceiling=low | MEDIUM | $0.05–0.10 | Reuse `analyze_internal_links` page corpus + 1 Sonnet TOFU/MOFU/BOFU classifier on 50 sample blog URLs. **No velocity claims** — purely descriptive |
| 23 | `audit_abm_signals` | conditional (B2B enterprise) | HIGH (vendor detection) / MEDIUM (maturity tier) | ~$0 | Extend `fingerprint_martech_stack` ruleset with ABM categories — every vendor has documented stable JS signatures (Mutiny `client-registry.mutinycdn.com`, 6sense `j.6sc.co`, Demandbase `tag.demandbase.com`, Clearbit Reveal `js.clearbit.com`, RB2B, Albacross `_nQc`, Leadfeeder, etc.) |

**Group total**: ~$0.05–0.10/audit; mostly free.

### Group 5 — Specialized + Conditional Enrichments (8 items)

| # | Primitive | Trigger | Confidence | $/audit when triggered | Key signal source |
|---|---|---|---|---|---|
| 24 | `audit_plg_motion` | conditional (SaaS) | HIGH | $0.05 | RenderedFetcher + SerpAPI `"powered by <brand>"` for viral-loop detection + Sonnet motion classifier (pure_freemium / free_trial / reverse_trial / hybrid). **Reverse-trial detection added** (Verna/OpenView pattern) |
| 25 | `audit_devex` | conditional (dev-tool) | HIGH | $0.04 | Docs platform fingerprints (Mintlify/Stoplight/Redoc/Scalar = modern; raw Swagger UI = legacy); OpenAPI spec discovery; npm/PyPI for SDK freshness; GitHub for SDK coverage |
| 26 | `audit_aso` 6-dim + desktop | conditional (mobile-app) | HIGH (iOS/Android) / MEDIUM (Mac/Windows) | $0.30–0.80 | iTunes Search API (free) + existing AppStore/PlayStore Apify adapters cover all 6 dims. **AppFollow/data.ai NOT required** (only needed for top-100 keyword rank — out of scope) |
| 27 | `scrape_careers` employer-brand ext | always-on >50 employees | HIGH (ATS) / MEDIUM (LinkedIn) / LOW (Glassdoor) | $0.20 baseline / $0.70 with Glassdoor / $5 full LinkedIn enum | **ATS public APIs (Greenhouse/Lever/Ashby/Workable) all FREE** — primary path. **Pay-transparency compliance is the anchor finding** ("Acme posts 40 CA roles without salary ranges; $400K legal exposure"). LinkedIn via Apify ($0.05 page-only). Glassdoor via Bright Data ($0.10–0.50, 70-80% success) |
| 28 | R23 `attach-demo` | conditional enrichment | MEDIUM-HIGH | $2–5 | Playwright isolated context + Sonnet vision (Wes Bush Bowling Alley + Hulick + EUREKA frameworks). **Critical safety surface** — see safety pattern below |
| 29 | R24 `attach-budget` | conditional enrichment | HIGH | $0.05 | Pure CSV parse + benchmark table. **Cited 2025 sources**: Gartner CMO Spend Survey (7.7% revenue / 22.4% MarTech / 30.6% paid media), OpenView/High Alpha SaaS Benchmarks. Codify benchmarks in `src/audit/data/budget_benchmarks.yaml` |
| 30 | R25 `attach-crm` | conditional enrichment | HIGH | $0.10 | HubSpot CSV path = primary v1 (no OAuth complexity); pipeline velocity formula canonical. **2025 benchmarks**: win rate ~21%, sales cycle 84d median, ACV $26K median, velocity $8.2K/day SaaS median. Sources: First Page Sage, Drivetrain.ai, OpenView, ICONIQ |
| 31 | R26 `attach-winloss` | conditional enrichment | HIGH | $0.50–2.00 | Pure LLM + embeddings (no external deps). Klue methodology baseline (31 questions framework). PII-redaction Sonnet pre-pass mandatory before deliverable |

**Group total**: ~$3–8/audit when all enrichments fire.

---

## R23 attach-demo safety pattern (critical — research-flagged)

The most novel safety surface in the plan. Required mitigations:

1. **CLI signature**: `freddy audit attach-demo --client <slug> --url <demo-url> --username <user> --password <pass> --readonly-mode <bool>`
2. **Pre-flight contract**: signed acknowledgment that demo account is sandboxed; agent will perform read-mostly nav + non-destructive interactions; no DELETE / admin / billing / public submissions
3. **Isolated browser context**: Playwright `browser.new_context()` per audit run; cookies destroyed after
4. **Prefer Playwright MCP snapshot mode** (accessibility tree) over screenshots for sensitive fields — no PII in API logs
5. **Hook safety**: register `PreToolUse` hook in `src/audit/hooks.py` that intercepts URLs containing `/admin`, `/billing`, `/users`, `/destroy`, `/delete` or `DELETE` HTTP method → kills action + Slack-alerts JR
6. **Trace recording**: Playwright trace saved to `clients/<slug>/audit/enrichments/demo-trace.zip` so JR can audit what the agent did
7. **Disposable test fixtures**: never type real PII; predefined fixture set (`test+gofreddy@example.com`, "Test User", "555-0100")
8. **Time-box**: hard 15-min total timeout; max 30 navigation actions; max 5 form submissions
9. **Pre-flight ToS check** on robots.txt + ToS clause for automation prohibition

---

## Net delta to plan

| Dimension | Current | After R1+R2 (gap doc) | After research synthesis |
|---|---|---|---|
| Collection primitives | 31 | 50 (proposed) | **47** (form_cro_deep folded into capture_surface_scan; messaging_consistency, partnership_footprint, content_strategy_shape, executive_visibility, aso, scrape_careers, audit_pricing_page kept as deepenings of existing — net new primitives only count once) |
| Reasoning primitives | 1 | 1 | 1 |
| Conditional enrichments | 5 (R18–R22) | 9 (proposed) | **9** (R23/R24/R25/R26 all kept) |
| Conditional firmographic primitives | 1 (audit_aso) | 6 | **6** (audit_aso + audit_local_seo + audit_oss_footprint + audit_abm_signals + audit_plg_motion + audit_devex) |
| Lenses | 9 | 9 | 9 |
| New providers (clean modules) | 0 | — | **6** (github, producthunt, crtsh, amo, atlassian_marketplace, wikipedia) |
| New env vars | 0 | — | **2 required** (GITHUB_TOKEN, PRODUCT_HUNT_TOKEN) + 1 optional (WIKIMEDIA_API_KEY) |
| Net coverage | ~90% | ~99% (claimed) | **~99% (research-validated)** |
| Cost per audit baseline | $X | $X + $0.90–1.80 | $X + ~$1.50–3.50 (when all triggered); +$3–8 when enrichments R23/R26 also fire |

---

## High-confidence "go" items (24 of 34 — HIGH confidence per research)

All Group 1 (5), Group 2 (5 — esp. directory presence + OSS footprint + launch cadence), Group 3 customer_education + public_roadmap + earned_media_wikipedia + customer_story (4), Group 4 trust_signals + form_cro_deep + abm_signals (3), Group 5 plg_motion + devex + aso + budget + crm + winloss (6). Total: 23 plus a few I'm rounding. Apply with confidence.

## Medium-confidence items needing care (8)

- `audit_local_seo` — citation aggregator long-tail without paid tools; v1 covers 80%
- `audit_pricing_page` tier extraction — needs Sonnet fallback for non-regex-friendly layouts
- `audit_corporate_responsibility` — gate at mid-market+ to avoid SMB false-negatives
- `audit_messaging_consistency` headline scoring — opinion not science; surface as directional
- `audit_content_strategy_shape` newsletter subscriber claims — `confidence: claimed` (unverified)
- `audit_funnel_content_shape` — reframed; cap severity at `low`
- `scrape_careers` Glassdoor — 70-80% success rate; degrade gracefully
- R23 `attach-demo` — safety surface non-trivial; ship with hook + trace recording

## Low-confidence items (kept but flagged)

- `audit_executive_visibility` LinkedIn subfield — flag `linkedin_data_quality: limited` honestly; do not pretend completeness
- `audit_funnel_content_shape` — value depends on whether descriptive content shape is useful to JR's diagnostic narrative; may be redundant after first 5 audits

## Items where research changed the spec materially

1. `audit_funnel_velocity_proxies` → renamed `audit_funnel_content_shape` (Agent 4)
2. `audit_form_cro_deep` → folded into existing `capture_surface_scan` P23 (Agent 4)
3. `scrape_careers` Glassdoor → swapped to Bright Data path; pay-transparency compliance is anchor finding (Agent 5)
4. `audit_local_seo` → DataForSEO Business Data + free path covers 80%; BrightLocal deferred (Agent 1)
5. `audit_aso` → AppFollow/data.ai NOT required for 6-dim rubric; iTunes API + existing adapters suffice (Agent 5)
6. `audit_accessibility` → flag overlays (UserWay/AccessiBe) as NEGATIVE signal not positive (Agent 1 + Agent 4)
7. `audit_oss_footprint` → cross-link to GEO lens (high-star repos = AI-citation supply) (Agent 2)

## Items where research surfaced new sub-signals to add

- `audit_plg_motion`: reverse-trial detection (Verna/OpenView pattern)
- `scrape_careers`: pay-transparency compliance is the publishable anchor finding (CA/NY/CO/WA jurisdictional violations)
- `audit_directory_presence`: AI-firmographic-conditional subset (TAAFT, Futurepedia, Toolify) for AI-tool prospects
- `audit_oss_footprint`: contributor employment affiliation (community-driven vs in-house)
- `audit_devex`: SDK freshness via npm/PyPI publish-date check

---

## Sources

Full source citations live in agent transcripts (see decision log in `2026-04-22-001-audit-coverage-gaps.md` for the originating gap entries). Key 2025-2026 references:

- Gartner 2025 CMO Spend Survey
- OpenView/High Alpha 2025 SaaS Benchmarks
- ICONIQ Growth State of GTM 2024
- First Page Sage 2026 Pipeline Velocity Report
- The Digital Bloom 2025 SaaS Funnel Benchmarks
- Klue 2025 Win-Loss methodology
- DataForSEO 2026 hreflang + Business Data API updates
- Wikipedia ORES → Lift Wing migration (Jan 2025)
- SecurityHeaders.com sunset (April 2026, Snyk acquisition)
- Glassdoor consolidation into Indeed (July 2025, Recruit Holdings)
- 2026 Pay Transparency Laws by State (Paycor / Jackson Lewis)
- Mozilla HTTP Observatory v2 (replaces SecurityHeaders.com)
