#!/usr/bin/env python3
"""Vision sub-judge — grades rendered report screenshots against the
RND-1..5 rubric.

Two backends:

  - **claude** (default) — shells out to the local `claude -p` CLI with
    Claude Sonnet 4.6 multimodal. Reads the image via Claude Code's
    built-in Read tool. No extra SDK dependency, no Gemini key — uses the
    same `claude` CLI auth the rest of the substrate already relies on
    (mirrors src/evaluation/judges/sonnet_agent.py's pattern). The
    default since the rest of the renderer pipeline uses Claude/codex
    CLIs anyway, so adding Gemini was a needless dependency.
  - **gemini** — original path, kept for backward compat. Uses
    google-genai SDK + `GEMINI_API_KEY` / `GOOGLE_API_KEY` if either is
    set. Lane allowlist applies (Gemini is an external endpoint).

Backend selection:

  RENDER_JUDGE_BACKEND=claude  (default)
  RENDER_JUDGE_BACKEND=gemini  (legacy)
  RENDER_JUDGE_BACKEND=stub    (skip both — testing path)

Usage:
    render_judge.py <png_path> [--rubric programs/render-rubric.md] [-o out.json]

Returns gracefully (no-op + warn) when neither backend is reachable so
it doesn't block the rest of the pipeline.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_RUBRIC_PATH = Path(__file__).resolve().parent.parent / "programs" / "render-rubric.md"

# RND criterion names (must match rubric)
CRITERIA = ["RND-1", "RND-2", "RND-3", "RND-4", "RND-5"]


# Lane allowlist for screenshot transmission to Gemini. Per 2026-05-08 review
# (sec-5): customer audit screenshots embed transcripts, scraped page content,
# and ParentFinding text — that data must not be uploaded to Gemini's consumer
# endpoint without an explicit operator decision. Default allows only the
# evolution-test lanes whose fixtures are NOT customer data. Operators can
# opt-in marketing_audit by setting RENDER_JUDGE_LANES_ALLOWED=geo,competitive,
# monitoring,storyboard,marketing_audit (or the literal value "all").
_DEFAULT_ALLOWED_LANES = "geo,competitive,monitoring,storyboard"


def _lane_from_screenshot(png_path: Path) -> str | None:
    """Best-effort lane extraction from .../sessions/<lane>/<client>/report-screenshot.png."""
    try:
        parts = png_path.resolve().parts
    except OSError:
        return None
    if "sessions" not in parts:
        return None
    idx = parts.index("sessions")
    if idx + 1 < len(parts):
        return parts[idx + 1]
    return None


def grade_with_gemini(png_path: Path, rubric_text: str) -> list[dict] | None:
    """Returns list of {criterion, score, rationale} or None when unavailable.

    Refuses to upload screenshots whose lane is not in
    RENDER_JUDGE_LANES_ALLOWED (default: only the evolution-test lanes
    geo/competitive/monitoring/storyboard, NOT marketing_audit). Set
    RENDER_JUDGE_LANES_ALLOWED=all to override; set per-lane (comma-separated)
    for finer control.
    """
    allowed = os.environ.get("RENDER_JUDGE_LANES_ALLOWED", _DEFAULT_ALLOWED_LANES).strip().lower()
    if allowed != "all":
        lane = _lane_from_screenshot(png_path)
        allowed_set = {s.strip() for s in allowed.split(",") if s.strip()}
        if lane is None or lane not in allowed_set:
            print(
                f"  render_judge: skipping Gemini upload — lane='{lane}' not in "
                f"RENDER_JUDGE_LANES_ALLOWED='{allowed}' (set =all to override).",
                file=sys.stderr,
            )
            return None

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        return None

    if not png_path.exists():
        return None

    image_bytes = png_path.read_bytes()
    prompt = f"""You are grading a rendered report screenshot against the
following rendering-quality rubric. Score each criterion from 1–5 per its
gradient anchors. Return ONLY a JSON array of objects with fields
{{criterion, score, rationale}}.

Rubric:
{rubric_text}

