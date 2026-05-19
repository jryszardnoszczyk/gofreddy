---
title: "Client Portal Telemetry — Design Doc v1"
type: design
status: draft
date: 2026-05-13
owner: gofreddy
related:
  - docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md (consumes telemetry via U7 reviewer events)
  - landing/index.html §01 (commits to "live portal · agent transcripts · cost ledger · reviewer events · audit trail")
prerequisites_in_code:
  - autoresearch/events.py (log_event with rotation + flock + fsync + per-path override)
  - src/api/routers/portal.py (/v1/portal/{slug}/* with Supabase membership auth)
  - src/common/cost_recorder.py (130 LOC JSONL cost append)
  - autoresearch/evaluate_variant.py:_ensure_render_score (post-fixture render scoring)
---

# Client Portal Telemetry — Design v1

A unified event stream + per-client live HTML portal showing every agent action,
reviewer decision, cost line-item, and rendered report — across autoresearch
lanes AND Claude Code interactive sessions AND human reviewer events. Codex
deferred to v1.5.

## Premise

The landing page at gofreddy.ai commits to:
- "Live portal: agent transcripts, cost ledger, reviewer events, audit trail."
- "Compliance gating where your industry requires it."
- The §01 diagram explicitly shows reviewer signals flowing back to L1
  auto-research — that loop needs a substrate to flow through.

Plan 002 builds the lanes that emit this data (the new content engines) and the
reviewer service (U7) that captures human decisions. Plan 002 does not specify
the portal itself; this doc does.

## Foundations already on main — DO NOT rebuild

Verified 2026-05-13 by `Explore` agent against `origin/main`. Treat these as
load-bearing prerequisites; the design extends them.

| Component | Path | Shape |
|---|---|---|
| Canonical event-stream JSONL writer | `autoresearch/events.py` → `log_event(kind, *, path=None, **data)` | rotation at 100MB, exclusive flock on write, shared lock on read, fsync after every entry, per-path override for per-tenant isolation |
| Cost recording | `src/common/cost_recorder.py` → `cost_recorder.record(provider, operation, *, cost_usd, tokens_in, tokens_out, model, metadata)` | async, JSONL append, ~130 LOC, NOT currently wired to `events.py` |
| Membership-gated portal route | `src/api/routers/portal.py:44` → `/v1/portal/{slug}/summary` + `/v1/portal/{slug}/reports/{lane}/{variant}/{fixture}` | `get_auth_principal` + `resolve_client_access()` via Supabase, Phase 1 placeholder returns JSON `{"phase": 1, "message": "Phase 2 will render real JSONL data here."}` |
| Render-judge after every fixture | `autoresearch/evaluate_variant.py:62` → `_ensure_render_score()` | idempotent; writes `render_score.json`; gated on `GEMINI_API_KEY` + lane having `render_rubric_ids` |
| Self-improving HTML reports | `freddy autoresearch render` (Typer CLI) | renders to `autoresearch/archive/<variant>/sessions/<lane>/<fixture>/report.html`; Stage-1 transcript extract + Stage-2 Codex synthesis |
| Variant lineage | `autoresearch/lane_runtime.py:179` → `lineage.jsonl` | variant promotion/evolution records; orthogonal to client telemetry |
| Variant alerts | `autoresearch/compute_metrics.py` → `METRICS_DIR/alerts.jsonl` | variant-state alerts; also orthogonal |

**Auth is solved.** Storage is solved (JSONL + rotation + flock). Per-client URL routing
is solved. Membership check is solved. What's missing is the canonical event
schema, multi-source ingestion, live streaming, and the Phase 2 frontend.

## What's missing — v1 build scope

1. **Canonical event schema** — extends `events.py` shape, adds `client_id`,
   `actor`, `cost_usd`, etc. Loadbearing.
2. **Multi-source ingestion** — autoresearch sessions (instrument
   `cost_recorder` + `evaluate_variant`), Claude Code sessions (hook script),
   human reviewer events (plan 002 U7 emits via `log_event`).
3. **SSE live-stream endpoint** — `GET /v1/portal/{slug}/stream` reads
   per-client events.jsonl, streams new lines as they land.
4. **Phase 2 frontend** — replace the placeholder JSON with a live transcript
   view that reuses landing-page CSS (`.log-stream`, `.log-line`, `.caret-blink`,
   `.metric-live`, `@keyframes log-line-reveal`).
5. **Cost ledger rollup** — `/v1/portal/{slug}/costs` aggregates `cost_usd`
   across events per day / per lane / per session. Reuse cost_recorder's
   existing JSONL; reads, not writes.

Out of v1 scope:
- Codex session integration (plain-text logs; v1.5 once we add a structured
  capture layer)
- Long-term retention / cold-archive to R2 (defer until first client hits 100MB
  rotation)
- WebSocket bidirectional (SSE one-way is enough — the portal observes; it
  doesn't talk back)
- Real-time edit collaboration (we are not building a doc editor)
- Per-client custom branding beyond the portal page's `<title>` and brand_tokens

## Canonical event schema

Single schema; every source emits this shape via `log_event(path=<per-client>, **payload)`.

```jsonl
{
  "ts": "2026-05-13T15:42:01.234Z",
  "event_id": "01HXYZ...",
  "kind": "tool_call|model_call|edit|review_approve|review_reject|render|session_start|session_end|cost",
  "session_id": "uuid",
  "parent_event_id": "ulid|null",
  "source": "autoresearch|claude_code|codex|portal|reviewer",
  "client_id": "klinika-melitus|dwf-poland|null",
  "actor": "agent|human|system",
  "lane": "marketing_audit|x_engine|site_engine|null",
  "variant": "v123|null",
  "fixture": "klinika_hero|null",
  "action": "string — short verb",
  "args": {},
  "status": "started|complete|failed|skipped",
  "cost_usd": 0.0123,
  "model": "claude-opus-4-7|gpt-5.5|gemini-2.5|null",
  "tokens_in": 1234,
  "tokens_out": 567,
  "metadata": {}
}
```

Notes on schema decisions:
- `kind` is the canonical event type for dispatch; `action` is human-readable
  free-text within that kind.
- `event_id` is a ULID (sortable by ts, K-sortable across hosts).
- `parent_event_id` enables tree views — a `model_call` inside a `tool_call`,
  or a `review_approve` referencing the artifact it approved.
- `client_id` is nullable: autoresearch's L1 self-improvement loop has no client
  attribution (it's pre-client work). L3 production sessions always carry a
  client_id.
- `cost_usd` is the marginal cost of the action; cost-ledger rollup sums these.
- `metadata` is an open dict for source-specific fields we don't want to
  promote to first-class.

This is a **superset** of `events.py`'s current `{kind, timestamp, **data}`
shape — existing callers continue to work; new fields land in `**data` and
become first-class as adopters wire them.

## Three ingestion paths

### A. Autoresearch sessions
Already emit via `events.py` + `cost_recorder`. Two surgical changes:
1. Augment `cost_recorder.record()` to call `events.log_event(kind="cost", ...)`
   in addition to its own JSONL — single source of truth for downstream.
2. Wrap `evaluate_variant._ensure_render_score()` to emit
   `kind="render"` events on completion.
3. Add `client_id` to `WorkflowConfig` snapshot at run-start (plan 002 D7
   already does this for per-client config); pass to all `log_event` calls
   during that run.

Per-client event path: `clients/<slug>/audit/<run_id>/events.jsonl`. Falls
back to `~/.local/share/gofreddy/events.jsonl` when `client_id` is null
(L1 self-improvement loop).

**Effort: 1 day.** Mostly wiring existing primitives.

### B. Claude Code interactive sessions
Claude Code has a hooks system. Configure a small shell script (~30 LOC) at
`~/.claude/hooks/portal-telemetry.sh` that fires on `PostToolUse` and POSTs
the tool call as an event to a local ingestion endpoint:

```bash
#!/usr/bin/env bash
# fires after each tool use
curl -s -X POST http://127.0.0.1:8000/v1/portal/_ingest \
  -H "Authorization: Bearer $GOFREDDY_INGEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<EOF
{
  "source": "claude_code",
  "session_id": "$CLAUDE_SESSION_ID",
  "kind": "tool_call",
  "action": "$CLAUDE_TOOL_NAME",
  "args": $CLAUDE_TOOL_INPUT,
  "status": "complete",
  "client_id": "${GOFREDDY_CLIENT_ID:-null}"
}
EOF
)"
```

Plus a one-time backfill script that ingests Claude Code's own JSONL
transcripts at `~/.claude/projects/<dir>/<session>.jsonl` so historical work
shows up.

`client_id` is set per-shell-session by the operator (e.g.,
`export GOFREDDY_CLIENT_ID=klinika-melitus` before opening Claude Code in
that client's worktree). Defaults to null (operator-internal work).

**Effort: 1–2 days.** Hook setup + ingestion endpoint + Claude Code
transcript backfill script.

### C. Human reviewer events
Plan 002 U7 already plans to write audit logs at
`review_audit/<client_slug>/<YYYY-MM>/audit.jsonl`. Change that to call
`events.log_event(kind="review_approve|review_reject|sla_breach", ...)` with
the per-client path. **U7 becomes a `log_event` caller, not a separate writer.**

This is a coordination point with the main plan-002 agent: when U7 lands, it
should write through the canonical event log, not its own file. If U7 ships
before this design lands, the U7 audit file becomes a second ingestion path
that the portal tails. Easier to coordinate now.

**Effort: 0 days inside this design** (it's a constraint on plan 002's U7
implementation). 1 day if U7 already shipped with its own writer and we need
a tail-follower.

### D. Codex sessions — DEFERRED to v1.5
Codex writes plain text at `harness/runs/run-<ts>/track-<x>/cycle-<n>/codex.log`.
A structured-capture wrapper is non-trivial (parsing the codex CLI output
format). Defer.

## Live streaming — SSE

`GET /v1/portal/{slug}/stream`

```python
@router.get("/v1/portal/{slug}/stream")
async def stream(slug: str, principal = Depends(get_auth_principal)):
    resolve_client_access(slug, principal)  # existing auth
    path = client_events_path(slug)  # clients/<slug>/audit/*/events.jsonl

    async def event_generator():
        # Stream existing events first (last N)
        async for event in tail_jsonl(path, follow=True, backlog=50):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

`tail_jsonl` reads with shared flock (compatible with `events.py`'s exclusive
write lock), seeks past the file size on first read, then polls (or uses
inotify) for new lines. Rotation handled by reopening on file-size shrink.

Frontend connects via `EventSource`:

```javascript
const stream = new EventSource(`/v1/portal/${slug}/stream`);
stream.onmessage = (e) => {
  const event = JSON.parse(e.data);
  appendToTranscript(event);  // reuses .log-stream / .log-line CSS
};
```

**Effort: 1–2 days.** Tail logic + SSE wiring + reconnect handling.

## Phase 2 frontend

Replace the placeholder JSON in `src/api/routers/portal.py:66` with a Jinja2
template (or stretched: a small Astro / static-HTML page) that renders:

1. **Header** — client name, lane summary, this-month cost
2. **Live transcript** (right column, sticky) — connects to `/stream`, renders
   each event in `.log-line` style with `.caret-blink` on the latest. Color
   per `kind`: lime for `tool_call`/`model_call`/`render`/`ship`, warm for
   `review_approve`/`review_reject`, dim for `cost`/`session_start`.
3. **Recent reports list** — links to existing
   `/v1/portal/{slug}/reports/{lane}/{variant}/{fixture}` route which already
   serves rendered HTML reports.
4. **Cost ledger card** — today / this-week / this-month rollup from
   `/v1/portal/{slug}/costs`.
5. **Audit trail tab** — paginated event log with filter chips
   (`kind=review_*`, `actor=human`, etc.).

CSS classes copied from `landing/index.html`:
- `.log-stream`, `.log-line`, `.caret-blink`, `.metric-live`
- `@keyframes log-line-reveal`, `@keyframes log-cycle`, `@keyframes caret-blink`
- Color tokens (lime `#c4fa0d`, warm `#f4b95b`, ink scale)

**Effort: 2–3 days.** Most time goes to making it feel as good as the landing
page; the data plumbing is small.

## Auth — already solved

The existing `/v1/portal/{slug}/*` routes use `get_auth_principal` +
`resolve_client_access(slug, principal)` via Supabase membership. This is the
same machinery the Phase 2 routes inherit unchanged.

For the `/v1/portal/_ingest` endpoint (Claude Code hook target): use a
shared-secret token from `GOFREDDY_INGEST_TOKEN` env var (operator machine
only, never sent to clients). This is the same token any operator-side
instrumentation uses.

For magic-link emails when a NEW reviewer needs portal access for the first
time: matches plan 002 U7's `pre_publish_reviewer` URL pattern — HMAC-signed
short-lived URLs land the reviewer on the membership table.

## Phasing — 1–2 weeks total

| Phase | Days | Deliverable |
|---|---|---|
| P1 — Schema lock | 0.5 | This doc + canonical event schema in `events.py` docstring; PR to merge schema decision |
| P2 — Autoresearch ingestion | 1 | `cost_recorder` augmentation; `_ensure_render_score` event emission; per-client path resolution |
| P3 — Claude Code hook | 1.5 | Hook script; `/v1/portal/_ingest` endpoint; transcript backfill script |
| P4 — SSE stream | 1.5 | `/v1/portal/{slug}/stream` endpoint; `tail_jsonl` helper; reconnect handling |
| P5 — Phase 2 frontend | 2.5 | Jinja2 template; live transcript view; cost ledger card; reports list; audit trail tab |
| P6 — Klinika smoke + polish | 1 | Run end-to-end against Klinika; reviewer-of-record sees their pipeline live; fix what shakes out |

Total: **8 working days = 1.5–2 calendar weeks** with focused work.

Codex integration (v1.5) adds another 2–3 days once structured capture lands.

## Risks

| Risk | Mitigation |
|---|---|
| Plan 002 U7 ships its own audit writer before this design lands, creating two writers | Coordinate now via the handoff prompt: U7 must call `events.log_event(kind="review_*", ...)` not `open(...).write()`. Already drafted in the site_engine handoff; extend to telemetry. |
| `events.py` rotation at 100MB doesn't compose with SSE tail-follower (tail must reopen on rotate) | `tail_jsonl` helper handles rotation by detecting file-size shrink → reopen. Tested against synthetic rotation in `tests/api/test_portal_stream.py`. |
| Claude Code hook fires too often (every tool call → ingestion endpoint pressure) | Local-only endpoint (127.0.0.1) + batch-send option in the hook script if rate becomes an issue. Realistic max ~10 events/sec per shell. |
| Per-client path resolution wrong (events leak across clients) | Single helper `client_events_path(slug)` used everywhere; unit test ensures `client_id=null` falls back to operator-internal path, never to a numbered client. |
| Cost ledger rollup expensive at scale | JSONL append-only; rollup is `sum(cost_usd)` group-by date — can be cached at 5-minute granularity if read latency matters. v1 reads JSONL directly. |
| Reviewer event privacy (PII in `args`) | `args` field carries reviewer notes; clients see their own reviewer's notes, never others'. `resolve_client_access` enforces. Audit log redacts email addresses in long-term retention per plan 002 TD-14. |
| SSE connection drops on bad network | EventSource auto-reconnects; backlog of last 50 events on reconnect prevents missing-event anxiety. |

## Open questions for the operator

These weren't decided unilaterally — flag if you want a different call.

1. **Codex deferral** — should v1 include Codex integration despite the
   plain-text-log complexity, or is v1.5 fine? *Default: v1.5.*
2. **Frontend stack** — Jinja2 templates inside the FastAPI app (simple,
   ships with existing infra) vs static Astro/Hugo page that consumes the API
   (more polish-friendly, separates concerns)? *Default: Jinja2 first, port
   to static if polish becomes the bottleneck.*
3. **Hook installation** — automatic via a `freddy hooks install` Typer
   command, or manual one-time setup in operator onboarding doc? *Default:
   Typer command + onboarding doc covers both.*
4. **Per-client cost-budget alerts** — fire an event when daily/monthly cost
   exceeds a per-client threshold? *Default: yes in v1, simple threshold
   in client.yaml, hard-coded alert recipient = operator email for v1.*
5. **Historical backfill** — when this lands, do we backfill all past
   `cost_recorder` JSONL into the canonical events stream so the cost
   ledger shows history, or fresh-start from go-live? *Default: backfill the
   last 90 days, fresh-start everything earlier.*

## Coordination with plan 002

This design extends plan 002 in three places:

1. **U7 reviewer service** must emit via `events.log_event` not its own
   writer. Edit U7's file list + approach to reflect this. (Cost: 1 line in
   U7's `approach` section + a test case.)
2. **U2 per-client config** gains a `telemetry:` block with
   `cost_budget_monthly_usd`, `cost_alert_email_recipients` (optional list),
   and `live_transcript_enabled` (bool, default true).
3. **Site_engine (U15b)** already emits via `cost_recorder` through its
   inherited substrate; no additional wiring needed. SE-1..SE-8 score events
   automatically appear in the per-client transcript.

These three are minor edits to plan 002; can land as a follow-up PR after
plan 002's main scope is committed.

## Recommended first move

Lock this schema in `events.py`'s docstring as the canonical contract.
That's the single change that lets every downstream piece begin in
parallel — autoresearch wiring, Claude Code hook, SSE endpoint,
frontend rendering all have a stable interface to build against.

Schema PR is ~30 lines of code (docstring + 8 new optional fields with
Pydantic-style validation in a sibling module). Half a day.

Everything else flows from that.

## See also

- `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` —
  consumes telemetry via U7 reviewer events
- `landing/index.html` §01 — what we sold the buyer
- `autoresearch/events.py` — the rotation/locking/durability foundation
- `src/api/routers/portal.py` — the Phase 1 placeholder this design promotes
  to Phase 2
- `~/.claude/projects/<dir>/<session>.jsonl` — Claude Code transcript format
  (one JSON object per line; `type=tool-call|tool-result|message`)
