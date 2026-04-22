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
    """CI: brief.md exists and is substantive; at least one competitors/*.json parses.

    Shape-only checks — no content rules. Placeholder briefs with no
    underlying data previously passed structural with 100 chars + 3
    headers (dead-weight report pattern). Bumping to 500 chars and
    requiring parseable competitor data blocks that failure mode
    without encoding content judgments in frozen code.
    """
    failures: list[str] = []

    # Find brief file
    brief_files = {k: v for k, v in outputs.items() if "brief" in k.lower() and k.endswith(".md")}
    if not brief_files:
        failures.append("No brief.md found")
        return StructuralResult(passed=False, failures=failures)

    brief_content = next(iter(brief_files.values()))

    if not brief_content or len(brief_content.strip()) < 500:
        failures.append("Brief content too short (<500 chars)")
        return StructuralResult(passed=False, failures=failures)

    # Must have section headers
    headers = re.findall(r"^#{1,3}\s+.+", brief_content, re.MULTILINE)
    if len(headers) < 3:
        failures.append(f"Brief has only {len(headers)} section headers (need ≥3)")

    # At least one competitors/*.json must exist and parse. Shape only —
    # judges evaluate whether the data is sufficient (CI-2 evidence-traced).
    # Underscore-prefixed files (e.g. _client_baseline.json) are not
    # competitors — same convention as cli/freddy/commands/evaluate.py.
    def _is_competitor_file(key: str) -> bool:
        if not (key.startswith("competitors/") and key.endswith(".json")):
            return False
        name = key[len("competitors/"):]
        return not name.startswith("_")

    competitor_files = {k: v for k, v in outputs.items() if _is_competitor_file(k)}
    if not competitor_files:
        failures.append("No competitors/*.json — brief has no underlying data")
    else:
        valid = 0
        for fname, content in competitor_files.items():
            try:
                json.loads(content)
                valid += 1
            except json.JSONDecodeError:
                failures.append(f"{fname}: invalid JSON")
        if valid < 1:
            failures.append("No competitors/*.json parses as JSON")

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
    def _attempt_int(val: object) -> int:
        if isinstance(val, bool):
            return 1
        if isinstance(val, int):
            return val
        if isinstance(val, str):
            try:
                return int(val)
            except ValueError:
                return 1
        return 1

    over_3 = [r for r in synth if _attempt_int(r.get("attempt", 1)) > 3]
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
    #     Agents have written the count under either `sources` or
    #     `current_sources` historically; accept either key.
    select = [r for r in results if r.get("type") == "select_mentions"]
    if select:
        raw_sources = select[-1].get("sources", select[-1].get("current_sources", 0))
        if isinstance(raw_sources, list):
            sources_count = len(raw_sources)
        elif isinstance(raw_sources, bool):
            sources_count = int(raw_sources)
        elif isinstance(raw_sources, int):
            sources_count = raw_sources
        elif isinstance(raw_sources, str):
            try:
                sources_count = int(raw_sources)
            except ValueError:
                sources_count = 0
        else:
            sources_count = 0
        _assert(
            "source_coverage",
            sources_count >= 2 or has_digest,
            f"Only {sources_count} sources",
        )

    # 14. Digest hallucination guard — agents have written narrative claims
    #     like "Digest persisted via `freddy digest persist ... --file
    #     synthesized/digest-meta.json`" into session.md without running the
    #     command. Reject when session.md asserts persistence but the
    #     metadata file the claim names is absent from outputs.
    if session_md and "Digest persisted" in session_md:
        _assert(
            "digest_meta_grounded",
            "synthesized/digest-meta.json" in outputs,
            "session.md claims digest persisted but synthesized/digest-meta.json missing",
        )

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
        if not isinstance(scenes, list):
            failures.append(f"{filename}: scenes must be a list, got {type(scenes).__name__}")
            continue
        if not scenes:
            failures.append(f"{filename}: no scenes or scene_plan array")
            continue

        # Scene count consistency (coerce declared_count to int; skip on mismatch)
        declared_count = story.get("scene_count")
        if isinstance(declared_count, bool):
            declared_count = None
        elif isinstance(declared_count, str):
            try:
                declared_count = int(declared_count)
            except ValueError:
                declared_count = None
        elif not isinstance(declared_count, int):
            declared_count = None
        if declared_count is not None and declared_count != len(scenes):
            failures.append(
                f"{filename}: scene_count={declared_count} but {len(scenes)} scenes found"
            )

        # Every scene must have non-empty prompt; camera accepts aliases
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
        if not isinstance(scenes, list):
            scenes = []
        # Fallback: scenes may be nested inside source_story_plan (draft/staging format)
        if not scenes:
            plan = sb.get("source_story_plan")
            if isinstance(plan, dict):
                nested = plan.get("scenes", [])
                scenes = nested if isinstance(nested, list) else []
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


