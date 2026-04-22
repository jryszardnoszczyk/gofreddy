---
title: Harness scope + gating deep research (F1.1-F1.4, F2.1-F2.6)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-004-pipeline-overengineering-deep-research.md
---

# Deep research: harness over-engineering audit

## Executive summary

Of the 10 findings, my honest read is **3 KEEP**, **3 SIMPLIFY**, **2 REDESIGN**, **2 DELETE/OBSOLETE**, with **F2.1 (per-cycle smoke), F2.3 (inventory pre-computation), and F1.2 (single-worktree allowlist machinery)** as the most consequential.

Two findings (F1.3 `_capture_patch` and F2.4 `compose_pr_body` agent + 200-char floor) describe **code that no longer exists** in the harness — the audit collected these from outdated plan docs, not from the live source. `_capture_patch` was inlined out and replaced with the fixer prompt writing its own patch (`fixer.md:55-62`); `compose_pr_body` was never implemented as an agent — `harness/review.py:59-79` is a deterministic markdown formatter. Both should be marked **DELETE/OBSOLETE** as audit items.

The most defensible KEEPs are the parallel-safety primitives (`commit_lock`, `restart_lock`, `parse_rate_limit`) — those handle real concurrency, are cited as load-bearing in the audit's own KEEP list, and survived 92 tests. The most consequential SIMPLIFYs are F2.1 (smoke is mostly redundant after preflight + tip) and F2.3 (the CLI/API inventory subprocesses are bug magnets and the agent can introspect itself faster than we can subprocess-introspect for it). F1.2 deserves REDESIGN if the harness scales beyond 3 tracks; today, the per-track-allowlist machinery is paying its cost without a clearly winning alternative.

---

## F1.1 — `SCOPE_ALLOWLIST` + `check_scope` + `rollback_track_scope` per-track machinery

- **Today:** `safety.SCOPE_ALLOWLIST` (3-entry regex dict, `safety.py:8-12`) is consulted by `check_scope` (`safety.py:49-64`), `rollback_track_scope` (`worktree.py:135-179`), and `_commit_fix` (`run.py:278-280`). The fixer prompt also lists each track's allowlist explicitly (`fixer.md:34-42`). `check_scope` filters out peer tracks' in-flight dirty files; `rollback_track_scope` reverts only paths matching the current track's regex.
- **Why it exists:** Single shared worktree + 3 parallel fixer threads means every git mutation has to reason about whose work it can touch. Per-track regex was the cheap alternative to per-track worktrees. Bug history (`128b43a`, `771027f`, `b6f3a61`) shows three rounds of fixes all inside this machinery — most subtle was that the original `git diff pre_sha..HEAD` returned empty because the fixer leaves edits uncommitted.
- **What's wrong:** The fixer prompt names the allowlist (so the agent self-restricts), the orchestrator re-checks via `check_scope`, and `rollback_track_scope` re-applies the allowlist regex on rollback. That's the SAME knowledge encoded three times — Python regex (`safety.py:8-12`), prompt template (`fixer.md:34-42`), and rollback predicate (`worktree.py:164`). The "other_patterns" peer-filtering trick (`safety.py:60-62`) is genuinely subtle and was bug #4 of plan-2; an evaluator could plausibly read this code wrong and not catch a leak in review. Also the `git checkout -- <files>` + `git reset HEAD --` + `Path.unlink` triple in `rollback_track_scope` (`worktree.py:175-178`) is path-list-driven, not snapshot-driven, so any edge case in `git status --porcelain -z` parsing can leak.
- **The right model — hybrid (deterministic check, agentic primary enforcement):** The fixer prompt is already the primary enforcement — agents respect their allowlist 95%+ of the time. Keep deterministic `check_scope` as a *gate*, not a scrub. Drop `rollback_track_scope`'s scope filter and just `git checkout` the per-track files the agent claims it touched (read from sentinel/agent log) plus a `git status --porcelain` cleanup of anything in-scope. Tradeoff: lose the "we'll catch the agent if it lies" guarantee on rollback-only paths. But scope violations on rollback don't ship; they only bloat the dirty tree until the next commit attempt's `check_scope` catches them.
- **Concrete redesign:** (1) Keep `SCOPE_ALLOWLIST` and `check_scope`. (2) Delete the peer-filter logic in `check_scope` and require commits to land sequentially under `commit_lock` (already do!), so the dirty tree at commit time only contains *this* track's edits + harness artifacts. (3) Simplify `rollback_track_scope` to read the agent's reported touched files and just `git checkout HEAD -- <files>` + `git clean` for untracked-in-scope. ~30 LOC removed across `safety.py` and `worktree.py`. Eliminates the "in-flight peer edits" mental model from the rollback path.
- **Complexity removed:** `safety.py`: ~10 LOC of peer-filter (lines 60-63). `worktree.py`: ~15 LOC of allowlist-scoped status iteration (lines 159-178). Three tests in `test_safety.py` (parametrized `test_check_scope_ignores_peer_tracks_dirty_files`, `test_check_scope_parallel_scenario_a_only_flags_own_violations`) shrink. Net: ~30 LOC and one mental model.
- **New risks:** If the agent under-reports its touched files in the sentinel, rollback misses untracked debris. Mitigation: `git status --porcelain` at end of rollback; if anything remains in-scope, hard fail. Also if commits stop being sequential under `commit_lock`, the simplification breaks — needs a test asserting the lock is held.
- **Verdict:** **SIMPLIFY**. The machinery works but is over-defended. Fold peer-filter into the lock, slim the rollback path.

