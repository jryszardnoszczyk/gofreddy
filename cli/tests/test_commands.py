"""Tests for CLI commands via Typer CliRunner."""

import json

import pytest
from typer.testing import CliRunner

from freddy.main import app

runner = CliRunner()


class TestAuthCommands:

    def test_login_saves_config(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".freddy"
        config_file = config_dir / "config.json"
        monkeypatch.setattr("freddy.config._CONFIG_DIR", config_dir)
        monkeypatch.setattr("freddy.config._CONFIG_FILE", config_file)
        monkeypatch.delenv("FREDDY_API_KEY", raising=False)

        result = runner.invoke(app, ["auth", "login", "--api-key", "vi_sk_test123"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert config_file.exists()

    def test_logout_no_config(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".freddy"
        config_file = config_dir / "config.json"
        monkeypatch.setattr("freddy.config._CONFIG_DIR", config_dir)
        monkeypatch.setattr("freddy.config._CONFIG_FILE", config_file)
        monkeypatch.delenv("FREDDY_API_KEY", raising=False)

        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["message"] == "No config file found"


class TestSessionCommands:

    def test_session_status_no_active(self, tmp_path, monkeypatch):
        session_file = tmp_path / "session.json"
        monkeypatch.setattr("freddy.session._SESSION_FILE", session_file)

        result = runner.invoke(app, ["session", "status"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "no_active_session"

    def test_session_end_no_active(self, tmp_path, monkeypatch):
        session_file = tmp_path / "session.json"
        monkeypatch.setattr("freddy.session._SESSION_FILE", session_file)
        monkeypatch.delenv("FREDDY_API_KEY", raising=False)

        # Remove config too
        config_dir = tmp_path / ".freddy_cfg"
        config_file = config_dir / "config.json"
        monkeypatch.setattr("freddy.config._CONFIG_DIR", config_dir)
        monkeypatch.setattr("freddy.config._CONFIG_FILE", config_file)

        result = runner.invoke(app, ["session", "end"])
        # Should fail: no config or no active session
        assert result.exit_code == 1


class TestHumanOutput:

    def test_human_flag_accepted(self, tmp_path, monkeypatch):
        session_file = tmp_path / "session.json"
        monkeypatch.setattr("freddy.session._SESSION_FILE", session_file)

        result = runner.invoke(app, ["--human", "session", "status"])
        assert result.exit_code == 0
        # Human output should NOT be JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)


class TestTranscriptCommand:

    def test_upload_without_from_hook_flag(self):
        result = runner.invoke(app, ["transcript", "upload"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["error"]["code"] == "missing_flag"
