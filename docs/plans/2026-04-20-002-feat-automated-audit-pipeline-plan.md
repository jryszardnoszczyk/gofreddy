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
- R10. **$1,000 full audit as lead magnet** for $15K+ engagements. Preceded by a free AI Visibility Scan (see R16) that qualifies the prospect. $1,000 paid upfront via Stripe Checkout before Stage 2 fires. JR sends a Checkout URL after the sales call via `freddy audit send-invoice`; Stripe webhook (`POST /v1/audit/stripe`) sets `state.paid = True` and Slack-pings JR. Credited in full to the first engagement invoice if the prospect signs within 60 days (credit-note logic handled manually at engagement-invoice time, not in code). The $1K tier is the engagement anchor — a 15× jump to a $15K engagement reads as a natural next step; this price converts better than $300 or $750 on engagement close rate despite fewer paid sign-ups.
- R11. Data retention: workspace kept active 90 days post-delivery, archived 1 year, then deleted. Deliverable at `reports.gofreddy.ai/<slug>` preserved full 1 year. Pre-paid leads (Stage 1 complete, payment never received) follow the same retention.
- R12. PII hygiene: VoC quotes sourced only from public channels; quotes always cite source URL; private/paywalled content never embedded verbatim.
- R13. Branding: every HTML page and PDF includes a persistent "Prepared by GoFreddy · gofreddy.ai" footer, preserved when shared externally.
- R14. Manual-fire philosophy for the **deep audit pipeline**: all pipeline stages (0–5 of the paid audit) are triggered by JR via `freddy audit run` locally — no poller, no auto-fire on webhook for the expensive stages. External events (Stripe payment, Fireflies transcripts) may update state via webhooks, but pipeline stage progression is always JR's call. The **free AI Visibility Scan** (R16) is exempt — it's lightweight lead-gen that auto-runs on form submission because volume matters there and risk is low ($1–2 per scan). Auto-firing the full audit pipeline is a future work item, deferred out of this plan.
- R15. Two-call model: a **sales call** happens after the free AI Visibility Scan and before payment — JR pitches the $1K full audit using the scan's AI visibility gap as the opening hook ("you're cited by Perplexity but not Claude — let's look at why, and what else is underneath"). A **walkthrough call** happens after delivery — JR walks through findings and pitches the 3-tier engagement. Both calls are captured by Fireflies with separate webhook endpoints and separate fit-signals schemas (`SalesFitSignals` vs `WalkthroughFitSignals`).
- R16. **Free AI Visibility Scan** (lead magnet, auto-runs on form submission). Narrow teaser: runs `score_ai_visibility` + `analyze_serp_features.ai_overview` subset + ONE Opus call that produces a 1-page branded note highlighting 2–3 specific AI-search findings ("You're cited by Perplexity for 8/10 queries but by Claude for only 2 — costing you enterprise buyers"). Delivered as both (a) markdown email to the prospect and (b) shareable HTML page at `reports.gofreddy.ai/scan/<slug>/` (prospects share this internally, generating compounding lead flow). Cost: ~$1–2 per scan. Deliberately narrow: shows the problem on one dimension, doesn't give away the full diagnosis. Creates FOMO for the $1K full audit — "what about my SEO, conversion, competitive positioning?"

## Scope

**In:** **Free AI Visibility Scan auto-runner** (lead magnet, ~$1–2 per scan, delivered via email + shareable URL at `reports.gofreddy.ai/scan/<slug>/`), 6-stage paid audit pipeline (manually fired per stage via `freddy audit run`), 18 pre-discovery primitives (including SaaS-parity coverage: backlinks via DataForSEO Backlinks API, Core Web Vitals via Google PageSpeed Insights API, historical rank/traffic trends via DataForSEO Historical, on-page SEO audit, content quality audit, traffic estimation), 4 ports from Freddy (`content_extractor`, `clients` schema, `content_gen` output models, `competitive/brief.py` pattern), HTML+PDF rendering, Cloudflare Worker intake + scan hosting + audit hosting, Slack lead-notification, Stripe Checkout + payment webhook, two Fireflies webhooks (sales call + walkthrough call), 6 consolidated Corey Haines reference files, eval harness.

**Out / deferred to a future plan:** Autoresearch work, post-sign delivery execution, outbound prospecting, multi-tenant infra, free-tier audits, pre-analysis discovery call (the sales call fills that role now), **laptop poller / auto-firing the pipeline on form submission**, **Stripe-webhook-auto-fires-Stage-2** (webhook only updates `state.paid`; JR fires Stage 2), **3-business-day SLA enforcement** (target only), **engagement-invoice credit-note accounting** (manual).

## Architecture

