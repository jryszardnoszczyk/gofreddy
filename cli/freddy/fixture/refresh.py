"""Manual fixture cache refresh orchestration.

Operator-triggered only. Never auto-refetches — that would defeat the
staleness-flag-and-manual-refresh contract.

Phase 6 of Plan A (docs/plans/2026-04-21-002-feat-fixture-infrastructure-plan.md).

Behavior summary:
  * Archives any existing version dir before writing fresh (`v1.0` →
    `v1.0.archive-YYYYMMDDTHHMMSSZ`).
  * Emits `kind=content_drift` events via ``autoresearch.events.log_event``
    when the new artifact's sha1 differs from the prior cached record.
  * `--isolation=local` (default) executes subprocess fetches with the
    operator's ambient environment. `--isolation=ci` reads holdout
    credentials from a chmod-600 file at
    ``~/.config/gofreddy/holdouts/.credentials`` and exports them to the
    subprocess scope only. Missing file or wrong perms = hard-fail.
  * ``--dry-run`` prints the fetch plan without touching the filesystem.
  * Per-fixture refresh gates on `staleness_status` unless `--force` is set.
  * Batch modes (``--all-stale`` / ``--all-aging``) iterate the manifest
    and filter by staleness tier.
"""
from __future__ import annotations

import getpass
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from cli.freddy.fixture.cache import (
    CacheManifest,
    DataSourceRecord,
    artifact_filename,
    cache_path_for,
    load_cache_manifest,
    staleness_status,
    write_cache_manifest,
)
from cli.freddy.fixture.schema import (
    FixtureSpec,
    SuiteManifest,
    assert_pool_matches,
    parse_suite_manifest,
)


Isolation = Literal["local", "ci"]

HOLDOUT_CREDENTIALS_PATH = Path.home() / ".config/gofreddy/holdouts/.credentials"


@dataclass
class RefreshResult:
    fixture_id: str
    report_lines: list[str]
    cache_dir: Path | None
    cost_usd: float


# -- config loaders ------------------------------------------------------

_SOURCES_CONFIG: dict[str, Any] | None = None
_POOL_POLICIES: dict[str, Any] | None = None


def _load_sources_config() -> dict[str, Any]:
    global _SOURCES_CONFIG
    if _SOURCES_CONFIG is None:
        config_path = Path(__file__).resolve().parent / "sources.json"
        _SOURCES_CONFIG = json.loads(config_path.read_text())
    return _SOURCES_CONFIG


def _load_pool_policies() -> dict[str, Any]:
    """Load pool → miss-semantics mapping. Unknown pool falls back to _default."""
    global _POOL_POLICIES
    if _POOL_POLICIES is None:
        config_path = Path(__file__).resolve().parent / "pool_policies.json"
        _POOL_POLICIES = json.loads(config_path.read_text())
    return _POOL_POLICIES


def pool_on_miss(pool: str) -> str:
    """Return the miss-semantics verdict for ``pool`` ('live_fetch' | 'hard_fail').

    Unknown pools fall through to ``_default`` (fail-closed). Callers on the
    session-read path use this to decide whether to live-fetch or raise.
    """
    policies = _load_pool_policies()
    entry = policies.get(pool, policies.get("_default", {"on_miss": "hard_fail"}))
    return str(entry.get("on_miss", "hard_fail"))


# -- isolation / credentials ---------------------------------------------


def _load_ci_credentials() -> dict[str, str]:
    """Parse chmod-600 holdout credentials file. Raises on missing or wide perms.

    Format: KEY=value per line, `#` and blank lines ignored. Values must not
    contain newlines; quoting is not supported — keys are env vars.
    """
    path = HOLDOUT_CREDENTIALS_PATH
    if not path.exists():
        raise RuntimeError(
            f"--isolation=ci requires holdout credentials at {path}; file not found. "
            f"Create it (chmod 600) with KEY=value lines for each required env var."
        )
    mode = path.stat().st_mode & 0o777
    # Group + other bits must be zero: owner-only read/write.
    if mode & 0o077:
        raise RuntimeError(
            f"holdout credentials at {path} have insecure permissions {oct(mode)}; "
            f"must be chmod 600 (0o600). Run: chmod 600 {path}"
        )
    creds: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        creds[key.strip()] = value.strip()
    return creds


