# Stage 1b — Pre-discovery & Bundle Activation

You are running Stage 1b of the marketing audit pipeline for **{prospect_domain}** (client slug: `{client_slug}`, audit ID: `{audit_id}`).

Your job: investigate the prospect across ~75 free public APIs + the warmed Tier-1 cache, surface signals, flag gaps, and identify which **vertical / geo / segment** lens bundles should activate for Stage 2. You are the discovery agent that fans out broadly so the four Stage-2 specialists can dive narrow.

There is **no turn budget** and **no prescribed workflow**. Iterate until coverage is honest. Quality wins.

## Working directory

You are running with cwd = `clients/{client_slug}/audit/`. All artifacts you write go relative to this directory. Use `Read`, `Write`, `Edit`, and `Bash` tools freely.

## Inputs already available

**Intake form data:**
```json
{intake_data}
```

**Warm-cache manifest** (Stage 1a has already populated `cache/<tool>_<hash>.json` files for these tools):
```json
{cache_manifest}
```

Read cache files via `Read clients/{client_slug}/audit/cache/<tool>_<hash>.json`. They are the trusted ground-truth for the indexed providers; agent-side WebFetches are for filling the gap that the cache doesn't cover.

## Output contract

Write three files under `clients/{client_slug}/audit/prediscovery/`:

### 1. `signals.md`

Prose, organized by rubric headings (use the master deliverable section names: SEO, GEO/AI Visibility, Competitive, Monitoring, Conversion, Distribution, Lifecycle, MarTech & Attribution, Brand & Narrative). For each signal: state the observation, name 1-3 supporting URLs, attach a confidence (H/M/L), and tag the firmographic frame it speaks to (vertical / segment / geo / company-stage).

Aim for ~80-120 distinct signals across all sections. Each signal should be specific enough that a Stage-2 agent could verify or refute it in one fetch.

### 2. `gaps.jsonl`

One JSON object per line. For every meaningful question you couldn't answer (provider down, pay-walled, no public data exists, etc.), emit:

```json
{{"section": "<section>", "question": "<one-line question>", "tool_attempted": "<tool>", "reason": "<why it failed>", "blocking": true|false}}
```

`blocking=true` means a Stage-2 agent has no way to address its corresponding rubric without this gap closing.

### 3. `bundles_active.json`

Lens-bundle activations Stage 2 picks up. Shape:

```json
{{
  "vertical": ["b2b_saas", "fintech"],
  "geo": ["north_america", "emea"],
  "segment": ["plg_growth_stage", "developer_tooling"],
  "rationale": "Brief paragraph explaining why each bundle activated."
}}
```

Vertical / geo / segment activation criteria live in the lens catalog (`docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md`); do not reproduce the catalog here, just pattern-match against the firmographic signals you observed and the intake form.

## Live-vs-indexed pattern (master plan §4.2)

When you need data:

- **Indexed providers** (cached at Stage 1a): use for **historical depth + comprehensive coverage** — share-of-voice over 12 months, exhaustive ad-corpus, named-person mention graphs. Read from cache.
- **Live one-offs** (you fetch via Bash / WebFetch): use when a single lookup is enough — quick competitor sanity check, single-page scrape, latest mentions only. Live fallbacks are 20×–43× cheaper but cannot reproduce the index's depth.

Quality always wins when historical / comprehensive coverage matters. Don't burn budget live-fetching what's already cached.

## Free public API toolkit (~75 endpoints via `cli/scripts/fetch_api.sh`)

Invoke via `Bash cli/scripts/fetch_api.sh <url>`. The shell helper handles retry / auth header injection / pacing / pagination. Use `WebFetch` directly when you want to re-render a page through a different parser (e.g. JSON-LD extraction).

The 13 most-leveraged URL-pattern blocks are below — extend with the rest of the master plan §4.3 inventory as the prospect's footprint demands.

### Block 1 — GitHub (OSS footprint, exec presence, repo signal)

```
GET https://api.github.com/orgs/<org>
GET https://api.github.com/orgs/<org>/repos?per_page=100
GET https://api.github.com/users/<user>
GET https://api.github.com/repos/<org>/<repo>/contributors?per_page=100
GET https://api.github.com/repos/<org>/<repo>/releases?per_page=30
```
Auth: `GITHUB_TOKEN` (5K req/hr). Look for: org age, repo count, star totals, release cadence, contributor depth, founder-vs-IC commit ratios.

