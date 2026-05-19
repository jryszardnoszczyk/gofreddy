"""U15 — signal_merger dedupe + source confidence weighting (TD-42)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.ads.signal_aggregator.merger import merge_ad_signals
from src.ads.signal_aggregator.providers import AdSignal


def _signal(
    *, source: str, advertiser_id: str = "advA", creative: str = "Tired of broken workflows? Meet the future.",
    format: str = "meta_image", days_running: int = 30, ad_id: str | None = None,
    last_seen: datetime | None = None,
) -> AdSignal:
    return AdSignal(
        ad_id=ad_id,
        advertiser_id=advertiser_id,
        creative_text=creative,
        format=format,
        last_seen_active=last_seen or datetime.now(timezone.utc),
        days_running=days_running,
        sources=[source],
    )


def test_empty_signals_returns_empty() -> None:
    assert merge_ad_signals([]) == []


def test_single_signal_passes_through() -> None:
    sigs = [_signal(source="foreplay")]
    merged = merge_ad_signals(sigs)
    assert len(merged) == 1


def test_dedupe_by_ad_id_when_present() -> None:
    """Same ad_id across providers → one merged entry; sources union."""
    sigs = [
        _signal(source="foreplay", ad_id="ad_123"),
        _signal(source="adyntel", ad_id="ad_123"),
    ]
    merged = merge_ad_signals(sigs)
    assert len(merged) == 1
    assert set(merged[0][0].sources) == {"foreplay", "adyntel"}


def test_dedupe_by_content_hash_when_no_ad_id() -> None:
    """Same normalized creative text + advertiser + format → merged."""
    sigs = [
        _signal(source="foreplay", creative="Hello World"),
        _signal(source="adyntel", creative="hello   world"),  # whitespace/case differs
    ]
    merged = merge_ad_signals(sigs)
    assert len(merged) == 1


def test_cross_validation_bonus_applies() -> None:
    """Ads in ≥2 sources get × 1.3 confidence."""
    sigs_two = [
        _signal(source="foreplay", ad_id="x"),
        _signal(source="adyntel", ad_id="x"),
    ]
    sigs_one = [_signal(source="foreplay", ad_id="y", advertiser_id="advB")]
    merged_two = merge_ad_signals(sigs_two)
    merged_one = merge_ad_signals(sigs_one)
    assert merged_two[0][1] > merged_one[0][1]


def test_meta_ad_library_outweighs_foreplay() -> None:
    """Meta Ad Library (weight 1.00) ranks higher than Foreplay (0.75)
    for a single-source signal."""
    sigs = [
        _signal(source="meta_ad_library", ad_id="x"),
        _signal(source="foreplay", ad_id="y", advertiser_id="advB"),
    ]
    merged = merge_ad_signals(sigs)
    assert merged[0][0].sources == ["meta_ad_library"]


def test_freshness_floor_discards_old_ads() -> None:
    """Ads with last_seen_active > 90 days → discarded."""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=120)
    fresh = now - timedelta(days=30)
    sigs = [
        _signal(source="foreplay", ad_id="old", last_seen=old),
        _signal(source="foreplay", ad_id="fresh", last_seen=fresh),
    ]
    merged = merge_ad_signals(sigs)
    assert len(merged) == 1
    assert merged[0][0].ad_id == "fresh"


def test_top_n_truncation() -> None:
    """Default top_n=8; extra signals discarded after rank."""
    sigs = [
        _signal(source="foreplay", ad_id=f"ad_{i}", advertiser_id=f"adv_{i}")
        for i in range(15)
    ]
    merged = merge_ad_signals(sigs)
    assert len(merged) <= 8


def test_longevity_factor_boosts_long_running_ads() -> None:
    sigs = [
        _signal(source="foreplay", ad_id="long_runner", days_running=90),
        _signal(source="foreplay", ad_id="new", advertiser_id="advB", days_running=1),
    ]
    merged = merge_ad_signals(sigs)
    # Long-runner should rank higher.
    assert merged[0][0].ad_id == "long_runner"


def test_weights_override_for_tests() -> None:
    """Tests can inject custom weights to verify scoring logic."""
    sigs = [_signal(source="foreplay")]
    custom = {
        "source_weights": {"foreplay": 5.0},
        "cross_validation_bonus": 1.0,
        "freshness_floor_days": 90,
        "top_n": 8,
    }
    merged = merge_ad_signals(sigs, weights=custom)
    # Score should reflect the inflated foreplay weight.
    assert merged[0][1] > 5.0  # weight 5.0 × longevity_factor
