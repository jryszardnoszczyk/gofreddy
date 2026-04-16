from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import archive_index
import evaluate_variant
import frontier


def _search_manifest() -> dict:
    return json.loads((AUTORESEARCH_DIR / "eval_suites" / "search-v1.json").read_text())


def test_search_promotion_summary_marks_search_scored_without_holdout() -> None:
    summary = evaluate_variant._search_promotion_summary(
        variant_entry={"id": "v002"},
        baseline_entry=None,
        search_suite_manifest=_search_manifest(),
        policy={"promotion": {"require_holdout": False}},
    )
    assert summary == {"eligible_for_promotion": True, "reason": "search_scored"}


def test_search_promotion_summary_requires_holdout_when_configured() -> None:
    summary = evaluate_variant._search_promotion_summary(
        variant_entry={"id": "v002"},
        baseline_entry=None,
        search_suite_manifest=_search_manifest(),
        policy={"promotion": {"require_holdout": True}},
    )
    assert summary == {"eligible_for_promotion": False, "reason": "holdout_required"}


def test_hidden_holdout_promotion_requires_strict_composite_improvement() -> None:
    baseline_entry = {"id": "v001"}

    eligible, reason = evaluate_variant._eligible_for_promotion(
        baseline_entry=baseline_entry,
        holdout_scores={"composite": 0.61},
        baseline_holdout_scores={"composite": 0.60},
    )
    assert eligible is True
    assert reason == "holdout_passed"

    eligible, reason = evaluate_variant._eligible_for_promotion(
        baseline_entry=baseline_entry,
        holdout_scores={"composite": 0.60},
        baseline_holdout_scores={"composite": 0.60},
    )
    assert eligible is False
    assert reason == "holdout_not_better_than_baseline"


def test_private_holdout_cache_requires_matching_suite_id(tmp_path: Path, monkeypatch) -> None:
    private_dir = tmp_path / "private"
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_dir))

    result_dir = private_dir / "v001"
    result_dir.mkdir(parents=True)
    (result_dir / "holdout_result.json").write_text(
        json.dumps(
            {
                "variant_id": "v001",
                "suite_id": "holdout-v1",
                "scores": {"composite": 0.55},
            }
        )
    )

    cached = evaluate_variant._load_private_holdout_result("v001", "holdout-v1")
    assert cached is not None
    assert cached["scores"]["composite"] == 0.55

    assert evaluate_variant._load_private_holdout_result("v001", "holdout-v2") is None


def test_private_holdout_cache_defaults_outside_repo_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", raising=False)
    expected = Path(tempfile.gettempdir()).resolve() / "autoresearch-holdouts"
    assert evaluate_variant._private_holdout_root() == expected


def test_promotion_baseline_uses_lane_specific_current_head(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "current.json").write_text(
        json.dumps(
            {
                "core": "v001",
                "geo": "v002",
                "competitive": "v003",
                "monitoring": "v004",
                "storyboard": "v005",
            }
        )
        + "\n"
    )
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"id": "v001", "lane": "core", "search_metrics": {"suite_id": "search-v1", "composite": 0.4}}),
                json.dumps({"id": "v002", "lane": "geo", "search_metrics": {"suite_id": "search-v1", "composite": 0.3, "domains": {"geo": {"score": 0.9}}}}),
                json.dumps({"id": "v003", "lane": "competitive", "search_metrics": {"suite_id": "search-v1", "composite": 0.2}}),
            ]
        )
        + "\n"
    )

    baseline = evaluate_variant._promotion_baseline(archive_dir, "v999", "geo")

    assert baseline is not None
    assert baseline["id"] == "v002"

