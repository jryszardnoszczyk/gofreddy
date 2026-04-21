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

- R1. Form → deliverable in 3 business days, no manual work between intake and founder review.
- R2. `freddy audit run --client <slug>` runs all 6 stages end-to-end with per-stage checkpoints.
- R3. 5 lens analyses: SEO, GEO, competitive, monitoring, conversion. Canonical findings schema with severity + confidence.
- R4. Synthesis produces ranked findings, 3–5 surprises, and a 3-tier proposal (Fix-it / Build-it / Run-it) with deterministic registry-based pricing.
- R5. Deliverable = HTML at `reports.gofreddy.ai/<slug>` + downloadable PDF; Fireflies captures the walkthrough call.
- R6. Local storage only. Everything under `clients/<slug>/audit/`, git-committed per stage.
- R7. Per-audit cost ≤ $30 soft / $60 hard. Monthly infra ≤ $70 (Fireflies $10 + DataForSEO Traffic add-on + Apify actors pay-per-run).
- R8. First 5 audits use per-stage approval gates; after calibration, a single permanent gate remains between Stage 1 and Stage 2 (JR reviews the pre-discovery brief before lens analysis runs — this is the manual intake filter for every audit).
- R9. No autoresearch coupling. Audit does not touch `src/evaluation/` or `autoresearch/`.
- R10. $1,000 audit, credited to first invoice if signed within 60 days. Invoicing mechanism itself is out of scope for this plan.
- R11. Data retention: workspace kept active 90 days post-delivery, archived 1 year, then deleted. Deliverable at `reports.gofreddy.ai/<slug>` preserved full 1 year.
- R12. PII hygiene: VoC quotes sourced only from public channels; quotes always cite source URL; private/paywalled content never embedded verbatim.
- R13. Branding: every HTML page and PDF includes a persistent "Prepared by GoFreddy · gofreddy.ai" footer, preserved when shared externally.
- R14. Throughput cap: at most 3 audits concurrently in flight. Poller does not start a new audit while ≥3 rows have status=processing.

## Scope

**In:** 6-stage pipeline, 9 pre-discovery primitives, 4 ports from Freddy (`content_extractor`, `clients` schema, `content_gen` output models, `competitive/brief.py` pattern), HTML+PDF rendering, Cloudflare Worker intake + hosting, Fireflies integration, 6 consolidated Corey Haines reference files.

**Out:** Autoresearch work, post-sign delivery execution, outbound prospecting, multi-tenant infra, free-tier audits, pre-analysis discovery call (replaced by rich intake form + post-delivery walkthrough).

## Architecture

6 stages run sequentially. Each stage is a Python function that reads state, does work (deterministic Python or structured Claude API calls), writes outputs, updates state. **No agent loops except in Stage 2.** No Stage abstract class. No skills library under `.claude/skills/`. Prompts are string constants in `src/audit/prompts.py`.

```
Form submit → Cloudflare Worker → Fly API /v1/audit/intake → audit_pending row
Laptop poller (every 5 min) → freddy audit run --client <slug>

  ├─ Stage 0: Intake       — Python only, populates workspace from form data
  ├─ Stage 1: Pre-discovery — runs 9 primitives; ONE Opus call synthesizes signals into brief
  ├─ [calibration gate: first 5 audits only]
  ├─ Stage 2: Lenses        — 5 Sonnet Agent SDK sessions in parallel (asyncio.gather)
  ├─ Stage 3: Synthesis     — brief.py-style async fan-out → Opus synthesis
  ├─ Stage 4: Proposal      — Opus picks capability IDs + writes narrative; Python applies pricing
  └─ Stage 5: Deliverable   — Jinja2 → HTML, WeasyPrint → PDF, upload to R2, publish

Fireflies webhook (post walkthrough call) → Opus extracts fit signals → clients/<slug>/audit/walkthrough/fit_signals.json
```

**Module layout:**

```
src/audit/
  run.py                    # freddy audit run entry point, orchestrator loop
  state.py                  # state.json read/write, cost gate, git commit
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
  templates/audit_report.html.j2
  references/*.md           # 6 consolidated Corey skill references
.claude/skills/audit-run/SKILL.md  # invoke with /audit-run in interactive Claude Code
cli/freddy/commands/audit.py       # freddy audit {run,poll,publish,ingest-transcript}
src/api/routers/audit_intake.py    # POST /v1/audit/intake (form webhook)
src/api/routers/audit_walkthrough.py  # POST /v1/audit/walkthrough (Fireflies webhook)
landing/audit-intake.html          # gofreddy.ai form
cloudflare-workers/audit-intake/   # form→Fly relay
cloudflare-workers/audit-hosting/  # reports.gofreddy.ai/<slug> edge
supabase/migrations/20260420000001_audit_intake.sql
```

