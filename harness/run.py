"""Harness orchestrator. One top-level `run()` that wires every module together.

Parallel fixer/verifier across tracks on a single shared worktree. Per-track
worker threads drain their own scope allowlists; `commit_lock` + `restart_lock`
serialize the two shared resources (git index, backend port).
"""
from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from harness import engine, findings as findings_mod, inventory, preflight, review, safety, smoke, worktree

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
    commits: list[review.CommitRecord] = field(default_factory=list)
    all_findings: list["Finding"] = field(default_factory=list)
    start_ts: float = field(default_factory=time.time)
    zero_high_conf_cycles: int = 0
    commits_this_cycle: int = 0
    graceful_stop_requested: bool = False
    graceful_stop_reason: str = ""
    commit_lock: threading.Lock = field(default_factory=threading.Lock)
    restart_lock: threading.Lock = field(default_factory=threading.Lock)


def run(config: "Config") -> int:
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
    state = RunState(run_dir=run_dir, staging_branch=wt.branch, token=token, ts=ts, pre_dirty=pre_dirty)
    # Share the wall-clock deadline with engine.py so its retry loop can short-circuit
    # when the overall budget is exhausted (fix for smoke-run issue: retries extended
    # the run past max_walltime by 2×).
    engine.set_deadline(state.start_ts + config.max_walltime)

    try:
        inventory.generate(wt.path, run_dir / "inventory.md")
        smoke.check(wt, config, token)
        subprocess.run(["git", "checkout", state.staging_branch], cwd=wt.path, check=False)
        exit_reason = _cycle_loop(config, wt, state)
        with state.restart_lock:
            worktree.restart_backend(wt, config)
        tip_smoke_ok = _tip_smoke(wt, config, state)
        _write_outputs(run_dir, state, tip_smoke_ok)
        pr_url = _push_and_pr(wt, state, run_dir) if state.commits else None
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
    cycle = 0
    while True:
        if time.time() - state.start_ts > config.max_walltime:
            return "walltime"
        cycle += 1
        state.commits_this_cycle = 0
        smoke.check(wt, config, state.token)
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

        if total_actionable == 0 and state.commits_this_cycle == 0:
            state.zero_high_conf_cycles += 1
            if state.zero_high_conf_cycles >= 2:
                return "no-progress"
        else:
            state.zero_high_conf_cycles = 0


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
    handling the graceful stop, so they still reach `review.md`."""
    results: dict[str, list["Finding"]] = {t: [] for t in config.tracks}
    with ThreadPoolExecutor(max_workers=len(config.tracks)) as pool:
        futures = {pool.submit(engine.evaluate, config, t, wt, cycle, run_dir): t for t in config.tracks}
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
    pre_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=wt.path, text=True).strip()
    # Fix #4: scoped rollback only — don't touch peer tracks' in-flight edits.
    # Under commit_lock because `git checkout --` reads the shared index.
    with state.commit_lock:
        worktree.rollback_track_scope(wt, finding.track)

    engine.fix(config, finding, wt, state.run_dir)

    # Fix #1: restart backend BETWEEN fix and verify (not after commit) so the
    # verifier sees the fixer's changes. uvicorn runs without --reload.
    with state.restart_lock:
        worktree.restart_backend(wt, config)

    verdict = engine.verify(config, finding, wt, state.run_dir)

    scope_violations = safety.check_scope(wt.path, pre_sha, finding.track) or []
    leak_violations = safety.check_no_leak(state.pre_dirty) or []
    violations = scope_violations + leak_violations

    if verdict.verified and not violations:
        with state.commit_lock:
            commit = _commit_fix(wt, finding, pre_sha, verdict)
            if commit:
                state.commits.append(commit)
                state.commits_this_cycle += 1
    else:
        parts = []
        if not verdict.verified:
            parts.append(f"verdict={verdict.reason or 'failed'}")
        if scope_violations:
            parts.append(f"scope={scope_violations}")
        if leak_violations:
            parts.append(f"leak={leak_violations}")
        log.warning("finding %s: rolling back — %s", finding.id, "; ".join(parts) or "unknown")
        _capture_patch(wt.path, finding, state.run_dir)
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
    ]), file=sys.stderr)
