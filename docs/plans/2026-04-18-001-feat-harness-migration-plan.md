---
title: "feat: Migrate QA eval-fix harness from Freddy to GoFreddy"
type: feat
status: active
date: 2026-04-18
---

# Migrate QA Eval-Fix Harness from Freddy to GoFreddy

> **Target repo:** gofreddy. All paths repo-relative unless prefixed with `freddy:`.
> **Source repo:** freddy (`freddy:harness/` — 8 Python modules, ~4,800 lines, validated in run `20260415-143612`).

## Overview

Copy the eval-fix-verify harness from Freddy, modify Freddy-specific values to GoFreddy equivalents, implement JWT minting via GoTrue (the only new code), write GoFreddy-specific test matrix and prompt files, validate.

## What GoFreddy actually is (from code, not docs)

CLI-first agency tool. 221 Python files, ~40K lines. No chat, no SSE streaming, no agent orchestrator, no workspace/canvas. Testable surfaces:

- **48 CLI commands** across 23 modules — `freddy audit seo`, `freddy client new`, `freddy session start`, etc. Mix of direct provider calls, REST API wrappers, and local file I/O.
- **61 API endpoints** across 9 routers — sessions CRUD, monitoring (15+ endpoints), GEO audits, evaluation, competitive, API keys, auth. All real implementations, no stubs.
- **4 frontend pages** — Login (Supabase OAuth), Sessions (list+filter+actions), Settings (API keys), AuthCallback.
- **17 DB tables** across 3 migrations.
- **E2E auth bypass** — same pattern as Freddy: `VITE_E2E_BYPASS_AUTH=1` + `__e2e_auth=1` URL param.
- **Services set to None** (return 503): `webhook_delivery`, `creator_search_service`, `workspace_repository`, `seo_service`. Excluded from test matrix.
- **Empty stub dirs**: `conversations/`, `workspace/`, `extraction/`, `content_gen/`, `billing/`, `policies/`, `preferences/`.
- **Backend**: `uvicorn src.api.main:app` (no factory), `/health` only (no `/ready`), port 8080. Frontend: Vite on 5173.
- **Seed script** (`scripts/seed_local.py`): creates user+client+membership via GoTrue signup + SQL. Does NOT return a JWT.

## What copies as-is (zero changes)

- `harness/__init__.py` (2 lines)
- `harness/__main__.py` (16 lines)
- `harness/conftest.py` (1 line — `collect_ignore = ["runs"]`, prevents pytest scanning run artifacts)
- `harness/engine.py` (606 lines) ��� pure codex/claude subprocess dispatch
- `harness/scorecard.py` (533 lines) — pure YAML parsing/merging/grading
- `harness/README.md` — documentation (update GoFreddy-specific references in Unit 2)
- `tests/harness/__init__.py` — needed for pytest discovery
- `tests/harness/test_engine.py` — generic engine tests
- `tests/harness/test_worktree.py` — generic git/file tests
- `tests/harness/test_convergence.py` (287 lines) — convergence/escalation/Flow 4 tests. Mostly generic; fixture capability IDs need updating in Unit 2.

## What gets modified (find-replace Freddy → GoFreddy values)

Every change below is replacing a Freddy-specific string/value with GoFreddy's equivalent. No logic changes.

**`harness/config.py`:**
- `REQUIRED_ENV_VARS` tuple → GoFreddy's: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_ANON_KEY`, `GOOGLE_API_KEY`
- `backend_cmd` default → `"uvicorn src.api.main:app --host 0.0.0.0 --port 8080"`
- `backend_log` → `"/tmp/gofreddy-backend.log"`
- `frontend_url` → `"http://localhost:5173"`
- `tracks` → `["a", "b", "c"]`
- `fixer_domains` → `["A", "B", "C"]` (CLI, API, Frontend)

