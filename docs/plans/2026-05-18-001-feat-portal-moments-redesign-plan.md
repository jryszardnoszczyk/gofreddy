---
title: "feat: Portal-moments redesign (timeline + tailer + transcript drill-down + cookie auth)"
type: feat
status: active
date: 2026-05-18
origin: docs/brainstorms/2026-05-15-portal-moments-redesign-requirements.md
---

# Portal-Moments Redesign — Implementation Plan

## Reconciliation Note (2026-05-18, post-TD-56)

This plan was committed at `b6c2be3` (20:11) assuming `emit_moment(...)` would
ship as a thin wrapper in `autoresearch/events.py`. Six minutes later, plan-002
TD-56 binary-cuts pass (`9ef667f`, 20:17) REJECTED the wrapper across the
codebase:

> "REJECTED: ... emit_moment wrapper, rubric_resolver module, ... mandate stays,
>  wrapper goes." — plan-002 §triage 2026-05-18 TD-56

JR reconciled in favor of TD-56: **no wrapper. Lanes (and all callers, including
`cost_observability.py`) emit moments via direct `events.log_event(kind="moment",
client_id=<slug>, metadata={"moment_kind": ..., "title": ..., ...})` calls.**

What this changes in the plan below:

- **Unit 0**: still ships a plan-002 coordination edit, but rewrites U6b's
  "Files" section instead of just adding a pointer line. plan-002 U6b becomes
  contract-only (defines emission mandates); schema extensions move to this
  plan's Unit 1.
- **Unit 1**: drops the `emit_moment` helper + its dedicated test file. Keeps
  the `KNOWN_KINDS` + `CANONICAL_FIELDS` extensions, drift-test updates, and
  the `cost_observability._check_thresholds` rewrite — the rewrite now calls
  `log_event(kind="moment", ...)` directly instead of `emit_moment(...)`.
- **Units 2, 3, 5, 6, 7**: any mention of `emit_moment(...)` should be read as
  `log_event(kind="moment", client_id=..., metadata={moment_kind=..., title=...,
  ...})`. No semantic change beyond the missing wrapper.
- **R-Lane-1** requirement (the `emit_moment` helper itself) is dropped from
  this plan's scope; R-Lane-2 (lane emission checkpoints) and R-Lane-3 (lane
  emission table) remain in force via direct `log_event` calls.

The High-Level Technical Design diagram below still labels the schema layer
`log_event + emit_moment` — read it as `log_event` only.

## Overview

The PR #61 P5 frontend at `portal/templates/portal_phase2.html` renders the
per-client event log as a flat list of `tool_call · Bash` rows — technically
correct, useless to a non-engineer client. This plan replaces it with a
**moments timeline** (one-line client-visible work units) plus a
**transcript drill-down** that shows the underlying CC + Codex JSONL evidence
for any moment. Along the way it ships the substrate pieces a redesigned
page needs: an `emit_moment` helper + schema extensions, an in-process
asyncio transcript-tailer, a moments REST endpoint, server-side redaction
on agent-produced content, and a cookie-auth migration that removes the
`?token=<jwt>` URL fallback.

The PR #61 P5 page stays in place on `main` while this work happens on the
existing `design/client-portal-telemetry` branch; the redesign ships as a
**separate follow-up PR** that flips `portal_shell` to the new template.

## Problem Frame

gofreddy is a generic AI-native marketing agency for tech-savvy founders.
Clients oversee work done by AI agents (autoresearch lanes, interactive
Claude Code sessions, Codex CLI sessions). The portal must let a client
answer "what did the agency do this week?" in under 30 seconds. The
current Phase 2 page can't — it surfaces raw tool calls without context.
See origin doc §"Problem Frame" for the operator-observed evidence basis
and SC4 (one real client comprehension test) as the actual exit gate.

## Requirements Trace

Every requirement IDs forward from `docs/brainstorms/2026-05-15-portal-moments-redesign-requirements.md`:

- **R1, R1.1, R1.2** — Single-page layout: cost-ledger header + moments
  timeline; no narrative intro / active-sessions card / awaiting-input
  pane / filter chips / load-more.
- **R2, R3, R3.1, R4** — 50 newest moments, one-line rows, click →
  drill-down route (no inline expand).
- **R5–R5.5, R6, R7** — Attribution: CC hook env-first/cwd-fallback;
  tailer cwd-only; conflict → operator-internal; slug validated against
  `clients` table; 6+3+1 testable invariants.
- **R8, R8.1, R8.2, R8.3, R8.4** — Unified transcript tailer (in-process
  asyncio, polling, session boundaries, dedup against CC hook, session
  registry).
- **R9, R9.1, R9.2, R9.3, R9.4** — Transcript drill-down with IDOR guard
  via session registry, CC + Codex JSONL parsing, reasoning collapsed by
  default, `?event_id` anchor.
- **R-Sec-1..R-Sec-5** — Server-side redaction on transcripts + moment
  titles/bodies/metadata; Bash/Read of secret-file patterns
  default-deny; redactions logged; versioned; HTML-escape after
  redaction.
- **R-Cost-1, R-Cost-2** — Cost-ledger rollups; `cost_threshold_crossed`
  reclassified to `kind="moment"` / `moment_kind="cost_milestone"`.
- **R-Live-1, R-Live-2, R-Live-3** — Moments REST endpoint; SSE filters
  client-side; reconnect backfills via `?since=<event_id>`.
- **R-Schema-1..R-Schema-4** — `moment` + `review_required` added to
  KNOWN_KINDS; CANONICAL_FIELDS extended with `moment_kind` /
  `source_event_ids` / `title` / `body`; `cost_threshold_crossed`
  retires.
- **R-Lane-1, R-Lane-2, R-Lane-3** — `emit_moment(...)` helper; lane
  emission checkpoint table; plan-002 will consume from this plan's
  Unit 1.
- **R-Auth-1..R-Auth-4** — Membership check on all routes; new
  `POST /v1/auth/cookie` + `DELETE /v1/auth/cookie`; remove `?token=`
  URL fallback; 401 → /login redirect.
- **R-Runbook-1** — Update `docs/runbooks/portal-client-onboarding.md`
  to reflect the redesigned portal.
- **SC1–SC5** — Latency, signal density, cross-tenant isolation,
  one-real-client comprehension test, Codex parity.
- **T1–T4 (carried from origin)** — `.env`/Read denylist + secret regex
  layered defense; env-vs-cwd conflict fail-closed; session-registry
  IDOR guard with 404-on-registry-miss; HTML-escape after redaction +
  CSP forbidding inline scripts.
