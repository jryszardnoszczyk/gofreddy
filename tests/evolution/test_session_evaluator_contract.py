from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = REPO_ROOT / "autoresearch" / "archive" / "v001"
SCRIPTS_DIR = ARCHIVE_ROOT / "scripts"
MODULE_PATH = SCRIPTS_DIR / "evaluate_session.py"
# `evaluate_session.py` imports `from workflows.session_eval_*`, so its
# parent (the variant root) needs to be on sys.path before we exec it.
if str(ARCHIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_ROOT))
SPEC = importlib.util.spec_from_file_location("autoresearch_evaluate_session", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
evaluate_session = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluate_session)


def test_critique_unavailable_forces_rework_for_all_domains(tmp_path: Path) -> None:
    """Phase 3 (Unit 6): heuristic fallback is gone. When external critique
    is unavailable, every domain returns REWORK with a deterministic
    `critique_unavailable:` reason — no silent KEEPs.
    """
    for domain in ("competitive", "geo", "monitoring", "storyboard"):
        session_dir = tmp_path / "sessions" / domain / "client"
        session_dir.mkdir(parents=True)
        artifact = session_dir / "brief.md"
        artifact.write_text("# Brief\n\nThis is enough structure for the test.")

        with patch.object(
            evaluate_session,
            "_invoke_external_critique",
            side_effect=RuntimeError("backend down"),
        ):
            output = asyncio.run(
                evaluate_session.evaluate_all_criteria(
                    domain,
                    "full",
                    artifact,
                    session_dir,
                )
            )

        assert output["decision"] == "REWORK", (
            f"{domain} must force REWORK when the critique backend is down"
        )
        assert output["reason"].startswith("critique_unavailable:")
        assert output["results"] == []
        assert output["warnings"][0].startswith("Trusted external critique unavailable:")


def test_evaluate_session_no_longer_exports_heuristic_fallback() -> None:
    """The heuristic-fallback symbols deleted by Unit 6 must stay deleted."""
    deleted = (
        "evaluate_all_criteria_heuristic",
        "_degraded_external_critique_output",
    )
    for symbol in deleted:
        assert not hasattr(evaluate_session, symbol), (
            f"evaluate_session.{symbol} was deleted in Phase 3 Unit 6 (Option B)"
        )
    # The replacement helper does exist:
    assert callable(evaluate_session._critique_unavailable)
