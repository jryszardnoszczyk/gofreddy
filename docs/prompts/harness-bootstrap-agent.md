# GoFreddy Harness Bootstrap & Smoke Run

You are bootstrapping and running the QA eval-fix harness in the GoFreddy repo. Your goal: get the local stack healthy, then run the harness in dry-run mode to verify the full eval-fix-verify loop works end-to-end.

## What GoFreddy is

CLI-first agency tool. Backend is `uvicorn src.api.main:app` on port 8080. Frontend is Vite on port 3001. Auth is Supabase (Postgres on 54322, GoTrue on 54321). No chat, no SSE streaming, no canvas — just CLI commands, REST API endpoints, and 4 frontend pages.

## What the harness does

Autonomous QA loop: evaluator agents test capabilities → scorecard → fixer agents debug failures → verifier agents confirm with paraphrased inputs → commit or rollback. Three domains: A (CLI), B (API), C (Frontend). In dry-run mode it tests just one capability (A-1: `freddy client list`) through one cycle.

## Step 1: Verify Supabase is running

```bash
supabase status
```

If not running: `supabase start`. Wait until all services report healthy. You need:
- Postgres on `127.0.0.1:54322`
- Auth (GoTrue) on `127.0.0.1:54321`

If `supabase` CLI is not found, stop and tell the operator.

## Step 2: Verify .env

The harness needs these 5 env vars. Source the .env and check each:

```bash
set -a; source .env; set +a
```

Required (preflight will abort if missing):
- `DATABASE_URL` — must point to localhost:54322
- `SUPABASE_URL` — must point to localhost:54321 (the Auth/GoTrue API, NOT the Postgres port)
- `SUPABASE_JWT_SECRET` — the JWT signing secret from Supabase
- `SUPABASE_ANON_KEY` — the publishable anon key from Supabase
- `GOOGLE_API_KEY` — needed for evaluation/GEO endpoints

**For dry-run**: only A-1 (`freddy client list`) runs. It does NOT need GOOGLE_API_KEY. If that key is missing, set a dummy: `export GOOGLE_API_KEY=dry-run-not-used`. But the preflight env check runs before the dry-run filter, so the var must exist (even if dummy). Do NOT set dummy values for the other 4 — those are used by the harness itself for JWT minting and DB access.

If any of the first 4 are missing from .env, check `supabase status` output — it prints the connection strings and keys.

## Step 3: Apply database migrations

```bash
set -a; source .env; set +a
for f in supabase/migrations/*.sql; do
  psql "$DATABASE_URL" -f "$f" && echo "OK: $f" || echo "FAIL: $f"
done
```

All 3 must succeed. They're idempotent (`CREATE TABLE IF NOT EXISTS`), so re-running is safe.

## Step 4: Start the backend

```bash
kill -9 $(lsof -ti:8080) 2>/dev/null  # clear port
set -a; source .env; set +a
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8080 >/tmp/gofreddy-backend.log 2>&1 &
sleep 3
curl -s http://localhost:8080/health
```

Must return a 2xx JSON response. If it fails, check `/tmp/gofreddy-backend.log` for import errors or missing dependencies (`pip install -e .` or `uv sync` if needed).

**There is no `/ready` endpoint.** Only `/health`.

## Step 5: Start the frontend

```bash
kill -9 $(lsof -ti:3001) 2>/dev/null  # clear port
cd frontend && npm install && cd ..

# For the harness to work, Vite needs E2E bypass env vars.
# The harness's refresh_vite_jwt handles this during preflight,
# but for manual boot we need a running vite first.
cd frontend
VITE_SUPABASE_URL="$SUPABASE_URL" \
VITE_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
VITE_E2E_BYPASS_AUTH=1 \
VITE_E2E_BYPASS_ACCESS_TOKEN=placeholder \
VITE_E2E_BYPASS_USER_ID=placeholder \
VITE_E2E_BYPASS_EMAIL=harness@local.gofreddy.ai \
nohup npm run dev >/tmp/gofreddy-vite.log 2>&1 &
cd ..
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001
```

Must return 200. The harness's preflight will kill and restart Vite with a real JWT, so the placeholder values above are just to get it booted.

## Step 6: Verify codex profiles

The harness uses codex as the default engine. It needs profiles in `~/.codex/config.toml`:

```bash
grep -c "harness-evaluator\|harness-fixer\|harness-verifier" ~/.codex/config.toml
```

Must find at least `harness-evaluator` and `harness-fixer`. If missing, you need to create them. The profiles need:
- `sandbox_mode = "danger-full-access"` (fixer needs to edit files and run arbitrary commands)
- `shell_environment_policy.inherit = "all"` (pass through env vars)

If `harness-verifier` is missing, add it with the same settings as `harness-evaluator`.

If you're using `claude` engine instead of `codex`, skip this step and pass `--engine claude`.

## Step 7: Run the harness (dry-run smoke test)

```bash
set -a; source .env; set +a
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-dry-run-not-used}"
python3.13 -m harness --dry-run --engine codex --cycles 1
```

**What should happen:**
1. Preflight passes: engine check, safety guards, env vars, DB schema, health check, CORS, JWT minting, frontend bypass, state cleanup
2. Staging worktree created at `/tmp/harness-run-<timestamp>/`
3. Evaluator dispatched for Track A, capability A-1 only
4. Evaluator runs `freddy client list`, grades PASS or FAIL
5. If FAIL: fixer dispatched, fixes code, verifier confirms
6. Summary written to `harness/runs/<timestamp>/summary.md`
7. Exit with "DRY RUN PASS" or cycle exhaustion

**What to watch for:**
- Preflight failure on JWT minting → Supabase Auth not reachable or SUPABASE_ANON_KEY wrong
- Preflight failure on health check → backend not running or wrong port
- Preflight failure on frontend bypass → Vite not running or wrong port
- Evaluator produces empty scorecard → check `harness/runs/<ts>/eval-1-track-a.log`
- "all evaluators failed" → rate limit or codex profile misconfigured

## Step 8: Check results

```bash
ls harness/runs/
# Find the latest run directory
cat harness/runs/$(ls -t harness/runs/ | head -1)/summary.md
```

Report what happened: did preflight pass? Did the evaluator produce a scorecard? What was the exit reason?

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Missing env vars: GOOGLE_API_KEY` | Not in .env | `export GOOGLE_API_KEY=dry-run-not-used` |
| `JWT minting: signup request failed` | Supabase Auth not running | `supabase start` |
| `Timeout waiting for http://localhost:8080/health` | Backend not running | Check `/tmp/gofreddy-backend.log` |
| `No vite on http://localhost:3001` | Frontend not running | Check `/tmp/gofreddy-vite.log` |
| `Missing Codex profile [harness-evaluator]` | Profile not in config.toml | Add `[profiles.harness-evaluator]` section |
| `codex CLI not found in PATH` | Codex not installed | Use `--engine claude` instead |
| Backend starts but `freddy` CLI not found | .venv not activated or CLI not installed | `uv sync` then verify `which freddy` |