def test_public_archive_summary_redacts_holdout_and_promotion_metadata(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    variant_dir = archive_dir / "v002"
    variant_dir.mkdir(parents=True)

    entry = {
        "id": "v002",
        "parent": "v001",
        "timestamp": "2026-04-01T12:00:00+00:00",
        "backend": "codex",
        "model": "gpt-5.4",
        "eval_target": {"backend": "codex", "model": "gpt-5.4", "reasoning_effort": "high"},
        "scores": {
            "geo": 0.51,
            "competitive": 0.49,
            "monitoring": 0.47,
            "storyboard": 0.50,
            "composite": 0.4925,
        },
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": 0.4925,
            "api_cost_estimate": 12.4,
            "wall_time_seconds": 180.0,
            "domains": {},
        },
        "holdout_metrics": {
            "ran": True,
            "suite_id": "holdout-private-v1",
            "domains": {"geo": 0.9},
        },
        "suite_versions": {
            "search": "search-v1",
            "holdout": "holdout-private-v1",
        },
        "campaign_ids": {
            "search": "search-v1:v002",
            "holdout": "holdout-private-v1:v002",
        },
        "promotion_summary": {
            "eligible_for_promotion": False,
            "reason": "holdout_required",
        },
    }

    public_summary = archive_index.public_entry_summary(archive_dir, entry)
    encoded = json.dumps(public_summary)

    assert "holdout-private-v1" not in encoded
    assert "promotion_summary" not in public_summary
    assert "promoted_at" not in public_summary
    assert "campaign_ids" not in public_summary
    assert public_summary["search_summary"]["composite"] == 0.4925


def test_prepare_meta_workspace_exposes_search_only_archive_snapshot(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    workspace_root = tmp_path / "workspace"
    variant_dir = archive_dir / "v002"
    variant_dir.mkdir(parents=True)
    other_dir = archive_dir / "v001"
    other_dir.mkdir(parents=True)
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"id": "v001", "timestamp": "2026-04-01T00:00:00+00:00"}),
                json.dumps({"id": "v002", "timestamp": "2026-04-01T01:00:00+00:00"}),
            ]
        )
        + "\n"
    )
    (archive_dir / "current").symlink_to("v001")
    (archive_dir / "index.json").write_text("{}\n")
    (archive_dir / "frontier.json").write_text("{}\n")
    (variant_dir / "meta.md").write_text("prompt\n")
    (other_dir / "run.py").write_text("print('ok')\n")

    visible_root, variant_workspace = archive_index.prepare_meta_workspace(
        archive_dir=archive_dir,
        variant_id="v002",
        workspace_root=workspace_root,
    )

    assert visible_root == workspace_root / "archive"
    assert variant_workspace == visible_root / "v002"
    assert (visible_root / "index.json").exists()
    assert (visible_root / "frontier.json").exists()
    assert (visible_root / "v001" / "run.py").exists()
    assert not (visible_root / "lineage.jsonl").exists()
    assert not (visible_root / "current").exists()


