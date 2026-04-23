"""Harness orchestrator. One top-level `run()` that wires every module together.

Parallel fixer/verifier across tracks on a single shared worktree. Per-track
worker threads drain their own scope allowlists; `commit_lock` + `restart_lock`
serialize the two shared resources (git index, backend port).
"""
from __future__ import annotations

import logging
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
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
class _WorkerPool:
    """Bounded pool of idle worker worktrees.

    `acquire()` blocks on `available` until a worker is free. Workers are
    returned via `release()` after each finding. The staging worktree is
    NOT a member of the pool — it's held by the orchestrator for cherry-pick
    merges + tip-smoke.
    """
    workers: list["worktree.Worktree"]
    available: "queue.Queue[worktree.Worktree]" = field(init=False)

    def __post_init__(self) -> None:
        self.available = queue.Queue()
        for w in self.workers:
            self.available.put(w)

    def acquire(self) -> "worktree.Worktree":
        return self.available.get()

    def release(self, wt: "worktree.Worktree") -> None:
        self.available.put(wt)


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
    no_op_fixers: list[str] = field(default_factory=list)
    start_ts: float = field(default_factory=time.time)
    commits_this_cycle: int = 0
    graceful_stop_requested: bool = False
    graceful_stop_reason: str = ""
    # Serializes cherry-pick merges onto the staging worktree + mutations to the
    # shared run state (state.commits/no_op_fixers/graceful_stop_*). Per-finding
    # workers each own an isolated worktree + backend, so no lock is needed for
    # their fix/verify/commit-to-own-branch sequence; the lock ONLY covers the
    # narrow cherry-pick-onto-staging window + the result-collection writes.
    staging_lock: threading.Lock = field(default_factory=threading.Lock)
    # `commit_lock` + `restart_lock` are legacy aliases preserved for tests that
    # predate the worker pool. Single-worker mode (max_workers=1) uses the
    # staging worktree as a worker, reverting to the old shared-state model
    # where these locks had meaning. Under the pool model both aliases point
    # at the same staging_lock.
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


def _warn_if_vite_stale(config: "Config", wt_path: Path) -> None:
    """Warn if Vite dev server is serving content from elsewhere than this worktree.

    Bug #18: the Vite dev server on :5173 is assumed pre-started by the operator.
    If it's rooted at the main repo (or another worktree), frontend fixer edits
    in this worktree are invisible to verifier Playwright probes → spurious
    rollbacks. Smoke 20260422-224908 F-c-1-3 rolled back this way. Full Vite
    lifecycle management is out of scope (architectural); this check is
    best-effort and advisory only.
    """
    served_url = config.frontend_url.rstrip("/") + "/src/main.tsx"
    wt_main = wt_path / "frontend" / "src" / "main.tsx"
    if not wt_main.is_file():
        return  # no frontend surface in this worktree
    try:
        with urllib.request.urlopen(served_url, timeout=2) as resp:  # noqa: S310
            served = resp.read(2048).decode("utf-8", errors="replace")
    except Exception:
        return  # Vite unreachable is preflight's problem, not ours
    wt_first = wt_main.read_text(encoding="utf-8")[:2048]
    # Dev-server may inject HMR + transform modules — substring check on a
    # distinctive worktree-local snippet is more robust than exact match.
    snippet = wt_first[:120].strip()
    if snippet and snippet not in served:
        log.warning(
            "vite on %s does not appear to serve this worktree's frontend — "
            "frontend fixes may be invisible to verifier. "
            "Restart vite from %s/frontend to fix.",
            config.frontend_url, wt_path,
        )


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


