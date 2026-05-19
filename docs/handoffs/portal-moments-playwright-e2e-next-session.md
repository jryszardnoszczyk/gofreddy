---
title: "Portal-moments redesign — Playwright E2E validation next session"
type: handoff
status: ready
date: 2026-05-19
owner: JR
related:
  - docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
  - docs/runbooks/portal-client-onboarding.md
  - PR #61
---

# Handoff: Playwright E2E for the portal-moments redesign

## Goal

Drive the new portal end-to-end through a real browser against the running
FastAPI backend + Supabase + Postgres. Validate every user-visible path the
unit + smoke tests can't cover (cookie roundtrip, EventSource SSE, drill-down
navigation, real CC session moment-flow, redaction rendering, CSP enforcement).

This is the **SC4-readiness check** — once Playwright E2E is green, the
redesign is gate-ready for the one-real-client comprehension test with Klinika
or DWF.

## What's already validated (don't re-do)

- Unit + integration tests: **356 portal-relevant tests green** locally
  (`tests/test_api/` + `tests/portal/` + `tests/scripts/test_portal_telemetry_attribute.py` +
  `tests/autoresearch/test_events.py` + `tests/audit/test_cost_thresholds.py` +
  `tests/shared/test_scrub.py`).
- Server-side smoke (operator-driven 2026-05-18, on a fresh :8001 instance):
  - Routes register: `GET /portal/{slug}`, `GET /v1/portal/{slug}/moments`,
    `GET /portal/{slug}/transcript/{sid}`, `POST/DELETE /v1/auth/cookie`.
  - Auth: 401 `missing_credentials` when unauth, 401 `invalid_token` on bad
    JWT, 401 `bad_token` on bad ingest token.
  - `/_ingest` R5.5 server-side slug validation:
    - 400 `invalid_client` on slug failing `^[a-z0-9-]{1,64}$` regex.
    - 400 `invalid_client` on slug not in `clients` table.
  - Hook attribution helper R7 (a) + (c) verified via stdin/env subprocess.
  - Tailer end-to-end: dropped CC JSONL under hyphen-free cwd
    `/tmp/clients/default/work`; within 3s `clients/default/audit/events.jsonl`
    got `kind="session_start" client_id="default"` row + sessions.jsonl
    registry row.
  - Bonus: tailer caught real Codex idle-timeout `session_end` during the run.
  - Bonus: redaction layer fired on the malformed-JWT POST attempt
    (`moment_kind="redaction_applied" redaction_kind="jwt"` audit row in
    operator-internal log).
  - CSP header on `/portal/{slug}`: `default-src 'self'; script-src 'self'; …`
  - Static assets served: `/static/portal_moments.js` (15.9 KB),
    `/static/portal_transcript.js` (2.5 KB).
- CC encoded-cwd decoder limitation surfaced: paths with `-` in any directory
  name lose info on decode → operator-internal attribution. JR's worktree
  path contains `-` (`client-portal-telemetry`), so CC sessions launched from
  the worktree itself need `GOFREDDY_CLIENT_ID=<slug>` env override.
  Documented; not a regression.

## What Playwright E2E must cover

These are the user-visible flows the headless tests can't fully validate:

### Login + cookie roundtrip

1. Visit `http://127.0.0.1:8000/portal/<slug>` while unauthenticated.
2. Assert redirect to `/login`.
3. Sign in via Supabase magic-link mock (local dev path) OR password signup
   with the seeded test user.
4. After Supabase JS returns a session, assert `POST /v1/auth/cookie` is
   fired and `sb_session` cookie is set with `HttpOnly + Secure + SameSite=Strict`.
5. Assert redirect lands on `/portal/<slug>` AFTER the cookie set succeeds
   (not before — the U4 flow is "cookie-then-redirect").
6. Reload `/portal/<slug>` — page renders without re-login (cookie persists).

### Cost-ledger header + moments timeline

7. Page-load: assert cost-ledger header populates within 300ms (SC1) with
   today / this-week / this-month USD values.
8. Empty-client state: a slug with zero moments shows the literal copy
   `No moments yet. Activity will appear here as agents work for you.`
   in dim ink-500.
9. Populated state: hit `POST /v1/portal/_ingest` (via a side curl with
   `GOFREDDY_INGEST_TOKEN`) to seed 5 moments with different `moment_kind`
   values; assert all 5 render as `<a>` rows with the right
   `k-<kind> k-mk-<moment_kind>` class combo and correct ts / session-tag /
   title.
10. Click a moment row → assert navigation to
    `/portal/<slug>/transcript/<session_id>?event_id=<event_id>` (R4 single-click).

### Drill-down + reasoning expand

11. Transcript page: assert CSP header present, no inline scripts in the DOM.
12. Reasoning rows render with `class="agent-reasoning collapsed"` by default.
13. Click a reasoning row → assert `.expanded` class toggles and body becomes
    visible.
14. `?event_id=<id>` anchor: assert the linked event is scrolled into view +
    highlighted.
15. Back link → `/portal/<slug>` re-renders the timeline (browser back button
    also tested).

### Logout + revocation

16. Click `#logout` button → assert `DELETE /v1/auth/cookie` fires with
    the cookie attached, response is 204, then `window.location = '/login'`.
17. Attempt to GET `/v1/portal/<slug>/moments` via fetch from the
    now-unauthenticated context → assert 401.
18. (Security side-channel) Try `Authorization: Bearer <stale-JWT>` on
    `/v1/portal/<slug>/moments` → assert 401 (T6: JWT was revoked by the
    DELETE).

### SSE live tail + reconnect

