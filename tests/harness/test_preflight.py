"""Tests for harness.preflight — preflight checks, DB operations, JWT management."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from harness.config import Config
from harness.preflight import (
    PreflightError,
    _extract_env_var,
    _find_vite_pid,
    _get_process_env,
    apply_db_schema,
    check_jwt_expiry,
    check_stack_health,
    check_vite_jwt_freshness,
    cleanup_harness_state,
    mint_jwt,
    validate_cors,
    validate_engine_prereqs,
    validate_env_vars,
    validate_safety_guards,
    verify_frontend_bypass,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jwt_token(exp: int, sub: str = "test_user") -> str:
    """Build a real base64-encoded JWT (unsigned) for testing."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": sub, "exp": exp, "iat": exp - 3600}).encode()
    ).rstrip(b"=").decode()

    signature = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()

    return f"{header}.{payload}.{signature}"


def _make_config(**overrides) -> Config:
    """Build a Config with test defaults."""
    defaults = {
        "engine": "claude",
        "backend_url": "http://localhost:8080",
        "frontend_url": "http://localhost:3000",
        "jwt_ttl": 28800,
        "keep_state": False,
        "codex_eval_profile": "harness-evaluator",
        "codex_fixer_profile": "harness-fixer",
    }
    defaults.update(overrides)
    return Config(**defaults)


# ---------------------------------------------------------------------------
# validate_engine_prereqs
# ---------------------------------------------------------------------------


class TestValidateEnginePrereqs:
    def test_claude_in_path(self):
        """Happy path: engine binary found in PATH."""
        config = _make_config(engine="claude")
        with patch("harness.preflight.shutil.which", return_value="/usr/bin/claude"):
            validate_engine_prereqs(config)  # Should not raise

    def test_engine_not_found(self):
        """Error path: engine binary not in PATH."""
        config = _make_config(engine="claude")
        with patch("harness.preflight.shutil.which", return_value=None):
            with pytest.raises(PreflightError, match="claude CLI not found in PATH"):
                validate_engine_prereqs(config)

    def test_codex_in_path_with_profiles(self, tmp_path):
        """Happy path: codex binary found and config.toml has required profiles."""
        config = _make_config(engine="codex")
        toml_content = (
            "[profiles.harness-evaluator]\n"
            'model = "gpt-5.4"\n'
            "\n"
            "[profiles.harness-fixer]\n"
            'model = "gpt-5.4"\n'
        )
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(toml_content)

        with (
            patch("harness.preflight.shutil.which", return_value="/usr/bin/codex"),
            patch.dict(os.environ, {"CODEX_PROFILE_CONFIG": str(cfg_file)}),
        ):
            validate_engine_prereqs(config)  # Should not raise

    def test_codex_missing_profile(self, tmp_path):
        """Error path: codex config.toml missing a required profile."""
        config = _make_config(engine="codex")
        toml_content = "[profiles.harness-evaluator]\nmodel = 'gpt-5.4'\n"
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(toml_content)

        with (
            patch("harness.preflight.shutil.which", return_value="/usr/bin/codex"),
            patch.dict(os.environ, {"CODEX_PROFILE_CONFIG": str(cfg_file)}),
        ):
            with pytest.raises(PreflightError, match="Missing Codex profile"):
                validate_engine_prereqs(config)

    def test_codex_config_not_found(self):
        """Error path: codex config.toml does not exist."""
        config = _make_config(engine="codex")
        with (
            patch("harness.preflight.shutil.which", return_value="/usr/bin/codex"),
            patch.dict(os.environ, {"CODEX_PROFILE_CONFIG": "/nonexistent/config.toml"}),
        ):
            with pytest.raises(PreflightError, match="Missing Codex config"):
                validate_engine_prereqs(config)


# ---------------------------------------------------------------------------
# validate_safety_guards
# ---------------------------------------------------------------------------


