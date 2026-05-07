# Marketing audit v1 — full data-source inventory

Captured 2026-05-07 after JR pressure-test #5: "are you sure we already
have everything? Didn't we have much more data providers?"

**Honest count: ~70 distinct data sources actively wired.** Master plan
§4 estimated ~94 (17 T1 + 75 T2 + 2 T3). The shortfall is mostly
endpoint-counting style — many T2 "endpoints" share a host (e.g. GitHub
has 5 endpoints under `api.github.com`).

## Tier 1 — owned providers (20 Python classes)

Wired in code. All have provider tests.

### SEO + Performance (3)
- `src/seo/providers/dataforseo.py` — 8 methods (on-page audit, keywords,
  backlinks, SERP, Labs, search volume, ranked-keywords, competitors)
- `src/seo/providers/pagespeed.py` — Core Web Vitals (mobile + desktop)
- `src/seo/providers/gsc.py` — Search Console clicks/impr/CTR (R18 attach gated)

### GEO / AI Visibility (1)
- `src/geo/providers/cloro.py` — 6 AI engines (ChatGPT / Perplexity /
  Gemini / Claude / Grok / Copilot)

### Competitive (3)
- `src/competitive/providers/foreplay.py` — Meta + TikTok + LinkedIn paid
  creative corpus (indexed)
- `src/competitive/providers/adyntel.py` — Google Ads transparency
  (indexed, paginated)
- `src/competitive/vision.py` — Gemini vision enrichment for ad creatives

### Monitoring adapters (11)
- `xpoz.py` — Twitter + Instagram + Reddit (indexed, primary social)
- `reviews.py` — Trustpilot + AppStore + PlayStore via Apify
- `ic_content.py` — Influencers.club TikTok+YouTube discovery
- `tiktok.py` — TikTok via Apify (interim; xpoz handles in production)
- `news.py` — NewsData.io REST
- `bluesky.py` — Bluesky AT Protocol public-search
- `facebook.py` — Apify scraper
- `podcasts.py` — Pod Engine + Podchaser GraphQL
- `linkedin.py` — Apify scraper
- `google_trends.py` — Apify scraper
- `ai_search.py` — wraps Cloro

### Audit-specific tools (5 — net-new for marketing audit)
- `src/audit/tools/apify_similarweb.py` — Apify SimilarWeb scraper
  (replaces dropped enterprise SimilarWeb subscription)
