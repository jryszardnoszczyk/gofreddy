"""article_engine SessionEvalSpec — per Content Engine Lanes v1 U13.

Mirrors `session_eval_x_engine.py` shape: per-rubric display criteria
strings, per-artifact `structural_gate` enforcing the U13 §structural
contract (frontmatter / platform / length brackets / blog schema.org
/ LinkedIn fold-safe hook / citation presence / anti-patterns), a
`load_source_data` returning the topic + source material + voice
substrate + relevant briefs, and a cross-cohort criterion for AE-8.

Per TD-40: anti-patterns YAML pre-check runs BEFORE judge dispatch;
hits cap AE-1 at 4 (penalty, not auto-reject — the surrounding prose
may still salvage the draft).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from .session_eval_common import CrossItemCriterion, SessionEvalSpec


# Display-criteria strings — what the in-session evaluator shows the
# agent. Separate from the FINAL judge rubrics in src/evaluation/
# rubrics.py (which is what the outer judge service scores against).
# Both should stay aligned at lock-step JR-review of L2 prose.
CRITERIA: dict[str, str] = {
    "AE-1": (
        "Hook — first 60 words (blog) or 210 chars (LinkedIn fold) "
        "deliver a falsifiable claim, named subject, or concrete "
        "result; testable against the body's main thesis."
    ),
    "AE-2": (
        "Thesis specificity & falsifiability — at least one claim "
        "a thoughtful operator could disagree with publicly. Floor: "
        "≥3 concrete numeric/named-entity claims per 1,000 words."
    ),
    "AE-3": (
        "Citation density + verifier rate — every numeric/attributive "
        "claim carries an inline [N] reference traceable to brief.source_id, "
        "voice.md entity, or verifier-checked URL. Untraceable = "
        "structural fail."
    ),
    "AE-4": (
        "Voice fidelity — first-person operator voice; lived-work "
        "claims name entities in voice.md; no slop register words."
    ),
    "AE-5": (
        "Argument coherence — visible problem → mechanism → evidence "
        "→ implication arc. Paragraphs NOT freely reorderable."
    ),
    "AE-6": (
        "Skimmability — subheads every 200-300 words; paragraphs ≤4 "
        "sentences (blog) / ≤3 (LinkedIn); one TL;DR or summary callout."
    ),
    "AE-7": (
        "Platform-adapter compliance — blog: H1 + meta 140-160 chars "
        "+ schema.org Article JSON + image briefs. LinkedIn Article: "
        "210-char fold hook + 3-5 hashtags + no markdown headers."
    ),
    "AE-8": (
        "Cross-cohort diversity — no two drafts in this batch share "
        "opening pattern, thesis shape, or named-entity invocation."
    ),
}


# Length brackets per TD-40 — blog (standard / deep_dive) +
# linkedin_article (short / long). Hard caps fall outside these
# bounds → structural fail; rubric AE-7 scores qualitative platform
# fit within the brackets.
_LENGTH_BRACKETS_BY_PLATFORM: dict[str, dict[str, tuple[int, int]]] = {
    "blog": {
        "standard": (1500, 2500),
        "deep_dive": (2200, 3500),
    },
    "linkedin_article": {
        "short": (1200, 1500),
        "long": (1500, 2200),
    },
}

# Hard caps per platform (outside these = structural fail regardless
# of length_bracket). Mirrors TD-40 line 1400.
_HARD_CAPS_BY_PLATFORM: dict[str, tuple[int, int]] = {
    "blog": (800, 4000),
    "linkedin_article": (600, 2200),
}

# Required frontmatter keys per U13 §structural contract.
_REQUIRED_FRONTMATTER_KEYS: tuple[str, ...] = (
    "draft_id", "topic", "platform", "length_bracket",
    "voice_persona", "word_count",
)


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter dict or None if absent/invalid."""
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _word_count(text: str) -> int:
    """Approximate word count — splits on whitespace. Article-engine
    length brackets are tolerant enough that approximate counts suffice."""
    return len(text.split())


def _load_anti_patterns(variant_root: Path) -> list[dict] | None:
    """Load the lane's anti_patterns.yml. Returns None on missing/
    malformed file (logged via the gate's failure list)."""
    path = variant_root / "templates" / "article_engine" / "anti_patterns.yml"
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    patterns = data.get("patterns")
    return patterns if isinstance(patterns, list) else None


