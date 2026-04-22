"""Tests for harness.findings — parse + route."""
from __future__ import annotations

from pathlib import Path

import pytest

from harness.findings import DEFECT_CATEGORIES, Finding, parse, route


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "findings.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_parse_single_finding(tmp_path: Path) -> None:
    text = """---
id: F-a-1-01
track: a
category: crash
confidence: high
summary: freddy --help crashes
files:
  - cli/freddy/main.py
reproduction: |
  .venv/bin/freddy --help
---

Stack trace: ImportError foo bar
"""
    findings = parse(_write(tmp_path, text))
    assert len(findings) == 1
    f = findings[0]
    assert f.id == "F-a-1-01"
    assert f.category == "crash"
    assert f.confidence == "high"
    assert f.track == "a"
    assert f.files == ("cli/freddy/main.py",)
    assert "Stack trace" in f.evidence


def test_parse_multiple_findings(tmp_path: Path) -> None:
    text = """---
id: F-a-1-01
track: a
category: crash
confidence: high
summary: one
---

body 1

---
id: F-a-1-02
track: a
category: doc-drift
confidence: medium
summary: two
---

body 2
"""
    findings = parse(_write(tmp_path, text))
    assert len(findings) == 2
    assert findings[0].id == "F-a-1-01"
    assert findings[1].category == "doc-drift"


def test_parse_empty_and_missing(tmp_path: Path) -> None:
    assert parse(tmp_path / "missing.md") == []
    assert parse(_write(tmp_path, "")) == []
    assert parse(_write(tmp_path, "   \n\n")) == []


def test_parse_malformed_yaml_raises(tmp_path: Path) -> None:
    text = """---
id: F-a-1-01
track: a
category: [unclosed
---

body
"""
    with pytest.raises(ValueError, match="malformed YAML"):
        parse(_write(tmp_path, text))


def test_parse_rejects_unknown_category(tmp_path: Path) -> None:
    text = """---
id: X
track: a
category: invented
confidence: high
summary: s
---

body
"""
    with pytest.raises(ValueError, match="unknown category"):
        parse(_write(tmp_path, text))


def _make(category: str, confidence: str, track: str = "a", fid: str = "X") -> Finding:
    return Finding(id=fid, track=track, category=category, confidence=confidence, summary=fid)


def test_route_partitions_high_confidence_defects() -> None:
    findings = [
        _make("crash", "high", fid="A1"),
        _make("5xx", "high", fid="A2"),
        _make("crash", "medium", fid="M1"),
        _make("doc-drift", "high", fid="D1"),
        _make("low-confidence", "high", fid="L1"),
        _make("console-error", "low", fid="C1"),
    ]
    actionable, review = route(findings)
    assert {f.id for f in actionable} == {"A1", "A2"}
    assert {f.id for f in review} == {"M1", "D1", "L1", "C1"}


def test_route_is_disjoint() -> None:
    findings = [_make(c, "high") for c in DEFECT_CATEGORIES] + [
        _make("doc-drift", "high"),
        _make("low-confidence", "high"),
    ]
    actionable, review = route(findings)
    assert set(actionable).isdisjoint(set(review))
    assert len(actionable) + len(review) == len(findings)
