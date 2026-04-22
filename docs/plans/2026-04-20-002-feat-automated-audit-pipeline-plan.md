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
- R3. 9 lens analyses: **SEO** (technical + on-page + content quality + backlinks + keyword gaps + Core Web Vitals + Screaming Frog parity + **international hreflang** + **local business + GBP + NAP citations** + **WCAG 2.1 AA accessibility** + **help-center docs SEO**), **GEO** (AI-search citations across ChatGPT/Perplexity/Gemini/Grok/Copilot/Claude/Google AI Mode + AI Overview presence + **OSS footprint correlation** since high-star repos heavily indexed by AI), **Competitive** (head-to-head backlink + keyword + SERP feature + AI Overview + paid-creative gap analysis), **Monitoring** (cross-platform mention velocity + sentiment drift + pain-point clusters + share-of-voice + press-tier + podcast presence + community footprint), **Conversion** (page CRO + form CRO with field-by-field audit + **trust signals + security headers + CMP** + **pricing page anchoring + localization** + **funnel content shape** + **ABM signals when B2B-enterprise**), **Distribution** (paid + organic social + video + podcast + earned-media + ASO with 6-dim rubric + desktop marketplaces when mobile/desktop apps detected + **directory presence G2/Capterra/AlternativeTo/Product Hunt/CWS** + **marketplace listings Zapier/Slack/AppExchange/AWS/HubSpot/Atlassian** + **launch cadence PH/changelog/RSS** + **free tools / engineering-as-marketing** + **OSS footprint when dev-tool**), **Lifecycle** (email capture + martech fingerprint + DNS deliverability posture; real flow metrics when ESP access granted via R19), **MarTech-Attribution** (full martech stack + attribution maturity + privacy-compliance surface + **ABM personalization/reverse-IP/intent-data when B2B-enterprise** + **budget allocation vs Gartner/OpenView benchmarks when R24 attach-budget granted** + **CRM pipeline velocity when R25 attach-crm granted**), **Brand/Narrative** (messaging consistency + **copy-quality scoring** + thought leadership + **founder-led weighting for early-stage** + content-strategy shape + **newsletter subscribers + glossary marketing** + earned-media narrative + **Wikipedia depth + Lift Wing reference quality** + partnership/event/community footprint + **press kit + status page + webinars** + **customer education program** + **public roadmap** + **corporate responsibility / ESG when mid-market+** + **customer story program** + **employer brand + pay-transparency compliance** + **PLG motion when SaaS** + **devex when dev-tool** + **win-loss themes when R26 attach-winloss granted** + **demo-flow audit when R23 attach-demo granted**). Canonical findings schema with severity + confidence.
- R4. Synthesis produces ranked findings, 3–5 surprises, and a 3-tier proposal (Fix-it / Build-it / Run-it) with deterministic registry-based pricing.
- R5. Deliverable = HTML at `reports.gofreddy.ai/<slug>` + downloadable PDF; Fireflies captures the walkthrough call.
- R6. Local storage only. Everything under `clients/<slug>/audit/`, git-committed per stage.
- R7. Costs are telemetry by default, with three operational circuit breakers (see "Telemetry, not gating" decision: per-audit `max_audit_cost_usd` ceiling, concurrent-run lock, pre-flight adversarial check). Every stage appends to `cost_log.jsonl` for post-hoc analysis. Monthly cost envelope at ~20 audits/month splits into two layers:
  - **Subscription + per-call infra**: ~$80–140/month — Fireflies (~$10 flat) + DataForSEO base subscription (fixed) + **DataForSEO Backlinks + Labs endpoints (pay-per-use, roughly $20–60/mo)** + Apify pay-per-run + Stripe transaction fees. Google PageSpeed Insights API free (25K queries/day).
  - **LLM inference (Sonnet + Opus)**: estimated **~$50–150 per audit** at default settings, → **~$1,000–3,000/month** at 20 audits. Per-stage breakdown (estimates, to be re-baselined after first 5 dogfood audits with real `cost_log.jsonl` data):
    - Free AI Visibility Scan: ~$1–2 per scan (1 Opus call + minimal Sonnet)
    - Stage 1a cache warmup: ~$2-4 (no LLM, just owned-provider API calls)
    - Stage 1b Sonnet pre-discovery: ~$10-30 (1 session × 30-90 turns × adaptive WebFetch surface; prompt caching mitigates context regrowth)
    - Stage 1c Opus brief synthesis: ~$0.50-1
    - Stage 2 (7 agents × Sonnet × critique loop): ~$30-80 (7 × ~$5-12; critique loop contributes 30-50% of per-agent cost; cache hits eliminate provider re-pays)
    - Stage 3 (9 section Opus + master + surprise critique + rationale): ~$5-10
    - Stage 4 proposal Opus call: ~$1-2
    - Stage 5 deliverable: no LLM (Jinja + WeasyPrint)
  Hard `max_audit_cost_usd=$50` default ceiling means a single audit cannot quietly exceed that budget — it halts and escalates to JR. Adjust per-client when an audit warrants more depth.
- R8. Three permanent gates every audit, plus a temporary calibration gate for the first 5. (1) Intake review: after Stage 1, JR reviews the pre-discovery brief. (2) Payment gate: between Stage 1 and Stage 2, sales call happens and $1K Stripe payment must clear (`state.paid = True`) before Stage 2 fires. (3) Final publish: JR manually runs `freddy audit publish` after reviewing the rendered deliverable. First-5 calibration mode adds approval prompts after every stage.
- R9. No autoresearch coupling. Audit does not touch `src/evaluation/` or `autoresearch/`.
- R10. **$1,000 full audit as lead magnet** for $15K+ engagements. Preceded by a free AI Visibility Scan (see R16) that qualifies the prospect. $1,000 paid upfront via Stripe Checkout before Stage 2 fires. JR sends a Checkout URL after the sales call via `freddy audit send-invoice`; Stripe webhook (`POST /v1/audit/stripe`) sets `state.paid = True` and Slack-pings JR. Credited in full to the first engagement invoice if the prospect signs within 60 days (credit-note logic handled manually at engagement-invoice time, not in code). **Pricing hypothesis (unvalidated until first 5 audits run):** the $1K tier is the engagement anchor — the bet is that paying prospects close to a $15K engagement at materially higher rate than $300 or $750 prospects despite fewer paid sign-ups. Kill-criterion: if after the first 10 paid audits, fewer than 2 close a $15K+ engagement within 60 days, JR revisits the price point + qualification + sales motion before scaling. Engagement-conversion is the primary success metric, not audit revenue.
- R11. Data retention: workspace kept active 90 days post-delivery, archived 1 year, then deleted. Deliverable at `reports.gofreddy.ai/<slug>` preserved full 1 year. Pre-paid leads (Stage 1 complete, payment never received) follow the same retention.
- R12. PII hygiene: VoC quotes sourced only from public channels; quotes always cite source URL; private/paywalled content never embedded verbatim.
- R13. Branding: every HTML page and PDF includes a persistent "Prepared by GoFreddy · gofreddy.ai" footer, preserved when shared externally.
- R14. Manual-fire philosophy for the **deep audit pipeline**: all pipeline stages (0–5 of the paid audit) are triggered by JR via `freddy audit run` locally — no poller, no auto-fire on webhook for the expensive stages. External events (Stripe payment, Fireflies transcripts) may update state via webhooks, but pipeline stage progression is always JR's call. The **free AI Visibility Scan** (R16) is exempt — it's lightweight lead-gen that auto-runs on form submission because volume matters there and risk is low ($1–2 per scan). Auto-firing the full audit pipeline is a future work item, deferred out of this plan.
- R15. Two-call model: a **sales call** happens after the free AI Visibility Scan and before payment — JR pitches the $1K full audit using the scan's AI visibility gap as the opening hook ("you're cited by Perplexity but not Claude — let's look at why, and what else is underneath"). A **walkthrough call** happens after delivery — JR walks through findings and pitches the 3-tier engagement. Both calls are captured by Fireflies with separate webhook endpoints and separate fit-signals schemas (`SalesFitSignals` vs `WalkthroughFitSignals`).
- R16. **Free AI Visibility Scan** (lead magnet, auto-runs on form submission). Narrow teaser: runs `score_ai_visibility` + `analyze_serp_features.ai_overview` subset + ONE Opus call that produces a 1-page branded note highlighting 2–3 specific AI-search findings ("You're cited by Perplexity for 8/10 queries but by Claude for only 2 — costing you enterprise buyers"). Delivered as both (a) markdown email to the prospect and (b) shareable HTML page at `reports.gofreddy.ai/scan/<slug>/` (prospects share this internally, generating compounding lead flow). Cost: ~$1–2 per scan. Deliberately narrow: shows the problem on one dimension, doesn't give away the full diagnosis. Creates FOMO for the $1K full audit — "what about my SEO, conversion, competitive positioning?"
- R17. **Owned-provider-first discipline.** Every primitive that consumes external data must prefer an owned, wired provider (`src/seo/providers/dataforseo.py`, `src/geo/providers/cloro.py`, `src/competitive/providers/{foreplay,adyntel}.py`, the 12 monitoring adapters, `src/seo/providers/gsc.py`, `src/fetcher/instagram.py`) over a new integration. A full inventory of owned providers + their primitive/lens consumers lives in the "Data provider inventory" subsection under Architecture. Adding a new external integration requires explicit evidence that the owned stack cannot cover the signal — not a default.
- R18. **Conditional GSC enrichment.** If the prospect grants Google Search Console access on the sales call (one-click OAuth or service-account share), `GSCClient` (`src/seo/providers/gsc.py`, free) pulls real search analytics during Stage 1 — clicks / impressions / CTR / position per page for the last 90 days — and enriches SEO + Conversion lenses with truth rather than estimation. Absence degrades Stage 1 gracefully to public-signal estimation (no pipeline block). Capture happens via the sales call prompt; CLI: `freddy audit attach-gsc --client <slug> --service-account-json <path>` or OAuth flow TBD at implementation time.
- R19. **Conditional ESP enrichment.** If the prospect grants ESP (email-service-provider) API access on the sales call — Klaviyo, Mailchimp, Customer.io, HubSpot, Braze, Iterable, ActiveCampaign — pull real lifecycle data during Stage 1: list size + growth rate + segmentation depth, welcome-series open/click/CVR, cart/browse/checkout abandonment flow metrics, winback/reengagement/sunset flow presence + performance, SMS send frequency + TCPA compliance, deliverability rates (inbox vs spam), revenue-by-flow attribution. Lifecycle lens findings pivot from "we detect a capture popup" to "your welcome series converts 8% vs the 15% Klaviyo benchmark for your ICP — here's why." CLI: `freddy audit attach-esp --client <slug> --vendor <klaviyo|mailchimp|customerio|hubspot|braze|iterable|activecampaign> --api-key <key>` (or OAuth per vendor). Absence = Lifecycle lens operates on public signals only.
- R20. **Conditional ad-platform enrichment.** If the prospect grants ad-platform access (Google Ads / Meta Ads Manager / LinkedIn Campaign Manager / TikTok Ads Manager) via OAuth on the sales call, pull real paid-media data during Stage 1: actual spend by campaign, impressions, clicks, CPC, CPM, conversion events, ROAS, audience overlap, creative performance rankings, search-query reports (Google), lookalike-audience composition (Meta). Distribution lens findings pivot from "estimated spend ~$X/mo" (SpyFu estimate) to "you spent $47K on Meta last month; your top-performing ad has run 120 days with declining CTR — refresh needed." CLI: `freddy audit attach-ads --client <slug> --platform <google|meta|linkedin|tiktok> --oauth-token <token>`. Absence = Distribution lens operates on public ad-library signals only.
- R21. **Conditional survey / customer research upload.** If the prospect shares NPS survey data, churn-reason coding, CSAT responses, or exit-interview transcripts (CSV / JSON upload), Stage 1 ingests + one Opus call codes the pain points + maps them to findings. Monitoring lens + Conversion lens findings pivot from "public reviews surface X pain point" to "your NPS detractors cite X (quoted from actual responses); your churn-reason coding shows 34% cite pricing — the pricing page audit flagged 3 pricing-clarity issues that match." CLI: `freddy audit attach-survey --client <slug> --file <path.csv|json> --type <nps|csat|churn|exit>`. Absence = VoC operates on public-signal corpus (`gather_voc`) only.
- R22. **Conditional client-asset upload.** If the prospect shares internal brand assets (sales deck, one-pager, brand book / style guide, pricing page PDF, product screenshots, ICP persona docs), Stage 1 ingests them and runs a cross-asset consistency audit — logo lockup variants, primary color palette, typography stack, voice/tone, value-prop alignment — comparing against the website-derived external audit from `audit_brand_visual_identity_external` (part of Brand/Narrative lens). Brand/Narrative lens findings pivot from "website uses consistent typography" to "sales deck uses Helvetica but the website uses Inter; customer-facing docs are misaligned on the new positioning launched 3 months ago." CLI: `freddy audit attach-assets --client <slug> --files <path1> <path2> ...`. Absence = Brand/Narrative lens operates on web-surface signals only.
- R23. **Conditional onboarding-flow audit (`attach-demo`).** If the prospect provides demo-account credentials on the sales call, JR runs `freddy audit attach-demo --client <slug> --url <demo-url> --username <user> --password <pass> [--readonly-mode true]` post-Stage-1, post-payment — this triggers a scoped sub-session (NOT part of Stage 1 pre-discovery; runs alongside Stage 2 as a separate enrichment session) executing a Playwright-driven onboarding-flow audit in an isolated browser context. Findings flow to the Conversion-Lifecycle agent's output via shared cache. Captures TTFV (time-to-first-value), empty-state quality, contextual-help density, in-product guidance vendor (Appcues / Pendo / Userflow / Chameleon), friction points, progressive disclosure — scored against Wes Bush "Bowling Alley", Samuel Hulick teardown, and Ramli John EUREKA frameworks. **Critical safety surface** (capability restriction with three reinforcing controls — see "Safety via capability restriction" decision): (1) **Scoped session config** — `permission_mode="default"` (NOT bypass) + `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` + `mcp_servers={"playwright_obs": build_playwright_obs_server()}` + `allowed_tools=["mcp__playwright_obs__page_goto", "mcp__playwright_obs__page_screenshot", "mcp__playwright_obs__locator_get_attribute", "mcp__playwright_obs__accessibility_snapshot"]`. The destructive capability (page.click, page.fill, page.evaluate, Bash, WebFetch) is positively absent from the allow-list AND the MCP-server tool surface AND the deny-list — three reinforcing layers. Agent cannot execute destructive actions even if the prompt is compromised. (2) **Orchestrator pre-conditions** — opt-in flag + readonly-mode flag + credential-encryption validated before primitive invocation. (3) **Per-action human confirmation** — if agent identifies a form submission necessary for flow measurement, CLI prompts "Agent wants to submit form on /onboarding. Approve? [y/N]" (not pre-approved by flag). (4) **Isolated Playwright browser context** per run; disposable test fixtures (never real PII). (5) **Playwright trace recording** for post-hoc audit log. (6) **Hard 15-min timeout** + `max_turns=400` sentinel. (7) Pre-flight ToS check on robots.txt + automation clauses. (8) OS-keychain credential storage — never plain-text in git-tracked state.json. (9) Engagement letter disclosure. Conversion lens findings pivot from "we detect a signup form" to "your TTFV is 8 min vs Linear's 90 sec; empty-state quality 30/100; missing in-product guidance entirely." CLI: `freddy audit attach-demo --client <slug> --url <demo-url> --username <user> --password <pass> [--readonly-mode true]`. Absence = Conversion lens operates on signup-page snapshot only.
- R24. **Conditional marketing budget audit (`attach-budget`).** If the prospect uploads a marketing budget breakdown (CSV/JSON: % by channel × monthly $), Stage 1 audits against codified benchmarks in `src/audit/data/budget_benchmarks.yaml` — 70/20/10 rule (proven/experiment/bet), MarTech as % of marketing (Gartner 2025: 22.4% baseline), paid-media share (Gartner 2025: 30.6% baseline), marketing as % of revenue (Gartner 2025: 7.7% baseline, adjusted upward for early-stage SaaS to 15-50%), per-channel deviation from vertical benchmark, channel-mix vs OpenView/High Alpha SaaS Benchmarks. MarTech-Attribution + Distribution lens findings pivot from external estimation to "you spend $21K/mo MarTech but `fingerprint_martech_stack` detected 47 tools — investigate consolidation; you're underinvested in MOFU content vs vertical benchmark." CLI: `freddy audit attach-budget --client <slug> --file <path.csv|json>`.
- R25. **Conditional CRM data audit (`attach-crm`).** If the prospect connects CRM via API or uploads CSV (HubSpot / Salesforce / Pipedrive / Close / Attio), Stage 1 normalizes to canonical `Opportunity` Pydantic model and computes pipeline velocity formula (`opps × ACV × win_rate ÷ sales_cycle_days`), lead-to-opp conversion, opp-to-close, sales-cycle median + p25/p75, MQL→SQL → close, lead-source ROI ranking, dead-lead recovery candidates. Benchmarks codified in `src/audit/data/crm_benchmarks.yaml` from cited 2025 sources (First Page Sage: ~21% win rate, 84d sales cycle, $26K median ACV, $8.2K/day pipeline velocity; OpenView/High Alpha; ICONIQ Growth State of GTM). Conversion + MarTech-Attribution lens findings pivot from external proxies to real funnel velocity numbers. **CRM data is PII-sensitive** — stored under `clients/<slug>/audit/enrichments/crm/` with `.gitignore` exclusion; only derived aggregate findings ever git-committed. CLI v1: HubSpot CSV path primary (no OAuth complexity); Salesforce/Pipedrive/Close/Attio added in v2 after first 5 audits validate demand. CLI: `freddy audit attach-crm --client <slug> --source <hubspot|salesforce|pipedrive|close|attio|csv> --file <path>`.
- R26. **Conditional win-loss interview audit (`attach-winloss`).** If the prospect uploads win-loss interview transcripts (PDF / Markdown / CSV / DOCX), Stage 1 parses + classifies each interview as won/lost/no_decision (Sonnet, with filename-hint fallback), per-interview Sonnet pass extracts decision criteria + competitive mentions + pricing references + persona signals + verbatim quotes with sentiment, embeds via `text-embedding-3-small` (existing dep), clusters via HDBSCAN/k-means, final Sonnet pass names clusters into themes + ranks top-3 win/loss reasons + builds competitive displacement matrix. Methodology baseline: Klue 31-questions framework, Crayon, Primary Intelligence, Anova Consulting templates. **PII redaction is mandatory** — pre-output Sonnet pass redacts names + company names + deal sizes before findings ship in deliverable. Brand/Narrative + Competitive + Conversion lens findings pivot to "verbatim NPS detractor language: 'pricing was opaque'; you lose 67% of deals to Competitor X on integrations; 4-mo median time-to-decision per Director persona." CLI: `freddy audit attach-winloss --client <slug> --files <path1> <path2> ...`.

## Scope

