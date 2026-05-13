---
title: "Portal: onboard a new client + reviewer"
type: runbook
status: stable
date: 2026-05-13
owner: gofreddy
related:
  - docs/brainstorms/2026-05-13-client-portal-telemetry-design.md
  - src/api/routers/portal.py
  - supabase/migrations/20260417000001_init.sql
---

# Portal: onboard a new client + reviewer

Walks the operator through everything the portal itself needs to surface
events, costs, and reports for a new client. Scope is portal-only — the
broader `clients/<slug>/client.yaml` schema (content lanes, brand_tokens,
content denylists) is owned by plan-002 and lives in its own runbook
once that lands.

## Pre-flight

| Check | Command |
|---|---|
| Supabase is reachable | `curl -s http://127.0.0.1:54321/auth/v1/health` |
| App migrations applied | `psql $DATABASE_URL -c "\dt users clients user_client_memberships"` |
| Portal tests green | `pytest tests/test_api/test_portal.py tests/test_api/test_portal_phase2.py tests/test_api/test_portal_stream.py -q` |
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

The reviewer needs a Supabase user record so their JWT carries a `sub` claim
the portal can resolve. Two paths:

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

## 4. Confirm portal access

The reviewer hits `https://portal.gofreddy.ai/klinika-melitus` (or `localhost:8000`
locally). The page is unauthenticated HTML; the embedded JS reads the
Supabase session from localStorage and fetches the authed `/v1/portal/<slug>/summary`.

Expected outcomes:

| Reviewer state | Result |
|---|---|
| Not signed in | Redirected to `/login` |
| Signed in, no membership | Page loads, then renders `HTTP 403 — no_membership` |
| Signed in, member | Page renders with empty cost ledger + empty audit (until events land) |

The live transcript pane will say `connecting…` then `connected` once the
SSE handshake completes (under a second on localhost).

## 5. Emit the first events

A live portal needs events. Two practical paths:

**A. Autoresearch session** — start any lane run for the client. The
`cost_recorder` is already wired (P2 commit `b0b0c6b`) and emits a
`kind="cost"` event into `clients/<slug>/audit/events.jsonl` whenever it
records a provider charge. The `_ensure_render_score` hook emits a
`kind="render"` event after fixture rendering.

```bash
# Tail to confirm events are landing for the right client
tail -f clients/klinika-melitus/audit/events.jsonl
```

**B. Claude Code hook** — for interactive Claude Code work on the client's
worktree, install the PostToolUse hook (P3 commit `b21a23c`):

```bash
# One-time per operator machine
cp scripts/claude-code-hooks/portal-telemetry.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/portal-telemetry.sh

# Per-shell-session, for the client whose work you're about to do
export GOFREDDY_CLIENT_ID=klinika-melitus
export GOFREDDY_INGEST_TOKEN=<operator-secret>  # same secret the API expects
```

Each tool call now POSTs to `/v1/portal/_ingest` and lands as a
`kind="tool_call"` event under `clients/klinika-melitus/audit/events.jsonl`.

## 6. Watch the live view

The reviewer's portal page should now show, in near-real-time:

* **Cost ledger card** — today / week / month USD rollup
* **Recent reports** — any rendered `report.html` under
  `autoresearch/archive/<variant>/sessions/marketing_audit/klinika-melitus/`
* **Audit trail** — paginated list of every event, filterable by kind
  (chip row)
* **Live transcript (right column)** — each new event flows in within
  ~250ms of being appended to the JSONL log

If the transcript stays empty after events are clearly landing in the
JSONL, check:

1. Browser devtools → Network → the `/stream` request should be `text/event-stream`
   with `Cache-Control: no-cache`. If it's `text/plain` or buffered, a proxy
   in front is breaking SSE — set `X-Accel-Buffering: no` upstream too.
2. The reviewer's JWT is for the right `email` linked to the right
   `users.id` linked to a membership for this slug. The `/summary` endpoint
   will 403 with `code: "no_membership"` before the SSE even tries to open.

## 7. Decommission

To revoke a reviewer:

```sql
DELETE FROM user_client_memberships
 WHERE user_id = (SELECT id FROM users WHERE email = 'maria@klinikamelitus.pl')
   AND client_id = (SELECT id FROM clients WHERE slug = 'klinika-melitus');
```

The reviewer's existing JWT is still valid until expiry (~1h default) but
every authed `/v1/portal/<slug>/*` call will now 403. The events log on
disk is untouched — historical state remains for the audit trail; only
new access is denied.

## What's NOT in this runbook

* **`clients/<slug>/client.yaml` schema** — content lanes, brand_tokens,
  content denylists, telemetry block (cost budgets, alert recipients).
  That belongs to plan-002 U18 once it ships. The portal works off the
  database tables above; the YAML file is only needed when the content
  engine reads per-client config at runtime.
* **Per-client cost-budget alerts** — explicitly out of v1 scope per the
  design doc. Captured-data only; no alerting.
* **Codex session ingestion** — deferred to v1.5.

## See also

* `docs/brainstorms/2026-05-13-client-portal-telemetry-design.md` — the
  full design that this runbook operationalises.
* `scripts/claude-code-hooks/portal-telemetry.sh` — the hook header
  documents one-time install + per-shell env-var requirements.
* `src/api/routers/portal.py` — the routes this runbook references
  (`/portal/<slug>`, `/v1/portal/<slug>/summary`, `/v1/portal/<slug>/stream`,
  `/v1/portal/_ingest`).