def _detect_agent_commit(wt_path: Path, pre_sha: str, finding_id: str) -> str | None:
    """Return the new HEAD sha if HEAD advanced AND any commit in pre_sha..HEAD
    is attributable to THIS finding (agent bypass or our own _commit_fix), else
    None.

    Track-awareness is load-bearing: under parallel execution, peer tracks commit
    legitimately during this track's fix phase, advancing HEAD. Without checking
    commit subjects, we'd wrongly treat any advance as "this track's agent
    bypass" and the rollback path would `git reset --hard pre_sha`, destroying
    peer tracks' legitimate commits. Smoke run 20260422-224908 lost F-b-1-2's
    verified commit (319acf8) exactly this way — F-c-1-2's pre_sha was older
    than F-b-1-1 and F-b-1-2, so F-c-1-2's "bypass" rollback wiped both.

    `_commit_fix` writes subjects of the form `harness: fix <finding.id>@c<n> — ...`
    so a commit attributable to THIS finding must contain `finding.id`. We scan
    ALL commits in pre_sha..HEAD (not just HEAD) because a fixer agent that
    commits twice — e.g. scaffolding + real fix — would otherwise defeat the
    check when only the newest subject is inspected.

    Caller must hold `commit_lock` so peer `_commit_fix` cannot interleave between
    the rev-parse and the log.
    """
    post_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=wt_path, text=True,
    ).strip()
    if post_sha == pre_sha:
        return None
    subjects = subprocess.check_output(
        ["git", "log", f"{pre_sha}..HEAD", "--format=%s"],
        cwd=wt_path, text=True,
    ).splitlines()
    for subj in subjects:
        if finding_id in subj:
            return post_sha
    # Every commit in the range belongs to a peer finding — not this track's bypass.
    return None


def _clean_main_repo_leaks(main_repo: Path, leaked_paths: list[str]) -> None:
    """Delete fixer-originated leaked files from the main repo after rollback.

    Called only on the rollback path with `leak_actionable` — check_no_leak
    pre-filters these to paths (a) matching the fixer-reachable regex AND
    (b) absent from the pre-run dirty snapshot. So these files did not exist
    when the run started; they were created by a fixer that wrote outside
    its worktree. Safe to delete.

    The worktree's `rollback_track_scope` handles the worktree; this handles
    the main repo, where untracked files persist across `git reset --hard`
    and pollute the next finding's dirty snapshot.

    Errors are logged, not raised — best-effort cleanup must not crash the run.
    """
    for rel in leaked_paths:
        target = main_repo / rel
        try:
            if target.is_symlink() or target.is_file():
                target.unlink(missing_ok=True)
            elif target.is_dir():
                shutil.rmtree(target, ignore_errors=False)
        except OSError as exc:
            log.warning("leak cleanup failed for %s: %s", rel, exc)


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