Output exactly 5 entries (RND-1 through RND-5). Use score 0 for any
criterion that is N/A (e.g. RND-5 on a PDF-only review)."""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                genai_types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt,
            ],
        )
        # Extract JSON from the model's text output (it may include markdown fences)
        text = response.text or ""
        text = text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])
        return json.loads(text)
    except Exception as e:
        print(f"  WARNING: gemini grading failed: {e}", file=sys.stderr)
        return None


def grade_with_claude(png_path: Path, rubric_text: str) -> list[dict] | None:
    """Returns list of {criterion, score, rationale} or None when unavailable.

    Shells out to ``claude -p`` (Claude Code CLI) with a prompt that asks
    the model to Read the screenshot via its built-in Read tool and grade
    against the rubric. Same auth as the rest of the substrate — no
    extra API key required.

    No lane allowlist enforced for the Claude backend: the call is local
    (`claude` is a CLI tool the operator has already installed + auth'd),
    not a third-party upload to a separate endpoint. The Gemini backend's
    allowlist exists because Gemini is an external Google service.
    """
    if not png_path.exists():
        return None
    if not shutil.which("claude"):
        return None

    model = os.environ.get(
        "RENDER_JUDGE_CLAUDE_MODEL", "claude-sonnet-4-6"
    )
    timeout = int(os.environ.get("RENDER_JUDGE_TIMEOUT_SECONDS", "120"))

    prompt = (
        f"You are grading a rendered report screenshot against the "
        f"rendering-quality rubric below. Use the Read tool to load the "
        f"image at this absolute path:\n\n"
        f"  {png_path}\n\n"
        f"Then score each of RND-1..RND-5 from 1-5 per the gradient "
        f"anchors in the rubric. Use score 0 for any N/A criterion.\n\n"
        f"OUTPUT CONTRACT:\n"
        f"  - Return ONLY a JSON array of 5 objects.\n"
        f"  - Each object has fields: criterion, score, rationale.\n"
        f"  - rationale cites concrete visual evidence (element type, "
        f"approximate position, comparison to anchor).\n"
        f"  - Do NOT include any preamble, markdown fences, or commentary "
        f"outside the JSON array.\n\n"
        f"=== RUBRIC ===\n{rubric_text}\n=== END RUBRIC ===\n\n"
        f"Now Read the screenshot and emit the JSON array."
    )

    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", model,
                "--max-turns", "3",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(
            f"  WARNING: claude render-judge unavailable "
            f"({type(e).__name__}: {e})", file=sys.stderr,
        )
        return None
    if result.returncode != 0:
        print(
            f"  WARNING: claude render-judge returned rc={result.returncode}: "
            f"{(result.stderr or '')[:300]}",
            file=sys.stderr,
        )
        return None

    text = (result.stdout or "").strip()
    # Strip code fences if the model wrapped them despite the contract
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # The CLI sometimes prepends a brief acknowledgement before the JSON;
    # locate the first '[' and last ']' to extract the array robustly.
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        print(
            f"  WARNING: claude render-judge produced no JSON array: "
            f"{text[:200]!r}",
            file=sys.stderr,
        )
        return None
    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        print(
            f"  WARNING: claude render-judge JSON parse failed: {e}",
            file=sys.stderr,
        )
        return None
    if not isinstance(parsed, list):
        return None
    return parsed


def grade(png_path: Path, rubric_path: Path = DEFAULT_RUBRIC_PATH) -> dict:
    """Top-level grading function. Dispatches on RENDER_JUDGE_BACKEND.

    Returns dict with keys:
      - criteria: list of {criterion, score, rationale}
      - aggregate: arithmetic mean of non-zero scores
      - source: "claude" | "gemini" | "stub"
    """
    rubric_text = rubric_path.read_text() if rubric_path.exists() else ""

    backend = os.environ.get("RENDER_JUDGE_BACKEND", "claude").strip().lower()

    results: list[dict] | None = None
    source = "stub"

    if backend == "claude":
        results = grade_with_claude(png_path, rubric_text)
        if results is not None:
            source = "claude"
    elif backend == "gemini":
        results = grade_with_gemini(png_path, rubric_text)
        if results is not None:
            source = "gemini"
    elif backend == "stub":
        pass  # explicit stub for testing
    else:
        print(
            f"  WARNING: unknown RENDER_JUDGE_BACKEND={backend!r}; using stub.",
            file=sys.stderr,
        )

    if results is None:
        # Stub fallback: return neutral scores so downstream code doesn't break.
        # _aggregate_render_quality filters aggregate=0 stubs out of the
        # composite blend so this doesn't dilute the evolution signal.
        reason = {
            "claude": "claude CLI not on PATH / call failed",
            "gemini": "GEMINI_API_KEY or google-genai not available",
            "stub":   "RENDER_JUDGE_BACKEND=stub",
        }.get(backend, "unknown backend")
        results = [
            {"criterion": c, "score": 0,
             "rationale": f"stub · {reason}"}
            for c in CRITERIA
        ]

    # Aggregate
    valid_scores = [r["score"] for r in results if r.get("score", 0) > 0]
    aggregate = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

    return {
        "criteria": results,
        "aggregate": aggregate,
        "source": source,
        "screenshot": str(png_path),
    }


def main():
    p = argparse.ArgumentParser(description="Vision sub-judge — grade rendered report screenshot")
    p.add_argument("png_path", type=Path)
    p.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC_PATH)
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args()

    result = grade(args.png_path.resolve(), args.rubric.resolve())
    js = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(js)
        print(f"Wrote {args.output} · source={result['source']} aggregate={result['aggregate']}", file=sys.stderr)
    else:
        print(js)


if __name__ == "__main__":
    main()
