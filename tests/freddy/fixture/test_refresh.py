"""Tests for `freddy fixture refresh`.

Subprocess calls are stubbed via `@patch("cli.freddy.fixture.refresh._run_source_fetch")`
— no real freddy commands run. All cache I/O uses ``tmp_path``.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app
from cli.freddy.fixture.cache import (
    CacheManifest,
    DataSourceRecord,
    cache_path_for,
    load_cache_manifest,
    write_cache_manifest,
)
from cli.freddy.fixture.refresh import (
    HOLDOUT_CREDENTIALS_PATH,
    _determine_sources,
    pool_on_miss,
)
from cli.freddy.fixture.schema import FixtureSpec


_MON_FIXTURES = [{
    "fixture_id": "mon-a", "client": "acme",
    "context": "https://acme.com", "version": "1.0",
    "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"},
}]


_BATCH_FIXTURES = [
    {"fixture_id": f"mon-{name}", "client": "acme",
     "context": f"https://{name}.com", "version": "1.0",
     "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"}}
    for name in ("fresh", "aging", "stale")
]


# -- dry-run / structural ------------------------------------------------


def test_refresh_dry_run_prints_plan_no_write(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1",
        "--cache-root", str(tmp_path / "cache"),
        "--dry-run",
    ])
    assert result.exit_code == 0, result.output
    assert "plan" in result.output.lower() or "would fetch" in result.output.lower()
    assert not (tmp_path / "cache").exists()


def test_refresh_rejects_pool_manifest_mismatch(manifest_file, tmp_path):
    """--pool must equal manifest.suite_id (cross-pool contamination guard)."""
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "holdout-v1",  # mismatched against suite_id "search-v1"
        "--cache-root", str(tmp_path / "cache"),
        "--dry-run",
    ])
    assert result.exit_code == 1
    assert "does not match" in result.output.lower()
    assert "suite_id" in result.output.lower()


def test_refresh_missing_fixture_id_fails(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "no-such-fixture",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1",
        "--cache-root", str(tmp_path / "cache"),
        "--dry-run",
    ])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


# -- successful refresh + archival ---------------------------------------


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_writes_cache_manifest(mock_fetch, manifest_file, fetch_payload, tmp_path):
    mock_fetch.return_value = fetch_payload(record_count=1200, cost_usd=0.5)
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1",
        "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 0, result.output
    cache_dir = cache_path_for(tmp_path / "cache", "search-v1", "mon-a", "1.0")
    assert cache_dir.exists()
    manifest = load_cache_manifest(cache_dir)
    assert manifest.fixture_id == "mon-a"
    assert manifest.fixture_version == "1.0"
    assert manifest.pool == "search-v1"
    assert len(manifest.data_sources) >= 1
    # Monitoring has 3 descriptors (mentions/sentiment/sov) → 3 fetch calls.
    assert mock_fetch.call_count == 3


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_archives_prior_cache(mock_fetch, manifest_file, fetch_payload, tmp_path):
    mock_fetch.return_value = fetch_payload(cost_usd=0.1)
    mpath = manifest_file(domain="monitoring", fixtures=_MON_FIXTURES)
    runner = CliRunner()
    first = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert first.exit_code == 0, first.output
    second = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
        "--force",
    ])
    assert second.exit_code == 0, second.output
    pool_dir = tmp_path / "cache" / "search-v1" / "mon-a"
    archived = [d for d in pool_dir.iterdir() if "archive-" in d.name]
    assert len(archived) == 1
    # Fresh v1.0 dir exists alongside archived one.
    assert (pool_dir / "v1.0").exists()


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_fresh_cache_skips_without_force(
    mock_fetch, manifest_file, fetch_payload, tmp_path,
):
    mock_fetch.return_value = fetch_payload(cost_usd=0.1)
    mpath = manifest_file(domain="monitoring", fixtures=_MON_FIXTURES)
    runner = CliRunner()
    runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    calls_first = mock_fetch.call_count
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 0
    assert "fresh" in result.output.lower()
    # No additional fetches on the re-run.
    assert mock_fetch.call_count == calls_first


# -- content-drift -------------------------------------------------------


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_emits_content_drift_event(
    mock_fetch, manifest_file, fetch_payload, tmp_path, monkeypatch,
):
    """Second refresh with a new content_sha1 emits a content_drift event."""
    events_log = tmp_path / "events.jsonl"
    monkeypatch.setattr(
        "autoresearch.events.EVENTS_LOG", events_log,
    )

    # First refresh: baseline sha1.
    mock_fetch.return_value = fetch_payload(content_sha1="sha-v1", cost_usd=0.0)
    mpath = manifest_file(domain="monitoring", fixtures=_MON_FIXTURES)
    runner = CliRunner()
    r1 = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert r1.exit_code == 0, r1.output

    # Second refresh: different sha1 → drift event.
    mock_fetch.return_value = fetch_payload(content_sha1="sha-v2", cost_usd=0.0)
    r2 = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
        "--force",
    ])
    assert r2.exit_code == 0, r2.output

    # Read events back and assert at least one content_drift record.
    lines = events_log.read_text().splitlines()
    drift_events = [json.loads(l) for l in lines if l.strip()]
    drift_events = [e for e in drift_events if e.get("kind") == "content_drift"]
    assert len(drift_events) >= 1, f"expected content_drift events, got {lines}"
    e = drift_events[0]
    assert e["fixture_id"] == "mon-a"
    assert e["old_sha1"] == "sha-v1"
    assert e["new_sha1"] == "sha-v2"


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_no_drift_event_on_first_refresh(
    mock_fetch, manifest_file, fetch_payload, tmp_path, monkeypatch,
):
    events_log = tmp_path / "events.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", events_log)

    mock_fetch.return_value = fetch_payload(content_sha1="sha-v1", cost_usd=0.0)
    mpath = manifest_file(domain="monitoring", fixtures=_MON_FIXTURES)
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 0
    # events.jsonl either absent or contains no content_drift records.
    if events_log.exists():
        for line in events_log.read_text().splitlines():
            if line.strip():
                assert json.loads(line).get("kind") != "content_drift"


def test_content_sha1_roundtrips_through_cache_manifest(tmp_path):
    """DataSourceRecord.content_sha1 survives write/load_cache_manifest."""
    from datetime import datetime, timezone

    cache_dir = tmp_path / "cache" / "search-v1" / "mon-a" / "v1.0"
    cache_dir.mkdir(parents=True)
    manifest = CacheManifest(
        fixture_id="mon-a", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc), fetched_by="t",
        data_sources=[DataSourceRecord(
            source="xpoz", data_type="mentions", arg="https://acme.com",
            retention_days=30, cached_artifact="xpoz_mentions__abc.json",
            content_sha1="abc1234567890",
        )],
    )
    write_cache_manifest(cache_dir, manifest)
    loaded = load_cache_manifest(cache_dir)
    assert loaded.data_sources[0].content_sha1 == "abc1234567890"


# -- batch modes ---------------------------------------------------------


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_all_stale_only_refreshes_stale(
    mock_fetch, manifest_file, fetch_payload, seed_cache,
):
    mock_fetch.return_value = fetch_payload(record_count=10, cost_usd=0.0)
    mpath = manifest_file(domain="monitoring", fixtures=_BATCH_FIXTURES)
    seed_cache("search-v1", "mon-fresh", age_days=5)
    seed_cache("search-v1", "mon-aging", age_days=20)
    cache_root = seed_cache("search-v1", "mon-stale", age_days=35)

    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "--all-stale", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(cache_root),
    ])
    assert result.exit_code == 0, result.output
    assert "mon-stale" in result.output
    # Monitoring: 3 descriptors × 1 stale fixture = 3 fetches.
    assert mock_fetch.call_count == 3


@patch("cli.freddy.fixture.refresh._run_source_fetch")
def test_refresh_all_aging_covers_aging_and_stale(
    mock_fetch, manifest_file, fetch_payload, seed_cache,
):
    mock_fetch.return_value = fetch_payload(record_count=5, cost_usd=0.0)
    mpath = manifest_file(domain="monitoring", fixtures=_BATCH_FIXTURES)
    seed_cache("search-v1", "mon-fresh", age_days=5)
    seed_cache("search-v1", "mon-aging", age_days=20)
    cache_root = seed_cache("search-v1", "mon-stale", age_days=35)

    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "--all-aging", "--manifest", mpath,
        "--pool", "search-v1", "--cache-root", str(cache_root),
    ])
    assert result.exit_code == 0, result.output
    # aging + stale = 2 fixtures × 3 descriptors = 6.
    assert mock_fetch.call_count == 6


def test_refresh_all_with_fixture_id_rejected(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a", "--all-stale",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 1
    assert "do not combine" in result.output.lower()


def test_refresh_all_stale_and_all_aging_mutually_exclusive(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "--all-stale", "--all-aging",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 1
    assert "mutually exclusive" in result.output.lower()


def test_refresh_without_fixture_or_batch_flag_errors(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
    ])
    assert result.exit_code == 1
    assert "required" in result.output.lower()


# -- isolation / credentials ---------------------------------------------


def test_refresh_isolation_ci_fails_when_credentials_missing(
    manifest_file, tmp_path, monkeypatch,
):
    # Point the creds path at a guaranteed-absent file inside tmp_path.
    missing = tmp_path / "does-not-exist" / ".credentials"
    monkeypatch.setattr(
        "cli.freddy.fixture.refresh.HOLDOUT_CREDENTIALS_PATH", missing,
    )
    runner = CliRunner()
    # Use a holdout manifest so --isolation=ci semantics make sense.
    mpath = manifest_file(
        suite_id="holdout-v1", domain="monitoring",
        fixtures=_MON_FIXTURES,
    )
    with patch("cli.freddy.fixture.refresh._run_source_fetch"):
        result = runner.invoke(fixture_app, [
            "refresh", "mon-a", "--manifest", mpath,
            "--pool", "holdout-v1", "--cache-root", str(tmp_path / "cache"),
            "--isolation", "ci",
        ])
    assert result.exit_code == 1
    assert "credentials" in result.output.lower()
    assert "not found" in result.output.lower()


def test_refresh_isolation_ci_fails_on_insecure_perms(
    manifest_file, tmp_path, monkeypatch,
):
    creds = tmp_path / ".credentials"
    creds.write_text("FOO=bar\n")
    os.chmod(creds, 0o644)  # group+other readable — insecure.
    monkeypatch.setattr(
        "cli.freddy.fixture.refresh.HOLDOUT_CREDENTIALS_PATH", creds,
    )
    runner = CliRunner()
    mpath = manifest_file(
        suite_id="holdout-v1", domain="monitoring", fixtures=_MON_FIXTURES,
    )
    # Prevent actually invoking any subprocess.
    with patch("cli.freddy.fixture.refresh._run_source_fetch"):
        result = runner.invoke(fixture_app, [
            "refresh", "mon-a", "--manifest", mpath,
            "--pool", "holdout-v1", "--cache-root", str(tmp_path / "cache"),
            "--isolation", "ci",
        ])
    assert result.exit_code == 1
    assert "insecure" in result.output.lower() or "chmod" in result.output.lower()


def test_refresh_rejects_invalid_isolation_value(manifest_file, tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "refresh", "mon-a",
        "--manifest", manifest_file(domain="monitoring", fixtures=_MON_FIXTURES),
        "--pool", "search-v1", "--cache-root", str(tmp_path / "cache"),
        "--isolation", "bogus", "--dry-run",
    ])
    assert result.exit_code == 1
    assert "isolation" in result.output.lower()


# -- pool policies -------------------------------------------------------


def test_pool_policies_known_pools():
    # Both pools hard_fail on miss so automatic Python live-fetch never
    # silently fills a gap — priming agent is the only fetch path.
    assert pool_on_miss("search-v1") == "hard_fail"
    assert pool_on_miss("holdout-v1") == "hard_fail"


def test_pool_policies_unknown_falls_back_to_default_fail_closed():
    # Any unregistered pool falls through to _default = hard_fail.
    assert pool_on_miss("adversarial-v1") == "hard_fail"
    assert pool_on_miss("") == "hard_fail"


# -- source resolution ---------------------------------------------------


def test_determine_sources_monitoring_has_three_descriptors():
    fixture = FixtureSpec(
        fixture_id="mon-a", client="acme", context="https://acme.com",
        version="1.0",
    )
    descriptors = _determine_sources(fixture, "monitoring")
    assert len(descriptors) == 3
    data_types = {d["data_type"] for d in descriptors}
    assert data_types == {"mentions", "sentiment", "sov"}
    # Retention resolves via _default → 30.
    assert all(d["retention_days"] == 30 for d in descriptors)


def test_determine_sources_env_retention_override():
    fixture = FixtureSpec(
        fixture_id="mon-a", client="acme", context="https://acme.com",
        version="1.0", env={"RETENTION_DAYS": "7"},
    )
    descriptors = _determine_sources(fixture, "monitoring")
    assert all(d["retention_days"] == 7 for d in descriptors)


def test_determine_sources_geo_uses_per_datatype_defaults():
    fixture = FixtureSpec(
        fixture_id="geo-a", client="acme", context="https://acme.com",
        version="1.0",
    )
    descriptors = _determine_sources(fixture, "geo")
    by_type = {d["data_type"]: d for d in descriptors}
    assert by_type["page"]["retention_days"] == 180
    assert by_type["visibility"]["retention_days"] == 90


def test_determine_sources_unknown_domain_raises():
    fixture = FixtureSpec(
        fixture_id="x", client="acme", context="ctx", version="1.0",
    )
    with pytest.raises(ValueError, match="no source descriptors"):
        _determine_sources(fixture, "not-a-domain")
