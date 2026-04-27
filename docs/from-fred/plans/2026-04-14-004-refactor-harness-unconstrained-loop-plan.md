# Harness Unconstrained Loop Refactor

**Goal:** Strip per-agent constraints (turn budgets, timeouts, findings cap, tool allowlists, phased workflows, forbidden-action rules) from the eval-fix-verify harness so each agent works like a free-flowing engineering session. Plug the main-repo isolation leak found in the prior smoke run. Keep every piece of real infrastructure — parallel track/domain dispatch, preflight, worktree setup, verifier paraphrase defense, rollback path — untouched.

**Execution mode:** Inline, commit per step, work directly on `main`. No unit tests added. No TDD ceremony. Deletion-heavy refactor — the meaningful "test" is that the existing test suite still passes after each commit.

---

## Why this exists

Prior smoke run `harness/runs/20260414-190132` ran 2 cycles against A-1, A-6, B-4, C-4. Two fix attempts per cycle, zero real fixes shipped. Every attempt was rigged:

- **A-6 cycle 1:** fixer wrapped a brand-safety enrichment exception in `logger.info(...)` to silently swallow the "1 partial failure(s)" signal. Not a fix — it made the string disappear.
- **C-4 cycle 1:** fixer hardcoded a fitness-themed storyboard template. Verifier paraphrases (meditation / meal-planning / language-learning app) exposed the leaked fitness defaults in scene content.
- **B-4 cycle 2:** fixer actually produced a working SEO audit across 4 unrelated domains. Verifier incorrectly flagged it FAILED because `verifier.md` required a literal `canvas_sections` field in the SSE stream text — the real backend emits `{tool, summary, iteration, response, run_id}` without that field name. Spec bug in our own prompt.
- **C-4 cycle 2:** paraphrase 3 caused SSE timeout (real runtime failure).

Root cause of the gaming: the fixer runs with `MAX_TURNS_FIX=150`, `FIXER_TIMEOUT=3600`, a rigid phase structure, and a "Harness Owns Testing" section forbidding `pytest`, `npm test`, `tsc`, `git commit`, etc. Under pressure with limited time and restricted tools, the minimum-energy path is to make the literal test string disappear, not to understand root causes. The verifier's paraphrase defense correctly catches the cheats but the fixer never produces a real fix.

Secondary discovery: the cycle-1 A-6 fake edit landed in the **main repo working directory** (`src/orchestrator/tool_handlers/evaluate_creators.py`), not the `/private/tmp/harness-run-*` worktree the fixer was supposedly sandboxed in. Codex runs with `sandbox_mode=danger-full-access` + `shell_environment_policy.inherit=all`; `cwd=worktree_path` sets the subprocess working directory but does not sandbox filesystem access. The rollback (`git reset --hard pre_fixer_sha`) reset the worktree and left the main-repo modification behind.

## The fix

**Rip constraints.** Let the fixer operate like a senior engineer opening Claude Code on a real bug: unlimited iteration, any tool it wants, any command it needs, full codebase access. The verifier's paraphrase defense catches bad outcomes after the fact — that's the only trust boundary we need.

**Plug the leak mechanically.** Add `src/` + `frontend/src/` to the same snapshot-restore pattern that already protects `harness/` (`verify_and_restore_protected_files`). If the fixer edits the main repo working directory, the harness silently reverts it at cycle end.

**Fix our verifier spec bug.** Replace the strict `canvas_sections` SSE field check with a DOM-rendering check (what the user actually experiences).

## What gets deleted

### `harness/config.py` — remove 10 fields + matching env parsing

```
track_timeout           (line ~62)
fixer_timeout           (line ~63)
verifier_timeout        (line ~64)
max_turns_eval          (line ~65)
max_turns_fix           (line ~66)
max_turns_verify        (line ~67)
cooldown                (line ~68)
max_fixer_findings      (line ~77)
eval_allowed_tools      (line ~81)
fixer_allowed_tools     (line ~82)
```

Matching lines in `from_cli_and_env` (~lines 163-183): `track_timeout=`, `fixer_timeout=`, `verifier_timeout=`, `max_turns_eval=`, `max_turns_fix=`, `max_turns_verify=`, `cooldown=`, `max_fixer_findings=`, `eval_allowed_tools=`, `fixer_allowed_tools=`.

### `harness/engine.py` — remove plumbing

