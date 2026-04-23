from datetime import datetime, timezone

from cli.freddy.fixture.cache import (
    CacheManifest,
    DataSourceRecord,
    arg_hash,
    artifact_filename,
    cache_path_for,
    load_cache_manifest,
    write_cache_manifest,
)


def test_cache_path_conventions(tmp_path):
    path = cache_path_for(tmp_path / "cache", "holdout-v1", "monitoring-shopify", "1.0")
    assert path == tmp_path / "cache" / "holdout-v1" / "monitoring-shopify" / "v1.0"


def test_arg_hash_stable_across_calls():
    assert arg_hash("https://acme.com") == arg_hash("https://acme.com")


def test_arg_hash_differs_across_args():
    assert arg_hash("https://a.com") != arg_hash("https://b.com")


def test_arg_hash_incorporates_shape_flags():
    plain = arg_hash("https://acme.com")
    flagged = arg_hash("https://acme.com", {"format": "summary"})
    assert plain != flagged


def test_arg_hash_order_independent_shape_flags():
    a = arg_hash("x", {"format": "summary", "lane": "p"})
    b = arg_hash("x", {"lane": "p", "format": "summary"})
    assert a == b


def test_artifact_filename_composition():
    name = artifact_filename("xpoz", "mentions", "mon-uuid-123")
    assert name.startswith("xpoz_mentions__")
    assert name.endswith(".json")
    assert len(name) == len("xpoz_mentions__") + 12 + len(".json")


def test_cache_manifest_roundtrip(tmp_path):
    path = cache_path_for(tmp_path / "cache", "search-v1", "monitoring-shopify", "1.0")
    path.mkdir(parents=True)
    manifest = CacheManifest(
        fixture_id="monitoring-shopify",
        fixture_version="1.0",
        pool="search-v1",
        fetched_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
        fetched_by="tester",
        data_sources=[
            DataSourceRecord(
                source="xpoz", data_type="mentions", arg="mon-uuid-123",
                retention_days=30,
                cached_artifact="xpoz_mentions__a1b2c3d4e5f6.json",
                record_count=1200, cost_usd=0.50,
            ),
        ],
        total_fetch_cost_usd=0.50,
        fetch_duration_seconds=45,
    )
    write_cache_manifest(path, manifest)
    loaded = load_cache_manifest(path)
    assert loaded == manifest


def test_cache_manifest_lookup_matches_tuple():
    manifest = CacheManifest(
        fixture_id="f", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc),
        fetched_by="t",
        data_sources=[
            DataSourceRecord(source="xpoz", data_type="mentions", arg="a1",
                             retention_days=30, cached_artifact="f1.json"),
            DataSourceRecord(source="xpoz", data_type="mentions", arg="a2",
                             retention_days=30, cached_artifact="f2.json"),
        ],
    )
    hit = manifest.lookup("xpoz", "mentions", "a2")
    assert hit is not None and hit.cached_artifact == "f2.json"
    assert manifest.lookup("xpoz", "mentions", "nope") is None


def test_cache_manifest_lookup_respects_source_and_data_type():
    manifest = CacheManifest(
        fixture_id="f", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc),
        fetched_by="t",
        data_sources=[
            DataSourceRecord(source="xpoz", data_type="mentions", arg="a",
                             retention_days=30, cached_artifact="x.json"),
            DataSourceRecord(source="scrape", data_type="page", arg="a",
                             retention_days=30, cached_artifact="s.json"),
        ],
    )
    assert manifest.lookup("xpoz", "mentions", "a").cached_artifact == "x.json"
    assert manifest.lookup("scrape", "page", "a").cached_artifact == "s.json"
    assert manifest.lookup("xpoz", "page", "a") is None
