"""--single-fixture / --seeds / --json-output CLI surface on evaluate_variant.py.

The subprocess-callable interface Plan A Phase 7 specified. The in-process
callable is exercised by test_evaluate_single_fixture.py; this test pins
the CLI contract so `python autoresearch/evaluate_variant.py
--single-fixture <pool>:<fid> --manifest ... --seeds N --json-output`
still works.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_single_fixture_cli_rejects_bad_format(tmp_path):
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "autoresearch" / "evaluate_variant.py"),
         "--single-fixture", "missing-colon"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "<pool>:<fixture_id>" in (result.stderr + result.stdout)


def test_single_fixture_cli_rejects_missing_manifest():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "autoresearch" / "evaluate_variant.py"),
         "--single-fixture", "search-v1:geo-a"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "--manifest" in (result.stderr + result.stdout)


def test_search_mode_still_requires_positional_args():
    """Non --single-fixture mode still requires variant_dir + archive_dir + --search-suite."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "autoresearch" / "evaluate_variant.py")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    err = result.stderr + result.stdout
    assert "variant_dir" in err or "required" in err.lower()


def test_single_fixture_cli_invokes_entry_point(tmp_path, monkeypatch):
    """With valid args, the CLI should reach evaluate_single_fixture.

    We patch the symbol to short-circuit the real session execution.
    """
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({
        "suite_id": "search-v1", "version": "1.0",
        "domains": {"geo": [
            {"fixture_id": "geo-a", "client": "c", "context": "https://x.com",
             "version": "1.0", "env": {}},
        ]},
    }))
    # Use a wrapper-script approach: patch via PYTHONPATH sitecustomize.
    # Simpler: import the module and call main() directly with sys.argv swap.
    import autoresearch.evaluate_variant as ev

    calls = {}

    def _fake(fixture_id, *, manifest_path, pool, baseline, seeds, cache_root):
        calls["fixture_id"] = fixture_id
        calls["manifest_path"] = manifest_path
        calls["pool"] = pool
        calls["baseline"] = baseline
        calls["seeds"] = seeds
        return {"per_seed_scores": [0.5, 0.6], "structural_passed": True,
                "cost_usd": 0.0, "duration_seconds": 1}

    # Production contract: --single-fixture preflights EVOLUTION_INVOKE_TOKEN
    # so empty/missing tokens fail before burning ~25min per fixture
    # (instead of bubbling httpx "Bearer " illegal-header errors). Set a
    # placeholder so the entry point is reached.
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "test-token-stub")
    monkeypatch.setattr(ev, "evaluate_single_fixture", _fake)
    monkeypatch.setattr(
        sys, "argv",
        ["evaluate_variant.py",
         "--single-fixture", "search-v1:geo-a",
         "--manifest", str(manifest),
         "--seeds", "2",
         "--baseline-variant", "v006",
         "--cache-root", str(tmp_path / "cache"),
         "--json-output"],
    )
    import io
    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    ev.main()
    assert calls["fixture_id"] == "geo-a"
    assert calls["pool"] == "search-v1"
    assert calls["seeds"] == 2
    assert calls["baseline"] == "v006"
    # Output is JSON with per_seed_scores
    out = json.loads(buf.getvalue())
    assert out["per_seed_scores"] == [0.5, 0.6]


def test_single_fixture_cli_auto_materializes_current_runtime(tmp_path, monkeypatch):
    """Regression: ``--single-fixture`` must materialize ``current_runtime/``
    before dispatching, mirroring ``evolve.py:cmd_run``. Without it,
    fresh-worktree invocations crash with cryptic "Error: No such file or
    directory (os error 2)" because the per-fixture runner cd's into
    ``archive/current_runtime`` (gitignored, missing on first checkout).

    Caught 2026-05-08 on stripe-docs-payments validation: the agent had
    to manually ``cp -R archive/v006 archive/current_runtime`` before any
    fixture would run. evolve.py auto-materializes; this is the equivalent
    for direct/CLI invocations.
    """
    import autoresearch.evaluate_variant as ev

    # Set up a minimal archive with a lane manifest pointing at a real
    # variant dir, so has_lane_manifest -> True and ensure_materialized_runtime
    # has something to copy from.
    archive_dir = tmp_path / "archive"
    variant_dir = archive_dir / "v006"
    (variant_dir / "programs").mkdir(parents=True)
    (variant_dir / "workflows").mkdir(parents=True)
    (variant_dir / "scripts").mkdir(parents=True)
    (variant_dir / "templates").mkdir(parents=True)
    (variant_dir / "programs" / "geo-session.md").write_text("test")
    (variant_dir / "workflows" / "__init__.py").write_text("")
    # current.json points all lanes at v006 (the legacy single-promoted shape).
    import json as _json
    (archive_dir / "current.json").write_text(_json.dumps({
        "core": "v006", "geo": "v006", "competitive": "v006",
        "monitoring": "v006", "storyboard": "v006", "marketing_audit": "v006",
        "x_engine": "v006", "linkedin_engine": "v006",
    }))
    # lineage.jsonl with a single entry so the manifest passes shape checks.
    (archive_dir / "lineage.jsonl").write_text(_json.dumps({
        "id": "v006", "lane": "core", "parent": None,
        "timestamp": "2026-04-01T00:00:00+00:00",
    }) + "\n")

    manifest = tmp_path / "m.json"
    manifest.write_text(_json.dumps({
        "suite_id": "search-v1", "version": "1.0",
        "domains": {"geo": [
            {"fixture_id": "geo-a", "client": "c", "context": "https://x.com",
             "version": "1.0", "env": {}},
        ]},
    }))

    def _fake(fixture_id, *, manifest_path, pool, baseline, seeds, cache_root):
        return {"per_seed_scores": [0.5], "structural_passed": True,
                "cost_usd": 0.0, "duration_seconds": 1}

    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "test-token-stub")
    monkeypatch.setattr(ev, "evaluate_single_fixture", _fake)
    monkeypatch.setattr(
        sys, "argv",
        ["evaluate_variant.py",
         "--single-fixture", "search-v1:geo-a",
         "--manifest", str(manifest),
         "--seeds", "1",
         "--baseline-variant", "v006",
         "--cache-root", str(tmp_path / "cache"),
         str(variant_dir),  # variant_dir positional
         str(archive_dir),  # archive_dir positional — drives _ensure_runtime_materialized
         ],
    )

    import io
    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    ev.main()

    # Verify current_runtime/ was auto-materialized before dispatch.
    assert (archive_dir / "current_runtime").is_dir(), (
        "current_runtime/ must be materialized before single-fixture dispatch"
    )