def _find_variant_root(session_dir: Path) -> Path | None:
    """Walk up from session_dir to find the variant root (the dir
    containing programs/, templates/, workflows/)."""
    try:
        from harness.session_paths import find_variant_root  # type: ignore  # noqa: PLC0415
        return find_variant_root(session_dir)
    except (ValueError, ImportError):
        if len(session_dir.parents) > 2:
            return session_dir.parents[2]
    return None


def structural_gate(_mode: str, artifact: Path, session_dir: Path) -> list[str]:
    """Per-artifact structural gate. Returns list of failure strings
    (empty list = pass)."""
    failures: list[str] = []
    if not artifact.exists():
        failures.append(f"Artifact not found: {artifact}")
        return failures
    text = artifact.read_text(encoding="utf-8", errors="replace")

    # Frontmatter parse + required keys
    fm = _parse_frontmatter(text)
    if fm is None:
        failures.append(
            "No YAML frontmatter found OR invalid YAML. FIX: add a `---` "
            f"block at the top with: {list(_REQUIRED_FRONTMATTER_KEYS)}."
        )
        return failures
    missing = [k for k in _REQUIRED_FRONTMATTER_KEYS if k not in fm]
    if missing:
        failures.append(f"Frontmatter missing required keys: {missing}.")
        return failures

    platform = fm.get("platform")
    if platform not in _LENGTH_BRACKETS_BY_PLATFORM:
        failures.append(
            f"platform={platform!r} invalid; must be one of "
            f"{list(_LENGTH_BRACKETS_BY_PLATFORM)}."
        )
        return failures

    bracket = fm.get("length_bracket")
    brackets = _LENGTH_BRACKETS_BY_PLATFORM[platform]
    if bracket not in brackets:
        failures.append(
            f"length_bracket={bracket!r} invalid for platform={platform!r}; "
            f"must be one of {list(brackets)}."
        )
        return failures

    # Body extraction — drafts are markdown; "body" = everything after
    # frontmatter, with the frontmatter stripped. (Article_engine doesn't
    # use [BODY] sentinels like x_engine — articles are normal markdown.)
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)
    word_count = _word_count(body)

    # Hard caps first — outside these = structural fail.
    hard_lo, hard_hi = _HARD_CAPS_BY_PLATFORM[platform]
    if not (hard_lo <= word_count <= hard_hi):
        failures.append(
            f"word_count={word_count} outside hard caps for {platform} "
            f"[{hard_lo}, {hard_hi}]. Structural fail."
        )
        return failures

    # Length-bracket check (within hard caps but outside bracket = note).
    lo, hi = brackets[bracket]
    if not (lo <= word_count <= hi):
        failures.append(
            f"word_count={word_count} outside {bracket} bracket [{lo}, {hi}] "
            f"for platform={platform!r}. The draft is within hard caps but "
            f"the bracket should match — either pick a different bracket or "
            f"adjust the word count."
        )

    # Platform-specific structural requirements
    if platform == "blog":
        failures.extend(_blog_structural_checks(text, fm))
    elif platform == "linkedin_article":
        failures.extend(_linkedin_article_structural_checks(text, body, fm))

    # Citation check — every numeric/attributive claim should carry [N]
    # references; flag obvious anti-patterns. The full traceability
    # check happens at evaluate-variant time (verifier fires post-gate),
    # so this is a structural lower-bound only.
    failures.extend(_citation_anti_pattern_checks(body))

    # Anti-patterns YAML deterministic pre-check (TD-40 — 12 patterns).
    variant_root = _find_variant_root(session_dir)
    if variant_root is not None:
        anti_patterns = _load_anti_patterns(variant_root)
        if anti_patterns:
            hits = _check_anti_patterns(body, anti_patterns)
            if hits:
                # Per TD-40: cap AE-1 at 4 (penalty, not auto-reject).
                # The gate notes the hits; the judge applies the cap.
                failures.append(
                    f"anti_patterns hits ({len(hits)}): "
                    f"{hits[:3]}{'...' if len(hits) > 3 else ''}. "
                    f"Score penalty applies; revise prose."
                )

    return failures


