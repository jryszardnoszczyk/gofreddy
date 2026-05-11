"""Tests for autoresearch_v2/tools/alert_check.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch_v2.tools import alert_check


# --- helpers ----------------------------------------------------------------


def _write_tsv(repo: Path, lane: str, rows: list[tuple]) -> Path:
    path = repo / "autoresearch_v2" / "lanes" / lane / "results.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(alert_check._TSV_COLUMNS)]
    for row in rows:
        lines.append("\t".join(str(c) for c in row))
    path.write_text("\n".join(lines) + "\n")
    return path


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_V2_ROOT", str(tmp_path))
    return tmp_path


def _improving_trajectory():
    return [
        ("2026-05-11T00:00:00Z", "aaa1111", f"{4.0 + i * 0.1:.4f}", "100", "keep", f"iter {i}", "{}")
        for i in range(5)
    ]


def _collapse_trajectory():
    """v176/v177-class: 4 keeps at 5.0 then a collapse to 0.5."""
    rows = [
        ("2026-05-11T00:00:00Z", f"a{i:06d}", "5.0000", "100", "keep", f"iter {i}", "{}")
        for i in range(4)
    ]
    rows.append(("2026-05-11T04:00:00Z", "b000005", "0.5000", "100", "keep", "regression", "{}"))
    return rows


def _generation_failure_trajectory():
    """6/10 fail with status=crash, > 30% threshold."""
    return (
        [("ts", f"a{i:06d}", "5.0000", "100", "keep", f"ok {i}", "{}") for i in range(4)]
        + [("ts", f"b{i:06d}", "", "30", "crash", f"crash {i}", '{"exit":1}') for i in range(6)]
    )


# --- trajectory reading -----------------------------------------------------


def test_read_trajectory_returns_last_n_rows(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _improving_trajectory() + _improving_trajectory())
    rows = alert_check.read_trajectory("geo", n=5)
    assert len(rows) == 5


def test_read_trajectory_missing_file(tmp_repo: Path):
    assert alert_check.read_trajectory("geo") == []


def test_variant_output_failure_rate_correct(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _generation_failure_trajectory())
    rows = alert_check.read_trajectory("geo", n=10)
    rate = alert_check.variant_output_failure_rate(rows)
    assert rate == 0.6


def test_variant_output_failure_rate_empty():
    assert alert_check.variant_output_failure_rate([]) == 0.0


# --- prompt building --------------------------------------------------------


def test_build_alert_prompt_drops_v1_aggregation_fields(tmp_repo: Path):
    """Audit-driven: prompt MUST NOT reference Pearson/keep-rate/per-generation
    aggregation fields (those are dropped per Plan B U6)."""
    _write_tsv(tmp_repo, "geo", _improving_trajectory())
    rows = alert_check.read_trajectory("geo")
    prompt = alert_check._build_alert_prompt("geo", rows)
    for dropped in ("inner_outer_corr", "Pearson", "mean_keep", "keep_rate"):
        assert dropped not in prompt, f"prompt references dropped v1 field {dropped!r}"


def test_build_alert_prompt_includes_trajectory_and_failure_rate(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _generation_failure_trajectory())
    rows = alert_check.read_trajectory("geo", n=10)
    prompt = alert_check._build_alert_prompt("geo", rows)
    assert "Variant-output-failure rate" in prompt
    assert "0.60" in prompt  # 6/10 = 60%
    assert "Recent trajectory" in prompt
    # trajectory line format: ts=... sha=... composite=... status=... desc=...
    assert "sha=" in prompt and "composite=" in prompt and "status=" in prompt


def test_build_alert_prompt_lane_specific(tmp_repo: Path):
    _write_tsv(tmp_repo, "competitive", _improving_trajectory())
    rows = alert_check.read_trajectory("competitive")
    prompt = alert_check._build_alert_prompt("competitive", rows)
    assert "Lane: competitive" in prompt


# --- alert agent integration (mocked) ---------------------------------------


def test_short_history_returns_empty_without_calling_agent(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _improving_trajectory()[:2])
    called = {"n": 0}

    def agent(prompt: str) -> str:
        called["n"] += 1
        return "[]"

    result = alert_check.alert_check(lane="geo", agent_caller=agent)
    assert result["alerts"] == []
    assert "insufficient" in result.get("skipped", "")
    assert called["n"] == 0


def test_no_alerts_on_clean_trajectory(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _improving_trajectory())

    def agent(prompt: str) -> str:
        return "[]"

    result = alert_check.alert_check(lane="geo", agent_caller=agent)
    assert result["alerts"] == []
    assert result["rows_seen"] == 5


def test_collapse_alert_emits_to_alerts_jsonl(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _collapse_trajectory())

    agent_response = json.dumps([{
        "code": "collapse",
        "severity": "high",
        "variant_id": "b000005",
        "detail": "composite dropped 5.0 -> 0.5 in one keep",
        "confidence": "high",
    }])

    result = alert_check.alert_check(lane="geo", agent_caller=lambda p: agent_response)
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["code"] == "collapse"
    assert result["alerts"][0]["severity"] == "high"

    alerts_file = tmp_repo / "autoresearch_v2" / "alerts.jsonl"
    assert alerts_file.is_file()
    written = json.loads(alerts_file.read_text().strip())
    assert written["code"] == "collapse"
    assert written["lane"] == "geo"
    assert written["source"] == "agent"


def test_low_severity_not_written_to_jsonl(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _improving_trajectory())
    agent_response = json.dumps([{
        "code": "drift",
        "severity": "low",
        "variant_id": None,
        "detail": "barely worth mentioning",
        "confidence": "low",
    }])
    result = alert_check.alert_check(lane="geo", agent_caller=lambda p: agent_response)
    # Low alert is returned in the result, but NOT written to alerts.jsonl
    assert len(result["alerts"]) == 0 or all(a["severity"] != "high" for a in result["alerts"])
    # alerts.jsonl is empty or missing
    alerts_file = tmp_repo / "autoresearch_v2" / "alerts.jsonl"
    assert not alerts_file.exists() or alerts_file.read_text().strip() == ""


def test_agent_call_failure_returns_empty_no_crash(tmp_repo: Path, capsys):
    _write_tsv(tmp_repo, "geo", _improving_trajectory())

    def agent(prompt: str) -> str:
        raise RuntimeError("network down")

    result = alert_check.alert_check(lane="geo", agent_caller=agent)
    assert result["alerts"] == []
    assert "network down" in result.get("error", "")
    err = capsys.readouterr().err
    assert "agent call failed" in err


def test_malformed_json_response_handled(tmp_repo: Path, capsys):
    _write_tsv(tmp_repo, "geo", _improving_trajectory())
    result = alert_check.alert_check(lane="geo", agent_caller=lambda p: "not json")
    assert result["alerts"] == []
    assert "error" in result


def test_extract_json_array_strips_code_fences():
    raw = "```json\n[{\"code\":\"plateau\",\"severity\":\"low\",\"detail\":\"flat\",\"confidence\":\"low\"}]\n```"
    parsed = alert_check._extract_json_array(raw)
    assert len(parsed) == 1
    assert parsed[0]["code"] == "plateau"


def test_extract_json_array_tolerates_leading_prose():
    raw = "Here is the JSON:\n[{\"code\":\"plateau\",\"severity\":\"low\",\"detail\":\"flat\",\"confidence\":\"low\"}]"
    parsed = alert_check._extract_json_array(raw)
    assert len(parsed) == 1


def test_validate_alert_rejects_invalid_code(tmp_repo: Path):
    bad = {"code": "made_up_code", "severity": "high", "detail": "x", "confidence": "low"}
    assert alert_check._validate_alert(bad) is None


def test_validate_alert_rejects_invalid_severity(tmp_repo: Path):
    bad = {"code": "collapse", "severity": "critical", "detail": "x", "confidence": "high"}
    assert alert_check._validate_alert(bad) is None


def test_validate_alert_rejects_missing_detail(tmp_repo: Path):
    bad = {"code": "collapse", "severity": "high", "detail": "", "confidence": "high"}
    assert alert_check._validate_alert(bad) is None


def test_validate_alert_normalises_confidence(tmp_repo: Path):
    ok = {"code": "collapse", "severity": "high", "detail": "x", "confidence": "weird"}
    norm = alert_check._validate_alert(ok)
    assert norm["confidence"] == "medium"


def test_alert_count_capped_at_max(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _improving_trajectory())
    many = [{
        "code": "drift", "severity": "high",
        "variant_id": None, "detail": f"alert {i}", "confidence": "low",
    } for i in range(10)]
    result = alert_check.alert_check(lane="geo", agent_caller=lambda p: json.dumps(many))
    assert len(result["alerts"]) <= alert_check._ALERT_MAX_COUNT


def test_generation_failure_signal_in_prompt(tmp_repo: Path):
    """Stream A Bug 3 integration — failure rate appears in the prompt
    so the LLM can flag it."""
    _write_tsv(tmp_repo, "geo", _generation_failure_trajectory())
    prompts: list[str] = []

    def agent(prompt: str) -> str:
        prompts.append(prompt)
        return json.dumps([{
            "code": "generation_failure", "severity": "high",
            "variant_id": None,
            "detail": "60% of last 10 attempts produced no output",
            "confidence": "high",
        }])

    result = alert_check.alert_check(lane="geo", agent_caller=agent)
    assert "0.60" in prompts[0]
    assert "generation_failure" in result["alerts"][0]["code"]


def test_v176_v177_replay_emits_collapse(tmp_repo: Path):
    """Manual replay scenario: a sharp drop in composite after several
    keeps. Agent flags collapse, alert appears in alerts.jsonl."""
    _write_tsv(tmp_repo, "geo", _collapse_trajectory())
    result = alert_check.alert_check(
        lane="geo",
        agent_caller=lambda p: json.dumps([{
            "code": "collapse", "severity": "high",
            "variant_id": "b000005",
            "detail": "v176/v177-class: composite dropped 5.0 -> 0.5",
            "confidence": "high",
        }]),
    )
    assert result["alerts"][0]["code"] == "collapse"
    alerts_file = tmp_repo / "autoresearch_v2" / "alerts.jsonl"
    assert alerts_file.read_text().strip()


def test_no_write_mode_skips_alerts_jsonl(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", _collapse_trajectory())

    agent_response = json.dumps([{
        "code": "collapse", "severity": "high",
        "variant_id": "b000005", "detail": "x", "confidence": "high",
    }])

    result = alert_check.alert_check(
        lane="geo", agent_caller=lambda p: agent_response, write_alerts=False,
    )
    assert result["alerts"]
    alerts_file = tmp_repo / "autoresearch_v2" / "alerts.jsonl"
    assert not alerts_file.exists()


def test_alert_agent_model_resolution(tmp_repo: Path, monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_ALERT_MODEL", raising=False)
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "claude")
    assert alert_check._alert_agent_model() == "sonnet"
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "codex")
    assert alert_check._alert_agent_model() == "gpt-5.5"
    monkeypatch.setenv("AUTORESEARCH_ALERT_BACKEND", "opencode")
    assert "deepseek" in alert_check._alert_agent_model()
    monkeypatch.setenv("AUTORESEARCH_ALERT_MODEL", "explicit-override")
    assert alert_check._alert_agent_model() == "explicit-override"


def test_unknown_backend_raises():
    with pytest.raises(RuntimeError, match="not supported"):
        alert_check._build_alert_cmd("gemini", "model", "prompt")


def test_main_cli_always_exits_zero(tmp_repo: Path, capsys, monkeypatch):
    _write_tsv(tmp_repo, "geo", _improving_trajectory())

    # Use empty trajectory so agent isn't called
    monkeypatch.setattr(alert_check, "read_trajectory", lambda lane, n=10: [])
    rc = alert_check.main(["--lane", "geo"])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["lane"] == "geo"