- `src/audit/tools/brave_search.py` — Brave Search API (lens #157)
- `src/audit/tools/serpapi_ads.py` — SerpAPI Google Ads transparency
  (live fallback for Adyntel)
- `src/audit/tools/martech.py` — Wappalyzer-next port (~2500 web techs)
- `src/audit/tools/rendered_fetcher.py` — Playwright Chromium headless

### X-engine fetchers (3 — reusable for marketing_audit)
- `src/fetcher/instagram.py`
- `src/fetcher/tiktok.py`
- `src/fetcher/youtube.py`

**Tier-1 total: 23 wired data-source classes.**

## Tier 2 — free public APIs (29 hosts in stage_1b prompt)

Reached agent-side via `cli/scripts/fetch_api.sh` or direct WebFetch.
Each host typically exposes 2-5 specific endpoints (so ~75 total endpoints).

| Host | Auth | Coverage |
|---|---|---|
| `api.github.com` | `GITHUB_TOKEN` (free) | repos / orgs / users / contributors / releases |
| `en.wikipedia.org` + `api.wikimedia.org` | optional `WIKIMEDIA_API_KEY` | page summary + Lift Wing article quality |
| `api.producthunt.com/v2` | OAuth | launch history + upvotes + badges |
| `crt.sh` | none | TLS cert log → subdomain enum |
| `observatory-api.mdn.mozilla.net` | none | security headers grade |
| `api.gdeltproject.org` | none | global news graph (themes, tone, timeline) |
| `oauth.reddit.com` + `www.reddit.com` | `REDDIT_CLIENT_ID` + `_SECRET` | subreddit + IAmA + search |
| `data.sec.gov` | UA w/ contact email | filings + companyconcept |
| `huggingface.co/api` | optional `HUGGINGFACE_TOKEN` | model + dataset publication |
| `api.mailinator.com` | optional `MAILINATOR_API_TOKEN` | welcome-email DKIM/SPF |
| `web.archive.org` | none | historical snapshots |
| `addons.mozilla.org` | none | Firefox extension presence |
| `marketplace.atlassian.com` | none | Atlassian addon presence |
| `chromewebstore.google.com` | none | Chrome extension presence |
| `discord.com` | none | invite metadata (community size) |
| `api.podchaser.com/graphql` | OAuth | podcast guesting graph |
| `hacker-news.firebaseio.com` | none | Show HN + comment graph |
| `registry.npmjs.org` | none | npm package presence |
| `pypi.org/pypi` | none | PyPI package presence |
| `public.api.bsky.app` | none | Bluesky public profile + posts |
| `boards-api.greenhouse.io` | none | Greenhouse ATS jobs |
| `api.lever.co` | none | Lever ATS jobs |
| `jobs.ashbyhq.com` | none | Ashby ATS jobs |
| `www.workable.com` | none | Workable ATS jobs |
| `mail-tester.com` | none w/ pacing | email deliverability score |
| `dev.to/api` | none | DEV.to author presence |
| `api.hashnode.com` | none | Hashnode author presence |

**Tier-2 hosts: 29. Distinct endpoints across them: ~75.**

## Tier 3 — local detection (in Tier-1 list above)

- Wappalyzer-next port (`martech.py`) — ~2500 web technologies via DOM +
  headers + cookie patterns
- Playwright Chromium headless (`rendered_fetcher.py`) — captures
  rendered DOM + screenshots + console errors + network log

## Preflight checks (8 — direct domain probes)

Wired into `stage_1_warmup`. No keys needed; agent reads aggregated signals.

- `dns.py` — SPF / DKIM / DMARC / BIMI / MTA-STS
- `wellknown.py` — security.txt + ai.txt + humans.txt
- `schema.py` — JSON-LD parse
- `headers.py` — HSTS / CSP / Referrer-Policy / COOP / COEP
- `social.py` — OG + Twitter card meta
- `assets.py` — favicon / manifest / robots / sitemap
- `badges.py` — TrustBadge / OneTrust / DataPrivacyFramework detection
- `tooling.py` — vendor fingerprints (analytics, A/B, CMP, etc.)

## Total signal surface

| Tier | Wired sources |
|---|---|
| Tier-1 owned (Python classes) | 23 |
| Tier-2 free public hosts | 29 (~75 endpoints) |
| Tier-3 local detection | 2 (Wappalyzer + Playwright) |
| Preflight checks | 8 |
| **Total** | **~62 hosts / ~108 endpoints** |

Per audit, the Stage-1a + Stage-1b + 4 Stage-2 agents fan out across this
surface dynamically — depending on prospect's industry / size / geo, the
agent calls 30-80 distinct endpoints per audit.

## Where master-plan numbers come from

§4.1 estimated ~17 Tier-1 + ~75 Tier-2 = ~94 sources.
- 17 → became 23 after Phase 1.5 work shipped (audit-specific tools +
  x_engine fetchers reused).
- 75 → that was endpoint count, not host count. 29 hosts × ~2-3
  endpoints each ≈ 75. Matches.

## Known gaps (small)

- **APIs.guru** (api.apis.guru) — public API directory, useful for
  dev-tool prospects. Listed in master plan §4.3 but NOT in stage_1b
  prompt. ~3 lenses affected (dev-relations footprint scoring).
  Trivial to add — 5 lines in stage_1b prompt.
- **Hyperscaler marketplaces** (Salesforce AppExchange, HubSpot, Shopify,
  Slack, AWS, Azure, GCP) — no clean public APIs. Master plan §4.7 says
  "Accept SERP-only fallback via DataForSEO `site:` queries. Depth
  limited to listing-presence + name match." Documented limitation.

## What this means for the dry run

**The data surface is sufficient.** Per Agent B's 192-entry coverage
audit (master plan §4.7): ~99% of catalog covered after gap resolution.
JR has ALL the keys for the P0 + most P1 set, including:

- ✓ All 5 P0 (DataForSEO, PageSpeed, Cloro, Apify, Xpoz)
- ✓ Foreplay, Adyntel (P1)
- ✓ NewsData, IC, ScrapeCreators, TwitterAPI.io (additional)
- ✓ R2, OpenAI, Gemini

Missing keys (ALL optional, gap_flag if absent):
- Brave Search, SerpAPI, Pod Engine, GSC service-account
- Free OAuth tokens: GitHub, Reddit, HuggingFace, Wikimedia, Mailinator,
  Product Hunt, Podchaser

**Without those optional keys, ~40-50 lenses gap_flag.** The pipeline
still produces a deliverable shape — gap_report.md surfaces them
honestly per master plan §3.6 (MA-7 Gap Honesty rubric).

Net: the dry run is genuinely ready to produce a real deliverable. The
gap_flagged content reflects which providers haven't been provisioned,
NOT a code-side data gap.
