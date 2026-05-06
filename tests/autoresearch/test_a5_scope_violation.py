"""G4 (review of d128a5c, finding #8): real ScopeViolation coverage for sync_variant_workspace.

The conftest in this directory stubs ``archive_index``, ``frontier``,
``lane_paths``, and ``lane_runtime`` with no-op lambdas so most tests don't
pull in the full module graph. The A5 ``ScopeViolation`` enforcement lives
in ``archive_index.sync_variant_workspace`` and must be exercised
end-to-end (creating files, computing hashes, raising on mutation /
deletion / creation), so this test file uses the REAL ``archive_index``.

To do that without the cascade of stubbed dependencies, we shim
``frontier`` / ``lane_paths`` / ``lane_runtime`` with the minimum names
``archive_index`` needs at import. The real ``path_owned_by_lane`` is
loaded from disk so the geo-lane ownership semantics that
``sync_variant_workspace`` relies on are real (``workflows/geo.py`` and
``programs/geo-session.md`` register as owned by the geo lane).

The fixture is per-test so other tests in this directory keep using the
conftest stub. Module-level state is reset on teardown to avoid
cross-test pollution.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

_AUTORESEARCH = Path(__file__).resolve().parents[2] / "autoresearch"


@pytest.fixture()
def real_archive_index(monkeypatch: pytest.MonkeyPatch):
    """Reload ``archive_index`` with the real code (not the conftest stub)
    plus minimal real-shaped ``frontier`` / ``lane_paths`` / ``lane_runtime``
    shims. Scoped per test so other tests in the directory are unaffected
    — pytest's monkeypatch undoes the ``sys.modules`` writes on teardown.
    """
    # Drop the conftest stubs for the module graph we're about to reload.
    for mod_name in (
        "archive_index", "frontier", "lane_paths", "lane_runtime",
    ):
        monkeypatch.delitem(sys.modules, mod_name, raising=False)

    # Build minimal real-shaped shims for frontier. archive_index imports
    # these names but ``sync_variant_workspace`` itself doesn't call them
    # — they're used by other archive_index functions. Set up no-op
    # callables shaped like the real ones.
    frontier = types.ModuleType("frontier")
    frontier.DOMAINS = ("geo", "competitive", "monitoring", "storyboard")
    frontier.LANES = ("core", "geo", "competitive", "monitoring", "storyboard")
    frontier.best_variant_in_lane = lambda *a, **k: None
    frontier.composite_score = lambda entry: 0.0
    frontier.domain_score = lambda entry, lane: 0.0
    frontier.entry_lane = lambda entry: "core"
    frontier.has_search_metrics = lambda entry: False
    frontier.objective_score = lambda entry, lane: 0.0
    monkeypatch.setitem(sys.modules, "frontier", frontier)

    # lane_paths needs the REAL path_owned_by_lane. Load the real module
    # from disk under a different name and bridge the function over so
    # the geo-lane ownership check inside sync_variant_workspace works.
    lane_paths = types.ModuleType("lane_paths")
    lane_paths.WORKFLOW_LANES = ("geo", "competitive", "monitoring", "storyboard")
    lane_paths.normalize_lane = lambda x: x

    real_lane_paths_path = _AUTORESEARCH / "lane_paths.py"
    spec = importlib.util.spec_from_file_location(
        "lane_paths_real_g4", real_lane_paths_path
    )
    real_mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(real_mod)
    lane_paths.path_owned_by_lane = real_mod.path_owned_by_lane
    monkeypatch.setitem(sys.modules, "lane_paths", lane_paths)

    # lane_runtime is also stubbed by conftest. Provide just
    # load_current_manifest — the only symbol archive_index imports.
    lane_runtime = types.ModuleType("lane_runtime")
    lane_runtime.load_current_manifest = lambda archive_dir: None
    monkeypatch.setitem(sys.modules, "lane_runtime", lane_runtime)

    # Now load the real archive_index from disk.
    spec = importlib.util.spec_from_file_location(
        "archive_index", _AUTORESEARCH / "archive_index.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "archive_index", mod)
    spec.loader.exec_module(mod)
    return mod


def _make_variant(
    root: Path, *, geo_workflow_body: str | None, geo_session_body: str = "session prog\n"
) -> Path:
    """Build a variant directory shaped like a real autoresearch variant.

    ``programs/geo-session.md`` is the editable mutation-target; it's
    always present so the variant exists even when the readonly workflow
    file is missing. ``workflows/geo.py`` is created only if
    ``geo_workflow_body`` is not None — that's the readonly file under
    test.
    """
    variant = root / "v_test"
    (variant / "programs").mkdir(parents=True)
    (variant / "programs" / "geo-session.md").write_text(geo_session_body)
    (variant / "workflows").mkdir(parents=True)
    if geo_workflow_body is not None:
        (variant / "workflows" / "geo.py").write_text(geo_workflow_body)
    return variant


def test_sync_variant_workspace_rejects_workflow_edit(
    real_archive_index, tmp_path: Path
) -> None:
    """G4: meta-agent edited ``workflows/geo.py`` (readonly for the geo
    lane) — sync raises ``ScopeViolation`` mentioning the file."""
    import lane_registry

    # Pre-mutation (target) state: original workflow body.
    target = _make_variant(
        tmp_path / "target", geo_workflow_body="ORIGINAL\n"
    )
    # Post-mutation (source) state: meta-agent edited the workflow body.
    source = _make_variant(
        tmp_path / "source", geo_workflow_body="MUTATED\n"
    )

    with pytest.raises(lane_registry.ScopeViolation, match="workflows/geo.py"):
        real_archive_index.sync_variant_workspace(source, target, lane="geo")


def test_sync_variant_workspace_accepts_unchanged_workflow(
    real_archive_index, tmp_path: Path
) -> None:
    """G4 negative: identical bytes for the readonly workflow file → no
    violation. The hash check is the only gate, so byte-equal contents
    must pass."""
    body = "from autoresearch.workflows.specs import WorkflowSpec\n"
    target = _make_variant(tmp_path / "target", geo_workflow_body=body)
    source = _make_variant(tmp_path / "source", geo_workflow_body=body)
    real_archive_index.sync_variant_workspace(source, target, lane="geo")


def test_sync_variant_workspace_rejects_workflow_deletion(
    real_archive_index, tmp_path: Path
) -> None:
    """G4: meta-agent deleted ``workflows/geo.py`` (readonly for the geo
    lane) — sync raises ``ScopeViolation`` mentioning ``deleted``.

    Source = post-mutation (the meta-agent's workspace) — workflow file
    is missing.
    Target = pre-mutation (the original variant_dir) — workflow file
    is present.
    Per ``sync_variant_workspace`` semantics, this is a delete.
    """
    import lane_registry

    target = _make_variant(tmp_path / "target", geo_workflow_body="ok\n")
    source = _make_variant(tmp_path / "source", geo_workflow_body=None)

    with pytest.raises(lane_registry.ScopeViolation, match="deleted"):
        real_archive_index.sync_variant_workspace(source, target, lane="geo")


def test_sync_variant_workspace_rejects_workflow_creation(
    real_archive_index, tmp_path: Path
) -> None:
    """G4: meta-agent created ``workflows/geo.py`` where the original
    variant had none — sync raises ``ScopeViolation`` mentioning
    ``created``."""
    import lane_registry

    # Target (pre-mutation) has no workflow file.
    target = _make_variant(tmp_path / "target", geo_workflow_body=None)
    # Source (post-mutation) has a fresh workflow file.
    source = _make_variant(tmp_path / "source", geo_workflow_body="NEW\n")

    with pytest.raises(lane_registry.ScopeViolation, match="created"):
        real_archive_index.sync_variant_workspace(source, target, lane="geo")


def test_sync_variant_workspace_rejects_shared_infra_edit_on_core(
    real_archive_index, tmp_path: Path
) -> None:
    """G4 + G1: shared workflow infra (``workflows/__init__.py``) is
    readonly for ALL lanes via ``SHARED_WORKFLOW_READONLY``. The
    realistic attack vector is a CORE-lane mutation (``core`` owns
    ``workflows/__init__.py`` because no workflow lane claims it) that
    monkey-patches the shared module so every workflow lane's holdout
    silently inherits the contamination.

    Pre-G1, ``core`` had an empty ``readonly_subprefixes`` so the
    sync gate did nothing. G1 added ``SHARED_WORKFLOW_READONLY`` and
    wired it into ``path_is_readonly``. This test pins that wiring
    end-to-end through ``sync_variant_workspace``.

    (For workflow lanes like ``geo``, the same sync of
    ``workflows/__init__.py`` is filtered out earlier by
    ``path_owned_by_lane`` — the file simply isn't part of the geo
    lane's owned tree, so the sync ignores it. The test below uses
    ``lane='core'`` where ownership matches and the readonly check
    actually fires.)
    """
    import lane_registry

    target = tmp_path / "target" / "v_test"
    (target / "workflows").mkdir(parents=True)
    (target / "workflows" / "__init__.py").write_text("# original shared infra\n")

    source = tmp_path / "source" / "v_test"
    (source / "workflows").mkdir(parents=True)
    (source / "workflows" / "__init__.py").write_text("# MUTATED shared infra\n")

    with pytest.raises(
        lane_registry.ScopeViolation, match="workflows/__init__.py"
    ):
        real_archive_index.sync_variant_workspace(source, target, lane="core")


def test_sync_variant_workspace_accepts_editable_change(
    real_archive_index, tmp_path: Path
) -> None:
    """G4: edits to non-readonly paths owned by the lane (e.g.,
    ``programs/geo-session.md``, the actual mutation target) are allowed
    — the gate fires only on readonly subprefixes."""
    target = _make_variant(
        tmp_path / "target",
        geo_workflow_body="frozen\n",
        geo_session_body="ORIGINAL session\n",
    )
    source = _make_variant(
        tmp_path / "source",
        geo_workflow_body="frozen\n",  # readonly file unchanged
        geo_session_body="MUTATED session — meta-agent edit OK\n",
    )

    # Should NOT raise — programs/geo-session.md is the editable target.
    real_archive_index.sync_variant_workspace(source, target, lane="geo")

    # Verify the edit actually propagated to target.
    assert (
        (target / "programs" / "geo-session.md").read_text()
        == "MUTATED session — meta-agent edit OK\n"
    )