def _subprocess_env(fixture_id: str, fixture: FixtureSpec, isolation: Isolation) -> dict[str, str]:
    """Build the env dict passed to source-fetch subprocesses.

    Scrubs any inherited ``FREDDY_FIXTURE_*`` to prevent recursive cache reads
    from within the child freddy process. `ci` isolation overlays holdout
    credentials on top of the scrubbed env.
    """
    parent_env = {k: v for k, v in os.environ.items() if not k.startswith("FREDDY_FIXTURE_")}
    env = {
        **parent_env,
        "FREDDY_FIXTURE_ID": fixture_id,
        "FREDDY_FIXTURE_VERSION": fixture.version,
    }
    if isolation == "ci":
        env.update(_load_ci_credentials())
    return env


# -- source resolution ---------------------------------------------------


def _determine_sources(fixture: FixtureSpec, domain: str) -> list[dict[str, Any]]:
    """Return ordered source-fetch descriptors for this fixture (by domain).

    Descriptors come from sources.json. ``retention_days`` is resolved from
    the ``retention_defaults`` table keyed by the descriptor's sentinel
    (``_default``, ``page``, ``visibility``, …). Per-fixture override via
    env var ``RETENTION_DAYS``.
    """
    config = _load_sources_config()
    domain_descriptors = config.get("domains", {}).get(domain)
    if domain_descriptors is None:
        raise ValueError(
            f"no source descriptors registered for domain {domain!r} "
            f"in cli/freddy/fixture/sources.json. Add the domain block before refreshing."
        )

    out: list[dict[str, Any]] = []
    for desc in domain_descriptors:
        resolved = dict(desc)
        default_key = resolved["retention_days"]
        default_val = int(config["retention_defaults"][domain][default_key])
        env_override = fixture.env.get("RETENTION_DAYS")
        if env_override and str(env_override).isdigit():
            resolved["retention_days"] = int(env_override)
        else:
            resolved["retention_days"] = default_val
        out.append(resolved)
    return out


def _resolve_ref(fixture: FixtureSpec, ref: dict[str, Any]) -> str:
    """Resolve one ``args_template`` entry's value from the fixture.

    Supported keys:
      * ``from: "context"``       → ``fixture.context``
      * ``from: "client"``        → ``fixture.client``
      * ``from: "env.<NAME>"``    → ``fixture.env[NAME]`` (empty if missing)
      * ``fallback_from: ...``    → same grammar, used when the primary
                                    source resolves to empty/missing
      * ``default: "<literal>"``  → final fallback (static string)

    Returns a string (possibly empty). Empty ≠ failure — the caller decides
    whether to pass or skip the arg.
    """
    def _lookup(key: str) -> str:
        if key == "context":
            return fixture.context or ""
        if key == "client":
            return fixture.client or ""
        if key.startswith("env."):
            return str(fixture.env.get(key[4:], "") or "")
        return ""

    primary = ref.get("from")
    value = _lookup(primary) if primary else ""
    if not value:
        fallback = ref.get("fallback_from")
        if fallback:
            value = _lookup(fallback)
    if not value:
        value = str(ref.get("default", ""))
    return value


