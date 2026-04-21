"""Harness orchestrator. One top-level `run()` that wires every module together."""
from __future__ import annotations

import logging
import subprocess
import sys
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

    wt = worktree.create(ts, config)
    state = RunState(run_dir=run_dir, staging_branch=wt.branch, token=token, ts=ts, pre_dirty=pre_dirty)

    try:
        inventory.generate(wt.path, run_dir / "inventory.md")
        smoke.check(wt, config, token)
        subprocess.run(["git", "checkout", state.staging_branch], cwd=wt.path, check=False)
        exit_reason = _cycle_loop(config, wt, state)
        tip_smoke_ok = _tip_smoke(wt, config, state)
        _write_outputs(run_dir, state, tip_smoke_ok)
        pr_url = _push_and_pr(wt, state, run_dir) if state.commits else None
        _print_summary(run_dir, state, exit_reason, pr_url, tip_smoke_ok)
        return 0
    except smoke.SmokeError as exc:
        log.error("%s", exc)
        return 3
    except Exception:  # noqa: BLE001
        log.exception("unhandled failure during run")
        return 4
    finally:
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

        track_findings = _evaluate_tracks(config, wt, cycle, state.run_dir)
        state.all_findings.extend(f for fs in track_findings.values() for f in fs)

        if cycle == 1 and all(not fs for fs in track_findings.values()):
            return "zero-first-cycle"

        actionable: list["Finding"] = []
        for fs in track_findings.values():
            a, _ = findings_mod.route(fs)
            actionable.extend(a)

        for finding in actionable:
            if time.time() - state.start_ts > config.max_walltime:
                log.warning("walltime exceeded mid-cycle; stopping after commit-or-rollback of prior finding")
                return "walltime"
            _process_finding(config, wt, finding, state)

        # Process findings first, THEN check agent-signaled-done — otherwise agents that signal
        # done in cycle 1 (the common case) would skip the fixer loop entirely.
        if _all_tracks_signaled_done(state.run_dir, cycle):
            return "agent-signaled-done"

        if not actionable and state.commits_this_cycle == 0:
            state.zero_high_conf_cycles += 1
            if state.zero_high_conf_cycles >= 2:
                return "no-progress"
        else:
            state.zero_high_conf_cycles = 0


def _evaluate_tracks(config: "Config", wt: worktree.Worktree, cycle: int, run_dir: Path) -> dict[str, list["Finding"]]:
    results: dict[str, list["Finding"]] = {t: [] for t in config.tracks}
    with ThreadPoolExecutor(max_workers=len(config.tracks)) as pool:
        futures = {pool.submit(engine.evaluate, config, t, wt, cycle, run_dir): t for t in config.tracks}
        for fut in as_completed(futures):
            track = futures[fut]
            try:
                results[track] = fut.result()
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
    # Guarantee a clean starting tree so residue from prior findings doesn't pollute this one.
    worktree.rollback_to(wt, pre_sha)
    try:
        engine.fix(config, finding, wt, state.run_dir)
        verdict = engine.verify(config, finding, wt, state.run_dir)
    except Exception as exc:  # noqa: BLE001
        log.warning("finding %s: fix/verify raised: %s — rolling back", finding.id, exc)
        _rollback(wt, config, pre_sha, finding, state.run_dir)
        return

    scope_violations = safety.check_scope(wt.path, pre_sha, finding.track) or []
    leak_violations = safety.check_no_leak(state.pre_dirty) or []
    violations = scope_violations + leak_violations

    if verdict.verified and not violations:
        commit = _commit_fix(wt, finding, pre_sha, verdict)
        if commit:
            state.commits.append(commit)
            state.commits_this_cycle += 1
        worktree.restart_backend(wt, config)
    else:
        parts = []
        if not verdict.verified:
            parts.append(f"verdict={verdict.reason or 'failed'}")
        if scope_violations:
            parts.append(f"scope={scope_violations}")
        if leak_violations:
            parts.append(f"leak={leak_violations}")
        log.warning("finding %s: rolling back — %s", finding.id, "; ".join(parts) or "unknown")
        _rollback(wt, config, pre_sha, finding, state.run_dir)


def _rollback(wt: worktree.Worktree, config: "Config", pre_sha: str, finding: "Finding", run_dir: Path) -> None:
    _capture_patch(wt, pre_sha, "HEAD", finding, run_dir)
    worktree.rollback_to(wt, pre_sha)
    worktree.restart_backend(wt, config)


def _commit_fix(wt: worktree.Worktree, finding: "Finding", pre_sha: str, verdict: engine.Verdict) -> review.CommitRecord | None:
    # Fixer edits are uncommitted in the worktree; stage + commit them now.
    # scope check already confirmed every changed path is within the track's allowlist,
    # and HARNESS_ARTIFACTS (backend.log etc.) are filtered out of working_tree_changes.
    files = tuple(safety.working_tree_changes(wt.path))
    if not files:
        log.info("finding %s: no diff — skipping commit", finding.id)
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


def _capture_patch(wt: worktree.Worktree, pre_sha: str, head: str, finding: "Finding", run_dir: Path) -> Path:
    out_dir = run_dir / "fix-diffs" / finding.track
    out_dir.mkdir(parents=True, exist_ok=True)
    patch_path = out_dir / f"F-{finding.id}.patch"
    diff = subprocess.run(
        ["git", "diff", pre_sha, head], cwd=wt.path, capture_output=True, text=True, check=False,
    )
    patch_path.write_text(diff.stdout, encoding="utf-8")
    return patch_path


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
        (run_dir / "pr-body.md").write_text(review.pr_body(run_dir, state.commits, tip_smoke_ok), encoding="utf-8")


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