## Key decisions (resolved in 2026-04-19/20 design session)

- Claude Agent SDK (Python), not ported Freddy ADK; inline prompts, not skills library.
- Sonnet for pre-discovery synthesis + all 5 lenses; Opus for synthesis, surprises, proposal.
- Local file storage only; per-stage git commits.
- Rich intake form + single walkthrough call at delivery (no pre-analysis call).
- Greenfield primitives replace paid APIs: python-Wappalyzer → BuiltWith, crt.sh + subfinder → SecurityTrails, public-page scraping → PDL + TheirStack.
- Registry-driven pricing: LLM picks capability IDs, Python applies prospect-size multiplier deterministically.
- HTML primary + PDF rendered from same HTML (WeasyPrint).
- Auto intake via Cloudflare Worker → Fly API → laptop poller.
- Phase 1 infra: ~$40–70/mo. Phase 2 upgrades (PDL, TheirStack, SecurityTrails paid tiers, BuiltWith) only if real audits reveal gaps.

## Deferred to implementation

- Exact capability registry content (ship 12–15 starter entries; iterate based on first 5 audits).
- Jinja2 template specifics (start from `src/competitive/templates/competitive_brief.html`; iterate).
- Lens agent max-turn budget (start 20, tune).
- Scraper retry/backoff specifics (graceful degradation with `partial: true` flags).
- ASO module — build only if any of first 5 prospects have a mobile app.
- Exact Fireflies GraphQL field paths (use docs at implementation time).
- $1K audit invoicing mechanism (Stripe link / manual invoice / credit-note accounting) — assumed handled separately; this plan stops at deliverable publishing.
- Auto-expiration of archived audits past 1 year — cron script; defer until first archived audit approaches expiry (~April 2027).

## Implementation units

### U1. Foundation: workspace + state + ports

**Goal:** Create `src/audit/` skeleton, state.json schema + cost gate, CLI entry, and port three small pieces of Freddy code.

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
- `state.py`: `AuditState` TypedDict with `current_stage`, `stage_results` (dict), `cost_spent_usd`, `calibration_mode` (bool). Plus functions `load()`, `save()`, `check_cost_gate(state, soft=30, hard=60)`, `commit_stage(state, stage_name, outputs)`. No class hierarchy.
- `run.py`: single `run_audit(slug, target_stage=None)` function that loops through stage functions and calls them in order.
- Workspace layout: `clients/<slug>/audit/{intake,prediscovery,lenses,synthesis,proposal,deliverable,walkthrough}/` + `state.json` + `cost_log.jsonl`.
- Atomic state writes: `state.json.tmp` → rename → `git add && git commit`.

**Test scenarios:**
- Happy: fresh workspace + `freddy audit run` populates state.json and commits.
- Happy: `freddy audit run --stage 3` resumes at stage 3 only.
- Edge: cost gate hard cap stops pipeline before next stage.
- Edge: corrupted state.json raises actionable error with `--reset` hint.
- Happy: `content_extractor.extract(url)` returns non-empty result for HTML, PDF, YouTube URLs.

**Done when:** `freddy client new test --url https://example.com && freddy audit run --client test` produces valid empty workspace + state.json with all stages pending + one git commit.

---

### U2. Pre-discovery primitives (9 functions)

**Goal:** All 9 primitives in a single `src/audit/primitives.py` file — plus a shared Playwright fetcher. Each primitive is a Python function returning a TypedDict, graceful degradation with `partial: bool` on all of them.

