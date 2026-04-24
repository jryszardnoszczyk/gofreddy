"""Helpers for freddy commands to read from fixture cache when env vars are set.

This module is the ONLY place that consults ``pool_policies.json``. Commands
call :func:`try_read_cache` which decides miss semantics from the active pool:

- ``search-v1`` (``on_miss=live_fetch``) → cache miss returns ``None``; caller
  proceeds with the live fetch.
- ``holdout-v1`` (``on_miss=hard_fail``) → cache miss raises ``RuntimeError``.
  A live fetch from a holdout session would leak holdout identity to provider
  logs (request auth, IP, UA), destroying credential isolation.
- Unknown pool → ``_default`` → hard-fail (default-deny). A future pool
  naming-convention change cannot silently downgrade isolation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from cli.freddy.fixture.cache import (
    artifact_filename,
    cache_path_for,
    load_cache_manifest,
    staleness_status,
)


def fixture_cache_context() -> dict[str, str] | None:
    """Return fixture-cache context if env indicates cache-first mode, else None.

    All four ``FREDDY_FIXTURE_*`` env vars must be set (and non-empty after
    strip) for the command to operate in cache-first mode. A partially set
    environment is treated the same as unset — the command live-fetches
    (preserving today's manual workflow).
    """
    required = (
        "FREDDY_FIXTURE_CACHE_DIR",
        "FREDDY_FIXTURE_POOL",
        "FREDDY_FIXTURE_ID",
        "FREDDY_FIXTURE_VERSION",
    )
    values = {k: os.environ.get(k, "").strip() for k in required}
    if not all(values.values()):
        return None
    return values


def try_read_cache(
    source: str,
    data_type: str,
    arg: str,
    shape_flags: dict[str, str] | None = None,
) -> dict | list | None:
    """Return cached data for the given ``(source, data_type, arg)`` triple.

    Cache miss semantics are read from ``pool_policies.json`` per the active
    ``FREDDY_FIXTURE_POOL``:

    - ``on_miss == "live_fetch"`` → return ``None``; the caller live-fetches.
    - ``on_miss == "hard_fail"`` → raise ``RuntimeError`` with the exact
      ``freddy fixture refresh …`` command to remediate. Unknown pools fall
      through to ``_default`` which is also ``hard_fail``.

    Prints a stderr warning when the cache entry is stale but still returns
    the cached payload; refresh is never automatic.
    """
    import typer

    ctx = fixture_cache_context()
    if ctx is None:
        return None

    cache_dir = cache_path_for(
        Path(ctx["FREDDY_FIXTURE_CACHE_DIR"]),
        ctx["FREDDY_FIXTURE_POOL"],
        ctx["FREDDY_FIXTURE_ID"],
        ctx["FREDDY_FIXTURE_VERSION"],
    )

    # Consult pool_policies.json for miss semantics. Unknown pool →
    # ``_default`` → hard_fail. Default-deny prevents a future pool-naming
    # convention change from silently downgrading isolation.
    _policies_path = Path(__file__).resolve().parent / "pool_policies.json"
    _policies = json.loads(_policies_path.read_text())
    _pool = ctx["FREDDY_FIXTURE_POOL"]
    _on_miss = _policies.get(_pool, _policies["_default"])["on_miss"]
    hard_fail_on_miss = _on_miss == "hard_fail"

    def _miss(reason: str) -> None:
        if hard_fail_on_miss:
            # Holdout-specific language preserved for the pool where a live
            # fetch would leak identity; other pools get an agent-priming
            # pointer (Python callers must not silently fall back to live
            # data — gaps surface loudly and the agent handles the fetch).
            if _pool == "holdout-v1":
                raise RuntimeError(
                    f"Holdout cache miss for {source}/{data_type} "
                    f"(arg={arg[:60]}): {reason}. "
                    f"Live-fetch would leak holdout identity to provider logs. "
                    f"Run: freddy fixture refresh {ctx['FREDDY_FIXTURE_ID']} "
                    f"--pool {ctx['FREDDY_FIXTURE_POOL']} "
                    f"--manifest <your-manifest>"
                )
            raise RuntimeError(
                f"Cache miss for {source}/{data_type} "
                f"(arg={arg[:60]}) in pool {_pool!r}: {reason}. "
                f"Automatic live-fetch is disabled — gaps are filled by the "
                f"priming agent, not by Python. "
                f"Run the prime-fixtures agent "
                f"(docs/agent-tasks/prime-fixtures.md) with "
                f"fixture_ids={ctx['FREDDY_FIXTURE_ID']}, pool={_pool}."
            )

    if not cache_dir.exists():
        _miss("cache directory does not exist")
        return None

    try:
        manifest = load_cache_manifest(cache_dir)
    except Exception as exc:
        _miss(f"manifest unreadable: {exc}")
        return None

    expected_artifact = artifact_filename(source, data_type, arg, shape_flags)
    for src in manifest.data_sources:
        # ``src.arg == arg`` guards against sha1-truncation collisions: a
        # 48-bit filename-hash match with a different raw arg returns cache
        # miss instead of silently serving wrong data.
        if (
            src.source == source
            and src.data_type == data_type
            and src.arg == arg
            and src.cached_artifact == expected_artifact
        ):
            status = staleness_status(manifest)
            if status != "fresh":
                typer.echo(
                    f"WARNING: Fixture {ctx['FREDDY_FIXTURE_ID']} cache is "
                    f"{status.upper()}. Refresh: freddy fixture refresh "
                    f"{ctx['FREDDY_FIXTURE_ID']} "
                    f"--pool {ctx['FREDDY_FIXTURE_POOL']}",
                    err=True,
                )
            artifact_path = cache_dir / src.cached_artifact
            return json.loads(artifact_path.read_text())

    _miss("no matching (source, data_type, arg) entry in manifest")
    return None
