"""Tests for scripts/harness_verdict_audit — internal-consistency checks
between fixer-written verdicts and actual git state on the staging branch."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest
import yaml

# Load the script as a module (it lives outside any package).
_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "harness_verdict_audit.py"
_spec = importlib.util.spec_from_file_location("harness_verdict_audit", _SCRIPT)
audit_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit_mod)


@pytest.fixture()
def staging_repo(tmp_path, monkeypatch):
    """A bare repo with a `main` branch and a `harness/run-<ts>` branch the
    audit script can `git log main..` against."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "seed.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed"], check=True)
    subprocess.run(["git", "-C", str(repo), "checkout", "-qb", "harness/run-test"], check=True)
    monkeypatch.chdir(repo)
    return repo


def _commit_fix(repo: Path, finding_id: str, cycle: int = 1) -> str:
    """Land a `harness: fix <id>@c<n>` commit on the current branch."""
    target = repo / f"{finding_id}.txt"
    target.write_text(f"{finding_id}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-qm",
         f"harness: fix {finding_id}@c{cycle} — test fix"],
        check=True,
    )
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
    ).strip()


def _revert_commit(repo: Path, sha: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "revert", "--no-edit", sha],
        check=True, capture_output=True,
    )


def _make_run_dir(tmp_path: Path) -> Path:
    rd = tmp_path / "run-test"
    rd.mkdir()
    return rd


def _write_verdict(run_dir: Path, track: str, finding_id: str,
                   verdict: str, reason: str = "") -> None:
    p = run_dir / "verdicts" / track / f"{finding_id}.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump({"verdict": verdict, "reason": reason, "adjacent_checked": []}),
        encoding="utf-8",
    )


def test_audit_clean_run_no_inconsistencies(staging_repo, tmp_path):
    run_dir = _make_run_dir(tmp_path)
    _commit_fix(staging_repo, "F-a-1")
    _write_verdict(run_dir, "a", "F-a-1", "passed", "repro green")

    results = audit_mod.audit(run_dir)
    assert results == {}


def test_audit_detects_claimed_passed_but_missing(staging_repo, tmp_path):
    """Verdict says passed but no commit ever landed (e.g., orchestrator
    crashed between verdict-write and _commit_fix)."""
    run_dir = _make_run_dir(tmp_path)
    _write_verdict(run_dir, "a", "F-a-1", "passed", "repro green")
    # No fix commit on the branch.

    results = audit_mod.audit(run_dir)
    assert "claimed-passed-but-missing" in results
    assert results["claimed-passed-but-missing"][0][0] == "F-a-1"


def test_audit_detects_claimed_passed_but_reverted(staging_repo, tmp_path):
    """Verdict says passed and commit landed, but commit was reverted —
    likely a stale-verdict-on-resume scenario (commit 54ade91 fix)."""
    run_dir = _make_run_dir(tmp_path)
    sha = _commit_fix(staging_repo, "F-a-1")
    _revert_commit(staging_repo, sha)
    _write_verdict(run_dir, "a", "F-a-1", "passed", "stale verdict")

    results = audit_mod.audit(run_dir)
    assert "claimed-passed-but-reverted" in results


def test_audit_detects_claimed_failed_but_not_reverted(staging_repo, tmp_path):
    """Verdict says failed but the commit is still on the branch (revert-phase
    crashed mid-revert, or operator manually un-reverted)."""
    run_dir = _make_run_dir(tmp_path)
    _commit_fix(staging_repo, "F-a-1")
    _write_verdict(run_dir, "a", "F-a-1", "failed", "probe 4 broke")

    results = audit_mod.audit(run_dir)
    assert "claimed-failed-but-not-reverted" in results


def test_audit_detects_no_verdict_but_shipped(staging_repo, tmp_path):
    """Commit on branch with no verdict YAML at all — the fixer skipped
    writing it, or the YAML was deleted."""
    run_dir = _make_run_dir(tmp_path)
    _commit_fix(staging_repo, "F-a-1")
    # Intentionally write no verdict.

    results = audit_mod.audit(run_dir)
    assert "no-verdict-but-shipped" in results
    assert results["no-verdict-but-shipped"][0][0] == "F-a-1"


def test_audit_main_exits_0_on_clean(staging_repo, tmp_path, capsys):
    run_dir = _make_run_dir(tmp_path)
    _commit_fix(staging_repo, "F-a-1")
    _write_verdict(run_dir, "a", "F-a-1", "passed", "ok")

    rc = audit_mod.main(["--run-dir", str(run_dir)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "clean" in captured.out


def test_audit_main_exits_1_on_inconsistency(staging_repo, tmp_path, capsys):
    run_dir = _make_run_dir(tmp_path)
    _commit_fix(staging_repo, "F-a-1")
    # No verdict YAML for F-a-1 — should be flagged.

    rc = audit_mod.main(["--run-dir", str(run_dir)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "no-verdict-but-shipped" in captured.out


def test_audit_main_missing_run_dir_exits_2(tmp_path, capsys):
    rc = audit_mod.main(["--run-dir", str(tmp_path / "nope")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "run-dir not found" in err
