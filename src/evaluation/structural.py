"""Structural gate — Layer 2 of evaluation pipeline.

Domain-specific validation that outputs have the right shape
before LLM judges run. Free, deterministic, fast.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class StructuralResult:
    """Result of structural gate validation."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    dqs_score: float | None = None  # Monitoring only: Digest Quality Score


async def structural_gate(domain: str, outputs: dict[str, str]) -> StructuralResult:
    """Run domain-specific structural validation.

    Async because the monitoring validator includes a claim-grounding
    agent call (R-#37). Sync validators (geo/competitive/storyboard)
    return immediately; only monitoring awaits a Sonnet call, and only
    when ``session.md`` contains side-effect claims worth verifying.

    Args:
        domain: One of "geo", "competitive", "monitoring", "storyboard".
        outputs: {filename: content} dict of generated outputs.

    Returns:
        StructuralResult with pass/fail and failure reasons.
    """
    if domain == "geo":
        return _validate_geo(outputs)
    if domain == "competitive":
        return _validate_competitive(outputs)
    if domain == "storyboard":
        return _validate_storyboard(outputs)
    if domain == "monitoring":
        return await _validate_monitoring(outputs)
    if domain == "marketing_audit":
        return _validate_marketing_audit(outputs)
    return StructuralResult(passed=False, failures=[f"Unknown domain: {domain}"])


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
    """CI: brief.md exists and is non-empty; at least one competitors/*.json parses.

    Shape-only checks by default — no content rules. A missing or entirely empty
    brief is a structural failure; anything past that is a quality
    question for the gradient + calibration judges (R-#35 dropped the
    `<500 chars` + `<3 headers` gates because length/header count is
    not a quality signal).

    When ``CI_STRUCTURAL_V33=1``, runs the v3.3 9-check expansion: the
    existing 2 shape checks plus 2 new shape checks (word count band,
    Klue 5-section spine) and 5 anti-hallucination checks (URL validity,
    quote-grep against competitor corpus, entity-existence, "as of" date
    marker, ≥1 cited date within 90 days). Default OFF preserves the
    live freddy-eval contract; variant_scorer.py sets the env when
    running evolution under v3.3 (see scope-B implementation 2026-05-18).
    """
    failures: list[str] = []

    # Find brief file
    brief_files = {k: v for k, v in outputs.items() if "brief" in k.lower() and k.endswith(".md")}
    if not brief_files:
        failures.append("No brief.md found")
        return StructuralResult(passed=False, failures=failures)

    brief_content = next(iter(brief_files.values()))

    # Genuinely-absent content is still a structural failure; >50-char
    # non-whitespace floor distinguishes "empty file" from "real output".
    if not brief_content or len(brief_content.strip()) < 50:
        failures.append("Brief content empty or effectively empty (<50 chars of non-whitespace)")
        return StructuralResult(passed=False, failures=failures)

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
    parsed_competitors: dict[str, dict] = {}
    if not competitor_files:
        failures.append("No competitors/*.json — brief has no underlying data")
    else:
        for fname, content in competitor_files.items():
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    parsed_competitors[fname] = parsed
            except json.JSONDecodeError:
                failures.append(f"{fname}: invalid JSON")
        if not parsed_competitors:
            failures.append("No competitors/*.json parses as JSON")

    # v3.3 extension: 7 additional deterministic checks when env-gated on.
    if _ci_v33_enabled():
        failures.extend(_ci_check_brief_word_count(brief_content))
        failures.extend(_ci_check_klue_spine(brief_content))
        failures.extend(_ci_check_url_syntactic_validity(brief_content))
        failures.extend(_ci_check_quote_grep(brief_content, parsed_competitors))
        failures.extend(_ci_check_entity_existence(brief_content, list(parsed_competitors.keys())))
        failures.extend(_ci_check_as_of_marker(brief_content))
        failures.extend(_ci_check_recent_date(brief_content))

    return StructuralResult(passed=len(failures) == 0, failures=failures)


# ─── v3.3 CI structural-gate extensions (env-gated by CI_STRUCTURAL_V33) ──
# Each helper returns a list[str] of failure strings (empty on pass) so the
# composite validator can extend its own failures list directly.
#
# Spec: docs/handoffs/2026-05-17-judge-design-step1-competitive.md §3.
# 5 anti-hallucination + 4 shape-conformance = 9 total deterministic checks
# (the 4 shape checks = the 2 existing + the 2 added here).


def _ci_v33_enabled() -> bool:
    """Read at call-time so monkeypatch can flip behaviour per-test."""
    return os.environ.get("CI_STRUCTURAL_V33", "0") == "1"


# §1.5 artifact-shape lock: 800-2,000 words total.
_CI_V33_WORD_MIN = 800
_CI_V33_WORD_MAX = 2_000


