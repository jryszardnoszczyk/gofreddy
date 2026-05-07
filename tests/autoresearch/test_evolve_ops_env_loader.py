"""Regression tests for evolve_ops.load_repo_env_defaults — the .env loader.

Pins the two-tier allowlist (explicit per-key + prefix-based) shipped at
ca00c99 + 1654f05 (2026-05-06). Pre-fix the loader required every fixture
xpoz UUID to be added to a hardcoded list, which silently broke
``--lane all`` runs when a new monitoring fixture's UUID wasn't allowlisted.

Reference: ``autoresearch/evolve_ops.py:44-116``.
"""

from __future__ import annotations

import pytest

import evolve_ops


def _write_env(tmp_path, body):
    path = tmp_path / ".env"
    path.write_text(body)
    return path


def test_load_repo_env_defaults_explicit_keys_pass(tmp_path):
    """All keys in ``_ALLOWED_ENV_KEYS_EXPLICIT`` must round-trip through
    the loader.
    """
    env = _write_env(
        tmp_path,
        "EVOLUTION_EVAL_BACKEND=codex\n"
        "EVOLUTION_EVAL_MODEL=gpt-5.5\n"
        "EVOLUTION_EVAL_REASONING_EFFORT=high\n"
        "EVOLUTION_HOLDOUT_MANIFEST=/tmp/holdout.json\n"
        "EVOLUTION_HOLDOUT_JSON=/tmp/holdout.json\n"
        "EVOLUTION_PRIVATE_ARCHIVE_DIR=/tmp/private\n"
        "FREDDY_API_URL=http://localhost:7100\n"
        "FREDDY_API_KEY=secret\n"
        "OPENAI_API_KEY=sk-test\n",
    )
    result = dict(evolve_ops.load_repo_env_defaults(env))
    expected_keys = set(evolve_ops._ALLOWED_ENV_KEYS_EXPLICIT)
    assert set(result.keys()) == expected_keys
    assert result["EVOLUTION_EVAL_MODEL"] == "gpt-5.5"


def test_load_repo_env_defaults_prefix_keys_pass(tmp_path):
    """Keys matching ``AUTORESEARCH_SEARCH_MONITORING_*`` and
    ``AUTORESEARCH_HOLDOUT_MONITORING_*`` prefixes must auto-load without
    being declared in the explicit list.
    """
    env = _write_env(
        tmp_path,
        "AUTORESEARCH_SEARCH_MONITORING_abc123=fixture-uuid-1\n"
        "AUTORESEARCH_SEARCH_MONITORING_def456=fixture-uuid-2\n"
        "AUTORESEARCH_HOLDOUT_MONITORING_xyz789=holdout-uuid\n",
    )
    result = dict(evolve_ops.load_repo_env_defaults(env))
    assert result["AUTORESEARCH_SEARCH_MONITORING_abc123"] == "fixture-uuid-1"
    assert result["AUTORESEARCH_SEARCH_MONITORING_def456"] == "fixture-uuid-2"
    assert result["AUTORESEARCH_HOLDOUT_MONITORING_xyz789"] == "holdout-uuid"


def test_load_repo_env_defaults_random_key_rejected(tmp_path):
    """Keys outside the allowlist (explicit or prefix) must NOT load.
    Exfiltration / accidental-leak guard.
    """
    env = _write_env(
        tmp_path,
        "RANDOM_API_KEY=should-not-load\n"
        "AUTORESEARCH_BUT_NOT_MONITORING_x=should-not-load\n"
        "AUTORESEARCH_SEARCH_OTHER_y=should-not-load\n"
        "EVOLUTION_EVAL_MODEL=gpt-5.5\n",  # control
    )
    result = dict(evolve_ops.load_repo_env_defaults(env))
    assert result == {"EVOLUTION_EVAL_MODEL": "gpt-5.5"}
    assert "RANDOM_API_KEY" not in result
    assert "AUTORESEARCH_BUT_NOT_MONITORING_x" not in result


def test_load_repo_env_defaults_explicit_first_then_prefix_in_env_order(tmp_path):
    """Order invariant: explicit-allowlist keys come first (in the order
    declared in ``_ALLOWED_ENV_KEYS_EXPLICIT``), then prefix-loaded keys
    in the order they appear in the .env file. Stable order prevents
    .env shuffles from changing the resulting env-injection order
    downstream.
    """
    env = _write_env(
        tmp_path,
        # Mixed order in .env on purpose
        "AUTORESEARCH_SEARCH_MONITORING_zzz=last\n"
        "EVOLUTION_EVAL_MODEL=gpt-5.5\n"
        "AUTORESEARCH_SEARCH_MONITORING_aaa=first\n"
        "OPENAI_API_KEY=sk-test\n"
        "AUTORESEARCH_HOLDOUT_MONITORING_mmm=middle\n",
    )
    result = list(evolve_ops.load_repo_env_defaults(env))
    keys_in_order = [k for k, _ in result]
    # Explicit keys come first, in _ALLOWED_ENV_KEYS_EXPLICIT order.
    explicit_present = [
        k for k in evolve_ops._ALLOWED_ENV_KEYS_EXPLICIT if k in dict(result)
    ]
    assert keys_in_order[: len(explicit_present)] == explicit_present
    # Prefix keys after the explicit block, in .env order: zzz, aaa, mmm.
    prefix_keys = [
        k for k in keys_in_order
        if k.startswith(("AUTORESEARCH_SEARCH_MONITORING_", "AUTORESEARCH_HOLDOUT_MONITORING_"))
    ]
    assert prefix_keys == [
        "AUTORESEARCH_SEARCH_MONITORING_zzz",
        "AUTORESEARCH_SEARCH_MONITORING_aaa",
        "AUTORESEARCH_HOLDOUT_MONITORING_mmm",
    ]


def test_load_repo_env_defaults_empty_file_returns_empty(tmp_path):
    env = _write_env(tmp_path, "")
    assert evolve_ops.load_repo_env_defaults(env) == []


def test_load_repo_env_defaults_missing_file_returns_empty(tmp_path):
    missing = tmp_path / "does-not-exist.env"
    assert evolve_ops.load_repo_env_defaults(missing) == []


def test_load_repo_env_defaults_strips_quotes_and_comments(tmp_path):
    env = _write_env(
        tmp_path,
        "# leading comment\n"
        "\n"
        "EVOLUTION_EVAL_MODEL='gpt-5.5'\n"
        'OPENAI_API_KEY="sk-test"\n'
        "# trailing comment\n",
    )
    result = dict(evolve_ops.load_repo_env_defaults(env))
    assert result["EVOLUTION_EVAL_MODEL"] == "gpt-5.5"
    assert result["OPENAI_API_KEY"] == "sk-test"


def test_is_allowed_env_key_unit_helpers():
    """Direct unit checks on the predicate to lock the contract."""
    assert evolve_ops._is_allowed_env_key("EVOLUTION_EVAL_MODEL")
    assert evolve_ops._is_allowed_env_key("AUTORESEARCH_SEARCH_MONITORING_anything")
    assert evolve_ops._is_allowed_env_key("AUTORESEARCH_HOLDOUT_MONITORING_x")
    assert not evolve_ops._is_allowed_env_key("RANDOM_KEY")
    assert not evolve_ops._is_allowed_env_key("AUTORESEARCH_SEARCH_GEO_x")  # only monitoring
