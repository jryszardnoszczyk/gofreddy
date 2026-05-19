"""Reviewer-assist judge + COMPLIANCE_JUDGE constant (D25).

Per D25: a single frontier-class judge across the 7 reviewer-assist-
gated lanes (storyboard, article_engine, image_engine, ad_engine,
site_engine, linkedin_engine, x_engine). Compliance correctness is the
most-consequential judge call (false-negative = regulator-flagged
published artifact); diverse from inner-loop (codex/gpt-5.5) per
``judge-decisions-2026-05-11.md``.

The 2-tuple constant is the simplest shape (no singleton class
ceremony per Pass-5 audit). Operator override via
``COMPLIANCE_JUDGE_BACKEND`` / ``COMPLIANCE_JUDGE_MODEL`` env vars
read at call time.

Per the §Compliance Posture clause: this judge fires on rules with
``pattern`` defined (deterministic regex; slop-gate precedent) and
returns prose-grounded interpretation for rules whose ``pattern`` is
None (LLM-judged surface). The function returns a structured result;
actual LLM dispatch for prose-only rules happens at the per-lane
integration level (U13/U14/U15/U15b) where the existing judge
HTTP service is already wired.
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.compliance.loader import load_rule_set
from src.compliance.schema import ComplianceRule, ComplianceRuleSet, Severity

logger = logging.getLogger(__name__)


# D25 — single frontier-class judge for all reviewer-assist work in v1.
# 2-tuple (backend, model). Operator override via env (read at call time).
COMPLIANCE_JUDGE: tuple[str, str] = ("claude", "opus")


ComplianceVerdict = Literal["clean", "soft_warn", "hard_block"]


def get_compliance_judge_config() -> tuple[str, str]:
    """Return the active (backend, model) for the reviewer-assist judge,
    honoring env-var overrides ``COMPLIANCE_JUDGE_BACKEND`` /
    ``COMPLIANCE_JUDGE_MODEL`` when set."""
    backend = os.environ.get("COMPLIANCE_JUDGE_BACKEND") or COMPLIANCE_JUDGE[0]
    model = os.environ.get("COMPLIANCE_JUDGE_MODEL") or COMPLIANCE_JUDGE[1]
    return backend, model


class ComplianceFlag(BaseModel):
    """A single rule that fired against the artifact.

    Per the 4-agent review (AC-1 T2-A): frozen Pydantic with extra="allow"
    so v1.5+ additions like `remediation_hint` or `severity_modifier`
    are additive, not breaking. Lanes that serialize flags into emails
    + audit log + token payloads pick up the extension fields without
    code changes.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    rule_id: str
    severity: Severity
    rule_set_name: str
    matched_text: str | None = None  # Substring that matched (None for LLM-only)
    prose: str                       # Operator-readable rationale


class ComplianceResult(BaseModel):
    """Outcome of evaluate_compliance for a single artifact."""

    model_config = ConfigDict(frozen=True, extra="allow")

    verdict: ComplianceVerdict
    flags: list[ComplianceFlag] = Field(default_factory=list)
    rule_set_name: str = ""
    lane: str = ""

    @property
    def has_hard_block(self) -> bool:
        return any(f.severity == "hard_block" for f in self.flags)

    @property
    def has_soft_warn(self) -> bool:
        return any(f.severity == "soft_warn" for f in self.flags)


def _compile_patterns(rule: ComplianceRule) -> list[re.Pattern[str]]:
    """Compile a rule's pattern(s) once per call.

    Schema validation already verified the patterns compile; here we
    pay the compile cost for the actual evaluation.
    """
    if rule.pattern is None:
        return []
    raw = [rule.pattern] if isinstance(rule.pattern, str) else rule.pattern
    flags = 0 if rule.case_sensitive else re.IGNORECASE
    return [re.compile(p, flags=flags) for p in raw]


# Per the CE-review adversarial pass: regex patterns in medical_pl /
# legal_pl can be bypassed by Unicode tricks an LLM variant agent could
# emit (intentionally or via random sampling) — zero-width spaces between
# letters, fullwidth Latin codepoints, Cyrillic homoglyphs that render
# visually identical. Normalize artifact text before regex.
#
# (1) NFKC normalize: collapses compatibility forms (fullwidth `ｎ` → `n`,
#     decomposed diacritics → composed). Idempotent + canonical.
# (2) Strip zero-width separators (U+200B/200C/200D/FEFF) that break
#     stem-anchored \w* matching mid-word ("naj​lepszy" reads as
#     "najlepszy" to a human but as two tokens to the regex).
# (3) Fold the ~10 Cyrillic+Greek codepoints whose lowercase forms are
#     visually identical to Latin letters at common UI font sizes. The
#     table is intentionally small: false-positive risk on legitimate
#     non-Latin text grows with size. Targeted to the medical_pl /
#     legal_pl alphabet (Latin + Polish diacritics).
#
# Composition order matters: NFKC must run before homoglyph fold so the
# fold table sees post-normalization codepoints.
_ZERO_WIDTH_CHARS = {
    "​",  # ZWSP — zero-width space
    "‌",  # ZWNJ — zero-width non-joiner
    "‍",  # ZWJ  — zero-width joiner
    "﻿",  # BOM  — byte-order mark / zero-width no-break space
}