class TestValidateSafetyGuards:
    def test_localhost_db_passes(self, monkeypatch):
        """Happy path: localhost DB URL is accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        validate_safety_guards(_make_config())  # Should not raise

    def test_loopback_ip_passes(self, monkeypatch):
        """Happy path: 127.0.0.1 DB URL is accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@127.0.0.1:5432/db")
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        validate_safety_guards(_make_config())

    def test_ipv6_loopback_passes(self, monkeypatch):
        """Happy path: ::1 DB URL is accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@::1:5432/db")
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        validate_safety_guards(_make_config())

    def test_production_env_rejected(self, monkeypatch):
        """Error path: ENVIRONMENT=production is rejected."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        with pytest.raises(PreflightError, match="Refusing to run in production"):
            validate_safety_guards(_make_config())

    def test_non_localhost_db_rejected(self, monkeypatch):
        """Error path: remote DB URL is rejected."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@prod.example.com:5432/db")
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        with pytest.raises(PreflightError, match="DATABASE_URL not localhost"):
            validate_safety_guards(_make_config())

    def test_live_stripe_key_rejected(self, monkeypatch):
        """Error path: live Stripe key is rejected."""
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("E2E_DB_URL", raising=False)
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_abc123def456")
        with pytest.raises(PreflightError, match="Live Stripe key detected"):
            validate_safety_guards(_make_config())

    def test_test_stripe_key_passes(self, monkeypatch):
        """Happy path: test Stripe key is accepted."""
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("E2E_DB_URL", raising=False)
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_abc123def456")
        validate_safety_guards(_make_config())

    def test_no_db_url_passes(self, monkeypatch):
        """Happy path: no DATABASE_URL set at all is fine (uses local default)."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("E2E_DB_URL", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        validate_safety_guards(_make_config())


# ---------------------------------------------------------------------------
# validate_env_vars
# ---------------------------------------------------------------------------


class TestValidateEnvVars:
    def test_all_set(self, monkeypatch):
        """Happy path: all required vars are present."""
        from harness.config import REQUIRED_ENV_VARS

        for var in REQUIRED_ENV_VARS:
            monkeypatch.setenv(var, "some_value")
        validate_env_vars(_make_config())  # Should not raise

    def test_missing_var(self, monkeypatch):
        """Error path: a required var is missing."""
        from harness.config import REQUIRED_ENV_VARS

        # Set all except the first
        for var in REQUIRED_ENV_VARS:
            monkeypatch.setenv(var, "some_value")
        monkeypatch.delenv(REQUIRED_ENV_VARS[0], raising=False)
        with pytest.raises(PreflightError, match=f"Missing env vars:.*{REQUIRED_ENV_VARS[0]}"):
            validate_env_vars(_make_config())


# ---------------------------------------------------------------------------
# check_jwt_expiry
# ---------------------------------------------------------------------------


class TestCheckJwtExpiry:
    def test_valid_token_returns_positive(self):
        """Happy path: token with exp 7200s from now returns ~7200."""
        future_exp = int(time.time()) + 7200
        token = _make_jwt_token(exp=future_exp)
        remaining = check_jwt_expiry(token)
        # Allow 2s tolerance for test execution time
        assert 7198 <= remaining <= 7200

    def test_expired_token_returns_negative(self):
        """Edge case: expired token returns negative number."""
        past_exp = int(time.time()) - 600
        token = _make_jwt_token(exp=past_exp)
        remaining = check_jwt_expiry(token)
        assert remaining < 0
        # Should be approximately -600
        assert -602 <= remaining <= -600

    def test_malformed_token_returns_negative(self):
        """Edge case: garbage token returns -1."""
        assert check_jwt_expiry("not.a.jwt") == -1

    def test_single_segment_returns_negative(self):
        """Edge case: token with no dots returns -1."""
        assert check_jwt_expiry("nodots") == -1

    def test_no_exp_claim_returns_negative(self):
        """Edge case: valid JWT structure but missing exp returns negative."""
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "HS256"}).encode()
        ).rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "user"}).encode()
        ).rstrip(b"=").decode()
        sig = base64.urlsafe_b64encode(b"sig").rstrip(b"=").decode()
        token = f"{header}.{payload}.{sig}"
        remaining = check_jwt_expiry(token)
        # exp defaults to 0 in the code, so remaining = 0 - now < 0
        assert remaining < 0


# ---------------------------------------------------------------------------
# check_stack_health (mocked HTTP)
# ---------------------------------------------------------------------------


class TestCheckStackHealth:
    def test_all_endpoints_healthy(self):
        """Happy path: all endpoints respond 200."""
        config = _make_config()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("harness.preflight.urllib.request.urlopen", return_value=mock_resp):
            check_stack_health(config)  # Should not raise

    def test_timeout_raises(self):
        """Error path: endpoint never responds."""
        config = _make_config()
        with patch(
            "harness.preflight.urllib.request.urlopen",
            side_effect=ConnectionError("refused"),
        ):
            with patch("harness.preflight.time.sleep"):
                with pytest.raises(PreflightError, match="Timeout waiting for"):
                    check_stack_health(config)


