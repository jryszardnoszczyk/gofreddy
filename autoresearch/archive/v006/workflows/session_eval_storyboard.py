from __future__ import annotations

import json
from pathlib import Path

from .session_eval_common import (
    CrossItemCriterion,
    SessionEvalSpec,
    truncate,
)


CRITERIA: dict[str, str] = {
    "SB-1": (
        "The story feels like the creator made it — not like someone studied the creator and "
        "generated a plausible imitation. Voice, obsessions, worldview, and the specific way "
        "they surprise an audience are all present."
    ),
    "SB-2": (
        "The hook is irreplaceable — a concrete, specific image or sentence that could not "
        "come from any other story. Something you would describe to a friend in one breath. "
        "The mechanism may be an impossible concept, raw emotional vulnerability, absurd "
        "juxtaposition, or visual impossibility — what matters is specificity and "
        "irreplaceability, not which mechanism achieves them."
    ),
    "SB-3": (
        "Every emotional transition in the story is earned by a specific beat, not just "
        "declared in metadata. The emotional arc described in the plan is actually produced "
        "by the story structure — through concrete revelations, actions, or juxtapositions — "
        "not asserted as \"the viewer now feels dread\" without a beat that produces dread."
    ),
    "SB-4": (
        "The turn recontextualizes the beginning. By the end, the opening scene means "
        "something different than it appeared to mean. The emotional arc is not just a "
        "progression but a reframing."
    ),
    "SB-5": (
        "The voice script is performable speech with designed silence. A voice actor could "
        "perform it cold, and the audio design — including what is deliberately absent, "
        "processed, or contrasted — carries as much story as the visuals."
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
    failures = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures

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
