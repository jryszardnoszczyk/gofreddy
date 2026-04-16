"""Tests for shared metric computation functions extracted from commodity_baseline."""

from datetime import date

from src.monitoring.intelligence.metric_computations import (
    compute_date_gaps,
    compute_engagement_spikes,
    compute_velocity_flags,
)


class TestComputeEngagementSpikes:
    def test_empty_items(self):
        assert compute_engagement_spikes([], 100.0) == []

    def test_zero_average(self):
        items = [{"engagement": 100, "source_id": "1", "content": "test"}]
        assert compute_engagement_spikes(items, 0.0) == []

    def test_none_above_threshold(self):
        items = [
            {"engagement": 50, "source_id": "1", "content": "low engagement"},
            {"engagement": 80, "source_id": "2", "content": "medium engagement"},
        ]
        result = compute_engagement_spikes(items, 10.0)
        assert result == []

    def test_finds_outliers(self):
        items = [
            {"engagement": 5, "source_id": "1", "content": "normal"},
            {"engagement": 200, "source_id": "2", "content": "viral post"},
        ]
        result = compute_engagement_spikes(items, 10.0)
        assert len(result) == 1
        assert result[0]["source_id"] == "2"
        assert result[0]["ratio"] == 20.0

    def test_content_preview_truncated(self):
        items = [{"engagement": 200, "source_id": "1", "content": "x" * 300}]
        result = compute_engagement_spikes(items, 10.0, content_preview_len=50)
        assert len(result[0]["content"]) == 50


class TestComputeVelocityFlags:
    def test_no_consecutive_increases(self):
        volumes = {"2026-03-01": 10, "2026-03-02": 5, "2026-03-03": 8, "2026-03-04": 3}
        assert compute_velocity_flags(volumes) == []

    def test_detects_streak(self):
        volumes = {
            "2026-03-01": 1,
            "2026-03-02": 2,
            "2026-03-03": 3,
            "2026-03-04": 4,
            "2026-03-05": 5,
        }
        result = compute_velocity_flags(volumes)
        assert len(result) >= 1
        assert "2026-03-04" in result

    def test_empty_input(self):
        assert compute_velocity_flags({}) == []

    def test_single_day(self):
        assert compute_velocity_flags({"2026-03-01": 10}) == []


class TestComputeDateGaps:
    def test_finds_missing_dates(self):
        volumes = {"2026-03-01": 5, "2026-03-03": 3}
        gaps = compute_date_gaps(volumes, date(2026, 3, 1), date(2026, 3, 3))
        assert "2026-03-02" in gaps

    def test_no_gaps(self):
        volumes = {"2026-03-01": 5, "2026-03-02": 3, "2026-03-03": 7}
        gaps = compute_date_gaps(volumes, date(2026, 3, 1), date(2026, 3, 3))
        assert gaps == []

    def test_empty_volumes(self):
        gaps = compute_date_gaps({}, date(2026, 3, 1), date(2026, 3, 3))
        assert len(gaps) == 3
