from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app
from cli.freddy.fixture.cache import (
    CacheManifest,
    DataSourceRecord,
    staleness_status,
)


def _manifest(days_ago: int, retention_days: int = 30) -> CacheManifest:
    return CacheManifest(
        fixture_id="x", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        fetched_by="t",
        data_sources=[DataSourceRecord(
            source="xpoz", data_type="mentions", arg="abc",
            retention_days=retention_days,
            cached_artifact="xpoz_mentions__deadbeef0001.json",
        )],
    )


@pytest.mark.parametrize("age_days,expected", [
    (0, "fresh"), (10, "fresh"), (14, "fresh"),
    (15, "aging"), (25, "aging"),
    (30, "stale"), (45, "stale"),
])
def test_staleness_tiers_for_30d_retention(age_days, expected):
    assert staleness_status(_manifest(age_days, 30)) == expected


def test_staleness_uses_shortest_retention():
    manifest = CacheManifest(
        fixture_id="x", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc) - timedelta(days=20),
        fetched_by="t",
        data_sources=[
            DataSourceRecord(
                "freddy-scrape", "page", "https://x.com", 180,
                "freddy-scrape_page__aaaa00000001.json",
            ),
            DataSourceRecord(
                "xpoz", "mentions", "mon-uuid", 30,
                "xpoz_mentions__bbbb00000001.json",
            ),
        ],
    )
    assert staleness_status(manifest) == "aging"


def test_staleness_empty_sources_is_fresh():
    manifest = CacheManifest(
        fixture_id="x", fixture_version="1.0", pool="search-v1",
        fetched_at=datetime.now(timezone.utc) - timedelta(days=100),
        fetched_by="t",
        data_sources=[],
    )
    assert staleness_status(manifest) == "fresh"


def test_staleness_cli_lists_fixtures(seed_cache):
    seed_cache("search-v1", "mon-a", age_days=5)
    root = seed_cache("search-v1", "mon-b", age_days=35)
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["staleness", "--cache-root", str(root)])
    assert result.exit_code == 0, result.output
    assert "mon-a" in result.output and "fresh" in result.output
    assert "mon-b" in result.output and "stale" in result.output


def test_staleness_cli_stale_only_filter(seed_cache):
    seed_cache("search-v1", "mon-a", age_days=5)
    root = seed_cache("search-v1", "mon-b", age_days=35)
    runner = CliRunner()
    result = runner.invoke(
        fixture_app, ["staleness", "--cache-root", str(root), "--stale-only"]
    )
    assert result.exit_code == 0
    assert "mon-a" not in result.output
    assert "mon-b" in result.output


def test_staleness_cli_pool_filter(seed_cache):
    seed_cache("search-v1", "mon-a", age_days=5)
    root = seed_cache("holdout-v1", "mon-b", age_days=35)
    runner = CliRunner()
    result = runner.invoke(
        fixture_app, ["staleness", "--cache-root", str(root), "--pool", "holdout-v1"]
    )
    assert result.exit_code == 0
    assert "mon-b" in result.output
    assert "mon-a" not in result.output
