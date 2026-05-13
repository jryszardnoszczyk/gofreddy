from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import (
    CrossItemCriterion,
    SessionEvalSpec,
    artifact_or_failure,
    truncate,
)


# Structural-validator bullets — see session_eval_geo.STRUCTURAL_DOC_FACTS for
# the contract these enforce. ``autoresearch.regen_program_docs`` reads this
# tuple when stamping the AUTOGEN block in ``programs/storyboard-session.md``.
STRUCTURAL_DOC_FACTS: tuple[str, ...] = (
    "At least one `stories/*.json` (PLAN_STORY phase) or `storyboards/*.json` (IDEATE phase) file is present.",
    "Each story/storyboard file parses as valid JSON and the top level is an object.",
    "Each file has a non-empty `scenes` / `scene_plan` array (storyboards may fall back to `source_story_plan.scenes`).",
    "When a story declares `scene_count`, it matches the length of the scenes array.",
    "Every scene has a non-empty `prompt`.",
    "Every scene (PLAN_STORY) has a non-empty camera field — `camera`, `camera_motion`, or `camera_movement`.",
)


CRITERIA: dict[str, str] = {
    "SB-1": (
        "The plan cites at least 3 distinct creator-specific pattern details, each meeting "
        "all three tests: source-cited (names which prior creator output the reference draws "
        "from — episode, video title, or pattern_id), passes the creator-substitution test "
        "(replacing the pattern data with a different creator's would break the reference), "
        "AND plan-shaping (drives a concrete storytelling choice — scene order, surprise "
        "mechanism, character reaction — not just a name-drop in setup paragraph). Score 3: "
        "references abstract enough that a different creator's pattern data could plausibly "
        "fit. Anti-gaming: 3 creator-specific name-drops concentrated in the first "
        "paragraph followed by a generic plan body fails — references must distribute "
        "across the plan's actual structural choices."
    ),
    "SB-2": (
        "The hook is immediately arresting AND passes the substitution test: removing or "
        "changing the specific creator, setting, or stakes would break the hook's appeal. "
        "The hook depends on this story's specific context for its impact — at least one "
        "element a competing creator could not replicate without copying this story's "
        "specific premise. Score 3: hook has a specific element but could exist in a "
        "different story unchanged — identifiable, not irreplaceable. Anti-gaming: generic "
        "high-stakes phrasing (\"a man with everything to lose,\" \"the impossible "
        "choice\") that could attach to any story fails."
    ),
    "SB-3": (
        "Each emotion in emotional_map maps to a specific beat containing a diegetic cause "
        "— a revelation, action, or juxtaposition that would produce that emotion in a "
        "viewer who didn't yet know what to feel (cause must be on-screen content, not "
        "narration about feelings). Transitions are justified by content the viewer just "
        "received, with the transition's logic visible in the preceding beat — not by the "
        "emotional_map asserting them. The climactic emotional moment rests on context "
        "unique to THIS story, not on a generic dramatic structure (sacrifice, recognition, "
        "reversal) any story in the genre could use. A viewer reading beats in order with "
        "the emotional_map hidden would experience the predicted emotions inevitably. "
        "Anti-gaming: beats that say \"the viewer feels X\" without a cause the viewer "
        "would experience fail."
    ),
    "SB-4": (
        "The turn recontextualizes the beginning. By the end, the opening scene means "
        "something different than it appeared to mean. The emotional arc is not just a "
        "progression but a reframing."
    ),
    "SB-5": (
        "Voice script delivery directions vary line-to-line to track each line's "
        "rhetorical purpose — not the same instruction (\"intense,\" \"slow and "
        "measured\") attached to every dramatic line. Silence/absence is specified as a "
        "timed beat with a stated narrative function (\"0:42-0:45 three seconds silence, "
        "marking the moment the character realizes\") — not just \"dramatic pause.\" "
        "Vocal-quality shifts map to specific story turns with explicit story-event tie. "
        "At least one audio element (music cue, SFX, silence) carries story information "
        "the visuals and voice do NOT — a sound revealing what the camera doesn't show, a "
        "music shift contradicting dialogue's surface meaning. Anti-gaming: music labeled "
        "\"tension\" or \"release\" that just underscores what visuals already show fails."
    ),
    "SB-6": (
        "Every scene describes something current AI video models can actually produce — not "
        "too vague (\"a person in a room\") and not too ambitious (subtle micro-expressions, "
        "specific text legibility). Consistency anchors are functional engineering decisions "
        "(what must stay identical, what may vary, and why) rather than decorative "
        "restatements of the character description."
    ),
    "SB-7": (
        "The pacing matches the platform and the creator's actual rhythm — scene count, cut "
        "frequency, and duration target are grounded in how the creator's real videos move, "
        "not in how a screenplay reads."
    ),
    "SB-8": (
        "The five plans are genuinely different bets — different premises, different "
        "emotional registers, different structural choices — while sharing a creative "
        "universe. They are not five variations on the plan the AI found easiest to generate."
    ),
}

def structural_gate(_mode: str, artifact: Path, _session_dir: Path) -> list[str]:
    early = artifact_or_failure(artifact)
    if early is not None:
        return early
    failures: list[str] = []

    try:
        data = json.loads(artifact.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        failures.append(f"Invalid JSON: {exc}")
        return failures

    if not isinstance(data, dict):
        failures.append("JSON root is not an object")
        return failures

    for field in ("duration_target_seconds", "scene_count", "voice_script"):
        if not data.get(field):
            failures.append(f"Missing or empty field: {field}")

    scenes = data.get("scenes")
    if scenes is not None:
        if not isinstance(scenes, list):
            failures.append("'scenes' field is not an array")
        elif data.get("scene_count") and len(scenes) != data["scene_count"]:
            failures.append(f"scene_count={data['scene_count']} but scenes array has {len(scenes)} entries")
    return failures


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    parts: list[str] = []
    patterns_dir = session_dir / "patterns"
    if patterns_dir.exists():
        for path in sorted(patterns_dir.glob("*.json"))[:5]:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            parts.append(f"## Pattern: {path.name}\n```json\n{truncate(content, 1000)}\n```")
    stories_dir = session_dir / "stories"
    if stories_dir.exists():
        for path in sorted(stories_dir.glob("*.json"))[:5]:
            if path.resolve() == artifact.resolve():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            parts.append(f"## Prior Story Plan: {path.name}\n```json\n{truncate(content, 1500)}\n```")
    fmd = session_dir / "findings.md"
    if fmd.exists():
        try: parts.append(f"## Creative Intent\n{fmd.read_text(encoding='utf-8', errors='replace')[:1500]}")
        except OSError: pass
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="storyboard",
    domain_name="Storyboard (Video Story Plans)",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={"SB-8": CrossItemCriterion(glob="stories/*.json", max_items=4, words_per_item=None)},
)