---

## F1.2 — Per-track ephemeral worktrees vs current single-worktree+allowlist

- **Today:** One shared worktree (`worktree.create`, `worktree.py:35-56`), 3 parallel `_process_track_queue` threads (`run.py:157-193`), per-track regex scope, `commit_lock` + `restart_lock`. Backend restarts under `restart_lock` between fix and verify (`run.py:241-242`).
- **Why it exists:** Per-track worktrees were rejected in plan 2026-04-22-003 as "git orchestration complexity." The chosen design saved disk + sidestepped cherry-pick consolidation. Single backend port (`8000`) was the other forcing function — multiple worktrees would multiply backend processes.
- **What's wrong:** The single backend is a serialization bottleneck — the verifier MUST see the fixer's changes, so backend restart serializes around `restart_lock`, which means tracks can't overlap their fix→verify boundaries. In practice, when 3 tracks all hit verify simultaneously, two wait. Also: the scope/rollback/leak machinery (F1.1, F1.4) exists *only* because the worktree is shared. Per-track worktrees would let `git reset --hard` work normally and delete ~80 LOC of shared-state careful-thinking.
- **The right model — deterministic (worktree per track):** Per-track worktrees + per-track backend ports + cherry-pick consolidation at the end is more LOC at the worktree boundary but less LOC across the whole pipeline, and far fewer subtle correctness modes. Tradeoff: 3× disk for `.venv` (mitigated by symlinks already used), 3× backend memory (~150 MB each = manageable), and a cherry-pick step at the end. The current design's invisible cost — the ratio of harness-internal bug-fix commits (7) to product fixes (3) — is the empirical signal that the saved complexity migrated elsewhere.
- **Concrete redesign:** (1) `worktree.create` accepts a track id, picks port from `8000+offset`, creates `<staging_root>/<ts>-<track>` worktree. (2) Each track thread holds its own worktree handle. (3) At cycle end, cherry-pick each track's commits onto a final integration branch (linear, deterministic — one operator). (4) Delete `commit_lock`, `restart_lock`, `rollback_track_scope`, `check_scope`'s peer-filter, and `_commit_fix`'s allowlist-stage filter. (5) Add `worktree.consolidate(tracks) -> branch` (~30 LOC).
- **Complexity removed:** `safety.py:60-63` (peer filter), `worktree.py:135-179` (`rollback_track_scope`'s in-scope dance), `run.py:42-43` (`commit_lock`/`restart_lock` declarations) and ~15 lock-acquire sites. ~80-100 LOC net.
- **New risks:** Cherry-pick conflicts (low — tracks have disjoint scope by definition). 3× backend startup time (~30s vs ~10s). 3× DB seeding (mitigated: shared local Supabase). Worktree disk consumption (manageable). The biggest real risk: if a fixer in track B touches a file in `cli/freddy/` (track A's scope) — currently caught by `check_scope`, in the new design caught by cherry-pick conflict. Test coverage would shift from 8 scope tests to ~4 cherry-pick tests.
- **Verdict:** **REDESIGN** if you plan to scale beyond 3 tracks or you keep paying for shared-state bugs. **KEEP AS-IS** if you trust the current 92-test suite and don't expect to add a 4th track. My read: the rejection was right *for plan 2 alone*, but the 7:3 meta-fix:product-fix ratio argues for revisiting if a plan 3 expands tracks.

---

## F1.3 — `_capture_patch` manual unified-diff construction

- **Today:** **The function does not exist in the current codebase.** Patch capture is delegated to the fixer agent itself: `fixer.md:55-62` instructs the agent to run `git diff HEAD > {run_dir}/fix-diffs/{track}/F-{finding_id}.patch` before stopping. `review.py:104-109` reads whatever patches landed in `fix-diffs/`.
- **Why it exists:** Per the 2026-04-21-001 plan (`run.py:283`), `_capture_patch` was specced as inline manual unified-diff construction. It was deleted before plan-2 shipped — the audit picked it up from the plan doc, not the source.
- **What's wrong:** Nothing — the function is gone. The cited test `tests/harness/test_run.py:91-108` (`test_capture_patch_writes_non_empty_diff_for_uncommitted_fix`) also doesn't exist; the closest is `test_commit_fix_stages_only_in_scope_files` (lines 47-72) which tests staging, not patch capture. (`grep -n capture_patch tests/harness/` returns no current matches.)
- **The right model — agentic (already done):** The agent runs `git diff HEAD > <path>` itself. This is an exemplar of "let the agent do the obvious thing instead of Python-faking it."
- **Concrete redesign:** Already shipped. Optional improvement: add `safety.working_tree_changes` check post-fix that warns if the patch file is missing (currently silent). ~5 LOC.
- **Complexity removed:** Already removed. ~50 LOC of unified-diff construction was deleted in the greenfield rewrite path.
- **New risks:** The agent might forget to write the patch. `review.py:108`'s `rglob("F-*.patch")` would silently miss it. Worth a single test asserting that on a verified fix, the patch file exists.
- **Verdict:** **DELETE (audit item is obsolete).** Add a one-line patch-existence assertion in `_process_finding` for safety net.

---

## F1.4 — `HARNESS_ARTIFACTS` + `_FIXER_REACHABLE` regex exception lists

- **Today:** Two regexes in `safety.py:18-22`. `HARNESS_ARTIFACTS` excludes paths the harness itself writes (`backend.log`, `.venv`, `node_modules`, `clients`, `frontend/node_modules`). `_FIXER_REACHABLE` is the union of all 3 tracks' allowlists; used in `check_no_leak` (`safety.py:86`) so concurrent dev work in `docs/`, `harness/`, `tests/` is not flagged as a leak.
- **Why it exists:** Each entry is an empirically-discovered false positive. `clients/` from `smoke-cli-client-new` (creates per-cycle workspace litter, F2.1). `node_modules` from npm install (used to be triggered by fixer running `npm install` before the prompt forbade it — `fixer.md:51-52`). `backend.log` from `worktree.restart_backend` (`worktree.py:122`). `_FIXER_REACHABLE` is the dual: anything matching a track's allowlist could plausibly be the fixer's, anything else is dev-on-main noise.
- **What's wrong:** Two regex sources of truth that must stay in sync (HARNESS_ARTIFACTS shouldn't overlap any track's scope; `_FIXER_REACHABLE` is hand-derived from `SCOPE_ALLOWLIST`). When you add a new track or harness artifact, you have to remember to update both. `_FIXER_REACHABLE` is also literally the union of the 3 SCOPE_ALLOWLIST regexes — derivable, but spelled out by hand.
- **The right model — deterministic (with derivation):** Build `_FIXER_REACHABLE` from `SCOPE_ALLOWLIST` programmatically. Source HARNESS_ARTIFACTS from a single `WORKTREE_GENERATED_PATHS` set defined adjacent to `worktree.create` (since that's where `clients/` mkdir, `.venv` symlink, `backend.log` open live). Net: same behavior, one source per concept.
- **Concrete redesign:** (1) In `worktree.py`, define a tuple `WORKTREE_GENERATED_PATHS = ("backend.log", ".venv", "node_modules", "clients", "frontend/node_modules")` next to `create()`. (2) In `safety.py`, build `HARNESS_ARTIFACTS` from that import. (3) In `safety.py`, build `_FIXER_REACHABLE` as `re.compile("|".join(p.pattern for p in SCOPE_ALLOWLIST.values()))`.
- **Complexity removed:** Not LOC — just synchronization burden. Eliminates "where is this list defined" hunts. ~5 LOC saved, but more importantly co-locates each path with its origin.
- **New risks:** Very low — the regex compile-time error surface is unchanged, just restructured. Tests in `test_safety.py:106-112` (`test_check_scope_ignores_harness_artifacts`) still pass without modification.
- **Verdict:** **SIMPLIFY**. Small, mechanical, low-risk. Worth doing whenever you next touch `safety.py`.

---

## F2.1 — Per-cycle smoke check

- **Today:** `smoke.check` runs at preflight (`run.py:73`), at the start of every cycle (`run.py:108`), and once at tip (`run.py:78`, `_tip_smoke`). 5 hardcoded checks in `harness/SMOKE.md`: CLI help, API health, API auth GET, Playwright frontend, and `freddy client new smoke-check-$(date +%s)` which writes a new directory under `clients/` every cycle.
- **Why it exists:** Catch "fixer broke the world" early so the next cycle doesn't burn agent time on a regressed app. Bug history shows 3 fixes inside smoke: `7ae6361` (POST→GET for idempotency), `b976591` (status code), `d4db06d` (playwright cwd resolution). Round-3 audit notes the `clients/` litter explicitly.
- **What's wrong:** (a) Per-cycle smoke is duplicative with `verify`, which already exercises the fixed code path with paraphrased inputs (`verifier.md:22-24`). If the fix verified, the world isn't fundamentally broken. (b) The litter from `smoke-cli-client-new` accumulates on disk every cycle until `worktree.cleanup` runs — for long runs this is real garbage. (c) Three of five checks fire against the *worktree*, but the Playwright check against frontend port 5173 actually exercises a *separate* dev server the harness doesn't manage — yet smoke fails the run if that drifts. (d) The `--shell=true` expansion path (`smoke.py:81-85`) is a footgun if anyone ever marks an LLM-generated check trusted.
- **The right model — deterministic (preflight + tip only):** Smoke is a gate, not a per-cycle observability tool. Run at preflight (catch broken `.venv`, dead backend) and at tip (catch landed-fixes-broke-the-world). Drop per-cycle. The verifier already paraphrase-tests every fix; if 3 fixes verified, the world is at least 3-fixes-worth-of-functional. The litter goes away automatically.
- **Concrete redesign:** (1) Delete the `smoke.check` call at `run.py:108` (cycle start). (2) Drop `smoke-cli-client-new` from SMOKE.md (or change it to `freddy client list` — read-only). (3) Keep preflight + tip with the existing 4 checks. (4) Optional: add a "smoke ran more than 30s ago" gate inside `_process_track_queue` for very long runs.
- **Complexity removed:** ~5 LOC in `run.py`. ~10 LOC in SMOKE.md. The whole `clients/smoke-check-*` litter problem. One source of false-fail (Playwright + dev-server drift) becomes only-at-tip noise. `tests/harness/test_smoke.py` shrinks slightly — one fewer check to assert against.
- **New risks:** A fix that breaks the API health endpoint mid-cycle won't be caught until tip-smoke or until a verifier hits 5xx. Mitigation: verifier already tests adjacent capabilities (`verifier.md:24`), which catches "endpoint X completely dead" within the same cycle. Real risk: a cycle 2 fix breaks something cycle 1 didn't touch and tip-smoke is the first signal — the team loses the in-cycle visibility. This is an observability regression worth measuring before deleting outright.
- **Verdict:** **SIMPLIFY** (drop per-cycle smoke; keep preflight + tip; drop `smoke-cli-client-new` litter check). One of the highest-confidence simplifications — the audit cited 3 fix commits inside this surface.

---

## F2.2 — `_zero_high_conf_cycles >= 2` no-progress gate

- **Today:** `run.py:149-154`. After every cycle, if `total_actionable == 0 AND state.commits_this_cycle == 0`, increment `_zero_high_conf_cycles`. At 2, exit with `"no-progress"`. Reset to 0 on any commit or actionable finding.
- **Why it exists:** Catches "agent keeps generating zero findings (or all low-conf) and we're spending budget for nothing." Belt-and-suspenders to `_all_tracks_signaled_done` (agent self-signals exhaustion via sentinel) and `max_walltime` (hard ceiling).
- **What's wrong:** Triple coverage of the same exit. `_all_tracks_signaled_done` (`run.py:143-144`) catches the agent saying "I'm done" — which is the agent's own assessment, more accurate than the orchestrator guessing from finding counts. `max_walltime` (`run.py:104-105`) caps wall time. The 2-cycle no-progress gate fires when the agent doesn't signal done but also produces no findings — a narrow case (agent confused, or evaluator-only zero-yield cycle). Round-2 caveat in audit notes: at very long cycle times, faster termination might matter — but in practice cycles are 5-15 min and walltime is 4 hours, so worst-case waste is ~30 min over walltime.
- **The right model — deterministic (delete this gate):** The agent's self-signal IS the right termination — it knows what it just did and can say "exhausted my surface" directly. Walltime is the hard backstop. The 2-cycle counter adds a 3rd, weaker signal that's harder to reason about ("why did we exit no-progress when track B clearly had findings? — oh, they were all low-confidence, so `route()` returned them as review-only, so total_actionable was 0").
- **Concrete redesign:** (1) Delete `state.zero_high_conf_cycles` from `RunState` (`run.py:38`). (2) Delete the gate at `run.py:149-154`. (3) Trust `_all_tracks_signaled_done` + walltime.
- **Complexity removed:** ~8 LOC. One conceptual exit reason. The reset/decrement bookkeeping at line 154 disappears. No test changes — `test_run.py` doesn't cover this path directly.
- **New risks:** If the agent stops signaling done correctly (regression in `evaluator-base.md`'s sentinel discipline), the orchestrator runs to walltime instead of cycle-2-no-progress. Worst case wastes ~3 hours. Mitigation: a single test asserting the evaluator prompt mandates `done reason=` in sentinel.txt — already implicit in the prompt template.
- **Verdict:** **DELETE.** Unambiguous over-engineering — the audit's own caveat ("keep if cycles are slow") doesn't apply here. Cycles are minutes, walltime is hours.

---

## F2.3 — `inventory.generate` pre-computation every run

- **Today:** `inventory.py` (160 LOC). Spawns 4 subprocesses to introspect: CLI commands (Typer-walking script), API endpoints (subprocess `scripts/export_openapi.py`), frontend routes (already pivoted to "agent reads `routes.ts`"), autoresearch programs (filesystem + first-docstring-line). Result written to `run_dir/inventory.md` for evaluator to read.
- **Why it exists:** Give the evaluator agent a fast survey of "what surfaces exist" so it can frame findings as "this CLI command's reproduction is X" without first having to discover it. Bug commit `e3d7537` fixed PYTHONPATH so the subprocess could import `cli.freddy.main`.
- **What's wrong:** (a) The frontend section already self-corrected to "agent reads the file itself" (`inventory.py:107-117`) — this is the right pattern, applied inconsistently. (b) The CLI subprocess (`inventory.py:54-70`) imports `cli.freddy.main` which means the inventory walks the *worktree's* CLI, but the agent could just run `.venv/bin/freddy --help` itself and get authoritative output with zero subprocess complexity. (c) The OpenAPI subprocess writes a temp file (`inventory.py:80, 90`), parses JSON, formats markdown — the agent could `curl http://127.0.0.1:8000/openapi.json` and read it directly. (d) The 30-second + 60-second subprocess timeouts (`inventory.py:58, 84`) and stderr-tail-on-failure handling indicate this surface failed often enough to need defensive code.
- **The right model — agentic (pivot the rest like frontend already did):** Replace the whole file with a single static markdown file `inventory.md` checked into `harness/` that says "Read `freddy --help`, `curl /openapi.json`, `frontend/src/lib/routes.ts`, and `ls autoresearch/*.py` to discover surfaces. The agent runs it once per evaluator invocation, fresh, with full context."
- **Concrete redesign:** (1) Create `harness/INVENTORY.md` with breadcrumbs (~20 lines, reads like the current frontend section but for all 4 surfaces). (2) Delete `inventory.py` entirely. (3) `run.py:72` calls become a `shutil.copy(harness/INVENTORY.md, run_dir/inventory.md)` (~3 LOC) or skip and let the evaluator prompt point at the static file.
- **Complexity removed:** All 160 LOC of `inventory.py`. `_CLI_SCRIPT` Typer-walking literal. PYTHONPATH-fix surface. 4 subprocess timeout/error-handling sites. Probably ~20 LOC of test (no test_inventory.py exists currently — confirms this is also untested today).
- **New risks:** The agent now spends ~30s on each evaluator invocation discovering surfaces instead of reading a precomputed file. With 3 evaluator calls per cycle that's ~90s extra per cycle. Probably acceptable given evaluator calls are 5-15 min total. The bigger risk: if `freddy --help` doesn't list a subcommand, the agent might miss that surface — but the current inventory has the same risk (Typer-walk catches only registered commands).
- **Verdict:** **REDESIGN** (delete + replace with breadcrumb file). High confidence. Frontend pivot already proves the pattern works. This is the audit's strongest "agent can do this faster than we can do it for them" case.

---

## F2.4 — PR-body agent + 200-char floor + template fallback

- **Today:** **The agent does not exist in the current codebase.** PR body is composed deterministically by `review.pr_body` (`review.py:59-79`) — a plain Python function that formats commits + tracks into markdown. No 200-char floor (`engine.py:111-135` the audit cites is `_build_codex_cmd` and friends, not `compose_pr_body`). The cited test `tests/harness/test_engine.py:167-187` is `test_rate_limit_hit_is_exception` and `test_engine_exhausted_is_exception` — unrelated.
- **Why it exists (historically):** The 2026-04-20-001 plan envisioned an agent for richer prose. The greenfield rewrite (`5900b48`) chose deterministic — PR body is a thin wrapper around CommitRecord lists, which the agent has no advantage in formatting.
- **What's wrong:** Nothing — the function is deterministic and works. The audit picked it up from a stale plan or a memory-of-design reference.
- **The right model — deterministic (already shipped):** The current `review.pr_body` is the right shape: it iterates commits, groups by track, lists files + adjacent_checked, scrubs secrets via `_scrub`. ~20 LOC of straightforward formatting.
- **Concrete redesign:** None. Optional polish: the per-commit `summary` line is whatever the evaluator wrote in the finding's YAML front-matter; if those are sometimes ugly, scrub them in `_scrub` or normalize in `Finding.from_block`. Not pressing.
- **Complexity removed:** Nothing — this code is already minimal.
- **New risks:** None.
- **Verdict:** **DELETE (audit item is obsolete).** Note: the modified `harness/prompts/fixer.md` and `verifier.md` mentioned in `git status` are NOT pr-body prompts — those are the fixer's "save patch" addition (`fixer.md:55-62`) and the verifier's read-only enforcement (`verifier.md:5`). The new `harness/prompts/pr-body.md` referenced in git status doesn't actually exist on disk (`ls harness/prompts/` shows no such file).

---

## F2.5 — `Verdict.parse` strict 'verified' string matching

- **Today:** `engine.py:69-85`. Reads `verdict_path` YAML, calls `verdict_str = str(data.get("verdict", "")).strip()`, sets `verified=(verdict_str == "verified")`. Anything else — including `verdict: pass`, `verdict: OK`, `verdict: ✓`, `verdict: verified-with-notes` — yields `verified=False`.
- **Why it exists:** The verifier prompt (`verifier.md:32`) hard-spells `verdict: verified | failed`. Strict match enforces that the agent followed the contract. Loose matching invites the agent to drift toward "verified-with-caveats" → "verified-mostly" → never-failing.
- **What's wrong:** Brittle envelope check on the wrong axis. The agent can correctly verify a fix and write `verdict: pass` (synonym), and the orchestrator throws away a real green light. Round-3 finding cites `✓` and other synonyms as plausible. Inverse risk: if agents start adding qualifier strings ("verified-with-notes"), strict match silently fails — the operator sees `verified=False, reason=verified-with-notes` and has to debug.
- **The right model — hybrid (deterministic with a small accept-list):** Accept the prompted contract (`verified`) plus an explicit small whitelist of prompt-stable synonyms. Reject everything else. This is "agent contract enforcement with a paper-cut allowance," not "let LLM decide what verified means."
- **Concrete redesign:** (1) Define `_VERIFIED_TOKENS = {"verified", "pass", "passed", "ok"}` adjacent to `Verdict`. (2) `verified=(verdict_str.lower() in _VERIFIED_TOKENS)`. (3) Don't accept "verified-with-notes" or anything containing additional qualifiers — strict membership only. (4) Update `verifier.md:27` to say "use one of: verified | pass | failed" so the contract is loosened explicitly, not by accident.
- **Complexity removed:** Net zero — adds ~3 LOC (set + membership check) but eliminates a class of false-rollback bug. The bigger value is the *prompt* loosening, not the parser change.
- **New risks:** Drift: 6 months from now someone adds `verified-with-caveats` to the prompt and the gate stops firing. Mitigation: a test asserting `_VERIFIED_TOKENS` is exactly the documented set; updating it requires a test change.
- **Verdict:** **SIMPLIFY** (small, defensive — accept a 2-3 token whitelist; loosen the prompt accordingly). Low priority, low risk, immediately removes a class of paper-cut rollbacks.

---

## F2.6 — `_TRANSIENT_PATTERNS` substring matches

- **Today:** `engine.py:31-37`. Tuple of substrings — `"429"`, `"stream disconnected"`, `"Reconnecting"`, `"overloaded"`, `"rate limit"`, `"503"`, `"502"`, `"API Error: 5"`, `"Internal server error"`, `'"type":"error"'`. `_is_transient` (line 212) tail-reads 8000 chars and checks `any(pat in tail)`. If transient, retry with backoff (`_RETRY_DELAYS = (5, 30, 120)`).
- **Why it exists:** Agent CLIs (claude, codex) emit transient errors in stderr/streamjson; auto-retry recovers from network blips. Each pattern was added on observation.
- **What's wrong:** (a) The substring `'"type":"error"'` is the audit's named false-positive — it matches benign JSON containing that fragment (e.g., the agent's own stream-json that happens to mention an error type). (b) `"429"` matches any line with that 3-digit substring, including legitimate timestamps `1234295` or status codes in unrelated test output. (c) `"API Error: 5"` is a prefix-match for any 5xx and would falsely match `API Error: 5xx documented in section 4.5`. (d) The 8 KB tail is fine for length but doesn't structure-parse — JSON events on adjacent lines aren't disambiguated from prose.
- **The right model — deterministic (proper JSON parse for stream events; substring only for prose):** The same engine.py already has `parse_rate_limit` (line 158) which does the right thing — line-by-line JSON parse, only counts `data.get("type") == "rate_limit_event"`. Apply the same shape to error events: parse stream-json lines, only count `type=="error"`. Keep substring matches for codex's prose stderr (codex doesn't speak stream-json).
- **Concrete redesign:** (1) Add `_parse_error_event(log_path)` analogous to `parse_rate_limit` — scans tail for JSON lines with `type=="error"`. (2) Remove `'"type":"error"'` from `_TRANSIENT_PATTERNS`. (3) `_is_transient` becomes: prose-substring scan AND `_parse_error_event` returned non-None. (4) Tighten `"API Error: 5"` to `"API Error: 5xx"` or use a regex `\bAPI Error: 5\d\d\b`.
- **Complexity removed:** Replaces one fragile substring with one structured parser (~15 LOC added, matches existing `parse_rate_limit` pattern). Net LOC: roughly even, but eliminates known false-positive class.
- **New risks:** If the JSON event format changes, `_parse_error_event` misses transient errors and the agent fails fast instead of retrying. Mitigation: keep substring fallback for `"stream_error"` text in case the structured parser misses. Test at `test_engine.py:156-164` (`test_is_transient_detects_claude_json_error_event`) needs to keep passing — do via the new structured parser.
- **Verdict:** **SIMPLIFY**. Mirror the existing `parse_rate_limit` pattern. Audit's named false-positive case is real; fix is small and proven.

---

## Methodology notes

I read each cited file in full plus tests, then verified by running `git log -p` on key fix commits (`128b43a`, `771027f`, `ff2f2e4`) and `grep` for the audit's named symbols. Two findings (F1.3 and F2.4) cite functions that don't exist in HEAD — `_capture_patch` and `compose_pr_body` are referenced only in old plan docs and historical run-archive copies under `harness/runs/*/harness/`. The audit picked these from plan-doc grep, not source-code grep. The other 8 findings describe live code accurately.
