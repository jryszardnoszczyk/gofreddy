"""Contract tests for the R-#30 alert agent in ``autoresearch.compute_metrics``.

Returns schema-valid alert list (even empty). Mock the Claude CLI subprocess;
no behavioral mocks.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

import compute_metrics


@pytest.fixture
def sample_row() -> dict:
    return {
        "lane": "core",
        "gen_id": 42,
        "n": 3,
        "mean_composite": 0.62,
        "mean_keep": 0.48,
        "inner_outer_corr": 0.31,
        "rows": [
            {"variant_id": "v-0001", "composite": 0.72, "max_fixture_sd": 0.35, "keep_rate": 0.6},
            {"variant_id": "v-0002", "composite": 0.55, "max_fixture_sd": 0.12, "keep_rate": 0.4},
            {"variant_id": "v-0003", "composite": 0.58, "max_fixture_sd": 0.22, "keep_rate": 0.45},
        ],
    }


def _mock_claude_json(result_text: str) -> mock.MagicMock:
    envelope = json.dumps({"result": result_text})
    proc = mock.MagicMock()
    proc.returncode = 0
    proc.stdout = envelope
    proc.stderr = ""
    return proc


def test_judge_alerts_parses_valid_agent_response(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")

    agent_json = json.dumps([
        {
            "code": "inner_outer_drift",
            "severity": "high",
            "variant_id": None,
            "detail": "inner_outer_corr fell to 0.31 AND mean_composite regressed from 0.70 to 0.62",
            "confidence": "high",
        },
        {
            "code": "uneven_generalization",
            "severity": "medium",
            "variant_id": "v-0001",
            "detail": "v-0001 has max_fixture_sd=0.35 at composite=0.72 — likely fixture saturation",
            "confidence": "medium",
        },
    ])
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json(agent_json)):
        alerts = compute_metrics.judge_alerts(sample_row)

    assert isinstance(alerts, list)
    assert len(alerts) == 2
    for a in alerts:
        assert a["code"] in compute_metrics._VALID_ALERT_CODES
        assert a["severity"] in compute_metrics._VALID_SEVERITIES
        assert a["confidence"] in compute_metrics._VALID_SEVERITIES
        assert a["lane"] == "core"
        assert a["gen_id"] == 42
        assert a["source"] == "agent"
        assert isinstance(a["detail"], str) and a["detail"]


def test_judge_alerts_returns_empty_on_empty_agent_array(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json("[]")):
        alerts = compute_metrics.judge_alerts(sample_row)
    assert alerts == []


def test_judge_alerts_drops_unknown_codes(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    agent_json = json.dumps([
        {"code": "plateau", "severity": "low", "variant_id": None,
         "detail": "ok", "confidence": "low"},
        {"code": "totally_made_up", "severity": "high", "variant_id": None,
         "detail": "spurious", "confidence": "high"},
    ])
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json(agent_json)):
        alerts = compute_metrics.judge_alerts(sample_row)
    assert len(alerts) == 1
    assert alerts[0]["code"] == "plateau"


def test_judge_alerts_drops_hallucinated_variant_ids(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    agent_json = json.dumps([
        {"code": "overfitting", "severity": "medium",
         "variant_id": "v-HALLUCINATED", "detail": "d", "confidence": "medium"},
    ])
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json(agent_json)):
        alerts = compute_metrics.judge_alerts(sample_row)
    assert len(alerts) == 1
    # Hallucinated variant id is dropped to None (treated as lane-level alert).
    assert alerts[0]["variant_id"] is None


def test_judge_alerts_handles_malformed_json(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json("not json at all")):
        alerts = compute_metrics.judge_alerts(sample_row)
    assert alerts == []


def test_judge_alerts_returns_empty_on_subprocess_failure(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    failing = mock.MagicMock()
    failing.returncode = 1
    failing.stdout = ""
    failing.stderr = "claude: binary not found"
    with mock.patch("compute_metrics.subprocess.run", return_value=failing):
        alerts = compute_metrics.judge_alerts(sample_row)
    assert alerts == []


def test_judge_alerts_caps_at_max_count(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    too_many = [
        {"code": "plateau", "severity": "low", "variant_id": None,
         "detail": f"a{i}", "confidence": "low"}
        for i in range(10)
    ]
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json(json.dumps(too_many))):
        alerts = compute_metrics.judge_alerts(sample_row)
    assert len(alerts) <= compute_metrics._ALERT_MAX_COUNT


def test_check_alerts_emits_to_alerts_jsonl(
    sample_row: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    monkeypatch.setattr(compute_metrics, "_ALERTS_LOG", tmp_path / "alerts.jsonl")

    agent_json = json.dumps([
        {"code": "overfitting", "severity": "medium", "variant_id": None,
         "detail": "test", "confidence": "medium"},
    ])
    with mock.patch("compute_metrics.subprocess.run", return_value=_mock_claude_json(agent_json)):
        compute_metrics.check_alerts(sample_row)

    alerts_path = tmp_path / "alerts.jsonl"
    assert alerts_path.exists()
    lines = [json.loads(l) for l in alerts_path.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0]["code"] == "overfitting"
    assert lines[0]["source"] == "agent"


def test_alert_agent_uses_opencode_when_backend_env_set(
    sample_row: dict,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When AUTORESEARCH_ALERT_BACKEND=opencode, alert agent calls opencode run."""
    monkeypatch.setattr(compute_metrics, "METRICS_DIR", tmp_path)
    monkeypatch.setattr(compute_metrics, "_GENERATIONS_LOG", tmp_path / "generations.jsonl")
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "opencode")
    monkeypatch.setenv("AUTORESEARCH_ALERT_MODEL", "openrouter/deepseek/deepseek-v4-pro")

    captured_argv: list[str] = []
    captured_env: dict[str, str] = {}

    def fake_run(cmd, capture_output, text, check, timeout, env):
        nonlocal captured_argv, captured_env
        captured_argv = list(cmd)
        captured_env = dict(env)
        proc = mock.MagicMock()
        proc.returncode = 0
        # Synthesize an OpenCode JSONL with a final_answer "[]" (empty alerts)
        proc.stdout = (
            '{"type":"step_finish","part":{"reason":"stop","tokens":{"cache":{"read":0}},"cost":0.001}}\n'
            '{"type":"text","part":{"text":"[]","metadata":{"openai":{"phase":"final_answer"}}}}\n'
        )
        proc.stderr = ""
        return proc

    monkeypatch.setattr(compute_metrics.subprocess, "run", fake_run)

    result = compute_metrics._run_alert_agent_json(prompt="test", model="openrouter/deepseek/deepseek-v4-pro", timeout=30)

    assert captured_argv[0] == "opencode"
    assert captured_argv[1] == "run"
    assert "--format" in captured_argv
    assert result == "[]"


