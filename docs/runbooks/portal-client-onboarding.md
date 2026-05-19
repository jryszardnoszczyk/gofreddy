---
title: "Portal: onboard a new client + reviewer"
type: runbook
status: stable
date: 2026-05-18
owner: gofreddy
related:
  - docs/brainstorms/2026-05-13-client-portal-telemetry-design.md
  - docs/brainstorms/2026-05-15-portal-moments-redesign-requirements.md
  - docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md
  - src/api/routers/portal.py
  - src/api/routers/auth.py
  - src/portal/transcript_tailer.py
  - supabase/migrations/20260417000001_init.sql
---

# Portal: onboard a new client + reviewer

Walks the operator through everything the portal needs to surface
moments, costs, and transcripts for a new client. Scope is portal-only;
the broader `clients/<slug>/client.yaml` schema (content lanes,
brand_tokens, content denylists) is owned by plan-002.

## Pre-flight

| Check | Command |
|---|---|
| Supabase is reachable | `curl -s http://127.0.0.1:54321/auth/v1/health` |
| App migrations applied | `psql $DATABASE_URL -c "\dt users clients user_client_memberships"` |
| Portal tests green | `pytest tests/test_api/test_portal_moments_page.py tests/test_api/test_portal_moments.py tests/test_api/test_portal_transcript.py tests/test_api/test_auth_cookie.py tests/test_api/test_portal_stream.py tests/portal/ -q` |
| Ingest token configured | `echo "${GOFREDDY_INGEST_TOKEN:?unset}"` |

If any of those fail, fix that first — the rest of this runbook will hit
weird symptoms otherwise.

## 1. Create the client row

The portal joins on `clients.slug`. Slug format is `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
(enforced by check constraint).

```sql
INSERT INTO clients (slug, name) VALUES
  ('klinika-melitus', 'Klinika Melitus')
ON CONFLICT (slug) DO NOTHING;
```

## 2. Invite the reviewer (Supabase signup)

The reviewer needs a Supabase user record so their JWT carries a `sub`
claim the portal can resolve. Two paths:

**Production (magic-link, what the reviewer sees):**

The reviewer visits `/login`, enters their email, receives a magic link,
clicks it. On first sign-in the portal's `_resolve_user_from_jwt` upserts
into `users`. Their `users.id` is what step 3 needs.

**Local dev (no email round-trip):**

```bash
curl -s -X POST http://127.0.0.1:54321/auth/v1/signup \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"maria@klinikamelitus.pl","password":"<temporary>"}'
```

The response carries `user.id` (Supabase) — the portal will mint a `users`
row keyed by that on first authenticated request.

## 3. Grant membership

Roles: `admin` (operator/JR), `owner` (primary reviewer), `editor`,
`viewer`. Owners see their own client; admins see everything.

```sql
INSERT INTO user_client_memberships (user_id, client_id, role)
SELECT u.id, c.id, 'owner'
  FROM users u, clients c
 WHERE u.email = 'maria@klinikamelitus.pl'
   AND c.slug = 'klinika-melitus'
ON CONFLICT (user_id, client_id) DO UPDATE SET role = EXCLUDED.role;
```

Verify:

```sql
SELECT c.slug, u.email, m.role
  FROM user_client_memberships m
  JOIN users u   ON u.id = m.user_id
  JOIN clients c ON c.id = m.client_id
 WHERE c.slug = 'klinika-melitus';
