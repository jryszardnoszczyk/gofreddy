"""Hash-dedup cache layer for audit tool calls.

Master plan §4.5 contract:

    def cache_or_call(tool_name, args, fn, ttl_hours=24) -> Any: ...

Cache key = ``sha256(json.dumps(args, sort_keys=True))[:12]``.
Cache file = ``<cache_dir>/<tool_name>_<key>.json``.
Default ``cache_dir`` = ``clients/<slug>/audit/cache/`` resolved from the
calling audit's state; callers may pass an explicit ``cache_dir`` override
(used in tests + non-default workflow integrations).

Hit semantics
-------------
- File exists AND its ``cached_at_iso`` timestamp is within ``ttl_hours``:
  read JSON, return ``payload["result"]``. NO ``fn`` invocation, NO cost
  recording side effects.
- File exists but TTL expired: treat as miss + overwrite the file.
- File missing or corrupt: treat as miss.

Miss semantics
--------------
- Call ``fn(**args)`` (or ``await fn(**args)`` if coroutine). Side effects
  inside ``fn`` (cost-ledger writes, network) fire on this path only.
- On success, atomically write the result + metadata to the cache file.
- Re-raise on failure — the cache stores successful payloads only.

F6 self-review (master plan): providers are singletons. Cost-recording side
effects MUST live INSIDE the provider method (i.e. inside ``fn``), AFTER the
real call completes. The cache layer is intentionally side-effect-free on
hits so retries / replays don't double-bill.
"""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping

logger = logging.getLogger(__name__)

DEFAULT_TTL_HOURS = 24
HASH_PREFIX_LEN = 12


@dataclass(frozen=True)
class CacheStats:
    """Per-process counters for hits / misses / writes (used by tests)."""

    hits: int = 0
    misses: int = 0
    writes: int = 0
    expired: int = 0
    corrupt: int = 0


_stats_counters: dict[str, int] = {
    "hits": 0,
    "misses": 0,
    "writes": 0,
    "expired": 0,
    "corrupt": 0,
}


def get_stats() -> CacheStats:
    """Snapshot current per-process counters."""
    return CacheStats(**_stats_counters)


def reset_stats() -> None:
    for k in _stats_counters:
        _stats_counters[k] = 0


def _hash_args(args: Mapping[str, Any]) -> str:
    """Deterministic 12-char prefix of sha256 over canonical-JSON args.

    ``sort_keys=True`` + ``default=str`` keeps the hash stable across
    dict-ordering changes and across Path/datetime/etc. fallbacks. Callers
    that pass non-JSON-serializable objects get a stringified form rather
    than an exception.
    """
    canonical = json.dumps(dict(args), sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:HASH_PREFIX_LEN]


def cache_path(cache_dir: Path, tool_name: str, args: Mapping[str, Any]) -> Path:
    """Resolve the on-disk cache file path for ``(tool_name, args)``."""
    return Path(cache_dir) / f"{tool_name}_{_hash_args(args)}.json"


def _is_expired(cached_at_iso: str, ttl_hours: int) -> bool:
    if ttl_hours <= 0:
        return False  # ttl=0 → never expire (test convenience)
    try:
        cached_at = datetime.fromisoformat(cached_at_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return True
    if cached_at.tzinfo is None:
        cached_at = cached_at.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
    return age_seconds > ttl_hours * 3600


def read_cache(
    cache_dir: Path | str,
    tool_name: str,
    args: Mapping[str, Any],
    *,
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> Any | None:
    """Return cached result if present + fresh, else ``None``.

    Pure read — does NOT mutate counters by design (used by agent-side
    filesystem readers that don't share the Python-side counter namespace).
    Use ``cache_or_call`` for the counted path.
    """
    path = cache_path(Path(cache_dir), tool_name, args)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if _is_expired(payload.get("cached_at", ""), ttl_hours):
        return None
    return payload.get("result")


def write_cache(
    cache_dir: Path | str,
    tool_name: str,
    args: Mapping[str, Any],
    result: Any,
) -> Path:
    """Atomic write of ``result`` keyed by ``(tool_name, args)``.

    Uses tempfile + ``os.replace`` for crash-safety: a partial write never
    leaves a malformed cache file readable. Returns the resolved cache path.
    """
    path = cache_path(Path(cache_dir), tool_name, args)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool_name": tool_name,
        "args": dict(args),
        "result": _to_jsonable(result),
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }
    # tempfile in same dir guarantees the rename is atomic on POSIX.
    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, default=_json_default)
        os.replace(tmp_path, path)
    except Exception:
        # Best-effort cleanup of the tempfile if rename never happened.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    _stats_counters["writes"] += 1
    return path


