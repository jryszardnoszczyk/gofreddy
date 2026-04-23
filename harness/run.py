"""Harness orchestrator. One top-level `run()` that wires every module together.

Parallel fixer/verifier across tracks on a single shared worktree. Per-track
worker threads drain their own scope allowlists; `commit_lock` + `restart_lock`
serialize the two shared resources (git index, backend port).
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from harness import engine, findings as findings_mod, preflight, review, safety, smoke, worktree
from harness import sessions as sessions_mod
from harness.sessions import SessionsFile, SessionRecord

if TYPE_CHECKING:
    from harness.config import Config
    from harness.findings import Finding

log = logging.getLogger("harness.run")


@dataclass
class RunState:
    run_dir: Path
    staging_branch: str
    token: str
    ts: str
    pre_dirty: set[str]
    sessions: SessionsFile
    commits: list[review.CommitRecord] = field(default_factory=list)
    all_findings: list["Finding"] = field(default_factory=list)
    start_ts: float = field(default_factory=time.time)
    commits_this_cycle: int = 0
    graceful_stop_requested: bool = False
    graceful_stop_reason: str = ""
    commit_lock: threading.Lock = field(default_factory=threading.Lock)
    restart_lock: threading.Lock = field(default_factory=threading.Lock)


def _run_dir_for_branch(branch: str, staging_root: Path) -> Path:
    """Derive the run_dir from a harness staging branch name.

    Branch and run_dir share the same timestamp by construction:
        worktree.create/attach_to_branch → branch = f"harness/run-{ts}"
        run() → run_dir = staging_root / f"run-{ts}"
    So `--resume-branch harness/run-<ts>` unambiguously points at the prior run_dir.
    """
    ts = branch.removeprefix("harness/run-")
    return staging_root / f"run-{ts}"


def _resume_starting_cycle(run_dir: Path) -> int:
    """Return the cycle number to resume from (1 if no prior cycles). On resume,
    the orchestrator scans run_dir for the highest existing `track-*/cycle-N`
    directory and picks up at that N. Fresh runs always return 1."""
    max_cycle = 0
    for track_dir in run_dir.glob("track-*"):
        for cycle_dir in track_dir.glob("cycle-*"):
            try:
                n = int(cycle_dir.name.removeprefix("cycle-"))
                max_cycle = max(max_cycle, n)
            except ValueError:
                continue
    return max(max_cycle, 1)


def _viable_resume_id(record: SessionRecord | None, wt_path: Path) -> str | None:
    """Return the session_id if claude can actually resume it, else None.

    A session is viable for `claude --resume` only if:
    1. The record status is 'running' (not 'complete', which means no retry needed,
       or 'failed', which means a fresh invocation is the right choice)
    2. The local JSONL file exists under ~/.claude/projects/<encoded-cwd>/<sid>.jsonl

    Overnight smoke 20260422-224908 exposed the need for #2: 3 fixers silent-hung
    on a subscription rate limit BEFORE claude-CLI could create a JSONL. sessions.json
    still recorded status='running' with their session_ids, so a naive resume would
    pass those IDs to `--resume` → claude CLI errors out on missing JSONL. This
    helper's caller falls back to a fresh invocation (new UUID) when it returns None.
    """
    if not record or record.status != "running":
        return None
    jsonl = sessions_mod.claude_session_jsonl(wt_path, record.session_id)
    if not jsonl.is_file():
        log.info(
            "resume: session %s has no local JSONL at %s — falling back to fresh",
            record.session_id[:8], jsonl,
        )
        return None
    return record.session_id


def _copy_inventory_if_present(wt_path: Path, run_dir: Path) -> None:
    """Copy the checked-in INVENTORY.md breadcrumb into run_dir for evaluator prompts.

    Non-fatal if missing. Older harness branches (cut before commit 5dc860b which
    introduced the INVENTORY.md breadcrumb — refactor/pipeline-simplifications-007)
    don't have the file. Evaluators can still discover the surface via Glob/Grep;
    the inventory is just a head-start. Surfaced when attempting to resume smoke
    20260422-190507 (cut from bc92755, pre-INVENTORY.md) — without this guard the
    whole run crashed on shutil.copy → FileNotFoundError.
    """
    src = wt_path / "harness" / "INVENTORY.md"
    if src.is_file():
        shutil.copy(src, run_dir / "inventory.md")
    else:
        log.warning(
            "inventory source missing at %s — evaluators will run without the "
            "inventory breadcrumb (expected on branches cut before commit 5dc860b)",
            src,
        )


def _detect_agent_commit(wt_path: Path, pre_sha: str) -> str | None:
    """Return the new HEAD sha if the agent advanced HEAD during fix, else None.

    Fixer agents run with `--dangerously-skip-permissions` and Bash access, so
    they CAN run `git commit` directly despite the prompt's "Do not commit"
    instruction (F-c-1-4 in smoke run 20260422-190507 did exactly this). When
    that happens, the orchestrator's scope check + `_commit_fix` are bypassed.
    This helper lets `_process_finding` detect the bypass and either accept the
    commit (if verdict verified + no violations) or reset HEAD to pre_sha
    (if the verdict failed — otherwise an unverified commit stays on the branch
    even after `rollback_track_scope`, which only touches the working tree).
    """
    post_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=wt_path, text=True,
    ).strip()
    return post_sha if post_sha != pre_sha else None


def _pop_orphan_stash(wt_path: Path, finding_id: str) -> None:
    """If the fixer left stash entries behind, attempt to pop and log loudly.

    Fixer agents ran `git stash && <tests> && git stash pop` patterns on the
    shared worktree in smoke run 20260422-190507 (F-a-1-2, F-b-1-3, F-c-1-3).
    When the `<tests>` step exits non-zero with `&&`, the pop is skipped and
    peer tracks' in-flight edits stay stashed — invisible to subsequent fixers
    and to `_commit_fix`'s scope filter. This safety net pops any orphan stash
    post-fix and logs if recovery fails.
    """
    stash_list = subprocess.run(
        ["git", "stash", "list"], cwd=wt_path,
        capture_output=True, text=True, check=False,
    )
    pending = stash_list.stdout.strip()
    if not pending:
        return
    log.warning(
        "finding %s: fixer left stash entries — attempting pop: %s",
        finding_id, pending,
    )
    pop = subprocess.run(
        ["git", "stash", "pop"], cwd=wt_path,
        capture_output=True, text=True, check=False,
    )
    if pop.returncode != 0:
        log.error(
            "finding %s: stash pop FAILED — worktree state unknown: %s",
            finding_id, pop.stderr.strip(),
        )


def _reconstruct_commit_record(
    wt_path: Path, finding: "Finding", sha: str, run_dir: Path,
) -> review.CommitRecord:
    """Rebuild a CommitRecord from an existing commit on the branch.

    Used when the orchestrator didn't create the commit via `_commit_fix` but
    needs to attribute it to a finding anyway:
    - Resume skip: a prior invocation's commit is already on the branch.
    - Agent bypass: the fixer agent committed directly (Fix 2).

    Without this, `state.commits` under-reports and PR body + review.md miss
    real commits (smoke run 20260422-190507 PR body listed 9 fixes when the
    branch had 12).
    """
    files = tuple(subprocess.check_output(
        ["git", "show", "--name-only", "--format=", sha],
        cwd=wt_path, text=True,
    ).strip().splitlines())
    verdict_path = run_dir / "verdicts" / finding.track / f"{finding.id}.yaml"
    verdict = engine.Verdict.parse(verdict_path)
    return review.CommitRecord(
        sha=sha, finding_id=finding.id, summary=finding.summary,
        track=finding.track, files=files,
        reproduction=finding.reproduction,
        adjacent_checked=verdict.adjacent_checked,
    )


def _commit_exists_for_finding(wt_path: Path, finding_id: str) -> bool:
    """Return True iff a `harness: fix <finding_id> — ...` commit is on THIS branch.

    Uses the structured commit message format produced by `_commit_fix`. Called
    during resume to decide which findings are already done and should be skipped.

    **Scoped to `main..HEAD`.** Finding IDs (`F-a-1-1`, etc.) are not globally
    unique — every run starts at `F-a-1-1`. Without scoping, a historical fix
    commit from a previously merged harness run would match and cause this run's
    same-ID finding to be wrongly skipped. Caught during the smoke-e resume at
    run-20260422-190507 when F-a-1-1/2/3 were skipped due to inherited commits
    from a prior merged branch.
    """
    result = subprocess.run(
        ["git", "log", "main..HEAD", "--grep", f"harness: fix {finding_id} ", "--format=%H"],
        cwd=wt_path, capture_output=True, text=True, check=False,
    )
    return bool(result.stdout.strip())


def run(config: "Config") -> int:
    # On --resume-branch, reuse the prior run_dir (deterministically mapped from
    # the branch timestamp) so sessions.json, findings.md, verdicts/, and logs
    # remain continuous. Fresh runs allocate a new run_dir from the current ts.
    if config.resume_branch:
        run_dir = _run_dir_for_branch(config.resume_branch, config.staging_root)
        ts = run_dir.name.removeprefix("run-")
        log.info("resume: reusing run_dir %s", run_dir)
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        run_dir = config.staging_root / f"run-{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "fix-diffs").mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(run_dir / "harness.log")],
    )

    pre_dirty = safety.snapshot_dirty()
    try:
        token = preflight.check_all(config)
    except preflight.PreflightError as exc:
        log.error("preflight: %s", exc)
        return 2

    if config.resume_branch:
        wt = worktree.attach_to_branch(config.resume_branch, config)
    else:
        wt = worktree.create(ts, config)
    sessions = SessionsFile(run_dir / "sessions.json")
    state = RunState(
        run_dir=run_dir, staging_branch=wt.branch, token=token, ts=ts,
        pre_dirty=pre_dirty, sessions=sessions,
    )
    # Share the wall-clock deadline with engine.py so its retry loop can short-circuit
    # when the overall budget is exhausted (fix for smoke-run issue: retries extended
    # the run past max_walltime by 2×).
    engine.set_deadline(state.start_ts + config.max_walltime)

    try:
        _copy_inventory_if_present(wt.path, run_dir)
        smoke.check(wt, config, token)
        subprocess.run(["git", "checkout", state.staging_branch], cwd=wt.path, check=False)
        exit_reason = _cycle_loop(config, wt, state)
        # Fix #12: each post-cycle step runs in its own try/except so one failure
        # doesn't skip the others. Overnight smoke 20260422-224908 crashed here
        # with "backend failed to become healthy" inside restart_backend, which
        # erased the whole post-cycle chain — no summary, no outputs, no resume
        # hint. Critical property: _print_summary ALWAYS runs so the user gets
        # exit_reason + branch name + resume command, even when other steps fail.
        try:
            with state.restart_lock:
                worktree.restart_backend(wt, config)
            tip_smoke_ok = _tip_smoke(wt, config, state)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "post-cycle backend restart or tip-smoke failed: %s — "
                "state.commits + findings still recoverable from run_dir", exc,
            )
            tip_smoke_ok = False
        try:
            _write_outputs(run_dir, state, tip_smoke_ok)
        except Exception:
            log.exception("writing outputs failed — recover manually from run_dir")
        pr_url = None
        if state.commits:
            try:
                pr_url = _push_and_pr(wt, state, run_dir)
            except Exception:
                log.exception("push/PR failed — commits remain on local branch for manual push")
        _print_summary(run_dir, state, exit_reason, pr_url, tip_smoke_ok)
        if state.graceful_stop_requested:
            # Graceful stop is expected behavior (rate limit / transient exhaustion),
            # not a run error — exit 0 with a warning so it's visible but not scary.
            log.warning(
                "graceful stop: %s — to resume: python -m harness --engine %s --resume-branch %s",
                state.graceful_stop_reason, config.engine, state.staging_branch,
            )
        return 0
    except smoke.SmokeError as exc:
        log.error("%s", exc)
        return 3
    except Exception:  # noqa: BLE001
        log.exception("unhandled failure during run")
        return 4
    finally:
        engine.set_deadline(None)  # don't leak across test runs / back-to-back invocations
        if not config.keep_worktree:
            worktree.cleanup(wt)


def _cycle_loop(config: "Config", wt: worktree.Worktree, state: RunState) -> str:
    # On resume, start at the highest cycle directory that already exists so we
    # don't rerun completed cycles from scratch. (Each `track-*/cycle-N` dir is
    # created by the evaluator stage, so the max existing N is the cycle to
    # resume — either already complete per skip logic, or mid-flight.)
    cycle = _resume_starting_cycle(state.run_dir) - 1
    while True:
        if time.time() - state.start_ts > config.max_walltime:
            return "walltime"
        cycle += 1
        state.commits_this_cycle = 0
        log.info("--- cycle %d ---", cycle)

        track_findings = _evaluate_tracks(config, wt, cycle, state.run_dir, state)
        # Append partial findings BEFORE checking graceful_stop — tracks that did
        # complete successfully must still land in review.md for post-run inspection.
        state.all_findings.extend(f for fs in track_findings.values() for f in fs)

        if state.graceful_stop_requested:
            return "graceful-stop"

        if cycle == 1 and all(not fs for fs in track_findings.values()):
            return "zero-first-cycle"

        # Per-track queues of actionable findings, to be drained in parallel.
        per_track_queues: dict[str, list["Finding"]] = {
            t: findings_mod.route(track_findings.get(t, []))[0] for t in config.tracks
        }
        total_actionable = sum(len(q) for q in per_track_queues.values())

        if total_actionable > 0:
            with ThreadPoolExecutor(max_workers=len(config.tracks)) as pool:
                futures = {
                    pool.submit(_process_track_queue, config, wt, per_track_queues[t], state): t
                    for t in config.tracks if per_track_queues[t]
                }
                for fut in as_completed(futures):
                    track = futures[fut]
                    try:
                        fut.result()
                    except Exception as exc:  # noqa: BLE001 — unexpected worker crash
                        log.warning("track %s worker crashed: %s", track, exc)

        # Process findings first, THEN check agent-signaled-done — otherwise agents that signal
        # done in cycle 1 (the common case) would skip the fixer loop entirely.
        if _all_tracks_signaled_done(state.run_dir, cycle):
            return "agent-signaled-done"

        if state.graceful_stop_requested:
            return "graceful-stop"


def _process_track_queue(
    config: "Config", wt: worktree.Worktree, queue: list["Finding"], state: RunState,
) -> None:
    """Drain one track's queue serially. Cross-track parallelism comes from
    this function running in a thread per track."""
    for finding in queue:
        if state.graceful_stop_requested:
            return
        if time.time() - state.start_ts > config.max_walltime:
            log.warning("walltime exceeded — track %s stopping", finding.track)
            return
        log.info("finding %s (track %s): starting fix", finding.id, finding.track)
        t0 = time.time()
        try:
            _process_finding(config, wt, finding, state)
        except (engine.RateLimitHit, engine.EngineExhausted) as exc:
            reason = f"track {finding.track} finding {finding.id}: {exc}"
            # Atomic: set stop state AND clean up partial edits under a single lock.
            # Without this, two tracks rate-limiting near-simultaneously race on
            # the check-then-set of graceful_stop_reason.
            with state.commit_lock:
                state.graceful_stop_requested = True
                if not state.graceful_stop_reason:
                    state.graceful_stop_reason = reason
                worktree.rollback_track_scope(wt, finding.track)
            log.error("graceful stop trigger — track %s finding %s: %s",
                      finding.track, finding.id, exc)
            return
        except Exception as exc:  # noqa: BLE001 — one bad finding must not kill the track
            log.warning("finding %s: unexpected worker error: %s — rolling back and continuing",
                        finding.id, exc)
            with state.commit_lock:
                try:
                    worktree.rollback_track_scope(wt, finding.track)
                except Exception as roll_exc:  # noqa: BLE001
                    log.error("finding %s: rollback also failed: %s", finding.id, roll_exc)
        log.info("finding %s: done in %ds", finding.id, int(time.time() - t0))


def _evaluate_tracks(
    config: "Config", wt: worktree.Worktree, cycle: int, run_dir: Path, state: RunState,
) -> dict[str, list["Finding"]]:
    """Run all track evaluators in parallel. RateLimitHit / EngineExhausted trip
    `state.graceful_stop_requested` so peer tracks that did complete are preserved
    in the returned dict — the orchestrator appends them to `state.all_findings` before
    handling the graceful stop, so they still reach `review.md`.

    Resume: if a track's sentinel + findings already exist on disk, skip the
    evaluator entirely and reuse the stored findings. If the sentinel is absent
    but a `running` session record exists, invoke with `claude --resume <id>`.
    """
    results: dict[str, list["Finding"]] = {t: [] for t in config.tracks}

    def _dispatch(track: str) -> list["Finding"]:
        cycle_dir = run_dir / f"track-{track}" / f"cycle-{cycle}"
        sentinel = cycle_dir / "sentinel.txt"
        findings_md = cycle_dir / "findings.md"
        if sentinel.exists() and findings_md.exists():
            log.info("resume: track %s cycle %d eval already complete — reusing findings",
                     track, cycle)
            return findings_mod.parse(findings_md)
        record = state.sessions.get(f"eval-{track}-c{cycle}")
        resume_id = _viable_resume_id(record, wt.path)
        if resume_id:
            log.info("resume: track %s cycle %d eval resuming session %s",
                     track, cycle, resume_id[:8])
        return engine.evaluate(
            config, track, wt, cycle, run_dir,
            sessions=state.sessions, resume_session_id=resume_id,
        )

    with ThreadPoolExecutor(max_workers=len(config.tracks)) as pool:
        futures = {pool.submit(_dispatch, t): t for t in config.tracks}
        for fut in as_completed(futures):
            track = futures[fut]
            try:
                results[track] = fut.result()
            except (engine.RateLimitHit, engine.EngineExhausted) as exc:
                reason = f"evaluator track {track}: {exc}"
                with state.commit_lock:
                    state.graceful_stop_requested = True
                    if not state.graceful_stop_reason:
                        state.graceful_stop_reason = reason
                log.error("graceful stop during evaluator track=%s: %s", track, exc)
            except Exception as exc:  # noqa: BLE001
                log.warning("evaluator track=%s cycle=%d failed: %s", track, cycle, exc)
    return results


def _all_tracks_signaled_done(run_dir: Path, cycle: int) -> bool:
    for track in ("a", "b", "c"):
        reason = engine.read_sentinel(run_dir / f"track-{track}" / f"cycle-{cycle}" / "sentinel.txt")
        if reason != "agent-signaled-done":
            return False
    return True


def _process_finding(config: "Config", wt: worktree.Worktree, finding: "Finding", state: RunState) -> None:
    # Resume: if a prior run already committed a fix for this finding, skip
    # entirely. Keyed on commit subject (structured by _commit_fix) rather than
    # session status, because a fix can have status=complete in sessions.json
    # but have been rolled back by scope checks — in which case we want to retry.
    if _commit_exists_for_finding(wt.path, finding.id):
        # Reconstruct the CommitRecord so PR body + review.md describe this
        # commit even though THIS invocation didn't create it. Without this,
        # state.commits under-reports on resume (smoke 20260422-190507 bug #4).
        sha = subprocess.check_output(
            ["git", "log", "main..HEAD", "--grep", f"harness: fix {finding.id} ",
             "--format=%H", "-n", "1"],
            cwd=wt.path, text=True,
        ).strip()
        if sha:
            record = _reconstruct_commit_record(wt.path, finding, sha, state.run_dir)
            state.commits.append(record)
            log.info("resume: finding %s already committed %s — reused", finding.id, sha[:7])
        else:
            log.info("resume: finding %s already has commit on branch — skipping", finding.id)
        return

    pre_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=wt.path, text=True).strip()
    # Fix #4: scoped rollback only — don't touch peer tracks' in-flight edits.
    # Under commit_lock because `git checkout --` reads the shared index.
    with state.commit_lock:
        worktree.rollback_track_scope(wt, finding.track)

    fix_record = state.sessions.get(f"fix-{finding.id}")
    fix_resume_id = _viable_resume_id(fix_record, wt.path)
    if fix_resume_id:
        log.info("resume: finding %s fixer resuming session %s", finding.id, fix_resume_id[:8])
    engine.fix(config, finding, wt, state.run_dir,
               sessions=state.sessions, resume_session_id=fix_resume_id)

    # Post-fix safety probes (run before verify so any leftover state is
    # cleaned up first):
    # 1. Did the agent commit directly? (Fix 2 — smoke 20260422-190507 F-c-1-4)
    bypass_sha = _detect_agent_commit(wt.path, pre_sha)
    if bypass_sha:
        log.warning(
            "finding %s: agent committed %s directly (bypassed orchestrator)",
            finding.id, bypass_sha[:7],
        )
    # 2. Did the fixer leave an orphan stash? (Fix 5 — smoke 20260422-190507)
    _pop_orphan_stash(wt.path, finding.id)

    # Fix #1: restart backend BETWEEN fix and verify (not after commit) so the
    # verifier sees the fixer's changes. uvicorn runs without --reload.
    with state.restart_lock:
        worktree.restart_backend(wt, config)

    verify_record = state.sessions.get(f"verify-{finding.id}")
    verify_resume_id = _viable_resume_id(verify_record, wt.path)
    if verify_resume_id:
        log.info("resume: finding %s verifier resuming session %s", finding.id, verify_resume_id[:8])
    verdict = engine.verify(config, finding, wt, state.run_dir,
                            sessions=state.sessions, resume_session_id=verify_resume_id)

    scope_violations = safety.check_scope(wt.path, pre_sha, finding.track) or []
    leak_violations = safety.check_no_leak(state.pre_dirty) or []
    violations = scope_violations + leak_violations

    if verdict.verified and not violations:
        with state.commit_lock:
            commit = _commit_fix(wt, finding, pre_sha, verdict)
            if commit:
                state.commits.append(commit)
                state.commits_this_cycle += 1
            elif bypass_sha:
                # _commit_fix found no in-scope diff because the agent already
                # committed. Synthesize a CommitRecord from the bypass so the
                # fix shows up in state.commits / PR body / review.md.
                record = _reconstruct_commit_record(
                    wt.path, finding, bypass_sha, state.run_dir,
                )
                state.commits.append(record)
                state.commits_this_cycle += 1
                log.info(
                    "finding %s: accepted agent-bypass commit %s",
                    finding.id, bypass_sha[:7],
                )
    else:
        parts = []
        if not verdict.verified:
            parts.append(f"verdict={verdict.reason or 'failed'}")
        if scope_violations:
            parts.append(f"scope={scope_violations}")
        if leak_violations:
            parts.append(f"leak={leak_violations}")
        log.warning("finding %s: rolling back — %s", finding.id, "; ".join(parts) or "unknown")
        # Escalate leaks to ERROR so they're visible separate from ordinary
        # rollback warnings. rollback_track_scope only touches the worktree —
        # main-repo leaked files stay dirty and require manual cleanup.
        if leak_violations:
            log.error(
                "finding %s: LEAK in main repo — manual cleanup required for %s",
                finding.id, leak_violations,
            )
        _capture_patch(wt.path, finding, state.run_dir)
        # If the agent bypassed and we're rolling back, reset HEAD first —
        # otherwise `rollback_track_scope` (working-tree-only) leaves the
        # unverified commit on the branch (smoke 20260422-190507 would have
        # done this if F-c-1-4's verdict had been failed).
        if bypass_sha:
            with state.commit_lock:
                subprocess.run(
                    ["git", "reset", "--hard", pre_sha], cwd=wt.path, check=True,
                )
            log.warning(
                "finding %s: reset HEAD to %s to undo agent-bypass commit",
                finding.id, pre_sha[:7],
            )
        # rollback_track_scope does `git reset HEAD --` + `git checkout --`, both of
        # which acquire `.git/index.lock`. Serialize with peers' commits.
        with state.commit_lock:
            worktree.rollback_track_scope(wt, finding.track)


def _capture_patch(wt_path: Path, finding: "Finding", run_dir: Path) -> None:
    """Capture the fixer's working-tree diff for post-mortem review.

    Runs after fixer exits, before rollback. Writes to run_dir (absolute,
    outside the worktree) so the patch file itself never appears in the
    worktree's git status and can't trip scope checks.

    Uses `git add -N` to surface untracked files in the diff, then resets
    the intent-to-add markers so the working tree is unchanged.
    """
    out_dir = run_dir / "fix-diffs" / finding.track
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{finding.id}.patch"
    subprocess.run(
        ["git", "add", "-N", "--", "."], cwd=wt_path, check=False, capture_output=True,
    )
    diff = subprocess.run(
        ["git", "diff", "HEAD", "--no-color"],
        cwd=wt_path, capture_output=True, text=True, check=False,
    ).stdout
    subprocess.run(
        ["git", "reset", "--", "."], cwd=wt_path, check=False, capture_output=True,
    )
    out_path.write_text(diff, encoding="utf-8")


def _commit_fix(
    wt: worktree.Worktree, finding: "Finding", pre_sha: str, verdict: engine.Verdict,
) -> review.CommitRecord | None:
    # Fix #3: under parallel execution, only stage files within this track's allowlist.
    # Peer tracks' in-flight dirty files must not bleed into this commit.
    pattern = safety.SCOPE_ALLOWLIST[finding.track]
    all_changes = safety.working_tree_changes(wt.path)
    files = tuple(f for f in all_changes if pattern.match(f))
    if not files:
        log.info("finding %s: no in-scope diff — skipping commit", finding.id)
        return None
    summary_line = finding.summary.splitlines()[0] if finding.summary else finding.id
    subprocess.run(["git", "add", "--", *files], cwd=wt.path, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"harness: fix {finding.id} — {summary_line}"],
        cwd=wt.path, check=True,
    )
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=wt.path, text=True).strip()
    log.info("finding %s: committed %s", finding.id, sha[:7])
    return review.CommitRecord(
        sha=sha, finding_id=finding.id, summary=finding.summary, track=finding.track,
        files=files, reproduction=finding.reproduction, adjacent_checked=verdict.adjacent_checked,
    )


def _tip_smoke(wt: worktree.Worktree, config: "Config", state: RunState) -> bool:
    extra: list[smoke.Check] = []
    for commit in state.commits:
        repro = (commit.reproduction or "").strip()
        # Best-effort: only executable-looking single-line reproductions become extra checks.
        # Multi-line prose reproductions require a human to verify; skip rather than shell-exec them.
        if repro and "\n" not in repro and any(repro.startswith(tok) for tok in
                                                (".venv/", "curl", "npm", "python", "node", "freddy", "git", "gh")):
            extra.append(smoke.Check(
                id=f"repro-{commit.finding_id}",
                type="shell",
                raw={"command": repro, "expected_exit": 0},
            ))
    try:
        smoke.check(wt, config, state.token, extra_checks=extra)
        return True
    except smoke.SmokeError as exc:
        log.warning("tip-smoke failed: %s", exc)
        return False


def _write_outputs(run_dir: Path, state: RunState, tip_smoke_ok: bool) -> None:
    review_md = review.compose(run_dir, state.commits, state.all_findings, tip_smoke_ok)
    (run_dir / "review.md").write_text(review_md, encoding="utf-8")
    if state.commits:
        (run_dir / "pr-body.md").write_text(
            review.pr_body(run_dir, state.commits, tip_smoke_ok), encoding="utf-8",
        )


def _push_and_pr(wt: worktree.Worktree, state: RunState, run_dir: Path) -> str | None:
    push = subprocess.run(
        ["git", "push", "--set-upstream", "origin", state.staging_branch],
        cwd=wt.path, capture_output=True, text=True, check=False,
    )
    if push.returncode != 0:
        log.error(
            "git push failed — pr-body preserved at %s\n  manual: git -C %s push --set-upstream origin %s && "
            "gh pr create --body-file %s --head %s",
            run_dir / "pr-body.md", wt.path, state.staging_branch, run_dir / "pr-body.md", state.staging_branch,
        )
        return None

    pr_body_path = run_dir / "pr-body.md"
    title = f"harness: run {state.ts} — {len(state.commits)} fixes"
    gh = subprocess.run(
        ["gh", "pr", "create", "--title", title, "--body-file", str(pr_body_path), "--head", state.staging_branch],
        cwd=wt.path, capture_output=True, text=True, check=False,
    )
    if gh.returncode != 0:
        log.error(
            "gh pr create failed — pr-body preserved at %s; manual: gh pr create --body-file %s --head %s\n%s",
            pr_body_path, pr_body_path, state.staging_branch, gh.stderr.strip(),
        )
        return None
    return gh.stdout.strip().splitlines()[-1] if gh.stdout.strip() else None


def _print_summary(run_dir: Path, state: RunState, exit_reason: str, pr_url: str | None, tip_smoke_ok: bool) -> None:
    by_cat: dict[str, int] = {}
    for f in state.all_findings:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
    duration = int(time.time() - state.start_ts)
    if pr_url:
        pr_line = pr_url
    elif not state.commits:
        pr_line = "no PR — zero verified fixes"
    else:
        pr_line = "push/create failed — see log"
    print("\n".join([
        f"commits: {len(state.commits)}",
        f"findings: {sum(by_cat.values())} ({', '.join(f'{k}={v}' for k, v in sorted(by_cat.items()))})",
        f"tip-smoke: {'OK' if tip_smoke_ok else 'FAILED'}",
        f"pr: {pr_line}",
        f"exit_reason: {exit_reason}",
        f"duration: {duration}s",
        f"run_dir: {run_dir}",
        f"branch: {state.staging_branch} (preserved for possible resume; prune accumulated "
        f"branches with: git branch | grep 'harness/run-' | xargs git branch -D)",
    ]), file=sys.stderr)