- **T6–T8 (NEW, introduced by this plan's design)** — JWT replay
  after cookie delete (blocklist via existing `is_token_revoked`
  hook); sessions.jsonl registry write-trust (tailer canonicalizes
  file_path before persistence); path traversal via registry
  file_path (Unit 6 `_safe_transcript_path` symlink-rejecting helper
  + explicit test scenarios). (T5/CSRF deferred to plan-002, which
  ships the first state-changing cookie-authed endpoints.)

## Scope Boundaries

Carried verbatim from origin doc §"Scope Boundaries" — no scope creep
introduced in this plan:

- LLM moment-derivation: REJECTED. Determinism/citation/precedence
  unresolved.
- LLM narrative intro: REJECTED. Moment titles cover the 30s test.
- Dedicated active-sessions card, awaiting-input pane, filter chip UI,
  inline accordion expand, load-more / archive UI, cross-client
  warning: REJECTED.
- Mobile/responsive: out (desktop-only).
- Multi-client operator dashboard: out (per-client URLs only).
- Approval/reject UI for `review_required`: owned by plan-002 U7, this
  plan deep-links to it.
- Single-host operator deployment: architecture, not limitation.
- No automated retention / right-to-erasure: accepted limitation;
  runbook documents the manual workaround.

## Context & Research

### Relevant Code and Patterns (verified by Phase 1 repo scan)

**Schema substrate** (`autoresearch/events.py`):
- `KNOWN_KINDS` (line ~102) — 12 kinds; `moment` + `review_required` are NOT present today.
- `CANONICAL_FIELDS` (line ~123) — 19 fields today; `moment_kind`, `source_event_ids`, `title`, `body` are NOT present.
- `client_events_path(client_id, run_id=None)` returns `clients/<slug>/audit/events.jsonl` (the per-client wide log this plan tails).
- `log_event(kind, *, path=None, **data)` — POSIX flock + 100MB rotation.
- `tail_events_sse(path, ...)` — existing SSE async generator with inode-rotation detection. **Pattern to mirror for the multi-directory tailer.**
- Drift tests at `tests/autoresearch/test_events.py:83-116` — adding kinds requires updating the asserted sets.

**Routing** (`src/api/routers/portal.py`, 897 lines):
- `router = APIRouter()` (no prefix); mounted in `src/api/main.py`.
- Existing route pattern: `@router.get(...)` + `@limiter.limit("60/minute")` + `Annotated[AuthPrincipal, Depends(get_auth_principal)]` + `resolve_client_access(...)`.
- **`?token=` URL fallback site** for SSE auth: `_resolve_principal_for_sse` at `src/api/routers/portal.py:816-847` + `portal_stream` route at 850-897. Removed by Unit 4.
- `portal_shell` at lines 43-55 — unauthenticated HTML shell. Flipped to new template in Unit 7.

**Auth** (`src/api/dependencies.py:125-233`):
- `verify_supabase_token(token)` — JWKS first, HS256 fallback; aud=`authenticated`; iss=`{supabase_url}/auth/v1`; expired → HTTP 401 code=`token_expired`.
- `get_auth_principal` — currently reads `Authorization` header OR `X-API-Key` header. No cookie path. Cookie support added in Unit 4.
- `src/api/membership.py:21-49 resolve_client_access(pool, user_id, slug)` — single chokepoint, admin-on-any == admin-on-every.

**Lifespan** (`src/api/main.py:59-642`):
- Single `@asynccontextmanager async def lifespan(app)` registered at line 642. Pattern: load configs → init pools → instantiate services → `app.state.<name>` → yield → cleanup in finally. **Tailer attaches here in Unit 2.**

**Redaction** (`src/shared/reporting/scrub.py`):
- ~17 regex patterns: JWT, GitHub, AWS, Stripe, Anthropic `sk-ant-`, OpenAI `sk-proj-`/`sk-`, Slack, Google, PEM, GCP service-account JSON, DB URLs with creds, Authorization/Cookie/X-Api-Key headers, coarse base64-40+, `api_key=`. **Reused and extended in Unit 5; do not duplicate.**

**Cost observability reclassification target**:
- `src/audit/cost_observability.py:60-66 _check_thresholds` emits `kind="cost_threshold_crossed"` via `log_to_audit`. Note: `cost_threshold_crossed` is NOT in KNOWN_KINDS today — silent unknown-kind write. Unit 1 closes this drift by reclassifying to `emit_moment(moment_kind="cost_milestone", ...)`.

**Cost ledger mirror** (`src/audit/cost_ledger.py:117-167`):
- `_mirror_to_canonical_events` already mirrors `kind="cost"` to per-client wide log when `audit_dir` matches `clients/<slug>/audit/<audit_id>/`. Used by R-Cost-1 rollups; unchanged by this plan.

**Transcript path resolution** (`autoresearch/sessions.py:169-194 viable_resume_id`):
- CC: `~/.claude/projects/<cwd-with-slashes-as-dashes>/<sid>.jsonl`.
- Codex: `~/.codex/sessions/**/rollout-*-<sid>.jsonl` (recursive glob).
- Same encoding logic reused by the tailer (Unit 2) and the drill-down route (Unit 6).

**CC hook script** (`scripts/claude-code-hooks/portal-telemetry.sh`):
- Currently emits `kind="tool_call"` only — does NOT emit `session_start`/`session_end`. R8.3 dedup is forward-looking; for v1 the tailer is the sole emitter for those kinds, so no dedup needed yet — but the dedup check is implemented anyway for forward compatibility with a later hook extension.

**Test patterns**:
- `tests/test_api/conftest.py:69-72` — `api_client` fixture uses `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))`.
- `tests/test_api/test_portal_stream.py:9-20` — documented constraint: `httpx.ASGITransport` buffers infinite generators forever. SSE route tests **monkeypatch** `tail_events_sse` to a finite generator; tailer logic is unit-tested directly with a tmp_path.

### Institutional Learnings

`docs/solutions/` does not exist in this repo. Institutional knowledge
lives in:

- The origin requirements doc (referenced throughout).
- PR #61 commits on this branch: `30b2e0c` (P1 schema lock), `b0b0c6b`
  (P2 autoresearch mirror), `b21a23c` (P3 ingest endpoint), `29a947f`
  (P4 SSE — implied by lineage), `f602092` (P5 frontend being
  replaced).
- The `httpx.ASGITransport`-infinite-generator gotcha documented in
  `tests/test_api/test_portal_stream.py:9-20` — must monkeypatch for
  SSE route tests.

### External References

Skipped. Local patterns are strong (existing `tail_events_sse`,
`scrub.py`, route + auth conventions, test scaffolding). Planning-deferred
Qs (watchdog vs inotify, secret-regex source, reasoning rendering) all
resolvable from local research.

## Key Technical Decisions

- **Unit 1 of this plan ships the `emit_moment` helper and schema
  extensions**, because plan-002 U6b is doc-only (`git log -S
  "emit_moment" --all` returns zero commits as of `9876fec`). Plan-002
  will CONSUME from this plan's commit once plan-002 begins
  implementation. Origin doc's "plan-002 already adopted the contract"
  framing refers to the plan, not the code. **Follow-up:** plan-002 doc
  needs a one-line note pointing to this plan's commit; tracked in
  Documentation Plan below.
- **Tailer = polling-glob asyncio task** (NOT `watchdog` / `inotify`).
  Mirrors the existing `tail_events_sse` polling pattern, adds no
  dependency, cross-platform without conditionals. Polling cadence:
  ~1.5s default, env-tunable via `GOFREDDY_TAILER_INTERVAL_S`.
  Sub-second session-start latency is not a stated SC; SC1 only
  bounds page-load. **Watchdog/inotify rejected** (see Alternatives).
- **Tailer lifecycle = FastAPI lifespan asyncio task.** Same uvicorn
  worker, same event loop, no IPC. On startup: reconcile registry
  against watched roots, resume from last-known position. On shutdown:
  cancel the task + flush in-flight writes. Crash-recovery via session
  registry, not external state store.
- **Secret-regex = extend `src/shared/reporting/scrub.py`.** Reuse 17
  existing patterns; add Supabase service_role (`eyJ` JWT pattern
  likely caught already — verify by test); env-var `[A-Z][A-Z0-9_]*_(API_)?KEY=`;
  `password=` literal; ensure `DATABASE_URL=` and similar
  scheme-with-creds patterns covered. **trufflehog / detect-secrets /
  gitleaks rejected** (see Alternatives).
- **`.env`/`*.pem`/`id_rsa*` file-pattern denylist (R-Sec-2)** is
  separate from scrub.py — it intercepts Bash and Read tool args and
  outputs BEFORE scrub.py runs in the transcript renderer. Net-new
  logic in Unit 5.
- **Redaction is versioned (R-Sec-4).** Module exports
  `REDACTOR_VERSION = "v1"`. Stamped on every rendered output via an
  HTML comment `<!-- redacted-by:portal-redactor v1 -->` so future
  improvements can re-scan already-served content (manual reprocessing
  outside the scope of this plan).
- **Cookie auth = extend `get_auth_principal`** in
  `src/api/dependencies.py` with a cookie-reading branch BEFORE the
  Authorization-header branch. Same `verify_supabase_token` machinery;
  no auth duplication. Cookie name `sb_session`; httpOnly,
  SameSite=Strict, Secure; Max-Age mirrors JWT `exp` claim.
- **`?token=` URL fallback removed entirely** (R-Auth-3) at
  `src/api/routers/portal.py:816-847` (backend) and
  `portal/templates/portal_phase2.html:557-558` (frontend, replaced
  when the template is retired in Unit 7).
- **CSRF posture (T5).** SameSite=Strict on the cookie blocks
  cross-site CSRF, which is sufficient for v1 single-host
  deployment with no subdomains. Same-site CSRF (subdomain-XSS,
  open-redirect chains) is not in v1's threat model because v1 has
  no subdomain surface. **When plan-002 ships state-changing
  cookie-authed endpoints (review_approve/reject)**, that plan adds
  an `Origin`/`Referer` check at a shared dependency. Out of scope
  for this plan.
- **EventSource same-origin assumption.** v1 deployment is
  single-host, so EventSource SSE inherits the `sb_session` cookie
  automatically without `withCredentials`. If the SPA + API ever
  diverge to different origins, `EventSource(url, {withCredentials:
  true})` + `Access-Control-Allow-Credentials: true` is required —
  flagged in runbook (R-Runbook-1).
- **Moments REST = derived-on-read** (origin Key Decision). The
  `GET /v1/portal/<slug>/moments` endpoint scans the per-client
  `events.jsonl` and rotated segments, filters on timeline-eligible
  kinds server-side. No materialized `moments.jsonl` view in v1; v1
  expects <100K events per client, scan completes in <100ms.
- **Error-status convention (T3 mitigation + existing-route
  consistency):** the new routes follow the existing portal-router
  convention of **403 `no_membership`** when `resolve_client_access`
  returns `None` (matches `portal_summary`, `portal_report_view`,
  `portal_stream`, etc. at `src/api/routers/portal.py:284, 401, 464,
  573, 878`). This is NOT cross-tenant existence disclosure because
  the slug is in the URL path — the user already knows which client
  they tried to access. **404 is reserved specifically for the IDOR
  session-registry case:** `<session_id>` is well-formed but not in
  `clients/<slug>/audit/sessions.jsonl`. That's the only path where
  the response would otherwise leak that the session exists in
  another client's registry. Existing routes' 403 stays as-is; no
  flip required.
- **`portal_phase2.html` is retired** (template removed in Unit 7);
  two new templates `portal/templates/portal_moments.html` +
  `portal_transcript.html` extend `base.html`. CSS classes
  (`.log-stream`, `.log-line` per-kind colours, `.caret-blink`,
  `log-line-reveal` keyframes) currently inlined in
  `portal_phase2.html` lines 260-308 are extracted to
  `portal/templates/portal_moments.html` (re-inlined) or to a shared
  partial — pick during implementation.

## Open Questions

### Resolved During Planning

- **R8 tailer library** — polling-glob asyncio task in the spirit of
  `tail_events_sse`. No `watchdog` / `inotify` / `pyinotify` dependency.
  Rationale above + Alternatives below.
- **R-Sec-1 secret-regex source** — reuse + extend
  `src/shared/reporting/scrub.py`. Three new patterns added with unit
  tests (Supabase service_role, env-var assignment, password=
  literal); existing 17 patterns retained.
- **Plan-002 U6b ownership** — portal redesign ships it (Unit 1).
  Plan-002 consumes from this plan's commit when plan-002 begins
  implementation. Plan-002 doc to be updated as a separate one-line
  follow-up (out of this plan's scope to edit a sibling plan's doc).
- **Reasoning-block render shape (R9.3)** — collapsed-by-default with
  markdown body parsed (linkify + code blocks). Specific click-to-expand
  trigger UX (inline accordion vs side panel vs modal) prototyped during
  implementation against real CC transcripts; lightweight decision, no
  rework risk regardless of trigger choice.

### Deferred to Implementation

- **Markdown parser for reasoning rendering** — REMOVED from v1. Plain
  text + escape + auto-linkify. See Unit 6 Approach for rationale and
  future-plan trigger.
- **Specific reasoning-block trigger UX** — inline accordion vs side
  panel vs modal. Implementer prototypes 2–3 against real transcripts
  and picks. Either way the data shape is the same (markdown body,
  redaction-then-escape).
- **Exact polling interval for the tailer** — 1.5s default, tunable
  via `GOFREDDY_TAILER_INTERVAL_S`. Implementer may adjust based on
  observed CPU cost during smoke; not blocking.
- **CSS extraction strategy** — inline in `portal_moments.html` /
  `portal_transcript.html` vs extract to shared partial vs extract to
  static CSS file. Picked at impl time based on what reads cleanest;
  not architectural.
- **Whether to extend the CC hook to emit `session_start` /
  `session_end`** — out of this plan's scope. R8.3 dedup is
  implemented as a forward-compatible no-op for v1 (tailer is sole
  emitter); a later plan can extend the hook and the dedup will
  activate without change.

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

### Moment flow (end-to-end)

```mermaid
flowchart TB
    subgraph Producers
        A[Autoresearch + plan-002 lanes]
        B[Audit cost_observability]
        C[Unified transcript tailer<br/>polling 1.5s]
    end
    subgraph Schema layer (Unit 1)
        H[autoresearch/events.py<br/>log_event + emit_moment<br/>KNOWN_KINDS + CANONICAL_FIELDS]
    end
    subgraph Persistence
        W[clients/&lt;slug&gt;/audit/events.jsonl<br/>+ rotated segments]
        R[clients/&lt;slug&gt;/audit/sessions.jsonl<br/>tailer session registry]
        O[~/.local/share/gofreddy/events.jsonl<br/>operator-internal]
    end
    subgraph Serving
        M[GET /v1/portal/&lt;slug&gt;/moments<br/>derived-on-read]
        S[GET /v1/portal/&lt;slug&gt;/stream<br/>existing SSE]
        T[GET /portal/&lt;slug&gt;/transcript/&lt;sid&gt;<br/>IDOR via registry + redaction]
        L[POST /v1/auth/cookie<br/>+ DELETE /v1/auth/cookie]
    end
    subgraph Frontend
        P[portal_moments.html<br/>filterless timeline + click-to-drill]
        D[portal_transcript.html<br/>collapsed-reasoning + redaction marker]
    end

    A -->|log_event / emit_moment| H
    B -->|emit_moment cost_milestone| H
    C -->|log_event session_start/end<br/>cwd attribution| H
    H --> W
    H -->|attribution conflict / unattributed| O
    C -->|writes/reads| R
    W --> M
    W --> S
    R -->|IDOR guard lookup| T
    M --> P
    S --> P
    P -->|click row| T
    T --> D
    L -->|sets sb_session cookie| P
    L -->|sets sb_session cookie| D
```

### Tailer sketch (polling-glob asyncio task)

```pseudo
async def transcript_tailer_task(app):
    registry = SessionRegistry()
    await registry.reconcile_on_startup(watched_roots=[CC_ROOT, CODEX_ROOT])
    interval = float(os.environ.get("GOFREDDY_TAILER_INTERVAL_S", "1.5"))
    while not app.state.shutting_down:
        try:
            for path in glob_session_files(CC_ROOT, CODEX_ROOT):
                if path not in registry:
                    handle_new_session(path, registry)   # R8.2 + R8.3 dedup
                else:
                    handle_existing_session(path, registry)  # mtime + size + Codex end events
            for sid in registry.idle_threshold_breached(now()):
                emit_session_end(sid, registry, reason="idle_timeout")
        except Exception as exc:
            log_global(kind="alert", action="tailer_tick_failed", error=repr(exc))
        await asyncio.sleep(interval)
```

> *Polling cadence and registry shape are illustrative; the implementing agent picks data structure (dict vs in-memory + persisted JSONL append) based on the registry size — likely small dict, JSONL append for persistence.*

## Implementation Units

Sequencing summary: **Unit 0 doc-only ships first** (plan-002 coordination); **Unit 1 blocks everything else.** Units 2/3/4/5 are
independent and can land in any order after Unit 1. Units 6/7 depend on
2+5 (drill-down) and 1+3+4 (frontend). Unit 8 (runbook) lands last.

```
                    ┌─────────────────┐
                    │ Unit 1: schema  │
                    └────────┬────────┘
        ┌─────────────┬──────┴──────┬─────────────┐
        ▼             ▼             ▼             ▼
   ┌────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐
   │ U2 tail│   │ U3 REST  │   │ U4 cook│   │ U5 redact│
   └───┬────┘   └────┬─────┘   └───┬────┘   └────┬─────┘
       │             │             │             │
       └──────┬──────┘             └──────┬──────┘
              ▼                           ▼
        ┌──────────┐                ┌──────────────┐
        │ U6 drill │                │ U7 frontend  │
        └─────┬────┘                └──────┬───────┘
              └──────────┬─────────────────┘
                         ▼
                    ┌──────────┐
                    │ U8 runbook│
                    └──────────┘
```

- [ ] **Unit 0: Plan-002 coordination doc edit (revised post-TD-56)**

**Goal:** Reconcile plan-002 U6b with the post-TD-56 reality + this plan's
Unit 1 scope. plan-002 U6b on `main` currently lists `KNOWN_KINDS` +
`CANONICAL_FIELDS` modifications in its "Files" section — those modifications
are now owned by this plan's Unit 1. The edit turns plan-002 U6b into a
**contract-only** section: defines the moment-emission mandate
(`session_start` / `deliverable_ready` / `session_completed`) but does NOT
ship the schema edits.

**Requirements:** Coordination — not from origin doc. Eliminates the race
where a plan-002 implementer reads U6b's "Modify `autoresearch/events.py`"
lines and double-implements the schema extensions.

**Dependencies:** None.

**Files:**
- Modify: `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md`
  — under the `U6b: Canonical event-schema extension for portal moments
  (no helper wrapper)` heading:
  1. In the "Files:" subsection, replace the two `Modify: autoresearch/events.py:KNOWN_KINDS` / `:CANONICAL_FIELDS` lines with a single line:
     `Schema extensions (KNOWN_KINDS + CANONICAL_FIELDS) ship via the portal-moments redesign at docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md (Unit 1). plan-002 U6b is contract-only: it defines the moment-emission mandate that lanes must follow.`
  2. Leave the "Modify: `tests/autoresearch/test_events.py`" drift-test line in place; the drift test for KNOWN_KINDS/CANONICAL_FIELDS naturally lives in the test file regardless of which plan ships the schema.
  3. Leave the rest of U6b (mandate, kinds list, title convention, integration test) untouched.

**Approach:**
- Doc-only edit. One commit, one file changed.
- Commit message: `plan(content-engine-v1): U6b schema work delegated to portal-moments redesign`.
- No push needed mid-Unit; ships with the rest of U0+U1 commit train.

**Execution note:** First unit to land. Trivial work; tripwire for the
schema-overlap conflict.

**Patterns to follow:** None — single doc edit.

**Test scenarios:**
- Test expectation: none — doc-only unit. Verification: `git diff` of
  plan-002 doc shows the U6b "Files:" section trimmed, no other changes.

**Verification:**
- `grep "docs/plans/2026-05-18-001" docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` finds the cross-reference inside U6b.
- `grep "Modify.*KNOWN_KINDS" docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` returns zero hits (the schema-edit lines are gone).

---

- [ ] **Unit 1: Schema extensions + cost_milestone reclassification (no wrapper, per TD-56)**

**Goal:** Land the substrate primitives every downstream unit (and
plan-002) depends on: extended kinds + fields, plus the
`cost_threshold_crossed` → `cost_milestone` reclassification.
**No `emit_moment` wrapper** — callers use `log_event(kind="moment", ...)`
directly per TD-56 reconciliation.

**Requirements:** R-Schema-1, R-Schema-2 (frontend mapping consumed by
Unit 7), R-Schema-3, R-Schema-4, R-Cost-2. (R-Lane-1 — the wrapper helper —
is dropped; R-Lane-2 / R-Lane-3 remain via direct `log_event` calls.)

**Dependencies:** None.

**Files:**
- Modify: `autoresearch/events.py` — extend `KNOWN_KINDS` with
  `moment` + `review_required`; extend `CANONICAL_FIELDS` with
  `moment_kind` + `source_event_ids` + `title` + `body`. **No helper
  function added.**
- Modify: `src/audit/cost_observability.py` — `_check_thresholds`
  switches from `log_to_audit(kind="cost_threshold_crossed", ...)` to
  `log_event(kind="moment", client_id=<slug>, metadata={"moment_kind": "cost_milestone", "title": ..., ...})`.
- Modify: `tests/autoresearch/test_events.py` — update drift-test
  assertions at lines 83-116 to match new sets.
- Modify or create: `tests/test_audit/test_cost_observability.py` — verify
  the new `kind="moment" / moment_kind="cost_milestone"` emission shape
  and idempotency. Verify via repo scan during impl whether the file
  exists.

**Approach:**
- Schema extensions in `events.py` are purely additive — `KNOWN_KINDS`
  set gains 2 members, `CANONICAL_FIELDS` set gains 4.
- The `cost_milestone` rewrite removes the previous unknown-kind drift
  (the literal string `cost_threshold_crossed` is not in `KNOWN_KINDS`
  today — silent unknown-kind write).
- Direct `log_event` call shape at the rewrite site:
  `log_event(kind="moment", client_id=<slug>, action="cost_threshold_crossed", metadata={"moment_kind": "cost_milestone", "title": f"Cost threshold crossed: ${threshold:.2f}", "threshold_usd": threshold, "cumulative_usd": cumulative, ...})`.
  Exact title text and metadata keys are operator-readable English per
  plan-002 U6b ≤120-char convention.
- Title HTML-escape is a render-time concern (R-Sec-5); not done by
  callers. Untrusted metadata values follow the same render-time
  redaction + escape contract that Unit 5 + Unit 7 own.
- No backward-compat shim for the old `cost_threshold_crossed` kind —
  it was never in `KNOWN_KINDS`, never consumed.

**Execution note:** Test-first for the cost_observability rewrite —
update or write the cost_observability test BEFORE flipping the call
site, so the new emission shape is asserted before the implementation
changes. Schema extensions are tested via the existing drift test;
update the asserted sets in the same commit as the `events.py` edit.

**Patterns to follow:**
- `autoresearch/events.py log_event` signature + flock pattern (the
  call site, not a wrapper).
- `tests/autoresearch/test_events.py` drift-test structure for the
  KNOWN_KINDS + CANONICAL_FIELDS sets.
- `src/audit/cost_ledger.py:_mirror_to_canonical_events` for the
  pattern of calling `autoresearch.events.log_event` directly from
  audit code.

**Test scenarios:**
- **Drift test (R-Schema-1)** — `KNOWN_KINDS` assertion at `tests/autoresearch/test_events.py:83-116` exactly matches the extended set (existing kinds + `moment` + `review_required`); same for `CANONICAL_FIELDS` (existing fields + `moment_kind` + `source_event_ids` + `title` + `body`).
- **Drift test (negative)** — removing `moment` or `review_required` from `KNOWN_KINDS` makes the drift test fail loudly.
- **Integration (cost_milestone happy path)** — calling `_check_thresholds` from `src/audit/cost_observability.py` when cumulative crosses a threshold writes `kind="moment"` with `metadata.moment_kind="cost_milestone"`, `metadata.title="Cost threshold crossed: $<threshold>"`, and the relevant cumulative + threshold numbers, to the per-client wide log (NOT `kind="cost_threshold_crossed"` any longer).
- **Integration (cost_milestone idempotency)** — calling `_check_thresholds` repeatedly for the same crossed threshold emits only one `cost_milestone` (existing idempotency preserved through the rewrite).
- **Integration (cost_milestone routing)** — the emission lands at `client_events_path(<slug>)` (per-client wide log), matching the existing `cost_recorder` mirror pattern.

**Verification:**
- `pytest tests/autoresearch/test_events.py tests/test_audit/test_cost_observability.py` green (or equivalent paths if cost_observability test file lives elsewhere — verify via grep before running).
- `grep -r "cost_threshold_crossed" src/ autoresearch/` returns zero hits in source code (tests + docs may still mention it as historical reference, that's fine).
- `grep -r "def emit_moment\|emit_moment(" src/ autoresearch/ tests/` returns zero hits — confirming no wrapper landed.

---

- [ ] **Unit 2: Unified transcript tailer (polling asyncio task + session registry)**

**Goal:** A background asyncio task watches both
`~/.claude/projects/<*>/*.jsonl` and
`~/.codex/sessions/<*>/<*>/<*>/rollout-*.jsonl`, emits
`session_start`/`session_end` to the per-client wide log via cwd-only
attribution, and maintains the session registry that the drill-down
route (Unit 6) reads for the IDOR guard.

**Requirements:** R8, R8.1, R8.2, R8.3, R8.4, R5.4, R5.5, R6, R7
(tailer + integration sub-cases g/h/i/j).

**Dependencies:** Unit 1 (uses `emit_moment` for `attribution_conflict`
operator-internal log; uses extended fields for session_start metadata).

**Files:**
- Create: `src/portal/__init__.py` — **new namespace introduced by this plan** (verified absent at planning time). Houses `transcript_tailer.py`, `redaction.py`, `transcript_parser.py` across Units 2/5/6.
- Create: `src/portal/transcript_tailer.py` — the asyncio task,
  `SessionRegistry` class, attribution helper, glob helpers, session
  boundary detection.
- Modify: `src/api/main.py` — extend the existing `lifespan(app)`
  context manager (registered at line 642). **Strict startup
  ordering:** `create_task(...)` the tailer ONLY after
  `app.state.db_pool` is set (line ~82); cancel + await it BEFORE
  pool close in the `finally` block. The tailer also checks
  `app.state.db_pool` presence at top of every tick and silently
  skips if pool isn't ready yet (defensive; should never fire given
  the startup ordering above).
- Create: `tests/portal/__init__.py`.
- Create: `tests/portal/test_transcript_tailer.py` — unit tests run
  the tailer's internal helpers (glob, attribution, dedup, boundary
  detection) directly against tmp_path JSONLs; lifespan-attach is
  smoke-tested via a separate route test.

