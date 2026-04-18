"""Core cycle loop and summary generation for the QA eval-fix harness.

Replaces the ``main()`` function in ``scripts/eval_fix_harness.sh``
(lines 1450-1803) with a typed, testable Python implementation.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml

from harness.config import Config
from harness.engine import Engine
from harness.preflight import (
    check_jwt_expiry,
    check_stack_health,
    check_vite_jwt_freshness,
    cleanup_harness_state,
    refresh_vite_jwt,
    run_preflight,
)
from harness.prompts import (
    render_eval_prompt,
    render_fixer_prompt,
    render_verifier_prompt,
)
from harness.scorecard import (
    Finding,
    Scorecard,
    check_convergence,
    compute_escalated_findings,
    count_escalated_non_pass,
    parse_flow4_capabilities,
)
from harness.worktree import (
    ProcessTracker,
    cleanup_staging_worktree,
    create_staging_worktree,
    detect_backend_changes,
    restart_backend,
    snapshot_backend_tree,
    snapshot_main_repo_working_dir,
    snapshot_protected_files,
    verify_and_restore_main_repo_working_dir,
    verify_and_restore_protected_files,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repository / path helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MATRIX_PATH = Path(__file__).parent / "test-matrix.md"

# Path-prefix-to-domain mapping for GoFreddy overlap attribution.
# Domain A = CLI commands, Domain B = API routers, Domain C = Frontend.
_DOMAIN_PREFIXES: list[tuple[str, str]] = [
    ("cli/freddy/commands/", "A"),
    ("src/api/routers/", "B"),
    ("frontend/src/", "C"),
]


def attribute_file(path: str) -> str | None:
    """Attribute a changed file to a domain letter, ``"SHARED"``, or ``None``.

    Returns the domain letter (e.g. ``"A"``) for domain-owned files,
    ``"SHARED"`` for files under ``src/`` that don't match a specific domain,
    or ``None`` for files outside the main source trees.
    """
    normalized = path.replace("\\", "/")
    for prefix, domain in _DOMAIN_PREFIXES:
        if normalized.startswith(prefix):
            return domain
    if normalized.startswith("src/"):
        return "SHARED"
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run(config: Config) -> None:
    """Orchestrate the full QA eval-fix loop.

    Called by ``harness/__main__.py`` after CLI parsing.
    """
    # ---- timestamp + run dir ------------------------------------------------
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = _REPO_ROOT / "harness" / "runs" / run_ts
    run_dir.mkdir(parents=True, exist_ok=True)

    # ---- main-repo leak guard baseline --------------------------------------
    # Snapshot src/ + frontend/src/ dirt state before anything runs. The
    # codex fixer runs with danger-full-access + inherit=all, so its cwd
    # does not actually sandbox filesystem writes. If the fixer edits files
    # outside the staging worktree, verify_and_restore_main_repo_working_dir
    # reverts them at the end of each cycle.
    main_repo_snapshot = snapshot_main_repo_working_dir(_REPO_ROOT)
    logger.info(
        "Main repo leak guard: snapshot has %d pre-existing dirty path(s)",
        len(main_repo_snapshot),
    )

    # ---- preflight ----------------------------------------------------------
    pf = run_preflight(config)
    token = pf.jwt_token
    user_id = pf.harness_user_id

    # ---- staging worktree ---------------------------------------------------
    worktree_path, staging_branch = create_staging_worktree(config, run_ts)

    logger.info(
        "Starting harness run: %s (engine=%s, dry_run=%s)",
        run_ts, config.engine, config.dry_run,
    )

    # ---- loop state ---------------------------------------------------------
    engine = Engine(config.engine)
    prev_merged: Scorecard | None = None
    last_merged: Scorecard | None = None
    exit_reason = "max cycles reached"
    completed_cycles = 0
    prev_pass: int | None = None
    harness_start = time.monotonic()
    escalated_ids: set[str] = set()
    tracks_to_run: list[str] = ["a"] if config.dry_run else config.tracks

    # ---- resume logic -------------------------------------------------------
    if config.resume_cycle > 1:
        logger.info(
            "Resuming from cycle %d (skipping 1-%d)",
            config.resume_cycle, config.resume_cycle - 1,
        )
        completed_cycles = config.resume_cycle - 1
        logger.info("Restarting backend from resumed staging worktree...")
        restart_backend(config, worktree_path)
        logger.info("Backend restarted from staging worktree")

    # ---- cycle loop ---------------------------------------------------------
    with ProcessTracker() as tracker:
        tracker.set_worktree(
            worktree_path, staging_branch, config.auto_cleanup,
            repo_root=_REPO_ROOT,
        )

        for cycle in range(config.resume_cycle, config.max_cycles + 1):
            # 1. Wall-time cap
            elapsed = time.monotonic() - harness_start
            if elapsed > config.max_walltime:
                logger.warning(
                    "Wall-time cap reached (%.0fs > %ds). Stopping before cycle %d.",
                    elapsed, config.max_walltime, cycle,
                )
                exit_reason = f"wall-time cap ({int(elapsed)}s elapsed)"
                break

            # 2. JWT freshness (cycle > 1)
            if cycle > 1:
                logger.info("Re-checking vite JWT freshness before cycle %d...", cycle)
                freshness = check_vite_jwt_freshness(config)
                if freshness < 600:
                    logger.info("Vite JWT expiring soon (%ds remaining) -- auto-refreshing...", max(0, freshness))
                    try:
                        token = refresh_vite_jwt(config)
                        logger.info("Vite JWT refreshed before cycle %d", cycle)
                    except Exception:
                        logger.error("Vite JWT auto-refresh failed")
                        exit_reason = f"vite JWT expiring/expired mid-run before cycle {cycle} (auto-refresh failed)"
                        break

            logger.info(
                "========== CYCLE %d / %d (elapsed=%.0fs) ==========",
                cycle, config.max_cycles, elapsed,
            )

            # 3. Stack health
            try:
                check_stack_health(config)
            except Exception:
                logger.warning("Stack unhealthy before cycle %d. Waiting 30s...", cycle)
                time.sleep(30)
                try:
                    check_stack_health(config)
                except Exception:
                    logger.error("Stack still unhealthy. Aborting.")
                    exit_reason = "stack unhealthy"
                    break

            # 4. Increment completed_cycles
            completed_cycles += 1

            # 5. Between-cycle cleanup (conversations_only, cycle > 1)
            if cycle > 1:
                logger.info("Cleaning conversations before cycle %d (keeping monitors)...", cycle)
                cleanup_harness_state(config, user_id, scope="conversations_only")

            # 6. Restore session IDs from dotfiles -- handled internally by Engine

            # 7-8. Dispatch evaluators in parallel
            track_scorecards: list[Scorecard] = []

            with ThreadPoolExecutor(max_workers=len(tracks_to_run)) as pool:
                futures = {}
                for track in tracks_to_run:
                    scorecard_out = run_dir / f"scorecard-{cycle}-track-{track}.md"
                    prompt_path = render_eval_prompt(
                        track, cycle, str(scorecard_out), config, run_dir,
                    )
                    future = pool.submit(
                        engine.evaluate, track, cycle, prompt_path, config, run_dir,
                    )
                    futures[future] = track

                for future in as_completed(futures):
                    track = futures[future]
                    try:
                        sc_path = future.result()
                        if sc_path.exists():
                            track_scorecards.append(Scorecard.from_yaml(sc_path))
                        else:
                            logger.error("Track %s scorecard missing: %s", track.upper(), sc_path)
                    except Exception:
                        logger.exception("Evaluator track %s raised an exception", track.upper())

            logger.info("All evaluators completed (cycle %d)", cycle)

            # 9. Merge scorecards
            merged = Scorecard.merge(track_scorecards) if track_scorecards else Scorecard(cycle=cycle, track=None, findings=[])
            merged_path = run_dir / f"scorecard-{cycle}-merged.md"
            merged_path.write_text(merged.to_markdown(track_order=tracks_to_run), encoding="utf-8")
            last_merged = merged
            logger.info("Merged scorecard: %s", merged_path)

            # 10. Compute escalated findings
            escalated_ids = compute_escalated_findings(run_dir, cycle, config.max_fix_attempts)
            if escalated_ids:
                # Write sidecar
                esc_path = run_dir / f".escalated-{cycle}.txt"
                esc_path.write_text("\n".join(sorted(escalated_ids)) + "\n", encoding="utf-8")
                logger.info(
                    "Escalated findings active this cycle: %d -- %s",
                    len(escalated_ids), " ".join(sorted(escalated_ids)),
                )

            # 11. Extract counts
            m_pass = merged.pass_count
            m_partial = merged.partial_count
            m_fail = merged.fail_count
            m_blocked = merged.blocked_count
            logger.info(
                "Results: pass=%d partial=%d fail=%d blocked=%d",
                m_pass, m_partial, m_fail, m_blocked,
            )

            # 12. Regression brake
            if prev_pass is not None and m_pass < prev_pass:
                logger.error(
                    "Net regression detected: pass count %d -> %d (delta %d)",
                    prev_pass, m_pass, m_pass - prev_pass,
                )
                exit_reason = f"net regression (pass count {prev_pass} -> {m_pass})"
                break
            prev_pass = m_pass

            # Escalated non-pass counts for ALL PASS decision
            escalated_non_pass = count_escalated_non_pass(merged, escalated_ids) if escalated_ids else 0
            non_escalated_non_pass = max(0, m_fail + m_partial + m_blocked - escalated_non_pass)

            # 13. Rate-limit check
            if m_pass == 0 and m_fail == 0 and m_partial == 0 and m_blocked == 0:
                rate_limit_sentinel = run_dir / ".rate-limit-hit"
                if rate_limit_sentinel.exists():
                    logger.error("Claude rate limit reached -- run aborted.")
                    exit_reason = "rate_limit (claude 5h Opus window)"
                    break
                logger.error("No evaluator produced results. Check eval logs in %s", run_dir)
                exit_reason = "all evaluators failed"
                break

            # 15. Evaluation-incomplete check
            if merged.evaluator_failed and non_escalated_non_pass == 0:
                logger.error(
                    "Evaluation incomplete: %s -- refusing to report ALL PASS",
                    merged.evaluator_failure_reason,
                )
                exit_reason = "evaluation incomplete"
                break

            # 16. ALL PASS check
            if not merged.evaluator_failed and m_pass > 0 and non_escalated_non_pass == 0:
                if config.dry_run:
                    logger.info("DRY RUN PASS! Harness complete.")
                    exit_reason = "DRY RUN PASS"
                elif escalated_non_pass > 0:
                    logger.info(
                        "ALL NON-ESCALATED CAPABILITIES PASS! "
                        "(%d escalated finding(s) still need human review.) "
                        "Harness complete.",
                        escalated_non_pass,
                    )
                    exit_reason = f"ALL PASS (with {escalated_non_pass} escalated)"
                else:
                    logger.info("ALL CAPABILITIES PASS! Harness complete.")
                    exit_reason = "ALL PASS"
                break

            # 17. Convergence check
            flow4_ids = parse_flow4_capabilities(_MATRIX_PATH)
            if not merged.evaluator_failed and prev_merged is not None:
                if check_convergence(merged, prev_merged, flow4_ids, escalated_ids):
                    logger.warning(
                        "Converged -- no improvement since cycle %d on "
                        "non-escalated, non-dynamic findings. Stopping.",
                        cycle - 1,
                    )
                    exit_reason = "converged"
                    break
            prev_merged = merged

            # 18. Eval-only gate
            if config.eval_only:
                logger.info("EVAL_ONLY=true -- skipping fixer. Cycle %d complete.", cycle)
                exit_reason = "eval-only"
                break

            # 19. Snapshot backend tree
            backend_before = snapshot_backend_tree(worktree_path)

            # 20. Snapshot protected files
            harness_backup = snapshot_protected_files(_REPO_ROOT, run_dir, cycle)

            # 20b. Capture pre-fixer SHA so the verifier can rollback
            #      if it marks any finding FAILED. Without a baseline SHA
            #      we cannot rollback — abort the cycle entirely.
            try:
                pre_fixer_sha = _capture_git_sha(worktree_path)
            except RuntimeError:
                logger.exception(
                    "Could not capture pre-fixer SHA — aborting cycle %d", cycle,
                )
                exit_reason = "git rev-parse failed"
                break

            # 21. Persist merged scorecard (no findings cap — fixer owns
            #     the full list and iterates unconstrained).
            capped = merged
            capped_path = run_dir / f"scorecard-{cycle}-capped.md"
            capped_path.write_text(capped.to_markdown(track_order=tracks_to_run), encoding="utf-8")

            # 22. Run fixer — unified dispatch: fixer_workers=1 uses a
            #     single "all" domain; fixer_workers>1 splits by domain.
            if config.fixer_workers <= 1:
                actionable = [
                    f for f in capped.findings
                    if f.grade in ("FAIL", "PARTIAL")
                ]
                fixer_units: dict[str, Scorecard] = (
                    {"all": Scorecard(
                        cycle=cycle, track=None, findings=actionable,
                    )}
                    if actionable else {}
                )
            else:
                splits = capped.split_by_domain(config.fixer_domains)
                fixer_units = {
                    d: sc for d, sc in splits.items()
                    if any(f.grade in ("FAIL", "PARTIAL") for f in sc.findings)
                }

            verdicts: dict[str, dict[str, str]] = {}
            commit_sha: str | None = None

            if not fixer_units:
                logger.info("No actionable findings — skipping fixer + verifier")
            else:
                logger.info(
                    "Fixer dispatch: %d unit(s) — %s",
                    len(fixer_units), ", ".join(sorted(fixer_units)),
                )

                workers = max(1, min(config.fixer_workers, len(fixer_units)))
                with ThreadPoolExecutor(max_workers=workers) as fixer_pool:
                    fixer_futures = {}
                    for domain, domain_sc in fixer_units.items():
                        d_lower = domain.lower()
                        domain_fixes_path = run_dir / f"fixes-{cycle}-{d_lower}.md"
                        domain_scope_ids = ",".join(
                            f.id for f in domain_sc.findings
                            if f.grade in ("FAIL", "PARTIAL")
                        ) or "all"
                        domain_prompt = render_fixer_prompt(
                            cycle, str(capped_path), str(domain_fixes_path),
                            config, run_dir,
                            full_merged_path=str(merged_path),
                            scope_ids=domain_scope_ids,
                        )
                        future = fixer_pool.submit(
                            engine.fix, cycle, domain_prompt, config, run_dir,
                            domain_suffix=d_lower,
                            cwd=worktree_path,
                        )
                        fixer_futures[future] = domain

                    for future in as_completed(fixer_futures):
                        domain = fixer_futures[future]
                        try:
                            future.result()
                            logger.info("Fixer unit %s completed", domain)
                        except Exception:
                            logger.exception(
                                "Fixer unit %s raised an exception", domain,
                            )

                logger.info("All fixers completed (cycle %d)", cycle)

                # 22b. First restore — catch in-flight harness/* writes
                #      before the verifier boots.
                verify_and_restore_protected_files(_REPO_ROOT, harness_backup)

                # 22c. Restart backend so verifier tests against new code
                backend_after = snapshot_backend_tree(worktree_path)
                if detect_backend_changes(backend_before, backend_after):
                    logger.info(
                        "Backend changed — restarting before verifier dispatch",
                    )
                    try:
                        proc = restart_backend(config, worktree_path)
                        tracker.register(proc.pid)
                    except Exception:
                        logger.warning(
                            "Backend restart failed before verifier — "
                            "verdicts may be unreliable",
                        )

                # 22d. Run verifier per active domain
                verdicts = _dispatch_verifiers(
                    cycle=cycle,
                    capped_scorecard=capped,
                    run_dir=run_dir,
                    config=config,
                    engine=engine,
                    worktree_path=worktree_path,
                )

                # 22e. Commit if all verified, rollback if any failed
                commit_sha = _commit_or_rollback(
                    worktree_path, verdicts, pre_fixer_sha,
                    run_dir, cycle, config,
                )

                # 22f. Merge per-domain fix reports
                _merge_fix_reports(
                    cycle, fixer_units, run_dir,
                    commit_sha or "rolled-back",
                )

            # 23. Second restore — brackets the verifier window
            verify_and_restore_protected_files(_REPO_ROOT, harness_backup)

            # 23b. Main-repo leak guard — revert any src/ or frontend/src/
            #      edits that escaped the worktree during this cycle.
            leaked = verify_and_restore_main_repo_working_dir(
                _REPO_ROOT, main_repo_snapshot,
            )
            if leaked:
                logger.warning(
                    "Cycle %d leaked %d file(s) outside worktree; reverted: %s",
                    cycle, len(leaked), ", ".join(leaked),
                )

            # 24. Restart backend if needed
            backend_after = snapshot_backend_tree(worktree_path)
            changes = detect_backend_changes(backend_before, backend_after)
            if changes:
                logger.info(
                    "Backend files changed (%d file(s)) -- restarting...",
                    len(changes),
                )
                try:
                    proc = restart_backend(config, worktree_path)
                    tracker.register(proc.pid)
                except Exception:
                    logger.warning(
                        "Backend restart failed. Next cycle's evaluator may see stale behavior."
                    )

    # ---- summary ------------------------------------------------------------
    write_summary(
        run_dir, config, last_merged, completed_cycles,
        exit_reason, staging_branch, escalated_ids,
        tracks_used=tracks_to_run,
    )
    logger.info("Harness complete. Summary: %s/summary.md", run_dir)

    if staging_branch:
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", f"main..{staging_branch}"],
                capture_output=True, text=True, cwd=str(_REPO_ROOT),
            )
            ahead = int(result.stdout.strip()) if result.returncode == 0 else 0
        except (ValueError, OSError):
            ahead = 0
        if ahead > 0:
            logger.info("Staging branch: %s (%d commit(s) ahead of main)", staging_branch, ahead)
            logger.info("To accept: git merge --ff-only %s", staging_branch)
            logger.info("To discard: git branch -D %s", staging_branch)


# ---------------------------------------------------------------------------
# Parallel fixer helpers
# ---------------------------------------------------------------------------


def _capture_git_sha(worktree: Path) -> str:
    """Run ``git rev-parse HEAD`` in *worktree* and return the SHA.

    Raises ``RuntimeError`` if git fails — without a baseline SHA we
    cannot rollback, so the cycle must abort cleanly.
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=str(worktree),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git rev-parse HEAD failed in {worktree}: {result.stderr.strip()}"
        )
    sha = result.stdout.strip()
    if not sha:
        raise RuntimeError(
            f"git rev-parse HEAD returned empty SHA in {worktree}"
        )
    return sha