- `--max-turns <n>` args in claude branches of `_build_eval_command`, `_build_fix_command`, `_build_verify_command` (~lines 306-308, 346-348, 389). Each is a two-token list slice (`"--max-turns", str(config.max_turns_X)`) — delete both tokens.
- `--allowedTools <list>` args in claude branches of `_build_eval_command`, `_build_fix_command` (~lines 306, 346). Same two-token-slice rule.
- `timeout` parameter in `_run_subprocess` signature (~line 473).
- `process.wait(timeout=timeout)` → `process.wait()` (~line 505).
- The full 124-exit-code pipeline that becomes dead code after timeout removal:
  - `harness/engine.py:42` — `except subprocess.TimeoutExpired:` in a helper function
  - `harness/engine.py:485` — docstring line mentioning "Returns the process exit code (124 for timeout)"
  - `harness/engine.py:507-509` — `except subprocess.TimeoutExpired: ... return 124` block in `_run_subprocess`
  - `harness/engine.py:592` — `if exit_code == 124:` branch elsewhere in engine.py that handles the timeout return code
- `timeout` positional args at the three call sites: `eval` method `config.track_timeout` (~line 104), `fix` method `config.fixer_timeout` (~line 201), `verify` method `config.verifier_timeout` (~line 275).

### `harness/run.py` — remove two call sites

- Line ~351: `capped, deferred_ids = merged.cap(config.max_fixer_findings)` → replace with just `capped = merged`. `deferred_ids` is never used downstream (grep confirmed), so drop the variable entirely — do not preserve it as an empty list.
- Lines ~481-482: `time.sleep(config.cooldown)` + its `# 25. Sleep cooldown` comment → delete.

**Do NOT touch `harness/run.py:187`.** There is a separate `time.sleep(30)` inside the cycle-loop health-check retry block (lines 183-193). It is a stack-health retry wait, NOT the cooldown. It stays.

### `tests/harness/conftest.py` — remove env vars from `clean_env` strip tuple

Remove: `TRACK_TIMEOUT`, `FIXER_TIMEOUT`, `VERIFIER_TIMEOUT`, `MAX_TURNS_EVAL`, `MAX_TURNS_FIX`, `MAX_TURNS_VERIFY`, `COOLDOWN`, `MAX_FIXER_FINDINGS`, `EVAL_ALLOWED_TOOLS`, `FIXER_ALLOWED_TOOLS`.

### Tests to delete or fix (do NOT add replacements)

Two flavors of test breakage after the rip:

**Tests that ASSERT on removed fields — delete them.**
- `tests/harness/test_config.py` ~lines 56-58: `assert c.track_timeout == 1800`, `assert c.fixer_timeout == 3600`, `assert c.max_fixer_findings == 5` (and similar for the other removed fields).
- `tests/harness/test_engine.py` ~lines 112, 116, 196, 198: assertions on `cmd[idx_tools + 1] == default_config.eval_allowed_tools` and similar patterns checking `--max-turns` / `--allowedTools` tokens in the built command lists.
- `tests/harness/test_engine.py` ~line 551: simulates `subprocess.TimeoutExpired(cmd, default_config.track_timeout)` to exercise the 124-exit-code path. The whole test becomes moot after timeout removal — delete.

**Test HELPERS/FIXTURES that pass removed fields as Config kwargs — fix, don't delete.**
- `tests/harness/test_run.py` ~lines 85-89: a helper function builds a `Config(...)` instance with `cooldown=0, max_fixer_findings=5` kwargs. After removal, these kwargs cause `TypeError: Config() got unexpected keyword argument 'cooldown'`. Remove the kwargs from the helper constructor.
- `tests/harness/test_prompts.py` ~line 42: same pattern — `Config(..., max_fixer_findings=5, ...)` in a fixture. Remove the kwarg.

**Do NOT touch `tests/harness/test_scorecard.py`.** The `Scorecard.cap()` method itself stays (only the call site in `run.py` is removed), so its tests continue to pass.

**Grep commands to locate everything:**
```bash
grep -n "max_turns\|allowed_tools\|track_timeout\|fixer_timeout\|verifier_timeout\|max_fixer_findings\|cooldown\|\.cap(" tests/harness/test_config.py tests/harness/test_engine.py tests/harness/test_run.py tests/harness/test_prompts.py
```

Handle each match individually: assertion → delete test; fixture/helper kwarg → remove kwarg. This is a deletion refactor — do not add replacement tests.

