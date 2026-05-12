"""Novelty rejection for evolve mutants (Stream C C1).

Hybrid design — mirrors ShinkaEvolve's algorithm with two adaptations
to fit gofreddy's "subscription-CLI only, no API keys" convention:

1. **Similarity metric:** word-shingle Jaccard instead of vector
   embeddings (no external embedding model needed)
2. **Tie-breaker:** codex CLI (subscription) instead of a free-form
   LLM client

Flow per candidate:

1. Gather candidate's source-file concatenation (the same text the
   judges score against).
2. Find the K most-recent same-lane siblings from lineage history.
3. Compute Jaccard similarity vs each sibling (cheap, deterministic).
4. If ``max similarity < similarity_threshold`` → auto-accept (the
   candidate is clearly different; no codex call).
5. Otherwise, invoke codex CLI with the (most-similar sibling,
   candidate) pair and ask NOVEL or DUPLICATE.
6. Reject only when codex returns DUPLICATE.

Gated on ``AUTORESEARCH_NOVELTY_REJECTION`` at the call site
(``evolve.cmd_run``). Accept-by-default on any error (codex outage,
empty candidate, no siblings, etc.) so an infra hiccup never blocks
the evolve loop.

Pattern source: SakanaAI/ShinkaEvolve commit
``5aadedaa940be9da9fdfe6cecc710f307f0817e2`` (Apache-2.0). The
algorithm structure (cheap similarity pre-filter + LLM tie-breaker)
is the part we re-use; the specific similarity metric and LLM
client are swapped for codebase-appropriate alternatives. See
``vendor/shinka_evolve/ATTRIBUTION.md``.
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# Text extensions that count as "variant source" for novelty purposes.
# We embed only the agent-modifiable source (lane prose, programs,
# configs) — not generated sessions or judge outputs, which would
# drift with scoring noise rather than with actual mutation.
_TEXT_EXTS = frozenset({".md", ".yaml", ".yml", ".txt"})

# Subdirectories under a variant_dir whose contents must NEVER be
# included in the similarity input — they are runtime/generated
# artifacts, not source. Including them would make sibling
# similarity track score noise instead of mutation.
_SKIP_SUBDIRS = frozenset({
    "sessions", "metrics", "archived_sessions", ".meta_workspace", "logs",
})

# Word-shingle size (k-grams of words). 5 words is the standard
# trade-off: small enough to catch local edits, large enough to
# avoid spurious overlap from common phrases.
_SHINGLE_K = 5

# Jaccard threshold above which we ask codex for a verdict. Below it
# we auto-accept. Default 0.3 means: when at least 30% of word-shingles
# overlap with a sibling, we treat it as borderline and let codex
# decide. Operator-tunable via AUTORESEARCH_NOVELTY_THRESHOLD.
_DEFAULT_THRESHOLD = 0.3

# Number of most-recent same-lane siblings to compare against. The
# meta-agent rarely duplicates ancient history, so a tight window
# keeps costs bounded without missing realistic duplicate patterns.
_DEFAULT_K_RECENT = 5

# Per-variant character cap for the codex prompt. Codex handles long
# inputs but we cap to keep latency + cost predictable. ~30K chars
# ≈ ~7-8K tokens per variant, ~16K total — well under context limits.
_PROMPT_CHAR_CAP = 30_000

# Codex timeout for the novelty verdict. Way shorter than the judge
# default (15 min) — this is a one-shot yes/no, not heavy scoring.
_CODEX_TIMEOUT_S = 120


_NOVELTY_PROMPT_TEMPLATE = """You are comparing two variants of agent prose used in an autoresearch evolution loop.

The goal is to decide whether Variant B is a meaningfully different STRATEGY from Variant A, or just a paraphrase / near-duplicate of it.

<variant_a>
{variant_a}
</variant_a>

<variant_b>
{variant_b}
</variant_b>

Definitions:
- NOVEL: Variant B uses a substantively different approach — different instructions, different constraints, different angle, different operational behavior — than Variant A. The underlying strategy for the agent has changed in a way that would plausibly change what the agent does.
- DUPLICATE: Variant B is essentially the same as Variant A. Same intent, same operational behavior, same constraints. Differences are wording, formatting, ordering, or trivial edits that do not change what the agent would do.

