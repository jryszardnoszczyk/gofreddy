"""Tests for autoresearch_v2/tools/verify_critique_integrity.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoresearch_v2.tools import verify_critique_integrity as v


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch):
    """Tmp repo with stub defended files at the expected relative paths."""
    monkeypatch.setenv("AUTORESEARCH_V2_ROOT", str(tmp_path))

    defended_dir = tmp_path / "judges" / "session" / "prompts"
    defended_dir.mkdir(parents=True)
    (defended_dir / "critique.md").write_text("# critique prompt (canonical)\n", encoding="utf-8")
    (defended_dir / "review.md").write_text("# review prompt (canonical)\n", encoding="utf-8")
    return tmp_path


def test_init_writes_manifest_with_expected_hashes(tmp_repo: Path):
    rc = v.main(["--init"])
    assert rc == 0
    manifest = tmp_repo / "autoresearch_v2" / ".critique-manifest.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text())
    assert set(data.keys()) == {p for p in v.DEFENDED_PATHS}
    for h in data.values():
        assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def test_verify_ok_after_init(tmp_repo: Path, capsys):
    v.main(["--init"])
    capsys.readouterr()
    rc = v.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "INTEGRITY OK" in out


def test_verify_detects_modified_prompt(tmp_repo: Path, capsys):
    v.main(["--init"])
    capsys.readouterr()
    (tmp_repo / "judges" / "session" / "prompts" / "critique.md").write_text(
        "# critique prompt (tampered)\n", encoding="utf-8"
    )
    rc = v.main([])
    out = capsys.readouterr().out
    assert rc == 2
    assert "INTEGRITY MISMATCH" in out
    assert "judges/session/prompts/critique.md" in out


def test_verify_missing_manifest_emits_remediation(tmp_repo: Path, capsys):
    rc = v.main([])
    out = capsys.readouterr().out
    assert rc == 2
    assert "MANIFEST MISSING" in out
    assert "verify_critique_integrity --init" in out


def test_verify_missing_defended_file_emits_clear_error(tmp_repo: Path, capsys):
    v.main(["--init"])
    capsys.readouterr()
    (tmp_repo / "judges" / "session" / "prompts" / "critique.md").unlink()
    rc = v.main([])
    out = capsys.readouterr().out
    assert rc == 2
    assert "DEFENDED FILE MISSING" in out
    assert "critique.md" in out


def test_grace_mode_manifest_refused(tmp_repo: Path, capsys):
    manifest = tmp_repo / "autoresearch_v2" / ".critique-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"__grace_mode__": True}))
    rc = v.main([])
    out = capsys.readouterr().out
    assert rc == 2
    assert "MANIFEST INVALID" in out or "grace" in out.lower()


def test_manifest_invalid_shape_refused(tmp_repo: Path, capsys):
    manifest = tmp_repo / "autoresearch_v2" / ".critique-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("[1, 2, 3]")  # array, not object
    rc = v.main([])
    out = capsys.readouterr().out
    assert rc == 2
    assert "INVALID" in out


def test_extra_unmanifested_file_flagged(tmp_repo: Path, capsys):
    v.main(["--init"])
    capsys.readouterr()
    rc, msg = v.verify(defended_paths=(*v.DEFENDED_PATHS, "judges/session/prompts/extra.md"))
    # extra.md doesn't exist on disk so we get DEFENDED FILE MISSING first
    assert rc == 2
    assert "DEFENDED FILE MISSING" in msg or "missing" in msg.lower()


def test_compute_live_hashes_raises_on_missing_file(tmp_repo: Path):
    (tmp_repo / "judges" / "session" / "prompts" / "review.md").unlink()
    with pytest.raises(FileNotFoundError):
        v.compute_live_hashes()


def test_manifest_path_override_via_env(tmp_repo: Path, monkeypatch, tmp_path):
    alt = tmp_path / "alt-manifest.json"
    monkeypatch.setenv("CRITIQUE_MANIFEST_PATH", str(alt))
    rc = v.main(["--init"])
    assert rc == 0
    assert alt.is_file()
    capsys_out = json.loads(alt.read_text())
    assert "judges/session/prompts/critique.md" in capsys_out


def test_diff_hashes_pure_function():
    a = {"x": "0" * 64, "y": "1" * 64}
    b = {"x": "0" * 64, "y": "1" * 64}
    assert v.diff_hashes(a, b) == []

    b2 = {"x": "0" * 64, "y": "2" * 64}
    issues = v.diff_hashes(a, b2)
    assert len(issues) == 1
    assert "y" in issues[0]

    b3 = {"x": "0" * 64}  # missing y
    issues = v.diff_hashes(a, b3)
    assert len(issues) == 1
    assert "missing live file" in issues[0]
