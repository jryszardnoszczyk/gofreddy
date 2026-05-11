# Attribution — SakanaAI/ShinkaEvolve

**Source:** https://github.com/SakanaAI/ShinkaEvolve
**Commit:** `5aadedaa940be9da9fdfe6cecc710f307f0817e2` (verified 2026-05-11)
**License:** Apache-2.0 (see `LICENSE` in this directory)
**Vendored:** 2026-05-11 for gofreddy Stream C Unit C1 (Novelty-rejection sampling)
**Paper:** *ShinkaEvolve* — Sakana AI, ICLR 2026, arXiv 2509.19349

## Files vendored

- `novelty_judge.py` (225 LOC) — `shinka/core/novelty_judge.py` from upstream, verbatim
- `LICENSE` — Apache-2.0 verbatim from upstream root

## Modifications applied (when wired into autoresearch/)

(v2 was deprecated; the integration target is autoresearch/, not autoresearch_v2/.)

- `from shinka.database import Program` → replaced with `Program = Any` type stub
- `from shinka.llm import LLMClient` → replaced with `LLMClient = Any` type stub
- `from shinka.prompts import NOVELTY_SYSTEM_MSG, NOVELTY_USER_MSG` → empty/inline placeholders (the LLM tie-breaker path is unused — gofreddy passes ``novelty_llm_client=None`` for first-pass deployment, so these are never read at runtime)
- All other lines preserved verbatim from upstream commit ``5aadedaa940be9da9fdfe6cecc710f307f0817e2``

## API surface (post-modification)

```python
class NoveltyJudge:
    def __init__(self, novelty_llm_client=None, language="python",
                 similarity_threshold=1.0, max_novelty_attempts=3): ...
    def assess_novelty_with_rejection_sampling(
        self, exec_fname, code_embedding, parent_program, database
    ) -> tuple[bool, dict]: ...
    def should_check_novelty(self, code_embedding, generation,
                              parent_program, database) -> bool: ...
    def check_llm_novelty(self, proposed_code, most_similar_program
    ) -> tuple[bool, str, float]: ...
```

## Database duck-typing required from caller

`database` must implement:
- `compute_similarity(embedding: List[float], island_idx: int) -> List[float]`
- `get_most_similar_program(embedding: List[float], island_idx: int) -> Program | None`
- `island_manager.are_all_islands_initialized()` (optional)

For gofreddy v2: implement these on a `Backend` protocol that reads `lanes/<lane>/results.tsv` + embeds historical sibling code via `embed_client.py`.

## Compliance notes (Apache-2.0 §4)

- LICENSE file preserved verbatim in this directory ✓
- No NOTICE file required (upstream has none — verified 2026-05-11) ✓
- Modifications documented in this ATTRIBUTION.md ✓
- File header of vendored file unchanged (no per-file copyright header in upstream) ✓