def _assemble_cli_args(
    fixture: FixtureSpec, source_desc: dict[str, Any],
) -> tuple[list[str], str]:
    """Return ``(cli_args, cache_key_arg)`` for one source.

    ``cli_args`` is the list to append to ``source_desc["command"]``, honoring
    the ``args_template`` shape (positional + flag kinds). Empty-valued flag
    entries are skipped silently; empty-valued positional entries emit an
    empty string (breaking downstream subprocess — surfaces loudly).

    ``cache_key_arg`` is the ``arg_for_cache_key`` ref resolved to a string.
    It must match what the session-invoked CLI uses as its ``try_read_cache``
    arg, otherwise cache lookups miss.

    Every source in sources.json ships with ``args_template`` +
    ``arg_for_cache_key``; the absence of either is a config bug.
    """
    template = source_desc.get("args_template")
    cache_ref = source_desc.get("arg_for_cache_key")
    if template is None or cache_ref is None:
        raise ValueError(
            f"source descriptor missing args_template or arg_for_cache_key: "
            f"{source_desc.get('source')}/{source_desc.get('data_type')}"
        )

    cli_args: list[str] = []
    for entry in template:
        kind = entry.get("kind", "positional")
        value = _resolve_ref(fixture, entry)
        if kind == "flag":
            flag = entry.get("flag")
            if not flag:
                raise ValueError(f"args_template entry missing 'flag': {entry!r}")
            if value:
                cli_args.extend([flag, value])
            # empty-value flag: silently skip (treat as optional)
        elif kind == "positional":
            cli_args.append(value)
        else:
            raise ValueError(f"unknown args_template kind: {kind!r}")

    cache_arg = _resolve_ref(fixture, cache_ref) if cache_ref else ""
    return cli_args, cache_arg


# -- cost extraction -----------------------------------------------------


def _extract_cost_usd(data: Any) -> float:
    """Permissively extract cost_usd from a parsed-JSON payload.

    Accepts dicts with ``_meta.cost_usd`` (nested) or top-level ``cost_usd``.
    Lists and other shapes report 0.0 — the caller already flagged the
    command's expectation via Phase 0 inventory.
    """
    if isinstance(data, dict):
        meta = data.get("_meta")
        if isinstance(meta, dict) and "cost_usd" in meta:
            try:
                return float(meta["cost_usd"])
            except (TypeError, ValueError):
                return 0.0
        if "cost_usd" in data:
            try:
                return float(data["cost_usd"])
            except (TypeError, ValueError):
                return 0.0
    return 0.0


# -- subprocess fetch ----------------------------------------------------


