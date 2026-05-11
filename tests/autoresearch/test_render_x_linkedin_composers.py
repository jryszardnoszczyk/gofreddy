"""Composer tests for x_engine + linkedin_engine in render_report.py.

Hand-crafts a minimal fixture session_dir per platform (no v006 sessions
exist for these lanes yet — the real sessions in v007-curated have empty
drafts/) and renders end-to-end. Asserts the composer:

- registers in COMPOSERS
- surfaces every draft (BODY + META + per-draft eval JSON + frontmatter)
- surfaces angles/<id>.json source data
- applies the cross-lane data-transparency sections (session.md, evals
  appendix, intermediate state, decisions panel, transcripts)
- counts ship-eligible drafts correctly (KEEP decision in eval.json)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDER_REPORT_PATH = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "scripts"
    / "render_report.py"
)


@pytest.fixture(scope="module")
def render_report_module():
    spec = importlib.util.spec_from_file_location(
        "render_report_test_module", RENDER_REPORT_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_test_module"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_x_fixture(root: Path) -> Path:
    sd = root / "x-fixture"
    (sd / "drafts").mkdir(parents=True)
    (sd / "angles").mkdir()
    (sd / "logs").mkdir()
    (sd / "angles" / "angle-001.json").write_text(json.dumps({
        "angle_id": "angle-001",
        "title": "Why early-stage CTOs ship before fundraising",
        "voice_pillars": ["build_first"],
    }, indent=2))
    (sd / "drafts" / "draft-001.md").write_text(
        "---\n"
        "draft_id: draft-001\n"
        "angle_id: angle-001\n"
        "platform: x\n"
        "length_bracket: sharp\n"
        "char_count: 268\n"
        "voice_pillar: build_first\n"
        "---\n\n"
        "[BODY]\n"
        "Most pre-seed CTOs raise before the demo. The ones who ship "
        "first get the stronger term sheets. I watched a friend close "
        "$2M in 6 days after he tweeted the live product. The deck "
        "killed nothing. The demo killed everyone else with a deck.\n"
        "[/BODY]\n\n"
        "[META]\n"
        "hook: Most pre-seed CTOs raise before the demo.\n"
        "authority_anchor: Friend closed $2M in 6 days after a live tweet.\n"
        "specific_number: 6 days\n"
        "attribution: JR (first-person)\n"
        "[/META]\n"
    )
    (sd / "drafts" / "draft-001.eval.json").write_text(json.dumps({
        "decision": "KEEP", "score": 8.4,
        "per_criterion": {"X-1": {"score": 9}},
    }, indent=2))
    (sd / "drafts" / "draft-002.md").write_text(
        "---\ndraft_id: draft-002\nlength_bracket: build\n---\n\n"
        "[BODY]\n" + ("x" * 700) + "\n[/BODY]\n\n"
        "[META]\nhook: x\n[/META]\n"
    )
    (sd / "drafts" / "draft-002.eval.json").write_text(json.dumps({
        "decision": "REVISE", "score": 6.2,
    }, indent=2))
    (sd / "session.md").write_text(
        "# X Engine Session\n\n## Status: COMPLETE\n\n"
        "Runtime context: domain=x_engine, client=jr\n"
    )
    (sd / "session_summary.json").write_text(json.dumps({
        "iterations": {"total": 4},
        "findings_count": 0,
        "status": "COMPLETE",
        "eval_summary": {"draft_decisions": [
            {"artifact": "drafts/draft-001.md", "decision": "KEEP"},
            {"artifact": "drafts/draft-002.md", "decision": "REVISE"},
        ]},
    }, indent=2))
    (sd / "results.jsonl").write_text("\n".join([
        json.dumps({"iteration": 1, "type": "draft", "status": "ok",
                    "decision": "KEEP", "artifact": "drafts/draft-001.md"}),
        json.dumps({"iteration": 2, "type": "draft", "status": "ok",
                    "decision": "REVISE", "artifact": "drafts/draft-002.md"}),
    ]) + "\n")
    (sd / "findings.md").write_text("## Observations\n\n- [VOICE] Strong hook beats long runway.\n")
    (sd / "logs" / "multiturn_session.log.err").write_text(
        "codex\nI'll start by reading session.md.\nexec\n"
        "/bin/zsh -lc \"ls drafts/\"\ncodex\nDrafting against SHARP first.\n"
        "tokens used\n5.0\n"
    )
    return sd


def _write_linkedin_fixture(root: Path) -> Path:
    sd = root / "li-fixture"
    (sd / "drafts").mkdir(parents=True)
    (sd / "angles").mkdir()
    (sd / "logs").mkdir()
    (sd / "angles" / "angle-002.json").write_text(json.dumps({
        "angle_id": "angle-002",
        "title": "How agencies price an AI retainer",
    }, indent=2))
    (sd / "drafts" / "draft-101.md").write_text(
        "---\n"
        "draft_id: draft-101\n"
        "angle_id: angle-002\n"
        "platform: linkedin\n"
        "length_bracket: short_take\n"
        "char_count: 745\n"
        "voice_pillar: agency_op\n"
        "hashtags: 4\n"
        "---\n\n"
        "[BODY]\n" + ("x" * 745) + "\n[/BODY]\n\n"
        "[META]\nhook: x\nhashtags: #agencyops #ai #pricing #retainer\n[/META]\n"
    )
    (sd / "drafts" / "draft-101.eval.json").write_text(json.dumps({
        "decision": "KEEP", "score": 8.0,
    }, indent=2))
    (sd / "session.md").write_text(
        "# LinkedIn Engine Session\n\n## Status: COMPLETE\n"
    )
    (sd / "session_summary.json").write_text(json.dumps({
        "iterations": {"total": 3},
        "findings_count": 0,
        "status": "COMPLETE",
        "eval_summary": {"draft_decisions": [
            {"artifact": "drafts/draft-101.md", "decision": "KEEP"},
        ]},
    }, indent=2))
    (sd / "results.jsonl").write_text(json.dumps({
        "iteration": 1, "type": "draft", "status": "ok",
        "decision": "KEEP", "artifact": "drafts/draft-101.md",
    }) + "\n")
    (sd / "findings.md").write_text("## Observations\n")
    (sd / "logs" / "multiturn_session.log.err").write_text(
        "codex\nI'll start by reading the angle JSON.\n"
    )
    return sd


def test_x_engine_composer_registered(render_report_module):
    assert "x_engine" in render_report_module.COMPOSERS
    assert "linkedin_engine" in render_report_module.COMPOSERS


def test_x_engine_composer_surfaces_drafts(render_report_module, tmp_path):
    sd = _write_x_fixture(tmp_path)
    extract = render_report_module.extract_session(sd)
    sections = render_report_module.compose_x_engine(sd, "jr", extract)
    html = "\n".join(body for _, body in sections)

    # Hero + stats
    assert "X ENGINE" in html
    assert "ship-eligible" in html

    # Both drafts surface (frontmatter + body)
    assert "draft-001" in html
    assert "draft-002" in html

    # BODY text is rendered inline
    assert "Most pre-seed CTOs raise before the demo" in html

    # Per-draft eval surfaced
    assert "drafts/draft-001.md" in html or "draft-001.eval.json" in html
    assert "KEEP" in html
    assert "REVISE" in html

    # Source angle data surfaced
    assert "Source angles" in html
    assert "angle-001" in html

    # Cross-lane data-transparency sections present
    assert "Prompt the agent received" in html
    assert "Session evaluator outputs" in html
    assert "Per-artefact decisions" in html
    assert "Investigation trail" in html
    assert "Agent transcripts" in html


def test_x_engine_ship_eligible_count(render_report_module, tmp_path):
    sd = _write_x_fixture(tmp_path)
    extract = render_report_module.extract_session(sd)
    sections = render_report_module.compose_x_engine(sd, "jr", extract)
    html = "\n".join(body for _, body in sections)
    # Drafts (2 · 1 ship-eligible) — KEEP=1, REVISE=1
    assert "Drafts (2 · 1 ship-eligible)" in html


def test_linkedin_engine_composer_surfaces_hashtags(render_report_module, tmp_path):
    sd = _write_linkedin_fixture(tmp_path)
    extract = render_report_module.extract_session(sd)
    sections = render_report_module.compose_linkedin_engine(sd, "jr", extract)
    html = "\n".join(body for _, body in sections)

    assert "LINKEDIN ENGINE" in html
    assert "draft-101" in html

    # LinkedIn-only meta field surfaces
    assert "hashtags" in html
    assert "#agencyops" in html

    # length_bracket short_take is LinkedIn-specific
    assert "short_take" in html

    # Cross-lane sections
    assert "Prompt the agent received" in html
    assert "Per-artefact decisions" in html
    assert "Source angles" in html


def test_parse_draft_md_round_trip(render_report_module):
    text = (
        "---\n"
        "draft_id: d1\n"
        "platform: x\n"
        "length_bracket: sharp\n"
        "---\n\n"
        "[BODY]\nHello world.\n[/BODY]\n\n"
        "[META]\nhook: hi\nattribution: JR\n[/META]\n"
    )
    parsed = render_report_module._parse_draft_md(text)
    assert parsed["frontmatter"]["draft_id"] == "d1"
    assert parsed["frontmatter"]["length_bracket"] == "sharp"
    assert parsed["body"] == "Hello world."
    assert parsed["meta"]["hook"] == "hi"
    assert parsed["meta"]["attribution"] == "JR"
    assert parsed["char_count"] == len("Hello world.")


def test_parse_draft_md_handles_missing_blocks(render_report_module):
    text = "no frontmatter, no blocks here"
    parsed = render_report_module._parse_draft_md(text)
    assert parsed["frontmatter"] == {}
    assert parsed["body"] == ""
    assert parsed["meta"] == {}
    assert parsed["char_count"] == 0
