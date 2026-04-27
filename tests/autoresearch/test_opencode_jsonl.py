"""Unit tests for the OpenCode JSONL parser."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Path-bootstrap mirrors test_backend_selection.py / test_evolve_config.py
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

from harness import opencode_jsonl  # noqa: E402


SAMPLE_JSONL = """{"type":"step_start","timestamp":1,"sessionID":"s","part":{"type":"step-start"}}
{"type":"text","timestamp":2,"sessionID":"s","part":{"type":"text","text":"thinking out loud","metadata":{"openai":{"phase":"commentary"}}}}
{"type":"tool_use","timestamp":3,"sessionID":"s","part":{"type":"tool","tool":"read","state":{"status":"completed","input":{"filePath":"/x"},"output":"file contents"}}}
{"type":"step_finish","timestamp":4,"sessionID":"s","part":{"reason":"tool-calls","tokens":{"total":100,"input":80,"output":20,"reasoning":0,"cache":{"write":0,"read":0}},"cost":0.01}}
{"type":"text","timestamp":5,"sessionID":"s","part":{"type":"text","text":"Final answer is 42.","metadata":{"openai":{"phase":"final_answer"}}}}
{"type":"step_finish","timestamp":6,"sessionID":"s","part":{"reason":"stop","tokens":{"total":50,"input":10,"output":40,"reasoning":0,"cache":{"write":0,"read":80}},"cost":0.005}}
"""


def test_parse_total_cost_sums_all_step_finish_events(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(SAMPLE_JSONL)

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.total_cost == pytest.approx(0.015)


def test_parse_total_cache_reads_sums_all_step_finish_events(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(SAMPLE_JSONL)

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.total_cache_reads == 80


def test_parse_final_answer_returns_last_text_before_stop(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(SAMPLE_JSONL)

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.final_answer == "Final answer is 42."


def test_parse_returns_empty_summary_on_empty_file(tmp_path: Path) -> None:
    log_path = tmp_path / "empty.jsonl"
    log_path.write_text("")

    summary = opencode_jsonl.parse_session(log_path)

    assert summary.total_cost == 0.0
    assert summary.total_cache_reads == 0
    assert summary.final_answer is None


def test_parse_skips_malformed_lines(tmp_path: Path) -> None:
    """Malformed JSON lines should be skipped, not fatal."""
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(
        SAMPLE_JSONL
        + "this is not json\n"
        + '{"type":"step_finish","part":{"reason":"stop","tokens":{"cache":{"read":0}},"cost":0.001}}\n'
    )

    summary = opencode_jsonl.parse_session(log_path)

    # Total cost = 0.01 + 0.005 + 0.001 (the second valid step_finish)
    assert summary.total_cost == pytest.approx(0.016)
