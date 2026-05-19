"""Signal merger — dedupe + source confidence weighting (TD-42, U15).

Per Decision 1 research in U15 plan:
- Dedupe key: `ad_id` where present (Meta Ad Library has stable IDs);
  otherwise `sha256(advertiser_id + normalize(creative_text) + format)`.
- Source confidence weights from weights.yaml.
- Cross-validation bonus: ads observed in ≥2 sources get × 1.3.
- Freshness floor: discard ads with `last_seen_active > 90d` ago.
- Top-N cutoff after rank.

All logic is deterministic (Rule 5 — code, not LLM). The single LLM
call is the final brief-synthesis step in aggregator.py, which uses
this module's output as input.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from src.ads.signal_aggregator.providers import AdSignal

logger = logging.getLogger(__name__)


_WEIGHTS_PATH = Path(__file__).resolve().parent / "weights.yaml"


def _load_weights() -> dict:
    """Load weights.yaml; cached at call-time so meta-agent edits
    propagate without process restart."""
    return yaml.safe_load(_WEIGHTS_PATH.read_text(encoding="utf-8"))


def _normalize_text(text: str) -> str:
    """Lowercase + collapse whitespace + strip — for dedupe hashing."""
    return " ".join(text.lower().split())


def _dedupe_key(signal: AdSignal) -> str:
    """Stable cross-provider key. Prefer `ad_id` (Meta Ad Library has
    stable IDs); fall back to hash of (advertiser_id + normalized
    creative_text + format)."""
    if signal.ad_id:
        return f"ad_id:{signal.ad_id}"
    payload = (
        f"{signal.advertiser_id}|"
        f"{_normalize_text(signal.creative_text)}|"
        f"{signal.format}"
    )
    return f"hash:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def merge_ad_signals(
    signals: list[AdSignal],
    *,
    weights: dict | None = None,
    now: datetime | None = None,
) -> list[tuple[AdSignal, float]]:
    """Dedupe across providers, apply source confidence weights +
    cross-validation bonus + freshness floor, return ranked list of
    `(merged_signal, confidence_score)` tuples sorted descending.

    Args:
        signals: raw signals from all providers (may contain
            duplicates across sources).
        weights: optional override of weights.yaml (for tests).
        now: optional reference time for freshness floor (default
            UTC now).

    Returns:
        list of (signal, score) where each `signal.sources` carries
        the union of providers that observed it, and `score` is the
        confidence score after weight + cross-validation + freshness
        gating. Sorted descending by score. Truncated to top_n.
    """
    if weights is None:
        weights = _load_weights()
    if now is None:
        now = datetime.now(timezone.utc)

    source_weights = weights.get("source_weights", {})
    cross_val_bonus = float(weights.get("cross_validation_bonus", 1.30))
    freshness_days = int(weights.get("freshness_floor_days", 90))
    top_n = int(weights.get("top_n", 8))

    floor = now - timedelta(days=freshness_days)

    # Bucket by dedupe key, merging source lists + keeping the most-
    # recent record (in case providers disagree on body text — Meta
    # Ad Library is authoritative).
    buckets: dict[str, AdSignal] = {}
    for sig in signals:
        # Coerce naive datetimes to UTC for comparison safety.
        last_seen = sig.last_seen_active
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        if last_seen < floor:
            continue  # freshness floor

        key = _dedupe_key(sig)
        if key not in buckets:
            buckets[key] = sig
        else:
            # Merge: union sources; prefer Meta Ad Library's body text.
            prior = buckets[key]
            merged_sources = list(dict.fromkeys(prior.sources + sig.sources))
            # If Meta Ad Library is in the union and this entry is from
            # MAL, use its body; otherwise keep the prior.
            authoritative = sig if "meta_ad_library" in sig.sources else prior
            buckets[key] = replace(
                authoritative,
                sources=merged_sources,
                # Keep the later last_seen_active to reflect cross-source
                # most-recent observation.
                last_seen_active=max(
                    prior.last_seen_active.replace(tzinfo=timezone.utc)
                    if prior.last_seen_active.tzinfo is None
                    else prior.last_seen_active,
                    last_seen,
                ),
            )

    # Score each merged signal.
    scored: list[tuple[AdSignal, float]] = []
    for sig in buckets.values():
        # Use the highest-weighted source on this signal.
        max_weight = max(
            (float(source_weights.get(s, 0.0)) for s in sig.sources),
            default=0.0,
        )
        # Cross-validation: ≥2 sources → multiplicative bonus.
        if len(sig.sources) >= 2:
            max_weight *= cross_val_bonus
        # Days-running boost (longevity proxy).
        longevity_factor = 1.0 + min(sig.days_running / 90.0, 1.0)
        score = max_weight * longevity_factor
        scored.append((sig, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_n]


__all__ = ["merge_ad_signals"]
