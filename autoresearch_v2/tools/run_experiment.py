"""autoresearch_v2/tools/run_experiment.py — invoke v006/run.py for one experiment.

Wraps `autoresearch/archive/v006/run.py` as a subprocess. The session loop
itself is NOT rewritten in v2 (per Plan B's "wrap don't rewrite" decision);
this tool is a thin invocation harness that:

- builds the argv per the v006/run.py contract
- enforces a wall-clock timeout
- captures exit code + last N chars of stdout
- inspects the resulting session_dir for a `session.md` (the basic
  "session-actually-ran" marker) so callers can distinguish "variant
  produced no output" (variant-generation failure, Bug 3 class) from
  "variant produced low-scoring output"

Returns a JSON record so the caller (`autoresearch.md` driver or higher-level
tool) can decide keep/discard.

Env passthrough (NOT consumed here; just inherited from os.environ):
- EVAL_BACKEND_OVERRIDE, EVAL_MODEL_OVERRIDE
- MAX_PARALLEL_AGENTS (U2 itself is sequential; concurrency wires in U8)
- AUTORESEARCH_CONTEXT, AUTORESEARCH_SESSION_DIR
- X_ENGINE_ANGLE_ID / LINKEDIN_ENGINE_ANGLE_ID (set by v007-curated workflows)
- Stream A flags (AUTORESEARCH_EVAL_FIX_*)

Usage:
    run_experiment --domain geo --client mayoclinic --context https://example.com \\
        --max-iter 30 --timeout 1800
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

VALID_LANES = frozenset({
    "geo",
    "competitive",
    "monitoring",
    "storyboard",
    "marketing_audit",
    "x_engine",
    "linkedin_engine",
})

DEFAULT_STRATEGY_PER_LANE = {
    "marketing_audit": "fresh",
    # Others default to "multiturn"; see v006/run.py:1161 + Unit 3 of plan-mode plan.
}
_DEFAULT_FALLBACK_STRATEGY = "multiturn"

_STDOUT_TAIL_CHARS = 2000
_TIMEOUT_EXIT_CODE = 124


def _repo_root() -> Path:
    override = os.environ.get("AUTORESEARCH_V2_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _v006_runpy() -> Path:
    return _repo_root() / "autoresearch" / "archive" / "v006" / "run.py"


def _default_session_root() -> Path:
    return _repo_root() / "autoresearch" / "archive" / "v006" / "sessions"


def _resolve_strategy(lane: str, override: str | None) -> str:
    if override:
        return override
    return DEFAULT_STRATEGY_PER_LANE.get(lane, _DEFAULT_FALLBACK_STRATEGY)


def _deliverable_present(session_dir: Path) -> bool:
    """v006/run.py writes session.md as its first artifact; its absence means
    the variant did not produce any output (Bug 3 class).
    """
    return (session_dir / "session.md").is_file()


def run_experiment(
    *,
    domain: str,
    client: str,
    context: str,
    max_iter: int,
    timeout: int,
    strategy: str | None = None,
    session_root: Path | None = None,
    extra_env: dict | None = None,
    runner: list[str] | None = None,
) -> dict:
    if domain not in VALID_LANES:
        raise ValueError(f"unknown lane {domain!r}; valid: {sorted(VALID_LANES)}")
    if not client or "/" in client:
        raise ValueError(f"invalid client {client!r}")
    if max_iter < 1:
        raise ValueError(f"max_iter must be >= 1, got {max_iter}")
    if timeout < 1:
        raise ValueError(f"timeout must be >= 1, got {timeout}")

    resolved_strategy = _resolve_strategy(domain, strategy)
    base_runner = runner if runner is not None else [sys.executable, str(_v006_runpy())]
    argv = [
        *base_runner,
        "--domain", domain,
        "--strategy", resolved_strategy,
        "--no-confirm",
        client,
        context,
        str(max_iter),
        str(timeout),
    ]

    env = os.environ.copy()
    if extra_env:
        env.update({k: str(v) for k, v in extra_env.items()})

    root = session_root if session_root is not None else _default_session_root()
    session_dir = root / domain / client

    start = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=_repo_root(),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout + 30,  # subprocess hard ceiling = inner timeout + grace
            check=False,
        )
        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        exit_code = _TIMEOUT_EXIT_CODE
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
    wall_time_s = time.monotonic() - start

    tail_source = stderr if exit_code not in (0,) and stderr else stdout
    stdout_tail = tail_source[-_STDOUT_TAIL_CHARS:] if tail_source else ""

    return {
        "domain": domain,
        "client": client,
        "context": context,
        "strategy": resolved_strategy,
        "session_dir": str(session_dir),
        "exit_code": exit_code,
        "wall_time_seconds": round(wall_time_s, 3),
        "deliverable_present": _deliverable_present(session_dir),
        "stdout_tail": stdout_tail,
        "timed_out": exit_code == _TIMEOUT_EXIT_CODE,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Invoke v006/run.py for one experiment and report a JSON result.",
    )
    p.add_argument("--domain", required=True, choices=sorted(VALID_LANES))
    p.add_argument("--client", required=True)
    p.add_argument("--context", required=True, help="URL or fixture identifier passed to run.py")
    p.add_argument("--max-iter", type=int, required=True)
    p.add_argument("--timeout", type=int, required=True, help="Per-session wall-clock budget (seconds)")
    p.add_argument("--strategy", default=None,
                   help="multiturn | fresh; default chosen per lane (marketing_audit=fresh)")
    args = p.parse_args(argv)

    try:
        result = run_experiment(
            domain=args.domain,
            client=args.client,
            context=args.context,
            max_iter=args.max_iter,
            timeout=args.timeout,
            strategy=args.strategy,
        )
    except ValueError as e:
        sys.stderr.write(f"run_experiment: error: {e}\n")
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["exit_code"] == 0 and result["deliverable_present"] else 1


if __name__ == "__main__":
    sys.exit(main())
