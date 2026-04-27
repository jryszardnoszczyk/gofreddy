"""Contract tests for program_prescription_critic (R-#15, Unit 9).

Per-plan: contract-level only. No behavioral mocks of the LLM's semantic
judgement — we assert the module's return-shape contract, the env-escape
short-circuit, and that subprocess failures soft-fail to ``"no-change"``
without ever raising.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

import program_prescription_critic as ppc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_program_pair(tmp_path: Path, *, old: str, new: str, domain: str = "geo") -> tuple[Path, Path]:
    """Lay out a parent/variant pair with one program file each."""
    parent = tmp_path / "parent"
    variant = tmp_path / "variant"
    (parent / "programs").mkdir(parents=True)
    (variant / "programs").mkdir(parents=True)
    (parent / "programs" / f"{domain}-session.md").write_text(old)
    (variant / "programs" / f"{domain}-session.md").write_text(new)
    return parent, variant


class _FakeProc:
    """Stand-in for subprocess.run's CompletedProcess."""

    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _canned_ok(verdict: str = "advise", reasoning: str = "Adds imperative rule.") -> _FakeProc:
    """Canned Claude CLI envelope shaped like ``--output-format json``."""
    envelope = {"type": "result", "result": json.dumps({"verdict": verdict, "reasoning": reasoning})}
    return _FakeProc(stdout=json.dumps(envelope))


# ---------------------------------------------------------------------------
# Contract: return-shape schema
# ---------------------------------------------------------------------------


def test_critique_program_returns_contract_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shape: ``{"verdict": ∈{"advise","no-change"}, "reasoning": non-empty str}``."""
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        return _canned_ok()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ppc.critique_program("geo", "old text", "new text with rule")

    assert set(result.keys()) == {"verdict", "reasoning"}
    assert result["verdict"] in {"advise", "no-change"}
    assert isinstance(result["reasoning"], str)
    assert result["reasoning"].strip() != ""


def test_unchanged_program_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    """If OLD == NEW, skip the subprocess entirely."""
    called: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        called.append(cmd)
        return _canned_ok()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "same text", "same text")

    assert called == []  # no subprocess call
    assert result["verdict"] == "no-change"


@pytest.mark.parametrize("verdict", ["advise", "no-change"])
def test_both_verdict_values_roundtrip(
    monkeypatch: pytest.MonkeyPatch, verdict: str
) -> None:
    """Both ``advise`` and ``no-change`` pass through unchanged."""

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        return _canned_ok(verdict=verdict, reasoning="canned")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert result["verdict"] == verdict


def test_unknown_verdict_collapses_to_no_change(monkeypatch: pytest.MonkeyPatch) -> None:
    """Malformed verdict values must not leak out of the module."""
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        return _canned_ok(verdict="BLOCK-EVOLUTION", reasoning="bogus")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert result["verdict"] == "no-change"
    assert result["reasoning"]  # non-empty


# ---------------------------------------------------------------------------
# Contract: env escape
# ---------------------------------------------------------------------------


def test_env_escape_skips_critic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """EVOLVE_SKIP_PRESCRIPTION_CRITIC=1 returns an empty dict, no subprocess."""
    parent, variant = _make_program_pair(tmp_path, old="old", new="new")

    called: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        called.append(cmd)
        return _canned_ok()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ppc.critique_all_programs(
        parent_dir=parent,
        variant_dir=variant,
        env={"EVOLVE_SKIP_PRESCRIPTION_CRITIC": "1"},
    )

    assert result == {}
    assert called == []
    # critic_reviews.md must not have been created
    assert not (variant / "critic_reviews.md").exists()


def test_env_escape_disabled_runs_critic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With the env var unset, the critic does run and writes its log."""
    parent, variant = _make_program_pair(
        tmp_path,
        old="The agent researches the topic.",
        new="The agent researches the topic. Never use em-dashes.",
    )

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _canned_ok(verdict="advise"))

    result = ppc.critique_all_programs(
        parent_dir=parent,
        variant_dir=variant,
        lane="geo",
        env={},
    )

    assert "geo" in result
    assert result["geo"]["verdict"] in {"advise", "no-change"}
    review_path = variant / "critic_reviews.md"
    assert review_path.is_file()
    body = review_path.read_text()
    assert "geo" in body
    assert "verdict" in body


# ---------------------------------------------------------------------------
# Contract: subprocess-failure soft-fail
# ---------------------------------------------------------------------------


def test_subprocess_timeout_soft_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """TimeoutExpired → no-change verdict, never raised to caller."""
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        raise subprocess.TimeoutExpired(cmd, 120)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert result["verdict"] == "no-change"
    assert "timed out" in result["reasoning"].lower()


def test_subprocess_nonzero_exit_soft_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-zero exit → no-change verdict, never raised to caller."""
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        return _FakeProc(stdout="", stderr="boom", returncode=2)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert result["verdict"] == "no-change"
    assert result["reasoning"]


def test_claude_cli_missing_soft_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """FileNotFoundError (claude binary absent) must not crash the caller."""
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        raise FileNotFoundError("claude")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert result["verdict"] == "no-change"


def test_malformed_json_soft_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garbage stdout → no-change verdict with contract-valid shape."""
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        return _FakeProc(stdout="this is not json at all")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert result["verdict"] == "no-change"
    assert result["reasoning"]


# ---------------------------------------------------------------------------
# Contract: critique_all_programs never rejects + writes log
# ---------------------------------------------------------------------------