def test_prepare_meta_workspace_prunes_non_owned_paths_for_lane_workspace(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    workspace_root = tmp_path / "workspace"
    variant_dir = archive_dir / "v002"
    variant_dir.mkdir(parents=True)
    (archive_dir / "lineage.jsonl").write_text(json.dumps({"id": "v002", "timestamp": "2026-04-01T01:00:00+00:00"}) + "\n")
    (archive_dir / "index.json").write_text("{}\n")
    (archive_dir / "frontier.json").write_text("{}\n")
    (variant_dir / "meta.md").write_text("prompt\n")
    (variant_dir / "run.py").write_text("print('shared')\n")
    (variant_dir / "programs").mkdir()
    (variant_dir / "programs" / "geo-session.md").write_text("geo prompt\n")
    (variant_dir / "programs" / "competitive-session.md").write_text("competitive prompt\n")
    (variant_dir / "templates" / "geo").mkdir(parents=True)
    (variant_dir / "templates" / "geo" / "brief.md").write_text("geo template\n")

    _visible_root, variant_workspace = archive_index.prepare_meta_workspace(
        archive_dir=archive_dir,
        variant_id="v002",
        workspace_root=workspace_root,
        lane="geo",
    )

    assert (variant_workspace / "meta.md").exists()
    assert not (variant_workspace / "run.py").exists()
    assert (variant_workspace / "programs" / "geo-session.md").exists()
    assert not (variant_workspace / "programs" / "competitive-session.md").exists()


def test_sync_variant_workspace_propagates_edits_and_deletions(tmp_path: Path) -> None:
    source_variant_dir = tmp_path / "source"
    target_variant_dir = tmp_path / "target"
    (source_variant_dir / "scripts").mkdir(parents=True)
    (target_variant_dir / "scripts").mkdir(parents=True)
    (source_variant_dir / "run.py").write_text("print('new')\n")
    (source_variant_dir / "scripts" / "helper.py").write_text("HELPER = 1\n")
    (target_variant_dir / "run.py").write_text("print('old')\n")
    (target_variant_dir / "obsolete.py").write_text("print('remove')\n")
    (target_variant_dir / "meta-session.log").write_text("keep local log\n")

    archive_index.sync_variant_workspace(source_variant_dir, target_variant_dir)

    assert (target_variant_dir / "run.py").read_text() == "print('new')\n"
    assert (target_variant_dir / "scripts" / "helper.py").exists()
    assert not (target_variant_dir / "obsolete.py").exists()
    assert (target_variant_dir / "meta-session.log").read_text() == "keep local log\n"


def test_refresh_archive_outputs_keeps_lane_views_logical_only(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    for variant_id in ("v001", "v002"):
        variant_dir = archive_dir / variant_id
        variant_dir.mkdir()
        (variant_dir / "run.py").write_text(f"# {variant_id}\n")
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "v001",
                        "lane": "core",
                        "timestamp": "2026-04-01T00:00:00+00:00",
                        "search_metrics": {
                            "suite_id": "search-v1",
                            "composite": 0.8,
                            "api_cost_estimate": 2.0,
                            "wall_time_seconds": 20.0,
                            "domains": {domain: {"score": 0.8} for domain in frontier.DOMAINS},
                        },
                    }
                ),
                json.dumps(
                    {
                        "id": "v002",
                        "lane": "geo",
                        "timestamp": "2026-04-01T01:00:00+00:00",
                        "search_metrics": {
                            "suite_id": "search-v1",
                            "objective_domain": "geo",
                            "active_domains": ["geo"],
                            "composite": 0.9,
                            "api_cost_estimate": 1.0,
                            "wall_time_seconds": 10.0,
                            "domains": {
                                "geo": {"score": 0.9, "active": True},
                                "competitive": {"score": 0.0, "active": False},
                                "monitoring": {"score": 0.0, "active": False},
                                "storyboard": {"score": 0.0, "active": False},
                            },
                        },
                    }
                ),
            ]
        )
        + "\n"
    )

    archive_index.refresh_archive_outputs(archive_dir, suite_manifest=_search_manifest())

    # Phase 2 (Unit 4 + 5): frontier.json now stores a single best per lane,
    # not a Pareto member list. Each `lanes[lane]` value is either the summary
    # dict for the best variant or `None`.
    frontier_payload = json.loads((archive_dir / "frontier.json").read_text())
    assert frontier_payload["lanes"]["core"]["id"] == "v001"
    assert frontier_payload["lanes"]["geo"]["id"] == "v002"
    # Lanes with no entries surface as None (not omitted), so the schema is stable.
    assert frontier_payload["lanes"]["competitive"] is None
    assert not (archive_dir / "core").exists()
    assert not (archive_dir / "workflows").exists()


def test_project_suite_manifest_for_workflow_lane_keeps_only_target_domain() -> None:
    manifest = evaluate_variant._project_suite_manifest_for_lane(_search_manifest(), "geo")

    assert manifest["objective_domain"] == "geo"
    assert manifest["active_domains"] == ["geo"]
    assert len(manifest["domains"]["geo"]) > 0
    assert manifest["domains"]["competitive"] == []
    assert manifest["domains"]["monitoring"] == []
    assert manifest["domains"]["storyboard"] == []


