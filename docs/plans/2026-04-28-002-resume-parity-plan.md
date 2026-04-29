---
status: shipped (with caveats — see Status section)
created: 2026-04-28
shipped: 2026-04-29
owner: tbd
priority: P1
context: 5+ killed evolution runs on 2026-04-27/28 burned ~3hr of opus tokens because evolve.py + variant session loop have no resume. Shipped a minimal resume in PR-pending (--resume-variant flag, on-disk artifact keyed) but full harness-parity is deferred to this plan.
---

## Status (2026-04-29)

PR #38 (`71bacca`) shipped Sections 1, 3, 6, 7 in full plus partial Sections 2 + 5. Follow-up commit on 2026-04-29 closed Section 4 (claude per-fixture session-id capture in `harness/agent.py:run_agent_session`). Second follow-up added 13 missing tests (Section 4 sentinel logic + acceptance criterion #1 mocked end-to-end). Caveats remaining:

- **Section 2 (codex pre-mint):** verified empirically on 2026-04-29 that `codex exec -c experimental.session_id="<uuid>"` is silently ignored — codex generates its own internal thread id (`019dd960-…`) regardless of the override, and no rollout JSONL is created at the operator-supplied UUID path. Pre-mint genuinely not viable. Codex meta-agent resume falls through to fresh on kill. `codex_session_jsonl()` helper exists in `autoresearch/sessions.py` but is not yet wired into post-spawn rollout detection (would require timestamp-based correlation since codex never exposes its internal sid back to the parent process). Workaround: when codex meta dies, the existing on-disk artifacts (variant_dir + .session_ids.json record marked `failed`) still let `--resume-variant` pick up at search-scoring or finalize without redoing the meta-template.
- **Section 5 (`--resume-fixture` semantics):** plan said "pick up mid-fixture-session"; shipped as "force-rerun one fixture from scratch (clear sentinel + wipe session_dir)". Actual mid-fixture conversation resume now works for claude via Section 4's sentinel — the flag's intent is honored when the sentinel + JSONL are intact, the rerun behavior kicks in as a forced-restart escape hatch.
- **End-to-end live verification:** acceptance criterion #1 ("conversation continues from where it stopped") now has a mocked end-to-end test (`test_resume_meta_agent_invokes_claude_resume_with_continue_prompt`) that asserts `_resume_meta_agent` forwards `resume_sid` (not `session_id`), the prompt is a short continue message (not full meta-template), and the SessionsFile record transitions to `complete`. Live validation against a real claude subprocess still pending the next operator-driven evolution run.

# Resume parity for evolve.py + variant session runner

Mirror `harness/run.py`'s session-id-checkpoint pattern across the autoresearch evolution loop AND the per-variant session runner so any kill (SIGINT, SIGTERM, OOM, crash) can resume without re-spending agent tokens.

## What the harness already does (reference, don't reinvent)

- `harness/sessions.py` — `SessionsFile` (atomic JSON), `SessionRecord`, `claude_session_jsonl(wt_path, session_id)` for verifying resume viability.
- `harness/engine.py:_build_claude_cmd` — `--session-id <uuid>` on fresh, `--resume <session_id>` + short "continue" prompt on resume.
- `harness/run.py:_viable_resume_id` — returns session_id only if `~/.claude/projects/<encoded>/<sid>.jsonl` exists; falls back to fresh otherwise (catches the silent-hang case where claude rate-limited before creating its JSONL).
- `harness/run.py` cycle pickup at lines 1078-1084 (eval), 1167-1206 (fix), 810-815 (verify) — per-artifact skip-if-already-done.
- `harness/cli.py:25-28` — `--resume-branch`, `--fixers-only` flags.

## What ships now (already done in PR-pending — minimal viable)

- `autoresearch/evolve.py`: `--resume-variant <id>` flag, `_resume_search_scored()` (scores.json composite>0 check), `_resume_parent_id()` (lineage.jsonl lookup), resume branch in `cmd_run()`. Picks up at search-scoring or finalize. Skips meta-agent if variant_dir already exists. ~60 lines.
- This handles "kill happens during search-scoring or finalize" — the most common case observed in v3-v8.

## What's deferred to this plan (full parity, this PR)

### 1. SessionsFile abstraction (port from harness/)

- New module `autoresearch/sessions.py` — copy `harness/sessions.py` near-verbatim.
- Keep the same `SessionRecord` shape (`agent_key`, `session_id`, `engine`, `status`, timestamps).
- Atomic JSON writes (tmp + os.replace), threading.Lock for concurrency.
- Sessions file location: `archive/<variant_id>/.session_ids.json` (per-variant, not per-run, since evolve.py treats each variant as the unit of work).