**In:**
- **Free AI Visibility Scan auto-runner** (lead magnet, ~$1–2 per scan, delivered via email + shareable URL at `reports.gofreddy.ai/scan/<slug>/`)
- **6-stage paid audit pipeline** manually fired per stage via `freddy audit run`
- **~15 cache-backed SDK tool methods** via `@cached_tool` decorator in `src/audit/tools/` wrapping existing wired providers (DataForSEO, Cloro, Foreplay+Adyntel via `CompetitiveAdService`, 12 monitoring adapters, GSC); cache 24h TTL at `clients/<slug>/audit/cache/`; cache files double as eval-harness fixtures
- **~68 free-public-API signals** (Wikipedia, GitHub, Product Hunt, crt.sh, Firefox AMO, Atlassian Marketplace, SEC EDGAR, HuggingFace, Reddit OAuth, APIs.guru, Mailinator, mail-tester, GDELT, Discord, etc.) handled by agents via WebFetch + Bash with auth env vars + polite-pace patterns named in agent prompts — **no Python wrapper modules**
- **2 local-only Python primitives** that run without network: `fingerprint_martech_stack` (wappalyzer-next + `data/martech_rules.yaml`) + `content_strategy_embeddings_cluster` (`text-embedding-3-small` + k-means)
- **7 Stage-2 agents producing 9 report-section narratives**: Findability (→SEO+GEO), Brand/Narrative, Conversion-Lifecycle (→Conversion+Lifecycle), Distribution, MarTech-Attribution, Monitoring, Competitive. Agent↔section routing via `Finding.report_section: Literal[...]` enum tagged by the producing agent
- **Evaluator-optimizer critique loop per Stage-2 agent** (initial → self-critique → optional revision, capped at 3 iterations) + **`AgentOutput.rubric_coverage: dict[rubric_id, "covered"|"gap_flagged"]`** map enforcing no-silent-skips
- **4 ports from Freddy** (`content_extractor`, `clients` schema, `content_gen` output models, `competitive/brief.py` pattern)
- HTML+PDF rendering, Cloudflare Worker intake + scan hosting + audit hosting, Slack lead-notification, Stripe Checkout + payment webhook, two Fireflies webhooks (sales + walkthrough)
- **9 consolidated agent reference files** (`stats-library` + 8 per-agent reference files)
- **Full eval harness** (runner + rubric + fixture_proxy + variance/coverage/gap-flag-honesty metrics)
- **2 enrichment modules + 9 credential-store CLI subcommands** for R18–R26 conditional enrichments (only `enrichments/assets.py` ~30 LOC for PDF/PPTX text extraction and `enrichments/demo.py` ~150 LOC for safety-critical Playwright scoped toolbelt are Python; the 7 other subcommands each ~20 LOC validate + write to state.json + store credentials in OS keychain or .env; agents read uploaded files via Bash/WebFetch)
- **0 new provider modules** (agent WebFetches free public APIs directly)
- **Full capability registry content shipped in-plan** (~48 YAML entries with scope + pricing + prerequisites)
- **Full template structure spec shipped in-plan** (9 sections, component partials, data contracts, print CSS rules)

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
  ├─ Stage 1: Pre-discovery — (a) parallel cache-warmup fires all owned-provider tool handlers unconditionally; (b) ONE Sonnet pre-discovery session with `tools={"type":"preset","preset":"claude_code"}` + `mcp_servers={"audit": register_audit_tools(state)}` + `allowed_tools=["mcp__audit__*"]` — reads cache + WebFetches free public APIs per prompt-named URL patterns; (c) ONE Opus synthesis call → brief.md + brief.json
  ├─ Stage 2: Agents        — 7 Sonnet SDK sessions in parallel (Semaphore 7); findings tagged with report_section Literal enum; AgentOutput carries rubric_coverage map (no silent skips); critique loop per agent ≤3 iterations
  ├─ Stage 3: Synthesis     — group findings by report_section enum; 9 section Opus calls + master merge + Python-deterministic health-score arithmetic + Opus rationale call; validates rubric_coverage + report_section routing
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
  primitives.py             # 2 local-only helpers: `fingerprint_martech_stack()` (wappalyzer-next + data/martech_rules.yaml) + `content_strategy_embeddings_cluster()` (text-embedding-3-small + k-means)
  rendered_fetcher.py       # Shared Playwright wrapper used by `scoped_tools.build_playwright_obs_server()` (powers attach-demo + hiring-funnel scoped sessions) and the deep-form-CRO observation path
  tools/                    # Cache-backed `@cached_tool` decorator wrapping existing wired providers; agents call at runtime; cache 24h TTL; cache files double as eval-harness fixtures
    __init__.py             # `register_audit_tools(state) -> SdkMcpServer` builds an `SdkMcpServer` via `create_sdk_mcp_server(name="audit", tools=[...])` — each tool wraps an existing wired-provider method (`src/seo/providers/dataforseo`, `src/geo/providers/cloro`, `src/competitive/service:CompetitiveAdService`, `src/monitoring/adapters/*`, `src/seo/providers/gsc` conditional on `state.enrichments.gsc.attached`) under `@cached_tool`. Agent reaches them as `mcp__audit__<toolname>` (e.g. `mcp__audit__backlinks`, `mcp__audit__ai_visibility`, `mcp__audit__voc`); attach via `mcp_servers={"audit": register_audit_tools(state)}` + `allowed_tools=["mcp__audit__*"]` in ClaudeAgentOptions. ~60 LOC
    cache.py                # read/write helpers; JSON at `clients/<slug>/audit/cache/<tool_name>_<hash>.json`; 24h TTL; `force=True` bypasses. ~50 LOC
    cached_tool.py          # decorator: hash args → cache.read → return-on-hit; else call → cache.write → return; on exception return ToolError. ~30 LOC
    types.py                # ToolError Pydantic envelope. ~20 LOC
  hooks.py                  # PostToolUse (loop-detection ring + per-agent token-spend alert at 3× rolling median — statistical helpers delegated to telemetry.py), PreCompact (transcript archive), Stop (telemetry flush). NO PreToolUse safety hooks — Tier-D safety lives in capability restriction
  scoped_tools.py           # Per-safety-critical-primitive scoped MCP servers + the matching `ClaudeAgentOptions` builder. Each `build_*_options()` returns options with three reinforcing controls: `permission_mode="default"` (NOT bypass), `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]`, and `mcp_servers={"<obs_name>": <server>}` + `allowed_tools=[<positive list of mcp__*__ tools>]`. Servers: `build_mailbox_obs_server()` (IMAP-read + DNS-lookup + Sonnet-classify wrappers; NO submit_form), `build_playwright_obs_server()` (page.goto + screenshot + locator.get_attribute + accessibility.snapshot wrappers; NO click/fill/evaluate), `build_ats_obs_server()` (httpx GET wrappers for Greenhouse/Lever/Ashby/Workable JSON endpoints; NO form.submit). Companion safety-invariant tests in `tests/audit/scoped_tools/` assert every blocked operation raises at SDK level under each scoped session
  stages.py                 # stage_0 through stage_5 functions + `stage_free_scan` + Stage 3 `_synthesize_sections()` helper. Stage 1 is (a) cache warmup / (b) Sonnet pre-discovery / (c) Opus brief synthesis — see U3
  prompts/                  # One `.md` file per prompt, readable prose. `predischarge.md`, `predischarge_synthesis.md`, 7 agent prompts (`agent_{findability,brand_narrative,conversion_lifecycle,distribution,martech_attribution,monitoring,competitive}.md`), `agent_critique.md` (shared template covering critique + revision phases), `synthesis_section.md`, `synthesis_master.md` (section-merge + surprise-quality-bar prose; the health score is computed in Python — see `_compute_health_score` in U5), `health_score_rationale.md` (small Opus prompt that takes the Python-computed score block + top findings → 3-5 sentence rationale paragraph), `surprise_quality_check.md`, `proposal.md`, `free_scan_synthesis.md`, `fit_signals.md` (shared template with section per call-type — sales / walkthrough). Plus `prompts/reference/fetch-api-patterns.md` — shared per-API auth/rate-limit/pagination reference + 11 AI-crawler user-agent strings inline
  prompts.py                # Thin loader: `load_prompt(name: str, **vars) -> str` reads `prompts/{name}.md` with format-string substitution. ~30 LOC
  capability_registry.py    # YAML loader + pricing multiplier
  capability_registry.yaml  # ~48 capability entries (full content in U6)
  clients_schema.py         # Pydantic Client model
  agent_models.py           # Finding (6 required: id, title, evidence_urls, recommendation, severity, confidence + report_section Literal enum; 7 optional fields). AgentOutput with required `rubric_coverage: dict[rubric_id, "covered"|"gap_flagged"]`. SalesFitSignals + WalkthroughFitSignals schemas
  agent_runner.py           # Critique-loop orchestrator (≤3 iterations)
  renderer.py               # render_html + render_pdf
  webhooks_helpers.py       # Shared HMAC verifiers (Stripe + Fireflies) + GraphQL transcript fetch + Slack-ping helpers — used by audit_webhooks.py handlers (consolidates prior stripe.py + fireflies.py)
  telemetry.py              # cost_log.jsonl writer + rolling statistics helpers (median, p95, σ) + 3σ-above-rolling-p95 anomaly alert (Slack). Single source of truth for rolling stats — hooks.py delegates here
  enrichments/
    assets.py               # PDF/PPTX text-extraction helper for R22 (pdfplumber + python-pptx). ~30 LOC
    demo.py                 # Safety-critical Playwright onboarding-flow audit for R23: isolated context, scoped toolbelt, orchestrator pre-conditions (opt-in + readonly + credential encryption), per-submit human confirmation, 15-min timeout, Playwright trace recording. ~150 LOC
  data/                     # 10 YAML lookup files (cross-audit consistency layer) + 7 per-agent rubric YAMLs (source-of-truth for Stage 3 rubric_coverage + report_section validation; agent prompt template loads from these so prompt + validator stay in sync)
    rubrics_findability.yaml          # rubric_id → {evaluation_question, expected_finding_shape, report_section}
    rubrics_brand_narrative.yaml      # same shape, brand_narrative section
    rubrics_conversion_lifecycle.yaml # ditto, splits across conversion + lifecycle
    rubrics_distribution.yaml         # ditto, distribution
    rubrics_martech_attribution.yaml  # ditto, martech_attribution
    rubrics_monitoring.yaml           # ditto, monitoring
    rubrics_competitive.yaml          # ditto, competitive
    martech_rules.yaml      # Custom regex/JS-fingerprint extending Wappalyzer. Categories: cdp, esp, sms, automation, ab_test, personalization, session_recording, chat, scheduling, consent, accessibility, loyalty, reviews, referral, subscription, search, cms, ecommerce, edge_network, payments, lms, reverse_ip, intent_data, chat_intent, docs_platforms, regional_payment_methods
    jargon_corpus.yaml      # ~300 buzzwords; consumed by `audit_messaging_consistency` jargon-density metric. Quarterly review
    pub_tier_dict.yaml      # ~200 publications across 10 verticals (Tier-1 flagship / Tier-2 trade / Tier-3 syndicate); consumed by `audit_earned_media_footprint`. Quarterly review
    conf_list.yaml          # Major conferences per vertical; consumed by `audit_partnership_event_community_footprint`
    budget_benchmarks.yaml  # R24 — Gartner 2025 CMO Spend Survey (7.7% revenue / 22.4% MarTech / 30.6% paid) + OpenView/High Alpha SaaS Benchmarks; vertical+ARR-band keyed
    crm_benchmarks.yaml     # R25 — First Page Sage 2026 + OpenView/High Alpha + ICONIQ Growth State of GTM
    aso_benchmarks.yaml     # P31 ASO 6-dim weighted rubric + brand-maturity tier adjustment
    vertical_compliance_rules.yaml  # Per-vertical compliance signals (HIPAA / PCI-DSS / FERPA / FDA / DMA-DSA / SOX / GLBA)
    analyst_position_awards.yaml    # Industry-award lookup (Inc 5000, Fast Company, Deloitte Fast 500, G2 Leader, Capterra Shortlist); annual refresh
  eval/                     # Full eval harness: runner.py + rubric.py + fixture_proxy.py + metrics.py (variance + coverage + gap-flag-honesty) + fixtures/<slug>/{cache/, brief.md, agent_outputs/, expected_rubrics.yaml}
  templates/audit_report.html.j2
  references/*.md           # 9 agent reference files: stats-library, findability-agent, conversion-lifecycle-agent, competitive-agent, monitoring-agent, distribution-agent, martech-attribution-agent, brand-narrative-agent, voc-source-playbooks
.claude/skills/audit-run/SKILL.md  # invoke with /audit-run in interactive Claude Code
cli/freddy/commands/audit.py       # freddy audit {run,publish,mark-paid,send-invoice,ingest-transcript,eval,scan,attach-{gsc,esp,ads,survey,assets,demo,budget,crm,winloss}}
src/api/routers/audit_webhooks.py  # Single router hosting 6 endpoints: POST /v1/audit/intake, POST /v1/scan/request, POST /v1/audit/stripe, POST /v1/audit/sales-call (with inline ~20 LOC SalesFitSignals Opus extraction), POST /v1/audit/walkthrough, GET /v1/audit/pending
landing/audit-intake.html          # gofreddy.ai form
cloudflare-workers/audit-intake/   # form→Fly relay
cloudflare-workers/audit-hosting/  # reports.gofreddy.ai/<ulid>/ (paid audit) + reports.gofreddy.ai/scan/<slug>/ (free scan)
supabase/migrations/20260420000001_audit_intake.sql
supabase/migrations/20260420000002_audit_payment.sql   # payment_events table
supabase/migrations/20260420000003_ai_visibility_scans.sql   # scans table (slug, email, scan_url, delivered_at)
```

## Data provider inventory (single source of truth)

Every external data signal routes through an owned provider unless explicitly justified. New integrations require evidence that owned coverage is insufficient (R17).

**File column conventions:** rows marked `(owned provider)` are existing wired code in `src/seo/providers/`, `src/geo/providers/`, `src/competitive/`, `src/monitoring/adapters/` — `src/audit/tools/` exposes these to agents as cache-backed SDK tools. Rows marked `(agent WebFetch)` are free public APIs the agent reaches directly via WebFetch + `cli/scripts/fetch_api.sh` with URL patterns + auth env vars named in agent prompts — no Python wrapper module.

| Provider | File | Exposes | Cost model | Consumers (primitives → lenses) |
|---|---|---|---|---|
| `DataForSeoProvider` | `src/seo/providers/dataforseo.py` | On-page audit, keyword analysis, backlinks, domain rank, traffic, SERP features, historical, Labs | Per-call $0.01–0.05 | `analyze_backlinks`, `audit_page_speed`, `historical_rank_trends`, `keyword_gap_analysis`, `analyze_serp_features`, `audit_on_page_seo`, `audit_content_quality`, `estimate_traffic` → SEO + Competitive + Conversion |
| `GSCClient` | `src/seo/providers/gsc.py` | Clicks / impressions / CTR / position per page (90 days) via service account | **Free** | Conditional enrichment per R18 → SEO + Conversion |
| `CloroClient` | `src/geo/providers/cloro.py` | AI citation tracking (ChatGPT, Perplexity, Gemini, Grok, Copilot, Claude, Google AI Mode) with positional metrics (`word_count`, `position_weight`, `word_pos_score`) | $0.01/query | `score_ai_visibility` → GEO |
| `ForeplayProvider` | `src/competitive/providers/foreplay.py` | Meta + TikTok + LinkedIn ads — rich normalized fields: `persona`, `emotional_drivers`, `creative_targeting`, `market_target`, `product_category`, `cards`, `transcription`, `running_duration` | Subscription + ~$0.001/ad | `freddy audit competitive` subprocess + `detect_paid_ads_social` → Competitive + Distribution |
| `AdyntelProvider` | `src/competitive/providers/adyntel.py` | Google Ads — paginated advertiser-level, creative HTML, variants | $0.0088/page | `freddy audit competitive` subprocess + `detect_paid_ads_google` → Competitive + Distribution |
| `CompetitiveAdService` | `src/competitive/service.py` | Foreplay + Adyntel orchestration with parallel fan-out, domain-mismatch filter, TTLCache 30min | — | `scan_competitor_pages`, `detect_paid_ads_*` → Competitive + Distribution |
| `XpozAdapter` | `src/monitoring/adapters/xpoz.py` | Twitter + Instagram + Reddit — posts, users (followers / engagement / verification / inauthenticity / relevance), comments, subreddits | Per-call $ | `gather_voc`, `audit_channel_presence`, `freddy audit monitor` → Monitoring + Distribution |
| `ICContentAdapter` | `src/monitoring/adapters/ic_content.py` | **Creator-first** TikTok + YouTube: discover creators mentioning brand → fetch their posts with engagement + author followers/verified | Per-discovery + per-content | `gather_voc`, `audit_channel_presence`, `detect_influencer_affiliate` → Monitoring + Distribution |
| `PodEngineAdapter` | `src/monitoring/adapters/podcasts.py` | Podcast transcript search — matched segments with show/host/episode, sentiment, `is_ad_segment` flag, speaker ID | Per-call $ | `gather_voc`, `audit_podcast_footprint` → Monitoring + Distribution |
| `TrustpilotAdapter` / `AppStoreAdapter` / `PlayStoreAdapter` | `src/monitoring/adapters/reviews.py` | Reviews + ratings + sentiment + verified flag + business replies | Apify CU | `gather_voc` → Monitoring + Conversion |
| `NewsDataAdapter` | `src/monitoring/adapters/news.py` | News articles + sentiment + AI tags + `source_priority` + category | Per-request | `gather_voc`, `audit_earned_media_footprint` → Monitoring + Distribution |
| `GoogleTrendsAdapter` | `src/monitoring/adapters/google_trends.py` | Search-interest series + related queries/topics + geo + breakout detection | Apify CU | `gather_voc` (trend context), `audit_earned_media_footprint` → Monitoring |
| `BlueskyMentionFetcher` | `src/monitoring/adapters/bluesky.py` | Bluesky public posts via AT Protocol | **Free** | `gather_voc`, `audit_channel_presence` → Monitoring + Distribution |
| `FacebookMentionFetcher` / `LinkedInMentionFetcher` / `TikTokAdapter` (monitoring) | `src/monitoring/adapters/{facebook,linkedin,tiktok}.py` | Public posts via Apify scrapers | Apify CU | `gather_voc` → Monitoring |
| `InstagramFetcher` | `src/fetcher/instagram.py` | IG reel + profile scraper via Apify | Apify CU | Optional `audit_channel_presence` enrichment → Distribution |
| YouTube Data API v3 | (new, env `YOUTUBE_API_KEY`) | Channel stats, upload cadence, shorts:long-form, top videos | **Free (10K units/day)** | `audit_youtube_channel` → Distribution |
| Google PageSpeed Insights API | (env `PAGESPEED_API_KEY`) | Core Web Vitals (LCP, INP, CLS) + performance score for mobile + desktop | **Free (25K/day)** | `audit_page_speed` → SEO + Conversion |
| Google Ads Transparency Center (BigQuery) | `bigquery-public-data.google_ads_transparency_center` (optional) | Historical Google ad corpus (ads back to 2023) | **Free (1 TB/mo)** | Supplemental depth for `detect_paid_ads_google`; Adyntel stays primary — defer until evidence of gap |
| `wappalyzer-next` (s0md3v fork, supersedes unmaintained `python-Wappalyzer`) + custom regex rules in `src/audit/data/martech_rules.yaml` | `src/audit/primitives.py:tech_stack`, `fingerprint_martech_stack` | Tech fingerprinting + extended categories (CDP/ESP/CRM/A-B/heatmap/chat/consent/loyalty/subscription/referral/reviews + LMS + reverse-IP + intent-data + ABM personalization + docs platforms + regional payment methods + accessibility overlays) | Local, free | `tech_stack`, `fingerprint_martech_stack`, `capture_surface_scan`, `audit_customer_education` (LMS), `audit_abm_signals`, `audit_devex` (docs platforms), `audit_pricing_page` (payment methods), `audit_accessibility` (overlay red flag), `audit_trust_signals` (CMP) → SEO + GEO + Lifecycle + MarTech-Attribution + Conversion + Brand/Narrative + Distribution |
| Playwright `RenderedFetcher` | `src/audit/rendered_fetcher.py` | Shared browser context: HTML + JSON-LD + network requests + screenshots | Compute only | All rendered primitives |
| DNS queries (SPF / DKIM / DMARC / BIMI / MTA-STS / TLS-RPT / CNAME) | `dnspython` (new dep) | Deliverability hygiene + martech CNAME fingerprinting | **Free** | `deliverability_posture`, `fingerprint_martech_stack` → Lifecycle + MarTech-Attribution |
| Wayback Machine CDX API | `https://web.archive.org/cdx/search/cdx` | Historical homepage / pricing / positioning snapshots for tagline-evolution diffs + editorial-cadence archives | **Free** | `audit_messaging_consistency`, `audit_content_strategy_shape` → Brand/Narrative |
| Wikipedia REST API | `https://en.wikipedia.org/api/rest_v1` | Brand page existence + length + last-edit date + reference count | **Free** | `audit_earned_media_footprint` → Brand/Narrative |
| SerpAPI (Google News + site-restricted search) | `https://serpapi.com/search` (or SearchApi alt) | Press-tier lookup, exec quoted-in-press, bylined-article discovery, award/accolade queries, conference-speaker hits | ~$50/mo entry | `audit_earned_media_footprint`, `audit_executive_visibility` → Brand/Narrative |
| GDELT DOC 2.0 API | `https://api.gdeltproject.org/api/v2/doc/doc` | Global news-graph themes + tone time-series for narrative extraction | **Free** | `audit_earned_media_footprint` → Brand/Narrative (supplements SerpAPI) |
| Podchaser GraphQL (guest appearances) | `https://api.podchaser.com/graphql` (free tier) | Executive guest-appearance data per person (supplements Pod Engine's brand-name transcript search) | **Free tier** | `audit_executive_visibility` → Brand/Narrative |
| Discord Invite API | `https://discord.com/api/v10/invites/<code>?with_counts=true` | Member count + presence count for public server invites | **Free, unauthenticated** | `audit_partnership_event_community_footprint` → Brand/Narrative |
| Reddit `/r/<sub>/about.json` | Reddit free tier | Subreddit subscribers + active users | **Free** | `audit_partnership_event_community_footprint` → Brand/Narrative |
| Luma / Eventbrite / Hopin / Goldcast indexed pages | SerpAPI site-restricted search | Owned-event registration pages + past-event archives | SerpAPI | `audit_partnership_event_community_footprint` → Brand/Narrative |
| Embeddings (OpenAI `text-embedding-3-small` or Voyage) | Existing `openai>=1.80.0` dep | Blog-title clustering → content pillar detection | ~$0.01 per 100 titles | `audit_content_strategy_shape` → Brand/Narrative |
| iTunes Search API (App Store) + Google Play (via existing Apify adapters) | Owned — `AppStoreAdapter`, `PlayStoreAdapter` | App listing metadata, ratings, review velocity, screenshot count, top-100 keyword rank via keyword search | Apify CU | `audit_aso` (conditional) → Distribution |
| GitHub REST + GraphQL APIs | (agent WebFetch — `api.github.com`) | Org existence, repo enumeration, stars, contributors, release atom feeds, license, README, CONTRIBUTING.md, sponsor program, contributor employment affiliation | **Free** (5K req/hr authed via `GITHUB_TOKEN`) | `audit_oss_footprint`, `audit_devex` (SDK coverage), `audit_launch_cadence` (release.atom), `audit_free_tools` (tool repos) → Distribution + Brand/Narrative + GEO (AI-citation supply correlation) |
| Product Hunt GraphQL API | (agent WebFetch — `api.producthunt.com/v2/api/graphql`) | Historical launches by maker/brand, upvotes, badges, launch dates | **Free** (OAuth client-credentials, ~6250 complexity points/15min); commercial-use is gray — confirm with `hello@producthunt.com` before scale | `audit_directory_presence` (PH listings), `audit_launch_cadence` (PH history) → Distribution |
| Certificate Transparency log search (crt.sh) | (agent WebFetch — `crt.sh/?q=%25.{domain}&output=json`) | Subdomain enumeration via TLS certificate logs (catches `tools.<domain>`, `app.<domain>`, `calculator.<domain>`) | **Free, unauthenticated** (~1 req/sec polite rate); fallback `https://api.certspotter.com/v1/issuances?domain=` (free 100/hr) | `audit_free_tools` (subdomain enum) → Distribution |
| Firefox Add-ons (AMO) public search API | (agent WebFetch — AMO public search) | Browser-extension lookup by author/publisher | **Free, unauthenticated** | `audit_free_tools` (Firefox extensions) → Distribution |
| Atlassian Marketplace REST API v3 | (agent WebFetch — Atlassian Marketplace REST v3) | Add-on search, install count, rating, review count, app key — only platform marketplace with clean public API | **Free, unauthenticated** | `audit_marketplace_listings` (Atlassian slice) → Distribution |
| MediaWiki Action API + REST + Lift Wing inference | (agent WebFetch — MediaWiki REST + Lift Wing) | Article existence, length, references, revisions/cadence, langlinks, infobox, articlequality + reference-quality scoring (replaces deprecated ORES, served via Lift Wing since Jan 2025) | **Free** (no key for read; optional `WIKIMEDIA_API_KEY` for Lift Wing) | `audit_earned_media_footprint` (Wikipedia depth), `audit_executive_visibility` (founder Wikipedia) → Brand/Narrative |
| Mozilla HTTP Observatory v2 | `https://observatory-api.mdn.mozilla.net/api/v2/scan` | Security headers grade + score (CSP / HSTS / X-Frame-Options / X-Content-Type-Options / Referrer-Policy / Permissions-Policy) — **replaces SecurityHeaders.com which sunsets April 2026 (Snyk acquisition)** | **Free, no auth** (1 scan/host/min cooldown) | `audit_trust_signals` → Conversion + MarTech-Attribution |
| ATS public job-board APIs — Greenhouse, Lever, Ashby, Workable | Direct httpx (no provider wrapper needed — JSON endpoints) | Open roles enumeration with `content=true`: title, department, location, full description (extract tech-stack mentions + salary ranges for pay-transparency compliance) | **Free, unauthenticated** (no rate-limit issues at 20 audits/mo) | `scrape_careers` (primary path, supersedes flaky page scraping) → Brand/Narrative + MarTech-Attribution (pay-transparency compliance is the publishable anchor finding for CA/NY/CO/WA jurisdictions) |
| LinkedIn company-page metadata via Apify | Apify actor `harvestapi/linkedin-company-employees` (page-only mode) | Followers, employee count, growth rate, recent posts — page metadata only (full employee enum not used in v1: $4-$8/1K + rate-limited) | Apify CU ~$0.05/audit | `scrape_careers` (LinkedIn supplement), `audit_executive_visibility` (founder LinkedIn URL) → Brand/Narrative |
| Glassdoor via Bright Data Cloudflare-bypass scraping | Bright Data "Glassdoor company reviews collected by URL" | Overall rating, review count, CEO approval, recommend-to-friend %, recent-review sentiment trend — **only realistic path** since Glassdoor consolidated into Indeed July 2025 (Recruit Holdings); API dead, plain scraping Cloudflare-blocked | $0.10–0.50/audit, ~70-80% success rate; Tier-2 escalation for >$10M revenue prospects only | `scrape_careers` (Glassdoor — optional Tier-2 enrichment) → Brand/Narrative |
| Comparably public profile pages | `src/audit/rendered_fetcher.py` (RenderedFetcher) | Cultural-dimension scores broken out by gender/ethnicity (16 dimensions, 70K+ companies) — data not available elsewhere | **Free, polite scraping** (1 req/2s) | `scrape_careers` (employer-brand culture layer) → Brand/Narrative |
| Indeed Company Pages (lighter bot defense than Glassdoor) | `src/audit/rendered_fetcher.py` at low volume; Apify `epctex/indeed-scraper` at scale | Reviews, ratings — primary survivor of Glassdoor/Indeed merger | Free at <20 audits/day; Apify ~$0.05 at scale | `scrape_careers` (Indeed reviews fallback) → Brand/Narrative |
| Foursquare Places API | Direct httpx (free tier 50/day suffices) | NAP data for the Foursquare slice of `audit_local_seo` citation consistency check | **Free tier** | `audit_local_seo` → SEO |
| npm registry + PyPI JSON APIs | Direct httpx (`registry.npmjs.org/<pkg>/latest` + `pypi.org/pypi/<pkg>/json`) | Last-publish timestamp per package — used for SDK staleness detection | **Free, no auth, no rate limit** | `audit_devex` (SDK freshness) → Conversion |
| Google PageSpeed Insights API (extended call) | (existing env `PAGESPEED_API_KEY`) | Add `category=accessibility` param (5 LOC change) — unlocks Lighthouse a11y score + per-rule audit results | **Free** (already in inventory; new use only) | `audit_accessibility` → Conversion + SEO |
| `axe-playwright-python` | New PyPI dep (`axe-playwright-python>=0.1.4`, actively maintained by Pamela Fox) | Injects axe-core via Playwright; ~90 a11y rules vs Lighthouse's ~45; per-selector violation reporting | **Free** (open-source axe-core CDN) | `audit_accessibility` → Conversion + SEO |
| `textstat` (pinned 0.7.4 — PyPI "Inactive"-flagged but functional) + `py-readability-metrics` (fallback) | New PyPI deps | 7 readability metrics (Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau, ARI, Dale-Chall, Flesch Reading Ease) for copy-quality scoring; quarterly review for textstat replacement | **Free** | `audit_messaging_consistency` (copy-quality deepening) → Brand/Narrative |
| `spaCy` + `en_core_web_sm` model (~50MB) | New PyPI dep | POS tagging, dependency parse, NER for headline-strength + voice-consistency scoring | **Free** | `audit_messaging_consistency` (copy-quality deepening) → Brand/Narrative |
| DataForSEO On-Page hreflang fields (extension to existing provider) | `src/seo/providers/dataforseo.py:audit_hreflang()` (new method calling `/v3/on_page/links?include_hreflang=true`) | hreflang validation per URL — `is_valid_hreflang`, hreflang values, reciprocity check inputs | Per-call ~$0.01 | `audit_international_seo` → SEO |
| DataForSEO Business Data API — Google My Business (extension) | `src/seo/providers/dataforseo.py:business_data_gbp()` (new method calling `/v3/business_data/google/my_business_info/live`) | Public GBP data — name, address, phone, categories, rating, review count, hours, claimed status — **without needing GBP API approval** | ~$0.05/lookup | `audit_local_seo` → SEO (the keystone reuse — no GBP OAuth gate) |
| DataForSEO SERP `local_pack` + `serp_site_query` (extension) | `src/seo/providers/dataforseo.py:local_pack_serp()` + `serp_site_query()` | Local-pack rankings for "near me" + city queries; `site:domain` queries for directory/marketplace presence detection (G2/Capterra/Zapier/AppExchange/etc.) | ~$0.0006-0.002/query | `audit_local_seo`, `audit_directory_presence`, `audit_marketplace_listings`, `audit_corporate_responsibility` (PDF discovery) → SEO + Distribution + Brand/Narrative |
| DataForSEO SERP Advanced (Knowledge Panel + AI Overview + sitelinks + reviews stars + PAA) | `src/seo/providers/dataforseo.py` — same endpoint | Brand-name SERP for defensive-perimeter audit — single call returns Knowledge Panel claimed-status + sitelinks accuracy + reviews stars + AI Overview cited sources + People-Also-Ask defensive queries (`is X legit?`, `is X scam?`) + top stories + featured snippet on `<brand>` + `<brand> reviews` + `<brand> alternatives` | ~$0.0006/query × 4 = $0.003/audit | `audit_branded_serp` → Brand/Narrative |
| Google autosuggest endpoint (free) + SerpAPI fallback | Direct httpx (`http://suggestqueries.google.com/complete/search?client=chrome&q=<seed>`) | Brand autosuggest mining — `is <brand>...`, `<brand> reviews`, `<brand> alternatives`, `<brand> vs Y`, `<brand> scam`, `<brand> down` | **Free** direct / $0.05 worst-case SerpAPI fallback | `audit_branded_autosuggest` → Brand/Narrative |
| SEC EDGAR APIs | (agent WebFetch — `data.sec.gov`) | Ticker → CIK lookup via `company_tickers.json` (daily-refresh ~3MB); filings history via `data.sec.gov/submissions/CIK<10-digit-padded>.json`; required `User-Agent` header enforced | **Free, 10 req/sec** | `audit_public_company_ir` (conditional public firmographic) → Brand/Narrative |
| Hugging Face Hub API | (agent WebFetch — `huggingface.co/api`) | Org page existence + model count + total downloads (current + all-time) + likes + datasets + spaces + library tags (transformers/diffusers/sentence-transformers) + inference-provider mappings + trending score | **Free**, optional `HUGGINGFACE_TOKEN` raises ceiling (PRO/Team tier) | `audit_huggingface_presence` (conditional AI firmographic) → Distribution + GEO |
| Mailinator public inbox API + Maildrop / GuerrillaMail / tempmail.io fallback | (agent WebFetch — Mailinator public/private inbox API) | Disposable inbox polling for welcome-email capture via `GET api.mailinator.com/v2/domains/public/inboxes/<inbox-name>` + per-message fetch; HTML body + raw headers (DKIM/SPF/DMARC parse) | **Free** (public) / ~$99/mo private Mailinator domain at scale | `audit_welcome_email_signup` (conditional free-trial/freemium detected + manual user opt-in flag) → PLG + Lifecycle + MarTech |
| APIs.guru OpenAPI directory | (agent WebFetch — `api.apis.guru/v2/list.json`) | Cached `GET https://api.apis.guru/v2/list.json` (1.7MB, weekly refresh); lookup by prospect domain in `info.contact.url` or `info.x-providerName` | **Free** | `audit_open_api_public_data_access` → Distribution |
| Reddit OAuth API (free tier) | (agent WebFetch — Reddit OAuth) | IAmA history search + brand-subreddit existence + activity. **Reddit free unauthenticated search.json formally degraded in 2026** — requires OAuth client-credentials flow | **Free** (with `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`; one-time ~30min OAuth app setup) | `audit_reddit_ama_brand_subreddit` → Brand/Narrative + Monitoring |
| Mail-Tester sender reputation (rate-limited free) | (agent parse — raw .eml DMARC-alignment headers) | Sender reputation scoring when we POST captured welcome-email .eml — but heavily rate-limited. Alternative: parse DMARC-alignment (RFC 7489) from raw headers directly | **Free** with rate limit | `audit_welcome_email_signup` sender-reputation sub |
| Firebase Dynamic Links (`*.page.link`) | — | **DEAD as of 2025-08-25 (Firebase FAQ)** — detection should flag as **broken-FDL finding** (still-live FDL = active outage), NOT treat as live infra. Live alternatives: Branch.io (`*.app.link`), Adjust, AppsFlyer OneLink | N/A — deprecation detection | `audit_mobile_app_linking` (conditional mobile-app firmographic) → Distribution |
| Greenhouse Job Board API `?questions=true` extension | `src/audit/primitives.py:scrape_careers` extension | Full application-form question schema per job (fields, required flags, types, document-upload spec, demographic questions, GDPR consent fields) | **Free, unauthenticated** | `audit_hiring_funnel_ux` (conditional ATS detected) → Brand/Narrative + Conversion |
| Ashby Job Posting API | Direct httpx via `scrape_careers` extension | Public board listing + full job details schema (`https://api.ashbyhq.com/posting-api/job-board/<board>`) | **Free, unauthenticated** | `audit_hiring_funnel_ux` (conditional ATS detected) |
| Website Carbon Calculator API | Direct httpx | Free `https://api.websitecarbon.com/site?url=<url>` — CO2/page estimate + green-hosting signal | **Free** | `audit_sustainability_carbon` (sub of `audit_corporate_responsibility`) → Brand/Narrative |
| Green Web Foundation greencheck API | Direct httpx | `https://api.thegreenwebfoundation.org/api/v3/greencheck/<domain>` — green-hosting verification | **Free** | `audit_sustainability_carbon` sub |
| Wayback Machine CDX (extended) | Direct httpx (already in plan) | Logo-evolution via pHash diff on historical hero images + name-change via meta-title diff + domain-migration history | **Free** | `audit_rebrand_history` (sub of `audit_messaging_consistency`) → Brand/Narrative |
| Podchaser GraphQL (extended, free tier) | (already in plan) | Owned-podcast ratings + reviews + guest-tier | **Free tier** | `audit_owned_podcast_quality` (sub of `audit_podcast_footprint`) |
| Substack / Beehiiv public leaderboards | Direct httpx (RenderedFetcher) | Substack `/discover/rising` + `/discover/top` per category; Beehiiv `/explore`; ConvertKit `kit.com/<handle>`; SparkLoop network indicator | **Free** scrape | `audit_newsletter_leaderboard_rank` (sub of `audit_content_strategy_shape`) → Brand/Narrative |
| Atlassian Statuspage `/history.atom` + Better Stack `/feed` | Direct httpx | Incident-history feeds for status page maturity audit (incident frequency last 90d, MTTR signals, post-mortem cadence) | **Free** | `audit_status_page_maturity` (sub of `audit_partnership_event_community_footprint`) |
| HackerNews / Show HN / Reddit dev-event data | HN free Firebase API + Reddit OAuth + SerpAPI | Hackathon sponsorship detection (`site:mlh.io`, HackerEarth, Devpost) | **Free + SerpAPI** | `audit_hackathon_dev_event_sponsorships` (conditional dev-tool, sub of `audit_partnership_event_community_footprint`) |
| RapidAPI / Postman Public Network / APIs.guru / Bump.sh | DataForSEO `serp_site_query` + direct APIs.guru | API-marketplace presence detection. **ProgrammableWeb dead since 2022** (Mulesoft consolidation) — dropped from scope. **RapidAPI declining post-Nokia 2024** — historical signal only | **Free** (APIs.guru) / SerpAPI fallback | `audit_open_api_public_data_access` → Distribution |

**Cancelation candidates (revisit after 5 audits):** none in v1. Foreplay's `persona` / `emotional_drivers` / `creative_targeting` fields are audit gold that raw Apify Meta Ad Library scrapes don't provide; Adyntel is already cheap ($0.027/audit at max 3 pages). Google Ads Transparency BigQuery is optional supplemental depth only — not a replacement. If the first 5 audits reveal Foreplay coverage gaps, add an Apify Meta Ad Library scraper as a **secondary** source; don't cancel Foreplay.

## Key decisions (resolved in 2026-04-19/20 design session)

- Claude Agent SDK (Python), not ported Freddy ADK; inline prompts, not skills library.
- Sonnet for pre-discovery synthesis + all 7 Stage-2 agents (findings work); Opus for Stage-3 synthesis, surprises, proposal. 7 Stage-2 agent sessions → 9 report sections decoupled deliberately: SEO+GEO merged into Findability agent (shared EEAT/robots/schema/content-authority signals); Conversion+Lifecycle merged into one funnel agent (shared capture/trust/martech-stack-slice signals); Brand/Narrative + Distribution + MarTech-Attribution + Monitoring + Competitive each have dedicated agents. Findings route to sections via `Finding.report_section: Literal["seo","geo","competitive","monitoring","conversion","distribution","lifecycle","martech_attribution","brand_narrative"]` enum tagged by the producing agent; no pivot table.
- Local file storage only; per-stage git commits.
- Two-call sales model: sales call between free scan and $1K paid audit (JR pitches using AI-visibility gap as hook); walkthrough call post-delivery (JR walks through findings + pitches $15K+ engagement). Both captured by Fireflies via separate webhook endpoints.
- Manual-fire pipeline for the paid audit: JR runs every `freddy audit run [--stage N]` command locally via Claude Code. No laptop poller. Webhooks (Stripe, Fireflies) update state but never trigger pipeline stages. The free AI Visibility Scan (R16) auto-runs on form submission because it's lightweight and volume matters there. Auto-firing the full audit pipeline deferred to a future plan.
- **Two-tier product model — audit as lead magnet, engagement as the real product.** Free AI Visibility Scan (narrow, ~$1–2 infra) drives top-of-funnel volume; $1K full audit filters serious prospects and anchors the $15K+ engagement close. Audit revenue is secondary; engagement conversion is the primary success metric. Positioning: "free teaser of your AI search posture" → "$1K full marketing diagnosis" → "$15K+ engagement that actually does the work." **Conversion-rate assumption is unvalidated** (see R10 kill-criterion); the architecture commits regardless because the audit deliverable has standalone value to the prospect even if engagement conversion under-performs.
- **Audit delivers diagnosis + pitch, not a DIY playbook.** Findings' `recommendation` field is strategic (what to solve) + tier-mapped (which proposal tier addresses it), NOT tactical execution detail. "Recommended Next Steps" section maps findings directly to Fix-it / Build-it / Run-it proposal tiers. The engagement delivers implementation, account-gated data (Search Console, Analytics, Ad platforms, ESP), monthly iteration, and reports the audit cannot produce. The audit shows WHAT; the engagement DOES.
- Greenfield primitives replace paid APIs: python-Wappalyzer → BuiltWith, crt.sh + subfinder → SecurityTrails, public-page scraping → PDL + TheirStack.
- Registry-driven pricing: LLM picks capability IDs, Python applies prospect-size multiplier deterministically.
- HTML primary + PDF rendered from same HTML (WeasyPrint).
- Lead capture only via Cloudflare Worker → Fly API → Supabase row → Slack ping to JR (no poller, no auto-fire). JR manually creates workspace + fires stages in Claude Code.
- **SaaS-parity signal coverage**: prospects compare audits against Ahrefs / SEMrush / PageSpeed Insights baseline expectations. Three primitives close the obvious gaps: `analyze_backlinks` (DataForSEO Backlinks API — referring domains, anchor text, toxic signals), `audit_page_speed` (Google PageSpeed Insights API — Core Web Vitals LCP/INP/CLS for mobile + desktop), `historical_rank_trends` (DataForSEO Historical — 6-month organic traffic and rank drift). These are inputs to existing lenses, not new lenses. Positioning: we don't out-scan Ahrefs on raw depth — we synthesize across signals SaaS tools don't integrate (backlinks + GEO + VoC + conversion in one narrative).
- **Coverage expansions (Option B + C + R1 + R2)**: through four expansion rounds the audit grew to **86 named primitives across 9 report sections** (vs the baseline ~32 primitives across 4 sections); 9 conditional enrichments (R18–R26) layer additional depth when the prospect grants access. Coverage is described against our own catalog (constructed for this product), not an external standard — comparable in breadth to a Big-4 consultancy teardown plus AI search. Per-expansion details — including the 7 R1 spec changes (textstat pin, wappalyzer-next swap, Lift Wing replacement of ORES, Bright Data Glassdoor path, Mozilla HTTP Observatory v2 replacement of SecurityHeaders.com, `audit_funnel_content_shape` rename + severity-cap, `audit_form_cro_deep` fold into `capture_surface_scan`) and the 4 R2 infrastructure decisions (Firebase Dynamic Links flagged as broken-FDL outage, ProgrammableWeb dropped, RapidAPI demoted to historical, Reddit OAuth required) — captured in `docs/plans/2026-04-22-002-audit-coverage-research.md` and `docs/plans/2026-04-22-003-audit-coverage-research-r2.md`. Cost delta worst-case: +$2.50–5.50/audit incremental when all triggered, +$3–8 with R23 demo + R26 winloss firing. Within R7 budget envelope.
- **Owned-provider-first discipline (R17):** the plan references 15+ owned providers via the Data provider inventory (Architecture section). Every new data signal must be justified against that inventory before adding an external integration. Paid-media intel flows through `CompetitiveAdService` (Foreplay + Adyntel) because `_normalize_foreplay` exposes `persona`, `emotional_drivers`, `creative_targeting`, `market_target`, `transcription` — fields a raw Apify Meta Ad Library scrape does not provide. BigQuery Google Ads Transparency dataset is available as optional supplemental historical depth only.
- Phase 1 infra: ~$40–70/mo. Phase 2 upgrades (PDL, TheirStack, SecurityTrails paid tiers, BuiltWith) only if real audits reveal gaps.
- **Agents get directions, not instructions.** All LLM prompts follow a directive skeleton (role / objective / context / tools+heuristics / effort scaling / quality bar / output contract / termination) rather than step-by-step playbooks. Anthropic's north star for agentic work: *"good heuristics rather than rigid rules."* Count mandates become quality bars; prescribed sequences become objectives.
- **Design history**: the plan crystallized through five iterative restructure passes (2026-04-22) that converged on the current shape — cache-backed SDK tools + agent-driven free-API investigations + capability restriction for safety + full eval harness. Reader does not need the history to understand the design; current state is described in Architecture + Module layout + each U section.
- **Safety via capability restriction, not hooks.** 3 safety-critical code paths (`audit_welcome_email_signup` per P84, `audit_hiring_funnel_ux` per P86, `attach-demo` per R23) run under scoped `ClaudeSDKClient` sessions configured to *positively* restrict capability surface — three reinforcing controls because `permission_mode="bypassPermissions"` (used everywhere else in the pipeline) would otherwise grant every SDK builtin: (1) `permission_mode="default"` (NOT bypass) for the safety-bounded session — every tool use prompts unless explicitly pre-allowed; (2) `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` to deny-list every general-purpose builtin even before the prompt-deny stage; (3) `mcp_servers={"playwright_obs": build_playwright_obs_server()}` (or `{"mailbox_obs": build_mailbox_obs_server()}` / `{"ats_obs": build_ats_obs_server()}` per primitive) + `allowed_tools=["mcp__playwright_obs__page_goto", "mcp__playwright_obs__page_screenshot", "mcp__playwright_obs__locator_get_attribute", "mcp__playwright_obs__accessibility_snapshot"]` — only observation primitives are reachable. The destructive capability (form submit, link click, Bash) is positively absent from the agent's allow-list AND the deny-list AND the MCP-server tool surface, so the safety story rests on three independent layers, not on "we forgot to expose it." R21 attach-survey and R22 attach-assets are NOT under capability restriction (survey is a CSV/JSON read via Bash; assets is a text-extraction helper). URL-blocklist PreToolUse hooks rejected because blocklists are infinitely bypassable (URL encoding, nested paths, agent routes around via WebFetch). Orchestrator pre-conditions (opt-in flag, 1-shot cap, identifiable-fixture validation) enforce invariants in Python before primitive invocation. Per-action human confirmation for irrecoverable operations (demo form submission, welcome-email signup send). Observability hooks (PostToolUse + PreCompact + Stop) remain as telemetry/archive/flush, not safety. Sentinel `max_turns` per session: 500 (Stage 2 agents) / 600 (Stage 1 brief Sonnet) / 400 (demo-flow scoped session) — runaway-loop backstop at 5-10× expected normal max, never a cognitive budget. No cost gates beyond the per-audit ceiling (see U1 cost-circuit-breaker + concurrent-run lock), no output-quality auto-aborts. **Required regression tests in `tests/audit/scoped_tools/test_safety_invariants.py`**: hostile-agent harness that simulates a Sonnet session under each scoped toolbelt and asserts every blocked operation (Bash, WebFetch, page.click, page.fill, page.evaluate, Task delegation) raises `ToolNotFound` / `PermissionDenied` at SDK level, not "the prompt happened not to ask for it."
- **Session resumability is native.** Every `ClaudeSDKClient` session persists its `session_id` into `state.json` and runs with `enable_file_checkpointing=True`. A crashed agent resumes via `resume=<session_id>` rather than restart. Recovery scope: a crash AFTER the first `ResultMessage` resumes cleanly via the persisted `session_id`; a crash BEFORE first `ResultMessage` (no `session_id` ever persisted) restarts that session from scratch — JR loses at most one session's worth of work, never the whole audit because earlier stages were git-committed. `permission_mode="bypassPermissions"` enables unattended roaming for the standard pipeline; the 3 safety-bounded scoped sessions explicitly set `permission_mode="default"` instead — see "Safety via capability restriction" decision above.
- **Envelope schemas, not content schemas.** Pydantic contracts (`Finding`, `AgentOutput`, `ProposalSection`, `FitSignals`) prescribe the *shape* that downstream code consumes; agents fill them freely (any count, any severity mix). Counts ("3–5 surprises", "pick 3 capabilities") are quality-bar heuristics in prompts, never mandates.
- **Telemetry, not gating — with three operational circuit breakers.** Per-tool-call telemetry streams `total_cost_usd + duration_ms + num_turns + model_usage + session_id` into `clients/<slug>/audit/cost_log.jsonl`. Cost anomaly alerts (3σ above rolling p95) Slack-ping JR for post-hoc review. Telemetry doesn't gate normal variance, but three hard circuit breakers DO gate catastrophic cases (the cost of an unbounded failure on a solo-operator setup is high enough to warrant a hard cap):
  - **Per-audit cost ceiling.** `state.cost_spent_usd` is incremented by every `ResultMessage`; if cumulative spend on an audit crosses `max_audit_cost_usd` (default $50, configurable per-client), the orchestrator raises `CostCeilingExceeded` and halts subsequent stages. JR resolves manually (raise the ceiling + resume, or abort + refund). Prevents adversarial-prospect or runaway-loop scenarios from silently costing $200-500.
  - **Concurrent-run lock.** `state.active_run` carries `{pid, started_at, host}`. `freddy audit run` refuses to start if `active_run.pid` is alive (`os.kill(pid, 0)` succeeds) — exits with `AuditRunInProgress` and prompts JR to wait or `--force-clear-lock` (after confirming the prior process is truly dead). Prevents double-fire from misclick / forgotten background terminal / "thought it crashed."
  - **Pre-flight adversarial check.** Before Stage 2 fires, Stage-1-end pre-flight inspects: (a) `freddy sitemap` URL count — reject if >500 (configurable); (b) crt.sh subdomain count — reject if >500 (wildcard-DNS trap); (c) prospect domain age via WHOIS — flag if <30 days (potential burn account). Rejection writes `state.preflight_block` + Slack-pings JR; JR can `--override-preflight` after manual review.

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
- `state.py`: Pydantic `class AuditState(BaseModel)` with `.load(slug)` / `.save()` / `.record_session()` / `.record_payment()` / `.record_call()` / `.record_enrichment()` / `.commit_stage()` / `.acquire_run_lock()` / `.release_run_lock()` / `.add_cost(usd)` / `.preflight_check(sitemap_urls, subdomains, domain_age_days)` methods (~120 LOC).
  - `acquire_run_lock(pid)` raises `AuditRunInProgress` if `state.active_run.pid` is alive (verified via `os.kill(pid, 0)` + host match).
  - `add_cost(usd)` increments `state.cost_spent_usd` and raises `CostCeilingExceeded` if `cost_spent_usd > state.max_audit_cost_usd` (default $50).
  - `preflight_check(...)` writes `state.preflight_block` and raises `PreflightFailed` if sitemap >500 URLs OR crt.sh >500 subdomains OR domain_age_days <30. JR overrides via `freddy audit run --override-preflight`.
  Fields:
  - `current_stage`, `stage_results` (dict), `cost_spent_usd` (telemetry + circuit-breaker source), `calibration_mode` (bool)
  - `max_audit_cost_usd` (default 50.0; per-client override)
  - `active_run: {pid: int, started_at: datetime, host: str} | None` — concurrent-run lock
  - `preflight_block: {reason: str, sitemap_urls: int, subdomains: int, domain_age_days: int} | None` — pre-flight gate state
  - `sessions`: dict keyed by agent role → `{session_id, last_turn, last_cost_usd, last_duration_ms}`. Roles span Stage-1 (pre-discovery Sonnet + brief-synthesis Opus), all 7 Stage-2 agent names + their `<agent>_critique` / `<agent>_revision` sub-sessions, all 9 Stage-3 section synthesis calls + `synthesis_master` + `surprise_critique` + `proposal`, per-safety-bounded-primitive scoped sessions (`welcome_email_signup`, `hiring_funnel_ux`, `attach_demo`), and sales/walkthrough/free-scan roles
  - `cache_dir`: str, defaults to `clients/<slug>/audit/cache/`
  - `agents_rubric_status: dict[agent_name, {covered_count, gap_flagged_count, total_rubrics}]` — updated after each Stage-2 agent, surfaced in `synthesis/gap_report.md`
  - `payment: {paid: bool, stripe_session_id, stripe_payment_intent_id, amount_usd, paid_at}`
  - `sales_call: {scheduled_at, completed_at, transcript_path, fit_signals_path}` and `walkthrough_call` with same shape
  - **`enrichments`** (dict covering R18–R26 conditional enrichments):
  ```
  enrichments: {
    gsc: {attached: bool, service_account_path, site_url, attached_at},               # R18
    esp: {attached: bool, vendor: "klaviyo"|"mailchimp"|..., attached_at},            # R19
    ads: {google: {...}, meta: {...}, linkedin: {...}, tiktok: {...}},                # R20 per-platform
    survey: {nps: {...}, csat: {...}, churn: {...}, exit: {...}},                     # R21 per-type
    assets: {attached: bool, asset_ids: [], attached_at},                             # R22
    demo: {attached: bool, url, username_redacted, readonly_mode, trace_path,         # R23 (credentials never persisted in plain text)
           attached_at, audit_completed_at, ttfv_seconds, ttfv_steps},
    budget: {attached: bool, file_path, total_monthly_spend, currency, attached_at},  # R24
    crm: {attached: bool, source: "hubspot"|"salesforce"|"pipedrive"|"close"|"attio"|"csv",  # R25 (PII-sensitive — gitignore'd)
          file_path_or_oauth_redacted, opportunity_count, period_days, attached_at},
    winloss: {attached: bool, file_paths: [], interview_count, attached_at}           # R26
  }
  ```
  All enrichment slots start as `{attached: false}`. Plus functions `load()`, `save()`, `record_session(state, role, result_message)`, `record_payment(state, stripe_event)`, `record_call(state, call_type, fit_signals)`, `record_enrichment(state, enrichment_type, metadata)` (single unified function covering GSC / ESP / Ads / Survey / Assets), `commit_stage(state, stage_name, outputs)`. No class hierarchy. No cost gates — costs are appended to `cost_log.jsonl` via `telemetry.py` and never block execution. Stage 2 raises `PaymentRequired` if `state.payment.paid == False` when attempted — operational safety, not an agent cap.
- `run.py`: single `run_audit(slug, target_stage=None)` function that loops through stage functions and calls them in order.
- Workspace layout: `clients/<slug>/audit/{intake,cache,prediscovery,agents,synthesis,proposal,deliverable,walkthrough}/` + `state.json` + `cost_log.jsonl`. Each Stage-2 agent writes to `agents/<agent>/`; findings tagged with `report_section` Literal enum route to 9 report sections in Stage 3. `cache/` holds tool-handler cache files keyed by `<tool_name>_<sha256(args)[:12]>.json`, 24h TTL, doubles as eval-fixture substrate.
- Atomic state writes: `state.json.tmp` → rename → `git add && git commit`.

**Test scenarios:**
- Happy: fresh workspace + `freddy audit run` populates state.json and commits.
- Happy: `freddy audit run --stage 3` resumes at stage 3 only.
- Happy: `state.sessions[<role>].session_id` populated after any Claude Agent SDK call completes; subsequent resume uses it.
- Happy: `record_payment(state, stripe_event)` sets `state.payment.paid = True` and persists via atomic rename + git commit.
- Edge: running `freddy audit run --stage 2` with `state.payment.paid == False` raises `PaymentRequired` with message pointing JR to `freddy audit send-invoice` and `freddy audit mark-paid`.
- Edge: a second `freddy audit run --client acme` while the first is alive raises `AuditRunInProgress` with `state.active_run.pid` in the message; `--force-clear-lock` after manual confirmation succeeds.
- Edge: cumulative `state.cost_spent_usd` crosses `max_audit_cost_usd` mid-stage → `CostCeilingExceeded` raised; orchestrator halts; subsequent stages refuse to run until JR raises ceiling or aborts.
- Edge: pre-flight check fires on a prospect whose sitemap returns 1200 URLs → `PreflightFailed` with `preflight_block` populated; JR reviews + either overrides or aborts the audit.
- Edge: corrupted state.json raises actionable error with `--reset` hint.
- Happy: `content_extractor.extract(url)` returns non-empty result for HTML, PDF, YouTube URLs.

**Done when:** `freddy client new test --url https://example.com && freddy audit run --client test` produces valid empty workspace + state.json with all stages pending + one git commit.

---

### U2. Pre-discovery primitives (2 local helpers + 6 cache-backed SDK tool handlers + ~75 agent-driven free-API investigations)

**Goal:** Stage-1 pre-discovery agent + 7 Stage-2 agents + 2 local helpers + 6 cache-backed tool handlers cover the full signal surface area of the audit coverage catalog. The agent layer does WebFetch/Bash work directly per prompt-mention instructions.

**Composition:**
- **~15 owned-provider tool handlers** under `src/audit/tools/` (~300 LOC total, see U2.5 below): `dataforseo_tool` (8 endpoints) + `cloro_tool.ai_visibility` + `competitive_tool.ads` (Foreplay+Adyntel via existing CompetitiveAdService) + `monitoring_tool` (dispatches to 12 existing adapters) + `gsc_tool` (when attached). Each is cache-aware: read cache → return on hit; provider-call → write cache → return on miss. Handlers wrap existing wired providers in `src/seo/providers/*`, `src/geo/providers/*`, `src/competitive/*`, `src/monitoring/adapters/*` — zero new provider modules.
- **2 local-only Python helpers** in `src/audit/primitives.py`: `fingerprint_martech_stack()` (wappalyzer-next + `data/martech_rules.yaml` regex/JS-fingerprint extension) and `content_strategy_embeddings_cluster()` (text-embedding-3-small + k-means for content-pillar clustering). Both run locally without network.
- **~75 free-public-API investigations** become **prompt-mention instructions** in the Stage-1 pre-discovery agent prompt (`prompts/predischarge.md`) and the 7 Stage-2 agent prompts. Each prompt names: target URL pattern, auth pattern, polite pace, pagination pattern, expected response shape, and the rubric the data feeds. Agent uses WebFetch / `cli/scripts/fetch_api.sh` (curl-with-retry) to execute. Sources covered include GitHub REST/GraphQL, Wikipedia/Lift Wing, SEC EDGAR, HuggingFace Hub, Reddit OAuth, Product Hunt GraphQL, crt.sh, Firefox AMO, Atlassian Marketplace, MediaWiki, GDELT, Discord Invite, Podchaser, APIs.guru, Mailinator/disposable-email, Mail-Tester, Mozilla HTTP Observatory, npm registry, PyPI JSON, Greenhouse/Lever/Ashby/Workable ATS APIs, Wayback CDX, Bluesky AT Protocol, axe-playwright accessibility.
- **3 safety-bounded primitives** (`audit_welcome_email_signup`, `audit_hiring_funnel_ux`, R23 `attach-demo`) require capability restriction via `src/audit/scoped_tools.py` — the destructive capability isn't in the agent's toolbelt at all.

**Coverage catalog:** the audit covers ~80 primitives across 11 functional groups. Full per-primitive specs — signals / sources / cost / confidence / trigger conditions / dependencies — live in `docs/plans/2026-04-22-002-audit-coverage-research.md` (P1–P48 + 2 conditional firmographic primitives) and `docs/plans/2026-04-22-003-audit-coverage-research-r2.md` (P49–P86 + 3 reasoning primitives). Primitive groups:

| Group | Count | Trigger | Research doc |
|---|---:|---|---|
| Baseline (P1–P9) | 9 | Unconditional | R1 |
| SaaS-parity (P10–P18) | 9 | Unconditional | R1 |
| Full-agency Distribution/Lifecycle/MarTech-Attribution (P19–P25) | 7 | Unconditional | R1 |
| Brand/Narrative baseline (P26–P30) | 5 | Unconditional | R1 |
| ASO (P31) | 1 | Conditional: mobile-app detected | R1 |
| Coverage-expansion R1 SEO/Distribution/Brand/Conversion (P32–P48) | 17 | Mix (conditional per group) | R1 |
| Conditional firmographic (plg_motion, devex) | 2 | Conditional: SaaS / dev-tool | R1 |
| Coverage-expansion R2 Group A SEO+GEO+Compliance (P49–P55) | 7 + 5 extensions | Mix | R2 |
| Coverage-expansion R2 Group B Brand+Narrative+PR (P56–P59) | 4 + 9 extensions | Mix | R2 |
| Coverage-expansion R2 Group C Conversion+Trust+Sales (P60–P68) | 9 + 3 extensions | Mix | R2 |
| Coverage-expansion R2 Group D Distribution+Community (P69–P78) | 10 + 3 extensions | Mix | R2 |
| Coverage-expansion R2 Group E Specialized (P79–P86) | 8 | Mix | R2 |
| Reasoning primitives | 3 | Synthesis | R1+R2 |

**Key notes the research docs don't already carry** (plan-level decisions, not per-primitive specs):
- `audit_funnel_content_shape` (P47) has severity-cap=low — descriptive content/CTA shape only, NEVER framed as a velocity claim. Stage 3 `synthesis_master.md` explicitly excludes this primitive from velocity-language permissions.
- `audit_industry_analyst_position` (P58) is the single largest remaining B2B SaaS finding — Gartner MQ Leader drives 30-50% enterprise close rate.
- `audit_email_signature_marketing_indicators` (P79) emits findings only when ≥2 weak signals concur (MEDIUM-LOW confidence triangulation).
- `audit_welcome_email_signup` (P84) and `audit_hiring_funnel_ux` (P86) and `attach-demo` are the 3 safety-bounded primitives — manual opt-in + capability restriction + per-action human confirmation.
- `audit_error_page_ux` (P80) uses 2-probes-max + jittered random `/__gofreddy-audit-{uuid}-404test` paths (WAF safety).

**External source cost envelope:** Net-new sources are all free or near-free. Two new paid dependencies: Bright Data for Glassdoor (~$0.10–0.50/audit, Tier-2 escalation for >$10M revenue only) and Apify LinkedIn page-only scrape (~$0.05/audit Tier-1 default). Existing paid: SerpAPI, DataForSEO. Total cost delta worst-case: +$2.50–5.50/audit when all conditional primitives trigger; +$3–8 when R23 attach-demo + R26 attach-winloss also fire.

**Per-primitive coverage specs** — full dossiers (triggers / signals / sources / cost / confidence) live in `docs/plans/2026-04-22-002-audit-coverage-research.md` (P32–P48 + audit_plg_motion + audit_devex) and `docs/plans/2026-04-22-003-audit-coverage-research-r2.md` (P49–P86 + reasoning primitives). Baseline P1–P31 coverage is delivered by cache-backed tool handlers (U2.5) or agent prompt-mention investigations (U3 + U4). Agent prompts inline URL patterns + auth + polite-pace per rubric. Dependency ordering is implicit in Stage 1 (cache warmup precedes Sonnet pre-discovery), not encoded in a registry.

**Files:**
- Create `src/audit/rendered_fetcher.py` — `RenderedFetcher` class (context manager, single shared browser context per audit).
- Create `src/audit/primitives.py` — 2 local-only helpers: `fingerprint_martech_stack()` + `content_strategy_embeddings_cluster()`.
- Create `src/audit/data/` YAMLs — see Module layout for the 10-file inventory + per-file consumer notes.
- Modify `pyproject.toml` — add `claude-agent-sdk>=0.1.0` (pipeline orchestration foundation; pulls in the Claude Code Node CLI subprocess at runtime — Node 18+ required on JR's laptop), `playwright>=1.45.0`, `wappalyzer-next>=0.4.0` (PyPI install name is `wappalyzer-next`, NOT `wappalyzer`; supersedes unmaintained `python-Wappalyzer`), `beautifulsoup4>=4.12.0`, `dnspython>=2.6.0`, `google-api-python-client>=2.0.0` (YouTube + GSC), `hdbscan>=0.8.40` (requires C compiler — XCode CLT on macOS, build-essential on Linux; `scikit-learn>=1.4.0` fallback), `textstat==0.7.4` (pinned; `py-readability-metrics>=1.5.0` fallback), `spacy>=3.7.0`, `axe-playwright-python>=0.1.4`, `python-pptx>=0.6.23`, `pdfplumber>=0.11.0` (R26 win-loss; PyMuPDF already in deps), `imagehash>=4.3.1` (Wayback logo-evolution pHash), `praw>=7.7.0` (Reddit OAuth + backoff), `feedparser>=6.0.0` (Statuspage `/history.atom` + Better Stack `/feed`), `huggingface-hub>=0.20.0`, `stripe>=7.0.0`. `email` stdlib for raw .eml header parsing. **Post-install steps** (Makefile target `make audit-bootstrap`): (a) `playwright install chromium` (downloads Chromium binary ~150MB); (b) `python -m spacy download en_core_web_sm` (~50MB model); (c) `axe-playwright-python` uses axe-core via CDN at runtime — no extra install. DataForSEO calls extend existing `src/seo/providers/dataforseo.py` with `audit_hreflang()`, `business_data_gbp()`, `local_pack_serp()`, `serp_site_query()` methods + matching `HreflangValidation` / `GBPInfo` / `LocalPackResult` / `SiteQueryResult` Pydantic response models + `_parse_*` privates (~100-150 LOC, not 5-LOC stubs). All other free public-API calls use `httpx` directly. Bright Data Glassdoor + Apify scrapers via existing `_common.py` wrapper.
- Environment vars (required): `PAGESPEED_API_KEY`, `YOUTUBE_API_KEY`, `SERPAPI_KEY` (~$130/mo upgraded tier), `PODCHASER_API_KEY`, `GITHUB_TOKEN` (free PAT, 5K req/hr), `PRODUCT_HUNT_TOKEN` (free OAuth client-credentials), `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` (Reddit OAuth). Optional: `WIKIMEDIA_API_KEY` (Lift Wing), `BRIGHTDATA_API_KEY` (Tier-2 Glassdoor for >$10M revenue), `HUGGINGFACE_TOKEN` (raises HF Hub ceiling), `MAILINATOR_API_TOKEN` (private domain at scale). Per-client OAuth tokens for R19–R22 enrichments (`KLAVIYO_API_KEY`, `MAILCHIMP_API_KEY`, `CUSTOMERIO_API_KEY`, `HUBSPOT_API_KEY`, `BRAZE_API_KEY`, `GOOGLE_ADS_OAUTH_TOKEN`, `META_ADS_OAUTH_TOKEN`, `LINKEDIN_ADS_OAUTH_TOKEN`, `TIKTOK_ADS_OAUTH_TOKEN`) live in `clients/<slug>/audit/enrichments.json`, not global env.
- Test: `tests/audit/test_primitives.py` — integration tests for the 2 local helpers; tool-handler tests in U2.5; agent investigation coverage validated in U9 eval harness.

**Approach:** all network-bound signal gathering happens via U2.5 cache-backed tool handlers (owned-provider calls) or U3/U4 agent investigations (free-public-API WebFetch with URL patterns named in agent prompts). `RenderedFetcher` is the shared Playwright context used by `scoped_tools.py` (attach-demo, hiring-funnel observation) and by the Sonnet pre-discovery agent when it needs JS-rendered HTML.

**Done when:** the 2 local helpers return schema-valid output on 3 dogfood prospects, and every coverage entry in the research-doc per-primitive catalog is reached by either a tool handler, a prompt-mentioned URL pattern, or a local helper (no orphan primitives).

---

### U2.5. Cache-backed SDK tool decorator (`src/audit/tools/`)

**Goal:** Ship the cache-backed `@cached_tool` decorator + cache layer + `register_audit_tools()` builder. One decorator wraps any existing provider method with hash → cache → provider-call → cache-write → ToolError-on-exception semantics uniformly; no per-provider wrapper files. Tools register as a single MCP server via `create_sdk_mcp_server`, attached to ClaudeAgentOptions via `mcp_servers={"audit": …}`.

**Files:**
- Create `src/audit/tools/__init__.py` (~60 LOC) — `register_audit_tools(state) -> SdkMcpServer`: imports existing wired providers (`src/seo/providers/dataforseo.DataForSeoProvider`, `src/geo/providers/cloro.CloroClient`, `src/competitive/service.CompetitiveAdService`, `src/monitoring/adapters/*`, `src/seo/providers/gsc.GSCClient` conditional), wraps each exposed method with the `@cached_tool` decorator + an `@tool(name, description, schema)` SDK decorator, then bundles them via `create_sdk_mcp_server(name="audit", version="1.0.0", tools=[...])`. Tool names: `backlinks`, `on_page`, `ai_visibility`, `voc`, `press`, `podcasts`, `gsc_search_analytics`, etc. — agents reach them as `mcp__audit__<toolname>`. Conditional: GSC tools included only when `state.enrichments.gsc.attached==True` (constructed at server-build time, not gated downstream).
- Create `src/audit/tools/cache.py` (~50 LOC) — `read_cache(slug, tool_name, args, ttl_hours=24) -> dict | None` + `write_cache(slug, tool_name, args, result) -> None`. Cache files at `clients/<slug>/audit/cache/<tool_name>_<sha256(json.dumps(args, sort_keys=True))[:12]>.json`. Each entry: `{ts, args, result, error?}`. TTL check on read returns `None` if expired. `force=True` tool-call arg bypasses cache.
- Create `src/audit/tools/cached_tool.py` (~30 LOC) — `@cached_tool` decorator: wraps any async callable with the cache pattern. Pseudocode: `async def wrapper(*args, force=False, **kwargs): if not force and (hit := await cache.read_cache(slug, name, args)): return hit; try: result = await func(*args, **kwargs); await cache.write_cache(slug, name, args, result); return result; except Exception as e: return ToolError(tool_name=name, args_hash=..., diagnostic=str(e), retryable=isinstance(e, (RetryableError, HTTPError)), retried_count=0)`. One retry internally on retryable errors before returning ToolError.
- Create `src/audit/tools/types.py` (~20 LOC) — `ToolError` Pydantic envelope: `{tool_name, args_hash, diagnostic: str, retryable: bool, retried_count: int}`. Agent prompt instructs "on ToolError, retry once with `force=True`; if still error, emit a gap_flag Finding with diagnostic."
- Test: `tests/audit/tools/test_cache.py` (TTL, hash determinism, force=True bypass) + `tests/audit/tools/test_register.py` (conditional gsc inclusion + decorator applied to every exposed method) + VCR-cassette integration tests for one happy-path call per provider.

**Approach:**
- Decorator pattern eliminates duplicated hash+cache+ToolError boilerplate that R5 had in 6 per-provider files. Existing providers carry the domain logic (auth, pagination, rate-limiting); the decorator is pure infrastructure.
- `register_audit_tools` iterates a small allowlist of `(provider_class, method_name, tool_name)` tuples — adding a new tool = one line. Returns an `SdkMcpServer` (from `claude_agent_sdk.create_sdk_mcp_server`); callers attach via `ClaudeAgentOptions(mcp_servers={"audit": server}, allowed_tools=["mcp__audit__*"])`.
- Cache key: `f"{tool_name}_{sha256(json.dumps(args, sort_keys=True))[:12]}"`. Deterministic in args.
- Cache files double as eval-harness fixtures; eval harness (U9) freezes a `cache/` dir per fixture prospect.
- **Total new LOC across `tools/`: ~160**.

**Test scenarios:**
- Happy: `dataforseo_tool.on_page(url=X)` first call → cache miss → provider call → cache write → result returned. Second call → cache hit → result returned (no provider call). Unit test asserts provider mock called exactly once.
- Happy: `force=True` on second call bypasses cache, provider mock called twice.
- Happy: cache TTL — set entry ts to >24h ago, second call treats as miss.
- Happy: hash determinism across arg key order.
- Happy: `register_audit_tools(state_with_gsc_attached)` returns an `SdkMcpServer` whose tool list includes `gsc_search_analytics`; `register_audit_tools(state_without_gsc)` does not.
- Edge: provider raises retryable error → handler retries once → if still fails → ToolError returned. Agent retries with `force=True` → if still error → emits gap_flag Finding.
- Integration: Stage 1 warmup populates cache; Stage 2 agents all see cache-hits for their initial tool calls; only drill-down calls add to cache.

**Done when:** A Stage-2 dogfood agent invocation pulls 5+ cache-hits for free and 2-3 drill-down calls that pay normal price; total Stage 2 cost is dominated by Sonnet inference, not provider calls.

---

### U3. Stages 0 + 1: intake + pre-discovery (cache-warmup + Sonnet pre-discovery + Opus brief)

**Goal:** Stage 0 (Python-only) populates workspace from intake form. Stage 1 runs in **three sub-stages** aligned with the cache-backed-SDK-tools design:

- **Stage 1 (a) — Cache warmup (parallel Python, unconditional).** `stages.py:stage_1_warmup` invokes the underlying provider methods directly (NOT via the MCP server — warmup is Python-side, no agent in the loop) in parallel via `asyncio.Semaphore(12)` to warm the per-audit cache. Full warmup set fired unconditionally: `DataForSeoProvider.{on_page,backlinks,historical_rank,serp_features,business_data_gbp}` + `CloroClient.ai_visibility` + monitoring `gather_voc/press/podcasts` dispatchers. (`backlinks` is prospect-only; competitor calls happen in U4 by Competitive agent.) Each call routes through the same `tools/cached_tool.py:cache_or_call(tool_name, args, fn)` helper the MCP-tool wrappers use, so the cache files Stage 1a writes are bit-identical to what Stage 2 agents will read via `mcp__audit__*` tool calls. The only conditional is GSC — included in `register_audit_tools(state)` only when `state.enrichments.gsc.attached==True` (gated at MCP-server-build time). Irrelevant signals for off-fit prospects cost ~$0.50-2/prospect; cache absorbs the waste. Agent prompts carry URL-pattern hints for free-public-API signals (GitHub, SEC EDGAR, HuggingFace, etc.) and agents decide whether to WebFetch based on prospect context surfaced in `brief.md` — no Python gating. Also runs the 2 local-only helpers synchronously: `fingerprint_martech_stack()` + cheap homepage Playwright fetch to seed `content_extractor`. Writes cached JSON via `tools/cache.py:write_cache(tool, args, result)`. Cost ~$2-4/prospect; wall-clock ~60-120s.
- **Stage 1 (b) — Sonnet pre-discovery agent (default Claude Code toolbelt + audit MCP server).** `stages.py:stage_1_brief_sonnet` opens ONE `ClaudeSDKClient` (model=sonnet) with `tools={"type":"preset","preset":"claude_code"}` (full Claude Code toolbelt — WebFetch, WebSearch, Task, Bash, Read, Write, Grep, Glob) **plus** `mcp_servers={"audit": register_audit_tools(state)}` + `allowed_tools=["mcp__audit__*"]` — exposing the 6 cache-backed audit tools as `mcp__audit__backlinks`, `mcp__audit__on_page`, `mcp__audit__ai_visibility`, etc. System prompt (`prompts/predischarge.md`) briefs agent with: (a) the warm-cache manifest (tool_name + hash → path on disk, so agent reads cache directly via Read or via tool handlers which transparently cache-hit); (b) firmographic signals from intake form; (c) **explicit URL-pattern blocks** for all free public-API signals the agent may reach — GitHub (`api.github.com/orgs/{org}` with Bearer $GITHUB_TOKEN + User-Agent `GoFreddy-Audit`), Wikipedia (`en.wikipedia.org/api/rest_v1/page/summary/{brand_slug}` + Lift Wing `api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict`), Reddit (`reddit.com/api/v1/access_token` OAuth with $REDDIT_CLIENT_ID/SECRET → then `reddit.com/r/<sub>/about.json`), SEC EDGAR (`data.sec.gov/...` + User-Agent with contact email required), HuggingFace (`huggingface.co/api/{org}` + optional $HUGGINGFACE_TOKEN), Product Hunt GraphQL (`api.producthunt.com/v2/api/graphql` OAuth client-credentials), crt.sh (`crt.sh/?q=%25.{domain}&output=json` with 1-req/sec polite pace), Mailinator (`api.mailinator.com/api/v2/domains/private` with $MAILINATOR_API_TOKEN if set), GDELT, Discord Invite API, Podchaser GraphQL, APIs.guru, Atlassian Marketplace, Firefox AMO, Mozilla HTTP Observatory, npm registry + PyPI JSON — each with polite-pace notes + pagination patterns; (d) **rubric-oriented investigation guidance** ("to seed brief sections for brand-credibility, investigate founder LinkedIn, Wikipedia article if present, industry-analyst position claims on brand site, Trust Center subdomain, press-page earned-media tier — decide depth per signal"); (e) explicit `gap_flag` instruction: "when data is absent or API blocked, emit a `{rubric, reason}` gap entry — do not skip silently"; (f) `fetch_with_retry` usage pattern (`cli/scripts/fetch_api.sh` shell wrapper — curl with exponential backoff, auth injection, pagination follow, User-Agent header — ~30 LOC). Agent explores adaptively, chasing anomalies, firing tool handlers that cache-hit instead of re-paying DataForSEO. Writes `signals.md` (prose notes, organized by rubric headings) + `gaps.jsonl` (one row per gap_flag with rubric + reason). Agent runs under `max_turns=600` sentinel (5-10× expected 30-90 turns), `permission_mode="bypassPermissions"`, `enable_file_checkpointing=True`, session_id persisted via `state.record_session("stage_1_brief_sonnet", result)`. Cost typical $2-6, wall-clock 6-12min. Hooks: observability only (PostToolUse loop-detect + token-spend alert + telemetry, PreCompact archive, Stop flush).
- **Stage 1 (c) — Opus brief synthesis.** `stages.py:stage_1_brief_opus` runs ONE Opus call (`prompts/predischarge_synthesis.md` — unchanged structural role) against `signals.md` + `gaps.jsonl` + cache manifest + form data. Outputs structured `PrediscoveryBrief` (Pydantic envelope): ICP hypothesis with confidence label, inferred competitor list (reconciled from intake form + backlinks overlap + Foreplay/Adyntel shared ad-category competitors), pain points, tech posture summary, AI-visibility headline, hypotheses to validate on walkthrough. Writes `brief.md` (prose for Stage-2 agent consumption) + `brief.json` (structured). Cost ~$0.50-1. session_id persisted via `state.record_session("stage_1_brief_opus", result)`.

Stage 0 also loads any conditional enrichments present (GSC / ESP / Ad / Survey / Assets / Demo / Budget / CRM / WinLoss per R18–R26) from `clients/<slug>/audit/enrichments/` and surfaces them to downstream stages.

**Stage 1 design rationale:** a single Sonnet pre-discovery agent reading the warm cache + exploring free public APIs via WebFetch covers the full signal surface with simpler shape than a primitive-registry-driven discovery layer; same rubric discipline through prompt instructions; reproducibility via cache fixtures + explicit gap_flag entries. The 3 safety-bounded primitives (`audit_welcome_email_signup`, `audit_hiring_funnel_ux`, attach-demo) run as scoped sub-sessions invoked from U2/U8 — never from this Stage 1 brief agent — with capability restriction + orchestrator pre-conditions in `scoped_tools.py`.

**Files:**
- Create `src/audit/stages.py` with `stage_0_intake(state)`, `stage_1_warmup(state)`, `stage_1_brief_sonnet(state)`, `stage_1_brief_opus(state)` functions
- Create `src/audit/prompts.py`, thin loader only (~30 LOC). `load_prompt(name: str, **vars) -> str` reads `src/audit/prompts/{name}.md` and applies format-string substitution for template variables. No prompt prose in Python.
- Create `src/audit/prompts/predischarge.md` (Stage 1 Sonnet system prompt — rubric-oriented investigation + pointer to `reference/fetch-api-patterns.md` + gap_flag instruction + fetch_with_retry usage) + `src/audit/prompts/predischarge_synthesis.md` (Stage 1 Opus, unchanged structural role).
- Create `cli/scripts/fetch_api.sh` — ~30 LOC shell helper: curl with exponential backoff (3 retries, 2s → 4s → 8s), auth-header injection from env, User-Agent header, pagination follow-link handling. Used by Sonnet pre-discovery agent and Stage-2 agents for any free-public-API call.
- Test: `tests/audit/test_stages_0_1.py` + `tests/audit/test_stage_1_brief.py`

**Approach:**
- `stage_0_intake`: reads intake form data from `audit_pending` row (populated by Unit 7), writes `clients/<slug>/audit/intake/form.json` + `clients/<slug>/config.json` (prospect Client model). No LLM.
- `stage_1_warmup`: opens shared `RenderedFetcher` context; fires direct provider-method calls (DataForSEO/Cloro/monitoring) in parallel via `asyncio.gather` + `Semaphore(12)`, all routed through `tools/cached_tool.py:cache_or_call` so writes match what MCP-served agent calls would produce. Invokes the existing `freddy` CLI subprocesses (see list below) alongside for their specific payloads. Runs `fingerprint_martech_stack()` local helper synchronously. All outputs write to `clients/<slug>/audit/cache/<tool>_<hash>.json` via `tools/cache.py:write_cache`.
- `stage_1_brief_sonnet`: as described above — Sonnet agent with full toolbelt + cache-backed tools + prompt-mentioned URL patterns for free APIs.
- `stage_1_brief_opus`: existing `brief.py` pattern; Opus synthesis call over signals.md + gaps.jsonl → brief.md + brief.json.
- Existing `freddy` CLI subprocesses invoked from Stage 1a cache warmup (verified against actual code — descriptions reflect what each command actually returns):
     - `freddy sitemap <url>` → up to 100 URLs with `{url, lastmod, priority}`. Feeds page-corpus seed for Sonnet agent's investigation.
     - `freddy scrape <url>` → fetches one page, returns text + word count. Used for homepage hero text extraction.
     - `freddy detect <url> --full` → per-URL DataForSEO technical audit + PageSpeed Core Web Vitals for the homepage. Complementary to the dataforseo_tool.on_page tool for richer single-page detail.
     - `freddy audit seo <domain>` → **thin: DataForSEO domain rank snapshot.** Keep for rank snapshot.
     - `freddy audit competitive <domain>` → competitor AD data (Foreplay + Adyntel). Paid-media intel; competitive_tool wraps CompetitiveAdService for runtime access but this CLI is invoked for its side effect of populating the competitor brand-name list.
     - `freddy audit monitor "<brand>"` → recent brand mentions via Xpoz. Also covered by monitoring_tool.voc at runtime; this CLI populates the initial brand-name sweep cache.
     - `freddy visibility` subprocess **NOT invoked** — `cloro_tool.ai_visibility` supersedes.
     Each cache write keys by tool+args hash so re-invoking the tool at Stage 2 is a cache hit.
- Competitor discovery happens inside the Sonnet pre-discovery agent: it merges (a) prospect-provided competitors from intake form, (b) top-SERP overlap from backlinks cache, (c) shared ad-category competitors from Foreplay/Adyntel cache. Agent reconciles into a final ranked list of 3–5 competitors written to `signals.md:competitors`. Opus synthesis validates the list.
- Concurrency: Stage 1a uses `asyncio.Semaphore(12)` across cache-warmup tool calls + 6 `freddy` CLI subprocesses. Stage 1b is a single Sonnet session. Stage 1c is one Opus call.
- **No registry, no `primitive_registry.yaml`, no `agent_discovery_log.jsonl`.** Dependency graph is implicit: warm cache precedes Sonnet pre-discovery; Sonnet reads what's there and uses fetch_with_retry / cache-backed tools for anything else.
- Telemetry: per-tool-call cost/duration rows appended to `cost_log.jsonl`; Sonnet agent's transcript archived by PreCompact hook; `gaps.jsonl` captures every explicit gap the agent flagged (reproducibility substrate).

**Test scenarios:**
- Happy: intake form with URL → Stage 0 writes valid config.json + form.json.
- Happy: Stage 1 warmup fires conditional tool set (B2B-SaaS prospect triggers different set than local-business prospect) and writes `cache/*.json` under 2 min.
- Happy: Sonnet pre-discovery agent on a known prospect reads cache, WebFetches ~8-15 free public APIs per URL patterns in prompt, produces `signals.md` organized by rubric headings + `gaps.jsonl` with explicit gap_flags for any unreachable sources.
- Happy: Opus brief synthesis on full signals.md + gaps.jsonl produces brief.md covering ICP hypothesis + competitor list + pain points + tech posture + AI-visibility headline.
- Edge: cache warmup tool failure (e.g., Cloro throttled, DataForSEO 503) → `cache/<tool>_<hash>.json` contains `{"error": "...", "ts": ...}`; Sonnet agent reads error, retries via tool handler (with `force=True`), falls back to gap_flag if still broken.
- Edge: 10+ of the ~8-15 free-API calls fail (rate-limit / auth / pagination) → agent emits gap_flag per rubric affected; Opus brief flags partials in narrative and proceeds.
- Edge: Sonnet agent rabbit-holes → `max_turns=600` sentinel fires → Slack alert → JR reviews transcript. Also: PostToolUse token-spend alert (3× median) fires earlier, giving JR heads-up before sentinel.
- Edge: free-API auth env var missing ($GITHUB_TOKEN unset) → agent emits `gap_flag: "GITHUB_TOKEN not configured — oss_footprint unavailable"`; continues.
- Safety: Tier-D primitives (welcome_email_signup, hiring_funnel_ux, attach-demo) are NOT invoked during Stage 1 pre-discovery — they run as scoped sub-sessions triggered out-of-band: `welcome_email_signup` and `hiring_funnel_ux` are invoked by the Conversion-Lifecycle / Brand-Narrative Stage-2 agents only when (a) the relevant trigger primitive (PLG motion detected for welcome_email; ATS detected for hiring_funnel) AND (b) the matching opt-in flag (`state.welcome_email_signup.opted_in == True` for welcome-email; always-on for hiring_funnel since observation-only) hold. `attach-demo` is triggered exclusively by the `freddy audit attach-demo` CLI subcommand (U8) — never auto-invoked by an agent. All three sessions use the three-layer capability-restriction config from `scoped_tools.py` (permission_mode="default" + disallowed_tools + scoped MCP server).
- Integration: `brief.json` validates against `PrediscoveryBrief` Pydantic schema; `cost_log.jsonl` has rows for warmup tool calls + Sonnet session events + Opus synthesis call; `gaps.jsonl` has one row per agent-flagged gap.

**Done when:** Running `freddy audit run --client <dogfood-prospect> --stage 1` produces a `brief.md` that JR reads and finds non-trivially useful without manual editing, AND `gaps.jsonl` records the agent's reasoning about what it could not reach (so quality-loss risks are explicit rather than silent).

---

### U4. Stage 2: parallel multi-agent analysis (7 agents → 9 report sections)

**Goal:** 7 Claude Agent SDK sessions (Sonnet) run in parallel via `asyncio.gather` with a `Semaphore(7)`, each producing a canonical `AgentOutput` with structured findings tagged by `report_section: Literal[...]` enum + a `rubric_coverage: dict[rubric_id, "covered"|"gap_flagged"]` map enforcing no-silent-skips. Agent count (7) and report count (9) decoupled deliberately — SEO+GEO produced by Findability agent; Conversion+Lifecycle produced by one funnel agent. Each agent attaches the audit MCP server (`mcp_servers={"audit": register_audit_tools(state)}`) on top of the Claude Code preset toolbelt; under `permission_mode="bypassPermissions"` both surfaces are reachable without further `allowed_tools=` enumeration. Runs the evaluator-optimizer critique loop (≤3 iterations).

**The 7 agents → 9 report-section mapping:**

| Agent | Report sections it produces | Why merged |
|---|---|---|
| **A. Findability** | SEO + GEO | Shared EEAT, robots, schema, content-authority signals; AI search is part of findability |
| **B. Brand/Narrative** | Brand/Narrative | Unchanged (~20 primitives — splitting Credibility from Narrative loses cross-cut coherence) |
| **C. Conversion-Lifecycle** | Conversion + Lifecycle | Unified funnel (visit→capture→convert→retain); shared `capture_surface_scan`, `audit_trust_signals`, martech-stack-slice signals |
| **D. Distribution** | Distribution | Unchanged (cohesive paid + organic + podcast + platforms) |
| **E. MarTech-Attribution** | MarTech-Attribution | Unchanged (specialized stack/attribution work) |
| **F. Monitoring** | Monitoring | Unchanged (VoC corpus = different data shape; pattern-clustering specialist work) |
| **G. Competitive** | Competitive | Unchanged (head-to-head competitor data fetching + comparison; not just synthesis) |

Each agent reads `brief.md` + `cache/*.json` (the warm cache from Stage 1 — any cache-backed tool call is a free cache-hit during Stage 2) and outputs `Finding[]` tagged with `report_section: Literal[...]` enum. Stage 3 synthesis groups findings by `report_section` directly — no pivot table.

**Files:**
- Create `src/audit/stages.py:stage_2_agents` function (runs all 7 agents via `asyncio.gather` + `Semaphore(7)` — each agent is an `async run_agent(agent_cfg)` call that executes: initial pass → self-critique pass → optional revision pass, capped at 3 iterations total)
- Create `src/audit/agent_models.py` — `Finding`, `AgentOutput` Pydantic models:
  - `Finding` required fields: `id`, `title`, `evidence_urls[]`, `recommendation`, `severity(0-3)`, `confidence(H/M/L)`. Optional: `evidence_quotes[]`, `reach(0-3)`, `feasibility(0-3)`, `effort_band(S/M/L)`, `category_tags[]`, `proposal_tier_mapping` (populated in Stage 3 after Stage 4 generates proposal tiers). **Required tagging field**: `report_section: Literal["seo","geo","competitive","monitoring","conversion","distribution","lifecycle","martech_attribution","brand_narrative"]` — the agent's declaration of which section the finding feeds; Pydantic rejects invalid values. The `recommendation` field is strategic, not tactical (unchanged from prior).
  - `AgentOutput` required field: `rubric_coverage: dict[str, Literal["covered","gap_flagged"]]` where keys are the rubric IDs for that agent's domain (drawn from the prompt's rubric checklist). Stage 3 validates that every rubric listed in the agent's prompt checklist appears as a key with a value of `covered` (≥1 finding produced) OR `gap_flagged` (explicit "insufficient signal" declaration) — a missing key is an invariant violation.
- Create 7 agent-specific prompts as markdown files under `src/audit/prompts/`: `agent_findability.md`, `agent_brand_narrative.md`, `agent_conversion_lifecycle.md`, `agent_distribution.md`, `agent_martech_attribution.md`, `agent_monitoring.md`, `agent_competitive.md`. Prompts are prose markdown loaded via `prompts.load_prompt()`, not Python string constants. Each prompt carries (a) explicit rubric-coverage checklist — 5-10 rubrics this agent must cover with evaluation-question + expected-finding-shape + report_section mapping; (b) **pointer to shared `prompts/reference/fetch-api-patterns.md`** for per-API auth/rate-limit/pagination guidance; (c) short critique-loop instruction: "after findings, self-critique; reject tactical recommendations, weak evidence, <50-word substance; revise once; ≤3 iterations" (fuller template in shared `prompts/agent_critique.md`); (d) output contract — AgentOutput shape + rubric_coverage map; (e) gap_flag instruction. Each prompt injects `brief.md` + cache manifest + matching `src/audit/references/<agent>-references.md` at runtime.
- Create `src/audit/prompts/reference/fetch-api-patterns.md` — shared reference doc listing per-API auth env vars + polite-pace rules + pagination patterns for GitHub, SEC EDGAR, Reddit OAuth, Wikipedia, HuggingFace, Product Hunt, crt.sh, SerpAPI, etc. All 7 agent prompts + Stage-1 pre-discovery prompt reference this one file instead of duplicating blocks.
- Create `src/audit/prompts/agent_critique.md` — single shared critique-loop template covering both critique and revision phases (loaded with `phase=<critique|revision>` format variable). Used by every Stage-2 agent.
- Create `src/audit/agent_runner.py` — small orchestrator implementing the critique loop: `async def run_agent(agent_cfg) -> AgentOutput`. Pseudocode: `output = sonnet_call(initial_prompt); critique = sonnet_call(critique_prompt, context=output); if critique.passes: return output; else: output = sonnet_call(revision_prompt, context=output + critique); [repeat up to 3]`. Telemetry records `critique_iterations_used` per agent.
- Create `src/audit/references/` directory with 9 consolidated reference files:
  - Existing 4 (renamed for consistency): `stats-library.md`, `competitive-agent-references.md`, `monitoring-agent-references.md`, `voc-source-playbooks.md`
  - **2 cross-agent merged**: `findability-agent-references.md` (SEO + GEO content) and `conversion-lifecycle-agent-references.md` (Conversion + Lifecycle content). Detailed file purposes in the References consolidation section.
  - **3 for full-agency lenses (renamed)**: `distribution-agent-references.md` (paid-creative teardown framework, hook taxonomy, offer patterns, UGC-vs-produced, channel-native-fit, podcast-presence interpretation, YouTube upload-cadence benchmarks, influencer-tier tagging patterns, **ASO grading rubric** when mobile-app detected), `martech-attribution-agent-references.md` (Consent Mode v2 interpretation, server-side tagging maturity tiers, UTM-taxonomy scoring rubric, CDP/ESP/CRM category definitions, accessibility-overlay red-flag context, dormant-pixel bloat thresholds), `brand-narrative-agent-references.md` (April Dunford 5-component positioning rubric, cross-surface coherence-scoring framework, pub-tier classification model — Tier-1 flagship / Tier-2 trade / Tier-3 syndicate, GDELT tone-reading heuristics, content-pillar cluster-balance thresholds, proprietary-research publishing benchmarks, editorial-cadence stability bands, conference-tier list per vertical, community-presence member-count tier interpretation, Wikipedia-presence reference-quality rubric, **client-asset-enrichment interpretation** when R22 fires — cross-asset consistency scoring)
- Test: `tests/audit/test_stage_2_agents.py`

**Rubric coverage discipline:**

Source-of-truth for each agent's rubric checklist is `src/audit/data/rubrics_<agent>.yaml` — each entry: `{id, evaluation_question, expected_finding_shape, report_section}`. The agent prompt template loads from this YAML at render time (via `prompts.load_prompt("agent_findability", rubrics=load_yaml("data/rubrics_findability.yaml"))`) and substitutes the rubric block into the prompt — so the prompt the agent sees and the validator's expectations are always in sync. Routing happens via the `Finding.report_section: Literal[...]` enum each agent tags + the optional `Finding.addresses_rubrics: list[str]`; Stage 3 validates both rubric coverage (every YAML rubric ID must appear as `covered` or `gap_flagged` in `AgentOutput.rubric_coverage`) AND report_section routing (every addressed rubric's declared `report_section` must match the finding's tagged section). Example slice of the Findability agent's rubric checklist (rendered into `prompts/agent_findability.md` from `data/rubrics_findability.yaml`):

```
Rubrics you MUST cover (emit ≥1 Finding per rubric OR mark `gap_flagged` in rubric_coverage):
- tech_seo_health                 → report_section="seo"   — Is the site technically healthy for crawlers? Look at on-page, internal-linking, content quality, page-speed, schema, robots strategic posture, crawl-budget bloat, error-page UX, schema-vs-competitor.
- link_authority                  → report_section="seo"   — Does the site have earned authority? Examine backlinks cache + branded-vs-commercial anchor-text distribution.
- ai_search_visibility            → report_section="geo"   — Is the brand cited in AI search; citation-supply trajectory? cloro_tool + robots_strategic posture + EEAT author-entity composite + HuggingFace downloads (when AI firmographic) + OSS footprint correlation.
- international_local_accessibility → report_section="seo" — Hreflang + GBP + NAP + WCAG when applicable.
... [~6-10 rubrics per agent, inline]

When you've produced findings, populate rubric_coverage with {rubric_id: "covered" | "gap_flagged"} for every rubric above.
```

Per-section health score is produced by Opus in Stage 3 with rationale (no weighted rollup).

**Approach:**
- `Finding` schema (6 required + report_section enum): **Required**: `{id, title, evidence_urls[], recommendation, severity(0-3), confidence(H/M/L), report_section: Literal["seo","geo","competitive","monitoring","conversion","distribution","lifecycle","martech_attribution","brand_narrative"]}`. **Optional**: `{evidence_quotes[], reach(0-3), feasibility(0-3), effort_band(S/M/L), category_tags[], proposal_tier_mapping, agent, addresses_rubrics: list[str]}`. `addresses_rubrics` is the rubric IDs from the agent's `rubrics_<agent>.yaml` that this finding addresses — Stage 3 cross-validates that every addressed rubric's declared `report_section` matches the finding's tagged `report_section` (raises `ReportSectionMismatch` on drift). Pydantic rejects invalid `report_section` values — routing is deterministic. Agent fills any count of Findings freely. **The `recommendation` field is strategic, not tactical** — it states *what would solve this* in terms the engagement delivers, not a DIY execution guide. Example (good): *"Enterprise landing pages lack schema coverage, suppressing rich-result eligibility for 8 of 10 tracked enterprise queries."* Example (bad — too tactical): *"Add Organization, Product, and FAQ schema with these JSON-LD snippets to /enterprise/."* Tactical execution detail is engagement work, not audit output. `proposal_tier_mapping` populated in Stage 3 synthesis once proposal is generated in Stage 4 — see U5.
- `AgentOutput` (R5 shape): `{agent_name, findings[], agent_summary, rubric_coverage: dict[str, Literal["covered","gap_flagged"]], critique_iterations_used: int, metadata{session_id, total_cost_usd, duration_ms, num_turns, model_usage, partial}}`. `rubric_coverage` is required — missing keys = invariant violation at Stage 3. `critique_iterations_used` records how many critique-loop iterations ran (1 if first pass passed self-critique; up to 3).
- Each Stage-2 agent: open `ClaudeSDKClient` with a **directive** `system_prompt` (role / objective / context / rubric-checklist / per-API auth blocks / fetch_with_retry usage / critique-loop instructions / output contract / termination). Inject `brief.md` + cache manifest + matching `src/audit/references/<agent>-references.md`. Agent decides depth per rubric using tool discretion. **Config** (verified against Claude Agent SDK shape — not a single `tools=` list concatenation, which would be a TypeError): `ClaudeAgentOptions(tools={"type":"preset","preset":"claude_code"}, mcp_servers={"audit": register_audit_tools(state)}, permission_mode="bypassPermissions", enable_file_checkpointing=True, max_turns=500, model="claude-sonnet-4-6")`. The preset grants the full Claude Code toolbelt (WebFetch, WebSearch, Task, Bash, Read/Write/Grep/Glob); the audit MCP server adds `mcp__audit__backlinks`, `mcp__audit__on_page`, `mcp__audit__ai_visibility`, `mcp__audit__voc`, `mcp__audit__press`, `mcp__audit__podcasts` (+ `mcp__audit__gsc_search_analytics` when `state.enrichments.gsc.attached`). Both surfaces are reachable under `bypassPermissions` without further `allowed_tools=` enumeration. Cache-backed tools are cache-hits during Stage 2 for anything Stage 1 warmed; agent pays for drill-down calls only. (Sentinel rationale: `max_turns=500` is 5-10× expected normal max of 15-60 turns, merged agents up to 25-90.)
- **Critique loop** (`agent_runner.run_agent`): initial pass produces Findings + rubric_coverage → same-agent self-critique pass re-reads the output with the critique prompt ("reject findings with tactical recommendations, weak evidence, severity/confidence mismatched to evidence, <50-word substance; verify every rubric is `covered` or `gap_flagged`") → if critique passes, ship; if critique flags issues, one revision pass, then ship (passes or not). Max 3 agent-model calls per agent session (initial + critique + revision). `critique_iterations_used` logged.
- Hooks wired per agent: `PostToolUse` → loop-detection (hash `(tool_name, tool_input)`; Slack-alert on 5× consecutive, no abort) + telemetry + **per-agent token-spend alert (3× rolling median → Slack)**; `PreCompact` → archive full transcript to `clients/<slug>/audit/agents/<agent>/transcripts/`; `Stop` → flush `ResultMessage` telemetry to `cost_log.jsonl` and record `session_id` via `state.record_session`.
**Per-report-section content (which agent produces each section):** The narratives below describe what each of the 9 report sections covers. Per the agent → section mapping above: SEO + GEO sections are produced by **Agent A (Findability)**; Conversion + Lifecycle sections by **Agent C (Conversion-Lifecycle)**; the remaining 5 sections (Brand/Narrative, Distribution, MarTech-Attribution, Monitoring, Competitive) are each produced by their dedicated agent. Cross-cut signals (e.g. `audit_eeat_signals`, `audit_trust_signals`, `audit_oss_footprint`) are investigated by multiple agents (each pulls what it needs from `brief.md` + `cache/` + WebFetch); findings surface tagged with `Finding.report_section` enum per R5 routing.

- **Monitoring section** (produced by Agent F — Monitoring) consumes the full VoC corpus from `gather_voc` (10 owned adapters — see Data provider inventory) plus trend context from `GoogleTrendsAdapter` (breakout detection, related queries) and press narrative from `NewsDataAdapter` (`source_priority`, `ai_tags`). Findings surface: mention velocity trends, sentiment drift by platform, pain-point and praise clusters with direct `RawMention` URL citations, share-of-voice on high-interest queries, press-tier distribution (Tier-1 flagship vs Tier-3 syndicated-aggregator), podcast presence signal (owned vs guest appearances derived from Pod Engine show_name frequency + `is_ad_segment` filter), community footprint (subreddit presence from Xpoz), brand defensive perimeter (branded SERP + autosuggest + Reddit AMA). Does NOT duplicate Distribution section's structural-presence audit — Monitoring is the *narrative* layer ("what are people saying and where"), Distribution is the *footprint* layer ("do you have a handle there and how active is it").
- **Distribution lens** (new, full-agency coverage) consumes: (a) `CompetitiveAdService`-normalized Foreplay + Adyntel paid-ad corpus with `persona` / `emotional_drivers` / `creative_targeting` / `transcription` fields; (b) `audit_channel_presence` organic-social scorecard across 7 platforms; (c) `audit_youtube_channel` YouTube footprint; (d) `audit_podcast_footprint` owned + guest + sponsorship presence; (e) `NewsDataAdapter` press / earned-media corpus with `source_priority` tier classification. Lens findings surface: **paid-media creative strategy** (hook taxonomy, offer patterns, UGC-vs-produced ratio, landing-page congruence with ad promise, channel-native-fit, spend-intensity signal from ad volume + run duration); **organic footprint maturity** (present-or-absent × cadence × engagement-rate vs category benchmark); **video strategy** (upload cadence, shorts-vs-long ratio, dormancy); **podcast posture** (owned-show existence, exec guest appearances in trade-relevant shows); **earned-media tier distribution** (Tier-1 flagship vs Tier-3 syndicate). Does NOT re-litigate backlink / keyword / technical signals — those belong to SEO lens. Does NOT re-litigate sentiment — that belongs to Monitoring lens. Distribution is specifically the **channel + creative + cadence** layer.
- **Lifecycle lens** (new, full-agency coverage — MVP scope, flow-observation deferred) consumes: (a) `capture_surface_scan` popup + form + SMS-capture + lead-magnet data; (b) `fingerprint_martech_stack` lifecycle-slice (ESP / SMS / loyalty / reviews / referral / subscription vendor inventory); (c) `deliverability_posture` DNS hygiene (SPF / DKIM / DMARC / BIMI / MTA-STS). Lens findings surface: **capture-UX maturity** (popup timing + incentive vs Klaviyo benchmarks; exit-intent present; SMS 2-step opt-in TCPA-compliant; preference-center-at-signup); **lifecycle-stack sophistication tier** (derived from P25 — none / basic / ESP+SMS / full-lifecycle); **deliverability posture** (DMARC policy band, SPF-lookup-count health, BIMI + VMC presence); **retention-surface presence** (loyalty / referral / subscribe-and-save pages, reviews density on PDPs). Explicit scope caveat in every Lifecycle finding: "this audit cannot observe open/click/conversion rates without ESP access; those metrics are engagement-scope." **Flow observation** (welcome / cart / winback) is deferred to an optional 2-week supplemental report — too slow for the 3-day SLA — and is sold as an add-on at walkthrough-call time.
- **MarTech-Attribution lens** (new, full-agency coverage) consumes: (a) `fingerprint_martech_stack` full vendor inventory across 20+ categories; (b) `assess_attribution_maturity` derived signals (server-side tagging tier, Consent Mode v2, UTM discipline, tool overlap, dormant pixels); (c) `analyze_internal_links` page corpus for UTM-taxonomy mining; (d) `scrape_careers` mentions of dbt / Snowflake / Fivetran / Hightouch (CDP-warehouse-signal proxy). Lens findings surface: **stack completeness vs ICP** (a B2B prospect without a CRM form vendor is a red flag; a B2C prospect without loyalty / reviews vendors is a red flag); **attribution loop integrity** (client-side only vs server-side vs first-party-ID vs full closed-loop); **privacy + compliance posture** (CMP present; jurisdictional coverage gaps; DNT/GPC handling; dormant-pixel PII leak risk); **tool overlap / bloat** (multiple heatmapping / multiple chat / multiple scheduler = cleanup opportunity); **accessibility-overlay red flag** (AccessiBe / UserWay present = ADA-lawsuit-magnet flag). This is the lens agencies charge $15K standalone for — it's the single highest-leverage addition.
- **Brand/Narrative lens** (new, Option C full-agency coverage + 2026-04-22 expansion) consumes: (a) `audit_messaging_consistency` per-surface positioning rubric + coherence score + tagline evolution **+ copy-quality scoring (readability, jargon density, headline strength, voice consistency)**; (b) `audit_executive_visibility` per-exec thought-leadership output (bylines, podcast guesting, speaking, press quotes, Wikipedia) **+ founder-led weighting when employee_count<50**; (c) `audit_content_strategy_shape` pillar count + balance + proprietary research + editorial cadence + persona mapping **+ newsletter subscribers + glossary marketing depth**; (d) `audit_earned_media_footprint` tier-classified press + narrative themes + competitor SOV **+ Wikipedia depth via Lift Wing reference-quality scoring + article quality class (FA/GA/B/C/Start/Stub)**; (e) `audit_partnership_event_community_footprint` integrations + customer logos + conference sponsorships + owned events + Discord/subreddit/Slack/Circle/Skool community presence + affiliate-program detection **+ press kit + status page + owned webinar series**; (f) **`audit_customer_education`** academy/university/certifications/LMS-platform; (g) **`audit_public_roadmap`** Canny/Productboard/Featurebase + transparency score; (h) **`audit_corporate_responsibility`** ESG/sustainability/B-Corp/diversity/accessibility-statement (when mid-market+); (i) **`audit_customer_story_program`** case-study count + outcome quantification + video case studies + G2/Capterra review velocity; (j) **`scrape_careers` employer-brand layer** (Glassdoor when Tier-2, Indeed, Comparably culture dimensions, pay-transparency compliance — anchor finding for CA/NY/CO/WA jurisdictional violations); (k) optional enrichment from R22 client-asset upload + **R26 attach-winloss themes**. Lens findings surface: **positioning coherence**, **copy-quality vs vertical norms**, **thought-leadership index** (with founder-mode weighting for early-stage), **content-strategy maturity**, **newsletter/glossary asset class signals**, **earned-media tier gap + Wikipedia depth**, **ecosystem presence map** (community + partnerships + events + customer education + public roadmap + ESG signals), **customer story program quality** (hard-outcome quantification ratio), **employer brand + pay-transparency compliance exposure**, **brand-asset consistency** (when R22 fires), **win-loss themes** (when R26 fires). Does NOT re-litigate SEO content quality (that's SEO lens) or sentiment (Monitoring lens) or paid creative strategy (Distribution lens). Brand/Narrative is the **narrative + positioning + strategic layer** that differentiates a full-service agency audit from a channel-specific audit.

- **Conversion lens** consumes (additions from 2026-04-22 expansion): existing capture_surface_scan/martech-stack/page-CRO inputs **plus** `audit_trust_signals` (badges, security certs, social proof density, CMP deployment quality, Mozilla HTTP Observatory headers grade) **plus** `audit_pricing_page` (tier structure, anchoring patterns, billing toggle, free trial signals, currency switcher + regional payment methods when multi-locale) **plus** `audit_funnel_content_shape` descriptive content/CTA portfolio analysis (severity-cap=low — never frames as velocity claim) **plus** `audit_abm_signals` (when B2B-enterprise: personalization vendors, reverse-IP, intent-data, named-account landing pages with templated detection) **plus** `audit_plg_motion` (when SaaS: pure_freemium / free_trial / reverse_trial / hybrid classification + viral mechanism scoring) **plus** `audit_devex` (when dev-tool: docs platform tier, OpenAPI discoverability, SDK coverage + freshness, quickstart quality) **plus** R23 attach-demo TTFV + onboarding-flow audit when granted **plus** R25 attach-crm pipeline velocity when granted. Lens findings surface: **trust signal density vs vertical**, **pricing-page anchoring effectiveness + localization gaps**, **content/CTA shape** (descriptive — pairs with R20 ad-platform + R25 CRM for true velocity), **ABM stack maturity tier** (none/basic/growing/enterprise), **PLG motion classification + benchmark gaps** (freemium 7% conv vs trial 10-25%), **devex modernity tier** (modern Mintlify/Stoplight vs legacy raw Swagger UI), **demo onboarding TTFV gaps** (when R23 fires), **funnel velocity vs SaaS benchmarks** (when R25 fires).

- **SEO lens** consumes (additions from 2026-04-22 expansion): existing technical/on-page/backlinks/keywords/page-speed inputs **plus** `audit_international_seo` hreflang reciprocity + locale URL strategy + geo-redirect indexability blocks (when multi-locale) **plus** `audit_local_seo` GBP completeness + NAP citation consistency + local-pack rankings + LocalBusiness schema (when local-business firmographic) **plus** `audit_accessibility` WCAG 2.1 AA via Lighthouse + axe-core **with overlay vendors flagged as NEGATIVE signal** (UserWay/AccessiBe/EqualWeb = ADA-litigation-magnet) **plus** `audit_help_center_docs` knowledge-base depth + Algolia DocSearch detection. Lens findings surface: **international-SEO gaps**, **local-SEO citation cleanup priority**, **WCAG critical+serious violations + ADA-overlay risk**, **help-center investment signal** (modern docs platform = engineering investment).

- **Distribution lens** consumes (additions from 2026-04-22 expansion): existing paid-media/organic-social/video/podcast/earned-media inputs **plus** `audit_directory_presence` G2/Capterra/AlternativeTo/Product Hunt/Chrome Web Store/AI directories **plus** `audit_marketplace_listings` Zapier/Slack/AppExchange/AWS/HubSpot/Atlassian/Shopify/Notion/Stripe **plus** `audit_launch_cadence` Product Hunt history + changelog cadence + waitlist mechanism + GitHub releases.atom **plus** `audit_free_tools` engineering-as-marketing surface (subdomain/path/extensions/SEO-driven tool pages/GitHub tool repos) **plus** `audit_oss_footprint` GitHub org maturity (when dev-tool/tech firmographic). Lens findings surface: **directory listing optimization opportunities**, **integration ecosystem reach**, **launch cadence + ship velocity narrative**, **engineering-as-marketing maturity** (tool-led / tools-as-funnel / no-surface), **OSS footprint health + AI-citation supply correlation** (high-star repos heavily indexed by AI search).

- **MarTech-Attribution lens** consumes: existing fingerprint_martech_stack + assess_attribution_maturity inputs **plus** R24 attach-budget when granted (channel mix vs Gartner 70/20/10 + MarTech % vs 22.4% baseline + paid-media % vs 30.6% baseline + per-channel deviation from vertical median, with bloat flag when MarTech spend high but `fingerprint_martech_stack` detected many tools) **plus** R25 attach-crm pipeline velocity formula when granted. Lens findings surface: **budget allocation gaps vs vertical benchmark + MarTech bloat opportunity** (when R24 fires), **pipeline velocity vs SaaS benchmarks + lead-source ROI ranking** (when R25 fires).

**Lens additions from the R2 coverage expansion (full per-primitive specs in `docs/plans/2026-04-22-003-audit-coverage-research-r2.md`):**

- **SEO lens (additions)**: `audit_eeat_signals` (author bios + Person schema + expertise indicators + YMYL classifier — Google #1 ranking factor since 2023); `audit_robots_strategic` (AI crawler controls — strategic GEO decision); `audit_crawl_budget_bloat` (index-bloat detection beyond orphan pages); `audit_conversational_query_optimization` (renamed from voice-search; FAQPage schema + question-format `<h2>` + AI-conversational query pattern); footer optimization sub of `audit_on_page_seo`; documentation translations sub of `audit_help_center_docs`; backlink anchor-text branded-vs-commercial sub of `analyze_backlinks`; `audit_schema_competitive` reasoning (vs top 3 competitors); `audit_error_page_ux` (custom 404/500 + WAF safety pattern). **Lens findings surface**: EEAT readiness for content-heavy prospects, AI crawler strategic posture (allow vs block as future-citation-supply decision), index-bloat cleanup priority, schema gap vs competitors.

- **GEO lens (additions)**: `audit_robots_strategic` (AI crawler controls directly affect future AI-search citations); `audit_eeat_signals` cross-link (author entities improve AI citation likelihood); `audit_huggingface_presence` for AI prospects (HF model downloads correlate with AI-search citation supply). **Lens findings surface**: AI-citation-supply trajectory (growing/flat/declining based on robots.txt + EEAT + HF presence + OSS footprint composite).

- **Brand/Narrative lens (additions)**: `audit_branded_serp` (Knowledge Panel + sitelinks + reviews stars + AI Overview + PAA defensive perimeter); `audit_branded_autosuggest` (Google autosuggest mining for `is X scam?` / `X reviews` / `X alternatives`); `audit_industry_analyst_position` (**single largest remaining B2B SaaS finding** — Gartner MQ Leader drives 30-50% enterprise close rate); `audit_clv_retention_signals` (NPS / retention-rate / GRR/NRR public claims); `audit_ai_policy` (`/responsible-ai` + `/ai-ethics`); `audit_sustainability_carbon` (Website Carbon + Green Web Foundation); `audit_reddit_ama_brand_subreddit`; `audit_customer_advisory_board_references` (B2B); `audit_university_academic_partnerships` (research-heavy/dev-tool/edtech); `audit_geographic_expansion`; `audit_public_company_ir` (public-company); `audit_hiring_funnel_ux` (employer brand via ATS-questions schema); plus 9 deepening extensions: newsletter quality + research depth + leaderboard rank subs of `audit_content_strategy_shape`; owned-podcast quality sub of `audit_podcast_footprint`; rebrand history Wayback + brand voice cross-platform subs of `audit_messaging_consistency`; wire-vs-original press ratio + M&A history subs of `audit_earned_media_footprint`; status page maturity + comments engagement + branded merchandise/swag subs of `audit_partnership_event_community_footprint`; brand demand trend sub of `gather_voc`. **Lens findings surface**: brand defensive-perimeter health, analyst-position tier (Leader/Challenger/Niche/Visionary), retention/CLV signal density, AI-policy maturity, customer-listening program presence (CAB), employer-brand + pay-transparency exposure, public-company IR maturity for public prospects, comprehensive narrative coherence.

- **Conversion lens (additions)**: `audit_customer_support` (live chat deployment quality + multilingual + AI chatbot on-brand + escalation paths); `audit_cro_experimentation_maturity` (cookie-pattern + URL-param + Wayback variant rotation cadence); `audit_ecommerce_catalog` (DTC/e-comm: per-SKU + Product schema + recommendations engine + guest-checkout); `audit_b2c_personalization` (B2C: Dynamic Yield/Adobe Target/VWO Personalize/Insider/Bloomreach/Movable Ink); `audit_homepage_demo_video` (Wistia/Vimeo/Loom/YouTube embed + view counts + transcripts); `audit_first_party_data_strategy` (quizzes/configurators/surveys + CDP activation); `audit_trust_center` (SafeBase/Vanta/Drata/Whistic/Conveyor — cuts enterprise sales cycle 30-60 days); `audit_mobile_ux` (touch targets + viewport + mobile checkout flow); `audit_paywall_upgrade_cro` (freemium upgrade-CTA placement + urgency/scarcity copy); `audit_eeat_signals` cross-cut (author trust); plus deepening extensions: push notification opt-in sub of `capture_surface_scan` (OneSignal/Pushwoosh/Pusher/VWO Engage); cross-sell/upsell sub on product+pricing pages. **Lens findings surface**: support-deployment quality vs vertical, experimentation cadence (0 vs 50 tests/month), e-commerce catalog completeness, B2C personalization tier, demo video conversion lever, first-party data maturity, Trust Center procurement-readiness, mobile UX touch-target compliance, paywall-upgrade friction.

- **Distribution lens (additions)**: `audit_mobile_app_linking` (smart app banner + universal links + branch.io + flag dead Firebase Dynamic Links); `audit_branded_merchandise_swag`; `audit_hackathon_dev_event_sponsorships` (dev-tool); `audit_university_academic_partnerships` (cross-cut); `audit_ctv_ads_detection` (degraded — pointer to R20); `audit_apple_search_ads` (mobile + R20); `audit_geographic_expansion` (cross-cut); `audit_open_api_public_data_access` (RapidAPI/Postman/APIs.guru/Bump.sh + ProgrammableWeb dropped); `audit_github_discussions_volume` (community); `audit_huggingface_presence` (AI model distribution); `audit_influencer_ftc_compliance` (legal-exposure finding when influencer mentions detected). **Lens findings surface**: mobile-app deep-linking maturity (or broken-FDL active outage), swag-program signal, dev-event sponsorship footprint, public API distribution, GitHub Discussions community engagement, Hugging Face model-download distribution, influencer FTC compliance gaps.

- **MarTech-Attribution lens (additions)**: `audit_first_party_data_strategy` cross-cut (CDP activation maturity); `audit_email_signature_marketing_indicators` (MEDIUM-LOW confidence triangulation; emit only ≥2 weak signals); sub-processor / DPA disclosure sub of `audit_trust_signals` (B2B EU sales requirement); `audit_vertical_compliance` (HIPAA/PCI-DSS/FERPA/state-MTL/DMA/DSA/FDA/SOX/GLBA); `audit_ai_policy` cross-cut (AI governance + model-training opt-out). **Lens findings surface**: first-party data activation tier, email-signature marketing presence (when triangulated), GDPR sub-processor compliance gap, vertical compliance posture, AI-policy procurement readiness.

- **Synthesis layer additions**: `audit_sales_motion_classification` reasoning primitive composes pricing-transparency + sales-rep enumeration + "Talk to Sales" gating + outbound-tool detection → `motion_type ∈ {plg, inside_sales, enterprise_sales, hybrid_plg_to_sales, hybrid_smb_to_enterprise}`. **Informs entire engagement-scope conversation** — different motion = different engagement (PLG → activation/onboarding engagement; enterprise-sales → ABM engagement; hybrid → both). `audit_schema_competitive` reasoning compares prospect schema to top 3 competitors — synthesis-layer cheap win.
- Run 7 agents via `asyncio.gather(*[run_agent(a) for a in agents])` with `Semaphore(7)` (infra concurrency, not cognitive cap). Each session is an isolated SDK subprocess. If Claude Agent SDK parallel-session limits are hit at 7, fall back to `Semaphore(4)` and two waves (correctness preserved, wall-clock ~40% longer).
- **Agent G (Competitive) performs head-to-head comparison** using the final competitor list from Stage 1's Opus synthesis (`brief.json:competitors`). It re-invokes `dataforseo_tool.backlinks` + `dataforseo_tool.keyword_gaps` for each competitor domain (cache-backed — first competitor call pays, replays hit cache) and surfaces the following competitive insights in its narrative: (a) **linking gap** — which competitor domains have materially more referring domains / higher `dataforseo_rank`; (b) **link intersect** (Ahrefs flagship feature) — domains that link to 2+ competitors but NOT the prospect, computed as a set operation on the backlinks data already collected, ranked by domain authority; (c) **keyword gap** — top 100 keywords competitors rank for that prospect doesn't; (d) **SERP feature gap** — who owns featured snippets and AI Overview citations vs. prospect. It also consumes the ad-intel data from the `freddy audit competitive` subprocess (Foreplay + Adyntel via `CompetitiveAdService`) and folds it into the narrative as **paid-competitive posture**. The normalized ad shape exposes rich Foreplay fields — `persona`, `emotional_drivers`, `creative_targeting`, `market_target`, `product_category`, `running_duration`, `transcription`, `cards`. Competitive findings should surface **creative strategy patterns** (hook taxonomy, offer patterns, UGC-vs-produced ratio, landing-page congruence) — not just "competitor runs Meta ads." Agent D (Distribution) is the primary consumer of paid-intel corpus for narrative integration; Agent G focuses specifically on head-to-head comparison work. This is where competitor-comparison data is actually produced; Stage 1's `analyze_backlinks` + `keyword_gap_analysis` primitives deliberately produce prospect-only output because Stage 1 runs before `derive_competitors` resolves the final list.
- Each agent writes to `clients/<slug>/audit/agents/<agent>/{output.json, narrative.md}` (output.json contains `findings[]` tagged with `report_section` Literal enum + `rubric_coverage` map + `critique_iterations_used`; narrative.md is the agent's prose summary).
- On agent exception (not turn/budget — those don't exist): mark `AgentOutput.partial = True`, log to `state.sessions[<agent>].error`, pipeline continues. If ≥3 agents raise exceptions, orchestrator surfaces to JR (operational safety, not agent cap) rather than auto-publishing a broken audit. Crashed agents are resumable on a subsequent `freddy audit run --resume` via `resume=<session_id>`.

**Test scenarios:**
- Happy: all 7 agents complete with `ResultMessage.subtype=="success"` on a dogfood prospect; findings count logged to telemetry, not asserted.
- Happy: Findings validate against canonical envelope schema (including `report_section` Literal enum populated); count and severity distribution are agent judgment.
- Happy: each agent's `session_id` persisted to `state.sessions`; `PostToolUse` + `PreCompact` hooks fire and emit telemetry rows; `critique_iterations_used` logged per agent.
- Happy: **rubric_coverage completeness** — every rubric in each agent's prompt checklist appears in `AgentOutput.rubric_coverage` with a value of `covered` or `gap_flagged` (no silent skips). Integration test with a mocked agent output that omits a rubric must fail Stage 3 validation.
- Happy: cache-backed tool calls during Stage 2 return cache-hits for signals Stage 1 warmed (zero incremental DataForSEO/Cloro cost for those); drill-down calls pay normal price and append to cache.
- Edge: agent critique loop rejects initial findings (tactical recommendations or weak evidence) → revision pass emits stronger findings; `critique_iterations_used=2` logged. Integration test: feed a weak-findings fixture and verify revision fires.
- Edge: one agent's Claude API error → retried once → raised as partial; subsequent `freddy audit run --resume` picks up from `state.sessions[<agent>].session_id`.
- Edge: loop-detection hook observes 5× consecutive identical tool call → Slack alert fires + telemetry row written; agent run is NOT aborted.
- Edge: per-agent token-spend crosses 3× rolling median → Slack alert; agent continues (observation only, no abort).
- Edge: agent reports gap_flag for a rubric (e.g., "audit_industry_analyst_position: gap_flagged — no analyst claim detectable on brand site or SerpAPI") → rubric_coverage registers gap explicitly; Stage 3 surfaces to deliverable review.
- Edge: ToolError return from a cache-backed tool → agent retries once; if still error, emits a gap_flag Finding with error_diagnostics (not silent failure).
- Integration: Stage 2 telemetry logged per agent to `cost_log.jsonl` (total_cost_usd, duration_ms, num_turns, model_usage, critique_iterations_used). No cost assertion.

**Done when:** Stage 2 dogfood produces 36–72 ranked findings across 7 agents (routed to 9 report sections via `Finding.report_section` enum) with evidence citations traceable back to cache files or prospect URLs, AND every agent's `rubric_coverage` map is complete with explicit `covered` / `gap_flagged` for each rubric in its checklist.

---

### U5. Stage 3: synthesis (ported brief.py pattern — R6 merged into stages.py)

**Goal:** Adapt Freddy's `src/competitive/brief.py` async-fan-out-plus-Opus-synthesis pattern to produce ranked findings, 3–5 surprises, and the audit report body. Lives as `_synthesize_sections()` helper inside `stages.py`; no standalone `brief.py` module.

**Files:**
- Create `src/audit/stages.py:stage_3_synthesis` function + private `_synthesize_sections()` helper (ported from `/Users/jryszardnoszczyk/Documents/GitHub/freddy/src/competitive/brief.py`, adapted — replaces 6 CI sections with the 9 audit report sections). Combined ~200-250 LOC inside stages.py.
- Create `src/audit/prompts/synthesis_section.md`, `synthesis_master.md` (section-merge + surprise quality-bar prose; **does NOT compute the health score** — arithmetic is Python via `_compute_health_score`, see step 6), `health_score_rationale.md` (small Opus prompt: takes `{overall, per_section, signal_breakdown, band, top_findings_per_section}` → 3-5 sentence rationale paragraph at `temperature=0`), `surprise_quality_check.md`. Markdown prompts loaded at runtime via `prompts.load_prompt()`.
- Test: `tests/audit/test_synthesis.py`

**Approach:**
- `stage_3_synthesis`:
  1. Reads all 7 `agent_outputs[]` (Findability, Brand/Narrative, Conversion-Lifecycle, Distribution, MarTech-Attribution, Monitoring, Competitive) + `brief.md`. Groups all findings by `Finding.report_section` Literal enum directly — no pivot table, no rubric_themes.yaml mapping step. This yields 9 logical report-section buckets from 7 agent outputs (Findability agent's findings split across "seo" + "geo" buckets based on each Finding's own `report_section` tag; Conversion-Lifecycle agent's findings split across "conversion" + "lifecycle" similarly).
  2. **Rubric-coverage + report_section routing validation**: source-of-truth for the rubric→section mapping is `src/audit/data/rubrics_<agent>.yaml` (each rubric carries `id`, `evaluation_question`, `expected_finding_shape`, `report_section`); the agent prompt template loads from this YAML so prompt + validator stay in sync. Two checks run:
     - **Coverage**: for each of the 7 `AgentOutput.rubric_coverage` maps, verify every rubric key from the agent's `rubrics_<agent>.yaml` is present AND its value is `"covered"` or `"gap_flagged"`. Missing key or invalid value raises `RubricCoverageIncomplete`.
     - **Routing**: each `Finding` carries optional `addresses_rubrics: list[str]` (rubric IDs the agent claims it covers). For every finding with `addresses_rubrics` non-empty, assert `finding.report_section == rubrics_yaml[rubric_id].report_section` for each addressed rubric. Mismatch raises `ReportSectionMismatch` with `{agent, finding_id, addressed_rubric, expected_section, tagged_section}`. Catches the silent mis-routing failure mode where a Findability agent tags GEO findings as "seo" (or vice versa) and biases per-section health scores.
     Both raise actionable errors pointing to the specific agent + rubric — operational safety, catches prompt-drift and tag-drift independently. Aggregates all gap_flags into `synthesis/gap_report.md` surfaced to JR at the publish gate: "X of Y rubrics were gap_flagged in this audit — review before publishing."
  3. Soft quality check: logs a warning to `cost_log.jsonl` if any report section has 0 findings AND no `not_applicable=true` flag on the upstream agent, but does NOT abort — synthesis renders that section gracefully ("no issues surfaced at this depth of analysis").
  4. Calls `AuditBrief.generate()` (ported from Freddy): async fan-out of 9 section LLM calls (Opus, directive prompts — one per report section, fed the bucket of findings routed to that section via Finding.report_section); no per-call deadline — sections complete when complete. Each call uses `enable_file_checkpointing=True`; `session_id`s recorded via `state.record_session`. Results merged by a final Opus synthesis call.
  5. **Evaluator-optimizer self-critique** (Anthropic pattern): runs `prompts/surprise_quality_check.md` as a second Opus call that critiques each surprise against four bars (non-obvious · evidence-backed · tied to revenue/cost · feasible). The critique is passed *back to the synthesis agent* along with the original surprises — the agent decides whether to revise, retain, or mark them with `quality_warning=true`. At most one regeneration pass; no forced override. The four bars also live inline in `prompts/synthesis_master.md` so the synthesis agent self-assesses before the critique pass.
  6. **Health score = Python-deterministic arithmetic + Opus-written rationale.** The arithmetic is too consequential to leave to Opus stochasticity (the score is the Hero TL;DR's prominent number). Pure-Python helper `_compute_health_score(findings: list[Finding]) -> dict` computes: `overall = max(1, 10 - 2 * count(severity==3) - 1 * count(severity==2) - 0.5 * count(severity==1))`; `per_section[s] = max(1, 10 - 2 * count(s, severity==3) - 1 * count(s, severity==2) - 0.5 * count(s, severity==1))` for each of the 9 report_sections; `band = "red" if overall <= 4 else "yellow" if overall <= 7 else "green"`; `signal_breakdown = [{section, findings_counted, arithmetic: f"10 - 2×{cN} - 1×{cH} - 0.5×{cM} = {sub}"} for s in sections]`. This block is bit-deterministic. **Opus then writes only the rationale** — one separate ~250-token call that takes `{overall, per_section, signal_breakdown, band, top_findings_per_section}` as input and produces a 3-5 sentence rationale paragraph covering which sections drove the score, systemic patterns, and whether the band is tight at the boundary. Opus call uses `temperature=0` for the rationale to minimize prose-level variance. The numeric output is invariant across re-renders; the rationale paragraph may vary stylistically but cannot disagree with the arithmetic. Final `report.json:health_score` shape: `{overall: 1-10, per_section: {...}, signal_breakdown: [...], band: "red"|"yellow"|"green", rationale: "..."}`. Per-section subscores feed Stage-4 proposal-tier matching (Fix-it should disproportionately address the lowest-scoring sections).
  7. Writes `clients/<slug>/audit/synthesis/{findings.md, surprises.md, report.md, report.json, gap_report.md}`. `report.json` contains top-level `health_score` key with `{overall: 1-10, per_section: {...}, signal_breakdown: [...], band: "red"|"yellow"|"green", rationale: "..."}`. `gap_report.md` lists every rubric `gap_flagged` across all 7 agents, surfaced to JR at the publish gate.
- 9 report sections (envelope contract for rendering): Hero TL;DR (leads with health_score + per-section breakdown), Executive Summary, What We Found (per section), Surprises, Competitive Positioning, AI Visibility Posture, Technical Posture, **Recommended Next Steps (maps findings to proposal tiers, not a DIY playbook)**, About This Audit. Agent decides per-section length, number of findings, number of surprises within each section's quality bar. **Stage 3 synthesis back-fills each Finding's `proposal_tier_mapping` field** after Stage 4 generates the tier plan — so every finding explicitly says "Fix-it delivers this" / "Build-it delivers this" / "Run-it sustains this." The Recommended Next Steps section is rendered as: *"Fix-it tier addresses findings [#3, #7, #12] — high-severity technical and on-page issues scoped to the $[price] engagement. Build-it tier addresses [#1, #5, #9] — content and competitive infrastructure scoped to $[price]. Run-it tier sustains [#15, #18, #22] via monthly optimization scoped to $[price]/mo."* No separate execution playbook exists in the audit — that's engagement scope. The audit is the pitch; the engagement is the delivery.

**Test scenarios:**
- Happy: synthesis on dogfood Stage 2 output (7 agent_outputs) produces findings.md + surprises.md + report.md + gap_report.md (9 sections rendered). Counts of findings/surprises logged to telemetry, not asserted.
- Happy: `state.sessions["synthesis_*"]` entries populated for each of the 9 section calls + final merge + quality-critique call + health_score call.
- Happy: `report.json:health_score` populated with `{overall: 1-10, per_section, signal_breakdown, band, rationale}` after synthesis completes; overall between 1–10; band correct for the overall value (red 0–4 / yellow 5–7 / green 8–10).
- Happy: every Finding's `report_section` enum value is one of the 9 valid Literals (Pydantic enforces — orphan = construction-time error, not runtime).
- Happy: `rubric_coverage` validation passes — every rubric in every agent's checklist is present with `covered` or `gap_flagged` value. Integration test feeds a mocked AgentOutput with a missing rubric key and asserts `RubricCoverageIncomplete` is raised.
- Happy: cache-replay determinism — running synthesis twice against the same agent_outputs produces bit-identical `health_score.{overall, per_section, signal_breakdown, band}` (Python arithmetic). Rationale paragraph may differ in wording but cannot contradict the numbers.
- Edge: one report section has 0 findings + upstream agent flagged `not_applicable=true` → synthesis renders "not applicable" section gracefully.
- Edge: one report section has 0 findings AND no not_applicable flag → warning logged to `cost_log.jsonl`; synthesis renders "no issues surfaced" section and proceeds.
- Edge: ≥3 of 7 agents have `gap_flagged` count >50% of their rubric checklist → `gap_report.md` includes warning at top: "audit may be under-covered — review before publish."
- Edge: surprise quality-critique surfaces weaknesses → synthesis agent reviews critique, decides whether to revise or keep with `quality_warning=true`. No forced regeneration beyond one optional pass.
- Integration: synthesis telemetry logged (session_ids, per-call cost, duration). No cost/time assertion.

**Done when:** Synthesis output reads like a credible audit JR would sign off without rewriting AND `gap_report.md` either is empty or surfaces only expected gaps (e.g., R23 attach-demo not granted → onboarding-flow gap is expected).

---

### U6. Stage 4: proposal with capability registry

**Goal:** Opus picks the capability IDs it judges best fit the findings — count and tier mix are the agent's decision — and writes narrative per capability; Python validates IDs + applies pricing deterministically.

**Files:**
- Create `src/audit/capability_registry.yaml` with **~48 starter capabilities** (full content shipped below, not deferred to implementation) spanning SEO / GEO / Competitive / Content / Monitoring / Distribution / Lifecycle / MarTech-Attribution / **Brand-Narrative** across Fix-it / Build-it / Run-it tiers (23 baseline + 12 from R1 coverage expansion + ~13 from R2 coverage expansion covering industry-analyst-position-claim, brand-SERP defense, customer-support rebuild, EEAT content overhaul, e-commerce catalog CRO, B2C personalization, Trust Center stand-up, sales-motion shift advisory, mobile-app linking, paywall-upgrade CRO, robots-strategic-decision advisory, vertical-compliance audit + remediation, public-company IR build)
- Create `src/audit/capability_registry.py` — YAML loader + `pick_pricing(capability_id, prospect_size_band) -> (price, price_range)` function applying multipliers (small 0.8 / mid 1.0 / enterprise 1.3), clamped to `price_range`
- Create `src/audit/stages.py:stage_4_proposal` function
- Create `src/audit/prompts/proposal.md` (directive skeleton; loaded via `prompts.load_prompt("proposal")`)
- Test: `tests/audit/test_capability_registry.py`, `tests/audit/test_stage_4_proposal.py`

**Approach:**
- YAML schema per capability: `id, name, tier, scope, price_range [min,max], typical_price, prerequisites[], jr_time_hours`.
- `stage_4_proposal`:
  1. Reads synthesis + prospect context
  2. Opus call (`prompts/proposal.md`, directive skeleton): picks capability IDs matching findings + writes narrative per capability. Prompt carries the **heuristic** "offer at least one Fix-it and one Run-it when the findings support them; span tiers when natural," not a hard count mandate — a 2-capability or 5-capability proposal is fine when that's what the findings warrant. `session_id` persisted via `state.record_session("proposal", result)`; `enable_file_checkpointing=True`.
  3. Python validates returned IDs exist in registry (raises `ProposalValidationError` on hallucination — operational safety, not an agent cap)
  4. Python applies pricing via `pick_pricing()`; LLM never touches numbers
  5. Writes `clients/<slug>/audit/proposal/{proposal.md, proposal.json}`
- **Full starter registry content (23 entries, shipped in plan, not deferred):**

```yaml
# src/audit/capability_registry.yaml
# Price multipliers applied by pick_pricing(): small=0.8, mid=1.0, enterprise=1.3, clamped to [price_range.min, price_range.max]
# jr_time_hours is the founder's estimated hands-on hours per delivery cycle (month for retainers, one-shot for fix/build)

capabilities:
  # ═════ SEO tier ═════
  - id: seo-fix-schema-sitewide
    name: "Sitewide schema + structured-data fix"
    tier: fix
    scope: "Implement Organization, Product, Article, FAQ, BreadcrumbList JSON-LD across template library; validate in Rich Results Test; resolve existing errors in GSC."
    price_range: [2500, 5500]
    typical_price: 3500
    prerequisites: []
    jr_time_hours: 12
  - id: seo-fix-internal-linking
    name: "Internal-linking + orphan-page repair"
    tier: fix
    scope: "Resolve orphan pages, repair broken internal links, rebalance link equity to money pages based on `analyze_internal_links` output."
    price_range: [2000, 4500]
    typical_price: 3000
    prerequisites: []
    jr_time_hours: 10
  - id: seo-retainer-basic
    name: "SEO growth retainer (basic)"
    tier: run
    scope: "Monthly: technical crawl, rank monitoring, 4 content briefs, GSC hygiene, quarterly strategy review."
    price_range: [3500, 8000]
    typical_price: 5500
    prerequisites: []
    jr_time_hours: 20  # per month

  # ═════ GEO tier ═════
  - id: geo-fix-infra
    name: "AI-search crawlability infra (llms.txt + robots + schema)"
    tier: fix
    scope: "Ship llms.txt + llms-full.txt, audit robots.txt for AI crawler blocks, add AI-friendly schema (HowTo, QAPage, FAQPage), validate across ChatGPT + Perplexity + Gemini + Claude."
    price_range: [2000, 4500]
    typical_price: 3000
    prerequisites: []
    jr_time_hours: 10
  - id: geo-build-llms-txt-suite
    name: "Full llms.txt content architecture"
    tier: build
    scope: "Build llms-full.txt with canonical product/pricing/docs content; entity-resolve brand + product + exec; establish AI-crawler sitemap patterns."
    price_range: [6000, 14000]
    typical_price: 9500
    prerequisites: [geo-fix-infra]
    jr_time_hours: 30

  # ═════ Competitive tier ═════
  - id: competitive-build-monitoring
    name: "Competitive monitoring infrastructure"
    tier: build
    scope: "Stand up monthly competitive intel pipeline — backlinks / keywords / ads / SERP features / AI citations / press — delivered as a quarterly briefing."
    price_range: [5000, 12000]
    typical_price: 7500
    prerequisites: []
    jr_time_hours: 25

  # ═════ Content tier ═════
  - id: content-build-pseo-engine
    name: "Programmatic SEO content engine"
    tier: build
    scope: "Ship a pSEO template system with 500–2000 page coverage — keyword research, template design, data source integration, publishing pipeline, indexation monitoring."
    price_range: [15000, 45000]
    typical_price: 25000
    prerequisites: [seo-fix-schema-sitewide, seo-fix-internal-linking]
    jr_time_hours: 80
  - id: content-retainer
    name: "Content production retainer"
    tier: run
    scope: "Monthly: 4 long-form articles + 8 supporting assets + distribution; briefs, editing, publishing, internal linking."
    price_range: [4500, 10000]
    typical_price: 6500
    prerequisites: []
    jr_time_hours: 25  # per month

  # ═════ Monitoring tier ═════
  - id: monitoring-retainer
    name: "Brand + VoC monitoring retainer"
    tier: run
    scope: "Monthly: cross-platform mention tracking (Xpoz + IC + NewsData + Pod Engine + reviews), sentiment-drift reporting, pain-point coding, alerts on reputation events."
    price_range: [2500, 6000]
    typical_price: 3500
    prerequisites: []
    jr_time_hours: 12  # per month

  # ═════ Distribution tier ═════
  - id: paid-fix-creative-refresh
    name: "Paid-ad creative refresh"
    tier: fix
    scope: "Rebuild stale ad creative based on Foreplay teardown findings — new hooks + offers + landing-page coherence + channel-native UGC. Ship 10–20 new ad variants."
    price_range: [3500, 8000]
    typical_price: 5000
    prerequisites: []
    jr_time_hours: 20
  - id: paid-build-channel-expansion
    name: "Paid-media channel expansion"
    tier: build
    scope: "Launch a missing paid channel identified by `audit_channel_presence` gap — creative + landing-page + attribution wiring for one new channel (Meta / TikTok / LinkedIn / Reddit)."
    price_range: [8000, 20000]
    typical_price: 12000
    prerequisites: [paid-fix-creative-refresh]
    jr_time_hours: 40
  - id: organic-social-retainer
    name: "Organic social + creator retainer"
    tier: run
    scope: "Monthly cadence across the 3–5 platforms where the prospect is active — content production, community engagement, creator outreach, engagement-rate optimization."
    price_range: [4000, 10000]
    typical_price: 6000
    prerequisites: []
    jr_time_hours: 30  # per month
  - id: full-distribution-retainer
    name: "Full distribution retainer (paid + organic + video + podcast)"
    tier: run
    scope: "All distribution channels — paid media management across Meta + Google + LinkedIn + TikTok, organic social across 3–5 platforms, YouTube cadence, monthly podcast-guest bookings, earned-media pitching."
    price_range: [8000, 25000]
    typical_price: 15000
    prerequisites: []
    jr_time_hours: 60  # per month

  # ═════ Lifecycle tier ═════
  - id: lifecycle-fix-capture-rebuild
    name: "Email + SMS capture-UX rebuild"
    tier: fix
    scope: "Rebuild popup timing + incentive + copy + design based on `capture_surface_scan` findings + Klaviyo benchmarks; ship exit-intent + embedded form variants; TCPA-compliant SMS 2-step opt-in."
    price_range: [2500, 6000]
    typical_price: 3500
    prerequisites: []
    jr_time_hours: 12
  - id: lifecycle-build-flow-engine
    name: "Lifecycle flow engine (welcome + cart + winback + post-purchase)"
    tier: build
    scope: "Build out 6–10 lifecycle flows in the prospect's ESP — welcome series, cart/browse/checkout abandonment, post-purchase, replenishment, winback, sunset, VIP, birthday. Requires ESP access (R19) for delivery."
    price_range: [9000, 22000]
    typical_price: 14000
    prerequisites: [lifecycle-fix-capture-rebuild]
    jr_time_hours: 50
  - id: lifecycle-retainer
    name: "Lifecycle optimization retainer"
    tier: run
    scope: "Monthly: flow performance review, A/B test cadence, segmentation refinement, deliverability monitoring, quarterly list hygiene."
    price_range: [3500, 8000]
    typical_price: 5000
    prerequisites: []
    jr_time_hours: 18  # per month

  # ═════ MarTech-Attribution tier ═════
  - id: martech-fix-stack-cleanup
    name: "MarTech stack cleanup (dormant pixels + tool overlap)"
    tier: fix
    scope: "Remove dormant pixels flagged by `fingerprint_martech_stack`; consolidate overlapping tools (multiple heatmappers / chats / schedulers); remove accessibility-overlay ADA-risk vendors."
    price_range: [2000, 5000]
    typical_price: 3000
    prerequisites: []
    jr_time_hours: 10
  - id: martech-build-attribution-closed-loop
    name: "Closed-loop attribution build (sGTM + Consent Mode v2 + CDP)"
    tier: build
    scope: "Ship server-side GTM with first-party cookie domain, Consent Mode v2 with `ad_user_data` / `ad_personalization` signals, Meta CAPI integration, Segment or RudderStack CDP with identity resolution + warehouse sync."
    price_range: [12000, 35000]
    typical_price: 18000
    prerequisites: [martech-fix-stack-cleanup]
    jr_time_hours: 60
  - id: martech-retainer
    name: "MarTech + attribution-integrity retainer"
    tier: run
    scope: "Monthly: attribution-integrity monitoring, privacy-posture tracking (CMP / Consent Mode / DMA), UTM-discipline enforcement, quarterly tool-overlap audit."
    price_range: [2500, 6500]
    typical_price: 4000
    prerequisites: []
    jr_time_hours: 10  # per month

  # ═════ Brand/Narrative tier ═════
  - id: brand-fix-messaging-consistency
    name: "Cross-surface messaging consistency fix"
    tier: fix
    scope: "Reconcile positioning drift across homepage / pricing / LinkedIn / Twitter / G2 / meta tags based on `audit_messaging_consistency` findings. One positioning doc + 8–12 surface rewrites."
    price_range: [3500, 8000]
    typical_price: 5000
    prerequisites: []
    jr_time_hours: 18
  - id: brand-build-narrative-platform
    name: "Brand narrative + thought-leadership platform"
    tier: build
    scope: "Ship positioning framework (April Dunford), content-pillar architecture, exec thought-leadership editorial calendar, proprietary-research program kickoff (1 report or index) with press + distribution plan."
    price_range: [15000, 40000]
    typical_price: 22000
    prerequisites: [brand-fix-messaging-consistency]
    jr_time_hours: 70
  - id: pr-retainer
    name: "PR + earned-media retainer"
    tier: run
    scope: "Monthly: press pitching (2–4 pitches), exec podcast-guesting bookings, Tier-1 trade relationship building, Wikipedia hygiene, award nomination pipeline."
    price_range: [5000, 15000]
    typical_price: 8000
    prerequisites: []
    jr_time_hours: 25  # per month

  # ═════ 2026-04-22 expansion: SEO + Site Quality ═════
  - id: seo-fix-international
    name: "International SEO setup (hreflang + locale URL strategy + regional sitemaps)"
    tier: fix
    scope: "Implement hreflang reciprocity across all locale pages, fix x-default, resolve canonical-vs-hreflang conflicts, ship regional sitemaps, fix IP-based geo-redirect blocking alt-locale indexing. Per `audit_international_seo` findings."
    price_range: [3500, 9000]
    typical_price: 5000
    prerequisites: []
    jr_time_hours: 18
  - id: seo-fix-local
    name: "Local SEO citation cleanup + GBP optimization"
    tier: fix
    scope: "Claim/optimize Google Business Profile (categories, hours, attributes, photos, services, products); reconcile NAP across Yelp + Apple Maps + Bing Places + TripAdvisor + Foursquare + Yellow Pages + BBB; ship LocalBusiness schema; build geographic landing pages for top 5 cities. For local-business prospects only."
    price_range: [2500, 7000]
    typical_price: 4000
    prerequisites: []
    jr_time_hours: 14
  - id: seo-fix-accessibility-wcag
    name: "WCAG 2.1 AA accessibility remediation"
    tier: fix
    scope: "Resolve all axe-core critical + serious violations from `audit_accessibility`; fix color-contrast failures (4.5:1 normal / 3:1 large); add alt-text coverage; fix form-label associations; fix landmark structure + heading-skip issues; remove ADA-litigation-magnet accessibility overlays (UserWay/AccessiBe/EqualWeb); ship accessibility statement page. **Reduces ADA-lawsuit exposure** — most US-targeting sites are technically non-compliant."
    price_range: [4500, 12000]
    typical_price: 7000
    prerequisites: []
    jr_time_hours: 25
  - id: seo-build-help-center
    name: "Help center / docs SEO architecture build"
    tier: build
    scope: "Stand up Algolia DocSearch (or Mintlify/Stoplight/GitBook depending on technical maturity) + content architecture for product docs; ship initial 50–100 articles per `audit_help_center_docs` gap analysis; structured schema (FAQPage, HowTo); search-bar prominence + nav depth optimization."
    price_range: [12000, 30000]
    typical_price: 18000
    prerequisites: [seo-fix-schema-sitewide]
    jr_time_hours: 60

  # ═════ 2026-04-22 expansion: Distribution + Listings ═════
  - id: distribution-fix-directory-listings
    name: "Directory + marketplace listings optimization"
    tier: fix
    scope: "Claim + optimize G2/Capterra/GetApp/AlternativeTo/Product Hunt listings (description, screenshots, reviews response strategy); ship Atlassian/Zapier/HubSpot/Shopify integration listings where applicable; AI-directory submissions (TAAFT/Futurepedia) for AI-tool prospects. Per `audit_directory_presence` + `audit_marketplace_listings` gaps."
    price_range: [3500, 10000]
    typical_price: 5500
    prerequisites: []
    jr_time_hours: 20
  - id: distribution-build-oss-program
    name: "OSS footprint + developer-community program"
    tier: build
    scope: "Stand up GitHub org strategy (license posture, CONTRIBUTING.md, sponsor program, good-first-issue labeling, README quality), ship 1–2 OSS SDK or sample-app repos, GitHub Discussions community setup. **Tied to AI-search citation supply** — high-star repos heavily indexed by Claude/ChatGPT/Perplexity. For dev-tool/tech prospects only."
    price_range: [10000, 30000]
    typical_price: 15000
    prerequisites: []
    jr_time_hours: 50
  - id: distribution-build-launch-program
    name: "Product launch + changelog program"
    tier: build
    scope: "Stand up Product Hunt launch playbook (launch-day cadence, hunter outreach, asset templates), changelog architecture (`/changelog` + RSS + email subscribers), waitlist mechanism for next 3–6 launches. Per `audit_launch_cadence` gap."
    price_range: [6000, 18000]
    typical_price: 10000
    prerequisites: []
    jr_time_hours: 40

  # ═════ 2026-04-22 expansion: Conversion + Trust + ABM + PLG + DevEx ═════
  - id: conversion-fix-trust-signals
    name: "Trust signals + security headers + CMP deployment"
    tier: fix
    scope: "Add SOC 2 / ISO 27001 / HIPAA / PCI-DSS attestation pages; ship customer logo wall + testimonial blocks + Trustpilot/G2 widget integration; remediate Mozilla HTTP Observatory grade gaps (CSP, HSTS, X-Frame-Options, Permissions-Policy); deploy CMP (OneTrust/Cookiebot/Iubenda) with Consent Mode v2 wired. Per `audit_trust_signals` findings."
    price_range: [3500, 9000]
    typical_price: 5500
    prerequisites: []
    jr_time_hours: 18
  - id: conversion-build-abm-stack
    name: "ABM stack build (personalization + reverse-IP + intent data)"
    tier: build
    scope: "Stand up named-account personalization layer (Mutiny / RightMessage / Demandbase); deploy reverse-IP visitor identification (Clearbit Reveal / Snitcher / Leadfeeder / RB2B); wire intent-data subscriptions (Bombora / G2 Buyer Intent / ZoomInfo Intent); ship 5–15 named-account landing pages with dynamic personalization. **For B2B enterprise prospects ($50K+ ACV) only.**"
    price_range: [25000, 75000]
    typical_price: 40000
    prerequisites: [martech-build-attribution-closed-loop]
    jr_time_hours: 100
  - id: plg-build-self-serve-motion
    name: "PLG self-serve motion build (free trial + viral loops + reverse-trial)"
    tier: build
    scope: "Build self-serve signup → activation → expansion motion: pricing-page restructure (free-trial / freemium / reverse-trial / hybrid per `audit_plg_motion` recommendation), TTFV onboarding optimization, in-product viral mechanisms (powered-by branding + share-to-unlock + referral program), Appcues/Pendo/Userflow guidance layer. **For SaaS prospects only.**"
    price_range: [18000, 50000]
    typical_price: 28000
    prerequisites: []
    jr_time_hours: 80
  - id: devex-build-api-docs-stack
    name: "DevEx stack build (Mintlify/Stoplight docs + OpenAPI + SDK coverage)"
    tier: build
    scope: "Migrate from legacy docs (raw Swagger UI / GitBook) to modern API-docs platform (Mintlify or Stoplight or Scalar or Redoc per prospect technical preference); ship OpenAPI spec at `/openapi.json`; build quickstart with <5min time-to-first-API-call; ship 3–5 SDK clients (TypeScript/Python/Go primary); 2 sample apps + cookbook. **For dev-tool prospects only.**"
    price_range: [15000, 45000]
    typical_price: 25000
    prerequisites: []
    jr_time_hours: 70

  # ═════ 2026-04-22 expansion: Brand/Narrative customer programs ═════
  - id: brand-build-customer-education
    name: "Customer education program (academy/university/certifications)"
    tier: build
    scope: "Stand up branded learning platform (Thinkific/Teachable/Skilljar/Northpass per scale); ship 8–15 courses across product fundamentals + advanced workflows + admin/operator track; certification program + Credly/Accredible badges. Single highest-leverage retention + advocacy mechanism for SaaS — HubSpot Academy / Salesforce Trailhead / Klaviyo / Twilio Quest pattern."
    price_range: [25000, 80000]
    typical_price: 40000
    prerequisites: []
    jr_time_hours: 100
  - id: brand-fix-public-roadmap
    name: "Public roadmap + customer-feedback portal"
    tier: fix
    scope: "Stand up Canny / Productboard / Featurebase / Frill public roadmap; configure status labels (Planned / In Progress / Shipped); seed with 30–50 active items; train team on weekly response cadence + monthly progress narratives. Customer-centricity signal — different from changelog (past) — roadmap is future."
    price_range: [3000, 8000]
    typical_price: 4500
    prerequisites: []
    jr_time_hours: 16
  - id: brand-build-employer-program
    name: "Employer brand + careers-site optimization"
    tier: build
    scope: "Optimize Glassdoor + Indeed + Comparably presence (claim profiles, response strategy, salary transparency for CA/NY/CO/WA jurisdictional compliance — fines $100-$10K/violation), build culture content for careers site, optimize JD structure (tech-stack disclosure, salary ranges, async-first signals), LinkedIn employer-page strategy. **Pay-transparency compliance is the publishable anchor finding** — most prospects have $100K+ legal exposure from non-disclosure."
    price_range: [12000, 35000]
    typical_price: 18000
    prerequisites: []
    jr_time_hours: 60
  - id: brand-build-winloss-program
    name: "Win-loss interview program (Klue methodology)"
    tier: build
    scope: "Stand up structured win-loss interview program per Klue 31-questions methodology; conduct 12–20 quarterly interviews per cycle; theme-cluster + competitive-displacement matrix + pricing-objection synthesis; quarterly readout to product/sales/marketing leadership. Mature signal of GTM rigor."
    price_range: [15000, 40000]
    typical_price: 22000
    prerequisites: []
    jr_time_hours: 60  # per quarter
  - id: conversion-fix-demo-flow
    name: "Onboarding flow + demo-account TTFV optimization"
    tier: fix
    scope: "Per R23 attach-demo audit findings: optimize empty-state quality, ship contextual help / in-product guidance (Appcues/Pendo/Userflow), reduce friction points in signup → first-value-moment path, implement progressive disclosure. Target: TTFV reduction by 50% per Wes Bush Bowling Alley framework."
    price_range: [8000, 22000]
    typical_price: 12000
    prerequisites: []
    jr_time_hours: 50

  # ═════ 2026-04-22 R2 expansion: Brand defense + analyst position + executive perimeter ═════
  - id: brand-build-analyst-position-claim
    name: "Industry analyst position pursuit (G2 / Forrester / Gartner / IDC)"
    tier: build
    scope: "Pursue analyst recognition: G2 Grid quadrant inclusion + Capterra Shortlist submission + Forrester briefing prep + Gartner MQ vendor briefing pursuit + IDC MarketScape inclusion + industry awards (Inc 5000, Fast Company Most Innovative, Deloitte Fast 500). **Single largest enterprise-revenue lever** — Gartner MQ Leader designation drives 30-50% enterprise close rate. 6-12 month timeline."
    price_range: [25000, 80000]
    typical_price: 45000
    prerequisites: [pr-retainer]
    jr_time_hours: 120
  - id: brand-fix-serp-defense
    name: "Branded SERP defense + Knowledge Panel claim"
    tier: fix
    scope: "Claim + complete Google Knowledge Panel; fix sitelinks via Search Console; implement Organization + Person schema for entity disambiguation; address PAA defensive queries ('is X scam?', 'is X safe?') via dedicated FAQ pages + reputation content; pursue Wikipedia article + brand entity on Wikidata. Per `audit_branded_serp` findings."
    price_range: [4500, 12000]
    typical_price: 7000
    prerequisites: []
    jr_time_hours: 25
  - id: brand-build-public-company-ir
    name: "Investor relations page + IR program build (public-company)"
    tier: build
    scope: "Stand up IR page (`/investors`) with SEC filings linked + earnings call transcript publishing + analyst coverage list + IR contact + stock chart widget (Q4/NIRI-style) + ESG report linkage + DEF 14A proxy publication discipline. Conditional public-company prospect."
    price_range: [18000, 45000]
    typical_price: 25000
    prerequisites: []
    jr_time_hours: 80

  # ═════ 2026-04-22 R2 expansion: Conversion + Trust ═════
  - id: conversion-build-customer-support-rebuild
    name: "Customer support rebuild (chat deployment + multilingual + AI chatbot)"
    tier: build
    scope: "Per `audit_customer_support` findings: rebuild live chat deployment (Intercom/Drift/Zendesk) — set business hours visible, multilingual support, bot-vs-human triage, response-time SLA published, on-brand AI chatbot with escalation-to-human path, support-language coverage. Includes content for top 50 support topics."
    price_range: [12000, 35000]
    typical_price: 18000
    prerequisites: []
    jr_time_hours: 60
  - id: seo-build-eeat-content-overhaul
    name: "E-E-A-T content overhaul (author bios + Person schema + expertise indicators)"
    tier: build
    scope: "Per `audit_eeat_signals` findings: ship author bio pages (`/author/<slug>/`) for top 20 contributors with Person JSON-LD schema (jobTitle, worksFor, sameAs[] to LinkedIn/ORCID/Google Scholar); add 'Reviewed by [credentialed expert]' for YMYL content; ship `/about`, `/editorial-policy`, `/methodology`, `/corrections-policy` pages. **Google #1 ranking factor since 2023.**"
    price_range: [15000, 40000]
    typical_price: 22000
    prerequisites: [seo-fix-schema-sitewide]
    jr_time_hours: 70
  - id: conversion-build-ecommerce-catalog-cro
    name: "E-commerce catalog CRO (per-SKU optimization + recommendations + checkout)"
    tier: build
    scope: "Per `audit_ecommerce_catalog` findings: per-SKU optimization (image count, Product schema, AggregateRating), recommendations engine integration (Searchspring/Algolia Recommend/Klaviyo Reviews), guest-checkout enablement, faceted-nav UX, 'Frequently bought together' + 'Customers also viewed' widgets. For DTC/e-comm prospects."
    price_range: [18000, 50000]
    typical_price: 28000
    prerequisites: []
    jr_time_hours: 80
  - id: conversion-build-b2c-personalization
    name: "B2C personalization platform build (Dynamic Yield / Optimizely / VWO Personalize)"
    tier: build
    scope: "Stand up B2C personalization layer (Dynamic Yield / Optimizely Web Personalization / VWO Personalize / Adobe Target / Insider / Bloomreach Engagement); ship 5-10 audience-segment campaigns; CDP integration for activation. Distinct from B2B ABM. For B2C/DTC prospects only."
    price_range: [22000, 65000]
    typical_price: 35000
    prerequisites: [martech-build-attribution-closed-loop]
    jr_time_hours: 90
  - id: conversion-fix-trust-center-stand-up
    name: "Trust Center stand-up (SafeBase / Vanta / Drata / Whistic)"
    tier: fix
    scope: "Stand up self-serve security review platform (SafeBase / Vanta Trust Center / Drata Trust Hub / Whistic / Conveyor); upload SOC 2 Type II + ISO 27001 + HIPAA + PCI-DSS reports + DPA + sub-processor list + DPIA + security questionnaire pre-fills. **Cuts enterprise sales cycle 30-60 days when present.** Per `audit_trust_center` finding."
    price_range: [6000, 18000]
    typical_price: 10000
    prerequisites: []
    jr_time_hours: 30
  - id: conversion-fix-paywall-upgrade-cro
    name: "Paywall + upgrade-CTA CRO (freemium prospects)"
    tier: fix
    scope: "Per `audit_paywall_upgrade_cro` findings (when freemium detected): rebuild upgrade-CTA placement, urgency/scarcity copy, social-proof on upgrade prompts, in-product upgrade-trigger placement (requires R23 demo for full audit), reduce clicks-to-upgrade. Conditional on freemium."
    price_range: [4000, 12000]
    typical_price: 6500
    prerequisites: []
    jr_time_hours: 25

  # ═════ 2026-04-22 R2 expansion: Distribution + Mobile + AI Crawler Strategy ═════
  - id: distribution-fix-mobile-app-linking
    name: "Mobile app linking + universal links + smart app banner"
    tier: fix
    scope: "Ship `<meta name='apple-itunes-app'>` smart app banner; deploy `/.well-known/apple-app-site-association` (Universal Links) + `/.well-known/assetlinks.json` (Android App Links); migrate from dead Firebase Dynamic Links (sunset 2025-08-25) to Branch.io / Adjust / AppsFlyer OneLink. **4-8x install-from-web conversion when wired.** For mobile-app prospects."
    price_range: [3500, 10000]
    typical_price: 5500
    prerequisites: []
    jr_time_hours: 20
  - id: seo-fix-robots-ai-crawler-decision
    name: "Robots.txt + AI crawler strategic decision (allow/block GPTBot/ClaudeBot/PerplexityBot)"
    tier: fix
    scope: "**Strategic decision audit**: review GPTBot / ClaudeBot / anthropic-ai / CCBot / Bytespider / Google-Extended / PerplexityBot / OAI-SearchBot allow vs block patterns; weigh future AI-search citation supply vs content-monetization risk; ship resulting robots.txt + `meta name='robots' content='noai'` decisions; document strategic rationale for stakeholders. Per `audit_robots_strategic` finding."
    price_range: [2500, 7000]
    typical_price: 4000
    prerequisites: []
    jr_time_hours: 12
  - id: martech-fix-vertical-compliance
    name: "Vertical compliance disclosure + Trust Center population (HIPAA/PCI/FERPA/etc.)"
    tier: fix
    scope: "Per `audit_vertical_compliance` findings (conditional vertical): publish HIPAA BAA template (healthtech) / PCI-DSS Level disclosure + state MTL public listing (fintech) / FERPA disclosure (edtech) / FDA 510(k) clearance language (medical devices) / DSA-DMA transparency reports (EU large platforms) / SOX disclosures (public) / GLBA disclosures (financial services). Cross-reference Trust Center build."
    price_range: [8000, 25000]
    typical_price: 12000
    prerequisites: [conversion-fix-trust-center-stand-up]
    jr_time_hours: 40

  # ═════ 2026-04-22 R2 expansion: Synthesis advisory ═════
  - id: synthesis-advisory-sales-motion-shift
    name: "Sales motion shift advisory (PLG ↔ inside-sales ↔ enterprise-sales transition)"
    tier: build
    scope: "When `audit_sales_motion_classification` reveals motion-mismatch (e.g., sales-led with PLG ICP, or PLG with enterprise-only ICP): structured 90-day advisory + transition plan (pricing-page restructure, sales-rep hiring/restructure, qualification-stage redesign, marketing-message-realignment, CRM-pipeline-stage redefinition). Hybrid model often correct answer."
    price_range: [25000, 75000]
    typical_price: 40000
    prerequisites: []
    jr_time_hours: 100
```

The registry is iterable — weights (`typical_price`, `price_range`) re-tune after first 10 audits based on close rate by tier; new capability entries added as patterns emerge across the funnel. **Tiers span all 9 report-section categories (SEO / GEO / Competitive / Monitoring / Conversion / Distribution / Lifecycle / MarTech-Attribution / Brand-Narrative); every finding severity-3 in any section has at least one Fix-it or Build-it capability that addresses it.** Capability selection is driven by `Finding.report_section` (the R5 Literal enum tagged by each agent), not the Stage-2 agent that produced the finding.

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

- **Full template structure spec (shipped in-plan, not deferred):**

  ```
  src/audit/templates/audit_report.html.j2  (single-file Jinja2 template with embedded partials)

  {# ═══════════════════════════════════════════════════════════════════════
     Section 1 — Hero TL;DR  (above-the-fold, prospect-screenshot-optimized)
     Data consumed: report.json.health_score.{overall (1-10), per_section, signal_breakdown[], band, rationale}
     Partial:       _partials/hero.j2
     Print CSS:     page-break-after: avoid; keep health-score block + radar together
     Render notes:  Health-score numeral uses Tailwind text-9xl; color classes bound
                    to band (red-500 | yellow-500 | green-500). Radar via inline SVG
                    (no chart-library dependency — print-safe, PDF-safe).
     ═══════════════════════════════════════════════════════════════════════ #}

  {# Section 2 — Executive Summary
     Data consumed: report.md → Section 2 prose (Opus-generated, 200–400 words)
     Partial:       _partials/exec_summary.j2
     Render notes:  Renders markdown → HTML via mistune; preserves pullquote blocks. #}

  {# Section 3 — What We Found (per report section, 9 subsections rendered in order)
     Data consumed: synthesis section-buckets (findings grouped by Finding.report_section
                    Literal enum tagged at Stage 2; findings originate from any of the 7 Stage-2 agents)
                    + per-section intro paragraph from Stage 3 synthesis
     Partial:       _partials/report_section.j2 (looped)
     Render notes:  Each finding renders:
                      - title (h3)
                      - severity pill (0–3 color-coded)
                      - reach + feasibility pills
                      - evidence_quotes block (blockquote with cite-URL footer)
                      - evidence_urls footnote refs
                      - recommendation paragraph (strategic, tier-mapped)
                      - proposal_tier_mapping chip (Fix-it | Build-it | Run-it)
                      - category_tags (muted chips)
                    Report section with 0 findings + upstream agent not_applicable=true →
                    collapsed to one-liner.
                    Report section with 0 findings without not_applicable → "no issues
                    surfaced at this depth" placeholder paragraph. #}

  {# Section 4 — Surprises  (2–6 items, agent-determined count)
     Data consumed: report.json.surprises[] → {headline, evidence_block, quality_warning}
     Partial:       _partials/surprises.j2
     Render notes:  Each surprise is a full-width card with bold headline + 2–3 sentence
                    evidence block + supporting screenshot if screenshot_path is set.
                    quality_warning=true renders a muted "reviewer note" pill but DOES NOT
                    suppress the finding — JR makes the final call at Gate 3. #}

  {# Section 5 — Competitive Positioning  (synthesizes Competitive lens + Distribution
                                             lens paid-creative findings + Brand/Narrative
                                             positioning findings — unified competitor view)
     Data consumed: report.md → Section 5 prose + competitor_comparison_table.json
     Partial:       _partials/competitive.j2
     Render notes:  Includes a comparison table (prospect vs 3–5 competitors on
                    referring_domains / keyword_overlap / paid_creative_volume /
                    earned_media_tier_1_share / positioning_category). Sortable in HTML,
                    static in PDF. #}

  {# Section 6 — AI Visibility Posture  (GEO lens deep-dive)
     Data consumed: score_ai_visibility output + analyze_serp_features.ai_overview
     Partial:       _partials/ai_visibility.j2
     Render notes:  Per-platform citation-count chart (bar chart, inline SVG);
                    word_pos_score prominence indicator per platform; competitor-SOV
                    stacked-bar comparison on the same prompts. #}

  {# Section 7 — Technical Posture  (merges SEO technical + MarTech-Attribution lens)
     Data consumed: audit_on_page_seo site-level rollup + audit_page_speed mobile/desktop
                    + fingerprint_martech_stack derived stack + assess_attribution_maturity
     Partial:       _partials/technical.j2
     Render notes:  Core Web Vitals scorecard (LCP/INP/CLS — mobile + desktop bands);
                    martech-stack category-inventory table; attribution-maturity tier
                    badge (absent / basic / sGTM / closed-loop). #}

  {# Section 8 — Recommended Next Steps  (maps findings → proposal tiers — NOT a DIY playbook)
     Data consumed: proposal.json → capabilities[] + pricing + tier_mapping
                    + findings_by_tier groupings
     Partial:       _partials/next_steps.j2
     Render notes:  Fix-it tier block (capability narrative + price + mapped findings list);
                    same for Build-it + Run-it. Total of 3 tier blocks maximum (some tiers
                    may be absent if findings don't support them). Each capability gets
                    name + one-paragraph scope + price (no ranges — rendered as one number
                    via pick_pricing). Pre-engagement expectations set here only. #}

  {# Section 9 — About This Audit  (verbatim template copy — NOT LLM-generated; frames
                                     audit-vs-engagement scope)
     Data consumed: static template copy + {{ audit_fee }} + {{ credit_window_days }}
     Partial:       _partials/about_audit.j2
     Render notes:  9-paragraph explainer. Final paragraph renders Fix-it / Build-it /
                    Run-it pricing table footer. #}

  {# Global footer (every page, HTML + PDF)
     <footer class="gofreddy-footer">
       Prepared by GoFreddy · <a href="https://gofreddy.ai">gofreddy.ai</a>
     </footer>

     Print CSS (@page @bottom-center) preserves footer on every PDF page. #}
  ```

  **Print CSS rules (in `src/audit/templates/print.css`, loaded via `<link media="print">`):**

  ```css
  @page {
    size: A4;
    margin: 2cm 1.5cm 2cm 1.5cm;
    @bottom-center { content: "Prepared by GoFreddy · gofreddy.ai  —  Page " counter(page) " of " counter(pages); font-size: 9pt; color: #666; }
  }
  /* Prevent Hero TL;DR splitting across pages */
  .hero-tldr { page-break-after: avoid; page-break-inside: avoid; }
  /* Keep each finding card together */
  .finding-card { page-break-inside: avoid; break-inside: avoid-page; }
  /* Surprise cards span full width, keep together */
  .surprise-card { page-break-inside: avoid; break-inside: avoid-page; }
  /* Section headers don't orphan */
  section > h2 { page-break-after: avoid; break-after: avoid-page; }
  /* Tables split at row boundaries */
  table { page-break-inside: auto; }
  tr { page-break-inside: avoid; break-inside: avoid-page; }
  thead { display: table-header-group; }
  tfoot { display: table-footer-group; }
  /* Radar SVG scales to container */
  .radar-chart { max-width: 100%; height: auto; }
  ```

  **WeasyPrint-specific notes:**
  - `<img>` embeds must use absolute file paths resolved at render time
  - Inline `<style>` + CDN Tailwind work in HTML but WeasyPrint needs the compiled CSS — generate via `tailwindcss -i input.css -o dist.css` at render time (5-sec step) or ship a pre-compiled `audit_report.css` in the repo (simpler, chosen)
  - Custom fonts (Inter for body, JetBrains Mono for code snippets) declared via `@font-face` with local file paths; font files committed to `src/audit/templates/fonts/`
  - Max PDF size target: ≤5 MB for email attachability; screenshots pre-compressed to ≤200 KB each at `prediscovery/screenshots/` write time (`Pillow` in deps via `pymupdf` already)
- **Hero TL;DR leads with the health score**: a large 1–10 numeral (color-coded by band — red 1–4, yellow 5–7, green 8–10 per R5 Opus-generated score) + a compact per-section breakdown (horizontal bar chart or **9-axis radar** covering SEO / GEO / Competitive / Monitoring / Conversion / Distribution / Lifecycle / MarTech-Attribution / Brand-Narrative). The rationale paragraph Opus produces renders as subtitle below the numeral. This is the metric prospects will screenshot and share internally — worth disproportionate design investment. Template reads `report.json:health_score` directly; no LLM involved in rendering the number (Opus wrote it in Stage 3).
- **About This Audit section (section 9)** explicitly frames audit vs. engagement scope to prevent prospects from thinking the audit replaces the engagement. Template copy (rendered verbatim, not LLM-generated): *"This audit uses public signals to diagnose what's happening in your marketing across nine dimensions — AI visibility, SEO, competitive posture, conversion, brand/voice/mentions, paid-plus-organic distribution, lifecycle/email capture, marketing technology stack, and brand narrative / positioning / thought leadership / PR. It's the diagnosis. The engagement is the treatment. With an engagement, we add account access (Google Search Console, Google Analytics, Ad platforms, ESP, CDP, NPS/survey data, brand assets) that reveals metrics this audit literally cannot surface: bounce rate, conversion funnels, user-flow drop-offs, channel-level ROI, email open/click/CVR, ad ROAS, NPS detractor reasons, cross-asset brand consistency. We also bring implementation capacity — actually doing the work in the Recommended Next Steps, not just identifying it — plus monthly optimization cycles that compound over time. The audit shows you WHAT to fix; the engagement FIXES it. Fix-it / Build-it / Run-it pricing is in Section 8, credited against the $1,000 audit fee if you sign within 60 days."* This paragraph sets expectations cleanly for the walkthrough-call engagement pitch.
- WeasyPrint renders same HTML → PDF (≤ 5 MB for email attachability).
- Stage 5 generates ULID slug, writes to state.json, produces `deliverable/{report.html, report.pdf, assets/}`.
- `freddy audit publish --client <slug>` uploads deliverable tree to R2 bucket `gofreddy-audits/<ulid>/`; prints final URL `https://reports.gofreddy.ai/<ulid>`.
- Cloudflare Worker on `reports.gofreddy.ai/*`: validates path matches ULID regex, proxies to R2; else 404.
- Every rendered page (HTML + PDF) includes a footer partial `<footer class="gofreddy-footer">Prepared by GoFreddy · <a href="https://gofreddy.ai">gofreddy.ai</a></footer>` — preserved on every page of the PDF via WeasyPrint `@page { @bottom-center }` CSS rule.

