"""linkedin_engine SessionEvalSpec — sibling to session_eval_x_engine.py.

Per master plan v13 §4.4. Same shape with platform divergences:
- length brackets: short_take (500-900), thought_leader (1500-2500),
  case_study (2500-3000)
- [META] requires `hashtags` field (in addition to X's required keys)
- structural_gate enforces hashtag count ∈ [1, 5] (0 blocked at structural,
  quality on count goes to LI-5; >5 spam guardrail blocked at structural)
- slop-check called with --platform linkedin
- cross-item words_per_item=600 (LinkedIn drafts are longer than X)
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .session_eval_common import CrossItemCriterion, SessionEvalSpec


CRITERIA: dict[str, str] = {
    "LI-1": (
        "Voice — JR's LinkedIn first-person, story-led, professional register, "
        "accessible to B2B buyers + agency operators + C-suite. The lever is "
        "thoughtful authority, not contrarian punch. AUTOMATIC ≤4 if the "
        "draft reads as bait-y or Twitter-translated."
    ),
    "LI-2": (
        "Factual specificity — same SOURCE/INTERPRETIVE split as X-2. HARD "
        "FLOOR: lived-work claims REQUIRE the named entity in voice.md. "
        "Score capped at 7 for any first-person specific claim that doesn't "
        "name the entity (LinkedIn audience punishes vague specificity harder)."
    ),
    "LI-3": (
        "Hook strength — story-led + concrete-result openings. PUNISHES "
        "contrarian hot-takes that work on X (≤3 even when the same hook "
        "would score 5 on X). First 1-2 sentences must beat the show-more "
        "cutoff at ~210 chars."
    ),
    "LI-4": (
        "Slop-freeness — zero AI-tells AND zero LinkedIn-AI-tells. "
        "Banned phrases per slop_gate.py --platform linkedin regex are a "
        "deterministic floor; this dimension judges what slips through "
        "(`Thoughts? 👇`, `Agree? 🤔`, `Here's what I learned.` close, etc.)."
    ),
    "LI-5": (
        "Structural richness + hashtag-count quality. Bracket-aware: "
        "SHORT_TAKE/THOUGHT_LEADER/CASE_STUDY each have distinct structural "
        "bars. 3-5 targeted hashtags = ideal; 1-2 = suboptimal (cap at 7); "
        "0 = ≤4. Spam (>5) is hard-failed by structural_gate."
    ),
    "LI-6": (
        "Cross-cohort — narrative archetype variance (story-led vs lesson-led "
        "vs comparison vs case-study) AND voice_pillar spread. Punishes "
        "same-tone-same-format streaks. Hashtag-set diversity is NOT scored "
        "here (per-pillar drafts may legitimately share signature combos)."
    ),
}


_LENGTH_BRACKETS: dict[str, tuple[int, int]] = {
    "short_take": (500, 900),
    "thought_leader": (1500, 2500),
    "case_study": (2500, 3000),
}

# X-shape required META keys + hashtags (LinkedIn-only).
_REQUIRED_META_KEYS: tuple[str, ...] = (
    "hook", "authority_anchor", "specific_number", "attribution", "hashtags",
)

# LinkedIn hashtag count bounds enforced at structural_gate. >5 = spam
# guardrail; 0 ships are blocked too (zero-tag posts get less LinkedIn
# distribution; LI-5 quality on count handles 1-2 vs 3-5 grading).
_HASHTAG_MIN, _HASHTAG_MAX = 1, 5


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    failures: list[str] = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures
    text = artifact.read_text(encoding="utf-8", errors="replace")

    # Frontmatter + length_bracket.
    frontmatter = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not frontmatter:
        failures.append("No YAML frontmatter found.")
        return failures
    fm_text = frontmatter.group(1)
    bracket_match = re.search(r"^length_bracket:\s*(\w+)", fm_text, re.MULTILINE)
    if not bracket_match:
        failures.append("Frontmatter missing `length_bracket` field.")
        return failures
    bracket = bracket_match.group(1)
    if bracket not in _LENGTH_BRACKETS:
        failures.append(
            f"length_bracket={bracket!r} invalid; must be one of "
            f"{list(_LENGTH_BRACKETS)}."
        )
        return failures

    # [BODY] presence + bracket fit.
    body_match = re.search(r"\[BODY\]\s*\n(.*?)\n\[/BODY\]", text, re.DOTALL)
    if not body_match:
        failures.append("No [BODY] block found.")
        return failures
    body = body_match.group(1).strip()
    if not body:
        failures.append("[BODY] block is empty.")
    body_chars = len(body)
    lo, hi = _LENGTH_BRACKETS[bracket]
    if not (lo <= body_chars <= hi):
        failures.append(
            f"[BODY] char_count={body_chars} outside {bracket} bracket [{lo}, {hi}]."
        )

    # [META] presence + required keys (incl. hashtags).
    meta_match = re.search(r"\[META\]\s*\n(.*?)\n\[/META\]", text, re.DOTALL)
    if not meta_match:
        failures.append(
            f"No [META] block found. Required keys: {list(_REQUIRED_META_KEYS)}."
        )
        return failures
    meta_text = meta_match.group(1)
    for key in _REQUIRED_META_KEYS:
        if not re.search(rf"^{key}:\s*\S", meta_text, re.MULTILINE):
            failures.append(f"[META] missing or empty key: {key!r}.")

    # Hashtag count in [1, 5]. Both deterministic gates. The count check fires
    # whenever the `hashtags:` field exists in [META] — including the empty-
    # quoted-string case `hashtags: ""` — because LI-5 requires ≥1 tag for
    # LinkedIn distribution.
    hashtags_match = re.search(r"^hashtags:\s*(.+?)\s*$", meta_text, re.MULTILINE)
    if hashtags_match:
        raw = hashtags_match.group(1).strip().strip('"').strip("'")
        tags = [t.strip() for t in raw.split(",") if t.strip()] if raw else []
        n = len(tags)
        if n < _HASHTAG_MIN:
            failures.append(
                f"[META] hashtags count={n} below LinkedIn floor "
                f"({_HASHTAG_MIN}); zero-tag posts get less distribution."
            )
        if n > _HASHTAG_MAX:
            failures.append(
                f"[META] hashtags count={n} above spam guardrail "
                f"({_HASHTAG_MAX}). Reduce to 3-5 targeted tags."
            )

    # slop-check via xeng --platform linkedin. Missing xeng surfaces as a
    # structural failure (per session_eval_x_engine pattern); timeout/json
    # errors remain best-effort.
    try:
        result = subprocess.run(
            ["xeng", "slop-check", body, "--platform", "linkedin"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                payload = None
            if payload and not payload.get("passed"):
                flags = payload.get("phrase_flags") or []
                failures.append(
                    f"slop-check failed: {flags[:3]}"
                    f"{'...' if len(flags) > 3 else ''}"
                )
    except FileNotFoundError:
        failures.append(
            "xeng not on PATH — slop-check could not run. "
            "Verify the variant's PATH includes the venv with xeng installed."
        )
    except subprocess.TimeoutExpired:
        pass

    return failures


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    """Same shape as x_engine — angle JSON + voice substrate. Both lanes
    share the substrate (single source of truth for JR-identity + named
    lived-work entities)."""
    parts: list[str] = []

    angles_dir = session_dir / "angles"
    if angles_dir.exists():
        for angle_file in sorted(angles_dir.glob("*.json"))[:1]:
            try:
                payload = json.loads(angle_file.read_text(encoding="utf-8", errors="replace"))
                parts.append(
                    f"## Angle (`{angle_file.name}`)\n```json\n"
                    f"{json.dumps(payload, indent=2)[:3000]}\n```"
                )
            except (json.JSONDecodeError, OSError):
                continue

    # 2026-05-15 (task #97): use find_variant_root — see x_engine eval
    # for full rationale (per-context isolation deepens session_dir).
    voice_path = None
    try:
        from harness.session_paths import find_variant_root  # type: ignore  # noqa: PLC0415
        variant_root = find_variant_root(session_dir)
        voice_path = variant_root / "programs" / "references" / "voice.md"
    except (ValueError, ImportError):
        if len(session_dir.parents) > 2:
            voice_path = session_dir.parents[2] / "programs" / "references" / "voice.md"
    if voice_path is not None and voice_path.exists():
        try:
            voice_text = voice_path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"## Voice substrate (programs/references/voice.md)\n{voice_text[:4000]}")
        except OSError:
            pass

    return "\n\n".join(parts)


SPEC = SessionEvalSpec(
    domain="linkedin_engine",
    domain_name="LinkedIn Engine",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={
        "LI-6": CrossItemCriterion(
            glob="drafts/*.md",
            max_items=10,
            words_per_item=600,
        ),
    },
)
