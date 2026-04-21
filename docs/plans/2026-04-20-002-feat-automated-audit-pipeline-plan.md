---
title: "feat: Automated Audit Pipeline — Prospect Acquisition System"
type: feat
status: active
date: 2026-04-20
---

# Automated Audit Pipeline — Prospect Acquisition System

## Overview

Build a production-ready marketing-audit pipeline that turns a prospect URL into a complete audit deliverable (HTML + PDF + proposal) in 3 days with minimal manual work. Orchestrated on JR's laptop via Claude Agent SDK + existing provider stack. Analysis-only — the audit does not touch prospect assets or run optimization; post-sign delivery work uses the existing autoresearch system and is out of scope.

This plan is scoped for implementation by a single coding agent (Claude Code) — flat module layout, inline prompts, functions over class hierarchies, thin state in JSON, no abstract base classes or framework-style indirection.

## Requirements

- R1. Delivery target: 3 business days between payment confirmation and audit delivery. Not enforced as an SLA — JR fires each stage manually via Claude Code locally, so pace depends on availability.
- R2. `freddy audit run --client <slug>` runs all 6 stages end-to-end with per-stage checkpoints.
- R3. 5 lens analyses: SEO, GEO, competitive, monitoring, conversion. Canonical findings schema with severity + confidence.
- R4. Synthesis produces ranked findings, 3–5 surprises, and a 3-tier proposal (Fix-it / Build-it / Run-it) with deterministic registry-based pricing.
- R5. Deliverable = HTML at `reports.gofreddy.ai/<slug>` + downloadable PDF; Fireflies captures the walkthrough call.
- R6. Local storage only. Everything under `clients/<slug>/audit/`, git-committed per stage.
- R7. Costs are telemetry, not gates. Every stage appends to `cost_log.jsonl` for post-hoc analysis; no cap blocks execution. Monthly infra directionally **~$80–140, volume-dependent**: Fireflies (~$10 flat) + DataForSEO base subscription (fixed) + **DataForSEO Backlinks + Labs endpoints (pay-per-use, roughly $20–60/mo at ~20 audits/month)** + Apify pay-per-run + Stripe transaction fees. Google PageSpeed Insights API is free (25K queries/day, far more than needed). Not enforced. Rationale: budget gates cause agents to cut corners.
- R8. Three permanent gates every audit, plus a temporary calibration gate for the first 5. (1) Intake review: after Stage 1, JR reviews the pre-discovery brief. (2) Payment gate: between Stage 1 and Stage 2, sales call happens and $1K Stripe payment must clear (`state.paid = True`) before Stage 2 fires. (3) Final publish: JR manually runs `freddy audit publish` after reviewing the rendered deliverable. First-5 calibration mode adds approval prompts after every stage.
- R9. No autoresearch coupling. Audit does not touch `src/evaluation/` or `autoresearch/`.
- R10. $1,000 audit paid upfront via Stripe Checkout before Stage 2 fires. JR sends a Checkout URL after the sales call via `freddy audit send-invoice`; Stripe webhook (`POST /v1/audit/stripe`) sets `state.paid = True` and Slack-pings JR. Credited in full to the first engagement invoice if the prospect signs within 60 days (credit-note logic handled manually at engagement-invoice time, not in code).
- R11. Data retention: workspace kept active 90 days post-delivery, archived 1 year, then deleted. Deliverable at `reports.gofreddy.ai/<slug>` preserved full 1 year. Pre-paid leads (Stage 1 complete, payment never received) follow the same retention.
- R12. PII hygiene: VoC quotes sourced only from public channels; quotes always cite source URL; private/paywalled content never embedded verbatim.
- R13. Branding: every HTML page and PDF includes a persistent "Prepared by GoFreddy · gofreddy.ai" footer, preserved when shared externally.
- R14. Manual-fire philosophy: all pipeline stages (0–5) are triggered by JR via `freddy audit run` locally — no poller, no auto-fire on webhook. External events (form submission, Stripe payment, Fireflies transcripts) may update state via webhooks, but stage progression is always JR's call. Auto-firing the pipeline is a future work item, deferred out of this plan.
- R15. Two-call model: a **sales call** happens after Stage 1 and before payment — JR pitches the $1K audit using the pre-discovery brief as sales prep. A **walkthrough call** happens after delivery — JR walks through findings and pitches the 3-tier engagement. Both calls are captured by Fireflies with separate webhook endpoints and separate fit-signals schemas (`SalesFitSignals` vs `WalkthroughFitSignals`).

## Scope

**In:** 6-stage pipeline (manually fired per stage via `freddy audit run`), 15 pre-discovery primitives (including SaaS-parity coverage: backlinks via DataForSEO Backlinks API, Core Web Vitals via Google PageSpeed Insights API, historical rank/traffic trends via DataForSEO Historical), 4 ports from Freddy (`content_extractor`, `clients` schema, `content_gen` output models, `competitive/brief.py` pattern), HTML+PDF rendering, Cloudflare Worker intake + hosting, Slack lead-notification, Stripe Checkout + payment webhook, two Fireflies webhooks (sales call + walkthrough call), 6 consolidated Corey Haines reference files, eval harness.

**Out / deferred to a future plan:** Autoresearch work, post-sign delivery execution, outbound prospecting, multi-tenant infra, free-tier audits, pre-analysis discovery call (the sales call fills that role now), **laptop poller / auto-firing the pipeline on form submission**, **Stripe-webhook-auto-fires-Stage-2** (webhook only updates `state.paid`; JR fires Stage 2), **3-business-day SLA enforcement** (target only), **engagement-invoice credit-note accounting** (manual).

## Architecture

6 stages run sequentially. Each stage is a Python function that reads state, does work (deterministic Python or structured Claude API calls), writes outputs, updates state. **No agent loops except in Stage 2.** No Stage abstract class. No skills library under `.claude/skills/`. Prompts are string constants in `src/audit/prompts.py`.

```
Form submit → Cloudflare Worker → Fly API /v1/audit/intake → audit_pending row → Slack ping JR
                                                                                     │
                                                      (JR manually creates client + fires stages)
                                                                                     ▼
  $ freddy audit run --client <slug> --stage 1
  ├─ Stage 0: Intake       — Python only, populates workspace from form data
  └─ Stage 1: Pre-discovery — runs 15 primitives; ONE Opus call synthesizes signals into brief.md

🛑 INTAKE GATE — JR reads brief.md, decides whether to pursue

  (JR books + runs sales call; Fireflies captures; sales-call webhook writes sales_fit_signals.json)

  $ freddy audit send-invoice --client <slug>     ← Stripe Checkout URL → email/Slack prospect
                                                     │
                                                     ▼
                                               prospect pays
                                                     │
                                Stripe webhook → POST /v1/audit/stripe → state.paid = True + Slack JR

🛑 PAYMENT GATE — state.paid must be True before Stage 2 will run

  $ freddy audit run --client <slug>              ← resumes Stage 2 onward
  ├─ Stage 2: Lenses        — 5 Sonnet Agent SDK sessions in parallel (asyncio.gather)
  ├─ Stage 3: Synthesis     — brief.py-style async fan-out → Opus synthesis
  ├─ Stage 4: Proposal      — Opus picks capability IDs + writes narrative; Python applies pricing
  └─ Stage 5: Deliverable   — Jinja2 → HTML, WeasyPrint → PDF, upload to R2, publish

  $ freddy audit publish --client <slug>          ← JR reviews + publishes to reports.gofreddy.ai/<ulid>

  (JR runs walkthrough call; Fireflies webhook → POST /v1/audit/walkthrough → walkthrough_fit_signals.json)
```

Every `$ freddy …` line is a manual invocation in Claude Code / terminal. The two auto-arrows left in the flow are passive receivers: form → Supabase + Slack (lead capture only) and Fireflies/Stripe webhooks → state updates (no stage firing).

**Module layout:**

```
src/audit/
  run.py                    # freddy audit run entry point, orchestrator loop
  state.py                  # state.json read/write, session persistence, git commit
  primitives.py             # 9 pre-discovery functions
  rendered_fetcher.py       # Playwright wrapper (shared)
  stages.py                 # stage_0 through stage_5 functions
  brief.py                  # ported synthesis pattern (adapted)
  prompts.py                # all LLM prompts as string constants
  capability_registry.py    # YAML loader + pricing multiplier
  capability_registry.yaml  # ~15 capability entries
  clients_schema.py         # Pydantic Client model
  lens_models.py            # Finding, LensOutput Pydantic models
  renderer.py               # render_html, render_pdf
  fireflies.py              # HMAC verify + transcript fetch + fit signals
  hooks.py                  # PreToolUse/PostToolUse/PreCompact/Stop hook handlers
  telemetry.py              # cost_log.jsonl writer + anomaly alerting (Slack)
  stripe.py                 # Stripe Checkout Session creation + webhook signature verify
  sales_call.py             # Fireflies sales-call fit-signals extraction
  eval/                     # U9 eval harness (rubric, runner, report)
  templates/audit_report.html.j2
  references/*.md           # 6 consolidated Corey skill references
.claude/skills/audit-run/SKILL.md  # invoke with /audit-run in interactive Claude Code
cli/freddy/commands/audit.py       # freddy audit {run,publish,mark-paid,send-invoice,ingest-transcript,eval}
src/api/routers/audit_intake.py    # POST /v1/audit/intake (form webhook → Supabase + Slack ping)
src/api/routers/audit_stripe.py    # POST /v1/audit/stripe (Stripe webhook → state.paid)
src/api/routers/audit_sales_call.py      # POST /v1/audit/sales-call (Fireflies webhook, pre-Stage-2 call)
src/api/routers/audit_walkthrough.py     # POST /v1/audit/walkthrough (Fireflies webhook, post-delivery call)
landing/audit-intake.html          # gofreddy.ai form
cloudflare-workers/audit-intake/   # form→Fly relay
cloudflare-workers/audit-hosting/  # reports.gofreddy.ai/<slug> edge
supabase/migrations/20260420000001_audit_intake.sql
supabase/migrations/20260420000002_audit_payment.sql   # payment_events table
```

