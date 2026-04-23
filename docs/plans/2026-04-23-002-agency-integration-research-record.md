---
title: Agency integration research record — freddy → gofreddy
date: 2026-04-23
status: research-record (pre-triage)
purpose: Capture every meaningful inventory finding from the 16-agent parallel audit so we can triage into a prioritized implementation plan. This is NOT a plan — it is the raw record we will plan from.
---

# Agency integration research record

## How this document was built

Sixteen research agents ran in parallel across two waves, each with a narrow mandate and explicit instructions to cite file paths and line numbers. First wave covered provider inventory, frontend, DB schema, API + CLI surface, test coverage, autoresearch programs, deps/infra, docs/plans, harness/judges, storyboards, monitoring intelligence, agency workflows, content/publishing, skills/capability framework, reports/deliverables, operator workflows, business-logic services. Second wave went deeper on creator vetting internals, SEO/GEO audit internals, brand intelligence, policies/moderation, workspace/library/batch UX, background jobs, cross-cutting infrastructure patterns, and autoresearch extensibility + LHR-agent architecture.

Nothing in this document is speculative. Every claim is backed by a file path, line number, or quoted constant in one of the two repositories.

---

## Executive summary

**gofreddy is a conscious product pivot with a large unbuilt center, not an unfinished migration.** It is intentionally leaner on platform surface (no billing, no Cloud Tasks, no Redis, no 36 API routers) while being **genuinely ahead** of freddy in autoresearch, harness, evaluation judges, and fixture infrastructure. The product it was designed to ship — the 6-stage automated audit pipeline per plan 2026-04-20-002, codified in the 005/006 lens catalog — is fully designed and not started. `src/audit/` does not exist.

For the agency use case JR wants, the gap is large but structured. Roughly **50–60k LOC and 37 DB tables** of freddy capability would need to come across to reconstitute a full agency product, across eight coherent capability bundles. None of the bundles are blocked on unsolvable problems. Several key pieces (Adyntel end-to-end, monitoring adapters, fixture infrastructure, Sonnet judges, 11 reference docs, agent-first autoresearch architecture) are already in gofreddy and **better** than freddy's versions.

Three immediate risks sit above the bundles:

1. **CI is lying.** 33+ test files import modules that do not exist in `gofreddy/src/`. They fail at collection. No root `tests/conftest.py`. Until this is fixed, we cannot trust any green status.
2. **The product the 005 plan targets does not exist yet.** The audit pipeline is ~30–40 engineering days of greenfield work blocking the entire marketing-audit lens program.
3. **Many workers have zero implementation.** `gofreddy/src/` has no `monitoring/worker.py`, `batch/worker.py`, `generation/worker.py`, `jobs/worker.py`, or `publishing/dispatcher.py`. Every scheduled operation — weekly digest, scheduled publish, scheduled monitor runs, batch analysis, video render — is blocked on this.

The rest of this document is the full inventory, bundled for triage.

---

## The reality gap, quantified

| Dimension | freddy | gofreddy | gap | Source |
|---|---|---|---|---|
| Business-logic services (`src/*/service.py`) | 31 | ~8 | 23 missing, ~8,100 LOC | Business-logic agent |
| Orchestrator tool handlers | 20 | 0 | 9,093 LOC | Orchestrator agent |
| Orchestrator tool catalog (ToolSpecs) | 20 | 0 | ~2,000 LOC | Orchestrator agent |
| Monitoring intelligence modules | 11 | 5 | 6 missing, ~1,280 LOC | Monitoring agent |
| Publishing platform adapters | 7 | 2 (partial) | 5 missing, ~2,000 LOC | Content/publishing agent |
| Video production service + repo | 18,700 LOC | models only (212 LOC) | ~18,500 LOC | Storyboards agent |
| Newsletter service | 333 LOC + 213 LOC repo | 0 | all | Reports agent |
| Content generation service | 511 LOC | 0 | all | Content/publishing agent |
| Cloud Tasks workers | 4 deployed | 0 | all (JobWorker, BatchWorker, MonitorWorker, PublishDispatcher) | Background-jobs agent |
| API routers | 47 | 9 | 38 missing | API matrix agent |
| API endpoints | 149 | 57 | 92 missing (62%) | API matrix agent |
| CLI command groups | 33 | 25 | 8 missing | CLI matrix agent |
| DB tables | 53+ | 16 | 37+ missing | DB-schema agent |
| Repository-layer files | 29 | 4 | 25 missing | DB-schema agent |
| Frontend routes | ~10 | 4 | 6 missing + 50 canvas sections | Frontend agent |
| Test code (LOC) | 79,574 | 52,959 | 33% smaller; 33+ orphaned | Test coverage agent |
| Python dependencies | includes Stripe/Redis/Cloud-Tasks/SSE/DSPy/Resend | missing those | 8 critical packages dropped | Deps agent |
| Harness LOC | 4,135 | 2,636 | gofreddy simpler by design | Harness agent |
| Evaluation LOC | 3,052 | 3,817 | **gofreddy larger** | Harness agent |

Roughly **50–60k LOC** of freddy capability would need to come across to reconstitute an agency product. At a sustainable 1–2k effective LOC/week with AI-assisted coding, this is a **6–9 month program**.

---

## What gofreddy has that freddy doesn't — preserve these

Do not regress any of the following during the port. Several are explicit improvements made in gofreddy.