**Test scenarios:**
- Happy: render produces valid HTML (W3C validator passes) + openable PDF.
- Happy: screenshots embedded correctly in both HTML and PDF.
- Happy: Hero TL;DR displays `report.json:health_score.overall` (1-10) as a large number with correct color band (red 1-4 / yellow 5-7 / green 8-10); per-section breakdown shows all 9 sub-scores; rationale paragraph renders as subtitle.
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
- Create `src/api/routers/audit_webhooks.py` — single router hosting 6 endpoints. U8 ships 3: `POST /v1/audit/intake` (writes Supabase `audit_pending` row + triggers `stages.stage_free_scan()`), `GET /v1/audit/pending`, `POST /v1/scan/request` (manual scan re-run for testing). U10 extends with 3 commercial-flow endpoints. Combined ~150 LOC.
- Create `src/audit/stages.py:stage_free_scan(slug, url, form_data)`. Free AI Visibility Scan orchestrator: (a) invokes `cloro_tool.ai_visibility(brand, queries)` with queries derived from URL + form priorities (b) invokes `dataforseo_tool.serp_features(keywords)` narrow slice for AI Overview detection on ~10 queries (c) ONE Opus call with `prompts/free_scan_synthesis.md` that produces a 1-page branded note (title, 2–3 specific AI-search findings with numbers, a hook question for the sales call, CTA to the $1K full audit). Writes `clients/__scans__/<slug>/{scan.md, scan.json, scan.html}`. Uploads `scan.html` to R2 at `gofreddy-scans/<slug>/`. Sends the markdown via SMTP to the prospect's email; Slack-pings JR with scan summary + URL + copy-pasteable sales-call booking suggestion. ~100 LOC.
- Create `src/audit/prompts/free_scan_synthesis.md` (directive skeleton — role: AI-search analyst; objective: surface 2–3 specific AI-visibility findings with numbers + a hook; quality bar: specific, evidence-cited, non-generic; output contract: markdown with headline + findings + CTA).
- Extend `cloudflare-workers/audit-hosting/worker.js` to route `/scan/<slug>/*` paths to R2 bucket `gofreddy-scans/`, alongside existing `/<ulid>/*` routes for paid audits.
- Modify `src/api/main.py` to register the consolidated `audit_webhooks` router (R6: single registration, no per-endpoint router file imports)
- Create `supabase/migrations/20260420000001_audit_intake.sql` — `audit_pending` table
- Create `supabase/migrations/20260420000003_ai_visibility_scans.sql` — `ai_visibility_scans` table (`slug ulid primary key, email, company, url, scan_url, delivered_at, sales_call_booked_at nullable`)
- Extend `cli/freddy/commands/audit.py`:
  - `freddy audit scan --url <url> --email <email> [--company <name>]` — manual scan invocation (for JR dogfooding + demos)
  - `freddy audit scan --rerun --client <slug>` — re-runs a scan for an existing lead
