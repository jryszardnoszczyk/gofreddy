"""Tests for CLI config management."""

import json
import os
import stat
from pathlib import Path

import pytest

from freddy.config import delete_config, load_config, save_config


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    """Override config directory to use tmp_path."""
    config_dir = tmp_path / ".freddy"
    config_file = config_dir / "config.json"
    monkeypatch.setattr("freddy.config._CONFIG_DIR", config_dir)
    monkeypatch.setattr("freddy.config._CONFIG_FILE", config_file)
    monkeypatch.delenv("FREDDY_API_KEY", raising=False)
    monkeypatch.delenv("FREDDY_API_URL", raising=False)
    return config_dir


class TestConfig:

    def test_load_returns_none_when_no_config(self, config_dir):
        assert load_config() is None

    def test_save_and_load(self, config_dir):
        save_config(api_key="vi_sk_test123", base_url="http://localhost:8080")
        config = load_config()
        assert config is not None
        assert config.api_key == "vi_sk_test123"
        assert config.base_url == "http://localhost:8080"

    def test_save_creates_0600_permissions(self, config_dir):
        save_config(api_key="vi_sk_test")
        config_file = config_dir / "config.json"
        file_stat = config_file.stat()
        assert stat.S_IMODE(file_stat.st_mode) == 0o600

    def test_env_var_takes_precedence(self, config_dir, monkeypatch):
        save_config(api_key="file_key")
        monkeypatch.setenv("FREDDY_API_KEY", "env_key")
        config = load_config()
        assert config.api_key == "env_key"

    def test_delete_config(self, config_dir):
        save_config(api_key="vi_sk_test")
        assert delete_config() is True
        assert load_config() is None

    def test_delete_nonexistent_config(self, config_dir):
        assert delete_config() is False

    def test_default_base_url(self, config_dir):
        save_config(api_key="vi_sk_test")
        config = load_config()
        assert config.base_url == "https://api.freddy.example"