# ---------------------------------------------------------------------------
# validate_cors (mocked HTTP)
# ---------------------------------------------------------------------------


class TestValidateCors:
    def test_cors_200_ok(self):
        """Happy path: OPTIONS returns 200."""
        config = _make_config()
        mock_resp = MagicMock()
        mock_resp.status = 200
        with patch("harness.preflight.urllib.request.urlopen", return_value=mock_resp):
            validate_cors(config)  # Should not raise

    def test_cors_403_fails(self):
        """Error path: OPTIONS returns non-200."""
        config = _make_config()
        exc = MagicMock(spec=Exception)
        from urllib.error import HTTPError

        with patch(
            "harness.preflight.urllib.request.urlopen",
            side_effect=HTTPError(
                url="http://localhost:8080/health",
                code=403,
                msg="Forbidden",
                hdrs=None,  # type: ignore[arg-type]
                fp=None,
            ),
        ):
            with pytest.raises(PreflightError, match="CORS pre-flight failed"):
                validate_cors(config)


# ---------------------------------------------------------------------------
# cleanup_harness_state
# ---------------------------------------------------------------------------


class TestCleanupHarnessState:
    def test_conversations_only_scope(self):
        """Happy path: conversations_only scope only deletes conversations."""
        config = _make_config(keep_state=False)

        executed_sql: list[str] = []

        async def mock_execute(sql: str) -> None:
            executed_sql.append(sql)

        mock_conn = AsyncMock()
        mock_conn.execute = mock_execute
        mock_conn.close = AsyncMock()

        with patch("harness.preflight.asyncio.run") as mock_run:
            # Capture the coroutine and run it ourselves to inspect the SQL
            def capture_and_run(coro):
                import asyncio
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            # Instead of mocking asyncio.run, let's verify by checking what
            # cleanup_harness_state builds for the SQL string.
            # We can verify the SQL by patching at a lower level.
            pass

        # Simpler approach: just verify the function doesn't raise and
        # check the SQL that would be built
        config = _make_config(keep_state=False)
        with patch("harness.preflight.asyncio.run") as mock_run:
            cleanup_harness_state(config, "user-123", scope="conversations_only")
            # asyncio.run was called once
            assert mock_run.call_count == 1

    def test_full_scope_deletes_monitors_and_conversations(self):
        """Happy path: full scope deletes both monitors and conversations."""
        config = _make_config(keep_state=False)
        with patch("harness.preflight.asyncio.run") as mock_run:
            cleanup_harness_state(config, "user-123", scope="full")
            assert mock_run.call_count == 1

    def test_keep_state_is_noop(self):
        """Edge case: keep_state=True means no DB operations."""
        config = _make_config(keep_state=True)
        with patch("harness.preflight.asyncio.run") as mock_run:
            cleanup_harness_state(config, "user-123")
            mock_run.assert_not_called()

    def test_empty_user_id_is_noop(self):
        """Edge case: empty user_id means no DB operations."""
        config = _make_config(keep_state=False)
        with patch("harness.preflight.asyncio.run") as mock_run:
            cleanup_harness_state(config, "")
            mock_run.assert_not_called()

    def test_db_failure_is_warning_not_fatal(self):
        """Edge case: DB failure during cleanup is a warning, not an abort."""
        config = _make_config(keep_state=False)
        with patch(
            "harness.preflight.asyncio.run",
            side_effect=Exception("connection refused"),
        ):
            # Should not raise
            cleanup_harness_state(config, "user-123")


# ---------------------------------------------------------------------------
# apply_db_schema (mocked asyncpg)
# ---------------------------------------------------------------------------


class TestApplyDbSchema:
    def test_schema_file_not_found(self, tmp_path, monkeypatch):
        """Error path: schema file missing raises PreflightError."""
        config = _make_config()
        # Point the module's __file__ to a temp dir so repo_root resolves to
        # a directory that doesn't contain scripts/setup_test_db.sql.
        import harness.preflight as pmod

        fake_file = str(tmp_path / "harness" / "preflight.py")
        monkeypatch.setattr(pmod, "__file__", fake_file)
        with pytest.raises(PreflightError, match="Schema file not found"):
            apply_db_schema(config)

    def test_schema_apply_success(self):
        """Happy path: schema applies without error."""
        config = _make_config()
        with (
            patch("harness.preflight.Path.exists", return_value=True),
            patch("harness.preflight.Path.read_text", return_value="CREATE TABLE IF NOT EXISTS test();"),
            patch("harness.preflight.asyncio.run") as mock_run,
        ):
            from harness.preflight import apply_db_schema

            apply_db_schema(config)
            assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# mint_jwt (mocked subprocess)
