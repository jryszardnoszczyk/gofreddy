"""Judge calibration anchor — cross-family drift detection.

Monthly: ``python autoresearch/judge_calibration.py --check``. The
evolution-judge-service loads a stored baseline per (variant, fixture)
pair and dispatches bi-directional cross-family scoring: Claude judges
Codex's drift by reading Codex's baseline + current traces, Codex does
the same in reverse. Autoresearch sees only the aggregated verdict.

Baseline storage + PR-gated judge-service prompt deploy (Phase 0c
merge-to-main → local-daemon.sh restart) prevents runtime tampering.

Pair identifiers live out-of-repo at
``~/.config/gofreddy/calibration-pairs.json`` (operator maintains,
PR-gated on the judge-service mirror). Autoresearch holds only the
identifiers — scoring + drift-detection logic lives judge-side.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


CALIBRATION_PAIRS_PATH = Path.home() / ".config/gofreddy/calibration-pairs.json"


def check() -> int:
    """Monthly drift check — single HTTP call, aggregated cross-family verdict.

    Return codes:
      * 0 — verdict == "stable"
      * 1 — verdict in {"magnitude_drift", "variance_drift", "reasoning_drift", "mixed"}
      * 2 — configuration error (pairs file missing); operator action needed
    """
    from autoresearch.events import log_event
    from autoresearch.judges.quality_judge import call_quality_judge

    if not CALIBRATION_PAIRS_PATH.exists():
        print(
            f"ERROR: no calibration-pairs config at {CALIBRATION_PAIRS_PATH}; "
            "deploy one via PR before --check.",
            file=sys.stderr,
        )
        return 2
    try:
        config = json.loads(CALIBRATION_PAIRS_PATH.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: {CALIBRATION_PAIRS_PATH} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    pairs = config.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        print(
            f"ERROR: {CALIBRATION_PAIRS_PATH} must contain a non-empty "
            '"pairs" array of (variant, fixture) identifiers.',
            file=sys.stderr,
        )
        return 2

    verdict = call_quality_judge({
        "role": "calibration_drift",
        "pairs": pairs,
        "check_timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Judge-service side emits its own kind="judge_drift" events with the
    # full baseline + reasoning comparisons (Phase 0c boundary). Autoresearch
    # mirrors the top-line verdict into its own events log for lineage.
    log_event(
        kind="judge_drift",
        verdict=verdict.verdict,
        reasoning=verdict.reasoning,
        confidence=verdict.confidence,
    )

    if verdict.verdict == "stable":
        print(f"judge calibration clean: {verdict.reasoning}")
        return 0
    print(
        f"⚠️  judge drift: {verdict.verdict} — {verdict.reasoning}",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--check"]:
        return check()
    print(
        "Usage: python autoresearch/judge_calibration.py --check\n"
        "(rebaselining is a PR-gated judge-service operation, not a runtime call)",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
