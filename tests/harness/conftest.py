"""Shared fixtures for harness tests."""

from __future__ import annotations

import os

import pytest

from harness.config import Config


@pytest.fixture()
def clean_env(monkeypatch):
    """Strip all HARNESS_* / harness-related env vars so tests start clean."""
    for key in list(os.environ):
        if key.startswith("HARNESS_") or key in (
            "MAX_CYCLES", "DRY_RUN", "MAX_RETRIES", "RETRY_DELAY",
            "PHASE", "EVAL_ONLY", "MAX_FIX_ATTEMPTS",
            "EVAL_MODEL", "FIXER_MODEL",
            "CODEX_EVAL_PROFILE", "CODEX_FIXER_PROFILE", "CODEX_VERIFIER_PROFILE",
            "CODEX_EVAL_MODEL", "CODEX_FIXER_MODEL", "CODEX_VERIFIER_MODEL",
            "BACKEND_PORT", "BACKEND_CMD", "BACKEND_LOG",
            "FIXER_WORKERS", "FIXER_DOMAINS",
            "FRONTEND_URL", "BACKEND_URL", "DATABASE_URL",
            "SUPABASE_URL", "SUPABASE_JWT_SECRET", "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
        ):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def default_config(clean_env) -> Config:
    """Config with all defaults (no CLI args, no env overrides)."""
    return Config.from_cli_and_env([])
