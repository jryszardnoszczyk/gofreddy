"""x_engine SessionEvalSpec — per master plan v13 §4.4.

Mirrors `session_eval_geo.py` shape: 6 display-criteria strings (one per
X-1..X-6), a per-artifact `structural_gate` checking BODY/META blocks +
char_count brackets + slop-check, a `load_source_data` returning the angle
JSON + voice substrate, and a `cross_item_criteria` entry for X-6 over
`drafts/*.md`."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .session_eval_common import CrossItemCriterion, SessionEvalSpec


# Display-criteria strings — what the in-session evaluator shows the agent
# (separate from the rubric prose in src/evaluation/rubrics.py, which is
# what the FINAL judge service scores against). Both should stay aligned;
# JR review covers both at L2 prose lock-step.
CRITERIA: dict[str, str] = {
    "X-1": (
        "Voice — JR's first-person, opinionated, plain-language register, "
        "accessible to a non-engineer founder/marketer. Jargon without inline "
        "plain-English context caps this dimension."
    ),
    "X-2": (
        "Factual specificity — SOURCE claims trace to source_text; "
        "INTERPRETIVE claims framed as JR's view. HARD FLOOR: any first-person "
        "specific lived-work claim REQUIRES the named entity to appear in "
        "programs/references/voice.md."
    ),
    "X-3": (
        "Hook strength — bracket-aware. SHARP earns 5 with one sharp "
        "claim+support pair in the first 12 words. BUILD/CASE-STUDY: the "
        "first 1-2 sentences must beat the show-more cutoff."
    ),
    "X-4": (
        "Slop-freeness — zero AI-tells. Banned phrases per slop_gate.py "
        "regex are a deterministic floor; this dimension judges what slips "
        "through (parallel structures, formulaic transitions, cadence)."
    ),
    "X-5": (
        "Structural richness — bracket-aware. SHARP earns 10 with one sharp "
        "claim+support pair; BUILD with prose intro + structural pivot + "
        "3-5 bullets + authority anchor + outcome metric; CASE-STUDY with "
        "multi-paragraph narrative + sensory detail + numbers timeline + "
        "implication close. Pad-to-length = ≤4."
    ),
    "X-6": (
        "Cross-cohort — across all drafts in this session's drafts/, no two "
        "use the same primary differentiator, source, or hook archetype. "
        "Spread across voice_pillars listed in angle metadata."
    ),
    "X-9": (
        "The [BODY] block and any [REPLY] blocks contain no external URLs (http://, "
        "https://, bare domains like 'example.com/path', or markdown link syntax). URLs to "
        "x.com / twitter.com are exempt. Citations name sources inline (\"per the 2024 "
        "Buffer analysis\") rather than embedding links. Drafts with disguised redirects "
        "(URL shorteners, \"link in bio,\" \"DM for the PDF,\" QR codes, pasted reference "
        "codes) fail — the substrate must not route the user off-platform indirectly. "
        "Rationale: Buffer 2026 18.8M-post analysis shows ~0% median engagement for "
        "non-Premium link posts since March 2025; X's open-source TweetUrlMultiplier "
        "confirms 30-50% algorithm penalty. Any [BODY]/[REPLY] URL is a structural "
        "reach-failure regardless of body-text quality."
    ),
}


# Length brackets per master plan v13 §2.2.
_LENGTH_BRACKETS: dict[str, tuple[int, int]] = {
    "sharp": (250, 300),
    "build": (500, 900),
    "case_study": (1000, 1500),
}

# Required META keys per §2.2 X-shape.
_REQUIRED_META_KEYS: tuple[str, ...] = (
    "hook", "authority_anchor", "specific_number", "attribution",
)


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    """Return list of failure strings (empty list = pass). Per-artifact only;
    evaluate_session.py invokes one artifact at a time."""
    failures: list[str] = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures
    text = artifact.read_text(encoding="utf-8", errors="replace")

    # Frontmatter + length_bracket validation.
    frontmatter = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not frontmatter:
        failures.append(
            "No YAML frontmatter found. FIX: add a `---` block at the top "
            "with draft_id, angle_id, platform, length_bracket, char_count, "
            "voice_pillar."
        )
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

    # [BODY] block presence + char_count fits bracket.
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

    # [META] block + required keys.
    meta_match = re.search(r"\[META\]\s*\n(.*?)\n\[/META\]", text, re.DOTALL)
    if not meta_match:
        failures.append(
            f"No [META] block found. FIX: add [META] with keys: "
            f"{list(_REQUIRED_META_KEYS)}."
        )
        return failures
    meta_text = meta_match.group(1)
    for key in _REQUIRED_META_KEYS:
        if not re.search(rf"^{key}:\s*\S", meta_text, re.MULTILINE):
            failures.append(f"[META] missing or empty key: {key!r}.")

    # slop-check via xeng. FileNotFoundError surfaces as a structural failure
    # (xeng must be on PATH for the lane to function — silently skipping
    # would let drafts pass the regex floor on broken envs). Timeout +
    # JSONDecodeError remain best-effort: a slow xeng or malformed output
    # shouldn't block the gate, but a missing tool should.
    try:
        result = subprocess.run(
            ["xeng", "slop-check", body, "--platform", "x"],
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
        # 30s timeout — xeng is unusually slow but not a structural failure.
        # Final judge still scores X-4 against the regex floor at scoring time.
        pass

    return failures


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    """Concatenate the angle JSON (cached at session start) + the shared voice
    substrate. Both lanes' load_source_data return the same shape; the
    substrate at programs/references/voice.md lives outside `session_dir` so
    it must be loaded explicitly here for the X-2 hard-floor to verify
    lived-work claims."""
    parts: list[str] = []

    # Angle JSON — cached by the agent at session start via xeng angle-show.
    angles_dir = session_dir / "angles"
    if angles_dir.exists():
        for angle_file in sorted(angles_dir.glob("*.json"))[:1]:  # one fixture = one angle
            try:
                payload = json.loads(angle_file.read_text(encoding="utf-8", errors="replace"))
                parts.append(
                    f"## Angle (`{angle_file.name}`)\n```json\n"
                    f"{json.dumps(payload, indent=2)[:3000]}\n```"
                )
            except (json.JSONDecodeError, OSError):
                continue

    # Shared voice substrate — locked READ-ONLY; outside session_dir.
    # 2026-05-15 (task #97): use find_variant_root instead of fixed
    # parents[N] arithmetic. After the per-context isolation fix,
    # x_engine session_dir is `<variant>/sessions/x_engine/<client>/<context>/`
    # (4 levels deep) instead of `<variant>/sessions/x_engine/<client>/`
    # (3 levels deep). parents[2] would land on `sessions/`, not `<variant>/`.
    # find_variant_root walks up until it sees `sessions/` and returns the
    # variant root regardless of shape — robust to either layout.
    voice_path = None
    try:
        from harness.session_paths import find_variant_root  # type: ignore  # noqa: PLC0415
        variant_root = find_variant_root(session_dir)
        voice_path = variant_root / "programs" / "references" / "voice.md"
    except (ValueError, ImportError):
        # Fallback: legacy 2-level shape, parents[2] gives variant root.
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
    domain="x_engine",
    domain_name="X Engine",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={
        "X-6": CrossItemCriterion(
            glob="drafts/*.md",
            max_items=10,
            words_per_item=400,
        ),
    },
)