**Files:**
- Create `src/audit/rendered_fetcher.py` — `RenderedFetcher` class (context manager, single shared browser context per audit)
- Create `src/audit/primitives.py` — 9 functions:
  - `tech_stack(rendered_page) -> dict` — python-Wappalyzer + custom regex rules for pixels, server-side tagging, modern auth
  - `enumerate_subdomains(domain) -> dict` — crt.sh HTTP + `subfinder` CLI + `whois` CLI, classify live/parked/404
  - `scrape_careers(domain) -> dict` — try `/careers`, `/jobs`, `/work-with-us`; Sonnet extracts role titles + tech mentions
  - `scrape_firmographics(domain) -> dict` — Crunchbase public page + LinkedIn company page via rendered fetcher; Sonnet structured extraction
  - `detect_schema(rendered_page) -> dict` — parse JSON-LD blocks, flag missing high-value types
  - `score_ai_visibility(brand, queries, competitors) -> dict` — wraps existing `src/geo/providers/cloro.py`; returns per-platform SOV + gaps
  - `scan_competitor_pages(prospect_domain, competitor_domains) -> dict` — fetch sitemaps, grep `/vs/`, `/alternatives/`, `/compare/`
  - `gather_voc(brand, platforms) -> dict` — wraps existing Xpoz + IC + review adapters + Apify G2/Capterra actors
  - `detect_analytics_tags(rendered_page) -> dict` — GA4/GTM/Segment/Mixpanel/Meta Pixel/TikTok Pixel presence + declared events + server-side tagging detection. Shares regex-rule helpers with `tech_stack` but is a separate function because analytics/tag findings feed the conversion + monitoring lenses specifically, while `tech_stack` feeds the SEO + GEO lenses.
- Modify `pyproject.toml`: add `playwright>=1.45.0`, `python-Wappalyzer>=0.4.0`
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
- Edge: Crunchbase page 404 → firmographic returns partial=true + missing_fields.
- Edge: Cloro rate-limited → ai_visibility returns partial=true, cached data.
- Integration: all 9 primitives run sequentially on one real prospect without exceptions; total wall-clock < 10 min.

**Done when:** Each primitive runs standalone from a python REPL against a real URL and returns a non-empty, schema-valid result.

---

### U3. Stages 0 + 1: intake + pre-discovery with brief synthesis

**Goal:** Stage 0 (Python-only) populates workspace from intake form. Stage 1 runs all 9 primitives in Python, then makes ONE Opus call to synthesize a `prospect-brief.md` + `signals.json`.

**Files:**
- Create `src/audit/stages.py` with `stage_0_intake(state)` and `stage_1_prediscovery(state)` functions
- Create `src/audit/prompts.py` with `PREDISCOVERY_SYNTHESIS_PROMPT` string constant
- Test: `tests/audit/test_stages_0_1.py`

**Approach:**
- `stage_0_intake`: reads intake form data from `audit_pending` row (populated by Unit 7), writes `clients/<slug>/audit/intake/form.json` + `clients/<slug>/config.json` (prospect Client model). No LLM.
- `stage_1_prediscovery`:
  1. Opens shared `RenderedFetcher` context
  2. Gathers signals by running both the 9 new primitives from U2 AND these existing freddy CLI commands via subprocess: `freddy sitemap <url>`, `freddy scrape <url>`, `freddy detect <url> --full`, `freddy audit seo <domain>`, `freddy audit competitive <domain>`, `freddy audit monitor "<brand>"`, `freddy visibility --brand <x> --keywords <y>`. Each result (primitive or CLI) writes to `clients/<slug>/audit/prediscovery/signals.json` under a top-level key.
    2a. Competitor discovery is explicit: a small helper `derive_competitors(form_data, dataforseo_serp, foreplay_ad_categories) -> list[str]` merges (a) prospect-provided competitors from intake form, (b) top-SERP overlap from DataForSEO, (c) shared ad-category competitors from Foreplay/Adyntel. The Opus synthesis call reconciles into a final ranked list of 3–5 competitors written to `signals.json:competitors`. This list is the input to `score_ai_visibility` and `scan_competitor_pages`.
  3. One Opus call (`PREDISCOVERY_SYNTHESIS_PROMPT`) takes signals.json + form data, outputs structured `PrediscoveryBrief` (Pydantic): ICP hypothesis with confidence label, inferred competitor list, pain points, tech posture summary, AI-visibility headline, 3 hypotheses to validate on walkthrough
  4. Writes `brief.md` (prose) + `brief.json` (structured)
- Budget: $8 hard cap for entire Stage 1 (most is Sonnet LLM usage inside `scrape_firmographics` + `scrape_careers`; final Opus synthesis < $0.50).

