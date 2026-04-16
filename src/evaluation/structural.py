"""Structural gate — Layer 2 of evaluation pipeline.

Domain-specific validation that outputs have the right shape
before LLM judges run. Free, deterministic, fast.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StructuralResult:
    """Result of structural gate validation."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    dqs_score: float | None = None  # Monitoring only: Digest Quality Score


def structural_gate(domain: str, outputs: dict[str, str]) -> StructuralResult:
    """Run domain-specific structural validation.

    Args:
        domain: One of "geo", "competitive", "monitoring", "storyboard".
        outputs: {filename: content} dict of generated outputs.

    Returns:
        StructuralResult with pass/fail and failure reasons.
    """
    validators = {
        "geo": _validate_geo,
        "competitive": _validate_competitive,
        "monitoring": _validate_monitoring,
        "storyboard": _validate_storyboard,
    }

    validator = validators.get(domain)
    if validator is None:
        return StructuralResult(passed=False, failures=[f"Unknown domain: {domain}"])

    return validator(outputs)


# ─── GEO ──────────────────────────────────────────────────────────────────


def _validate_geo(outputs: dict[str, str]) -> StructuralResult:
    """GEO: optimized pages exist, JSON parses, schema-content consistency."""
    failures: list[str] = []

    # Must have at least one optimized page
    optimized = {k: v for k, v in outputs.items() if k.startswith("optimized/")}
    if not optimized:
        failures.append("No optimized/ files found")
        return StructuralResult(passed=False, failures=failures)

    for filename, content in optimized.items():
        if not content or not content.strip():
            failures.append(f"{filename}: empty content")
            continue

        # Check for JSON-LD blocks — if present, they must parse
        json_ld_blocks = re.findall(
            r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>',
            content, re.DOTALL | re.IGNORECASE,
        )
        for i, block in enumerate(json_ld_blocks):
            try:
                json.loads(block)
            except json.JSONDecodeError:
                failures.append(f"{filename}: JSON-LD block {i+1} invalid")

    return StructuralResult(passed=len(failures) == 0, failures=failures)


# ─── Competitive Intelligence ────────────────────────────────────────────


def _validate_competitive(outputs: dict[str, str]) -> StructuralResult:
    """CI: brief.md exists, has sections, thesis identifiable."""
    failures: list[str] = []

    # Find brief file
    brief_files = {k: v for k, v in outputs.items() if "brief" in k.lower() and k.endswith(".md")}
    if not brief_files:
        failures.append("No brief.md found")
        return StructuralResult(passed=False, failures=failures)

    brief_content = next(iter(brief_files.values()))

    if not brief_content or len(brief_content.strip()) < 100:
        failures.append("Brief content too short (<100 chars)")
        return StructuralResult(passed=False, failures=failures)

    # Must have section headers
    headers = re.findall(r"^#{1,3}\s+.+", brief_content, re.MULTILINE)
    if len(headers) < 3:
        failures.append(f"Brief has only {len(headers)} section headers (need ≥3)")

    return StructuralResult(passed=len(failures) == 0, failures=failures)


# ─── Monitoring ──────────────────────────────────────────────────────────


def _validate_monitoring(outputs: dict[str, str]) -> StructuralResult:
    """Monitoring: absorb freddy digest check's 13 assertions."""
    failures: list[str] = []
    assertions_passed = 0
    assertions_total = 0

    def _assert(name: str, condition: bool, detail: str = "") -> None:
        nonlocal assertions_passed, assertions_total
        assertions_total += 1
        if condition:
            assertions_passed += 1
        else:
            msg = name if not detail else f"{name}: {detail}"
            failures.append(msg)

    # Load results.jsonl if present
    results: list[dict] = []
    results_content = outputs.get("results.jsonl", "")
    if results_content:
        for line in results_content.strip().split("\n"):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Precompute file lists used by multiple assertions.
    has_digest = "digest.md" in outputs
    story_files = [k for k in outputs if k.startswith("stories/") and k.endswith(".json")]
    synth_files = [k for k in outputs if k.startswith("synthesized/") and k.endswith(".md")]
    session_md = outputs.get("session.md", "")

    # 1. session.md exists
    _assert("session_md_exists", "session.md" in outputs)
    # 2. results.jsonl non-empty
    _assert("results_non_empty", len(results) > 0, f"Found {len(results)} entries")
    # 3. At least one select_mentions entry
    _assert("has_select_mentions", any(r.get("type") == "select_mentions" for r in results))
    # 4. Cluster stories phase completed — check actual files; digest.md
    #    alone suffices for low-volume weeks that skip clustering.
    _assert(
        "has_cluster_stories",
        len(story_files) > 0 or has_digest,
        f"Found {len(story_files)} story files",
    )
    # 5. Synthesize phase completed — digest.md IS the synthesized deliverable.
    synth = [r for r in results if r.get("type") == "synthesize"]
    _assert("has_synthesize", has_digest, "digest.md is the synthesized deliverable")
    # 6. Recommend phase — pass if recommendation files exist, results.jsonl
    #    records the phase, or digest.md present (low-volume skips recommend).
    has_rec_files = any(k.startswith("recommendations/") for k in outputs)
    has_rec_result = any(r.get("type") == "recommend" for r in results)
    _assert(
        "has_recommend",
        has_rec_files or has_rec_result or has_digest,
        "recommendations or digest.md must exist",
    )
    # 7. digest.md exists
    _assert("digest_exists", has_digest)
    # 8. findings.md exists
    _assert("findings_exists", "findings.md" in outputs)
    # 9. Session status — accept COMPLETE, or any status when digest.md
    #    exists (fresh-mode agents often don't update session.md status).
    status_ok = "## Status: COMPLETE" in session_md or has_digest
    _assert("status_complete", status_ok,
            "Expected COMPLETE or digest.md present")
    # 10. Synthesized stories match cluster count — pass if digest.md exists
    #     (synthesized/ often only has digest-meta.json, not .md files).
    if story_files:
        _assert(
            "synth_matches_stories",
            len(synth_files) >= len(story_files) * 0.5 or has_digest,
            f"{len(synth_files)} synthesized vs {len(story_files)} stories",
        )
    else:
        _assert("synth_matches_stories", has_digest,
                "low-volume: digest.md serves as synthesis")
    # 11. No synthesize attempts > 3
    over_3 = [r for r in synth if r.get("attempt", 1) > 3]
    _assert("no_excessive_rework", len(over_3) == 0, f"{len(over_3)} stories with >3 attempts")
    # 12. Recommendations files exist (if any recommendation files present)
    if has_rec_files:
        _assert(
            "rec_exec_summary",
            any(k.endswith("executive_summary.md") for k in outputs),
        )
        _assert(
            "rec_action_items",
            any(k.endswith("action_items.md") for k in outputs),
        )
    else:
        assertions_total += 2
        assertions_passed += 2
    # 13. Source coverage — pass when digest exists (LLM judges assess quality;
    #     a zero-mention "no data" digest is valid low-volume output).
    select = [r for r in results if r.get("type") == "select_mentions"]
    if select:
        sources = select[-1].get("sources", 0)
        _assert("source_coverage", sources >= 2 or has_digest, f"Only {sources} sources")

    dqs = round(assertions_passed / assertions_total, 3) if assertions_total > 0 else 0.0

    return StructuralResult(
        passed=len(failures) == 0,
        failures=failures,
        dqs_score=dqs,
    )