def _blog_structural_checks(text: str, fm: dict) -> list[str]:
    """Blog-specific checks per U13: H1 + meta + schema.org + image briefs."""
    failures: list[str] = []

    # H1 (markdown `# Headline` on a top-level line)
    if not re.search(r"^# \S", text, re.MULTILINE):
        failures.append(
            "Blog missing H1 (top-level `# Headline` line). Add an H1 "
            "matching the article title."
        )

    # Meta description (in frontmatter or [META] block)
    meta_desc = fm.get("meta_description") or ""
    if not meta_desc:
        meta_match = re.search(
            r"^meta_description:\s*[\"']?(.*?)[\"']?\s*$", text, re.MULTILINE,
        )
        meta_desc = meta_match.group(1) if meta_match else ""
    if not meta_desc:
        failures.append(
            "Blog missing meta_description (140-160 chars) in frontmatter."
        )
    elif not (140 <= len(meta_desc) <= 160):
        failures.append(
            f"Blog meta_description length={len(meta_desc)} outside "
            f"[140, 160]. Adjust for SEO snippet rendering."
        )

    # schema.org Article JSON block (look for ```json fenced block)
    schema_match = re.search(
        r"```json\s*\n(.*?)\n```", text, re.DOTALL,
    )
    schema_ok = False
    if schema_match:
        try:
            schema = json.loads(schema_match.group(1))
            if isinstance(schema, dict):
                schema_ok = all(
                    k in schema for k in
                    ("headline", "author", "datePublished", "image")
                )
        except json.JSONDecodeError:
            pass
    if not schema_ok:
        failures.append(
            "Blog missing schema.org Article JSON or missing required "
            "keys {headline, author, datePublished, image}. Add a "
            "```json fenced block with the Article schema."
        )

    # Image briefs — look for "hero image" + at least one "inline image"
    if not re.search(r"hero image", text, re.IGNORECASE):
        failures.append("Blog missing hero image brief.")
    inline_count = len(re.findall(r"inline image", text, re.IGNORECASE))
    if inline_count < 1:
        failures.append("Blog missing inline image brief (≥1 required).")

    return failures


def _linkedin_article_structural_checks(
    text: str, body: str, fm: dict,
) -> list[str]:
    """LinkedIn Article-specific checks per U13: fold-safe hook + hashtags
    + no markdown headers (LI strips them)."""
    failures: list[str] = []

    # Fold-safe hook — first 210 chars of body must hold; not start
    # with a markdown header.
    fold = body.lstrip()[:210]
    if not fold:
        failures.append("LinkedIn Article body is empty above the fold.")
    elif fold.lstrip().startswith("#"):
        failures.append(
            "LinkedIn Article opens with a markdown `#` header. LI strips "
            "headers; use bold + line breaks instead."
        )

    # Hashtag count (3-5)
    hashtag_count = len(re.findall(r"(?:^|\s)#\w+", body))
    if not (3 <= hashtag_count <= 5):
        failures.append(
            f"LinkedIn Article hashtag count={hashtag_count} outside "
            f"[3, 5]. Adjust hashtags to the algorithm-friendly range."
        )

    # No `#` markdown headers anywhere in body
    if re.search(r"^#{1,6}\s", body, re.MULTILINE):
        failures.append(
            "LinkedIn Article contains markdown headers (`# Headline`). "
            "LI strips these; use **bold** + line breaks instead."
        )

    return failures


def _citation_anti_pattern_checks(body: str) -> list[str]:
    """Flag obvious anti-patterns the AE-3 rubric penalizes. Full
    traceability verification fires at evaluate-variant time (the
    citation_verifier handles URL fetch + claude verification)."""
    failures: list[str] = []
    # "studies show" / "experts say" / "research indicates" without
    # inline citation — anti-pattern per AE-3.
    bad_attributive = re.findall(
        r"\b(studies show|experts say|research (indicates|suggests|shows))"
        r"(?![^.]*?\[\d+\])",
        body, re.IGNORECASE,
    )
    if bad_attributive:
        failures.append(
            f"AE-3 anti-pattern: {len(bad_attributive)} attributive "
            f"phrase(s) without inline citation. 'Studies show' / "
            f"'experts say' must carry [N] reference + named source."
        )
    return failures


