"""Argparse entry point: parses flags, builds Config, invokes run."""
from __future__ import annotations

import argparse
import sys

from harness.config import Config, ConfigError
from harness.run import run


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="harness", description="GoFreddy QA harness — free-roaming preservation-first agents.",
    )
    p.add_argument("--engine", choices=["claude", "codex"], default=None,
                   help="Agent CLI to invoke for evaluator/fixer/verifier (default claude).")
    p.add_argument("--claude-mode", choices=["oauth", "bare"], default=None,
                   help=(
                       "Claude auth mode: oauth uses subscription + 5h limit + ~37K preamble tokens per call; "
                       "bare uses ANTHROPIC_API_KEY, skips preamble, no 5h cap. Default oauth."
                   ))
    p.add_argument("--eval-model", type=str, default=None, help="Claude model for evaluator role (default opus).")
    p.add_argument("--fixer-model", type=str, default=None, help="Claude model for fixer role (default opus).")
    p.add_argument("--verifier-model", type=str, default=None, help="Claude model for verifier role (default opus).")
    p.add_argument("--resume-branch", type=str, default=None,
                   help="Reattach to an existing harness branch (from a prior graceful-stop run) and continue.")
    p.add_argument("--keep-worktree", action="store_true", help="Do not delete staging worktree on exit.")
    p.add_argument("--max-walltime", type=int, default=None, help="Hard walltime in seconds (default 14400).")
    p.add_argument("--backend-port", type=int, default=None, help="Port for uvicorn (default 8000).")
    p.add_argument("--staging-root", type=str, default=None, help="Root for per-run staging dirs (default harness/runs).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = Config.from_cli_and_env(args)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