Reply with exactly one word on its own line at the end of your response: either NOVEL or DUPLICATE. Do not hedge."""


def _gather_variant_text(variant_dir: Path) -> str:
    """Concatenate the variant's source files into a single string.
    Stable across runs (sorted paths + relative anchors)."""
    if not variant_dir.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(variant_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _TEXT_EXTS:
            continue
        try:
            rel = path.relative_to(variant_dir)
        except ValueError:
            continue
        if any(part in _SKIP_SUBDIRS for part in rel.parts):
            continue
        try:
            chunks.append(
                f"# {rel.as_posix()}\n{path.read_text(encoding='utf-8', errors='replace')}"
            )
        except OSError:
            continue
    return "\n\n".join(chunks)


def _shingles(text: str, k: int = _SHINGLE_K) -> set[str]:
    """Return the set of k-word shingles for ``text``. Short texts
    (fewer than k words) collapse to a single bucket so they can still
    participate in Jaccard against another short text."""
    words = text.split()
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard index in [0, 1]. Returns 0 when either side is empty
    so the caller can treat that as "no overlap, accept-by-default"."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    if intersection == 0:
        return 0.0
    return intersection / len(a | b)


def _resolve_recent_siblings(
    archive_dir: Path, lane: str, exclude_id: str, k: int = _DEFAULT_K_RECENT,
) -> list[tuple[str, Path]]:
    """Return ``(variant_id, variant_dir)`` for the ``k`` most-recent
    same-lane siblings, excluding ``exclude_id``. Sources from
    ``load_lineage_history`` which is chronologically ordered.
    """
    try:
        from autoresearch.archive_index import load_lineage_history  # noqa: PLC0415
    except ImportError:
        return []
    try:
        entries = load_lineage_history(archive_dir)
    except Exception:
        return []

    seen: set[str] = set()
    siblings: list[tuple[str, Path]] = []
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        variant_id = entry.get("id")
        if not isinstance(variant_id, str) or not variant_id:
            continue
        if variant_id == exclude_id or variant_id in seen:
            continue
        seen.add(variant_id)
        entry_lane = str(entry.get("lane") or "").strip().lower()
        if entry_lane and entry_lane != lane.strip().lower():
            continue
        variant_dir = archive_dir / variant_id
        if not variant_dir.is_dir():
            continue
        siblings.append((variant_id, variant_dir))
        if len(siblings) >= k:
            break
    return siblings


def _default_threshold() -> float:
    try:
        return float(os.environ.get("AUTORESEARCH_NOVELTY_THRESHOLD", _DEFAULT_THRESHOLD))
    except (TypeError, ValueError):
        return _DEFAULT_THRESHOLD


def _truncate_for_prompt(text: str, cap: int = _PROMPT_CHAR_CAP) -> str:
    if len(text) <= cap:
        return text
    # Truncate in the middle so we keep the head + tail context (a
    # variant's intro and its closing notes both signal the strategy).
    half = cap // 2
    return text[:half] + "\n\n[... TRUNCATED FOR PROMPT ...]\n\n" + text[-half:]


def _parse_novelty_verdict(text: str) -> bool | None:
    """Return ``True`` for NOVEL, ``False`` for DUPLICATE, ``None`` on
    ambiguous/empty output. Callers map ``None`` to accept-by-default
    so an unparseable codex response can't reject a legitimate variant.
    """
    if not text:
        return None
    # Search lines from the tail forward — codex typically emits a
    # rationale paragraph followed by the verdict word.
    for raw in reversed(text.splitlines()):
        token = raw.strip().upper().rstrip(".:,!?*-_").lstrip("*_")
        if token == "NOVEL" or token == "**NOVEL**":
            return True
        if token == "DUPLICATE" or token == "**DUPLICATE**":
            return False
    # Fallback: look at the last ~500 chars and prefer the *later*
    # occurrence (in case the model talks about both definitions in
    # its rationale before its final word).
    tail = text.upper()[-500:]
    novel_pos = tail.rfind("NOVEL")
    dup_pos = tail.rfind("DUPLICATE")
    if novel_pos < 0 and dup_pos < 0:
        return None
    if dup_pos > novel_pos:
        return False
    return True


def _codex_novelty_judge(
    variant_a_text: str,
    variant_b_text: str,
) -> tuple[bool, str]:
    """Ask codex whether Variant B is novel vs Variant A. Returns
    ``(is_novel, raw_verdict)`` where ``raw_verdict`` is "NOVEL",
    "DUPLICATE", or "AMBIGUOUS-ACCEPT". Accept-by-default on any
    failure (codex error, empty output, unparseable verdict) so the
    novelty check never wrongly blocks the evolve loop on infra noise.
    """
    prompt = _NOVELTY_PROMPT_TEMPLATE.format(
        variant_a=_truncate_for_prompt(variant_a_text),
        variant_b=_truncate_for_prompt(variant_b_text),
    )
    try:
        from judges.invoke_cli import invoke_codex  # noqa: PLC0415
    except ImportError:
        return True, "AMBIGUOUS-ACCEPT"
    try:
        stdout = asyncio.run(invoke_codex(prompt, timeout=_CODEX_TIMEOUT_S))
    except (RuntimeError, OSError, asyncio.TimeoutError):
        return True, "AMBIGUOUS-ACCEPT"
    verdict = _parse_novelty_verdict(stdout)
    if verdict is None:
        return True, "AMBIGUOUS-ACCEPT"
    return verdict, ("NOVEL" if verdict else "DUPLICATE")


def check_novelty(
    *,
    variant_dir: Path,
    parent_id: str,
    lane: str,
    archive_dir: Path,
    similarity_threshold: float | None = None,
    k_most_recent: int = _DEFAULT_K_RECENT,
) -> tuple[bool, dict[str, Any]]:
    """Return ``(is_novel, metadata)`` for the candidate at ``variant_dir``.

    See module docstring for the full algorithm. ``similarity_threshold``
    defaults to ``AUTORESEARCH_NOVELTY_THRESHOLD`` env (or 0.3 if unset);
    above the threshold a codex tie-breaker fires. Below it the candidate
    is auto-accepted.
    """
    threshold = (
        similarity_threshold if similarity_threshold is not None
        else _default_threshold()
    )
    metadata: dict[str, Any] = {
        "similarity_threshold": threshold,
        "lane": lane,
        "parent_id": parent_id,
        "k_most_recent": k_most_recent,
    }

    candidate_text = _gather_variant_text(variant_dir)
    if not candidate_text:
        metadata["error"] = "candidate has no embeddable source files"
        return True, metadata

    siblings = _resolve_recent_siblings(
        archive_dir, lane, exclude_id=variant_dir.name, k=k_most_recent,
    )
    metadata["sibling_count"] = len(siblings)
    if not siblings:
        return True, metadata

    candidate_shingles = _shingles(candidate_text)
    similarities: list[tuple[str, float, str]] = []
    for sib_id, sib_dir in siblings:
        sib_text = _gather_variant_text(sib_dir)
        if not sib_text:
            continue
        sib_shingles = _shingles(sib_text)
        sim = _jaccard_similarity(candidate_shingles, sib_shingles)
        similarities.append((sib_id, sim, sib_text))

    if not similarities:
        metadata["note"] = "no embeddable siblings"
        return True, metadata

    similarities.sort(key=lambda triple: triple[1], reverse=True)
    most_similar_id, max_sim, most_similar_text = similarities[0]
    metadata["max_similarity"] = max_sim
    metadata["most_similar_id"] = most_similar_id
    metadata["all_similarities"] = [(sid, sim) for sid, sim, _ in similarities]

    if max_sim < threshold:
        metadata["codex_invoked"] = False
        return True, metadata

    is_novel, raw_verdict = _codex_novelty_judge(most_similar_text, candidate_text)
    metadata["codex_invoked"] = True
    metadata["codex_verdict"] = raw_verdict
    return is_novel, metadata
