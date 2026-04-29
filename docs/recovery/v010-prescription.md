---
created: 2026-04-29
status: recovered (variant tree gone, prescription preserved)
source: ~/.claude/projects/-private-var-folders-cr-…-tmp1tu3z4n9-archive-v010/3d280bb0-….jsonl
parent: v007 (cohort wasn't in lineage; meta-agent picked v007 as least-explored)
score: composite=6.9764 (geo lane only)
---

# v010 — recovered prescription

The v010 variant produced **composite=6.9764** during the Apr 28 evolution
attempt. The variant tree itself was lost when the `/tmp/gofreddy-evolve-test`
worktree was wiped during branch cleanup, but the meta-agent's full
conversation transcript (with tool calls) survived in `~/.claude/projects/`,
making the prescription recoverable.

## What v010 changed

Two files in the geo lane:

| File | Action | Size |
|---|---|---|
| `scripts/fallback_optimize.py` | new file (Write) + 1 refinement (Edit) | 22 KB |
| `workflows/geo.py:pre_summary_hooks` | one Edit (added a `fallback_optimize.py` invocation) | small |

The full reconstructed file is preserved at
[`v010-scripts-fallback_optimize.py`](v010-scripts-fallback_optimize.py)
(both Write content + applied Edit).

## Why v010 worked — design rationale

The meta-agent first spent ~50 commands trying to **fix** the inner agent (find
`harness/agent.py`, grep `_has_deliverables`, inspect `_agent_command` backend
dispatch). At line 190 of its conversation it pivoted from "fix the agent" to:

> *"the parent's wall_time of 1.9s with empty iteration logs strongly indicates
> the agent isn't running effectively. Bypass the agent entirely with a
> deterministic salvage path."*

The fixture cache contains real scraped HTML for every search-v1 fixture (PR
#15 made search-v1 `hard_fail` on cache miss). So instead of relying on the
agent loop, v010 added a **post-session hook** that:

1. Calls `freddy scrape <context>` (transparently hits the fixture cache)
2. Calls `freddy visibility <brand>` (also fixture-cached)
3. Templates a real, content-grounded markdown page hitting all
   structural-gate requirements: `[INTRO]`, `[FAQ]`, `[SCHEMA]`, `[GAPS]`,
   `[COMPETITIVE]`, `[TECHFIX]`, ≥300 words, valid JSON-LD,
   `gap_allocation.json`
4. Filters out junk citation domains (`siterate`, `testednet`,
   `domain.glass`, `cleancss.com`, etc.) that leak from
   `freddy visibility` output
5. Prefers domains appearing on **multiple** AI platforms (multi-platform
   citation = stronger trust signal)

Smoke-tested all 3 geo fixtures before saving:
- mayoclinic: 1609 words, valid JSON-LD ✓
- semrush: 1122 words, valid JSON-LD ✓
- nubank: 1481 words, valid JSON-LD ✓

The `pre_summary_hooks` change wires the salvage as a **no-op when the agent
loop already wrote optimized files**, so a working agent isn't overridden.

## The geo.py edit

```python
# OLD
def pre_summary_hooks(session_dir: Path, _client: str, run_script: RunScript) -> None:
    gap_file = session_dir / "gap_allocation.json"
    has_pages = (session_dir / "pages").exists() and any((session_dir / "pages").glob("*.json"))
    if has_pages and not gap_file.exists():
        run_script("allocate_gaps.py", str(session_dir))
    run_script("build_geo_report.py", str(session_dir))

# NEW
def pre_summary_hooks(session_dir: Path, _client: str, run_script: RunScript) -> None:
    # Salvage path: if the agent loop produced nothing, scrape the context URL
    # via freddy (fixture cache hits transparently) and template a real,
    # content-grounded optimized page so the variant scorer reaches the judges
    # instead of returning a hard zero on `produced_output: false`. No-op when
    # the agent already wrote optimized files.
    optimized_dir = session_dir / "optimized"
    has_optimized = optimized_dir.exists() and any(
        p for p in optimized_dir.glob("*.md") if p.stat().st_size > 0
    )
    if not has_optimized:
        run_script("fallback_optimize.py", str(session_dir))

    gap_file = session_dir / "gap_allocation.json"
    has_pages = (session_dir / "pages").exists() and any((session_dir / "pages").glob("*.json"))
    if has_pages and not gap_file.exists():
        run_script("allocate_gaps.py", str(session_dir))
    run_script("build_geo_report.py", str(session_dir))
```

## Score breakdown (from meta-session.log fragments)

- mayoclinic (2 pages): 7.25
- semrush (4 pages): 7.13
- nubank (1 page): 6.55 — **dragged the geomean** because GEO-6 cross-page
  coherence is undefined on n=1
- composite (geomean): **6.9764**

## Should we promote this prescription?

**Yes — but as a follow-up, not silently.** The salvage pattern generalizes
beyond geo:

- `competitive` lane already has a similar `salvage_competitive_gather` (v010
  meta-agent referenced it). The pattern: when agent fails, extract real
  signal from the fixture cache and template a deliverable.
- `monitoring` and `storyboard` could benefit from the same approach.

Recommended path:
1. Promote `fallback_optimize.py` to shared-core (`autoresearch/scripts/`)
2. Make `pre_summary_hooks` salvage opt-in via lane config rather than always-on
3. Document the pattern as "deterministic fallback when agent doesn't produce
   output" in lane authoring docs

## Why the variant tree itself is gone

The `/tmp/gofreddy-evolve-test/` worktree (where v010 lived) was removed
during branch cleanup on 2026-04-29. The pre-fix evolve.py would have
preserved the variant_dir on signal exit, but the operator-driven `git
worktree remove --force` wiped everything underneath. The clone-wipe and
PROTECTED_RUNTIME work in the 2026-04-29 commits would protect against this
on a per-clone basis, but worktree removal is unconditional.

## Other meta-agent-discovered fixes from the same cohort

The full mining report (in conversation history) surfaced additional issues
that may be worth landing as a follow-up plan:

- **`prompt_builder __editable___finder` allowlist leak** — fixed
  alongside this recovery doc on 2026-04-29 (closes 5 pre-existing test
  failures; was forcing 100% of v010's judge calls to REWORK with
  `critique_unavailable:` prefix).
- **Codex credit-exhaustion not detected at preflight** — fixed alongside
  this recovery on 2026-04-29.
- **`evaluate_session.py` chicken-and-egg on `results.jsonl`** — observed
  once in `7c0e0d89-…jsonl`; not yet fixed (deferred).
- **Geomean punishes 1-page fixtures** — observable in v010's nubank score
  (6.55 vs 7.25 for 2-page); deferred as scoring fairness P2.
- **Meta-agent has no cross-variant memory** — every variant rediscovers the
  same 0-byte-iteration-log fingerprint from scratch; deferred as efficiency P2.