19. With moments page loaded, side-curl an ingest POST for a new
    `kind="moment"` row; assert it appears at the top of the timeline
    within 2 seconds (SSE prepend).
20. Force-disconnect (kill the EventSource by navigating away then back,
    or via `window.stop()`): assert reconnect indicator appears in dim
    ink-500.
21. On reconnect: assert frontend re-fetches `/moments?since=<last_seen>`
    to backfill missed rows.

### Auth-expiry edge

22. Manually expire the cookie (set `document.cookie="sb_session=; Max-Age=0"`
    via Playwright JS): assert next SSE error → 401 probe → redirect to
    `/login`.

### Redaction visible

23. Side-ingest a moment whose `metadata.title` contains a fake-but-pattern-
    matching Stripe key (`sk_test_DEADBEEF…`); assert the rendered row
    title contains `<redacted:stripe_key>` not the original.
24. (Drill-down) seed a CC transcript JSONL with a `STRIPE_SECRET=...` line in
    a `tool_result.content`; render `/portal/<slug>/transcript/<sid>`; assert
    the body shows `<redacted:stripe_key>` and the footer reads
    `N values redacted · portal-redactor v1`.

### Cross-tenant (T3 / SC3)

25. Sign in as a member of slug `A`; navigate to `/portal/B` (where B is a
    real other client this user has NO membership for); assert 403
    `no_membership`.
26. Try `/portal/A/transcript/<sid-from-B>` where the session_id is real
    but belongs to client B's registry; assert 404 `transcript_unavailable`
    (R9.1 + T3).

## Setup the next session needs

### Services

Local stack the next session should verify is running before starting:

```bash
# Supabase (port 54321)
lsof -nP -iTCP:54321 -sTCP:LISTEN

# Postgres (port 54322, container)
psql "$DATABASE_URL" -c "\dt clients" | head

# FastAPI on :8000 (or :8001 for an isolated smoke instance)
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

JR's current setup runs a supervisor loop (`scripts/run_backend.sh`, PID
38728 as of 2026-05-18) that auto-restarts uvicorn from the MAIN worktree
at `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.venv/bin/uvicorn`.
**Critical:** the supervisor runs the MAIN worktree's code, NOT this
branch's. To Playwright-validate the new portal, the next session must
either:

1. **Stop the supervisor + start uvicorn from this worktree:**
   ```bash
   # As JR (or `kill 38728` from the agent if explicitly authorized)
   # Then from this worktree:
   set -a; source /Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.env; set +a
   ./.venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 8000
   ```
2. **Or start a second instance on :8001 and point Playwright at it:**
   ```bash
   # Env was extracted from the running PID 31522 on 2026-05-18; the
   # canonical .env on main has the same values. Use that or `ps Eww`.
   GOFREDDY_INGEST_TOKEN="..." \
   DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres" \
   SUPABASE_ANON_KEY="..." \
   SUPABASE_JWT_SECRET="super-secret-jwt-token-with-at-least-32-characters-long" \
   SUPABASE_URL="http://127.0.0.1:54321" \
   ./.venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 8001
   ```

Test user / client seed (use the existing `test_tenant` fixture pattern in
`tests/test_api/conftest.py` for shape; a Playwright-friendly seed lives
TBD — the next session can either reuse a real Supabase signup or extend
conftest to a seed script).

### Tools

- The `playwright-cli` skill (available in the session's skill list) drives
  Playwright via the `agent-browser` CLI. Use it for visit + click + assert.
- `pytest-playwright` is NOT currently a dev dep; install via `uv add
  --dev pytest-playwright` if Python-driven tests are wanted instead of the
  ad-hoc CLI. (Adds `playwright` + `pytest-playwright` to the venv.)

### Files Playwright tests should land at

Suggest `tests/e2e/test_portal_moments.py` (new file; create
`tests/e2e/__init__.py`). Mark with `@pytest.mark.e2e` and add an `e2e`
marker to `pyproject.toml`'s `[tool.pytest.ini_options]` so the suite
can be skipped in CI without these services.

## Exit criteria for the next session

The Playwright suite is "passing" when all 26 scenarios above are green
against a running stack (Supabase + Postgres + FastAPI from this branch's
code). At that point:

- SC4 readiness signal: the redesign is functionally validated; only the
  real-client comprehension test (Klinika or DWF) remains as the actual
  exit gate.
- The PR description's "Post-Deploy Monitoring & Validation" section can
  reference this handoff doc as evidence of pre-merge smoke depth.

## Resume prompt (paste into a fresh session)

```
Read docs/handoffs/portal-moments-playwright-e2e-next-session.md from the
worktree at /Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/client-portal-telemetry
and drive the Playwright E2E suite per the 26 scenarios listed. Use the
playwright-cli skill. Surface any failure as a concrete fix (or a finding
to escalate to JR if it's a design question). Don't touch the supervisor
loop without asking — start a second uvicorn on :8001 instead.
```

## Current branch state (as of this handoff)

- Branch `design/client-portal-telemetry` @ HEAD (pushed; PR #61 is
  MERGEABLE, all CI green).
- 26 commits ahead of `main` covering 10 redesign units + 2 merges.
- Plan status flipped to `completed`.
- Smoke artifacts left in `clients/default/audit/events.jsonl` from the
  2026-05-18 smoke (one `kind="moment"` ingest test row, one
  `session_start` from the tailer smoke). Harmless; can be wiped before
  Playwright runs if a clean slate is wanted:
  `rm -f clients/default/audit/events.jsonl clients/default/audit/sessions.jsonl`.
- `~/.local/share/gofreddy/sessions.jsonl` registry has live data from
  real CC + Codex sessions; **do not delete** without operator approval.