**Test scenarios:**
- Happy: intake form with URL → Stage 0 writes valid config.json + form.json.
- Happy: Stage 1 end-to-end on a known prospect produces brief.md with all 11 signal sections + ICP hypothesis.
- Edge: 3 of 9 primitives return partial → brief flags "partial signals" + proceeds.
- Edge: Stage 1 cost exceeds $8 → raises CostCeilingExceeded before Opus synthesis.
- Integration: brief.json validates against `PrediscoveryBrief` Pydantic schema.

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
- `Finding` schema: `{id, lens, title, severity(0-3), reach(0-3), feasibility(0-3), evidence_urls[], evidence_quotes[], recommendation, effort_band(S/M/L), confidence(H/M/L), category_tags[]}`.
- `LensOutput`: `{lens_name, findings[], lens_summary, metadata{cost, turns, duration}}`.
- Each lens agent: open `ClaudeSDKClient` with lens-specific prompt as system_prompt, inject `prospect-brief.md` + full `signals.json` + matching `src/audit/references/<lens>-references.md`, allowed_tools = `{Read, Write, Bash}` (Bash for ad-hoc checks like additional DataForSEO calls), max_turns=20, model=sonnet.
- Run 5 lenses via `asyncio.gather(*[run_lens(l) for l in lenses])` with `Semaphore(5)`.
- Each writes to `clients/<slug>/audit/lenses/<lens>/{output.json, narrative.md}`.
- On lens failure: mark `LensOutput.partial = True`, pipeline continues; only raise if ≥3 lenses fail.

**Test scenarios:**
- Happy: all 5 lenses produce 3–8 findings each on a dogfood prospect; parallel wall-clock under 90 min.
- Happy: Findings validate against canonical schema.
- Edge: one lens hits max_turns → LensOutput.partial=True; other 4 complete cleanly.
- Edge: one lens's Claude API error → retried once → raised as partial.
- Integration: total Stage 2 cost under $20 for a medium-complexity prospect.

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
  2. Runs structural gate: each lens has ≥1 finding OR explicit `not_applicable=true`; if not, raise actionable error
  3. Calls `AuditBrief.generate()` (ported from Freddy): async fan-out of 9 section LLM calls (Opus) with 160s deadline; results merged by a final Opus synthesis call
  4. Runs `SURPRISE_QUALITY_CHECK_PROMPT` as second-pass Opus verification — each surprise must satisfy (a) non-obvious, (b) evidence-backed, (c) tied to revenue/cost, (d) feasible; any failing → regenerate
  5. Writes `clients/<slug>/audit/synthesis/{findings.md, surprises.md, report.md, report.json}`
- 9 report sections: Hero TL;DR, Executive Summary, What We Found (per lens), Surprises, Competitive Positioning, AI Visibility Posture, Technical Posture, Recommended Next Steps (placeholder for Stage 4 output), About This Audit.

**Test scenarios:**
- Happy: synthesis on dogfood Stage 2 output produces findings.md (ranked 15–30 items) + surprises.md (3–5 surprises passing quality check) + report.md (9 sections).
- Edge: one lens has 0 findings + not_applicable=true → synthesis renders "not applicable" section gracefully.
- Edge: structural gate fails (one lens has 0 findings AND no not_applicable flag) → raises with specific lens name.
- Edge: surprise quality check rejects all initial surprises → one regeneration attempt; if second attempt fails, emits with `low_quality_warning=true` for founder review.
- Integration: synthesis cost < $8, wall-clock < 10 min.

**Done when:** Synthesis output reads like a credible audit JR would sign off without rewriting.

---

### U6. Stage 4: proposal with capability registry

**Goal:** Opus picks 3 capability IDs (one per tier when applicable) and writes narrative per capability; Python applies pricing deterministically.

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
  2. Opus call (`PROPOSAL_PROMPT`): picks 3 capability IDs matching findings + writes narrative per capability
  3. Python validates returned IDs exist in registry (raises on hallucination)
  4. Python applies pricing via `pick_pricing()`; LLM never touches numbers
  5. Writes `clients/<slug>/audit/proposal/{proposal.md, proposal.json}`
- Starter registry entries include: `geo-fix-infra`, `seo-fix-schema-sitewide`, `seo-fix-internal-linking`, `content-build-pseo-engine`, `competitive-build-monitoring`, `geo-build-llms-txt-suite`, `seo-retainer-basic`, `monitoring-retainer`, `content-retainer`, `full-distribution-retainer`, and 5 more.

**Test scenarios:**
- Happy: high-severity findings → proposal picks 3 capabilities with narrative.
- Happy: pricing deterministic: same capability + size_band always yields same number.
- Edge: no fix-it prerequisites met → proposal returns 2 capabilities (Build-it + Run-it).
- Edge: LLM returns capability ID not in registry → raises `ProposalValidationError`.
- Integration: proposal total always matches `sum(pick_pricing(id, size) for id in capabilities)`.

