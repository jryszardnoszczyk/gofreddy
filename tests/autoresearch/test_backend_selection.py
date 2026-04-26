"""Backend selection coverage for harness/backend.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add autoresearch dir to path (mirrors harness/backend.py's own bootstrap).
# Insert at index 0 *after* removing any pre-existing entry so we beat the
# repo-root entry that pytest prepends (otherwise `import harness` resolves
# to the unrelated repo-root harness/ package).
AUTORESEARCH_DIR = str(Path(__file__).resolve().parents[2] / "autoresearch")
if AUTORESEARCH_DIR in sys.path:
    sys.path.remove(AUTORESEARCH_DIR)
sys.path.insert(0, AUTORESEARCH_DIR)

# Drop any stale `harness` module cached against the wrong package so the
# fresh import below resolves against autoresearch/harness/.
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    if not getattr(sys.modules[_mod], "__file__", "").startswith(AUTORESEARCH_DIR):
        del sys.modules[_mod]

from harness import backend as harness_backend  # noqa: E402


def test_session_backend_accepts_opencode_via_autoresearch_session_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "opencode")
    monkeypatch.delenv("EVAL_BACKEND_OVERRIDE", raising=False)
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    assert harness_backend.session_backend() == "opencode"


def test_session_backend_accepts_opencode_via_eval_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVAL_BACKEND_OVERRIDE", "opencode")
    monkeypatch.delenv("AUTORESEARCH_SESSION_BACKEND", raising=False)
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    assert harness_backend.session_backend() == "opencode"


def test_default_session_model_opencode_uses_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", "openrouter/qwen/qwen3-coder")
    assert harness_backend.default_session_model("opencode") == "openrouter/qwen/qwen3-coder"


def test_default_session_model_opencode_falls_back_to_deepseek(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", raising=False)
    assert harness_backend.default_session_model("opencode") == "openrouter/deepseek/deepseek-v3"


def test_agent_command_opencode_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """harness/agent.py _agent_command() returns opencode argv when backend=opencode."""
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "opencode")
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    from harness import agent as harness_agent

    cmd = harness_agent._agent_command(
        model="openrouter/deepseek/deepseek-v3",
        max_turns=20,
        prompt_text="Fix finding F-test-1",
    )

    assert cmd[0] == "opencode"
    assert cmd[1] == "run"
    assert "--dangerously-skip-permissions" in cmd
    assert "-m" in cmd
    assert "openrouter/deepseek/deepseek-v3" in cmd
    assert "--format" in cmd
    assert "json" in cmd
    assert "--dir" in cmd
    assert cmd[-1] == "Fix finding F-test-1"


def test_agent_command_opencode_branch_no_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """When prompt_text=None, command still well-formed (prompt fed via stdin elsewhere)."""
    monkeypatch.setenv("AUTORESEARCH_SESSION_BACKEND", "opencode")
    monkeypatch.setattr(harness_backend.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    from harness import agent as harness_agent

    cmd = harness_agent._agent_command(
        model="anthropic/claude-opus-4.7",
        max_turns=20,
        prompt_text=None,
    )

    assert cmd[0] == "opencode"
    assert "anthropic/claude-opus-4.7" in cmd
    # No trailing positional prompt arg when prompt_text is None
    assert not cmd[-1].startswith("Fix")