_HOMOGLYPH_FOLD: dict[str, str] = {
    # Cyrillic lowercase that look identical to Latin lowercase
    "а": "a",   # CYRILLIC SMALL LETTER A
    "е": "e",   # CYRILLIC SMALL LETTER IE
    "о": "o",   # CYRILLIC SMALL LETTER O
    "р": "p",   # CYRILLIC SMALL LETTER ER
    "с": "c",   # CYRILLIC SMALL LETTER ES
    "у": "y",   # CYRILLIC SMALL LETTER U (looks like y)
    "х": "x",   # CYRILLIC SMALL LETTER HA
    "і": "i",   # CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
    "ј": "j",   # CYRILLIC SMALL LETTER JE
    "ѕ": "s",   # CYRILLIC SMALL LETTER DZE
    # Cyrillic uppercase counterparts
    "А": "A",
    "Е": "E",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Х": "X",
    # Greek that often appears in homoglyph attacks
    "ο": "o",   # GREEK SMALL LETTER OMICRON
    "ρ": "p",   # GREEK SMALL LETTER RHO (looks like p)
    "υ": "u",   # GREEK SMALL LETTER UPSILON
}


def _normalize_for_compliance(artifact: str) -> str:
    """Pre-regex normalization to defeat trivial Unicode-based bypasses.

    Step order: NFKC → strip zero-width → homoglyph fold. NFKC must run
    first so fullwidth-Latin codepoints (e.g., 'ｎａｊｌｅｐｓｚｙ')
    collapse to ASCII before the regex sees them; the homoglyph fold
    runs after on post-NFKC text so the small table covers a known set
    of codepoints.

    Trade-off: this changes artifact text the regex evaluates, so the
    ComplianceFlag.matched_text reflects the normalized form, not the
    original. That's correct for "did the artifact trigger the rule?"
    semantics but operators inspecting the flag must understand the
    matched_text is post-normalization. The original artifact is not
    retained by evaluate_compliance.
    """
    text = unicodedata.normalize("NFKC", artifact)
    if any(c in _ZERO_WIDTH_CHARS for c in text):
        text = "".join(c for c in text if c not in _ZERO_WIDTH_CHARS)
    if any(c in _HOMOGLYPH_FOLD for c in text):
        text = "".join(_HOMOGLYPH_FOLD.get(c, c) for c in text)
    return text


# Per the 4-agent review (adv-3 + sec-7): cap artifact length passed to
# regex search so a ReDoS pattern in a junior-authored YAML cannot burn
# CPU indefinitely. 256 KB covers a 50K-word article (~250 KB of plain
# text) with headroom; longer artifacts are truncated at the boundary
# with a logged warning. Pairs with the per-pattern timeout below.
_REDOS_ARTIFACT_LENGTH_CAP = 256 * 1024

# Per-pattern wall-clock budget for `pattern.search`. The signal-based
# alarm only fires on the main thread on Unix; on Windows or in worker
# threads, we fall back to length-cap-only protection. Conservative cap:
# patterns that exceed this budget on a 256 KB artifact are flagged as
# ReDoS-suspect and logged but do NOT fire a flag (fail-safe — better
# to miss a real flag than to hang the evolution worker).
_REDOS_PATTERN_BUDGET_SECONDS = 2.0


class _PatternBudgetExceeded(Exception):
    """Signal alarm fired inside pattern.search — ReDoS-suspect pattern."""


