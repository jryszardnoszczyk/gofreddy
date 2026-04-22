"""Tests for harness.preflight — fail-loud checks."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import pytest

from pathlib import Path

from harness import preflight
from harness.config import REQUIRED_ENV_VARS, Config, ConfigError


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


def test_claude_auth_missing_cli_raises(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: None)
    with pytest.raises(preflight.PreflightError, match="claude CLI not in PATH"):
        preflight._check_claude_auth(Config(engine="claude"))


def test_claude_auth_bare_requires_api_key(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(preflight.PreflightError, match="ANTHROPIC_API_KEY"):
        preflight._check_claude_auth(Config(engine="claude", claude_mode="bare"))


def test_claude_auth_bare_passes_with_api_key(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    preflight._check_claude_auth(Config(engine="claude", claude_mode="bare"))


def test_claude_auth_oauth_needs_dot_claude_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setattr(preflight.Path, "home", lambda: tmp_path)  # no ~/.claude
    with pytest.raises(preflight.PreflightError, match="~/.claude not found"):
        preflight._check_claude_auth(Config(engine="claude", claude_mode="oauth"))


def test_claude_auth_oauth_passes_with_dot_claude(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: "/usr/bin/claude")
    (tmp_path / ".claude").mkdir()
    monkeypatch.setattr(preflight.Path, "home", lambda: tmp_path)
    preflight._check_claude_auth(Config(engine="claude", claude_mode="oauth"))


def test_config_defaults_reflect_plan():
    """Success criterion: `--engine claude` is default, models default to 'opus'."""
    cfg = Config()
    assert cfg.engine == "claude"
    assert cfg.claude_mode == "oauth"
    assert cfg.eval_model == "opus"
    assert cfg.fixer_model == "opus"
    assert cfg.verifier_model == "opus"
    assert cfg.resume_branch == ""


def test_from_cli_and_env_rejects_invalid_engine(monkeypatch):
    from argparse import Namespace
    _valid_env(monkeypatch)
    ns = Namespace(engine="bogus")
    with pytest.raises(ConfigError, match="engine"):
        Config.from_cli_and_env(ns)


def test_from_cli_and_env_rejects_invalid_claude_mode(monkeypatch):
    from argparse import Namespace
    _valid_env(monkeypatch)
    ns = Namespace(claude_mode="weird")
    with pytest.raises(ConfigError, match="claude-mode"):
        Config.from_cli_and_env(ns)


@pytest.mark.parametrize("field,value", [
    ("claude_mode", "bare"),
    ("eval_model", "sonnet"),
    ("fixer_model", "opus"),
    ("verifier_model", "haiku"),
])
def test_from_cli_and_env_rejects_claude_flags_with_codex_engine(monkeypatch, field, value):
    """--engine codex + any claude-specific flag = operator-hostile silent ignore.
    ConfigError lists the conflicting flag so the user can fix it."""
    from argparse import Namespace
    _valid_env(monkeypatch)
    kwargs = {"engine": "codex", field: value}
    ns = Namespace(**kwargs)
    with pytest.raises(ConfigError, match="engine codex ignores"):
        Config.from_cli_and_env(ns)


def test_check_all_codex_skips_claude_auth(tmp_path, monkeypatch):
    """Success criterion: --engine codex doesn't touch Claude preflight."""
    _valid_env(monkeypatch)
    claude_checked = {"hit": False}
    def fake_claude(_cfg):
        claude_checked["hit"] = True
    monkeypatch.setattr(preflight, "_check_claude_auth", fake_claude)
    # Fail early at codex profile check so we don't run the whole pipeline.
    monkeypatch.setattr(preflight, "_check_codex_profiles",
                        lambda _cfg: (_ for _ in ()).throw(preflight.PreflightError("stop here")))
    with pytest.raises(preflight.PreflightError, match="stop here"):
        preflight.check_all(Config(engine="codex"))
    assert claude_checked["hit"] is False


def _init_local_repo(tmp_path: Path, monkeypatch) -> None:
    import subprocess as sp
    monkeypatch.chdir(tmp_path)
    sp.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    sp.run(["git", "-C", str(tmp_path), "config", "user.email", "t@test"], check=True)
    sp.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    (tmp_path / "a.txt").write_text("x\n", encoding="utf-8")
    sp.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    sp.run(["git", "-C", str(tmp_path), "commit", "-qm", "seed"], check=True)


@pytest.mark.parametrize("bad_branch", [
    "harness/run-does-not-exist",            # wrong format entirely
    "foo/bar",                                # wrong namespace
    "harness/run-20260101",                   # missing time
    "harness/run-123-456",                    # wrong digit counts
    "harness/run-20260101-000000; rm -rf /",  # injection attempt
    "harness/run-20260101-000000/../../etc",  # path traversal attempt
])
def test_check_resume_branch_rejects_malformed(tmp_path, monkeypatch, bad_branch):
    """Format check catches typos + closes git-ref-injection edge."""
    _init_local_repo(tmp_path, monkeypatch)
    with pytest.raises(preflight.PreflightError, match="not a harness staging branch"):
        preflight._check_resume_branch(bad_branch)


def test_check_resume_branch_well_formed_but_missing_raises(tmp_path, monkeypatch):
    """Well-formed but non-existent branch gets the 'not found' error after format passes."""
    _init_local_repo(tmp_path, monkeypatch)
    with pytest.raises(preflight.PreflightError, match="not found locally"):
        preflight._check_resume_branch("harness/run-20260101-000000")


def test_check_resume_branch_existing_passes(tmp_path, monkeypatch):
    import subprocess as sp
    _init_local_repo(tmp_path, monkeypatch)
    sp.run(["git", "-C", str(tmp_path), "branch", "harness/run-20260101-000000"], check=True)
    preflight._check_resume_branch("harness/run-20260101-000000")


def test_check_all_claude_skips_codex_profiles(tmp_path, monkeypatch):
    """Success criterion: --engine claude doesn't touch Codex preflight."""
    _valid_env(monkeypatch)
    codex_checked = {"hit": False}
    def fake_codex(_cfg):
        codex_checked["hit"] = True
    monkeypatch.setattr(preflight, "_check_codex_profiles", fake_codex)
    monkeypatch.setattr(preflight, "_check_claude_auth",
                        lambda _cfg: (_ for _ in ()).throw(preflight.PreflightError("stop here")))
    with pytest.raises(preflight.PreflightError, match="stop here"):
        preflight.check_all(Config(engine="claude"))
    assert codex_checked["hit"] is False


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