def _run_source_fetch(
    source_desc: dict[str, Any],
    fixture_id: str,
    fixture: FixtureSpec,
    cache_dir: Path,
    arg: str,
    isolation: Isolation = "local",
    cli_args: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Execute the freddy CLI call for one source.

    ``arg`` is the cache-key arg (one scalar used for artifact filename +
    cache record). ``cli_args`` is the full list of CLI args assembled
    from ``args_template`` (flags + positionals). Both are required in
    production; ``cli_args=None`` only appears in legacy tests that stub
    ``_run_source_fetch`` entirely.

    Returns a list of dicts (single-element) shaped to match DataSourceRecord
    constructor kwargs — the caller flattens and records them.

    Stubbed under tests via ``@patch("cli.freddy.fixture.refresh._run_source_fetch")``.
    """
    env = _subprocess_env(fixture_id, fixture, isolation)
    if cli_args is None:
        cli_args = [arg] if arg else []
    cmd = [*source_desc["command"], *cli_args]
    out_path = cache_dir / artifact_filename(
        source_desc["source"], source_desc["data_type"], arg,
    )
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=fixture.timeout, env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"fetch failed for {source_desc['source']}/{source_desc['data_type']} "
            f"(arg={arg[:60]}): {result.stderr[:500]}"
        )
    out_path.write_text(result.stdout)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"fetch for {source_desc['source']} returned non-JSON output"
        )
    record_count = len(data) if isinstance(data, list) else 1
    cost_usd = _extract_cost_usd(data)
    # Canonicalize for sha1 so cosmetic whitespace does not register as drift.
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    content_sha1 = hashlib.sha1(canonical.encode()).hexdigest()

    return [{
        "source": source_desc["source"],
        "data_type": source_desc["data_type"],
        "arg": arg,
        "retention_days": source_desc["retention_days"],
        "cached_artifact": out_path.name,
        "record_count": record_count,
        "cost_usd": cost_usd,
        "content_sha1": content_sha1,
    }]


# -- manifest helpers ----------------------------------------------------


def _parse_manifest(manifest_path: Path) -> SuiteManifest:
    payload = json.loads(Path(manifest_path).read_text())
    return parse_suite_manifest(payload)


def _find_fixture(manifest: SuiteManifest, fixture_id: str) -> tuple[FixtureSpec, str]:
    for domain, fixtures in manifest.fixtures.items():
        for f in fixtures:
            if f.fixture_id == fixture_id:
                return f, domain
    raise KeyError(f"fixture {fixture_id!r} not found in manifest")


def _archive_existing(cache_dir: Path) -> Path | None:
    """If ``cache_dir`` exists, rename it with an archive-<timestamp> suffix.

    Returns the archived path or None if nothing to archive.
    """
    if not cache_dir.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = cache_dir.parent / f"{cache_dir.name}.archive-{ts}"
    cache_dir.rename(archive)
    return archive


def _maybe_emit_drift(
    fixture_id: str,
    source_desc: dict[str, Any],
    arg: str,
    new_sha1: str,
    prior_manifest: CacheManifest | None,
) -> None:
    if prior_manifest is None:
        return
    prior = prior_manifest.lookup(source_desc["source"], source_desc["data_type"], arg)
    if prior is None or not prior.content_sha1:
        return
    if prior.content_sha1 == new_sha1:
        return
    # Deferred import: autoresearch.events is an autoresearch-side module;
    # we touch it only when there's actual drift to emit.
    from autoresearch.events import log_event

    log_event(
        kind="content_drift",
        fixture_id=fixture_id,
        source=source_desc["source"],
        data_type=source_desc["data_type"],
        arg=arg,
        old_sha1=prior.content_sha1,
        new_sha1=new_sha1,
    )


# -- main entry ----------------------------------------------------------


def refresh_fixture(
    *,
    manifest_path: Path,
    pool: str,
    fixture_id: str,
    cache_root: Path,
    dry_run: bool = False,
    force: bool = False,
    isolation: Isolation = "local",
) -> RefreshResult:
    """Refresh one fixture's cache. See module docstring for semantics."""
    parsed_manifest = _parse_manifest(Path(manifest_path))
    assert_pool_matches(pool, parsed_manifest)

    # Validate isolation credentials upfront — before any cache I/O or fetches.
    # Catches the missing/insecure-perms case loudly even when the subprocess
    # layer is mocked out (tests) or never reached (dry-run).
    if isolation == "ci":
        _load_ci_credentials()

    fixture, domain = _find_fixture(parsed_manifest, fixture_id)
    cache_dir = cache_path_for(cache_root, pool, fixture.fixture_id, fixture.version)
    sources = _determine_sources(fixture, domain)

    lines: list[str] = [
        f"Refreshing {fixture_id}@{fixture.version} ({pool}, domain={domain})"
    ]

    if dry_run:
        lines.append("Sources that would be fetched (plan):")
        for src in sources:
            cli_args, cache_arg = _assemble_cli_args(fixture, src)
            lines.append(
                f"  - {src['source']}/{src['data_type']} "
                f"cmd={' '.join([*src['command'], *cli_args])!r} "
                f"cache_key={cache_arg[:60]!r} retention={src['retention_days']}d"
            )
        lines.append("(dry-run; no fetches performed)")
        return RefreshResult(
            fixture_id=fixture_id, report_lines=lines,
            cache_dir=None, cost_usd=0.0,
        )

    # Freshness gate unless --force.
    prior_manifest: CacheManifest | None = None
    if cache_dir.exists():
        try:
            prior_manifest = load_cache_manifest(cache_dir)
        except Exception:
            prior_manifest = None
        if prior_manifest and not force and staleness_status(prior_manifest) == "fresh":
            lines.append("cache is fresh; pass --force to refresh anyway")
            return RefreshResult(
                fixture_id=fixture_id, report_lines=lines,
                cache_dir=cache_dir, cost_usd=0.0,
            )

    # Archive prior before writing fresh.
    archived = _archive_existing(cache_dir)
    if archived is not None:
        lines.append(f"archived prior cache to {archived.name}")

    cache_dir.mkdir(parents=True)
    start = time.time()
    records: list[DataSourceRecord] = []
    total_cost = 0.0
    for src in sources:
        cli_args, cache_arg = _assemble_cli_args(fixture, src)
        payloads = _run_source_fetch(
            src, fixture.fixture_id, fixture, cache_dir, cache_arg, isolation,
            cli_args=cli_args,
        )
        for payload in payloads:
            # Stubs (via @patch) may omit content_sha1; default-empty keeps
            # the DataSourceRecord dataclass happy and means first-seen.
            payload.setdefault("content_sha1", "")
            _maybe_emit_drift(
                fixture.fixture_id, src, payload.get("arg", cache_arg),
                payload["content_sha1"], prior_manifest,
            )
            records.append(DataSourceRecord(**payload))
            total_cost += float(payload.get("cost_usd", 0.0))
            lines.append(
                f"  ✓ {payload['source']}/{payload['data_type']}"
                f" (cache_key={cache_arg[:40]!r}) {payload['record_count']} records  "
                f"${payload['cost_usd']:.2f}"
            )

    duration = int(time.time() - start)
    cache_manifest = CacheManifest(
        fixture_id=fixture.fixture_id,
        fixture_version=fixture.version,
        pool=pool,
        fetched_at=datetime.now(timezone.utc),
        fetched_by=getpass.getuser(),
        data_sources=records,
        total_fetch_cost_usd=total_cost,
        fetch_duration_seconds=duration,
    )
    write_cache_manifest(cache_dir, cache_manifest)
    lines.append(
        f"  Total: {sum(r.record_count for r in records)} records, "
        f"${total_cost:.2f}, {duration}s"
    )
    lines.append(f"Cache written: {cache_dir}")
    return RefreshResult(
        fixture_id=fixture_id, report_lines=lines,
        cache_dir=cache_dir, cost_usd=total_cost,
    )


def refresh_all(
    *,
    manifest_path: Path,
    pool: str,
    cache_root: Path,
    tier_filter: str,  # "stale" | "aging-or-worse"
    dry_run: bool = False,
    isolation: Isolation = "local",
) -> list[RefreshResult]:
    """Batch-refresh every fixture in ``manifest_path`` at or past ``tier_filter``."""
    manifest = _parse_manifest(Path(manifest_path))
    assert_pool_matches(pool, manifest)
    results: list[RefreshResult] = []
    for fixtures in manifest.fixtures.values():
        for fixture in fixtures:
            cache_dir = cache_path_for(
                cache_root, pool, fixture.fixture_id, fixture.version,
            )
            if not cache_dir.exists():
                continue  # Nothing to refresh; no baseline cache exists.
            try:
                cm = load_cache_manifest(cache_dir)
            except Exception:
                continue
            status = staleness_status(cm)
            if tier_filter == "stale" and status != "stale":
                continue
            if tier_filter == "aging-or-worse" and status == "fresh":
                continue
            results.append(
                refresh_fixture(
                    manifest_path=Path(manifest_path),
                    pool=pool,
                    fixture_id=fixture.fixture_id,
                    cache_root=Path(cache_root),
                    dry_run=dry_run,
                    force=True,
                    isolation=isolation,
                )
            )
    return results
