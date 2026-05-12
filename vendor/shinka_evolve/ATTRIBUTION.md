# Attribution — SakanaAI/ShinkaEvolve

**Source:** https://github.com/SakanaAI/ShinkaEvolve
**Commit referenced:** `5aadedaa940be9da9fdfe6cecc710f307f0817e2` (verified 2026-05-11)
**License:** Apache-2.0 (see `LICENSE` in this directory)
**Pattern adopted:** 2026-05-11 for gofreddy Stream C Unit C1 (Novelty-rejection)
**Paper:** *ShinkaEvolve* — Sakana AI, ICLR 2026, arXiv 2509.19349

## What we use from upstream

Pattern only — no upstream code is redistributed. We re-implemented the
algorithm structure of `shinka/core/novelty_judge.py:assess_novelty_with_rejection_sampling`:

1. Compute similarity between a candidate and known siblings
2. If max similarity > threshold, ask an LLM whether the candidate is
   meaningfully different from the most-similar sibling
3. Reject the candidate when the LLM says it is a duplicate

Our implementation lives at `autoresearch/novelty_check.py`. We swap two
pieces of the upstream design to fit gofreddy's conventions:

- **Similarity metric:** word-shingle Jaccard, not vector embeddings.
  Upstream embeds via `text-embedding-3-small` (OpenAI API key); this
  codebase uses subscription-CLI models only (no embeddings exposed).
- **LLM tie-breaker client:** `judges.invoke_cli.invoke_codex`, not the
  upstream's `LLMClient`. Same role (the LLM is the authority on
  novel-vs-duplicate when similarity is borderline), different transport.

## Why pattern-only instead of vendoring

The earlier vendor of `novelty_judge.py` (4 lines patched, otherwise
verbatim) was removed on 2026-05-11 because, after the embedding swap,
we no longer invoke any line of upstream code at runtime. Carrying a
225-line "reference" file that isn't called creates a maintenance hazard:
future readers might think we use it. Keeping just the pattern reference
in this ATTRIBUTION.md + the Apache-2.0 LICENSE is the cleaner credit
path.

## Compliance notes (Apache-2.0)

- LICENSE preserved in this directory for clear credit ✓
- No NOTICE file required (upstream has none — verified 2026-05-11) ✓
- Pattern + commit + paper cited above ✓
- No upstream code redistributed (no §4 redistribution clause applies) ✓
