"""Novelty rejection for evolve mutants (Stream C C1).

Wraps ``vendor/shinka_evolve/novelty_judge.py``'s ``NoveltyJudge`` with a
gofreddy-shaped adapter so we can reject candidate variants too similar
to recent siblings *before* spending judge $ on them. Embeddings come from
``embed_client.embed_text`` (OpenAI ``text-embedding-3-small``).

Gated on ``AUTORESEARCH_NOVELTY_REJECTION`` at the call site (evolve.py).
Inert when the env flag is unset or when the candidate has no siblings
in the same lane (first variant of a lane is always novel).

Failure mode: any EmbeddingUnavailable / IOError during the check fans out
to ``check_novelty`` returning ``(True, {...})`` — i.e., accept by default.
This keeps an embeddings outage from blocking the evolve loop; operators
see the warning in stderr and decide whether to dial back the rejection.

Pattern source: SakanaAI/ShinkaEvolve commit
``5aadedaa940be9da9fdfe6cecc710f307f0817e2`` (Apache-2.0). License + full
attribution at ``vendor/shinka_evolve/{LICENSE,ATTRIBUTION.md}``.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Repo root is on sys.path via the package boot in evolve.py; the vendor
# subdir doesn't have an __init__.py so import it as a path-anchored
# module via the dotted name.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from vendor.shinka_evolve.novelty_judge import NoveltyJudge  # noqa: E402

from autoresearch.embed_client import EmbeddingUnavailable, embed_text  # noqa: E402


# Text extensions that count as "variant code" for novelty purposes. We
# embed only the agent-modifiable source (lane prose, programs, configs)
# — not generated sessions or judge outputs, which would drift with
# scoring noise rather than with actual mutation.
_TEXT_EXTS = frozenset({".md", ".yaml", ".yml", ".txt"})

# Subdirectories under a variant_dir whose contents must NEVER be included
# in the variant's embedding — they are runtime/generated artifacts, not
# source code. Including them would make sibling embeddings drift with
# scoring noise and tank the similarity signal.
_SKIP_SUBDIRS = frozenset({
    "sessions", "metrics", "archived_sessions", ".meta_workspace", "logs",
})


@dataclass
class _Program:
    """Duck-typed stand-in for ShinkaEvolve's ``Program``.

    The vendored ``NoveltyJudge`` only accesses ``.code`` (when invoking the
    LLM tie-breaker, which we don't enable for first-pass deployment) and
    ``.island_idx`` (used by the database adapter to scope similarity to
    one island). gofreddy doesn't have islands, so we use lane-as-island
    and always pass ``island_idx=0``.
    """
    code: str = ""
    island_idx: int = 0
    variant_id: str = ""


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [-1, 1]; clipped to [0, 1] for novelty use
    (negative similarity has no meaningful interpretation here)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def _gather_variant_text(variant_dir: Path) -> str:
    """Concatenate the variant's source files into a single string for
    embedding. Stable across runs of the same variant (sorted paths +
    relative anchors)."""
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
            chunks.append(f"# {rel.as_posix()}\n{path.read_text(encoding='utf-8', errors='replace')}")
        except OSError:
            continue
    return "\n\n".join(chunks)


class _ArchiveAdapter:
    """Database-shaped adapter that NoveltyJudge consumes.

    Provides:
    - ``compute_similarity(embedding, island_idx) -> list[float]``: cosine
      similarity scores against each known sibling embedding (excluding
      the candidate itself).
    - ``get_most_similar_program(embedding, island_idx) -> _Program | None``:
      the sibling with the highest similarity (None when no siblings).

    ``island_idx`` is ignored — gofreddy lanes are treated as a single
    island. The adapter is constructed with sibling (variant_id, embedding)
    pairs already resolved; sibling discovery happens in ``check_novelty``.
    """

    def __init__(self, siblings: list[tuple[str, list[float]]]):
        self._siblings = siblings  # list of (variant_id, embedding)
        self.island_manager = None  # not used by the path we exercise

    def compute_similarity(
        self, embedding: list[float], island_idx: int | None = 0,
    ) -> list[float]:
        return [_cosine_similarity(embedding, emb) for _, emb in self._siblings]

    def get_most_similar_program(
        self, embedding: list[float], island_idx: int | None = 0,
    ) -> _Program | None:
        if not self._siblings:
            return None
        sims = [_cosine_similarity(embedding, emb) for _, emb in self._siblings]
        best_idx = max(range(len(sims)), key=lambda i: sims[i])
        return _Program(code="", island_idx=0, variant_id=self._siblings[best_idx][0])


def _resolve_siblings(
    archive_dir: Path, lane: str, exclude_id: str,
) -> list[tuple[str, Path]]:
    """Return ``(variant_id, variant_dir)`` pairs for known siblings of
    ``exclude_id`` on ``lane``. Siblings are sourced from
    ``archive_index.load_latest_lineage`` and filtered by lane field on
    the lineage entry. Skips entries whose directory is missing.
    """
    try:
        from autoresearch.archive_index import load_latest_lineage  # noqa: PLC0415
    except ImportError:
        return []
    try:
        latest = load_latest_lineage(archive_dir)
    except Exception:
        return []
    siblings: list[tuple[str, Path]] = []
    for variant_id, entry in latest.items():
        if variant_id == exclude_id:
            continue
        if not isinstance(entry, dict):
            continue
        entry_lane = str(entry.get("lane") or "").strip().lower()
        if entry_lane and entry_lane != lane.strip().lower():
            continue
        variant_dir = archive_dir / variant_id
        if not variant_dir.is_dir():
            continue
        siblings.append((variant_id, variant_dir))
    return siblings


def _default_threshold() -> float:
    try:
        return float(os.environ.get("AUTORESEARCH_NOVELTY_THRESHOLD", "0.95"))
    except (TypeError, ValueError):
        return 0.95


def check_novelty(
    *,
    variant_dir: Path,
    parent_id: str,
    lane: str,
    archive_dir: Path,
    similarity_threshold: float | None = None,
    max_attempts: int = 1,
) -> tuple[bool, dict[str, Any]]:
    """Return ``(is_novel, metadata)`` for the candidate at ``variant_dir``.

    Embeds the candidate's source-file concatenation via
    ``embed_text`` and compares against each sibling variant on the same
    lane (one embedding per sibling, in-memory LRU cached). Defers the
    accept/reject decision to ``NoveltyJudge.assess_novelty_with_rejection_sampling``
    so the vendor's algorithm stays the source of truth.

    Defaults to a strict ``similarity_threshold=0.95`` — only near-duplicate
    mutants get rejected. Operators can dial down via
    ``AUTORESEARCH_NOVELTY_THRESHOLD``.

    ``max_attempts=1`` disables the vendor's retry-with-resample loop: we
    don't drive mutation from here, so retrying inside the check would
    just re-test the same candidate against the same siblings.
    """
    metadata: dict[str, Any] = {
        "similarity_threshold": (
            similarity_threshold if similarity_threshold is not None
            else _default_threshold()
        ),
        "lane": lane,
        "parent_id": parent_id,
    }

    try:
        candidate_text = _gather_variant_text(variant_dir)
    except Exception as exc:
        metadata["error"] = f"gather_variant_text failed: {exc}"
        return True, metadata
    if not candidate_text:
        metadata["error"] = "candidate has no embeddable source files"
        return True, metadata

    sibling_paths = _resolve_siblings(archive_dir, lane, exclude_id=variant_dir.name)
    if not sibling_paths:
        metadata["sibling_count"] = 0
        return True, metadata

    try:
        candidate_embedding = embed_text(candidate_text)
    except EmbeddingUnavailable as exc:
        metadata["error"] = f"candidate embedding unavailable: {exc}"
        return True, metadata

    sibling_embeddings: list[tuple[str, list[float]]] = []
    for sib_id, sib_dir in sibling_paths:
        try:
            sib_text = _gather_variant_text(sib_dir)
            if not sib_text:
                continue
            sib_emb = embed_text(sib_text)
        except (EmbeddingUnavailable, OSError):
            # Sibling-level errors don't tank the whole check; the
            # remaining siblings can still provide a similarity signal.
            continue
        sibling_embeddings.append((sib_id, sib_emb))

    if not sibling_embeddings:
        metadata["sibling_count"] = 0
        metadata["note"] = "all siblings failed to embed"
        return True, metadata

    threshold = metadata["similarity_threshold"]
    adapter = _ArchiveAdapter(sibling_embeddings)
    judge = NoveltyJudge(
        novelty_llm_client=None,
        similarity_threshold=threshold,
        max_novelty_attempts=max(1, int(max_attempts)),
    )
    is_novel, vendor_meta = judge.assess_novelty_with_rejection_sampling(
        exec_fname=str(variant_dir / "_novelty_candidate.txt"),  # unused; LLM path off
        code_embedding=candidate_embedding,
        parent_program=_Program(code="", island_idx=0, variant_id=parent_id),
        database=adapter,
    )
    metadata["sibling_count"] = len(sibling_embeddings)
    metadata["max_similarity"] = vendor_meta.get("max_similarity")
    metadata["similarity_scores"] = vendor_meta.get("similarity_scores", [])
    return bool(is_novel), metadata
