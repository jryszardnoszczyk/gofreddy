# QA Harness — preservation-first, free-roaming agents

The harness exercises the live GoFreddy stack through three parallel codex agents (CLI, API, Frontend), lets each one discover defects on its own, fixes the high-confidence ones, verifies the fixes, and opens a PR per run.

Everything lives in `harness/`; runtime artefacts go to `harness/runs/<timestamp>/` (gitignored). This document covers bootstrap, running, reading output, and troubleshooting.

## What the harness does

For each run:

1. **Preflight** — env vars present, not in production, local DB, codex profiles sane, CLI console script works, `gh auth status` OK, Supabase schema applied, harness JWT minted with enough TTL, backend + frontend healthy
2. **Staging worktree** — `git worktree add` on `harness/run-<ts>`, symlink `.venv` and `node_modules`, `mkdir clients/`, `chmod 0700`, start a dedicated uvicorn
3. **Inventory** — auto-generate a markdown listing of CLI commands, API routes, frontend routes, autoresearch entry points (read via subprocess; no pollution of the orchestrator env)
4. **Smoke** — 5 deterministic must-work flows. Any failure = hard abort
5. **Cycle loop** — three evaluator codex agents run in parallel (one per track). High-confidence defects (`crash`, `5xx`, `console-error`, `self-inconsistency`, `dead-reference`) go through a **fixer → verifier → safety-check → commit-or-rollback** pipeline, serial per track. Lower-confidence findings + `doc-drift` are routed to `review.md`
6. **Tip smoke** — smoke runs once more against the staging branch tip (with each landed finding's reproduction appended as an extra check)
7. **PR** — push staging branch, `gh pr create` against main

Four termination paths: every evaluator writes `done reason=...` to its sentinel file; two consecutive cycles with zero new high-confidence defects AND zero commits → `no-progress`; wallclock exceeds `max_walltime` → `walltime`; cycle 1 finds nothing across all three tracks → `zero-first-cycle`.

## Bootstrap

One-time setup on a fresh machine:

```bash
# 1. Python dependencies + editable install (rebuilds .venv/bin/freddy)
uv sync
uv pip install -e .

# 2. Frontend deps
(cd frontend && npm ci)

# 3. Local Supabase stack
supabase start

# 4. .env — copy .env.example, fill in GEMINI_API_KEY and Supabase locals
cp .env.example .env
# edit .env

# 5. GitHub CLI auth
gh auth login

# 6. Codex CLI profiles — ensure ~/.codex/config.toml has all three:
#    [profiles.harness-evaluator|harness-fixer|harness-verifier]
#    approval_policy      = "never"
#    sandbox_mode         = "danger-full-access"
#    shell_environment_policy.inherit = "all"
#    model                = "gpt-5.4"
#    model_reasoning_effort = "xhigh"
```

**Remove stale shims** if you inherited them:

```bash
rm -f /opt/homebrew/bin/freddy /opt/homebrew/bin/uvicorn
```

## Running

```bash
.venv/bin/python -m harness                       # full run with defaults
.venv/bin/python -m harness --max-walltime 3600   # 1-hour cap
.venv/bin/python -m harness --keep-worktree       # leave the staging worktree for debugging
.venv/bin/python -m harness --backend-port 8100   # alternate port (avoid collisions)
```

Flags:

| Flag | Default | Purpose |
|---|---|---|
| `--max-walltime` | 14400 (4h) | Hard wallclock cap |
| `--keep-worktree` | False | Skip worktree cleanup on exit |
| `--backend-port` | 8000 | Port uvicorn binds inside the worktree |
| `--staging-root` | `harness/runs` | Where per-run dirs are created |

A run prints a 7-line summary to stderr at the end:

```
commits: 3
findings: 14 (5xx=2, crash=1, doc-drift=6, low-confidence=5)
tip-smoke: OK
pr: https://github.com/you/gofreddy/pull/123
exit_reason: agent-signaled-done
duration: 4213s
run_dir: /path/to/harness/runs/run-20260421-103000
```

## Reading output

Inside `harness/runs/run-<ts>/`:

- `harness.log` — orchestrator log (mirrors stderr)
- `inventory.md` — auto-generated surface listing passed to evaluators
- `track-<a|b|c>/cycle-<n>/findings.md` — YAML-front-matter findings
- `track-<a|b|c>/cycle-<n>/sentinel.txt` — agent termination signal
- `fixes/<finding-id>/codex.log` — fixer agent output
- `verifies/<finding-id>/codex.log` — verifier agent output
- `verdict-<finding-id>.yaml` — verifier verdict (verified / failed / reproduction-broken)
- `fix-diffs/F-<finding-id>.patch` — rolled-back patches preserved for review
- `review.md` — everything not PR-worthy (doc-drift, low-confidence, rollbacks)
- `pr-body.md` — the body of the opened PR

Findings vs commits: high-confidence findings in the five-defect enum flow to the fixer; everything else is written to `review.md`. A commit lands only when the verifier passes AND the safety checks (per-track scope allowlist, no main-repo leak) pass.

## Troubleshooting

| Symptom | Likely cause & fix |
|---|---|
| `preflight: .venv/bin/freddy --help exited 1` | Stale editable install. `uv pip install -e .` |
| `preflight: gh auth status failed` | `gh auth login` |
| `preflight: missing env vars: ...` | Populate `.env`; re-run |
| `preflight: minted JWT TTL (Xs) < max_walltime+padding` | Raise GoTrue `JWT_EXP` in `supabase/config.toml` or lower `--max-walltime` |
| `smoke broken: smoke-api-key — status=401` | JWT secret mismatch — re-run `supabase start`, confirm `SUPABASE_JWT_SECRET` in `.env` matches |
| `backend failed to become healthy` within 40s | Check `harness/runs/*/backend.log` for the actual stack trace |
| Old `/opt/homebrew/bin/freddy` intercepts | `rm -f /opt/homebrew/bin/freddy` |
| Leak violation on every finding | Fixer is writing outside the worktree — inspect `fix-diffs/F-*.patch` |

## What the harness does NOT do

- Auto-merge PRs
- Modify tests or anything under `harness/`
- Change public surfaces (endpoint paths, response shapes, CLI flags) to conform to docs — `doc-drift` is routed to the human reviewer
- Run without a human-reviewable PR at the end