def _dispatch_verifiers(
    cycle: int,
    capped_scorecard: Scorecard,
    run_dir: Path,
    config: Config,
    engine: Engine,
    worktree_path: Path,
) -> dict[str, dict[str, str]]:
    """Render and run a per-domain verifier for every active domain.

    Returns ``{domain_letter: {finding_id: "VERIFIED"|"FAILED"}}``.
    Empty dict when ``config.eval_only`` is set or there are no active
    findings. Any domain whose verdict file is missing, unparseable, or
    incomplete has ALL its findings force-failed — rollback is the
    correct response to an unreliable verifier.
    """
    if config.eval_only:
        return {}

    abs_test_matrix_path = _REPO_ROOT / "harness" / "test-matrix.md"

    splits = capped_scorecard.split_by_domain(config.fixer_domains)
    active: dict[str, list[Finding]] = {}
    for domain, sc in splits.items():
        actionable = [f for f in sc.findings if f.grade in ("FAIL", "PARTIAL")]
        if actionable:
            active[domain] = actionable

    if not active:
        logger.info("No active findings to verify — skipping verifier dispatch")
        return {}

    logger.info(
        "Dispatching verifiers for %d domain(s): %s",
        len(active), ", ".join(sorted(active)),
    )

    # Defense-in-depth: unlink any pre-existing verdict file so the fixer
    # cannot pre-plant a verdict for the harness to read.
    rendered_prompts: dict[str, tuple[Path, Path, list[Finding]]] = {}
    for domain, findings in active.items():
        d_lower = domain.lower()
        verdict_path = run_dir / f"verifier-{cycle}-{d_lower}.md"
        if verdict_path.exists():
            verdict_path.unlink()

        prompt_path = render_verifier_prompt(
            cycle=cycle,
            domain_letter=d_lower,
            focus_findings=findings,
            report_path=str(verdict_path),
            run_dir=run_dir,
            config=config,
            abs_test_matrix_path=abs_test_matrix_path,
        )
        rendered_prompts[domain] = (prompt_path, verdict_path, findings)

    verdicts: dict[str, dict[str, str]] = {}
    max_workers = min(len(active), max(1, config.fixer_workers))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for domain, (prompt_path, verdict_path, findings) in rendered_prompts.items():
            d_lower = domain.lower()
            future = pool.submit(
                engine.verify,
                cycle=cycle,
                prompt_path=prompt_path,
                config=config,
                run_dir=run_dir,
                domain_suffix=d_lower,
                cwd=worktree_path,
            )
            futures[future] = domain

        for future in as_completed(futures):
            domain = futures[future]
            findings = rendered_prompts[domain][2]
            verdict_path = rendered_prompts[domain][1]
            try:
                future.result()
            except Exception:
                logger.exception("Verifier domain %s raised an exception", domain)
                verdicts[domain] = {f.id: "FAILED" for f in findings}
                continue

            if not verdict_path.exists():
                logger.warning(
                    "Verifier domain %s wrote no verdict file — force-failing",
                    domain,
                )
                verdicts[domain] = {f.id: "FAILED" for f in findings}
                continue

            text = verdict_path.read_text(encoding="utf-8")
            parts = text.split("---", 2)
            if len(parts) < 3:
                logger.warning(
                    "Verifier domain %s verdict missing YAML frontmatter",
                    domain,
                )
                verdicts[domain] = {f.id: "FAILED" for f in findings}
                continue
            try:
                data = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                logger.warning(
                    "Verifier domain %s verdict YAML parse failed", domain,
                )
                verdicts[domain] = {f.id: "FAILED" for f in findings}
                continue

            raw_findings = data.get("findings", [])
            if not isinstance(raw_findings, list):
                verdicts[domain] = {f.id: "FAILED" for f in findings}
                continue

            per_finding: dict[str, str] = {}
            for entry in raw_findings:
                if not isinstance(entry, dict):
                    continue
                fid = str(entry.get("id", "")).strip()
                status = str(entry.get("status", "")).strip().upper()
                if fid and status in ("VERIFIED", "FAILED"):
                    per_finding[fid] = status

            # Missing per-finding verdict → FAILED (fail-closed)
            domain_verdicts: dict[str, str] = {}
            for f in findings:
                domain_verdicts[f.id] = per_finding.get(f.id, "FAILED")

            verdicts[domain] = domain_verdicts

    return verdicts