def _check_anti_patterns(body: str, patterns: list[dict]) -> list[str]:
    """Run the 12 anti-pattern regexes from anti_patterns.yml; return
    list of matched pattern names."""
    hits: list[str] = []
    body_lower = body.lower()
    for entry in patterns:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "unnamed")
        pattern = entry.get("regex")
        if not isinstance(pattern, str):
            continue
        try:
            if re.search(pattern, body_lower, re.IGNORECASE):
                hits.append(name)
        except re.error:
            continue
    return hits


def load_source_data(_mode: str, artifact: Path, session_dir: Path) -> str:
    """Concatenate: topic + source material (operator-curated) + voice
    substrate. The judge service sees this alongside the artifact at
    scoring time."""
    parts: list[str] = []

    topic = os.environ.get("ARTICLE_ENGINE_TOPIC", "").strip()
    if topic:
        parts.append(f"## Topic\n{topic}")

    # Source material — operator-curated handoff content. Read from
    # the env var that the lane's configure_env wires from the
    # client config. If the path resolves to a real list, walk it
    # via the shared loader.
    sm_paths_raw = os.environ.get("ARTICLE_ENGINE_SOURCE_MATERIAL_PATHS", "").strip()
    if sm_paths_raw:
        try:
            from src.source_material.loader import load_source_material  # noqa: PLC0415
            sm_paths = [Path(p.strip()) for p in sm_paths_raw.split(",") if p.strip()]
            sm_files = load_source_material(sm_paths)
            if sm_files:
                sm_chunks = [
                    f"### {f.path.name} ({f.format})\n{f.text[:5000]}"
                    for f in sm_files
                ]
                parts.append("## Source Material\n" + "\n\n".join(sm_chunks))
        except (ImportError, FileNotFoundError):
            # Source-material loader unavailable or path missing —
            # surface via the lane's session log, not the source data.
            pass

    # Voice substrate — compiled at configure_env time, lives at
    # current_runtime/programs/references/voice.md.
    variant_root = _find_variant_root(session_dir)
    if variant_root is not None:
        voice_path = variant_root / "programs" / "references" / "voice.md"
        if voice_path.is_file():
            try:
                parts.append(
                    f"## Voice substrate\n"
                    f"{voice_path.read_text(encoding='utf-8', errors='replace')[:4000]}"
                )
            except OSError:
                pass

    return "\n\n".join(parts)


# Structural gate functions referenced by LaneSpec.structural_gate_functions.
# Each is a thin lambda wrapping the per-aspect check inside structural_gate;
# evaluate_session's test_structural_doc_facts assertion looks these up by
# qualified name (matches the x_engine / linkedin_engine pattern).

def frontmatter_yaml_required_fields(artifact: Path, session_dir: Path) -> list[str]:
    """Subset of structural_gate — frontmatter parse + required keys."""
    return [f for f in structural_gate("full", artifact, session_dir)
            if "Frontmatter" in f or "frontmatter" in f]


def platform_valid(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "platform=" in f]


def length_bracket_valid(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "length_bracket=" in f or "bracket [" in f]


def word_count_fits_bracket(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "word_count=" in f]


def blog_meta_and_schema_present(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "meta_description" in f or "schema.org" in f or "H1" in f
            or "image brief" in f]


def linkedin_fold_hook_present(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "fold" in f or "hashtag" in f.lower() or "markdown header" in f.lower()]


def every_claim_has_citation(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "AE-3" in f or "citation" in f.lower()]


def anti_patterns_within_threshold(artifact: Path, session_dir: Path) -> list[str]:
    return [f for f in structural_gate("full", artifact, session_dir)
            if "anti_patterns" in f.lower()]


# os import for the load_source_data env var reads
import os  # noqa: E402


SPEC = SessionEvalSpec(
    domain="article_engine",
    domain_name="Article Engine",
    criteria=CRITERIA,
    structural_gate=structural_gate,
    load_source_data=load_source_data,
    cross_item_criteria={
        "AE-8": CrossItemCriterion(
            glob="drafts/*.md",
            max_items=10,
            words_per_item=600,  # bigger than X drafts; articles are longer
        ),
    },
)