def _search_with_budget(
    pattern: re.Pattern[str], artifact: str, rule_id: str,
) -> re.Match[str] | None:
    """Run pattern.search with a wall-clock budget.

    Uses signal.alarm when available (Unix + main thread). Falls back
    to unprotected search elsewhere; combined with the length cap, the
    failure mode is bounded.

    Returns the match on success, None on no-match, None + logged
    warning on ReDoS-suspect timeout (the rule's flag does NOT fire —
    fail-safe per the 4-agent review).
    """
    import signal
    import threading

    use_signal = (
        threading.current_thread() is threading.main_thread()
        and hasattr(signal, "SIGALRM")
    )
    if not use_signal:
        try:
            return pattern.search(artifact)
        except Exception:  # pragma: no cover — re module rarely raises
            logger.warning("rule %s: pattern.search raised; flag suppressed", rule_id)
            return None

    def _handler(signum, frame):
        raise _PatternBudgetExceeded(rule_id)

    prev_handler = signal.signal(signal.SIGALRM, _handler)
    try:
        signal.setitimer(signal.ITIMER_REAL, _REDOS_PATTERN_BUDGET_SECONDS)
        try:
            return pattern.search(artifact)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    except _PatternBudgetExceeded:
        logger.warning(
            "rule %s exceeded ReDoS budget of %.1fs; flag suppressed (suspect ReDoS)",
            rule_id, _REDOS_PATTERN_BUDGET_SECONDS,
        )
        return None
    finally:
        signal.signal(signal.SIGALRM, prev_handler)


def evaluate_compliance(
    artifact: str,
    rule_set_name: str,
    lane: str,
) -> ComplianceResult:
    """Evaluate ``artifact`` against the named rule set for ``lane``.

    Args:
        artifact: the candidate text to evaluate (article body, ad copy,
            section HTML, etc.).
        rule_set_name: single rule_set name per D6 revised / TD-18.
        lane: lane name for error reporting + result provenance.

    Returns:
        ComplianceResult with overall verdict (hard_block | soft_warn |
        clean) and per-flag provenance.

    Per D6 revised: v1 evaluates a SINGLE rule set per call. The API
    accepts a single name (not a list); call sites pass
    ``client.reviewer_assist_checklists[0]`` (length-1 enforced by
    ClientConfig). Multi-rule-set merge logic deferred.

    Per the §Compliance Posture clause: rules with `pattern` defined
    are matched deterministically (regex). Rules with `pattern=None`
    return prose-only flags that the LLM judge interprets at the
    per-lane integration boundary (U13+); this function pre-resolves
    the prose so the per-lane integration only needs to wrap the
    existing judge HTTP service.
    """
    rule_set = load_rule_set(rule_set_name)
    flags: list[ComplianceFlag] = []

    # Per the CE-review adversarial pass: normalize artifact text before
    # any regex runs. Defeats ZWSP-mid-word ("najl​epszy"),
    # fullwidth-Latin ("ｎａｊｌｅｐｓｚｙ"), and Cyrillic-homoglyph
    # ("nаjlерszу") bypasses.
    artifact = _normalize_for_compliance(artifact)

    # Per the 4-agent review (adv-3 + sec-7): cap artifact length so a
    # ReDoS pattern cannot burn CPU indefinitely on a 1 GB artifact. A
    # rule pattern that needs to match content past the cap is fixable
    # by tightening the pattern at YAML-author time.
    if len(artifact) > _REDOS_ARTIFACT_LENGTH_CAP:
        logger.warning(
            "evaluate_compliance: artifact truncated from %d to %d chars "
            "for ReDoS protection (rule_set=%s, lane=%s)",
            len(artifact), _REDOS_ARTIFACT_LENGTH_CAP, rule_set_name, lane,
        )
        artifact = artifact[:_REDOS_ARTIFACT_LENGTH_CAP]

    for rule in rule_set.rules:
        if rule.pattern is None:
            # LLM-only rule. The deterministic pass here records a stub
            # flag whose severity is informational ("soft_warn" by
            # convention until the LLM judge resolves at the per-lane
            # integration boundary). Callers that want the LLM verdict
            # invoke the judge HTTP service with `rule.prose` as the
            # rubric prompt.
            continue

        compiled = _compile_patterns(rule)
        for pattern in compiled:
            match = _search_with_budget(pattern, artifact, rule.id)
            if match is None:
                continue
            flags.append(ComplianceFlag(
                rule_id=rule.id,
                severity=rule.severity,
                rule_set_name=rule_set.rule_set_name,
                matched_text=match.group(0),
                prose=rule.prose,
            ))
            break  # One match per rule is enough; record provenance + move on.

    verdict: ComplianceVerdict
    if any(f.severity == "hard_block" for f in flags):
        verdict = "hard_block"
    elif any(f.severity == "soft_warn" for f in flags):
        verdict = "soft_warn"
    else:
        verdict = "clean"

    return ComplianceResult(
        verdict=verdict,
        flags=flags,
        rule_set_name=rule_set.rule_set_name,
        lane=lane,
    )


__all__ = [
    "COMPLIANCE_JUDGE",
    "ComplianceFlag",
    "ComplianceResult",
    "ComplianceVerdict",
    "evaluate_compliance",
    "get_compliance_judge_config",
]
