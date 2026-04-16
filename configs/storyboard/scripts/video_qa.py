#!/usr/bin/env python3
"""Video QA script — scores a generated video against its prompt using Gemini.

Downloads the video from a URL, uploads to Gemini Files API, and asks
Gemini Flash to score it on scene fidelity, motion quality, style
consistency, and audio continuity.  Prints JSON to stdout; errors to stderr.

Usage:
    python video_qa.py \
      --video-url "https://..." \
      --prompt "A gaunt bureaucrat stamps cosmic documents..." \
      [--anchor-image "https://..."]
"""

from __future__ import annotations

from src.common.gemini_models import GEMINI_FLASH

import argparse
import json
import os
import sys
import tempfile
import time

import httpx


def _download(url: str, dest: str, timeout: float = 120.0) -> None:
    with httpx.Client(timeout=httpx.Timeout(30.0, read=timeout), follow_redirects=True) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_bytes(8192):
                    f.write(chunk)


def _score_video(
    video_path: str,
    prompt: str,
    anchor_image_url: str | None = None,
) -> dict:
    """Upload video to Gemini Files API and score against prompt."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not set", "scene_score": 0, "motion_score": 0, "style_score": 0}

    client = genai.Client(api_key=api_key)
    uploaded_files = []  # Track all uploads for cleanup

    try:
        # Upload video file
        video_file = client.files.upload(file=video_path)
        uploaded_files.append(video_file)

        # Wait for processing (up to 120s)
        deadline = time.monotonic() + 120
        while video_file.state.name == "PROCESSING":
            if time.monotonic() > deadline:
                return {"error": "Gemini file processing timeout", "scene_score": 0, "motion_score": 0, "style_score": 0}
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            return {"error": "Gemini file processing failed", "scene_score": 0, "motion_score": 0, "style_score": 0}

        # Build content parts — video file + optional anchor image + text prompt
        content_parts = [video_file]

        # Download and upload anchor image as actual file (not just URL text)
        # Gemini can't fetch URLs — it needs the image uploaded via Files API
        if anchor_image_url:
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp:
                    img_path = img_tmp.name
                _download(anchor_image_url, img_path, timeout=30.0)
                anchor_file = client.files.upload(file=img_path)
                uploaded_files.append(anchor_file)
                content_parts.append(anchor_file)
                os.unlink(img_path)
            except Exception as e:
                print(f"Warning: could not upload anchor image: {e}", file=sys.stderr)

        # Build evaluation prompt
        eval_prompt = (
            "You are a video quality evaluator. Watch AND listen to this generated video "
            "and score it against the original creative prompt.\n\n"
            f"ORIGINAL PROMPT:\n<user_input>{prompt}</user_input>\n\n"
            "Score the video on FIVE dimensions (1-10 each):\n\n"
            "VISUAL:\n"
            "1. **scene_score**: Does the video match the scene description? "
            "Are the subjects, setting, and actions correct?\n"
            "2. **motion_score**: Is the motion natural and coherent? "
            "No glitches, artifacts, or unnatural movement?\n"
            "3. **style_score**: Does the video match the expected visual style? "
            "Lighting, color grade, mood consistent across ALL scenes?"
        )

        if anchor_image_url:
            eval_prompt += (
                " Compare the video's visual style to the REFERENCE IMAGE provided above."
            )

        eval_prompt += (
            "\n\nAUDIO:\n"
            "4. **voice_score**: Are character voices consistent across scenes? "
            "Same pitch, tone, accent, speaking speed throughout? If no speech, score based on "
            "ambient sound consistency.\n"
            "5. **audio_score**: Is background music/sound continuous and cohesive? "
            "No jarring music changes at scene transitions? Volume levels consistent?\n\n"
            "Also identify which specific scene(s) have issues, if any.\n\n"
            "Respond with ONLY valid JSON:\n"
            '{"scene_score": N, "motion_score": N, "style_score": N, '
            '"voice_score": N, "audio_score": N, '
            '"problem_scenes": [0, 3] or [], '
            '"improvement_suggestion": "..." or null}'
        )

        content_parts.append(eval_prompt)

        response = client.models.generate_content(
            model=GEMINI_FLASH,
            contents=content_parts,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.5,
            ),
        )

        # Check finish reason (handle both string and enum values)
        if response.candidates:
            fr = response.candidates[0].finish_reason
            fr_name = fr.name if hasattr(fr, "name") else str(fr)
            if fr_name not in ("STOP", "None", ""):
                return {
                    "error": f"Gemini finish_reason: {fr_name}",
                    "scene_score": 0, "motion_score": 0, "style_score": 0,
                }

        if not response.text:
            return {"error": "Empty Gemini response", "scene_score": 0, "motion_score": 0, "style_score": 0}

        result = json.loads(response.text)

        # Clamp scores to 1-10
        for key in ("scene_score", "motion_score", "style_score", "voice_score", "audio_score"):
            val = result.get(key, 0)
            result[key] = max(1, min(10, int(val or 0)))

        return result

    except json.JSONDecodeError:
        return {"error": "Invalid JSON from Gemini", "scene_score": 0, "motion_score": 0, "style_score": 0}
    except Exception as e:
        return {"error": str(e)[:200], "scene_score": 0, "motion_score": 0, "style_score": 0}
    finally:
        # Clean up ALL uploaded files
        for f in uploaded_files:
            try:
                client.files.delete(name=f.name)
            except Exception:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Video QA via Gemini")
    parser.add_argument("--video-url", required=True, help="URL of the generated video")
    parser.add_argument("--prompt", required=True, help="Original creative prompt")
    parser.add_argument("--anchor-image", default=None, help="URL of style reference image")
    args = parser.parse_args()

    # Download video to temp file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        print("Downloading video...", file=sys.stderr)
        _download(args.video_url, tmp_path)

        print("Scoring with Gemini...", file=sys.stderr)
        result = _score_video(tmp_path, args.prompt, args.anchor_image)

        # Output JSON to stdout
        print(json.dumps(result))

    except httpx.HTTPError as e:
        print(json.dumps({"error": f"Download failed: {e}", "scene_score": 0, "motion_score": 0, "style_score": 0}))
        sys.exit(1)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
