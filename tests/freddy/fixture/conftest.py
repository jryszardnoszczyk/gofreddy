"""Shared fixtures for freddy fixture test modules.

Note: imports from ``cli.freddy.fixture.cache`` are deferred to fixture
function bodies (not at module level). This lets conftest collection
succeed at Phase 2 time; fixture invocation triggers import at Phase 4+
when the module actually exists.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def manifest_file(tmp_path):
    """Factory: write a minimal suite manifest and return the path (as str)."""
    def _make(suite_id="search-v1", version="1.0", domain="geo", fixtures=None):
        fixtures = fixtures or [{
            "fixture_id": f"{domain}-a", "client": "acme",
            "context": "https://acme.com", "version": "1.0",
        }]
        payload = {"suite_id": suite_id, "version": version,
                   "domains": {domain: fixtures}}
        path = tmp_path / "m.json"
        path.write_text(json.dumps(payload))
        return str(path)
    return _make


@pytest.fixture
def fetch_payload():
    """Factory: returns a _run_source_fetch return list (single-element list)."""
    def _make(**overrides):
        base = {
            "source": "xpoz", "data_type": "mentions", "arg": "https://acme.com",
            "retention_days": 30,
            "cached_artifact": "xpoz_mentions__deadbeefcafe.json",
            "record_count": 100, "cost_usd": 0.10,
        }
        base.update(overrides)
        return [base]
    return _make


@pytest.fixture
def seed_cache(tmp_path):
    """Factory: seed a cache dir with a CacheManifest. Returns the cache root."""
    def _make(pool, fixture_id, version="1.0", source="xpoz",
              data_type="mentions", arg="https://acme.com", age_days=0.0):
        from cli.freddy.fixture.cache import (  # deferred: created in Phase 4
            CacheManifest, DataSourceRecord, cache_path_for, write_cache_manifest,
        )
        cache_root = tmp_path / "cache"
        cache_dir = cache_path_for(cache_root, pool, fixture_id, version)
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{source}_{data_type}__deadbeefcafe.json").write_text("{}")
        fetched_at = datetime.now(timezone.utc) - timedelta(days=age_days)
        write_cache_manifest(cache_dir, CacheManifest(
            fixture_id=fixture_id, fixture_version=version, pool=pool,
            fetched_at=fetched_at, fetched_by="seed",
            data_sources=[DataSourceRecord(
                source=source, data_type=data_type, arg=arg,
                retention_days=30,
                cached_artifact=f"{source}_{data_type}__deadbeefcafe.json",
                record_count=100, cost_usd=0.10,
            )],
        ))
        return cache_root
    return _make
