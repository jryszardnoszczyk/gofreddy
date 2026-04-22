"""Contract tests for the R-#31 verdict agent in ``autoresearch.geo_verify``.

Returns ``{per_query_verdict, aggregate_verdict, evidence_strings,
regression_flags}`` — schema only, no behavioral mocks.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

import geo_verify


REQUIRED_KEYS = {
    "aggregate_verdict",
    "per_query_verdict",
    "evidence_strings",
    "regression_flags",
}


def _mock_claude_envelope(result_text: str) -> mock.MagicMock:
    proc = mock.MagicMock()
    proc.returncode = 0
    proc.stdout = json.dumps({"result": result_text})
    proc.stderr = ""
    return proc


@pytest.fixture
def session_dir_with_baseline(tmp_path: Path) -> Path:
    session = tmp_path / "session"
    session.mkdir()
    competitors = session.parent / "competitors"
    competitors.mkdir()
    (competitors / "visibility.json").write_text(json.dumps({
        "queries": {"freddy ai": {"position": 4}, "competitor x": {"position": 1}},
    }))
    (session / "results.jsonl").write_text(
        json.dumps({"type": "competitive", "queries": ["freddy ai", "competitor x"]}) + "\n"
    )
    return session


def test_compute_verdict_returns_required_keys(
    session_dir_with_baseline: Path,
) -> None:
    agent_json = json.dumps({
        "aggregate_verdict": "PASS",
        "per_query_verdict": [
            {"query": "freddy ai", "verdict": "improved",
             "evidence": "appears at position 1 with brand mention"},
            {"query": "competitor x", "verdict": "held",
             "evidence": "still position 1 — no change"},
        ],
        "evidence_strings": ["freddy ai now ranks #1", "competitor x unchanged"],
        "regression_flags": [],
        "summary": "Majority improved, no regressions.",
        "confidence": "high",
    })

    results = [
        ("freddy ai", '{"position": 1}'),
        ("competitor x", '{"position": 1}'),
    ]
    with mock.patch("geo_verify.subprocess.run", return_value=_mock_claude_envelope(agent_json)):
        verdict = geo_verify.compute_verdict(session_dir_with_baseline, results)

    assert REQUIRED_KEYS.issubset(verdict.keys())
    assert verdict["aggregate_verdict"] in {"PASS", "PARTIAL", "FAIL"}
    assert isinstance(verdict["per_query_verdict"], list)
    assert isinstance(verdict["evidence_strings"], list)
    assert isinstance(verdict["regression_flags"], list)


def test_compute_verdict_per_query_shape(
    session_dir_with_baseline: Path,
) -> None:
    agent_json = json.dumps({
        "aggregate_verdict": "PARTIAL",
        "per_query_verdict": [
            {"query": "freddy ai", "verdict": "improved", "evidence": "now top 3"},
        ],
        "evidence_strings": [],
        "regression_flags": ["competitor x"],
        "summary": "Mixed.",
        "confidence": "medium",
    })
    with mock.patch("geo_verify.subprocess.run", return_value=_mock_claude_envelope(agent_json)):
        verdict = geo_verify.compute_verdict(
            session_dir_with_baseline,
            [("freddy ai", "{}"), ("competitor x", "{}")],
        )
    for item in verdict["per_query_verdict"]:
        assert set(item.keys()) >= {"query", "verdict", "evidence"}
        assert item["verdict"] in {"improved", "regressed", "held", "unknown"}


def test_compute_verdict_drops_hallucinated_query_names(
    session_dir_with_baseline: Path,
) -> None:
    agent_json = json.dumps({
        "aggregate_verdict": "PASS",
        "per_query_verdict": [
            {"query": "freddy ai", "verdict": "improved", "evidence": "ev"},
            {"query": "totally-fabricated-query", "verdict": "improved", "evidence": "ev"},
        ],
        "evidence_strings": [],
        "regression_flags": [],
        "summary": "ok",
        "confidence": "high",
    })
    with mock.patch("geo_verify.subprocess.run", return_value=_mock_claude_envelope(agent_json)):
        verdict = geo_verify.compute_verdict(
            session_dir_with_baseline,
            [("freddy ai", "{}"), ("competitor x", "{}")],
        )
    queries_in_verdict = {item["query"] for item in verdict["per_query_verdict"]}
    assert "totally-fabricated-query" not in queries_in_verdict


def test_compute_verdict_no_baseline_returns_unknown(tmp_path: Path) -> None:
    session = tmp_path / "session_no_baseline"
    session.mkdir()
    # No competitors/visibility.json anywhere reachable
    verdict = geo_verify.compute_verdict(session, [("q", "{}")])
    assert verdict["aggregate_verdict"] == "UNKNOWN_NO_BASELINE"
    assert verdict["per_query_verdict"] == []
    assert verdict["evidence_strings"] == []
    assert verdict["regression_flags"] == []


def test_compute_verdict_rejects_invalid_aggregate(
    session_dir_with_baseline: Path,
) -> None:
    bad = json.dumps({
        "aggregate_verdict": "MEH",
        "per_query_verdict": [],
        "evidence_strings": [],
        "regression_flags": [],
        "summary": "",
        "confidence": "low",
    })
    with mock.patch("geo_verify.subprocess.run", return_value=_mock_claude_envelope(bad)):
        with pytest.raises(ValueError, match="aggregate_verdict"):
            geo_verify.compute_verdict(
                session_dir_with_baseline, [("freddy ai", "{}")],
            )


def test_write_report_renders_verdict_section(
    session_dir_with_baseline: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report must include a Verdict section and write the sibling JSON."""
    agent_json = json.dumps({
        "aggregate_verdict": "PASS",
        "per_query_verdict": [
            {"query": "freddy ai", "verdict": "improved", "evidence": "now #1"},
        ],
        "evidence_strings": ["freddy ai improved"],
        "regression_flags": [],
        "summary": "Looks good.",
        "confidence": "high",
    })
    with mock.patch("geo_verify.subprocess.run", return_value=_mock_claude_envelope(agent_json)):
        report_path = geo_verify.write_report(
            session_dir_with_baseline, [("freddy ai", '{"position": 1}')],
        )

    assert report_path.exists()
    text = report_path.read_text()
    assert "## Verdict" in text
    assert "PASS" in text
    assert "## Raw Query Results" in text  # raw kept for spot-check

    verdict_path = session_dir_with_baseline / "verification-verdict.json"
    assert verdict_path.exists()
    parsed = json.loads(verdict_path.read_text())
    assert REQUIRED_KEYS.issubset(parsed.keys())


def test_write_report_falls_back_on_agent_failure(
    session_dir_with_baseline: Path,
) -> None:
    """Subprocess failure -> UNKNOWN verdict, but report still written + JSON sibling."""
    failing = mock.MagicMock()
    failing.returncode = 1
    failing.stdout = ""
    failing.stderr = "claude failed"
    with mock.patch("geo_verify.subprocess.run", return_value=failing):
        report_path = geo_verify.write_report(
            session_dir_with_baseline, [("freddy ai", "{}")],
        )
    assert report_path.exists()
    verdict_path = session_dir_with_baseline / "verification-verdict.json"
    parsed = json.loads(verdict_path.read_text())
    assert parsed["aggregate_verdict"] == "UNKNOWN_NO_BASELINE"