def _ci_check_brief_word_count(brief: str) -> list[str]:
    word_count = len(brief.split())
    if word_count < _CI_V33_WORD_MIN:
        return [
            f"v3.3 shape: brief word count {word_count} below floor "
            f"{_CI_V33_WORD_MIN} (Klue executive-briefing format requires "
            f"800–2,000 words)"
        ]
    if word_count > _CI_V33_WORD_MAX:
        return [
            f"v3.3 shape: brief word count {word_count} above ceiling "
            f"{_CI_V33_WORD_MAX} (Klue executive-briefing format requires "
            f"800–2,000 words; longer outputs route to teardown shape, "
            f"which is out-of-scope for this lane)"
        ]
    return []


# §1.5 Klue 5-section spine: headline-as-claim → rationale → comparison →
# implications → recommendations. Check section headers exist (case-insensitive,
# tolerant of synonym variants the judges accept).
_CI_V33_KLUE_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("headline", ("headline", "thesis", "claim", "tldr", "summary")),
    ("rationale", ("rationale", "reasoning", "background", "why this matters")),
    ("comparison", ("comparison", "competitors", "landscape", "alternatives", "competitive")),
    ("implications", ("implications", "so what", "consequences", "impact")),
    ("recommendations", ("recommendation", "next step", "action item")),
)


def _ci_check_klue_spine(brief: str) -> list[str]:
    """Each of the 5 Klue spine sections must be present as a heading."""
    header_lines = [
        line.lstrip("#").strip().lower()
        for line in brief.splitlines()
        if line.lstrip().startswith("#")
    ]
    missing: list[str] = []
    for canonical, synonyms in _CI_V33_KLUE_SECTIONS:
        if not any(any(s in h for s in synonyms) for h in header_lines):
            missing.append(canonical)
    if missing:
        return [
            f"v3.3 shape: Klue 5-section spine missing — no heading found "
            f"for: {', '.join(missing)} (need headline / rationale / "
            f"comparison / implications / recommendations)"
        ]
    return []


# §3 anti-hallucination: URLs cited in the brief must be well-formed.
# Real HEAD resolution is documented as a follow-up because the judge
# service host may not have outbound HTTP. Until that lands, this check
# catches obvious slop (no scheme / no host / malformed paths) which is
# what most hallucinated URLs look like.
_CI_V33_URL_REGEX = re.compile(r"https?://[^\s)\]>\"',]+", re.IGNORECASE)


def _ci_check_url_syntactic_validity(brief: str) -> list[str]:
    bad: list[str] = []
    for url in _CI_V33_URL_REGEX.findall(brief):
        try:
            parsed = urlparse(url)
        except ValueError:
            bad.append(url)
            continue
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            bad.append(url)
            continue
        # Hostnames need at least one dot (subdomain.tld), reject single-word
        # hosts that look like placeholder slop ("http://example", "http://x").
        if "." not in parsed.netloc:
            bad.append(url)
    if bad:
        sample = ", ".join(bad[:3])
        suffix = "" if len(bad) <= 3 else f" (+{len(bad) - 3} more)"
        return [
            f"v3.3 anti-hallucination: {len(bad)} URL(s) syntactically "
            f"invalid or look hallucinated: {sample}{suffix}"
        ]
    return []


# §3 quote-grep: any double-quoted span ≥6 words in the brief should appear
# verbatim in some competitor data file. Short quotes (idioms, "the company")
# are excluded to keep false-positives low.
_CI_V33_QUOTE_REGEX = re.compile(r"\"([^\"\n]{30,400})\"")


def _ci_check_quote_grep(
    brief: str, parsed_competitors: dict[str, dict]
) -> list[str]:
    if not parsed_competitors:
        return []  # already flagged at the earlier check
    corpus = json.dumps(parsed_competitors, sort_keys=True).lower()
    fabricated: list[str] = []
    for raw_quote in _CI_V33_QUOTE_REGEX.findall(brief):
        quote = raw_quote.strip()
        # Only enforce on quotes long enough to be load-bearing — 6+ words.
        if len(quote.split()) < 6:
            continue
        if quote.lower() not in corpus:
            fabricated.append(quote[:80])
    if fabricated:
        sample = " | ".join(f'"{q}…"' for q in fabricated[:2])
        suffix = "" if len(fabricated) <= 2 else f" (+{len(fabricated) - 2} more)"
        return [
            f"v3.3 anti-hallucination: {len(fabricated)} quote(s) not "
            f"found in competitor data corpus: {sample}{suffix}"
        ]
    return []