**Approach:**
- Polling-glob async task. Default interval 1.5s, env-tunable via
  `GOFREDDY_TAILER_INTERVAL_S` (cast `float`, default 1.5, min 0.25,
  max 60.0). **Note on scale and pattern divergence from
  `tail_events_sse`:** the existing tailer tails ONE file with
  inode tracking; this tailer scans directory trees. On a
  long-running operator host the watched trees can hold thousands
  of historical JSONLs (verified 308 CC project dirs + 2045 Codex
  rollouts on the current host). Mitigations:
  1. **Bounded session-of-interest set.** Only sessions whose JSONL
     mtime is within the last 24h are eligible for active tail; older
     files are registered once (so the IDOR guard can resolve them)
     and skipped on subsequent ticks. Cuts the per-tick work from
     "thousands of files" to "active sessions" (typically <20).
  2. **No held file descriptors.** Each tick opens, reads the
     tail, closes. fd exhaustion impossible.
  3. **Registry size:** v1 appends without bound. If a real client's
     registry crosses ~10K rows and load impact appears, archival
     becomes operational tuning, not a v1 build.
- CC path encoding logic mirrored from
  `autoresearch/sessions.py:viable_resume_id` (slashes-as-dashes with
  leading marker `-`). **The decoder (dirname→cwd) is net-new** —
  `viable_resume_id` only goes one direction. Decode inverts
  `replace("/", "-")` with edge cases: paths that legitimately
  contain `-` (no perfect inverse — accept ambiguity by anchoring on
  existence of the resulting path on disk), leading-slash handling
  (strip the leading `-` marker), and normalization (resolve symlinks
  + assert resulting path exists). Add direct encode/decode tests on
  `viable_resume_id` before copying.
- Codex sessions: parse first ~10 lines of each new JSONL for
  `session_meta` event; cwd field present at the top of every Codex
  rollout.