# ─── Structural doc facts ────────────────────────────────────────────────
#
# Single source of truth for the ``## Structural Validator Requirements``
# section in each ``programs/<domain>-session.md``. ``regen_program_docs``
# imports this dict to rewrite those sections on every variant clone so
# the docs never drift from the code. A bidirectional paired test
# (``tests/autoresearch/test_structural_doc_facts.py``) enforces that
# every gate function here has a bullet and every bullet maps to a gate
# function — drift fails CI loud in both directions.
#
# Bullets describe only the gates actually enforced by the validator
# above. Gates removed by Unit 12 (competitive ``<500 chars`` /
# ``<3 headers``, monitoring ``no_excessive_rework`` /
# ``synth_matches_stories`` / digest-hallucination regex) are NOT
# listed — adding them back here would re-introduce the live 5x drift
# bug this infrastructure exists to prevent.

STRUCTURAL_DOC_FACTS: dict[str, list[str]] = {
    "competitive": [
        "A file with `brief` in its name ending in `.md` exists (e.g. `brief.md`).",
        "At least one `competitors/<name>.json` (excluding `_`-prefixed helpers) is present and parses as valid JSON — shape only; judges evaluate sufficiency.",
    ],
    "monitoring": [
        "`session.md` exists.",
        "`results.jsonl` is non-empty and parseable.",
        "At least one `results.jsonl` entry has `type: select_mentions`.",
        "Clustering evidence is present — either `stories/*.json` files or a `digest.md` (low-volume weeks may skip clustering).",
        "Synthesis evidence is present — `digest.md` is the synthesized deliverable.",
        "Recommendation evidence is present — `recommendations/` files, a `results.jsonl` entry with `type: recommend`, or `digest.md`.",
        "`digest.md` exists.",
        "`findings.md` exists.",
        "Session status is terminal — `## Status: COMPLETE` in `session.md` or `digest.md` present.",
        "If any `recommendations/` files exist, `executive_summary.md` and `action_items.md` are both present.",
        "Source coverage — the latest `select_mentions` entry reports ≥2 sources, or `digest.md` is present (low-volume fallback).",
    ],
    "geo": [
        "At least one `optimized/<file>` is present with non-empty content.",
        "Every `<script type=\"application/ld+json\">` block inside an optimized file parses as valid JSON.",
    ],
    "storyboard": [
        "At least one `stories/*.json` (PLAN_STORY phase) or `storyboards/*.json` (IDEATE phase) file is present.",
        "Each story/storyboard file parses as valid JSON and the top level is an object.",
        "Each file has a non-empty `scenes` / `scene_plan` array (storyboards may fall back to `source_story_plan.scenes`).",
        "When a story declares `scene_count`, it matches the length of the scenes array.",
        "Every scene has a non-empty `prompt`.",
        "Every scene (PLAN_STORY) has a non-empty camera field — `camera`, `camera_motion`, or `camera_movement`.",
    ],
}


# Mapping from each bullet back to the gate function(s) it describes.
# Used by the bidirectional paired test to detect drift in either
# direction. Gate functions not listed here are expected to have no
# corresponding bullet (e.g., assertions Unit 12 will remove remain in
# ``_validate_monitoring`` until Unit 12 lands, and must be explicitly
# excluded from the paired test's strict-mode gate enumeration).
STRUCTURAL_GATE_FUNCTIONS: dict[str, tuple[str, ...]] = {
    "competitive": (
        "_validate_competitive.brief_exists",
        "_validate_competitive.competitor_json_parses",
    ),
    "monitoring": (
        "session_md_exists",
        "results_non_empty",
        "has_select_mentions",
        "has_cluster_stories",
        "has_synthesize",
        "has_recommend",
        "digest_exists",
        "findings_exists",
        "status_complete",
        "rec_exec_summary_and_action_items",
        "source_coverage",
    ),
    "geo": (
        "_validate_geo.optimized_non_empty",
        "_validate_geo.json_ld_parses",
    ),
    "storyboard": (
        "_validate_storyboard.files_present",
        "_validate_storyboard.json_parses",
        "_validate_storyboard.scenes_non_empty",
        "_validate_storyboard.scene_count_matches",
        "_validate_storyboard.scene_has_prompt",
        "_validate_storyboard.scene_has_camera",
    ),
}
