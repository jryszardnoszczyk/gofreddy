#!/usr/bin/env python3
"""Autoresearch production session runner.

Usage:
    run.py --domain geo semrush https://www.semrush.com     # Single domain
    run.py --domain geo,competitive                          # Multi domain (defaults)
    run.py                                                   # All 4 domains (parallel)
    run.py --resume                                          # Resume incomplete
    run.py --dry-run                                         # Print plan, don't run
    run.py --help                                            # Show usage
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Line-buffer parent stdout so iteration-progress prints flush live when the
# parent log is redirected to a file (non-TTY, otherwise block-buffered).
try:
    sys.stdout.reconfigure(line_buffering=True)
except (AttributeError, OSError):
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
ARCHIVE_SCRIPTS_DIR = SCRIPT_DIR / "scripts"
AUTORESEARCH_DIR = SCRIPT_DIR.parent.parent
if str(ARCHIVE_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_SCRIPTS_DIR))
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

from watchdog import (  # type: ignore
    POLL_INTERVAL_SECONDS,
    SNAPSHOT_INTERVAL_SECONDS,
    count_lines,
    is_phase_event,
    iter_new_result_entries,
)
from runtime import competitive as competitive_runtime  # type: ignore
from runtime import config as runtime_config  # type: ignore
from runtime import post_session as runtime_post_session  # type: ignore
from workflows import WORKFLOW_SPECS, get_workflow_spec  # type: ignore

# ── Harness imports ───────────────────────────────────────────────────────

from harness.agent import (  # type: ignore
    _terminate_subprocess,
    run_agent_session,
    spawn_agent_process,
)
from harness.backend import (  # type: ignore
    codex_sandbox,
    session_backend,
    session_model,
)
from harness.stall import (  # type: ignore
    count_kept_entries,
    count_phase_events,
    snapshot_state,
    state_changed,
)
from harness.telemetry import (  # type: ignore
    push_iteration,
    push_phase_event,
    tracking_end,
    tracking_start,
)
from harness.util import (  # type: ignore
    _run_script,
    acquire_lock,
    default_timeout_for_strategy,
    release_lock,
)

# ── Config (absorbs launcher.conf values) ──────────────────────────────────

# Phase 5 (Unit 11 sub-task 2): DOMAIN_CONFIG removed; resolve via
# `get_workflow_spec(domain).config` directly at the call site.
SESSION_MAX_ITER = runtime_config.SESSION_MAX_ITER
FRESH_MAX_TURNS = runtime_config.FRESH_MAX_TURNS
MAX_PARALLEL = runtime_config.MAX_PARALLEL

# ── Environment ────────────────────────────────────────────────────────────


def init_env():
    """Source .env, normalize local CLI/runtime env, and validate required tools."""
    repo_root = next((parent for parent in SCRIPT_DIR.parents if (parent / "cli" / "pyproject.toml").exists()), None)
    cli_root = repo_root / "cli" if repo_root else None

    # Make the repo-local Freddy package importable even when the globally
    # installed `freddy` console script points at a Python environment that does
    # not have the package installed. This keeps production autoresearch pinned
    # to the checked-out repo state instead of ambient machine state.
    if cli_root and cli_root.is_dir():
        existing_pythonpath = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
        cli_path = str(cli_root)
        if cli_path not in existing_pythonpath:
            os.environ["PYTHONPATH"] = os.pathsep.join([cli_path, *existing_pythonpath])

    env_file = SCRIPT_DIR / ".env"
    if not env_file.exists():
        # Walk up to repo root looking for .env
        for parent in SCRIPT_DIR.parents:
            candidate = parent / ".env"
            if candidate.exists():
                env_file = candidate
                break

    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                os.environ.setdefault(key, value)

    os.environ.pop("ANTHROPIC_API_KEY", None)

    # Codex session sandboxes have been more reliable against 127.0.0.1 than
    # localhost for the local Freddy API. Normalize to loopback early so every
    # downstream freddy subprocess inherits the same base URL.
    api_url = os.environ.get("FREDDY_API_URL", "").strip()
    if api_url.startswith("http://localhost:"):
        os.environ["FREDDY_API_URL"] = api_url.replace("http://localhost:", "http://127.0.0.1:", 1)
    elif api_url == "http://localhost":
        os.environ["FREDDY_API_URL"] = "http://127.0.0.1"

    if not shutil.which("freddy"):
        print("ERROR: freddy CLI not found in PATH", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            ["freddy", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            env=os.environ.copy(),
        )
    except Exception as exc:
        print(f"ERROR: freddy CLI failed to start: {exc}", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        print(f"ERROR: freddy CLI is not runnable in the current environment: {detail}", file=sys.stderr)
        sys.exit(1)


def configure_fresh_start(resume: bool):
    """Match launcher behavior: non-resume runs archive prior COMPLETE sessions."""
    if resume:
        os.environ.pop("AUTORESEARCH_FRESH", None)
    else:
        os.environ["AUTORESEARCH_FRESH"] = "true"


def resolve_domain_target(
    domain: str,
    client_override: str | None = None,
    context_override: str | None = None,
    *,
    allow_placeholder: bool = False,
) -> tuple[str, str, str | None]:
    return runtime_config.resolve_domain_target(
        domain,
        client_override=client_override,
        context_override=context_override,
        allow_placeholder=allow_placeholder,
    )


# ── Session Lifecycle ──────────────────────────────────────────────────────


def init_session(client: str, domain: str, context: str) -> Path:
    """Create dirs, render templates, findings init, resume safety. Returns session_dir."""
    cfg = get_workflow_spec(domain).config
    session_dir = SCRIPT_DIR / "sessions" / domain / client
    fresh = os.environ.get("AUTORESEARCH_FRESH", "false") == "true"

    # Fresh run: archive any prior session state, not only COMPLETE sessions.
    # Non-resume execution should start from a clean workspace regardless of
    # whether the previous attempt was complete, partial, or stale.
    if fresh and session_dir.exists() and any(session_dir.iterdir()):
        archive_dir = SCRIPT_DIR / "archived_sessions" / f"{datetime.now():%Y%m%d-%H%M%S}-{domain}-{client}"
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(session_dir), str(archive_dir))
        print(f"Archived prior session state -> {archive_dir}")

    # Archive retention: delete iteration logs + raw/*/ from archived_sessions
    # entries older than 30 days. Keep session_summary.json and any .jsonl
    # files — they're small and lineage consumers may reference them.
    archived_root = SCRIPT_DIR / "archived_sessions"
    if archived_root.exists():
        cutoff = time.time() - (30 * 86400)
        for entry in archived_root.iterdir():
            try:
                if not entry.is_dir() or entry.stat().st_mtime >= cutoff:
                    continue
            except OSError:
                continue
            for child in entry.rglob("*"):
                if not child.is_file():
                    continue
                if child.suffix in (".jsonl", ".json") or child.name == "session.md":
                    continue
                try:
                    child.unlink()
                except OSError:
                    continue

    # Fresh run: also purge the agent's workspace under current_runtime/sessions
    # so stale files from earlier runs can't pollute this one. This is the
    # agent workspace (not canonical scoring state), so we delete rather than
    # archive. Paired with the sync step that commits artifacts back to v006
    # after each iteration.
    if fresh:
        current_runtime_session_dir = (
            AUTORESEARCH_DIR / "archive" / "current_runtime" / "sessions" / domain / client
        )
        if current_runtime_session_dir.exists():
            shutil.rmtree(current_runtime_session_dir, ignore_errors=True)
            print(f"Purged current_runtime workspace -> {current_runtime_session_dir}")

        # Sweep stale empty-session dirs from OTHER lanes too. `init_session`
        # touches a 0-byte `results.jsonl` the moment it creates a session
        # shell, and those shells survive across runs when a variant launches
        # fewer lanes than present. Empty dirs break ad-hoc scoring (scorer
        # sees no results) and pollute diffs.
        #
        # Preserve populated and freshly-init'd sessions: (1) skip if
        # results.jsonl has content, (2) skip if the dir has any iteration
        # log (a real session started iterating), (3) skip if the dir was
        # touched within the last 15 minutes (a parallel evolve worker may
        # have just init'd it).
        sessions_root = AUTORESEARCH_DIR / "archive" / "current_runtime" / "sessions"
        if sessions_root.exists():
            now_ts = time.time()
            for results in sessions_root.glob("*/*/results.jsonl"):
                try:
                    stat = results.stat()
                except OSError:
                    continue
                if stat.st_size > 0:
                    continue
                other_client_dir = results.parent
                other_domain = other_client_dir.parent.name
                if (other_domain, other_client_dir.name) == (domain, client):
                    continue
                logs_dir = other_client_dir / "logs"
                if logs_dir.exists() and any(logs_dir.glob("iteration_*.log")):
                    continue
                if now_ts - stat.st_mtime < 900:
                    continue
                shutil.rmtree(other_client_dir, ignore_errors=True)
                print(f"Swept stale session dir -> {other_client_dir}")

    # Create subdirs
    for subdir in cfg.subdirs:
        (session_dir / subdir).mkdir(parents=True, exist_ok=True)

    session_md = session_dir / "session.md"

    # Resume safety: IN_PROGRESS -> RUNNING
    if session_md.exists():
        text = session_md.read_text()
        if "## Status: IN_PROGRESS" in text:
            print("Previous session interrupted. Resetting to RUNNING for resume.")
            session_md.write_text(text.replace("## Status: IN_PROGRESS", "## Status: RUNNING"))

    # Initialize session.md from template
    if not session_md.exists():
        template = SCRIPT_DIR / "templates" / domain / "session.md"
        if template.exists():
            text = template.read_text()
            text = _render_template(text, client, context, domain)
            session_md.parent.mkdir(parents=True, exist_ok=True)
            session_md.write_text(text)
            print(f"Initialized {session_md}")

    # Initialize results.jsonl
    (session_dir / "results.jsonl").touch()

    # Initialize findings.md from template
    findings_md = session_dir / "findings.md"
    if not findings_md.exists():
        findings_template = SCRIPT_DIR / "templates" / domain / "findings.md"
        if findings_template.exists():
            text = findings_template.read_text()
            text = text.replace("{client}", client)
            findings_md.write_text(text)
            print(f"Initialized {findings_md}")

    # Create logs directory
    (session_dir / "logs").mkdir(exist_ok=True)

    return session_dir


def _render_template(text: str, client: str, context: str, _domain: str = "") -> str:
    """Render template variables."""
    return runtime_config.render_template(text, client, context, _domain)


def is_complete(session_dir: Path, domain: str | None = None) -> bool:
    return runtime_config.is_complete(session_dir, domain)


def is_blocked(session_dir: Path) -> bool:
    return runtime_config.is_blocked(session_dir)


def configure_domain_env(domain: str, client: str):
    """Apply domain-specific environment variables."""
    runtime_config.configure_domain_env(domain, client)


def reset_interrupted_session(session_dir: Path):
    """Resume safety for abnormal multi-turn exits."""
    runtime_config.reset_interrupted_session(session_dir)


# ── Agent Invocation ───────────────────────────────────────────────────────


def render_prompt(program_path: Path, client: str, context: str, domain: str,
                  strategy: str = "multiturn") -> str:
    """Template rendering + append global findings + strategy override."""
    return runtime_config.render_prompt(
        SCRIPT_DIR,
        program_path,
        client,
        context,
        domain,
        strategy=strategy,
        session_backend=session_backend,
        session_model=session_model,
    )


# ── Iteration Contract Enforcement ────────────────────────────────────────


def _count_results_lines(session_dir: Path) -> int:
    """Return line count of results.jsonl, or 0 if the file does not exist."""
    results_file = session_dir / "results.jsonl"
    if not results_file.exists():
        return 0
    try:
        with results_file.open() as fh:
            return sum(1 for line in fh if line.strip())
    except OSError:
        return 0


def _normalize_new_results(
    session_dir: Path, iteration: int, lines_before: int
) -> None:
    """Post-write normalizer for entries appended during current iteration.

    Injects `iteration` metadata when missing so cross-iteration grouping
    (summarize_session, eval_session) can correlate entries. Warns on
    missing `type` or `status` so schema drift is visible in parent log.
    Only touches entries written during this iteration (offset-tracked) --
    never rewrites prior entries. Never alters agent-authored payload keys.
    """
    import json as _json
    results_file = session_dir / "results.jsonl"
    if not results_file.exists():
        return
    try:
        lines = results_file.read_text().splitlines()
    except OSError:
        return
    if len(lines) <= lines_before:
        return

    new_slice = lines[lines_before:]
    mutated = False
    for idx, raw in enumerate(new_slice):
        line = raw.strip()
        if not line:
            continue
        try:
            entry = _json.loads(line)
        except _json.JSONDecodeError:
            print(
                f"WARNING: results.jsonl line {lines_before + idx + 1} is not valid JSON; skipping normalization.",
                file=sys.stderr,
            )
            continue
        changed = False
        if "iteration" not in entry:
            entry["iteration"] = iteration
            changed = True
        for required in ("type", "status"):
            if required not in entry:
                print(
                    f"WARNING: iteration {iteration} results.jsonl entry missing '{required}' key: {line[:120]}",
                    file=sys.stderr,
                )
        if changed:
            new_slice[idx] = _json.dumps(entry)
            mutated = True

    if mutated:
        combined = lines[:lines_before] + new_slice
        try:
            results_file.write_text("\n".join(combined) + "\n")
        except OSError as exc:
            print(f"WARNING: failed to persist normalized results.jsonl: {exc}", file=sys.stderr)


def enforce_iteration_contract(
    domain: str,
    iteration: int,
    session_dir: Path,
    log_path: Path,
    results_lines_before: int,
) -> None:
    """Harness self-diagnostics for known agent-compliance drift patterns.

    These checks emit warnings (non-fatal) when the runner detects the
    exact failure modes the run #5/#6 forensic uncovered. Program-level
    prompt text alone did not prevent these drifts, so the runner now
    treats them as structural defects worth surfacing.

    Checks:
      1. `results.jsonl` did not grow this iteration -- the agent skipped
         the LOG step (broke geo OPTIMIZE in run #5, monitoring low-volume
         path in run #6).
      2. Monitoring-only: `freddy digest persist` was only invoked with
         `--help`, never with a real argument payload (agent drift in
         run #6 iter 2).
    """
    results_lines_after = _count_results_lines(session_dir)
    if results_lines_after == results_lines_before:
        print(
            (
                f"INFO: iteration {iteration} wrote no phase event in this call "
                f"(may complete in the next iteration). "
                f"Expected schema: {{'iteration': {iteration}, 'type': ..., 'status': ...}}. "
                f"File: {session_dir / 'results.jsonl'}"
            ),
            file=sys.stderr,
        )

    if domain == "monitoring" and log_path.exists():
        try:
            log_text = log_path.read_text(errors="replace")
        except OSError:
            log_text = ""
        if log_text:
            help_invocations = log_text.count("freddy digest persist --help")
            total_invocations = log_text.count("freddy digest persist")
            if help_invocations > 0 and help_invocations == total_invocations:
                print(
                    (
                        f"WARNING: iteration {iteration} invoked "
                        f"`freddy digest persist --help` but never the actual "
                        f"persist command. The weekly digest was not saved to "
                        f"the backend, and a subsequent week's LOAD_CONTEXT "
                        f"will miss this week's context."
                    ),
                    file=sys.stderr,
                )


# ── Post-Session Hooks ────────────────────────────────────────────────────


_SYNC_SKIP_NAMES = {"logs", ".progress_snapshot", ".session_snapshot"}


def _sync_agent_workspace(domain: str, client: str) -> None:
    """Copy agent output from current_runtime/sessions → v006/sessions.

    Preserves workspace/scorer separation per Meta-Harness §5: agent writes
    live in current_runtime (messy iterative state), canonical artifacts
    land in v006/sessions so the scorer reads a complete view. Idempotent
    and fails silently if the source is empty (no agent activity yet).

    Skipped paths: logs/ (each dir owns its own), *.tmp (atomic-write
    partials), .progress_snapshot / .session_snapshot (runner-local state).
    """
    src = AUTORESEARCH_DIR / "archive" / "current_runtime" / "sessions" / domain / client
    dst = SCRIPT_DIR / "sessions" / domain / client
    if not src.exists():
        return
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        if path.name.endswith(".tmp"):
            continue
        if any(part in _SYNC_SKIP_NAMES for part in rel.parts):
            continue
        target = dst / rel
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        except OSError as exc:
            print(
                f"WARNING: sync failed for {rel}: {exc}", file=sys.stderr,
            )


def post_session_hooks(domain: str, session_dir: Path, client: str):
    """Domain-specific post-session logic."""
    _sync_agent_workspace(domain, client)
    runtime_post_session.post_session_hooks(
        domain,
        session_dir,
        client,
        run_script=_run_script,
        is_complete=is_complete,
    )
    # Clear the CLI session-id cache so the next autoresearch run starts fresh
    # without emitting `HTTP 409 Action logging failed` against a stale session.
    cli_session_file = Path.home() / ".freddy" / "session.json"
    cli_session_file.unlink(missing_ok=True)
    # Sweep any atomic-write partials the agent left under current_runtime.
    current_runtime_session_dir = (
        AUTORESEARCH_DIR / "archive" / "current_runtime" / "sessions" / domain / client
    )
    if current_runtime_session_dir.exists():
        for tmp_file in current_runtime_session_dir.rglob("*.tmp"):
            tmp_file.unlink(missing_ok=True)


# ── Single Domain Runner ──────────────────────────────────────────────────


def run_domain_fresh(domain: str, client: str, context: str, max_iter: int,
                     timeout: int, no_confirm: bool = False) -> int:
    """Current fresh-restart loop preserved for evaluation and fallback."""
    cfg = get_workflow_spec(domain).config
    subdirs = cfg.subdirs
    stall_limit = cfg.stall_limit or 5
    max_turns = cfg.fresh_max_turns or FRESH_MAX_TURNS
    max_wall_time = cfg.max_wall_time_seconds
    backend = session_backend()
    model = session_model()

    lock_fd = acquire_lock(domain, client)
    if lock_fd is None:
        return 0

    configure_domain_env(domain, client)
    os.environ["AUTORESEARCH_CONTEXT"] = context
    os.environ["AUTORESEARCH_STRATEGY"] = "fresh"
    os.environ["MAX_ITER"] = str(max_iter)
    os.environ["AUTORESEARCH_TIMEOUT_SECONDS"] = str(timeout)

    session_dir = init_session(client, domain, context)
    program = SCRIPT_DIR / "programs" / f"{domain}-session.md"
    if not program.exists():
        print(f"ERROR: Program not found: {program}", file=sys.stderr)
        release_lock(lock_fd, domain, client)
        return 0

    session_id = tracking_start(client, "autoresearch", f"{domain.upper()} session: {context}")
    log_dir = session_dir / "logs"

    print(f"Starting {domain.upper()} session for {client} ({context}) [fresh]")
    print(f"Agent: {backend} ({model})")
    print(f"Max iterations: {max_iter}, Timeout: {timeout}s")
    print(f"Session dir: {session_dir}")
    print("---")

    from watchdog import TERMINATION_GRACE_SECONDS  # type: ignore

    fail_count = 0
    stall_count = 0
    guard_reentries = 0
    i = 0
    session_start = time.monotonic()

    for i in range(1, max_iter + 1):
        print(f"[Iteration {i}/{max_iter}]")

        if is_complete(session_dir, domain):
            # Run completion guard INSIDE the loop so it can trigger rework
            # iterations. Prior behavior: guard ran only in post_session_hooks
            # after the loop exited, which could downgrade COMPLETE→RUNNING
            # but had no way to spawn the next subprocess for rework —
            # leaving sessions like storyboard/Gossip.Goblin stranded in
            # RUNNING state. The guard runs the agent's OWN session-evaluator
            # (workspace-local), not the external `freddy evaluate variant`
            # scorer, so this does not leak scorer info to the agent.
            try:
                eval_summary = runtime_post_session.snapshot_session_evaluations(
                    domain, session_dir, _run_script
                )
                runtime_post_session.enforce_completion_guard(
                    domain, session_dir, eval_summary,
                    is_complete=lambda d: is_complete(d, domain),
                )
            except Exception as guard_exc:
                print(
                    f"WARNING: in-loop completion guard failed: {guard_exc}; "
                    "accepting declared COMPLETE.", file=sys.stderr,
                )
                print("Session complete.")
                break
            if is_complete(session_dir, domain):
                print("Session complete (guard validated).")
                break
            guard_reentries += 1
            print(
                f"Completion guard downgraded COMPLETE → RUNNING "
                f"(rework #{guard_reentries}/3). Continuing loop.",
                file=sys.stderr,
            )
            if guard_reentries >= 3:
                print(
                    "CRITICAL: completion guard keeps downgrading after 3 "
                    "reworks — exiting with BLOCKED status.", file=sys.stderr,
                )
                session_md = session_dir / "session.md"
                if session_md.exists():
                    try:
                        text = session_md.read_text()
                        if "## Status: RUNNING" in text:
                            session_md.write_text(
                                text.replace("## Status: RUNNING", "## Status: BLOCKED", 1)
                            )
                    except OSError:
                        pass
                break

        snapshot_state(session_dir, subdirs, domain)
        log_path = log_dir / f"iteration_{i:03d}.log"
        results_lines_before_iter = _count_results_lines(session_dir)
        prompt = render_prompt(program, client, context, domain, strategy="fresh")
        start = time.monotonic()
        initial_phase_count = count_phase_events(domain, session_dir)
        process, log_handle = spawn_agent_process(prompt, log_path, model, max_turns)
        phase_completed = False
        exit_code = 0
        try:
            while True:
                try:
                    exit_code = process.wait(timeout=2)
                    break
                except subprocess.TimeoutExpired:
                    current_phase_count = count_phase_events(domain, session_dir)
                    if current_phase_count > initial_phase_count or is_complete(session_dir, domain) or is_blocked(session_dir):
                        phase_completed = current_phase_count > initial_phase_count or is_complete(session_dir, domain) or is_blocked(session_dir)
                        _terminate_subprocess(process, "fresh phase complete")
                        exit_code = process.wait(timeout=TERMINATION_GRACE_SECONDS)
                        break
                    if time.monotonic() - start > timeout:
                        _terminate_subprocess(process, "timeout")
                        exit_code = 124
                        break
        finally:
            log_handle.close()

        current_phase_count = count_phase_events(domain, session_dir)
        if (
            domain == "competitive"
            and not phase_completed
            and current_phase_count == initial_phase_count
            and not is_complete(session_dir, domain)
            and not is_blocked(session_dir)
        ):
            if competitive_runtime.salvage_competitive_gather(session_dir, client, context, i):
                phase_completed = True
                exit_code = 0
                print("Recovered competitive gather state from raw evidence.")

        # Sync agent workspace → canonical before we evaluate state.
        # This lets state_changed/count_phase_events see the latest files and
        # ensures the scorer has the full picture if we stop early.
        _sync_agent_workspace(domain, client)

        if phase_completed and exit_code not in {0, 124}:
            exit_code = 0
        duration_ms = int((time.monotonic() - start) * 1000)
        push_iteration(session_id, i, session_dir, exit_code, duration_ms, log_path)
        # Schema normalizer: inject `iteration` into new entries missing it
        # (monitoring agent drift), warn on missing `type`/`status`.
        _normalize_new_results(session_dir, i, results_lines_before_iter)
        # Harness self-diagnostics (non-fatal warnings) -- catches known
        # agent-compliance drift patterns from run #5 (geo LOG skip) and
        # run #6 (monitoring `freddy digest persist --help`-only).
        enforce_iteration_contract(
            domain, i, session_dir, log_path, results_lines_before_iter,
        )

        if domain == "geo" and is_blocked(session_dir):
            print("Session BLOCKED (site unreachable). Stopping.")
            break

        if exit_code != 0:
            fail_count += 1
            print(f"Iteration {i} failed (exit {exit_code}). Failures: {fail_count}/3")
            if fail_count >= 3:
                print("Circuit breaker: 3 consecutive failures. Stopping.")
                break
        else:
            fail_count = 0

        if state_changed(session_dir, subdirs, domain):
            stall_count = 0
        else:
            stall_count += 1
            print(f"No new phase type or file growth. Stall: {stall_count}/{stall_limit}")
            if stall_count >= stall_limit:
                print(f"Stall detected: {stall_limit} iterations without progress. Stopping.")
                break

        if max_wall_time:
            elapsed_seconds = time.monotonic() - session_start
            if elapsed_seconds > max_wall_time:
                print(f"Wall-time limit reached ({elapsed_seconds:.0f}s > {max_wall_time}s). Stopping.")
                break

    post_session_hooks(domain, session_dir, client)

    for f in [session_dir / ".progress_snapshot", session_dir / ".session_snapshot"]:
        f.unlink(missing_ok=True)

    total = min(i, max_iter)
    kept = count_kept_entries(session_dir)
    tracking_end(session_id, f"{domain.upper()} session for {client}: {total} iterations, {kept} kept")

    release_lock(lock_fd, domain, client)

    print("---")
    print(f"Session finished. Results in: {session_dir}/")
    return total


def run_domain_multiturn(domain: str, client: str, context: str, timeout: int) -> int:
    """Continuous multi-turn session with watchdog safety and telemetry."""
    cfg = get_workflow_spec(domain).config
    subdirs = cfg.subdirs
    stall_limit = cfg.stall_limit or 5
    max_turns = cfg.multiturn_max_turns or 2500
    max_wall_time = cfg.max_wall_time_seconds
    backend = session_backend()
    model = session_model()

    lock_fd = acquire_lock(domain, client)
    if lock_fd is None:
        return 0

    configure_domain_env(domain, client)
    os.environ["AUTORESEARCH_CONTEXT"] = context
    os.environ["AUTORESEARCH_STRATEGY"] = "multiturn"
    os.environ["AUTORESEARCH_TIMEOUT_SECONDS"] = str(timeout)

    session_dir = init_session(client, domain, context)
    program = SCRIPT_DIR / "programs" / f"{domain}-session.md"
    if not program.exists():
        print(f"ERROR: Program not found: {program}", file=sys.stderr)
        release_lock(lock_fd, domain, client)
        return 0

    session_id = tracking_start(client, "autoresearch", f"{domain.upper()} session: {context}")
    log_dir = session_dir / "logs"
    log_path = log_dir / "multiturn_session.log"
    prompt = render_prompt(program, client, context, domain, strategy="multiturn")

    print(f"Starting {domain.upper()} session for {client} ({context}) [multiturn]")
    print(f"Agent: {backend} ({model})")
    print(f"Timeout: {timeout}s | Max turns: {max_turns}")
    print(f"Session dir: {session_dir}")
    print("---")

    start_monotonic = time.monotonic()
    results_file = session_dir / "results.jsonl"
    process, log_handle = spawn_agent_process(prompt, log_path, model, max_turns)

    snapshot_state(session_dir, subdirs, domain)
    state = {
        "stop": threading.Event(),
        "stop_reason": None,
        "processed_lines": count_lines(results_file),
        "phase_events": count_phase_events(domain, session_dir),
        "stall_count": 0,
        "last_snapshot_at": start_monotonic,
        "last_phase_at": start_monotonic,
    }

    def drain_new_results(now: float):
        new_entries, next_line = iter_new_result_entries(results_file, state["processed_lines"])
        state["processed_lines"] = next_line
        for _, raw_line, entry in new_entries:
            if not is_phase_event(domain, entry):
                continue
            state["phase_events"] += 1
            duration_ms = int((now - state["last_phase_at"]) * 1000)
            push_phase_event(session_id, state["phase_events"], session_dir, raw_line, entry, duration_ms, log_path)
            state["last_phase_at"] = now

    def watchdog_loop():
        while not state["stop"].is_set():
            now = time.monotonic()
            drain_new_results(now)

            if now - state["last_snapshot_at"] >= SNAPSHOT_INTERVAL_SECONDS:
                if state_changed(session_dir, subdirs, domain):
                    state["stall_count"] = 0
                else:
                    state["stall_count"] += 1
                    print(f"No progress detected. Stall: {state['stall_count']}/{stall_limit}")
                    if state["stall_count"] >= stall_limit and state["stop_reason"] is None:
                        state["stop_reason"] = "stall"
                        _terminate_subprocess(process, "stall")
                        break
                snapshot_state(session_dir, subdirs, domain)
                state["last_snapshot_at"] = now

            elapsed = now - start_monotonic
            if max_wall_time and elapsed > max_wall_time and state["stop_reason"] is None:
                state["stop_reason"] = "wall-time ceiling"
                _terminate_subprocess(process, "wall-time ceiling")
                break

            if elapsed > timeout and state["stop_reason"] is None:
                state["stop_reason"] = "timeout"
                _terminate_subprocess(process, "timeout")
                break

            if is_blocked(session_dir) and process.poll() is None and state["stop_reason"] is None:
                state["stop_reason"] = "blocked"
                _terminate_subprocess(process, "blocked")
                break

            if process.poll() is not None:
                break

            state["stop"].wait(POLL_INTERVAL_SECONDS)

    watchdog = threading.Thread(target=watchdog_loop, daemon=True)
    watchdog.start()

    exit_code = process.wait()
    state["stop"].set()
    watchdog.join(timeout=30)
    drain_new_results(time.monotonic())
    log_handle.close()

    if state["stop_reason"] == "timeout":
        exit_code = 124

    if exit_code != 0 and not is_complete(session_dir, domain):
        reset_interrupted_session(session_dir)

    post_session_hooks(domain, session_dir, client)

    total = state["phase_events"]
    kept = count_kept_entries(session_dir)
    tracking_end(session_id, f"{domain.upper()} session for {client}: {total} phase events, {kept} kept")

    release_lock(lock_fd, domain, client)

    print("---")
    print(f"Session finished. Results in: {session_dir}/")
    return total


def run_domain(domain: str, client: str, context: str, max_iter: int,
               timeout: int, no_confirm: bool = False, strategy: str = "multiturn") -> int:
    """Run one domain in fresh or multi-turn mode."""
    if strategy == "fresh":
        return run_domain_fresh(domain, client, context, max_iter, timeout, no_confirm)
    return run_domain_multiturn(domain, client, context, timeout)


# ── Orchestrator ───────────────────────────────────────────────────────────


def run_all(domains: list[str], max_parallel: int = MAX_PARALLEL,
            max_iter: int = SESSION_MAX_ITER, resume: bool = False,
            dry_run: bool = False, no_confirm: bool = False,
            strategy: str = "multiturn"):
    """Parallel domain execution for the production archive runner."""
    run_dir = SCRIPT_DIR / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")

    tasks = []
    for domain in domains:
        client, context, warning = resolve_domain_target(domain, allow_placeholder=dry_run)
        timeout = default_timeout_for_strategy(domain, strategy)

        # Check skip-completed markers
        done_marker = run_dir / f"{domain}.done"
        if resume and done_marker.exists():
            print(f"Skipping {domain} (already completed)")
            continue

        tasks.append((domain, client, context, max_iter, timeout, no_confirm, strategy, warning))

    if dry_run:
        print("=== DRY RUN ===")
        for domain, client, context, mi, to, nc, strat, warning in tasks:
            print(f"  {domain}: client={client}, context={context}, max_iter={mi}, timeout={to}, strategy={strat}")
            if warning:
                print(f"    WARNING: {warning}")
        print(f"Parallel: {max_parallel}")
        print(f"Run dir: {run_dir}")
        return

    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting {len(tasks)} domains (parallel={max_parallel})")
    print(f"Run dir: {run_dir}")
    print(f"Strategy: {strategy}")
    print("===")

    if max_parallel <= 1 or len(tasks) <= 1:
        for domain, client, context, mi, to, nc, strat, _warning in tasks:
            total = run_domain(domain, client, context, mi, to, nc, strat)
            (run_dir / f"{domain}.done").write_text(str(total))
    else:
        with ProcessPoolExecutor(max_workers=max_parallel) as executor:
            futures = {}
            for domain, client, context, mi, to, nc, strat, _warning in tasks:
                f = executor.submit(run_domain, domain, client, context, mi, to, nc, strat)
                futures[f] = domain
            for future in as_completed(futures):
                domain = futures[future]
                try:
                    total = future.result()
                    (run_dir / f"{domain}.done").write_text(str(total))
                    print(f"=== {domain} finished: {total} iterations ===")
                except Exception as e:
                    (run_dir / f"{domain}.failed").write_text(str(e))
                    print(f"=== {domain} FAILED: {e} ===")

    print("===")
    print(f"All domains complete. Run dir: {run_dir}")


# ── CLI ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Autoresearch session runner")
    parser.add_argument("--domain", type=str, default=None,
                        help="Domain(s) to run, comma-separated (default: all)")
    parser.add_argument("--strategy", choices=["fresh", "multiturn"], default="multiturn",
                        help="Execution strategy: fresh restart loop or continuous multi-turn session")
    parser.add_argument("--backend", choices=["claude", "codex"], default=None,
                        help="Agent backend for session execution")
    parser.add_argument("--model", type=str, default=None,
                        help="Agent model override for the selected backend")
    parser.add_argument("--reasoning-effort", type=str, default=None,
                        help="Codex reasoning effort override")
    parser.add_argument("--resume", action="store_true", help="Resume incomplete sessions")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without running")
    parser.add_argument("--no-confirm", action="store_true", help="Skip interactive confirmations")
    parser.add_argument("client", nargs="?", help="Client name (required for single domain)")
    parser.add_argument("context", nargs="?", help="Context (URL, UUID, etc.)")
    parser.add_argument("max_iter", nargs="?", type=int, default=SESSION_MAX_ITER, help="Max iterations")
    parser.add_argument("timeout", nargs="?", type=int, default=None, help="Timeout in seconds")

    args = parser.parse_args()

    # Determine domains
    if args.domain:
        domains = [d.strip() for d in args.domain.split(",")]
        for d in domains:
            if d not in WORKFLOW_SPECS:
                parser.error(f"Unknown domain: {d}")
    else:
        domains = list(WORKFLOW_SPECS.keys())

    init_env()
    if args.backend:
        os.environ["AUTORESEARCH_SESSION_BACKEND"] = args.backend
    if args.model:
        os.environ["AUTORESEARCH_SESSION_MODEL"] = args.model
    if args.reasoning_effort:
        os.environ["AUTORESEARCH_SESSION_REASONING_EFFORT"] = args.reasoning_effort
    configure_fresh_start(args.resume)

    if codex_sandbox() == "danger-full-access":
        print("┌──────────────────────────────────────────────────────────┐")
        print("│  WARNING: AUTORESEARCH_SESSION_SANDBOX=danger-full-access│")
        print("│  The session agent has full host access. It can read,    │")
        print("│  write, and execute anything on this machine.            │")
        print("└──────────────────────────────────────────────────────────┘")

    # Single domain with explicit client/context
    if len(domains) == 1 and args.client:
        client, context, warning = resolve_domain_target(
            domains[0],
            client_override=args.client,
            context_override=args.context,
            allow_placeholder=args.dry_run,
        )
        timeout = args.timeout or default_timeout_for_strategy(domains[0], args.strategy)
        if args.dry_run:
            print(f"=== DRY RUN ===\n  {domains[0]}: client={client}, context={context}, "
                  f"max_iter={args.max_iter}, timeout={timeout}, strategy={args.strategy}")
            if warning:
                print(f"  WARNING: {warning}")
            return
        run_domain(domains[0], client, context,
                   args.max_iter, timeout, args.no_confirm, args.strategy)
    else:
        # Multi-domain orchestration
        run_all(domains, MAX_PARALLEL, args.max_iter, args.resume, args.dry_run, args.no_confirm, args.strategy)


if __name__ == "__main__":
    # Handle signals gracefully
    signal.signal(signal.SIGINT, lambda *_: sys.exit(130))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    main()