**Done when:** Proposal has 3 scoped capabilities, narrative ties to specific findings, prices are registry-deterministic.

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
- WeasyPrint renders same HTML → PDF (≤ 5 MB for email attachability).
- Stage 5 generates ULID slug, writes to state.json, produces `deliverable/{report.html, report.pdf, assets/}`.
- `freddy audit publish --client <slug>` uploads deliverable tree to R2 bucket `gofreddy-audits/<ulid>/`; prints final URL `https://reports.gofreddy.ai/<ulid>`.
- Cloudflare Worker on `reports.gofreddy.ai/*`: validates path matches ULID regex, proxies to R2; else 404.
- Every rendered page (HTML + PDF) includes a footer partial `<footer class="gofreddy-footer">Prepared by GoFreddy · <a href="https://gofreddy.ai">gofreddy.ai</a></footer>` — preserved on every page of the PDF via WeasyPrint `@page { @bottom-center }` CSS rule.

**Test scenarios:**
- Happy: render produces valid HTML (W3C validator passes) + openable PDF.
- Happy: screenshots embedded correctly in both HTML and PDF.
- Edge: proposal has 2 capabilities → template omits third tier gracefully.
- Edge: synthesis has a `not_applicable` lens → template renders collapsed section.
- Integration: end-to-end: Stage 5 → `freddy audit publish` → curl to `reports.gofreddy.ai/<ulid>` returns 200 with HTML; bogus ULID returns 404.

**Done when:** Dogfood audit is viewable at a live `reports.gofreddy.ai/<slug>` URL and downloadable as a PDF.

---

### U8. Intake + Fireflies + poller infrastructure

**Goal:** Wire the form-to-audit pipeline: gofreddy.ai intake form → Cloudflare Worker → Fly API → laptop poller → `freddy audit run`. Plus Fireflies webhook capturing walkthrough transcripts.

**Files:**
- Create `landing/audit-intake.html` — Tailwind-styled form matching existing landing page
- Create `cloudflare-workers/audit-intake/worker.js` + `wrangler.toml`
- Create `src/api/routers/audit_intake.py` — `POST /v1/audit/intake`, `GET /v1/audit/pending`
- Create `src/api/routers/audit_walkthrough.py` — `POST /v1/audit/walkthrough` (Fireflies webhook)
- Modify `src/api/main.py` to register both routers
- Create `supabase/migrations/20260420000001_audit_intake.sql` — `audit_pending` table
- Create `cli/freddy/commands/audit.py:poll` subcommand
- Create `cli/freddy/commands/audit.py:ingest_transcript` subcommand (manual fallback if Fireflies webhook fails)
- Create `src/audit/fireflies.py` — HMAC signature verification + GraphQL transcript fetch + fit-signals extraction (Opus)
- Extend `src/audit/prompts.py` with `FIT_SIGNALS_EXTRACTION_PROMPT`
- Test: `tests/api/test_audit_intake.py`, `tests/audit/test_fireflies.py`

**Approach:**
- `audit_pending` table: `id, slug (ulid), submitted_at, processed_at nullable, form_data jsonb, status enum(pending, processing, complete, failed)`.
- Form fields: name, email, company, URL, size_band, budget_band, 3 top priorities, timeline, decision_maker, what they've tried, current agency status.
- Cloudflare Worker: HMAC-signs + POSTs to Fly API. Turnstile on form for spam mitigation.
- `freddy audit poll`: loop every 5 min, GET `/v1/audit/pending`, for each: `freddy client new <slug> ...`, mark `processed_at`, spawn `freddy audit run --client <slug>` (background). Ctrl-C to exit.
- Fireflies webhook: verify HMAC-SHA256 via `x-hub-signature`, fetch transcript via GraphQL, Opus extracts `FitSignals{decision_maker, budget_confirmed, stated_goals[], objections[], timeline, next_step, confidence}`, writes to `clients/<slug>/audit/walkthrough/fit_signals.json`, notifies JR via Slack.
- `freddy audit ingest-transcript --client <slug> --file <path>` manual fallback.

**Test scenarios:**
- Happy: form submit → Cloudflare Worker → Fly API writes pending row → poller creates workspace + spawns `freddy audit run`.
- Happy: Fireflies webhook → transcript fetched → fit_signals.json written + Slack ping.
- Edge: poller encounters spawn failure → marks `status=failed` + logs; continues to next row.
- Edge: Fireflies webhook with bad signature → 401 response + log; no state change.
- Integration: submit a real test form → prospect flows end-to-end to audit completion without manual intervention (except calibration approval gates).