- Extend `cli/freddy/commands/client.py`: add `freddy client new <slug> --from-pending <id>` flag so JR can populate a full paid-audit workspace from a Supabase lead row in one command (after payment clears)
- Extend `cli/freddy/commands/audit.py` with **nine conditional-enrichment attach subcommands** (per R18–R26). 7 of these 9 trim to ~20 LOC each — they validate input, write to state.json, store credential in OS keychain or .env, and flag `state.enrichments.<type>.attached=True`. The Stage-1 Sonnet pre-discovery agent and the relevant Stage-2 agent read the credential or uploaded file via Bash/WebFetch when the flag is set. **No vendor adapters, no parsing modules, no Stage-1 orchestrators** for the trimmed 7. Only `attach-assets` (PDF/PPTX text extraction can't be agent-WebFetched) and `attach-demo` (safety-critical Playwright) keep substantive Python:
  - `freddy audit attach-gsc --client <slug> --service-account-json <path>` (R18, ~30 LOC) — writes `clients/<slug>/audit/enrichments/gsc.json` (encrypted credential) and sets `state.enrichments.gsc = {attached: true, site_url, attached_at}`. The GSC tool (exposed as `mcp__audit__gsc_search_analytics`, included in the MCP server only when `state.enrichments.gsc.attached==True`) wraps existing `src/seo/providers/gsc.py` and is callable by Stage-1 pre-discovery + Stage-2 Findability/Conversion-Lifecycle agents at runtime — pulls clicks/impressions/CTR/position per page on demand, cache-backed.
  - `freddy audit attach-esp --client <slug> --vendor <klaviyo|mailchimp|customerio|hubspot|braze|iterable|activecampaign> --api-key <key>` (R19, ~20 LOC) —: validates vendor name + API-key format (lightweight ping per vendor), stores key in OS keychain (e.g., `keyring.set_password("gofreddy-audit", f"{slug}/esp/{vendor}", key)`), writes `state.enrichments.esp = {attached: true, vendor, attached_at}` (no key in state.json). **No vendor adapter modules**. The Conversion-Lifecycle agent prompt includes per-vendor URL patterns and auth header examples ("Klaviyo: GET `a.klaviyo.com/api/lists/` with `Authorization: Klaviyo-API-Key $key`; Mailchimp: GET `<dc>.api.mailchimp.com/3.0/lists` with Bearer $key; HubSpot: GET `api.hubapi.com/marketing/v3/marketing-events` with private-app token Bearer; ..."). Agent reads credential from keychain via Bash, uses `fetch_with_retry` to pull list size + growth + flow performance + deliverability + revenue-by-flow.
  - `freddy audit attach-ads --client <slug> --platform <google|meta|linkedin|tiktok> --oauth-token <token>` (R20, ~20 LOC) —: same shape as attach-esp — validates token + platform, stores in keychain, sets `state.enrichments.ads.<platform> = {attached, attached_at}`. **No vendor adapter modules**. The Distribution agent prompt includes per-platform URL patterns ("Google Ads: POST `googleads.googleapis.com/v17/customers/{cid}/googleAds:searchStream` with `developer-token` + `Authorization: Bearer $oauth`; Meta Marketing: GET `graph.facebook.com/v21.0/act_{ad_account}/insights` with `access_token=$oauth`; LinkedIn Ads: GET `api.linkedin.com/rest/adAnalytics` with `LinkedIn-Version` header; TikTok Ads: GET `business-api.tiktok.com/open_api/v1.3/report/integrated/get/` with `Access-Token` header"). Agent reads credential, fetches actual spend + impressions + CPC + conversion + ROAS at runtime.
  - `freddy audit attach-survey --client <slug> --file <path.csv|json> --type <nps|csat|churn|exit>` (R21, ~20 LOC) —: validates file exists + schema sniff, copies to `clients/<slug>/audit/enrichments/survey_<type>.<ext>` (gitignored), sets `state.enrichments.survey.<type> = {attached, file_path, row_count, attached_at}`. **No SURVEY_SYNTHESIS_PROMPT, no Opus orchestrator module**. The Monitoring/Conversion/Brand-Narrative agents detect the flag and read the file via Bash (`cat`, `python -c "import csv; ..."`) inline, code pain points + praise themes themselves, fold into their findings.
  - `freddy audit attach-assets --client <slug> --files <path1> <path2> ...` (R22, ~30 LOC + ~30 LOC `enrichments/assets.py`) —: keeps minimal Python helper — `enrichments/assets.py:extract_text(path) -> str` uses `pdfplumber` + `python-pptx` + `Pillow` to extract text/metadata from non-WebFetchable formats (agent can't curl a local PDF). CLI validates file existence, calls `extract_text` per file, writes `clients/<slug>/audit/enrichments/assets/<asset_id>.txt`, sets `state.enrichments.assets = {attached, asset_ids, attached_at}`. **No `audit_brand_visual_identity_internal` reasoning primitive module** — the Brand/Narrative agent reads the extracted text files via Bash, does cross-asset consistency audit (logo lockup mentions, color palette references, voice/tone vs website copy, value-prop alignment) inline using its existing tools.
  - `freddy audit attach-demo --client <slug> --url <demo-url> --username <user> --password <pass> [--readonly-mode true]` (R23) — captures demo-account credentials for Playwright-driven onboarding-flow audit. Writes `clients/<slug>/audit/enrichments/demo.json` (credentials encrypted at rest via OS-keychain or in-memory only — never plain-text in git-tracked state.json) and sets `state.enrichments.demo`. The CLI subcommand itself triggers the `enrichments/demo.py` orchestrator inline (NOT a Stage-1 hand-off — JR fires this after payment, runs alongside Stage 2 as an independent enrichment session, results land in the shared cache for Conversion-Lifecycle agent consumption). Orchestrator opens isolated Playwright browser context (`browser.new_context()` per audit run; cookies/storage destroyed after), logs in, time-stamps every page transition, captures accessibility-tree snapshots (preferred via Playwright MCP snapshot mode over screenshots for sensitive fields — no PII in API logs), walks likely TTFV path heuristically (detect biggest CTA, click, repeat 5x), at each major route captures (a) accessibility tree snapshot, (b) form field inventory, (c) help-overlay detection (Appcues/Pendo CSS), (d) empty-state markers, ships snapshot + thumbnail to Sonnet vision call for friction score per Wes Bush "Bowling Alley" / Hulick / EUREKA frameworks. **Critical safety pattern** (three-layer capability restriction — see "Safety via capability restriction" decision): scoped `ClaudeSDKClient` session built from `build_demo_flow_options()` in `src/audit/scoped_tools.py` — `permission_mode="default"` + `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` + `mcp_servers={"playwright_obs": build_playwright_obs_server()}` + `allowed_tools=["mcp__playwright_obs__page_goto","mcp__playwright_obs__page_screenshot","mcp__playwright_obs__locator_get_attribute","mcp__playwright_obs__accessibility_snapshot"]`. The destructive capability is positively absent from the allow-list AND the MCP-server tool surface AND the deny-list. Agent cannot execute destructive actions even under prompt-injection because the SDK has no path to those tools in this session. When agent identifies a form submission would measure flow, CLI prompts "Agent wants to submit form on <URL>. Approve? [y/N]" — per-action human confirmation, not pre-approved by flag. Disposable test fixtures used (`test+gofreddy@example.com`, "Test User", "555-0100") — never real PII. Hard limits: 15-min total timeout, `max_turns=400` sentinel. Pre-flight check on `robots.txt` + ToS clauses for automation prohibition — if prohibited, audit cannot run. Playwright trace saved to `clients/<slug>/audit/enrichments/demo-trace.zip` for JR audit-log review. Conversion lens findings pivot from "we detect a signup form" to "your TTFV is 8 min vs Linear's 90 sec; empty-state quality 30/100; missing in-product guidance entirely."
  - `freddy audit attach-budget --client <slug> --file <path.csv|json>` (R24, ~20 LOC) —: validates file + schema sniff (columns: channel, subcategory, monthly_usd, percent_of_marketing, notes), copies to `clients/<slug>/audit/enrichments/budget.<ext>` (gitignored if raw contains confidential numbers), sets `state.enrichments.budget = {attached, file_path, attached_at}`. **No `enrichments/budget.py` orchestrator module**. The MarTech-Attribution + Distribution agents detect the flag, read the file + `src/audit/data/budget_benchmarks.yaml` via Bash, compute the budget deltas inline: % of revenue, MarTech % vs 22.4% baseline (cross-reference `fingerprint_martech_stack` to flag bloat), paid-media % vs 30.6% baseline, 70/20/10 split, per-channel deviation from vertical median. Findings tier-mapped to Fix-it/Build-it/Run-it. **Vertical-aware caveat**: Gartner's 7.7% benchmark is enterprise-skewed; agent applies explicit caveat when prospect <$50M ARR.
  - `freddy audit attach-crm --client <slug> --source <hubspot|salesforce|pipedrive|close|attio|csv> --file <path>` (R25, ~20 LOC) — **v1: HubSpot CSV path primary**; Salesforce/Pipedrive/Close/Attio added in a v2 module if demand proves out.: validates file exists + source enum, copies to `clients/<slug>/audit/enrichments/crm/<source>.<ext>` (explicit `.gitignore` exclusion — CRM exports contain PII: contact names, emails, phone, ACV — raw never git-committed; only derived aggregate findings are git-committed via the agent's output). Sets `state.enrichments.crm = {attached, source, file_path, attached_at}`. **No `enrichments/crm/<vendor>.py` modules**. The Conversion-Lifecycle + MarTech-Attribution agents detect the flag, read the CSV via Bash (`python -c "import csv; ..."` or pandas inline), normalize to canonical Opportunity shape via a quick Sonnet column-mapping pass if needed (Salesforce custom fields are per-org wildly inconsistent), compute pipeline velocity (`opps × ACV × win_rate ÷ sales_cycle_days`), lead-to-opp + opp-to-close + sales-cycle median/p25/p75, MQL→SQL → close, lead-source ROI ranking, dead-lead recovery (no activity 60+ days). Reads `src/audit/data/crm_benchmarks.yaml` for benchmark comparisons. **Lead-source attribution caveat**: agent flags attribution-data-quality % up-front when `lead_source = Other / Web` dominates.
  - **Opt-in flag for `audit_welcome_email_signup` (P84)**: `freddy audit attach-welcome-email --client <slug> --opt-in` — **manual-fire opt-in only**, NEVER scheduled. When flag set AND `audit_plg_motion` detected free-trial/freemium: a scoped `ClaudeSDKClient` sub-session opens via `build_welcome_email_options()` from `src/audit/scoped_tools.py` — three-layer capability restriction (`permission_mode="default"` + `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` + `mcp_servers={"mailbox_obs": build_mailbox_obs_server()}` + `allowed_tools=["mcp__mailbox_obs__imap_poll","mcp__mailbox_obs__dns_lookup","mcp__mailbox_obs__sonnet_classify","mcp__mailbox_obs__submit_signup_form"]`). The `submit_signup_form` MCP tool wraps Playwright form-submit and rejects payment-field inputs at the wrapper level (Luhn check + payment-keyword regex); other Playwright operations (page.click on links, page.fill on arbitrary fields) are absent from the MCP server entirely. Single throwaway-email signup via Mailinator public inbox (or private Mailinator domain when `MAILINATOR_API_TOKEN` set at scale); captures welcome email for design + sender-reputation + CAN-SPAM + signature-fingerprinting audit. Orchestrator pre-conditions in `stages.py` enforce: `if not opt_in_flag: raise OptInRequired`; `if state.welcome_email_completed: raise AlreadyRun` (1-shot cap); `if not identifiable_fixture(email): raise FixtureValidation` (e.g., `gofreddy-audit-{audit_id}@mailinator.com` pattern). Per-form human confirmation at submit moment (CLI prompt, not pre-approved by the opt-in flag). Uncheck-marketing boxes defaulted by wrapper. Public-audit-log entry documenting the signup. Document explicitly in client engagement letter before running.
  - `freddy audit attach-winloss --client <slug> --files <path1> <path2> ...` (R26, ~20 LOC) —: validates files exist + extension matrix (PDF/MD/CSV/DOCX), copies to `clients/<slug>/audit/enrichments/winloss/<interview_id>.<ext>` (gitignored — interview transcripts contain PII: interviewee names, company names, deal sizes, competitive intelligence), sets `state.enrichments.winloss = {attached, file_paths, interview_count, attached_at}`. **No `enrichments/winloss.py` orchestrator, no embeddings + HDBSCAN clustering Python**. The Brand/Narrative + Competitive + Conversion-Lifecycle agents detect the flag, read the files via Bash (`pdfplumber` available as a CLI helper, `pandoc` for DOCX→markdown, `cat` for MD/CSV), classify won/lost/no_decision per interview inline, extract decision criteria + competitive mentions + pricing references + persona signals + verbatim quotes themselves, qualitatively cluster into themes via Sonnet (HDBSCAN over 5-20 transcripts is overkill — qualitative clustering by Sonnet on small datasets is methodologically equivalent and more defensible than k-means/HDBSCAN noise). Methodology baseline named in agent prompts: Klue 31-questions framework, Crayon, Primary Intelligence, Anova Consulting templates. **PII redaction is mandatory** — agent prompt instructs pre-output Sonnet pass redacts names + company names + deal sizes before findings ship in deliverable (per R12 PII hygiene). **Sample-size caveat**: agent always includes "with <10 interviews findings are directional only — statistical-confidence caveat applies" when interview_count < 10. **Open question for JR**: if "auditable methodology" becomes a sales talking point, flip this back to ACCEPT a `winloss.py` Python helper with deterministic embeddings + HDBSCAN — until then, qualitative Sonnet clustering ships.
- All nine attach commands validate credentials/files immediately (lightweight ping) before writing state; a failed validation exits with an actionable error and writes nothing (no dangling partial state).
- **Attach commands are idempotent**: running `freddy audit attach-<thing>` a second time overwrites the enrichment file and re-validates; no duplicate entries.
- **Conditional enrichments are ADDITIVE, never required**: Stage 1 always runs with whatever's available. Absence of any enrichment = no pipeline block, no error; the relevant lens just operates on public signals.
- Test: `tests/api/test_audit_webhooks.py` (R6: consolidated), `tests/audit/test_stages.py::test_stage_free_scan` (R6: scan merged into stages)

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

**Goal:** Full eval harness for iterating on directive prompts without shipping bad audits. Ships complete (runner + rubric + fixture_proxy + metrics) — R6's "defer fixture_proxy + metrics to v2" reversed under R7 cut-or-keep constraint because both carry lifetime value: fixture_proxy prevents accidental live-API billing during eval runs, and variance + gap-flag-honesty metrics add rigor the rubric scoring alone doesn't catch. Coverage metric is redundant with production `RubricCoverageIncomplete` path; kept anyway as belt-and-suspenders for eval-time regressions.

**Files:**
- Create `src/audit/eval/__init__.py`, `src/audit/eval/runner.py` (~120 LOC), `src/audit/eval/rubric.py` (~80 LOC), `src/audit/eval/fixture_proxy.py` (~100 LOC), `src/audit/eval/metrics.py` (~80 LOC), `src/audit/eval/fixtures/` (2-3 frozen dogfood prospects, each with `cache/` dir of frozen tool responses + `brief.md` + `agent_outputs/` golden expectations + `expected_rubrics.yaml`). Total ~380 LOC Python.
- Create `cli/freddy/commands/audit.py:eval` subcommand — `freddy audit eval [--stage N] [--fixture <slug>] [--baseline <run-id>] [--n-runs 5]` (~30 LOC).
- Create `src/audit/eval/rubric.md` — scoring rubric per stage (brief coherence · finding specificity · evidence density · surprise non-obviousness · proposal fit-to-findings). Markdown, not Python.
- Test: `tests/audit/test_eval_harness.py`, `tests/audit/test_eval_fixture_proxy.py`, `tests/audit/test_eval_metrics.py` (orchestration tests only per R7 testing philosophy — verify fixture_proxy raises FixtureMissing on cache miss, verify metrics compute correctly on synthetic inputs; NO LLM-output mocks).

**Approach:**
- Fixtures are per-prospect bundles under `src/audit/eval/fixtures/<slug>/`: (a) `cache/` dir with frozen JSON files for every tool-call signature the prospect's audit produces (initially seeded by running real audits in calibration mode and snapshotting the cache); (b) `brief.md` (golden Stage-1 output for Stage-2 prompt tuning); (c) `agent_outputs/<agent>/output.json` (golden Stage-2 output for Stage-3 tuning); (d) `expected_rubrics.yaml` listing the rubrics every Stage-2 agent must cover for this fixture (drives the coverage metric).
- `runner.py`: `run_eval(stage, fixtures, prompt_variant, n_runs=1) -> EvalReport`. For each fixture, runs the target stage N times with the candidate prompt set (n_runs>1 enables variance measurement); writes outputs to `clients/__eval__/<run-id>/<fixture>/`. Uses `fixture_proxy` to ensure frozen-cache-only behavior.
- `rubric.py`: per-stage Opus-as-judge scoring against `eval/rubric.md`. Returns `{fixture, stage, score_0_10, per_criterion_scores{}, reviewer_notes}`. Human-in-the-loop: JR can override or annotate.
- `fixture_proxy.py`: enforces frozen-cache-only responses during eval. Pattern: (a) `EVAL_MODE=1` env var inspected by `cli/scripts/fetch_api.sh` and the `@cached_tool` decorator — both raise `FixtureMissing` on cache miss instead of paying live; (b) PreToolUse hook installed for the eval-mode `ClaudeAgentOptions` rejects WebFetch/WebSearch calls whose URL is not present in the fixture's frozen cache manifest. Two-layer enforcement (env var for our own code paths + hook for SDK-builtin tools the agent reaches independently). Prevents eval runs from accidentally billing live DataForSEO/Cloro/SerpAPI/free-public-API surfaces during prompt iteration.
- `metrics.py`: computes finding-shape variance (pairwise Jaccard ≥0.80 target across N runs when `--n-runs >= 2`), rubric-coverage completeness against `expected_rubrics.yaml` per fixture (must equal 1.0), and gap-flag honesty (verifies that gap_flagged rubrics in AgentOutput correspond to an actual WebFetch/tool-call probe attempt in the session transcript — no "gap-flag without trying" regressions).
- Eval report: markdown table comparing candidate prompts vs. a named baseline. Highlights regressions vs wins on the rubric + variance + coverage + gap-flag-honesty dimensions.
- **This is telemetry for prompt development, not a gate.** Nothing in the eval harness is in the production audit path. Stage 3's `RubricCoverageIncomplete` validation IS in the production path (different system — Stage 3 enforces rubric_coverage completeness on every real audit, not just eval runs).
- When to re-run: before merging any prompt change in U4/U5/U6/U8; after Stage 1 output shape changes; monthly sanity check against fixtures.
- **First-5 calibration mode integration**: every paid audit's `cache/` dir is automatically promoted to `eval/fixtures/<slug>/cache/` after JR signs off the deliverable. Within the first 5 audits we'll have 5 high-quality fixtures.

**Test scenarios:**
- Happy: `freddy audit eval --stage 2 --fixture acme` runs all 7 Stage-2 agents against the acme fixture once; report shows per-rubric scores.
- Happy: rubric scoring on a known-good prompt yields ≥7/10; on a known-bad variant yields <5/10.
- Happy: baseline comparison table flags a regression when a prompt change drops rubric score by ≥1 point on any fixture.
- Happy: `--n-runs 5` triggers variance metric — pairwise Jaccard across N findings lists must be ≥0.80 for a passing prompt.
- Happy: coverage metric computes from `expected_rubrics.yaml` — must equal 1.0 for a passing prompt.
- Happy: gap-flag-honesty metric inspects session transcripts — a gap_flagged rubric without a matching probe attempt raises `HonestyViolation`.
- Edge: fixture missing brief.md → runner skips with clear error.
- Edge: cache miss during eval with fixture_proxy active → `FixtureMissing` raised (no live-API billing).
- Integration: a prompt tweak to `prompts/agent_findability.md` → run eval → diff report → JR accepts or rejects based on rubric delta + variance delta + sample reads.

**Done when:** `freddy audit eval --stage 2 --fixture <slug> [--n-runs 5]` produces a markdown diff report (per-rubric scores + baseline delta + variance + coverage + gap-flag-honesty) in under 15 min and is the default artifact JR reviews before merging any prompt-affecting PR.

---

### U10. Commercial flow: Stripe payment + sales/walkthrough calls

**Goal:** Wire the commercial plumbing between Stage 1 and Stage 2 (payment) and the two-call sales motion. JR sends a Stripe Checkout URL after the sales call; payment webhook flips `state.payment.paid`; Stripe webhook plus sales-call + walkthrough-call Fireflies webhooks all write into the audit workspace. No pipeline stage auto-fires — the webhooks only update state and ping JR on Slack.

**Files:**
- Create `src/audit/webhooks_helpers.py` — shared Stripe Checkout Session creation + Stripe webhook signature verify (uses `stripe` Python SDK) + Fireflies HMAC-SHA256 verify + Fireflies GraphQL transcript fetch + Slack-ping helpers (consolidates prior stripe.py + fireflies.py). ~120 LOC.
- Sales-call fit-signals extraction is a handler-local Opus call (~20 LOC inline) inside the `POST /v1/audit/sales-call` handler in `audit_webhooks.py`. `SalesFitSignals` Pydantic schema lives in `agent_models.py`. No standalone `sales_call.py` module.
- **Extend `src/api/routers/audit_webhooks.py`** with Stripe + sales-call + walkthrough endpoints: `POST /v1/audit/stripe` (Stripe webhook → `state.payment.paid = True` + Slack ping), `POST /v1/audit/sales-call` (Fireflies webhook for sales call), `POST /v1/audit/walkthrough` (Fireflies webhook for post-delivery walkthrough). No separate router files.
- (No `src/api/main.py` modification needed — `audit_webhooks` router was registered in U8; U10 only adds endpoint handlers to the existing router file.)
- Create `supabase/migrations/20260420000002_audit_payment.sql` — `payment_events` table (audit log of Stripe webhook events, idempotency dedupe)
- Extend `cli/freddy/commands/audit.py`:
  - `freddy audit send-invoice --client <slug> [--amount 1000] [--description "..."]` — creates a Stripe Checkout Session, writes URL + session_id to `state.payment.stripe_session_id`, prints URL for JR to copy/send
  - `freddy audit mark-paid --client <slug> --stripe-id <intent-id>` — manual fallback that sets `state.payment.paid = True` without waiting for webhook (for test/dev or if webhook fails)
  - `freddy audit ingest-transcript --client <slug> --call-type {sales,walkthrough} --file <path>` — manual fallback if either Fireflies webhook fails
- Create `src/audit/prompts/fit_signals.md` — single shared markdown template with section per call-type (sales-call extraction criteria + walkthrough-call extraction criteria + shared directive skeleton + output contract). Loaded via `prompts.load_prompt("fit_signals", call_type=<sales|walkthrough>)`.
- Add `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `FIREFLIES_WEBHOOK_SECRET` to env-required list
- Test: `tests/audit/test_webhooks_helpers.py` (Stripe Checkout creation + webhook signature verify + Fireflies HMAC + transcript fetch) and `tests/api/test_audit_webhooks.py` (routers + payment-gate behavior + inline sales-call fit-signals extraction). No standalone `test_sales_call.py` or `test_fireflies.py`.

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

**9 audit-level reference files** at `src/audit/references/`. Reconcile vs existing files at `autoresearch/archive/v006/programs/references/` — pick more current, redirect or merge, never keep duplicates. The reference files carry **proprietary/recent benchmarks + vendor inventories + methodology decisions + cross-audit classification dictionaries** — content the agent cannot reliably reproduce across audits. Framework explainers the agent already encodes in its inline rubric checklist are deleted.

| File | Purpose |
|---|---|
| `stats-library.md` | Cross-cutting citations (Princeton KDD 2024, SE Ranking, ZipTie, Core Web Vitals, form-field tradeoff, churn split) used across every agent |
| `findability-agent-references.md` | SEO + GEO: backlink-interpretation thresholds, Core Web Vitals pass/improve/fail bands, Cloro positional-metric reading, EEAT interpretation, AI-crawler strategic posture, crawl-budget thresholds, AI Overview citation reading |
| `competitive-agent-references.md` | Backlink-gap + keyword-gap prioritization framework, SERP-feature opportunity scoring, Gartner MQ/Forrester Wave/G2 Grid tier reading |
| `monitoring-agent-references.md` | NewsData source_priority tier reading, Xpoz inauthenticity scoring, Google Trends breakout detection, branded-SERP defensive-perimeter grading, Reddit AMA + brand-subreddit maturity |
| `conversion-lifecycle-agent-references.md` | Core Web Vitals → conversion benchmarks, Klaviyo 2026 welcome-series thresholds, Omnisend flow standards, TCPA SMS compliance checklist, DMARC grading rubric, popup-timing by vertical, loyalty/referral/subscribe benchmarks, Trust Center enterprise-sales-cycle signal, capture-UX maturity bands |
| `voc-source-playbooks.md` | Customer research Mode 2 + confidence labels + product-marketing-context schema |
| `distribution-agent-references.md` | Paid-creative hook taxonomy, offer patterns, channel-native-fit rubric, UGC-vs-produced benchmarks by vertical, podcast/YouTube cadence benchmarks, influencer tier definitions, directory/marketplace listing tiers, mobile-app linking maturity + dead-FDL remediation flag |
| `martech-attribution-agent-references.md` | Consent Mode v2 signal reading, sGTM maturity tiers, UTM scoring rubric, 20+ vendor category definitions, accessibility-overlay red-flag context, dormant-pixel thresholds, vertical-compliance interpretation, sub-processor/DPA reading |
| `brand-narrative-agent-references.md` | Dunford 5-component rubric, cross-surface coherence scoring, pub-tier classification model, GDELT tone heuristics, content-pillar cluster-balance thresholds, proprietary-research benchmarks, conference-tier list per vertical, Wikipedia reference-quality rubric, pay-transparency jurisdictional compliance, Gartner MQ Leader close-rate effect |

Excluded (no audit value): cold-email, community-marketing, referral-program, marketing-ideas as standalone, and 4 other low-value Corey skills.

**Reference-file scope discipline:** every reference file carries what the agent cannot reliably reproduce across audits — proprietary benchmarks, specific vendor inventories, methodology decisions we've made (severity-cap policies, gap-flag honesty rules), cross-audit-consistent classification dictionaries (pub-tier, conference rosters). **Does NOT carry** training-grade framework recaps the agent already encodes in its inline rubric checklist — e.g., a RACE framework paragraph when the rubric already lists the specific RACE-derived evaluation questions is redundant and deleted. ~200 LOC trimmed across 9 reference files under this discipline. When in doubt: if the content is referenced by an inline rubric-question in the agent prompt, it belongs in the reference file; if it's a framework explainer with no consuming rubric, it's training-data duplication and deleted.

## Manual review gates (intake, payment, calibration)

Three permanent gates + calibration training wheels for first 5 audits. Detailed behaviors are in R8 (Requirements), the Architecture stage flow, and U10's payment-gate spec.

- **Gate 1: Intake review** — after Stage 1, JR reads `brief.md` and decides whether to pursue. JR can add `clients/<slug>/audit/intake/operator_notes.md` for downstream Stage-2 agents.
- **Gate 2: Payment** — Stripe webhook sets `state.payment.paid=True`; Stage 2 raises `PaymentRequired` until this flag is True. Financial gate, not editorial.
- **Gate 3: Final publish** — Stage 5 renders files locally; JR reviews then runs `freddy audit publish`.
- **Calibration gates (first 5 audits, temporary)** — `state.calibration_mode` prompts for approval after every stage; auto-flips off after 5 published audits.

## Agent observability & safety

This section codifies the hooks, telemetry, and recovery mechanisms that replace cost/turn gates. Referenced by U1 (state), U3–U8 (agent sessions), and the Risks section.

**Hook contracts (all live in `src/audit/hooks.py`):**
- `PostToolUse` — for every tool call: (a) append `{timestamp, agent_role, session_id, tool_name, tool_input_hash, tool_output_summary, cumulative_turns, cumulative_cost_usd, critique_iterations_used}` row to `clients/<slug>/audit/cost_log.jsonl`; (b) maintain a rolling ring of recent `(tool_name, tool_input)` hashes per session — if the same hash appears 5× consecutively, Slack-ping JR with `{slug, agent_role, session_id, loop_signature}`; **never abort**; (c) **per-agent token-spend alert**: maintain rolling median of completed-agent total_cost_usd per agent_role; if current session's cumulative_cost_usd crosses 3× rolling median (min 5 historical points before alerting), Slack-ping JR with `{slug, agent_role, current_cost, rolling_median, multiplier}`; observation only, no abort. Claude receives nothing from the hook on the happy path.
- `PreCompact` — before the SDK auto-compacts older history, archive the full pre-compaction transcript to `clients/<slug>/audit/<stage>/transcripts/<agent_role>-<session_id>-<ts>.jsonl` so the original reasoning trace is preserved for post-hoc review.
- `Stop` — on `ResultMessage` arrival, flush final telemetry (`total_cost_usd, duration_ms, num_turns, model_usage, stop_reason`) to `cost_log.jsonl` and call `state.record_session(role, result_message)`.
- `PreToolUse` — no URL-blocklist safety hooks wired. URL blocklists are infinitely bypassable (URL encoding, case variations, nested paths, query params); blocking clicks doesn't help when WebFetch can hit the same URL. Safety lives in capability restriction (`scoped_tools.py`) + orchestrator pre-conditions (Python, before primitive invocation: `if not opt_in_flag: raise OptInRequired` etc.) + per-action human confirmation for irrecoverable operations + engagement-letter disclosure. `PreToolUse` is reserved for future soft guardrails (e.g., WebFetch domain allowlist) but carries zero safety load on Day 1.

**Telemetry schema (`cost_log.jsonl`):** one JSON object per line. Shared fields: `{ts, slug, agent_role, session_id, event_type}` where `event_type ∈ {tool_use, tool_result, result_message, hook_alert, anomaly}`. Per-event fields vary. Log is append-only; rotated per-audit (lives under the audit workspace, not global).

**Cost anomaly alert:** `telemetry.compute_anomaly(slug)` runs on `Stop` for the root audit. If `total_cost_usd` of the finished audit exceeds `p95(recent_audits) + 3 × σ(recent_audits)` (rolling over the last 20 audits), Slack-ping JR with the outlier's cost_log summary. Observation only — no gate, no rollback.

**Sentinel `max_turns`:** every `ClaudeSDKClient` runs with `max_turns=500`. This is **not a budget**; normal agents complete in 15–60 turns. 500 exists solely as a runaway-infinite-loop backstop — if it fires, a prompt or tool is genuinely broken and JR should know. If it ever fires in practice, raise the sentinel, don't lower it.

**Session resumability:** every Claude Agent SDK invocation sets `enable_file_checkpointing=True`. Standard-pipeline sessions use `permission_mode="bypassPermissions"` for unattended roaming; the 3 safety-bounded scoped sessions (welcome_email_signup, hiring_funnel_ux, attach-demo) use `permission_mode="default"` instead — see "Safety via capability restriction" decision. On first `ResultMessage`, `session_id` is persisted via `state.record_session(role, result)`. Recovery scope: a crash AFTER the first `ResultMessage` resumes cleanly with `ClaudeSDKClient(resume=state.sessions[role].session_id)`; a crash BEFORE first `ResultMessage` (no `session_id` persisted) restarts that session from scratch — earlier stages are already git-committed so nothing upstream is lost. `freddy audit run --resume` picks up whichever stage/role last wrote a session.

**What we deliberately don't do:**
- No turn cap that constrains normal cognition (sentinel-only; 500 is not a budget).
- No cost gate that blocks execution — only alerts.
- No auto-abort on output quality (prompts encode quality bars; JR reviews via the Stage 1 → Stage 2 gate and calibration gates).
- No auto-override of agent output — the evaluator-optimizer critique in Stage 3 is passed back to the agent, never forced.

**Testing philosophy:** orchestration tests earn their weight; LLM-output mock tests do not. **Write:** does `stage_2_agents` fan out 7 ClaudeSDKClient sessions via the semaphore; does `stage_3_synthesis` raise `RubricCoverageIncomplete` when an `AgentOutput.rubric_coverage` key is missing; does `agent_runner.run_agent` terminate at `critique_iterations_used ≤ 3`; does `POST /v1/audit/stripe` dedupe by `event_id`; does `capability_registry.pick_pricing` clamp to `price_range`; does `tools/cache.py` TTL-expire at 24h; does the Stage-1 payment gate raise `PaymentRequired`. **Don't write:** tests that assert the agent produced 5 findings at severity 2, or that mock the Sonnet call and assert on `output.findings[0].title` — these test mocks not behavior, break on every prompt tweak, and give false confidence. Quality-of-findings regressions are caught by the eval harness + calibration mode, not unit tests. ~800 LOC of LLM-output mock tests cut under this discipline.

## Risks flagged inline

- Claude Agent SDK parallel-session limits: fall back to sequential Stage 2 execution if hit (adds 1–2h wall-clock; correctness preserved).
- **Cache staleness producing wrong findings**: cache TTL is 24h; if a cached DataForSEO rank snapshot is 23h old and the prospect just published 50 new pages, the agent reads stale data and misses signals. Mitigation: (a) 24h TTL is short enough for ~weekly-cadence audits; (b) agent prompts instruct "if a finding seems implausible vs prospect's recent activity, retry with `force=True`"; (c) per-tool TTL override available (monitoring_tool.voc TTL 6h since mention velocity moves fast); (d) cache files include `ts` field so post-hoc diagnosis can identify staleness as cause.
- **Coverage-consistency loss as code-burden shifts to prompts**: with 68 wrapper functions deleted, agent prompts must encode rubric checklists rigorously. Risk: prompt drift over time leaves rubrics silently uncovered. Mitigation: (a) `AgentOutput.rubric_coverage` map enforced by Stage 3 — missing rubric raises `RubricCoverageIncomplete`; (b) eval harness coverage metric (must equal 1.0) catches regressions before merge; (c) `gap_report.md` surfaced at publish gate forces JR review of any audit with high gap counts.
- **Agent token-spend explosion**: agents do WebFetch + Bash + analysis at runtime instead of consuming pre-computed JSON. Per-audit token cost may be 2-5× pre-R5. Mitigation: (a) PostToolUse hook tracks per-agent token spend vs rolling median; 3× alert Slack-pings JR for triage; (b) cache-backed tools mean repeat owned-provider calls are free; (c) calibration mode (R8) surfaces total cost per audit to JR; (d) `max_turns=500` sentinel (Stage 2) / 600 (Stage 1 brief) catches runaways.
- **Auth/rate-limit/pagination drift in agent prompts**: each agent prompt must carry per-API auth/pace/pagination blocks. Risk: agent fails to follow polite-pace, gets 429'd, fails silently. Mitigation: (a) `cli/scripts/fetch_api.sh` shell helper enforces backoff in one place — agent prompts instruct usage; (b) ToolError envelope returned by tool handlers on retry-exhaustion, agent prompted to retry-with-force then gap_flag; (c) eval-harness gap-flag-honesty metric verifies the agent actually probed the URL before declaring gap.
- **Finding-depth variance**: 6-required-fields Finding schema (vs 13-required) lowers the floor — agent can produce thin findings unless critique loop catches them. Mitigation: (a) per-agent critique loop (≤3 iterations) explicitly rejects findings with weak evidence_urls or <50-word substance; (b) eval harness rubric scores penalize finding-shape variance; (c) Stage 3 synthesis_master prompt prompts Opus to reject thin findings during section narration.
- **Silent error swallowing via tool errors**: tool handler returns ToolError → agent reads error → if agent forgets to retry, audit ships with gap. Mitigation: ToolError pattern + agent prompt explicit instruction "on ToolError, retry once with `force=True`; if still error, emit a gap_flag Finding with diagnostic" — turns silent failure into explicit gap-flag (visible in `gap_report.md`).
- **Sonnet pre-discovery agent rabbit-holing**: single Sonnet session for Stage 1 brief may spend disproportionate turns on one prospect surface. Mitigation: (a) `max_turns=600` sentinel; (b) PostToolUse loop-detect (5× consecutive identical tool call → Slack); (c) per-agent token-spend alert (3× rolling median); (d) `gaps.jsonl` exposes what the agent tried-and-failed vs. what it never tried (spotting bias).
- **Prompt-engineering burden as the load-bearing quality investment**: code is reduced ~70% but prompt complexity rises (rubric checklists + auth/pace blocks + critique-loop instructions + URL patterns). Risk: lazy prompts produce poor audits. Mitigation: (a) calibration mode for first 5 audits — JR reviews every artifact; (b) eval harness scoring required before merging any prompt change; (c) prompts written iteratively with eval feedback, not in one pass.
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
- **YouTube Data API quota** (10K units/day): `audit_youtube_channel` uses ~5–20 units per prospect — plenty of headroom for ~500 audits/day. If we ever hit it, primitive returns `partial=true` and the Distribution lens narrates around the gap. No code change needed day-1.
- **Foreplay credit exhaustion on high-volume days**: existing circuit breaker + daily_credit_limit tracking in `src/competitive/providers/foreplay.py` already logs warnings at 50% / 20% / 5% remaining. No new risk; operational-only.
- **7-agent Stage 2 parallelism**: 7 concurrent `ClaudeSDKClient` sessions may exceed Anthropic's practical parallel-session limits depending on plan tier. Fallback: `Semaphore(4)` + second wave (correctness preserved, ~40% wall-clock increase).
- **Lifecycle-lens flow-observation scope creep**: the MVP Lifecycle lens deliberately skips welcome / cart / winback flow observation (requires 10–14 day subscribe-and-observe window; breaks 3-day SLA). Risk: prospects expect flow audit. Mitigation: Lifecycle-lens findings explicitly caveat "this audit cannot observe open/click/CVR without ESP access" + walkthrough-call pitches the supplemental 2-week flow report as an add-on. If prospects consistently want flows, build the async observation pipeline in a v2 plan.
- **Burner-inbox infra for future flow-audit work** (deferred v2): if/when flow observation is added, burner-domain infra + mailbox parsing needs a dedicated design pass. Not a v1 risk.
- **DNS-based martech detection false positives**: CNAME heuristics for Segment/Rudderstack/Snowplow occasionally flag non-CDP subdomains. Mitigation: confidence score on every fingerprint entry; lens narrates "low-confidence" detections as "possibly" rather than "confirmed." Zero-downside since the miss is additive, not subtractive.
- **SerpAPI quota exhaustion** on `audit_earned_media_footprint` + `audit_executive_visibility`: entry tier is ~$50/mo for ~5K searches. At 20 audits/mo with ~40 searches per audit (10 per primitive × 2 primitives × 2 execs avg), we're at ~16K searches/mo — needs a $130/mo tier. Budget explicitly; cost warranted given Brand/Narrative is the lens category with the highest-margin engagement mappings.
- **Pub-tier dictionary maintenance**: `pub_tier_dict.yaml` starts with ~200 entries across 10 verticals but rots — trade-pub M&A changes tier positioning. Mitigation: quarterly review flagged in `docs/plans/README.md`; flag low-confidence pub classifications in agent output ("classification uncertain — review manually").
- **Brand/Narrative false "inconsistency" findings**: `audit_messaging_consistency` may flag intentional positioning variation (e.g., enterprise landing-page positions differently than SMB pricing page) as drift. Mitigation: coherence score thresholds tuned on first 5 audits; intentional-variant-vs-drift signal requires Opus synthesis pass not just rubric comparison.
- **Wayback Machine CDX coverage gaps**: for young domains (<1 year) or ones with robots.txt blocking the Wayback crawler, tagline-evolution series will be sparse. Mitigation: primitive returns `partial=true` with available snapshots; lens narrates "insufficient history for tagline drift analysis."
- **Conditional-enrichment adoption rate**: R18–R26 only fire if prospects grant access on the sales call. Unknown empirically; likely 30–60% for R18 GSC (low-friction), 20–40% for R19 ESP (requires API key copy-paste), 10–25% for R20 ad platforms (OAuth friction), 10–20% for R21 surveys, 20–40% for R22 sales deck uploads, 15–30% for R23 demo accounts (sales-friction), 30–50% for R24 budget upload (CSV format-friendly), 25–45% for R25 CRM CSV upload (HubSpot CSV path is low-friction; OAuth higher), 10–15% for R26 win-loss transcripts (rare even at scale; companies running win-loss programs are themselves a maturity signal). The audit remains valuable at 0% adoption; each granted enrichment is additive. Track adoption rate per enrichment type after first 20 audits to tune sales-call pitch.
- **Per-vendor URL pattern drift in `prompts/reference/fetch-api-patterns.md`**: ESP and ad-platform APIs evolve; URL patterns + auth headers in the shared prompt reference can rot. Mitigation: agent gap-flags any vendor returning 4xx with diagnostic (JR sees at publish gate); integration test exercises one happy-path call per vendor against sandbox APIs; low-adoption vendors (per calibration tracking) deprecated from prompt reference after 12 months of <2 audits.
- **Client-asset upload (R22) — PII / confidential-asset handling**: sales decks may contain pricing, customer logos under NDA, roadmap slides. Mitigation: `enrichments/assets/` storage is per-client-workspace only (not global); `freddy audit detach-assets --client <slug>` wipes the parsed corpus + original files; retention mirrors main audit (R11: 90 days active / 1 year archived / then deleted). Document this explicitly in the sales-call prompt ("we'll delete the deck after audit delivery; nothing leaves your workspace").
- **R23 attach-demo safety surface**: demo-account audits are the most novel safety risk in the plan. Direct-to-demo automation could plausibly trigger destructive actions, leak PII, or violate prospect ToS. **Mitigation stack** (codified in U8 attach-demo CLI + `src/audit/scoped_tools.py:build_demo_flow_options()`): (1) **Three-layer capability restriction** (primary) — `permission_mode="default"` (NOT bypass) + `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` + `mcp_servers={"playwright_obs": build_playwright_obs_server()}` + `allowed_tools=["mcp__playwright_obs__page_goto","mcp__playwright_obs__page_screenshot","mcp__playwright_obs__locator_get_attribute","mcp__playwright_obs__accessibility_snapshot"]`. The destructive capability (page.click, page.fill, page.evaluate, Bash, WebFetch) is positively absent from the allow-list AND the MCP-server tool surface AND the deny-list — three reinforcing controls. Companion regression tests in `tests/audit/scoped_tools/test_safety_invariants.py` assert each blocked operation raises at SDK level under a hostile-agent harness. (2) **Orchestrator pre-conditions** — `attach-demo` CLI validates opt-in flag + readonly-mode flag + credential-encryption before invoking; raises before primitive runs if any invariant violated. (3) **Per-form human confirmation** — if the agent identifies a form submission is needed (e.g., to measure 2-step onboarding flow), CLI prompts JR: "Agent wants to submit form on /onboarding. Approve? [y/N]". Not pre-approved by flag. (4) **Isolated Playwright browser context** per run (disposable test fixtures only, never real PII; context discarded post-audit). (5) **Pre-flight ToS check** on robots.txt + automation clauses. (6) **Playwright trace recording** for post-hoc audit. (7) **Hard 15-min timeout** as Playwright session limit. (8) **OS-keychain credential storage** — never plain-text in git-tracked state.json. (9) **Engagement letter disclosure** — prospect signs explicit authorization that includes demo flow audit scope. Demo audit cannot replace real-user-behavior data (TTFV measured here is one persona × one path; cohort data needs Mixpanel/Amplitude — engagement-scope).
- **R25 attach-crm PII handling**: CRM exports contain contact names, emails, phone, ACV, deal close dates. Storage under `clients/<slug>/audit/enrichments/crm/` with explicit `.gitignore` exclusion — only derived aggregate findings ever git-committed. `freddy audit detach-crm --client <slug>` wipes raw exports. Document explicitly in sales-call prompt.
- **R26 attach-winloss PII redaction**: win-loss interview transcripts contain interviewee names + company names + deal sizes + competitive intelligence. Mandatory pre-output Sonnet redaction pass before findings ship in deliverable (per R12). Sample-size caveat: <10 interviews = directional only, must include statistical-confidence note.
- **Glassdoor scraping reliability** (Tier-2 enrichment in `scrape_careers`): Bright Data Cloudflare bypass achieves 70-80% success rate in independent benchmarks — not 100%. Budget for failure; degrade gracefully when scrape fails. Glassdoor consolidated into Indeed July 2025 (Recruit Holdings) — API permanently dead, scraping is the only path. Cost $0.10–0.50/audit only justified for >$10M revenue prospects. **Pay-transparency compliance** (CA/NY/CO/WA jurisdictional) is the load-bearing finding from `scrape_careers` and comes from FREE ATS APIs (Greenhouse/Lever/Ashby/Workable) — Glassdoor is additive, not essential.
- **LinkedIn data quality limited honesty**: LinkedIn aggressive bot-blocking (TLS fingerprinting, behavioral detection, real-time fraud scoring as of April 2026) means full-employee enumeration costs $4-$8/1K via Apify and gets rate-limited on retry. Default Tier-1: company-page metadata only via Apify (~$0.05/audit). Mark `linkedin_data_quality: "limited"` in output — do not pretend to have data. hiQ Labs v. LinkedIn settled the legality of public-data scraping in the US, but technical feasibility is the constraint.
- **G2 / Capterra bot-blocking** (Cloudflare + DataDome): direct scraping fails. Use DataForSEO `serp_site_query` for presence-detection only; accept "presence yes / quality unknown" disclaimer in `audit_directory_presence` output. Listing-quality enrichment (review count, claimed status) requires paid Apify actors with bypass infra (`alizarin_refrigerator-owner/g2-scraper`) at variable reliability — defer to Phase 2 if Quality data becomes load-bearing.
- **Wikipedia ORES deprecated Jan 2025**: must use Lift Wing API endpoints (`api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict` + `references:predict`) — old ORES URLs return 404. Free tier requires `WIKIMEDIA_API_KEY` signup. ~70% of B2B SaaS prospects have no Wikipedia article — `wikipedia.present=false` is the modal outcome; surface honestly as a finding rather than an error.
- **`textstat` PyPI maintenance status**: package flagged "Inactive" by Snyk April 2026 (no PyPI release in 12+ months). Pin `textstat==0.7.4` and document `py-readability-metrics>=1.5.0` as fallback path. Quarterly review — swap if textstat goes fully unmaintained or breaks on Python 3.13+.
- **`python-Wappalyzer` (chorsley fork) unmaintained**: swap to `wappalyzer-next` (s0md3v fork, last update Jan 2026). Existing detection logic mostly compatible; verify regex ruleset against new fingerprint format at integration-test time.
- **SecurityHeaders.com sunset April 2026** (Snyk acquisition): do NOT integrate. Use Mozilla HTTP Observatory v2 (`https://observatory-api.mdn.mozilla.net/api/v2/scan`, free, no auth, 1 scan/host/min cooldown) as primary. APIVoid Security Headers ($0.005/check) only as fallback if Mozilla rate-limit becomes a bottleneck after first 5 audits — defer.
- **Conditional firmographic primitive trigger accuracy**: ~16 conditional primitives across R1+R2 (`audit_aso`, `audit_local_seo`, `audit_oss_footprint`, `audit_abm_signals`, `audit_plg_motion`, `audit_devex`, `audit_international_seo`, `audit_corporate_responsibility`, `audit_vertical_compliance`, `audit_ecommerce_catalog`, `audit_b2c_personalization`, `audit_mobile_app_linking`, `audit_public_company_ir`, `audit_huggingface_presence`, `audit_hiring_funnel_ux`, `audit_welcome_email_signup`) depend on accurate firmographic classification from `scrape_firmographics`. Misclassification → primitive runs when irrelevant (audit-spam findings) or skips when applicable (missed coverage). Mitigation: trigger gates are based on multiple signals, not single fields (e.g., `audit_local_seo` requires `business_type ∈ local_categories` OR `<address>` block OR `>2` location pages; `audit_huggingface_presence` requires firmographic AI flag OR HF mention in JD/site OR detected ML signal in tech_stack); calibration after first 5 audits to tune thresholds.
- **Audit-coverage research expansion cost increase**: worst-case +$1.00–2.00/audit incremental when all R2 expansion primitives + ~24 deepening extensions trigger (most items <$0.05; biggest spenders: brand demand trend $0.14, original research depth $0.13, welcome-email signup $0.10); +$3–8 with R23 demo + R26 winloss enrichments. Within R7 envelope but worth tracking — telemetry alerts via existing 3σ-above-p95 anomaly detection.
- **GitHub PAT rate limit** (`audit_oss_footprint` + `audit_devex` + `audit_launch_cadence` + `audit_free_tools` all share `GITHUB_TOKEN`): 5K req/hr authed. At 20 audits/mo × ~30 calls/audit total = 600/month — well inside 5K/hr. No concern at this volume.
- **Product Hunt commercial-use gray area**: PH API "no commercial use without contacting them" clause. For a $1K paid audit running ~20×/month this is gray-area but low-risk. **Action item**: email `hello@producthunt.com` for written approval before launch.
- **Pay-transparency compliance findings exposure**: `scrape_careers` flagging "Acme posts 40 CA roles without salary ranges = $400K legal exposure" is a publishable finding but also **directly actionable legal advice for the prospect**. Frame in deliverable as "potential exposure per state AG guidance" not "you owe $400K in fines"; recommend prospect consult employment counsel for compliance interpretation.
- **Wikipedia title disambiguation false matches**: brand-name → Wikipedia title resolution can match the wrong "Notion" (company vs music software vs philosophical concept). Mitigation: verify infobox `industry` field matches firmographic vertical before claiming match.
- **Funnel content shape vs velocity claim discipline**: `audit_funnel_content_shape` (renamed from velocity_proxies per research) is severity-cap=low and surfaces `_caveat` per-finding. Risk that downstream synthesis (Stage 3) lifts findings from this primitive into velocity claims. Mitigation: Stage 3 `prompts/synthesis_master.md` explicitly excludes `audit_funnel_content_shape` from velocity-language permissions (e.g., "your funnel converts X%"); allowed framing is descriptive only ("your content portfolio is TOFU-heavy with no BOFU assets").
- **`audit_welcome_email_signup` (P84) — most novel safety surface in plan**: signup with disposable email may breach prospect ToS (CFAA "exceeding authorized access" risk); ~50-60% signup success rate due to disposable-email blocklists (Mailinator/Maildrop/GuerrillaMail domains); captured PII potentially world-readable on public Mailinator inboxes. **Mitigation stack** (codified in U2 P84 spec + `src/audit/scoped_tools.py:build_welcome_email_options()` + orchestrator pre-conditions in `src/audit/stages.py`): (1) **Three-layer capability restriction** (primary) — `permission_mode="default"` + `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` + `mcp_servers={"mailbox_obs": build_mailbox_obs_server()}` + `allowed_tools=["mcp__mailbox_obs__imap_poll","mcp__mailbox_obs__dns_lookup","mcp__mailbox_obs__sonnet_classify","mcp__mailbox_obs__submit_signup_form"]`. Only IMAP-read + DNS-lookup + Sonnet-classify + the narrow `submit_signup_form` wrapper (which rejects payment-field inputs via Luhn check + payment-keyword regex) are reachable. WebFetch (can't click email links), `page.click`/`page.fill` on arbitrary pages, Bash — all positively absent from the allow-list AND the MCP-server tool surface AND the deny-list. (2) **Orchestrator pre-conditions** (Python, before invocation): `if not opt_in_flag: raise OptInRequired`; `if state.welcome_email_completed: raise AlreadyRun` (1-shot cap); `if not identifiable_fixture(email): raise FixtureValidation` (ensures `gofreddy-audit-{id}@mailinator.com` pattern). Cannot be bypassed because alternate tools aren't reachable in this scoped session. (3) **Manual-fire only** — NEVER scheduled; JR runs `freddy audit attach-welcome-email --client <slug> --opt-in` explicitly. (4) **Human confirmation at signup send** — CLI prompts "Agent prepared signup form for <domain>. Submit? [y/N]" before `submit_signup_form` invocation. (5) Engagement letter disclosure that audit may include single test signup. (6) Private Mailinator domain ($99/mo) at scale (>10 audits/month) to eliminate public-exposure risk + bypass disposable-email blocklists.
- **`audit_hiring_funnel_ux` (P86) — fraud risk if form submitted**: rendering application page is fine; submitting application form constitutes fraudulent job application. **Mitigation**: three-layer capability restriction via `build_hiring_funnel_options()` from `src/audit/scoped_tools.py` — `permission_mode="default"` + `disallowed_tools=["Bash","WebFetch","WebSearch","Write","Edit","Task"]` + `mcp_servers={"playwright_obs": build_playwright_obs_server(), "ats_obs": build_ats_obs_server()}` + `allowed_tools=["mcp__playwright_obs__page_goto","mcp__playwright_obs__locator_get_attribute","mcp__playwright_obs__accessibility_snapshot","mcp__playwright_obs__axe_audit","mcp__ats_obs__greenhouse_jobs","mcp__ats_obs__lever_jobs","mcp__ats_obs__ashby_jobs","mcp__ats_obs__workable_jobs"]`. `page.click`, `page.fill`, `form.submit()` are positively absent from the allow-list AND the MCP-server tool surface AND the deny-list. Render-only DOM inspection via `_deep_inspect_forms()` from P23 provides the field-structure analysis without needing submit capability.
- **`audit_error_page_ux` (P80) — WAF rate-trigger risk**: deliberate fetch of unknown paths can trip WAF rules. Mitigation: 2 probes max, randomized paths (`/__gofreddy-audit-{uuid}-404test`), 10s spaced apart, never `/admin`/`/wp-admin`/`/.env` patterns. Cloudflare challenge pages (1020/1015) distinguished by `cf-ray` header — flagged separately from genuine 4xx.
- **Firebase Dynamic Links DEAD as of 2025-08-25**: `audit_mobile_app_linking` flags `*.page.link` references as broken-FDL active outage requiring migration to Branch.io / Adjust / AppsFlyer OneLink. Risk: prospects may have deeplinks-on-page that fail silently — surface as URGENT severity finding, not info-only.
- **Reddit free unauthenticated API formally degraded 2026**: `audit_reddit_ama_brand_subreddit` requires `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` env vars (free OAuth client-credentials tier sufficient at ~20 audits/month). When env vars missing: returns `{partial: true, degraded_reason: "REDDIT_CLIENT_ID/SECRET env vars not set"}` rather than silent skip. One-time ~30min app setup at `reddit.com/prefs/apps`.
- **ProgrammableWeb dropped (dead since 2022 Mulesoft consolidation)** + **RapidAPI declining post-Nokia 2024 acquisition**: `audit_open_api_public_data_access` treats RapidAPI as historical-only signal; ProgrammableWeb removed from scope.
- **`audit_industry_analyst_position` (P58) — Gartner/Forrester direct paywalled**: full analyst-report data behind paywalls. Mitigation: triangulate via brand's own marketing pages declaring "Gartner MQ Leader 2024" + SerpAPI brand-name + analyst-firm queries + cached awards lookup. Self-promoted analyst-position via marketing pages is HIGH-confidence signal even without paid access. G2 quadrant detail Cloudflare-blocked (MEDIUM confidence) — accept presence-only when blocked.
- **`audit_email_signature_marketing_indicators` (P79) — invisible by design**: tools install at email-client/Exchange/Gmail-tenant level, not website. Most prospects with these tools leave ZERO web-visible traces. **Emit finding only when ≥2 weak signals concur** (else silent). Best detection via welcome-email signature fingerprinting cross-feed from P84.
- **Cloudflare/DataDome bot defenses on G2/Capterra/Glassdoor**: presence detection works via DataForSEO `serp_site_query`, but listing-quality data requires paid Apify actors with bypass infra (variable reliability). Cost-quality tradeoff documented per primitive.
- **DataForSEO SERP `local_pack` cost** scales with conditional `audit_local_seo` (~5 queries × $0.002 per local-business audit) — keep `audit_local_seo` strictly conditional on local-business firmographic to avoid burning DataForSEO budget on non-local prospects.
- **Sonnet vision cost on diversity-imagery** would have been ~$0.05/audit but **rejected by research due to LOW confidence + litigation risk** (defamatory mis-categorization of skin-tone/age/gender-presentation). Use structural ESG signals in `audit_corporate_responsibility` instead.

## Sources

- Origin design: 20+ turn conversation 2026-04-19/20.
- Related plans: `docs/plans/2026-04-17-agency-visibility-plan.md`, `docs/plans/2026-04-18-deploy-plan.md`.
- Freddy ports: `src/extraction/content_extractor.py`, `src/clients/`, `src/content_gen/output_models.py`, `src/competitive/brief.py`, `src/competitive/templates/competitive_brief.html`.
- GoFreddy owned providers (full enumeration in "Data provider inventory"): `src/competitive/pdf.py`, `src/geo/providers/cloro.py`, `src/monitoring/adapters/` (12 adapters), `src/competitive/providers/{foreplay,adyntel}.py` + `src/competitive/service.py`, `src/seo/providers/{dataforseo,gsc}.py`, `src/fetcher/instagram.py`.
- Coverage-expansion design sessions 2026-04-21 (Option B: 3 new lenses + P19–P25; Option C: Brand/Narrative 9th lens + P26–P30 + P31 + 4 conditional enrichments) and 2026-04-22 (R1 research validating P32–P48 + R2 research validating P49–P86 + 3 reasoning primitives). Full per-session detail + citation sources + benchmark-data provenance (Gartner 2025 CMO Spend, OpenView/High Alpha, ICONIQ Growth State of GTM, First Page Sage 2026, Klue 31-questions) consolidated in `docs/plans/2026-04-22-001-audit-coverage-gaps.md`, `docs/plans/2026-04-22-002-audit-coverage-research.md`, `docs/plans/2026-04-22-003-audit-coverage-research-r2.md`.
- External: Claude Agent SDK Python docs, Fireflies.ai webhook + GraphQL docs, wappalyzer-next (s0md3v fork), crt.sh + subfinder, DataForSEO Traffic Analytics + On-Page hreflang + Business Data API + SERP local_pack + serp_site_query, Princeton GEO study (KDD 2024), Mozilla HTTP Observatory v2 API docs, GitHub REST + GraphQL rate limits, Product Hunt API v2 docs, MediaWiki Action API + REST + Lift Wing inference reference, Wikimedia Enterprise Structured Contents beta endpoint, Atlassian Marketplace REST v3, Greenhouse/Lever/Ashby/Workable public job-board APIs, Bright Data Glassdoor scraper, Apify scrapers (Chrome Web Store / AlternativeTo / TAAFT / Futurepedia / Slack Marketplace / AWS Marketplace / Stripe Marketplace / G2 + Capterra detail / LinkedIn Company Profile / Indeed / Mac App Store), axe-playwright-python, textstat + py-readability-metrics, spaCy en_core_web_sm, Klue 31-questions win-loss methodology, Wes Bush "Bowling Alley" + Samuel Hulick UserOnboard.com + Ramli John EUREKA onboarding frameworks, Playwright MCP snapshot mode docs, npm registry + PyPI JSON last-publish-date endpoints, Mintlify/Stoplight/Redoc/Scalar API-docs vendor comparison.
