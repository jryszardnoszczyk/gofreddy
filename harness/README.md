# QA Eval-Fix Harness

An automated loop that drives the frontend with an LLM evaluator agent, grades capabilities against `harness/test-matrix.md`, and hands failures to a fixer agent that edits `src/` until convergence or `MAX_CYCLES`.

Entry point: `scripts/eval_fix_harness.sh`.

This README documents the **pre-boot dance** — the manual steps you run once before invoking the harness. The harness itself does NOT boot the backend/frontend or mint auth tokens; it expects a healthy, running, authenticated stack. Get all of this right before you run the script.

## Prerequisites

- Docker Desktop running (for local Supabase containers)
- `supabase` CLI installed (`brew install supabase/tap/supabase`)
- `psql` installed (PostgreSQL 17+ client; any recent version works)
- `uv` installed and the project venv hydrated: `uv sync`
- `node` + `npm` installed
- `playwright-cli` installed: `brew install playwright-cli` or `npm install -g @playwright/cli@latest`
- Either `claude` (for `HARNESS_ENGINE=claude`, the default) or `codex` (for `HARNESS_ENGINE=codex`) on `PATH` and authenticated
- For codex: profiles named `harness-evaluator` and `harness-fixer` registered in `~/.codex/config.toml` (see the bottom of this doc)
- A `.env` file at the repo root with all the keys in `HARNESS_REQUIRED_ENV_VARS` (see `harness/config.sh`)

## The pre-boot dance

Run these **in order**. Every step has to succeed before moving to the next. If any step fails, the harness will either refuse to start or (worse) run against a broken stack and produce misleading findings.

```bash
# Paths used below
REPO=/Users/jryszardnoszczyk/Documents/GitHub/freddy
cd "$REPO"

# 1. Docker must be running.
open -a Docker
# Wait a few seconds, then:
docker info >/dev/null || { echo "Docker not ready"; exit 1; }

# 2. Start local Supabase (Postgres on 54522, Auth on 54521).
supabase start
# Capture the output; you'll need the `Publishable` key later if you want
# to mirror it into VITE_SUPABASE_ANON_KEY for the frontend.

# 3. Apply the test schema. This creates ~46 tables AND the functional
# unique index the seed script needs.
psql "postgresql://postgres:postgres@127.0.0.1:54522/postgres" \
    -f "$REPO/scripts/setup_test_db.sql"

# 4. Hydrate the Python venv if not already.
uv sync

# 5. Load .env into your shell AND set the local-Supabase overrides.
set -a
source ./.env
set +a
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54522/postgres"
export SUPABASE_URL="http://127.0.0.1:54521"
export ENVIRONMENT="development"
export EXTERNALS_MODE="real"     # or "fake" — see notes below
export TASK_CLIENT_MODE="mock"
export CORS_ALLOWED_ORIGINS="http://localhost:3010,http://127.0.0.1:3010"

# 6. Boot the backend on port 8090 (kept off 8080 to avoid colliding
# with any existing dev server). Run in a background shell / tmux pane.
"$REPO/.venv/bin/uvicorn" src.api.main:create_app \
    --factory --host 127.0.0.1 --port 8090 \
    > /tmp/freddy-harness-backend.log 2>&1 &

# Wait for it to come up.
until curl -fsS http://127.0.0.1:8090/health >/dev/null; do sleep 1; done
echo "backend ready"

# 7. Mint the harness JWT by running the seed script. The harness does
# this itself when it starts, but you need it NOW to pass as a vite env
# var (step 8). Save it for reuse.
HARNESS_TOKEN=$("$REPO/.venv/bin/python" "$REPO/scripts/e2e_seed_auth_tokens.py" \
    --db-url "$DATABASE_URL" \
    --supabase-url "$SUPABASE_URL" \
    --jwt-secret "$SUPABASE_JWT_SECRET" \
    --harness | "$REPO/.venv/bin/python" -c "import sys,json; print(json.load(sys.stdin)['harness_token'])")
echo "$HARNESS_TOKEN" > /tmp/freddy-harness-jwt.txt
[ -n "$HARNESS_TOKEN" ] || { echo "seed failed"; exit 1; }

# 8. Boot the frontend with the JWT injected. This is the critical env
# var that makes the e2e auth bypass actually work — without it, the
# frontend falls back to the literal "e2e-bypass-token" string and the
# backend (correctly) rejects every request with 401.
cd "$REPO/frontend"
# If node_modules is missing, install first: npm install
VITE_E2E_BYPASS_AUTH=1 \
VITE_E2E_BYPASS_ACCESS_TOKEN="$HARNESS_TOKEN" \
VITE_E2E_BYPASS_USER_ID="harness_qa_pro_user" \
VITE_E2E_BYPASS_EMAIL="harness@test.local" \
VITE_API_URL="http://127.0.0.1:8090" \
VITE_SUPABASE_URL="http://127.0.0.1:54521" \
VITE_SUPABASE_ANON_KEY="<paste sb_publishable_... from supabase start output>" \
npm run dev -- --host 127.0.0.1 --port 3010 --strictPort \
    > /tmp/freddy-harness-frontend.log 2>&1 &
cd "$REPO"
until curl -fsS -o /dev/null http://127.0.0.1:3010/; do sleep 1; done
echo "frontend ready"

# 9. Sanity check: hit a protected endpoint with the harness JWT.
# HTTP 200 means the auth bypass is fully wired; anything else means
# stop and fix before running the harness.
curl -fsS -H "Authorization: Bearer $HARNESS_TOKEN" \
    http://127.0.0.1:8090/v1/usage | head -c 200; echo

# 10. Run the harness. Defaults are PHASE=all, HARNESS_SKIP=empty,
# HARNESS_ENGINE=claude, DRY_RUN=false.
export BACKEND_PORT=8090
export BACKEND_URL="http://localhost:8090"
export FRONTEND_URL="http://localhost:3010"
export BACKEND_CMD="$REPO/.venv/bin/uvicorn src.api.main:create_app --factory --host 0.0.0.0 --port 8090"

# First run — smoke. Just validate the loop wires up.
PHASE=1 DRY_RUN=true ./scripts/eval_fix_harness.sh

# Phase 1 pilot (real mode, no dry run) — costs real API $.
PHASE=1 HARNESS_SKIP=A4 ./scripts/eval_fix_harness.sh

# Full matrix — plan for 4-8 hours and $50-200 in API costs.
PHASE=all HARNESS_SKIP=A4 HARNESS_MAX_WALLTIME=18000 ./scripts/eval_fix_harness.sh
```