**`harness/preflight.py`:**
- Remove `/ready` health check (GoFreddy only has `/health`)
- `apply_db_schema` → run all 3 migrations idempotently: `supabase/migrations/20260417000001_init.sql`, `20260418000001_sessions.sql`, `20260418000002_autoresearch_tables.sql`. The single `scripts/setup_db.sql` only covers init — monitoring/evaluation tables need the third migration.
- `cleanup_harness_state` SQL → `DELETE FROM agent_sessions WHERE org_id = ?; DELETE FROM monitors WHERE user_id = ?; DELETE FROM geo_audits WHERE user_id = ?; DELETE FROM evaluation_results WHERE user_id = ?;` (cascading FKs clean children)
- Remove Stripe safety check
- `verify_frontend_bypass` / `refresh_vite_jwt` → port 5173, log path `/tmp/gofreddy-vite.log`
- CORS origin → `localhost:5173`
- `mint_jwt` → **new implementation** (see Unit 3)

**`harness/run.py`:**
- `_HANDLER_DOMAINS` → GoFreddy file-path mapping: `cli/freddy/commands/*` → A, `src/api/routers/*` → B, `frontend/src/*` → C, else SHARED
- `attribute_file()` → parse GoFreddy paths instead of `tool_handlers/`
- Remove Vite JWT refresh timing (E2E bypass token doesn't expire mid-run)

**`harness/worktree.py`:**
- `_MAIN_REPO_GUARDED_PREFIXES` → `("src/", "cli/", "frontend/src/")`
- Porcelain dirty set → include `cli/`
- Protected scripts → `"setup_db.sql", "seed_local.py"`
- `snapshot_backend_tree` → include `cli/freddy/` for change detection
- Symlinks → add `clients/` alongside `.venv`, `node_modules`

**`harness/prompts.py`:**
- Dry-run prompt → `"freddy client list"` / `"A-1"`

**`tests/harness/conftest.py`:**
- Env var strip list → match GoFreddy config fields

**`tests/harness/test_config.py`, `test_run.py`, `test_prompts.py`, `test_scorecard.py`, `test_convergence.py`:**
- Update default assertions (3 tracks, GoFreddy ports/paths)
- Update fixture capability IDs (A-1..A-10, B-1..B-10, C-1..C-3)
- Update domain references (file-path based, not handler-name based)
- Adapt fixture scorecard files: keep `track-a.md`, `track-b.md`, `track-c.md`, `track-failed.md`, `track-d-empty.md` (rename to `track-empty.md`), `fixes-1.md`, `fixes-2.md`, `test-matrix.md`. Delete `track-d.md`, `track-e.md`, `track-f.md` (GoFreddy has 3 tracks not 6). Update capability IDs inside each fixture.

**`tests/harness/test_preflight.py`** (665 lines):
- Update endpoint checks (`/health` only, no `/ready`)
- Update DB table names in cleanup assertions
- Update seed script references → GoTrue signup pattern
- Update Vite port/path references
- Remove Stripe safety check assertions
- This is the most Freddy-coupled test file — expect ~30-40 lines changed.

**`harness/prompts/evaluator-track-{d,e,f}.md`:**
- Delete after copy. GoFreddy uses 3 tracks (a/b/c), not 6. New track prompts written in Unit 4.

## What's genuinely new code

Only `mint_jwt` in `preflight.py` (~40-60 lines). Freddy calls `scripts/e2e_seed_auth_tokens.py` which returns JSON with `{harness_token, harness_user_id}`. GoFreddy's `seed_local.py` doesn't return a token. New implementation:

1. POST `{SUPABASE_URL}/auth/v1/signup` with `harness@local.gofreddy.ai` + password
2. If 422 (user exists), POST `{SUPABASE_URL}/auth/v1/token?grant_type=password` instead
3. Extract `access_token` + `user.id` from response
4. Ensure DB rows exist: `users` (INSERT ON CONFLICT), `clients` for `harness-test` slug, `user_client_memberships` with role `admin`
5. Return `PreflightResult(jwt_token, harness_user_id)`

Pattern: follows `scripts/seed_local.py` exactly, just returns the token instead of printing credentials.

## Implementation Units

- [ ] **Unit 1: Copy everything from Freddy**

  Copy `freddy:harness/` → `harness/` and `freddy:tests/harness/` → `tests/harness/` (including `fixtures/`). Verify `python -c "import harness"` succeeds.

- [ ] **Unit 2: Modify all Freddy-specific values**

  One pass through the copied files replacing every Freddy-specific string with GoFreddy's equivalent. All changes listed in "What gets modified" above. Update test fixtures with GoFreddy capability IDs. Run `pytest tests/harness/test_engine.py tests/harness/test_worktree.py -q` to confirm the generic tests still pass. The rest will fail until Unit 3 (preflight JWT minting) is done.

- [ ] **Unit 3: Implement GoTrue JWT minting in preflight.py**

  Replace the Freddy `mint_jwt` (calls `e2e_seed_auth_tokens.py` script) with direct GoTrue signup/signin + DB seeding. This is the only new code (~40-60 lines). Follow `scripts/seed_local.py` as the reference implementation. Handle the "user already exists" fallback (signup → 422 → signin). After this, `pytest tests/harness/ -q` should be fully green.

- [ ] **Unit 4: Write test-matrix.md + prompt files**

  **`harness/test-matrix.md`** — ~23 capabilities across 3 domains:

  Domain A (CLI, track a): `freddy client new/list`, `freddy session start`, `freddy audit monitor`, `freddy sitemap`, `freddy detect`, `freddy scrape`, `freddy audit seo` (needs DATAFORSEO key), `freddy audit competitive` (needs FOREPLAY key), `freddy search_content` (needs IC key).

  Domain B (API, track b): `POST/GET/PATCH /v1/sessions`, `POST /v1/sessions/{id}/actions`, `POST/GET /v1/monitors`, `POST /v1/api-keys`, `POST /v1/evaluation/evaluate` (needs GOOGLE key), `POST /v1/geo/audit` (needs GOOGLE key + GEO enabled), `POST /v1/competitive/ads/search` (needs FOREPLAY key).

  Domain C (Frontend, track c): Login page renders, Sessions page renders with `?__e2e_auth=1`, Settings page renders with API keys section.

  Phases: 1 = smoke (client CRUD, session CRUD, login page), 2 = core (monitoring, evaluation, API keys), 3 = provider-dependent (DataForSEO, Foreplay, IC — BLOCKED when keys missing).

  **Capability ordering**: Some capabilities are chained. B1→B2→B3→B4 form a session lifecycle flow (create → list → complete → log action). B5→B6 form a monitor flow (create monitor → query mentions). The evaluator prompt and test matrix must mark these as sequential within a flow so the evaluator doesn't try to query a monitor that doesn't exist yet. Same pattern as Freddy's "Flow 1" chained capabilities.

  **`harness/prompts/evaluator-base.md`** — Hostile QA engineer. Three observation methods: CLI (`freddy <cmd>`, check exit code + JSON), API (`curl` with Bearer token, check status + response), Browser (playwright-cli, page snapshot, element presence). Same grading rules (PASS/PARTIAL/FAIL/BLOCKED). BLOCKED for missing API keys. Same scorecard YAML format.

  **`harness/prompts/fixer.md`** — Unconstrained engineer. Context: `cli/freddy/commands/` for CLI, `src/api/routers/` for API, `src/*/service.py` for services, `frontend/src/pages/` for frontend. Backend restart recipe with `src.api.main:app`. Two hard invariants (no git state, no harness edits). `READY_FOR_VERIFICATION` signal.

  **`harness/prompts/verifier.md`** — Paraphrase defense adapted for CLI/API: vary input domains/queries/client-names instead of chat prompts. All 4 variants must produce valid output. Page tests skip paraphrasing. Fail-closed rule. YAML verdict format.

  **`harness/prompts/evaluator-track-{a,b,c}.md`** — 3 short files (~15 lines each) describing each track's scope: CLI commands, API endpoints, frontend pages.

- [ ] **Unit 5: Validate**

  `python -m harness --help` works. `pytest tests/harness/ -q` all green. Config `hasattr` sanity check. Dry-run: `python -m harness --dry-run --engine codex --cycles 1` against live GoFreddy stack — preflight passes, evaluator runs, scorecard written.

## Risks

| Risk | Mitigation |
|------|------------|
| `freddy` CLI not available in worktree | `.venv` symlink should provide it. Verify in Unit 5. |
| GoTrue signup → user already exists | `mint_jwt` falls back to signin (same as `seed_local.py`). |
| Missing provider API keys | Phase 3 capabilities graded BLOCKED, not FAIL. |
| Frontend port 5173 conflict | `FRONTEND_URL` env override. |