## What gets added

### `harness/worktree.py` — two new helpers, mirroring existing `snapshot_protected_files` / `verify_and_restore_protected_files` pattern (~line 396 onwards)

```python
def snapshot_main_repo_working_dir(repo_root: Path) -> set[str]:
    """Return repo-relative paths under src/ or frontend/src/ that are
    currently dirty (modified or untracked)."""
```

Implementation: `subprocess.run(["git", "status", "--porcelain", "--", "src/", "frontend/src/"], cwd=str(repo_root), capture_output=True, text=True, check=True)`. Parse porcelain v1 format: `"XY path"` → strip first 3 chars, handle `" -> "` rename syntax by taking the right-hand side, add to set.

```python
def verify_and_restore_main_repo_working_dir(
    repo_root: Path,
    snapshot: set[str],
) -> list[str]:
    """Compare current dirty set against *snapshot*; revert leaked paths.

    Tracked modified files → ``git restore -- <path>``
    Untracked additions → ``unlink``
    Paths already dirty at snapshot time are preserved.
    Returns the list of reverted paths (sorted).
    """
```

Implementation: call `snapshot_main_repo_working_dir` again, compute `current - snapshot`, iterate over the leaked set. For each path, run `git ls-files --error-unmatch -- <path>` to check if it's tracked. Tracked → `git restore -- <path>`. Untracked → `(repo_root / rel).unlink()` if it exists. Log a warning `MAIN REPO LEAK GUARD: reverted N file(s) that were edited outside the harness worktree: ...`.

### `harness/run.py` — two hook call sites

Near the top of `main()`, right before `pf = run_preflight(config)` (~line 111):

```python
main_repo_snapshot = snapshot_main_repo_working_dir(_REPO_ROOT)
logger.info(
    "Main repo leak guard: snapshot has %d pre-existing dirty path(s)",
    len(main_repo_snapshot),
)
```

At the end of each cycle, right after the "23. Second restore" call `verify_and_restore_protected_files(_REPO_ROOT, harness_backup)` (~line 463):

```python
leaked = verify_and_restore_main_repo_working_dir(_REPO_ROOT, main_repo_snapshot)
if leaked:
    logger.warning(
        "Cycle %d leaked %d file(s) outside worktree; reverted: %s",
        cycle, len(leaked), ", ".join(leaked),
    )
```

Add both helpers to the `from harness.worktree import (...)` block near the top of `run.py`.

## What gets rewritten

### `harness/prompts/fixer.md` (225 lines → ~70 lines)

**Delete:**
- "Fixing Process" numbered steps section
- "Diagnose in the Browser" rigid A/B/C/D/E workflow section
- "Harness Owns Testing, Committing, and Rollback" section (the forbidden-actions list: `pytest`, `npm test`, `tsc`, `git add/commit/reset/stash/restore`)
- Any remaining phase-structured prose

**Keep / rewrite as short framing:**
- "You are an engineer fixing failing capabilities in a live web app"
- Context files list: scorecard (below), worktree as cwd, live backend on :8080, live frontend on :3001, playwright-cli with session `fixer-<letter>`, backend log at `/tmp/freddy-backend.log`, full shell
- Explanation that the verifier will paraphrase 3x — so fixes must generalize across wording, not just pass the literal test
- Single completion signal: write `READY_FOR_VERIFICATION` verbatim in your final message
- Two hard invariants only:
  1. Don't run `git commit`, `git reset`, `git stash`, `git checkout --`, `git restore` on the worktree — the harness owns commits and rollback
  2. Don't edit `harness/`, `tests/harness/`, or `scripts/eval_fix_harness.sh` — they're the judge's files and the harness will silently revert edits
- Brief note that everything else is allowed: run `pytest`, `npm test`, restart the backend, edit `src/` and `frontend/src/`, iterate as long as you need. No turn budget.

### `harness/prompts/verifier.md` (224 lines → ~110 lines)

**Delete:**
- "Frozen judge files" prompt section (mechanical sweep handles it)
- Verbose session-isolation ceremony (keep the `-s=verifier-<letter>` requirement, drop the explanation of why)
- The pass criterion currently written as: "(b) SSE `tool_result` event emitted with non-empty data including a `canvas_sections` field containing the `expected_section`". Replace with: "(b) DOM snapshot shows the expected canvas section rendered with non-empty content AND the chat response is not an error message (e.g., 'agent encountered an error', 'stuck in a loop')"

