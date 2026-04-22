# QA Harness — preservation-first, free-roaming agents

The harness exercises the live GoFreddy stack through three parallel agents (CLI, API, Frontend), lets each one discover defects on its own, fixes the high-confidence ones, verifies the fixes, and opens a PR per run. Both Claude Code (default) and Codex are supported — `--engine claude|codex`.

Everything lives in `harness/`; runtime artefacts go to `harness/runs/<timestamp>/` (gitignored). This document covers bootstrap, running, reading output, and troubleshooting.

## What the harness does

For each run:

1. **Preflight** — env vars present, not in production, local DB, codex profiles sane, CLI console script works, `gh auth status` OK, Supabase schema applied, harness JWT minted with enough TTL, backend + frontend healthy
2. **Staging worktree** — `git worktree add` on `harness/run-<ts>`, symlink `.venv` and `node_modules`, `mkdir clients/`, `chmod 0700`, start a dedicated uvicorn
3. **Inventory** — auto-generate a markdown listing of CLI commands, API routes, frontend routes, autoresearch entry points (read via subprocess; no pollution of the orchestrator env)
4. **Smoke** — 5 deterministic must-work flows. Any failure = hard abort
5. **Cycle loop** — three evaluator agents run in parallel (one per track). High-confidence defects (`crash`, `5xx`, `console-error`, `self-inconsistency`, `dead-reference`) go through a **fixer → verifier → safety-check → commit-or-rollback** pipeline — serial within a track, parallel across tracks on a single shared worktree. Lower-confidence findings + `doc-drift` are routed to `review.md`
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

**Prerequisite:** both backend and frontend must be running before you invoke the harness — preflight polls `/health` and `/` for 30s each before starting. The harness takes over the backend inside its own git worktree (kills whatever listens on `--backend-port`, spawns its own uvicorn); the frontend keeps serving from your main repo.

**`gh` token lifetime:** `gh auth status` only checks the token exists, not when it expires. For runs close to `--max-walltime`, refresh with `gh auth refresh` before starting — otherwise `gh pr create` may fail 401 at run end and strand commits on the remote staging branch (the error message tells you exactly how to recover manually).

```bash
# In two separate shells, before running the harness:
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000   # shell 1
(cd frontend && npm run dev -- --host 127.0.0.1 --port 5173)                # shell 2

# Then:
.venv/bin/python -m harness                       # full run with defaults
.venv/bin/python -m harness --max-walltime 3600   # 1-hour cap
.venv/bin/python -m harness --keep-worktree       # leave the staging worktree for debugging
.venv/bin/python -m harness --backend-port 8100   # alternate port (avoid collisions)
```

Flags:

| Flag | Default | Purpose |
|---|---|---|
| `--engine` | `claude` | Agent CLI to invoke (`claude` or `codex`) |
| `--claude-mode` | `oauth` | Claude auth mode (`oauth` or `bare`) — see "Claude auth modes" |
| `--eval-model` / `--fixer-model` / `--verifier-model` | `opus` | Claude model per role |
| `--resume-branch` | — | Reattach to a prior graceful-stop branch and continue |
| `--max-walltime` | 14400 (4h) | Hard wallclock cap |
| `--keep-worktree` | False | Skip worktree cleanup on exit |
| `--backend-port` | 8000 | Port uvicorn binds inside the worktree |
| `--staging-root` | `harness/runs` | Where per-run dirs are created |

### Engine selection

`--engine claude` (default) uses Claude Opus via the Claude Code CLI. Rate-limit events from Claude's stream-json output are detected deterministically (`rate_limit_event` with `status=rejected`) and trigger a graceful stop with a resume hint.

`--engine codex` uses Codex with the profiles defined in `~/.codex/config.toml`. Preflight validates each of the three profiles (`harness-evaluator`, `harness-fixer`, `harness-verifier`) has `shell_environment_policy.inherit = "all"`.

### Claude auth modes

| Mode | Auth | Preamble | 5h budget | Cost |
|---|---|---|---|---|
| `oauth` (default) | Claude Code subscription keychain token | ~37K tokens/call (user hooks, skills, CLAUDE.md, memory) | Subject to subscription 5-hour cap | Included in subscription |
| `bare` | `ANTHROPIC_API_KEY` env var | None (`--bare` skips user globals) | No 5-hour cap | Pay-per-token — ~10–20× cheaper than oauth's preamble-heavy usage |

Preflight fails loudly if the chosen mode is not usable: `oauth` needs `~/.claude/`; `bare` needs `ANTHROPIC_API_KEY`.

**Mixed auth caveat:** If `ANTHROPIC_API_KEY` is set alongside OAuth login, Claude Code may silently fall back to pay-per-token billing. If you want subscription usage, `unset ANTHROPIC_API_KEY` before running, or run `--claude-mode bare` explicitly.

### Running long sessions

`caffeinate -i .venv/bin/python -m harness ...` keeps the Mac awake through an overnight run without inhibiting display sleep.

### Resume from a graceful stop

When Claude hits its 5-hour limit or an agent subprocess exhausts its transient-retry budget, the harness:

- logs `graceful stop: <reason> — to resume: python -m harness --engine claude --resume-branch <branch>`
- finishes writing `review.md` and exits cleanly with return code 0

To continue after the reset window or API hiccup:

```bash
.venv/bin/python -m harness --engine claude --resume-branch harness/run-<ts>
```

The harness reattaches to the branch (reusing the existing worktree if present), runs a fresh evaluator, and keeps any commits already on the branch. The cycle counter starts at 1 again — fresh evaluators naturally re-discover whatever work remains.

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
- `fixes/<track>/<finding-id>/agent.log` — fixer agent output
- `verifies/<track>/<finding-id>/agent.log` — verifier agent output
- `verdicts/<track>/<finding-id>.yaml` — verifier verdict (verified / failed / reproduction-broken)
- `fix-diffs/<track>/F-<finding-id>.patch` — rolled-back patches preserved for review
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
