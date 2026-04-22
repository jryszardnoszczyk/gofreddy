"""freddy fixture — fixture authoring and calibration CLI.

Subcommands added by subsequent phases:
  - fixture validate / list / envs  (Phase 3)
  - fixture staleness               (Phase 5)
  - fixture refresh                 (Phase 6)
  - fixture dry-run                 (Phase 7)
  - fixture discriminate            (Phase 10)
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import typer

from cli.freddy.fixture.cache import (
    DEFAULT_CACHE_ROOT,
    load_cache_manifest,
    staleness_status,
)
from cli.freddy.fixture.schema import (
    FixtureValidationError,
    parse_suite_manifest,
)

app = typer.Typer(
    name="fixture",
    help="Author, validate, calibrate, and refresh fixtures for search and holdout suites.",
    no_args_is_help=True,
    invoke_without_command=True,
)

_ENV_REF_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _fail(message: str) -> None:
    """Emit an error to stderr and exit with code 1."""
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(1)


def _load_manifest_payload(manifest_path: str) -> dict:
    """Read + JSON-parse a manifest, exiting cleanly on malformed JSON."""
    try:
        return json.loads(Path(manifest_path).read_text())
    except json.JSONDecodeError as exc:
        _fail(f"manifest at {manifest_path!r} is not valid JSON: {exc}")


@app.command("validate")
def validate_cmd(
    manifest_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
) -> None:
    """Validate a fixture manifest's schema and structural invariants."""
    payload = _load_manifest_payload(str(manifest_path))
    try:
        manifest = parse_suite_manifest(payload)
    except FixtureValidationError as exc:
        _fail(str(exc))

    seen: set[str] = set()
    for domain, fixtures in manifest.fixtures.items():
        for fixture in fixtures:
            if fixture.fixture_id in seen:
                _fail(f"duplicate fixture_id {fixture.fixture_id!r} in domain {domain!r}")
            seen.add(fixture.fixture_id)

    total = sum(len(f) for f in manifest.fixtures.values())
    typer.echo(
        f"✓ {manifest.suite_id}@{manifest.version}: {total} fixture(s) across "
        f"{len(manifest.fixtures)} domain(s)"
    )


@app.command("list")
def list_cmd(
    manifest_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    domain: str | None = typer.Option(None, "--domain", help="Filter to a specific domain."),
) -> None:
    """List fixtures in a manifest, optionally filtered by domain."""
    payload = _load_manifest_payload(str(manifest_path))
    try:
        manifest = parse_suite_manifest(payload)
    except FixtureValidationError as exc:
        _fail(str(exc))
    typer.echo(f"{'Fixture':<40} {'Domain':<14} {'Ver':<6} {'Anchor':<7}")
    for dom, fixtures in manifest.fixtures.items():
        if domain and dom != domain:
            continue
        for f in fixtures:
            typer.echo(
                f"{f.fixture_id:<40} {dom:<14} {f.version:<6} "
                f"{'yes' if f.anchor else 'no':<7}"
            )


@app.command("envs")
def envs_cmd(
    manifest_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    missing: bool = typer.Option(False, "--missing", help="Only show env vars NOT currently set."),
) -> None:
    """List all env var references across a manifest's fixtures."""
    payload = _load_manifest_payload(str(manifest_path))
    try:
        manifest = parse_suite_manifest(payload)
    except FixtureValidationError as exc:
        _fail(str(exc))
    refs: set[str] = set()
    for fixtures in manifest.fixtures.values():
        for f in fixtures:
            for value in (f.context, *f.env.values()):
                refs.update(_ENV_REF_RE.findall(value))
    for var in sorted(refs):
        set_status = var in os.environ
        if missing and set_status:
            continue
        marker = "✓" if set_status else "✗"
        typer.echo(f"{marker} {var}")


@app.command("staleness")
def staleness_cmd(
    cache_root: Path = typer.Option(
        Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False,
    ),
    pool: str | None = typer.Option(None, "--pool", help="Filter to a specific pool."),
    stale_only: bool = typer.Option(False, "--stale-only"),
    aging_or_worse: bool = typer.Option(False, "--aging-or-worse"),
) -> None:
    """List cached fixtures with staleness tier."""
    root = Path(cache_root)
    if not root.exists():
        typer.echo("cache root does not exist; nothing to report")
        return
    rows = []
    for pool_dir in sorted(root.iterdir()):
        if pool and pool_dir.name != pool:
            continue
        if not pool_dir.is_dir():
            continue
        for fixture_dir in sorted(pool_dir.iterdir()):
            for version_dir in sorted(fixture_dir.iterdir()):
                try:
                    manifest = load_cache_manifest(version_dir)
                except Exception:
                    continue
                status = staleness_status(manifest)
                if stale_only and status != "stale":
                    continue
                if aging_or_worse and status == "fresh":
                    continue
                rows.append(
                    (pool_dir.name, manifest.fixture_id,
                     manifest.fixture_version, status)
                )
    typer.echo(f"{'Pool':<16} {'Fixture':<40} {'Ver':<6} {'Status':<8}")
    for row in rows:
        typer.echo(f"{row[0]:<16} {row[1]:<40} {row[2]:<6} {row[3]:<8}")