def test_load_holdout_manifest_prefers_lane_specific_env_and_projects_to_lane(tmp_path: Path, monkeypatch) -> None:
    manifest_path = tmp_path / "holdout.json"
    manifest_path.write_text(json.dumps(_search_manifest()) + "\n")
    monkeypatch.setenv("EVOLUTION_HOLDOUT_MANIFEST_GEO", str(manifest_path))
    monkeypatch.delenv("EVOLUTION_HOLDOUT_MANIFEST", raising=False)
    monkeypatch.delenv("EVOLUTION_HOLDOUT_JSON", raising=False)

    manifest = evaluate_variant._load_holdout_manifest(dict(os.environ), "geo")

    assert manifest is not None
    assert manifest["objective_domain"] == "geo"
    assert manifest["domains"]["geo"]
    assert manifest["domains"]["competitive"] == []


def test_aggregate_suite_results_uses_only_active_lane_domains() -> None:
    suite_manifest = evaluate_variant._project_suite_manifest_for_lane(_search_manifest(), "geo")
    fixtures_by_domain = {
        domain: [
            evaluate_variant.Fixture(
                suite_id="search-v1",
                domain=domain,
                fixture_id=f"{domain}-fixture",
                client="client",
                context="context",
                max_iter=1,
                timeout=1,
                regression_floor=0.0,
                env={},
            )
        ]
        if domain == "geo"
        else []
        for domain in frontier.DOMAINS
    }
    scored_fixtures = {
        "geo": [{"score": 0.8, "api_cost_estimate": 1.5, "wall_time_seconds": 12.0}],
        "competitive": [{"score": 0.1, "api_cost_estimate": 999.0, "wall_time_seconds": 999.0}],
        "monitoring": [],
        "storyboard": [],
    }

    scores, aggregated = evaluate_variant._aggregate_suite_results(
        suite_manifest,
        fixtures_by_domain,
        scored_fixtures,
    )

    assert scores["geo"] == 0.8
    assert scores["composite"] == 0.8
    assert aggregated["search_metrics"]["objective_domain"] == "geo"
    assert aggregated["search_metrics"]["objective_score"] == 0.8
    assert aggregated["search_metrics"]["active_domains"] == ["geo"]
    assert aggregated["search_metrics"]["domains"]["competitive"]["active"] is False


def test_private_finalize_status_requires_current_baseline_match(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "v001",
                        "promoted_at": "2026-04-01T00:00:00+00:00",
                        "search_metrics": {"suite_id": "search-v1", "composite": 0.60},
                    }
                ),
                json.dumps(
                    {
                        "id": "v002",
                        "search_metrics": {"suite_id": "search-v1", "composite": 0.70},
                    }
                ),
            ]
        )
        + "\n"
    )
    private_dir = tmp_path / "private"
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_dir))
    result_path = private_dir / "v002" / "finalize_result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "variant_id": "v002",
                "suite_id": "holdout-v1",
                "baseline_variant_id": "v000",
                "eligible_for_promotion": True,
                "reason": "holdout_passed",
                "scores": {"composite": 0.75},
            }
        )
    )

    eligible, reason, record = evaluate_variant._private_finalize_status(
        archive_dir=archive_dir,
        variant_id="v002",
        suite_id="holdout-v1",
    )

    assert eligible is False
    assert reason == "baseline_changed"
    assert record is not None


def test_private_finalize_shortlist_is_ranked_and_private(tmp_path: Path, monkeypatch) -> None:
    private_dir = tmp_path / "private"
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_dir))

    shortlist_path = evaluate_variant._write_private_finalized_shortlist(
        suite_id="holdout-v1",
        baseline_variant_id="v001",
        results=[
            {
                "variant_id": "v003",
                "suite_id": "holdout-v1",
                "scores": {"composite": 0.61},
                "eligible_for_promotion": False,
                "reason": "holdout_not_better_than_baseline",
                "evaluated_at": "2026-04-02T00:00:00+00:00",
                "baseline_variant_id": "v001",
                "baseline_holdout_composite": 0.62,
            },
            {
                "variant_id": "v002",
                "suite_id": "holdout-v1",
                "scores": {"composite": 0.70},
                "eligible_for_promotion": True,
                "reason": "holdout_passed",
                "evaluated_at": "2026-04-02T00:00:01+00:00",
                "baseline_variant_id": "v001",
                "baseline_holdout_composite": 0.62,
            },
        ],
    )

    assert shortlist_path is not None
    payload = json.loads(shortlist_path.read_text())
    assert shortlist_path.is_relative_to(private_dir)
    assert payload["baseline_variant_id"] == "v001"
    assert [candidate["variant_id"] for candidate in payload["candidates"]] == ["v002", "v003"]


