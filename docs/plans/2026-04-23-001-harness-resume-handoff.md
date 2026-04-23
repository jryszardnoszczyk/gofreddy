# Harness resume handoff — 2026-04-23 20:57

Context doc for next Claude session to pick up the harness work.

## Current state

- **Branch**: `feat/fixture-infrastructure` (ahead of main by fixture work + 5 new harness fixes)
- **Main HEAD**: `9a2d808` — squash-merged pipeline-simplifications-007 at 22:19 CEST yesterday
- **Latest commit on current branch**: `8979682` — 5 bugs fixed, NOT yet merged to main
- **Harness tests**: 158 green
- **Zero active harness processes** (last run killed at 20:57 today)

## What's been done today

### Morning: overnight run analysis
Overnight run `run-20260422-224908` crashed at 01:22 CEST:
- 20 findings written by evaluators (7+6+7 across tracks a/b/c)
- All 3 fixers silent-hung on Claude 5h rate limit (subscription exhausted by overnight evaluators + my debug work)
- 4.5h burned retrying silent hangs (no RateLimitHit event emitted)
- Post-cycle `restart_backend` failed → unhandled exception → no summary/PR

### Mid-day: 3 fixes committed as `a8dfd48` (now squash-merged into `9a2d808`)
- Bug #11 — silent-hang detection: timeout+<512 bytes output → RateLimitHit
- Bug #12 — post-cycle steps isolated in try/except so `_print_summary` always runs
- Bug #14 — `_viable_resume_id` falls back to fresh if claude-CLI JSONL missing

### Afternoon: resume attempt of `run-20260422-224908`
Launched at 20:30, killed at 20:57. Progress:
- ✅ Fix #14 worked — 3 stale session_ids fell back to fresh
- ✅ Fix #3 worked — eval skip fired for all 3 tracks
- ✅ Fix #4 worked — commit-success log lines visible
- ❌ **Bug #15 fired DATA LOSS**: F-b-1-2's verified commit (319acf8) wiped by false bypass detection
- ❌ **Bug #16 fired FALSE ROLLBACKS**: 5 findings rolled back because user was editing `docs/plans/*` in parallel Claude session

### Evening: 5 more fixes committed as `8979682` (on `feat/fixture-infrastructure`, NOT on main yet)
- Bug #15 — Track-aware bypass detection: `_detect_agent_commit(wt, pre_sha, finding_id)` checks newest commit subject for THIS finding.id. Peer tracks' legit commits no longer trigger reset.
- Bug #16 — `check_no_leak` returns `(actionable, advisory)`. Only actionable (fixer-reachable paths) triggers rollback. Advisory (docs/, tests/, .github/) is warn-only. Restored `_FIXER_REACHABLE` in `harness/config.py`.
- Bug #17 — `Verdict.parse` retries once with 200ms sleep on `yaml.YAMLError` (handles mid-write races)
- Bug #18 — `_warn_if_vite_stale` in `run.py` best-effort-fetches `/src/main.tsx` from `frontend_url` and compares to worktree. Warn on mismatch.
- Bug #19 — Invocation marker log line after `logging.basicConfig`: `========== invocation ts=<ts> pid=<pid> resume=<bool> ==========`

## Total bug inventory (harness)