## Config knobs

All declared in `harness/config.sh`. Override by exporting before the harness runs.

| Var | Default | What |
|---|---|---|
| `HARNESS_ENGINE` | `claude` | `claude` or `codex` |
| `PHASE` | `all` | `all`, `1`, `2`, `3` — filters capabilities via the YAML phases block at the top of `test-matrix.md` |
| `HARNESS_SKIP` | empty | Comma-separated capability IDs to skip (e.g. `A4,B14`) |
| `HARNESS_MAX_WALLTIME` | `14400` (4h) | Hard wall-time cap in seconds |
| `DRY_RUN` | `false` | `true` = Track A only, capability A1 only. For smoke-testing the loop. |
| `MAX_CYCLES` | `5` | Max eval/fix cycles before bailing |
| `BACKEND_PORT` | `8080` | Port the harness checks/restarts. Override to `8090` if your dev stack owns 8080. |
| `BACKEND_URL` | `http://localhost:8080` | Must match `BACKEND_PORT` |
| `FRONTEND_URL` | `http://localhost:3000` | Must match the vite port you booted in step 8 |
| `BACKEND_CMD` | inline | Command the harness uses to restart the backend after fixer changes. Set to the venv uvicorn path for reliability. |
| `HARNESS_REQUIRED_ENV_VARS` | (array) | Env vars the preflight check requires. Edit in `config.sh` to narrow scope. |
| `HARNESS_VENV_PYTHON` | `$REPO_ROOT/.venv/bin/python` | Python interpreter used for seeding. Override to point at the main checkout's venv when running from a git worktree that has no `.venv` of its own (see Troubleshooting → worktree). |
| `MAX_FIX_ATTEMPTS` | `2` | Max cycles a given finding ID may be attempted by the fixer before the harness auto-escalates it. Escalated findings are excluded from convergence and the fixer is told to skip them. |

## Safety guards

The harness refuses to run in these conditions (hard fail before any other work):

- `ENVIRONMENT=production`
- `DATABASE_URL` / `E2E_DB_URL` pointing anywhere other than `localhost` / `127.0.0.1` / `::1`
- `STRIPE_SECRET_KEY` starting with `sk_live_`

