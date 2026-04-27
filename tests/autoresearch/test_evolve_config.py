"""META_BACKEND opencode dispatch coverage for evolve.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Same path-bootstrap as test_backend_selection.py to evade the repo-root harness/ shadow
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import evolve  # noqa: E402


def _opencode_config(tmp_path: Path) -> "evolve.EvolutionConfig":
    """Minimal EvolutionConfig with meta_backend='opencode'."""
    # `command` is the only required (no-default) field on EvolutionConfig.
    return evolve.EvolutionConfig(
        command="run",
        meta_backend="opencode",
        meta_model="openrouter/deepseek/deepseek-v4",
        max_turns=10,
        codex_sandbox="workspace-write",
        codex_approval_policy="never",
        codex_reasoning_effort="high",
        codex_web_search="disabled",
    )


def test_build_meta_command_opencode_branch(tmp_path: Path) -> None:
    """_build_meta_command returns opencode argv when meta_backend=opencode."""
    config = _opencode_config(tmp_path)
    cmd = evolve._build_meta_command(config, tmp_path)

    assert cmd[0] == "opencode"
    assert cmd[1] == "run"
    assert "--dangerously-skip-permissions" in cmd
    assert "openrouter/deepseek/deepseek-v4" in cmd
    assert "--format" in cmd
    assert "json" in cmd


def test_build_meta_env_opencode_uses_codex_pattern(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_build_meta_env opencode branch should follow codex pattern (os.environ.copy minus holdout)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key")
    monkeypatch.setenv("HOME", "/Users/test")

    config = _opencode_config(tmp_path)
    env = evolve._build_meta_env(config, tmp_path)

    # Should include OPENROUTER_API_KEY (codex-style passes it through)
    assert env.get("OPENROUTER_API_KEY") == "or-test-key"
    # Should include HOME
    assert env.get("HOME") == "/Users/test"
    # Should include PYTHONPATH set to workdir
    assert env.get("PYTHONPATH") == str(tmp_path)
    # Should NOT raise


def test_build_meta_env_opencode_strips_holdout_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """opencode env stripping must use _CODEX_HOLDOUT_KEYS."""
    # Pick at least one key from _CODEX_HOLDOUT_KEYS to verify it's stripped.
    # If the constant is renamed, this test will break — that's intentional,
    # to surface the rename.
    import evolve as _e

    holdout_sample = next(iter(_e._CODEX_HOLDOUT_KEYS))
    monkeypatch.setenv(holdout_sample, "should-be-stripped")

    config = _opencode_config(tmp_path)
    env = evolve._build_meta_env(config, tmp_path)

    assert holdout_sample not in env


def test_build_meta_command_opencode_appends_prompt_text(tmp_path: Path) -> None:
    """When prompt_text is provided, opencode branch appends it as positional argv.

    Resolves the stdin/argv mismatch that was a known risk in the original T5:
    opencode reads prompt from positional argv, not stdin, so run_meta_agent
    now reads the prompt file content and passes it via this parameter.
    """
    config = _opencode_config(tmp_path)
    cmd = evolve._build_meta_command(
        config, tmp_path, prompt_text="Run generation gen_id=42"
    )

    assert cmd[-1] == "Run generation gen_id=42"
    # When prompt_text is None, no trailing positional prompt; command ends
    # with --format json (no --dir flag — subprocess cwd= handles workdir).
    cmd_no_prompt = evolve._build_meta_command(config, tmp_path, prompt_text=None)
    assert cmd_no_prompt[-2] == "--format"
    assert cmd_no_prompt[-1] == "json"
