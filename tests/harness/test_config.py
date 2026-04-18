"""Tests for harness.config — Config dataclass, CLI parsing, env var loading."""

from __future__ import annotations

import pytest

from harness.config import Config, normalize_id


# ── normalize_id ──────────────────────────────────────────────────────


class TestNormalizeId:
    def test_uppercase_with_leading_zero(self):
        assert normalize_id("A01") == "A-1"

    def test_lowercase(self):
        assert normalize_id("b4") == "B-4"

    def test_double_digit(self):
        assert normalize_id("C12") == "C-12"

    def test_already_normalized(self):
        assert normalize_id("A-1") == "A-1"

    def test_with_dash_and_leading_zero(self):
        assert normalize_id("a-01") == "A-1"

    def test_outside_abc_range_unchanged(self):
        # Only [A-C] prefixes are handled; D and beyond pass through
        assert normalize_id("D5") == "D5"

    def test_whitespace_stripped(self):
        assert normalize_id("  B-3  ") == "B-3"

    def test_no_match_returns_stripped(self):
        assert normalize_id("foobar") == "foobar"


# ── Config defaults ───────────────────────────────────────────────────


class TestConfigDefaults:
    def test_default_values(self, default_config):
        c = default_config
        assert c.max_cycles == 5
        assert c.dry_run is False
        assert c.engine == "codex"
        assert c.eval_only is False
        assert c.only == []
        assert c.phase == "all"
        assert c.skip == []
        assert c.resume_branch == ""
        assert c.resume_cycle == 1
        assert c.tracks == ["a", "b", "c"]
        assert c.backend_port == 8080

    def test_config_is_frozen(self, default_config):
        with pytest.raises(AttributeError):
            default_config.max_cycles = 10


# ── CLI arg overrides ─────────────────────────────────────────────────


class TestCLIOverrides:
    def test_cycles_override(self, clean_env):
        c = Config.from_cli_and_env(["--cycles", "3"])
        assert c.max_cycles == 3

    def test_dry_run_flag(self, clean_env):
        c = Config.from_cli_and_env(["--dry-run"])
        assert c.dry_run is True

    def test_engine_override(self, clean_env):
        c = Config.from_cli_and_env(["--engine", "codex"])
        assert c.engine == "codex"

    def test_engine_case_insensitive(self, clean_env):
        c = Config.from_cli_and_env(["--engine", "CLAUDE"])
        assert c.engine == "claude"

    def test_eval_only_flag(self, clean_env):
        c = Config.from_cli_and_env(["--eval-only"])
        assert c.eval_only is True

    def test_only_comma_separated(self, clean_env):
        c = Config.from_cli_and_env(["--only", "A5,B2"])
        assert c.only == ["A-5", "B-2"]

    def test_only_with_leading_zeros(self, clean_env):
        c = Config.from_cli_and_env(["--only", "A01,b04"])
        assert c.only == ["A-1", "B-4"]

    def test_skip_parsed(self, clean_env):
        c = Config.from_cli_and_env(["--skip", "A4,B14"])
        assert c.skip == ["A-4", "B-14"]

    def test_phase_override(self, clean_env):
        c = Config.from_cli_and_env(["--phase", "2"])
        assert c.phase == "2"

    def test_fixer_workers_override(self, clean_env):
        c = Config.from_cli_and_env(["--fixer-workers", "3"])
        assert c.fixer_workers == 3


# ── Env var overrides ─────────────────────────────────────────────────


class TestEnvOverrides:
    def test_env_max_cycles(self, clean_env, monkeypatch):
        monkeypatch.setenv("MAX_CYCLES", "10")
        c = Config.from_cli_and_env([])
        assert c.max_cycles == 10

    def test_cli_overrides_env(self, clean_env, monkeypatch):
        monkeypatch.setenv("MAX_CYCLES", "10")
        c = Config.from_cli_and_env(["--cycles", "3"])
        assert c.max_cycles == 3

    def test_env_tracks_space_separated(self, clean_env, monkeypatch):
        monkeypatch.setenv("HARNESS_TRACKS", "a b c")
        c = Config.from_cli_and_env([])
        assert c.tracks == ["a", "b", "c"]

    def test_env_tracks_comma_separated(self, clean_env, monkeypatch):
        monkeypatch.setenv("HARNESS_TRACKS", "a,b,c")
        c = Config.from_cli_and_env([])
        assert c.tracks == ["a", "b", "c"]

    def test_env_tracks_mixed_separators(self, clean_env, monkeypatch):
        monkeypatch.setenv("HARNESS_TRACKS", "a, b c")
        c = Config.from_cli_and_env([])
        assert c.tracks == ["a", "b", "c"]

    def test_env_bool_true_variants(self, clean_env, monkeypatch):
        for val in ("true", "1", "yes", "True", "YES"):
            monkeypatch.setenv("DRY_RUN", val)
            c = Config.from_cli_and_env([])
            assert c.dry_run is True, f"DRY_RUN={val} should be True"

    def test_env_bool_false(self, clean_env, monkeypatch):
        monkeypatch.setenv("DRY_RUN", "false")
        c = Config.from_cli_and_env([])
        assert c.dry_run is False

    def test_env_engine(self, clean_env, monkeypatch):
        monkeypatch.setenv("HARNESS_ENGINE", "codex")
        c = Config.from_cli_and_env([])
        assert c.engine == "codex"

    def test_env_only(self, clean_env, monkeypatch):
        monkeypatch.setenv("HARNESS_ONLY", "A5")
        c = Config.from_cli_and_env([])
        assert c.only == ["A-5"]

    def test_env_fixer_workers(self, clean_env, monkeypatch):
        monkeypatch.setenv("FIXER_WORKERS", "3")
        c = Config.from_cli_and_env([])
        assert c.fixer_workers == 3

    def test_cli_fixer_workers_overrides_env(self, clean_env, monkeypatch):
        monkeypatch.setenv("FIXER_WORKERS", "1")
        c = Config.from_cli_and_env(["--fixer-workers", "3"])
        assert c.fixer_workers == 3

    def test_env_fixer_domains_mixed_separators(self, clean_env, monkeypatch):
        monkeypatch.setenv("FIXER_DOMAINS", "A,B C")
        c = Config.from_cli_and_env([])
        assert c.fixer_domains == ["A", "B", "C"]

    def test_fixer_domains_default(self, clean_env):
        c = Config.from_cli_and_env([])
        assert c.fixer_domains == ["A", "B", "C"]


# ── Validation errors ─────────────────────────────────────────────────


class TestValidation:
    def test_invalid_engine(self, clean_env):
        with pytest.raises(SystemExit):
            Config.from_cli_and_env(["--engine", "gpt"])

    def test_resume_cycle_without_branch(self, clean_env):
        with pytest.raises(SystemExit):
            Config.from_cli_and_env(["--resume-cycle", "2"])

    def test_resume_cycle_with_branch_ok(self, clean_env):
        c = Config.from_cli_and_env(["--resume-branch", "harness/run-123", "--resume-cycle", "2"])
        assert c.resume_cycle == 2
        assert c.resume_branch == "harness/run-123"

    def test_fixer_workers_zero(self, clean_env):
        with pytest.raises(SystemExit):
            Config.from_cli_and_env(["--fixer-workers", "0"])