If any trip, fix the environment before retrying.

## Frozen judge + evolvable orchestration

The harness is the judge; the fixer is the worker. A worker cannot grade its own exam by editing the rubric. Four paths are strictly off-limits to the fixer:

- `harness/` (all contents, including prompts, config, and test matrix)
- `scripts/eval_fix_harness.sh`
- `scripts/setup_test_db.sql`
- `tests/harness/`

Two enforcement layers back this up:

1. **Prompt rule** — `harness/prompts/fixer.md` has a "Hard Rules — Frozen Judge Files" section at the top telling the fixer not to touch those paths, and a `harness_issues_identified:` YAML field in its output template for flagging genuine harness bugs it noticed while fixing product code.

2. **Machine-side safety net** — `scripts/eval_fix_harness.sh` copies every protected file to a sidecar directory (`harness/runs/<ts>/.harness-backup-<cycle>/`) before each fixer invocation. After the fixer returns, it byte-for-byte compares the live tree against the backup: modifications are overwritten from the backup, new files are removed, deletions are restored. The sidecar captures the pre-fixer *working-tree* state, not the committed HEAD state — so legitimate uncommitted work on harness files is preserved while fixer tampering gets reverted. Violations are logged loudly to stderr and appended to `fixer-<cycle>.log`. This holds even if a future model decides to "help" by editing the harness.

The safety net runs per cycle, so if a fixer edits `harness/prompts/fixer.md` in cycle 2, the damage is reverted before cycle 3 runs. (Bash function definitions are cached at source time, so mid-run edits don't even affect the current cycle's behavior — they only matter for subsequent cycles, which is exactly when the safety net catches them.)

## Reviewing fixer output

After each run, inspect `harness/runs/<ts>/fixes-<cycle>.md` for two sections the fixer may have populated:

