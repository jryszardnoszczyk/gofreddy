"""Cache-first read semantics for session-invoked freddy commands.

Covers the contract (search-v1 flipped to hard_fail 2026-04-24):
  - search pool: cache miss → RuntimeError pointing at the prime-fixtures agent
    (no silent Python live-fetch fallback — gaps are filled by the agent).
  - holdout pool: cache miss → RuntimeError (hard-fail prevents identity leak).
  - unknown pool: hard-fail via `_default` (default-deny).
  - sha1-truncation collision guard (`src.arg == arg`).
  - Staleness warning is emitted but the cached payload is still returned.
  - Shape flags produce distinct cache keys.
  - End-to-end: `freddy monitor mentions` reads cache and never calls the
    live API when FREDDY_FIXTURE_* env is set to a seeded entry.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.freddy.fixture.cache import (
    CacheManifest,
    DataSourceRecord,
    artifact_filename,
    cache_path_for,
    write_cache_manifest,
)


# --- helpers ----------------------------------------------------------------


def _seed(
    cache_root: Path,
    pool: str,
    fixture_id: str,
    *,
    source: str,
    data_type: str,
    arg: str,
    version: str = "1.0",
    payload: dict | list | None = None,
    shape_flags: dict[str, str] | None = None,
    age_days: float = 0.0,
) -> Path:
    """Seed a valid cache entry (artifact + manifest) using real arg_hash."""
    cache_dir = cache_path_for(cache_root, pool, fixture_id, version)
    cache_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_filename(source, data_type, arg, shape_flags)
    (cache_dir / artifact).write_text(json.dumps(payload if payload is not None else {}))
    fetched_at = datetime.now(timezone.utc) - timedelta(days=age_days)
    write_cache_manifest(
        cache_dir,
        CacheManifest(
            fixture_id=fixture_id,
            fixture_version=version,
            pool=pool,
            fetched_at=fetched_at,
            fetched_by="test",
            data_sources=[
                DataSourceRecord(
                    source=source,
                    data_type=data_type,
                    arg=arg,
                    retention_days=30,
                    cached_artifact=artifact,
                )
            ],
        ),
    )
    return cache_root


def _set_env(monkeypatch, cache_root: Path, pool: str, fixture_id: str, version: str = "1.0"):
    monkeypatch.setenv("FREDDY_FIXTURE_CACHE_DIR", str(cache_root))
    monkeypatch.setenv("FREDDY_FIXTURE_POOL", pool)
    monkeypatch.setenv("FREDDY_FIXTURE_ID", fixture_id)
    monkeypatch.setenv("FREDDY_FIXTURE_VERSION", version)


# --- try_read_cache: direct unit tests --------------------------------------


def test_returns_none_when_env_not_set(tmp_path, monkeypatch):
    for var in (
        "FREDDY_FIXTURE_CACHE_DIR",
        "FREDDY_FIXTURE_POOL",
        "FREDDY_FIXTURE_ID",
        "FREDDY_FIXTURE_VERSION",
    ):
        monkeypatch.delenv(var, raising=False)

    from cli.freddy.fixture.cache_integration import try_read_cache

    assert try_read_cache("xpoz", "mentions", "mon-a") is None


def test_returns_none_when_only_some_env_vars_set(tmp_path, monkeypatch):
    # Partial env must be treated as unset; live-fetch preserves today's
    # manual workflow.
    monkeypatch.setenv("FREDDY_FIXTURE_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("FREDDY_FIXTURE_POOL", "search-v1")
    monkeypatch.delenv("FREDDY_FIXTURE_ID", raising=False)
    monkeypatch.delenv("FREDDY_FIXTURE_VERSION", raising=False)

    from cli.freddy.fixture.cache_integration import try_read_cache

    assert try_read_cache("xpoz", "mentions", "mon-a") is None


def test_returns_cached_payload_on_search_pool_hit(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    _seed(
        cache_root, "search-v1", "mon-a",
        source="xpoz", data_type="mentions", arg="mon-a",
        payload={"mentions": [{"id": "m1"}], "total": 1},
    )
    _set_env(monkeypatch, cache_root, "search-v1", "mon-a")

    from cli.freddy.fixture.cache_integration import try_read_cache

    data = try_read_cache("xpoz", "mentions", "mon-a")
    assert data == {"mentions": [{"id": "m1"}], "total": 1}


def test_search_pool_cache_miss_raises_with_priming_agent_pointer(tmp_path, monkeypatch):
    """search-v1 miss hard-fails with a pointer to the prime-fixtures agent.

    Policy flip (2026-04-24): silent Python live-fetch was removed. Gaps are
    now filled exclusively by the priming agent, and the error message
    surfaces that remediation path.
    """
    cache_root = tmp_path / "cache"
    _seed(
        cache_root, "search-v1", "mon-a",
        source="xpoz", data_type="mentions", arg="mon-a",
        payload={"mentions": []},
    )
    _set_env(monkeypatch, cache_root, "search-v1", "mon-a")

    from cli.freddy.fixture.cache_integration import try_read_cache

    with pytest.raises(RuntimeError) as excinfo:
        try_read_cache("xpoz", "mentions", "mon-missing")
    msg = str(excinfo.value)
    assert "Automatic live-fetch is disabled" in msg
    assert "prime-fixtures" in msg
    assert "mon-a" in msg  # fixture_id in the remediation


def test_holdout_pool_cache_miss_raises_runtimeerror(tmp_path, monkeypatch):
    _set_env(monkeypatch, tmp_path / "empty", "holdout-v1", "mon-missing")

    from cli.freddy.fixture.cache_integration import try_read_cache

    with pytest.raises(RuntimeError) as excinfo:
        try_read_cache("xpoz", "mentions", "mon-missing")
    msg = str(excinfo.value)
    assert "Holdout cache miss" in msg
    # Remediation command is part of the error message.
    assert "freddy fixture refresh" in msg
    assert "mon-missing" in msg


def test_unknown_pool_defaults_to_hard_fail(tmp_path, monkeypatch):
    # `_default` policy is hard_fail → unknown pool names cannot silently
    # downgrade isolation. Non-holdout pools use the generic priming-agent
    # remediation message (holdout keeps its identity-leak wording).
    _set_env(monkeypatch, tmp_path / "empty", "some-future-pool", "mon-a")

    from cli.freddy.fixture.cache_integration import try_read_cache

    with pytest.raises(RuntimeError, match="Automatic live-fetch is disabled"):
        try_read_cache("xpoz", "mentions", "mon-a")


def test_sha1_collision_guard_by_arg_equality(tmp_path, monkeypatch):
    """If two raw args hashed to the same 12-char prefix, src.arg check saves us.

    Simulated by manually writing a manifest whose DataSourceRecord has a
    different raw ``arg`` than the one requested, but claims the same
    ``cached_artifact`` the lookup would compute. The lookup MUST NOT return
    that record.
    """
    cache_root = tmp_path / "cache"
    pool, fixture_id = "search-v1", "mon-a"
    cache_dir = cache_path_for(cache_root, pool, fixture_id, "1.0")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Real hash for the requested arg.
    requested_arg = "wanted-arg"
    artifact = artifact_filename("xpoz", "mentions", requested_arg)
    (cache_dir / artifact).write_text(json.dumps({"leak": True}))

    # Manifest records the OTHER arg but points at the same artifact name
    # (simulating a hypothetical hash collision). `src.arg != requested_arg`
    # must cause cache-miss.
    write_cache_manifest(
        cache_dir,
        CacheManifest(
            fixture_id=fixture_id,
            fixture_version="1.0",
            pool=pool,
            fetched_at=datetime.now(timezone.utc),
            fetched_by="test",
            data_sources=[
                DataSourceRecord(
                    source="xpoz", data_type="mentions",
                    arg="other-arg",  # <-- different raw arg
                    retention_days=30,
                    cached_artifact=artifact,
                )
            ],
        ),
    )
    _set_env(monkeypatch, cache_root, pool, fixture_id)

    from cli.freddy.fixture.cache_integration import try_read_cache

    # Search pool → miss raises (policy flipped 2026-04-24); the guard still
    # works — we never return the wrong record's body.
    with pytest.raises(RuntimeError, match="Automatic live-fetch is disabled"):
        try_read_cache("xpoz", "mentions", requested_arg)


def test_staleness_warning_returns_cached_payload(tmp_path, monkeypatch, capsys):
    cache_root = tmp_path / "cache"
    # retention_days=30 in the seeded record; age_days=40 → stale.
    _seed(
        cache_root, "search-v1", "mon-a",
        source="xpoz", data_type="mentions", arg="mon-a",
        payload={"mentions": [{"id": "m1"}]},
        age_days=40.0,
    )
    _set_env(monkeypatch, cache_root, "search-v1", "mon-a")

    from cli.freddy.fixture.cache_integration import try_read_cache

    data = try_read_cache("xpoz", "mentions", "mon-a")
    assert data == {"mentions": [{"id": "m1"}]}
    captured = capsys.readouterr()
    # Warning lands on stderr, data still returned.
    assert "STALE" in captured.err.upper() or "AGING" in captured.err.upper()


def test_shape_flags_produce_distinct_cache_entries(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    # Seed with DEFAULT shape (no shape_flags).
    _seed(
        cache_root, "search-v1", "mon-a",
        source="xpoz", data_type="mentions", arg="mon-a",
        payload={"mentions": []},
    )
    _set_env(monkeypatch, cache_root, "search-v1", "mon-a")

    from cli.freddy.fixture.cache_integration import try_read_cache

    # Default shape → hit.
    assert try_read_cache("xpoz", "mentions", "mon-a") is not None
    # Non-default shape → cache miss (different hash), search pool → raises.
    with pytest.raises(RuntimeError, match="Automatic live-fetch is disabled"):
        try_read_cache(
            "xpoz", "mentions", "mon-a", shape_flags={"format": "summary"}
        )


# --- integration: freddy monitor mentions via Typer CliRunner ---------------


def test_monitor_mentions_uses_cache_without_calling_api(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    # The monitor.mentions CLI passes shape_flags={"format": format}; default
    # value of --format is "full", so the cache must be seeded with that shape.
    _seed(
        cache_root, "search-v1", "mon-abc",
        source="xpoz", data_type="mentions", arg="mon-abc",
        payload={"mentions": [{"id": "m1"}], "total": 1},
        shape_flags={"format": "full"},
    )
    _set_env(monkeypatch, cache_root, "search-v1", "mon-abc")

    from cli.freddy.commands import monitor as monitor_mod

    with patch.object(monitor_mod, "api_request") as mock_api, \
         patch.object(monitor_mod, "make_client") as mock_client, \
         patch.object(monitor_mod, "_require_config") as mock_cfg:
        mock_cfg.return_value = {"api_key": "x"}
        runner = CliRunner()
        result = runner.invoke(monitor_mod.app, ["mentions", "mon-abc"])
        assert result.exit_code == 0, result.output
        # Cached payload emitted on stdout.
        assert "m1" in result.output
        # Live fetch MUST NOT run.
        mock_api.assert_not_called()
        mock_client.assert_not_called()


def test_monitor_mentions_different_format_raises_on_miss(tmp_path, monkeypatch):
    """Shape-flag change hard-fails on search pool — no silent live-fetch.

    Policy flip (2026-04-24): the CLI must not silently fall back to the live
    API when the cache doesn't match the requested shape. The operator runs
    the priming agent (or adjusts the shape) instead.
    """
    cache_root = tmp_path / "cache"
    # Seed DEFAULT-shape cache (format=full).
    _seed(
        cache_root, "search-v1", "mon-abc",
        source="xpoz", data_type="mentions", arg="mon-abc",
        payload={"mentions": [{"id": "m1"}], "total": 1},
        shape_flags={"format": "full"},
    )
    _set_env(monkeypatch, cache_root, "search-v1", "mon-abc")

    from cli.freddy.commands import monitor as monitor_mod

    with patch.object(monitor_mod, "api_request") as mock_api, \
         patch.object(monitor_mod, "make_client") as mock_client, \
         patch.object(monitor_mod, "_require_config") as mock_cfg:
        mock_cfg.return_value = {"api_key": "x"}

        runner = CliRunner()
        result = runner.invoke(
            monitor_mod.app, ["mentions", "mon-abc", "--format", "summary"],
            catch_exceptions=False,
        )
        # The RuntimeError must surface (catch_exceptions=False): either
        # reraised, or Typer wraps it into exit 1 with the message on stderr.
        combined = (result.output or "") + (result.stderr or "") if hasattr(result, "stderr") else (result.output or "")
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            combined += str(result.exception)
        assert "Automatic live-fetch is disabled" in combined or result.exit_code != 0
        # The live API was never called either way.
        mock_api.assert_not_called()
        mock_client.assert_not_called()