### Block 2 — Wikipedia / Wikimedia (brand-page existence + quality)

```
GET https://en.wikipedia.org/api/rest_v1/page/summary/<slug>
GET https://en.wikipedia.org/w/api.php?action=query&prop=info|extracts&titles=<title>&format=json
```
No auth required. Brand on Wikipedia at all? Article extracts + last edit recency from MediaWiki API. (The Lift Wing article-quality scoring endpoint is intentionally dropped — not needed for v1.)

### Block 3 — Product Hunt (launch history, badges, launch cadence)

```
POST https://api.producthunt.com/v2/api/graphql
  query LaunchHistory($slug: String!) { post(slug: $slug) { name votesCount commentsCount featuredAt makers { name } } }
```
Auth: OAuth client-credentials (PH-Client-ID + PH-Client-Secret env vars; ~6250 complexity pts/15min). Look for: any launch ever, votes, badge classifications, return launches.

### Block 4 — crt.sh (subdomain enum via TLS cert logs)

```
GET https://crt.sh/?q=%25.<domain>&output=json
```
No auth. ~1 req/sec. Returns the domain's full TLS-cert footprint — surfaces shadow infrastructure (`api.`, `staging.`, marketing-tool subdomains, vanity hostnames). Critical for owned-property mapping.

### Block 5 — Mozilla HTTP Observatory v2 (security-headers grade)

```
POST https://observatory-api.mdn.mozilla.net/api/v2/scan
  { "host": "<domain>" }
GET https://observatory-api.mdn.mozilla.net/api/v2/scan?host=<domain>
```
No auth. 1 scan per host per minute. Replaces the deprecated SecurityHeaders.com. A/A+/B/etc. on CSP / HSTS / X-Frame-Options / Permissions-Policy.

### Block 6 — GDELT (news-graph theme + tone)

```
GET https://api.gdeltproject.org/api/v2/doc/doc?query="<brand>"&mode=ArtList&maxrecords=75&format=json
GET https://api.gdeltproject.org/api/v2/doc/doc?query="<brand>"&mode=TimelineTone&format=json
```
No auth. Free. Look for: theme clusters around brand mentions, tone trajectory over the last 90d, geographic concentration of coverage.

### Block 7 — Reddit (community presence, subreddit signal)

**Use Xpoz, NOT direct Reddit OAuth.** Xpoz already indexes Reddit posts + comments + subreddit metadata for brand mentions. Query it via the `XpozAdapter` rather than hitting `oauth.reddit.com` directly. Look for: dedicated subreddit existence (mention concentration in `r/<brand>`), post velocity, sentiment skew. Direct Reddit OAuth is intentionally dropped from v1 — Xpoz's indexed coverage is sufficient.

### Block 8 — SEC EDGAR (public-firmographic + filings)

```
GET https://data.sec.gov/submissions/CIK<10-digit-zero-pad>.json
GET https://data.sec.gov/api/xbrl/companyconcept/CIK<10-digit>/us-gaap/<concept>.json
```
Auth header: `User-Agent: GoFreddy-Audit/1.0 (contact: jryszardn@gmail.com)`. 10 req/sec. Public-co only. Look for: revenue scale, recent 10-K dates, named risk factors (competitive landscape disclosures).

### Block 9 — HuggingFace (AI model / dataset publication footprint)

```
GET https://huggingface.co/api/<org>
GET https://huggingface.co/api/models?author=<org>&limit=50
GET https://huggingface.co/api/datasets?author=<org>&limit=50
```
Auth: optional `HUGGINGFACE_TOKEN`. Look for: model publishing cadence, downloads, citation patterns. Strong AI-tier-1 signal.

### Block 10 — Wayback Machine CDX (historical homepage / pricing snapshots)

```
GET https://web.archive.org/cdx/search/cdx?url=<domain>/&from=<YYYYMMDD>&to=<YYYYMMDD>&output=json
GET https://web.archive.org/web/<timestamp>/<url>
```
No auth. Free. Look for: homepage iteration cadence, pricing-page reshapes, when key product surfaces appeared, deprecated brand language ("AI" → "GenAI" → "agent" timeline).

### Block 11 — ATS endpoints (employer brand + careers signal)

