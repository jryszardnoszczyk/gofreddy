"""Fixture data cache — layout, manifest format, I/O primitives, staleness.

Authoritative conventions (referenced by SCHEMA.md and the plan):

  Cache root:  ~/.local/share/gofreddy/fixture-cache/<pool>/<fixture_id>/v<version>/
  Contents:    manifest.json + one artifact per (source, data_type, arg, shape_flags) tuple.
  Filename:    <source>_<data_type>__<arg_hash>.json
  arg_hash:    sha1("|".join([arg, *sorted(shape_flags.items())])).hexdigest()[:12]

  Shape flags are output-shape-affecting CLI flags that alter the payload a
  session receives (e.g. `freddy monitor mentions --format summary` returns an
  aggregated dict where `--format full` returns a list). Including them in the
  hash prevents a summary-shaped session from reading a full-shaped cache
  entry (silently wrong data). Hashing distinct (source, data_type, arg)
  triples lets one (source, data_type) pair hold multiple entries under one
  dir (e.g., three different URLs scraped by `freddy scrape` coexist).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Staleness = Literal["fresh", "aging", "stale"]

DEFAULT_CACHE_ROOT = Path("~/.local/share/gofreddy/fixture-cache").expanduser()
MANIFEST_FILENAME = "manifest.json"


def arg_hash(arg: str, shape_flags: dict[str, str] | None = None) -> str:
    """Stable short hash of a call's (arg + output-shape flags).

    shape_flags keys are sorted for determinism across callers. When
    shape_flags is None or empty, the hash is identical to the arg-only
    scheme — backward compatible for sources with no shape flags.
    """
    key = arg
    if shape_flags:
        key += "|" + "|".join(f"{k}={shape_flags[k]}" for k in sorted(shape_flags))
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def artifact_filename(
    source: str, data_type: str, arg: str,
    shape_flags: dict[str, str] | None = None,
) -> str:
    return f"{source}_{data_type}__{arg_hash(arg, shape_flags)}.json"


@dataclass(frozen=True)
class DataSourceRecord:
    source: str
    data_type: str
    arg: str
    retention_days: int
    cached_artifact: str
    record_count: int = 0
    cost_usd: float = 0.0
    # sha1 of the artifact body at write time — content-drift detection in
    # Phase 6 refresh. Empty string means pre-content-hash cache (treat as
    # first refresh).
    content_sha1: str = ""


@dataclass(frozen=True)
class CacheManifest:
    fixture_id: str
    fixture_version: str
    pool: str
    fetched_at: datetime
    fetched_by: str
    # data_sources is a list: one (source, data_type) may have multiple
    # entries keyed by distinct arg values.
    data_sources: list[DataSourceRecord] = field(default_factory=list)
    total_fetch_cost_usd: float = 0.0
    fetch_duration_seconds: int = 0

    def lookup(self, source: str, data_type: str, arg: str) -> DataSourceRecord | None:
        """Return the record matching (source, data_type, arg) exactly, else None."""
        for record in self.data_sources:
            if (
                record.source == source
                and record.data_type == data_type
                and record.arg == arg
            ):
                return record
        return None


def cache_path_for(root: Path, pool: str, fixture_id: str, fixture_version: str) -> Path:
    return root / pool / fixture_id / f"v{fixture_version}"


def _dt_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def write_cache_manifest(cache_dir: Path, manifest: CacheManifest) -> None:
    payload: dict[str, Any] = asdict(manifest)
    payload["fetched_at"] = _dt_to_iso(manifest.fetched_at)
    payload["data_sources"] = [asdict(src) for src in manifest.data_sources]
    (cache_dir / MANIFEST_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )


def load_cache_manifest(cache_dir: Path) -> CacheManifest:
    payload = json.loads((cache_dir / MANIFEST_FILENAME).read_text())
    sources_raw = payload.pop("data_sources")
    sources = [DataSourceRecord(**src) for src in sources_raw]
    payload["fetched_at"] = _iso_to_dt(payload["fetched_at"])
    return CacheManifest(data_sources=sources, **payload)


def staleness_status(
    manifest: CacheManifest, *, now: datetime | None = None,
) -> Staleness:
    """Return the cache's staleness tier.

    Based on the shortest retention window across data sources:
    - fresh: age < 50% of shortest retention
    - aging: 50% <= age < 100% (refresh soon before records age out)
    - stale: age >= 100%
    """
    current = now or datetime.now(timezone.utc)
    age = current - manifest.fetched_at
    if not manifest.data_sources:
        return "fresh"
    shortest = min(src.retention_days for src in manifest.data_sources)
    ratio = age.total_seconds() / (shortest * 86400)
    if ratio < 0.5:
        return "fresh"
    if ratio < 1.0:
        return "aging"
    return "stale"
