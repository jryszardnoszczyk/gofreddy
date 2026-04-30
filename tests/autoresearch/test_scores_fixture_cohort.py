"""Coverage for the fixture_cohort field in scores.json (transparency for
cohort drift across variants — v006 used different fixtures than v007)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Path-bootstrap matches sibling tests (harness/ shadow workaround)
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import evaluate_variant  # noqa: E402


def _make_target():
    return evaluate_variant.EvalTarget(
        backend="codex", model="gpt-5.5", reasoning_effort="high",
    )


def test_write_scores_file_includes_fixture_cohort(tmp_path):
    domains = {
        "search_metrics": {},
        "domains": {
            "geo": {
                "score": 7.95,
                "fixtures": 3,
                "results": [
                    {"fixture_id": "geo-semrush-pricing", "score": 8.0},
                    {"fixture_id": "geo-mayoclinic-bp", "score": 7.5},
                    {"fixture_id": "geo-nubank-br-conta", "score": 8.4},
                ],
            },
        },
    }
    evaluate_variant._write_scores_file(
        tmp_path,
        scores={"geo": 7.95, "composite": 7.95},
        eval_target=_make_target(),
        suite_manifest={"suite_id": "search-v1"},
        domains=domains,
        lane="geo",
    )
    written = json.loads((tmp_path / "scores.json").read_text())
    assert "fixture_cohort" in written
    assert written["fixture_cohort"]["geo"] == [
        "geo-semrush-pricing",
        "geo-mayoclinic-bp",
        "geo-nubank-br-conta",
    ]


def test_write_scores_file_omits_empty_cohorts(tmp_path):
    """Domains with no scored results don't pollute fixture_cohort."""
    domains = {
        "search_metrics": {},
        "domains": {
            "geo": {
                "score": 7.95,
                "results": [{"fixture_id": "geo-x", "score": 8.0}],
            },
            "competitive": {"score": 0.0, "results": []},
            "monitoring": {"score": 0.0, "results": []},
        },
    }
    evaluate_variant._write_scores_file(
        tmp_path,
        scores={"composite": 7.95},
        eval_target=_make_target(),
        suite_manifest={"suite_id": "search-v1"},
        domains=domains,
        lane="geo",
    )
    written = json.loads((tmp_path / "scores.json").read_text())
    assert written["fixture_cohort"] == {"geo": ["geo-x"]}
    # competitive + monitoring absent (no results to report)


def test_write_scores_file_handles_missing_fixture_ids(tmp_path):
    """Defensive: malformed result entries don't crash the writer."""
    domains = {
        "search_metrics": {},
        "domains": {
            "geo": {
                "score": 5.0,
                "results": [
                    {"fixture_id": "geo-ok", "score": 5.0},
                    {"score": 5.0},  # missing fixture_id
                    {"fixture_id": None, "score": 5.0},
                ],
            },
        },
    }
    evaluate_variant._write_scores_file(
        tmp_path,
        scores={"composite": 5.0},
        eval_target=_make_target(),
        suite_manifest={"suite_id": "search-v1"},
        domains=domains,
        lane="geo",
    )
    written = json.loads((tmp_path / "scores.json").read_text())
    assert written["fixture_cohort"]["geo"] == ["geo-ok"]
