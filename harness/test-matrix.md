---
phases:
  1: [A1, A2, B1, B2, B3, B4, C1]
  2: [A3, A4, A5, A6, B5, B6, B7, C2, C3]
  3: [A7, A8, A9, A10, B8, B9, B10]
tracks:
  a: [A1, A2, A3, A4, A5, A6, A7, A8, A9, A10]
  b: [B1, B2, B3, B4, B5, B6, B7, B8, B9, B10]
  c: [C1, C2, C3]
flow4: [A9, A10, B9, B10]
---

# GoFreddy QA Harness Test Matrix

CLI commands (48 across 23 modules), REST API endpoints (61 across 9 routers), and 4 frontend pages. Organized into 3 parallel evaluator tracks.

**Observation methods**: CLI → run command, check exit code + JSON/text output. API → curl with Bearer token, check HTTP status + response body. Frontend → playwright-cli page snapshot, check element presence.

**Convergence rule**: Flow 4 capabilities use dynamic inputs excluded from convergence checks. All other capabilities use fixed inputs.

**Phase scoping**: `PHASE=1` runs smoke subset (client/session CRUD + page renders). `PHASE=2` adds core flows (monitoring, evaluation, API keys). `PHASE=3` is provider-dependent (DataForSEO, Foreplay, IC — BLOCKED when keys missing).

**Capability ordering**: B1→B2→B3→B4 form a session lifecycle flow (create → list → complete → log action). B5→B6 form a monitor flow (create → query). These must run sequentially within their flow.

---

## Track A — CLI Domain

### Flow 1 (Fixed — convergence reference)

Sequential commands. Each depends on output from the previous.

| # | Command | Pass Criteria |
|---|---------|---------------|
| A1 | `freddy client new --name "Harness QA" --slug harness-qa` | Exit 0. JSON output with `id`, `slug`, `name` fields. |
| A2 | `freddy client list` | Exit 0. JSON array with at least 1 client including the harness-qa slug. |
| A3 | `freddy session start --client harness-qa` | Exit 0. JSON output with `session_id`. Backend `/v1/sessions` shows the session. |
| A4 | `freddy audit monitor --client harness-qa` | Exit 0. JSON output with monitor audit results or empty array (no monitors yet is valid). |
| A5 | `freddy sitemap --url https://example.com` | Exit 0. JSON or text output with sitemap URLs or "no sitemap found" message. |
| A6 | `freddy detect --url https://example.com` | Exit 0. JSON output with detection results (tech stack, CMS, etc.). |

### Flow 2

Independent commands, no chaining required.

| # | Command | Pass Criteria |
|---|---------|---------------|
| A7 | `freddy audit seo --url https://example.com` | Exit 0 **or** BLOCKED if DATAFORSEO_LOGIN not set. JSON with SEO scores when keys present. |
| A8 | `freddy audit competitive --query "marketing agency"` | Exit 0 **or** BLOCKED if FOREPLAY keys not set. JSON with competitive results when keys present. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Command | Pass Criteria |
|---|---------|---------------|
| A9 | `freddy scrape --url https://example.com` | Exit 0. Text or JSON with scraped page content. |
| A10 | `freddy search_content --query "content marketing trends"` | Exit 0 **or** BLOCKED if IC keys not set. JSON with search results when keys present. |

---

## Track B — API Domain

### Flow 1 (Fixed — convergence reference, sequential)

Session lifecycle flow. Must run B1→B2→B3→B4 in order.

| # | Method + Endpoint | Body/Params | Pass Criteria |
|---|-------------------|-------------|---------------|
| B1 | `POST /v1/sessions` | `{"client_name": "harness-test", "source": "harness"}` | HTTP 201. Response JSON has `id`, `status: "active"`. |
| B2 | `GET /v1/sessions` | — | HTTP 200. JSON array includes the session from B1. |
| B3 | `PATCH /v1/sessions/{id}` | `{"status": "completed"}` | HTTP 200. Session status updated to `completed`. |
| B4 | `POST /v1/sessions/{id}/actions` | `{"type": "note", "content": "harness test"}` | HTTP 201. Action logged to the session. |

### Flow 2 (Monitor flow, sequential)

| # | Method + Endpoint | Body/Params | Pass Criteria |
|---|-------------------|-------------|---------------|
| B5 | `POST /v1/monitors` | `{"name": "harness-monitor", "keywords": ["test"]}` | HTTP 201. Response has `id`, `name`. |
| B6 | `GET /v1/monitors` | — | HTTP 200. JSON array includes the monitor from B5. |

### Flow 3

| # | Method + Endpoint | Body/Params | Pass Criteria |
|---|-------------------|-------------|---------------|
| B7 | `POST /v1/api-keys` | `{"name": "harness-key"}` | HTTP 201. Response has `key` (shown once) and `id`. |
| B8 | `POST /v1/evaluation/evaluate` | `{"url": "https://example.com"}` | HTTP 200 **or** BLOCKED if GOOGLE_API_KEY not set. JSON evaluation results when key present. |

### Flow 4 (Dynamic — excluded from convergence)

| # | Method + Endpoint | Body/Params | Pass Criteria |
|---|-------------------|-------------|---------------|
| B9 | `POST /v1/geo/audit` | `{"query": "marketing agency", "location": "us"}` | HTTP 200 **or** BLOCKED if GOOGLE_API_KEY not set or GEO disabled. |
| B10 | `POST /v1/competitive/ads/search` | `{"query": "marketing"}` | HTTP 200 **or** BLOCKED if FOREPLAY keys not set. |

---

## Track C — Frontend Domain

Page tests. No chat interaction — navigate directly via URL with `?__e2e_auth=1`.

| # | Action | Route | Pass Criteria |
|---|--------|-------|---------------|
| C1 | Navigate to login page | `/` or `/login` | Page renders. Supabase OAuth button visible. No console errors. |
| C2 | Navigate to sessions page | `/sessions?__e2e_auth=1` | Page renders with E2E bypass. Session list visible (or empty state). Filter controls present. No console errors. |
| C3 | Navigate to settings page | `/settings?__e2e_auth=1` | Page renders. API keys section visible. No console errors. |

---

## Cross-Cutting Checks

After every capability test, the evaluator MUST:

1. **CLI**: Verify exit code is 0 (or expected non-zero). Verify output is valid JSON where expected.
2. **API**: Verify HTTP status code matches expected. Verify response body structure.
3. **Frontend**: Run `playwright-cli console` and check for unhandled errors. Verify page is not blank.
4. **BLOCKED grading**: If a capability requires API keys (DataForSEO, Foreplay, IC, GOOGLE_API_KEY) that are not set, grade as BLOCKED, not FAIL.

---

## Capability Coverage Summary

| Track | Capabilities | Count |
|-------|-------------|-------|
| A (CLI) | client new/list, session start, audit monitor/seo/competitive, sitemap, detect, scrape, search_content | 10 |
| B (API) | sessions CRUD, monitors CRUD, api-keys, evaluation, geo audit, competitive ads | 10 |
| C (Frontend) | Login, Sessions, Settings pages | 3 |

**Total**: 23 capabilities across 3 domains
