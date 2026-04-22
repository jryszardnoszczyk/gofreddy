"""Tests for producer-owned evaluation-scope YAML loading (R-#40).

Replaces the deleted ``_DOMAIN_FILE_PATTERNS`` dispatch. Each domain's
scored-artifact set now lives in
``<variant>/programs/<domain>-evaluation-scope.yaml``; these tests verify
the YAML loader walks up from session_dir correctly, fails loud on a
missing YAML, and that the glob walker selects the right files while
the inline ``competitors/_client_baseline.json`` carve-out still applies.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from cli.freddy.commands.evaluate import (
    _load_evaluation_scope,
    _read_files_from_scope,
)
from cli.freddy.main import app


runner = CliRunner()


# ─── _load_evaluation_scope ───────────────────────────────────────────────


def _write_scope_yaml(programs_dir: Path, domain: str, payload: dict) -> Path:
    programs_dir.mkdir(parents=True, exist_ok=True)
    path = programs_dir / f"{domain}-evaluation-scope.yaml"
    path.write_text(yaml.safe_dump(payload))
    return path


def test_load_scope_returns_dict_with_expected_keys(tmp_path: Path) -> None:
    variant = tmp_path / "v007"
    programs = variant / "programs"
    session = variant / "sessions" / "competitive" / "client-x"
    session.mkdir(parents=True)

    payload = {
        "domain": "competitive",
        "outputs": ["brief.md", "competitors/*.json"],
        "source_data": ["competitors/_client_baseline.json", "session.md"],
        "transient": ["logs/**/*"],
        "notes": "Test note.",
    }
    _write_scope_yaml(programs, "competitive", payload)

    scope = _load_evaluation_scope("competitive", session)
    assert scope["domain"] == "competitive"
    assert scope["outputs"] == ["brief.md", "competitors/*.json"]
    assert scope["source_data"] == [
        "competitors/_client_baseline.json",
        "session.md",
    ]
    assert scope["transient"] == ["logs/**/*"]


def test_load_scope_missing_yaml_raises_file_not_found(tmp_path: Path) -> None:
    variant = tmp_path / "v007"
    session = variant / "sessions" / "geo" / "client-x"
    session.mkdir(parents=True)
    # No programs/ dir, no YAML → must fail loud.
    with pytest.raises(FileNotFoundError, match="evaluation-scope YAML missing"):
        _load_evaluation_scope("geo", session)


def test_load_scope_walks_up_multiple_levels(tmp_path: Path) -> None:
    """Loader must walk from session_dir upward until it finds programs/."""
    variant = tmp_path / "v007"
    programs = variant / "programs"
    deep_session = variant / "sessions" / "storyboard" / "client" / "iter3"
    deep_session.mkdir(parents=True)

    _write_scope_yaml(
        programs,
        "storyboard",
        {
            "domain": "storyboard",
            "outputs": ["stories/*.json"],
            "source_data": [],
            "transient": [],
            "notes": "",
        },
    )

    scope = _load_evaluation_scope("storyboard", deep_session)
    assert scope["domain"] == "storyboard"


# ─── _read_files_from_scope (glob walker) ─────────────────────────────────


def test_glob_walker_selects_outputs_and_excludes_transient(tmp_path: Path) -> None:
    session = tmp_path / "session"
    (session / "stories").mkdir(parents=True)
    (session / "storyboards").mkdir(parents=True)
    (session / "logs").mkdir(parents=True)

    # Files in scope (outputs)
    (session / "stories" / "s1.json").write_text('{"id": 1}')
    (session / "storyboards" / "sb1.json").write_text('{"id": "a"}')
    # Transient file (NOT globbed by outputs/source_data — should be absent)
    (session / "logs" / "debug.log").write_text("noise")
    # A file outside the glob pattern — should also be absent
    (session / "unrelated.txt").write_text("x")

    outputs = _read_files_from_scope(
        session,
        ["stories/*.json", "storyboards/*.json"],
        is_source_data=False,
    )
    assert set(outputs.keys()) == {"stories/s1.json", "storyboards/sb1.json"}
    # Transient + unrelated must NOT appear
    assert "logs/debug.log" not in outputs
    assert "unrelated.txt" not in outputs


def test_glob_walker_preserves_client_baseline_exception(tmp_path: Path) -> None:
    """competitors/_client_baseline.json survives the underscore-skip.

    Other underscore-prefixed competitor files (scratch/work artifacts) must
    be dropped when reading source_data for the competitive domain.
    """
    session = tmp_path / "session"
    (session / "competitors").mkdir(parents=True)
    (session / "competitors" / "_client_baseline.json").write_text('{"client": "x"}')
    (session / "competitors" / "_ads_scratch.json").write_text('{"scratch": true}')
    (session / "competitors" / "acme.json").write_text('{"name": "acme"}')

    source_data = _read_files_from_scope(
        session,
        ["competitors/_client_baseline.json", "competitors/*.json"],
        is_source_data=True,
    )
    # Baseline (explicit) + acme (via *.json) in; scratch file filtered out.
    assert "competitors/_client_baseline.json" in source_data
    assert "competitors/acme.json" in source_data
    assert "competitors/_ads_scratch.json" not in source_data


def test_glob_walker_exact_path_pattern(tmp_path: Path) -> None:
    session = tmp_path / "session"
    session.mkdir()
    (session / "brief.md").write_text("# Brief")

    outputs = _read_files_from_scope(
        session, ["brief.md"], is_source_data=False
    )
    assert outputs == {"brief.md": "# Brief"}


# ─── End-to-end: variant command fails loud when YAML missing ─────────────


def test_variant_command_fails_loud_on_missing_scope_yaml(tmp_path: Path) -> None:
    """freddy evaluate variant must error (not silently skip) if YAML absent."""
    session = tmp_path / "sessions" / "geo" / "client-x"
    session.mkdir(parents=True)
    (session / "optimized").mkdir()
    (session / "optimized" / "page.md").write_text("# Optimized")

    # No programs/ dir anywhere up the tree → missing YAML.
    with patch("cli.freddy.api.make_client") as mock_make_client:
        mock_make_client.return_value = MagicMock()
        result = runner.invoke(
            app,
            ["evaluate", "variant", "geo", str(session)],
        )

    assert result.exit_code != 0
    output = json.loads(result.stdout.strip())
    assert "error" in output
    assert "evaluation-scope YAML missing" in output["error"]


def test_variant_command_reads_yaml_and_calls_backend(tmp_path: Path) -> None:
    """YAML-driven path: loader finds YAML, glob walks, backend gets outputs."""
    variant = tmp_path / "v007"
    programs = variant / "programs"
    session = variant / "sessions" / "geo" / "client-x"
    session.mkdir(parents=True)
    (session / "optimized").mkdir()
    (session / "optimized" / "page.md").write_text("# Optimized page")
    (session / "pages").mkdir()
    (session / "pages" / "page.json").write_text('{"url": "x"}')

    _write_scope_yaml(
        programs,
        "geo",
        {
            "domain": "geo",
            "outputs": ["optimized/*.md"],
            "source_data": ["pages/*.json"],
            "transient": [],
            "notes": "",
        },
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"domain_score": 7.5}
    mock_client.request.return_value = mock_response

    with patch("cli.freddy.api.make_client", return_value=mock_client):
        result = runner.invoke(
            app,
            ["evaluate", "variant", "geo", str(session)],
        )

    assert result.exit_code == 0, result.stdout
    request_body = mock_client.request.call_args.kwargs["json"]
    assert request_body["domain"] == "geo"
    assert "optimized/page.md" in request_body["outputs"]
    assert "pages/page.json" in request_body["source_data"]
