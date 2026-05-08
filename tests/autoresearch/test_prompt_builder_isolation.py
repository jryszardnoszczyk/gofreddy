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


def test_happy_path_with_origin_check_under_namespace_package():
    """Regression: ``autoresearch`` is a PEP 420 namespace package (no
    top-level ``__init__.py``), so ``autoresearch.__file__`` is ``None``.
    A naive ``os.path.realpath(autoresearch.__file__)`` raises
    ``TypeError: expected str, bytes or os.PathLike object, not
    NoneType`` and exits 1, silently disabling the in-session evaluator
    critique on every fixture (caught 2026-05-08 on stripe-docs-payments
    after PR #46 landed). The fix uses ``__path__`` for namespace
    packages — this test exercises the production shape end-to-end.
    """
    result = _run(
        {
            "criteria": [
                {
                    "domain_name": "geo",
                    "criterion_id": "c1",
                    "criterion_definition": "ns-pkg test",
                    "cross_item_context": None,
                }
            ]
        },
        extra_env={"AUTORESEARCH_EXPECTED_REPO_ROOT": str(_REPO_ROOT)},
    )
    assert result.returncode == 0, (
        f"namespace-package origin check failed unexpectedly: "
        f"stderr={result.stderr!r}"
    )
    response = json.loads(result.stdout)
    assert response["prompts"][0]["criterion_id"] == "c1"


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


def test_rogue_autoresearch_resolves_to_wrong_path(tmp_path):
    # Plant a rogue, complete ``autoresearch/`` package at ``tmp_path``
    # (with both the real entrypoint and a softer ``session_evaluator``)
    # and inject ``tmp_path`` (not the real repo root) as ``sys.path[0]``
    # via the bootstrap. The entrypoint loads from the rogue tree;
    # ``autoresearch.__file__`` then resolves under the rogue path. The
    # post-import file-origin check must notice this and exit 2 with a
    # diagnostic mentioning the wrong path.
    import shutil

    rogue_root = tmp_path / "rogue_repo"
    pkg_harness = rogue_root / "autoresearch" / "harness"
    pkg_harness.mkdir(parents=True)
    (rogue_root / "autoresearch" / "__init__.py").write_text("")
    (pkg_harness / "__init__.py").write_text("")
    # Copy the real entrypoint so ``runpy.run_module`` can find it under
    # the rogue ``autoresearch.harness`` namespace.
    shutil.copy(
        _REPO_ROOT / "autoresearch" / "harness" / "prompt_builder_entrypoint.py",
        pkg_harness / "prompt_builder_entrypoint.py",
    )
    # Plant a softer session_evaluator. If the rogue-package guard didn't
    # exist, the entrypoint's ``from autoresearch.harness.session_evaluator
    # import build_critique_prompt`` would resolve to this softer copy and
    # the prompt would silently weaken.
    (pkg_harness / "session_evaluator.py").write_text(
        "def build_critique_prompt(**kw):\n"
        "    return 'ROGUE_OVERRIDE'\n"
    )

    bootstrap = (
        "import sys;"
        f"sys.path.insert(0, {str(rogue_root)!r});"
        "import runpy;"
        "runpy.run_module("
        "'autoresearch.harness.prompt_builder_entrypoint',"
        "run_name='__main__'"
        ")"
    )
    env = os.environ.copy()
    env["AUTORESEARCH_EXPECTED_REPO_ROOT"] = str(_REPO_ROOT)
    result = subprocess.run(
        [sys.executable, "-I", "-c", bootstrap],
        input=json.dumps(
            {
                "criteria": [
                    {
                        "domain_name": "geo",
                        "criterion_id": "c1",
                        "criterion_definition": "def",
                        "cross_item_context": None,
                    }
                ]
            }
        ),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert result.returncode == 2, (
        f"expected exit 2, got {result.returncode}: stderr={result.stderr!r}"
    )
    # The diagnostic now references session_evaluator (the actual file
    # the threat targets), not the namespace package. Both wordings are
    # accepted to keep this test stable across future phrasing edits.
    assert (
        "session_evaluator resolved to" in result.stderr
        or "autoresearch resolved to" in result.stderr
        or "autoresearch path" in result.stderr
    ), result.stderr
    # The diagnostic should name the wrong path (under tmp_path) and the
    # expected path (the real repo root).
    assert str(rogue_root) in result.stderr
    assert str(_REPO_ROOT) in result.stderr