## Key decisions (resolved in 2026-04-19/20 design session)

- Claude Agent SDK (Python), not ported Freddy ADK; inline prompts, not skills library.
- Sonnet for pre-discovery synthesis + all 5 lenses; Opus for synthesis, surprises, proposal.
- Local file storage only; per-stage git commits.
- Two-call sales model: sales call pre-Stage-2 (JR pitches $1K audit using pre-discovery brief; prospect pays); walkthrough call post-delivery (JR walks through findings + pitches engagement). Both captured by Fireflies via separate webhook endpoints.
- Manual-fire pipeline in v1: JR runs every `freddy audit run [--stage N]` command locally via Claude Code. No laptop poller. Webhooks (Stripe, Fireflies) update state but never trigger stage progression. Auto-firing deferred to a future plan.
- Greenfield primitives replace paid APIs: python-Wappalyzer → BuiltWith, crt.sh + subfinder → SecurityTrails, public-page scraping → PDL + TheirStack.
- Registry-driven pricing: LLM picks capability IDs, Python applies prospect-size multiplier deterministically.
- HTML primary + PDF rendered from same HTML (WeasyPrint).
- Lead capture only via Cloudflare Worker → Fly API → Supabase row → Slack ping to JR (no poller, no auto-fire). JR manually creates workspace + fires stages in Claude Code.
- **SaaS-parity signal coverage**: prospects compare audits against Ahrefs / SEMrush / PageSpeed Insights baseline expectations. Three primitives close the obvious gaps: `analyze_backlinks` (DataForSEO Backlinks API — referring domains, anchor text, toxic signals), `audit_page_speed` (Google PageSpeed Insights API — Core Web Vitals LCP/INP/CLS for mobile + desktop), `historical_rank_trends` (DataForSEO Historical — 6-month organic traffic and rank drift). These are inputs to existing lenses, not new lenses. Positioning: we don't out-scan Ahrefs on raw depth — we synthesize across signals SaaS tools don't integrate (backlinks + GEO + VoC + conversion in one narrative).
- Phase 1 infra: ~$40–70/mo. Phase 2 upgrades (PDL, TheirStack, SecurityTrails paid tiers, BuiltWith) only if real audits reveal gaps.
- **Agents get directions, not instructions.** All LLM prompts follow a directive skeleton (role / objective / context / tools+heuristics / effort scaling / quality bar / output contract / termination) rather than step-by-step playbooks. Anthropic's north star for agentic work: *"good heuristics rather than rigid rules."* Count mandates become quality bars; prescribed sequences become objectives.
- **Safety via hooks, not caps.** `PreToolUse` / `PostToolUse` / `PreCompact` / `Stop` hooks (in `src/audit/hooks.py`) act as soft circuit breakers — alert on one pathological tool call, let Claude adapt. A sentinel `max_turns=500` runs under every agent as a runaway-loop backstop (5–10× expected normal max), never a cognitive budget. No cost gates, no output-quality auto-aborts.
- **Session resumability is native.** Every `ClaudeSDKClient` session persists its `session_id` into `state.json` and runs with `enable_file_checkpointing=True`. A crashed agent resumes via `resume=<session_id>` rather than restart. `permission_mode="bypassPermissions"` enables unattended roaming.
- **Envelope schemas, not content schemas.** Pydantic contracts (`Finding`, `LensOutput`, `ProposalSection`, `FitSignals`) prescribe the *shape* that downstream code consumes; agents fill them freely (any count, any severity mix). Counts ("3–5 surprises", "pick 3 capabilities") are quality-bar heuristics in prompts, never mandates.
- **Telemetry, not gating.** Every `ResultMessage` streams `total_cost_usd + duration_ms + num_turns + model_usage + session_id` into `clients/<slug>/audit/cost_log.jsonl`. Cost anomaly alerts (3σ above rolling p95) Slack-ping JR for post-hoc review; no cap blocks execution.

## Deferred to implementation

- Exact capability registry content (ship 12–15 starter entries; iterate based on first 5 audits).
- Jinja2 template specifics (start from `src/competitive/templates/competitive_brief.html`; iterate).
- Scraper retry/backoff specifics (graceful degradation with `partial: true` flags).
- ASO module — build only if any of first 5 prospects have a mobile app.
- Exact Fireflies GraphQL field paths (use docs at implementation time).
- Laptop poller (`freddy audit poll`) + any auto-firing of `freddy audit run` on form submission or payment webhook — JR fires every stage manually in v1. Automating this is a future plan, not a future task.
- Credit-note accounting for the $1K-applied-to-engagement-invoice model — handled manually at engagement-invoice time; no code support in v1.
- Auto-expiration of archived audits past 1 year — cron script; defer until first archived audit approaches expiry (~April 2027).
- 3-business-day SLA enforcement / monitoring — target only; no automated alarms on delivery lag.

## Implementation units

### U1. Foundation: workspace + state + ports

**Goal:** Create `src/audit/` skeleton, state.json schema + telemetry sink + session persistence, CLI entry, and port three small pieces of Freddy code.

**Files:**
- Create `src/audit/__init__.py`, `src/audit/state.py`, `src/audit/run.py` (skeleton only)
- Create `cli/freddy/commands/audit.py` with `freddy audit run` subcommand
- Modify `cli/freddy/main.py` to register
- Modify `cli/freddy/commands/client.py` to accept `--url --size-band --budget-band --vertical-hint` and create `audit/` subtree
- Port from `/Users/jryszardnoszczyk/Documents/GitHub/freddy/`: `src/extraction/content_extractor.py`, `src/extraction/config.py`, `src/extraction/exceptions.py` (drop XpozAdapter optional path)
- Port from Freddy: `src/content_gen/output_models.py`; add `AuditReport`, `LensFinding`, `ProposalSection`, `SurpriseEntry` Pydantic models
- Create lightweight `src/audit/clients_schema.py` — Pydantic Client model (slug, url, size_band, budget_band, priorities, competitor_brands, brand_context)
- Test: `tests/audit/test_state.py`, `tests/extraction/test_content_extractor.py`

**Approach:**
- `state.py`: `AuditState` TypedDict with `current_stage`, `stage_results` (dict), `cost_spent_usd` (telemetry only), `calibration_mode` (bool), `sessions` (dict keyed by agent role → `{session_id, last_turn, last_cost_usd, last_duration_ms}` for resumability), `payment` (`{paid: bool, stripe_session_id, stripe_payment_intent_id, amount_usd, paid_at}`), `sales_call` (`{scheduled_at, completed_at, transcript_path, fit_signals_path}`), `walkthrough_call` (same shape). Plus functions `load()`, `save()`, `record_session(state, role, result_message)`, `record_payment(state, stripe_event)`, `record_call(state, call_type, fit_signals)`, `commit_stage(state, stage_name, outputs)`. No class hierarchy. No cost gates — costs are appended to `cost_log.jsonl` via `telemetry.py` and never block execution. Stage 2 raises `PaymentRequired` if `state.payment.paid == False` when attempted — operational safety, not an agent cap.
- `run.py`: single `run_audit(slug, target_stage=None)` function that loops through stage functions and calls them in order.
- Workspace layout: `clients/<slug>/audit/{intake,prediscovery,lenses,synthesis,proposal,deliverable,walkthrough}/` + `state.json` + `cost_log.jsonl`.
- Atomic state writes: `state.json.tmp` → rename → `git add && git commit`.

**Test scenarios:**
- Happy: fresh workspace + `freddy audit run` populates state.json and commits.
- Happy: `freddy audit run --stage 3` resumes at stage 3 only.
- Happy: `state.sessions[<role>].session_id` populated after any Claude Agent SDK call completes; subsequent resume uses it.
- Happy: `record_payment(state, stripe_event)` sets `state.payment.paid = True` and persists via atomic rename + git commit.
- Edge: running `freddy audit run --stage 2` with `state.payment.paid == False` raises `PaymentRequired` with message pointing JR to `freddy audit send-invoice` and `freddy audit mark-paid`.
- Edge: corrupted state.json raises actionable error with `--reset` hint.
- Happy: `content_extractor.extract(url)` returns non-empty result for HTML, PDF, YouTube URLs.

**Done when:** `freddy client new test --url https://example.com && freddy audit run --client test` produces valid empty workspace + state.json with all stages pending + one git commit.

---

### U2. Pre-discovery primitives (15 functions)

