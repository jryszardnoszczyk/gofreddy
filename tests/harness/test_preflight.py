"""Tests for harness.preflight — fail-loud checks."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import pytest

from harness import preflight
from harness.config import REQUIRED_ENV_VARS, Config


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in REQUIRED_ENV_VARS + ("ENVIRONMENT",):
        monkeypatch.delenv(v, raising=False)


def _valid_env(monkeypatch):
    for v in REQUIRED_ENV_VARS:
        monkeypatch.setenv(v, "set")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")


def test_check_all_missing_env_var_raises(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/test")
    with pytest.raises(preflight.PreflightError, match="missing env vars"):
        preflight.check_all(Config())


def test_safety_guards_refuse_production(monkeypatch):
    _valid_env(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(preflight.PreflightError, match="production"):
        preflight._check_safety_guards(Config())


def test_safety_guards_refuse_nonlocal_db(monkeypatch):
    _valid_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@prod.supabase.co:5432/db")
    with pytest.raises(preflight.PreflightError, match="non-local"):
        preflight._check_safety_guards(Config())


def test_codex_profile_missing_raises(tmp_path, monkeypatch):
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "config.toml").write_text(
        "model = 'gpt-5.4'\n[profiles.harness-evaluator]\nshell_environment_policy.inherit = 'all'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(preflight.Path, "home", lambda: tmp_path)
    with pytest.raises(preflight.PreflightError, match="missing codex profile"):
        preflight._check_codex_profiles(Config())


def test_codex_profile_missing_inherit_raises(tmp_path, monkeypatch):
    (tmp_path / ".codex").mkdir()
    toml = (
        "[profiles.harness-evaluator]\n"
        "shell_environment_policy.inherit = 'core'\n"
        "[profiles.harness-fixer]\n"
        "shell_environment_policy.inherit = 'all'\n"
        "[profiles.harness-verifier]\n"
        "shell_environment_policy.inherit = 'all'\n"
    )
    (tmp_path / ".codex" / "config.toml").write_text(toml, encoding="utf-8")
    monkeypatch.setattr(preflight.Path, "home", lambda: tmp_path)
    with pytest.raises(preflight.PreflightError, match='inherit = "all"'):
        preflight._check_codex_profiles(Config())


def test_codex_profile_happy_path(tmp_path, monkeypatch):
    (tmp_path / ".codex").mkdir()
    toml = (
        "[profiles.harness-evaluator]\nshell_environment_policy.inherit = 'all'\n"
        "[profiles.harness-fixer]\nshell_environment_policy.inherit = 'all'\n"
        "[profiles.harness-verifier]\nshell_environment_policy.inherit = 'all'\n"
    )
    (tmp_path / ".codex" / "config.toml").write_text(toml, encoding="utf-8")
    monkeypatch.setattr(preflight.Path, "home", lambda: tmp_path)
    preflight._check_codex_profiles(Config())


def test_cli_integrity_missing_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(preflight.PreflightError, match="uv pip install"):
        preflight._check_cli_integrity()


def test_cli_integrity_nonzero_exit_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    freddy = bin_dir / "freddy"
    freddy.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    freddy.chmod(0o755)
    with pytest.raises(preflight.PreflightError, match="uv pip install"):
        preflight._check_cli_integrity()


def test_gh_auth_missing_raises(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: None)
    with pytest.raises(preflight.PreflightError, match="gh CLI not in PATH"):
        preflight._check_gh_auth()


def _fake_jwt(ttl_seconds: int) -> str:
    exp = int(time.time()) + ttl_seconds
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def test_jwt_envelope_too_short_raises():
    config = Config(max_walltime=14400, jwt_envelope_padding=600)
    token = _fake_jwt(ttl_seconds=100)
    with pytest.raises(preflight.PreflightError, match="TTL"):
        preflight._check_jwt_envelope(token, config)


def test_jwt_envelope_sufficient_passes():
    config = Config(max_walltime=100, jwt_envelope_padding=60)
    token = _fake_jwt(ttl_seconds=1000)
    preflight._check_jwt_envelope(token, config)