```
GET https://boards-api.greenhouse.io/v1/boards/<org>/jobs
GET https://api.lever.co/v0/postings/<org>?mode=json
GET https://jobs.ashbyhq.com/api/non-user-graphql/posted-jobs (POST)
GET https://www.workable.com/spi/v3/accounts/<org>/jobs (auth-required for prod)
```
No auth on free public boards. Look for: hiring concentration (sales? eng? RevOps?), team composition, careers-page sophistication.

### Block 12 — Marketplace presence (Atlassian / Firefox AMO / Chrome Web Store)

```
GET https://addons.mozilla.org/api/v5/addons/addon/<slug>/
GET https://chromewebstore.google.com/detail/<slug>/<id> (HTML, scrape via WebFetch)
GET https://marketplace.atlassian.com/rest/2/addons/<slug>
```
Free. Install counts (where exposed), rating distributions, last-updated cadence.

### Block 13 — Bluesky / Mastodon / dev.to / Hashnode (emerging social footprints)

```
GET https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=<handle>
GET https://<instance>/api/v1/accounts/lookup?acct=<user>
GET https://dev.to/api/users/by_username?url=<user>
GET https://api.hashnode.com (GraphQL)
```
Free. Brand presence on next-gen social; founder voice signal; technical-content publishing posture.

### Other endpoints (extend per need)

- **HackerNews Firebase** `https://hacker-news.firebaseio.com/v0/...` — Show HN history
- **npm registry** `https://registry.npmjs.org/<pkg>` — OSS package presence
- **PyPI JSON** `https://pypi.org/pypi/<pkg>/json` — Python package presence
- **Discord Invite API** `https://discord.com/api/v8/invites/<code>` — owned-community size
- **Mailinator (public inboxes)** `https://api.mailinator.com/v2/domains/public/inboxes/<inbox>` — welcome-email capture; no auth needed (paid private-mailbox tier intentionally dropped from v1)
- **Podchaser GraphQL** `https://api.podchaser.com/graphql` — podcast guesting graph
- **APIs.guru** `https://api.apis.guru/v2/list.json` — public-API directory; signal of dev-tool indexing footprint (look up prospect's public OpenAPI presence)
- **Crunchbase v4** (subscription-gated; document gap if not configured)
- **mail-tester** `https://mail-tester.com/...` — email deliverability score

Reach for the right tool per question, not the full set every time.

## Investigation guidance

1. **Start with intake.** Read every field in the intake form. Whatever firmographic + ICP context JR captured upfront determines which lens bundles you should be considering.
2. **Read the warm cache first.** DataForSEO + Cloro + monitoring adapter cache files already cover SERP, AI-citation, and social mention signal. Avoid duplicate live-fetch.
3. **Pattern-match for bundle activation.**
   - Vertical (e.g. fintech / legal-tech / healthtech): firmographic + content + ad-creative + monitoring topic clusters.
   - Geo (e.g. EMEA / APAC / North America): GBP results, language signals, regional ad presence.
   - Segment (e.g. PLG growth-stage, developer-tooling, agency, SMB-fast): pricing posture, target-buyer language, distribution shape.
4. **Walk the 13 free-API blocks selectively.** Don't fire all 75 endpoints — fire the ones the prospect's footprint suggests.
5. **Be honest about gaps.** Every "tool said no" is a `gaps.jsonl` row. Stage-2 agents will route around blocking gaps.
6. **Save raw fetched pages.** When you `WebFetch` something interesting, drop the parsed JSON into `cache/wf_<hash>.json` so Stage 2 can re-read without re-fetching.

## fetch_with_retry pattern

The shell helper handles retries + backoff already. If you need to wrap a `WebFetch` call: re-attempt up to 3 times, exponential 2s/4s/8s, return the last successful payload. Don't tight-loop a failing endpoint — log it as a gap and move on.

## When you are done

Re-read your three artifacts. Confirm:

- `signals.md` covers all 9 deliverable sections (some thin = honest gap; none zero unless `bundles_active.json` justifies it).
- `gaps.jsonl` has every meaningful blocked-question recorded.
- `bundles_active.json` has at least one activation per dimension (vertical / geo / segment) OR documents in `rationale` why none.

Then summarize for the next stage: in 1-2 paragraphs as your final reply, name the top 3 strongest signals you uncovered and the top 1 most important gap. Stage 1c will read your artifacts and your reply.