**Goal:** All 15 primitives in a single `src/audit/primitives.py` file — plus a shared Playwright fetcher. Each primitive is a Python function returning a TypedDict, graceful degradation with `partial: bool` on all of them. The final 6 primitives (`analyze_backlinks`, `audit_page_speed`, `historical_rank_trends`, `keyword_gap_analysis`, `analyze_serp_features`, `analyze_internal_links`) cover the **SaaS-parity signals** prospects expect (backlinks, Core Web Vitals, historical trends, keyword gaps, SERP features, internal link graph) so the deliverable doesn't read thin next to Ahrefs / SEMrush / PageSpeed Insights / Screaming Frog.

**Files:**
- Create `src/audit/rendered_fetcher.py` — `RenderedFetcher` class (context manager, single shared browser context per audit)
- Create `src/audit/primitives.py` — 15 functions (ordering: `analyze_serp_features` depends on keyword lists from `historical_rank_trends` + `keyword_gap_analysis`; `analyze_internal_links` depends on sitemap URLs from `freddy sitemap` subprocess. Stage 1 orchestrator runs the first 11 primitives + subprocess CLIs in parallel, then `historical_rank_trends` + `keyword_gap_analysis` + `analyze_internal_links` in parallel, then `analyze_serp_features`):
  - `tech_stack(rendered_page) -> dict` — python-Wappalyzer + custom regex rules for pixels, server-side tagging, modern auth
  - `enumerate_subdomains(domain) -> dict` — crt.sh HTTP + `subfinder` CLI + `whois` CLI, classify live/parked/404
  - `scrape_careers(domain) -> dict` — try `/careers`, `/jobs`, `/work-with-us`; Sonnet extracts role titles + tech mentions
  - `scrape_firmographics(domain) -> dict` — Crunchbase public page + LinkedIn company page via rendered fetcher; Sonnet structured extraction
  - `detect_schema(rendered_page) -> dict` — parse JSON-LD blocks, flag missing high-value types
  - `score_ai_visibility(brand, queries, competitors) -> dict` — wraps existing `src/geo/providers/cloro.py`; returns per-platform SOV + gaps
  - `scan_competitor_pages(prospect_domain, competitor_domains) -> dict` — fetch sitemaps, grep `/vs/`, `/alternatives/`, `/compare/`
  - `gather_voc(brand, platforms) -> dict` — wraps existing Xpoz + IC + review adapters + Apify G2/Capterra actors
  - `detect_analytics_tags(rendered_page) -> dict` — GA4/GTM/Segment/Mixpanel/Meta Pixel/TikTok Pixel presence + declared events + server-side tagging detection. Shares regex-rule helpers with `tech_stack` but is a separate function because analytics/tag findings feed the conversion + monitoring lenses specifically, while `tech_stack` feeds the SEO + GEO lenses.
  - **`analyze_backlinks(domain) -> dict`** — DataForSEO Backlinks API. Prospect-domain-only in Stage 1. Returns `{total_backlinks, referring_domains, dataforseo_rank, new_lost_30d, top_referring_domains[{domain, rank, links_count, category}], anchor_text_distribution, toxic_signals}`. The `dataforseo_rank` field is DataForSEO's proprietary authority score (0–1000 scale) — it is NOT equivalent to Moz DA or Ahrefs DR and the deliverable names it explicitly to avoid confusion. Feeds SEO lens (prospect's linking health); head-to-head competitor backlink comparison runs inside the **U4 competitive lens in Stage 2**, after `derive_competitors` has resolved the final competitor list (see U4 Approach). Graceful degradation if API rate-limited → `partial=true` with subset data.
  - **`audit_page_speed(urls) -> dict`** — Google PageSpeed Insights API (free, 25K queries/day). Called for up to ~10 key URLs (homepage, top 3 landing pages from sitemap, pricing, top blog post). Internally calls both `mobile` and `desktop` strategies per URL — callers get both in one return. Return shape: `{url: {mobile: {performance_score, lcp, inp, cls, opportunities[], diagnostics[]}, desktop: {...same shape...}}}`. Feeds SEO lens (Core Web Vitals is a Google ranking factor) + conversion lens (page speed directly affects bounce rate). Per-URL failures stay partial without failing the whole primitive.
  - **`historical_rank_trends(domain, keywords, timeframe="6mo") -> dict`** — DataForSEO Labs `Historical Search Volume` endpoint (keyword demand trend) + `Historical Rank Overview` endpoint (prospect's rank trajectory over time). Returns `{organic_traffic_trend: [{month, sessions_est}], keyword_rank_history[{keyword, rank_series[{date, rank}]}], visibility_index_series[{date, index}], notable_drops[{keyword, from_rank, to_rank, date}], notable_gains[same shape]}`. Feeds SEO lens (trend context turns a static finding into "declining for 6 months — urgent") + synthesis (historical context enables better "surprises"). Fallback: if no historical data available (brand-new domain), returns `{partial: true, missing_fields: ["historical"]}` and lenses proceed with snapshot-only signals.
  - **`keyword_gap_analysis(domain) -> dict`** — DataForSEO Labs `Competitors Keywords` + `Domain Intersection` endpoints. Auto-discovers top 20–50 SERP competitors by keyword overlap (independent of form-provided competitor list — that list seeds other primitives; this one surfaces whoever is actually competing for the prospect's keyword space). Returns `{prospect_keywords_count, top_competitors_by_overlap[{domain, overlap_count, missing_from_prospect_count, avg_rank}], keyword_gaps[{keyword, search_volume, competitor_rank, competitor_domain, opportunity_score}]` (top 100 gaps ranked by opportunity score = volume × ease × commercial intent)`}`. Feeds SEO lens (the biggest quick-win inventory SaaS users expect) + competitive lens (SERP-competitor picture). Graceful degradation on API quota exhaustion → returns top 25 gaps with `partial=true`.
  - **`analyze_serp_features(keywords) -> dict`** — DataForSEO SERP API. For up to 30 prospect-relevant keywords (drawn from `historical_rank_trends` + `keyword_gap_analysis` output — not independently picked, so this primitive runs AFTER those two), returns per-keyword SERP feature inventory: `{keyword: {featured_snippet: {present, owner_domain, opportunity_score}, people_also_ask[{question, answer_owner}], knowledge_panel: {present, entity}, ai_overview: {present, cited_domains[]}, related_searches[], video_carousel[], shopping_results[], image_pack}, ...}`. Feeds SEO lens (featured-snippet capture opportunities is a top SaaS insight) + GEO lens (`ai_overview.cited_domains` is the strongest public signal of AI-search citation, complementing `score_ai_visibility`). Graceful degradation on per-keyword failure leaves that keyword marked `partial`.
  - **`analyze_internal_links(domain, sitemap_urls) -> dict`** — Internal link-graph analysis (Screaming Frog / Sitebulb parity). Consumes sitemap output (already produced by `freddy sitemap` subprocess). Fetches up to 200 pages via `httpx` (not Playwright — link extraction doesn't need JS rendering; static HTML + BeautifulSoup is faster and cheaper); for sites under 200 pages, does a full crawl. Extracts `<a href>` tags, builds an internal link graph, computes depth from homepage. Returns `{page_count_crawled, crawl_coverage_pct, orphan_pages[{url, has_canonical, indexable}], deep_pages[{url, min_clicks_from_home}] (threshold: >3 clicks), broken_internal_links[{from_url, to_url, status_code}], link_equity_distribution: {top_linked_pages[{url, incoming_links}], tail_pages_pct}, anchor_text_internal_distribution}`. Feeds SEO lens (orphans and deep pages are common fixable wins that are visible in Screaming Frog but not in SEMrush/Ahrefs by default). Graceful degradation: large sites exceeding 200 pages → `partial=true` with sample; crawler blocked by robots.txt → `partial=true` with what was reached; total crawl cap 10 min to bound wall-clock.
- Modify `pyproject.toml`: add `playwright>=1.45.0`, `python-Wappalyzer>=0.4.0`, `beautifulsoup4>=4.12.0` (for `analyze_internal_links` HTML parsing). DataForSEO calls use existing `src/providers/dataforseo.py` client (already in the repo for SEO/competitive/monitoring audits). Google PageSpeed Insights + internal-link crawl use `httpx` directly — no new dependency beyond BeautifulSoup.
- Environment: `PAGESPEED_API_KEY` added to required env for `audit_page_speed` (free key from Google Cloud Console). DataForSEO creds already configured.
- Test: `tests/audit/test_primitives.py` — integration test hitting 2–3 real URLs per primitive

**Approach:**
- `RenderedFetcher.fetch(url)` returns a dict: `{url, html, ldjson_blocks, network_requests, status, render_failed, screenshot_path}`. Single browser context per audit (passed in); falls back to `httpx.get()` on render failure.
- Each primitive ~50–120 LOC, pure function, no shared state. Returns `{result: ..., partial: bool, missing_fields: [], cost_usd: float}`.
- Graceful degradation throughout: source unavailable → `partial: true`, no exceptions escape primitives.
- Shared LLM extraction helper (`_extract_structured(prompt, text, schema)`) for careers + firmographic scrapers — Sonnet with Pydantic output model.

**Test scenarios:**
- Happy: tech_stack on a Shopify store returns cms=Shopify + analytics list.
- Happy: enumerate_subdomains on stripe.com returns 30+ subdomains.
- Happy: score_ai_visibility for "notion" with 3 queries returns per-platform citation counts within $0.20.
- Happy: `analyze_backlinks("notion.so")` returns referring_domains > 1000 + non-empty top_referring_domains with rank/category fields populated.
- Happy: `audit_page_speed(["https://notion.so"])` returns both `mobile` and `desktop` nested entries with performance_score (0–100) + LCP/INP/CLS for each.
- Happy: `historical_rank_trends("notion.so", ["project management"])` returns a 6-month rank_series with at least some data points.
- Happy: `keyword_gap_analysis("notion.so")` returns at least 25 keyword_gaps with populated opportunity_score; top_competitors_by_overlap contains recognizable Notion competitors (Coda, Obsidian, Roam, etc.).
- Happy: `analyze_serp_features(["project management software"])` returns per-keyword dict with at least `featured_snippet`, `people_also_ask`, and `ai_overview` keys populated.
- Happy: `analyze_internal_links("notion.so", [...200 urls])` returns populated `orphan_pages`, `deep_pages`, and `link_equity_distribution`; `page_count_crawled` between 100 and 200 (respecting the cap).
- Edge: Crunchbase page 404 → firmographic returns partial=true + missing_fields.
- Edge: Cloro rate-limited → ai_visibility returns partial=true, cached data.
- Edge: DataForSEO Backlinks API credits exhausted → `analyze_backlinks` returns partial=true with the subset it fetched before hitting the limit; downstream lens proceeds with "backlink detail partial" flag.
- Edge: PageSpeed Insights returns 429 on a URL → that URL's entry is `{partial: true, error: "rate_limited"}`; other URLs' entries still present.
- Edge: prospect domain is brand-new (no historical data) → `historical_rank_trends` returns `{partial: true, missing_fields: ["historical"]}` and the brief notes "insufficient history for trend analysis."
- Edge: `keyword_gap_analysis` DataForSEO Labs quota exhausted → returns top 25 gaps + `partial=true`; synthesis proceeds with subset.
- Edge: `analyze_serp_features` called with 0 keywords (upstream primitives both returned `partial: true`) → returns `{partial: true, missing_fields: ["all_keywords"]}` without failing Stage 1.
- Edge: `analyze_internal_links` on a very large site (10K+ URLs in sitemap) → caps at 200-page sample, `partial=true`, `crawl_coverage_pct` populated so the lens can note the partial depth in its narrative.
- Edge: `analyze_internal_links` hit by robots.txt blocking → returns whatever was crawled before the block with `partial=true`.
- Integration: all 15 primitives run on one real prospect without exceptions; total wall-clock under 25 min (realistic range 15–25 min — `audit_page_speed` ~3–8 min + `analyze_internal_links` ~3–10 min depending on site size + `keyword_gap_analysis` + `historical_rank_trends` + `analyze_serp_features` collectively ~2–5 min).

**Done when:** Each primitive runs standalone from a python REPL against a real URL and returns a non-empty, schema-valid result. The 6 SaaS-parity primitives (`analyze_backlinks`, `audit_page_speed`, `historical_rank_trends`, `keyword_gap_analysis`, `analyze_serp_features`, `analyze_internal_links`) produce data comparable in shape to what a prospect would see from Ahrefs / PageSpeed Insights / SEMrush / Screaming Frog respectively.

---

### U3. Stages 0 + 1: intake + pre-discovery with brief synthesis

**Goal:** Stage 0 (Python-only) populates workspace from intake form. Stage 1 runs all 15 primitives in Python (with a small ordering constraint — see U2), then makes ONE Opus call to synthesize a `prospect-brief.md` + `signals.json`.

**Files:**
- Create `src/audit/stages.py` with `stage_0_intake(state)` and `stage_1_prediscovery(state)` functions
- Create `src/audit/prompts.py` with `PREDISCOVERY_SYNTHESIS_PROMPT` string constant
- Test: `tests/audit/test_stages_0_1.py`

**Approach:**
- `stage_0_intake`: reads intake form data from `audit_pending` row (populated by Unit 7), writes `clients/<slug>/audit/intake/form.json` + `clients/<slug>/config.json` (prospect Client model). No LLM.
- `stage_1_prediscovery`:
  1. Opens shared `RenderedFetcher` context
  2. Gathers signals by running both the 15 new primitives from U2 AND these existing freddy CLI commands via subprocess: `freddy sitemap <url>`, `freddy scrape <url>`, `freddy detect <url> --full`, `freddy audit seo <domain>`, `freddy audit competitive <domain>`, `freddy audit monitor "<brand>"`, `freddy visibility --brand <x> --keywords <y>`. Each result (primitive or CLI) writes to `clients/<slug>/audit/prediscovery/signals.json` under a top-level key.
    2a. Competitor discovery is explicit: a small helper `derive_competitors(form_data, dataforseo_serp, foreplay_ad_categories) -> list[str]` merges (a) prospect-provided competitors from intake form, (b) top-SERP overlap from DataForSEO, (c) shared ad-category competitors from Foreplay/Adyntel. The Opus synthesis call reconciles into a final ranked list of 3–5 competitors written to `signals.json:competitors`. This list is the input to `score_ai_visibility` and `scan_competitor_pages`.
  3. One Opus call (`PREDISCOVERY_SYNTHESIS_PROMPT`, directive skeleton) takes signals.json + form data, outputs structured `PrediscoveryBrief` (Pydantic envelope): ICP hypothesis with confidence label, inferred competitor list, pain points, tech posture summary, AI-visibility headline, hypotheses to validate on walkthrough (agent decides count). `session_id` + ResultMessage telemetry persisted via `state.record_session("prediscovery_synthesis", result)`.
  4. Writes `brief.md` (prose) + `brief.json` (structured)
- Concurrency: `asyncio.Semaphore(10)` across the 15 primitives + 7 `freddy` CLI subprocesses to bound Playwright / subprocess handles (infra limit, not cognitive cap). Ordering constraints (`analyze_serp_features` depends on `historical_rank_trends` + `keyword_gap_analysis`; `analyze_internal_links` depends on `freddy sitemap` subprocess) are handled with a small three-phase fan-out rather than single-phase gather.
- Telemetry: per-primitive cost/duration rows appended to `cost_log.jsonl`; no per-stage budget.

**Test scenarios:**
- Happy: intake form with URL → Stage 0 writes valid config.json + form.json.
- Happy: Stage 1 end-to-end on a known prospect produces brief.md covering all primitive-sourced signal categories + ICP hypothesis.
- Edge: 4 of 15 primitives return partial (e.g., backlinks API rate-limited + Crunchbase 404 + no historical data + Cloro throttled) → brief flags "partial signals" + proceeds.
- Edge: Semaphore(10) caps concurrent primitive/subprocess fan-out; remaining work queues. Two-phase run ensures `analyze_serp_features` waits for upstream dependencies without blocking other primitives.
- Integration: brief.json validates against `PrediscoveryBrief` Pydantic schema; `cost_log.jsonl` has one row per primitive/subprocess + one for the synthesis Opus call.

**Done when:** Running `freddy audit run --client <dogfood-prospect> --stage 1` produces a brief.md that JR reads and finds non-trivially useful without manual editing.

---

### U4. Stage 2: parallel multi-lens analysis

**Goal:** 5 Claude Agent SDK sessions (Sonnet) run in parallel via `asyncio.gather` with a `Semaphore(5)`, each producing a canonical `LensOutput` with structured findings.

**Files:**
- Create `src/audit/stages.py:stage_2_lenses` function
- Create `src/audit/lens_models.py` — `Finding`, `LensOutput` Pydantic models
- Extend `src/audit/prompts.py` with 5 lens-specific prompts: `LENS_SEO_PROMPT`, `LENS_GEO_PROMPT`, `LENS_COMPETITIVE_PROMPT`, `LENS_MONITORING_PROMPT`, `LENS_CONVERSION_PROMPT`
- Create `src/audit/references/` directory with 6 consolidated reference files:
  - `stats-library.md`, `seo-lens-references.md`, `geo-lens-references.md`, `competitive-lens-references.md`, `monitoring-lens-references.md`, `conversion-lens-references.md`, `voc-source-playbooks.md` (the conversion + voc files merge 7+3 Corey skills respectively — see consolidation table in "References" section below)
- Test: `tests/audit/test_stage_2_lenses.py`

**Approach:**
- `Finding` schema (envelope, not content constraint): `{id, lens, title, severity(0-3), reach(0-3), feasibility(0-3), evidence_urls[], evidence_quotes[], recommendation, effort_band(S/M/L), confidence(H/M/L), category_tags[]}`. Agent fills any count of Findings freely.
- `LensOutput`: `{lens_name, findings[], lens_summary, metadata{session_id, total_cost_usd, duration_ms, num_turns, model_usage, partial}}`.
- Each lens agent: open `ClaudeSDKClient` with a **directive** `system_prompt` (role / objective / context / tools+heuristics / effort-scaling / quality bar / output contract / termination — not a step-by-step playbook), inject `prospect-brief.md` + full `signals.json` + matching `src/audit/references/<lens>-references.md`. Config: `tools={"type":"preset","preset":"claude_code"}` (full Claude Code toolbelt incl. WebFetch, WebSearch, Task, Bash, Read/Write/Grep/Glob), `permission_mode="bypassPermissions"` for unattended roaming, `enable_file_checkpointing=True`, `max_turns=500` (sentinel runaway-loop backstop — not a budget; normal lens runs are 15–60 turns), `model=sonnet`. Hooks wired: `PostToolUse` → loop-detection (hash `(tool_name, tool_input)`; Slack-alert on 5× consecutive, no abort) + telemetry; `PreCompact` → archive full transcript to `clients/<slug>/audit/lenses/<lens>/transcripts/`; `Stop` → flush `ResultMessage` telemetry to `cost_log.jsonl` and record `session_id` via `state.record_session`.
- Run 5 lenses via `asyncio.gather(*[run_lens(l) for l in lenses])` with `Semaphore(5)` (infra concurrency, not cognitive cap). Each session is an isolated SDK subprocess.
- **Competitive lens performs head-to-head comparison** using the final competitor list from Stage 1's Opus synthesis (`signals.json:competitors`). It re-invokes DataForSEO Backlinks + Labs Competitors Keywords for each competitor domain and surfaces linking gaps + keyword gaps in its narrative. This is where competitor-comparison data is actually produced; Stage 1's `analyze_backlinks` + `keyword_gap_analysis` primitives deliberately produce prospect-only output because Stage 1 runs before `derive_competitors` resolves the final list.
- Each writes to `clients/<slug>/audit/lenses/<lens>/{output.json, narrative.md}`.
- On lens exception (not turn/budget — those don't exist): mark `LensOutput.partial = True`, log to `state.sessions[<lens>].error`, pipeline continues. If ≥3 lenses raise exceptions, orchestrator surfaces to JR (operational safety, not agent cap) rather than auto-publishing a broken audit. Crashed lenses are resumable on a subsequent `freddy audit run --resume` via `resume=<session_id>`.

**Test scenarios:**
- Happy: all 5 lenses complete with `ResultMessage.subtype=="success"` on a dogfood prospect; findings count logged to telemetry, not asserted.
- Happy: Findings validate against canonical envelope schema; count and severity distribution are agent judgment.
- Happy: each lens's `session_id` persisted to `state.sessions`; `PostToolUse` + `PreCompact` hooks fire and emit telemetry rows.
- Edge: one lens's Claude API error → retried once → raised as partial; subsequent `freddy audit run --resume` picks up from `state.sessions[<lens>].session_id`.
- Edge: loop-detection hook observes 5× consecutive identical tool call → Slack alert fires + telemetry row written; agent run is NOT aborted.
- Integration: Stage 2 telemetry logged per lens to `cost_log.jsonl` (total_cost_usd, duration_ms, num_turns, model_usage). No cost assertion.

**Done when:** Stage 2 dogfood produces 20–40 ranked findings across 5 lenses with evidence citations traceable back to signals.json or prospect URLs.

---

### U5. Stage 3: synthesis (ported brief.py pattern)

**Goal:** Adapt Freddy's `src/competitive/brief.py` async-fan-out-plus-Opus-synthesis pattern to produce ranked findings, 3–5 surprises, and the audit report body.

**Files:**
- Create `src/audit/brief.py` — ported from `/Users/jryszardnoszczyk/Documents/GitHub/freddy/src/competitive/brief.py`, adapted (replace 6 CI sections with the 9 audit report sections)
- Create `src/audit/stages.py:stage_3_synthesis` function
- Extend `src/audit/prompts.py` with `SYNTHESIS_SECTION_PROMPT` (per-section), `SYNTHESIS_MASTER_PROMPT` (final merge), `SURPRISE_QUALITY_CHECK_PROMPT` (paired second-pass verification)
- Test: `tests/audit/test_synthesis.py`

**Approach:**
- `stage_3_synthesis`:
  1. Reads all 5 `lens_outputs[]` + `prospect-brief.md`
  2. Soft quality check: logs a warning to `cost_log.jsonl` if any lens has 0 findings AND no `not_applicable=true` flag, but does NOT abort — synthesis renders that lens's section gracefully ("no issues surfaced at this depth of analysis").
  3. Calls `AuditBrief.generate()` (ported from Freddy): async fan-out of 9 section LLM calls (Opus, directive prompts); no per-call deadline — sections complete when complete. Each call uses `enable_file_checkpointing=True`; `session_id`s recorded via `state.record_session`. Results merged by a final Opus synthesis call.
  4. **Evaluator-optimizer self-critique** (Anthropic pattern): runs `SURPRISE_QUALITY_CHECK_PROMPT` as a second Opus call that critiques each surprise against four bars (non-obvious · evidence-backed · tied to revenue/cost · feasible). The critique is passed *back to the synthesis agent* along with the original surprises — the agent decides whether to revise, retain, or mark them with `quality_warning=true`. At most one regeneration pass; no forced override. The four bars also live inline in `SYNTHESIS_MASTER_PROMPT` so the synthesis agent self-assesses before the critique pass.
  5. **Computes `gofreddy_health_score`** (0–100) as a final deterministic Python rollup AFTER all LLM calls complete. Weighted sum of primitive-derived health signals: **SEO health 30%** (driven by Core Web Vitals pass rate + schema coverage + `analyze_internal_links` orphan-page % + `historical_rank_trends` direction), **backlink health 15%** (driven by `analyze_backlinks` toxic-link % + referring-domain velocity + `dataforseo_rank`), **AI visibility 15%** (driven by `score_ai_visibility` SOV + `analyze_serp_features.ai_overview` citation presence), **conversion health 15%** (driven by Core Web Vitals + form-CRO signals from conversion lens output), **competitive position 10%** (driven by `keyword_gap_analysis` gap count vs. top competitor + backlink gap), **technical health 15%** (driven by `tech_stack` modernity + `detect_analytics_tags` coverage + schema validity). Returns `{overall: 0-100, per_lens: {seo, geo, competitive, monitoring, conversion}, signal_breakdown: {signal_name: {score, weight, contribution_pts}}, band: "red"|"yellow"|"green"}` where band = red (0–40), yellow (41–70), green (71–100). Weights + signal→score mapping formulas are deferred to implementation and re-tuned after the first 10 audits; the plan specs the shape and responsibility.
  6. Writes `clients/<slug>/audit/synthesis/{findings.md, surprises.md, report.md, report.json}`. `report.json` contains top-level `health_score` key with the structure above.
- 9 report sections (envelope contract for rendering): Hero TL;DR (leads with health_score + per-lens breakdown), Executive Summary, What We Found (per lens), Surprises, Competitive Positioning, AI Visibility Posture, Technical Posture, Recommended Next Steps (placeholder for Stage 4 output), About This Audit. Agent decides per-section length, number of findings, number of surprises within each section's quality bar.

**Test scenarios:**
- Happy: synthesis on dogfood Stage 2 output produces findings.md + surprises.md + report.md (9 sections). Counts of findings/surprises logged to telemetry, not asserted.
- Happy: `state.sessions["synthesis_*"]` entries populated for each of the 9 section calls + final merge + quality-critique call.
- Happy: `report.json:health_score` populated with `{overall, per_lens, signal_breakdown, band}` after synthesis completes; overall between 0–100; band correct for the overall value.
- Edge: one lens has 0 findings + not_applicable=true → synthesis renders "not applicable" section gracefully.
- Edge: one lens has 0 findings AND no not_applicable flag → warning logged to `cost_log.jsonl`; synthesis renders "no issues surfaced" section and proceeds.
- Edge: surprise quality-critique surfaces weaknesses → synthesis agent reviews critique, decides whether to revise or keep with `quality_warning=true`. No forced regeneration beyond one optional pass.
- Integration: synthesis telemetry logged (session_ids, per-call cost, duration). No cost/time assertion.

**Done when:** Synthesis output reads like a credible audit JR would sign off without rewriting.

---

### U6. Stage 4: proposal with capability registry

**Goal:** Opus picks the capability IDs it judges best fit the findings — count and tier mix are the agent's decision — and writes narrative per capability; Python validates IDs + applies pricing deterministically.

**Files:**
- Create `src/audit/capability_registry.yaml` with ~15 starter capabilities spanning SEO / GEO / competitive / content / monitoring across fix-it / build-it / run-it tiers
- Create `src/audit/capability_registry.py` — YAML loader + `pick_pricing(capability_id, prospect_size_band) -> (price, price_range)` function applying multipliers (small 0.8 / mid 1.0 / enterprise 1.3), clamped to `price_range`
- Create `src/audit/stages.py:stage_4_proposal` function
- Extend `src/audit/prompts.py` with `PROPOSAL_PROMPT`
- Test: `tests/audit/test_capability_registry.py`, `tests/audit/test_stage_4_proposal.py`

**Approach:**
- YAML schema per capability: `id, name, tier, scope, price_range [min,max], typical_price, prerequisites[], jr_time_hours`.
- `stage_4_proposal`:
  1. Reads synthesis + prospect context
  2. Opus call (`PROPOSAL_PROMPT`, directive skeleton): picks capability IDs matching findings + writes narrative per capability. Prompt carries the **heuristic** "offer at least one Fix-it and one Run-it when the findings support them; span tiers when natural," not a hard count mandate — a 2-capability or 5-capability proposal is fine when that's what the findings warrant. `session_id` persisted via `state.record_session("proposal", result)`; `enable_file_checkpointing=True`.
  3. Python validates returned IDs exist in registry (raises `ProposalValidationError` on hallucination — operational safety, not an agent cap)
  4. Python applies pricing via `pick_pricing()`; LLM never touches numbers
  5. Writes `clients/<slug>/audit/proposal/{proposal.md, proposal.json}`
- Starter registry entries include: `geo-fix-infra`, `seo-fix-schema-sitewide`, `seo-fix-internal-linking`, `content-build-pseo-engine`, `competitive-build-monitoring`, `geo-build-llms-txt-suite`, `seo-retainer-basic`, `monitoring-retainer`, `content-retainer`, `full-distribution-retainer`, and 5 more.

**Test scenarios:**
- Happy: high-severity findings → proposal picks capabilities (count = agent judgment) with narrative tied to specific findings.
- Happy: pricing deterministic — same capability + size_band always yields same number.
- Happy: `state.sessions["proposal"].session_id` populated for resumability.
- Edge: findings only support Build-it and Run-it tiers → proposal cleanly omits Fix-it; tiers offered match what findings warrant.
- Edge: LLM returns capability ID not in registry → raises `ProposalValidationError` (operational safety).
- Integration: proposal total always matches `sum(pick_pricing(id, size) for id in capabilities)`.

**Done when:** Proposal has scoped capabilities (count = agent judgment), narrative ties to specific findings, prices are registry-deterministic.

---

### U7. Stage 5: deliverable (HTML + PDF + publish)

**Goal:** Render final HTML via Jinja2 + Tailwind, generate PDF via WeasyPrint, upload to R2, publish at `reports.gofreddy.ai/<slug>`.

**Files:**
- Create `src/audit/templates/audit_report.html.j2` — single Jinja2 template (no component library; inline partials)
- Create `src/audit/renderer.py` — `render_html(state)` + `render_pdf(html_path)` functions
- Create `src/audit/stages.py:stage_5_deliverable` function
- Create `cloudflare-workers/audit-hosting/worker.js` + `wrangler.toml` — validates ULID slug format, serves files from R2, 404 otherwise
- Create `cli/freddy/commands/audit.py:publish` subcommand — uploads `deliverable/` to R2
- Test: `tests/audit/test_renderer.py`

**Approach:**
- Template has 9 sections matching report.md. Tailwind-styled (via CDN link for simplicity, not build step). Embeds screenshots from `prediscovery/screenshots/`. Uses AI-generated prose from `report.md` + proposal + surprises.
- **Hero TL;DR leads with the health score**: a large 0–100 numeral (color-coded by band — red 0–40, yellow 41–70, green 71–100) + a compact per-lens breakdown (horizontal bar chart or 5-axis radar). This is the metric prospects will screenshot and share internally — worth disproportionate design investment. Template reads `report.json:health_score` directly; no LLM involved in rendering the number.
- WeasyPrint renders same HTML → PDF (≤ 5 MB for email attachability).
- Stage 5 generates ULID slug, writes to state.json, produces `deliverable/{report.html, report.pdf, assets/}`.
- `freddy audit publish --client <slug>` uploads deliverable tree to R2 bucket `gofreddy-audits/<ulid>/`; prints final URL `https://reports.gofreddy.ai/<ulid>`.
- Cloudflare Worker on `reports.gofreddy.ai/*`: validates path matches ULID regex, proxies to R2; else 404.
- Every rendered page (HTML + PDF) includes a footer partial `<footer class="gofreddy-footer">Prepared by GoFreddy · <a href="https://gofreddy.ai">gofreddy.ai</a></footer>` — preserved on every page of the PDF via WeasyPrint `@page { @bottom-center }` CSS rule.

**Test scenarios:**
- Happy: render produces valid HTML (W3C validator passes) + openable PDF.
- Happy: screenshots embedded correctly in both HTML and PDF.
- Happy: Hero TL;DR displays `report.json:health_score.overall` as a large number with correct color band (red/yellow/green); per-lens breakdown shows all sub-scores.
- Edge: proposal has 2 capabilities → template omits third tier gracefully.
- Edge: synthesis has a `not_applicable` lens → template renders collapsed section.
- Integration: end-to-end: Stage 5 → `freddy audit publish` → curl to `reports.gofreddy.ai/<ulid>` returns 200 with HTML; bogus ULID returns 404.

**Done when:** Dogfood audit is viewable at a live `reports.gofreddy.ai/<slug>` URL and downloadable as a PDF.

---

### U8. Intake lead-capture + Slack notification

**Goal:** Capture form submissions into a Supabase lead database and ping JR on Slack. No auto-firing of the audit pipeline — JR manually creates the client workspace and runs stages via Claude Code locally. The laptop poller and auto-firing are explicitly deferred to a future plan.

**Files:**
- Create `landing/audit-intake.html` — Tailwind-styled form matching existing landing page
- Create `cloudflare-workers/audit-intake/worker.js` + `wrangler.toml` — HMAC-sign + relay to Fly API
- Create `src/api/routers/audit_intake.py` — `POST /v1/audit/intake` (writes Supabase row + emits Slack webhook), `GET /v1/audit/pending` (for manual review via CLI)
- Modify `src/api/main.py` to register the intake router
- Create `supabase/migrations/20260420000001_audit_intake.sql` — `audit_pending` table
- Extend `cli/freddy/commands/client.py`: add `freddy client new <slug> --from-pending <id>` flag so JR can populate a workspace from a Supabase lead row in one command
- Test: `tests/api/test_audit_intake.py`

**Approach:**
- `audit_pending` table: `id, slug (ulid), submitted_at, form_data jsonb, consumed_at nullable` (consumed_at set when JR runs `freddy client new --from-pending`). No `status` state machine — simpler without a poller orchestrating stages.
- Form fields: name, email, company, URL, size_band, budget_band, 3 top priorities, timeline, decision_maker, what they've tried, current agency status.
- Cloudflare Worker: HMAC-signs + POSTs to Fly API. Turnstile on form for spam mitigation.
- `POST /v1/audit/intake` handler: inserts Supabase row, emits Slack webhook with `{slug, company, url, priorities[], budget_band}` — Slack message template: *"🎯 New lead: {company} ({url}) — run `freddy client new {slug} --from-pending {id}` then `freddy audit run --client {slug} --stage 1`."* Gives JR a copy-pasteable next command.
- `freddy client new --from-pending <id>`: reads Supabase row, creates `clients/<slug>/audit/` workspace, populates `intake/form.json` + `config.json`, marks `consumed_at`. Does NOT run any stage.

**Test scenarios:**
- Happy: form submit → Cloudflare Worker → Fly API writes pending row → Slack webhook fires with copy-pasteable command.
- Happy: `freddy client new test --from-pending <id>` reads the row and creates a valid workspace; `consumed_at` is set.
- Edge: Cloudflare Worker's HMAC sig is invalid → Fly API returns 401; no DB write; Slack silent.
- Edge: Supabase row already has `consumed_at` → `--from-pending` warns + exits without overwriting.
- Integration: submit a real test form → row lands in Supabase + Slack ping received with valid command; JR runs it and lands in a clean workspace.

**Done when:** Submitting the form on `gofreddy.ai/audit-intake` lands a lead in Supabase and Slack-pings JR with a ready-to-run CLI command. Zero pipeline stages have fired.

---

### U9. Evaluation harness

**Goal:** Tiny eval harness for iterating on the 8+ directive prompts without shipping bad audits to real prospects. Lets us refine lens + synthesis + proposal prompts against a frozen fixture set and score changes objectively. Built early in the cycle — inserted after U3 so lens prompts (U4) can be tuned against it, then reused through U8. Runs parallel to lens/synthesis/proposal implementation rather than blocking them.

**Files:**
- Create `src/audit/eval/__init__.py`, `src/audit/eval/runner.py`, `src/audit/eval/rubric.py`, `src/audit/eval/fixtures/` (3 frozen dogfood prospects with signals.json + expected brief themes)
- Create `cli/freddy/commands/audit.py:eval` subcommand — `freddy audit eval [--stage N] [--fixture <slug>] [--baseline <run-id>]`
- Create `src/audit/eval/rubric.md` — scoring rubric per stage (brief coherence · finding specificity · evidence density · surprise non-obviousness · proposal fit-to-findings)
- Test: `tests/audit/test_eval_harness.py`

**Approach:**
- Fixtures are real signals.json + brief.md + lens outputs from 3 dogfooded prospects (mix of sizes, verticals). Checked into git under `src/audit/eval/fixtures/<slug>/`.
- `runner.py`: `run_eval(stage, fixtures, prompt_variant) -> EvalReport`. Runs the target stage against each fixture using the candidate prompt set; writes outputs to `clients/__eval__/<run-id>/<fixture>/`.
- `rubric.py`: per-stage scoring via Opus (LLM-as-judge) against the rubric. Returns `{fixture, stage, score_0_10, per_criterion_scores{}, reviewer_notes}`. Human-in-the-loop: JR can override or annotate.
- Eval report: markdown table comparing candidate prompts vs. a named baseline. Highlights regressions and wins.
- **This is telemetry for prompt development, not a gate.** Nothing in the eval harness is in the production audit path.
- When to re-run: before merging any prompt change in U4/U5/U6/U8; after Stage 1 output shape changes; monthly sanity check against fixtures.

**Test scenarios:**
- Happy: `freddy audit eval --stage 2 --fixture acme` runs all 5 lens agents against the acme fixture's signals.json; report compares findings to baseline.
- Happy: rubric scoring on a known-good prompt yields ≥7/10; on a known-bad variant yields <5/10.
- Happy: baseline comparison table flags a regression when a prompt change drops rubric score by ≥1 point on any fixture.
- Edge: fixture missing signals.json → runner skips with clear error.
- Integration: a prompt tweak to `LENS_SEO_PROMPT` → run eval → diff report → JR accepts or rejects based on rubric delta + sample reads.

**Done when:** `freddy audit eval --stage 2` produces a markdown diff report in under 15 min and is the default artifact JR reviews before merging any prompt-affecting PR.

---

### U10. Commercial flow: Stripe payment + sales/walkthrough calls

**Goal:** Wire the commercial plumbing between Stage 1 and Stage 2 (payment) and the two-call sales motion. JR sends a Stripe Checkout URL after the sales call; payment webhook flips `state.payment.paid`; Stripe webhook plus sales-call + walkthrough-call Fireflies webhooks all write into the audit workspace. No pipeline stage auto-fires — the webhooks only update state and ping JR on Slack.

**Files:**
- Create `src/audit/stripe.py` — Stripe Checkout Session creation + webhook signature verify (uses `stripe` Python SDK)
- Create `src/audit/sales_call.py` — Fireflies sales-call fit-signals extraction (Opus)
- Modify `src/audit/fireflies.py` — shared HMAC verify + GraphQL transcript fetch helpers (used by both sales and walkthrough)
- Create `src/api/routers/audit_stripe.py` — `POST /v1/audit/stripe` (Stripe webhook → `state.payment.paid = True` + Slack ping)
- Create `src/api/routers/audit_sales_call.py` — `POST /v1/audit/sales-call` (Fireflies webhook for sales call)
- Create `src/api/routers/audit_walkthrough.py` — `POST /v1/audit/walkthrough` (Fireflies webhook for post-delivery walkthrough)
- Modify `src/api/main.py` to register the three new routers
- Create `supabase/migrations/20260420000002_audit_payment.sql` — `payment_events` table (audit log of Stripe webhook events, idempotency dedupe)
- Extend `cli/freddy/commands/audit.py`:
  - `freddy audit send-invoice --client <slug> [--amount 1000] [--description "..."]` — creates a Stripe Checkout Session, writes URL + session_id to `state.payment.stripe_session_id`, prints URL for JR to copy/send
  - `freddy audit mark-paid --client <slug> --stripe-id <intent-id>` — manual fallback that sets `state.payment.paid = True` without waiting for webhook (for test/dev or if webhook fails)
  - `freddy audit ingest-transcript --client <slug> --call-type {sales,walkthrough} --file <path>` — manual fallback if either Fireflies webhook fails
- Extend `src/audit/prompts.py` with `SALES_CALL_FIT_SIGNALS_PROMPT` + `WALKTHROUGH_FIT_SIGNALS_PROMPT` (directive skeleton, distinct criteria per call type)
- Add `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `FIREFLIES_WEBHOOK_SECRET` to env-required list
- Test: `tests/audit/test_stripe.py`, `tests/audit/test_sales_call.py`, `tests/api/test_audit_webhooks.py`

**Approach:**
- **Stripe Checkout Session**: `create_checkout_session(slug, amount_usd, metadata={"audit_slug": slug})`. Mode `payment`, success_url and cancel_url point at static pages on gofreddy.ai. Session metadata carries `audit_slug` so the webhook knows which workspace to update.
- **Stripe webhook handler** (`POST /v1/audit/stripe`): verify signature with `STRIPE_WEBHOOK_SECRET`, read `checkout.session.completed` event, dedupe via `payment_events` table (`event_id` unique key), load audit state by `metadata.audit_slug`, call `state.record_payment(stripe_event)` → atomic state.json rename + git commit, Slack-ping JR: *"💰 Payment received for {slug} ({company}, ${amount}). Run `freddy audit run --client {slug}` to start Stage 2."*
- **Sales-call Fireflies webhook** (`POST /v1/audit/sales-call`): verify HMAC-SHA256, fetch transcript, Opus extracts `SalesFitSignals` (directive prompt — criteria: *ICP hypothesis validation, decision-maker confirmed, budget alignment for $1K audit, timeline, objections, stated next step, go/no-go confidence*). Writes `clients/<slug>/audit/sales_call/fit_signals.json`. Slack-pings JR with summary. Session telemetry logged via `state.record_session("sales_call_fit_signals", result)` and `state.record_call("sales_call", fit_signals)`.
- **Walkthrough-call Fireflies webhook** (`POST /v1/audit/walkthrough`): same shape as sales-call, but Opus extracts `WalkthroughFitSignals` (criteria: *which findings resonated, tier preference Fix-it/Build-it/Run-it, objections to engagement, budget for engagement, stated next step, confidence to close*). Writes `clients/<slug>/audit/walkthrough/fit_signals.json` + `state.record_call("walkthrough_call", fit_signals)`.
- **Slug resolution for webhooks**: Fireflies meeting metadata should include the audit slug; plan has JR setting the meeting title to include `<slug>` or tagging the meeting. Webhook handler parses title for slug pattern; if ambiguous, writes to a quarantine path and Slack-pings JR to reconcile manually.
- **Idempotency**: both Stripe and Fireflies webhooks are idempotent — replaying the same event twice is a no-op. Stripe via `payment_events.event_id` unique key; Fireflies via `sales_call/fit_signals.json` existence check + overwrite-is-safe semantics.
- **Manual fallbacks**: every webhook has a CLI counterpart (`mark-paid`, `ingest-transcript --call-type sales`, `ingest-transcript --call-type walkthrough`). JR can always drive the flow manually if a webhook fails.

**Test scenarios:**
- Happy: `freddy audit send-invoice --client acme` creates Checkout Session → Stripe dashboard shows it → simulated webhook event → `state.payment.paid = True` + Slack ping.
- Happy: sales-call Fireflies webhook with valid HMAC → `SalesFitSignals` extracted + Slack ping with summary.
- Happy: walkthrough-call Fireflies webhook with valid HMAC → `WalkthroughFitSignals` extracted + Slack ping.
- Happy: running `freddy audit run --client acme` with `state.payment.paid = False` raises `PaymentRequired` with actionable message.
- Edge: duplicate Stripe webhook event (same `event_id`) → `payment_events` unique-key collision → handler returns 200 but skips the state write; idempotent.
- Edge: Fireflies webhook with bad HMAC sig → 401 + log; no state change.
- Edge: Fireflies meeting title missing `<slug>` → writes fit_signals to `clients/__quarantine__/<ts>.json` + Slack-pings JR to reconcile.
- Edge: `freddy audit mark-paid` works without any Stripe config (pure state mutation); dev/test convenience.
- Integration: full commercial flow — submit form → `freddy audit run --stage 1` → sales call → `freddy audit send-invoice` → prospect pays via Stripe Checkout → webhook fires → `freddy audit run` completes Stages 2–5 → `freddy audit publish` → walkthrough call → webhook fires → both `fit_signals.json` files present in workspace.

**Done when:** A real end-to-end test — JR manually walks through all 10 commands + 2 webhook-driven state transitions — produces a delivered audit + two fit-signal artifacts (sales + walkthrough) for a dogfooded prospect.

---

## References consolidation

6 Corey Haines audit-level reference files at `src/audit/references/` (reconcile vs existing 11 at `autoresearch/archive/v006/programs/references/` — pick more current, redirect or merge, never keep duplicates):

| File | Merges these Corey skills |
|---|---|
| `stats-library.md` | Princeton KDD 2024 + SE Ranking + ZipTie + Core Web Vitals + form-field tradeoff + churn split — cross-cutting citations cited across every lens |
| `seo-lens-references.md` | seo-audit + site-architecture + programmatic-seo + schema-markup (SEO rows) **+ backlink interpretation thresholds (toxic-link %, referring-domain velocity, anchor-text concentration red flags) + Core Web Vitals benchmarks by site type (LCP/INP/CLS pass/improve/fail bands per Google) + historical trend interpretation (what a 3-month rank drop vs. volatility looks like) + featured-snippet capture playbook** |
| `geo-lens-references.md` | ai-seo + schema-markup (GEO rows) **+ AI Overview citation interpretation (what `ai_overview.cited_domains` presence means for share-of-voice)** |
| `competitive-lens-references.md` | competitor-alternatives + customer-research (competitor section) + pricing-strategy (tier structure) **+ backlink gap interpretation (how to read competitor referring-domain overlap) + keyword gap prioritization framework (volume × ease × commercial intent scoring) + SERP feature opportunity scoring (who owns featured snippets, who owns AI Overview citations)** |
| `monitoring-lens-references.md` | analytics-tracking + revops + marketing-ideas (channel menu subset) |
| `conversion-lens-references.md` | page-cro + signup-flow-cro + form-cro + onboarding-cro + churn-prevention + popup-cro + paywall-upgrade-cro + copywriting + marketing-psychology (Challenge→Models table) **+ Core Web Vitals impact on conversion benchmarks (LCP/INP/CLS thresholds correlated with bounce + conversion rate drops, industry-specific data)** |
| `voc-source-playbooks.md` | customer-research (Mode 2 + confidence labels) + product-marketing-context schema |

Excluded (no audit value): cold-email, community-marketing, referral-program, marketing-ideas (as a standalone, though subset used elsewhere), and 4 other low-value Corey skills.

## Manual review gates (intake, payment, calibration)

Three permanent gates fire every audit, plus a temporary per-stage gate for the first 5 (calibration).

- **Gate 1: Intake review (every audit, permanent).** After Stage 1 pre-discovery completes, `freddy audit run --stage 1` prints the `brief.md` path. JR reads it, decides whether to pursue the prospect. No automated prompt — JR simply stops running commands if the lead isn't worth pursuing. If pursuing: JR can add context to `clients/<slug>/audit/intake/operator_notes.md` that downstream Stage 2 lens agents will read.
- **Gate 2: Payment (every audit, permanent).** Between Stage 1 and Stage 2, JR runs the sales call, sends the Stripe Checkout URL via `freddy audit send-invoice`, and the prospect pays. The Stripe webhook (`POST /v1/audit/stripe`) sets `state.payment.paid = True` and Slack-pings JR. Running `freddy audit run --client <slug>` at any later point will raise `PaymentRequired` until this flag is True. JR can bypass via `freddy audit mark-paid` for test/dev. This gate replaces any notion of "approve to proceed"— the gate is financial, not editorial.
- **Gate 3: Final publish (every audit, permanent).** Stage 5 produces the deliverable files but does NOT auto-upload. JR reviews `deliverable/report.html` + `report.pdf` locally, then runs `freddy audit publish` when satisfied. This is JR's final editorial control before the URL goes live to the prospect.
- **Calibration gates (first 5 audits only, temporary).** `state.calibration_mode = True` when `audit_count < 5` (computed from the number of audits with `state.current_stage == "published"`). In calibration mode, `freddy audit run` prompts for approval after EVERY stage, not just at the three permanent gates. After 5 successful audits, `calibration_mode` default flips to False; only the three permanent gates remain. The `--calibration` flag can force per-stage prompts on any audit.

That's the full review discipline. Three permanent gates (intake · payment · publish) + calibration training wheels for the first 5. The mechanism is in code; the judgment is JR's.

## Agent observability & safety

This section codifies the hooks, telemetry, and recovery mechanisms that replace cost/turn gates. Referenced by U1 (state), U3–U8 (agent sessions), and the Risks section.

**Hook contracts (all live in `src/audit/hooks.py`):**
- `PostToolUse` — for every tool call: (a) append `{timestamp, agent_role, session_id, tool_name, tool_input_hash, tool_output_summary, cumulative_turns, cumulative_cost_usd}` row to `clients/<slug>/audit/cost_log.jsonl`; (b) maintain a rolling ring of recent `(tool_name, tool_input)` hashes per session — if the same hash appears 5× consecutively, Slack-ping JR with `{slug, agent_role, session_id, loop_signature}`; **never abort**. Claude receives nothing from the hook on the happy path.
- `PreCompact` — before the SDK auto-compacts older history, archive the full pre-compaction transcript to `clients/<slug>/audit/<stage>/transcripts/<agent_role>-<session_id>-<ts>.jsonl` so the original reasoning trace is preserved for post-hoc review.
- `Stop` — on `ResultMessage` arrival, flush final telemetry (`total_cost_usd, duration_ms, num_turns, model_usage, stop_reason`) to `cost_log.jsonl` and call `state.record_session(role, result_message)`.
- `PreToolUse` — reserved for future soft guardrails (e.g., WebFetch domain allowlist); unused on Day 1.

**Telemetry schema (`cost_log.jsonl`):** one JSON object per line. Shared fields: `{ts, slug, agent_role, session_id, event_type}` where `event_type ∈ {tool_use, tool_result, result_message, hook_alert, anomaly}`. Per-event fields vary. Log is append-only; rotated per-audit (lives under the audit workspace, not global).

**Cost anomaly alert:** `telemetry.compute_anomaly(slug)` runs on `Stop` for the root audit. If `total_cost_usd` of the finished audit exceeds `p95(recent_audits) + 3 × σ(recent_audits)` (rolling over the last 20 audits), Slack-ping JR with the outlier's cost_log summary. Observation only — no gate, no rollback.

**Sentinel `max_turns`:** every `ClaudeSDKClient` runs with `max_turns=500`. This is **not a budget**; normal agents complete in 15–60 turns. 500 exists solely as a runaway-infinite-loop backstop — if it fires, a prompt or tool is genuinely broken and JR should know. If it ever fires in practice, raise the sentinel, don't lower it.

**Session resumability:** every Claude Agent SDK invocation sets `enable_file_checkpointing=True` and `permission_mode="bypassPermissions"`. On first `ResultMessage`, `session_id` is persisted via `state.record_session(role, result)`. A crashed run resumes with `ClaudeSDKClient(resume=state.sessions[role].session_id)`, not a restart. `freddy audit run --resume` picks up whichever stage/role last wrote a session.

**What we deliberately don't do:**
- No turn cap that constrains normal cognition (sentinel-only; 500 is not a budget).
- No cost gate that blocks execution — only alerts.
- No auto-abort on output quality (prompts encode quality bars; JR reviews via the Stage 1 → Stage 2 gate and calibration gates).
- No auto-override of agent output — the evaluator-optimizer critique in Stage 3 is passed back to the agent, never forced.

## Risks flagged inline

- Claude Agent SDK parallel-session limits: fall back to sequential Stage 2 execution if hit (adds 1–2h wall-clock; correctness preserved).
- python-Wappalyzer misses modern stack: custom augmentation rules in `primitives.tech_stack`; flag low-confidence detections.
- Scraper layout drift (Crunchbase, LinkedIn, /careers): graceful degradation; Phase 2 upgrade path to paid APIs if chronic.
- Playwright memory growth: single shared context per audit; hard timeout per URL.
- Cost variance without gates: single audits may range widely (expected $5–$80+). Mitigation: every `ResultMessage` streams to `cost_log.jsonl`; `telemetry.py` computes 3σ alerts above rolling p95 and Slack-pings JR for post-hoc review. No automated cap — that's the trade for agent freedom.
- Runaway turn count: no budget cap, but mitigated by (a) sentinel `max_turns=500` per agent (5–10× expected normal max; only fires on genuine infinite loops), (b) `PostToolUse` loop-detection hook (5× identical `(tool_name, tool_input)` hash → Slack alert), (c) session checkpointing + `resume=<session_id>` for recovery, (d) JR manual intervention on anomaly alerts.
- Fireflies webhook loss (either call type): `freddy audit ingest-transcript --call-type {sales,walkthrough}` manual fallback covers both.
- Stripe webhook loss or double-delivery: signature verification + `payment_events` table with unique-key dedupe on `event_id` makes handler idempotent. `freddy audit mark-paid` exists as manual fallback if webhook fails to arrive.
- Prospect ghosts after sales call (pays nothing): workspace sits in post-Stage-1 state indefinitely. 90-day retention (R11) eventually cleans it up. No automated followup in v1 — JR's sales hygiene handles followup manually.
- Slug resolution failure on Fireflies webhook (meeting title missing `<slug>`): fit_signals get written to `clients/__quarantine__/<ts>.json` and JR gets Slack-pinged to reconcile manually. Not data loss, just requires human routing.
- Health score misread as authoritative: `gofreddy_health_score` is a marketing-intuitive rollup (similar to Ahrefs / SEMrush Site Health) — it's directional, not a strict benchmark. Prospects may over-weight the precision of the number. Mitigation: (a) deliverable includes a small explanation of what the score measures + weights used; (b) weights are re-tuned after first 10 audits based on what predicts engagement close; (c) intended for shareability, not strict accuracy. The audit's real value is the narrative + findings, not the single number.

## Sources

- Design conversation 2026-04-19/20: 20+ turns resolving all decisions (functioned as origin brainstorm).
- Related plans: `docs/plans/2026-04-17-agency-visibility-plan.md` (existing dashboard), `docs/plans/2026-04-18-deploy-plan.md` (Fly API deployment reused).
- Port sources in `/Users/jryszardnoszczyk/Documents/GitHub/freddy/`: `src/extraction/content_extractor.py`, `src/clients/`, `src/content_gen/output_models.py`, `src/competitive/brief.py`, `src/competitive/templates/competitive_brief.html`.
- Existing GoFreddy pattern: `src/competitive/pdf.py` (WeasyPrint usage), `src/geo/providers/cloro.py` (AI-visibility provider), `src/monitoring/adapters/` (12 reused adapters).
- External: Claude Agent SDK Python docs, Fireflies.ai webhook + GraphQL docs, python-Wappalyzer, crt.sh + subfinder, DataForSEO Traffic Analytics add-on, Princeton GEO study (KDD 2024).
