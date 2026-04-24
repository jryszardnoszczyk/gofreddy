# Prime-fixtures agent task

**Invocation:**
```bash
claude --print --input-file docs/agent-tasks/prime-fixtures.md \
  --var pool=search-v1 \
  --var manifest_path=autoresearch/eval_suites/search-v1.json \
  --var fixture_ids="geo-semrush-pricing,geo-ahrefs-pricing,geo-moz-homepage"
# or --var fixture_ids=all to prime every fixture in the manifest
```

**Cadence:** on-demand. Run before a fresh canary or when switching to a new set of fixtures so subsequent session + evolution loops read warm cache instead of live-fetching.

**Goal:** populate the fixture cache for every listed fixture, reasoning about each failure mode individually instead of aborting on the first error. Emit a structured report at the end listing what was primed, what failed, and which class of failure it was.

## Inputs (via `--var`)

| Variable | Example | Purpose |
|---|---|---|
| `pool` | `search-v1` | Pool name, must equal `manifest.suite_id` |
| `manifest_path` | `autoresearch/eval_suites/search-v1.json` | Manifest file (in-repo for search-v1; out-of-repo for holdout-v1) |
| `fixture_ids` | `geo-semrush-pricing,geo-bmw-ix-de` or `all` | Subset filter. `all` iterates every fixture in the manifest. |

## Environment prerequisites

- `FREDDY_API_URL` + `FREDDY_API_KEY` (or freddy CLI auth state)
- For holdout pool: `~/.config/gofreddy/holdouts/.credentials` at chmod 600 when using `--isolation local`
- For any fixture whose source uses env-var resolution (e.g., `AUTORESEARCH_HOLDOUT_MONITORING_*_CONTEXT`): the operator must have exported those env vars before invocation

## Steps (agent reasons; do not hard-branch through this list)

### 1. Enumerate fixtures

Read `$manifest_path` with `jq`. If `fixture_ids=all`, list every fixture across all domains. Otherwise resolve the comma-separated list against the manifest and flag any id that doesn't exist.

### 2. For each fixture, attempt `freddy fixture refresh`

```bash
freddy fixture refresh <fixture_id> \
  --manifest <manifest_path> \
  --pool <pool> \
  --isolation local \
  --force
```

Capture stdout, stderr, exit code. Log a `kind="prime_attempt"` event via one of these methods (agent picks whichever is available):

- Preferred: `python3 -c "from autoresearch.events import log_event; log_event(kind='prime_attempt', fixture_id='...', pool='...', result='...')"`
- Fallback: append JSONL line to `~/.local/share/gofreddy/events.jsonl` directly

### 3. Classify failures + reason about each class

| Failure signature | Reason + action |
|---|---|
| `validation_error` on `freddy-visibility/visibility` containing `keywords: List should have at least 1 item` | Backend rejects empty keywords. Root cause was fixed in sources.json (`fallback_from: "client"`). If this still appears after the fix, verify the fixture's client field is non-empty and retry. If client IS empty, flag for operator (authoring bug). |
| `rate_limited` containing `per 1 minute` | Backend caps at 10/min. Sleep 10s, retry once. If retry also hits rate limit, sleep 60s and retry once more. After 2 retries, continue to next fixture and retry this one at the end. |
| `Client error '404 Not Found'` or `'403 Forbidden'` in `freddy-scrape/page` | URL is dead or scraper-blocked. Do NOT retry — it's a fixture authoring bug. Flag in the final report with the fixture_id + URL + HTTP code. Operator will update the fixture. |
| `Client error '5xx'` or generic `internal_error` with no specific reason | Transient backend issue. Retry twice with 5s backoff. If still failing, flag as "backend transient" and continue. |
| `connection_error` or httpx error | Backend down? Verify `curl $FREDDY_API_URL/docs` returns 200. If not, abort the whole run and report "backend unreachable." |
| `FREDDY_FIXTURE_*` related errors | Stale env vars from prior run. Unset and retry. |
| Missing env var referenced in fixture context (`${AUTORESEARCH_HOLDOUT_MONITORING_*_CONTEXT}` unset) | Operator setup gap. Skip this fixture, flag in final report with the required env var names. |

### 4. Pacing

