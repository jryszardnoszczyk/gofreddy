from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.env_doctor import check_env_contract

ENV_DOCTOR_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "env_doctor.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(
        root / ".env.example",
        "\n".join(
            [
                "DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54522/postgres",
                "SUPABASE_URL=http://127.0.0.1:54521",
            ]
        ),
    )
    _write(
        root / "frontend" / ".env.example",
        "\n".join(
            [
                "VITE_SUPABASE_URL=http://127.0.0.1:54521",
                "VITE_SUPABASE_ANON_KEY=test-anon",
                "VITE_API_URL=",
            ]
        ),
    )
    _write(
        root / "supabase" / "config.toml",
        """
[api]
port = 54521

[db]
port = 54522

[auth]
site_url = "http://127.0.0.1:3000"
additional_redirect_urls = ["http://localhost:3000/auth/callback"]
""".strip(),
    )
    _write(
        root / "frontend" / "vite.config.ts",
        """
export default {
  server: {
    port: 3000,
  },
}
""".strip(),
    )
    _write(
        root / "src" / "api" / "main.py",
        """
import os
origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
""".strip(),
    )
    return root


def test_env_doctor_reports_no_errors_for_proxy_first_defaults(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    findings = check_env_contract(root)
    errors = [finding for finding in findings if finding.level == "error"]
    assert errors == []


def test_env_doctor_fails_on_backend_port_mismatch(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    _write(
        root / ".env.example",
        "\n".join(
            [
                "DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:9999/postgres",
                "SUPABASE_URL=http://127.0.0.1:9998",
            ]
        ),
    )

    findings = check_env_contract(root)
    codes = {finding.code for finding in findings if finding.level == "error"}
    assert "supabase_port_mismatch" in codes
    assert "database_port_mismatch" in codes


def test_env_doctor_fails_when_frontend_required_keys_missing(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    _write(root / "frontend" / ".env.example", "VITE_SUPABASE_URL=http://127.0.0.1:54521")

    findings = check_env_contract(root)
    codes = {finding.code for finding in findings if finding.level == "error"}
    assert "frontend_env_missing_keys" in codes


def test_env_doctor_fails_when_vite_api_url_is_absolute(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    _write(
        root / "frontend" / ".env.example",
        "\n".join(
            [
                "VITE_SUPABASE_URL=http://127.0.0.1:54521",
                "VITE_SUPABASE_ANON_KEY=test-anon",
                "VITE_API_URL=http://localhost:8080",
            ]
        ),
    )
    _write(
        root / "src" / "api" / "main.py",
        'import os\norigins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:9999").split(",")\n',
    )

    findings = check_env_contract(root)
    codes = {finding.code for finding in findings if finding.level == "error"}
    assert "vite_api_url_not_proxy_first" in codes
    assert "dev_port_cors_contradiction" in codes


def _run_env_doctor(project_root: Path, *, strict: bool = False) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(ENV_DOCTOR_SCRIPT),
        "--project-root",
        str(project_root),
    ]
    if strict:
        command.append("--strict")
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_env_doctor_non_strict_reports_only_blocking_findings(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    result = _run_env_doctor(root, strict=False)
    assert result.returncode == 0
    assert "Environment doctor report: no blocking issues found" in result.stdout
    assert "cors_missing_loopback_variant" not in result.stdout
    assert "run with --strict to display non-blocking warning checks" in result.stdout


def test_env_doctor_strict_reports_warning_findings(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    result = _run_env_doctor(root, strict=True)
    assert result.returncode == 0
    assert "cors_missing_loopback_variant" in result.stdout
    assert "run with --strict to display non-blocking warning checks" not in result.stdout


def test_env_doctor_cli_returns_error_exit_code_on_contract_mismatch(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    _write(
        root / ".env.example",
        "\n".join(
            [
                "DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:9999/postgres",
                "SUPABASE_URL=http://127.0.0.1:9998",
            ]
        ),
    )
    result = _run_env_doctor(root, strict=False)
    assert result.returncode == 1
    assert "supabase_port_mismatch" in result.stdout
    assert "database_port_mismatch" in result.stdout
