#!/usr/bin/env python3
"""Vision sub-judge — spec section A7.

Takes a rendered report screenshot (PNG) and grades it against the RND-1..5
rendering rubric defined in programs/render-rubric.md. Returns a list of
{criterion, score, rationale} dicts in the same shape as the text scorer's
per_criterion array, so they merge cleanly into evaluate_variant's payload.

Reuses the existing Gemini Flash multimodal pattern from
src/generation/image_preview_service.py:verify_preview() (per spec).

Usage:
    render_judge.py <png_path> [--rubric programs/render-rubric.md] [-o out.json]

Returns gracefully (no-op + warn) when GEMINI_API_KEY / google-genai
package are unavailable, so it doesn't block the rest of the pipeline.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_RUBRIC_PATH = Path(__file__).resolve().parent.parent / "programs" / "render-rubric.md"

# RND criterion names (must match rubric)
CRITERIA = ["RND-1", "RND-2", "RND-3", "RND-4", "RND-5"]


def grade_with_gemini(png_path: Path, rubric_text: str) -> list[dict] | None:
    """Returns list of {criterion, score, rationale} or None when unavailable."""
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


def grade(png_path: Path, rubric_path: Path = DEFAULT_RUBRIC_PATH) -> dict:
    """Top-level grading function.

    Returns dict with keys:
      - criteria: list of {criterion, score, rationale}
      - aggregate: arithmetic mean of non-zero scores
      - source: "gemini" | "stub"
    """
    rubric_text = rubric_path.read_text() if rubric_path.exists() else ""

    results = grade_with_gemini(png_path, rubric_text)
    source = "gemini"

    if results is None:
        # Stub fallback: return neutral scores so downstream code doesn't break
        results = [
            {"criterion": c, "score": 0,
             "rationale": "stub · GEMINI_API_KEY or google-genai not available"}
            for c in CRITERIA
        ]
        source = "stub"

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
