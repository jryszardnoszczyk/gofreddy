"""Tests for autoresearch_v2/tools/freddy_inspect.py (renamed from inspect.py
on 2026-05-11 to avoid shadowing the stdlib inspect module — httpx/rich
pulled in inspect.get_annotations() during transitive import and resolved
it to our package-local file instead of stdlib)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from autoresearch_v2.tools import freddy_inspect as inspect


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_V2_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)
    return tmp_path


def _write_tsv(repo: Path, lane: str, rows: list[tuple]) -> Path:
    path = repo / "autoresearch_v2" / "lanes" / lane / "results.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(inspect.TSV_COLUMNS)]
    for row in rows:
        lines.append("\t".join(str(c) for c in row))
    path.write_text("\n".join(lines) + "\n")
    return path


# --- frontier ---------------------------------------------------------------


def test_frontier_returns_top_keep_per_lane(tmp_repo: Path, capsys):
    _write_tsv(tmp_repo, "geo", [
        ("2026-05-11T00:00:00Z", "abc1234", "4.5000", "100.0", "keep", "first", "{}"),
        ("2026-05-11T01:00:00Z", "def5678", "4.7700", "120.0", "keep", "second", "{}"),
        ("2026-05-11T02:00:00Z", "ghi9012", "0.0000", "30.0", "discard", "regress", "{}"),
    ])
    _write_tsv(tmp_repo, "competitive", [
        ("2026-05-11T00:00:00Z", "xyz0001", "7.4000", "200.0", "keep", "baseline", "{}"),
    ])
    rc = inspect.main(["frontier"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    by_lane = {d["lane"]: d for d in data}
    assert by_lane["geo"]["rows"] == 2
    assert by_lane["geo"]["top"]["composite"] == 4.77
    assert by_lane["geo"]["top"]["commit"] == "def5678"
    assert by_lane["competitive"]["top"]["composite"] == 7.4
    assert by_lane["monitoring"]["rows"] == 0
    assert by_lane["monitoring"]["top"] is None


def test_frontier_empty_tsv_no_crash(tmp_repo: Path, capsys):
    rc = inspect.main(["frontier"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert all(d["rows"] == 0 and d["top"] is None for d in data)


# --- topk -------------------------------------------------------------------


def test_topk_sorts_by_composite_desc(tmp_repo: Path, capsys):
    _write_tsv(tmp_repo, "geo", [
        ("t", "aaa1111", "2.5000", "10.0", "keep", "a", "{}"),
        ("t", "bbb2222", "4.5000", "10.0", "keep", "b", "{}"),
        ("t", "ccc3333", "3.5000", "10.0", "keep", "c", "{}"),
        ("t", "ddd4444", "5.5000", "10.0", "keep", "d", "{}"),
        ("t", "eee5555", "1.0000", "10.0", "discard", "e", "{}"),
    ])
    rc = inspect.main(["topk", "geo", "--k", "2"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2
    assert data[0]["commit"] == "ddd4444"
    assert data[1]["commit"] == "bbb2222"


def test_topk_unknown_lane_errors(tmp_repo: Path, capsys):
    rc = inspect.main(["topk", "bogus", "--k", "1"])
    assert rc == 2


def test_topk_empty_lane_prints_no_rows(tmp_repo: Path, capsys):
    rc = inspect.main(["topk", "geo", "--k", "5"])
    assert rc == 0
    assert "no rows" in capsys.readouterr().out


# --- show -------------------------------------------------------------------


def test_show_returns_tsv_match_and_git_summary(tmp_repo: Path, capsys):
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=tmp_repo,
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    _write_tsv(tmp_repo, "geo", [
        ("t", sha, "4.5000", "100.0", "keep", "match me", "{}"),
    ])

    rc = inspect.main(["show", sha])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["commit"] == sha
    assert len(data["tsv_rows"]) == 1
    assert data["tsv_rows"][0]["description"] == "match me"
    assert any("commit" in line.lower() for line in data["git_show"])


# --- diff -------------------------------------------------------------------


def test_diff_calls_git_with_lane_path(tmp_repo: Path, capsys):
    # 2 commits with a lane file in between
    lane_dir = tmp_repo / "autoresearch_v2" / "lanes"
    lane_dir.mkdir(parents=True, exist_ok=True)
    (lane_dir / "geo.md").write_text("v1\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "geo v1"], cwd=tmp_repo, check=True)
    sha1 = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_repo,
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    (lane_dir / "geo.md").write_text("v2\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "geo v2"], cwd=tmp_repo, check=True)
    sha2 = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_repo,
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    rc = inspect.main(["diff", sha1, sha2, "--lane", "geo"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "geo.md" in out
    assert "v1" in out or "v2" in out


# --- regressions ------------------------------------------------------------


def test_regressions_flags_drops_above_threshold(tmp_repo: Path, capsys):
    _write_tsv(tmp_repo, "geo", [
        ("t1", "a1111111", "5.0000", "10.0", "keep", "a", "{}"),
        ("t2", "b2222222", "4.8000", "10.0", "keep", "b", "{}"),
        ("t3", "c3333333", "2.0000", "10.0", "keep", "c", "{}"),  # drop > 20%
    ])
    rc = inspect.main(["regressions", "geo"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data["regressions"]) == 1
    assert data["regressions"][0]["from_commit"] == "b2222222"
    assert data["regressions"][0]["to_commit"] == "c3333333"
    assert data["regressions"][0]["drop_pct"] > 20


def test_regressions_insufficient_data(tmp_repo: Path, capsys):
    _write_tsv(tmp_repo, "geo", [
        ("t", "a1111111", "5.0000", "10.0", "keep", "a", "{}"),
        ("t", "b2222222", "4.8000", "10.0", "keep", "b", "{}"),
    ])
    rc = inspect.main(["regressions", "geo"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "need >=3" in out


# --- traces -----------------------------------------------------------------


def test_traces_lists_attempt_paths(tmp_repo: Path, capsys):
    attempt = tmp_repo / "autoresearch_v2" / "lanes" / "geo" / "attempts" / "abc1234" / "sessions" / "mayoclinic"
    attempt.mkdir(parents=True)
    (attempt / "session.md").write_text("# session\n")

    rc = inspect.main(["traces", "abc1234"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert any("abc1234" in p and "mayoclinic" in p for p in data["paths"])


def test_traces_unknown_commit_returns_empty(tmp_repo: Path, capsys):
    rc = inspect.main(["traces", "zzzzzzzz"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["paths"] == []


# --- failures ---------------------------------------------------------------


def test_failures_filters_severity_high(tmp_repo: Path, capsys):
    alerts = tmp_repo / "autoresearch_v2" / "alerts.jsonl"
    alerts.parent.mkdir(parents=True, exist_ok=True)
    alerts.write_text(
        json.dumps({"severity": "low", "code": "drift", "lane": "geo"}) + "\n"
        + json.dumps({"severity": "high", "code": "collapse", "lane": "geo"}) + "\n"
        + json.dumps({"severity": "medium", "code": "drift", "lane": "geo"}) + "\n"
        + json.dumps({"severity": "high", "code": "regression", "lane": "competitive"}) + "\n"
    )
    rc = inspect.main(["failures"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2
    assert all(r["severity"] == "high" for r in data)


def test_failures_no_alerts_file(tmp_repo: Path, capsys):
    rc = inspect.main(["failures"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "[]"


def test_failures_skips_malformed_lines(tmp_repo: Path, capsys):
    alerts = tmp_repo / "autoresearch_v2" / "alerts.jsonl"
    alerts.parent.mkdir(parents=True, exist_ok=True)
    alerts.write_text(
        json.dumps({"severity": "high", "code": "ok"}) + "\n"
        + "not valid json\n"
        + json.dumps({"severity": "high", "code": "ok2"}) + "\n"
    )
    rc = inspect.main(["failures"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2


# --- read_tsv low-level -----------------------------------------------------


def test_read_tsv_returns_empty_for_missing_file(tmp_repo: Path):
    assert inspect.read_tsv("geo") == []


def test_read_tsv_parses_composite_to_float(tmp_repo: Path):
    _write_tsv(tmp_repo, "geo", [
        ("t", "abc1234", "4.5000", "100.0", "keep", "x", "{}"),
        ("t", "def5678", "", "100.0", "crash", "y", "{}"),
    ])
    rows = inspect.read_tsv("geo")
    assert rows[0]["composite_float"] == 4.5
    assert rows[1]["composite_float"] is None