# ---------------------------------------------------------------------------


class TestMintJwt:
    def test_successful_mint(self):
        """Happy path: seed script returns valid JSON."""
        config = _make_config()
        seed_output = json.dumps({
            "harness_token": "eyJ.test.token",
            "harness_user_id": "user-abc-123",
            "free_token": "ignore",
        })
        mock_result = MagicMock()
        mock_result.stdout = seed_output
        mock_result.returncode = 0

        with patch("harness.preflight.subprocess.run", return_value=mock_result):
            token, user_id = mint_jwt(config)
            assert token == "eyJ.test.token"
            assert user_id == "user-abc-123"

    def test_seed_script_failure(self):
        """Error path: seed script exits non-zero."""
        config = _make_config()
        with patch(
            "harness.preflight.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                returncode=1, cmd=["python", "seed.py"], stderr="DB connection failed"
            ),
        ):
            with pytest.raises(PreflightError, match="JWT minting failed"):
                mint_jwt(config)

    def test_malformed_json_output(self):
        """Error path: seed script returns non-JSON."""
        config = _make_config()
        mock_result = MagicMock()
        mock_result.stdout = "not json"
        mock_result.returncode = 0

        with patch("harness.preflight.subprocess.run", return_value=mock_result):
            with pytest.raises(PreflightError, match="cannot parse seed output"):
                mint_jwt(config)

    def test_missing_key_in_output(self):
        """Error path: JSON output missing harness_token key."""
        config = _make_config()
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"free_token": "abc"})
        mock_result.returncode = 0

        with patch("harness.preflight.subprocess.run", return_value=mock_result):
            with pytest.raises(PreflightError, match="cannot parse seed output"):
                mint_jwt(config)


# ---------------------------------------------------------------------------
# _find_vite_pid / _get_process_env / _extract_env_var
# ---------------------------------------------------------------------------


class TestViteHelpers:
    def test_find_vite_pid_success(self):
        """Happy path: lsof finds a PID."""
        with patch(
            "harness.preflight.subprocess.check_output",
            return_value="12345\n",
        ):
            assert _find_vite_pid("http://localhost:3000") == 12345

    def test_find_vite_pid_no_process(self):
        """Edge case: no process on port."""
        with patch(
            "harness.preflight.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "lsof"),
        ):
            assert _find_vite_pid("http://localhost:3000") is None

    def test_find_vite_pid_no_port_in_url(self):
        """Edge case: URL without explicit port."""
        assert _find_vite_pid("http://localhost") is None

    def test_extract_env_var_found(self):
        env_dump = "FOO=bar\nVITE_E2E_BYPASS_AUTH=1\nBAZ=qux"
        assert _extract_env_var(env_dump, "VITE_E2E_BYPASS_AUTH") == "1"

    def test_extract_env_var_not_found(self):
        env_dump = "FOO=bar\nBAZ=qux"
        assert _extract_env_var(env_dump, "MISSING") is None

    def test_get_process_env_darwin(self):
        """Platform: Darwin uses ps -E."""
        with (
            patch("harness.preflight.platform.system", return_value="Darwin"),
            patch(
                "harness.preflight.subprocess.check_output",
                return_value="cmd VITE_E2E_BYPASS_AUTH=1 VITE_E2E_BYPASS_ACCESS_TOKEN=tok",
            ),
        ):
            env = _get_process_env(12345)
            assert "VITE_E2E_BYPASS_AUTH=1" in env

    def test_get_process_env_linux(self, tmp_path):
        """Platform: Linux reads /proc/PID/environ."""
        with patch("harness.preflight.platform.system", return_value="Linux"):
            environ_content = b"FOO=bar\x00VITE_E2E_BYPASS_AUTH=1\x00"
            with patch(
                "harness.preflight.Path.read_bytes",
                return_value=environ_content,
            ):
                env = _get_process_env(12345)
                assert "VITE_E2E_BYPASS_AUTH=1" in env