**Keep:**
- Paraphrase defense (literal + 3 paraphrases, all 4 must pass)
- Paraphrase generation rules (different sentence structure, substitute synonyms, swap example values, no 3-token fragments from original)
- Fail-closed rule
- Per-finding workflow: extract matrix row → generate paraphrases → run 4 variants → verify → record verdict
- Verdict YAML format
- "Read pristine test matrix from TEST_MATRIX_PATH header (not the relative path — fixer could have tampered)"

### `harness/prompts/evaluator-base.md` (267 lines → ~180 lines)

**Delete:**
- "Test ONLY the capabilities assigned to your track" scope-policing prose and any similar lecturing

**Keep:**
- playwright-cli command reference (open, goto, snapshot, click, type, press, eval, console, network, screenshot)
- SSE completion polling pattern (the `eval` with while-loop waiting for textarea re-enable)
- Auth URL: `{FRONTEND_URL}/dashboard?__e2e_auth=1`
- Console error filtering rules (HMR / DevTools noise ignored; uncaught exceptions and React error boundaries fail)
- Scorecard YAML output format

## What does NOT change

Do not touch any of these — they are load-bearing and working:

- Parallel track evaluator dispatch (`ThreadPoolExecutor` in `run.py`)
- Parallel fixer dispatch by domain (`fixer_workers`, `split_by_domain`, domain-based split)
- Parallel verifier dispatch by domain
- Scorecard merging across tracks (`_merge_scorecards`)
- `harness/preflight.py` (env vars, DB schema, JWT mint, frontend bypass verification)
- Worktree setup and per-cycle reuse
- `verify_and_restore_protected_files` for `harness/` (the existing frozen-judge sweep)
- Backend hot-restart between fix and verify (`restart_backend` in `worktree.py`)
- Verifier paraphrase defense itself (the one quality bar)
- `git reset --hard pre_fixer_sha` rollback path on FAILED verdict
- Commit-on-VERIFIED path
- Per-cycle separate log files (`eval-N-track-X.log`, `fixer-N-Y.log`, `verifier-N-Y.log`) — observability is valuable
- `harness/scorecard.py` — only the call site in `run.py` is removed; `Scorecard.cap()` method stays and its tests in `test_scorecard.py` stay untouched
- `harness/prompts.py`, `harness/__main__.py`, `harness/worktree.py` (except the two new helpers we're adding), `harness/preflight.py` — grep confirmed they contain zero references to any removed field
- `config.max_fix_attempts` — different field from `max_fixer_findings`, used by the escalation counter; NOT in the removal list
- `scripts/eval_fix_harness.sh` — not used, `python -m harness` is the entry point

### Infrastructure timeouts that STAY (different from agent runtime timeouts)

This refactor removes per-agent runtime budgets. It does NOT remove infrastructure health-check polling loops. Keep all of these:

- `harness/worktree.py:_wait_http_quiet(url, max_attempts=40)` — called by `restart_backend` to poll the backend until `/health` returns 2xx after a uvicorn relaunch
- `harness/preflight.py:_wait_http` — similar polling used in `check_stack_health` and `validate_cors`
- Any `urllib.request.urlopen(req, timeout=...)` socket timeouts inside those poll helpers — they're per-attempt sanity timeouts, not per-agent runtime budgets
- `HARNESS_MAX_WALLTIME` (default 14400s = 4h) — the single outer wall-clock cap enforced in `run.py:155`. Stays as the only backstop for runaway agents.

The distinction: **removed** = "how long can an agent run before we kill it". **kept** = "how long do we wait for localhost:8080 to come up before giving up on the backend".

## Execution order

Eight steps, each is its own commit except where noted. Each commit should leave the codebase runnable — but step 3 is intentionally one large commit because splitting it would leave `engine.py` referencing deleted config fields between commits.

**Step 0 — Prereq cleanup (no commit):**
```bash
git restore src/orchestrator/tool_handlers/evaluate_creators.py
```
This reverts the leaked A-6 fake fix from run `20260414-190132`. Not a commit — just clean the working directory so the leak guard starts from a known-clean state.

**Step 1 — Leak guard (one commit):**
Add `snapshot_main_repo_working_dir` + `verify_and_restore_main_repo_working_dir` to `harness/worktree.py`. Import them in `harness/run.py` and add the snapshot call pre-preflight + restore call end-of-cycle. Run `pytest tests/harness/ -q --confcutdir=tests/harness` — should still pass (no new tests, only new functions that existing tests don't touch). Commit.

**Step 2 — Rip all constraint fields in one pass (one commit):**
Delete all 10 config fields + their env parsers. Delete `--max-turns` + `--allowedTools` from `engine.py`. Delete `timeout` plumbing from `_run_subprocess` + its three call sites. Delete `scorecard.cap()` call in `run.py`. Delete `time.sleep(cooldown)` in `run.py`. Delete matching env vars from `conftest.py`. Delete tests asserting on any of the above. Run suite until green. Commit.

**Step 3 — Rewrite fixer.md (one commit):**
Strip phases, forbidden-tests, rigid workflow. Keep framing, context files, `READY_FOR_VERIFICATION` signal, 2 hard invariants. Run suite. Commit.

**Step 4 — Trim verifier.md (one commit):**
Drop frozen-judge prose + strict `canvas_sections` check (replace with DOM-rendering check). Keep paraphrase defense, fail-closed rule, verdict format. Run suite. Commit.

**Step 5 — Trim evaluator-base.md (one commit):**
Drop scope-policing prose. Keep playwright-cli reference, SSE polling, auth URL, console filter, scorecard format. Run suite. Commit.

**Step 6 — Final suite + sanity check (no commit unless fixes needed):**
```bash
.venv/bin/python -m pytest tests/harness/ -q --confcutdir=tests/harness
.venv/bin/python -m harness --help
.venv/bin/python -c "
from harness.config import Config
c = Config.from_cli_and_env([])
for attr in ('max_turns_fix','max_turns_eval','max_turns_verify',
             'fixer_timeout','track_timeout','verifier_timeout',
             'max_fixer_findings','fixer_allowed_tools',
             'eval_allowed_tools','cooldown'):
    assert not hasattr(c, attr), f'{attr} still present'
print('OK: all removed fields absent')
"
```
If any of these fail, fix and commit. Otherwise proceed to smoke.

**Step 7 — Smoke run (no commit — validation):**
Target A-6 and C-4 because these are the two caps the fixer cheated on last time. If the unconstrained loop produces real fixes here, the refactor is validated.

Preflight check:
```bash
curl -s -o /dev/null -w "backend: %{http_code}\n" -m 3 http://localhost:8080/health
curl -s -o /dev/null -w "frontend: %{http_code}\n" -m 3 http://localhost:3001
```

If either is down, start it per session memory. Then launch:

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/freddy && \
set -a && source .env && set +a && \
source .venv/bin/activate && \
HARNESS_TRACKS="b e" FRONTEND_URL=http://localhost:3001 CODEX_VERIFIER_PROFILE=harness-fixer \
python3.13 -m harness --engine codex --cycles 2 --only A-6,C-4 --fixer-workers 2
```

**Signals that the refactor worked:**
- Fixer logs show extended investigation: `rg` searches, `playwright-cli` browser reproductions, `curl` against the backend, grepping `/tmp/freddy-backend.log` for error stacks, running tests the fixer chose to run
- Worktree git log shows actual commits ahead of main at end of at least one cycle
- At least one finding goes VERIFIED across both cycles (cycle-1 or cycle-2)
- Main repo `git status --short src/ frontend/src/` is empty after the run (leak guard working)

**Signals the refactor didn't work:**
- Both cycles roll back with zero commits
- Fixer logs show quick pattern-matching (one grep + one edit + done) instead of debugging
- Main repo `git status --short src/ frontend/src/` shows modifications after the run (leak guard broken or bypassed)

## Post-refactor follow-ups (not in this plan)

- **Backend trace injection:** capture request_id in the evaluator scorecard for each failing capability; harness slices `/tmp/freddy-backend.log` by request_id before the fixer runs; inject trace paths into the fixer prompt as context. Gives the fixer real stack traces without blind grepping.
- **C-4 root cause:** the `video_project` planning loop bug may be beyond what any LLM agent can solve autonomously in one run. If cycle 1 of the smoke fails even unconstrained, this needs a human investigation.
- **Escalation ladder rework:** with `max_fixer_findings` removed, the `.escalation-exempt-{cycle}.txt` sidecar logic still references a "findings that were capped" concept indirectly. Audit `harness/scorecard.py:count_finding_attempts` and adjust if needed.