def _commit_or_rollback(
    worktree: Path,
    verdicts: dict[str, dict[str, str]],
    pre_fixer_sha: str,
    run_dir: Path,
    cycle: int,
    config: Config,
) -> str | None:
    """Commit verifier-approved changes or rollback the worktree.

    - Empty verdicts → None (nothing to commit).
    - Any FAILED → ``git reset --hard <sha>`` + ``git clean -fd`` +
      rollback sentinel + escalation-exempt sidecar + backend restart +
      return None.
    - All VERIFIED → ``git diff --name-only <sha>`` → explicit
      ``git add -- <files>`` → commit → return SHA.
    """
    if not verdicts:
        return None

    failed: list[tuple[str, str]] = []
    for domain, domain_verdicts in verdicts.items():
        for fid, status in domain_verdicts.items():
            if status == "FAILED":
                failed.append((domain, fid))

    if failed:
        logger.warning(
            "Verifier reported %d FAILED finding(s) — rolling back cycle %d",
            len(failed), cycle,
        )
        for domain, fid in failed[:10]:
            logger.warning("  %s/%s", domain, fid)

        subprocess.run(
            ["git", "reset", "--hard", pre_fixer_sha],
            capture_output=True, text=True, cwd=str(worktree), check=True,
        )
        subprocess.run(
            ["git", "clean", "-fd"],
            capture_output=True, text=True, cwd=str(worktree), check=True,
        )

        sentinel = run_dir / f".cycle-{cycle}-rolled-back"
        lines = [
            f"cycle: {cycle}",
            f"pre_fixer_sha: {pre_fixer_sha}",
            f"failed_findings: {len(failed)}",
            "",
        ]
        for domain, fid in failed:
            lines.append(f"  {domain}/{fid}")
        sentinel.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Rolled-back findings do not burn the escalation counter
        exempt_ids = sorted({fid for _, fid in failed})
        exempt_sidecar = run_dir / f".escalation-exempt-{cycle}.txt"
        exempt_sidecar.write_text(
            "\n".join(exempt_ids) + "\n", encoding="utf-8",
        )

        try:
            restart_backend(config, worktree)
        except Exception:
            logger.warning(
                "Backend restart after rollback failed — "
                "next cycle may see stale state",
            )

        return None

    # All VERIFIED — proceed to commit
    diff_result = subprocess.run(
        ["git", "diff", "--name-only", pre_fixer_sha],
        capture_output=True, text=True, cwd=str(worktree),
    )
    if diff_result.returncode != 0:
        logger.warning(
            "git diff failed during commit pipeline: %s",
            diff_result.stderr.strip(),
        )
        return None

    changed_files = [f for f in diff_result.stdout.strip().splitlines() if f]
    if not changed_files:
        logger.info(
            "Cycle %d verified clean but no files changed — no commit", cycle,
        )
        return None

    # Explicit `git add <file>` — NEVER `git add -A` (would sweep harness/)
    subprocess.run(
        ["git", "add", "--", *changed_files],
        capture_output=True, text=True, cwd=str(worktree), check=True,
    )

    domains_str = ",".join(sorted(verdicts.keys()))
    commit_result = subprocess.run(
        ["git", "commit", "-m",
         f"harness: cycle {cycle} verified fixes ({domains_str})"],
        capture_output=True, text=True, cwd=str(worktree),
    )
    if commit_result.returncode != 0:
        logger.warning(
            "git commit failed: %s",
            commit_result.stderr.strip() or commit_result.stdout.strip(),
        )
        return None

    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=str(worktree),
    )
    return sha_result.stdout.strip() if sha_result.returncode == 0 else None