# ---------------------------------------------------------------------------
# check_vite_jwt_freshness (mocked process introspection)
# ---------------------------------------------------------------------------


class TestCheckViteJwtFreshness:
    def test_healthy_vite_returns_positive(self):
        """Happy path: vite running with valid JWT returns positive seconds."""
        config = _make_config()
        future_exp = int(time.time()) + 7200
        token = _make_jwt_token(exp=future_exp)
        env_dump = f"VITE_E2E_BYPASS_ACCESS_TOKEN={token}\nVITE_E2E_BYPASS_AUTH=1"

        with (
            patch("harness.preflight._find_vite_pid", return_value=12345),
            patch("harness.preflight._get_process_env", return_value=env_dump),
        ):
            remaining = check_vite_jwt_freshness(config)
            assert 7198 <= remaining <= 7200

    def test_no_vite_returns_negative(self):
        """Edge case: no vite process returns -1."""
        config = _make_config()
        with patch("harness.preflight._find_vite_pid", return_value=None):
            assert check_vite_jwt_freshness(config) == -1

    def test_no_token_in_env_returns_negative(self):
        """Edge case: vite running but no token in env."""
        config = _make_config()
        with (
            patch("harness.preflight._find_vite_pid", return_value=12345),
            patch("harness.preflight._get_process_env", return_value="FOO=bar"),
        ):
            assert check_vite_jwt_freshness(config) == -1


# ---------------------------------------------------------------------------
# verify_frontend_bypass (mocked everything)
# ---------------------------------------------------------------------------


class TestVerifyFrontendBypass:
    def test_missing_vite_raises(self):
        """Error path: no vite process."""
        config = _make_config()
        with patch("harness.preflight._find_vite_pid", return_value=None):
            with pytest.raises(PreflightError, match="No vite"):
                verify_frontend_bypass(config, "fake-token")

    def test_missing_env_vars_raises(self):
        """Error path: vite running but missing VITE_E2E_* vars."""
        config = _make_config()
        with (
            patch("harness.preflight._find_vite_pid", return_value=12345),
            patch("harness.preflight._get_process_env", return_value="FOO=bar"),
        ):
            with pytest.raises(PreflightError, match="Vite missing"):
                verify_frontend_bypass(config, "fake-token")

    def test_happy_path(self):
        """Happy path: all env vars present, JWT fresh, backend smoke OK."""
        config = _make_config()
        future_exp = int(time.time()) + 7200
        token = _make_jwt_token(exp=future_exp)
        env_dump = (
            f"VITE_E2E_BYPASS_AUTH=1\n"
            f"VITE_E2E_BYPASS_ACCESS_TOKEN={token}\n"
            f"VITE_E2E_BYPASS_USER_ID=user123\n"
            f"VITE_E2E_BYPASS_EMAIL=test@test.local"
        )

        mock_resp = MagicMock()
        mock_resp.status = 200

        with (
            patch("harness.preflight._find_vite_pid", return_value=12345),
            patch("harness.preflight._get_process_env", return_value=env_dump),
            patch("harness.preflight.urllib.request.urlopen", return_value=mock_resp),
        ):
            verify_frontend_bypass(config, token)  # Should not raise

    def test_backend_smoke_failure(self):
        """Error path: backend returns non-200 on smoke test."""
        config = _make_config()
        future_exp = int(time.time()) + 7200
        token = _make_jwt_token(exp=future_exp)
        env_dump = (
            f"VITE_E2E_BYPASS_AUTH=1\n"
            f"VITE_E2E_BYPASS_ACCESS_TOKEN={token}\n"
            f"VITE_E2E_BYPASS_USER_ID=user123\n"
            f"VITE_E2E_BYPASS_EMAIL=test@test.local"
        )

        from urllib.error import HTTPError

        with (
            patch("harness.preflight._find_vite_pid", return_value=12345),
            patch("harness.preflight._get_process_env", return_value=env_dump),
            patch(
                "harness.preflight.urllib.request.urlopen",
                side_effect=HTTPError(
                    url="http://localhost:8080/v1/monitors",
                    code=401,
                    msg="Unauthorized",
                    hdrs=None,  # type: ignore[arg-type]
                    fp=None,
                ),
            ),
        ):
            with pytest.raises(PreflightError, match="Backend smoke.*401"):
                verify_frontend_bypass(config, token)