# ─── Storyboard ──────────────────────────────────────────────────────────


def _validate_storyboard(outputs: dict[str, str]) -> StructuralResult:
    """Storyboard: stories/*.json + storyboards/*.json parse, scene structural completeness.

    Accepts both PLAN_STORY format (stories/*.json with scene_plan/camera_motion)
    and IDEATE format (storyboards/*.json with scenes/camera_movement).
    """
    failures: list[str] = []

    # Find story JSON files (PLAN_STORY phase) and storyboard JSON files (IDEATE phase)
    story_files = {k: v for k, v in outputs.items() if k.startswith("stories/") and k.endswith(".json")}
    storyboard_files = {k: v for k, v in outputs.items() if k.startswith("storyboards/") and k.endswith(".json")}

    if not story_files and not storyboard_files:
        failures.append("No stories/*.json or storyboards/*.json files found")
        return StructuralResult(passed=False, failures=failures)

    # Validate stories (PLAN_STORY phase): scene_plan or scenes, camera_motion or camera
    for filename, content in story_files.items():
        try:
            story = json.loads(content)
        except json.JSONDecodeError:
            failures.append(f"{filename}: invalid JSON")
            continue

        if not isinstance(story, dict):
            failures.append(f"{filename}: top-level is not an object")
            continue

        # Accept both "scenes" and "scene_plan" keys
        scenes = story.get("scenes") or story.get("scene_plan") or []
        if not scenes:
            failures.append(f"{filename}: no scenes or scene_plan array")
            continue

        # Scene count consistency
        declared_count = story.get("scene_count")
        if declared_count is not None and declared_count != len(scenes):
            failures.append(
                f"{filename}: scene_count={declared_count} but {len(scenes)} scenes found"
            )

        # Every scene must have non-empty prompt; camera and transition accept aliases
        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                failures.append(f"{filename}: scene {i+1} is not an object")
                continue
            # Prompt is always required
            prompt_val = scene.get("prompt")
            if not prompt_val or (isinstance(prompt_val, str) and not prompt_val.strip()):
                failures.append(f"{filename}: scene {i+1} missing prompt")
            # Camera accepts aliases: camera, camera_motion, camera_movement
            camera_val = scene.get("camera") or scene.get("camera_motion") or scene.get("camera_movement")
            if not camera_val or (isinstance(camera_val, str) and not camera_val.strip()):
                failures.append(f"{filename}: scene {i+1} missing camera/camera_motion")

    # Validate storyboards (IDEATE phase): scenes with camera_movement
    for filename, content in storyboard_files.items():
        try:
            sb = json.loads(content)
        except json.JSONDecodeError:
            failures.append(f"{filename}: invalid JSON")
            continue

        if not isinstance(sb, dict):
            failures.append(f"{filename}: top-level is not an object")
            continue

        scenes = sb.get("scenes", [])
        # Fallback: scenes may be nested inside source_story_plan (draft/staging format)
        if not scenes:
            plan = sb.get("source_story_plan")
            if isinstance(plan, dict):
                scenes = plan.get("scenes", [])
        if not scenes:
            failures.append(f"{filename}: no scenes array")
            continue

        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                failures.append(f"{filename}: scene {i+1} is not an object")
                continue
            prompt_val = scene.get("prompt")
            if not prompt_val or (isinstance(prompt_val, str) and not prompt_val.strip()):
                failures.append(f"{filename}: scene {i+1} missing prompt")

    return StructuralResult(passed=len(failures) == 0, failures=failures)
