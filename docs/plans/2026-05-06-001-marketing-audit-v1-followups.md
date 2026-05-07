# Marketing audit v1 — follow-up backlog (post-merge work)

Captured 2026-05-07 from first §7.7 dry run on `anthropic.com`. These
items are real gaps surfaced during the dry run that should be addressed
in v1.1, but DO NOT block v1 merge per JR direction (Path A).

## Status of v1 dry run

The first dry run produced **customer-quality output**:
- 115 Stage-1b signals + 27 honest gap_flags
- Stage-1c brief.md identified 5 named pain points anchored to signal IDs
- 3 of 4 Stage-2 agents produced rich output (128 sub_signals + 30
  parent_findings + 114 lens-coverage entries across findability /
  experience / acquisition)
- Stage-2 narrative agent failed silent rc=1 across all 3 retries
  (max_turns=40 still tight for narrative's heavy research surface);
  scaffolded empty AgentOutput per stages.py:507-522 graceful-degradation
  path; Stage 3 proceeded
- Schema-fragmentation finding traced cleanly Stage 1b → 1c → 2 with
  proper evidence triangulation (7 SubSignals → 1 ParentFinding)

## v1.1 backlog (from 3-investigator audit)

### F1 — Tier-1 provider fan-out wiring (HIGH)

Master plan §4.2 declares: "Stage 1a's `stage_1_warmup(state)` invokes
provider methods directly via `asyncio.gather` + `Semaphore(12)`." The
23 Tier-1 owned providers exist as importable Python classes (verified
by `audit_wiring_check.py` — 0 IMPORT-ERRORs), but `src/audit/stages.py:
stage_1_warmup` writes an empty cache manifest (`{"tools": [], "checks_run":
0}`) and explicitly defers fan-out to "L4 work."

**Impact today**: Stage 2 agents do their own data fetching via Bash +
curl (95 tool calls in Stage 1b alone). This works because Sonnet/Opus
are smart enough to do real research from public sources, but:

1. **Cost tracking miss**: `tools/cache.py:cache_or_call` is wired to
   record per-call cost. Agent-side curl bypasses this entirely.
   `cost_actual.json` shows $0 across all stages — accidentally accurate
   because no paid API fired; real cost is LLM subscription quota.
2. **Cache reuse zero**: Each cohort cycle re-fetches the same prospect
   data. Variant rotation pays full LLM cost every cycle.
3. **Signal-depth ceiling**: Some lenses (DataForSEO SERP rankings,
   Cloro AI citations across 6 engines, Apify Reddit history) need the
   paid provider's depth. Agent-side WebFetch can't replicate.

**Fix scope**: ~3-5 days. Build `asyncio.gather + Semaphore(12)` over
the 23 providers in `stage_1_warmup`. Each provider's response writes
to `clients/<slug>/audit/cache/<tool>_<hash>.json` via existing
`cache_or_call`. Stage 1b/2 agents then hit cache before live fetch.

### F2 — Stage 2 narrative agent max_turns insufficient (MEDIUM)

Stage 2 narrative agent failed all 3 retries on the Anthropic dry run,
even with max_turns=40 and the fresh-UUID-per-attempt fix. Narrative
has the heaviest research surface: competitor framing + brand-voice +
thought-leadership + 5,280 HackerNews stories' commentary analysis.
Other 3 agents (findability/experience/acquisition) completed on first
attempt at max_turns=40.

**Fix scope**: bump narrative-specific max_turns to 60 OR refactor
narrative prompt to chunk research into 2 phases (research → write).

### F3 — Audit-local cache priming from fixture cache (MEDIUM)

Pre-fetched fixture cache (`~/.local/share/gofreddy/fixture-cache/<pool>/
<fid>/v1.0/`) is populated for all 7 marketing_audit fixtures via
`freddy audit prefetch`. But `freddy audit run` doesn't prime the
audit-local cache from it. Agents fetch live every time even when
data is already cached.

**Fix scope**: ~0.5 day. Add a hook at `cli/freddy/commands/audit.py:
ma_run` start: if fixture-cache exists for this prospect URL, copy
relevant cache files into `clients/<slug>/audit/cache/` before pipeline
fires. Stage 1a's `tools/cache.py:cache_or_call` then hits them on
provider calls.

### F4 — Treat "agent_output.json on disk" as success even on rc=1 (LOW)

When claude exits rc=1 with empty stderr after the agent has already
written its expected output file, current logic still raises
`AgentRunFailed`. Caught 2026-05-07 on Stage 1c (3 attempts all wrote
artifacts but rc=1 retried) and Stage 2 narrative (similar pattern).

**Fix scope**: ~1 hour. After `_spawn_once` returns rc!=0 with empty
stderr, check if expected output files exist on disk. If yes, treat as
graceful pass. If no, retry as transient.

### F5 — Holdout rotation policy (LOW, structural)

Standard ML hygiene says held-out test set is never seen during
training. Over many promotion cycles, the same 4 marketing_audit
holdout fixtures (Cursor/Ambroziak/Harvey/Hippocratic) become an
implicit second training set as variants that pass once continue
to pass on the same brands.

**Fix scope**: ~1 day. Add a rotation policy: every N cohort cycles,
swap one holdout fixture for a fresh one. Applies to ALL 5 lanes
equally — not marketing_audit-specific.

### F6 — Diversity expansion across narrow lanes (MEDIUM)

Per JR direction 2026-05-07: bump every lane to 16 fixtures (matches
geo's existing pattern). Distribution principle: ~70% internet/SaaS/AI,
~30% other.

| Lane | Current | Gap to 16 |
|---|---|---|
| competitive | 11 | +5 search |
| monitoring | 10 | +6 search |
| storyboard | 10 | +6 search |
| marketing_audit | 7 | +9 search (mine to extend; AI startups + non-AI mix) |

**Fix scope**: 1-2 hours code + $0 in pre-cache spend (use existing
`freddy audit prefetch` pattern for marketing_audit; other lanes use
their existing refresh sources). Recommendation: do AFTER first dry
run signal informs which prospect types need stress-testing.

## Order of work (suggested)

1. **F4** first (1 hour) — eliminates the silent-rc=1 retry waste;
   catches Stage 1c/Stage 2 narrative artifacts cleanly without retries
2. **F3** (0.5 day) — quick win on cache reuse for repeat audits
3. **F1** (3-5 days) — biggest impact on signal depth + cost tracking
4. **F2** (bundled with F4 or F1) — narrative max_turns bump
5. **F6** (parallel — JR-side picks, agent-side prefetch)
6. **F5** (whenever; structural — applies to all lanes)

## Decision gate

After v1 ships and 1-3 paid audits run, re-evaluate:
- If customers consistently flag "more signal density on X axis" → F1 is
  the unlock. Schedule it.
- If variant rotation cost becomes prohibitive → F3 is the unlock.
- If first audits' output quality is sufficient as-is, F1/F3 stay
  v1.2 backlog. Ship F4 + F6 as quality-of-life improvements.