```

## 4. Cookie auth flow

The portal uses an httpOnly `sb_session` cookie. EventSource and every
authed REST call ride the cookie via same-origin; the JWT is never in
the URL.

**Login round-trip:**

1. Reviewer visits `/portal/<slug>` → unauthenticated; redirected to
   `/login`.
2. `/login` runs Supabase JS `signIn`; on success it POSTs
   `{access_token: <jwt>}` to `POST /v1/auth/cookie`.
3. The server validates the JWT (same machinery as the existing
   `verify_supabase_token` — JWKS-first, HS256 fallback, `aud=authenticated`,
   `iss=<supabase_url>/auth/v1`, exp claim enforced, blocklist checked
   via `is_token_revoked`).
4. On success: sets `sb_session` with `httpOnly + SameSite=Strict +
   Secure + path=/`; `Max-Age = JWT exp − now()` clamped ≥ 0.
5. Frontend redirects to `/portal/<slug>` **only after** the cookie is set.
6. Every subsequent request to `/v1/portal/<slug>/*` and
   `/portal/<slug>/transcript/<sid>` resolves the principal from the
   cookie. `Authorization: Bearer <jwt>` and `X-API-Key` still work as
   fallback for non-browser callers (curl, scripts).

**Verify the cookie attributes:**

```bash
# In the browser devtools: Application → Cookies → sb_session
# Expect: HttpOnly=yes; SameSite=Strict; Secure=yes; Path=/.
# On http://localhost:8000 the Secure attribute is still honoured by
# modern browsers per W3C exception — verified on Firefox + Chrome.
# Older browsers may reject; the runbook deliberately does NOT
# work around that.
```

**Force a logout (operator-side):**

- `DELETE /v1/auth/cookie` — clears the cookie AND revokes the JWT via
  `is_token_revoked`. Subsequent `Authorization: Bearer <same-jwt>`
  attempts will 401 until the JWT exp passes naturally.
- Last-resort: rotate the Supabase JWT secret. Invalidates every issued
  JWT immediately; all reviewers re-login.

**Cross-origin note:** v1 is single-host. If the portal ever splits from
the API origin (subdomain or separate domain), EventSource needs
`new EventSource(url, {withCredentials: true})` AND the API must reply
with `Access-Control-Allow-Credentials: true` + an explicit allowed
origin (no `*`). SameSite=Strict on the cookie blocks cross-site CSRF
in the current single-host posture; the relax to `SameSite=Lax` (or
state-changing endpoints adding an `Origin`/`Referer` check via a
shared dependency) is plan-002's responsibility when
`review_approve`/`review_reject` ships.

## 5. Attribution precedence (env-first vs cwd-fallback)

Two mechanisms write events to a client's per-client log
(`clients/<slug>/audit/events.jsonl`):

- **Claude Code hook** (`scripts/claude-code-hooks/portal-telemetry.sh`)
  → uses `GOFREDDY_CLIENT_ID` env var first; cwd-fallback to
  `clients/<slug>/` segment if env unset.
- **Transcript tailer** (`src/portal/transcript_tailer.py`) → cwd-only.
  Reads the cwd from each new CC/Codex JSONL header (CC: decoded from
  the dirname; Codex: from the `session_meta` event). Attributes to
  the `<slug>` if cwd contains `clients/<slug>/<...>`; else writes the
  `session_start` / `session_end` to the operator-internal log
  `~/.local/share/gofreddy/events.jsonl`.

**Which to use:**

- **Interactive Claude Code session for a single client** — `export
  GOFREDDY_CLIENT_ID=klinika-melitus` for that shell, then work
  anywhere. Most reliable when working outside the client worktree.
- **Always work under `clients/<slug>/`** — let cwd-fallback +
  tailer handle attribution. Lower-friction; the env var is optional.
- **Conflict resolution** — when env says X but cwd says Y, the hook
  logs `kind="moment", moment_kind="attribution_conflict"` to
  operator-internal. The hook still writes to env-X's per-client log;
  the operator review the conflict event before trusting the row.

## 6. Transcript tailer

The tailer runs in-process with the FastAPI app — no separate service.
On `uvicorn` startup the lifespan task is created **after** the
asyncpg pool is set (the tailer's slug-validator borrows the pool).
On shutdown it's cancelled and awaited **before** the pool closes.

**Watched roots:**

- `~/.claude/projects/<encoded-cwd>/<sid>.jsonl` (CC sessions)
- `~/.codex/sessions/<...>/rollout-*.jsonl` (Codex sessions)

**Polling cadence:**

- Default 1.5s. Tunable via `export GOFREDDY_TAILER_INTERVAL_S=3.0`
  (clamped to `[0.25, 60.0]`). Sub-second latency is not a stated
  UX requirement — SC1 only bounds page-load.

**24h active-window:**

The tailer scans the watched roots on every tick, but only sessions
with JSONL mtime within the last 24h are eligible for live tailing.
Older files are registered once (so the IDOR guard can resolve them
for drill-down) and skipped on subsequent ticks. Verified on the
operator host with 308 CC project dirs + 2045 Codex rollouts — per-tick
work stays sub-millisecond.

**Session registry:**

Persisted at `clients/<slug>/audit/sessions.jsonl` (per-client) or
`~/.local/share/gofreddy/sessions.jsonl` (operator-internal for
sessions without a client). Append-only; two row shapes:

```jsonl
{"session_id": "...", "client_id": "klinika-melitus", "source": "cc", "file_path": "/abs/...", "started_at": "...", "hook_emitted": false}
{"session_id": "...", "ended_at": "...", "reason": "idle_timeout"}
```

Rebuilt from disk on startup via the latest-row-per-session-id rule.
Crash mid-tick → next startup picks up where we left off.

**Boundary detection:**

- `session_start` on first-time-seen file (after sanity-parse).
- `session_end` whichever fires first: idle timeout (10 min stale mtime
  AND no size growth across 3 ticks) OR Codex `task_completed` /
  `task_aborted` event observed mid-tail.

**Dedup:** if the Claude Code hook (currently `tool_call`-only; future
extension may add `session_start`) wrote a `session_start` with the
same `session_id` first, the tailer skips emission and marks
`hook_emitted=true` on the registry row.

**Inspect:**

```bash
tail -f clients/klinika-melitus/audit/sessions.jsonl
tail -f clients/klinika-melitus/audit/events.jsonl | jq -c 'select(.kind=="moment")'
```

## 7. First events + smoke procedure

A live portal needs events. Smoke path:

```bash
# 1. Authenticate as the operator (admin) and seed the cookie:
JWT=$(supabase auth signin ...)   # however you mint a JWT locally
curl -i -X POST http://localhost:8000/v1/auth/cookie \
  -H "Content-Type: application/json" \
  -c /tmp/portal_cookies.txt \
  -d "{\"access_token\":\"$JWT\"}"

# 2. Hit the moments REST endpoint with the cookie:
curl -s -b /tmp/portal_cookies.txt \
  http://localhost:8000/v1/portal/klinika-melitus/moments | jq .

# 3. Trigger a real CC session under the client's worktree:
cd ~/Documents/GitHub/gofreddy/clients/klinika-melitus/
claude    # do a few tool calls — the tailer should emit session_start

# 4. Confirm session_start landed:
tail -1 clients/klinika-melitus/audit/events.jsonl | jq .

# 5. Drill down on a moment:
EVT=$(curl -s -b /tmp/portal_cookies.txt \
  http://localhost:8000/v1/portal/klinika-melitus/moments | \
  jq -r '.moments[0].event_id')
SID=$(curl -s -b /tmp/portal_cookies.txt \
  http://localhost:8000/v1/portal/klinika-melitus/moments | \
  jq -r '.moments[0].metadata.session_id')
curl -s -b /tmp/portal_cookies.txt \
  "http://localhost:8000/portal/klinika-melitus/transcript/$SID?event_id=$EVT" | head -40

# 6. Logout + verify revocation:
curl -i -X DELETE http://localhost:8000/v1/auth/cookie \
  -b /tmp/portal_cookies.txt
# Reusing $JWT via Authorization: Bearer should now 401.
```

## 8. Confirm portal access (reviewer view)

The reviewer hits `https://portal.gofreddy.ai/klinika-melitus` (or
`http://localhost:8000` locally). Page loads:

| Reviewer state | Result |
|---|---|
| Not signed in | Redirected to `/login` |
| Signed in, no membership | 403 `no_membership` |
| Signed in, member | Cost-ledger header + moments timeline (newest 50). Click any row → transcript drill-down. |

Expected behavior:
- Cost-ledger header renders <300ms (SC1).
- Moments REST returns <2s for 50 rows.
- Live moments stream in via EventSource same-origin (cookie-authed); new
  rows prepend; hard cap 50 in DOM.
- Each moment row is an `<a>` — single click navigates to the transcript
  drill-down at `/portal/<slug>/transcript/<sid>?event_id=<id>`.
- Reasoning blocks are collapsed by default; click to expand.
- Secrets in transcripts and moment titles are redacted server-side; the
  redaction footer at the bottom of the transcript shows `N values
  redacted · portal-redactor v1` when N>0.

If the moments list stays empty despite events clearly landing in the
JSONL:

1. Browser devtools → Network → the `/stream` request should be
   `text/event-stream` with `Cache-Control: no-cache`. If it's
   `text/plain` or buffered, a proxy in front is breaking SSE — set
   `X-Accel-Buffering: no` upstream too.
2. The reviewer's cookie or JWT is for the right `email` linked to the
   right `users.id` linked to a membership for this slug. The
   `/moments` endpoint will 403 with `no_membership` before SSE even
   tries.
3. The events the reviewer's expecting may all be in the *timeline-
   ineligible* set (`tool_call`, `model_call`, `edit`, `cost`). The
   moments timeline filters server-side for `{moment, session_start,
   session_end, review_required, review_approve, review_reject,
   sla_breach, render, promotion}` only.

## 9. Decommission a reviewer

To revoke:

```sql
DELETE FROM user_client_memberships
 WHERE user_id = (SELECT id FROM users WHERE email = 'maria@klinikamelitus.pl')
   AND client_id = (SELECT id FROM clients WHERE slug = 'klinika-melitus');
```

The reviewer's existing JWT and `sb_session` cookie still validate until
exp, but every `/v1/portal/<slug>/*` call will now 403. To kill the
session immediately, the reviewer hits `/logout` (which calls
`DELETE /v1/auth/cookie` — revokes the JWT in addition to clearing the
cookie).

The events log on disk is untouched; historical state remains for the
audit trail.

## 10. Retention manual workaround (GDPR right-to-erasure)

There is no automated retention or right-to-erasure pipeline in v1.
When a deletion request lands:

1. Identify the slug and confirm the deletion request is in scope.
2. Remove all on-disk events:
   ```bash
   rm clients/<slug>/audit/events.jsonl*
   rm clients/<slug>/audit/sessions.jsonl
   rm -rf clients/<slug>/audit/<audit_id>/   # for each audit subdir
   ```
3. The cost-ledger header derives from `cost_actual.json` files under
   each `audit_id/`. Removing the directories above also removes
   cost data.
4. Revoke the reviewer's membership (Step 9) and force-logout (DELETE
   the cookie).
5. Backups (if any operator-side snapshots exist) are out of this
   runbook's scope; handle separately.

Document the request, the date, and the on-disk paths removed in the
operator's incident log. No automation; this is intentional in v1 to
keep the deletion surface small and auditable.

## What's NOT in this runbook

- **`clients/<slug>/client.yaml` schema** — content lanes, brand_tokens,
  content denylists, telemetry block. Owned by plan-002 U18 once it
  ships. The portal works off the database tables above; the YAML is
  only needed when the content engine reads per-client config at
  runtime.
- **Per-client cost-budget alerts** — out of v1 scope per the design
  doc. Captured-data only; no alerting.
- **Approval/reject UI for `review_required`** — plan-002 U7's
  responsibility. The portal deep-links from a `review_required` row to
  whatever URL plan-002 emits in the moment metadata.

## See also

- `docs/brainstorms/2026-05-13-client-portal-telemetry-design.md` — PR
  #61 substrate design.
- `docs/brainstorms/2026-05-15-portal-moments-redesign-requirements.md`
  — origin requirements for the redesigned portal.
- `docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md` — the
  9-unit plan this runbook operationalises.
- `scripts/claude-code-hooks/portal-telemetry.sh` — hook header
  documents one-time install + per-shell env-var requirements.
- `src/api/routers/portal.py` — `/portal/<slug>`, `/portal/<slug>/transcript/<sid>`,
  `/v1/portal/<slug>/summary`, `/v1/portal/<slug>/moments`,
  `/v1/portal/<slug>/stream`, `/v1/portal/_ingest`.
- `src/api/routers/auth.py` — `POST /v1/auth/cookie`, `DELETE /v1/auth/cookie`.
- `src/portal/transcript_tailer.py` — tailer + session registry.
- `src/portal/redaction.py` — server-side secret redaction.
