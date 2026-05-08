"""α7 unit tests for render_judge.py.

Exercises the stub fallback (no GEMINI_API_KEY) and the output-shape contract.
The Gemini path itself is mocked — we don't burn real API quota in tests.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

# Make the v006 scripts dir importable
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS_DIR))

import render_judge  # type: ignore  # noqa: E402


def test_grade_stub_fallback_when_no_api_key(tmp_path, monkeypatch):
    """Without GEMINI_API_KEY, grade() returns stub scores in the expected shape."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    png_path = tmp_path / "report-screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

    rubric_path = tmp_path / "render-rubric.md"
    rubric_path.write_text("# Test rubric\n\nRND-1: Typography\n", encoding="utf-8")

    result = render_judge.grade(png_path, rubric_path)

    assert result["source"] == "stub"
    assert result["aggregate"] == 0.0  # no valid scores in stub
    assert isinstance(result["criteria"], list)
    assert len(result["criteria"]) == 5
    for c in result["criteria"]:
        assert c["criterion"] in render_judge.CRITERIA
        assert "score" in c
        assert "rationale" in c


def test_grade_with_mocked_gemini_returns_aggregate(tmp_path, monkeypatch):
    """When grade_with_gemini returns valid scores, aggregate is the mean of non-zero."""
    png_path = tmp_path / "report-screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    rubric_path = tmp_path / "render-rubric.md"
    rubric_path.write_text("# rubric\n", encoding="utf-8")

    fake_results = [
        {"criterion": "RND-1", "score": 4, "rationale": "good typo"},
        {"criterion": "RND-2", "score": 5, "rationale": "great density"},
        {"criterion": "RND-3", "score": 3, "rationale": "ok print"},
        {"criterion": "RND-4", "score": 4, "rationale": "consistent tokens"},
        {"criterion": "RND-5", "score": 0, "rationale": "n/a for pdf"},
    ]
    with mock.patch.object(render_judge, "grade_with_gemini", return_value=fake_results):
        result = render_judge.grade(png_path, rubric_path)

    assert result["source"] == "gemini"
    assert result["criteria"] == fake_results
    # Aggregate excludes the 0 (n/a) score: (4+5+3+4)/4 = 4.0
    assert result["aggregate"] == 4.0
    assert result["screenshot"] == str(png_path)


def test_main_writes_output_json(tmp_path, monkeypatch, capsys):
    """`render_judge.py <png> -o <out>` writes well-formed JSON."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text("# rubric\n", encoding="utf-8")
    out_path = tmp_path / "render_score.json"

    monkeypatch.setattr(
        sys, "argv",
        ["render_judge.py", str(png_path), "--rubric", str(rubric_path), "-o", str(out_path)],
    )
    render_judge.main()

    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["source"] == "stub"
    assert isinstance(payload["criteria"], list)
    assert len(payload["criteria"]) == 5