def _commit_exists_for_finding(wt_path: Path, finding_id: str, cycle: int) -> bool:
    """Return True iff a `harness: fix <finding_id>@c<cycle> — ...` commit is on THIS branch.

    Uses the structured commit message format produced by `_commit_fix`. Called
    during resume to decide which findings are already done and should be skipped.

    **Scoped to `main..HEAD`.** Finding IDs (`F-a-1-1`, etc.) are not globally
    unique — every run starts at `F-a-1-1`. Without scoping, a historical fix
    commit from a previously merged harness run would match and cause this run's
    same-ID finding to be wrongly skipped. Caught during the smoke-e resume at
    run-20260422-190507 when F-a-1-1/2/3 were skipped due to inherited commits
    from a prior merged branch.

    **Cycle-qualified.** Evaluators restart finding numbering from 1 each cycle,
    so `F-c-1-5` in cycle 1 and `F-c-1-5` in cycle 2 are distinct findings. The
    `@c<cycle>` stamp in the commit subject keeps them separable; a substring
    match on just `F-c-1-5` would wrongly skip cycle 2's finding when cycle 1's
    was already committed (observed as a risk in run-20260422-224908 where
    cycle-2 produced a `F-c-1-5` that happened not to collide by luck).
    """
    result = subprocess.run(
        ["git", "log", "main..HEAD",
         "--grep", f"harness: fix {finding_id}@c{cycle} ",
         "--fixed-strings", "--format=%H"],
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
    # Bug #19: harness.log appends across resumes; emit a boundary marker so
    # readers (and grep-by-time) can distinguish interleaved invocations.
    log.info("========== invocation ts=%s pid=%d resume=%s ==========",
             ts, os.getpid(), bool(config.resume_branch))

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
    # Build worker pool for fix+verify parallelism. Staging (wt above) stays
    # the orchestrator-held worktree where cherry-picks land and evaluators
    # run. Workers are separate worktrees, each with its own backend port.
    # When max_workers==1, pool is None and the staging worktree plays the
    # worker role (back-compat single-worker mode).
    pool: "_WorkerPool | None" = None
    workers: list[worktree.Worktree] = []
    if config.max_workers > 1:
        workers = worktree.create_workers(ts, config, state.staging_branch)
        pool = _WorkerPool(workers=workers)
        log.info("worker pool ready: %d workers on ports %d..%d",
                 len(workers), workers[0].backend_port, workers[-1].backend_port)
    else:
        log.info("single-worker mode (max_workers=1) — staging doubles as worker")

    # Share the wall-clock deadline with engine.py so its retry loop can short-circuit
    # when the overall budget is exhausted.
    engine.set_deadline(state.start_ts + config.max_walltime)

    try:
        _copy_inventory_if_present(wt.path, run_dir)
        _warn_if_vite_stale(config, wt.path)
        smoke.check(wt, config, token)
        subprocess.run(["git", "checkout", state.staging_branch], cwd=wt.path, check=False)
        exit_reason = _cycle_loop(config, wt, pool, state)
        # Fix #12: each post-cycle step runs in its own try/except so one failure
        # doesn't skip the others. Overnight smoke 20260422-224908 crashed here
        # with "backend failed to become healthy" inside restart_backend, which
        # erased the whole post-cycle chain — no summary, no outputs, no resume
        # hint. Critical property: _print_summary ALWAYS runs so the user gets
        # exit_reason + branch name + resume command, even when other steps fail.
        try:
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
        # Tear down workers first (they symlink into .venv/node_modules inside staging).
        # Order matters for git worktree bookkeeping: each worker must be `git worktree remove`'d
        # before its branch is pruned, else the ref becomes orphaned.
        if not config.keep_worktree:
            for w in workers:
                try:
                    worktree.cleanup(w)
                except Exception as exc:  # noqa: BLE001
                    log.warning("worker %d cleanup failed: %s", w.worker_id, exc)
            worktree.cleanup(wt)


def _cycle_loop(
    config: "Config", staging_wt: worktree.Worktree, pool: "_WorkerPool | None",
    state: RunState,
) -> str:
    """Drive evaluate → fix-verify → merge cycles until a termination condition.

    Evaluators run in parallel (one per track) against the STAGING worktree's
    backend — they're read-only so sharing is fine. The actionable findings
    across all tracks go into a single global queue, drained by N parallel
    WORKER worktrees (each with its own backend port). Verified fixes land on
    worker branches and are cherry-picked onto staging under `state.staging_lock`.

    When `pool is None` (max_workers == 1), the staging worktree plays the
    worker role — back-compat with the original single-worktree model.
    """
    cycle = _resume_starting_cycle(state.run_dir) - 1
    while True:
        if time.time() - state.start_ts > config.max_walltime:
            return "walltime"
        cycle += 1
        state.commits_this_cycle = 0
        log.info("--- cycle %d ---", cycle)

        track_findings = _evaluate_tracks(config, staging_wt, cycle, state.run_dir, state)
        state.all_findings.extend(f for fs in track_findings.values() for f in fs)

        if state.graceful_stop_requested:
            return "graceful-stop"

        if cycle == 1 and all(not fs for fs in track_findings.values()):
            return "zero-first-cycle"

        # Global queue: all actionable findings across all tracks. Workers dequeue
        # without caring which track a finding came from — per-finding scope
        # enforcement lives in safety.check_scope (via track->allowlist).
        global_queue: list["Finding"] = []
        for track in config.tracks:
            actionable, _ = findings_mod.route(track_findings.get(track, []))
            global_queue.extend(actionable)

        if global_queue:
            _process_findings_parallel(
                config, staging_wt, pool, global_queue, state,
            )

        if _all_tracks_signaled_done(state.run_dir, cycle):
            return "agent-signaled-done"

        if state.graceful_stop_requested:
            return "graceful-stop"


def _process_findings_parallel(
    config: "Config", staging_wt: worktree.Worktree,
    pool: "_WorkerPool | None", findings: list["Finding"], state: RunState,
) -> None:
    """Drain `findings` through the worker pool, `max_workers` at a time.

    Each submission acquires a free worker, resets it to the current staging
    tip (so it sees all previously-merged fixes), runs fix+verify on that
    isolated worktree+backend, and — on success — cherry-picks the verified
    commit onto staging under `staging_lock`. Worker is released back to the
    pool on completion.

    When `pool is None` (single-worker fallback), `staging_wt` itself is used
    for fix+verify and commits land directly on staging (no cherry-pick).
    """
    if pool is None:
        # Single-worker mode: the staging worktree IS the worker. Serial.
        for finding in findings:
            if state.graceful_stop_requested:
                return
            if time.time() - state.start_ts > config.max_walltime:
                log.warning("walltime exceeded — stopping at %s", finding.id)
                return
            _run_one_finding(config, staging_wt, staging_wt, finding, state)
        return

    def _submit(finding: "Finding") -> None:
        worker_wt = pool.acquire()
        try:
            if state.graceful_stop_requested:
                return
            if time.time() - state.start_ts > config.max_walltime:
                log.warning("walltime exceeded — skipping %s", finding.id)
                return
            _run_one_finding(config, worker_wt, staging_wt, finding, state)
        finally:
            pool.release(worker_wt)

    max_concurrency = min(config.max_workers, len(findings))
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures = {executor.submit(_submit, f): f for f in findings}
        for fut in as_completed(futures):
            f = futures[fut]
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001
                log.warning("finding %s worker crashed: %s", f.id, exc)


def _run_one_finding(
    config: "Config", worker_wt: worktree.Worktree, staging_wt: worktree.Worktree,
    finding: "Finding", state: RunState,
) -> None:
    """Dispatch one finding to its assigned worker, catching graceful-stop
    exceptions that terminate the overall run.

    Kept separate from `_process_finding` so the graceful-stop + unexpected-
    error handling is one place regardless of which pool invoked us.
    """
    log.info("finding %s (track %s, worker %s): starting",
             finding.id, finding.track, worker_wt.worker_id)
    t0 = time.time()
    try:
        _process_finding(config, worker_wt, staging_wt, finding, state)
    except (engine.RateLimitHit, engine.EngineExhausted) as exc:
        reason = f"track {finding.track} finding {finding.id}: {exc}"
        with state.staging_lock:
            state.graceful_stop_requested = True
            if not state.graceful_stop_reason:
                state.graceful_stop_reason = reason
        log.error("graceful stop trigger — finding %s: %s", finding.id, exc)
        try:
            worktree.rollback_track_scope(worker_wt, finding.track)
        except Exception as roll_exc:  # noqa: BLE001
            log.warning("rollback after graceful stop failed: %s", roll_exc)
        return
    except Exception as exc:  # noqa: BLE001
        log.warning("finding %s: unexpected error: %s — rolling back worker and continuing",
                    finding.id, exc)
        try:
            worktree.rollback_track_scope(worker_wt, finding.track)
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
            return findings_mod.parse(findings_md, cycle=cycle)
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


def _process_finding(
    config: "Config",
    wt: worktree.Worktree,
    staging_wt: worktree.Worktree,
    finding: "Finding",
    state: RunState,
) -> None:
    """Run fix+verify for ONE finding on the given worker worktree, then
    cherry-pick the verified commit onto the staging worktree.

    `wt` is the worker assigned to this finding — its own worktree, own
    branch, own backend port. When the worker pool is disabled
    (max_workers==1), caller passes the staging worktree as `wt` and the
    cherry-pick is a no-op (commit already on staging).

    Resume skip: a prior invocation may have already landed this finding.
    Check on the STAGING branch (where cherry-picks live), not the worker
    branch, because worker branches are ephemeral.
    """
    is_single_worker = wt.path == staging_wt.path
    # Resume: if a prior run already committed a fix for this finding, skip.
    if _commit_exists_for_finding(staging_wt.path, finding.id, finding.cycle):
        sha = subprocess.check_output(
            ["git", "log", "main..HEAD", "--grep", f"harness: fix {finding.id}",
             "--fixed-strings", "--format=%H", "-n", "1"],
            cwd=staging_wt.path, text=True,
        ).strip()
        if sha:
            record = _reconstruct_commit_record(staging_wt.path, finding, sha, state.run_dir)
            with state.staging_lock:
                state.commits.append(record)
            log.info("resume: finding %s already on staging %s — reused", finding.id, sha[:7])
        else:
            log.info("resume: finding %s already has commit on staging — skipping", finding.id)
        return

    # Per-worker mode: sync worker to current staging tip so this finding sees
    # all previously-merged fixes. In single-worker mode, the worker IS staging.
    if not is_single_worker:
        with state.staging_lock:
            worktree.reset_worker_to_staging(wt, state.staging_branch)

    pre_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=wt.path, text=True,
    ).strip()
    # Clear any stale dirt before the fixer starts. In worker mode, `reset_worker_to_staging`
    # already cleaned the worktree — this is defensive for single-worker mode.
    worktree.rollback_track_scope(wt, finding.track)

    fix_record = state.sessions.get(f"fix-{finding.id}")
    fix_resume_id = _viable_resume_id(fix_record, wt.path)
    if fix_resume_id:
        log.info("resume: finding %s fixer resuming session %s", finding.id, fix_resume_id[:8])
    engine.fix(config, finding, wt, state.run_dir,
               sessions=state.sessions, resume_session_id=fix_resume_id)

    # Post-fix safety probes. In worker mode, no peer-track interference is
    # possible (worker's own isolated worktree), so the locks are now trivial.
    bypass_sha = _detect_agent_commit(wt.path, pre_sha, finding.id)
    if bypass_sha:
        log.warning(
            "finding %s: agent committed %s directly (bypassed orchestrator)",
            finding.id, bypass_sha[:7],
        )
    _pop_orphan_stash(wt.path, finding.id)

    # Restart THIS worker's backend so verifier sees the fix. Single-worker mode
    # restarts staging's backend; per-worker mode restarts the worker's own.
    worktree.restart_backend(wt, config)

    verify_record = state.sessions.get(f"verify-{finding.id}")
    verify_resume_id = _viable_resume_id(verify_record, wt.path)
    if verify_resume_id:
        log.info("resume: finding %s verifier resuming session %s", finding.id, verify_resume_id[:8])
    verdict = engine.verify(config, finding, wt, state.run_dir,
                            sessions=state.sessions, resume_session_id=verify_resume_id)

    scope_violations = safety.check_scope(wt.path, pre_sha, finding.track) or []
    leak_actionable, leak_advisory = safety.check_no_leak(state.pre_dirty)
    if leak_advisory:
        log.warning(
            "finding %s: main-repo paths dirtied during run (advisory, not fixer-caused): %s",
            finding.id, leak_advisory,
        )
    violations = scope_violations + leak_actionable

    if verdict.verified and not violations:
        commit = _commit_fix(wt, finding, pre_sha, verdict)
        if commit:
            if is_single_worker:
                # Commit already on staging (they're the same branch).
                with state.staging_lock:
                    state.commits.append(commit)
                    state.commits_this_cycle += 1
            else:
                # Cherry-pick worker's commit onto staging under staging_lock
                # so concurrent workers can't interleave their cherry-picks.
                ok = _merge_to_staging(wt, staging_wt, commit.sha, state.staging_lock)
                if ok:
                    with state.staging_lock:
                        state.commits.append(commit)
                        state.commits_this_cycle += 1
                else:
                    log.warning(
                        "finding %s: cherry-pick onto staging failed — fix stays on worker branch %s, NOT in staging",
                        finding.id, wt.branch,
                    )
                    _capture_patch(wt.path, finding, state.run_dir)
        elif bypass_sha:
            record = _reconstruct_commit_record(
                wt.path, finding, bypass_sha, state.run_dir,
            )
            if not is_single_worker:
                ok = _merge_to_staging(wt, staging_wt, bypass_sha, state.staging_lock)
                if not ok:
                    log.warning("finding %s: bypass-commit cherry-pick failed", finding.id)
                    return
            with state.staging_lock:
                state.commits.append(record)
                state.commits_this_cycle += 1
            log.info(
                "finding %s: accepted agent-bypass commit %s",
                finding.id, bypass_sha[:7],
            )
        else:
            log.warning(
                "finding %s: fixer produced no in-scope changes — skipped (verdict=%s)",
                finding.id, verdict.reason or "verified",
            )
            with state.staging_lock:
                state.no_op_fixers.append(finding.id)
            _capture_patch(wt.path, finding, state.run_dir)
    else:
        parts = []
        if not verdict.verified:
            parts.append(f"verdict={verdict.reason or 'failed'}")
        if scope_violations:
            parts.append(f"scope={scope_violations}")
        if leak_actionable:
            parts.append(f"leak={leak_actionable}")
        log.warning("finding %s: rolling back — %s", finding.id, "; ".join(parts) or "unknown")
        if leak_actionable:
            log.error(
                "finding %s: LEAK in main repo — cleaning paths %s",
                finding.id, leak_actionable,
            )
            _clean_main_repo_leaks(wt.main_repo, leak_actionable)
        _capture_patch(wt.path, finding, state.run_dir)
        if bypass_sha:
            subprocess.run(
                ["git", "reset", "--hard", pre_sha], cwd=wt.path, check=True,
            )
            log.warning(
                "finding %s: reset HEAD to %s to undo agent-bypass commit",
                finding.id, pre_sha[:7],
            )
        worktree.rollback_track_scope(wt, finding.track)


