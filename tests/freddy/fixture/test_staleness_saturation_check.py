"""Plan B acceptance criterion: ``freddy fixture staleness`` can batch
per-fixture saturation_cycle events to the system_health.saturation agent
and tag fixtures the agent returns as rotate_now.

The feature is opt-in via ``--with-saturation-check`` so the default
staleness output stays fast and local (no judge dependency).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from autoresearch.judges.quality_judge import QualityVerdict
from cli.freddy.commands.fixture import app as fixture_app


@pytest.fixture
def events_log(tmp_path, monkeypatch):
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", p)
    return p


def _seed_cache(tmp_path, pool, fixture_id) -> Path:
    """Create a minimal fresh cache manifest so the staleness walker finds it."""
    from datetime import datetime, timezone
    from cli.freddy.fixture.cache import (
        CacheManifest, DataSourceRecord, cache_path_for, write_cache_manifest,
    )
    cache_root = tmp_path / "cache"
    cache_dir = cache_path_for(cache_root, pool, fixture_id, "1.0")
    cache_dir.mkdir(parents=True)
    manifest = CacheManifest(
        fixture_id=fixture_id, fixture_version="1.0", pool=pool,
        fetched_at=datetime.now(timezone.utc), fetched_by="t",
        data_sources=[
            DataSourceRecord(
                source="s", data_type="d", arg="a",
                retention_days=365, cached_artifact="x.json",
                record_count=1, cost_usd=0.0, content_sha1="h",
            ),
        ],
        total_fetch_cost_usd=0.0, fetch_duration_seconds=0,
    )
    write_cache_manifest(cache_dir, manifest)
    return cache_root


def _seed_saturation_events(events_log_path, fixture_id, count):
    from autoresearch.events import log_event
    for i in range(count):
        log_event(
            kind="saturation_cycle", fixture_id=fixture_id,
            lane="geo", candidate_score=0.6 + i * 0.01,
            baseline_score=0.55, baseline_beat=True,
            candidate_id=f"v00{i + 1}", baseline_id=f"v00{i}",
        )


def test_staleness_without_flag_does_not_invoke_judge(events_log, tmp_path):
    cache_root = _seed_cache(tmp_path, "search-v1", "geo-a")
    runner = CliRunner()
    with patch("cli.freddy.commands.fixture._query_saturation_agent_per_fixture") as mock_q:
        result = runner.invoke(fixture_app, [
            "staleness", "--cache-root", str(cache_root),
        ])
    assert result.exit_code == 0
    assert "Rotate" not in result.output
    mock_q.assert_not_called()


def test_staleness_with_flag_tags_rotate_now_from_agent(events_log, tmp_path):
    cache_root = _seed_cache(tmp_path, "search-v1", "geo-a")
    _seed_saturation_events(events_log, "geo-a", 3)

    runner = CliRunner()
    with patch(
        "cli.freddy.commands.fixture.call_quality_judge",
        return_value=QualityVerdict(
            verdict="rotate_now", reasoning="saturated",
            confidence=0.85, recommended_action=None,
        ),
        create=True,
    ):
        # Patch the deferred import inside _query_saturation_agent_per_fixture
        with patch(
            "autoresearch.judges.quality_judge.call_quality_judge",
            return_value=QualityVerdict(
                verdict="rotate_now", reasoning="saturated",
                confidence=0.85, recommended_action=None,
            ),
        ):
            result = runner.invoke(fixture_app, [
                "staleness", "--cache-root", str(cache_root),
                "--with-saturation-check",
            ])
    assert result.exit_code == 0, result.output
    assert "Rotate" in result.output
    assert "rotate_now" in result.output


def test_staleness_with_flag_no_cycle_events_tags_no_data(events_log, tmp_path):
    """Fixture with zero saturation_cycle events → tag=no_data, no agent call."""
    cache_root = _seed_cache(tmp_path, "search-v1", "geo-a")
    # No seed_saturation_events call → no events for geo-a

    runner = CliRunner()
    with patch(
        "autoresearch.judges.quality_judge.call_quality_judge",
    ) as mock_judge:
        result = runner.invoke(fixture_app, [
            "staleness", "--cache-root", str(cache_root),
            "--with-saturation-check",
        ])
    assert result.exit_code == 0
    assert "no_data" in result.output
    mock_judge.assert_not_called()


def test_staleness_with_flag_judge_error_tags_error(events_log, tmp_path):
    """Judge raises → tag=error for that fixture, does not abort whole command."""
    cache_root = _seed_cache(tmp_path, "search-v1", "geo-a")
    _seed_saturation_events(events_log, "geo-a", 3)

    runner = CliRunner()
    with patch(
        "autoresearch.judges.quality_judge.call_quality_judge",
        side_effect=RuntimeError("judge down"),
    ):
        result = runner.invoke(fixture_app, [
            "staleness", "--cache-root", str(cache_root),
            "--with-saturation-check",
        ])
    assert result.exit_code == 0
    assert "error" in result.output
