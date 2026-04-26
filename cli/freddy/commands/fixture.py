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

from ..output import emit

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
    fixtures_out = []
    for dom, fixtures in manifest.fixtures.items():
        if domain and dom != domain:
            continue
        for f in fixtures:
            fixtures_out.append({
                "fixture_id": f.fixture_id,
                "domain": dom,
                "version": f.version,
                "anchor": f.anchor,
            })
    from ..main import get_state
    emit({"fixtures": fixtures_out}, human=get_state().human)


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
    env_vars = []
    for var in sorted(refs):
        set_status = var in os.environ
        if missing and set_status:
            continue
        env_vars.append({"name": var, "set": set_status})
    from ..main import get_state
    emit({"env_vars": env_vars}, human=get_state().human)


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


@app.command("discriminate")
def discriminate_cmd(
    fixture_id: str = typer.Argument(..., help="Fixture id."),
    manifest_path: Path = typer.Option(
        ..., "--manifest", exists=True, readable=True, dir_okay=False,
        help="Path to suite manifest JSON.",
    ),
    pool: str = typer.Option(..., "--pool", help="Pool name."),
    variants: str = typer.Option(
        ..., "--variants",
        help="Comma-separated variant ids (minimum two).",
    ),
    seeds: int = typer.Option(10, "--seeds", help="Replicates per variant."),
    cache_root: Path = typer.Option(
        Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False,
    ),
) -> None:
    """Check whether a fixture separates variants — agent reads raw distributions."""
    from cli.freddy.fixture.dryrun import run_discriminability_check

    try:
        report = run_discriminability_check(
            fixture_id=fixture_id,
            pool=pool,
            manifest_path=Path(manifest_path),
            variants=[v.strip() for v in variants.split(",") if v.strip()],
            seeds=seeds,
            cache_root=Path(cache_root),
        )
    except ValueError as exc:
        _fail(str(exc))

    typer.echo(json.dumps(report.to_dict(), indent=2))
    if report.verdict != "separable":
        typer.echo(
            f"error: fixture not separable: verdict={report.verdict}: {report.reasoning}",
            err=True,
        )
        raise typer.Exit(code=1)


@app.command("staleness")
def staleness_cmd(
    cache_root: Path = typer.Option(
        Path(str(DEFAULT_CACHE_ROOT)), "--cache-root", file_okay=False,
    ),
    pool: str | None = typer.Option(None, "--pool", help="Filter to a specific pool."),
    stale_only: bool = typer.Option(False, "--stale-only"),
    aging_or_worse: bool = typer.Option(False, "--aging-or-worse"),
    with_saturation_check: bool = typer.Option(
        False, "--with-saturation-check",
        help=(
            "Also ask the system_health.saturation agent whether any listed "
            "fixture should rotate_now based on its saturation_cycle history. "
            "Requires EVOLUTION_JUDGE_URL + EVOLUTION_INVOKE_TOKEN in env."
        ),
    ),
) -> None:
    """List cached fixtures with staleness tier.

    Default output: pool, fixture_id, version, age-based status
    (fresh/aging/stale from cache-manifest retention_days).

    ``--with-saturation-check`` adds a "Rotate" column with the
    system_health.saturation agent's verdict for each fixture. Reads
    ``kind="saturation_cycle"`` events from the unified events log,
    batches per-fixture history, and POSTs one agent call per fixture.
    Tags ``rotate_now`` in the output (or `-` if the agent said fine /
    rotate_soon / no data). No hardcoded beat-rate threshold — the
    agent decides.
    """
    from ..main import get_state
    root = Path(cache_root)
    if not root.exists():
        emit({"fixtures": [], "note": "cache root does not exist"}, human=get_state().human)
        return
    rows = []
    for pool_dir in sorted(root.iterdir()):
        if pool and pool_dir.name != pool:
            continue
        if not pool_dir.is_dir():
            continue
        for fixture_dir in sorted(pool_dir.iterdir()):
            for version_dir in sorted(fixture_dir.iterdir()):
                # Skip archive snapshots created by _archive_existing
                # (named "<live>.archive-<TIMESTAMP>Z"); only the live
                # cache dir should appear in staleness output.
                if ".archive-" in version_dir.name:
                    continue
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
                    [pool_dir.name, manifest.fixture_id,
                     manifest.fixture_version, status]
                )

    rotation_tags: dict[str, str] = {}
    if with_saturation_check:
        rotation_tags = _query_saturation_agent_per_fixture(
            [(r[0], r[1]) for r in rows],
        )

    fixtures_out = []
    for row in rows:
        entry = {
            "pool": row[0],
            "fixture_id": row[1],
            "version": row[2],
            "status": row[3],
        }
        if with_saturation_check:
            entry["rotate"] = rotation_tags.get(row[1], "-")
        fixtures_out.append(entry)
    emit({"fixtures": fixtures_out}, human=get_state().human)


def _query_saturation_agent_per_fixture(
    pool_fixture_pairs: list[tuple[str, str]],
) -> dict[str, str]:
    """For each (pool, fixture_id), batch its saturation_cycle events and
    POST to /invoke/system_health/saturation. Return {fixture_id → tag}
    where tag ∈ {"rotate_now", "rotate_soon", "fine", "no_data", "error"}.

    Operator-only path; default staleness output doesn't hit this.
    """
    try:
        from autoresearch.events import read_events
        from autoresearch.judges.quality_judge import call_quality_judge
    except Exception:
        return {fid: "error" for _, fid in pool_fixture_pairs}

    tags: dict[str, str] = {}
    all_events = list(read_events(kind="saturation_cycle"))
    for _pool, fixture_id in pool_fixture_pairs:
        cycle_events = [e for e in all_events if e.get("fixture_id") == fixture_id]
        if not cycle_events:
            tags[fixture_id] = "no_data"
            continue
        try:
            verdict = call_quality_judge({
                "role": "saturation",
                "fixture_id": fixture_id,
                "cycle_events": cycle_events,
            })
            tags[fixture_id] = str(verdict.verdict)
        except Exception:
            tags[fixture_id] = "error"
    return tags
