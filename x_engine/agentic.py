"""Agentic compose — master codex session orchestrates the whole pipeline.

In contrast to pipeline/compose.py (Python orchestrates, codex is one tool),
this entrypoint hands the orchestration TO codex. Codex reads voice + sources,
decides what to pull, picks angles, spawns parallel `xeng draft-angle` subagents
via shell `&`, and writes outputs.

Usage:
    uv run python -m x_engine.agentic                # default
    uv run python -m x_engine.agentic --effort medium
    uv run python -m x_engine.agentic --max-time 600 # seconds before kill

Master prompt: x_engine/prompts/agentic_master.md
Tool surface: `xeng <subcommand>` (see x_engine/cli.py)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

X_ENGINE_DIR = Path(__file__).parent
GOFREDDY_DIR = X_ENGINE_DIR.parent
MASTER_PROMPT_PATH = X_ENGINE_DIR / "prompts" / "agentic_master.md"

CODEX_BIN = os.environ.get("X_ENGINE_CODEX_BIN", "codex")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="x_engine agentic compose")
    parser.add_argument(
        "--effort", default=os.environ.get("X_ENGINE_REASONING_EFFORT", "medium"),
        choices=["minimal", "low", "medium", "high", "xhigh"],
        help="reasoning effort for the master orchestrator (default medium; "
             "the master needs more reasoning than per-task workers)",
    )
    parser.add_argument(
        "--max-time", type=int, default=int(os.environ.get("X_ENGINE_AGENTIC_TIMEOUT_S", "900")),
        help="hard kill on master codex session after this many seconds (default 900)",
    )
    parser.add_argument(
        "--extra-instructions", default="",
        help="optional extra string appended to the master prompt (e.g. 'today emphasize harness work')",
    )
    args = parser.parse_args(argv)

    load_dotenv(GOFREDDY_DIR / ".env")

    if not MASTER_PROMPT_PATH.exists():
        print(f"ERROR: master prompt missing at {MASTER_PROMPT_PATH}", file=sys.stderr)
        return 2

    if not os.environ.get("TWITTERAPI_IO_KEY"):
        print("ERROR: TWITTERAPI_IO_KEY not set", file=sys.stderr)
        return 2

    master_prompt = MASTER_PROMPT_PATH.read_text()
    if args.extra_instructions:
        master_prompt += f"\n\n## Extra instructions for today\n\n{args.extra_instructions}\n"

    # `--dangerously-bypass-approvals-and-sandbox` is required so the master codex
    # can spawn `xeng draft-angle` children (which themselves call codex). With
    # `--full-auto` (sandboxed), nested codex sessions get blocked from network
    # access to chatgpt.com.
    #
    # Safety: master prompt is read-only outside state.db/vault/drafts/tmp. JR's
    # own machine; trusted environment. NOT for shared/CI runs.
    cmd = [
        CODEX_BIN,
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "-C", str(GOFREDDY_DIR),
        "--color", "never",
        "-c", f"model_reasoning_effort={args.effort}",
        master_prompt,
    ]

    print(f"=== Agentic compose — codex master orchestrator ===")
    print(f"  effort: {args.effort}")
    print(f"  timeout: {args.max_time}s")
    print(f"  workdir: {GOFREDDY_DIR}")
    print()

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            timeout=args.max_time,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        print(f"\nERROR: master session exceeded {args.max_time}s", file=sys.stderr)
        return 3

    elapsed = time.time() - t0
    print(f"\n=== agentic compose finished in {elapsed:.0f}s, exit {result.returncode} ===")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