def test_new_domain_without_parent_advises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A program file present in variant but not parent → 'advise' (new-file)."""
    parent = tmp_path / "parent"
    variant = tmp_path / "variant"
    (parent / "programs").mkdir(parents=True)
    (variant / "programs").mkdir(parents=True)
    (variant / "programs" / "geo-session.md").write_text("new content")

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _canned_ok())

    result = ppc.critique_all_programs(
        parent_dir=parent, variant_dir=variant, lane="geo", env={}
    )

    assert result["geo"]["verdict"] == "advise"
    assert (variant / "critic_reviews.md").is_file()


def test_critique_all_programs_never_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Even if every subprocess call explodes, the aggregator returns cleanly."""
    parent, variant = _make_program_pair(
        tmp_path, old="old text", new="new text"
    )

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        raise RuntimeError("something weird")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ppc.critique_all_programs(
        parent_dir=parent, variant_dir=variant, lane="geo", env={}
    )
    assert "geo" in result
    assert result["geo"]["verdict"] == "no-change"


# ---------------------------------------------------------------------------
# Backend interchangeability — claude / codex / opencode
# ---------------------------------------------------------------------------


def test_resolve_critic_backend_explicit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("META_BACKEND", raising=False)
    for backend in ("claude", "codex", "opencode"):
        monkeypatch.setenv("AUTORESEARCH_CRITIC_BACKEND", backend)
        assert ppc._resolve_critic_backend() == backend


def test_resolve_critic_backend_falls_back_to_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTORESEARCH_CRITIC_BACKEND", raising=False)
    monkeypatch.setenv("META_BACKEND", "opencode")
    assert ppc._resolve_critic_backend() == "opencode"


def test_resolve_critic_backend_default_claude(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTORESEARCH_CRITIC_BACKEND", raising=False)
    monkeypatch.delenv("META_BACKEND", raising=False)
    assert ppc._resolve_critic_backend() == "claude"


def test_resolve_critic_model_per_backend_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTORESEARCH_CRITIC_MODEL", raising=False)
    monkeypatch.delenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", raising=False)
    assert ppc._resolve_critic_model("claude") == "claude-sonnet-4-5"
    assert ppc._resolve_critic_model("codex") == "gpt-5.4"
    assert ppc._resolve_critic_model("opencode") == "openrouter/deepseek/deepseek-v4-pro"
    monkeypatch.setenv("AUTORESEARCH_CRITIC_MODEL", "anthropic/claude-haiku-4.5")
    assert ppc._resolve_critic_model("opencode") == "anthropic/claude-haiku-4.5"


def test_critique_program_uses_opencode_when_backend_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """When AUTORESEARCH_CRITIC_BACKEND=opencode, critic invokes opencode run."""
    monkeypatch.setenv("AUTORESEARCH_CRITIC_BACKEND", "opencode")
    monkeypatch.setenv("AUTORESEARCH_CRITIC_MODEL", "openrouter/deepseek/deepseek-v4-pro")
    captured_argv: list[str] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:
        nonlocal captured_argv
        captured_argv = list(cmd)
        # Synthesize an opencode JSONL final_answer envelope
        return _FakeProc(stdout=(
            '{"type":"step_finish","part":{"reason":"stop","tokens":{"cache":{"read":0}},"cost":0.001}}\n'
            '{"type":"text","part":{"text":"{\\"verdict\\": \\"advise\\", '
            '\\"reasoning\\": \\"From opencode\\"}","metadata":{"openai":{"phase":"final_answer"}}}}\n'
        ))

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new with rule")
    assert captured_argv[0] == "opencode"
    assert "--format" in captured_argv
    assert result["verdict"] == "advise"
    assert "From opencode" in result["reasoning"]


def test_critique_program_uses_codex_when_backend_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTORESEARCH_CRITIC_BACKEND", "codex")
    monkeypatch.setenv("AUTORESEARCH_CRITIC_MODEL", "gpt-5.4")
    captured_argv: list[str] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:
        nonlocal captured_argv
        captured_argv = list(cmd)
        return _FakeProc(stdout='{"verdict": "no-change", "reasoning": "From codex"}')

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert captured_argv[0] == "codex"
    assert captured_argv[1] == "exec"
    assert result["verdict"] == "no-change"
    assert "From codex" in result["reasoning"]


def test_critique_program_retries_opencode_on_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTORESEARCH_CRITIC_BACKEND", "opencode")
    monkeypatch.setenv("AUTORESEARCH_CRITIC_MODEL", "openrouter/deepseek/deepseek-v4-pro")
    transient_jsonl = (
        '{"type":"error","error":{"data":{"message":"{\\"code\\":429,'
        '\\"error_type\\":\\"rate_limit_exceeded\\"}"}}}\n'
    )
    success_jsonl = (
        '{"type":"step_finish","part":{"reason":"stop","tokens":{"cache":{"read":0}},"cost":0.001}}\n'
        '{"type":"text","part":{"text":"{\\"verdict\\": \\"no-change\\", '
        '\\"reasoning\\": \\"OK\\"}","metadata":{"openai":{"phase":"final_answer"}}}}\n'
    )
    call_count = [0]

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeProc:  # noqa: ARG001
        call_count[0] += 1
        if call_count[0] < 2:
            return _FakeProc(stdout=transient_jsonl)
        return _FakeProc(stdout=success_jsonl)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ppc.critique_program("geo", "old", "new")
    assert call_count[0] == 2, "should have retried once"
    assert result["verdict"] == "no-change"
