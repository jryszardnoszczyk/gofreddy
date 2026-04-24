"""Plan B acceptance criterion: quality-judge material filter on content_drift.

``_maybe_emit_drift`` previously logged ``kind="content_drift"`` on every
sha1 change. Plan B spec: POST old+new content to the quality-judge with
role="content_drift"; emit only on verdict="material". Cosmetic changes
stay silent. Judge unreachable → emit conservatively (fallback).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autoresearch.judges.quality_judge import QualityVerdict


@pytest.fixture
def events_log(tmp_path, monkeypatch):
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", p)
    return p


def _setup_prior(tmp_path):
    """Create an archived prior artifact + a matching manifest so
    _maybe_emit_drift sees drift and can read the old content."""
    from cli.freddy.fixture.cache import CacheManifest, DataSourceRecord
    from datetime import datetime, timezone

    archived = tmp_path / "cache.archive-20260101T000000Z"
    archived.mkdir()
    artifact_name = "xpoz__mentions__abc.json"
    (archived / artifact_name).write_text('{"old": "content"}')

    manifest = CacheManifest(
        fixture_id="fx",
        fixture_version="1.0",
        pool="search-v1",
        fetched_at=datetime.now(timezone.utc),
        fetched_by="tester",
        data_sources=[
            DataSourceRecord(
                source="xpoz", data_type="mentions", arg="abc",
                retention_days=30, cached_artifact=artifact_name,
                record_count=1, cost_usd=0.0,
                content_sha1="sha1_OLD",
            ),
        ],
        total_fetch_cost_usd=0.0,
        fetch_duration_seconds=0,
    )
    src = {"source": "xpoz", "data_type": "mentions"}
    return archived, manifest, src


def test_material_verdict_emits_event_and_stderr(events_log, tmp_path, capsys):
    from cli.freddy.fixture.refresh import _maybe_emit_drift
    from autoresearch.events import read_events

    archived, manifest, src = _setup_prior(tmp_path)

    with patch(
        "cli.freddy.fixture.refresh.call_quality_judge",
        return_value=QualityVerdict(
            verdict="material", reasoning="numeric fields shifted by >5%",
            confidence=0.9, recommended_action=None,
        ),
        create=True,  # referenced via _classify_content_drift's local import
    ):
        # Simulate: call the inner classifier directly with mocked verdict.
        with patch(
            "cli.freddy.fixture.refresh._classify_content_drift",
            return_value=("material", "numeric fields shifted by >5%"),
        ):
            _maybe_emit_drift(
                "fx", src, "abc", "sha1_NEW", manifest,
                new_content='{"new": "content"}',
                archived_dir=archived,
            )
    records = list(read_events(kind="content_drift", path=events_log))
    assert len(records) == 1
    assert records[0]["verdict"] == "material"
    err = capsys.readouterr().err
    assert "content_drift (material)" in err


def test_cosmetic_verdict_is_silent(events_log, tmp_path, capsys):
    from cli.freddy.fixture.refresh import _maybe_emit_drift
    from autoresearch.events import read_events

    archived, manifest, src = _setup_prior(tmp_path)

    with patch(
        "cli.freddy.fixture.refresh._classify_content_drift",
        return_value=("cosmetic", "whitespace + ordering only"),
    ):
        _maybe_emit_drift(
            "fx", src, "abc", "sha1_NEW", manifest,
            new_content='{"new": "content"}',
            archived_dir=archived,
        )
    records = list(read_events(kind="content_drift", path=events_log))
    assert len(records) == 0
    assert capsys.readouterr().err == ""


def test_unknown_verdict_emits_conservatively(events_log, tmp_path, capsys):
    """Judge unreachable / import failed → fall back to emitting."""
    from cli.freddy.fixture.refresh import _maybe_emit_drift
    from autoresearch.events import read_events

    archived, manifest, src = _setup_prior(tmp_path)

    with patch(
        "cli.freddy.fixture.refresh._classify_content_drift",
        return_value=("unknown", "judge unreachable"),
    ):
        _maybe_emit_drift(
            "fx", src, "abc", "sha1_NEW", manifest,
            new_content='{"new": "content"}',
            archived_dir=archived,
        )
    records = list(read_events(kind="content_drift", path=events_log))
    assert len(records) == 1
    assert records[0]["verdict"] == "unknown"
    err = capsys.readouterr().err
    assert "content_drift (unknown)" in err


def test_no_drift_when_sha1_matches(events_log, tmp_path):
    """sha1 unchanged → early return, no judge call."""
    from cli.freddy.fixture.refresh import _maybe_emit_drift
    from autoresearch.events import read_events

    archived, manifest, src = _setup_prior(tmp_path)
    with patch(
        "cli.freddy.fixture.refresh._classify_content_drift",
    ) as mock_classify:
        _maybe_emit_drift(
            "fx", src, "abc", "sha1_OLD", manifest,  # same sha1 as prior
            new_content='{"old": "content"}',
            archived_dir=archived,
        )
    mock_classify.assert_not_called()
    assert list(read_events(kind="content_drift", path=events_log)) == []


def test_missing_archived_dir_falls_back_to_unknown(events_log, tmp_path, capsys):
    """When archived_dir is None or missing, old content can't be loaded →
    the classifier gets called with old_content=None → returns 'unknown' →
    event emitted conservatively."""
    from cli.freddy.fixture.refresh import _maybe_emit_drift
    from autoresearch.events import read_events

    _, manifest, src = _setup_prior(tmp_path)

    # archived_dir=None path
    _maybe_emit_drift(
        "fx", src, "abc", "sha1_NEW", manifest,
        new_content='{"new": "content"}',
        archived_dir=None,  # simulate lost archive
    )
    records = list(read_events(kind="content_drift", path=events_log))
    assert len(records) == 1
    assert records[0]["verdict"] == "unknown"