# §3 entity-existence: at least one competitor named in the brief must
# correspond to a competitors/<name>.json file. Catches generic-prose briefs
# that don't actually engage with the researched competitor set.
def _ci_check_entity_existence(
    brief: str, competitor_filenames: list[str]
) -> list[str]:
    if not competitor_filenames:
        return []  # already flagged earlier
    brief_lower = brief.lower()
    matched = [
        fname
        for fname in competitor_filenames
        if _stem_from_competitor_file(fname).lower() in brief_lower
    ]
    if not matched:
        sample = ", ".join(
            _stem_from_competitor_file(f) for f in competitor_filenames[:3]
        )
        return [
            f"v3.3 anti-hallucination: brief mentions none of the "
            f"researched competitor entities ({sample}); either the brief "
            f"is generic prose or it discusses competitors not in the "
            f"data set (possible entity confabulation)"
        ]
    return []


def _stem_from_competitor_file(filename: str) -> str:
    """`competitors/figma.json` → `figma`. Tokens like underscores and
    hyphens stay; the entity check substring-matches case-insensitively."""
    name = filename[len("competitors/"):] if filename.startswith("competitors/") else filename
    if name.endswith(".json"):
        name = name[: -len(".json")]
    return name


# §3 "as of" freshness marker: the brief must signal a knowledge cutoff
# somewhere. Catches briefs that read confidently without dating themselves.
_CI_V33_AS_OF_REGEX = re.compile(
    r"\bas of\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|"
    r"Q[1-4]\s+\d{4}|[A-Z][a-z]+\s+\d{4})",
    re.IGNORECASE,
)


def _ci_check_as_of_marker(brief: str) -> list[str]:
    if not _CI_V33_AS_OF_REGEX.search(brief):
        return [
            'v3.3 anti-hallucination: brief lacks an "as of <date>" '
            "freshness marker (required to signal knowledge cutoff and "
            "defend against recency-cutoff distortion)"
        ]
    return []


# §3 recent-date check: at least one parseable date in the brief should be
# within 90 days of "now". Without this, the brief may be silently projecting
# training-cutoff landscape into the present.
_CI_V33_ISO_DATE_REGEX = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_CI_V33_LONG_DATE_REGEX = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})\b"
)
_CI_V33_MONTH_INDEX = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_CI_V33_RECENT_WINDOW_DAYS = 90


def _ci_check_recent_date(
    brief: str, *, now: datetime | None = None
) -> list[str]:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=_CI_V33_RECENT_WINDOW_DAYS)
    found_dates: list[datetime] = []

    for y, m, d in _CI_V33_ISO_DATE_REGEX.findall(brief):
        try:
            found_dates.append(
                datetime(int(y), int(m), int(d), tzinfo=timezone.utc)
            )
        except ValueError:
            continue

    for month_str, day_str, year_str in _CI_V33_LONG_DATE_REGEX.findall(brief):
        month_key = month_str[:3].lower()
        month = _CI_V33_MONTH_INDEX.get(month_key)
        if not month:
            continue
        try:
            found_dates.append(
                datetime(int(year_str), month, int(day_str), tzinfo=timezone.utc)
            )
        except ValueError:
            continue

    if not found_dates:
        return [
            "v3.3 anti-hallucination: brief contains no parseable dates "
            "(ISO or month-name format) — cannot verify recency"
        ]
    if not any(d >= cutoff for d in found_dates):
        latest = max(found_dates)
        days_old = (now - latest).days
        return [
            f"v3.3 anti-hallucination: most recent cited date is "
            f"{latest.date().isoformat()} ({days_old} days old, > "
            f"{_CI_V33_RECENT_WINDOW_DAYS}-day window); brief may be "
            f"projecting stale / training-cutoff landscape"
        ]
    return []


# ─── Monitoring ──────────────────────────────────────────────────────────