6 stages run sequentially. Each stage is a Python function that reads state, does work (deterministic Python or structured Claude API calls), writes outputs, updates state. **No agent loops except in Stage 2.** No Stage abstract class. No skills library under `.claude/skills/`. Prompts are string constants in `src/audit/prompts.py`.

```
Form submit → Cloudflare Worker → Fly API /v1/scan/request → Supabase row
                                                                  │
                                    (auto-run, ~2 min, ~$1–2 — the free lead-magnet tier)
                                                                  ▼
  Free AI Visibility Scan (score_ai_visibility + analyze_serp_features.ai_overview + 1-page Opus note)
                                                                  │
                                                                  ▼
  → Email markdown scan.md to prospect + upload scan.html to R2 at reports.gofreddy.ai/scan/<slug>/
  → Slack ping JR: "🎯 Free scan delivered for <company> (<url>). Sales call ready."

                 (JR books + runs sales call; pitches $1K full audit using scan's AI-visibility gap as hook;
                                       Fireflies captures → sales_fit_signals.json)

  $ freddy audit send-invoice --client <slug>     ← Stripe Checkout URL at $1,000 → email/Slack prospect
                                                     │
                                                     ▼
                                               prospect pays
                                                     │
                                Stripe webhook → POST /v1/audit/stripe → state.paid = True + Slack JR

🛑 PAYMENT GATE — state.paid must be True before Stage 2 will run

  $ freddy client new <slug> --from-pending <id>  ← JR creates full workspace from Supabase row
  $ freddy audit run --client <slug>              ← runs full paid audit: Stages 0 through 5
  ├─ Stage 0: Intake       — Python only, populates workspace from form data
  ├─ Stage 1: Pre-discovery — runs 18 primitives; ONE Opus call synthesizes signals into brief.md
  ├─ Stage 2: Lenses        — 5 Sonnet Agent SDK sessions in parallel (asyncio.gather)
  ├─ Stage 3: Synthesis     — brief.py-style async fan-out → Opus synthesis + health score rollup
  ├─ Stage 4: Proposal      — Opus picks capability IDs + writes narrative; Python applies pricing
  └─ Stage 5: Deliverable   — Jinja2 → HTML, WeasyPrint → PDF, upload to R2 (not published yet)

🛑 PUBLISH GATE — JR reviews deliverable locally before going live

  $ freddy audit publish --client <slug>          ← publishes to reports.gofreddy.ai/<ulid>/

  (JR runs walkthrough call; Fireflies webhook → POST /v1/audit/walkthrough → walkthrough_fit_signals.json;
                                              pitches $15K+ engagement)
```