def _merge_to_staging(
    worker_wt: worktree.Worktree,
    staging_wt: worktree.Worktree,
    commit_sha: str,
    lock: threading.Lock,
) -> bool:
    """Cherry-pick a worker's verified commit onto the staging worktree.

    Returns True on clean merge, False on conflict (cherry-pick aborted).
    Conflicts are rare because track scope allowlists are non-overlapping —
    but if e.g. two workers both modify `pyproject.toml` (track A scope),
    the second cherry-pick collides with the first and this bails out
    cleanly rather than leaving staging in a half-merged state.
    """
    with lock:
        result = subprocess.run(
            ["git", "cherry-pick", "--allow-empty", commit_sha],
            cwd=staging_wt.path, capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            subprocess.run(
                ["git", "cherry-pick", "--abort"],
                cwd=staging_wt.path, check=False, capture_output=True,
            )
            log.error(
                "cherry-pick of %s onto staging failed: %s",
                commit_sha[:8], result.stderr.strip() or "(no stderr)",
            )
            return False
        return True


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
    # Subject format `harness: fix <id>@c<n> — ...` — the `@c<n>` stamp is how
    # `_commit_exists_for_finding` scopes resume-skip to THIS cycle. Without it,
    # cycle 2's `F-c-1-5` would be mis-skipped by cycle 1's commit with the
    # same id prefix (evaluators restart numbering from 1 each cycle).
    subprocess.run(
        ["git", "commit", "-m",
         f"harness: fix {finding.id}@c{finding.cycle} — {summary_line}"],
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
    review_md = review.compose(
        run_dir, state.commits, state.all_findings, tip_smoke_ok,
        no_op_finding_ids=tuple(state.no_op_fixers),
    )
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