def cache_or_call(
    tool_name: str,
    args: Mapping[str, Any],
    fn: Callable[..., Any] | Callable[..., Awaitable[Any]],
    *,
    ttl_hours: int = DEFAULT_TTL_HOURS,
    cache_dir: Path | str | None = None,
) -> Any | Awaitable[Any]:
    """Hash-dedup wrapper.

    Sync usage::

        result = cache_or_call("dataforseo.technical_audit", {"url": url},
                               dataforseo.technical_audit, cache_dir=cache_dir)

    Async usage (auto-detected when ``fn`` is a coroutine function)::

        result = await cache_or_call("cloro.ai_visibility", {"q": q},
                                     cloro.ai_visibility, cache_dir=cache_dir)

    On a hit, ``fn`` is NOT called — guarantees cost-recording side effects
    inside the provider method don't fire on cache reuse.

    ``cache_dir`` resolution
    ------------------------
    Required. Callers pass the audit-scoped path (typically
    ``clients/<slug>/audit/cache/``). Stage 1a fan-out resolves this from
    ``state.client_slug``; tests pass a tmp_path. Default-None raises so
    accidentally-unscoped writes never land in CWD.
    """
    if cache_dir is None:
        raise ValueError(
            "cache_or_call: cache_dir is required (typically clients/<slug>/audit/cache/)"
        )

    if inspect.iscoroutinefunction(fn):
        return _cache_or_call_async(tool_name, args, fn, ttl_hours, Path(cache_dir))
    return _cache_or_call_sync(tool_name, args, fn, ttl_hours, Path(cache_dir))


def _cache_or_call_sync(
    tool_name: str,
    args: Mapping[str, Any],
    fn: Callable[..., Any],
    ttl_hours: int,
    cache_dir: Path,
) -> Any:
    path = cache_path(cache_dir, tool_name, args)
    if path.exists():
        try:
            payload = json.loads(path.read_text("utf-8"))
            if not _is_expired(payload.get("cached_at", ""), ttl_hours):
                _stats_counters["hits"] += 1
                logger.debug("cache hit: %s", path.name)
                return payload.get("result")
            _stats_counters["expired"] += 1
        except (json.JSONDecodeError, OSError):
            _stats_counters["corrupt"] += 1

    _stats_counters["misses"] += 1
    result = fn(**dict(args))
    write_cache(cache_dir, tool_name, args, result)
    return result


async def _cache_or_call_async(
    tool_name: str,
    args: Mapping[str, Any],
    fn: Callable[..., Awaitable[Any]],
    ttl_hours: int,
    cache_dir: Path,
) -> Any:
    path = cache_path(cache_dir, tool_name, args)
    if path.exists():
        try:
            payload = json.loads(path.read_text("utf-8"))
            if not _is_expired(payload.get("cached_at", ""), ttl_hours):
                _stats_counters["hits"] += 1
                logger.debug("cache hit: %s", path.name)
                return payload.get("result")
            _stats_counters["expired"] += 1
        except (json.JSONDecodeError, OSError):
            _stats_counters["corrupt"] += 1

    _stats_counters["misses"] += 1
    result = await fn(**dict(args))
    write_cache(cache_dir, tool_name, args, result)
    return result


def _json_default(obj: Any) -> Any:
    """JSON encoder fallback for Pydantic, dataclasses, datetimes, Paths."""
    if hasattr(obj, "model_dump"):  # pydantic v2
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):  # pydantic v1 fallback / dataclass-asdict-style
        try:
            return obj.dict()
        except TypeError:
            pass
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    return repr(obj)


def _to_jsonable(value: Any) -> Any:
    """Best-effort coerce a result into something json.dump can serialize.

    Handles the common shapes returned by audit providers (Pydantic models,
    dataclasses, dict-of-models). Unrecognized types are passed through; the
    actual ``json.dump`` call will fall back through ``_json_default``.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(value)
    return value
