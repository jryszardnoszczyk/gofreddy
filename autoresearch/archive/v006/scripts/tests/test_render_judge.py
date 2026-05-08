"""Unit tests for render_judge.py.

Covers both backends (claude default + gemini legacy) + the stub
fallback. Subprocess calls are mocked — no real API or CLI invocation.
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


def test_grade_stub_fallback_when_backend_stub(tmp_path, monkeypatch):
    """RENDER_JUDGE_BACKEND=stub returns stub scores in the expected shape
    without hitting either backend."""
    monkeypatch.setenv("RENDER_JUDGE_BACKEND", "stub")

    png_path = tmp_path / "report-screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    rubric_path = tmp_path / "render-rubric.md"
    rubric_path.write_text("# Test rubric\n\nRND-1: Typography\n", encoding="utf-8")

    result = render_judge.grade(png_path, rubric_path)

    assert result["source"] == "stub"
    assert result["aggregate"] == 0.0
    assert isinstance(result["criteria"], list)
    assert len(result["criteria"]) == 5
    for c in result["criteria"]:
        assert c["criterion"] in render_judge.CRITERIA
        assert "score" in c
        assert "rationale" in c


def test_grade_default_backend_is_claude(tmp_path, monkeypatch):
    """Default backend (no env var set) should be claude."""
    monkeypatch.delenv("RENDER_JUDGE_BACKEND", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text("# rubric\n")

    fake_results = [
        {"criterion": "RND-1", "score": 5, "rationale": "claude graded"},
        {"criterion": "RND-2", "score": 4, "rationale": "claude graded"},
        {"criterion": "RND-3", "score": 4, "rationale": "claude graded"},
        {"criterion": "RND-4", "score": 5, "rationale": "claude graded"},
        {"criterion": "RND-5", "score": 0, "rationale": "n/a"},
    ]
    with mock.patch.object(
        render_judge, "grade_with_claude", return_value=fake_results,
    ):
        result = render_judge.grade(png_path, rubric_path)

    assert result["source"] == "claude"
    # (5+4+4+5)/4 = 4.5
    assert result["aggregate"] == 4.5


def test_grade_with_claude_extracts_json_from_response(tmp_path, monkeypatch):
    """grade_with_claude must locate + parse the JSON array even when the
    CLI prepends acknowledgement text or wraps in code fences."""
    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric_text = "# rubric\n"

    fake_response = (
        "I'll read the screenshot and grade it.\n\n"
        "```json\n"
        "[\n"
        '  {"criterion": "RND-1", "score": 4, "rationale": "good"},\n'
        '  {"criterion": "RND-2", "score": 5, "rationale": "great"},\n'
        '  {"criterion": "RND-3", "score": 3, "rationale": "ok"},\n'
        '  {"criterion": "RND-4", "score": 4, "rationale": "fine"},\n'
        '  {"criterion": "RND-5", "score": 0, "rationale": "n/a"}\n'
        "]\n"
        "```"
    )
    fake_proc = type("R", (), {
        "returncode": 0, "stdout": fake_response, "stderr": "",
    })()
    with mock.patch.object(render_judge.shutil, "which", return_value="/usr/bin/claude"), \
         mock.patch.object(render_judge.subprocess, "run", return_value=fake_proc):
        out = render_judge.grade_with_claude(png_path, rubric_text)

    assert out is not None
    assert len(out) == 5
    assert out[0]["criterion"] == "RND-1"
    assert out[0]["score"] == 4


def test_grade_with_claude_returns_none_when_cli_missing(tmp_path):
    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    with mock.patch.object(render_judge.shutil, "which", return_value=None):
        out = render_judge.grade_with_claude(png_path, "# rubric\n")
    assert out is None


def test_grade_with_claude_returns_none_on_rc_nonzero(tmp_path):
    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    fake_proc = type("R", (), {
        "returncode": 1, "stdout": "", "stderr": "some error",
    })()
    with mock.patch.object(render_judge.shutil, "which", return_value="/usr/bin/claude"), \
         mock.patch.object(render_judge.subprocess, "run", return_value=fake_proc):
        out = render_judge.grade_with_claude(png_path, "# rubric\n")
    assert out is None


def test_grade_with_claude_returns_none_on_unparseable_output(tmp_path):
    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    fake_proc = type("R", (), {
        "returncode": 0, "stdout": "no json here at all", "stderr": "",
    })()
    with mock.patch.object(render_judge.shutil, "which", return_value="/usr/bin/claude"), \
         mock.patch.object(render_judge.subprocess, "run", return_value=fake_proc):
        out = render_judge.grade_with_claude(png_path, "# rubric\n")
    assert out is None


def test_grade_falls_back_to_stub_when_claude_unavailable(tmp_path, monkeypatch):
    """Default backend=claude — when the CLI isn't on PATH, grade() falls
    back to stub (does NOT silently switch to gemini)."""
    monkeypatch.delenv("RENDER_JUDGE_BACKEND", raising=False)
    png_path = tmp_path / "screenshot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text("# rubric\n")

    with mock.patch.object(render_judge.shutil, "which", return_value=None):
        result = render_judge.grade(png_path, rubric_path)

    assert result["source"] == "stub"
    assert result["aggregate"] == 0.0


def test_grade_with_gemini_path_explicit_opt_in(tmp_path, monkeypatch):
    """Operator can still pin to gemini via RENDER_JUDGE_BACKEND=gemini."""
    monkeypatch.setenv("RENDER_JUDGE_BACKEND", "gemini")

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
    assert result["aggregate"] == 4.0
    assert result["screenshot"] == str(png_path)


def test_main_writes_output_json(tmp_path, monkeypatch, capsys):
    """`render_judge.py <png> -o <out>` writes well-formed JSON."""
    monkeypatch.setenv("RENDER_JUDGE_BACKEND", "stub")

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
