# QA Eval-Fix Harness (GoFreddy)

An automated loop that evaluates GoFreddy capabilities (CLI commands, API endpoints, frontend pages) against `harness/test-matrix.md`, grades them, and hands failures to a fixer agent that edits code until convergence or `MAX_CYCLES`.

Entry point: `python -m harness`

## Prerequisites

- Docker Desktop running (for local Supabase containers)
- `supabase` CLI installed
- `uv` installed and the project venv hydrated: `uv sync`
- `node` + `npm` installed
- `playwright-cli` installed
- Either `claude` or `codex` on `PATH` and authenticated
- A `.env` file at the repo root with required env vars (see `harness/config.py`)

## Quick Start

```bash
# 1. Start Supabase
supabase start

# 2. Apply migrations
for f in supabase/migrations/*.sql; do
  psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f "$f"
done

# 3. Seed local data
python scripts/seed_local.py

# 4. Start backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 &

# 5. Start frontend
cd frontend && npm run dev &

# 6. Run harness
python -m harness --engine codex --cycles 2
```

## Configuration

All config is in `harness/config.py`. Key knobs:

| Env Var | Default | Description |
|---------|---------|-------------|
| `HARNESS_ENGINE` | `codex` | Engine: `claude` or `codex` |
| `MAX_CYCLES` | `5` | Max evaluation-fix cycles |
| `FRONTEND_URL` | `http://localhost:3001` | Frontend URL (Vite dev server) |
| `BACKEND_URL` | `http://localhost:8080` | Backend URL |
| `FIXER_WORKERS` | `1` | Parallel fixer workers per domain |

## Three Domains

| Domain | Track | Observation Method |
|--------|-------|-------------------|
| A (CLI) | a | Run `freddy` commands, check exit code + JSON output |
| B (API) | b | `curl` endpoints with Bearer token, check HTTP status + response |
| C (Frontend) | c | `playwright-cli` page snapshot, check element presence |

## Safety

- Refuses to run against production or non-localhost databases
- Protected files (`harness/`, `tests/harness/`, `scripts/`) are backed up before each fixer cycle and restored after
- Main repo leak guard detects files edited outside the staging worktree and reverts them
