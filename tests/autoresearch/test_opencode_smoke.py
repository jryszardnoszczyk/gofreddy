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

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
# Mirror the path-bootstrap test_opencode_jsonl.py uses so the right `harness`
# package wins when pytest's collection phase has already cached an
# unrelated ``harness`` module from another test file's import chain.
if str(AUTORESEARCH_DIR) in sys.path:
    sys.path.remove(str(AUTORESEARCH_DIR))
sys.path.insert(0, str(AUTORESEARCH_DIR))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(AUTORESEARCH_DIR)):
        del sys.modules[_mod]

from harness.opencode_jsonl import session_has_transient_error  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("opencode") is None,
    reason="opencode binary not on PATH",
)

_SMOKE_MAX_ATTEMPTS = 3


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

    # Pin OPENCODE_CONFIG so opencode applies the repo's OpenRouter
    # provider-routing rules even though cwd=tmp_path is outside any git tree.
    # Without this opencode silently uses defaults and routes deepseek-v4-pro
    # to upstream providers that may not support tool-calling, producing the
    # mid-session 504s we hit before the routing config existed.
    env = os.environ.copy()
    config_path = REPO_ROOT / "opencode.json"
    if config_path.is_file() and not env.get("OPENCODE_CONFIG"):
        env["OPENCODE_CONFIG"] = str(config_path)

    # Retry transient upstream errors (rate_limit, provider_overloaded,
    # 504 timeouts) — same retry policy run_agent_session applies in
    # production. Three attempts mirrors _OPENCODE_MAX_ATTEMPTS default.
    exit_code = 0
    for attempt in range(1, _SMOKE_MAX_ATTEMPTS + 1):
        # Reset state before each attempt so a previous attempt's partial
        # success can't satisfy the assertion below.
        target.write_text('def hello():\n    return "world"\n')
        with log.open("w") as log_fh, err.open("w") as err_fh:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=log_fh,
                stderr=err_fh,
                text=True,
                cwd=str(tmp_path),
                env=env,
            )
            try:
                exit_code = proc.wait(timeout=240)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                exit_code = 124
        if exit_code == 0 and not session_has_transient_error(log):
            break
        if attempt < _SMOKE_MAX_ATTEMPTS:
            print(f"smoke attempt {attempt}/{_SMOKE_MAX_ATTEMPTS} hit transient error (exit={exit_code}), retrying")

    assert exit_code == 0, (
        f"opencode exited {exit_code}; stderr tail: {err.read_text()[-500:]}; "
        f"stdout tail: {log.read_text()[-500:]}"
    )
    assert "# spike-marker" in target.read_text(), (
        f"marker missing from target.py; stdout tail: {log.read_text()[-1000:]}"
    )