- `findings_escalated:` — finding IDs the fixer attempted 2 cycles in a row without resolving. These are waiting for a human to investigate; the harness will ignore them in subsequent cycles of the same run (they're also in the `.escalated-<cycle>.txt` sidecar the harness owns). A common pattern: the symptom persists because the root cause is deeper than the fixer's pattern-matching can reach.

- `harness_issues_identified:` — YAML list of `{file, finding, issue, suggested_change, severity}` entries. The fixer populates this when it notices an actual bug in a harness file (e.g., the evaluator prompt is ambiguous, a capability is framed in an unimplementable way). The fixer cannot edit those files — you must review and apply the suggestions yourself out-of-band.

Check `fixer-<cycle>.log` for `"FROZEN JUDGE VIOLATION"` — that means the fixer tried to edit a protected file despite the prompt rule. The safety net will have reverted the edit, but the attempt is a signal worth investigating (prompt drift, a finding the fixer felt it couldn't fix any other way, etc.).

## Convergence and escalation

The convergence check (used to decide "no more progress — stop iterating") compares the set of `{finding_id}:{grade}` pairs across two consecutive cycles. Two filters apply to the comparison set:

- **Flow 4 exclusion** — capabilities in "Flow 4 (Dynamic — excluded from convergence)" sections of `harness/test-matrix.md` use dynamic prompts that are inherently non-deterministic. The harness parses those sections at runtime and excludes their capability IDs from convergence. To change the Flow 4 set, edit the markdown header — no bash changes needed.

- **Escalation exclusion** — finding IDs in the current cycle's `.escalated-<cycle>.txt` sidecar are excluded too, because they are "stable by definition" (the harness won't try to fix them again in the same run).

This means a phased run (e.g., `PHASE=1`) will compare the full Phase 1 set minus Flow 4 minus escalated — not just the A1/B1/C1 reference flows the old hardcoded rule used. A Phase 1 capability flipping PARTIAL → PASS across cycles will correctly NOT trip early convergence.

The `MAX_FIX_ATTEMPTS` knob (default 2) controls how many cycles a finding ID may be attempted before the harness auto-escalates it. The attempt counter reads prior cycles' `fixes-<N>.md` `findings_addressed:` fields. The fixer prompt for cycle ≥ 2 includes a "Finding attempt tracker" block listing every previously-attempted ID with its cycle history and explicit ESCALATE markers for any at the limit.

## Codex profiles

If you want to run with `HARNESS_ENGINE=codex`, add this to `~/.codex/config.toml`:

```toml
[profiles.harness-evaluator]
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
approval_policy = "never"
sandbox_mode = "danger-full-access"
shell_environment_policy.inherit = "all"

[profiles.harness-fixer]
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
approval_policy = "never"
sandbox_mode = "danger-full-access"
shell_environment_policy.inherit = "all"
```

`approval_policy = "never"` is mandatory for headless runs. `sandbox_mode = "danger-full-access"` is required because `playwright-cli` launches Chrome and binds sockets; `workspace-write` is too restrictive. The worktree is your sandbox — keep the harness running inside a separate git worktree if you want fixer commits quarantined from main.

If codex hits "Your refresh token has been invalidated" mid-run, stop and re-authenticate with `codex login`. There's no in-harness recovery for a dead auth.

## Troubleshooting

Symptoms from today's first-ever runs — if you see them, here's the fix:

- **"Harness Pro user seeded. Token: ..." with an empty token** — never happens anymore (the harness now halts on seed failure). If you see a seed failure, check that the venv python at `$HARNESS_VENV_PYTHON` (default `$REPO/.venv/bin/python`) exists and is executable (`uv sync`), that Supabase Postgres is reachable, and that the functional index `users_email_lower_idx` is present (re-apply `scripts/setup_test_db.sql`).
- **"Venv python not found at ..." when running from a git worktree** — worktrees don't inherit the parent checkout's `.venv`. Either symlink it in (`ln -s /path/to/main/freddy/.venv .venv`) or, preferably, set `HARNESS_VENV_PYTHON` to the main checkout's interpreter: `export HARNESS_VENV_PYTHON=/path/to/main/freddy/.venv/bin/python`. The env var approach keeps the worktree clean and doesn't mask a missing venv in the main checkout.
- **Supabase CLI: "failed to parse environment file .env"** — you have a bare key with no `=value` in `.env`. Find it (`grep -n '^[A-Z_]*$' .env`) and add `=` or a value.
- **Vite: "vite: command not found"** — `frontend/node_modules` isn't installed. `cd frontend && npm install`.
- **Backend boots but frontend 401s everywhere** — `VITE_E2E_BYPASS_ACCESS_TOKEN` wasn't set when vite started. You must restart vite with the token in its env; vite env vars are baked at startup.
- **CORS "blocked by CORS policy" for port 3010** — the default `_DEFAULT_CORS_ALLOWED_ORIGINS` in `src/api/main.py` now includes 3010, but if you're running an older backend you may need to set `CORS_ALLOWED_ORIGINS` explicitly in the backend's environment.
- **Codex: "unexpected argument '--profile'" on cycle 2+** — fixed (harness no longer passes `--profile` to `codex exec resume`). If you still see this, you're running an older version of the harness script.

## Artifacts

Each run writes to `harness/runs/<YYYYMMDD-HHMMSS>/`:

- `scorecard-<cycle>-track-<a|b|c>.md` — per-track scorecard with findings
- `scorecard-<cycle>-merged.md` — merged scorecard for the cycle
- `fixes-<cycle>.md` — fixer's report of what it changed (or why it skipped, escalated, or flagged a harness issue)
- `eval-<cycle>-track-<a|b|c>.log` — raw LLM output (huge — full reasoning trace)
- `fixer-<cycle>.log` — fixer's raw LLM output (includes `FROZEN JUDGE VIOLATION` warnings appended by the safety net)
- `summary.md` — top-level summary (cycles, exit reason, final scorecard, artifact list)
- `.session-eval-<track>` — session IDs for resume across cycles
- `.backend-tree-{before,after}-<cycle>.tsv` — source-tree SHA snapshots used for change detection (backend restart trigger)
- `.harness-backup-<cycle>/` — frozen-judge safety net sidecar (full byte-for-byte copy of every protected file before the fixer ran; used to byte-compare and restore after)
- `.harness-snapshot-<cycle>.tsv` — SHA manifest of the backup dir, for quick-diff triage
- `.escalated-<cycle>.txt` — finding IDs escalated as of this cycle (sticky, one per line). Machine-side truth read by convergence and the fixer prompt's attempt tracker.

On a failure, the scorecard now includes `evaluator_failure_category` (one of `TIMEOUT`, `HARNESS_BUG`, `TRANSIENT`, `RESUME_FAIL`, `API_ERROR`, `AGENT_ERROR`, `TRACK_FAILED`), `evaluator_exit_code`, and the last 5 lines of the eval log so you can triage at a glance.
