---
title: "feat(harness): Claude Code engine + single-worktree parallel tracks + resumable graceful stop"
status: completed
date: 2026-04-22
deepened: 2026-04-22
completed: 2026-04-22
---

# Harness: Claude Code engine + single-worktree parallel tracks + resume

Adds Claude Code as a first-class engine alongside Codex, parallelizes the fixer and verifier phases **on a single shared worktree** with per-track worker threads, and introduces a graceful-stop/resume capability so Claude's 5-hour rate limit and exhausted transient retries leave the run in a resumable state.

## Origin

- Directly follows `docs/plans/2026-04-21-001-feat-harness-greenfield-rewrite-plan.md` (merged PR #1, commit `e8c494d`). That plan deferred parallel fixers (KTD #14) and was codex-only.
- Earlier draft of this plan proposed per-track worktrees + per-track backends + cherry-pick consolidation. **That design was withdrawn** after deeper analysis: it reintroduced the git-orchestration complexity the old multi-worktree harness suffered from. The current plan matches the old single-worktree architecture but uses the current harness's stronger verifier semantics (paraphrase defense instead of `git stash` state manipulation).
- **Five correctness bugs** in the current codex-only harness were surfaced during this analysis and are fixed as part of this work (see Correctness Fixes section). Three of them (Bugs #1, #2, #3) are latent in serial mode. Two (Bugs #4, #5) are blocking for parallel execution — without them, parallel mode would destroy peer tracks' work.

## Problem frame

Three concurrent problems came out of the first real end-to-end harness run:

1. **Engine lock-in.** `harness/engine.py:_run_codex` hardcodes `["codex", "exec", "--profile", profile]`. JR wants the next run with Claude Opus, which the current harness cannot invoke.
2. **Sequential fixer+verifier is the wall-clock bottleneck.** Run-20260421-220556 discovered 12 findings; each finding's fixer+verifier cycle takes ~7 min; sequential execution is 84 min for a single cycle. Parallelizing across tracks (A/B/C) cuts this to roughly the slowest track's serial time — ~3× speedup.
3. **No graceful recovery.** Claude's 5-hour hard limit and transient API failures (429, 503, connection drops) currently either retry forever or crash the run. A long overnight run with no resumability is fragile.

## Success criteria

- `python -m harness --engine claude --fixer-model opus` runs cleanly end-to-end and produces committed fixes on a staging branch.
- `python -m harness --engine codex` runs unchanged (default-engine flip doesn't regress codex behaviour).
- Fixer + verifier phases run in parallel across tracks A/B/C. Within a track, findings are processed serially.
- When Claude hits its 5-hour limit or a subprocess exhausts its transient-retry budget, the harness:
  - parses the `rate_limit_event` JSON event from stream-json output (deterministic, not a log string match)
  - writes a resume sentinel (`run_dir/.resume.yaml`) with cycle number, staging branch, and (for rate limits) `resetsAt` timestamp
  - completes the current finding's commit-or-rollback cleanly
  - exits with a non-error status and a clear log line
- Graceful-stop triggered by an evaluator's rate-limit skips this cycle's fixer dispatch entirely (evaluator findings from other tracks that did succeed are still written to `review.md` for post-run inspection, not dispatched).
- Resume via `python -m harness --resume-branch <branch> --resume-cycle N` continues from that cycle with the same tracks; fresh evaluator re-discovers findings.
- **Five correctness bugs** in current `run.py`, `worktree.py`, and `safety.py` are fixed (see Correctness Fixes). Two are blocking for parallel mode (Bugs #4 + #5).
- All existing tests still pass. New engine + parallelism + resume + correctness fixes have unit coverage for non-obvious paths.

## Scope boundaries

**In scope:**
- `harness/engine.py` — engine conditional (claude vs codex — no class hierarchy), rate-limit and transient detection, graceful-stop signal via distinct exception types.
- `harness/run.py` — per-track worker threads on single worktree, `commit_lock` + `restart_lock`, `restart_backend` moved to between fixer and verifier, graceful-stop propagation (both evaluator- and fixer-phase), per-worker exception policy, resume bootstrap, fixed `_capture_patch`.
- `harness/worktree.py` — new `rollback_track_scope(wt, track)` function that only reverts files in the given track's allowlist (replaces globally-destructive `rollback_to` call sites in per-finding paths).
- `harness/safety.py` — fix `check_scope` to attribute dirty files correctly under parallel fixers.
- `harness/config.py` + `harness/cli.py` — new CLI flags, new config fields, default `engine="claude"`, `claude_mode={oauth,bare}`.
- `harness/preflight.py` — check Claude auth (OAuth or `ANTHROPIC_API_KEY` depending on mode); warn if both are set in `oauth` mode (potential silent API-key billing).
- `harness/prompts/verifier.md` — rewrite to drop `git stash`, add evidence-quality gate, add paraphrase defense (ported from old harness).
- `tests/harness/` — unit tests for engine command construction, rate-limit event parsing, `commit_lock`/`restart_lock` behaviour, `check_scope` parallel correctness, `rollback_track_scope` parallel safety, `_capture_patch` captures working-tree diff.
- `harness/README.md` — engine choice, `--claude-mode` tradeoff, caffeinate note, resume usage.

**Out of scope (deliberate non-goals):**
- **Per-track worktrees + cherry-picking.** Proposed and withdrawn. Disjoint scope allowlists + track-filtered commit staging give us the same safety without multi-worktree git orchestration.
- Re-introducing `scorecard.py` / prescriptive test matrix — KTD #10 rejected.
- Re-introducing the "convergence check" stop condition — our four stop conditions (agent-signaled-done, no-progress, walltime, zero-first-cycle) are sufficient.
- Per-cycle all-or-nothing commit/rollback — the current per-finding commit model is strictly better.
- `max_fix_attempts` escalation and escalation-exempt sidecars — complexity that existed to manage scorecard state.
- Cross-cycle session-ID persistence (`.session-*` dotfiles) — fresh UUID per invocation. Matches preservation-first philosophy.
- Parallelism *within* a track — findings within a track can touch overlapping files. We keep within-track serial and rely on cross-track parallelism.
- An `Engine` class abstraction. We use a plain conditional inside `_run_agent` for two engines; a class would be premature abstraction.

## Architecture

### Engine conditional (no class)

`harness/engine.py` grows a branch inside `_run_codex` (renamed to `_run_agent`). Two command builders for the two engines. No Engine class — with only two branches, a class is overhead.

**Claude CLI invocation:**
```python
cmd = ["claude", "-p", prompt_content,
       "--output-format", "stream-json",
       "--include-partial-messages", "--verbose",
       "--session-id", fresh_uuid4(),
       "--model", model,
       "--dangerously-skip-permissions"]
if config.claude_mode == "bare":
    cmd.insert(1, "--bare")
# No stdin — prompt is inline via -p.
```

**Codex CLI invocation** (unchanged from current):
```python
cmd = ["codex", "exec", "--profile", profile]
if model_override: cmd += ["-m", model_override]
cmd.append("-")  # stdin=prompt
```

**Rate-limit detection (claude-only) — structured, not string-match:**
Claude's stream-json output contains this event on every response:
```json
{"type":"rate_limit_event","rate_limit_info":{
  "status":"allowed|rejected",
  "resetsAt":1776855600,
  "rateLimitType":"five_hour",
  "overageStatus":"rejected"
}}
```
Detection: parse each log line as JSON; if `type == "rate_limit_event"` and `rate_limit_info.status == "rejected"`, treat as rate-limit hit. Capture `resetsAt` for diagnostics. **This is deterministic — we are not string-matching error text.**

**Transient error detection (both engines, existing patterns kept):**
- Claude: `API Error: 5\d\d|API Error: 429|overloaded|Internal server error` + JSON `"type":"error"` events
- Codex: existing `429|503|stream disconnected|Reconnecting|overloaded|rate limit`

Retry policy: `_RETRY_DELAYS = (5, 30, 120)` — 3 retries with exponential backoff. On exhaustion, raise `EngineExhausted`. The orchestrator catches both `EngineExhausted` and `RateLimitHit` and triggers graceful-stop.

### OAuth vs bare mode — a cost and limit tradeoff

Claude Code 2.1.117 in stream-json mode injects ~37K tokens of user global config (SessionStart hooks, superpowers, auto-memory, CLAUDE.md, skills) into every invocation. At Opus pricing that's **~$0.23 per invocation of pure preamble overhead**. For 36 invocations per cycle (12 findings × 3 roles), that's ~$8 of waste per cycle plus 1.3M tokens of preamble counting against the 5-hour token budget.

Two modes addressable via `--claude-mode {oauth|bare}`:

| Mode | Auth | Preamble | 5-hour limit | Cost per run |
|---|---|---|---|---|
| `oauth` (default) | Claude Code subscription via keychain | ~37K tokens per call | Yes — subject to 5-hour budget | Included in subscription |
| `bare` | `ANTHROPIC_API_KEY` env var | None (`--bare` skips all hooks/memory/CLAUDE.md) | No 5-hour limit (pay-per-token) | Actual tokens only — ~10-20× cheaper |

Preflight (`harness/preflight.py`):
- `oauth` mode: run `claude auth status` (or probe `~/.claude/` for a valid keychain token). Fail loudly if not authenticated.
- `bare` mode: check `ANTHROPIC_API_KEY` env var is set. Fail loudly if missing.

Default is `oauth` — matches JR's current setup, no new env var required. Users comfortable with pay-per-token can opt into `bare` for faster, cheaper runs.

### Single-worktree parallelism with locks

`harness/run.py` — replace the serial `for finding in actionable` loop with per-track worker threads on a `ThreadPoolExecutor(max_workers=len(config.tracks))`. Each worker drains its track's queue serially. Cross-track file conflicts are impossible by construction because `SCOPE_ALLOWLIST` is disjoint per track.

Two `threading.Lock()` instances held on `RunState`:
- `commit_lock` — wrapped around `git add` + `git commit`. Prevents `.git/index.lock` races between parallel commits.
- `restart_lock` — wrapped around `kill_port` + `spawn uvicorn` + `poll /health`. Prevents two tracks from attempting a backend restart simultaneously.

**Per-track worker (new):**
```python
def _process_track_queue(config, wt, queue, state):
    for finding in queue:
        if state.graceful_stop_requested:
            break
        if walltime_exceeded(state, config):
            break
        _process_finding(config, wt, finding, state)
```

**`_process_finding` sequence (modified):**
1. `pre_sha = rev-parse HEAD`
2. `rollback_track_scope(wt, finding.track)` — clean slate for this track only (Fix #4)
3. `engine.fix(...)` — raising RateLimitHit/EngineExhausted triggers graceful stop
4. `with restart_lock: worktree.restart_backend(...)` — Fix #1, parallel-safe
5. `engine.verify(...)` — same exception handling
6. `check_scope` + `check_no_leak` (Fix #2 for parallel attribution)
7. If verified + clean → `with commit_lock: _commit_fix` (Fix #3, track-filtered staging). Else → `_rollback` (captures patch via Fix #5's single-arg diff, then `rollback_track_scope`).

**Exception policy:** `RateLimitHit` and `EngineExhausted` propagate up and set `state.graceful_stop_requested` — peers finish their current finding and drain. Any other exception gets logged and the worker moves to the next finding (one bad finding shouldn't kill a track). If a rate-limit fires during the evaluator phase, the cycle loop skips fixer dispatch — findings from tracks that did complete are written to `review.md` but not queued for fixing.

**`_commit_fix` modification (Fix #3):** filter `working_tree_changes` through `SCOPE_ALLOWLIST[finding.track]` before `git add`. Ensures track A's commit contains only A's files, even when track B has in-flight unstaged edits in src/.

### Correctness Fixes (pre-existing bugs, fixed as part of this work)

Five bugs in the current codex-only harness. Three (#1–#3) are latent in serial mode; two (#4, #5) are blocking for parallel. All are small once identified.

1. **`restart_backend` runs after commit instead of before verify** (`run.py:171`). uvicorn runs without `--reload`, so the verifier for backend-touching fixes never sees the fix. First run didn't expose it because all 3 shipped fixes were CLI-only. **Fix:** move the restart call into `_process_finding` between `engine.fix` and `engine.verify`, wrapped in `restart_lock`.

2. **`check_scope` misattributes under parallel** (`safety.py:49`). With parallel fixers, track A sees track B's dirty src/ files and flags them as A's scope violations. **Fix:** skip files matching any OTHER track's allowlist from the attribution set. ~3 LOC.

3. **`_commit_fix` stages all dirty files** (`run.py:194`). Under parallel, A's commit would include B's unstaged edits. **Fix:** filter `working_tree_changes` through `SCOPE_ALLOWLIST[finding.track]` before `git add`.

4. **`rollback_to` is globally destructive (BLOCKING for parallel)** (`worktree.py:91`, called from `run.py:153` and `:186`). `git reset --hard` + `git clean -fd` wipes the whole worktree — in parallel mode that destroys peer tracks' in-flight edits. **Fix:** new `rollback_track_scope(wt, track)`:
   - Call `git status --porcelain -z -uall` and parse each record's 2-char status code: `??` = untracked, anything else = modified.
   - Filter to paths matching `SCOPE_ALLOWLIST[track]` AND NOT matching `HARNESS_ARTIFACTS`.
   - `git checkout -- <files>` restores modified; `Path.unlink(missing_ok=True)` deletes untracked.
   - **Never** call `git reset --hard` or `git clean -fd` — those mutate global state.
   - Keep the old global `rollback_to` in `worktree.cleanup()` for graceful-exit only (no parallel tracks at that point).

5. **`_capture_patch` writes empty patch files** (`run.py:211-219`). Called from `_rollback` before the reset, at which point fixer edits are still unstaged — so `git diff pre_sha HEAD` (two-commit diff) is always empty. Rolled-back patches are silently lost. First run didn't expose it because no fixes were rolled back. **Fix:** use single-arg `git diff pre_sha -- <track-filtered files>` (working-tree diff from pre_sha).

### Verifier prompt rewrite

`harness/prompts/verifier.md` — drop the `git stash` dance (globally racy under parallel verifiers). The verifier's job: read the fixer's diff, run the reproduction against HEAD **plus a couple of varied inputs** (different slugs / names / params — catches fixers that hardcode the literal test string), check 2–3 adjacent capabilities still work, confirm no public surface moved. All steps are read-only on working-tree state, so parallel verifiers don't collide.

The input-variation requirement is a guardrail against rigged fixes, ported from the old harness's paraphrase-defense pattern but left lightweight — agent picks the variations itself. Strict "must run exactly 4 variants" prescription was judged overengineering.

### Resume capability

Simpler than the first draft: **no sentinel file, no cycle counter persistence.** Resume is just "continue on the branch."

- On graceful stop, log `to resume: python -m harness --resume-branch harness/run-<ts>` with the rate-limit `resetsAt` if applicable.
- `--resume-branch <branch>` makes `run()` skip worktree creation and attach to the existing branch (reusing the worktree dir if present, re-creating from the branch tip otherwise).
- Cycle counter starts at 1. Fresh evaluator runs against the branch's current state and finds whatever defects remain. Anything already committed stays committed. Self-healing.

**`RunState` new fields:**
- `graceful_stop_requested: bool = False`
- `commit_lock: threading.Lock`
- `restart_lock: threading.Lock`

**`Config` new fields:**
- `engine: Literal["claude", "codex"] = "claude"` (NEW DEFAULT)
- `claude_mode: Literal["oauth", "bare"] = "oauth"` (NEW)
- `eval_model: str = "opus"`, `fixer_model: str = "opus"`, `verifier_model: str = "opus"`
- `codex_eval_model: str = ""`, `codex_fixer_model: str = ""`, `codex_verifier_model: str = ""` (optional overrides)
- `resume_branch: str = ""`

### CLI surface

New flags in `harness/cli.py`:
- `--engine {claude,codex}` (default: claude)
- `--claude-mode {oauth,bare}` (default: oauth)
- `--eval-model`, `--fixer-model`, `--verifier-model`
- `--resume-branch`

Existing: `--max-walltime`, `--keep-worktree`, `--staging-root`, `--backend-port`.

## Implementation units

### Unit 1 — Engine conditional + rate-limit event parsing [~70 LOC]

**Goal:** `_run_agent(config, prompt_path, ...)` dispatches to claude or codex CLI. Parse rate-limit events from claude stream-json output.

**Files:**
- `harness/engine.py` — rename `_run_codex` → `_run_agent`. Add `_build_claude_cmd`, `_build_codex_cmd`. Add `parse_rate_limit(log_path)` that JSON-parses each line looking for `{"type":"rate_limit_event", "rate_limit_info":{"status":"rejected", ...}}`. Extend transient-error detection for claude patterns.
- `harness/engine.py` — add `EngineExhausted`, `RateLimitHit` exceptions. `_run_agent` raises these distinctly so the orchestrator can route each to the graceful-stop path.

**Patterns to follow:**
- `_RETRY_DELAYS = (5, 30, 120)` (existing).
- Fresh UUID per invocation via `uuid.uuid4()` — no session-id dotfile.
- Claude prompt goes inline via `-p <content>`; no stdin.
- Log path written to existing `codex.log` filename — rename to `agent.log` to avoid engine-name confusion (cosmetic).

**Test scenarios:**
- Happy path: `_build_claude_cmd` emits correct flags for both oauth and bare modes.
- Happy path: `_build_codex_cmd` matches current behaviour (regression).
- Rate-limit: given a log file with `{"type":"rate_limit_event","rate_limit_info":{"status":"rejected","resetsAt":1776855600,...}}`, `parse_rate_limit` returns `RateLimitHit(resets_at=1776855600)`.
- Rate-limit: given a log file with `"status":"allowed"`, returns None.
- Transient: given a log with `API Error: 429`, detects as transient. Given empty log, returns False.
- Edge: malformed JSON lines are skipped, not raising.

**Execution note:** test-first — build `tests/harness/test_engine.py` before the refactor.

---

### Unit 2 — Parallel dispatch + locks + correctness fixes [~60 LOC including bug fixes]

**Goal:** Replace serial finding loop with per-track worker pool. Add `commit_lock` + `restart_lock`. Wire in all five correctness fixes. Propagate graceful-stop from evaluator-phase too.

**Files:**
- `harness/run.py` — add `_process_track_queue`. Replace serial `for finding in actionable` with ThreadPoolExecutor fan-out. Modify `_process_finding`, `_commit_fix`, `_capture_patch` per architecture. Add `commit_lock`, `restart_lock`, `graceful_stop_requested` to `RunState`.
- `harness/run.py` — modify `_evaluate_tracks` to re-raise rate-limit / exhaustion instead of swallowing.
- `harness/safety.py` — Bug #2 fix to `check_scope` (~3 LOC).
- `harness/worktree.py` — add `rollback_track_scope(wt, track)`. Keep existing `rollback_to` for graceful-exit cleanup only.

**All five correctness bugs are fixed in this unit** (see Correctness Fixes section for detail).

**Test scenarios:**
- Happy path: 3 tracks × 2 findings each process in parallel; timestamps in log show tracks running concurrently; all 6 commits land.
- Happy path: `_process_track_queue` with `graceful_stop_requested=True` breaks out after the current finding.
- Edge: walltime exceeded mid-track drops remaining findings in that track.
- Exception policy: `_process_finding` raising a generic `RuntimeError` → track continues to next finding, error logged.
- Exception policy: `_process_finding` raising `RateLimitHit` → track stops, graceful-stop flag set, peer tracks drain.
- Evaluator graceful-stop: `_evaluate_tracks` worker raises `RateLimitHit` → cycle loop catches, skips fixer dispatch, writes resume sentinel.
- Integration: `_commit_fix` under parallel execution stages only the finding's track's files; other tracks' dirty files remain uncommitted for their own workers.
- Integration: `rollback_track_scope` under parallel execution — track A rollback leaves tracks B and C uncommitted files intact (this is THE blocking test for Bug #4).
- Integration: `_capture_patch` captures non-empty working-tree diff for a rolled-back finding (regression test for Bug #5).
- Lock safety: two threads concurrently calling `_commit_fix` don't hit `.git/index.lock` races (validated via integration test).

---

### Unit 3 — Graceful stop + resume [~25 LOC, down from 40]

**Goal:** On `RateLimitHit` or `EngineExhausted`, log a clear `to resume:` message and exit cleanly. `--resume-branch <branch>` reattaches and runs fresh from cycle 1.

**Files:**
- `harness/run.py` — bootstrap at top of `run()`: if `config.resume_branch`, skip worktree creation and attach to the existing branch.
- `harness/worktree.py` — `attach_to_branch(branch, config)`: reuse existing worktree dir if present, else `git worktree add <path> <branch>`.
- `harness/cli.py` — `--resume-branch` flag.
- `harness/config.py` — `resume_branch` field.

**Test scenarios:**
- Happy path: `--resume-branch <existing>` reattaches, skips `worktree.create`, starts cycle 1.
- Graceful stop propagation: one track worker raises `RateLimitHit` → peers observe `state.graceful_stop_requested` and drain after current finding.
- Edge: `--resume-branch <missing>` → preflight fails loudly.

---

### Unit 4 — Preflight + config + CLI [~20 LOC]

**Goal:** New Config fields, CLI flags, auth preflight.

**Files:**
- `harness/config.py` — add fields per architecture section. Wire new CLI args and env vars in `from_cli_and_env`.
- `harness/cli.py` — add new flags. Update `--help`.
- `harness/preflight.py` — `check_claude_auth(mode)`. `oauth` → run `claude auth status`, fail on non-zero. `bare` → check `ANTHROPIC_API_KEY` is set.

**Test scenarios:**
- `--engine claude --claude-mode oauth` without OAuth login → preflight fails with actionable message.
- `--engine claude --claude-mode bare` without `ANTHROPIC_API_KEY` → preflight fails.
- `--engine codex` doesn't touch Claude preflight.
- Config defaults: `engine=claude`, `claude_mode=oauth`, models default to `"opus"`.

---

### Unit 5 — Verifier prompt rewrite [prompt-only]

**Goal:** Rewrite verifier prompt so it doesn't mutate working-tree git state. No `git stash`. Keep the semantic simple: agent reads the fixer's diff, runs reproduction against HEAD, checks a couple of adjacent capabilities, confirms no public surface moved. Trust the agent to vary inputs and pick adjacent capabilities.

**Files:**
- `harness/prompts/verifier.md` — rewrite.

**Verification:**
- Manual: run a parallel cycle with 2+ verifiers active. Observe no `.git/stash` activity and no git index errors in the log.

---

### Unit 6 — Tests + smoke validation [~35 LOC net]

**Goal:** Unit coverage for the non-obvious paths; end-to-end smoke.

**Files:**
- `tests/harness/test_engine.py` — NEW. Command construction (claude oauth/bare/codex), rate-limit event parsing, transient detection.
- `tests/harness/test_safety.py` — ADD: parallel-safe `check_scope` cases.
- `tests/harness/test_run_parallel.py` — NEW. Per-track queue dispatch, `commit_lock` / `restart_lock` isolation, graceful-stop propagation, `rollback_track_scope` doesn't touch peer-track files, `_capture_patch` captures non-empty diff on rollback.
- `tests/harness/test_resume.py` — NEW. `attach_to_branch` round-trip.

**Verification:**
- `pytest tests/harness/` green.
- `python -m harness --engine claude --max-walltime 1800 --keep-worktree` completes one cycle end-to-end against real Claude Opus.

---

### Unit 7 — README + docs [~15 LOC]

**Goal:** Operator guidance for engine choice, claude-mode tradeoff, caffeinate, resume. Include a one-line note that `ANTHROPIC_API_KEY` set alongside OAuth may cause Claude to silently bill pay-per-token — unset it if you want subscription usage.

**Files:**
- `harness/README.md` — add sections: "Engine selection", "Claude auth modes", "Running long sessions (caffeinate)", "Resume from a failed run".

## Requirements trace

| Requirement | Unit |
|---|---|
| `--engine claude --fixer-model opus` runs end-to-end | Unit 1, Unit 4, Unit 6 |
| `--engine codex` unchanged | Unit 1, Unit 6 |
| Parallel fixer + verifier across tracks (single worktree) + all 5 correctness fixes | Unit 2 |
| 5-hour rate limit → graceful stop (deterministic event parsing) | Unit 1, Unit 3 |
| Transient exhaustion → graceful stop | Unit 1, Unit 3 |
| Evaluator-phase graceful-stop + track exception policy | Unit 2 |
| Resume from branch | Unit 3, Unit 4 |
| OAuth vs bare mode + auth preflight | Unit 1, Unit 4 |
| Verifier prompt rewrite (no `git stash`) | Unit 5 |
| Existing tests pass + new coverage | Unit 6 |
| README guidance (including mixed-auth note) | Unit 7 |

## Risks

| Risk | Mitigation |
|---|---|
| Claude CLI flag drift in a future version | Unit tests lock command shape; failures visible at version bump. |
| Rate-limit event structure changes | Parsing failure falls through to transient-retry → exhausted-retry → same graceful stop. |
| Cross-track syntax pollution (track B leaves broken src/ mid-run) | Backend restart fails loudly; log makes it clear. Defer an `ast.parse` guard unless it actually happens. |
| Data collisions in parallel verifiers (shared backend state) | Verifier prompt directs agents to vary inputs (slugs, emails) across checks. |
| `rollback_track_scope` misses an out-of-scope file the agent created | File stays dirty; `check_scope` catches it as a scope violation. Not destructive. |
| Resume branch missing | Preflight fails with actionable message. |
| OAuth preamble cost burns 5-hour budget faster than expected | Documented. User can switch to `--claude-mode bare`. |
| `ANTHROPIC_API_KEY` set alongside OAuth silently bills pay-per-token | README note flags it. Preflight doesn't warn (would be noise); users can `unset` if they want subscription usage. |

## Decisions made in this plan

- Unified log filename: `agent.log` (misleading to call it `codex.log` with two engines).
- Track worker exception policy: rate-limit / exhausted → graceful stop; anything else → log and continue.
- Evaluator-phase graceful-stop: skip fixer dispatch for that cycle; partial findings go to `review.md` only.
- Mixed-auth (`ANTHROPIC_API_KEY` set in oauth mode): README note only, no preflight warning. Users who hit it will see it in billing.
- Resume: branch-only (`--resume-branch <x>`). No `.resume.yaml`, no cycle counter. Fresh cycle from attached branch.
- Verifier prompt: trust the agent for input variation and adjacency selection — don't prescribe paraphrase structure programmatically.

## Deferred to implementation

- `ast.parse` guard before backend restart (defer until cross-track syntax pollution actually happens).
- Parsing `result` event for cost accounting (nice-to-have).
- Capturing `overageDisabledReason` in rate-limit log line (lean yes).

## Plan deepening notes

1. **Rate-limit detection is verified deterministic.** Live `claude --output-format stream-json` emits `{"type":"rate_limit_event","rate_limit_info":{...}}` with `status` and `rateLimitType` fields. We parse JSON, not strings.
2. **Cost accounting is tracked but not blocking.** Each response's `result` event includes `total_cost_usd`. Useful for per-run reports but not needed for correctness.
3. **`--bare` is a real operator choice, not a hidden implementation detail.** Document it in README with the specific tradeoff (5-hour limit visibility vs preamble cost).
4. **Three correctness fixes are independent of Claude support** but bundle naturally with parallelism work since the parallel path exposes them. Do not split into a separate PR — the tests for parallel behaviour depend on these fixes.
