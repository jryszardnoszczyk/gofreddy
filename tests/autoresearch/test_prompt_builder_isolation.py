"""Tests for subprocess isolation of ``prompt_builder_entrypoint`` (R-#24).

The threat we're defending against: a rogue package on ``PYTHONPATH``
(planted by a malicious variant under its own worktree, or smuggled
via a ``.pth`` file) that redefines
``autoresearch.harness.session_evaluator.build_critique_prompt`` to
return a softer prompt. Because the real caller runs under ``python3 -I``,
the ambient ``PYTHONPATH`` is discarded — the subprocess only sees the
repo root explicitly inserted by the ``-c`` bootstrap.

We verify:

1. A happy-path invocation produces the canonical prompt text.
2. Pointing ``PYTHONPATH`` at a rogue sibling package does NOT win —
   the subprocess still returns the real prompt.
3. Malformed stdin payloads fail loud (non-zero exit, diagnostic on
   stderr).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(
    payload: dict,
    extra_env: dict | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    bootstrap = (
        "import sys;"
        f"sys.path.insert(0, {str(_REPO_ROOT)!r});"
        "import runpy;"
        "runpy.run_module("
        "'autoresearch.harness.prompt_builder_entrypoint',"
        "run_name='__main__'"
        ")"
    )
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-I", "-c", bootstrap],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
        timeout=30,
    )


def test_happy_path_returns_canonical_prompt():
    result = _run(
        {
            "criteria": [
                {
                    "domain_name": "geo",
                    "criterion_id": "c1",
                    "criterion_definition": "Be thorough.",
                    "cross_item_context": None,
                }
            ]
        }
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    assert response["prompts"][0]["criterion_id"] == "c1"
    prompt = response["prompts"][0]["prompt"]
    # Check canonical GRADIENT_CRITIQUE_TEMPLATE fingerprint:
    assert "1-5 scale" in prompt
    assert "Be thorough." in prompt
    assert "No prior-item comparison context" in prompt


def test_polluted_pythonpath_does_not_win(tmp_path):
    # Plant a rogue `autoresearch.harness.session_evaluator` on a
    # bogus PYTHONPATH. If -I respected PYTHONPATH the subprocess would
    # import the rogue version and return the softer prompt; because
    # -I ignores PYTHONPATH, the real prompt must come back.
    rogue_root = tmp_path / "rogue"
    pkg = rogue_root / "autoresearch" / "harness"
    pkg.mkdir(parents=True)
    (rogue_root / "autoresearch" / "__init__.py").write_text("")
    (pkg / "__init__.py").write_text("")
    (pkg / "session_evaluator.py").write_text(
        "def build_critique_prompt(**kw):\n"
        "    return 'ROGUE_OVERRIDE'\n"
    )

    result = _run(
        {
            "criteria": [
                {
                    "domain_name": "geo",
                    "criterion_id": "c1",
                    "criterion_definition": "def",
                    "cross_item_context": None,
                }
            ]
        },
        extra_env={"PYTHONPATH": str(rogue_root)},
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    prompt = response["prompts"][0]["prompt"]
    assert "ROGUE_OVERRIDE" not in prompt
    assert "1-5 scale" in prompt


def test_cwd_pollution_does_not_win(tmp_path):
    # Even if we cd into a directory that contains a rogue
    # `autoresearch/` sibling, -I + the explicit sys.path.insert of
    # REPO_ROOT at the head should still win. (Python doesn't add cwd
    # to sys.path under -I.)
    cwd = tmp_path / "scratch"
    pkg = cwd / "autoresearch" / "harness"
    pkg.mkdir(parents=True)
    (cwd / "autoresearch" / "__init__.py").write_text("")
    (pkg / "__init__.py").write_text("")
    (pkg / "session_evaluator.py").write_text(
        "def build_critique_prompt(**kw):\n"
        "    return 'CWD_ROGUE'\n"
    )

    result = _run(
        {
            "criteria": [
                {
                    "domain_name": "geo",
                    "criterion_id": "c1",
                    "criterion_definition": "def",
                    "cross_item_context": None,
                }
            ]
        },
        cwd=cwd,
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    prompt = response["prompts"][0]["prompt"]
    assert "CWD_ROGUE" not in prompt


def test_malformed_stdin_fails_loud():
    bootstrap = (
        "import sys;"
        f"sys.path.insert(0, {str(_REPO_ROOT)!r});"
        "import runpy;"
        "runpy.run_module("
        "'autoresearch.harness.prompt_builder_entrypoint',"
        "run_name='__main__'"
        ")"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", bootstrap],
        input="not json{",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "invalid JSON" in result.stderr


def test_missing_criteria_field_fails_loud():
    result = _run({"no_criteria_here": True})
    assert result.returncode != 0
    assert "missing 'criteria' list" in result.stderr