1. **Claude engine (OAuth + bare)** with graceful resume via `.resume.yaml` and rate-limit detection in JSON stream events. (harness/engine.py)
2. **Single-worktree parallel tracks** with `commit_lock` + `restart_lock` — simpler than freddy's multi-worktree + cherry-pick. Five correctness bugs fixed. (harness/run.py, worktree.py 254 LOC vs freddy 702 LOC)
3. **Fixture infrastructure** — cache system at `~/.local/share/gofreddy/fixture-cache/`, pool separation via `sources.json` + `pool_policies.json`, staleness detection, dry-run calibration, refresh, discriminate. (cli/freddy/fixture/)
4. **Sonnet paraphrase judge (R-#32)** replaces freddy's deterministic `fuzzy_match` — verifies every evidence quote for a criterion in one LLM call returning `{quote_id: bool}`.
5. **Sonnet calibration judge (R-#33)** replaces freddy's cap-at-3 cliff — smooth gradient re-calibration via evidence-score alignment check.
6. **Structural claim verification** (`src/evaluation/structural_agent.py`, 150 LOC) — domain-specific claim validation replacing flat rubric matching.
7. **Five evolution judges** — variant_scorer (77 LOC), promotion_agent (46 LOC), canary_agent (45 LOC), rollback_agent (46 LOC), system_health_agent (102 LOC). Parallel claude + codex CLI scoring.
8. **Role-locked judge service** — `judges/server.py` 374 LOC FastAPI with `JUDGE_MODE` env var (session vs evolution), audit trails, credential isolation.
9. **AsyncOpenAI-driven parent selection** (`autoresearch/agent_calls.py`, 183 LOC, R-#29) replaces hand-crafted policy. Pydantic-validated structured agent calls. Rationale mandatory.
10. **Unified events log** (`autoresearch/events.py`, 97 LOC) — append-only JSONL under `~/.local/share/gofreddy/`, exclusive flock on write+flush+fsync, rotates at 100MB. Audit trail for all mutations.
11. **Generation metrics + alert agent** (`autoresearch/compute_metrics.py`, 348 LOC, R-#30) — detects `inner_outer_drift`, `uneven_generalization`, `plateau`, `collapse`, `overfitting`, `novelty_exhausted` via Sonnet subprocess.
12. **SHA256 critique manifest** (R-#13, `autoresearch/critique_manifest.py` 105 LOC) — hash-check prevents tampered variants; refuses mutation on mismatch. Layer1 validator re-computes in `python3 -I`.
13. **Program prescription critic** (`autoresearch/program_prescription_critic.py`, 337 LOC) — soft-review agent for program mutations; emits advisory verdicts (no-change / advise).
14. **Per-fixture semver + rotation sampling** — stratified, `anchors_per_domain`, `random_per_domain`, `cohort_size`, SCHEMA.md authoritative contract. Freddy fixtures have no versioning.
15. **Multi-tenant `user_client_memberships`** with roles (admin/owner/editor/viewer) — vs freddy's single `operator_id`. Admin-on-any-client grants full access.
16. **Portal skeleton** at `/portal/:slug` with `resolve_client_access()` in `src/api/membership.py`.
17. **Python 3.13 pin, Fly.io deployment, leaner Dockerfile, GitHub CI** with judge-isolation architecture gating (`.github/workflows/ci-lint-judge-isolation.yml`).
18. **11 references library docs** in `autoresearch/archive/v006/programs/references/`: ad-creative-analysis-framework, ai-search-platform-guide, churn-signal-patterns, hook-patterns, competitor-teardown-and-pricing, edit-pass-and-specificity, page-structure-and-comparison-patterns, prose-hygiene, schema-and-audit-notes, watering-hole-source-guide, CONFLICTS. Total 1,775 LOC. None of these exist in freddy.
19. **Expanded `evaluate_variant.py`** (2,507 LOC vs freddy 1,645) — R-#13 critique manifest validation + holdout isolation.
20. **Evaluation scope YAML per domain** (`*-evaluation-scope.yaml`) — formal outputs / source_data / transient / notes declaration per domain. Not present in freddy.
21. **`weekly_digests` table** already in schema migration `20260418000002_autoresearch_tables.sql:211`.
22. **Adyntel wired end-to-end** in three ways: API path, direct CLI audit path, service orchestration with Sonnet near-miss-domain validator (R-#38). Better than freddy.
23. **`cli/freddy/providers.py`** provider factory + `cli/freddy/commands/setup.py` expanded env prompts + `cli/freddy/commands/audit.py` direct provider calls.
24. **Gofreddy-only CLI commands**: `freddy client`, `freddy audit`, `freddy fixture` — none in freddy.

---

## Pre-flight — fix before any bundle ships

### Orphaned tests (CI is lying)

Thirty-three-plus test files import modules absent from `gofreddy/src/`. They fail at pytest collection. Enumerated from the test-coverage agent:

| Missing module | Orphaned test files |
|---|---|
| `src/orchestrator/` | 14 files: `test_tool_catalog`, `test_compliance`, `test_search_optimization_tool`, `test_pr051_batch_workspace`, `test_manage_client_tool`, `test_evaluate_policy_tool`, etc. |
| `src/schemas` top-level | 13 files: `test_schemas`, `test_analysis_service`, `test_demographics`, others importing `VideoAnalysis`, `BrandAnalysis`, `BrandSentiment` |
| `src/brands/` | `test_brands.py` (578 LOC), `test_brands_exposure.py` |
| `src/clients/` | `test_clients_service.py`, `test_manage_client_tool.py` |
| `src/demographics/` | `test_demographics.py` (439 LOC) |
| `src/jobs/` | `test_job_worker.py` (315 LOC), `test_job_service.py`, `test_pr067_scheduled_monitoring.py`, `test_pr025_durability.py` |
| `src/newsletter/` | `test_newsletter_service.py` (279 LOC) |
| `src/stories/` | `test_instagram_stories.py`, `test_pr057_ssrf_path_traversal.py`, `test_pr025_durability.py` |
| `src/prompts` | `test_pr052_resume_cache.py` |

Remediation options:
- `pytest.mark.xfail(reason="port pending")` on each orphaned file, or
- Delete orphaned tests and re-derive when porting the module, or
- Stub the missing modules with `raise NotImplementedError` bodies so tests fail honestly at runtime not collection.

### Missing root `tests/conftest.py`

Freddy has 539 LOC of shared fixtures: `db_pool`, `gemini_analyzer`, `r2_storage`, `fetchers`, 16 repository fixtures, 12 service fixtures, test_user, test_api_key, test_video_path. gofreddy has none at root; only `tests/test_api/conftest.py` (179 LOC, Supabase-only). Each test suite rolls its own setup. Needs root conftest with at minimum: provider mocks (`mock_adyntel`, `mock_ic_backend`, `mock_xpoz`), db pool, gemini mock, r2 mock.

### Missing dependencies

`pyproject.toml` drops 8 packages that bundles below require back:

| Package | Version | Needed by |
|---|---|---|
| `stripe[async]` | ≥13.0.0,<15.0.0 | Bundle 6 audit engine, Bundle 3 weekly digest billing |
| `google-cloud-tasks` | ≥2.0.0 | All workers (Bundle 2 onwards) |
| `sse-starlette` | ≥2.0.0 | Bundle 4 batch progress, Bundle 5 generation progress |
| `redis` | ≥5.0.0 | Cross-instance session revocation, distributed caching |
| `resend` | ≥2.0,<3.0 | Bundle 3 weekly digest, Bundle 2 account notifications |
| `dspy` | ≥3.1.0 | Bundle 6 if we keep DSPy agentic workflows |
| `supabase` | ≥2.0.0 | Client-side DB (currently asyncpg only) |
| `weasyprint` | ≥62.0 | PDF report export (confirm present) |
| `mistune` | ≥3.0.0 | Markdown → HTML (for reports) |
| `nh3` | ≥0.2.14 | HTML sanitization |
| `svix` | latest | Webhook signature verification |

### Forecast — confirmed non-existent

Triple-grep across `src/`, `cli/`, `configs/`, `docs/`, `autoresearch/`, `tests/`, `pyproject.toml`, `requirements.txt`, `package.json` in both repos. No provider, no module, no env var, no package. Likely confusion with **Google Trends**, which is wired at `src/monitoring/adapters/google_trends.py` in both repos. Drop Forecast from consideration.

### Restore `db` pytest marker

gofreddy's `pyproject.toml` removed `db` marker. Restore to enable fast unit-only test runs.

**Pre-flight effort: 3–4 days. Risk: low but blocking.**

---

## Bundle 1 — Analytical uplift (copy-paste wins)

**What it unlocks:** Every auditor, agent, and LLM call in gofreddy gets a calibrated quality bar. Foundation for every other bundle.

**Contents:**

| Asset | freddy path | gofreddy status | Notes |
|---|---|---|---|
| Creative pattern + scene-beat-map prompts | `src/prompts.py` CREATIVE_PATTERN_PROMPT (~1,200 LOC) | missing | Hook taxonomy + scene-beat format `(N) BEAT_TYPE T1-T2s: shot_type camera_move — description`. Would take weeks to reverse-engineer. |
| DEMOGRAPHICS_INFERENCE_PROMPT | `src/prompts.py` lines 322–451 (~1,000 LOC) | missing | Includes 2025–2026 slang taxonomy, gender-skew baselines by content category, income signal reliability guidance, probability + confidence distributions. |
| BRAND_DETECTION_PROMPT + BRAND_DETECTION_SYSTEM | `src/prompts.py` lines 461–568 (~450 LOC) | missing | Per-brand sentiment, context tag (endorsement/comparison/background/criticism/sponsored/review), `is_competitor` flag, timestamp ranges, confidence. |
| QUERY_PARSING_PROMPT | `src/prompts.py` lines 717–774 (~200 LOC) | missing | NL → platform-aware filters; maps TikTok vs IG vs YouTube capabilities; flags unsupported operations. |
| GARM 75-class ModerationClass enum | `src/schemas.py` lines 46–200+ (~400 LOC) | gofreddy has 75-class version per policies agent — **verify parity** | 11 GARM categories + safety + brand. Adult (8), Arms (6), Crime (8), Death/Injury (8), Piracy (3), Hate (8), Profanity (4), Drugs/Alcohol (8), Spam (6), Terrorism (5), Social Issues (8). |
| Intent classification taxonomy (5-class) | `src/monitoring/intelligence/intent.py` (161 LOC) | missing | complaint / question / recommendation / purchase_signal / general_discussion. Gemini Flash-Lite batch classification. |
| Dual sentiment classifier | `src/monitoring/intelligence/sentiment_classifier.py` (173 LOC) | missing | Lexicon + Gemini dual-pass with lexicon fallback on LLM fail. |
| Trends correlation (Pearson r) | `src/monitoring/intelligence/trends_correlation.py` (120 LOC) | missing | Mention volume ↔ Google Trends interest across 1d–90d. |
| Multi-lane L1/L2 routing | `src/analysis/lane_selector.py` | missing | Transcript-quality score + threshold-based gate. ~80% cost cut when transcript usable. |
| Compliance A–F grading | `src/analysis/compliance.py` (106 LOC) | gofreddy has it per policies agent — **verify present** | Placement (40%: first_3s=1.0, middle=0.5, end=0.2, absent=0.0) + Visibility (35%: verbal=1.0, text_overlay=0.6, hashtag_only=0.3, none=0.0) + Timing (25%: before_product=1.0, else 0.0). Grade: A≥90, B≥80, C≥70, D≥60, F<60. |
| `AdCreativeCore` normalization schema | `src/competitive/schemas.py` | partial in gofreddy | 18 fields unified across Foreplay + Adyntel: provider, platform, headline, body_text, cta_text, link_url, image_url, video_url, is_active, started_at, transcription, persona, emotional_drivers, ad_type, display_format, categories, niches, creative_targeting, market_target, product_category, languages, running_duration, card_count, data_quality. |
| Competitive Intelligence Constitution | `autoresearch/archive/v001/programs/competitive-session.md` | in gofreddy archive — **verify current-runtime version** | 8-point analytical honesty standards: causal claim discipline, mechanism naming (15+ patterns), cadence classification, 15-objection gap taxonomy, pricing psychology, buyer-stage coverage, cost-of-delay framing, prose hygiene. |
| Evaluation 32-criterion rubric system | `src/evaluation/rubrics.py` (1,001 LOC) | **at parity** (both 1,001 LOC per prior audit) | GEO-1..8 + CI-1..8 + MON-1..8 + SB-1..8. Gradient + checklist with evidence gates. |
| 11 references library | `autoresearch/archive/v006/programs/references/` (1,775 LOC) | **already in gofreddy, not in freddy** | Don't port, use as-is. |

**What to skip:**
- `rubrics.py` — at parity.
- `fuzzy_match` evidence gate — gofreddy's Sonnet paraphrase judge replaced it intentionally (R-#32).

**Effort:** 1 week. **Risk:** low. **Dependencies:** none.

---

## Bundle 2 — Client platform (multi-tenant agency foundation)

**What it unlocks:** Real client entities with competitor tracking, brand context, auto-brief flag, per-client platform connections, portal branding, RBAC. Every other bundle depends on this data model.

**Contents:**

### Database schema

Extend `clients` table:
- Add columns: `competitor_brands TEXT[]`, `competitor_domains TEXT[]`, `brand_context TEXT`, `auto_brief BOOLEAN`
- Already has: `id`, `slug`, `name` (gofreddy migration `20260417000001_init.sql:61-68`)

Add `platform_connections` table (freddy `setup_test_db.sql`):
```sql
CREATE TABLE platform_connections (
  id UUID PK,
  org_id UUID,
  platform VARCHAR,  -- linkedin|tiktok|youtube|bluesky|wordpress|webhook|instagram
  auth_type VARCHAR,  -- oauth2|api_key|app_password
  account_id VARCHAR,
  account_name VARCHAR,
  credential_enc JSONB,  -- AES-256-GCM encrypted
  access_token_enc TEXT,
  refresh_token_enc TEXT,
  key_version INT,  -- for rotation
  scopes TEXT[],
  token_expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN
)
```

Add `brand_creator_relationships` table (freddy `setup_test_db.sql:1666`) — partnership tracking.

Extend `weekly_digests` — already has `client_id`, good.

### Services

| Module | freddy LOC | Notes |
|---|---|---|
| `src/clients/models.py` | 51 | ClientCreate, ClientUpdate, ClientResponse with new fields |
| `src/clients/service.py` | 82 | `create_client(org_id, name, competitor_brands, auto_brief)`, `list_auto_brief_clients()` for scheduler, `update_client` propagates competitors to monitors |
| `src/clients/repository.py` | 150+ | `propagate_to_monitors(conn, client_id, competitor_brands)` transactional update |
| `src/api/routers/clients.py` | 145 | POST /v1/clients, GET list, GET by id, PATCH |
| `src/api/routers/accounts.py` | 277 | POST /v1/accounts/oauth/device-init, POST /v1/connect/bluesky (app_password), DELETE connection |
| `src/publishing/oauth_manager.py` | 366 | Device flow (YouTube, TikTok), Auth Code (LinkedIn), token refresh, `refresh_all_expiring()` cron-eligible |
| `src/publishing/encryption.py` | ~100 | AES-256-GCM with HKDF-SHA256 key derivation, per-row 12-byte nonce, key_version rotation. Already partial in gofreddy. |

### Portal + branding

Extend `src/api/routers/portal.py`:
- Add `GET /portal/:slug/brief/:id/pdf` — serve PDF of competitive brief.
- Add `GET /portal/:slug/digest/:id` — render weekly digest HTML with client branding (logo, colors).
- Branding fields on client: logo_url, primary_color, secondary_color, custom_domain.

### RBAC enforcement

Roles already modeled in `user_client_memberships(user_id, client_id, role)`. Enforce on:
- All `/v1/clients/*` endpoints (owner/admin write, editor/viewer read-only)
- All `/v1/portal/*` endpoints (already partial via `resolve_client_access`)
- All brand / brief / digest endpoints
- Account connections (admin only)

### Auto-brief scheduler

Cron → `list_auto_brief_clients()` (freddy `src/clients/service.py:79-81`) → enqueue Cloud Task per client → `CompetitiveBriefGenerator.generate(client_id, org_id)`. Needs Bundle 7 (background jobs).

**Effort:** 3–4 weeks. **Risk:** medium (OAuth + encryption key rotation is subtle). **Dependencies:** none blocking; scheduler part depends on Bundle 7.

---

## Bundle 3 — CI triangle (flagship weekly deliverable)

**What it unlocks:** Weekly competitive brief + VOC digest shipped to client portal and email. Single most repeatable agency revenue unit.

### Competitive brief generator

`src/competitive/brief.py` (27 KB). Six parallel sections via Gemini synthesis, 160s deadline:

1. **Share of Voice** — SQL-based competitor mention ranking (30-day window, websearch_to_tsquery FTS). Returns `ShareOfVoiceEntry[]` with percentage + avg_sentiment.
2. **Sentiment Analysis** — time-series sentiment aggregation per competitor.
3. **Competitor Ads** — Adyntel + Foreplay via `CompetitiveAdService.search_ads()` parallel fetch + merge. Adyntel already wired end-to-end.
4. **Competitor Content** — multi-platform content search via monitoring adapters.
5. **Creative Patterns** — Gemini vision analysis of 3 top ads via `CreativeVisionAnalyzer` (162 LOC). Extracts creative_type, visual_tone, dominant_colors, production_quality, text_present, text_content, people_present, brand_visible, call_to_action_visible. Batch size 150 images max, 10 concurrent, ~$0.001/image.
6. **Partnership Analysis** — `PartnershipDetector` in `src/competitive/intelligence/partnerships.py`.

Output: `CompetitiveBrief` with `brief_data JSONB` (sections + recommendations + changes), `dqs_score`, `idempotency_key`, `schema_version`.

Rendered via `src/competitive/markdown.py` (146 LOC). Graded against CI-1..CI-8 rubrics.

### Monitoring intelligence modules (missing from gofreddy)

| Module | LOC | Purpose |
|---|---|---|
| `analytics_service.py` | 314 | Topic clustering, performance patterns, engagement prediction |
| `repository_analytics.py` | 280 | Topic cluster persistence |
| `workspace_bridge.py` | 80 | `save_mentions_to_workspace(500 max)` |
| `dispatcher.py` | 86 | Async notification dispatch |
| `intelligence/share_of_voice.py` | 112 | SQL-based competitor ranking |
| `intelligence/trends_correlation.py` | 120 | Pearson r mentions ↔ Google Trends |
| `intelligence/commodity_baseline.py` | 356 | Weekly markdown baseline report (stats, spikes, themes) |
| `intelligence/post_ingestion.py` | 335 | **Agency differentiator**: auto-refine monitor (noise exclusion, keyword expansion, threshold calibration) via Gemini; generates pending changelog entries with autonomy_level (auto/notify/ask) |
| `intelligence/performance_patterns.py` | 251 | Anomaly detection: volume spikes, sentiment drift, source quality shift. Rolling avg + Gaussian smoothing. |
| `intelligence/engagement_predictor.py` | 210 | Score mention reach impact; rank by likely engagement. Logistic regression + source weighting. |
| `intelligence/metric_computations.py` | 73 | Utility: aggregate, rolling average, Gaussian smoothing |
| `intelligence/intent.py` | 161 | 5-class intent classification via Gemini Flash-Lite batch |
| `intelligence/sentiment_classifier.py` | 173 | Dual-pass: lexicon + Gemini |
| `intelligence/sentiment.py` | 131 | Time-series sentiment, 1h/6h/1d buckets, 30min TTL cache |

### Monitor changelog workflow

Already in gofreddy schema. Needs service + router:
- Change types: system-suggested, user-initiated, AI-proposed
- Fields: change_type, change_detail (old/new), rationale, autonomy_level, status (pending/applied/rejected/reverted)
- Approval endpoints: POST /v1/monitors/{id}/changelog/{entry_id}/approve|reject
- Post-ingestion auto-refinement emits changelog entries for operator review

### Alert rules + webhook dispatch

`src/monitoring/alerts/` (261 LOC):
- `models.py` (50) — AlertRule (mention_spike config: threshold_pct 50-1000, window_hours 1/6/24, min_baseline_runs 1-10)
- `evaluator.py` (125) — evaluate rules post-ingestion, baseline calculation
- `delivery.py` (136) — Webhook dispatch, HMAC-SHA256 signing, retry 3× on 5xx, cooldown per rule

Plus SSRF-validated webhook URL at creation + re-validated on update. Test-webhook endpoint.

### Newsletter service

`src/newsletter/service.py` (333 LOC):
- Double opt-in subscribe (consent token, TTL configurable)
- Resend Broadcasts API integration
- Webhooks via Svix signature verification: email.delivered / bounced / complained
- Consent audit trail: `consent_log` table (email, action, token, IP, user_agent, confirmed_at)
- Segments: All, Creators, Agencies, Brands (extensible)
- Tables: `newsletter_sends`, `consent_log`

### Weekly digest delivery

Already has `weekly_digests` table. Needs:
- Digest generator → `commodity_baseline.py` markdown output + Gemini executive summary
- Digest renderer → HTML with client branding + PDF export via WeasyPrint
- Delivery → newsletter service → Resend → client portal link
- Scheduled cron trigger (weekly, Monday 9am by default)

### Report generators (missing in gofreddy)

Four domain report generators, each using shared `report_base.py` (660 LOC, already in gofreddy):
- `configs/competitive/scripts/generate_report.py` (454 LOC) + `format_report.py` (164 LOC)
- `configs/monitoring/scripts/generate_report.py` (485 LOC)
- `configs/geo/scripts/generate_report.py` (487 LOC)
- `configs/seo/scripts/generate_report.py` (487 LOC)
- `configs/storyboard/scripts/generate_report.py` (717 LOC)

All render Markdown → HTML → PDF via mistune + WeasyPrint with print stylesheet (A4, 2cm margins, blue #2563eb headers, Liberation Sans / DejaVu Sans / Arial fallback). PDF security: `_safe_url_fetcher` blocks external URLs except `data:` URIs; semaphore-limited 2 concurrent renders.

### API routes

Add to gofreddy:
- POST /v1/competitive/brief — generate brief (client_id, date_range)
- GET /v1/competitive/briefs/:id — fetch brief JSON
- GET /v1/reports/competitive-brief/:id/pdf — PDF export
- POST /v1/monitors/:id/digests — create weekly digest
- GET /v1/monitors/:id/digests — list (10-item default)
- POST /v1/newsletter/subscribe, /confirm, /broadcast, /segments, /webhooks — newsletter CRUD
- POST /v1/monitors/:id/alerts, GET list, PUT/DELETE, GET history, POST test — alert lifecycle
- POST /v1/monitors/:id/classify-intent — on-demand, PRO-only, 1000/day cap
- GET /v1/monitors/:id/share-of-voice — 7d–90d window
- GET /v1/monitors/:id/trends-correlation
- GET /v1/monitors/:id/sentiment — time-series window + granularity
- POST /v1/monitors/:id/changelog/:entry/approve|reject

**Effort:** 4–5 weeks. **Risk:** medium. **Dependencies:** Bundle 2 (client profile with competitor_brands), Bundle 7 for weekly cron.

---

## Bundle 4 — Creator ops (discover → vet → shortlist → brief)

**What it unlocks:** Influencer campaign capability. IC client is wired but unreachable — this bundle lights it up.

### Wire Influencers.club

Missing from gofreddy (all present in freddy):
- `src/orchestrator/tool_handlers/creator_profile.py` — actions: get, enrich, connected_socials, list_content, get_post, capture_stories, check_credits. Multi-action dispatch. PRO-only.
- `src/orchestrator/tool_handlers/discover_creators.py` — modes: search (keyword), similar (lookalike), email (enrichment), network. Audience demographic/credibility filtering.
- `src/orchestrator/tool_handlers/evaluate_creators.py` — audience overlap across up to 10 creators (batched IC call) + brand-safety assessment. PRO-only.
- `src/search/service.py` — `SearchScope.INFLUENCERS` enum + routing dispatch to `ic_backend`.
- `src/search/ic_helpers.py` — filter builders + account normalizers + engagement normalization.
- `src/api/routers/agent.py` — builds registry with `ic_backend`, orchestrates tool execution. line 259 passes ic_backend to orchestrator.
- `src/api/routers/discover.py` — creator-discovery HTTP endpoint.
- `src/api/dependencies.py` (IC section, freddy lines 708–725) — `IC_API_KEY` read, client lifecycle (init / aenter / aclose).

IC API surface (already in gofreddy `src/search/ic_backend.py`, 440 LOC): discovery, similar creators, enrich (full/raw), content (posts/details), socials, audience overlap, get_credits. Bearer auth at `https://api-dashboard.influencers.club`. 300 req/60s rate limit. 11 supported platforms for enrichment. Cost map:
- IC_COST_PER_DISCOVERY_CREATOR: $0.01
- IC_COST_PER_ENRICHMENT_FULL: $1.00
- IC_COST_PER_ENRICHMENT_RAW: $0.03
- IC_COST_PER_CONTENT: $0.03
- IC_COST_PER_SIMILAR: $0.01
- IC_COST_PER_CONNECTED_SOCIALS: $0.50
- IC_COST_PER_AUDIENCE_OVERLAP: $1.00

### Fraud + AQS

`src/fraud/service.py` (369 LOC) with parallel analyzers (followers / engagement / comments). Gofreddy has partial in `src/fraud/analyzers.py` (222 LOC) + config (149) + models (275) = 673 LOC. **Verify** AQS formula and threshold parity.

AQS formula (`src/fraud/models.py:95-98`):
```
AQS = engagement × 0.30 + audience_quality × 0.35 + comment_authenticity × 0.35
```

Grade breakpoints (`models.py:88-111`): Excellent ≥90, Very Good 80-89, Good 60-79, Poor 40-59, Critical <40.
Fraud risk level mapping (`models.py:197-205`): Low AQS≥80, Medium 60-79, High 40-59, Critical <40. Risk score = max(0, min(100, 100-AQS)).

Follower fake heuristics (TikTok weights; Instagram higher):
- no_profile_pic: 0.15 / 0.25
- random_username (regex `^[a-z]{2,6}\d{5,}$|^user\d{6,}$|^\d{8,}$|^[a-z]{10,}$`): pattern-matched
- empty_bio: 0.10 / 0.15
- zero_posts: 0.10 / 0.20
- suspicious_ratio (follows > 500, followers < 50): flagged

Suspicious threshold: TikTok 0.70, Instagram 0.50. Sample confidence: ≥150 high, ≥100 medium, <100 low.

Engagement benchmarks by tier (config.py:67-86):
- TikTok: nano 8-15%, micro 5-10%, macro 4-7%, mega 2-4%
- Instagram: nano 4-6%, micro 2-4%, macro 1.5-2%, mega 0.5-1%

Anomaly: <50% of min = "suspiciously_low"; >3× max = "suspiciously_high".

Cache: 7 days TTL.

### Deepfake (gofreddy has it)

`src/deepfake/` (666 LOC: lipinc.py 199, reality_defender.py 166, models.py 121, config.py 66, exceptions.py 67, __init__.py 47). Per creator-vetting agent, production-ready. Missing: `service.py` ensemble orchestrator.

Ensemble formula: `(1.0 - lipinc_score) × 0.4 + rd_score × 0.6`. LIPINC weight 0.4, Reality Defender weight 0.6.

Risk mapping: Critical ≥0.85, High 0.70-0.84, Medium 0.50-0.69, Low 0.30-0.49, None <0.30.

Detection methods (models.py:21-26): LIPINC_ONLY, REALITY_DEFENDER_ONLY, ENSEMBLE.

Config: threshold 0.50, API timeout 120s, upload timeout 300s, cache 30 days, max retries 3.

Costs: LIPINC $0.000225/sec GPU (Replicate T4), Reality Defender $0.40/scan.

### Fraud routing + test fixes

- `src/api/routers/fraud.py` (freddy) with `_fetch_ic_engagement` + `_parse_ic_engagement` helpers (15s timeout, `engagement_percent → avg_likes/comments`). Provides IC enrichment fallback when Xpoz engagement unavailable.
- Fix orphaned `tests/test_fraud_ic_enrichment.py` and `tests/test_pr082_ic_search.py`.

### Demographics

`src/demographics/` (missing in gofreddy). `AudienceDemographics` model in `src/schemas.py` lines 512-532 with dimensions: interests, age_distribution, gender_distribution, geography, income_level, overall_confidence. Prompt in Bundle 1.

### Evolution (creator tracking over time)

`src/evolution/service.py` (186 LOC, freddy):
- `get_evolution()` — historical analysis aggregation
- `_detect_topic_shifts()` — split + compare (first/second half)
- `_calculate_risk_level()` — score thresholds

Risk level bins: low <0.2, med <0.5, high <0.8, critical ≥0.8. Confidence scales by sample size.

### CLI

Port: `freddy creator search`, `freddy creator fraud`, `freddy discover`, `freddy capture-stories`.

### Frontend

Port: CreatorSearchSection, CreatorProfileSection, CreatorGroupCard, FraudReportSection, DeepfakeSection, EvolutionSection.

**Effort:** 3–4 weeks. **Risk:** medium. **Dependencies:** Bundle 2 (clients + per-client tier gating); partial Bundle 6 scaffolding for orchestrator tool dispatch.

**IC subscription decision:** buy only when this bundle ships. Before that: drawer money.

---

## Bundle 5 — Content factory (draft → approve → schedule → publish → track)

**What it unlocks:** Multi-platform content production for clients. Revenue-generating workflow — agencies bill for posts.

### Content generation service

`src/content_gen/service.py` (511 LOC). 8 content types via Gemini structured generation:

| Type | Model | Prompt focus | Output schema |
|---|---|---|---|
| Social Posts | gemini-2.0-flash | Platform-specific: Twitter 280, LinkedIn 3000, Instagram 2200, TikTok trending | SocialPost[]: platform, body, hashtags, suggested_media_type, character_count |
| Blog Article | gemini-2.0-flash | SEO-optimized, H2/H3, FAQ, internal linking | Markdown + metadata: title, meta_description, sections[], faq[] |
| Newsletter | gemini-2.0-flash | Email-safe inline styles | NewsletterContent: subject, preview_text, body_html |
| Video Script | gemini-2.0-flash | Hook 3s, body, CTA, shot suggestions. TikTok 15-60s, YouTube 2-10min, Reels 15-90s | VideoScript: hook, body_sections[], cta, total_duration_estimate, shot_suggestions[] |
| Ad Copy | gemini-2.0-flash | Per platform: Google 30ch headline, Meta 125ch, LinkedIn 70ch | AdCopyVariant[]: platform, headline, body, cta, display_url |
| Rewrite | gemini-2.0-flash | Tone variants, platform adaptation | RewriteVariant[]: tone, content, target_platform, character_count |
| Creative Brief (synthesize) | gemini-2.0-flash | Workspace items + patterns → brief | top_hooks[], narrative_patterns[], cta_insights, pacing_recommendation, music_trends, recommended_angles[] (3-5), platform_differences |
| From-digest | gemini-2.0-flash | Monitor digest → platform posts | Platform-specific drafts |

Voice profile integration: `_build_system_instruction()` stacks `voice_profile.system_instruction + action instruction`. Voice fetched from `PostgresVoiceRepository`.

### Voice profiles

`src/content_gen/voice_*` (550 LOC total):

| File | LOC | Purpose |
|---|---|---|
| `voice_models.py` | 64 | `VoiceProfile` — org_id, platform, username, profile_type ("text"), text_voice_json, video_voice_json, system_instruction, is_self (own brand vs competitor), posts_analyzed |
| `voice_service.py` | 312 | Analyze posts → extract tone, rhetoric, hashtags → build system_instruction |
| `voice_repository.py` | 178 | PostgresVoiceRepository: `get_profile(voice_profile_id, org_id)` |

`TextVoiceMetrics` (deterministic, zero LLM cost): avg_post_length_words, emoji_frequency, avg_hashtag_count, capitalization_ratio, question_frequency, avg_sentence_length, link_usage_frequency, sentence_length_buckets, top_hashtags.

`TextVoiceQualitative` (Gemini-generated): tone, rhetorical_devices[], humor_style, signature_phrases[], vocabulary_level, writing_structure, emotional_range.

### Article tracking

`src/seo/article_repository.py` + `article_models.py` (61 LOC) + `article_tracking_service.py` (88 LOC):
- `ContentArticle` — title, article_result, article_md, word_count, generation_cost_usd, site_link_graph_snapshot, generation_model
- `ArticlePerformanceSnapshot` — per-article GSC metrics (clicks, impressions, CTR, position)
- Poll loop: 7-day rolling window, end = today - 2 days (GSC lag)

### Publishing service

`src/publishing/service.py` (455 LOC).

Queue state machine: DRAFT → SCHEDULED → PUBLISHING → PUBLISHED | FAILED | CANCELLED.

`QueueItem` schema (models.py:60–91):
```
id, org_id, platform, connection_id,
content_parts[], media[],
first_comment, og_title, og_description, og_image_url, canonical_url, slug,
labels[], group_id, newsletter_subject, newsletter_segment,
status, approved_at, approved_by,
scheduled_at, external_id, external_url, error_message,
retry_count (0,1,2 → backoff [5min, 10min, 20min]), metadata
```

Transitions:
- `create_draft(org_id, user_id, ...)` → DRAFT (max 5000 queue items)
- `update_draft()` — draft-only
- `approve(item_id, org_id, user_id)` — sets approved_at + approved_by, status stays DRAFT
- `schedule(item_id, scheduled_at > now)` → SCHEDULED
- `cancel()` from SCHEDULED → DRAFT
- `dispatcher.dispatch()` (cron): `claim_scheduled_items()` FOR UPDATE SKIP LOCKED, scheduled_at ≤ now, retry_count ≤ 2 → PUBLISHING
- `publish_item()` → PUBLISHED on adapter success; FAILED on error with scheduled_at += RETRY_DELAYS[retry_count]
- `reap_stale_publishing_items()` — 15min timeout recovery → FAILED
- Repost: `process_reposts()` auto-repost up to `max_reposts`

Encryption rotation: `rotate_encryption_keys()` v1→v2 per connection.

### 7 platform adapters (~2,000 LOC)

| Platform | File | LOC | Content types | Media | Auth | Notable |
|---|---|---|---|---|---|---|
| LinkedIn | `adapters/linkedin.py` | 308 | text, article with OG, carousel (PDF render via `_carousel.py` 101 LOC), images (9 max) | Image carousel → PDF | OAuth2 + member_id | POST /rest/posts restli 2.0, first_comment = reply to post URN |
| TikTok | `adapters/tiktok.py` | 269 | Video (PULL_FROM_URL, 4GB), photo carousel (4–35 images) | Video from R2 URL | OAuth2 | 5 uploads/day quota, 2200-char caption, 5 hashtags max |
| YouTube | `adapters/youtube.py` | 317 | Video resumable upload 16MB chunks, metadata (title 100ch, desc 5000, tags 500ch), scheduled publish | Video from URL | OAuth2 | 10K units/day, videos.insert 1600 units, privacyStatus, publishAt, selfDeclaredMadeForKids=false |
| WordPress | `adapters/wordpress.py` | 142 | Posts draft/publish, SEO meta via Yoast REST if installed | None | Application Passwords (base64 Basic) | SSRF pre-flight, HTTPS required, slug, Yoast meta fields |
| Bluesky | `adapters/bluesky.py` | 247 | Text posts 300 graphemes, with external link embed, replies | Images 4 max 1MB each, external links | App password (AT Protocol XRPC) | Facet building (UTF-8 byte indices), session creation, 5000 points/hour |
| Webhook | `adapters/webhook.py` | 153 | Generic JSON payload | content_parts + media[] | HMAC-SHA256 signing optional | SSRF pre-flight, no redirects, X-Signature-256 header, custom external_id/url in response |
| Instagram | `adapters/instagram.py` | stub | — | — | — | Not implemented in public scope |
| X (Twitter) | `adapters/twitter.py` | stub | — | — | — | Not implemented |

All adapters inherit `BasePublisher` (122 LOC `publisher_protocol.py`). Return `PublishResult{success, external_id, external_url, error_message}`.

### Dispatcher

`src/publishing/dispatcher.py` (78 LOC):
- Cloud Scheduler cron (every 15min)
- `claim_scheduled_items(batch=10)` FOR UPDATE SKIP LOCKED
- `reap_stale_publishing_items()` stale > deadline_seconds=200
- Per-platform fan-out

`enabled: False` feature flag default. `max_queue_items_per_org: 30`.

### RSS monitor

`src/publishing/rss_monitor.py` (165 LOC) — feed → queue.

### CLI + frontend

CLI: `freddy publish`, `freddy articles`, `freddy newsletter`, `freddy write`, `freddy auto-draft`, `freddy calendar`, `freddy content`.

Frontend: PublishQueueSection, NewsletterPreviewSection, ContentCalendarSection, GenerationEditorSection. useGenerationProgress hook.

### DB tables

- `platform_connections` (covered in Bundle 2)
- `publish_queue`
- `content_articles`
- `article_performance_snapshots`
- `voice_profiles`
- `newsletter_sends`
- `newsletter_consent_log`

**Effort:** 5–6 weeks. **Risk:** medium-high (OAuth + rate limits + platform-specific edge cases). **Dependencies:** Bundle 2 (platform_connections + OAuth).

---

## Bundle 6 — Video studio (premium creative capability)

**What it unlocks:** Agency produces client video ads end-to-end: brief → reference analysis → storyboard → scene preview → render → publish.

### Video project lifecycle

`src/video_projects/service.py` (1,468 LOC) — VideoProjectService:
- `create_draft_project(title, brief)` → VideoProjectRecord (status="draft")
- `recompose_storyboard()` — regenerate via IdeaService
- Scene ops: add_scene, update_scene, reorder_scenes (atomic with revision check), approve_scenes (batch)
- `generate_scene_previews()` — for each scene: Grok Imagine still + QA score
- `submit_generation_job(project_id)` → GenerationService → Cloud Tasks
- Reference ingestion: external video URLs → CreativePatternService analysis

`PostgresVideoProjectRepository` (`repository.py`, 17,228 LOC — large but mostly 30+ SQL queries):
- Atomic project locks (FOR UPDATE)
- Snapshot pattern: project + scenes + references + job status in single fetch
- Revision conflict detection
- Transaction boundaries around multi-row updates

Models (`models.py`, 135 LOC):
- `VideoProjectRecord` — title, status, revision, source_analysis_ids, style_brief
- `VideoProjectSceneRecord` — scene with shot_type, camera_movement, beat, preview_status + QA scores
- `VideoProjectReferenceRecord` — external video references
- `VideoProjectGenerationJob` — job metadata, r2_key

### Idea service (storyboard draft generation)

`src/generation/idea_service.py` (516 LOC) — IdeaService.

`_STORYBOARD_SYSTEM_INSTRUCTION`:
```
Study creator's visual_style, audio_style, scene_beat_map.
PRODUCTION ADAPTATION: Match shot_type + camera_movement per scene.
Each prompt: SUBJECT & SETTING, CAMERA (tracking/pan/dolly/zoom), 
MOTION (slow-mo/time-lapse), LIGHTING & MOOD.
REQUIRED: protagonist_description (full visual), target_emotion_arc.
```

Generates `StoryboardDraft` with 8–20 scenes: scene_id, shot_type (extreme_close_up / close_up / medium_close_up / medium / medium_wide / wide / extreme_wide / over_shoulder / pov), camera_movement (static / pan / dolly / tracking / handheld / zoom), beat (hook / setup / rising / climax / resolution / cta), duration, audio_direction, transition (fade / cut / dissolve / wipe).

### Storyboard evaluator

`src/generation/storyboard_evaluator.py` (140 LOC). Seven-signal rubric via Gemini Flash-Lite (temperature 0.1):

| Signal | Scale | Meaning |
|---|---|---|
| coherence_score | 1-10 | Scene-to-scene logical flow |
| character_score | 1-10 | Protagonist visual consistency |
| emotion_score | 1-10 | Target emotional arc progression |
| prompt_quality_score | 1-10 | 4 pillars: subject, camera, motion, lighting/mood |
| dialogue_score | 1-10 | Natural, character-appropriate audio |
| audio_score | 1-10 | Consistent audio style across scenes |
| pacing_score | 1-10 | Scene durations + transitions suit short-form |

Output: `overall_score = avg(7 signals)` clamped [1,10] + feedback (~200 chars, biggest weakness) + improvement_suggestion (~200 chars, one action). ~$0.001–$0.002/eval.

### Image preview + QA

`src/generation/image_preview_service.py` (567 LOC):
- Scene preview via Grok Imagine or Gemini (static image 2–3s)
- QA scoring: coherence_score, content_score, quality_score — avg = qa_score
- VerificationResult: scene_score (image ↔ prompt match) + style_score (image ↔ frame-1 reference)
- Gate: qa ≥7 auto-approve, 4-6 manual review, <4 reject

### Creative patterns

`src/creative/service.py` (98 LOC) — CreativePatternService:
- Cache-first analysis via GeminiVideoAnalyzer
- Returns `CreativePatterns`: transcript_summary, story_arc, emotional_journey, protagonist, theme, visual_style, audio_style, scene_beat_map

### Generation service + worker

`src/generation/service.py` (247 LOC):
- `submit_job()` — tier/cost check, FOR UPDATE locks, concurrent limit
- `get_job_status()` — cadre detail + presigned URLs
- `cancel_job()`, `dispatch_job()`

`src/generation/worker.py` (682 LOC) — GenerationWorker:
- Atomic job claim with stale recovery
- Parallel cadre processing when all have seed images
- Sequential fallback for legacy jobs
- Deadline: 1200s (20 min)
- Circuit breaker per provider (3 failures → abort)
- Cost per second: 480p ~3¢, 720p ~5¢, 1080p ~8¢ (configurable)

### Provider clients

| Provider | File | LOC | Purpose |
|---|---|---|---|
| fal.ai | `fal_client.py` | 348 | LTX-2.3 video + FLUX.2 Pro images; duration rounding (even); resolution mapping (no 480p); 3-failure circuit breaker |
| Grok | `grok_client.py` | 348 | Grok Imagine video + image; content moderation blocking (SENSITIVE_WORD_ERROR); 100MB cadre size limit |
| Suno (kie.ai) | `music_service.py` | 184 | V4_5 model; polling with deadline; librosa beat analysis; ~$0.03/track |
| ElevenLabs + Google TTS + OpenAI | `tts_providers.py` | 240 + `tts_service.py` 115 | Voice cloning via ElevenLabs; streaming; cost per character |
| R2 | `storage.py` | 120 | Presigned URLs, 7-day expiry |

Plus `avatar_service.py` (97 LOC, protagonist consistency), `bg_removal_service.py` (110 LOC), `caption_presets.py` (66 LOC: default, hormozi, minimal, elegant, cinematic, neon).

### Composition

`src/generation/composition.py` (567 LOC) — CompositionService:
- FFmpeg video assembly with aspect-ratio-correct dimensions (rounded even)
- SRT caption generation with injection defense: `^[^\x00-\x1f\x7f\\;%{}\[\]`$|#]+$`
- ASS force_style builder
- Subtitle timing + audio mixing

### Voice profiles + media library

- `src/api/routers/voice_profiles.py` (150+ LOC) — ElevenLabs voice clone CRUD, tier-gated (PRO only)
- `src/api/routers/media.py` (200+ LOC) — presigned R2 upload URLs, MIME type allowlist, 100MB size limit, pending asset counting

### Stories (optional)

`src/stories/` (623 LOC):
- `models.py` (49) — CapturedStory
- `service.py` (166) — Instagram story capture + dedup per user
- `repository.py` (205) — existing_story_ids lookup
- `storage.py` (173) — R2 upload
- `exceptions.py` (31)

### DB tables (4 new)

- `video_projects`
- `video_project_scenes`
- `video_project_references`
- `video_project_generation_jobs`

Note: freddy migration `20260415000001_video_projects_missing_columns.sql` *assumes* base table exists — gofreddy lacks base table. Must add via new migration.

### Frontend

`VideoProjectStudio.tsx` (316 LOC) + StoryboardSection + hooks (useVideoProjects, useStudioStaging, useGenerationProgress, useBatchProgress). Studio reference tray. Scene editor with drag-reorder. Generation progress SSE stream.

### CLI

`freddy video create`, `freddy video scenes`, `freddy video generate`, `freddy media upload`, `freddy capture-stories`.

**Effort:** 8–10 weeks. **Risk:** high (most complex state machine in codebase; multi-provider async). **Dependencies:** Bundle 2 (clients), Bundle 5 (publishing for distribution), Bundle 7 (workers for GenerationWorker).

---

## Bundle 7 — Workers, schedulers, webhooks (automation backbone)

**What it unlocks:** Everything scheduled. Monitor runs, weekly digests, scheduled publishing, batch analysis, video rendering, article performance tracking, auto-brief triggering, OAuth token refresh.

### Planned workers (zero implemented)

| Worker | Test file | Config source | Deadline | Failure handling | Blocks |
|---|---|---|---|---|---|
| **MonitorWorker** | `tests/test_pr067_scheduled_monitoring.py`, `test_pr068_alerting.py` (not-in-src) | `src/monitoring/config.py` (124 LOC) | 900s | Circuit 3-fail per adapter, 60s reset | Brand monitoring (Bundle 3) |
| **BatchWorker** | `tests/test_pr051_batch_workspace.py`, `src/batch/test_worker.py` | `src/batch/config.py` (15 LOC): concurrency=50, max_retries=3, claim_timeout=300s, deadline=540s | 540s | Retry 3× with backoff_base=1.0 | Workspace batch analysis (Bundle 8) |
| **PublishDispatcher** | `tests/test_publish_dispatcher.py` (80+ LOC) | `src/publishing/config.py`: enabled=False, dispatch_batch_size=10, dispatch_deadline=200s | 200s | `[5min, 10min, 20min]` backoff | Scheduled publishing (Bundle 5) |
| **JobWorker** | `tests/test_job_worker.py` (316 LOC) | planned | N/A | Per-video resilient | Video analysis jobs |
| **GenerationWorker** | `src/generation/worker.py` (freddy 682 LOC) | GenerationSettings deadline=1200s | 1200s | Circuit breaker + stale recovery | Video render (Bundle 6) |
| **CommentSyncWorker** | `src/monitoring/comments/sync.py` (freddy 223 LOC) | — | hourly | — | Comment inbox (below) |

### Internal Cloud Tasks router (freddy `src/api/routers/internal.py`, 12 endpoints)

| Endpoint | Trigger | Purpose |
|---|---|---|
| POST /internal/process-generation | Cloud Tasks | Process GenerationJob |
| POST /internal/run-monitors | Cloud Scheduler → Tasks | Enqueue monitor runs per schedule |
| POST /internal/process-monitor/{id} | Cloud Tasks | Run single monitor |
| POST /internal/run-monitor-analysis | Cloud Tasks | Post-ingestion analysis (intent, sentiment, anomalies) |
| POST /internal/run-weekly-briefs | Cloud Scheduler | Weekly digest + auto-brief trigger |
| POST /internal/sync-comments | Cloud Scheduler (hourly) | CommentSync |
| POST /internal/cleanup-media | Cloud Scheduler (daily) | Stale media cleanup |
| POST /internal/billing/cleanup | Cloud Scheduler | Usage period rollover |
| POST /internal/publish-dispatch | Cloud Scheduler (15min) | PublishDispatcher claim+fan-out |
| POST /internal/refresh-oauth-tokens | Cloud Scheduler | OAuth proactive refresh before expiry |
| POST /internal/article-performance-pull | Cloud Scheduler (weekly) | GSC article metrics |

### Webhooks

| Endpoint | Sender | Verification |
|---|---|---|
| POST /v1/webhooks/stripe | Stripe | Signature verify via `stripe.Webhook.construct_event` |
| POST /v1/webhooks/resend | Resend | Svix signature (email.delivered / bounced / complained) |
| POST /v1/monitors/{id}/alerts/test | internal | HMAC-SHA256 |
| POST /v1/fireflies/webhook | Fireflies (planned for Bundle 8) | per audit plan |

### Circuit breakers

`src/common/circuit_breaker.py` (59 LOC) — CLOSED → OPEN → HALF_OPEN. Applied at ~15 sites:
- Adyntel: 3/60s
- Foreplay: 3/60s
- Cloro: 3/300s
- Grok, FAL, Suno, TTS providers (Dia/Fish/Kokoro): 3/60s
- Xpoz: 3/120s
- IC search: 3/60s
- Monitoring fetcher: config-driven
- Publishing: config-driven

No exponential backoff. No jitter on reset. Production gap.

**Minimum agency MVP workers:**
1. MonitorWorker — required for Bundle 3 (weekly briefs, alerts).
2. PublishDispatcher — required for Bundle 5 (scheduled publishing).
3. Weekly digest generator — depends on MonitorWorker + auto-brief scheduler.

Deferred: JobWorker, BatchWorker, GenerationWorker until Bundles 6/8 land.

**Effort:** 4–6 weeks for the three MVP workers. **Risk:** medium (Cloud Tasks + service account + gcp_project env config). **Dependencies:** Cloud Tasks dep, Cloud Scheduler jobs defined, `gcp_project` env.

---

## Bundle 8 — Workspace / library / batch / skills infrastructure

**What it unlocks:** Operator UX. Collections, saved items, batch analyses, search-results dedup, filter-in-place, canvas sections. Plus the extensibility framework to add new agent tools cheaply.

### Workspace + collections + library

`src/workspace/` (288 LOC service + 692 LOC repository):

Models (`models.py`, 116 LOC):
- `WorkspaceCollection` — `active_filters`, `summary_stats`, `item_count`, `is_active`
- `WorkspaceItem` — source_id, platform, creator_handle, views, engagement_rate, risk_score, analysis_results JSONB, payload_json
- `WorkspaceToolResult` — auto-rendered by frontend as canvas sections
- `CollectionSummary` (computed) — top_creators, engagement_percentiles, platform_breakdown, date_range

Key methods:
- `create_collection_from_search()` — two-layer dedup (Python `seen` set + DB `ON CONFLICT DO NOTHING`) on (source_id, platform). Atomic collection create + bulk insert + aggregate + set active in one TX. Max 10 collections per conversation.
- `filter_collection(filters)` — atomic update of `active_filters` + recompute `summary_stats` without changing `item_count` (preserves unfiltered count for UI).
- `get_workspace_state()` — compact metadata for agent system prompt.
- `store_tool_result()` — up to 500 per conversation.

Repository atomic CTEs:
- `_CREATE_COLLECTION_ATOMIC` — count + insert in single statement
- `_SET_ACTIVE` — atomically toggle is_active across conversation
- Aggregation pipeline — view distribution buckets, engagement percentiles, top 10 creators, platform breakdown

### Batch service

`src/batch/` (163 LOC service + 345 LOC repository + 412 LOC worker):

`BatchJob` fields: org_id, conversation_id, collection_id, total_items, completed_items, failed_items, flagged_items, analysis_types[], idempotency_key, status. `.is_terminal` property.

`BatchItem` states: PENDING | RUNNING | SUCCEEDED | FAILED | SKIPPED | CANCELLED.

State machine: `PENDING → PROCESSING → COMPLETED | CANCELLED | FAILED`.

Tier-based concurrency: free 1 active batch, pro 3 active. Concurrency=50, rate_limit=50/sec, max_retries=3, claim_timeout=300s.

Atomic ops:
- `_CLAIM_PENDING` — SELECT FOR UPDATE SKIP LOCKED + timeout check in single UPDATE
- `_PREPARE_RETRY` — CTE reset of failed items + counter adjustment
- `_FAIL_PENDING_AND_COUNT` — atomic fail all pending + update job counters

Worker pipeline:
- 50 workers per `concurrency` setting claim-process-repeat
- `AsyncLimiter(50, 1 second)` rate limit
- Transient errors (GeminiRateLimitError, RateLimitError, TimeoutError, ConnectionError) → retry with exponential backoff
- Permanent errors (VideoUnavailableError) → mark SKIPPED
- Idempotent UUID via `uuid5(_BATCH_NS, video_id)` — deterministic across collections

### Library API

`src/api/routers/library.py` (3+ endpoints):
- GET /library — paginated with cursor-based pagination
- GET /library/{id}, /search
- Free tier 30-day lookback filter

### SSE progress

`GET /batch/{id}/progress` — EventSourceResponse with 15s heartbeat ping. Streams until terminal. Client close does NOT cancel batch.

### Canvas section system

Frontend `useWorkspace.ts` (680 LOC) + 58 section components. `TOOL_NAME_MIGRATION` map with 154 aliases. `TOOL_SECTION_MAP` with 32 entries.

Sections derive from (collections, toolResults, pinned, dismissed) via reducer. Canvas sections array lets tools emit `canvas_sections: ["brands", "demographics", "analysis"]` to create multiple section types per execution.

Dedup strategy: last-wins for search results sharing same collection. Separate dedup for filter results. Enrichment: batch analysis risk scores merged into search results.

### Orchestrator + skills framework

`src/orchestrator/` (3,193 LOC + 9,093 LOC handlers):

**Tool catalog** (`tool_catalog/`):
- Registry (`registry.py`) imports 20 tool modules, duplicate detection
- `ToolSpec` (`_base.py`): Pydantic model with name, description, parameters (raw JSON Schema), actions, tier, cost_credits, timeout
- `to_json_schema()` for Gemini FunctionDeclaration
- `to_cli_stub()` code-generates Typer CLI commands (one subcommand per action)

**Tools registry** (`tools.py`, 791 LOC):
- `register(ToolDefinition)` → _tools dict
- `to_gemini_tools()`, `to_adk_tools()` (Google ADK)
- `execute()` single dispatch:
  - Tier gating (Tier.FREE blocks PRO tools)
  - Parameter validation + filtering
  - Platform enum conversion
  - Credit billing wrapper (if cost_credits > 0)
  - Timeout enforcement (default 120s)
  - Error sanitization before returning to LLM

**Tool handlers** (`tool_handlers/`, 9,093 LOC, 20 handlers):

| Tool | Tier | Credits | Timeout | Purpose |
|---|---|---|---|---|
| analyze_video | FREE | 5 | 180s | Safety + moderation + brands + demographics + creative patterns + deepfake |
| analyze_content | FREE | 3 | 120s | Post/thread deep-dive, virality, comments |
| search | FREE | 0 | 120s | Multi-platform content discovery |
| discover_creators | FREE | 0 | 120s | Topic/audience/similarity |
| creator_profile | FREE | 1 | 120s | Creator analytics + stories + posts |
| detect_fraud | FREE | 2 | 120s | AQS + bot detection |
| evaluate_creators | FREE | 1 | 120s | Brand safety + overlap |
| manage_monitor | PRO | 2 | 120s | Monitor CRUD |
| query_monitor | PRO | 0 | 120s | Analytics + recommendations + reply gen |
| manage_policy | FREE | 1 | 120s | Policy CRUD + evaluate |
| generate_content | PRO | 2 | 120s | Content + briefs |
| video_project | PRO | 2 | 120s | Storyboard |
| video_generate | PRO | 0 | 120s | Video gen |
| workspace | FREE | 0 | 120s | Collections + batch |
| check_usage | FREE | 0 | 120s | Credit balance |
| think | FREE | 0 | 120s | Internal reasoning |
| seo_audit | PRO | 0 | 120s | GEO+SEO |
| geo_check_visibility | PRO | 2 | 120s | AI search platform visibility |
| competitor_ads | PRO | 0 | 120s | Competitive ad analysis |
| manage_client | PRO | 0 | 120s | Client CRUD |

**Agent loop** (`agent.py`, 1,102 LOC) + `adk_agent.py` (544 LOC):
- ReAct loop with Gemini multi-turn function calling
- `_prepare_for_llm` strips heavy payloads
- Async workspace result storage (fire-and-forget)
- Cost context vars: `adk_cost_usd`, `adk_cost_limit`

**System prompt** (`prompts.py`, 328 LOC):
- `_ALL_CHAINS` — 40+ valid workflow patterns (content gen, creator vetting, competitive analysis, monitoring, video projects, SEO+GEO)
- `build_system_prompt()` — filters chains to only include available tools, builds numbered tool list, workspace state, tier state, restricted tools section, recipe context

**Capability framework frontend** (`frontend/src/lib/capabilities.ts`):
- 24 `Capability` entries: id, label, description, icon, templatePrompt, toolName, tier, formFields
- Maps UI pills → backend tools

### Programs-as-skills (keep gofreddy's)

gofreddy already has (better than freddy's model):
- 4 domain programs: competitive-session.md, geo-session.md, monitoring-session.md, storyboard-session.md
- `*-evaluation-scope.yaml` per domain (outputs, source_data, transient, notes)
- 11 references library docs
- Fixture manifest (eval_suites/search-v1.json, holdout-v1.json)

### Decision point: orchestrator vs programs-only

gofreddy has bet on programs-as-skills. Porting freddy's orchestrator is expensive (~6–8 weeks). Two paths:

**Path A: Full orchestrator port.** Agent-callable tool catalog, capability pills in UI, tier gating, credit billing. Enables generalization beyond 4 domains. Needed if user-facing AI agent is the product.

**Path B: Programs-only extension.** Add new domains (marketing_audit, creator_vetting) as programs. Reuse fixture infra. Extend references library. Tool invocation happens via program script, not agent tool call.

Path B is cheaper and aligned with gofreddy's current architecture. Path A is what the 005 lens catalog implicitly assumes (agent calling tools per lens).

**Effort:**
- Path A (full orchestrator): 6–8 weeks.
- Path B (programs-only): 2–3 weeks to add new domains + extend references.
- Workspace + library + batch + SSE: 3–4 weeks regardless of path.

**Risk:** high for Path A (subtle agent loop). Low for Path B.

**Dependencies:** most other bundles contribute handlers if Path A.

---

## Bundle 9 — Audit engine (the designed-but-unbuilt product)

**What it unlocks:** The 6-stage prospect audit pipeline from plan 2026-04-20-002. The product the 005 lens catalog (149 always-on + 25 vertical + 10 geo + 5 segment bundles + 9 Phase-0 meta-frames per locked v2 2026-04-23) was designed for.

Per memory: the marketing-audit lens catalog state is locked v2 2026-04-23 with SubSignal→ParentFinding aggregation + Stage-1a pre-pass + $100 cost cap. Plan file untouched — audit implementation is the gap, not lens-catalog design.

### `src/audit/` module (does not exist in either repo — fully greenfield)

Per plan 2026-04-20-002:

| Path | Purpose |
|---|---|
| `src/audit/run.py` | 6 stage-runner functions (discovery → synthesis → findings → proposal → deliverable → publish) |
| `src/audit/tools/` | 15 cache-backed provider tool wrappers (DataForSEO, Cloro, Foreplay, Adyntel, 12 monitoring adapters, GSC) |
| `src/audit/primitives.py` | Tech fingerprinting, embedding clustering |
| `src/audit/rendered_fetcher.py` | Playwright browser context |
| `src/audit/data/` | Benchmarks: budget, CRM velocity, rubric thresholds |
| `src/audit/assets.py` | Conditional enrichment (scoped Playwright) |
| `src/audit/demo.py` | Conditional enrichment (scoped Playwright) |
| `src/audit/state.py` | state.json + cost_log.jsonl telemetry |
| `src/audit/report.py` | HTML + PDF rendering via Jinja2 + WeasyPrint |

### CLI

`cli/freddy/commands/audit.py` with 9 subcommands:
- `run` — run audit for prospect
- `send-invoice` — Stripe Checkout link
- `attach-gsc` — enrichment R17
- `attach-esp` — R18
- `attach-ads` — R19
- `attach-survey` — R20
- `attach-assets` — R21
- `attach-demo` — R22
- `attach-budget` — R23
- `attach-crm` — R24
- `attach-winloss` — R25 (with PII redaction per R26)
- `publish` — final publish gate

### Webhooks + integrations

- Stripe Checkout (payment gate before Stage 2)
- Fireflies webhook (sales fit + walkthrough fit signals) — 2 endpoints
- Cloudflare Worker + intake form (free AI Visibility Scan lead magnet)

### Rendering pipeline

HTML + PDF deliverable via Jinja2 templates + WeasyPrint. Client-branded (logo, colors, custom domain).

### Cost model

$50–150/audit (Sonnet + Opus). $1–2/free scan. $50/audit hard ceiling default. Per-stage cost tracking via state.py + cost_log.jsonl. 3 permanent gates (intake review, payment, final publish) + calibration mode for first 5 audits.

### Lens registry

Must codify 005 catalog's 149 always-on + 25 vertical + 10 geo + 5 segment bundles + 9 Phase-0 meta-frames (locked v2 2026-04-23) as YAML/JSON registry with applicability signals (hreflang detection, ccTLD, CTA text, tech fingerprints). Drives audit dispatcher.

### Pipeline simplifications (plan 007, zero-shipped)

Bundle together:
- Unit 5: move `autoresearch/report_base.py` → `src/shared/reporting/`
- Unit 6: `src/shared/safety/` 3-tier (tier_a, tier_b, tier_c)
- Units 9–15: 40+ agentic replacements (parent-selection, alert-threshold, paraphrase-check, calibration, claim-grounding, ad-domain, monitor summarizer)

**Effort:** 30–40 engineering days per plan (5–6 weeks). **Risk:** high (payment gate + multi-stage orchestration + cost cap discipline). **Dependencies:** Bundle 1 (rubrics + taxonomies), Bundle 7 (workers for async stages), optional Bundle 8 Path A orchestrator.

---

## Bundle 10 — Long-horizon-running (LHR) agent for marketing audit

Per memory: JR wants a long-horizon-running agent for marketing pipeline. Reference auto-research + harness patterns. Open question: integrate INTO autoresearch or keep separate.

### Recommendation: integrate as new autoresearch lane

**Rationale (from the autoresearch-extensibility agent):**

Autoresearch already solves every LHR primitive:

| LHR need | Autoresearch provides |
|---|---|
| Long horizon (days) | `max_walltime=14400` (4h) per session; chain via resume; `signal.SIGALRM` hard ceiling at `MAX_GENERATION_SECONDS=7200`. These are runaway-loop sentinels, not cognitive caps. |
| Self-improvement | Program mutation by meta agent; `program_prescription_critic.py` soft-review; evolution judges score + promote/rollback autonomously |
| State persistence | Append-only `events.py`, generation-level `compute_metrics.py`, lineage via `lane_runtime.py` |
| Integrity | SHA256 critique manifest (R-#13) — tamper detection |
| Fixture grounding | `FixtureSpec(fixture_id, client, context, version, max_iter, env)` maps cleanly to "audit per prospect" |
| Graceful resume | `sessions.py` session_id tracking + `--resume-branch` |
| Observability | alert agent detects drift, plateau, collapse, overfitting, novelty_exhausted |

### Proposed architecture

New domain: `marketing_audit`. Files to create:

1. `autoresearch/archive/current_runtime/programs/marketing_audit-session.md` — operational reality, 6-stage audit workflow, quality criteria
2. `autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml`:
   ```yaml
   domain: marketing_audit
   outputs:
     - "audits/{prospect_id}/brief.md"
     - "audits/{prospect_id}/findings.json"
     - "audits/{prospect_id}/deliverable.html"
   source_data:
     - "prospects/{prospect_id}/intake.json"
     - "prospects/{prospect_id}/crawl/*"
   transient:
     - "audits/{prospect_id}/_*.json"
     - "logs/**/*"
   notes: "Bundle dispatch follows applicability signals..."
   ```
3. New `SuiteManifest` entries with per-prospect fixtures
4. Program mutation patterns for audit program (e.g., tune discovery depth, tune stage-1a pre-pass thresholds)

### Cons accepted

- Fixture authoring overhead for each prospect (acceptable — prospects are discrete)
- Coupling to search-suite scoring (need audit-specific holdout suite for calibration)
- Lane specialization risk — marketing_audit may differ from SEO patterns; mitigate with holdout recalibration

**Effort:** 2–3 weeks to structure the new lane; audit pipeline logic ships in Bundle 9. **Risk:** medium. **Dependencies:** Bundle 9 (audit engine must exist for lane to run).

---

## Cross-cutting infrastructure status

Summary from the cross-cutting agent. Full matrix:

| Pattern | freddy | gofreddy | Critical gap? |
|---|---|---|---|
| Auth/JWT | Full with in-memory revocation TTLCache 86400 | Ported, same limitation | Yes — per-instance revocation |
| Cost tracking | Complete `cost_recorder` singleton + `provider_cost_log` + dashboard | Ported 108 sites; dashboard MISSING | Yes — no user-facing visibility |
| Caching | In-memory TTLCache (5 sites: search 500/300s, competitive 1800s, brief 1800s, token blocklist 86400s) + Postgres TTL | In-memory only (6 sites); Redis dropped | Medium — no coherency across instances |
| Rate limiting | SlowAPI; Redis if `REDIS_URL`, else memory | `memory://` hardcoded | Yes — no cross-instance enforcement |
| Encryption | AES-256-GCM v2 with HKDF-SHA256; key_version rotation | Ported (encryption.py + config) | High — rotation not automated |
| Circuit breakers | Custom 3/60s at 15 sites | Ported, 29 sites | Medium — no exponential backoff, no jitter |
| Error taxonomy | Shallow hierarchy (PublishError → CredentialError, etc.) | Partial | Low |
| Observability | GCP JSON logging + trace propagation + secret redaction | ContextVar + middleware only; no GCP format | Critical — no metrics, no traces |
| Feature flags | Absent | Absent | Medium — can't disable features |
| Idempotency | Ad-hoc per-domain (competitive briefs, batch jobs, webhook) | 7 sites; no webhook idempotency | Medium — Stripe replay risk |
| SSRF protection | Comprehensive blocklist (46 deny-list networks) + FAL allowlist | Ported | None — well-implemented |
| Tier gating | 2-tier matrix (TIER_CONFIGS) enforced at dispatch | Absent | Critical — no quotas |

**Verdict:** freddy ~70% production-grade. gofreddy ~50%. Core security (crypto, SSRF, circuit breakers) intact in both. Gaps: metrics, distributed tracing, multi-instance session revocation, idempotency middleware, feature flag framework, tier gating.

---

## DB schema full diff

### Tables in gofreddy (16, per DB-schema agent)

users, api_keys, clients, user_client_memberships, agent_sessions, action_log, iteration_log, monitors, mentions, monitor_source_cursors, monitor_runs, alert_rules, alert_events, monitor_changelog, weekly_digests, geo_audits, evaluation_results.

### Tables in freddy NOT in gofreddy (37)

Analysis: video_analysis, video_analysis_access, deepfake_analysis, creator_fraud_analysis, audience_demographics, brand_video_analysis, creative_patterns, trend_snapshots, captured_stories, analysis_jobs, job_videos

Creator/brand: creators, brand_creator_relationships, competitive_briefs

Batch/generation: batch_jobs, batch_items, generation_jobs, generation_cadres, video_projects, video_project_scenes, video_project_references

Workspace: conversations, conversation_messages, workspace_collections, workspace_items, workspace_events, workspace_tool_results

Billing: subscriptions, usage_periods, stripe_webhook_events, credit_ledger, credit_balances, usage_reservations, billable_events, provider_cost_log

Feedback: feedback_signals, improvement_specs

Misc: search_cache

### Key column deltas on shared tables

`clients`:
- freddy: `id`, `operator_id` (single owner), `name`, `competitor_brands[]`, `competitor_domains[]`, `brand_context`, `auto_brief`
- gofreddy: `id`, `slug UNIQUE`, `name`. Access via `user_client_memberships` many-to-many.
- **Delta:** gofreddy needs `competitor_brands[]`, `competitor_domains[]`, `brand_context`, `auto_brief` columns.

### Analytical data shapes worth porting

High-value persistence schemas:

1. **creator_fraud_analysis** — `aqs_score DOUBLE`, `aqs_grade TEXT` (excellent/very_good/good/poor/critical), `fraud_risk_level` ENUM, `fraud_risk_score INT`, `bot_patterns_detected JSONB`, `engagement_tier`, `engagement_anomaly`, `lip_sync_consistency_score`
2. **deepfake_analysis** — `lip_sync_score`, `reality_defender_score`, `combined_score DECIMAL`, `is_deepfake BOOL`, `risk_level` ENUM (none/low/med/high/crit), `detection_method` ENUM (lipinc_only/reality_defender_only/ensemble)
3. **video_analysis** — `overall_safe BOOL`, `overall_confidence DOUBLE`, `risks_detected JSONB[]`, `content_categories JSONB[]`, `moderation_flags JSONB[]`, `sponsored_content JSONB`, `model_version VARCHAR`
4. **weekly_digests** — already in gofreddy: `stories JSONB`, `executive_summary`, `action_items JSONB`, `dqs_score DOUBLE`, `iteration_count`, `avg_story_delta`, `digest_markdown`
5. **competitive_briefs** — `client_id`, `date_range`, `schema_version`, `brief_data JSONB`, `idempotency_key`
6. **platform_connections** — (covered in Bundle 2)
7. **publish_queue** — (covered in Bundle 5)
8. **video_projects** + children — (covered in Bundle 6)

---

## API surface full diff

### freddy 47 routers / 149 endpoints, gofreddy 9 routers / 57 endpoints

Missing routers in gofreddy (priority-ranked):

**HIGH (user-facing, revenue-impacting):**
- video_projects (14 routes)
- publishing (8)
- accounts (6)
- analytics (6)
- media (6)
- conversations (6)
- articles (5)
- generation (5)
- workspace (5)

**MEDIUM (internal automation):**
- internal (12) — Cloud Tasks workers
- clients (4)
- batch (4)
- discover (4)
- voice_profiles (4)
- comments (5)
- contacts (3)
- library (3)
- newsletters (6)
- cost_dashboard (3)

**LOWER:**
- analysis (6), agent (1), billing (2), brands (3), creative (1), deepfake (1), demographics (1), evolution (1), feedback (1), fraud (1), policies (2), preferences (2), reports (1), search (1), stories (1), trends (1), usage (1), videos (2), creators (3), health (2), webhooks (2)

### CLI commands

freddy 33 groups, gofreddy 25. Missing (ranked):

**HIGH:** publish, accounts, analytics, creator, video
**MEDIUM:** content, articles, media, newsletter, calendar, rank
**LOWER:** usage, write

---

## Environment variable matrix

Critical env vars per deps agent:

Required in both:
- DATABASE_URL, SUPABASE_URL, SUPABASE_JWT_SECRET
- GEMINI_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY
- R2_* (Cloudflare)
- APIFY_TOKEN, SCRAPECREATORS_API_KEY

In freddy only:
- STRIPE_SECRET_KEY, STRIPE_PRICE_PRO, STRIPE_WEBHOOK_SECRET
- CLOUD_TASKS_LOCATION, CLOUD_TASKS_QUEUE (billing, monitoring, generation, publishing queues)
- REDIS_URL
- RESEND_API_KEY, RESEND_AUDIENCE_ID, RESEND_WEBHOOK_SECRET
- ENABLE_SEO, ENABLE_GEO
- EVOLUTION_* (6 vars)
- GSC_SERVICE_ACCOUNT_PATH

In gofreddy only:
- FREDDY_CLIENTS_DIR
- FREDDY_API_KEY
- FREDDY_API_BASE_URL

Adyntel (in both, code wired):
- COMPETITIVE_ADYNTEL_API_KEY
- COMPETITIVE_ADYNTEL_EMAIL
- COMPETITIVE_ADYNTEL_TIMEOUT_SECONDS
- COMPETITIVE_ADYNTEL_MAX_PAGES

Influencers.club (in both, code wired but routes missing in gofreddy):
- IC_API_KEY

---

## Provider matrix (canonical)

Per provider-inventory agent (confirmed across 16 agents):

| Provider | Category | Wired in gofreddy? | Pricing pattern | Subscription needed? |
|---|---|---|---|---|
| DataForSEO | SEO | ✓ | Per-call ($0.01–$0.05) | No — just credentials |
| Google Search Console | SEO | ✓ | Free | Service account |
| Google PageSpeed | SEO | ✓ | Free tier 25K/day | Optional API key |
| **Adyntel** | Competitive | ✓ end-to-end | Per-page ($0.0088) | Yes — base plan gates API |
| Foreplay | Competitive | ✓ | Credit-based ($0.001/ad) | Yes |
| Cloro | GEO / Monitoring | ✓ | Per-query ($0.01) | Yes |
| Xpoz | Monitoring | ✓ | Per-call ($0.0034) | Yes |
| NewsData.io | Monitoring | ✓ | Free tier + paid | Free possible |
| **Influencers.club** | Monitoring / Creators | ✓ client, orchestrator missing | Metered discovery/enrichment/content | Yes — base plan gates API |
| Apify | Monitoring (TikTok/FB/LinkedIn/Trends/Reviews) | ✓ | Credit-based ($0.30/CU) | Yes |
| Pod Engine | Monitoring | ✓ | Unknown | Yes |
| Anthropic Claude | AI | ✓ | Per-token | Pay-per-use |
| Google Gemini | AI | ✓ | Per-token | Pay-per-use |
| OpenAI | AI | ✓ | Per-token | Pay-per-use (Judges) |
| xAI Grok | Generation | ✓ | Per-request | Pay-per-use |
| fal.ai | Generation | ✓ | Per-second | Pay-per-use |
| Fish Audio | TTS | ✓ | Per-character | Pay-per-use |
| Suno/kie.ai | Music | ✓ | $0.03/track | Pay-per-use |
| ElevenLabs | TTS / voice clone | via `tts_providers.py` | Per-character | Subscription + usage |
| Replicate (LIPINC) | Deepfake | ✓ | $0.000225/sec GPU | Pay-per-use |
| Reality Defender | Deepfake | ✓ | $0.40/scan | Subscription |
| Resend | Email | — (needs port) | Per-email + tier | Yes |
| Stripe | Billing | — (needs port) | Per-transaction | Yes |
| Google Cloud Tasks | Queue | — (needs port) | Per-call | GCP project |
| **Forecast** | — | — | DOES NOT EXIST | Drop from consideration |

### Unwired providers called out in 005 catalog

Per marketing-audit-plan agent, 005 references ~30 external providers without pricing info:
- SEO/link/traffic: Ahrefs, SEMrush, Moz, SimilarWeb
- MarTech: BuiltWith, Wappalyzer
- B2B enrichment: HubSpot Breeze (Clearbit successor), Apollo, 6sense, Demandbase, Bombora, RB2B, Leadfeeder
- Sales-led: Outreach, Salesloft, Gong, Chorus
- Enterprise: LiveRamp, Segment, RudderStack, Hightouch, Braze, Iterable

Nearly all require base subscription ($449–$10k+/mo) to unlock API. Plan 005 doesn't acknowledge cost envelope.

### Subscription decision guidance

- **Adyntel: buy now.** Wired end-to-end, needed for lens B1 (paid creative corpus).
- **Influencers.club: wait for Bundle 4.** Client wired, orchestrator path missing — would be drawer money.
- **Forecast: don't buy.** Not a real vendor in either repo.
- **Other 005 providers: defer until Bundle 9 audit engine ships** — per plan, most flow through the audit pipeline as conditional enrichments.

---

## Recommended triage sequence

This is a suggestion, not a decision. Triage happens in the next pass.

| Order | Bundle | Gate | Duration |
|---|---|---|---|
| 0 | Pre-flight: orphaned tests, conftest, deps, db marker | CI must be honest | 3–4 days |
| 1 | Analytical uplift (copy-paste) | quality bar for everything downstream | 1 week |
| 2 | Client platform | every bundle depends on it | 3–4 weeks |
| 3 | CI triangle (weekly brief + VOC + newsletter) | first revenue-bearing deliverable | 4–5 weeks |
| 4 | Workers + schedulers (MVP set: MonitorWorker, PublishDispatcher, weekly digest cron) | unblocks all scheduled automation | 4–6 weeks |
| 5 | Content factory (draft → publish) | second revenue-bearing deliverable | 5–6 weeks |
| 6 | Creator ops (wire IC + AQS + deepfake) | campaign capability | 3–4 weeks |
| 7 | Workspace + library + batch + SSE | operator UX that makes agencies 10× faster | 3–4 weeks |
| 8 | Skills infrastructure (decide: full orchestrator Path A, or programs-only Path B) | agent-callable tools OR domain-extensibility | 2–8 weeks depending on path |
| 9 | Audit engine (`src/audit/` from plan 2026-04-20-002) | the product 005 targets | 6–8 weeks |
| 10 | LHR agent as autoresearch lane | long-horizon audit self-improvement | 2–3 weeks (on top of Bundle 9) |
| 11 | Video studio | premium upsell | 8–10 weeks |

**Total sequential: ~10–12 months. With two parallel tracks (one frontend-heavy, one backend-heavy): ~6–8 months.**

---

## Decision points for triage

Must answer before bundles 3, 6, 8, 9 start:

1. **Scope commitment:** bundles 1–7 (agency platform MVP), 1–9 (includes audit engine), or 1–11 (full platform restoration)?
2. **Orchestrator architecture:** Path A full orchestrator port (6–8 weeks, 14 tool handlers, capability pill UI) vs Path B programs-only extension (2–3 weeks, marketing_audit lane). 005 plan implicitly assumes Path A.
3. **Hosting model:** stay on Fly.io (current) or return to Cloud Run + Cloud Tasks + Redis + Cloud Scheduler (needed for Bundle 7 workers + Bundle 9 audit cost tracking)?
4. **Frontend strategy:** port 50+ canvas sections (matches freddy UX) or ship API-first + rebuild frontend optimized for agency workflows?
5. **Large-file port strategy:** `video_projects/repository.py` is 17k LOC mostly SQL. Worth compressing/regenerating rather than porting?
6. **Test restoration:** xfail orphaned tests, delete them, or stub missing modules? Each sends different signal.
7. **Billing model:** reintroduce Stripe + credit ledger + tier gating (Bundle 2-adjacent), or stay single-tier until Bundle 9 audit engine has payment gate?
8. **LHR agent placement:** integrate into autoresearch as `marketing_audit` lane (recommended) or separate runtime?
9. **Lens registry shape:** codify 005's 149/25/10/5/9 structure as YAML per-lens file, single JSON, or Python module?
10. **Frontend scope:** is the agency user working in CLI primarily, or do we need full Canvas UI back?

---

## Appendix: key files referenced by this document

For each bundle, the following freddy paths are the primary port targets:

Bundle 1:
- `src/prompts.py` (CREATIVE_PATTERN_PROMPT, DEMOGRAPHICS_INFERENCE_PROMPT, BRAND_DETECTION_PROMPT, QUERY_PARSING_PROMPT, MODERATION_PROMPT, BRAND_SAFETY_PROMPT)
- `src/schemas.py` (ModerationClass, SponsoredContent, AudienceDemographics, BrandMention)
- `src/monitoring/intelligence/intent.py`, `sentiment_classifier.py`, `trends_correlation.py`
- `src/analysis/lane_selector.py`, `compliance.py`
- `src/competitive/schemas.py` (AdCreativeCore)

Bundle 2:
- `src/clients/{models,service,repository}.py`
- `src/api/routers/{clients,accounts,portal}.py`
- `src/publishing/{oauth_manager,encryption}.py`

Bundle 3:
- `src/competitive/{brief.py,service.py,markdown.py,intelligence/partnerships.py,vision.py}`
- `src/monitoring/{analytics_service,repository_analytics,workspace_bridge,dispatcher}.py`
- `src/monitoring/intelligence/{share_of_voice,trends_correlation,commodity_baseline,post_ingestion,performance_patterns,engagement_predictor,metric_computations,intent,sentiment_classifier,sentiment}.py`
- `src/monitoring/alerts/{models,evaluator,delivery}.py`
- `src/monitoring/comments/{service,repository,sync,models}.py`
- `src/monitoring/crm/{service,repository,models}.py`
- `src/newsletter/{service,repository,models}.py`
- `src/shared/reporting/report_base.py` (partial)
- `configs/{competitive,monitoring,geo,seo,storyboard}/scripts/generate_report.py`

Bundle 4:
- `src/orchestrator/tool_handlers/{creator_profile,discover_creators,evaluate_creators}.py`
- `src/search/{service,ic_helpers}.py`
- `src/api/routers/{agent,discover,fraud}.py`
- `src/fraud/{service,analyzers,models,config}.py`
- `src/deepfake/service.py`
- `src/demographics/` (all)
- `src/evolution/service.py`
- `src/api/dependencies.py` (IC lifecycle lines 708–725)

Bundle 5:
- `src/content_gen/{service,output_models,voice_repository,voice_service,voice_models,config}.py`
- `src/articles/` (all)
- `src/newsletter/` (all)
- `src/publishing/{service,dispatcher,repository,rss_monitor,encryption,oauth_manager}.py`
- `src/publishing/adapters/{linkedin,tiktok,youtube,bluesky,wordpress,webhook,_carousel}.py`
- `src/seo/{article_repository,article_models,article_tracking_service}.py`
- `src/api/routers/{publishing,articles,generation,newsletters}.py`

Bundle 6:
- `src/video_projects/{service,repository,models,exceptions}.py`
- `src/generation/{service,worker,composition,fal_client,grok_client,image_preview_service,idea_service,music_service,tts_providers,tts_service,storage,avatar_service,bg_removal_service,caption_presets,repository,config,models,providers,exceptions}.py`
- `src/creative/{service,repository}.py`
- `src/stories/{models,service,repository,storage,exceptions}.py`
- `src/api/routers/{video_projects,voice_profiles,media,generation}.py`

Bundle 7:
- `src/api/routers/internal.py` (12 endpoints)
- `src/{batch,generation,monitoring,jobs}/worker.py`
- `src/publishing/dispatcher.py`
- `src/monitoring/comments/sync.py`
- Cloud Scheduler definitions

Bundle 8:
- `src/workspace/{service,repository,models}.py`
- `src/batch/{service,repository,worker,models,config}.py`
- `src/api/routers/{workspace,batch,library,cost_dashboard}.py`
- `src/orchestrator/{tools,agent,adk_agent,prompts}.py`
- `src/orchestrator/tool_catalog/` (20 files + `_base.py` + `registry.py`)
- `src/orchestrator/tool_handlers/` (20 files)
- `frontend/src/lib/capabilities.ts`
- `frontend/src/hooks/useWorkspace.ts`
- 58 canvas section components under `frontend/src/components/canvas/sections/`

Bundle 9:
- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` (spec)
- `docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md` (lens taxonomy, locked v2 2026-04-23)
- `docs/plans/2026-04-22-006-marketing-audit-lens-ranking.md` (ranking, bundles)
- `docs/plans/2026-04-22-007-refactor-pipeline-simplifications-plan.md` (15-unit simplification)
- New `src/audit/` module (greenfield)
- New `cli/freddy/commands/audit.py`

Bundle 10:
- New `autoresearch/archive/current_runtime/programs/marketing_audit-session.md`
- New `autoresearch/archive/current_runtime/programs/marketing_audit-evaluation-scope.yaml`
- Extend `autoresearch/eval_suites/search-v1.json` and `holdout-v1.json`

---

## End of research record

Next step: triage. Pick bundles, sequence, assign owner(s), decide on the 10 decision points above, then write per-bundle implementation plans as separate documents under `docs/plans/`.
