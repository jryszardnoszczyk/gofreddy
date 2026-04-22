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


@app.command("refresh")
def refresh_cmd(
    fixture_id: str | None = typer.Argument(
        None, help="Fixture id to refresh. Omit when using --all-stale/--all-aging.",
    ),
    manifest_path: Path = typer.Option(
        ..., "--manifest", exists=True, readable=True, dir_okay=False,
        help="Path to suite manifest JSON.",
    ),
    pool: str = typer.Option(
        ..., "--pool",
        help="Pool name, must equal manifest.suite_id (e.g. 'search-v1').",
    ),
    cache_root: Path = typer.Option(
        Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False,
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print plan without fetching."),
    force: bool = typer.Option(False, "--force", help="Refresh even if cache is fresh."),
    isolation: str = typer.Option(
        "local", "--isolation",
        help="'local' (default) uses ambient env; 'ci' reads holdout creds from chmod-600 file.",
    ),
    all_stale: bool = typer.Option(False, "--all-stale", help="Batch-refresh every stale fixture."),
    all_aging: bool = typer.Option(
        False, "--all-aging", help="Batch-refresh every aging-or-worse fixture.",
    ),
) -> None:
    """Manually refresh cached data for a fixture (or a batch of fixtures)."""
    from cli.freddy.fixture.refresh import refresh_all, refresh_fixture

    if isolation not in ("local", "ci"):
        _fail(f"--isolation must be 'local' or 'ci', got {isolation!r}")

    if all_stale and all_aging:
        _fail("--all-stale and --all-aging are mutually exclusive")

    if all_stale or all_aging:
        if fixture_id:
            _fail("do not combine a specific fixture_id with --all-stale/--all-aging")
        tier = "stale" if all_stale else "aging-or-worse"
        try:
            results = refresh_all(
                manifest_path=Path(manifest_path), pool=pool,
                cache_root=Path(cache_root), tier_filter=tier,
                dry_run=dry_run, isolation=isolation,  # type: ignore[arg-type]
            )
        except ValueError as exc:
            _fail(str(exc))
        except RuntimeError as exc:
            _fail(str(exc))
        for r in results:
            for line in r.report_lines:
                typer.echo(line)
        typer.echo(f"Refreshed {len(results)} fixture(s) matching tier={tier!r}")
        return

    if not fixture_id:
        _fail("fixture_id is required unless --all-stale or --all-aging is set")

    try:
        result = refresh_fixture(
            manifest_path=Path(manifest_path), pool=pool, fixture_id=fixture_id,
            cache_root=Path(cache_root), dry_run=dry_run, force=force,
            isolation=isolation,  # type: ignore[arg-type]
        )
    except ValueError as exc:  # pool/suite_id mismatch
        _fail(str(exc))
    except KeyError as exc:
        _fail(str(exc))
    except RuntimeError as exc:  # isolation=ci credential problems
        _fail(str(exc))
    for line in result.report_lines:
        typer.echo(line)


@app.command("dry-run")
def dryrun_cmd(
    fixture_id: str = typer.Argument(..., help="Fixture id to calibrate."),
    manifest_path: Path = typer.Option(
        ..., "--manifest", exists=True, readable=True, dir_okay=False,
        help="Path to suite manifest JSON.",
    ),
    pool: str = typer.Option(
        ..., "--pool", help="Pool name, must equal manifest.suite_id.",
    ),
    baseline: str = typer.Option(
        "v006", "--baseline", help="Variant id to run the fixture against.",
    ),
    seeds: int = typer.Option(3, "--seeds", help="Judge replicate count (N)."),
    cache_root: Path = typer.Option(
        Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False,
    ),
) -> None:
    """Run a fixture against a baseline variant and report the judge verdict."""
    from cli.freddy.fixture.dryrun import JudgeUnreachable, run_dry_run

    try:
        report, exit_code = run_dry_run(
            fixture_id,
            manifest_path=Path(manifest_path),
            pool=pool,
            baseline=baseline,
            seeds=seeds,
            cache_root=Path(cache_root),
        )
    except ValueError as exc:  # pool/suite_id mismatch
        _fail(str(exc))
    except KeyError as exc:
        _fail(str(exc))
    except JudgeUnreachable as exc:
        _fail(f"quality judge unreachable: {exc}")

    typer.echo(json.dumps(report, indent=2))
    if exit_code == 2:
        typer.echo(
            "Quality judge abstained (verdict=unclear). Review the raw stats "
            "and reasoning above, then decide manually or re-run with more seeds.",
            err=True,
        )
        raise typer.Exit(code=2)
    if exit_code != 0:
        verdict = str((report.get("quality_verdict") or {}).get("verdict"))
        typer.echo(f"error: fixture not healthy: verdict={verdict}", err=True)
        raise typer.Exit(code=exit_code)


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