- CC sessions: encoded-cwd in the parent directory name; first ~10
  lines parsed only for sanity (any `{"type":...}` line confirms it's
  a CC session JSONL).
- Attribution: cwd contains `clients/<slug>/` segment → attribute to
  slug (after R5.5 slug validation against the `clients` table via
  the dependencies pool); else operator-internal
  (`~/.local/share/gofreddy/events.jsonl`).
- Dedup (R8.3): before emitting `session_start`, scan the per-client
  log (or operator-internal) for an existing `kind="session_start"`
  with `metadata.session_id == <sid>`. If found, skip emission and
  mark `hook_emitted=True` in the registry row.
- Session boundary detection (R8.2):
  - `session_start` on first-time-seen file (after sanity-parse).
  - `session_end` whichever fires first: idle timeout (10 min stale
    mtime AND no size growth across 3 ticks) OR Codex
    `task_completed`/`task_aborted` event in the JSONL.
- Session registry (R8.4) format (JSONL, append-only):
  ```jsonl
  {"session_id": "...", "client_id": "...", "source": "cc"|"codex", "file_path": "/abs/.../*.jsonl", "started_at": "...", "hook_emitted": false}
  {"session_id": "...", "ended_at": "...", "reason": "idle_timeout"|"task_completed"|"task_aborted"}
  ```
  Two row shapes — start (write-once) + end (write-once). Registry
  rebuild from disk on startup uses the latest-row-per-session-id
  rule.
- Operator-internal log path: `~/.local/share/gofreddy/events.jsonl`
  via `os.path.expanduser`. Create parent dir on first write.
- **Defense in depth: canonicalize `file_path` before registry write.**
  Tailer's glob output is `Path.resolve(strict=True)`-ed AND
  asserted under `CC_ROOT` or `CODEX_ROOT` before being appended to
  the registry row. Any symlink-leaving-roots is dropped at the
  source (no registry row written; emit `kind="alert"`
  operator-internal with `metadata.reason="path_outside_roots"`).
  This shrinks the trust surface even if a malicious or buggy writer
  to the registry slips through later.

**Execution note:** Add characterization coverage on
`autoresearch/sessions.py:viable_resume_id` BEFORE copying its
encoding/decoding logic — the existing function has no direct tests
of the encode/decode contract by itself, only behavioral tests of
viable_resume_id. The tailer needs the decode contract verified.

**Technical design:** *(directional — see High-Level Technical Design above for the loop sketch)*. The `SessionRegistry` is the only piece with non-obvious shape; treat the pseudo-code as illustrative of the loop, not the registry implementation.

**Patterns to follow:**
- `autoresearch/events.py:tail_events_sse` — polling + inode-rotation
  detection, async generator pattern. The tailer is a long-running
  task rather than a generator, but the polling + idempotency
  conventions transfer.
- `autoresearch/sessions.py:viable_resume_id` — exact CC encoded-cwd
  + Codex rollout-glob patterns.
- `src/api/main.py` lifespan — pattern for `asyncio.create_task(...)`
  + `task.cancel()` + `await task` cleanup.

**Test scenarios:**
- **Happy path (CC)** — drop a new CC JSONL at `~/.claude/projects/-tmp-clients-acme-foo/sid123.jsonl` with cwd-decoded-from-dirname = `/tmp/clients/acme/foo`. Tailer tick emits `kind="session_start"` to `clients/acme/audit/events.jsonl` with `metadata.session_id="sid123"`, `metadata.source="cc"`, `metadata.file_path="/abs/..."`, and appends a registry row.
- **Happy path (Codex)** — drop a Codex JSONL at `~/.codex/sessions/2026/05/18/rollout-2026-05-18T12-00-00-sidcodex.jsonl` with `session_meta` event containing `cwd=/tmp/clients/acme/foo`. Tailer emits same shape with `source="codex"`.
- **Happy path (operator-internal)** — CC session under `~/foo/bar/` (no `clients/<slug>/` segment) → emit `kind="session_start"` to `~/.local/share/gofreddy/events.jsonl`, NOT to any per-client log.
- **Edge case** — slug pattern validation: cwd contains `clients/Invalid Slug!/` → operator-internal + `kind="moment"` / `moment_kind="attribution_conflict"` with `metadata.reason="slug_invalid"` (R5.5).
- **Edge case** — slug looks valid but is not in the `clients` table → operator-internal + `attribution_conflict` with `metadata.reason="slug_unknown"` (R5.5 + R7 case i).
- **Edge case** — sanity-parse fails (file appears but has no valid CC or Codex first-line) → skip emission, retry next tick (file may be mid-write).
- **Edge case** — session_end via idle timeout: file mtime hasn't advanced in >10 min AND size unchanged across 3 ticks → emit `session_end` with `metadata.reason="idle_timeout"`.
- **Edge case (reconcile-on-startup with stale sessions)** — startup finds 308 CC project dirs, most with mtime > 24h ago. Tailer registers them in the session registry (so the IDOR guard can resolve them for drill-down) but does NOT emit any `session_start`/`session_end` to the wide log for historic sessions. Only newly-appearing files post-startup emit timeline events. Net: portal timeline isn't spammed with historic noise; historic sessions remain accessible via drill-down if a user has the URL.
- **Edge case** — session_end via Codex `task_completed` event observed mid-tail → emit `session_end` with `metadata.reason="task_completed"`.
- **Edge case** — session_end via Codex `task_aborted` event observed mid-tail → emit `session_end` with `metadata.reason="task_aborted"`.
- **Integration (R8.3 dedup)** — pre-existing `kind="session_start"` for the same `session_id` already in the per-client log → tailer skips emission, marks `hook_emitted=true` in registry, does not double-write.
- **Integration (restart-safety)** — sessions.jsonl has 5 prior rows on disk; tailer starts; rebuilt registry contains those 5 sessions in correct latest-row state. New JSONL appearing post-restart triggers `session_start` once.
- **Integration (R7 cross-tenant)** — sub-cases (g) cwd under `clients/A/` → A; (h) cwd elsewhere → operator-internal; (i) cwd matches but slug not in `clients` table → conflict-operator-internal; (j) hook emitted session_start for sid X, tailer notices same sid → tailer dedups (registry shows `hook_emitted=true`).
- **Error path** — tailer tick raises (e.g. PermissionError reading a CC file) → caught by outer try/except, emit `kind="alert"` operator-internal, loop continues. No tailer crash.
- **Lifespan integration** — uvicorn startup creates the task; uvicorn shutdown cancels + awaits; task does not leak.

**Verification:**
- `pytest tests/portal/test_transcript_tailer.py` green.
- Smoke: drop a real CC JSONL under `~/.claude/projects/-tmp-clients-smoke-test-001-bar/sidX.jsonl` while the backend runs; within ~2s a `session_start` event appears in `clients/smoke-test-001/audit/events.jsonl`.

---

- [ ] **Unit 3: Moments REST endpoint**

**Goal:** Serve the derived-on-read moments list that the frontend
loads on page open.

**Requirements:** R-Live-1, R-Live-3 (since-backfill).

**Dependencies:** Unit 1 (timeline-eligible kinds need to exist).

**Files:**
- Modify: `src/api/routers/portal.py` — add `portal_moments` route
  (`GET /v1/portal/{slug}/moments`).
- Create: `tests/test_api/test_portal_moments.py`.

**Approach:**
- Route signature: `async def portal_moments(slug: Annotated[str, Path(pattern=r"^[a-z0-9-]{1,64}$")], request: Request, principal: Annotated[AuthPrincipal, Depends(get_auth_principal)], limit: Annotated[int, Query(ge=1, le=200)] = 50, since: Annotated[str | None, Query(pattern=r"^evt_[A-Za-z0-9_-]+$")] = None, before: Annotated[str | None, Query(pattern=r"^evt_[A-Za-z0-9_-]+$")] = None, kind: Annotated[str | None, Query(pattern=r"^[a-z_]+(,[a-z_]+)*$")] = None, session: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9_-]{1,128}$")] = None)`. Path/Query patterns reject malformed input at the FastAPI layer with 422 before any handler logic runs (defense in depth against log-grep path injection or session-id substring shenanigans).
- `resolve_client_access(...)` gate (404 on no membership — match origin doc R-Auth-1 + T3 stance).
- `@limiter.limit("60/minute")` — match existing portal routes.
- Backend scan: `read_events(client_events_path(slug))` + rotated
  segments (use existing rotation helper if present in events.py;
  else just glob `events.jsonl*`). Filter server-side for kinds in
  the timeline-eligible set
  `{moment, session_start, session_end, review_required, review_approve, review_reject, sla_breach, render, promotion}`.
- The **timeline-eligible kind set**: `{"moment", "session_start",
  "session_end", "review_required", "review_approve",
  "review_reject", "sla_breach", "render", "promotion"}`. Defined
  inline in both this REST endpoint and the Unit 7 frontend with a
  `# Keep in sync with portal_moments.html` comment. If drift becomes
  a real problem, promote to a shared constant in a follow-up — not
  worth the indirection for v1.
- Apply additional filters: `kind=` (comma-separated; intersect with
  the timeline-eligible set), `session=` (filter by
  `metadata.session_id`), `since=<event_id>` (events strictly after,
  inclusive of `since` semantics matching the existing SSE stream's
  resume contract), `before=<event_id>` (events strictly before, for
  power-user pagination).
- Newest-first ordering, capped at `limit` (default 50, max 200).
- Apply redaction (Unit 5) to `metadata.title` + `metadata.body` of
  every returned moment BEFORE serialization. The moment row's
  `event_id` is the canonical identifier (R-Live-3); response schema:
  ```json
  {
    "moments": [
      {"event_id": "...", "ts": "...", "kind": "...", "metadata": {...redacted...}, "session_id": "...", "session_tag": "..."}
    ],
    "oldest_event_id": "...",
    "newest_event_id": "...",
    "has_more": false
  }
  ```
- `session_tag` is computed server-side from `metadata.lane` +
  optional `metadata.variant` per R3.1
  (`<lane>` or `<lane>·<variant>`); avoids each call site
  reimplementing.

**Patterns to follow:**
- `portal_summary` at `src/api/routers/portal.py:250-308` for the
  auth + membership + rate-limit + audit-page pattern.
- The `read_events` + rotation-aware path globbing pattern (existing
  in `autoresearch/events.py`).

**Test scenarios:**
- **Happy path** — slug with 75 moments (mix of `moment`,
  `session_start`, `review_required`) returns 50 newest, with
  `has_more=true` and `oldest_event_id` set.
- **Happy path** — empty slug returns `{"moments": [], "has_more": false}`, 200 (not 404).
- **Edge case** — limit=200 returns up to 200; limit=201 rejected by Query validator (422).
- **Edge case** — `since=<event_id>` returns only events strictly
  after that id, in newest-first order, capped at limit. Useful for
  SSE-reconnect backfill (R-Live-3).
- **Edge case** — `before=<event_id>` returns only events strictly
  before, capped at limit. Useful for `?before=` pagination.
- **Edge case** — `kind=session_start,moment` returns only those two
  kinds (intersected with the timeline-eligible set; `tool_call`
  filtered out even if asked for).
- **Edge case** — `session=<sid>` returns only events whose
  `metadata.session_id` matches.
- **Edge case** — rotated `events.jsonl.1`, `.2` segments present;
  endpoint reads all and merges newest-first across files.