### 2. Instrument the meta-agent spawn

- `evolve.py:_build_meta_command` — add `--session-id <uuid>` for claude, `-c experimental.session_id="<uuid>"` for codex (verify codex CLI supports this; if not, skip codex resume and document).
- `evolve.py:_run_meta_agent_once` — call `sessions.begin(agent_key="meta-{variant_id}", session_id=<uuid>, engine=<backend>)` BEFORE Popen; call `sessions.finish(...)` after exit.
- Resume path in `cmd_run`: if `variant_dir/.session_ids.json` has a `running` record for `meta-{variant_id}` AND `_viable_resume_id` returns the sid, re-invoke with `claude --resume <sid>` + short continue prompt instead of full meta-template.

### 3. Instrument the program critic spawn

- `autoresearch/program_prescription_critic.py:_build_critic_cmd` — same `--session-id` instrumentation.
- The recurring `[program_prescription_critic] WARN: claude exit=1` from v3-v9 will become recoverable.

### 4. Instrument the variant session runner (per-fixture)

- `archive/<variant>/run.py` — when claude/codex spawned per fixture, capture session-id and store at `archive/<variant>/sessions/<domain>/<client>/.session_id`.
- Resume path in `evaluate_variant.py:_run_and_score_fixture` — if `session_dir/.session_id` exists AND `_viable_resume_id` says yes AND structural artifacts incomplete, resume with `--resume <sid>`.
- Per-fixture skip-if-already-done: if structural artifacts exist (digest.md OR optimized/*.md OR brief.md per domain) AND scores already present, skip the whole fixture.

### 5. Resume CLI flags

- `--resume-variant <id>` (already done) — picks up at search-scoring or finalize.
- `--resume-fixture <variant>:<fixture_id>` (NEW) — picks up mid-fixture-session, useful when one fixture in a 3-parallel batch dies.
- `--fixtures-only` (NEW, mirrors `--fixers-only`) — re-run only the eval/score phase, skip variant agent.

### 6. Graceful-stop exit hint

- `evolve.py:_sigalrm_handler` (and SIGINT/SIGTERM) — before exit, print exact resume command:
  ```
  ./autoresearch/evolve.sh run --lane geo --candidates-per-iteration 1 --iterations 1 \
    --resume-variant v013
  ```
- Mirrors `harness/run.py:526-528`.

### 7. Tests

- `tests/autoresearch/test_resume_evolve.py` — at minimum:
  - `_resume_search_scored` true when scores.json has composite>0
  - `_resume_search_scored` false on stale-clone scores.json (composite=0)
  - `_resume_parent_id` reads lineage.jsonl correctly
  - SessionsFile begin/finish/reload roundtrip (port from `tests/harness/test_sessions.py`)
  - `_viable_resume_id` returns None when JSONL missing (claude rate-limit-before-create case)
  - End-to-end: kill an evolve run mid-meta-agent, re-invoke with --resume-variant, verify it resumes the conversation (mock the claude subprocess)
- Skip codex resume tests if codex CLI doesn't support session reattach.

## Out of scope for this plan

- Multi-generation resume (resume an interrupted `--iterations 5` run from generation 3). Single-variant resume covers 90%+ of operator pain.
- Promotion/finalize resume mid-rollback. The agentic Promotion+Rollback bookkeeping in evolve_ops already has its own caching via `finalize_result.json` which works.
- Holdout fixture-level resume — covered by the per-fixture session-id instrumentation above when shared with the variant session runner.

## Estimated size

- ~6 files touched
- ~400-600 lines net (most of it in `autoresearch/sessions.py` ported from harness/)
- ~3-5 hours including tests
- Recommend a single PR with all 7 sections, since they're a coherent system

## Acceptance criteria

1. Kill an evolve run mid-meta-agent → `--resume-variant <id>` re-invokes claude with `--resume <sid>` + short continue prompt; conversation continues from where it stopped.
2. Kill mid-fixture-session → resume picks up that single fixture without redoing the others.
3. Kill mid-finalize → resume skips already-finalized fixtures via existing `finalize_result.json` cache (no new code needed; just verify the path works).
4. SIGINT cleanly logs which session_ids are still `running` and prints the exact resume command.
5. tests/autoresearch/test_resume_evolve.py passes; existing tests still pass.

## Cross-references

- harness/sessions.py + harness/run.py:_viable_resume_id (the proven pattern to mirror)
- PR-pending (the minimal `--resume-variant` shipped today)
- Memory: `feedback-show-prs-before-merge.md` applies — full-parity PR ships with operator review before merge.