| # | Bug | Status | Commit |
|---|---|---|---|
| 1 | Widen `check_no_leak` (too narrow) | ✅ fixed + re-refined (#16) | 9a2d808 + 8979682 |
| 2 | Detect agent-initiated commits | ✅ fixed + re-refined (#15) | 9a2d808 + 8979682 |
| 3 | Restore `state.commits` fidelity | ✅ fixed | 9a2d808 |
| 4 | Log `_commit_fix` success | ✅ fixed | 9a2d808 |
| 5 | `git stash` safety net | ✅ fixed | 9a2d808 |
| 6 | Fixer prompt worktree-only | ✅ fixed | 9a2d808 |
| 7 | Duplicate cycle log entries (deferred) | ✅ fixed (#19) | 8979682 |
| 8 | Vite-worktree mismatch | ✅ fixed (pragmatic warn, #18) | 8979682 |
| 10 | INVENTORY.md missing crashes run | ✅ fixed | 3e30acf → 9a2d808 |
| 11 | Silent-hang → RateLimitHit | ✅ fixed | 9a2d808 |
| 12 | Isolate post-cycle steps | ✅ fixed | 9a2d808 |
| 13 | Fixer model tuning | ⏸️ deferred | — |
| 14 | `_viable_resume_id` JSONL check | ✅ fixed | 9a2d808 |
| 15 | Track-aware bypass detection (DATA LOSS) | ✅ fixed | 8979682 |
| 16 | Split leak detection actionable/advisory | ✅ fixed | 8979682 |
| 17 | Verdict YAML parse retry | ✅ fixed | 8979682 |
| 18 | Vite staleness preflight warn | ✅ fixed (pragmatic) | 8979682 |
| 19 | Invocation marker log | ✅ fixed | 8979682 |

Bugs #9, #20 were non-harness (rate limit quota; agent behavior).

## Known deferred / not-fixed

- **Full Vite lifecycle management** — `_warn_if_vite_stale` is pragmatic warn only. Full managed spawn (harness-owned Vite on per-run port) is ~50 LOC, separate plan.
- **Fixer model tuning (Bug #13)** — defaults to Opus for all 3 roles. Dropping fixer+verifier to Sonnet would save ~5x budget but lose quality.
- **Per-track worktrees** — would fundamentally prevent track-interaction bugs (#15 class) + `git stash` race. Major architectural change.
- **Multi-cycle exhaustive mode** — evaluator currently stops at "5+ defects" per prompt. No mode for "keep exploring until budget exhausted".

## Resume targets available

Branches on disk (not all pushed to origin):
```
harness/run-20260418-143943
harness/run-20260418-150236
harness/run-20260418-224554
harness/run-20260418-232711
harness/run-20260419-083144
harness/run-20260421-204028
harness/run-20260421-210825
harness/run-20260422-143941
harness/run-20260422-190507     ← shipped PR #2, 12 commits
harness/run-20260422-224908     ← killed at 20:57, 20 findings preserved, 2 surviving commits
```

The most promising to resume is **`harness/run-20260422-224908`** — has 20 fresh findings on disk from overnight, all 5 new fixes are active (8979682), F-b-1-2 is lost but everything else is recoverable.

## What the next session should probably do

1. **Decide**: merge `feat/fixture-infrastructure` → main first (squash, via GitHub UI or local `git merge --squash`), then resume from main. OR resume directly from `feat/fixture-infrastructure` — harness doesn't care about branch identity.
2. **Verify preflight**: backend on :8000, frontend on :5173, Supabase running, `.env` loaded. See command sequence below.
3. **Resume the run**: `nohup .venv/bin/python -m harness --resume-branch harness/run-20260422-224908 > /tmp/harness-resume.log 2>&1 & disown`
4. **Expected**: 3 eval-skip logs → Fix #14 3 session-fallback warnings → 20 fixers+verifiers dispatch (3 at a time) → ~40-60 min to complete if no new bugs fire.
5. **Watch for**: Bug #15 false positives (should NOT fire now), Bug #16 advisory logs for docs/ changes, Bug #18 Vite mismatch warning.

## Preflight command sequence

```bash
# 1. Supabase
docker ps | grep supabase_db_gofreddy   # should show healthy
# if not:
supabase start

# 2. Backend (from main repo)
set -a; source .env; set +a
nohup .venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 > /tmp/harness-backend.log 2>&1 &
# wait for healthy:
until curl -sS -m 2 http://127.0.0.1:8000/health | grep -q ok; do sleep 2; done

# 3. Frontend — should already be on :5173 (check)
curl -sS http://127.0.0.1:5173/ -o /dev/null -w "%{http_code}\n"

# 4. Launch resume
nohup .venv/bin/python -m harness --resume-branch harness/run-20260422-224908 > /tmp/harness-resume.log 2>&1 & disown
echo "pid=$! at $(date)"
```

## Key file locations (for next session)

- `harness/run.py` — orchestrator; `_process_finding`, `_detect_agent_commit`, `_warn_if_vite_stale`, `_viable_resume_id`
- `harness/engine.py` — subprocess wrapper; `_run_agent`, `Verdict.parse`, silent-hang detection
- `harness/safety.py` — thin shim over `src/shared/safety/tier_c.py`
- `harness/config.py` — `SCOPE_ALLOWLIST`, `HARNESS_ARTIFACTS`, `_FIXER_REACHABLE`, `Config`
- `src/shared/safety/tier_c.py` — `check_scope`, `check_no_leak` (two-list return)
- `harness/sessions.py` — `SessionsFile`, `claude_session_jsonl`
- `harness/prompts/fixer.md` / `evaluator-base.md` / `verifier.md` — agent prompts

## Active tasks (as of handoff)

```
#72 Sanity + commit — completed
#71 Bug #18 Vite staleness — completed
#70 Bug #19 invocation marker — completed
#69 Bug #17 YAML retry — completed
#68 Bug #16 split check_no_leak — completed
#67 Bug #15 track-aware bypass — completed
```

All green. No pending harness work beyond the decision of whether/when to resume run-20260422-224908.

## Repo state caveats

- **Pre-commit hook on this repo is aggressive**: it auto-stages concurrent in-flight changes from other Claude sessions into your commits. Expect some commit messages that don't perfectly match their diffs if you commit with hooks enabled.
- **Committer identity**: auto-configured as `J Ryszard Noszczyk <jryszardnoszczyk@Jans-MacBook-Pro-2.local>` by git. User hasn't set `git config --global user.email`. Not a blocker.
- **Rate limit**: user said "don't worry about rate limits, I'll use a different account" — but the overnight run showed this hadn't actually switched. Whatever account `~/.claude` points at is what the harness uses. Verify `claude --version` and a quick `claude -p "hi"` before launching a long run.