**Done when:** End-to-end test form submission on `gofreddy.ai/audit-intake` produces a delivered audit at `reports.gofreddy.ai/<slug>` within 3 business days including JR's review pass.

---

## References consolidation

6 Corey Haines audit-level reference files at `src/audit/references/` (reconcile vs existing 11 at `autoresearch/archive/v006/programs/references/` — pick more current, redirect or merge, never keep duplicates):

| File | Merges these Corey skills |
|---|---|
| `stats-library.md` | Princeton KDD 2024 + SE Ranking + ZipTie + Core Web Vitals + form-field tradeoff + churn split — cross-cutting citations cited across every lens |
| `seo-lens-references.md` | seo-audit + site-architecture + programmatic-seo + schema-markup (SEO rows) |
| `geo-lens-references.md` | ai-seo + schema-markup (GEO rows) |
| `competitive-lens-references.md` | competitor-alternatives + customer-research (competitor section) + pricing-strategy (tier structure) |
| `monitoring-lens-references.md` | analytics-tracking + revops + marketing-ideas (channel menu subset) |
| `conversion-lens-references.md` | page-cro + signup-flow-cro + form-cro + onboarding-cro + churn-prevention + popup-cro + paywall-upgrade-cro + copywriting + marketing-psychology (Challenge→Models table) |
| `voc-source-playbooks.md` | customer-research (Mode 2 + confidence labels) + product-marketing-context schema |

Excluded (no audit value): cold-email, community-marketing, referral-program, marketing-ideas (as a standalone, though subset used elsewhere), and 4 other low-value Corey skills.

## Manual review gate (permanent + calibration)

- Permanent Stage 1 → Stage 2 gate (every audit, always): after Stage 1 pre-discovery completes, orchestrator prints the `brief.md` path and prompts "Proceed to lens analysis? [y/n/notes]" and waits for stdin. This is the manual intake filter — JR reviews the pre-discovery brief before any expensive lens work runs. On `n`, orchestrator exits; on `notes`, JR can add context to `clients/<slug>/audit/intake/operator_notes.md` that Stage 2 lens agents will read.
- Calibration gates (first 5 audits only): `state.calibration_mode = True` when `audit_count < 5`. In calibration mode, the orchestrator prompts for approval after every stage (not just Stage 1). After 5 successful audits, `calibration_mode` default flips to False; only the permanent Stage 1 → Stage 2 gate remains. The `--calibration` flag can re-enable per-stage gates on demand.

That's the full review discipline. The mechanism is in code; the judgment is JR's.

## Risks flagged inline

- Claude Agent SDK parallel-session limits: fall back to sequential Stage 2 execution if hit (adds 1–2h wall-clock; correctness preserved).
- python-Wappalyzer misses modern stack: custom augmentation rules in `primitives.tech_stack`; flag low-confidence detections.
- Scraper layout drift (Crunchbase, LinkedIn, /careers): graceful degradation; Phase 2 upgrade path to paid APIs if chronic.
- Playwright memory growth: single shared context per audit; hard timeout per URL.
- Cost ceiling too tight: configurable per client in config.json; track cost variance after 10 audits.
- Fireflies webhook loss: `freddy audit ingest-transcript` manual fallback covers.
- Throughput overload if >3 prospects submit forms simultaneously: poller's `status=processing` counter acts as the concurrency gate. Forms queue; JR gets Slack notifications when queue depth > 5.

## Sources

- Design conversation 2026-04-19/20: 20+ turns resolving all decisions (functioned as origin brainstorm).
- Related plans: `docs/plans/2026-04-17-agency-visibility-plan.md` (existing dashboard), `docs/plans/2026-04-18-deploy-plan.md` (Fly API deployment reused).
- Port sources in `/Users/jryszardnoszczyk/Documents/GitHub/freddy/`: `src/extraction/content_extractor.py`, `src/clients/`, `src/content_gen/output_models.py`, `src/competitive/brief.py`, `src/competitive/templates/competitive_brief.html`.
- Existing GoFreddy pattern: `src/competitive/pdf.py` (WeasyPrint usage), `src/geo/providers/cloro.py` (AI-visibility provider), `src/monitoring/adapters/` (12 reused adapters).
- External: Claude Agent SDK Python docs, Fireflies.ai webhook + GraphQL docs, python-Wappalyzer, crt.sh + subfinder, DataForSEO Traffic Analytics add-on, Princeton GEO study (KDD 2024).