Keep refresh throughput under 6/min to stay safely under the backend's 10/min limit. Insert `sleep 10` between fixtures when approaching the boundary. Track recent timestamps in memory — don't sleep unnecessarily for fast-succeeding fixtures.

### 5. Final report to stdout

Structured markdown report with these sections:

```markdown
## Prime run — <pool> @ <timestamp>

### Primed successfully: N
- fixture_id (domain, sources fetched)

### Failed — fixable by operator: M
- fixture_id: <class>: <one-line summary + concrete fix suggestion>

### Failed — transient (retry worth trying): K
- fixture_id: <class>: <summary>

### Blocked on env: L
- fixture_id: needs export <ENV_VAR>
```

### 6. Exit codes

- Exit 0: all listed fixtures either primed or flagged as operator-fixable (no runtime errors, no surprises)
- Exit 1: unrecoverable runtime issue (backend unreachable, credentials wrong, manifest malformed)
- Exit 2: one or more fixtures blocked on env vars the operator hasn't exported (re-run after export)

## Agent-side behavior guidance

- **Be conservative about retries.** 3 total attempts per fixture max (initial + 2 retries). Exponential backoff: 5s, 15s.
- **Manifest edits: scoped autonomy.**
  - For `search-v1` pool: after 3 failed attempts with scraper-side `internal_error` (slow-fail or deterministic fail-fast patterns that look like anti-bot / geo-fence), the agent MAY attempt URL recovery. Allowed candidates (in order):
    1. Parent path (e.g., `nubank.com.br/conta-digital/` → `nubank.com.br/conta/`)
    2. Domain root (`https://<domain>/`)
    3. A single well-known sibling on the same registrable domain (`/about`, `/products`, `/pricing`)
    Validation: candidate must return 200 on `curl -sS -o /dev/null -w "%{http_code}"` AND a `freddy fixture refresh` succeeds against the swapped URL on a fresh attempt. Agent must NOT swap to a different registrable domain, must NOT change `client`, must NOT change taxonomy axes. If swap succeeds, write it to the manifest JSON via the Edit tool, log `kind="prime_url_swap"` event with `{fixture_id, old_url, new_url, reason}`. If no candidate validates, mark `failed_authoring` so the operator reconsiders the fixture.
  - For `holdout-v1` pool: NEVER edit the manifest. Holdout URLs are authored deliberately for adversarial value; automated swap destroys benchmark integrity. Flag for operator.
- **Log per-attempt to events.jsonl** so a future operator can reconstruct why a fixture was flagged or swapped.
- **Do NOT invoke judges.** Priming is pure data-fetching; judge calls belong to session / dry-run / canary.
- **Surface backend rate-limit pressure in the final report** — if >20% of attempts hit rate-limit, recommend reducing the concurrent pool or asking backend team to raise the limit.
- **Surface URL swaps in the final report** under a dedicated `url_swaps` section per the Output Contract.

## Output contract (for automation consumers)

Final stdout must include a machine-parseable tail:

```
=== PRIME_REPORT_JSON ===
{
  "pool": "<pool>",
  "timestamp": "<iso8601>",
  "primed": [<fixture_id>, ...],
  "url_swaps": [{"fixture_id": "...", "old_url": "...", "new_url": "...", "reason": "..."}],
  "failed_authoring": [{"fixture_id": "...", "reason": "..."}],
  "failed_transient": [{"fixture_id": "...", "reason": "..."}],
  "blocked_env": [{"fixture_id": "...", "env_var": "..."}]
}
=== /PRIME_REPORT_JSON ===
```

`url_swaps` is omitted when no swaps were applied.

## Why this is an agent task, not a script

A deterministic for-loop (my earlier attempt) fails uniformly on every fixture when the backend rejects one call (visibility validation) — because every fixture has the same broken visibility source. An agent can:

- Distinguish transient from authoring bugs and handle each appropriately
- Pace requests against a rate limit without operator intervention
- Surface a report that maps failures to specific operator actions (not a wall of errors)
- Skip to "what actually worked" quickly when a systemic issue is found — e.g., if all visibility calls fail, flag the systemic issue once rather than for every fixture

The alternative (Python with explicit error handling) replicates agent reasoning in code — and we'd have to update it every time a new failure mode shows up. Agent reasoning scales better for this shape of orchestration.
