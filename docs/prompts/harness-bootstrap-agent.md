# GoFreddy Harness Bootstrap Agent

You are bootstrapping the GoFreddy QA harness on a fresh machine or worktree. Get the local stack to a state where `python -m harness --max-walltime 900` runs a real short cycle end-to-end.

## What GoFreddy is

CLI-first agency tool. Backend is `uvicorn src.api.main:app` on port 8000. Frontend is Vite on port 5173. Auth is Supabase local (Postgres 54322, GoTrue 54321). No SSE chat, no canvas — CLI groups, REST endpoints, a handful of frontend routes.

## What the harness does (in one paragraph)

Three codex agents (`harness-evaluator` / `harness-fixer` / `harness-verifier`) run against a staging git worktree with an isolated backend. Evaluators discover defects (five categories: crash, 5xx, console-error, self-inconsistency, dead-reference). High-confidence findings get fixed by the fixer, checked by the verifier (reproduction gate + adjacent regression + public surface guard), passed through scope + leak checks, and committed on a per-run staging branch. One PR per run. Runtime artefacts go to `harness/runs/<ts>/` (gitignored).

## Bootstrap steps

### 1. Supabase

```bash
supabase status || supabase start
```

Confirm Postgres 54322 and GoTrue 54321 are up. The harness mints a JWT against GoTrue and seeds `users`, `clients`, `user_client_memberships` rows at preflight.

### 2. Env vars

```bash
cp .env.example .env   # if missing
```

Required (the harness fails fast if any are empty):

- `DATABASE_URL` — must be local (refused if it points at `supabase.co`, `amazonaws.com`, etc.)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
- `GEMINI_API_KEY` — the app reads this (NOT `GOOGLE_API_KEY`)

### 3. Python deps + editable install

```bash
uv sync
uv pip install -e .
.venv/bin/freddy --help   # must exit 0; otherwise stale console script
```

### 4. Frontend deps

```bash
(cd frontend && npm ci)
```

### 5. GitHub CLI

```bash
gh auth status || gh auth login
```

The harness opens a PR via `gh pr create`; preflight refuses to run if gh is unauthenticated.

### 6. Codex profiles

Three profiles must exist in `~/.codex/config.toml`:

```toml
[profiles.harness-evaluator]
model                            = "gpt-5.4"
model_reasoning_effort           = "xhigh"
approval_policy                  = "never"
sandbox_mode                     = "danger-full-access"
shell_environment_policy.inherit = "all"

[profiles.harness-fixer]
# identical

[profiles.harness-verifier]
# identical
```

Preflight parses this file and refuses to run if `inherit != "all"` — PATH prepend survival into the codex subprocess depends on it.

### 7. Stale shims

```bash
rm -f /opt/homebrew/bin/freddy /opt/homebrew/bin/uvicorn
```

### 8. Dry-smoke the bootstrap

Don't run the full harness yet. Instead:

```bash
.venv/bin/python -c "from harness import run; print('imports OK')"
.venv/bin/python -m harness --help
```

Both must succeed.

## Running the real thing

First start backend + frontend (preflight polls both before anything else):

```bash
# shell 1: backend
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
# shell 2: frontend
(cd frontend && npm run dev -- --host 127.0.0.1 --port 5173)
```

Then run the harness:

```bash
.venv/bin/python -m harness --max-walltime 900
```

900 seconds (15 min) is enough for one honest cycle plus a PR-create attempt. For a full production run use the default 4h.

Read the final 7-line stderr summary. If `pr:` is a URL, the run landed commits. If it's `no PR — zero verified fixes`, the run completed with no actionable defects — not a failure. Anything else in the pr field means `git push` or `gh pr create` failed; follow the recovery command in `harness.log`.

## What to DO NOT do

- Do not edit `harness/` or `tests/harness/` during a run — the fixer's scope allowlist already excludes them
- Do not set `--keep-worktree` routinely; it accumulates dead worktrees under `harness/runs/`
- Do not trust a green run on first try — tip-smoke failure can still surface after commits land

## Troubleshooting quick index

| Symptom | Fix |
|---|---|
| `PreflightError: missing env vars` | Fill `.env`, re-run |
| `PreflightError: .venv/bin/freddy ...` | `uv pip install -e .` |
| `PreflightError: gh auth status failed` | `gh auth login` |
| `smoke broken: smoke-api-key` | JWT secret drift; `supabase start` + re-check `.env` |
| Leak violation every cycle | Fixer writing outside worktree — inspect `fix-diffs/` patches |