def _merge_fix_reports(
    cycle: int,
    active_domains: dict[str, Scorecard],
    run_dir: Path,
    commit_sha: str,
) -> Path:
    """Merge per-domain fix reports into ``fixes-{cycle}.md``.

    Produces a minimal YAML frontmatter (cycle + findings_addressed union)
    followed by the full text of each per-domain report.  The frontmatter
    is what ``count_finding_attempts()`` reads for escalation tracking.
    """
    all_addressed: list[str] = []
    body_parts: list[str] = []

    for domain in sorted(active_domains):
        report_path = run_dir / f"fixes-{cycle}-{domain.lower()}.md"
        if not report_path.exists():
            logger.warning("Fix report missing for domain %s (fixer may have crashed)", domain)
            continue
        text = report_path.read_text(encoding="utf-8")
        body_parts.append(text)
        # Extract findings_addressed from YAML frontmatter
        m = re.search(r"findings_addressed:\s*\[([^\]]*)\]", text)
        if m and m.group(1).strip():
            all_addressed.extend(x.strip() for x in m.group(1).split(",") if x.strip())

    header = (
        f"---\ncycle: {cycle}\n"
        f"findings_addressed: [{', '.join(all_addressed)}]\n"
        f"commit: {commit_sha}\n---\n"
    )
    merged_path = run_dir / f"fixes-{cycle}.md"
    merged_path.write_text(header + "\n".join(body_parts), encoding="utf-8")
    return merged_path


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------