Every `$ freddy …` line is a manual invocation by JR. Auto-runs: form submission → free scan (cheap lead-gen, auto-fires on volume), Stripe + Fireflies webhooks → state updates only (never trigger pipeline stages). The full paid pipeline (Stages 0–5) is manually fired only after payment clears.

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
  scan.py                   # Free AI Visibility Scan orchestration (lead-magnet tier)
  eval/                     # U9 eval harness (rubric, runner, report)
  templates/audit_report.html.j2
  references/*.md           # 6 consolidated Corey skill references
.claude/skills/audit-run/SKILL.md  # invoke with /audit-run in interactive Claude Code
cli/freddy/commands/audit.py       # freddy audit {run,publish,mark-paid,send-invoice,ingest-transcript,eval,scan}
src/api/routers/audit_intake.py    # POST /v1/audit/intake (form webhook → Supabase + Slack ping + auto-runs free scan)
src/api/routers/audit_scan.py      # POST /v1/scan/request (scan trigger — called by intake handler)
src/api/routers/audit_stripe.py    # POST /v1/audit/stripe (Stripe webhook → state.paid)
src/api/routers/audit_sales_call.py      # POST /v1/audit/sales-call (Fireflies webhook, pre-Stage-2 call)
src/api/routers/audit_walkthrough.py     # POST /v1/audit/walkthrough (Fireflies webhook, post-delivery call)
landing/audit-intake.html          # gofreddy.ai form
cloudflare-workers/audit-intake/   # form→Fly relay
cloudflare-workers/audit-hosting/  # reports.gofreddy.ai/<ulid>/ (paid audit) + reports.gofreddy.ai/scan/<slug>/ (free scan)
supabase/migrations/20260420000001_audit_intake.sql
supabase/migrations/20260420000002_audit_payment.sql   # payment_events table
supabase/migrations/20260420000003_ai_visibility_scans.sql   # scans table (slug, email, scan_url, delivered_at)
```

## Key decisions (resolved in 2026-04-19/20 design session)

- Claude Agent SDK (Python), not ported Freddy ADK; inline prompts, not skills library.
- Sonnet for pre-discovery synthesis + all 5 lenses; Opus for synthesis, surprises, proposal.
- Local file storage only; per-stage git commits.
- Two-call sales model: sales call between free scan and $1K paid audit (JR pitches using AI-visibility gap as hook); walkthrough call post-delivery (JR walks through findings + pitches $15K+ engagement). Both captured by Fireflies via separate webhook endpoints.
- Manual-fire pipeline for the paid audit: JR runs every `freddy audit run [--stage N]` command locally via Claude Code. No laptop poller. Webhooks (Stripe, Fireflies) update state but never trigger pipeline stages. The free AI Visibility Scan (R16) auto-runs on form submission because it's lightweight and volume matters there. Auto-firing the full audit pipeline deferred to a future plan.
- **Two-tier product model — audit as lead magnet, engagement as the real product.** Free AI Visibility Scan (narrow, ~$1–2 infra) drives top-of-funnel volume; $1K full audit filters serious prospects and anchors the $15K+ engagement close (15× multiplier reads as natural progression). Audit revenue is secondary; engagement conversion is the primary success metric. Positioning: "free teaser of your AI search posture" → "$1K full marketing diagnosis" → "$15K+ engagement that actually does the work."
- **Audit delivers diagnosis + pitch, not a DIY playbook.** Findings' `recommendation` field is strategic (what to solve) + tier-mapped (which proposal tier addresses it), NOT tactical execution detail. "Recommended Next Steps" section maps findings directly to Fix-it / Build-it / Run-it proposal tiers. The engagement delivers implementation, account-gated data (Search Console, Analytics, Ad platforms, ESP), monthly iteration, and reports the audit cannot produce. The audit shows WHAT; the engagement DOES.
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

### U2. Pre-discovery primitives (18 functions)

**Goal:** All 18 primitives in a single `src/audit/primitives.py` file — plus a shared Playwright fetcher. Each primitive is a Python function returning a TypedDict, graceful degradation with `partial: bool` on all of them. The final 9 primitives (`analyze_backlinks`, `audit_page_speed`, `historical_rank_trends`, `keyword_gap_analysis`, `analyze_serp_features`, `analyze_internal_links`, `audit_on_page_seo`, `audit_content_quality`, `estimate_traffic`) cover the **SaaS-parity signals** prospects expect (backlinks, Core Web Vitals, historical trends, keyword gaps, SERP features, internal link graph, on-page SEO, content quality, traffic estimation) so the deliverable doesn't read thin next to Ahrefs / SEMrush / PageSpeed Insights / Screaming Frog / Similarweb.

**Files:**
- Create `src/audit/rendered_fetcher.py` — `RenderedFetcher` class (context manager, single shared browser context per audit)
- Create `src/audit/primitives.py` — 18 functions with a three-phase dependency order (see U3 Approach for full diagram). Phase 1: 9 independent primitives (tech_stack, enumerate_subdomains, scrape_careers, scrape_firmographics, detect_schema, score_ai_visibility, scan_competitor_pages, gather_voc, detect_analytics_tags) + subprocess CLIs. Phase 2: `analyze_backlinks`, `audit_page_speed`, `historical_rank_trends`, `keyword_gap_analysis`, `estimate_traffic`, `analyze_internal_links` (which seeds the shared page corpus). Phase 3: `audit_on_page_seo`, `audit_content_quality`, `analyze_serp_features` (all consume phase-2 outputs — page corpus or keyword lists):
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
  - **`analyze_internal_links(domain, sitemap_urls) -> dict`** — Internal link-graph analysis (Screaming Frog / Sitebulb parity). Consumes sitemap output (already produced by `freddy sitemap` subprocess). Fetches up to 200 pages via `httpx` (not Playwright — link extraction doesn't need JS rendering; static HTML + BeautifulSoup is faster and cheaper); for sites under 200 pages, does a full crawl. **The 200-page HTML corpus this primitive fetches is shared with `audit_on_page_seo` and `audit_content_quality` (both below) — fetch-once, parse-three-times — to avoid 3× HTTP cost.** Extracts `<a href>` tags, builds an internal link graph, computes depth from homepage. Returns `{page_count_crawled, crawl_coverage_pct, orphan_pages[{url, has_canonical, indexable}], deep_pages[{url, min_clicks_from_home}] (threshold: >3 clicks), broken_internal_links[{from_url, to_url, status_code}], link_equity_distribution: {top_linked_pages[{url, incoming_links}], tail_pages_pct}, anchor_text_internal_distribution, _raw_pages_cache}`. Feeds SEO lens (orphans and deep pages are common fixable wins that are visible in Screaming Frog but not in SEMrush/Ahrefs by default). Graceful degradation: large sites exceeding 200 pages → `partial=true` with sample; crawler blocked by robots.txt → `partial=true` with what was reached; total crawl cap 10 min to bound wall-clock.
  - **`audit_on_page_seo(pages_cache) -> dict`** — Per-URL technical SEO audit (Screaming Frog page-level parity). Consumes the 200-page HTML corpus already fetched by `analyze_internal_links` (no new HTTP). Parses each page for: `{url: {title: {text, length, is_duplicate_across_site}, meta_description: {text, length, is_duplicate}, h1: {count, text}, heading_hierarchy: {h1_count, h2_count, ..., issues[]} (flags skipped levels), canonical: {url, is_self, is_cross_domain}, directives: {noindex, nofollow, noarchive}, images: {total_count, missing_alt_count}, word_count, http_status_code, redirect_chain: [{from, to, status}], is_https, has_hsts}}`. Site-level rollup: `{duplicate_titles[], duplicate_meta_descriptions[], missing_h1_count, pages_with_noindex[], redirect_chains[{path, depth}], non_https_pages[], pages_with_broken_images[]}`. Feeds SEO lens (every prospect who's opened Screaming Frog expects this level of per-URL detail) + GEO lens (directives affect AI crawlability). Folds in image SEO alt-text audit + HTTPS/HSTS/security basics in a single primitive. `freddy detect <url> --full` already covers homepage-level DataForSEO technical audit for ONE page — this primitive is the same quality of analysis across all 200.
  - **`audit_content_quality(pages_cache) -> dict`** — Content quality audit (SEMrush Content Analyzer + Ahrefs Content Explorer parity). Same 200-page corpus reuse (no new HTTP). Returns: `{thin_pages[{url, word_count}] (threshold: word_count < 300), duplicate_content_clusters[{cluster_id, urls[], similarity_score}] (via simhash — deterministic + cheap, not embeddings), cannibalization_risks[{target_keyword, competing_urls[], recommendation}] (detected via title + H1 + first paragraph keyword overlap across multiple pages), stale_pages[{url, last_modified, days_stale}] (last-modified from HTTP Last-Modified header first, fallback to HTML meta — threshold: >365 days)}`. Feeds SEO lens (thin content and cannibalization are top SEMrush findings) + conversion lens (stale content correlates with declining conversions on content-driven sites).
  - **`estimate_traffic(domain, competitor_domains) -> dict`** — Organic + paid traffic estimation (Similarweb / SEMrush Traffic Analytics parity). Uses DataForSEO Traffic Analytics add-on (already budgeted in R7). Verification pass found that `freddy audit seo <domain>` subprocess is only a rank snapshot, NOT traffic estimation — so this is a real gap we close here. Returns: `{monthly_organic_visits_est, monthly_paid_visits_est, traffic_sources: {search_organic, search_paid, direct, referral, social, mail, display} as percentages, top_pages_by_traffic[{url, traffic_share, top_keyword}] (top 20), geographic_breakdown[{country_code, traffic_share}] (top 10), competitor_traffic_comparison[{competitor_domain, monthly_organic_visits_est, direction_vs_prospect}]}`. Feeds SEO lens (traffic trend context) + competitive lens (relative market position) + synthesis (Hero TL;DR can quote "~X monthly visits"). Graceful degradation on API quota / low-traffic-domain data sparsity → `partial=true`.
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
- Happy: `analyze_internal_links("notion.so", [...200 urls])` returns populated `orphan_pages`, `deep_pages`, and `link_equity_distribution`; `page_count_crawled` between 100 and 200 (respecting the cap); `_raw_pages_cache` populated for downstream primitives.
- Happy: `audit_on_page_seo(pages_cache)` returns per-URL title/meta/h1/canonical/directives/status analysis + site-level rollup with at least one duplicate_title detection.
- Happy: `audit_content_quality(pages_cache)` detects at least one thin_page + one duplicate_content_cluster on a known test site with intentional thin/duplicate content.
- Happy: `estimate_traffic("notion.so", [])` returns monthly_organic_visits_est > 0 + traffic_sources distribution summing to 100%.
- Edge: Crunchbase page 404 → firmographic returns partial=true + missing_fields.
- Edge: Cloro rate-limited → ai_visibility returns partial=true, cached data.
- Edge: DataForSEO Backlinks API credits exhausted → `analyze_backlinks` returns partial=true with the subset it fetched before hitting the limit; downstream lens proceeds with "backlink detail partial" flag.
- Edge: PageSpeed Insights returns 429 on a URL → that URL's entry is `{partial: true, error: "rate_limited"}`; other URLs' entries still present.
- Edge: prospect domain is brand-new (no historical data) → `historical_rank_trends` returns `{partial: true, missing_fields: ["historical"]}` and the brief notes "insufficient history for trend analysis."
- Edge: `keyword_gap_analysis` DataForSEO Labs quota exhausted → returns top 25 gaps + `partial=true`; synthesis proceeds with subset.
- Edge: `analyze_serp_features` called with 0 keywords (upstream primitives both returned `partial: true`) → returns `{partial: true, missing_fields: ["all_keywords"]}` without failing Stage 1.
- Edge: `analyze_internal_links` on a very large site (10K+ URLs in sitemap) → caps at 200-page sample, `partial=true`, `crawl_coverage_pct` populated so the lens can note the partial depth in its narrative.
- Edge: `analyze_internal_links` hit by robots.txt blocking → returns whatever was crawled before the block with `partial=true`.
- Integration: all 18 primitives run on one real prospect without exceptions; total wall-clock under 30 min (realistic range 18–30 min — `audit_page_speed` ~3–8 min + `analyze_internal_links` ~3–10 min depending on site size + `audit_on_page_seo` + `audit_content_quality` ~2–4 min (parse-only, no new HTTP) + `keyword_gap_analysis` + `historical_rank_trends` + `analyze_serp_features` + `estimate_traffic` collectively ~3–7 min).

**Done when:** Each primitive runs standalone from a python REPL against a real URL and returns a non-empty, schema-valid result. The 9 SaaS-parity primitives (`analyze_backlinks`, `audit_page_speed`, `historical_rank_trends`, `keyword_gap_analysis`, `analyze_serp_features`, `analyze_internal_links`, `audit_on_page_seo`, `audit_content_quality`, `estimate_traffic`) produce data comparable in shape to what a prospect would see from Ahrefs / PageSpeed Insights / SEMrush / Screaming Frog / Similarweb respectively.

---

### U3. Stages 0 + 1: intake + pre-discovery with brief synthesis

**Goal:** Stage 0 (Python-only) populates workspace from intake form. Stage 1 runs all 18 primitives in Python via a three-phase fan-out (see Approach), then makes ONE Opus call to synthesize a `prospect-brief.md` + `signals.json`.

**Files:**
- Create `src/audit/stages.py` with `stage_0_intake(state)` and `stage_1_prediscovery(state)` functions
- Create `src/audit/prompts.py` with `PREDISCOVERY_SYNTHESIS_PROMPT` string constant
- Test: `tests/audit/test_stages_0_1.py`

**Approach:**
- `stage_0_intake`: reads intake form data from `audit_pending` row (populated by Unit 7), writes `clients/<slug>/audit/intake/form.json` + `clients/<slug>/config.json` (prospect Client model). No LLM.
- `stage_1_prediscovery`:
  1. Opens shared `RenderedFetcher` context
  2. Gathers signals by running the 18 new primitives from U2 AND these existing `freddy` CLI commands via subprocess (verified against actual code — descriptions reflect what each command actually returns, not aspirational scope):
     - `freddy sitemap <url>` → up to 100 URLs with `{url, lastmod, priority}`. Feeds both `analyze_internal_links` (page corpus seed) and signals.json.
     - `freddy scrape <url>` → fetches one page, returns text + word count. Used for homepage hero text extraction; primitives do bulk fetching on their own.
     - `freddy detect <url> --full` → per-URL DataForSEO technical audit + PageSpeed Core Web Vitals for the homepage. Complementary to `audit_page_speed` (which covers 10 URLs × mobile + desktop for breadth) and `audit_on_page_seo` (200-URL Screaming Frog parity). The overlap is intentional: `freddy detect --full` gives rich single-page detail on the homepage.
     - `freddy audit seo <domain>` → **thin: just a DataForSEO domain rank snapshot.** Does NOT provide traffic estimation, top-pages-by-traffic, or keyword research. Those gaps are closed by the new primitives (`estimate_traffic`, `keyword_gap_analysis`, `historical_rank_trends`). Keep for the rank snapshot only.
     - `freddy audit competitive <domain>` → **actually returns competitor AD data (Foreplay + Adyntel).** Despite the name, this is paid-media intel, NOT organic competitive analysis. Feeds the competitive lens as *ad intelligence* (surfaces which channels and creative themes competitors run) rather than organic competitive data — that comes from `scan_competitor_pages`, `analyze_backlinks` (re-invoked in U4 for competitors), `keyword_gap_analysis`, and `estimate_traffic`.
     - `freddy audit monitor "<brand>"` → recent brand mentions via Xpoz across social platforms. Feeds monitoring lens.
     - `freddy visibility` subprocess is **NOT invoked** — it duplicates `score_ai_visibility` primitive, which wraps the same Cloro provider under the hood. Use the primitive.
     Each result (primitive or CLI) writes to `clients/<slug>/audit/prediscovery/signals.json` under a top-level key.
    2a. Competitor discovery is explicit: a small helper `derive_competitors(form_data, dataforseo_serp, foreplay_ad_categories) -> list[str]` merges (a) prospect-provided competitors from intake form, (b) top-SERP overlap from DataForSEO, (c) shared ad-category competitors from Foreplay/Adyntel. The Opus synthesis call reconciles into a final ranked list of 3–5 competitors written to `signals.json:competitors`. This list is the input to `score_ai_visibility` and `scan_competitor_pages`.
  3. One Opus call (`PREDISCOVERY_SYNTHESIS_PROMPT`, directive skeleton) takes signals.json + form data, outputs structured `PrediscoveryBrief` (Pydantic envelope): ICP hypothesis with confidence label, inferred competitor list, pain points, tech posture summary, AI-visibility headline, hypotheses to validate on walkthrough (agent decides count). `session_id` + ResultMessage telemetry persisted via `state.record_session("prediscovery_synthesis", result)`.
  4. Writes `brief.md` (prose) + `brief.json` (structured)
- Concurrency: `asyncio.Semaphore(10)` across the 18 primitives + 6 `freddy` CLI subprocesses (visibility removed — redundant) to bound Playwright / subprocess handles (infra limit, not cognitive cap). Ordering constraints: (a) `analyze_serp_features` depends on `historical_rank_trends` + `keyword_gap_analysis`; (b) `analyze_internal_links` depends on `freddy sitemap` subprocess; (c) `audit_on_page_seo` and `audit_content_quality` both consume the page corpus cached by `analyze_internal_links`. Handled with a three-phase fan-out: phase 1 = independent primitives + subprocess CLIs + `freddy sitemap`; phase 2 = `analyze_internal_links` + `historical_rank_trends` + `keyword_gap_analysis` + `estimate_traffic` in parallel; phase 3 = `audit_on_page_seo` + `audit_content_quality` + `analyze_serp_features` in parallel (phase-3 primitives consume phase-2 outputs).
- Telemetry: per-primitive cost/duration rows appended to `cost_log.jsonl`; no per-stage budget.

**Test scenarios:**
- Happy: intake form with URL → Stage 0 writes valid config.json + form.json.
- Happy: Stage 1 end-to-end on a known prospect produces brief.md covering all primitive-sourced signal categories + ICP hypothesis.
- Edge: 5 of 18 primitives return partial (e.g., backlinks API rate-limited + Crunchbase 404 + no historical data + Cloro throttled + traffic-estimation data sparse) → brief flags "partial signals" + proceeds.
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
- `Finding` schema (envelope, not content constraint): `{id, lens, title, severity(0-3), reach(0-3), feasibility(0-3), evidence_urls[], evidence_quotes[], recommendation, proposal_tier_mapping, effort_band(S/M/L), confidence(H/M/L), category_tags[]}`. Agent fills any count of Findings freely. **The `recommendation` field is strategic, not tactical** — it states *what would solve this* in terms the engagement delivers, not a DIY execution guide. Example (good): *"Enterprise landing pages lack schema coverage, suppressing rich-result eligibility for 8 of 10 tracked enterprise queries."* Example (bad — too tactical, don't do this): *"Add Organization, Product, and FAQ schema with these JSON-LD snippets to /enterprise/."* Tactical execution detail is engagement work, not audit output. The `proposal_tier_mapping` field names which of the Fix-it / Build-it / Run-it tiers delivers this recommendation (populated in Stage 3 synthesis once proposal is generated in Stage 4 — see U5).
- `LensOutput`: `{lens_name, findings[], lens_summary, metadata{session_id, total_cost_usd, duration_ms, num_turns, model_usage, partial}}`.
- Each lens agent: open `ClaudeSDKClient` with a **directive** `system_prompt` (role / objective / context / tools+heuristics / effort-scaling / quality bar / output contract / termination — not a step-by-step playbook), inject `prospect-brief.md` + full `signals.json` + matching `src/audit/references/<lens>-references.md`. Config: `tools={"type":"preset","preset":"claude_code"}` (full Claude Code toolbelt incl. WebFetch, WebSearch, Task, Bash, Read/Write/Grep/Glob), `permission_mode="bypassPermissions"` for unattended roaming, `enable_file_checkpointing=True`, `max_turns=500` (sentinel runaway-loop backstop — not a budget; normal lens runs are 15–60 turns), `model=sonnet`. Hooks wired: `PostToolUse` → loop-detection (hash `(tool_name, tool_input)`; Slack-alert on 5× consecutive, no abort) + telemetry; `PreCompact` → archive full transcript to `clients/<slug>/audit/lenses/<lens>/transcripts/`; `Stop` → flush `ResultMessage` telemetry to `cost_log.jsonl` and record `session_id` via `state.record_session`.
- Run 5 lenses via `asyncio.gather(*[run_lens(l) for l in lenses])` with `Semaphore(5)` (infra concurrency, not cognitive cap). Each session is an isolated SDK subprocess.
- **Competitive lens performs head-to-head comparison** using the final competitor list from Stage 1's Opus synthesis (`signals.json:competitors`). It re-invokes DataForSEO Backlinks + Labs Competitors Keywords for each competitor domain and surfaces the following competitive insights in its narrative: (a) **linking gap** — which competitor domains have materially more referring domains / higher `dataforseo_rank`; (b) **link intersect** (Ahrefs flagship feature) — domains that link to 2+ competitors but NOT the prospect, computed as a set operation on the backlinks data already collected, ranked by domain authority; (c) **keyword gap** — top 100 keywords competitors rank for that prospect doesn't; (d) **SERP feature gap** — who owns featured snippets and AI Overview citations vs. prospect. It also consumes the ad-intel data from the `freddy audit competitive` subprocess (Foreplay + Adyntel ad creative + channel mix) and folds it into the narrative as paid-competitive posture. This is where competitor-comparison data is actually produced; Stage 1's `analyze_backlinks` + `keyword_gap_analysis` primitives deliberately produce prospect-only output because Stage 1 runs before `derive_competitors` resolves the final list.
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
- 9 report sections (envelope contract for rendering): Hero TL;DR (leads with health_score + per-lens breakdown), Executive Summary, What We Found (per lens), Surprises, Competitive Positioning, AI Visibility Posture, Technical Posture, **Recommended Next Steps (maps findings to proposal tiers, not a DIY playbook)**, About This Audit. Agent decides per-section length, number of findings, number of surprises within each section's quality bar. **Stage 3 synthesis back-fills each Finding's `proposal_tier_mapping` field** after Stage 4 generates the tier plan — so every finding explicitly says "Fix-it delivers this" / "Build-it delivers this" / "Run-it sustains this." The Recommended Next Steps section is rendered as: *"Fix-it tier addresses findings [#3, #7, #12] — high-severity technical and on-page issues scoped to the $[price] engagement. Build-it tier addresses [#1, #5, #9] — content and competitive infrastructure scoped to $[price]. Run-it tier sustains [#15, #18, #22] via monthly optimization scoped to $[price]/mo."* No separate execution playbook exists in the audit — that's engagement scope. The audit is the pitch; the engagement is the delivery.

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
- **About This Audit section (section 9)** explicitly frames audit vs. engagement scope to prevent prospects from thinking the audit replaces the engagement. Template copy (rendered verbatim, not LLM-generated): *"This audit uses public signals to diagnose what's happening in your marketing — AI visibility, SEO, competitive posture, conversion, content, and technical health. It's the diagnosis. The engagement is the treatment. With an engagement, we add account access (Google Search Console, Google Analytics, Ad platforms, ESP) that reveals metrics this audit literally cannot surface: bounce rate, conversion funnels, user-flow drop-offs, channel-level ROI. We also bring implementation capacity — actually doing the work in the Recommended Next Steps, not just identifying it — plus monthly optimization cycles that compound over time. The audit shows you WHAT to fix; the engagement FIXES it. Fix-it / Build-it / Run-it pricing is in Section 8, credited against the $1,000 audit fee if you sign within 60 days."* This paragraph sets expectations cleanly for the walkthrough-call engagement pitch.
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

### U8. Intake + Free AI Visibility Scan (lead-magnet tier)

**Goal:** Capture form submissions, auto-run the lightweight free AI Visibility Scan (R16), deliver the scan to the prospect via email + shareable URL, Slack-ping JR to book the sales call. No auto-firing of the paid audit pipeline — JR manually creates the client workspace and runs stages via Claude Code locally after payment clears. The laptop poller and paid-pipeline auto-firing are explicitly deferred to a future plan.

**Files:**
- Create `landing/audit-intake.html` — Tailwind-styled form matching existing landing page
- Create `cloudflare-workers/audit-intake/worker.js` + `wrangler.toml` — HMAC-sign + relay to Fly API
- Create `src/api/routers/audit_intake.py` — `POST /v1/audit/intake` (writes Supabase `audit_pending` row + triggers free scan via `scan.run_free_scan()`), `GET /v1/audit/pending`
- Create `src/api/routers/audit_scan.py` — `POST /v1/scan/request` (internal: triggers a scan re-run on demand for testing / manual re-invocation)
- Create `src/audit/scan.py` — `run_free_scan(slug, url, form_data)` orchestrator: (a) invokes `score_ai_visibility(brand, queries)` with queries derived from URL + form priorities (b) invokes a narrow slice of `analyze_serp_features(keywords)` limited to AI Overview detection for ~10 queries (c) ONE Opus call with directive prompt `FREE_SCAN_SYNTHESIS_PROMPT` that produces a 1-page branded note (title, 2–3 specific AI-search findings with numbers, a hook question for the sales call, CTA to the $1K full audit). Writes `clients/__scans__/<slug>/{scan.md, scan.json, scan.html}`. Uploads `scan.html` to R2 at `gofreddy-scans/<slug>/`. Sends the markdown via SMTP to the prospect's email; Slack-pings JR with scan summary + URL + copy-pasteable sales-call booking suggestion.
- Extend `src/audit/prompts.py` with `FREE_SCAN_SYNTHESIS_PROMPT` (directive skeleton — role: AI-search analyst; objective: surface 2–3 specific AI-visibility findings with numbers + a hook; quality bar: specific, evidence-cited, non-generic; output contract: markdown with headline + findings + CTA).
- Extend `cloudflare-workers/audit-hosting/worker.js` to route `/scan/<slug>/*` paths to R2 bucket `gofreddy-scans/`, alongside existing `/<ulid>/*` routes for paid audits.
- Modify `src/api/main.py` to register intake + scan routers
- Create `supabase/migrations/20260420000001_audit_intake.sql` — `audit_pending` table
- Create `supabase/migrations/20260420000003_ai_visibility_scans.sql` — `ai_visibility_scans` table (`slug ulid primary key, email, company, url, scan_url, delivered_at, sales_call_booked_at nullable`)
- Extend `cli/freddy/commands/audit.py`:
  - `freddy audit scan --url <url> --email <email> [--company <name>]` — manual scan invocation (for JR dogfooding + demos)
  - `freddy audit scan --rerun --client <slug>` — re-runs a scan for an existing lead
- Extend `cli/freddy/commands/client.py`: add `freddy client new <slug> --from-pending <id>` flag so JR can populate a full paid-audit workspace from a Supabase lead row in one command (after payment clears)
- Test: `tests/api/test_audit_intake.py`, `tests/audit/test_scan.py`

**Approach:**
- `audit_pending` table: `id, slug (ulid), submitted_at, form_data jsonb, consumed_at nullable` (consumed_at set when JR runs `freddy client new --from-pending`). No `status` state machine — simpler without a poller orchestrating stages.
- `ai_visibility_scans` table: one row per scan delivered. Keyed to the same slug. Tracks delivery + sales-call state for funnel analytics.
- Form fields: name, email, company, URL, size_band, budget_band, 3 top priorities, timeline, decision_maker, what they've tried, current agency status.
- Cloudflare Worker: HMAC-signs + POSTs to Fly API. Turnstile on form for spam mitigation.
- `POST /v1/audit/intake` handler: (1) inserts `audit_pending` row; (2) **synchronously calls `scan.run_free_scan(slug, url, form_data)`** — this is the auto-run, ~2 min end-to-end; (3) emits Slack webhook on completion with `{slug, company, url, scan_url, ai_visibility_headline, sales_call_cta}`. Slack template: *"🎯 Free scan delivered for {company}: {ai_visibility_headline}. View: {scan_url}. When you're ready to pitch the $1K full audit, book a sales call with {email}."* Gives JR the sales-call hook written for them.
- `scan.run_free_scan`: cost ~$1–2 per run. Graceful degradation — if `score_ai_visibility` is rate-limited, scan proceeds with cached / partial data and flags it in the 1-pager. Never fails the form submission — even a barebones scan is better than no delivery.
- `freddy client new --from-pending <id>`: reads Supabase row, creates `clients/<slug>/audit/` workspace, populates `intake/form.json` + `config.json`, marks `consumed_at`. Does NOT run any pipeline stage. Run only after payment clears.

**Test scenarios:**
- Happy: form submit → Cloudflare Worker → Fly API writes pending row → scan runs → email + R2 upload + Slack ping, all within 3 min.
- Happy: scan.md includes at least 2 concrete numbers (citation counts per AI platform) and a named hook for the sales call.
- Happy: shareable URL at `reports.gofreddy.ai/scan/<slug>/` returns 200 with the branded HTML.
- Happy: `freddy client new test --from-pending <id>` reads the row and creates a valid workspace; `consumed_at` is set.
- Happy: `freddy audit scan --url notion.so --email test@example.com` produces a valid scan locally without touching Supabase (dev convenience).
- Edge: `score_ai_visibility` returns partial=true (Cloro rate-limited) → scan still delivers with caveat in the 1-pager; Slack ping flags the degradation.
- Edge: Cloudflare Worker's HMAC sig is invalid → Fly API returns 401; no DB write; no scan; Slack silent.
- Edge: Supabase row already has `consumed_at` → `--from-pending` warns + exits without overwriting.
- Integration: submit a real test form → scan lands in inbox within 3 min + URL live on `reports.gofreddy.ai/scan/<slug>/` + Slack ping with sales-call hook.

**Done when:** Submitting the form on `gofreddy.ai/audit-intake` (a) auto-delivers a branded AI Visibility Scan to the prospect's inbox within 3 minutes, (b) posts the scan at `reports.gofreddy.ai/scan/<slug>/`, (c) Slack-pings JR with a sales-call-ready summary. Zero paid pipeline stages have fired.

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