def test_alert_agent_defaults_to_claude_when_backend_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When AUTORESEARCH_ALERT_BACKEND unset, alert agent uses claude (existing behavior)."""
    monkeypatch.delenv("AUTORESEARCH_ALERT_BACKEND", raising=False)

    captured_argv: list[str] = []

    def fake_run(cmd, capture_output, text, check, timeout, env):
        nonlocal captured_argv
        captured_argv = list(cmd)
        proc = mock.MagicMock()
        proc.returncode = 0
        proc.stdout = json.dumps({"result": "[]"})
        proc.stderr = ""
        return proc

    monkeypatch.setattr(compute_metrics.subprocess, "run", fake_run)

    result = compute_metrics._run_alert_agent_json(prompt="test", model="sonnet", timeout=30)

    assert captured_argv[0] == "claude"
    assert "-p" in captured_argv
    assert result == "[]"


def test_alert_agent_model_default_per_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """_alert_agent_model() defaults to a backend-appropriate model when AUTORESEARCH_ALERT_MODEL unset."""
    monkeypatch.delenv("AUTORESEARCH_ALERT_MODEL", raising=False)

    # claude backend → "sonnet" default
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "claude")
    assert compute_metrics._alert_agent_model() == "sonnet"

    # opencode backend → opencode default model (matches harness/backend.py)
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "opencode")
    assert compute_metrics._alert_agent_model() == "openrouter/deepseek/deepseek-v4-pro"

    # opencode backend + AUTORESEARCH_OPENCODE_DEFAULT_MODEL override
    monkeypatch.setenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", "openrouter/qwen/qwen3-coder")
    assert compute_metrics._alert_agent_model() == "openrouter/qwen/qwen3-coder"

    # Explicit AUTORESEARCH_ALERT_MODEL trumps everything
    monkeypatch.setenv("AUTORESEARCH_ALERT_MODEL", "anthropic/claude-haiku-4.5")
    assert compute_metrics._alert_agent_model() == "anthropic/claude-haiku-4.5"