def write_summary(
    run_dir: Path,
    config: Config,
    last_merged: Scorecard | None,
    completed_cycles: int,
    exit_reason: str,
    staging_branch: str,
    escalated_ids: set[str],
    *,
    tracks_used: list[str] | None = None,
) -> Path:
    """Generate ``summary.md`` in *run_dir* matching the bash heredoc format.

    Returns the path to the written file.
    """
    run_ts = run_dir.name
    dry_run_str = "true" if config.dry_run else "false"

    # Test scope line
    if config.dry_run:
        test_scope = "Track A / capability A1 only"
    else:
        test_scope = "full harness"

    # Final scorecard section
    if last_merged is not None:
        scorecard_text = last_merged.to_markdown(track_order=tracks_used)
    else:
        scorecard_text = "No merged scorecard was produced.\n"

    # Overlap warnings section (parallel fixer only)
    overlap_logs = sorted(run_dir.glob(".fixer-overlap-*.log"))
    if overlap_logs:
        overlap_lines = []
        for ol in overlap_logs:
            overlap_lines.append(f"- {ol.name}")
            for line in ol.read_text(encoding="utf-8").splitlines():
                if line.startswith("  "):
                    overlap_lines.append(f"  {line.strip()}")
        overlap_text = "\n".join(overlap_lines) + "\n"
    else:
        overlap_text = ""

    # Escalated findings section
    if escalated_ids:
        esc_lines = [
            f"The following finding IDs were auto-escalated by the harness "
            f"after {config.max_fix_attempts} or more unsuccessful fix attempts. "
            f"Human review required.\n",
        ]
        for eid in sorted(escalated_ids):
            esc_lines.append(f"- {eid}")
        escalated_text = "\n".join(esc_lines) + "\n"
    else:
        escalated_text = "None.\n"

    # Run artifacts section
    artifacts = sorted(p.name for p in run_dir.glob("*.md"))
    if artifacts:
        artifacts_text = "\n".join(f"- {a}" for a in artifacts) + "\n"
    else:
        artifacts_text = "(no markdown artifacts)\n"

    # Triage section
    triage_text = _render_triage(staging_branch)

    # Build overlap section (only if overlaps occurred)
    overlap_section = ""
    if overlap_text:
        overlap_section = f"## Overlap Warnings\n{overlap_text}\n"

    summary = (
        f"# Harness Run Summary\n"
        f"\n"
        f"- **Run**: {run_ts}\n"
        f"- **Engine**: {config.engine}\n"
        f"- **Cycles completed**: {completed_cycles} / {config.max_cycles}\n"
        f"- **Dry run**: {dry_run_str}\n"
        f"- **Test scope**: {test_scope}\n"
        f"- **Exit reason**: {exit_reason}\n"
        f"\n"
        f"## Final Scorecard\n"
        f"{scorecard_text}\n"
        f"{overlap_section}"
        f"## Escalated Findings\n"
        f"{escalated_text}\n"
        f"## Run Artifacts\n"
        f"{artifacts_text}\n"
        f"## Triage\n"
        f"{triage_text}"
    )

    summary_path = run_dir / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    return summary_path


def _render_triage(staging_branch: str) -> str:
    """Render the Triage section of the summary."""
    if not staging_branch:
        return "No staging branch (legacy mode).\n"

    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"main..{staging_branch}"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
        )
        ahead = int(result.stdout.strip()) if result.returncode == 0 else 0
    except (ValueError, OSError):
        ahead = 0

    if ahead > 0:
        return (
            f"- **Branch**: {staging_branch}\n"
            f"- **Commits ahead of main**: {ahead}\n"
            f"- Review: `git log --oneline main..{staging_branch}`\n"
            f"- Accept all: `git merge --ff-only {staging_branch}`\n"
            f"- Cherry-pick: `git cherry-pick <SHA>`\n"
            f"- Squash: `git merge --squash {staging_branch}`\n"
            f"- Discard: `git branch -D {staging_branch}`\n"
        )

    return "No fixer commits \u2014 branch is empty.\n"