- **Error path** — 404 on slug-not-in-clients-table (slug literally doesn't exist).
- **Error path** — 403 `no_membership` on user-without-membership (matches existing route convention at `portal_summary` etc.).
- **Error path** — 401 on missing auth (covered by `Depends(get_auth_principal)`).
- **Integration (redaction)** — a moment whose `metadata.title` contains a fake API key (matched by scrub.py) returns with the key replaced by `<redacted:api_key>` in the response.
- **Integration (HTML in title)** — `metadata.title="<script>x</script>"` returns verbatim in the JSON (escape happens at HTML render time in Unit 7, not in the JSON API). Documented expectation.
- **Performance smoke** — 10K-event per-client log returns in <200ms locally (SC1 bound; not gated in CI).

**Verification:**
- `pytest tests/test_api/test_portal_moments.py` green.
- Smoke: `curl -H "Cookie: sb_session=$(cat ~/.gofreddy_smoke_jwt)" http://localhost:8000/v1/portal/smoke-test-001/moments | jq` returns sane shape against the smoke seed.

---

- [ ] **Unit 4: Cookie auth migration (`POST /v1/auth/cookie` + `DELETE /v1/auth/cookie` + remove `?token=`)**

**Goal:** Replace the SSE `?token=<jwt>` URL fallback with an
httpOnly cookie set by a new endpoint; EventSource then inherits
the cookie via same-origin. Cookies are SameSite=Strict + Secure.

**Requirements:** R-Auth-2, R-Auth-3, R-Auth-4. (T2 also relies on
this — JWT no longer in URL means no token disclosure in logs.)

**Dependencies:** None (independent of Unit 1; can land in parallel).

**Files:**
- Modify: `src/api/routers/auth.py` (existing file per repo scan) —
  add `POST /v1/auth/cookie` + `DELETE /v1/auth/cookie` routes.
- Modify: `src/api/dependencies.py` — extend `get_auth_principal` to
  read `sb_session` cookie BEFORE Authorization header (existing
  Authorization + X-API-Key paths preserved as fallbacks for
  non-browser callers).
- Modify: `src/api/routers/portal.py` — REMOVE `_resolve_principal_for_sse` (lines 816-847) and the `token: Annotated[str | None, Query()] = None` parameter on `portal_stream` (lines 850-897). `portal_stream` becomes `Depends(get_auth_principal)`-only like the other authed routes.
- Modify: `portal/templates/portal_phase2.html` — DEFER deletion to
  Unit 7 (the whole template retires there); but if Unit 4 lands
  first, ALSO strip the `?token=` query construction at lines
  557-558 so the template still works between Unit 4 and Unit 7.
- Modify: `portal/templates/login.html` — after the Supabase JS
  signIn resolves, POST `{access_token: <jwt>}` to
  `/v1/auth/cookie`. Redirect to `/portal/<slug>` only after the
  cookie is set.
- Create: `tests/test_api/test_auth_cookie.py`.

**Approach:**
- `POST /v1/auth/cookie` body: `{"access_token": "<jwt>"}`. Endpoint
  validates the JWT by **calling the same low-level decoder
  `_decode_supabase_jwt(token, supabase_settings, jwks_client)` that
  `verify_supabase_token` uses internally** (lines 98-180 of
  `src/api/dependencies.py`) — this preserves `aud="authenticated"`,
  `iss=<supabase_url>/auth/v1`, exp-claim enforcement, JWKS-first /
  HS256-fallback algorithm allowlist, AND the `is_token_revoked`
  blocklist check. Alternative (less clean): wrap the token as
  `HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)` and
  call `verify_supabase_token(request=request, credentials=...)`
  directly — the existing `_resolve_principal_for_sse` at
  `src/api/routers/portal.py:842` demonstrates this pattern. Either is
  acceptable; the direct decoder call is preferred for clarity. On
  success, `Response.set_cookie(key="sb_session", value=token,
  max_age=exp_seconds_from_now, httponly=True, samesite="strict",
  secure=True, path="/")`. On failure, 401 `invalid_token`.
- `DELETE /v1/auth/cookie` sets `sb_session` to empty with
  `max_age=0`. Returns 204.
- `get_auth_principal` precedence (highest→lowest): `sb_session`
  cookie → `Authorization: Bearer <jwt>` header → `X-API-Key`
  header. Cookie present and invalid → 401 (don't fall through to
  header).
- `Secure=True` requires the connection to be HTTPS. For local
  development (`http://localhost:8000`), browsers accept `Secure`
  cookies on `localhost` explicitly (W3C exception). Verified
  through manual smoke against `localhost:8000`; documented in
  runbook (R-Runbook-1) for non-localhost dev setups.
- `SameSite=Strict` is correct for first-party portal access. If
  the portal is ever embedded in an iframe (it is not in v1; out of
  scope per origin doc Scope Boundaries), this would need to relax
  to `Lax`.
- The `verify_supabase_token` HS256 fallback path uses
  `supabase_settings.supabase_jwt_secret`; ensure that config is
  loaded the same way the existing endpoints load it.
- 401 from any portal API → frontend handler (Unit 7) redirects to
  `/login`. EventSource `onerror` redirects on auth-failure events.

**Patterns to follow:**
- `src/api/dependencies.py:125-180 verify_supabase_token` for JWT
  validation reuse.
- `src/api/routers/auth.py` existing endpoints for route signature
  + pool dependency injection conventions.
- `src/api/routers/portal.py:portal_summary` for the `Depends(get_auth_principal)` baseline pattern that `portal_stream` adopts.

**Test scenarios:**
- **Happy path** — `POST /v1/auth/cookie` with a valid JWT sets `sb_session` cookie with httpOnly + SameSite=Strict + Secure + Max-Age matching JWT exp.
- **Happy path** — `DELETE /v1/auth/cookie` clears `sb_session` (Max-Age=0, value empty), returns 204.
- **Happy path** — request with valid `sb_session` cookie hits authed route → 200, principal resolved from cookie.
- **Edge case** — request with cookie + Authorization header both set: cookie wins (explicit precedence rule).
- **Edge case** — request with empty/blank `sb_session` cookie + Authorization header → falls through to header path.
- **Error path** — `POST /v1/auth/cookie` with invalid JWT → 401 `invalid_token`, cookie NOT set.
- **Error path** — `POST /v1/auth/cookie` with expired JWT → 401 `token_expired`, cookie NOT set.
- **Error path** — request with INVALID `sb_session` cookie does NOT fall through to Authorization header → 401 (cookie present-but-invalid is a definitive failure, not soft-fail).
- **Removal verification** — `grep -rn "_resolve_principal_for_sse\|token: Annotated\[str | None, Query" src/` returns no hits after the change.
- **Removal verification** — `portal_stream` route signature has no `?token` query parameter; calling with `?token=...` → param ignored, route uses cookie/header only.
- **Integration (SSE)** — `EventSource("/v1/portal/<slug>/stream")` from a logged-in browser session connects on cookie alone (no `?token=` in URL).
- **Integration (logout)** — `DELETE /v1/auth/cookie` followed by SSE reconnect → 401, EventSource.onerror fires.
- **Security (T6 logout revocation)** — call `DELETE /v1/auth/cookie` while authed; then attempt to reuse the JWT via `Authorization: Bearer <jwt>` → 401 (the blocklist via `is_token_revoked` blocks the replay until the JWT exp passes naturally).
- **Security (cookie claim parity)** — cookie path validation rejects: (a) JWT with wrong `aud`; (b) JWT with wrong `iss`; (c) revoked JWT (post-`DELETE /v1/auth/cookie`); (d) JWT signed with HS256 when JWKS endpoint expects ES256 (algorithm-confusion negative).

**Verification:**
- `pytest tests/test_api/test_auth_cookie.py tests/test_api/test_portal_stream.py` green (existing stream tests updated to use cookie or Authorization header — no more `?token=` test fixtures).
- `grep -rn "?token=" portal/templates/` returns no hits after Unit 7 (Unit 4 alone may leave the template's `?token=` construction in place if Unit 7 lands later).
- Smoke: browser login round-trip — `/login` page → cookie set → `/portal/<slug>` loads → SSE connects without URL token.

---

- [ ] **Unit 5: Server-side redaction pass (extend scrub.py + file-pattern denylist + versioned + operator log)**

**Goal:** All agent-produced content surfaces (transcript bodies,
moment titles + bodies + metadata) pass through a deterministic
redaction step before reaching the browser, with versioning and
audit logging.

**Requirements:** R-Sec-1, R-Sec-2, R-Sec-3, R-Sec-4, R-Sec-5.

**Dependencies:** Unit 1 (uses `emit_moment` for operator-internal
redaction audit events).

**Files:**
- Modify: `src/shared/reporting/scrub.py` — add patterns for: (a)
  Supabase service_role keys if not already JWT-caught (verify by
  test); (b) env-var assignments `[A-Z][A-Z0-9_]*_(API_)?KEY=<...>`
  (c) `password=<...>` literal; (d) confirm `DATABASE_URL=postgres(ql)?://user:pass@host/db` is caught (likely already by DB-creds regex; verify by test).
- Create: `src/portal/redaction.py` — top-level functions
  `redact_text(s: str) -> tuple[str, list[RedactionRecord]]`,
  `redact_metadata(d: dict) -> tuple[dict, list[RedactionRecord]]`,
  `redact_transcript_event(ev: dict) -> tuple[dict, list[RedactionRecord]]`.
  Exports `REDACTOR_VERSION = "v1"`.
- Create: `src/portal/file_denylist.py` (or inline in
  `redaction.py` — pick at impl) — file-pattern denylist for
  Bash/Read tool args matching `.env`/`.envrc`/`*.pem`/`id_rsa*`/`*.key`/`.git/credentials`.
- Create: `tests/portal/test_redaction.py` — comprehensive coverage
  including all R-Sec invariants.

**Approach:**
- `redact_text(s)` delegates to existing `scrub` for the regex
  patterns (added in this unit), then returns the redacted text +
  a list of `RedactionRecord(redaction_kind: str, source: str)`
  entries.
- `RedactionRecord` shape:
  `{redaction_kind: "api_key"|"jwt"|"aws"|"github"|...|"file_denylist", source: "transcript"|"moment_title"|"moment_body"|"moment_meta", original_length: int}` — original value NEVER logged (only kind + length for cardinality).
- `redact_metadata(d)` walks the dict, applying `redact_text` to
  every string leaf (titles, bodies, action, args_summary,
  reviewer_note, reason_text, etc.).
- `redact_transcript_event(ev)` applies a **layered defense**
  against T1 (Bash/Read reveals secrets):
  1. **File-pattern denylist on tool args** for Bash + Read + Write
     + Edit + MultiEdit + NotebookEdit + Grep (broadened from
     Bash/Read-only). Match against arg fields (`command`,
     `file_path`, `pattern`) for tokens
     `\b(\.env(\.\w+)?|\.envrc|id_rsa\w*|\.git/credentials|\.pem|\.key|\.crt|\.p12)\b`.
     Path resolution: extract candidate paths from the arg, expand
     `$HOME`/`~` server-side, re-check against the denylist.
  2. **`redact_text` over all remaining strings** (including any
     un-redacted tool results) catches inline secrets via
     `scrub.py`'s 17+ regex patterns.
  - If layer 1 fires, the tool's `result` is replaced with summary
    text; args remain visible (path is not the secret, contents are).
  - Layer 2 always runs.
  - **Note on residual risk:** regex-on-command has known evasions
    (`bash -c '...'`, alternate readers, command substitution). A
    tool-result-content heuristic was considered and deferred:
    operator-internal redaction audit log (R-Sec-3) surfaces what
    IS being redacted, so operators can add patterns when new
    shapes appear. If a real leak is found post-ship, a v2 plan
    adds the heuristic layer.
- Versioning: every redacted output carries
  `metadata.redactor_version = REDACTOR_VERSION`; consumers (Unit 6
  transcript renderer, Unit 3 moments REST) include this in their
  responses or HTML comments for future audits.
- Operator-internal logging (R-Sec-3): each
  `RedactionRecord` triggers `log_global(kind="moment", metadata={"moment_kind": "redaction_applied", "redaction_kind": ..., "source": ..., "original_length": ..., "redactor_version": ...}, path=operator_internal_path())`. Title omitted (we don't want redacted-content evidence in the operator log either).
- HTML-escape happens at render time (Unit 6 + Unit 7), NOT in
  `redact_*` — redact is regex over raw text; escape is HTML-safe
  conversion of the already-redacted output.
- Default-deny is configurable per-event via an explicit
  `allow_secret_file=True` boolean only set by operator UI (out of
  scope for v1 — the flag exists in the function signature, never
  toggled true in v1 code paths).

**Patterns to follow:**
- `src/shared/reporting/scrub.py` for the regex-list +
  `SECRET_PATTERNS` convention. Match existing pattern names where
  possible (`api_key` / `jwt` / etc.) so downstream consumers can
  count by kind.

**Test scenarios:**
- **Happy path (R-Sec-1)** — text containing `sk-ant-api03-abc...xyz` (Anthropic key) → replaced with `<redacted:anthropic_key>`; RedactionRecord with `redaction_kind="anthropic_key"`, `source` passed through.
- **Happy path** — text containing `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (JWT) → replaced with `<redacted:jwt>`.
- **Happy path** — text containing `OPENAI_API_KEY=sk-proj-abc123` → replaced with `<redacted:env_var_key>` (new pattern).
- **Happy path** — text containing `password=hunter2` → replaced with `<redacted:password>` (new pattern).
- **Happy path** — text containing `DATABASE_URL=postgresql://user:pass@host:5432/db` → replaced with `<redacted:db_url>` (verify existing pattern).
- **Happy path** — text containing Supabase service_role key (long JWT pattern) → caught by existing JWT pattern; verify via test.
- **Edge case** — text with no secrets → returned verbatim, empty RedactionRecord list.
- **Edge case (R-Sec-2 Bash denylist)** — Bash event with `args.command="cat .env"` → result replaced with summary text, args preserved.
- **Edge case (R-Sec-2 Read denylist)** — Read event with `args.file_path="/home/x/.env"` → result replaced with summary text.
- **Edge case (R-Sec-2 wildcard)** — Read event with `args.file_path="/home/x/secrets/id_rsa"` → result replaced. Glob match against `id_rsa*`.
- **Edge case (R-Sec-2 negative)** — Read of `/home/x/notes.md` → passes through unredacted; only secret-pattern files denylisted.
- **Edge case (R-Sec-2 negative)** — Bash with `ls -la` → passes through.
- **Edge case (denylist evasion 1)** — Bash `cat $HOME/.env` → server-side `$HOME` expansion + denylist re-check → result redacted.
- **Edge case (denylist evasion 2)** — Bash `head .env` → token match on `.env` in args → result redacted.
- **Edge case (denylist evasion 3)** — Bash `python -c 'print(open(\".env\").read())'` → token match on `.env` substring → result redacted.
- **Edge case (broader tools)** — Write tool with `file_path=/home/x/.env` → result redacted (broader-than-Bash/Read coverage).
- **Edge case (broader tools)** — Grep tool with `pattern=API_KEY` searching `.env` → file_path match triggers redaction.
- **Edge case (R-Sec-5 HTML in title)** — `redact_text("<script>x</script>")` returns the string unchanged (escape is render-time); HTML-escape unit test lives in Unit 6/7.
- **Integration (R-Sec-3 audit log)** — every RedactionRecord emits an operator-internal `moment_kind="redaction_applied"` event with kind + source + length but NO original value.
- **Integration (R-Sec-4 versioning)** — `redact_text` returned output's surrounding metadata is stamped with `redactor_version="v1"` by callers in Units 3/6/7.
- **Performance smoke** — 10MB transcript text + ~20 secret matches redacts in <50ms (not gated in CI; informational).

**Verification:**
- `pytest tests/portal/test_redaction.py tests/shared/test_scrub.py` green.
- Manual: tail operator-internal log while running smoke; redaction events should appear when secrets are present in seed data.

---

- [ ] **Unit 6: Transcript drill-down route + renderer (IDOR via registry + collapsed reasoning)**

**Goal:** `GET /portal/<slug>/transcript/<session_id>?event_id=...`
renders the underlying CC or Codex session transcript with
redaction + HTML-escape, gated by the session registry IDOR check.

**Requirements:** R9, R9.1, R9.2, R9.3, R9.4, T3.

**Dependencies:** Unit 2 (tailer writes the session registry that
the IDOR guard reads). Unit 5 (redaction). Unit 4 (cookie-authed
`Depends(get_auth_principal)` for browser navigation to the
drill-down — the route itself returns static HTML, no SSE on this
page).

**Files:**
- Modify: `src/api/routers/portal.py` — add `portal_transcript`
  route.
- Create: `src/portal/transcript_parser.py` — pure functions:
  `parse_cc_jsonl(path) -> list[TranscriptEvent]`,
  `parse_codex_jsonl(path) -> list[TranscriptEvent]`. Returns
  normalized events (user_msg, agent_text, agent_reasoning,
  tool_call, tool_result). Reused by tests independently of the
  route.
- Create: `portal/templates/portal_transcript.html` — Jinja2
  template extending `base.html`. CSS may be inline initially;
  extract to partial during impl if it grows.
- Create: `tests/test_api/test_portal_transcript.py`.
- Create: `tests/portal/test_transcript_parser.py`.

**Approach:**
- Route: `@router.get("/portal/{slug}/transcript/{session_id}", response_class=HTMLResponse)` with `Depends(get_auth_principal)` + `resolve_client_access(...)`.
- **IDOR guard (R9.1):** read `clients/<slug>/audit/sessions.jsonl`,
  scan for a row matching `session_id == <session_id>`. If absent
  → 404 (NOT 403). The registry also provides `file_path` —
  **never** construct the file path from `<session_id>` user input.
- **Path safety (defense in depth, T8):** the registry's
  `file_path` is operator-trusted by convention (only the tailer
  writes it) but enforced by code via:
  1. `Path(file_path).resolve(strict=True)` (resolves symlinks; raises
     `FileNotFoundError` on missing).
  2. Assert `resolved.is_relative_to(CC_ROOT) or
     resolved.is_relative_to(CODEX_ROOT)`, else 404
     `transcript_unavailable`.
  3. Walk each parent segment with `Path.is_symlink()` and refuse
     if any segment is a symlink that points outside the roots —
     mirrors the symlink-rejecting pattern in
     `src/api/routers/portal.py:_safe_archive_path`.
  4. Catch the resolve+assert in a single helper
     `_safe_transcript_path(file_path) -> Path | None`; returning
     `None` triggers 404, no traceback leaked.
- Parse the JSONL via `transcript_parser.parse_cc_jsonl(path)` or
  `parse_codex_jsonl(path)` based on the registry row's
  `source` field. Each parser returns a list of normalized
  `TranscriptEvent` records: `{event_id, role: "user"|"agent",
  kind: "msg"|"reasoning"|"tool_call"|"tool_result", body: str,
  ts: str, tool_name: str | None, args: dict | None, result: str |
  None, token_counts: dict | None}`.
- Apply `redact_transcript_event(ev)` to each (Unit 5) BEFORE
  rendering.
- HTML-escape via Jinja2 autoescape (already on for `.html`
  templates).
- Reasoning blocks: **v1 = inline accordion + plain-text rendering**
  (decided in planning; modal/side-panel + markdown parser deferred
  to a future plan if a real client complains). Same row gains a
  `.expanded` class on click, rendering the body inline below the
  one-line summary — consistent with tool-call expand behavior, no
  modal library, no side-panel JS. **Body rendered as escaped plain
  text inside `<pre class="agent-reasoning-body">`** with monospace
  font + a simple linkifier (regex `https?://\S+` → `<a href>` AFTER
  Jinja autoescape). No markdown parser dependency; no `|safe`
  filter; no XSS-after-redaction risk. If real transcripts show
  markdown that demands rendering, a v2 plan can add it with explicit
  order-of-operations (redact → markdown → sanitize → escape).
- Tool calls one-lined with `tool_name + args_summary` (e.g.
  `Bash · git status`); expand toggle reveals full args + result.
- `?event_id=<id>` anchor: page renders an `id="evt_<event_id>"`
  attribute per event; on load, JS scrolls to and highlights that
  element.
- Token counts + cache info gated behind a per-turn "details"
  toggle (R9.3).
- **Back-navigation:** header includes a left-aligned dim ink-500
  "← back to timeline" link pointing to `/portal/<slug>`. Browser
  back button also works via standard HTML anchor; no SPA state to
  persist in v1.
- **Interaction states (concrete):**
  - **loading** — server-rendered page; no JS pre-render. If a tiny
    inline-deferred script is needed to handle the `?event_id` scroll
    anchor, render the page shell first, then the script runs on
    `DOMContentLoaded`.
  - **large-transcript-paginating** — if parsed events exceed 500,
    render the first 500 inline + a "Load older events" link that hits
    the same route with `?before=<oldest_rendered_event_id>` (server
    paginates; no client-side fetch).
  - **file-not-found** (registry row points to missing file) — 404
    with body `transcript_unavailable`.
  - **parse-error** — render up to the broken line + a final muted
    footer row `Transcript truncated due to parse error.`
  - **redaction-applied** — the redaction footer described above.
- Page wraps content in a redaction footer at the bottom of the
  transcript scroll container, dim ink-500, JetBrains Mono, formatted
  exactly: `N values redacted · portal-redactor v1`. Footer omitted
  when N=0. Per-tool replacement uses origin-doc wording verbatim:
  `Read /path/to/.env (87 lines — contents redacted)` for Read;
  `Bash · cat .env (output redacted)` for Bash.
- CSP header set via FastAPI middleware on this route (and Unit 7's
  route): `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'`. No inline scripts allowed (T4). Inline `<style>` permitted by `'unsafe-inline'` for CSS only — JS lives in a `static/` file.

**Patterns to follow:**
- `src/api/routers/portal.py:portal_report_view` (lines 379-443)
  for the auth + membership + path-safety + HTMLResponse pattern
  + the symlink-rejecting `_safe_archive_path` reference.
- `autoresearch/sessions.py:viable_resume_id` for the CC + Codex
  path conventions (encoded-cwd ↔ real path).

**Test scenarios:**
- **Happy path (CC)** — registry has session `sid123` for slug `acme` mapped to `/home/x/.claude/projects/-tmp-acme-foo/sid123.jsonl`; route returns 200 HTML with user/agent/tool rows; `?event_id=evt_5` adds `data-anchor="evt_5"` to the corresponding element.
- **Happy path (Codex)** — same but for a Codex rollout; verify Codex `task_completed` event renders as `session_end` row.
- **Edge case (R9.1 IDOR)** — request for a `session_id` NOT in `clients/acme/audit/sessions.jsonl` → 404 (not 403). Same `session_id` IS in `clients/other-tenant/audit/sessions.jsonl` → STILL 404 from `acme`'s URL.
- **Edge case (R9.1 cross-tenant)** — outsider JWT with no membership requests any slug → 404 (covered by `resolve_client_access`).
- **Edge case (reasoning collapsed)** — render output contains `class="agent-reasoning collapsed"` for every reasoning event by default.
- **Edge case (large transcript)** — 2000-line CC JSONL renders without crashing; smoke timing in dev only, not CI-gated.
- **Edge case (redaction integration)** — Bash event with `cat .env` → renders as `Bash · cat .env` one-line, result shows `<file path> (N lines — contents redacted)` summary (Unit 5 invocation).
- **Edge case (redaction footer)** — if redactions occurred, the footer shows the count; if zero, the footer is omitted.
- **Edge case (Codex task_aborted)** — Codex transcript with `task_aborted` event renders the abort reason inline.
- **Error path** — registry row's `file_path` does not exist on disk (race condition: tailer recorded it, then operator deleted) → 404 `transcript_unavailable`.
- **Error path** — JSONL parse error mid-file → render up to the broken line + footer "Transcript truncated due to parse error".
- **Security (T8 path traversal)** — registry row with `file_path="/etc/passwd"` → 404 `transcript_unavailable` (NOT 500, NOT file read).
- **Security (T8 dot-dot)** — registry row with `file_path="~/.claude/projects/-foo/../../../etc/shadow.jsonl"` → resolve sees `/etc/shadow.jsonl`, not under either root → 404.
- **Security (T8 symlink)** — registry row with `file_path` pointing to a symlink whose target is outside the watched roots → 404 (resolved path fails the relative-to check).
- **Security (T8 symlink-in-parent)** — registry row with `file_path="/Users/x/.claude/projects/safe-link/sid.jsonl"` where `safe-link` is itself a symlink to `/Users/x/secrets/` → 404.
- **Security (T4)** — agent text containing `<script>alert(1)</script>` renders as escaped text, not executed. Verified by parsing the HTML response and asserting `<script>` does NOT appear unescaped.
- **Security (T4)** — CSP header present in response: `Content-Security-Policy: default-src 'self'; ...`.
- **Security (T4)** — moment title `<img src=x onerror=alert(1)>` (if it slipped through) renders escaped.
- **Performance** — 1000-line CC transcript renders in <500ms locally.

**Verification:**
- `pytest tests/test_api/test_portal_transcript.py tests/portal/test_transcript_parser.py` green.
- Smoke: click a moment in the new portal → drill-down renders the CC transcript with reasoning collapsed; click reasoning → expands.

---

- [ ] **Unit 7: Filterless moments-timeline frontend (replaces portal_phase2.html)**

**Goal:** The new `/portal/<slug>` page renders the cost-ledger
header + filterless moments timeline. Click → drill-down. SSE
subscribes to the existing stream + filters timeline-eligible kinds
client-side. Replaces `portal_phase2.html`.

**Requirements:** R1, R1.1, R1.2, R2, R3, R3.1, R4, R-Live-1,
R-Live-2, R-Live-3, R-Schema-2 (frontend mapping), R-Auth-4 (401
redirect), Design Language.

**Dependencies:** Unit 1 (kinds), Unit 3 (REST endpoint), Unit 4
(cookie auth so EventSource works without `?token=`), Unit 5
(metadata.title redacted by the API), Unit 6 (drill-down URL
targets).

**Files:**
- Create: `portal/templates/portal_moments.html` — extends
  `base.html`. Inlines or imports the cost-ledger header + timeline
  CSS (extracted from `portal_phase2.html` lines 260-308 or
  re-inlined; pick during impl).
- Modify: `src/api/routers/portal.py:portal_shell` — flip template
  rendering from `portal_phase2.html` to `portal_moments.html`.
- Delete: `portal/templates/portal_phase2.html` — retired with this
  unit. (Out of caution, keep the file in the PR diff for review;
  delete in the same commit that flips `portal_shell`.)
- Create: `tests/test_api/test_portal_moments_page.py` — smoke
  tests for the rendered HTML shape (presence of cost-ledger
  header, timeline container, expected JS bootstrap).

**Approach:**
- Page-load flow:
  1. JS fetches `GET /v1/portal/<slug>/moments` (Unit 3). Hard cap
     50 rows on first paint.
  2. JS connects to `GET /v1/portal/<slug>/stream` (existing SSE,
     now cookie-authed per Unit 4). Filters client-side for kinds
     in the timeline-eligible set.
  3. New SSE moments prepend to the list. The hard cap holds:
     prepending a moment evicts the oldest row from the rendered
     DOM (kept in JS memory only — no scroll-forever).
  4. **EventSource error classification (Unit 7 reality check —
     EventSource.onerror exposes no HTTP status code per W3C spec).**
     On every `onerror`, fire a lightweight auth-probe
     `fetch('/v1/portal/<slug>/moments?limit=1', {credentials: 'same-origin'})`:
     - **401** → cookie expired or invalidated; clear local UI state
       and `window.location = '/login'`.
     - **200** → auth still good; treat as transient drop. Show
       "reconnecting" indicator at the bottom (dim ink-500,
       non-blocking). EventSource browser auto-reconnects per spec.
     - **Network error on probe** → also transient; same UI as above;
       retry probe on next `onerror` fire.
     - On successful reconnect: re-fetch
       `/v1/portal/<slug>/moments?since=<last_seen_event_id>` to
       backfill missed moments (R-Live-3).
  5. The auth-probe is intentionally lightweight (limit=1, single
     row) so its cost on flapping connections is minimal.
- Row structure (R3 + R3.1):
  ```html
  <div class="log-line k-moment k-mk-deliverable_ready" data-event-id="...">
    <span class="ts">HH:MM:SS</span>
    <span class="session-tag">marketing_audit·v007</span>
    <span class="title">Drafted 4 LinkedIn posts in your voice</span>
  </div>
  ```
  Whole row is `<a href="/portal/<slug>/transcript/<session_id>?event_id=<id>">` — single click, navigates to drill-down (R4).
- **`review_required` badge (origin Scope Boundaries inheritance):**
  rows with `kind="review_required"` include a `<span class="badge
  badge-action">needs review</span>` element between `.session-tag` and
  `.title`. Styled as warm-accent pill, JetBrains Mono uppercase 11px.
  This is the user-visible affordance that distinguishes "you have to
  do something" from other warm-accent rows (attribution_conflict /
  sla_breach are operator-internal-flavored; review_required is the
  client call-to-action).
- Accent colours (R-Schema-2): CSS classes `k-<kind>` for top-level
  kinds, `k-mk-<moment_kind>` for `kind="moment"` rows. Class
  cascade resolves to lime / warm / dim ink-500 per the mapping
  table.
- Cost-ledger header: derived from `portal_summary`'s
  `_cost_rollup` (already shipped in PR #61 P5). Header renders in
  <300ms (SC1) because `portal_summary` is loaded in parallel with
  moments.
- Design language anchored to existing `landing/index.html` CSS
  vocabulary (Inter Tight + JetBrains Mono + Fraunces; ink scale
  `#0a0a0c` background; lime `#c4fa0d`, warm `#f4b95b`, dim ink-500
  `#78716c`). Reuse `.log-stream`, `.log-line`, `.caret-blink`
  from the previous portal page.
- **Interaction states (concrete):**
  - **populated** — rendered moments, newest-first, hard cap 50.
  - **empty-new-client** — REST returns `moments=[]`. Render the literal
    copy `No moments yet. Activity will appear here as agents work for you.`
    (from origin doc Interaction States) in dim ink-500 inside the
    timeline container.
  - **loading-from-REST** — 6 skeleton `.log-line` placeholders in dim
    ink-500 (static, not shimmer; matches restrained-motion design
    language) until REST resolves.
  - **SSE-disconnected** — small "reconnecting" indicator at the bottom
    of the timeline, dim ink-500, non-blocking. On reconnect, fire
    `GET /v1/portal/<slug>/moments?since=<last_seen_event_id>` to
    backfill (R-Live-3).
  - **partial-load** — single muted row at the bottom: `Showing newest
    50 of N moments — older history via ?before=` (only when N>50).
  - **auth-expired** — see step 4 below; redirect to `/login`.
- **Cost-ledger header states (R-Cost-1 inheritance):**
  - **populated** — three numerics in JetBrains Mono with lime accent on
    "this month".
  - **zero-spend** — same three numerics rendering `$0` (new clients pre-
    spend); no special treatment, lime accent retained.
  - **ledger-bridge-down** — `portal_summary._cost_rollup` returns
    null/error → header collapses to a single dim-ink row
    `cost data unavailable` (no operator-detail leak); operator-internal
    `kind="alert"` event already covers ops paging.
- "Page Title" line is the only allowed Fraunces moment (optional
  serif), per Design Language.

**Patterns to follow:**
- `portal/templates/portal_phase2.html` lines 260-308 for the CSS
  vocabulary that gets migrated.
- `portal_phase2.html` JS EventSource setup as the pattern to
  REPLACE (no `?token=`; cookie-only).
- `portal/templates/base.html` for the shell extension contract.

**Test scenarios:**
- **Happy path** — `GET /portal/<slug>` returns 200 HTML containing the cost-ledger header, an empty timeline container, and the JS bootstrap for `/v1/portal/<slug>/moments` + `/v1/portal/<slug>/stream`.
- **Edge case (R1.2)** — rendered HTML contains NO filter-chip elements, NO load-more button, NO active-sessions card, NO awaiting-input pane, NO narrative-intro section.
- **Edge case (R2 hard cap)** — JS code references the 50-row cap (asserted via inline JS string match or rendered config object).
- **Edge case (R3.1 session-tag)** — given a moment with `metadata.lane="marketing_audit"` + `metadata.variant="v007"`, the rendered row contains `marketing_audit·v007`. Given lane only (no variant) → `marketing_audit`.
- **Edge case (R-Schema-2 mapping)** — given a moment with `kind="moment"` + `metadata.moment_kind="cost_milestone"`, the row's class list includes `k-moment k-mk-cost_milestone` → resolves to dim ink-500 per the mapping.
- **Edge case (R-Schema-2 fallback)** — unrecognized moment_kind defaults to dim ink-500 class.
- **Edge case (R-Live-3 reconnect)** — JS handler for `EventSource.onerror` references `/moments?since=<last_event_id>` URL construction.
- **Edge case (R-Auth-4 401 redirect)** — JS code references `window.location = '/login'` in the auth-error path.
- **Security (T4)** — JS uses `textContent` (not `innerHTML`) when inserting moment titles into the row, preventing client-side script injection. Verified by inline JS pattern match.
- **CSP** — response header includes a `Content-Security-Policy` directive consistent with Unit 6's.
- **Smoke** — `portal_phase2.html` removed from the repo after Unit 7 commit (`grep -rn "portal_phase2" portal/templates/ src/` returns no source hits).
- **Smoke (real client)** — manual: load `http://localhost:8000/portal/smoke-test-001` after Unit 4+7 land; cookie auth flows correctly; moments render; click → drill-down (Unit 6). One real-client SC4 validation deferred to staging step.

**Verification:**
- `pytest tests/test_api/test_portal_moments_page.py` green.
- Browser smoke (operator): login → portal renders → click moment → transcript drill-down opens.

---

- [ ] **Unit 8: Runbook update**

**Goal:** Operator onboarding documentation reflects the redesigned
portal end-to-end.

**Requirements:** R-Runbook-1.

**Dependencies:** All other units (runbook references their final
shape).

**Files:**
- Modify: `docs/runbooks/portal-client-onboarding.md`.

**Approach:**
Update the existing runbook (P6 from PR #61) with these sections:
1. **Attribution precedence (R5 env-first):** when to set
   `GOFREDDY_CLIENT_ID` in the operator's shell vs. relying on
   `clients/<slug>/...` cwd structure. Examples for both flows.
2. **Transcript tailer install:** the tailer runs in-process with
   the FastAPI app (no separate service). The session registry
   lives at `clients/<slug>/audit/sessions.jsonl` — operator can
   inspect it directly. Tunables: `GOFREDDY_TAILER_INTERVAL_S`.
3. **Cookie auth flow:** how login sets `sb_session`; how to
   verify cookies are set with `Secure` + `SameSite=Strict`; HTTPS
   requirement for non-localhost; how to forcefully invalidate a
   session (`DELETE /v1/auth/cookie` or rotate Supabase JWT
   secret).
4. **Retention manual workaround:** for GDPR right-to-erasure
   requests, operator deletes `clients/<slug>/audit/events.jsonl*`
   + `clients/<slug>/audit/sessions.jsonl` + any
   `clients/<slug>/audit/<audit_id>/` subdirs. Backups (if any)
   need separate handling — out of scope here.
5. **Cross-origin EventSource note:** if portal ever splits from
   API origin, EventSource needs `withCredentials: true` +
   `Access-Control-Allow-Credentials: true`.
6. **Smoke procedure:** end-to-end `curl` snippets for the new
   `POST /v1/auth/cookie` flow + `GET /v1/portal/<slug>/moments` +
   `GET /portal/<slug>/transcript/<sid>`.

**Patterns to follow:**
- Existing runbook structure at
  `docs/runbooks/portal-client-onboarding.md` (P6 shipped in PR #61).

**Test scenarios:**
- Test expectation: none — documentation-only unit (R-Runbook-1).
- Verification: operator (JR) reads the updated runbook end-to-end
  before the redesign PR merges. Cited as the SC4 readiness
  signal in the PR description.

**Verification:**
- Runbook contains all 6 sections above.
- A fresh operator could follow the runbook to onboard a new client
  end-to-end without referencing this plan or the requirements doc.

## System-Wide Impact

- **Interaction graph:**
  - The FastAPI `lifespan` (`src/api/main.py:642`) gains a new
    asyncio task (the tailer). Cancellation must be ordered: cancel
    the task BEFORE closing the Postgres connection pool that the
    tailer's R5.5 slug-validation uses.
  - `src/api/dependencies.py:get_auth_principal` gains a cookie
    branch consumed by EVERY authed route in `src/api/routers/`
    (not just portal). Side effect: any non-portal route that uses
    `Depends(get_auth_principal)` becomes cookie-aware too. Audit
    grep before landing Unit 4: `grep -rn "Depends(get_auth_principal)" src/api/routers/` enumerates the surface.
  - `autoresearch/events.py:KNOWN_KINDS` / `CANONICAL_FIELDS` are
    asserted by `tests/autoresearch/test_events.py:83-116`; adding
    kinds breaks the drift test unless the assertion is updated in
    the same commit (Unit 1 covers this).
- **Error propagation:**
  - Tailer tick failures are caught and logged via `kind="alert"`
    operator-internal; tailer never crashes the FastAPI process.
    **Important:** outer try/except catches `Exception`, NOT
    `BaseException`, so `asyncio.CancelledError` (which inherits
    `BaseException` in 3.8+) propagates normally and the lifespan's
    `task.cancel() + await task` shuts the tailer down cleanly.
    Confirmed in test scenarios.
  - Cookie-auth path failure on a present-but-invalid cookie is
    definitive 401 (no soft-fall to Authorization header) — this
    is intentional but should be documented (above + runbook).
  - JSONL parse errors mid-transcript do NOT abort the render —
    partial transcript + truncation footer.
- **State lifecycle risks:**
  - Session registry (`clients/<slug>/audit/sessions.jsonl`) is
    append-only; reconciliation rule on startup is "latest row per
    session_id wins." Operator manual deletion of the registry
    (allowed for retention) causes the tailer to re-emit
    `session_start` for surviving JSONLs on next tick — accepted
    (the resulting events are dedup'd against any existing
    per-client `session_start` per R8.3).
  - Cookie `Max-Age` matches JWT `exp`; if the system clock skews
    significantly between API and browser, cookie may expire
    earlier or later than the JWT itself — Supabase JWT validation
    will catch the mismatch on the API side, returning 401, which
    the frontend redirects.
- **API surface parity:**
  - The `?token=` URL fallback is removed from EVERY route that
    used it (only the SSE route did; verified via grep). No other
    surface adopts a URL token.
  - The new `/v1/auth/cookie` endpoints are NOT versioned beyond
    `/v1/`; same convention as other portal endpoints.
- **Integration coverage:**
  - End-to-end smoke: tailer detects a new CC session, writes
    registry + `session_start`, frontend SSE delivers the row,
    user clicks → drill-down route reads registry and serves
    transcript. Run as the SC5 (Codex parity) check too.
- **Unchanged invariants:**
  - `autoresearch/events.py log_event(...)` signature, flock
    behavior, rotation behavior — UNCHANGED. `emit_moment` is a
    thin wrapper, not a replacement.
  - `src/api/membership.py:resolve_client_access` — UNCHANGED.
  - `src/audit/cost_ledger.py:_mirror_to_canonical_events` —
    UNCHANGED.
  - `tail_events_sse` SSE generator — UNCHANGED.
  - PR #61 `portal_summary` route — UNCHANGED.
  - `kind="cost_threshold_crossed"` is REMOVED from emitters
    (Unit 1 reclassifies); any external consumer that was watching
    for it must switch to `kind="moment"` +
    `metadata.moment_kind="cost_milestone"`. Verified that the
    only emitter was `cost_observability.py` and the only consumer
    was unused (it was never in `KNOWN_KINDS`).

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| **Plan-002 begins implementation in parallel and double-implements `emit_moment`.** | Mitigated by Unit 0 (plan-002 coordination doc edit, lands first). Cross-reference becomes the tripwire: a plan-002 implementer reads U6b → sees the pointer → consumes from this plan's commit. |
| **Tailer race on file-mid-write** (CC writes line N, tailer reads partial JSON). | Sanity-parse first ~10 lines; on JSON decode error, skip emission, retry next tick. Test scenario covers this. |
| **EventSource same-origin cookie assumption breaks if portal is ever proxied or split.** | Documented in runbook (R-Runbook-1 §5). If split, `withCredentials: true` + CORS adjustment required. Out of scope for v1 single-host deployment. |
| **Redaction false negatives** — secret pattern not caught by scrub.py + extensions. | scrub.py is regex-based, not exhaustive. Mitigation: layered defense — file-pattern denylist for `.env*` + `id_rsa*` files prevents most disclosure paths; operator-internal redaction audit log surfaces what IS being redacted (lets operators add patterns when new shapes appear); `REDACTOR_VERSION` allows future re-scan. |
| **Tailer cancellation leaves stale registry rows** if process crashes mid-emit. | Append-only registry tolerates this — the reconcile-on-startup rule rebuilds from disk; partial-row crashes are caught by JSON-parse-error skip. Worst case: a session has no `session_end` row, will be picked up via idle-timeout on next session_end check post-restart. |
| **Cookie `Secure=True` breaks localhost dev for non-Safari browsers** (Firefox/Chrome allow Secure on localhost; older browsers may not). | Documented in runbook. Operators should not block on this; modern browsers handle it. |
| **Drift test failure blocks Unit 1 if assertions stale.** | Unit 1 explicitly includes the test update in the same commit as the schema change. CLAUDE.md Rule 12 (Fail loud) — better to break test loudly than silently extend the set. |
| **moment_kind vocabulary growth.** | Soft allowlist: helper accepts any moment_kind but warns on unknown via `kind="alert"`. Frontend default-fallback handles render side. Lane authors don't need helper PRs to introduce subtypes. |
| **JSONL rotation across the moments REST endpoint.** | Endpoint scans `events.jsonl` + rotated segments via the same path-globbing pattern used by `read_events`; no special handling needed. |
| **CSP breaks legitimate inline JS in `portal_moments.html`.** | Plan dictates JS lives in a `static/` file, not inline. Unit 7 includes a smoke test that the page works with CSP active. |

## Alternative Approaches Considered

- **`watchdog` library for tailer (vs. polling-glob).** Rejected.
  Adds a dependency; cross-platform behavior on macOS (kqueue) is
  not always equivalent to inotify; event coalescing on bursty
  writes requires the same throttling logic that a polling
  approach naturally provides. Polling at 1.5s costs <0.1% CPU on
  the operator host given <50 watched files; sub-second latency
  is not a stated UX requirement.
- **Native `inotify`/`fsevents` (vs. polling).** Rejected. Same
  reasoning + adds a Linux/macOS conditional. v1 single-host
  deployment is the architecture — operator hosts vary.
- **trufflehog / detect-secrets / gitleaks rule import (vs.
  extending scrub.py).** Rejected. Adds a dependency or rule-file
  format conversion for marginal coverage gain over the existing
  17 patterns. The deferred Q expected a research-driven choice;
  the research showed `scrub.py` already covers the high-signal
  patterns. Three extensions (Supabase service_role, env-var
  assignment, password literal) cost ~30 LOC + 6 test cases.
- **Materialized `moments.jsonl` (vs. derived-on-read).** Rejected
  for v1. The derived-on-read scan is <100ms for v1 volumes
  (<100K events per client). Materialization is an operational
  upgrade trigger if any client crosses ~10K events/day, not a v1
  build.
- **Separate tailer process (vs. in-process asyncio task).** Rejected.
  IPC overhead; the registry would need cross-process coordination
  (filesystem locking on the JSONL is fine). The lifespan task
  pattern keeps the surface area smaller and the failure mode
  contained.
- **LLM moment-derivation.** Rejected in the brainstorm phase
  (origin doc). Not re-visited here.
- **Server-side `moment_id` distinct from `event_id`.** Rejected
  (origin doc v3.3, P1-7). `event_id` is the canonical
  identifier; no separate `moment_id` field.

## Success Metrics

Carried verbatim from origin doc SC1–SC5:

- **SC1 (latency).** First-paint <2s; cost-ledger <300ms; moments
  REST <2s for 50 rows. Verified via operator-internal event
  instrumentation captured during smoke.
- **SC2 (signal density).** 2-hour CC session → 2-5 moments
  (session_start + session_end from the tailer + any lane-emitted).
  Weekly aggregate for an active client: ~20-60 moments across
  5-15 sessions. No raw tool_call kinds leak.
- **SC3 (cross-tenant isolation).** R7 test cases (a)-(j) pass +
  outsider JWT to transcript route → 404.
- **SC4 (one real client comprehension test).** JR shows the
  redesign to ONE real client (Klinika OR DWF); client names 3
  agency activities from the week's timeline without scrolling
  past 10 entries. This is the redesign's actual exit criterion;
  staging happens AFTER all 8 units land.
- **SC5 (Codex parity).** Codex session in a per-client worktree
  produces session_start + session_end moments with the same
  drill-down quality as CC.

## Documentation Plan

- **Unit 8 = `docs/runbooks/portal-client-onboarding.md`** updated.
- **Plan-002 coordination edit** is now Unit 0 of this plan (was
  previously a follow-up). Lands first; eliminates the race.

## Operational / Rollout Notes

- **PR boundary:** This plan ships as a follow-up PR to PR #61
  (the existing telemetry pipeline). PR #61 P5
  (`portal_phase2.html`) stays in place on `main` until this
  plan's PR merges; the new template replaces it in a single
  commit (Unit 7). Main always has a working `/portal/<slug>`.
- **No feature flag.** Single-host operator deployment; the
  redesign is the whole point of the PR. CLAUDE.md Rule 2
  (Simplicity First) — no feature flag for a wholesale
  replacement.
- **Staging.** Before declaring done, JR runs the smoke script
  (`scripts/portal_smoke_seed.py --slug smoke-test-001 --reset`),
  invokes a CC session under
  `~/Documents/GitHub/gofreddy/clients/smoke-test-001/`, and
  verifies the tailer emits `session_start` + the moments REST
  endpoint returns it + clicking the row opens the drill-down.
- **Rollback plan.** If a critical bug surfaces post-merge: revert
  the single follow-up PR. `portal_phase2.html` returns; pre-PR
  state restored. The Unit 1 schema extensions remain on `main`
  (forward-only; the new kinds are additive).

## Sources & References

- **Origin document:** [docs/brainstorms/2026-05-15-portal-moments-redesign-requirements.md](../brainstorms/2026-05-15-portal-moments-redesign-requirements.md)
- **Related plan (consumer):** [docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md](2026-05-13-002-feat-content-engine-lanes-v1-plan.md) (U6b describes the helper; this plan ships it)
- **PR #61 substrate commits** (on `design/client-portal-telemetry`): `30b2e0c` (P1 schema), `b0b0c6b` (P2 mirror), `b21a23c` (P3 ingest), `f602092` (P5 frontend being replaced), `1dbf411` (audit ↔ canonical bridge), `9876fec` (plan-002 doc coordination)
- **Existing patterns referenced:** `autoresearch/events.py`, `autoresearch/sessions.py:viable_resume_id`, `src/api/routers/portal.py:portal_summary`, `src/api/routers/portal.py:portal_report_view`, `src/api/dependencies.py:verify_supabase_token`, `src/api/main.py` lifespan, `src/shared/reporting/scrub.py`, `tests/test_api/test_portal_stream.py:9-20` (ASGITransport gotcha)
