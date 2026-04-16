from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VARIANT_ROOT = REPO_ROOT / "autoresearch" / "archive" / "v001"
if str(VARIANT_ROOT) not in sys.path:
    sys.path.insert(0, str(VARIANT_ROOT))

from runtime import config as runtime_config
from runtime import post_session
from workflows import get_workflow_spec


def test_render_prompt_appends_global_findings_and_fresh_override(tmp_path: Path) -> None:
    script_dir = tmp_path / "variant"
    program_path = script_dir / "programs" / "geo-session.md"
    findings_path = script_dir / "geo-findings.md"
    program_path.parent.mkdir(parents=True)
    findings_path.write_text("Global insight\n", encoding="utf-8")
    program_path.write_text("# Program for {client} {site}\n", encoding="utf-8")

    prompt = runtime_config.render_prompt(
        script_dir,
        program_path,
        "semrush",
        "https://www.semrush.com",
        "geo",
        strategy="fresh",
        session_backend=lambda: "codex",
        session_model=lambda: "gpt-5.4",
    )

    assert "Global insight" in prompt
    assert "## Fresh Session Override" in prompt
    assert "Domain: geo" in prompt


def test_configure_domain_env_sets_monitoring_week_from_pins(monkeypatch) -> None:
    monkeypatch.setenv("AUTORESEARCH_WEEK_START", "2026-03-16")
    monkeypatch.setenv("AUTORESEARCH_WEEK_END", "2026-03-22")
    monkeypatch.delenv("WEEK_START", raising=False)
    monkeypatch.delenv("WEEK_END", raising=False)

    runtime_config.configure_domain_env("monitoring", "Shopify")

    assert os.environ["AUTORESEARCH_DOMAIN"] == "monitoring"
    assert os.environ["AUTORESEARCH_CLIENT"] == "Shopify"
    assert os.environ["WEEK_START"] == "2026-03-16"
    assert os.environ["WEEK_END"] == "2026-03-22"


def test_geo_post_session_hooks_promote_findings_only_with_domain_scope(
    tmp_path: Path,
    monkeypatch,
) -> None:
    script_dir = tmp_path / "variant"
    session_dir = tmp_path / "session"
    (session_dir / "pages").mkdir(parents=True)
    (session_dir / "pages" / "home.json").write_text("{}", encoding="utf-8")

    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_run_script(script_name: str, *args: str, stdout_file=None) -> None:
        calls.append((script_name, tuple(args)))

    def fake_run_subprocess(cmd: list[str]) -> None:
        calls.append(("subprocess", tuple(cmd)))

    monkeypatch.setattr(
        post_session,
        "snapshot_session_evaluations",
        lambda domain, session_dir, run_script: {"optimized_decisions": []},
    )
    monkeypatch.setattr(
        post_session,
        "enforce_completion_guard",
        lambda domain, session_dir, eval_summary, is_complete: None,
    )

    post_session.post_session_hooks(
        "geo",
        session_dir,
        "semrush",
        script_dir=script_dir,
        run_script=fake_run_script,
        run_subprocess=fake_run_subprocess,
        is_complete=lambda _session_dir: False,
    )

    assert ("allocate_gaps.py", (str(session_dir),)) in calls
    assert ("build_geo_report.py", (str(session_dir),)) in calls
    assert ("summarize_session.py", (str(session_dir), "geo", "semrush")) in calls
    assert ("promote_findings.py", ("geo",)) in calls
    assert ("promote_findings.py", ()) not in calls


def test_workflow_specs_own_summary_deliverable_listing(tmp_path: Path) -> None:
    geo_dir = tmp_path / "geo"
    (geo_dir / "optimized").mkdir(parents=True)
    (geo_dir / "report.md").write_text("report\n", encoding="utf-8")
    (geo_dir / "optimized" / "home.md").write_text("page\n", encoding="utf-8")

    competitive_dir = tmp_path / "competitive"
    (competitive_dir / "analyses").mkdir(parents=True)
    (competitive_dir / "brief.md").write_text("brief\n", encoding="utf-8")
    (competitive_dir / "analyses" / "one.md").write_text("analysis\n", encoding="utf-8")

    assert get_workflow_spec("geo").list_deliverables(geo_dir) == ["report.md", "optimized/home.md"]
    assert get_workflow_spec("competitive").list_deliverables(competitive_dir) == ["brief.md", "analyses/one.md"]