async def _validate_monitoring(outputs: dict[str, str]) -> StructuralResult:
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
    # R-#36 removed: `synth_matches_stories` and `no_excessive_rework` were
    # PROCESS gates, not output-quality measures. Output quality on the final
    # artifact is judged by the gradient + calibration judges — process
    # efficiency isn't a quality signal.
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

    # 14. Claim-grounding — R-#37 replaced a single-string regex guard
    #     ("Digest persisted") with a Sonnet pass that extracts ALL
    #     side-effect claims from session.md and verifies each against
    #     the outputs bundle. Covers more hallucination patterns than
    #     the old regex (which only caught one phrasing).
    #
    #     Deferred import — keeps the structural module import-clean when
    #     the Claude CLI is unavailable (e.g. in unit tests that never
    #     hit the claim-grounding path).
    if session_md:
        from .structural_agent import SonnetAgentError, verify_claims_async

        try:
            verdicts = await verify_claims_async(session_md, outputs)
        except SonnetAgentError as e:
            # Plan's "fail loud, no silent-fallback" policy — surface the
            # subprocess failure as a structural failure rather than
            # letting an unchecked claim pass through.
            failures.append(f"claim_grounding_unavailable: {e}")
        else:
            for verdict in verdicts:
                _assert(
                    "claim_grounded",
                    verdict.supported,
                    f"unsupported claim: {verdict.claim!r} — {verdict.reason}",
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

# ─── Marketing Audit ─────────────────────────────────────────────────────


# 9 deliverable sections per master plan §2.2 (CAD-2 lock = "Both"),
# matching src/audit/agent_models.py:ReportSection enum. These are the
# pydantic-validated SubSignal/ParentFinding routing keys; findings.md
# section headers render from these IDs (display renames per §2.2 —
# e.g. geo → "AI Visibility (GEO)", martech_attribution → "MarTech,
# Measurement & Compliance" — happen at template render-time, not at
# validator time).
#
# Note: findability/narrative/acquisition/experience are the 4 Stage-2
# AGENT names (CAD-3), distinct from these section IDs. state_of_business
# is the §2.6 deliverable-render opener for Phase-0 ParentFindings,
# also not a ReportSection ID.
NINE_SECTIONS_MARKETING_AUDIT: tuple[str, ...] = (
    "seo",
    "geo",
    "competitive",
    "monitoring",
    "conversion",
    "distribution",
    "lifecycle",
    "martech_attribution",
    "brand_narrative",
)

# 3-tier proposal headers in fixed order (master plan §3.7 + §7.2 +
# 2026-04-24-005:1310). Matches src.audit.agent_models.ProposalTier.
THREE_TIER_PROPOSAL: tuple[str, ...] = ("fix_it", "build_it", "run_it")


def _validate_marketing_audit(outputs: dict[str, str]) -> StructuralResult:
    """Marketing audit: findings.md has all 9 deliverable sections;
    proposal.md (when present) has the 3 tier headers in fixed order.

    Shape-only — judges score quality. Section names are matched
    case-insensitively against ``# `` / ``## `` markdown headers; the
    canonical names in NINE_SECTIONS_MARKETING_AUDIT are sufficient
    even if the rendered display name differs (e.g. ``geo`` displayed
    as ``AI Visibility``). Either ``findings.md`` is present and
    structurally valid, OR no findings file exists at all (a missing
    file is a structural failure for a marketing_audit deliverable).
    """
    failures: list[str] = []

    # ── findings.md — required, must list all 9 sections ──
    findings_keys = [
        k for k in outputs
        if k == "findings.md" or k.endswith("/findings.md")
    ]
    if not findings_keys:
        failures.append("No findings.md found")
        return StructuralResult(passed=False, failures=failures)

    findings_content = outputs[findings_keys[0]]
    if not findings_content or not findings_content.strip():
        failures.append(f"{findings_keys[0]}: empty content")
        return StructuralResult(passed=False, failures=failures)

    findings_lower = findings_content.lower()
    missing_sections = [
        s for s in NINE_SECTIONS_MARKETING_AUDIT
        if s not in findings_lower
    ]
    if missing_sections:
        failures.append(
            f"{findings_keys[0]}: missing required sections: "
            f"{', '.join(missing_sections)}"
        )

    # ── proposal.md — optional, but if present must have 3 tiers ──
    proposal_keys = [
        k for k in outputs
        if k == "proposal.md" or k.endswith("/proposal.md")
    ]
    if proposal_keys:
        proposal_content = outputs[proposal_keys[0]]
        if not proposal_content or not proposal_content.strip():
            failures.append(f"{proposal_keys[0]}: empty content")
        else:
            # Find each tier header's first occurrence; require
            # they appear in fixed order.
            proposal_lower = proposal_content.lower()
            tier_positions: list[int | None] = [
                proposal_lower.find(t) for t in THREE_TIER_PROPOSAL
            ]
            missing_tiers = [
                t for t, p in zip(THREE_TIER_PROPOSAL, tier_positions)
                if p == -1
            ]
            if missing_tiers:
                failures.append(
                    f"{proposal_keys[0]}: missing required tier "
                    f"headers: {', '.join(missing_tiers)}"
                )
            elif tier_positions != sorted(tier_positions):
                failures.append(
                    f"{proposal_keys[0]}: tier headers must appear "
                    f"in fixed order fix_it → build_it → run_it"
                )

    return StructuralResult(passed=len(failures) == 0, failures=failures)


# STRUCTURAL_DOC_FACTS and STRUCTURAL_GATE_FUNCTIONS now live in
# autoresearch.lane_registry as derived re-exports — single source of truth.
# Consumers (regen_program_docs, tests) import from lane_registry directly.
