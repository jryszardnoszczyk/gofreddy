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
        "not asserted as \"the viewer now feels dread\" without a beat that produces dread. "
        "Look for: does the story_beats or emotional_map identify the SPECIFIC line, action, or "
        "visual that causes each emotional shift? A string like 'curiosity → dread' with no "
        "mechanism fails. An entry that says 'dread is produced when X happens because Y' passes. "
        "If emotional_map is an array where each entry has a 'mechanism' field, evaluate whether "
        "the mechanism is a concrete story event, not a restated emotion."
    ),
    "SB-4": (
        "The turn recontextualizes the beginning. By the end, the opening scene means "
        "something different than it appeared to mean. The emotional arc is not just a "
        "progression but a reframing."
    ),
    "SB-5": (
        "The voice script is performable speech with designed silence. A voice actor could "
        "perform it cold, and the audio design — including what is deliberately absent, "
        "processed, or contrasted — carries as much story as the visuals. "
        "Check: are the voice_script lines actual dialogue (words a performer speaks) rather "
        "than descriptions of what is said? Does each beat have a 'silence_seconds' field or "
        "explicit pause notation that shows where silence is deliberately placed? Does the "
        "audio_design specify when music cuts, drops, or is absent — not just when it plays? "
        "A plan that lists dialogue correctly but treats silence as absence-of-notes rather "
        "than a designed beat fails this criterion."
    ),
    "SB-6": (
        "Every scene describes something current AI video models can actually produce — not "
        "too vague (\"a person in a room\") and not too ambitious (subtle micro-expressions, "
        "specific text legibility). Consistency anchors are functional engineering decisions "
        "(what must stay identical, what may vary, and why) rather than decorative "
        "restatements of the character description. "
        "Fail if: scene prompts use asymmetric physiological details (unequal pupils, subtle tremors) "
        "as a primary story element, require legible text to convey meaning, rely on precise two-person "
        "blocking that AI cannot hold across cuts, or treat 'character looks consistent' as an anchor "
        "without specifying the exact visual elements. "
        "Pass if: each consistency_anchor names specific attributes (exact hair color+length, specific "
        "prop in exact position) with a 'must_be_identical / may_vary / why' structure, and scene "
        "prompts convey emotion through staging and props rather than facial micro-acting."
    ),
    "SB-7": (
        "The pacing matches the platform and the creator's actual rhythm — scene count, cut "
        "frequency, and duration target are grounded in how the creator's real videos move, "
        "not in how a screenplay reads. "
        "Look for a pacing_grounding section (or equivalent) that cites actual source video durations, "
        "shows the median calculation, and derives scene_count from avg_scene_duration. A plan that "
        "simply states a duration without showing the calculation from source data is under-grounded. "
        "Duration target within 80-120% of the source median and scene count matching "
        "round(duration / avg_scene_duration) both pass; significant deviations without explanation fail."
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
    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="storyboard",
    domain_name="Storyboard (Video Story Plans)",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={"SB-8": CrossItemCriterion(glob="stories/*.json", max_items=4, words_per_item=None)},
)
