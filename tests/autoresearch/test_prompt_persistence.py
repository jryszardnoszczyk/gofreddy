"""Tests for the prompt-persistence helpers in autoresearch/harness/agent.py
and the evaluator request persistence in evaluate_session.py.

Verifies:
- _persist_prompt writes the .prompt.txt sibling file next to log_path.
- The path scheme is invertible: _prompt_path(log_path) == sibling.
- Permission errors degrade gracefully (best-effort, no raise).
- evaluator request payload lands at session_dir/evaluator_requests/.

Does NOT spawn real agent CLIs — the actual subprocess Popen is unit-
tested elsewhere; this only verifies the prompt-write side-effect.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_PATH = REPO_ROOT / "autoresearch" / "harness" / "agent.py"
EVAL_SESSION_PATH = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "scripts"
    / "evaluate_session.py"
)


@pytest.fixture(scope="module")
def agent_module():
    # autoresearch/harness imports `from watchdog import TERMINATION_GRACE_SECONDS`
    # which resolves to autoresearch/archive/v006/scripts/watchdog.py — that
    # path needs to be on sys.path BEFORE the parent autoresearch dir, so the
    # project's local watchdog.py wins over the pip-installed `watchdog`
    # package.
    paths = [
        str(REPO_ROOT / "autoresearch" / "archive" / "v006" / "scripts"),
        str(REPO_ROOT / "autoresearch"),
    ]
    for p in paths:
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("agent_under_test", AGENT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["agent_under_test"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for p in paths:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
    return mod


def test_prompt_path_for_iteration_log(agent_module, tmp_path):
    log = tmp_path / "logs" / "iteration_001.log"
    pp = agent_module._prompt_path(log)
    # iteration_001.log → iteration_001.log.prompt.txt
    assert pp.name == "iteration_001.log.prompt.txt"
    assert pp.parent == log.parent


def test_prompt_path_for_multiturn(agent_module, tmp_path):
    log = tmp_path / "logs" / "multiturn_session.log"
    pp = agent_module._prompt_path(log)
    assert pp.name == "multiturn_session.log.prompt.txt"


def test_persist_prompt_writes_file(agent_module, tmp_path):
    log = tmp_path / "logs" / "iteration_001.log"
    log.parent.mkdir(parents=True)
    prompt = "## Status: RUNNING\n\nDo the thing."

    agent_module._persist_prompt(log, prompt)

    pp = log.with_suffix(log.suffix + ".prompt.txt")
    assert pp.is_file()
    assert pp.read_text() == prompt


def test_persist_prompt_creates_parent(agent_module, tmp_path):
    """Even if logs/ doesn't exist yet, the helper mkdirs it."""
    log = tmp_path / "deep" / "logs" / "iteration_001.log"
    # parent doesn't exist — _persist_prompt should create it.
    agent_module._persist_prompt(log, "hello")

    assert log.parent.is_dir()
    pp = log.with_suffix(log.suffix + ".prompt.txt")
    assert pp.is_file()


def test_persist_prompt_swallows_oserror(agent_module, tmp_path, capsys):
    """Disk-full / permission-denied errors should print a warning but not
    raise. The agent run shouldn't abort just because we can't persist
    the prompt."""
    log = tmp_path / "logs" / "iteration_001.log"
    log.parent.mkdir(parents=True)

    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        # Must not raise
        agent_module._persist_prompt(log, "prompt body")

    captured = capsys.readouterr()
    assert "could not persist prompt" in captured.out


# ---------------------------------------------------------------------------
# evaluator request payload persistence


@pytest.fixture(scope="module")
def evaluate_session_module():
    paths = [
        str(REPO_ROOT / "autoresearch" / "archive" / "v006" / "scripts"),
        str(REPO_ROOT / "autoresearch" / "archive" / "v006"),
        str(REPO_ROOT / "autoresearch"),
    ]
    for p in paths:
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location(
        "evaluate_session_under_test", EVAL_SESSION_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["evaluate_session_under_test"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for p in paths:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
    return mod


def test_invoke_external_critique_persists_request(
    evaluate_session_module, tmp_path
):
    """When called with session_dir + artifact, the request payload lands
    at session_dir/evaluator_requests/<artifact-stem>.request.json."""
    sd = tmp_path / "sd"
    sd.mkdir()
    artifact = sd / "drafts" / "draft-001.md"
    artifact.parent.mkdir()
    artifact.write_text("[BODY]\nhi\n[/BODY]\n")

    criteria = [{"criterion_id": "X-1", "rubric_prompt": "p", "output_text": "o", "source_text": "s"}]

    # Mock subprocess.run to avoid spawning real `freddy` CLI
    fake_result = type("R", (), {"returncode": 0, "stdout": '{"results":[]}', "stderr": ""})()
    with patch.object(evaluate_session_module.subprocess, "run", return_value=fake_result):
        evaluate_session_module._invoke_external_critique(
            criteria, session_dir=sd, artifact=artifact
        )

    persisted = sd / "evaluator_requests" / "draft-001.request.json"
    assert persisted.is_file(), f"expected request payload at {persisted}"
    parsed = json.loads(persisted.read_text())
    assert parsed["criteria"] == criteria


def test_invoke_external_critique_no_session_dir_no_persist(
    evaluate_session_module, tmp_path
):
    """When session_dir/artifact are not passed, the call still works but
    nothing lands on disk."""
    fake_result = type("R", (), {"returncode": 0, "stdout": '{"results":[]}', "stderr": ""})()
    with patch.object(evaluate_session_module.subprocess, "run", return_value=fake_result):
        evaluate_session_module._invoke_external_critique([{"x": 1}])
    # No directory created anywhere
    assert not (tmp_path / "evaluator_requests").exists()
