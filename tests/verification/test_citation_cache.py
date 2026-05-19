"""CitationCache — JSON-backed verified-claim+URL store (AE-3 / TD-44)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.verification.citation_cache import CitationCache


def test_get_returns_none_for_missing_key(tmp_path: Path) -> None:
    cache = CitationCache(path=tmp_path / "cache.json")
    assert cache.get("claim", "https://example.com") is None


def test_set_then_get_roundtrips(tmp_path: Path) -> None:
    cache = CitationCache(path=tmp_path / "cache.json")
    cache.set(
        "claim text",
        "https://example.com",
        {"verified": True, "confidence": 0.9, "rationale": "matches"},
    )
    got = cache.get("claim text", "https://example.com")
    assert got is not None
    assert got["verified"] is True
    assert got["confidence"] == 0.9
    assert got["rationale"] == "matches"


def test_set_overwrites_prior_entry(tmp_path: Path) -> None:
    cache = CitationCache(path=tmp_path / "cache.json")
    cache.set("c", "u", {"verified": False, "confidence": 0.2, "rationale": "no"})
    cache.set("c", "u", {"verified": True, "confidence": 0.9, "rationale": "yes"})
    got = cache.get("c", "u")
    assert got["verified"] is True
    assert got["rationale"] == "yes"


def test_different_claims_same_url_yield_different_entries(tmp_path: Path) -> None:
    cache = CitationCache(path=tmp_path / "cache.json")
    cache.set("c1", "u", {"verified": True, "confidence": 0.9, "rationale": "r1"})
    cache.set("c2", "u", {"verified": False, "confidence": 0.1, "rationale": "r2"})
    assert cache.get("c1", "u")["rationale"] == "r1"
    assert cache.get("c2", "u")["rationale"] == "r2"


def test_clear_wipes_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    cache = CitationCache(path=cache_path)
    cache.set("c", "u", {"verified": True, "confidence": 0.9, "rationale": "ok"})
    assert cache.get("c", "u") is not None
    cache.clear()
    assert cache.get("c", "u") is None
    assert not cache_path.exists()


def test_persists_across_instances(tmp_path: Path) -> None:
    """A second CitationCache instance pointing at the same file
    reads prior-instance writes — the JSON file IS the store."""
    cache_path = tmp_path / "cache.json"
    CitationCache(path=cache_path).set(
        "c", "u", {"verified": True, "confidence": 0.9, "rationale": "yes"},
    )
    second = CitationCache(path=cache_path)
    assert second.get("c", "u")["verified"] is True


def test_corrupted_cache_file_starts_fresh(tmp_path: Path) -> None:
    """A malformed cache file should not crash the lane — log + start
    fresh. The cache is a cost-saving optimisation, not authoritative."""
    cache_path = tmp_path / "cache.json"
    cache_path.write_text("{not valid json")
    cache = CitationCache(path=cache_path)
    assert cache.get("c", "u") is None  # treated as empty
    cache.set("c", "u", {"verified": True, "confidence": 0.9, "rationale": "ok"})
    assert cache.get("c", "u") is not None


def test_cache_file_is_human_readable_json(tmp_path: Path) -> None:
    """Operators may inspect the cache file during ops; ensure it's
    pretty-printed deterministic JSON, not minified."""
    cache_path = tmp_path / "cache.json"
    cache = CitationCache(path=cache_path)
    cache.set("c", "u", {"verified": True, "confidence": 0.9, "rationale": "ok"})
    text = cache_path.read_text(encoding="utf-8")
    # Pretty-printed (multi-line, indented)
    assert "\n" in text
    assert "  " in text
    # Top-level structure parses
    parsed = json.loads(text)
    assert isinstance(parsed, dict)
    assert len(parsed) == 1


def test_set_creates_parent_dir(tmp_path: Path) -> None:
    """The default path is `cache/citation_verifications.json` at
    repo root — set() must create the `cache/` parent dir."""
    cache_path = tmp_path / "newdir" / "subdir" / "cache.json"
    cache = CitationCache(path=cache_path)
    cache.set("c", "u", {"verified": True, "confidence": 0.9, "rationale": "ok"})
    assert cache_path.is_file()