def test_best_finalized_candidate_uses_shortlist_and_filters_stale_baselines(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "v001",
                        "promoted_at": "2026-04-01T00:00:00+00:00",
                        "search_metrics": {"suite_id": "search-v1", "composite": 0.60},
                    }
                ),
                json.dumps(
                    {
                        "id": "v002",
                        "search_metrics": {"suite_id": "search-v1", "composite": 0.70},
                    }
                ),
                json.dumps(
                    {
                        "id": "v003",
                        "search_metrics": {"suite_id": "search-v1", "composite": 0.80},
                    }
                ),
            ]
        )
        + "\n"
    )
    private_dir = tmp_path / "private"
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_dir))
    (private_dir / "v002").mkdir(parents=True)
    (private_dir / "v003").mkdir(parents=True)
    (private_dir / "v002" / "finalize_result.json").write_text(
        json.dumps(
            {
                "variant_id": "v002",
                "suite_id": "holdout-v1",
                "baseline_variant_id": "v001",
                "scores": {"composite": 0.71},
                "eligible_for_promotion": True,
                "reason": "holdout_passed",
            }
        )
    )
    (private_dir / "v003" / "finalize_result.json").write_text(
        json.dumps(
            {
                "variant_id": "v003",
                "suite_id": "holdout-v1",
                "baseline_variant_id": "v000",
                "scores": {"composite": 0.99},
                "eligible_for_promotion": True,
                "reason": "holdout_passed",
            }
        )
    )
    evaluate_variant._write_private_finalized_shortlist(
        suite_id="holdout-v1",
        baseline_variant_id="v001",
        results=[
            evaluate_variant._load_private_finalize_result("v003", "holdout-v1"),
            evaluate_variant._load_private_finalize_result("v002", "holdout-v1"),
        ],
    )

    best = evaluate_variant._best_finalized_candidate(
        archive_dir=archive_dir,
        suite_id="holdout-v1",
    )

    assert best is not None
    assert best["variant_id"] == "v002"
    assert best["holdout_composite"] == 0.71


def test_best_finalized_candidate_prefers_highest_holdout_composite(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "v001",
                        "promoted_at": "2026-04-01T00:00:00+00:00",
                        "search_metrics": {"suite_id": "search-v1", "composite": 0.60},
                    }
                ),
                json.dumps({"id": "v002", "search_metrics": {"suite_id": "search-v1", "composite": 0.70}}),
                json.dumps({"id": "v003", "search_metrics": {"suite_id": "search-v1", "composite": 0.80}}),
            ]
        )
        + "\n"
    )
    private_dir = tmp_path / "private"
    monkeypatch.setenv("EVOLUTION_PRIVATE_ARCHIVE_DIR", str(private_dir))
    results = []
    for variant_id, composite in (("v002", 0.71), ("v003", 0.75)):
        (private_dir / variant_id).mkdir(parents=True)
        record = {
            "variant_id": variant_id,
            "suite_id": "holdout-v1",
            "baseline_variant_id": "v001",
            "scores": {"composite": composite},
            "eligible_for_promotion": True,
            "reason": "holdout_passed",
        }
        (private_dir / variant_id / "finalize_result.json").write_text(json.dumps(record))
        results.append(record)
    evaluate_variant._write_private_finalized_shortlist(
        suite_id="holdout-v1",
        baseline_variant_id="v001",
        results=results,
    )

    best = evaluate_variant._best_finalized_candidate(
        archive_dir=archive_dir,
        suite_id="holdout-v1",
    )

    assert best is not None
    assert best["variant_id"] == "v003"
    assert best["holdout_composite"] == 0.75
