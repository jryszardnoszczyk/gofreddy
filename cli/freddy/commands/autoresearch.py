"""freddy autoresearch — render + publish CLI for autoresearch reports.

Spec D1 (`docs/plans/2026-05-07-003-self-improving-report-rendering.md`).

    freddy autoresearch render <variant> <lane> <fixture>
        Re-render report.html / .pdf / .png for one fixture.

    freddy autoresearch publish <variant> <lane> <fixture> [--public]
        Default: portal-gated (returns the authed URL). With --public:
        also writes to R2 hosting bucket and returns a public slug URL.

    freddy autoresearch detect-meta-patterns
        Walk archive/v*/sessions/* and emit cross-lane meta-patterns.
"""
from __future__ import annotations
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    help="Autoresearch report render + publish (spec section D1).",
    no_args_is_help=True,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ARCHIVE_ROOT = _REPO_ROOT / "autoresearch" / "archive"


def _session_dir(variant: str, lane: str, fixture: str) -> Path:
    return _ARCHIVE_ROOT / variant / "sessions" / lane / fixture


def _resolve_render_script(variant: str) -> Path:
    candidates = [
        _ARCHIVE_ROOT / variant / "scripts" / "render_report.py",
        _ARCHIVE_ROOT / "current_runtime" / "scripts" / "render_report.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "render_report.py not found in either variant or current_runtime"
    )


def _resolve_python() -> str:
    return os.environ.get(
        "FREDDY_PYTHON",
        str(_REPO_ROOT / ".venv" / "bin" / "python3"),
    ) if (Path(os.environ.get("FREDDY_PYTHON", str(_REPO_ROOT / ".venv" / "bin" / "python3"))).exists()) else sys.executable


def _rel_or_abs(path: Path) -> str:
    """Best-effort path display relative to repo root; falls back to absolute."""
    try:
        return str(path.relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


@app.command("render")
def render(
    variant: str = typer.Argument(..., help="e.g. v009"),
    lane: str = typer.Argument(
        ...,
        help="geo / competitive / monitoring / storyboard / "
             "marketing_audit / x_engine / linkedin_engine",
    ),
    fixture: str = typer.Argument(..., help="e.g. nubank"),
) -> None:
    """(Re-)render report.html + .pdf + .png for one fixture."""
    if lane not in ("geo", "competitive", "monitoring", "storyboard",
                    "marketing_audit", "x_engine", "linkedin_engine"):
        typer.secho(f"unknown lane: {lane}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    sd = _session_dir(variant, lane, fixture)
    if not sd.exists():
        typer.secho(f"session dir not found: {sd}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    script = _resolve_render_script(variant)
    typer.secho(f"  Running: {_rel_or_abs(script)} {_rel_or_abs(sd)} {lane} {fixture}",
                fg=typer.colors.CYAN)
    rc = subprocess.run(
        [_resolve_python(), str(script), str(sd), lane, fixture],
        cwd=_REPO_ROOT,
    ).returncode
    if rc != 0:
        raise typer.Exit(rc)


@app.command("publish")
def publish(
    variant: str = typer.Argument(...),
    lane: str = typer.Argument(...),
    fixture: str = typer.Argument(...),
    client: str = typer.Option("", help="Client slug for portal-gated URL"),
    public: bool = typer.Option(False, "--public",
        help="Also publish a public R2 slug URL via rclone (audit-hosting bucket)"),
) -> None:
    """Publish a rendered report (portal-gated by default; --public for R2)."""
    if lane not in ("geo", "competitive", "monitoring", "storyboard",
                    "marketing_audit", "x_engine", "linkedin_engine"):
        typer.secho(f"unknown lane: {lane}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    sd = _session_dir(variant, lane, fixture)
    if not sd.exists():
        typer.secho(f"session dir not found: {sd}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    html = sd / "report.html"
    if not html.exists():
        typer.secho(
            f"report.html missing. Run `freddy autoresearch render {variant} {lane} {fixture}` first.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(1)
    pdf = sd / "report.pdf"
    png = sd / "report-screenshot.png"

    if public:
        slug = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:12].lower()
        typer.secho(f"  Slug:   {slug}", fg=typer.colors.CYAN)
        rclone = subprocess.run(["which", "rclone"], capture_output=True, text=True)
        if rclone.returncode == 0:
            cmd = [
                rclone.stdout.strip(), "copy", str(sd),
                f"r2:audit-hosting/reports/{slug}/",
                "--include", "report.html",
                "--include", "report.pdf",
                "--include", "report-screenshot.png",
            ]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                typer.secho(f"  ✓ Uploaded to R2.", fg=typer.colors.GREEN)
            else:
                typer.secho(
                    f"  ⚠ rclone returned rc={r.returncode}; dry-run only.",
                    fg=typer.colors.YELLOW,
                )
        else:
            typer.secho(
                "  ⚠ rclone not installed — dry-run only.",
                fg=typer.colors.YELLOW,
            )
        public_url = (
            f"https://reports.{os.environ.get('FREDDY_R2_DOMAIN', 'gofreddy.example')}"
            f"/{slug}/report.html"
        )
        typer.echo(f"\n  Public URL: {public_url}")
        return

    # Portal-gated path
    portal_url = (
        f"https://{os.environ.get('FREDDY_PORTAL_DOMAIN', 'portal.gofreddy.example')}"
        f"/v1/portal/{client}/reports/{lane}/{variant}/{fixture}"
    )
    typer.secho(f"  Portal-gated URL: {portal_url}", fg=typer.colors.CYAN)
    typer.echo(f"  (Requires Supabase membership in client '{client or '<none>'}'.)\n")
    typer.echo("  Artifacts on disk:")
    typer.echo(f"    {_rel_or_abs(html)}")
    if pdf.exists():
        typer.echo(f"    {_rel_or_abs(pdf)}")
    if png.exists():
        typer.echo(f"    {_rel_or_abs(png)}")


@app.command("detect-meta-patterns")
def detect_meta_patterns(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON here"),
    min_lanes: int = typer.Option(1, help="Min distinct lanes for a pattern to emit"),
    min_fixtures: int = typer.Option(2, help="Min distinct fixtures for a pattern to emit"),
) -> None:
    """Walk archive/v*/sessions/* and emit cross-lane meta-patterns (spec A9)."""
    script_candidates = [
        _ARCHIVE_ROOT / "current_runtime" / "scripts" / "detect_meta_patterns.py",
        _ARCHIVE_ROOT / "v009" / "scripts" / "detect_meta_patterns.py",
    ]
    script = next((p for p in script_candidates if p.exists()), None)
    if not script:
        typer.secho("detect_meta_patterns.py not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    cmd = [_resolve_python(), str(script), "--all-lanes",
           "--min-lanes", str(min_lanes), "--min-fixtures", str(min_fixtures)]
    if output:
        cmd += ["-o", str(output)]
    rc = subprocess.run(cmd, cwd=_REPO_ROOT).returncode
    if rc != 0:
        raise typer.Exit(rc)


if __name__ == "__main__":
    app()
