from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRET_SCAN_SCRIPT = PROJECT_ROOT / "scripts" / "secret_scan.sh"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    shutil.copy2(SECRET_SCAN_SCRIPT, repo / "scripts" / "secret_scan.sh")
    (repo / "README.md").write_text("test repo\n", encoding="utf-8")
    (repo / ".secret-scan-baseline.json").write_text("[]\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Secret Scan Test"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "README.md", ".secret-scan-baseline.json", "scripts/secret_scan.sh"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo


def _install_fake_docker(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "fake-docker.log"
    fake_docker = bin_dir / "docker"
    fake_docker.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            echo "$@" >> "${FAKE_DOCKER_LOG:?}"
            mode="${FAKE_DOCKER_MODE:-success}"
            report_json="${FAKE_DOCKER_REPORT_JSON:-[]}"

            mount_spec=""
            report_path=""
            for ((i=1; i<=$#; i++)); do
              arg="${!i}"
              if [[ "$arg" == "-v" ]]; then
                j=$((i+1))
                mount_spec="${!j}"
              elif [[ "$arg" == "--report-path" ]]; then
                j=$((i+1))
                report_path="${!j}"
              fi
            done

            exit_code=0
            write_report=1
            if [[ "$mode" == "fail_with_report" ]]; then
              exit_code=42
            elif [[ "$mode" == "fail_no_report" ]]; then
              exit_code=43
              write_report=0
            fi

            host_dir="${mount_spec%%:*}"
            container_dir="${mount_spec##*:}"
            if [[ "$write_report" == "1" && -n "$report_path" ]]; then
              host_report="${report_path/$container_dir/$host_dir}"
              mkdir -p "$(dirname "$host_report")"
              printf "%s\\n" "$report_json" > "$host_report"
            fi

            exit "$exit_code"
            """
        ),
        encoding="utf-8",
    )
    fake_docker.chmod(0o755)
    return bin_dir, log_file


def _env_with_fake_docker(bin_dir: Path, log_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_DOCKER_LOG"] = str(log_file)
    env.setdefault("FAKE_DOCKER_MODE", "success")
    env.setdefault("FAKE_DOCKER_REPORT_JSON", "[]")
    return env


def test_tracked_scan_uses_baseline_and_succeeds(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    bin_dir, log_file = _install_fake_docker(tmp_path)
    env = _env_with_fake_docker(bin_dir, log_file)
    env["FAKE_DOCKER_MODE"] = "success"
    env["FAKE_DOCKER_REPORT_JSON"] = "[]"

    proc = subprocess.run(
        ["bash", "scripts/secret_scan.sh", "tracked"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    report_path = repo / ".tmp" / "security-audit" / "gitleaks-tracked-report.json"
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == []

    log = log_file.read_text(encoding="utf-8")
    assert "--baseline-path /scan/.secret-scan-baseline.json" in log


def test_tracked_scan_cleans_tmp_dir_on_failure(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    bin_dir, log_file = _install_fake_docker(tmp_path)
    env = _env_with_fake_docker(bin_dir, log_file)
    env["FAKE_DOCKER_MODE"] = "fail_with_report"
    tmp_root = tmp_path / "tmp-root"
    tmp_root.mkdir()
    env["TMPDIR"] = str(tmp_root)
    env["FAKE_DOCKER_REPORT_JSON"] = '[{"Fingerprint":"fp-1"}]'

    proc = subprocess.run(
        ["bash", "scripts/secret_scan.sh", "tracked"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 42
    report_path = repo / ".tmp" / "security-audit" / "gitleaks-tracked-report.json"
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == [{"Fingerprint": "fp-1"}]
    leaked = list(tmp_root.glob("freddy-secret-scan-*"))
    assert leaked == []


def test_tracked_scan_failure_without_report_is_explicit(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    bin_dir, log_file = _install_fake_docker(tmp_path)
    env = _env_with_fake_docker(bin_dir, log_file)
    env["FAKE_DOCKER_MODE"] = "fail_no_report"

    proc = subprocess.run(
        ["bash", "scripts/secret_scan.sh", "tracked"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "tracked scan did not produce report" in proc.stderr
    report_path = repo / ".tmp" / "security-audit" / "gitleaks-tracked-report.json"
    assert not report_path.exists()


def test_baseline_refresh_updates_baseline_file(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    bin_dir, log_file = _install_fake_docker(tmp_path)
    env = _env_with_fake_docker(bin_dir, log_file)
    expected = [{"RuleID": "test-rule", "Fingerprint": "file:test-rule:1"}]
    env["FAKE_DOCKER_MODE"] = "success"
    env["FAKE_DOCKER_REPORT_JSON"] = json.dumps(expected)

    proc = subprocess.run(
        ["bash", "scripts/secret_scan.sh", "baseline-refresh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    baseline = json.loads((repo / ".secret-scan-baseline.json").read_text(encoding="utf-8"))
    assert baseline == expected
