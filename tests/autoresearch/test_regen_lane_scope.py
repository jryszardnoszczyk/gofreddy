"""Regression tests for Finding #115: cross-lane regen_program_docs writes.

When evolution clones a parent for an x_engine (or linkedin_engine) variant,
``regen_program_docs.regen()`` used to iterate over EVERY known
session-md filename. If the AUTOGEN block in any other lane's session-md
had drifted between the parent's clone and now (e.g. v008's
``geo-session.md`` AUTOGEN block diverging from what ``_build_block``
produces today), regen would silently rewrite it — surfacing in lineage
as a phantom cross-lane edit (``changed_files: ['programs/geo-session.md']``
on an x_engine variant). The fix accepts a ``lane`` argument and only
regenerates that lane's session-md.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_regen():
    spec = importlib.util.spec_from_file_location(
        "regen_program_docs_under_test",
        Path(__file__).resolve().parents[2]
        / "autoresearch"
        / "regen_program_docs.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def programs_dir(tmp_path: Path) -> Path:
    """Create a programs/ dir with stub session-md files for several lanes."""
    pdir = tmp_path / "programs"
    pdir.mkdir()
    regen = _load_regen()
    # Seed each known session-md with a marker AUTOGEN block + a unique
    # body line we can use to detect rewrites.
    for domain, filename in regen.DOMAIN_FILENAMES.items():
        target = pdir / filename
        target.write_text(
            f"# {domain} session\n\n"
            f"sentinel-line-{domain}\n\n"
            f"{regen.START_MARKER}\n- stale\n{regen.END_MARKER}\n",
            encoding="utf-8",
        )
    return pdir


def test_regen_with_lane_only_rewrites_that_lane(programs_dir: Path) -> None:
    regen = _load_regen()
    before = {p.name: p.read_text(encoding="utf-8") for p in programs_dir.iterdir()}

    results = regen.regen(programs_dir, lane="x_engine")

    # Only x_engine's filename should appear in the results dict.
    assert list(results.keys()) == [regen.DOMAIN_FILENAMES["x_engine"]]
    # Every other session-md must be byte-identical to its pre-regen state.
    for name, content in before.items():
        if name == regen.DOMAIN_FILENAMES["x_engine"]:
            continue
        after = (programs_dir / name).read_text(encoding="utf-8")
        assert after == content, (
            f"regen(lane='x_engine') wrote to {name} — cross-lane bleed "
            f"that Finding #115 specifically prohibits"
        )


def test_regen_no_lane_rewrites_all(programs_dir: Path) -> None:
    """Default behavior (no lane filter) still regenerates every lane —
    used by run.py bootstrap which doesn't know which lane will run."""
    regen = _load_regen()
    results = regen.regen(programs_dir, lane=None)
    # All known domains with present files should appear in results.
    assert set(results.keys()) == set(regen.DOMAIN_FILENAMES.values())


def test_regen_with_unknown_lane_falls_back_to_all(programs_dir: Path) -> None:
    """An unrecognized lane name shouldn't silently no-op — fall back to
    the full sweep so misconfigured callers don't ship variants with
    stale AUTOGEN blocks."""
    regen = _load_regen()
    results = regen.regen(programs_dir, lane="not_a_real_lane")
    assert set(results.keys()) == set(regen.DOMAIN_FILENAMES.values())
