"""End-to-end smoke test: harness subprocess.Popen → opencode run completes a Read+Edit+Bash loop.

Skipped automatically when opencode is not on PATH or unauthenticated.
This is the same shape used by the harness's run_agent_session at
autoresearch/harness/agent.py:99-124.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AUTORESEARCH_DIR = Path(__file__).resolve().parents[2] / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))


pytestmark = pytest.mark.skipif(
    shutil.which("opencode") is None,
    reason="opencode binary not on PATH",
)


def test_opencode_run_subprocess_completes_simple_tool_loop(tmp_path: Path) -> None:
    """Exercise the same Popen pattern harness/agent.py:108 uses against opencode.

    Pass criterion: file edit lands AND verification command exits 0.
    """
    # Workspace
    target = tmp_path / "spike-target.py"
    target.write_text('def hello():\n    return "world"\n')
    log = tmp_path / "session.jsonl"
    err = tmp_path / "session.err"

    prompt = (
        f"Edit the file {target}: add a single-line comment '# spike-marker' "
        "as the very first line of the file (before def hello). "
        f"After editing, verify with: head -1 {target}"
    )

    # Pick a model: prefer OPENCODE_SMOKE_MODEL env, else default. The default
    # MUST be one your opencode auth list has credentials for.
    # Default matches README's documented OpenRouter setup. Override via
    # OPENCODE_SMOKE_MODEL for operators authed against a different provider.
    model = os.environ.get("OPENCODE_SMOKE_MODEL", "openrouter/deepseek/deepseek-v4-pro")

    cmd = [
        "opencode", "run",
        "--dangerously-skip-permissions",
        "-m", model,
        "--format", "json",
        prompt,
    ]

    with log.open("w") as log_fh, err.open("w") as err_fh:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=log_fh,
            stderr=err_fh,
            text=True,
            cwd=str(tmp_path),
        )
        exit_code = proc.wait(timeout=120)

    assert exit_code == 0, (
        f"opencode exited {exit_code}; stderr tail: {err.read_text()[-500:]}; "
        f"stdout tail: {log.read_text()[-500:]}"
    )
    assert "# spike-marker" in target.read_text(), (
        f"marker missing from target.py; stdout tail: {log.read_text()[-1000:]}"
    )
