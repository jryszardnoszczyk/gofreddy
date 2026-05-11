"""Tests for autoresearch_v2/tools/log_experiment.py.

These run against an isolated tmp git repo (via the `AUTORESEARCH_V2_ROOT`
env var) so they exercise the real `git` invocations without touching the
real repo.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from autoresearch_v2.tools import log_experiment


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Fresh git repo at tmp_path with one initial commit + lane prose file."""
    monkeypatch.setenv("AUTORESEARCH_V2_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)

    lane_dir = tmp_path / "autoresearch_v2" / "lanes"
    lane_dir.mkdir(parents=True)
    lane_md = lane_dir / "geo.md"
    lane_md.write_text("# geo lane (initial)\n")

    gitignore = tmp_path / "autoresearch_v2" / ".gitignore"
    gitignore.write_text("lanes/*/results.tsv\nlanes/*/holdout_results.tsv\nlanes/*/attempts/\nalerts.jsonl\n")

    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)

    return tmp_path


def _short(ref: str, repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", ref], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_keep_commits_and_appends_with_new_sha(tmp_repo: Path):
    parent_sha = _short("HEAD", tmp_repo)

    lane_md = tmp_repo / "autoresearch_v2" / "lanes" / "geo.md"
    lane_md.write_text("# geo lane (mutated)\n")

    row = log_experiment.log_experiment(
        lane="geo",
        status="keep",
        composite=4.77,
        wall_time_s=123.4,
        description="added X heuristic",
        asi_json={"rationale": "top-1 parent"},
    )

    new_sha = _short("HEAD", tmp_repo)
    assert new_sha != parent_sha
    assert row["commit"] == new_sha
    assert row["status"] == "keep"
    assert row["composite"] == "4.7700"
    assert row["wall_time_s"] == "123.4"

    tsv = tmp_repo / "autoresearch_v2" / "lanes" / "geo" / "results.tsv"
    assert tsv.exists()
    content = tsv.read_text().splitlines()
    assert content[0].split("\t") == list(log_experiment.TSV_COLUMNS)
    assert len(content) == 2
    assert content[1].split("\t")[1] == new_sha


def test_keep_refuses_when_working_tree_clean(tmp_repo: Path):
    with pytest.raises(RuntimeError, match="clean"):
        log_experiment.log_experiment(
            lane="geo",
            status="keep",
            composite=4.0,
            wall_time_s=10.0,
            description="no edits",
            asi_json="{}",
        )


def test_discard_resets_and_appends_with_parent_sha(tmp_repo: Path):
    parent_sha = _short("HEAD", tmp_repo)

    lane_md = tmp_repo / "autoresearch_v2" / "lanes" / "geo.md"
    lane_md.write_text("# geo lane (bad mutation)\n")

    row = log_experiment.log_experiment(
        lane="geo",
        status="discard",
        composite=2.1,
        wall_time_s=99.5,
        description="X regressed composite",
        asi_json={"error": "composite dropped"},
    )

    head_now = _short("HEAD", tmp_repo)
    assert head_now == parent_sha
    assert row["commit"] == parent_sha
    assert row["status"] == "discard"

    assert lane_md.read_text() == "# geo lane (initial)\n"


def test_discard_preserves_untracked_tsv_file(tmp_repo: Path):
    tsv = tmp_repo / "autoresearch_v2" / "lanes" / "geo" / "results.tsv"
    tsv.parent.mkdir(parents=True, exist_ok=True)
    tsv.write_text("preexisting\trow\n")

    lane_md = tmp_repo / "autoresearch_v2" / "lanes" / "geo.md"
    lane_md.write_text("# geo lane (mutation)\n")

    log_experiment.log_experiment(
        lane="geo",
        status="discard",
        composite=0.0,
        wall_time_s=1.0,
        description="reset test",
        asi_json="{}",
    )

    after = tsv.read_text()
    assert "preexisting\trow\n" in after
    assert "reset test" in after


def test_discard_when_clean_still_records(tmp_repo: Path):
    parent_sha = _short("HEAD", tmp_repo)
    row = log_experiment.log_experiment(
        lane="geo",
        status="discard",
        composite=None,
        wall_time_s=None,
        description="aborted before edit",
        asi_json="{}",
    )
    assert row["commit"] == parent_sha
    assert row["composite"] == ""
    assert row["wall_time_s"] == ""


def test_crash_status_records_with_parent_sha(tmp_repo: Path):
    parent_sha = _short("HEAD", tmp_repo)
    (tmp_repo / "autoresearch_v2" / "lanes" / "geo.md").write_text("# crashed mid-edit\n")

    row = log_experiment.log_experiment(
        lane="geo",
        status="crash",
        composite=None,
        wall_time_s=12.0,
        description="subprocess returned 137",
        asi_json={"exit_code": 137, "stdout_tail": "OOM"},
    )

    assert row["status"] == "crash"
    assert row["commit"] == parent_sha
    assert _short("HEAD", tmp_repo) == parent_sha


def test_tsv_creates_header_on_first_write(tmp_repo: Path):
    tsv = tmp_repo / "autoresearch_v2" / "lanes" / "competitive" / "results.tsv"
    assert not tsv.exists()

    log_experiment.log_experiment(
        lane="competitive",
        status="discard",
        composite=0.0,
        wall_time_s=1.0,
        description="first row test",
        asi_json="{}",
    )

    lines = tsv.read_text().splitlines()
    assert lines[0] == "\t".join(log_experiment.TSV_COLUMNS)
    assert len(lines) == 2


def test_asi_json_escapes_tabs_and_newlines(tmp_repo: Path):
    log_experiment.log_experiment(
        lane="geo",
        status="discard",
        composite=1.0,
        wall_time_s=1.0,
        description="escape test",
        asi_json="line1\nline2\twith_tab",
    )

    tsv = tmp_repo / "autoresearch_v2" / "lanes" / "geo" / "results.tsv"
    row = tsv.read_text().splitlines()[1]
    assert "\n" not in row[: -1] or row.endswith("\n") is False
    cells = row.split("\t")
    assert len(cells) == len(log_experiment.TSV_COLUMNS)
    assert cells[-1] == "line1\\nline2 with_tab"


def test_invalid_status_raises():
    with pytest.raises(ValueError, match="status"):
        log_experiment.log_experiment(
            lane="geo",
            status="not_a_status",
            composite=1.0,
            wall_time_s=1.0,
            description="bad",
            asi_json="{}",
        )


@pytest.mark.parametrize("bad_lane", ["", "geo/sub", ".hidden", "../escape"])
def test_invalid_lane_raises(bad_lane: str):
    with pytest.raises(ValueError, match="lane"):
        log_experiment.log_experiment(
            lane=bad_lane,
            status="discard",
            composite=1.0,
            wall_time_s=1.0,
            description="bad lane",
            asi_json="{}",
        )


def test_dry_run_writes_nothing(tmp_repo: Path):
    parent_sha = _short("HEAD", tmp_repo)
    (tmp_repo / "autoresearch_v2" / "lanes" / "geo.md").write_text("# dry-run mutation\n")

    row = log_experiment.log_experiment(
        lane="geo",
        status="keep",
        composite=4.0,
        wall_time_s=10.0,
        description="dry run",
        asi_json="{}",
        dry_run=True,
    )

    assert row["status"] == "keep"
    assert _short("HEAD", tmp_repo) == parent_sha

    tsv = tmp_repo / "autoresearch_v2" / "lanes" / "geo" / "results.tsv"
    assert not tsv.exists()


def test_asi_json_dict_serialized_compactly(tmp_repo: Path):
    (tmp_repo / "autoresearch_v2" / "lanes" / "geo.md").write_text("# dict asi\n")
    row = log_experiment.log_experiment(
        lane="geo",
        status="keep",
        composite=5.0,
        wall_time_s=20.0,
        description="dict asi test",
        asi_json={"a": 1, "b": [2, 3]},
    )
    parsed = json.loads(row["asi_json"])
    assert parsed == {"a": 1, "b": [2, 3]}
    assert ", " not in row["asi_json"]


def test_main_cli_exit_code_and_output(tmp_repo: Path, capsys):
    (tmp_repo / "autoresearch_v2" / "lanes" / "geo.md").write_text("# main cli test\n")
    rc = log_experiment.main(
        [
            "--lane", "geo", "--status", "keep",
            "--composite", "4.5",
            "--wall-time-seconds", "100.0",
            "--description", "cli test",
            "--asi-json", '{"k":"v"}',
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["status"] == "keep"
    assert parsed["composite"] == "4.5000"


def test_main_cli_error_exit_code(tmp_repo: Path, capsys):
    rc = log_experiment.main(
        [
            "--lane", "geo", "--status", "keep",
            "--composite", "4.5",
            "--wall-time-seconds", "100.0",
            "--description", "no edits",
            "--asi-json", "{}",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "clean" in err
